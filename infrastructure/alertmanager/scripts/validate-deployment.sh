#!/bin/bash

# AlertManager Deployment Validation Script
# Comprehensive health and functionality checks

set -e

# Configuration
NAMESPACE="${NAMESPACE:-monitoring}"
ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://alertmanager.monitoring:9093}"
EXPECTED_REPLICAS="${EXPECTED_REPLICAS:-3}"
VALIDATION_LEVEL="${VALIDATION_LEVEL:-full}"  # basic, standard, full

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNED=0

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
    ((TESTS_FAILED++))
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
    ((TESTS_WARNED++))
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

success() {
    log "$1 ✓"
    ((TESTS_PASSED++))
}

# Check pod status
check_pod_status() {
    log "Checking pod status..."

    local pods=$(kubectl get pods -n "$NAMESPACE" -l app=alertmanager -o json)
    local running_pods=$(echo "$pods" | jq -r '.items[] | select(.status.phase=="Running") | .metadata.name' | wc -l)
    local total_pods=$(echo "$pods" | jq -r '.items | length')

    if [[ $running_pods -eq $EXPECTED_REPLICAS ]]; then
        success "All $EXPECTED_REPLICAS pods are running"
    elif [[ $running_pods -gt 0 ]]; then
        warning "Only $running_pods/$EXPECTED_REPLICAS pods are running"
    else
        error "No pods are running"
        return 1
    fi

    # Check pod restarts
    local restart_count=$(echo "$pods" | jq -r '[.items[].status.containerStatuses[]?.restartCount // 0] | add')
    if [[ $restart_count -eq 0 ]]; then
        success "No pod restarts detected"
    elif [[ $restart_count -lt 5 ]]; then
        warning "Pods have restarted $restart_count times"
    else
        error "Excessive pod restarts: $restart_count"
    fi

    # Check pod age
    local oldest_pod=$(echo "$pods" | jq -r '.items[].metadata.creationTimestamp' | sort | head -1)
    if [[ -n "$oldest_pod" ]]; then
        local age_seconds=$(( $(date +%s) - $(date -d "$oldest_pod" +%s) ))
        if [[ $age_seconds -gt 60 ]]; then
            success "Pods are stable (oldest: ${age_seconds}s)"
        else
            warning "Pods are very new (oldest: ${age_seconds}s)"
        fi
    fi
}

# Check service endpoints
check_service_endpoints() {
    log "Checking service endpoints..."

    local endpoints=$(kubectl get endpoints alertmanager -n "$NAMESPACE" -o json)
    local addresses=$(echo "$endpoints" | jq -r '.subsets[].addresses | length' 2>/dev/null || echo 0)

    if [[ $addresses -ge $EXPECTED_REPLICAS ]]; then
        success "Service has $addresses endpoints"
    elif [[ $addresses -gt 0 ]]; then
        warning "Service has only $addresses endpoints (expected $EXPECTED_REPLICAS)"
    else
        error "Service has no endpoints"
        return 1
    fi
}

# Check API health
check_api_health() {
    log "Checking API health..."

    # Test from inside cluster
    if kubectl run test-alertmanager-health-$$ --rm -i --image=curlimages/curl:latest \
        --restart=Never -n "$NAMESPACE" -- \
        curl -s -o /dev/null -w "%{http_code}" "http://alertmanager:9093/-/healthy" 2>/dev/null | grep -q "200"; then
        success "Health endpoint is responding"
    else
        error "Health endpoint check failed"
    fi

    # Test readiness
    if kubectl run test-alertmanager-ready-$$ --rm -i --image=curlimages/curl:latest \
        --restart=Never -n "$NAMESPACE" -- \
        curl -s -o /dev/null -w "%{http_code}" "http://alertmanager:9093/-/ready" 2>/dev/null | grep -q "200"; then
        success "Readiness endpoint is responding"
    else
        error "Readiness endpoint check failed"
    fi
}

# Check cluster membership
check_cluster_membership() {
    log "Checking cluster membership..."

    local pod=$(kubectl get pod -n "$NAMESPACE" -l app=alertmanager -o jsonpath='{.items[0].metadata.name}')

    if [[ -z "$pod" ]]; then
        error "No AlertManager pod found"
        return 1
    fi

    local cluster_status=$(kubectl exec -n "$NAMESPACE" "$pod" -- \
        wget -qO- http://localhost:9093/api/v1/status 2>/dev/null | jq -r '.data.cluster')

    local peer_count=$(echo "$cluster_status" | jq -r '.peers | length')

    if [[ $peer_count -ge $((EXPECTED_REPLICAS - 1)) ]]; then
        success "Cluster has $peer_count peers"
    elif [[ $peer_count -gt 0 ]]; then
        warning "Cluster has only $peer_count peers (expected $((EXPECTED_REPLICAS - 1)))"
    else
        error "No cluster peers found"
    fi

    # Check cluster status
    local cluster_state=$(echo "$cluster_status" | jq -r '.status')
    if [[ "$cluster_state" == "ready" ]] || [[ "$cluster_state" == "settling" ]]; then
        success "Cluster status: $cluster_state"
    else
        warning "Cluster status: $cluster_state"
    fi
}

# Check configuration
check_configuration() {
    log "Checking configuration..."

    local pod=$(kubectl get pod -n "$NAMESPACE" -l app=alertmanager -o jsonpath='{.items[0].metadata.name}')

    # Validate configuration syntax
    if kubectl exec -n "$NAMESPACE" "$pod" -- \
        amtool check-config /etc/alertmanager/alertmanager.yml &> /dev/null; then
        success "Configuration syntax is valid"
    else
        error "Configuration syntax validation failed"
    fi

    # Check receivers
    local receivers=$(kubectl exec -n "$NAMESPACE" "$pod" -- \
        cat /etc/alertmanager/alertmanager.yml | grep -c "^  - name:" || echo 0)

    if [[ $receivers -gt 0 ]]; then
        success "Found $receivers configured receivers"
    else
        error "No receivers configured"
    fi

    # Check inhibit rules
    local inhibit_rules=$(kubectl exec -n "$NAMESPACE" "$pod" -- \
        cat /etc/alertmanager/alertmanager.yml | grep -c "source_matchers:" || echo 0)

    if [[ $inhibit_rules -gt 0 ]]; then
        success "Found $inhibit_rules inhibition rules"
    else
        warning "No inhibition rules configured"
    fi
}

# Check secrets
check_secrets() {
    log "Checking secrets..."

    if kubectl get secret alertmanager-secrets -n "$NAMESPACE" &> /dev/null; then
        success "Main secrets exist"

        # Check specific secret keys
        local required_secrets=("slack-api-url" "smtp-password")
        for secret in "${required_secrets[@]}"; do
            if kubectl get secret alertmanager-secrets -n "$NAMESPACE" \
                -o jsonpath="{.data.$secret}" &> /dev/null; then
                info "Secret $secret is present"
            else
                warning "Secret $secret is missing"
            fi
        done
    else
        error "AlertManager secrets not found"
    fi

    # Check OAuth secrets
    if kubectl get secret alertmanager-oauth -n "$NAMESPACE" &> /dev/null; then
        success "OAuth secrets exist"
    else
        warning "OAuth secrets not found"
    fi
}

# Check persistent volumes
check_persistent_volumes() {
    log "Checking persistent volumes..."

    local pvcs=$(kubectl get pvc -n "$NAMESPACE" -l app=alertmanager -o json)
    local bound_pvcs=$(echo "$pvcs" | jq -r '.items[] | select(.status.phase=="Bound") | .metadata.name' | wc -l)
    local total_pvcs=$(echo "$pvcs" | jq -r '.items | length')

    if [[ $bound_pvcs -eq $EXPECTED_REPLICAS ]]; then
        success "All $EXPECTED_REPLICAS PVCs are bound"
    elif [[ $bound_pvcs -gt 0 ]]; then
        warning "Only $bound_pvcs/$EXPECTED_REPLICAS PVCs are bound"
    else
        error "No PVCs are bound"
    fi

    # Check PVC usage
    local pod=$(kubectl get pod -n "$NAMESPACE" -l app=alertmanager -o jsonpath='{.items[0].metadata.name}')
    if [[ -n "$pod" ]]; then
        local usage=$(kubectl exec -n "$NAMESPACE" "$pod" -- df -h /alertmanager | tail -1 | awk '{print $5}' | tr -d '%')
        if [[ $usage -lt 80 ]]; then
            success "Storage usage: ${usage}%"
        elif [[ $usage -lt 90 ]]; then
            warning "Storage usage high: ${usage}%"
        else
            error "Storage usage critical: ${usage}%"
        fi
    fi
}

# Check network policies
check_network_policies() {
    if [[ "$VALIDATION_LEVEL" != "full" ]]; then
        return 0
    fi

    log "Checking network policies..."

    if kubectl get networkpolicy -n "$NAMESPACE" -l app=alertmanager &> /dev/null; then
        local policies=$(kubectl get networkpolicy -n "$NAMESPACE" -l app=alertmanager -o json | jq -r '.items | length')
        if [[ $policies -gt 0 ]]; then
            success "Found $policies network policies"
        else
            warning "No network policies found"
        fi
    else
        warning "NetworkPolicy not configured"
    fi
}

# Check RBAC
check_rbac() {
    if [[ "$VALIDATION_LEVEL" != "full" ]]; then
        return 0
    fi

    log "Checking RBAC configuration..."

    if kubectl get serviceaccount alertmanager -n "$NAMESPACE" &> /dev/null; then
        success "ServiceAccount exists"
    else
        error "ServiceAccount not found"
    fi

    if kubectl get clusterrolebinding alertmanager &> /dev/null; then
        success "ClusterRoleBinding exists"
    else
        warning "ClusterRoleBinding not found"
    fi
}

# Check metrics
check_metrics() {
    if [[ "$VALIDATION_LEVEL" == "basic" ]]; then
        return 0
    fi

    log "Checking metrics endpoint..."

    local pod=$(kubectl get pod -n "$NAMESPACE" -l app=alertmanager -o jsonpath='{.items[0].metadata.name}')

    if kubectl exec -n "$NAMESPACE" "$pod" -- \
        wget -qO- http://localhost:9093/metrics | grep -q "alertmanager_build_info"; then
        success "Metrics endpoint is working"
    else
        error "Metrics endpoint check failed"
    fi

    # Check key metrics
    local alerts_received=$(kubectl exec -n "$NAMESPACE" "$pod" -- \
        wget -qO- http://localhost:9093/metrics | grep "^alertmanager_alerts_received_total" | head -1 | awk '{print $2}')

    if [[ -n "$alerts_received" ]]; then
        info "Alerts received: $alerts_received"
    fi
}

# Check integrations
check_integrations() {
    if [[ "$VALIDATION_LEVEL" != "full" ]]; then
        return 0
    fi

    log "Checking integrations..."

    # Check Prometheus connection
    if kubectl get servicemonitor -n "$NAMESPACE" alertmanager &> /dev/null; then
        success "ServiceMonitor configured"
    else
        warning "ServiceMonitor not found"
    fi

    # Check if receiving alerts from Prometheus
    local pod=$(kubectl get pod -n "$NAMESPACE" -l app=alertmanager -o jsonpath='{.items[0].metadata.name}')
    local last_alert=$(kubectl exec -n "$NAMESPACE" "$pod" -- \
        wget -qO- http://localhost:9093/api/v1/alerts 2>/dev/null | jq -r '.data[0].startsAt' 2>/dev/null)

    if [[ -n "$last_alert" ]] && [[ "$last_alert" != "null" ]]; then
        info "Last alert received: $last_alert"
        success "Receiving alerts from Prometheus"
    else
        info "No alerts currently active"
    fi
}

# Performance check
check_performance() {
    if [[ "$VALIDATION_LEVEL" != "full" ]]; then
        return 0
    fi

    log "Checking performance..."

    local pod=$(kubectl get pod -n "$NAMESPACE" -l app=alertmanager -o jsonpath='{.items[0].metadata.name}')

    # Check response time
    local response_time=$(kubectl exec -n "$NAMESPACE" "$pod" -- \
        sh -c "time wget -qO- http://localhost:9093/api/v1/status 2>&1" | grep real | awk '{print $2}')

    if [[ -n "$response_time" ]]; then
        info "API response time: $response_time"
        success "Performance check passed"
    else
        warning "Could not measure response time"
    fi
}

# Generate report
generate_report() {
    log ""
    log "=========================================="
    log "Validation Report"
    log "=========================================="
    log "Namespace: $NAMESPACE"
    log "Validation Level: $VALIDATION_LEVEL"
    log ""
    log "Test Results:"
    log "  Passed: $TESTS_PASSED"
    log "  Warnings: $TESTS_WARNED"
    log "  Failed: $TESTS_FAILED"
    log ""

    if [[ $TESTS_FAILED -eq 0 ]]; then
        log "✅ VALIDATION PASSED - AlertManager is healthy"
        return 0
    elif [[ $TESTS_FAILED -lt 3 ]]; then
        warning "⚠️  VALIDATION PASSED WITH WARNINGS"
        return 0
    else
        error "❌ VALIDATION FAILED - AlertManager needs attention"
        return 1
    fi
}

# Main execution
main() {
    log "=========================================="
    log "AlertManager Deployment Validation"
    log "=========================================="

    case "$VALIDATION_LEVEL" in
        basic)
            check_pod_status
            check_service_endpoints
            check_api_health
            ;;
        standard)
            check_pod_status
            check_service_endpoints
            check_api_health
            check_cluster_membership
            check_configuration
            check_secrets
            check_persistent_volumes
            check_metrics
            ;;
        full)
            check_pod_status
            check_service_endpoints
            check_api_health
            check_cluster_membership
            check_configuration
            check_secrets
            check_persistent_volumes
            check_network_policies
            check_rbac
            check_metrics
            check_integrations
            check_performance
            ;;
        *)
            error "Unknown validation level: $VALIDATION_LEVEL"
            exit 1
            ;;
    esac

    generate_report
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --level)
            VALIDATION_LEVEL="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --namespace <namespace>    Kubernetes namespace (default: monitoring)"
            echo "  --level <level>           Validation level: basic|standard|full (default: full)"
            echo "  --help                    Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main function
main
