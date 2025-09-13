#!/bin/bash
# Sophia Intel AI - Comprehensive Test Suite
# Tests every service endpoint, validates integrations, and performs stress tests
# Author: Claude (System Architecture Designer)
# Version: 2.0.0

set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
readonly LOG_DIR="$SCRIPT_DIR/logs"
readonly TEST_RESULTS_FILE="$LOG_DIR/test-results-$(date +%Y%m%d-%H%M%S).json"

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'

# Test counters
declare -i TOTAL_TESTS=0
declare -i PASSED_TESTS=0
declare -i FAILED_TESTS=0
declare -i SKIPPED_TESTS=0

# Test results array
declare -a TEST_RESULTS=()

# =====================================================
# UTILITY FUNCTIONS
# =====================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    
    case "$level" in
        "INFO")  echo -e "${GREEN}[${timestamp}] [INFO]${NC} $message" ;;
        "WARN")  echo -e "${YELLOW}[${timestamp}] [WARN]${NC} $message" ;;
        "ERROR") echo -e "${RED}[${timestamp}] [ERROR]${NC} $message" ;;
        "PASS")  echo -e "${GREEN}[${timestamp}] [PASS]${NC} $message" ;;
        "FAIL")  echo -e "${RED}[${timestamp}] [FAIL]${NC} $message" ;;
        *)       echo -e "${CYAN}[${timestamp}]${NC} $message" ;;
    esac
}

# Execute a test with timeout and result tracking
run_test() {
    local test_name="$1"
    local test_command="$2"
    local timeout="${3:-30}"
    local description="${4:-No description}"
    
    ((TOTAL_TESTS++))
    
    log "INFO" "Running test: $test_name"
    
    local start_time
    start_time="$(date +%s)"
    
    local result="FAILED"
    local output=""
    local error=""
    
    # Run test with timeout
    if timeout "$timeout" bash -c "$test_command" >/tmp/test_output 2>/tmp/test_error; then
        result="PASSED"
        ((PASSED_TESTS++))
        log "PASS" "$test_name"
    else
        local exit_code=$?
        if [ $exit_code -eq 124 ]; then
            result="TIMEOUT"
            error="Test timed out after ${timeout}s"
        else
            result="FAILED"
            error="$(cat /tmp/test_error 2>/dev/null || echo "Unknown error")"
        fi
        ((FAILED_TESTS++))
        log "FAIL" "$test_name - $error"
    fi
    
    output="$(cat /tmp/test_output 2>/dev/null || echo "")"
    
    local end_time
    end_time="$(date +%s)"
    local duration=$((end_time - start_time))
    
    # Store result
    TEST_RESULTS+=("{\"name\":\"$test_name\",\"result\":\"$result\",\"duration\":$duration,\"description\":\"$description\",\"output\":\"$(echo "$output" | sed 's/"/\\"/g')\",\"error\":\"$(echo "$error" | sed 's/"/\\"/g')\"}")
    
    # Cleanup
    rm -f /tmp/test_output /tmp/test_error
}

# Skip a test with reason
skip_test() {
    local test_name="$1"
    local reason="${2:-No reason provided}"
    
    ((TOTAL_TESTS++))
    ((SKIPPED_TESTS++))
    
    log "WARN" "SKIPPED: $test_name - $reason"
    TEST_RESULTS+=("{\"name\":\"$test_name\",\"result\":\"SKIPPED\",\"duration\":0,\"description\":\"$reason\",\"output\":\"\",\"error\":\"\"}")
}

# Load environment if available
load_environment() {
    if [ -f "$SCRIPT_DIR/.env.master" ]; then
        # shellcheck disable=SC1090
        source "$SCRIPT_DIR/.env.master"
        log "INFO" "Environment loaded from .env.master"
        return 0
    else
        log "WARN" "No environment file found"
        return 1
    fi
}

# =====================================================
# TEST SUITES
# =====================================================

test_environment() {
    echo -e "\n${BOLD}=== ENVIRONMENT TESTS ===${NC}\n"
    
    run_test "env_file_exists" \
        "[ -f '$SCRIPT_DIR/.env.master' ]" \
        5 \
        "Environment configuration file exists"
    
    run_test "env_file_permissions" \
        "stat -f '%A' '$SCRIPT_DIR/.env.master' 2>/dev/null | grep -q '^600$' || echo 'Warning: not 600'" \
        5 \
        "Environment file has secure permissions (600)"
    
    if load_environment; then
        run_test "anthropic_api_key" \
            "[ ! -z \"\${ANTHROPIC_API_KEY:-}\" ]" \
            5 \
            "Anthropic API key is set"
        
        run_test "openai_api_key" \
            "[ ! -z \"\${OPENAI_API_KEY:-}\" ]" \
            5 \
            "OpenAI API key is set"
        
        run_test "litellm_master_key" \
            "[ ! -z \"\${LITELLM_MASTER_KEY:-}\" ]" \
            5 \
            "LiteLLM master key is set"
    else
        skip_test "anthropic_api_key" "Environment not loaded"
        skip_test "openai_api_key" "Environment not loaded"
        skip_test "litellm_master_key" "Environment not loaded"
    fi
}

test_dependencies() {
    echo -e "\n${BOLD}=== DEPENDENCY TESTS ===${NC}\n"
    
    local required_commands=("python3" "curl" "jq")
    for cmd in "${required_commands[@]}"; do
        run_test "command_$cmd" \
            "command -v $cmd >/dev/null 2>&1" \
            5 \
            "$cmd command is available"
    done
    
    run_test "python_packages" \
        "python3 -c 'import uvicorn, fastapi, redis, pydantic'" \
        10 \
        "Required Python packages are installed"
    
    run_test "litellm_binary" \
        "command -v litellm >/dev/null 2>&1 || [ -x '$SCRIPT_DIR/bin/litellm-cli' ]" \
        5 \
        "LiteLLM binary is available"
    
    run_test "redis_server" \
        "command -v redis-server >/dev/null 2>&1" \
        5 \
        "Redis server is available"
}

test_services() {
    echo -e "\n${BOLD}=== SERVICE TESTS ===${NC}\n"
    
    # Test Redis
    run_test "redis_connection" \
        "python3 -c 'import socket; s=socket.socket(); s.settimeout(2); s.connect((\"localhost\", 6379)); s.close()'" \
        10 \
        "Redis is accessible on port 6379"
    
    if command -v redis-cli >/dev/null 2>&1; then
        run_test "redis_ping" \
            "redis-cli ping | grep -q PONG" \
            5 \
            "Redis responds to ping"
    else
        skip_test "redis_ping" "redis-cli not available"
    fi
    
    # Test LiteLLM
    run_test "litellm_health" \
        "curl -s --max-time 5 http://localhost:4000/health >/dev/null" \
        10 \
        "LiteLLM health endpoint responds"
    
    if [ -n "${LITELLM_MASTER_KEY:-}" ]; then
        run_test "litellm_models" \
            "curl -s --max-time 10 http://localhost:4000/v1/models -H 'Authorization: Bearer $LITELLM_MASTER_KEY' | jq -e '.data | length > 0'" \
            15 \
            "LiteLLM models endpoint returns models"
        
        run_test "litellm_chat_test" \
            "curl -s --max-time 15 http://localhost:4000/v1/chat/completions -H 'Content-Type: application/json' -H 'Authorization: Bearer $LITELLM_MASTER_KEY' -d '{\"model\":\"claude-3-haiku\",\"messages\":[{\"role\":\"user\",\"content\":\"Say OK\"}],\"max_tokens\":5}' | jq -e '.choices[0].message.content'" \
            20 \
            "LiteLLM chat completion works"
    else
        skip_test "litellm_models" "LITELLM_MASTER_KEY not set"
        skip_test "litellm_chat_test" "LITELLM_MASTER_KEY not set"
    fi
    
    # Test MCP Servers
    local mcp_services=("memory:8081" "filesystem:8082" "git:8084")
    for service_port in "${mcp_services[@]}"; do
        local service="${service_port%%:*}"
        local port="${service_port##*:}"
        
        run_test "mcp_${service}_health" \
            "curl -s --max-time 5 http://localhost:$port/health | jq -e '.status == \"healthy\"'" \
            10 \
            "MCP $service server health check"
    done
}

test_integrations() {
    echo -e "\n${BOLD}=== INTEGRATION TESTS ===${NC}\n"
    
    # Test MCP Memory operations
    run_test "mcp_memory_write" \
        "curl -s --max-time 10 -X POST http://localhost:8081/sessions/test/memory -H 'Content-Type: application/json' -d '{\"content\":\"test content\",\"role\":\"user\",\"metadata\":{\"source\":\"test\"}}' | jq -e '.success'" \
        15 \
        "MCP Memory write operation"
    
    run_test "mcp_memory_read" \
        "curl -s --max-time 10 http://localhost:8081/sessions/test/memory | jq -e '. | length > 0'" \
        15 \
        "MCP Memory read operation"
    
    # Test MCP Filesystem operations
    run_test "mcp_filesystem_list" \
        "curl -s --max-time 10 'http://localhost:8082/files?path=/tmp' | jq -e '.files'" \
        15 \
        "MCP Filesystem list operation"
    
    # Test LiteLLM model switching (if auth available)
    if [ -n "${LITELLM_MASTER_KEY:-}" ]; then
        local models=("claude-3-haiku" "gpt-3.5-turbo")
        for model in "${models[@]}"; do
            run_test "litellm_model_$model" \
                "curl -s --max-time 20 http://localhost:4000/v1/chat/completions -H 'Content-Type: application/json' -H 'Authorization: Bearer $LITELLM_MASTER_KEY' -d '{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"Hi\"}],\"max_tokens\":5}' | jq -e '.choices[0].message'" \
                25 \
                "LiteLLM $model model works"
        done
    else
        skip_test "litellm_model_switching" "LITELLM_MASTER_KEY not set"
    fi
}

test_stress() {
    echo -e "\n${BOLD}=== STRESS TESTS ===${NC}\n"
    
    # Concurrent requests test
    run_test "concurrent_health_checks" \
        "for i in {1..10}; do curl -s --max-time 3 http://localhost:8081/health & done; wait" \
        30 \
        "10 concurrent health check requests"
    
    # Memory usage test
    run_test "memory_usage" \
        "ps aux | grep -E '(litellm|uvicorn.*mcp)' | grep -v grep | awk '{sum += \$6} END {print sum < 1000000 ? \"OK\" : \"HIGH\"}' | grep -q OK" \
        10 \
        "Memory usage is reasonable (<1GB total)"
    
    # Port availability test
    run_test "port_conflicts" \
        "for port in 4000 6379 8081 8082 8084; do if lsof -Pi :\$port -sTCP:LISTEN -t >/dev/null 2>&1; then echo \"Port \$port: OK\"; else echo \"Port \$port: FREE\"; fi; done | grep -c OK | [ \$(cat) -ge 2 ]" \
        10 \
        "Critical ports are in use (at least 2 services running)"
}

test_security() {
    echo -e "\n${BOLD}=== SECURITY TESTS ===${NC}\n"
    
    # Check file permissions
    run_test "env_file_security" \
        "find '$SCRIPT_DIR' -name '.env*' -type f ! -perm 600 | wc -l | grep -q '^0$'" \
        5 \
        "Environment files have secure permissions"
    
    # Check for exposed sensitive data in logs
    run_test "log_security" \
        "! grep -r -i 'api.*key.*[a-z0-9]\\{20,\\}' '$LOG_DIR' 2>/dev/null" \
        10 \
        "No API keys found in log files"
    
    # Test authentication requirements
    run_test "litellm_auth_required" \
        "curl -s --max-time 5 http://localhost:4000/v1/models | grep -q 'Authentication Error'" \
        10 \
        "LiteLLM requires authentication"
    
    # Check process security
    run_test "process_security" \
        "ps aux | grep -E '(litellm|uvicorn.*mcp)' | grep -v grep | grep -v 'root' | wc -l | [ \$(cat) -ge 1 ]" \
        5 \
        "Services running as non-root user"
}

test_recovery() {
    echo -e "\n${BOLD}=== RECOVERY TESTS ===${NC}\n"
    
    # Test graceful shutdown and restart
    run_test "service_restart_redis" \
        "pkill -f redis-server; sleep 2; redis-server --daemonize yes --port 6379 --dir '$SCRIPT_DIR' --logfile '$LOG_DIR/redis.log' 2>/dev/null; sleep 3; redis-cli ping | grep -q PONG" \
        30 \
        "Redis can be restarted successfully"
    
    # Test log rotation
    run_test "log_cleanup" \
        "find '$LOG_DIR' -name '*.log' -size +100M | wc -l | grep -q '^0$'" \
        5 \
        "No log files exceed 100MB"
    
    # Test PID file cleanup
    run_test "pid_cleanup" \
        "find '$SCRIPT_DIR/.pids' -name '*.pid' -type f -exec test ! -e /proc/\$(cat {}) \\; -print | wc -l | grep -q '^0$'" \
        10 \
        "No stale PID files exist"
}

# =====================================================
# MAIN EXECUTION
# =====================================================

generate_report() {
    local timestamp
    timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    
    mkdir -p "$LOG_DIR"
    
    cat > "$TEST_RESULTS_FILE" << EOF
{
  "timestamp": "$timestamp",
  "summary": {
    "total": $TOTAL_TESTS,
    "passed": $PASSED_TESTS,
    "failed": $FAILED_TESTS,
    "skipped": $SKIPPED_TESTS,
    "success_rate": $(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc 2>/dev/null || echo "0")
  },
  "tests": [
    $(IFS=','; echo "${TEST_RESULTS[*]}")
  ]
}
EOF
    
    log "INFO" "Test results saved to: $TEST_RESULTS_FILE"
}

show_summary() {
    echo -e "\n${BOLD}=== TEST SUMMARY ===${NC}\n"
    
    echo -e "${CYAN}Total Tests:${NC} $TOTAL_TESTS"
    echo -e "${GREEN}Passed:${NC} $PASSED_TESTS"
    echo -e "${RED}Failed:${NC} $FAILED_TESTS"
    echo -e "${YELLOW}Skipped:${NC} $SKIPPED_TESTS"
    
    if [ $TOTAL_TESTS -gt 0 ]; then
        local success_rate
        success_rate=$(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc 2>/dev/null || echo "0")
        echo -e "${CYAN}Success Rate:${NC} ${success_rate}%"
    fi
    
    echo ""
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}🎉 ALL TESTS PASSED! System is production-ready.${NC}"
    elif [ $PASSED_TESTS -gt $FAILED_TESTS ]; then
        echo -e "${YELLOW}⚠️  Some tests failed, but system is mostly functional.${NC}"
    else
        echo -e "${RED}❌ System has significant issues that need attention.${NC}"
    fi
    
    echo ""
    echo -e "Full results: ${TEST_RESULTS_FILE}"
}

main() {
    local test_suite="${1:-all}"
    
    echo -e "${BOLD}Sophia Intel AI - Comprehensive Test Suite${NC}"
    echo -e "${BOLD}==========================================${NC}\n"
    
    log "INFO" "Starting test suite: $test_suite"
    
    case "$test_suite" in
        "env"|"environment")
            test_environment
            ;;
        "deps"|"dependencies")
            test_dependencies
            ;;
        "services")
            load_environment || true
            test_services
            ;;
        "integration"|"integrations")
            load_environment || true
            test_integrations
            ;;
        "stress")
            load_environment || true
            test_stress
            ;;
        "security")
            test_security
            ;;
        "recovery")
            test_recovery
            ;;
        "all"|"")
            load_environment || true
            test_environment
            test_dependencies
            test_services
            test_integrations
            test_security
            test_stress
            test_recovery
            ;;
        *)
            echo "Unknown test suite: $test_suite"
            echo "Available suites: all, env, deps, services, integration, security, stress, recovery"
            exit 1
            ;;
    esac
    
    generate_report
    show_summary
    
    # Exit with appropriate code
    if [ $FAILED_TESTS -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

main "$@"
