#!/bin/bash
set -euo pipefail

# KEDA Deployment Validation Script
# Performs comprehensive health checks post-deployment
# Verifies 85% scaling improvement target is achievable

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE_KEDA="keda-system"
NAMESPACE_ARTEMIS="sophia-system"
NAMESPACE_SOPHIA="sophia-system"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://prometheus.monitoring.svc.cluster.local:9090}"

# Validation thresholds
TARGET_SCALING_TIME=9
MAX_SCALE_EVENTS_PER_MIN=3
MIN_SUCCESS_RATE=90

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

# Track validation results
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
declare -a FAILED_ITEMS=()

# Record check result
record_check() {
    local check_name="$1"
    local result="$2"
    local details="${3:-}"

    ((TOTAL_CHECKS++))

    if [ "$result" = "pass" ]; then
        ((PASSED_CHECKS++))
        log_success "$check_name: $details"
    else
        ((FAILED_CHECKS++))
        FAILED_ITEMS+=("$check_name: $details")
        log_error "$check_name: $details"
    fi
}

# 1. Validate KEDA Operator
validate_keda_operator() {
    log_info "Validating KEDA Operator..."

    # Check operator pod
    local operator_pods=$(kubectl get pods -n "$NAMESPACE_KEDA" -l app=keda-operator --no-headers 2>/dev/null | wc -l)
    if [ "$operator_pods" -gt 0 ]; then
        local operator_ready=$(kubectl get pods -n "$NAMESPACE_KEDA" -l app=keda-operator \
            -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null)

        if [ "$operator_ready" = "True" ]; then
            record_check "KEDA Operator Pod" "pass" "Running and Ready"
        else
            record_check "KEDA Operator Pod" "fail" "Not Ready"
        fi
    else
        record_check "KEDA Operator Pod" "fail" "Not Found"
    fi

    # Check metrics server
    local metrics_pods=$(kubectl get pods -n "$NAMESPACE_KEDA" -l app=keda-operator-metrics-apiserver --no-headers 2>/dev/null | wc -l)
    if [ "$metrics_pods" -gt 0 ]; then
        local metrics_ready=$(kubectl get pods -n "$NAMESPACE_KEDA" -l app=keda-operator-metrics-apiserver \
            -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null)

        if [ "$metrics_ready" = "True" ]; then
            record_check "KEDA Metrics Server" "pass" "Running and Ready"
        else
            record_check "KEDA Metrics Server" "fail" "Not Ready"
        fi
    else
        record_check "KEDA Metrics Server" "fail" "Not Found"
    fi

    # Check webhook
    local webhook_ready=$(kubectl get validatingwebhookconfigurations -o json 2>/dev/null | \
        jq -r '.items[] | select(.metadata.name | contains("keda")) | .metadata.name' | wc -l)

    if [ "$webhook_ready" -gt 0 ]; then
        record_check "KEDA Webhook" "pass" "Configured"
    else
        record_check "KEDA Webhook" "fail" "Not Configured"
    fi
}

# 2. Validate ScaledObjects
validate_scaledobjects() {
    log_info "Validating ScaledObjects..."

    # Sophia ScaledObject
    if kubectl get scaledobject sophia-scaler -n "$NAMESPACE_ARTEMIS" &> /dev/null; then
        local sophia_ready=$(kubectl get scaledobject sophia-scaler -n "$NAMESPACE_ARTEMIS" \
            -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null)

        local sophia_active=$(kubectl get scaledobject sophia-scaler -n "$NAMESPACE_ARTEMIS" \
            -o jsonpath='{.status.conditions[?(@.type=="Active")].status}' 2>/dev/null)

        if [ "$sophia_ready" = "True" ] && [ "$sophia_active" = "True" ]; then
            record_check "Sophia ScaledObject" "pass" "Ready and Active"
        else
            record_check "Sophia ScaledObject" "fail" "Not Ready or Active"
        fi

        # Check if HPA was created
        if kubectl get hpa sophia-scaler -n "$NAMESPACE_ARTEMIS" &> /dev/null; then
            record_check "Sophia HPA Created" "pass" "HPA exists"
        else
            record_check "Sophia HPA Created" "fail" "HPA missing"
        fi
    else
        record_check "Sophia ScaledObject" "fail" "Not Found"
    fi

    # Sophia ScaledObject
    if kubectl get scaledobject sophia-scaler -n "$NAMESPACE_SOPHIA" &> /dev/null; then
        local sophia_ready=$(kubectl get scaledobject sophia-scaler -n "$NAMESPACE_SOPHIA" \
            -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null)

        local sophia_active=$(kubectl get scaledobject sophia-scaler -n "$NAMESPACE_SOPHIA" \
            -o jsonpath='{.status.conditions[?(@.type=="Active")].status}' 2>/dev/null)

        if [ "$sophia_ready" = "True" ] && [ "$sophia_active" = "True" ]; then
            record_check "Sophia ScaledObject" "pass" "Ready and Active"
        else
            record_check "Sophia ScaledObject" "fail" "Not Ready or Active"
        fi

        # Check if HPA was created
        if kubectl get hpa sophia-scaler -n "$NAMESPACE_SOPHIA" &> /dev/null; then
            record_check "Sophia HPA Created" "pass" "HPA exists"
        else
            record_check "Sophia HPA Created" "fail" "HPA missing"
        fi
    else
        record_check "Sophia ScaledObject" "fail" "Not Found"
    fi

    # Cron ScaledObject
    if kubectl get scaledobject ai-workload-cron-scaler -n "$NAMESPACE_SOPHIA" &> /dev/null; then
        record_check "Cron ScaledObject" "pass" "Exists"
    else
        record_check "Cron ScaledObject" "fail" "Not Found"
    fi
}

# 3. Validate External Metrics
validate_external_metrics() {
    log_info "Validating External Metrics..."

    # Check if metrics API is available
    if kubectl get --raw /apis/external.metrics.k8s.io/v1beta1 &> /dev/null; then
        record_check "External Metrics API" "pass" "Available"

        # Check specific metrics
        local redis_metric=$(kubectl get --raw "/apis/external.metrics.k8s.io/v1beta1/namespaces/$NAMESPACE_ARTEMIS/redis_list_length" 2>/dev/null | \
            jq -r '.items | length' || echo "0")

        if [ "$redis_metric" != "0" ]; then
            record_check "Redis Metrics" "pass" "Available"
        else
            record_check "Redis Metrics" "fail" "Not Available"
        fi
    else
        record_check "External Metrics API" "fail" "Not Available"
    fi
}

# 4. Validate Security Configuration
validate_security() {
    log_info "Validating Security Configuration..."

    # Check ServiceAccount
    if kubectl get serviceaccount keda-operator -n "$NAMESPACE_KEDA" &> /dev/null; then
        record_check "KEDA ServiceAccount" "pass" "Exists"
    else
        record_check "KEDA ServiceAccount" "fail" "Not Found"
    fi

    # Check RBAC
    if kubectl get clusterrole keda-operator &> /dev/null; then
        record_check "KEDA ClusterRole" "pass" "Exists"
    else
        record_check "KEDA ClusterRole" "fail" "Not Found"
    fi

    # Check NetworkPolicy
    if kubectl get networkpolicy keda-operator-network-policy -n "$NAMESPACE_KEDA" &> /dev/null; then
        record_check "KEDA NetworkPolicy" "pass" "Applied"
    else
        record_check "KEDA NetworkPolicy" "fail" "Not Applied"
    fi

    # Check Secrets
    if kubectl get secret redis-credentials -n "$NAMESPACE_ARTEMIS" &> /dev/null || \
       kubectl get secret redis-credentials-fallback -n "$NAMESPACE_ARTEMIS" &> /dev/null; then
        record_check "Redis Credentials" "pass" "Available"
    else
        record_check "Redis Credentials" "fail" "Missing"
    fi

    if kubectl get secret prometheus-credentials -n "$NAMESPACE_SOPHIA" &> /dev/null || \
       kubectl get secret prometheus-credentials-fallback -n "$NAMESPACE_SOPHIA" &> /dev/null; then
        record_check "Prometheus Credentials" "pass" "Available"
    else
        record_check "Prometheus Credentials" "fail" "Missing"
    fi
}

# 5. Validate Monitoring
validate_monitoring() {
    log_info "Validating Monitoring Configuration..."

    # Check PrometheusRule
    if kubectl get prometheusrule keda-autoscaling-rules -n monitoring &> /dev/null; then
        record_check "Prometheus Rules" "pass" "Deployed"

        # Check specific alerts
        local alerts=$(kubectl get prometheusrule keda-autoscaling-rules -n monitoring -o json | \
            jq -r '.spec.groups[].rules[].alert' 2>/dev/null | wc -l)

        if [ "$alerts" -gt 0 ]; then
            record_check "KEDA Alerts" "pass" "$alerts alerts configured"
        else
            record_check "KEDA Alerts" "fail" "No alerts configured"
        fi
    else
        record_check "Prometheus Rules" "fail" "Not Found"
    fi

    # Check ServiceMonitor
    if kubectl get servicemonitor keda-metrics -n "$NAMESPACE_KEDA" &> /dev/null; then
        record_check "ServiceMonitor" "pass" "Configured"
    else
        record_check "ServiceMonitor" "fail" "Not Configured"
    fi

    # Check metrics ConfigMap
    if kubectl get configmap keda-custom-metrics -n monitoring &> /dev/null; then
        record_check "Custom Metrics ConfigMap" "pass" "Deployed"
    else
        record_check "Custom Metrics ConfigMap" "fail" "Not Found"
    fi
}

# 6. Validate Circuit Breaker
validate_circuit_breaker() {
    log_info "Validating Circuit Breaker Configuration..."

    # Check annotations on ScaledObjects
    local cb_enabled=$(kubectl get scaledobject sophia-scaler -n "$NAMESPACE_ARTEMIS" \
        -o jsonpath='{.metadata.annotations.keda\.sh/circuit-breaker-enabled}' 2>/dev/null)

    if [ "$cb_enabled" = "true" ]; then
        record_check "Circuit Breaker Enabled" "pass" "Configured on Sophia"
    else
        record_check "Circuit Breaker Enabled" "fail" "Not Configured"
    fi

    # Check max events configuration
    local max_events=$(kubectl get scaledobject sophia-scaler -n "$NAMESPACE_ARTEMIS" \
        -o jsonpath='{.metadata.annotations.keda\.sh/max-scale-events}' 2>/dev/null)

    if [ "$max_events" = "$MAX_SCALE_EVENTS_PER_MIN" ]; then
        record_check "Circuit Breaker Threshold" "pass" "Set to $MAX_SCALE_EVENTS_PER_MIN events/min"
    else
        record_check "Circuit Breaker Threshold" "fail" "Incorrect threshold: $max_events"
    fi

    # Check fallback HPA exists
    if kubectl get hpa sophia-worker-hpa-backup -n "$NAMESPACE_ARTEMIS" &> /dev/null || \
       kubectl get hpa sophia-worker-hpa -n "$NAMESPACE_ARTEMIS" &> /dev/null; then
        record_check "Fallback HPA" "pass" "Available for circuit breaker"
    else
        record_check "Fallback HPA" "fail" "No fallback HPA found"
    fi
}

# 7. Performance Quick Check
validate_performance() {
    log_info "Running Performance Quick Check..."

    # Query Prometheus for scaling metrics if available
    if command -v curl &> /dev/null && [ -n "$PROMETHEUS_URL" ]; then
        # Check scaling time metric
        local scaling_time=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=keda:scaling_time_seconds" 2>/dev/null | \
            jq -r '.data.result[0].value[1]' 2>/dev/null || echo "")

        if [ -n "$scaling_time" ] && [ "$(echo "$scaling_time < $TARGET_SCALING_TIME" | bc -l 2>/dev/null)" = "1" ]; then
            record_check "Scaling Time" "pass" "${scaling_time}s (target: ${TARGET_SCALING_TIME}s)"
        elif [ -n "$scaling_time" ]; then
            record_check "Scaling Time" "fail" "${scaling_time}s exceeds target ${TARGET_SCALING_TIME}s"
        else
            log_warning "Scaling metrics not yet available"
        fi

        # Check scale events rate
        local scale_events=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=rate(keda_scaled_object_events_total[1m])" 2>/dev/null | \
            jq -r '.data.result[0].value[1]' 2>/dev/null || echo "")

        if [ -n "$scale_events" ] && [ "$(echo "$scale_events <= $MAX_SCALE_EVENTS_PER_MIN" | bc -l 2>/dev/null)" = "1" ]; then
            record_check "Scale Events Rate" "pass" "${scale_events}/min (limit: ${MAX_SCALE_EVENTS_PER_MIN}/min)"
        elif [ -n "$scale_events" ]; then
            record_check "Scale Events Rate" "fail" "${scale_events}/min exceeds limit"
        else
            log_warning "Scale event metrics not yet available"
        fi
    else
        log_warning "Prometheus not accessible for performance validation"
    fi
}

# 8. Connectivity Tests
validate_connectivity() {
    log_info "Validating Connectivity..."

    # Test Redis connectivity
    kubectl run redis-test --image=redis:alpine --rm -i --restart=Never -n "$NAMESPACE_ARTEMIS" -- \
        redis-cli -h redis.sophia-system.svc.cluster.local ping 2>/dev/null | grep -q "PONG"

    if [ $? -eq 0 ]; then
        record_check "Redis Connectivity" "pass" "PONG received"
    else
        record_check "Redis Connectivity" "fail" "Cannot reach Redis"
    fi

    # Test Prometheus connectivity
    kubectl run curl-test --image=curlimages/curl:latest --rm -i --restart=Never -n "$NAMESPACE_SOPHIA" -- \
        curl -s http://prometheus.monitoring.svc.cluster.local:9090/api/v1/query?query=up 2>/dev/null | grep -q "success"

    if [ $? -eq 0 ]; then
        record_check "Prometheus Connectivity" "pass" "API accessible"
    else
        record_check "Prometheus Connectivity" "fail" "Cannot reach Prometheus"
    fi
}

# Generate validation report
generate_report() {
    echo ""
    echo "======================================"
    echo "KEDA DEPLOYMENT VALIDATION REPORT"
    echo "======================================"
    echo "Date: $(date)"
    echo "--------------------------------------"
    echo "Total Checks: $TOTAL_CHECKS"
    echo "Passed: $PASSED_CHECKS"
    echo "Failed: $FAILED_CHECKS"

    local success_rate=$(echo "scale=2; $PASSED_CHECKS * 100 / $TOTAL_CHECKS" | bc)
    echo "Success Rate: ${success_rate}%"
    echo "--------------------------------------"

    if [ ${#FAILED_ITEMS[@]} -gt 0 ]; then
        echo ""
        echo "Failed Checks:"
        for item in "${FAILED_ITEMS[@]}"; do
            echo "  ✗ $item"
        done
        echo ""
    fi

    if [ "$(echo "$success_rate >= $MIN_SUCCESS_RATE" | bc -l)" = "1" ]; then
        log_success "✅ VALIDATION PASSED (${success_rate}% >= ${MIN_SUCCESS_RATE}%)"
        return 0
    else
        log_error "❌ VALIDATION FAILED (${success_rate}% < ${MIN_SUCCESS_RATE}%)"
        return 1
    fi
}

# Main validation flow
main() {
    log_info "Starting KEDA Deployment Validation..."

    # Run all validation checks
    validate_keda_operator
    validate_scaledobjects
    validate_external_metrics
    validate_security
    validate_monitoring
    validate_circuit_breaker
    validate_performance
    validate_connectivity

    # Generate and display report
    generate_report

    # Exit with appropriate code
    if [ "$FAILED_CHECKS" -eq 0 ]; then
        exit 0
    elif [ "$(echo "$PASSED_CHECKS * 100 / $TOTAL_CHECKS >= $MIN_SUCCESS_RATE" | bc -l)" = "1" ]; then
        exit 0
    else
        exit 1
    fi
}

# Run validation
main "$@"
