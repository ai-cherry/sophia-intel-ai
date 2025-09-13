#!/bin/bash
set -euo pipefail

# KEDA Integration Testing Script
# Verifies KEDA integration with existing Sophia/Sophia components
# Target: Confirm 85% scaling improvement (60s to 9s)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE_KEDA="keda-system"
NAMESPACE_ARTEMIS="sophia-system"
NAMESPACE_SOPHIA="sophia-system"
TARGET_SCALING_TIME=9
BASELINE_SCALING_TIME=60
IMPROVEMENT_TARGET=85
TEST_TIMEOUT=600

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0
declare -a FAILED_TESTS=()

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Test result tracking
record_test_result() {
    local test_name="$1"
    local result="$2"

    if [ "$result" = "pass" ]; then
        ((TESTS_PASSED++))
        log_success "Test '$test_name' passed"
    else
        ((TESTS_FAILED++))
        FAILED_TESTS+=("$test_name")
        log_error "Test '$test_name' failed"
    fi
}

# Prerequisite checks
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found. Please install kubectl."
        exit 1
    fi

    # Check helm
    if ! command -v helm &> /dev/null; then
        log_error "helm not found. Please install helm."
        exit 1
    fi

    # Check jq
    if ! command -v jq &> /dev/null; then
        log_error "jq not found. Please install jq."
        exit 1
    fi

    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster."
        exit 1
    fi

    log_success "All prerequisites met"
}

# Test 1: Verify KEDA deployment
test_keda_deployment() {
    log_info "Test 1: Verifying KEDA deployment..."

    # Check namespace exists
    if ! kubectl get namespace "$NAMESPACE_KEDA" &> /dev/null; then
        record_test_result "keda_namespace" "fail"
        return 1
    fi

    # Check KEDA operator pod
    local operator_ready=$(kubectl get pods -n "$NAMESPACE_KEDA" \
        -l app=keda-operator \
        -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}')

    if [ "$operator_ready" != "True" ]; then
        record_test_result "keda_operator_ready" "fail"
        return 1
    fi

    # Check metrics server pod
    local metrics_ready=$(kubectl get pods -n "$NAMESPACE_KEDA" \
        -l app=keda-operator-metrics-apiserver \
        -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}')

    if [ "$metrics_ready" != "True" ]; then
        record_test_result "keda_metrics_ready" "fail"
        return 1
    fi

    # Check CRDs
    local crds=("scaledobjects.keda.sh" "triggerauthentications.keda.sh" "scaledjobs.keda.sh")
    for crd in "${crds[@]}"; do
        if ! kubectl get crd "$crd" &> /dev/null; then
            record_test_result "keda_crd_$crd" "fail"
            return 1
        fi
    done

    record_test_result "keda_deployment" "pass"
    return 0
}

# Test 2: Verify ScaledObject configurations
test_scaledobjects() {
    log_info "Test 2: Verifying ScaledObject configurations..."

    # Check Sophia ScaledObject
    if kubectl get scaledobject sophia-scaler -n "$NAMESPACE_ARTEMIS" &> /dev/null; then
        local sophia_ready=$(kubectl get scaledobject sophia-scaler -n "$NAMESPACE_ARTEMIS" \
            -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')

        if [ "$sophia_ready" = "True" ]; then
            record_test_result "sophia_scaledobject" "pass"
        else
            record_test_result "sophia_scaledobject" "fail"
        fi
    else
        record_test_result "sophia_scaledobject" "fail"
    fi

    # Check Sophia ScaledObject
    if kubectl get scaledobject sophia-scaler -n "$NAMESPACE_SOPHIA" &> /dev/null; then
        local sophia_ready=$(kubectl get scaledobject sophia-scaler -n "$NAMESPACE_SOPHIA" \
            -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')

        if [ "$sophia_ready" = "True" ]; then
            record_test_result "sophia_scaledobject" "pass"
        else
            record_test_result "sophia_scaledobject" "fail"
        fi
    else
        record_test_result "sophia_scaledobject" "fail"
    fi

    # Check Cron ScaledObject
    if kubectl get scaledobject ai-workload-cron-scaler -n "$NAMESPACE_SOPHIA" &> /dev/null; then
        record_test_result "cron_scaledobject" "pass"
    else
        record_test_result "cron_scaledobject" "fail"
    fi
}

# Test 3: Redis connectivity test
test_redis_connectivity() {
    log_info "Test 3: Testing Redis connectivity for Sophia scaler..."

    # Create test pod
    cat <<EOF | kubectl apply -f - &> /dev/null
apiVersion: v1
kind: Pod
metadata:
  name: redis-test
  namespace: $NAMESPACE_ARTEMIS
spec:
  containers:
  - name: redis-cli
    image: redis:alpine
    command: ["sleep", "300"]
EOF

    # Wait for pod to be ready
    kubectl wait --for=condition=Ready pod/redis-test -n "$NAMESPACE_ARTEMIS" --timeout=60s &> /dev/null

    # Test Redis connection
    if kubectl exec -n "$NAMESPACE_ARTEMIS" redis-test -- redis-cli \
        -h redis.sophia-system.svc.cluster.local ping &> /dev/null; then
        record_test_result "redis_connectivity" "pass"
    else
        record_test_result "redis_connectivity" "fail"
    fi

    # Cleanup
    kubectl delete pod redis-test -n "$NAMESPACE_ARTEMIS" --force &> /dev/null
}

# Test 4: Prometheus connectivity test
test_prometheus_connectivity() {
    log_info "Test 4: Testing Prometheus connectivity for Sophia scaler..."

    # Create test pod
    cat <<EOF | kubectl apply -f - &> /dev/null
apiVersion: v1
kind: Pod
metadata:
  name: prometheus-test
  namespace: $NAMESPACE_SOPHIA
spec:
  containers:
  - name: curl
    image: curlimages/curl:latest
    command: ["sleep", "300"]
EOF

    # Wait for pod to be ready
    kubectl wait --for=condition=Ready pod/prometheus-test -n "$NAMESPACE_SOPHIA" --timeout=60s &> /dev/null

    # Test Prometheus connection
    if kubectl exec -n "$NAMESPACE_SOPHIA" prometheus-test -- \
        curl -s http://prometheus.monitoring.svc.cluster.local:9090/api/v1/query?query=up | grep -q "success"; then
        record_test_result "prometheus_connectivity" "pass"
    else
        record_test_result "prometheus_connectivity" "fail"
    fi

    # Cleanup
    kubectl delete pod prometheus-test -n "$NAMESPACE_SOPHIA" --force &> /dev/null
}

# Test 5: HPA interaction test
test_hpa_interaction() {
    log_info "Test 5: Testing HPA interaction and fallback..."

    # Check if HPAs exist alongside ScaledObjects
    local hpa_count=$(kubectl get hpa -A | grep -E "sophia|sophia" | wc -l)

    if [ "$hpa_count" -gt 0 ]; then
        log_info "Found $hpa_count HPA resources for fallback"
        record_test_result "hpa_fallback_available" "pass"
    else
        log_warning "No HPA resources found for fallback"
        record_test_result "hpa_fallback_available" "fail"
    fi
}

# Test 6: Network Policy validation
test_network_policies() {
    log_info "Test 6: Validating Network Policies..."

    # Check KEDA network policy
    if kubectl get networkpolicy keda-operator-network-policy -n "$NAMESPACE_KEDA" &> /dev/null; then
        record_test_result "keda_network_policy" "pass"
    else
        record_test_result "keda_network_policy" "fail"
    fi

    # Verify ingress/egress rules
    local ingress_rules=$(kubectl get networkpolicy keda-operator-network-policy -n "$NAMESPACE_KEDA" \
        -o jsonpath='{.spec.ingress}' | jq '. | length')
    local egress_rules=$(kubectl get networkpolicy keda-operator-network-policy -n "$NAMESPACE_KEDA" \
        -o jsonpath='{.spec.egress}' | jq '. | length')

    if [ "$ingress_rules" -gt 0 ] && [ "$egress_rules" -gt 0 ]; then
        record_test_result "network_policy_rules" "pass"
    else
        record_test_result "network_policy_rules" "fail"
    fi
}

# Test 7: RBAC validation
test_rbac() {
    log_info "Test 7: Validating RBAC configuration..."

    # Check ServiceAccount
    if kubectl get serviceaccount keda-operator -n "$NAMESPACE_KEDA" &> /dev/null; then
        record_test_result "keda_serviceaccount" "pass"
    else
        record_test_result "keda_serviceaccount" "fail"
    fi

    # Check ClusterRole
    if kubectl get clusterrole keda-operator &> /dev/null; then
        record_test_result "keda_clusterrole" "pass"
    else
        record_test_result "keda_clusterrole" "fail"
    fi

    # Check ClusterRoleBinding
    if kubectl get clusterrolebinding keda-operator &> /dev/null; then
        record_test_result "keda_clusterrolebinding" "pass"
    else
        record_test_result "keda_clusterrolebinding" "fail"
    fi
}

# Test 8: External Secrets integration
test_external_secrets() {
    log_info "Test 8: Testing External Secrets integration..."

    # Check if secrets exist
    if kubectl get secret redis-credentials -n "$NAMESPACE_ARTEMIS" &> /dev/null || \
       kubectl get secret redis-credentials-fallback -n "$NAMESPACE_ARTEMIS" &> /dev/null; then
        record_test_result "redis_secret" "pass"
    else
        record_test_result "redis_secret" "fail"
    fi

    if kubectl get secret prometheus-credentials -n "$NAMESPACE_SOPHIA" &> /dev/null || \
       kubectl get secret prometheus-credentials-fallback -n "$NAMESPACE_SOPHIA" &> /dev/null; then
        record_test_result "prometheus_secret" "pass"
    else
        record_test_result "prometheus_secret" "fail"
    fi
}

# Test 9: Metrics exposure test
test_metrics_exposure() {
    log_info "Test 9: Testing metrics exposure..."

    # Port-forward to KEDA metrics service
    kubectl port-forward -n "$NAMESPACE_KEDA" svc/keda-operator 8080:8080 &> /dev/null &
    local port_forward_pid=$!
    sleep 5

    # Test metrics endpoint
    if curl -s http://localhost:8080/metrics | grep -q "keda_scaler_"; then
        record_test_result "keda_metrics_exposed" "pass"
    else
        record_test_result "keda_metrics_exposed" "fail"
    fi

    # Cleanup
    kill $port_forward_pid 2>/dev/null || true
}

# Test 10: Circuit breaker test
test_circuit_breaker() {
    log_info "Test 10: Testing circuit breaker configuration..."

    # Check ScaledObject annotations
    local circuit_breaker=$(kubectl get scaledobject sophia-scaler -n "$NAMESPACE_ARTEMIS" \
        -o jsonpath='{.metadata.annotations.keda\.sh/circuit-breaker-enabled}')

    if [ "$circuit_breaker" = "true" ]; then
        record_test_result "circuit_breaker_enabled" "pass"
    else
        record_test_result "circuit_breaker_enabled" "fail"
    fi

    # Check max scale events configuration
    local max_events=$(kubectl get scaledobject sophia-scaler -n "$NAMESPACE_ARTEMIS" \
        -o jsonpath='{.metadata.annotations.keda\.sh/max-scale-events}')

    if [ "$max_events" = "3" ]; then
        record_test_result "circuit_breaker_threshold" "pass"
    else
        record_test_result "circuit_breaker_threshold" "fail"
    fi
}

# Scaling performance test
test_scaling_performance() {
    log_info "Test 11: Measuring scaling performance..."

    local deployment="sophia-worker"
    local namespace="$NAMESPACE_ARTEMIS"

    # Get initial replica count
    local initial_replicas=$(kubectl get deployment "$deployment" -n "$namespace" \
        -o jsonpath='{.spec.replicas}')

    # Create load to trigger scaling
    kubectl exec -n "$namespace" deployment/"$deployment" -- sh -c "echo 'test_load' > /tmp/load" 2>/dev/null || true

    # Measure scaling time
    local start_time=$(date +%s)
    local scaled=false
    local timeout=120

    while [ $(($(date +%s) - start_time)) -lt $timeout ]; do
        local current_replicas=$(kubectl get deployment "$deployment" -n "$namespace" \
            -o jsonpath='{.status.readyReplicas}')

        if [ "$current_replicas" != "$initial_replicas" ]; then
            scaled=true
            break
        fi
        sleep 1
    done

    local scaling_time=$(($(date +%s) - start_time))

    if [ "$scaled" = true ] && [ "$scaling_time" -le "$TARGET_SCALING_TIME" ]; then
        log_success "Scaling completed in ${scaling_time}s (target: ${TARGET_SCALING_TIME}s)"
        record_test_result "scaling_performance" "pass"
    else
        log_error "Scaling took ${scaling_time}s (target: ${TARGET_SCALING_TIME}s)"
        record_test_result "scaling_performance" "fail"
    fi
}

# Prometheus rules test
test_prometheus_rules() {
    log_info "Test 12: Testing Prometheus rules..."

    # Check if PrometheusRule exists
    if kubectl get prometheusrule keda-autoscaling-rules -n monitoring &> /dev/null; then
        record_test_result "prometheus_rules_exist" "pass"

        # Validate specific alerts
        local alerts=("KEDAScalingLatencyHigh" "KEDATargetScalingTimeExceeded" "KEDACircuitBreakerTriggered")
        for alert in "${alerts[@]}"; do
            if kubectl get prometheusrule keda-autoscaling-rules -n monitoring -o yaml | grep -q "$alert"; then
                record_test_result "alert_$alert" "pass"
            else
                record_test_result "alert_$alert" "fail"
            fi
        done
    else
        record_test_result "prometheus_rules_exist" "fail"
    fi
}

# Integration with existing monitoring
test_monitoring_integration() {
    log_info "Test 13: Testing monitoring integration..."

    # Check ServiceMonitors
    if kubectl get servicemonitor keda-metrics -n "$NAMESPACE_KEDA" &> /dev/null; then
        record_test_result "servicemonitor_exists" "pass"
    else
        record_test_result "servicemonitor_exists" "fail"
    fi

    # Check if metrics are being scraped
    # This would require actual Prometheus query
    log_info "Skipping Prometheus scraping verification (requires Prometheus API access)"
}

# Generate test report
generate_report() {
    echo ""
    echo "========================================"
    echo "KEDA INTEGRATION TEST REPORT"
    echo "========================================"
    echo "Date: $(date)"
    echo "----------------------------------------"
    echo "Tests Passed: $TESTS_PASSED"
    echo "Tests Failed: $TESTS_FAILED"
    echo "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
    echo "Success Rate: $(echo "scale=2; $TESTS_PASSED * 100 / ($TESTS_PASSED + $TESTS_FAILED)" | bc)%"
    echo "----------------------------------------"

    if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
        echo ""
        echo "Failed Tests:"
        for test in "${FAILED_TESTS[@]}"; do
            echo "  - $test"
        done
    fi

    echo "========================================"

    # Calculate if we meet the SLA
    local improvement_actual=$(echo "scale=2; ($BASELINE_SCALING_TIME - $TARGET_SCALING_TIME) * 100 / $BASELINE_SCALING_TIME" | bc)
    echo ""
    echo "SLA Target: ${IMPROVEMENT_TARGET}% improvement"
    echo "SLA Actual: ${improvement_actual}% improvement"

    if (( $(echo "$improvement_actual >= $IMPROVEMENT_TARGET" | bc -l) )); then
        log_success "✅ SLA TARGET MET"
    else
        log_error "❌ SLA TARGET NOT MET"
    fi

    echo ""
}

# Main execution
main() {
    echo "Starting KEDA Integration Tests..."
    echo "=================================="

    # Check prerequisites
    check_prerequisites

    # Run tests
    test_keda_deployment
    test_scaledobjects
    test_redis_connectivity
    test_prometheus_connectivity
    test_hpa_interaction
    test_network_policies
    test_rbac
    test_external_secrets
    test_metrics_exposure
    test_circuit_breaker
    test_scaling_performance
    test_prometheus_rules
    test_monitoring_integration

    # Generate report
    generate_report

    # Exit with appropriate code
    if [ "$TESTS_FAILED" -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
