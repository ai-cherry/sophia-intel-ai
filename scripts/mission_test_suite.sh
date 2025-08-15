#!/bin/bash
set -euo pipefail

# SOPHIA Intel - Mission Test Suite
# End-to-end testing of natural language to PR pipeline

echo "🎯 SOPHIA Intel Mission Test Suite"
echo "=================================="
echo "Time: $(date)"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Helper functions
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Configuration
API_BASE="${API_BASE:-http://localhost:5000}"
DASHBOARD_BASE="${DASHBOARD_BASE:-http://localhost:5001}"
PRODUCTION_API="${PRODUCTION_API:-https://api.sophia-intel.ai}"
PRODUCTION_DASHBOARD="${PRODUCTION_DASHBOARD:-https://www.sophia-intel.ai}"

# Test mission definitions
declare -A TEST_MISSIONS=(
    ["simple_docs"]="Create docs/HELLO.md with a simple hello world example"
    ["bug_fix"]="Fix any linting errors in the backend/services directory"
    ["feature_add"]="Add a /api/version endpoint that returns the current version"
    ["test_creation"]="Create unit tests for the health check endpoint"
    ["refactor"]="Refactor the model router to use async/await pattern"
    ["security"]="Add rate limiting to the mission creation endpoint"
    ["documentation"]="Update README.md with deployment instructions"
    ["integration"]="Add integration test for the complete mission pipeline"
)

# Mission test results
declare -A MISSION_RESULTS=()
MISSIONS_TOTAL=0
MISSIONS_PASSED=0
MISSIONS_FAILED=0

# Submit mission and track progress
submit_mission() {
    local mission_name="$1"
    local mission_goal="$2"
    local api_base="$3"
    
    log_info "Submitting mission: $mission_name"
    echo "Goal: $mission_goal"
    
    # Submit mission
    local response=$(curl -s -X POST "$api_base/api/missions" \
        -H "Content-Type: application/json" \
        -d "{\"goal\": \"$mission_goal\"}" 2>/dev/null || echo "failed")
    
    if echo "$response" | jq -e '.mission_id' >/dev/null 2>&1; then
        local mission_id=$(echo "$response" | jq -r '.mission_id')
        log_success "Mission created: $mission_id"
        
        # Monitor mission progress
        monitor_mission "$mission_id" "$api_base"
        return $?
    else
        log_error "Failed to create mission"
        echo "Response: $response"
        return 1
    fi
}

# Monitor mission progress via SSE
monitor_mission() {
    local mission_id="$1"
    local api_base="$2"
    local timeout=300  # 5 minutes
    
    log_info "Monitoring mission progress (timeout: ${timeout}s)..."
    
    # Create temporary file for SSE output
    local sse_output=$(mktemp)
    local status_file=$(mktemp)
    
    # Start SSE monitoring in background
    timeout $timeout curl -N -s "$api_base/api/missions/$mission_id/events" > "$sse_output" 2>/dev/null &
    local sse_pid=$!
    
    # Monitor for completion
    local start_time=$(date +%s)
    local last_event=""
    
    while [[ $(($(date +%s) - start_time)) -lt $timeout ]]; do
        # Check if mission completed
        local status=$(curl -s "$api_base/api/missions/$mission_id/status" 2>/dev/null || echo "failed")
        
        if echo "$status" | jq -e '.status' >/dev/null 2>&1; then
            local mission_status=$(echo "$status" | jq -r '.status')
            
            case "$mission_status" in
                "completed")
                    log_success "Mission completed successfully"
                    local pr_url=$(echo "$status" | jq -r '.pr_url // "N/A"')
                    if [[ "$pr_url" != "N/A" ]]; then
                        log_success "PR created: $pr_url"
                    fi
                    kill $sse_pid 2>/dev/null || true
                    rm -f "$sse_output" "$status_file"
                    return 0
                    ;;
                "failed")
                    log_error "Mission failed"
                    local error=$(echo "$status" | jq -r '.error // "Unknown error"')
                    echo "Error: $error"
                    kill $sse_pid 2>/dev/null || true
                    rm -f "$sse_output" "$status_file"
                    return 1
                    ;;
                "running"|"planning"|"coding"|"reviewing"|"testing")
                    # Show progress if available
                    if [[ -f "$sse_output" ]]; then
                        local new_events=$(tail -n 5 "$sse_output" 2>/dev/null | grep -v "^$last_event" || true)
                        if [[ -n "$new_events" ]]; then
                            echo "$new_events" | while read -r line; do
                                if [[ -n "$line" ]]; then
                                    echo "  📊 $line"
                                fi
                            done
                            last_event=$(tail -n 1 "$sse_output" 2>/dev/null || echo "")
                        fi
                    fi
                    ;;
            esac
        fi
        
        sleep 5
    done
    
    # Timeout reached
    log_warning "Mission monitoring timeout reached"
    kill $sse_pid 2>/dev/null || true
    rm -f "$sse_output" "$status_file"
    return 1
}

# Test dashboard interface
test_dashboard_interface() {
    local dashboard_base="$1"
    
    log_info "Testing dashboard interface..."
    
    # Test dashboard loading
    if curl -f "$dashboard_base" >/dev/null 2>&1; then
        log_success "Dashboard accessible"
    else
        log_error "Dashboard not accessible"
        return 1
    fi
    
    # Test API endpoints from dashboard
    if curl -f "$dashboard_base/api/health" >/dev/null 2>&1; then
        log_success "Dashboard API accessible"
    else
        log_error "Dashboard API not accessible"
        return 1
    fi
    
    # Test model endpoint
    if curl -f "$dashboard_base/api/models" >/dev/null 2>&1; then
        log_success "Model endpoint accessible"
    else
        log_error "Model endpoint not accessible"
        return 1
    fi
    
    return 0
}

# Test SSE streaming
test_sse_streaming() {
    local api_base="$1"
    
    log_info "Testing SSE streaming..."
    
    # Test SSE endpoint
    local sse_test=$(timeout 10s curl -N -s "$api_base/api/events/test-stream" 2>/dev/null | head -n 3 || echo "failed")
    
    if [[ "$sse_test" != "failed" ]] && [[ -n "$sse_test" ]]; then
        log_success "SSE streaming working"
        return 0
    else
        log_error "SSE streaming failed"
        return 1
    fi
}

# Test model allowlist enforcement
test_model_allowlist() {
    local api_base="$1"
    
    log_info "Testing model allowlist enforcement..."
    
    # Get allowed models
    local models=$(curl -s "$api_base/api/models" 2>/dev/null || echo "failed")
    
    if echo "$models" | jq -e '.allowed_models' >/dev/null 2>&1; then
        local allowed_count=$(echo "$models" | jq '.allowed_models | length')
        local blocked_count=$(echo "$models" | jq '.blocked_models | length')
        
        log_success "Model allowlist active: $allowed_count allowed, $blocked_count blocked"
        
        # Test model selection
        local selection=$(curl -s -X POST "$api_base/api/models/select" \
            -H "Content-Type: application/json" \
            -d '{"task_type": "coding"}' 2>/dev/null || echo "failed")
        
        if echo "$selection" | jq -e '.model' >/dev/null 2>&1; then
            local selected_model=$(echo "$selection" | jq -r '.model')
            log_success "Model selection working: $selected_model"
            return 0
        else
            log_error "Model selection failed"
            return 1
        fi
    else
        log_error "Model allowlist not accessible"
        return 1
    fi
}

# Run comprehensive mission tests
run_mission_tests() {
    local api_base="$1"
    local test_type="$2"
    
    log_info "Running $test_type mission tests..."
    
    for mission_name in "${!TEST_MISSIONS[@]}"; do
        local mission_goal="${TEST_MISSIONS[$mission_name]}"
        
        MISSIONS_TOTAL=$((MISSIONS_TOTAL + 1))
        
        log_info "Test $MISSIONS_TOTAL: $mission_name"
        
        if submit_mission "$mission_name" "$mission_goal" "$api_base"; then
            MISSION_RESULTS["$mission_name"]="PASS"
            MISSIONS_PASSED=$((MISSIONS_PASSED + 1))
            log_success "Mission test passed: $mission_name"
        else
            MISSION_RESULTS["$mission_name"]="FAIL"
            MISSIONS_FAILED=$((MISSIONS_FAILED + 1))
            log_error "Mission test failed: $mission_name"
        fi
        
        # Wait between missions to avoid overwhelming the system
        sleep 10
    done
}

# Test local environment
test_local_environment() {
    log_info "Testing local environment..."
    
    # Test dashboard interface
    if test_dashboard_interface "$DASHBOARD_BASE"; then
        log_success "Local dashboard tests passed"
    else
        log_error "Local dashboard tests failed"
        return 1
    fi
    
    # Test SSE streaming
    if test_sse_streaming "$API_BASE"; then
        log_success "Local SSE tests passed"
    else
        log_error "Local SSE tests failed"
    fi
    
    # Test model allowlist
    if test_model_allowlist "$API_BASE"; then
        log_success "Local model allowlist tests passed"
    else
        log_error "Local model allowlist tests failed"
    fi
    
    # Run mission tests (limited set for local)
    log_info "Running local mission tests (limited set)..."
    
    # Test simple mission only for local
    if submit_mission "simple_docs" "${TEST_MISSIONS[simple_docs]}" "$API_BASE"; then
        log_success "Local mission test passed"
    else
        log_warning "Local mission test failed"
    fi
}

# Test production environment
test_production_environment() {
    log_info "Testing production environment..."
    
    # Check if production is accessible
    if ! curl -f "$PRODUCTION_DASHBOARD" >/dev/null 2>&1; then
        log_warning "Production environment not accessible, skipping production tests"
        return 0
    fi
    
    # Test production dashboard
    if test_dashboard_interface "$PRODUCTION_DASHBOARD"; then
        log_success "Production dashboard tests passed"
    else
        log_error "Production dashboard tests failed"
        return 1
    fi
    
    # Test production SSE
    if test_sse_streaming "$PRODUCTION_API"; then
        log_success "Production SSE tests passed"
    else
        log_error "Production SSE tests failed"
    fi
    
    # Test production model allowlist
    if test_model_allowlist "$PRODUCTION_API"; then
        log_success "Production model allowlist tests passed"
    else
        log_error "Production model allowlist tests failed"
    fi
    
    # Run full mission test suite on production
    run_mission_tests "$PRODUCTION_API" "production"
}

# Generate comprehensive test report
generate_test_report() {
    echo ""
    echo "📊 Mission Test Suite Report"
    echo "============================"
    echo "Time: $(date)"
    echo "Total Missions Tested: $MISSIONS_TOTAL"
    echo "Passed: $MISSIONS_PASSED"
    echo "Failed: $MISSIONS_FAILED"
    
    if [[ $MISSIONS_TOTAL -gt 0 ]]; then
        echo "Success Rate: $(( MISSIONS_PASSED * 100 / MISSIONS_TOTAL ))%"
    fi
    
    echo ""
    echo "Mission Results:"
    echo "==============="
    
    for mission_name in "${!MISSION_RESULTS[@]}"; do
        local result="${MISSION_RESULTS[$mission_name]}"
        local status_icon="❌"
        if [[ "$result" == "PASS" ]]; then
            status_icon="✅"
        fi
        echo "$status_icon $mission_name: $result"
    done
    
    echo ""
    
    if [[ $MISSIONS_FAILED -eq 0 ]] && [[ $MISSIONS_TOTAL -gt 0 ]]; then
        log_success "All mission tests passed! 🎉"
        echo "SOPHIA Intel natural language → PR pipeline is fully operational."
    elif [[ $MISSIONS_TOTAL -eq 0 ]]; then
        log_warning "No missions were tested."
    else
        log_warning "$MISSIONS_FAILED mission tests failed. Review and fix issues."
    fi
    
    # Save detailed report
    cat > mission_test_report.json << EOF
{
    "timestamp": "$(date -Iseconds)",
    "total_missions": $MISSIONS_TOTAL,
    "passed": $MISSIONS_PASSED,
    "failed": $MISSIONS_FAILED,
    "success_rate": $(if [[ $MISSIONS_TOTAL -gt 0 ]]; then echo "$(( MISSIONS_PASSED * 100 / MISSIONS_TOTAL ))"; else echo "0"; fi),
    "results": {
$(for mission_name in "${!MISSION_RESULTS[@]}"; do
    echo "        \"$mission_name\": \"${MISSION_RESULTS[$mission_name]}\","
done | sed '$ s/,$//')
    },
    "status": "$(if [[ $MISSIONS_FAILED -eq 0 ]] && [[ $MISSIONS_TOTAL -gt 0 ]]; then echo "PASS"; else echo "FAIL"; fi)"
}
EOF
    
    log_success "Detailed report saved to mission_test_report.json"
}

# Main test execution
main() {
    local test_mode="${1:-both}"
    
    echo "🎯 Starting Mission Test Suite"
    echo "=============================="
    echo "Test Mode: $test_mode"
    echo ""
    
    case "$test_mode" in
        "local")
            test_local_environment
            ;;
        "production")
            test_production_environment
            ;;
        "both"|*)
            test_local_environment
            echo ""
            test_production_environment
            ;;
    esac
    
    # Generate final report
    generate_test_report
}

# Show usage if help requested
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    echo "SOPHIA Intel Mission Test Suite"
    echo ""
    echo "Usage: $0 [test_mode]"
    echo ""
    echo "Test Modes:"
    echo "  local      - Test local environment only"
    echo "  production - Test production environment only"
    echo "  both       - Test both environments (default)"
    echo ""
    echo "Environment Variables:"
    echo "  API_BASE              - Local API base URL (default: http://localhost:5000)"
    echo "  DASHBOARD_BASE        - Local dashboard URL (default: http://localhost:5001)"
    echo "  PRODUCTION_API        - Production API URL (default: https://api.sophia-intel.ai)"
    echo "  PRODUCTION_DASHBOARD  - Production dashboard URL (default: https://www.sophia-intel.ai)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Test both local and production"
    echo "  $0 local              # Test local only"
    echo "  $0 production         # Test production only"
    exit 0
fi

# Run test suite
main "$@"

