#!/bin/bash

# Sophia-Sophia Service Mesh Validation Script
# Validates Istio installation, mTLS, service connectivity, and policies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE_ISTIO="istio-system"
NAMESPACE_ARTEMIS="sophia-mesh"
NAMESPACE_SOPHIA="sophia-mesh"
NAMESPACE_SHARED="shared-services"
MAX_CONCURRENT_TASKS=8

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNINGS=0

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    ((TESTS_WARNINGS++))
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    ((TESTS_FAILED++))
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((TESTS_PASSED++))
}

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

check_istio_installation() {
    log_test "Checking Istio installation..."

    # Check if istioctl is available
    if ! command -v istioctl &> /dev/null; then
        log_error "istioctl is not installed"
        return 1
    fi

    # Check Istio version
    ISTIO_VERSION=$(istioctl version --short --remote 2>/dev/null || echo "unknown")
    log_info "Istio version: ${ISTIO_VERSION}"

    # Check Istio components
    if kubectl get deployment istiod -n ${NAMESPACE_ISTIO} &> /dev/null; then
        log_success "Istio control plane (istiod) is installed"
    else
        log_error "Istio control plane (istiod) is not found"
    fi

    if kubectl get deployment istio-ingressgateway -n ${NAMESPACE_ISTIO} &> /dev/null; then
        log_success "Istio ingress gateway is installed"
    else
        log_error "Istio ingress gateway is not found"
    fi

    if kubectl get deployment istio-egressgateway -n ${NAMESPACE_ISTIO} &> /dev/null; then
        log_success "Istio egress gateway is installed"
    else
        log_warning "Istio egress gateway is not found (optional)"
    fi

    # Run Istio analyze
    log_info "Running Istio configuration analysis..."
    if istioctl analyze --all-namespaces 2>&1 | grep -q "No validation issues"; then
        log_success "No Istio configuration issues found"
    else
        log_warning "Istio configuration issues detected:"
        istioctl analyze --all-namespaces
    fi
}

verify_mtls() {
    log_test "Verifying mTLS configuration..."

    # Check PeerAuthentication policies
    for namespace in ${NAMESPACE_ARTEMIS} ${NAMESPACE_SOPHIA} ${NAMESPACE_SHARED}; do
        PA_COUNT=$(kubectl get peerauthentication -n ${namespace} 2>/dev/null | grep -c "STRICT" || echo 0)
        if [ ${PA_COUNT} -gt 0 ]; then
            log_success "mTLS STRICT mode enabled in ${namespace}"
        else
            log_error "mTLS STRICT mode not configured in ${namespace}"
        fi
    done

    # Check actual mTLS status using istioctl
    log_info "Checking actual mTLS status between services..."

    # Get a pod from Sophia namespace
    ARTEMIS_POD=$(kubectl get pod -n ${NAMESPACE_ARTEMIS} -l app=sophia-orchestrator -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

    if [ ! -z "${ARTEMIS_POD}" ]; then
        MTLS_STATUS=$(istioctl authn tls-check ${ARTEMIS_POD}.${NAMESPACE_ARTEMIS} 2>/dev/null | grep -c "OK" || echo 0)
        if [ ${MTLS_STATUS} -gt 0 ]; then
            log_success "mTLS is active for Sophia services"
        else
            log_warning "mTLS status unclear for Sophia services"
        fi
    else
        log_warning "No Sophia pods found to check mTLS"
    fi
}

test_service_connectivity() {
    log_test "Testing service connectivity..."

    # Test Sophia orchestrator
    log_info "Testing Sophia orchestrator connectivity..."
    ARTEMIS_POD=$(kubectl get pod -n ${NAMESPACE_ARTEMIS} -l app=sophia-orchestrator -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

    if [ ! -z "${ARTEMIS_POD}" ]; then
        # Test health endpoint
        if kubectl exec -n ${NAMESPACE_ARTEMIS} ${ARTEMIS_POD} -c sophia-orchestrator -- \
            curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health/live 2>/dev/null | grep -q "200"; then
            log_success "Sophia orchestrator health check passed"
        else
            log_error "Sophia orchestrator health check failed"
        fi

        # Test cross-namespace connectivity to shared services
        if kubectl exec -n ${NAMESPACE_ARTEMIS} ${ARTEMIS_POD} -c sophia-orchestrator -- \
            curl -s -o /dev/null -w "%{http_code}" http://memory-service.shared-services:8080/health 2>/dev/null | grep -q "200\|404"; then
            log_success "Sophia can connect to shared services"
        else
            log_error "Sophia cannot connect to shared services"
        fi
    else
        log_warning "No Sophia pods available for connectivity test"
    fi

    # Test Sophia orchestrator
    log_info "Testing Sophia orchestrator connectivity..."
    SOPHIA_POD=$(kubectl get pod -n ${NAMESPACE_SOPHIA} -l app=sophia-orchestrator -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

    if [ ! -z "${SOPHIA_POD}" ]; then
        # Test health endpoint
        if kubectl exec -n ${NAMESPACE_SOPHIA} ${SOPHIA_POD} -c sophia-orchestrator -- \
            curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health/live 2>/dev/null | grep -q "200"; then
            log_success "Sophia orchestrator health check passed"
        else
            log_error "Sophia orchestrator health check failed"
        fi

        # Test cross-namespace connectivity to shared services
        if kubectl exec -n ${NAMESPACE_SOPHIA} ${SOPHIA_POD} -c sophia-orchestrator -- \
            curl -s -o /dev/null -w "%{http_code}" http://config-service.shared-services:8080/health 2>/dev/null | grep -q "200\|404"; then
            log_success "Sophia can connect to shared services"
        else
            log_error "Sophia cannot connect to shared services"
        fi
    else
        log_warning "No Sophia pods available for connectivity test"
    fi
}

validate_policies() {
    log_test "Validating policies..."

    # Check authorization policies
    log_info "Checking authorization policies..."
    AUTH_POLICIES=$(kubectl get authorizationpolicy --all-namespaces 2>/dev/null | wc -l)
    if [ ${AUTH_POLICIES} -gt 1 ]; then
        log_success "Authorization policies are configured (${AUTH_POLICIES} policies found)"
    else
        log_error "No authorization policies found"
    fi

    # Check VirtualServices
    log_info "Checking VirtualServices..."
    VS_ARTEMIS=$(kubectl get virtualservice -n ${NAMESPACE_ARTEMIS} 2>/dev/null | wc -l)
    VS_SOPHIA=$(kubectl get virtualservice -n ${NAMESPACE_SOPHIA} 2>/dev/null | wc -l)

    if [ ${VS_ARTEMIS} -gt 1 ]; then
        log_success "VirtualServices configured for Sophia (${VS_ARTEMIS} found)"
    else
        log_error "No VirtualServices found for Sophia"
    fi

    if [ ${VS_SOPHIA} -gt 1 ]; then
        log_success "VirtualServices configured for Sophia (${VS_SOPHIA} found)"
    else
        log_error "No VirtualServices found for Sophia"
    fi

    # Check DestinationRules
    log_info "Checking DestinationRules..."
    DR_ARTEMIS=$(kubectl get destinationrule -n ${NAMESPACE_ARTEMIS} 2>/dev/null | wc -l)
    DR_SOPHIA=$(kubectl get destinationrule -n ${NAMESPACE_SOPHIA} 2>/dev/null | wc -l)

    if [ ${DR_ARTEMIS} -gt 1 ]; then
        log_success "DestinationRules configured for Sophia (${DR_ARTEMIS} found)"
    else
        log_error "No DestinationRules found for Sophia"
    fi

    if [ ${DR_SOPHIA} -gt 1 ]; then
        log_success "DestinationRules configured for Sophia (${DR_SOPHIA} found)"
    else
        log_error "No DestinationRules found for Sophia"
    fi
}

test_concurrent_tasks() {
    log_test "Testing concurrent task limits..."

    # Check if concurrent task limit is configured
    log_info "Checking concurrent task configuration..."

    # Check Sophia configuration
    ARTEMIS_CONFIG=$(kubectl get configmap sophia-config -n ${NAMESPACE_ARTEMIS} -o jsonpath='{.data.application\.yaml}' 2>/dev/null || echo "")
    if echo "${ARTEMIS_CONFIG}" | grep -q "maxConcurrentTasks: ${MAX_CONCURRENT_TASKS}"; then
        log_success "Sophia concurrent task limit is configured (${MAX_CONCURRENT_TASKS})"
    else
        log_warning "Sophia concurrent task limit configuration not found"
    fi

    # Check Sophia configuration
    SOPHIA_CONFIG=$(kubectl get configmap sophia-config -n ${NAMESPACE_SOPHIA} -o jsonpath='{.data.application\.yaml}' 2>/dev/null || echo "")
    if echo "${SOPHIA_CONFIG}" | grep -q "maxConcurrentTasks: ${MAX_CONCURRENT_TASKS}"; then
        log_success "Sophia concurrent task limit is configured (${MAX_CONCURRENT_TASKS})"
    else
        log_warning "Sophia concurrent task limit configuration not found"
    fi
}

test_rate_limiting() {
    log_test "Testing rate limiting configuration..."

    # Check if rate limit service is deployed
    if kubectl get deployment ratelimit -n ${NAMESPACE_ISTIO} &> /dev/null; then
        log_success "Rate limit service is deployed"

        # Check if rate limit is configured
        RL_CONFIG=$(kubectl get configmap ratelimit-config -n ${NAMESPACE_ISTIO} 2>/dev/null | wc -l)
        if [ ${RL_CONFIG} -gt 0 ]; then
            log_success "Rate limit configuration found"
        else
            log_warning "Rate limit configuration not found"
        fi
    else
        log_warning "Rate limit service is not deployed"
    fi

    # Check EnvoyFilters for rate limiting
    EF_COUNT=$(kubectl get envoyfilter --all-namespaces 2>/dev/null | grep -c "ratelimit" || echo 0)
    if [ ${EF_COUNT} -gt 0 ]; then
        log_success "Rate limiting EnvoyFilters configured (${EF_COUNT} found)"
    else
        log_warning "No rate limiting EnvoyFilters found"
    fi
}

test_observability() {
    log_test "Testing observability configuration..."

    # Check Prometheus
    if kubectl get deployment prometheus -n ${NAMESPACE_ISTIO} &> /dev/null || \
       kubectl get statefulset prometheus -n ${NAMESPACE_ISTIO} &> /dev/null; then
        log_success "Prometheus is deployed"
    else
        log_warning "Prometheus is not deployed"
    fi

    # Check Grafana
    if kubectl get deployment grafana -n ${NAMESPACE_ISTIO} &> /dev/null; then
        log_success "Grafana is deployed"
    else
        log_warning "Grafana is not deployed"
    fi

    # Check Kiali
    if kubectl get deployment kiali -n ${NAMESPACE_ISTIO} &> /dev/null; then
        log_success "Kiali is deployed"
    else
        log_warning "Kiali is not deployed"
    fi

    # Check Zipkin
    if kubectl get deployment zipkin -n ${NAMESPACE_ISTIO} &> /dev/null; then
        log_success "Zipkin is deployed"
    else
        log_warning "Zipkin is not deployed"
    fi

    # Check telemetry configuration
    TELEMETRY_COUNT=$(kubectl get telemetry --all-namespaces 2>/dev/null | wc -l)
    if [ ${TELEMETRY_COUNT} -gt 1 ]; then
        log_success "Telemetry configuration found (${TELEMETRY_COUNT} configs)"
    else
        log_warning "No telemetry configuration found"
    fi
}

check_pod_status() {
    log_test "Checking pod status..."

    # Check pods in each namespace
    for namespace in ${NAMESPACE_ISTIO} ${NAMESPACE_ARTEMIS} ${NAMESPACE_SOPHIA} ${NAMESPACE_SHARED}; do
        log_info "Checking pods in ${namespace}..."

        TOTAL_PODS=$(kubectl get pods -n ${namespace} --no-headers 2>/dev/null | wc -l)
        READY_PODS=$(kubectl get pods -n ${namespace} --no-headers 2>/dev/null | grep -c "Running" || echo 0)

        if [ ${TOTAL_PODS} -eq 0 ]; then
            log_warning "No pods found in ${namespace}"
        elif [ ${TOTAL_PODS} -eq ${READY_PODS} ]; then
            log_success "All pods are running in ${namespace} (${READY_PODS}/${TOTAL_PODS})"
        else
            log_error "Some pods are not running in ${namespace} (${READY_PODS}/${TOTAL_PODS})"
            kubectl get pods -n ${namespace} --no-headers | grep -v "Running"
        fi
    done
}

check_service_mesh_metrics() {
    log_test "Checking service mesh metrics..."

    # Check if metrics are being collected
    log_info "Checking if Envoy metrics are exposed..."

    POD=$(kubectl get pod -n ${NAMESPACE_ARTEMIS} -l app=sophia-orchestrator -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

    if [ ! -z "${POD}" ]; then
        METRICS=$(kubectl exec -n ${NAMESPACE_ARTEMIS} ${POD} -c istio-proxy -- \
            curl -s http://localhost:15000/stats/prometheus 2>/dev/null | head -n 5)

        if [ ! -z "${METRICS}" ]; then
            log_success "Envoy metrics are being exposed"
        else
            log_warning "Could not verify Envoy metrics"
        fi
    else
        log_warning "No pods available to check metrics"
    fi
}

print_summary() {
    echo
    echo "========================================="
    echo "Service Mesh Validation Summary"
    echo "========================================="
    echo
    echo -e "${GREEN}Tests Passed:${NC} ${TESTS_PASSED}"
    echo -e "${YELLOW}Warnings:${NC} ${TESTS_WARNINGS}"
    echo -e "${RED}Tests Failed:${NC} ${TESTS_FAILED}"
    echo

    if [ ${TESTS_FAILED} -eq 0 ]; then
        echo -e "${GREEN}✓ All critical tests passed!${NC}"
        echo "The Sophia-Sophia service mesh is properly configured."
    else
        echo -e "${RED}✗ Some tests failed.${NC}"
        echo "Please review the errors above and fix the issues."
    fi

    echo
    echo "Quick debugging commands:"
    echo "  istioctl proxy-status"
    echo "  istioctl analyze --all-namespaces"
    echo "  kubectl get pods --all-namespaces -l istio-injection=enabled"
    echo "  istioctl dashboard kiali"
    echo
}

# Main execution
main() {
    log_info "Starting Sophia-Sophia Service Mesh validation..."
    echo

    check_istio_installation
    echo

    verify_mtls
    echo

    test_service_connectivity
    echo

    validate_policies
    echo

    test_concurrent_tasks
    echo

    test_rate_limiting
    echo

    test_observability
    echo

    check_pod_status
    echo

    check_service_mesh_metrics
    echo

    print_summary

    # Exit with error if any tests failed
    if [ ${TESTS_FAILED} -gt 0 ]; then
        exit 1
    fi
}

# Run main function
main "$@"
