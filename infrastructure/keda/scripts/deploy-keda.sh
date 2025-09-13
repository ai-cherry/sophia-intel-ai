#!/bin/bash
set -euo pipefail

# KEDA Staged Deployment Script
# Implements progressive rollout with validation at each stage
# Target: Deploy KEDA with 85% scaling improvement (60s to 9s)

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KEDA_DIR="$(dirname "$SCRIPT_DIR")"
NAMESPACE_KEDA="keda-system"
NAMESPACE_ARTEMIS="sophia-system"
NAMESPACE_SOPHIA="sophia-system"
HELM_RELEASE="sophia-intel-keda"
HELM_TIMEOUT="10m"

# Environment detection
ENVIRONMENT="${ENVIRONMENT:-dev}"
DRY_RUN="${DRY_RUN:-false}"
SKIP_TESTS="${SKIP_TESTS:-false}"
ROLLOUT_STRATEGY="${ROLLOUT_STRATEGY:-canary}"  # canary, blue-green, or direct

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
LOG_FILE="/tmp/keda-deployment-$(date +%Y%m%d-%H%M%S).log"
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

log_info() { echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }

# Error handling
trap 'handle_error $? $LINENO' ERR

handle_error() {
    local exit_code=$1
    local line_number=$2
    log_error "Deployment failed at line $line_number with exit code $exit_code"
    log_error "Rolling back changes..."
    rollback_on_failure
    exit $exit_code
}

# Pre-flight checks
preflight_checks() {
    log_info "Running pre-flight checks..."

    # Check required tools
    local required_tools=("kubectl" "helm" "jq" "yq")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is not installed"
            exit 1
        fi
    done

    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    # Check namespaces exist
    local namespaces=("$NAMESPACE_ARTEMIS" "$NAMESPACE_SOPHIA" "monitoring")
    for ns in "${namespaces[@]}"; do
        if ! kubectl get namespace "$ns" &> /dev/null; then
            log_error "Namespace $ns does not exist"
            exit 1
        fi
    done

    # Check if HPA exists (for fallback)
    local hpa_count=$(kubectl get hpa -A | grep -E "sophia|sophia" | wc -l)
    if [ "$hpa_count" -eq 0 ]; then
        log_warning "No existing HPA found for fallback - creating backup HPAs"
        create_backup_hpa
    fi

    log_success "Pre-flight checks passed"
}

# Create backup HPA for fallback
create_backup_hpa() {
    log_info "Creating backup HPAs for fallback..."

    # Sophia HPA
    cat <<EOF | kubectl apply -f -
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sophia-worker-hpa-backup
  namespace: $NAMESPACE_ARTEMIS
  labels:
    app: sophia
    type: backup
    created-by: keda-deployment
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sophia-worker
  minReplicas: 2
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
EOF

    # Sophia HPA
    cat <<EOF | kubectl apply -f -
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sophia-analytics-hpa-backup
  namespace: $NAMESPACE_SOPHIA
  labels:
    app: sophia
    type: backup
    created-by: keda-deployment
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sophia-analytics
  minReplicas: 3
  maxReplicas: 100
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
EOF

    log_success "Backup HPAs created"
}

# Capture baseline metrics
capture_baseline_metrics() {
    log_info "Capturing baseline metrics..."
    "$SCRIPT_DIR/metrics-baseline.sh"
    log_success "Baseline metrics captured"
}

# Stage 1: Deploy KEDA operator
deploy_keda_operator() {
    log_info "Stage 1: Deploying KEDA operator..."

    # Create namespace if it doesn't exist
    kubectl create namespace "$NAMESPACE_KEDA" --dry-run=client -o yaml | kubectl apply -f -

    # Label namespace to disable Istio injection
    kubectl label namespace "$NAMESPACE_KEDA" istio-injection=disabled --overwrite

    # Add KEDA Helm repository
    helm repo add kedacore https://kedacore.github.io/charts
    helm repo update

    # Deploy KEDA using Helm
    local values_file="$KEDA_DIR/helm/values.yaml"
    local env_values_file="$KEDA_DIR/helm/values-${ENVIRONMENT}.yaml"

    if [ "$DRY_RUN" = "true" ]; then
        log_info "DRY RUN: Would deploy KEDA with Helm"
        helm install "$HELM_RELEASE" kedacore/keda \
            --namespace "$NAMESPACE_KEDA" \
            --values "$values_file" \
            --values "$env_values_file" \
            --timeout "$HELM_TIMEOUT" \
            --dry-run \
            --debug
    else
        helm upgrade --install "$HELM_RELEASE" "$KEDA_DIR/helm" \
            --namespace "$NAMESPACE_KEDA" \
            --values "$values_file" \
            --values "$env_values_file" \
            --timeout "$HELM_TIMEOUT" \
            --wait \
            --atomic
    fi

    # Wait for KEDA to be ready
    log_info "Waiting for KEDA operator to be ready..."
    kubectl wait --for=condition=Ready pod \
        -l app=keda-operator \
        -n "$NAMESPACE_KEDA" \
        --timeout=300s

    kubectl wait --for=condition=Ready pod \
        -l app=keda-operator-metrics-apiserver \
        -n "$NAMESPACE_KEDA" \
        --timeout=300s

    log_success "KEDA operator deployed successfully"
}

# Stage 2: Deploy security configurations
deploy_security_configs() {
    log_info "Stage 2: Deploying security configurations..."

    # Apply RBAC
    kubectl apply -f "$KEDA_DIR/base/rbac.yaml"

    # Apply NetworkPolicies
    kubectl apply -f "$KEDA_DIR/base/networkpolicy.yaml"

    # Apply External Secrets
    if kubectl get crd externalsecrets.external-secrets.io &> /dev/null; then
        kubectl apply -f "$KEDA_DIR/base/external-secrets.yaml"
    else
        log_warning "External Secrets CRD not found, using fallback secrets"
        # Apply fallback secrets for dev/test
        kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: redis-credentials
  namespace: $NAMESPACE_ARTEMIS
type: Opaque
stringData:
  password: "changeme"
---
apiVersion: v1
kind: Secret
metadata:
  name: prometheus-credentials
  namespace: $NAMESPACE_SOPHIA
type: Opaque
stringData:
  bearer-token: "changeme"
EOF
    fi

    log_success "Security configurations deployed"
}

# Stage 3: Deploy ScaledObjects (Canary)
deploy_scaledobjects_canary() {
    log_info "Stage 3: Deploying ScaledObjects (Canary rollout)..."

    # Deploy Sophia ScaledObject with reduced scope
    log_info "Deploying Sophia ScaledObject (canary)..."
    kubectl apply -f "$KEDA_DIR/scalers/sophia-scaledobject.yaml"

    # Wait and validate
    sleep 30
    validate_scaledobject "sophia-scaler" "$NAMESPACE_ARTEMIS"

    # If successful, continue with Sophia
    log_info "Deploying Sophia ScaledObject (canary)..."
    kubectl apply -f "$KEDA_DIR/scalers/sophia-scaledobject.yaml"

    sleep 30
    validate_scaledobject "sophia-scaler" "$NAMESPACE_SOPHIA"

    # Deploy Cron scaler last
    log_info "Deploying Cron ScaledObject..."
    kubectl apply -f "$KEDA_DIR/scalers/ai-workload-cron-scaler.yaml"

    log_success "All ScaledObjects deployed successfully"
}

# Stage 4: Deploy monitoring
deploy_monitoring() {
    log_info "Stage 4: Deploying monitoring components..."

    # Apply Prometheus rules
    kubectl apply -f "$KEDA_DIR/monitoring/prometheus-rules.yaml"

    # Apply custom metrics ConfigMap
    kubectl apply -f "$KEDA_DIR/monitoring/custom-metrics-configmap.yaml"

    log_success "Monitoring components deployed"
}

# Validate ScaledObject
validate_scaledobject() {
    local scaledobject_name=$1
    local namespace=$2

    log_info "Validating ScaledObject $scaledobject_name in $namespace..."

    # Check if ScaledObject is ready
    local ready=$(kubectl get scaledobject "$scaledobject_name" \
        -n "$namespace" \
        -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')

    if [ "$ready" != "True" ]; then
        log_error "ScaledObject $scaledobject_name is not ready"
        return 1
    fi

    # Check if HPA was created
    if ! kubectl get hpa "$scaledobject_name" -n "$namespace" &> /dev/null; then
        log_error "HPA for $scaledobject_name was not created"
        return 1
    fi

    log_success "ScaledObject $scaledobject_name validated"
    return 0
}

# Run integration tests
run_integration_tests() {
    if [ "$SKIP_TESTS" = "true" ]; then
        log_warning "Skipping integration tests (SKIP_TESTS=true)"
        return 0
    fi

    log_info "Running integration tests..."

    if "$KEDA_DIR/tests/integration-test.sh"; then
        log_success "Integration tests passed"
        return 0
    else
        log_error "Integration tests failed"
        return 1
    fi
}

# Run performance benchmark
run_performance_benchmark() {
    if [ "$SKIP_TESTS" = "true" ]; then
        log_warning "Skipping performance benchmark (SKIP_TESTS=true)"
        return 0
    fi

    log_info "Running performance benchmark..."

    # Run minimal benchmark
    if python3 "$KEDA_DIR/tests/performance-benchmark.py" \
        --iterations 3 \
        --profiles burst gradual \
        --target-time 9; then
        log_success "Performance benchmark passed"
        return 0
    else
        log_error "Performance benchmark failed"
        return 1
    fi
}

# Rollback on failure
rollback_on_failure() {
    log_warning "Initiating rollback..."

    # Delete ScaledObjects
    kubectl delete scaledobject --all -n "$NAMESPACE_ARTEMIS" --ignore-not-found
    kubectl delete scaledobject --all -n "$NAMESPACE_SOPHIA" --ignore-not-found

    # Restore HPA if it was disabled
    kubectl patch hpa sophia-worker-hpa-backup -n "$NAMESPACE_ARTEMIS" \
        -p '{"spec":{"minReplicas":2}}' --type merge || true
    kubectl patch hpa sophia-analytics-hpa-backup -n "$NAMESPACE_SOPHIA" \
        -p '{"spec":{"minReplicas":3}}' --type merge || true

    log_info "Rollback completed - system restored to HPA"
}

# Main deployment flow
main() {
    log_info "=== Starting KEDA Deployment ==="
    log_info "Environment: $ENVIRONMENT"
    log_info "Dry Run: $DRY_RUN"
    log_info "Skip Tests: $SKIP_TESTS"
    log_info "Rollout Strategy: $ROLLOUT_STRATEGY"

    # Pre-flight checks
    preflight_checks

    # Capture baseline metrics
    capture_baseline_metrics

    # Stage 1: Deploy KEDA operator
    deploy_keda_operator

    # Stage 2: Deploy security configurations
    deploy_security_configs

    # Stage 3: Deploy ScaledObjects
    if [ "$ROLLOUT_STRATEGY" = "canary" ]; then
        deploy_scaledobjects_canary
    else
        log_info "Deploying all ScaledObjects at once..."
        kubectl apply -f "$KEDA_DIR/scalers/"
    fi

    # Stage 4: Deploy monitoring
    deploy_monitoring

    # Validation
    log_info "Waiting for system to stabilize..."
    sleep 60

    # Run tests
    run_integration_tests
    run_performance_benchmark

    # Final validation
    "$SCRIPT_DIR/validate-deployment.sh"

    log_success "=== KEDA Deployment Completed Successfully ==="
    log_info "Deployment log saved to: $LOG_FILE"

    # Display summary
    echo ""
    echo "Deployment Summary:"
    echo "=================="
    kubectl get scaledobjects -A
    echo ""
    kubectl get pods -n "$NAMESPACE_KEDA"
    echo ""
    echo "To monitor KEDA metrics:"
    echo "  kubectl port-forward -n $NAMESPACE_KEDA svc/keda-operator 8080:8080"
    echo "  curl http://localhost:8080/metrics"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --environment|-e)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN="true"
            shift
            ;;
        --skip-tests)
            SKIP_TESTS="true"
            shift
            ;;
        --rollout-strategy|-r)
            ROLLOUT_STRATEGY="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -e, --environment ENV    Environment (dev|staging|prod) [default: dev]"
            echo "  --dry-run               Perform dry run without actual deployment"
            echo "  --skip-tests            Skip integration and performance tests"
            echo "  -r, --rollout-strategy  Rollout strategy (canary|blue-green|direct) [default: canary]"
            echo "  -h, --help             Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main deployment
main
