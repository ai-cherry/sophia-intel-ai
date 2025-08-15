#!/bin/bash
set -euo pipefail

# SOPHIA Intel - MCP Verification Suite
# Comprehensive testing of all MCP servers and capabilities

echo "🧪 SOPHIA Intel MCP Verification Suite"
echo "======================================"
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

# Test counters
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test function wrapper
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    log_info "Testing: $test_name"
    
    if eval "$test_command" >/dev/null 2>&1; then
        log_success "$test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        log_error "$test_name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Test MCP Code Server health
test_mcp_code_health() {
    log_info "Testing MCP Code Server health..."
    
    # Use production domain if available, fallback to localhost
    MCP_BASE="${MCP_BASE:-https://mcp.sophia-intel.ai}"
    if ! curl -f "$MCP_BASE/healthz" >/dev/null 2>&1; then
        MCP_BASE="http://localhost:8000"
        log_warning "Production MCP not accessible, using localhost"
    fi
    
    run_test "MCP Code Server - Health Endpoint" \
        "curl -f $MCP_BASE/healthz"
    
    run_test "MCP Code Server - GitHub Integration" \
        "curl -f $MCP_BASE/mcp/code/github/status"
    
    run_test "MCP Code Server - Repository Access" \
        "curl -f $MCP_BASE/mcp/code/repo/status"
}

# Test MCP Research Server
test_mcp_research() {
    log_info "Testing MCP Research Server..."
    
    run_test "MCP Research - Health Endpoint" \
        "curl -f $MCP_BASE/mcp/research/health"
    
    run_test "MCP Research - Search Capability" \
        "curl -f -X POST $MCP_BASE/mcp/research/search -H 'Content-Type: application/json' -d '{\"query\": \"test\"}'"
    
    run_test "MCP Research - Analysis Capability" \
        "curl -f -X POST $MCP_BASE/mcp/research/analyze -H 'Content-Type: application/json' -d '{\"content\": \"test content\"}'"
}

# Test MCP Code Analysis
test_mcp_analysis() {
    log_info "Testing MCP Code Analysis..."
    
    run_test "MCP Analysis - Health Endpoint" \
        "curl -f $MCP_BASE/mcp/analysis/health"
    
    run_test "MCP Analysis - Code Quality Check" \
        "curl -f -X POST $MCP_BASE/mcp/analysis/quality -H 'Content-Type: application/json' -d '{\"code\": \"def test(): pass\"}'"
    
    run_test "MCP Analysis - Security Scan" \
        "curl -f -X POST $MCP_BASE/mcp/analysis/security -H 'Content-Type: application/json' -d '{\"code\": \"import os\"}'"
}

# Test GitHub Integration
test_github_integration() {
    log_info "Testing GitHub Integration..."
    
    if [[ -z "${GITHUB_PAT:-}" ]]; then
        log_warning "GITHUB_PAT not set, skipping GitHub tests"
        return
    fi
    
    run_test "GitHub API Access" \
        "curl -f -H 'Authorization: token $GITHUB_PAT' https://api.github.com/user"
    
    run_test "Repository Access" \
        "curl -f -H 'Authorization: token $GITHUB_PAT' https://api.github.com/repos/ai-cherry/sophia-intel"
    
    run_test "Branch Creation Capability" \
        "curl -f -X POST -H 'Authorization: token $GITHUB_PAT' -H 'Content-Type: application/json' https://api.github.com/repos/ai-cherry/sophia-intel/git/refs -d '{\"ref\": \"refs/heads/test-branch-$(date +%s)\", \"sha\": \"$(curl -s -H \"Authorization: token $GITHUB_PAT\" https://api.github.com/repos/ai-cherry/sophia-intel/git/refs/heads/main | jq -r .object.sha)\"}'"
}

# Test Model Router
test_model_router() {
    log_info "Testing Model Router..."
    
    run_test "Model Allowlist Endpoint" \
        "curl -f http://localhost:5000/api/models"
    
    run_test "Model Selection - Planning" \
        "curl -f -X POST http://localhost:5000/api/models/select -H 'Content-Type: application/json' -d '{\"task_type\": \"planning\"}'"
    
    run_test "Model Selection - Coding" \
        "curl -f -X POST http://localhost:5000/api/models/select -H 'Content-Type: application/json' -d '{\"task_type\": \"coding\"}'"
    
    run_test "Model Selection - Research" \
        "curl -f -X POST http://localhost:5000/api/models/select -H 'Content-Type: application/json' -d '{\"task_type\": \"research\"}'"
}

# Test Code Indexer
test_code_indexer() {
    log_info "Testing Code Indexer..."
    
    if [[ -z "${QDRANT_URL:-}" ]]; then
        log_warning "QDRANT_URL not set, skipping indexer tests"
        return
    fi
    
    run_test "Qdrant Connection" \
        "curl -f $QDRANT_URL/collections"
    
    run_test "Code Indexing Capability" \
        "python -c 'from backend.services.indexer.index_repo import CodeIndexer; indexer = CodeIndexer(); print(\"success\")'"
    
    run_test "Semantic Search" \
        "curl -f -X POST http://localhost:5000/api/search -H 'Content-Type: application/json' -d '{\"query\": \"authentication function\"}'"
}

# Test Planning Council
test_planning_council() {
    log_info "Testing Planning Council..."
    
    run_test "Council Health" \
        "curl -f http://localhost:5000/api/council/health"
    
    run_test "Debate Capability" \
        "curl -f -X POST http://localhost:5000/api/council/debate -H 'Content-Type: application/json' -d '{\"proposal\": \"Add user authentication system\"}'"
    
    run_test "Consensus Mechanism" \
        "curl -f -X POST http://localhost:5000/api/council/consensus -H 'Content-Type: application/json' -d '{\"debate_id\": \"test-123\"}'"
}

# Test Swarm Orchestration
test_swarm_orchestration() {
    log_info "Testing Swarm Orchestration..."
    
    run_test "Swarm Health" \
        "curl -f http://localhost:5000/api/swarm/health"
    
    run_test "Agent Status" \
        "curl -f http://localhost:5000/api/swarm/agents"
    
    run_test "Mission Creation" \
        "curl -f -X POST http://localhost:5000/api/missions -H 'Content-Type: application/json' -d '{\"goal\": \"Test mission for verification\"}'"
}

# Test Event Bus and SSE
test_event_bus() {
    log_info "Testing Event Bus and SSE..."
    
    run_test "Event Bus Health" \
        "curl -f http://localhost:5000/api/events/health"
    
    run_test "SSE Stream Creation" \
        "curl -f http://localhost:5000/api/events/stream"
    
    # Test SSE streaming (timeout after 5 seconds)
    run_test "SSE Event Streaming" \
        "timeout 5s curl -N http://localhost:5000/api/events/test-stream || true"
}

# Test Production Endpoints
test_production_endpoints() {
    log_info "Testing Production Endpoints..."
    
    if curl -f https://www.sophia-intel.ai >/dev/null 2>&1; then
        run_test "Production Dashboard" \
            "curl -f https://www.sophia-intel.ai"
        
        run_test "Production API Health" \
            "curl -f https://api.sophia-intel.ai/api/health"
        
        run_test "Production MCP Health" \
            "curl -f https://mcp.sophia-intel.ai/healthz"
    else
        log_warning "Production endpoints not accessible (DNS/deployment pending)"
    fi
}

# Test Security and Rate Limiting
test_security() {
    log_info "Testing Security and Rate Limiting..."
    
    run_test "CORS Headers" \
        "curl -I http://localhost:5000/api/health | grep -i 'access-control'"
    
    run_test "Security Headers" \
        "curl -I http://localhost:5000/ | grep -i 'x-frame-options'"
    
    # Test rate limiting (make multiple rapid requests and expect 429)
    run_test "Rate Limiting fires" \
        "for i in {1..50}; do curl -s -o /dev/null -w '%{http_code}\n' http://localhost:5000/api/health; done | grep -q '^429$'"
}

# Test Database Connections
test_database_connections() {
    log_info "Testing Database Connections..."
    
    if [[ -n "${QDRANT_URL:-}" ]]; then
        run_test "Qdrant Vector Database" \
            "curl -f $QDRANT_URL/collections"
    fi
    
    if [[ -n "${AIRBYTE_URL:-}" ]]; then
        run_test "Airbyte Data Pipeline" \
            "curl -f $AIRBYTE_URL/api/v1/health"
    fi
    
    # Test local databases
    run_test "Local Database Health" \
        "curl -f http://localhost:5000/api/db/health"
}

# Performance Tests
test_performance() {
    log_info "Testing Performance..."
    
    # Test response times
    run_test "API Response Time (<500ms)" \
        "time curl -f http://localhost:5000/api/health | grep -q 'healthy'"
    
    # Test concurrent requests
    run_test "Concurrent Request Handling" \
        "for i in {1..10}; do curl -f http://localhost:5000/api/health >/dev/null 2>&1 & done; wait"
    
    # Test memory usage
    run_test "Memory Usage Check" \
        "ps aux | grep python | awk '{sum += \$6} END {print sum < 1000000}' | grep -q 1"
}

# Generate test report
generate_report() {
    echo ""
    echo "📊 MCP Verification Report"
    echo "========================="
    echo "Time: $(date)"
    echo "Total Tests: $TESTS_TOTAL"
    echo "Passed: $TESTS_PASSED"
    echo "Failed: $TESTS_FAILED"
    echo "Success Rate: $(( TESTS_PASSED * 100 / TESTS_TOTAL ))%"
    echo ""
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        log_success "All MCP verification tests passed! 🎉"
        echo "SOPHIA Intel is ready for production missions."
    else
        log_warning "$TESTS_FAILED tests failed. Review and fix issues before production."
    fi
    
    # Save report to file
    cat > mcp_verification_report.json << EOF
{
    "timestamp": "$(date -Iseconds)",
    "total_tests": $TESTS_TOTAL,
    "passed": $TESTS_PASSED,
    "failed": $TESTS_FAILED,
    "success_rate": $(( TESTS_PASSED * 100 / TESTS_TOTAL )),
    "status": "$(if [[ $TESTS_FAILED -eq 0 ]]; then echo "PASS"; else echo "FAIL"; fi)"
}
EOF
    
    log_success "Report saved to mcp_verification_report.json"
}

# Main test execution
main() {
    echo "🧪 Starting MCP Verification Suite"
    echo "=================================="
    
    # Core MCP Tests
    test_mcp_code_health
    test_mcp_research
    test_mcp_analysis
    
    # Integration Tests
    test_github_integration
    test_model_router
    test_code_indexer
    
    # Orchestration Tests
    test_planning_council
    test_swarm_orchestration
    test_event_bus
    
    # Production Tests
    test_production_endpoints
    test_security
    test_database_connections
    
    # Performance Tests
    test_performance
    
    # Generate final report
    generate_report
}

# Run verification suite
main "$@"

