#!/bin/bash

# AlertManager Deployment Script
# Performs phased rollout with validation at each stage

set -e

# Configuration
NAMESPACE="${NAMESPACE:-monitoring}"
RELEASE_NAME="${RELEASE_NAME:-alertmanager}"
CHART_PATH="./infrastructure/alertmanager/helm"
VALUES_FILE="${VALUES_FILE:-values.yaml}"
ENVIRONMENT="${ENVIRONMENT:-production}"
ROLLOUT_STRATEGY="${ROLLOUT_STRATEGY:-canary}"
DRY_RUN="${DRY_RUN:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
    exit 1
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check required tools
    for tool in kubectl helm jq curl; do
        if ! command -v $tool &> /dev/null; then
            error "$tool is not installed"
        fi
    done

    # Check Kubernetes connectivity
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster"
    fi

    # Check namespace
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        info "Creating namespace $NAMESPACE..."
        kubectl create namespace "$NAMESPACE"
    fi

    log "Prerequisites check passed ✓"
}

# Backup current configuration
backup_configuration() {
    log "Backing up current configuration..."

    BACKUP_DIR="./backups/alertmanager-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    # Backup Helm release
    if helm get values "$RELEASE_NAME" -n "$NAMESPACE" &> /dev/null; then
        helm get values "$RELEASE_NAME" -n "$NAMESPACE" > "$BACKUP_DIR/values.yaml"
        helm get manifest "$RELEASE_NAME" -n "$NAMESPACE" > "$BACKUP_DIR/manifest.yaml"
        log "Backup saved to $BACKUP_DIR"
    else
        info "No existing release found, skipping backup"
    fi
}

# Validate configuration
validate_configuration() {
    log "Validating configuration..."

    # Validate Helm chart
    if [[ ! -f "$CHART_PATH/Chart.yaml" ]]; then
        error "Chart.yaml not found at $CHART_PATH"
    fi

    # Validate values file
    VALUES_PATH="$CHART_PATH/$VALUES_FILE"
    if [[ "$ENVIRONMENT" != "production" ]]; then
        VALUES_PATH="$CHART_PATH/values-${ENVIRONMENT}.yaml"
    fi

    if [[ ! -f "$VALUES_PATH" ]]; then
        error "Values file not found at $VALUES_PATH"
    fi

    # Lint the chart
    helm lint "$CHART_PATH" -f "$VALUES_PATH" || error "Helm chart validation failed"

    # Dry run
    info "Performing dry-run..."
    helm upgrade --install "$RELEASE_NAME" "$CHART_PATH" \
        -f "$VALUES_PATH" \
        -n "$NAMESPACE" \
        --dry-run \
        --debug > /tmp/alertmanager-dry-run.yaml

    log "Configuration validation passed ✓"
}

# Deploy AlertManager
deploy_alertmanager() {
    log "Deploying AlertManager..."

    VALUES_PATH="$CHART_PATH/$VALUES_FILE"
    if [[ "$ENVIRONMENT" != "production" ]]; then
        VALUES_PATH="$CHART_PATH/values-${ENVIRONMENT}.yaml"
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        warning "DRY RUN MODE - No actual deployment will occur"
        helm upgrade --install "$RELEASE_NAME" "$CHART_PATH" \
            -f "$VALUES_PATH" \
            -n "$NAMESPACE" \
            --dry-run \
            --debug
        return 0
    fi

    case "$ROLLOUT_STRATEGY" in
        canary)
            deploy_canary
            ;;
        blue-green)
            deploy_blue_green
            ;;
        rolling)
            deploy_rolling
            ;;
        *)
            error "Unknown rollout strategy: $ROLLOUT_STRATEGY"
            ;;
    esac
}

# Canary deployment
deploy_canary() {
    log "Starting canary deployment..."

    VALUES_PATH="$CHART_PATH/$VALUES_FILE"
    if [[ "$ENVIRONMENT" != "production" ]]; then
        VALUES_PATH="$CHART_PATH/values-${ENVIRONMENT}.yaml"
    fi

    # Phase 1: Deploy single replica
    info "Phase 1: Deploying canary instance..."
    helm upgrade --install "$RELEASE_NAME-canary" "$CHART_PATH" \
        -f "$VALUES_PATH" \
        --set replicaCount=1 \
        --set nameOverride="${RELEASE_NAME}-canary" \
        -n "$NAMESPACE" \
        --wait \
        --timeout 5m

    # Validate canary
    sleep 30
    if ! validate_deployment "${RELEASE_NAME}-canary"; then
        error "Canary validation failed"
    fi

    # Phase 2: Scale to 50%
    info "Phase 2: Scaling canary to 50%..."
    helm upgrade "$RELEASE_NAME-canary" "$CHART_PATH" \
        -f "$VALUES_PATH" \
        --set replicaCount=2 \
        --set nameOverride="${RELEASE_NAME}-canary" \
        -n "$NAMESPACE" \
        --wait \
        --timeout 5m

    sleep 60
    if ! validate_deployment "${RELEASE_NAME}-canary"; then
        error "50% canary validation failed"
    fi

    # Phase 3: Full deployment
    info "Phase 3: Full deployment..."
    helm upgrade --install "$RELEASE_NAME" "$CHART_PATH" \
        -f "$VALUES_PATH" \
        -n "$NAMESPACE" \
        --wait \
        --timeout 10m

    # Cleanup canary
    info "Cleaning up canary deployment..."
    helm delete "$RELEASE_NAME-canary" -n "$NAMESPACE" || true

    log "Canary deployment completed successfully ✓"
}

# Blue-Green deployment
deploy_blue_green() {
    log "Starting blue-green deployment..."

    VALUES_PATH="$CHART_PATH/$VALUES_FILE"
    if [[ "$ENVIRONMENT" != "production" ]]; then
        VALUES_PATH="$CHART_PATH/values-${ENVIRONMENT}.yaml"
    fi

    # Deploy green (new) version
    info "Deploying green environment..."
    helm upgrade --install "$RELEASE_NAME-green" "$CHART_PATH" \
        -f "$VALUES_PATH" \
        --set nameOverride="${RELEASE_NAME}-green" \
        -n "$NAMESPACE" \
        --wait \
        --timeout 10m

    # Validate green deployment
    if ! validate_deployment "${RELEASE_NAME}-green"; then
        error "Green deployment validation failed"
    fi

    # Switch traffic to green
    info "Switching traffic to green environment..."
    kubectl patch service alertmanager -n "$NAMESPACE" \
        -p '{"spec":{"selector":{"app":"alertmanager-green"}}}'

    sleep 30

    # Delete blue (old) version
    if helm list -n "$NAMESPACE" | grep -q "$RELEASE_NAME-blue"; then
        info "Removing blue environment..."
        helm delete "$RELEASE_NAME-blue" -n "$NAMESPACE"
    fi

    # Rename green to blue for next deployment
    info "Promoting green to blue..."
    helm upgrade "$RELEASE_NAME-blue" "$CHART_PATH" \
        -f "$VALUES_PATH" \
        --set nameOverride="${RELEASE_NAME}-blue" \
        -n "$NAMESPACE" \
        --reuse-values

    helm delete "$RELEASE_NAME-green" -n "$NAMESPACE"

    log "Blue-green deployment completed successfully ✓"
}

# Rolling deployment
deploy_rolling() {
    log "Starting rolling deployment..."

    VALUES_PATH="$CHART_PATH/$VALUES_FILE"
    if [[ "$ENVIRONMENT" != "production" ]]; then
        VALUES_PATH="$CHART_PATH/values-${ENVIRONMENT}.yaml"
    fi

    helm upgrade --install "$RELEASE_NAME" "$CHART_PATH" \
        -f "$VALUES_PATH" \
        -n "$NAMESPACE" \
        --wait \
        --timeout 15m \
        --atomic \
        --cleanup-on-fail

    log "Rolling deployment completed successfully ✓"
}

# Validate deployment
validate_deployment() {
    local release="${1:-$RELEASE_NAME}"
    log "Validating deployment $release..."

    # Check pods are running
    local ready_pods=$(kubectl get pods -n "$NAMESPACE" -l "app=alertmanager" \
        -o jsonpath='{.items[?(@.status.phase=="Running")].metadata.name}' | wc -w)

    if [[ $ready_pods -lt 1 ]]; then
        error "No AlertManager pods are running"
        return 1
    fi

    # Check service endpoint
    local service_ip=$(kubectl get service alertmanager -n "$NAMESPACE" \
        -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")

    if [[ -z "$service_ip" ]]; then
        service_ip=$(kubectl get service alertmanager -n "$NAMESPACE" \
            -o jsonpath='{.spec.clusterIP}')
    fi

    # Test AlertManager API
    info "Testing AlertManager API..."
    if kubectl run test-alertmanager-$$ --rm -i --image=curlimages/curl:latest \
        --restart=Never -n "$NAMESPACE" -- \
        curl -s -o /dev/null -w "%{http_code}" "http://alertmanager:9093/-/healthy" | grep -q "200"; then
        log "AlertManager API is healthy ✓"
    else
        error "AlertManager API health check failed"
        return 1
    fi

    # Check cluster status
    info "Checking cluster status..."
    local cluster_members=$(kubectl exec -n "$NAMESPACE" \
        $(kubectl get pod -n "$NAMESPACE" -l app=alertmanager -o jsonpath='{.items[0].metadata.name}') -- \
        wget -qO- http://localhost:9093/api/v1/status | \
        jq -r '.data.cluster.peers | length')

    if [[ $cluster_members -ge 2 ]]; then
        log "AlertManager cluster has $cluster_members members ✓"
    else
        warning "AlertManager cluster has only $cluster_members members"
    fi

    return 0
}

# Post-deployment tasks
post_deployment() {
    log "Running post-deployment tasks..."

    # Apply PrometheusRules
    info "Applying PrometheusRules..."
    kubectl apply -f "$CHART_PATH/../monitoring/prometheus-rules.yaml" || true

    # Configure notification channels
    info "Configuring notification channels..."
    ./infrastructure/alertmanager/scripts/configure-channels.sh || true

    # Run validation tests
    info "Running validation tests..."
    ./infrastructure/alertmanager/scripts/validate-deployment.sh || true

    log "Post-deployment tasks completed ✓"
}

# Rollback deployment
rollback_deployment() {
    error "Deployment failed, initiating rollback..."

    helm rollback "$RELEASE_NAME" -n "$NAMESPACE" || {
        error "Automatic rollback failed. Manual intervention required."
    }

    log "Rollback completed"
}

# Main execution
main() {
    log "=========================================="
    log "AlertManager Deployment Script"
    log "=========================================="
    log "Environment: $ENVIRONMENT"
    log "Namespace: $NAMESPACE"
    log "Release: $RELEASE_NAME"
    log "Strategy: $ROLLOUT_STRATEGY"
    log ""

    # Set trap for cleanup on error
    trap rollback_deployment ERR

    # Execute deployment phases
    check_prerequisites
    backup_configuration
    validate_configuration
    deploy_alertmanager

    if [[ "$DRY_RUN" != "true" ]]; then
        validate_deployment
        post_deployment
    fi

    # Clear trap
    trap - ERR

    log ""
    log "=========================================="
    log "✅ AlertManager deployment completed successfully!"
    log "=========================================="
    log ""
    log "Access AlertManager at:"
    log "  Internal: http://alertmanager.$NAMESPACE:9093"
    log "  External: https://alertmanager.sophia-artemis.ai"
    log ""
    log "To view status:"
    log "  kubectl get pods -n $NAMESPACE -l app=alertmanager"
    log "  helm status $RELEASE_NAME -n $NAMESPACE"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --strategy)
            ROLLOUT_STRATEGY="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN="true"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --namespace <namespace>    Kubernetes namespace (default: monitoring)"
            echo "  --environment <env>        Environment (dev|staging|production)"
            echo "  --strategy <strategy>      Rollout strategy (canary|blue-green|rolling)"
            echo "  --dry-run                  Perform dry run only"
            echo "  --help                     Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Run main function
main
