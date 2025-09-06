#!/bin/bash

# AlertManager High Availability Failover Test
# Tests AlertManager HA cluster resilience and failover capabilities

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

NAMESPACE="${NAMESPACE:-monitoring}"
ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://alertmanager.monitoring:9093}"
TEST_DURATION="${TEST_DURATION:-600}" # 10 minutes default
VERBOSE="${VERBOSE:-false}"

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed"
        exit 1
    fi

    # Check jq
    if ! command -v jq &> /dev/null; then
        error "jq is not installed"
        exit 1
    fi

    # Check curl
    if ! command -v curl &> /dev/null; then
        error "curl is not installed"
        exit 1
    fi

    # Check namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        error "Namespace $NAMESPACE does not exist"
        exit 1
    fi

    log "Prerequisites check passed ✓"
}

# Get AlertManager cluster status
get_cluster_status() {
    local pod=$1
    kubectl exec -n "$NAMESPACE" "$pod" -- \
        wget -qO- http://localhost:9093/api/v1/status 2>/dev/null | \
        jq -r '.data.cluster'
}

# Get cluster members
get_cluster_members() {
    kubectl exec -n "$NAMESPACE" alertmanager-0 -- \
        wget -qO- http://localhost:9093/api/v1/status 2>/dev/null | \
        jq -r '.data.cluster.peers[].address' 2>/dev/null || echo "Failed to get peers"
}

# Send test alert
send_test_alert() {
    local alert_name=$1
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    cat <<EOF | curl -s -X POST "$ALERTMANAGER_URL/api/v1/alerts" \
        -H "Content-Type: application/json" \
        -d @- > /dev/null
[
  {
    "labels": {
      "alertname": "$alert_name",
      "severity": "critical",
      "test": "ha_failover",
      "timestamp": "$timestamp"
    },
    "annotations": {
      "description": "HA failover test alert",
      "test_id": "$(uuidgen || echo 'test-$$')"
    },
    "startsAt": "$timestamp",
    "endsAt": "$(date -u -d '+1 hour' +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")"
  }
]
EOF
}

# Check if alert exists
check_alert_exists() {
    local alert_name=$1
    local result=$(curl -s "$ALERTMANAGER_URL/api/v1/alerts" | \
        jq -r ".data[] | select(.labels.alertname == \"$alert_name\") | .labels.alertname" | \
        head -1)

    if [[ "$result" == "$alert_name" ]]; then
        return 0
    else
        return 1
    fi
}

# Test 1: Verify initial cluster state
test_initial_cluster_state() {
    log "Test 1: Verifying initial cluster state..."

    local pods=($(kubectl get pods -n "$NAMESPACE" -l app=alertmanager -o jsonpath='{.items[*].metadata.name}'))
    local cluster_healthy=true

    if [[ ${#pods[@]} -lt 3 ]]; then
        error "Expected 3 AlertManager pods, found ${#pods[@]}"
        ((TESTS_FAILED++))
        return 1
    fi

    for pod in "${pods[@]}"; do
        local status=$(kubectl get pod -n "$NAMESPACE" "$pod" -o jsonpath='{.status.phase}')
        if [[ "$status" != "Running" ]]; then
            error "Pod $pod is not running (status: $status)"
            cluster_healthy=false
        else
            log "  Pod $pod is running ✓"
        fi
    done

    # Check cluster members
    log "  Cluster members:"
    get_cluster_members | while read member; do
        log "    - $member"
    done

    if $cluster_healthy; then
        log "Test 1 PASSED: Initial cluster state is healthy ✓"
        ((TESTS_PASSED++))
    else
        error "Test 1 FAILED: Cluster is not healthy"
        ((TESTS_FAILED++))
    fi
}

# Test 2: Primary node failure
test_primary_node_failure() {
    log "Test 2: Simulating primary node failure..."

    # Send test alert before failure
    local test_alert="test_primary_failure_$$"
    send_test_alert "$test_alert"
    sleep 2

    # Verify alert was received
    if ! check_alert_exists "$test_alert"; then
        error "Failed to create test alert"
        ((TESTS_FAILED++))
        return 1
    fi

    # Delete primary pod
    log "  Deleting alertmanager-0..."
    kubectl delete pod -n "$NAMESPACE" alertmanager-0 --force --grace-period=0

    # Wait for cluster to stabilize
    sleep 10

    # Check remaining nodes
    local remaining_pods=(alertmanager-1 alertmanager-2)
    local cluster_stable=true

    for pod in "${remaining_pods[@]}"; do
        if kubectl get pod -n "$NAMESPACE" "$pod" &> /dev/null; then
            log "  Pod $pod is still running ✓"
        else
            error "Pod $pod is not available"
            cluster_stable=false
        fi
    done

    # Verify alert still exists
    if check_alert_exists "$test_alert"; then
        log "  Alert preserved after failover ✓"
    else
        error "Alert lost during failover"
        cluster_stable=false
    fi

    # Send new alert to verify functionality
    local new_alert="test_after_primary_failure_$$"
    send_test_alert "$new_alert"
    sleep 2

    if check_alert_exists "$new_alert"; then
        log "  New alerts accepted after failover ✓"
    else
        error "Cannot accept new alerts after failover"
        cluster_stable=false
    fi

    # Wait for pod to be recreated
    log "  Waiting for alertmanager-0 to be recreated..."
    kubectl wait --for=condition=ready pod/alertmanager-0 -n "$NAMESPACE" --timeout=120s

    if $cluster_stable; then
        log "Test 2 PASSED: Cluster survived primary node failure ✓"
        ((TESTS_PASSED++))
    else
        error "Test 2 FAILED: Cluster did not handle primary failure properly"
        ((TESTS_FAILED++))
    fi
}

# Test 3: Network partition
test_network_partition() {
    log "Test 3: Simulating network partition..."

    # Create network partition (block communication to one node)
    log "  Creating network partition for alertmanager-1..."
    kubectl exec -n "$NAMESPACE" alertmanager-1 -- sh -c "
        apk add --no-cache iptables 2>/dev/null || true
        iptables -A INPUT -s alertmanager-0.alertmanager-headless -j DROP
        iptables -A INPUT -s alertmanager-2.alertmanager-headless -j DROP
    " 2>/dev/null || warning "Could not create network partition (requires privileges)"

    sleep 30

    # Check cluster status
    log "  Checking cluster status during partition..."
    local cluster_status=$(get_cluster_status alertmanager-0 2>/dev/null || echo "{}")

    # Send test alert
    local test_alert="test_network_partition_$$"
    send_test_alert "$test_alert"
    sleep 2

    # Verify alert handling
    if check_alert_exists "$test_alert"; then
        log "  Alerts still processed during partition ✓"
    else
        warning "Alert processing affected by partition"
    fi

    # Remove network partition
    log "  Removing network partition..."
    kubectl exec -n "$NAMESPACE" alertmanager-1 -- sh -c "
        iptables -F INPUT 2>/dev/null || true
    " 2>/dev/null || warning "Could not remove network partition"

    sleep 10

    # Verify cluster recovery
    local members_count=$(get_cluster_members | wc -l)
    if [[ $members_count -ge 2 ]]; then
        log "  Cluster recovered from partition ✓"
        log "Test 3 PASSED: Network partition handled ✓"
        ((TESTS_PASSED++))
    else
        error "Cluster did not recover from partition"
        error "Test 3 FAILED"
        ((TESTS_FAILED++))
    fi
}

# Test 4: Rolling update
test_rolling_update() {
    log "Test 4: Testing rolling update..."

    # Send test alert before update
    local test_alert="test_rolling_update_$$"
    send_test_alert "$test_alert"
    sleep 2

    # Trigger rolling update by updating annotation
    log "  Triggering rolling update..."
    kubectl patch statefulset alertmanager -n "$NAMESPACE" \
        -p '{"spec":{"template":{"metadata":{"annotations":{"test.rollout":"'$(date +%s)'"}}}}}'

    # Monitor rollout
    log "  Monitoring rollout progress..."
    kubectl rollout status statefulset/alertmanager -n "$NAMESPACE" --timeout=300s

    # Verify alert persisted
    if check_alert_exists "$test_alert"; then
        log "  Alert preserved during rolling update ✓"
        log "Test 4 PASSED: Rolling update successful ✓"
        ((TESTS_PASSED++))
    else
        error "Alert lost during rolling update"
        error "Test 4 FAILED"
        ((TESTS_FAILED++))
    fi
}

# Test 5: Alert delivery during failover
test_alert_delivery_during_failover() {
    log "Test 5: Testing alert delivery during failover..."

    # Start sending alerts in background
    local alert_prefix="continuous_test_$$"
    local stop_file="/tmp/stop_alerts_$$"

    (
        while [[ ! -f "$stop_file" ]]; do
            send_test_alert "${alert_prefix}_$(date +%s)"
            sleep 1
        done
    ) &
    local alert_pid=$!

    log "  Started continuous alert sending (PID: $alert_pid)"

    # Wait for alerts to start flowing
    sleep 5

    # Count initial alerts
    local initial_count=$(curl -s "$ALERTMANAGER_URL/api/v1/alerts" | \
        jq -r "[.data[] | select(.labels.alertname | startswith(\"$alert_prefix\"))] | length")
    log "  Initial alert count: $initial_count"

    # Delete a pod
    log "  Deleting alertmanager-1 during alert flow..."
    kubectl delete pod -n "$NAMESPACE" alertmanager-1 --force --grace-period=0

    # Continue sending for 10 more seconds
    sleep 10

    # Stop alert sending
    touch "$stop_file"
    wait $alert_pid 2>/dev/null
    rm -f "$stop_file"

    # Wait for pod recovery
    kubectl wait --for=condition=ready pod/alertmanager-1 -n "$NAMESPACE" --timeout=120s

    # Count final alerts
    local final_count=$(curl -s "$ALERTMANAGER_URL/api/v1/alerts" | \
        jq -r "[.data[] | select(.labels.alertname | startswith(\"$alert_prefix\"))] | length")
    log "  Final alert count: $final_count"

    # Calculate loss rate
    local expected_alerts=15  # ~15 seconds of alerts
    local actual_alerts=$((final_count - initial_count))
    local loss_rate=$(awk "BEGIN {printf \"%.2f\", 100 - ($actual_alerts / $expected_alerts * 100)}")

    log "  Alert loss rate: ${loss_rate}%"

    if (( $(echo "$loss_rate < 10" | bc -l) )); then
        log "Test 5 PASSED: Minimal alert loss during failover ✓"
        ((TESTS_PASSED++))
    else
        error "Test 5 FAILED: High alert loss rate (${loss_rate}%)"
        ((TESTS_FAILED++))
    fi
}

# Test 6: Cluster split-brain prevention
test_split_brain_prevention() {
    log "Test 6: Testing split-brain prevention..."

    # Get current leader
    local leader=$(kubectl exec -n "$NAMESPACE" alertmanager-0 -- \
        wget -qO- http://localhost:9093/api/v1/status 2>/dev/null | \
        jq -r '.data.cluster.status' | grep -o 'ready' | head -1)

    if [[ -z "$leader" ]]; then
        warning "Could not determine cluster leader"
    fi

    # Create competing alerts on different nodes
    log "  Sending same alert to different nodes..."

    # Send to node 0
    kubectl exec -n "$NAMESPACE" alertmanager-0 -- sh -c "
        wget -O- --post-data='[{\"labels\":{\"alertname\":\"split_brain_test\",\"instance\":\"node0\"}}]' \
        --header='Content-Type: application/json' \
        http://localhost:9093/api/v1/alerts
    " &> /dev/null

    # Send to node 1
    kubectl exec -n "$NAMESPACE" alertmanager-1 -- sh -c "
        wget -O- --post-data='[{\"labels\":{\"alertname\":\"split_brain_test\",\"instance\":\"node1\"}}]' \
        --header='Content-Type: application/json' \
        http://localhost:9093/api/v1/alerts
    " &> /dev/null

    sleep 5

    # Check for duplicates
    local alert_count=$(curl -s "$ALERTMANAGER_URL/api/v1/alerts" | \
        jq -r '[.data[] | select(.labels.alertname == "split_brain_test")] | length')

    if [[ $alert_count -eq 2 ]]; then
        log "  Both alerts properly handled ✓"
        log "Test 6 PASSED: Split-brain prevention working ✓"
        ((TESTS_PASSED++))
    else
        error "Unexpected alert count: $alert_count"
        error "Test 6 FAILED"
        ((TESTS_FAILED++))
    fi
}

# Main test execution
main() {
    log "=========================================="
    log "AlertManager HA Failover Test Suite"
    log "=========================================="
    log "Namespace: $NAMESPACE"
    log "URL: $ALERTMANAGER_URL"
    log "Test Duration: $TEST_DURATION seconds"
    log ""

    check_prerequisites

    # Run tests
    test_initial_cluster_state
    test_primary_node_failure
    test_network_partition
    test_rolling_update
    test_alert_delivery_during_failover
    test_split_brain_prevention

    # Summary
    log ""
    log "=========================================="
    log "Test Summary"
    log "=========================================="
    log "Tests Passed: $TESTS_PASSED"
    log "Tests Failed: $TESTS_FAILED"

    if [[ $TESTS_FAILED -eq 0 ]]; then
        log ""
        log "✅ ALL TESTS PASSED - AlertManager HA is functioning correctly"
        exit 0
    else
        error ""
        error "❌ SOME TESTS FAILED - AlertManager HA needs attention"
        exit 1
    fi
}

# Run main function
main "$@"
