#!/bin/bash
# Comprehensive System Test Suite
# Tests all components per the updated instructions

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "======================================"
echo "Sophia Intel AI - Comprehensive Tests"
echo "======================================"
echo ""

PASSED=0
FAILED=0

# Test function
test_command() {
    local name="$1"
    local cmd="$2"
    echo -n "Testing $name... "
    if eval "$cmd" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((FAILED++))
    fi
}

# 1. Test master control script
echo "=== Master Control Script (sophia) ==="
test_command "sophia status" "./sophia status"
# Skip full test suite - it's tested separately
echo ""

# 2. Test dev wrapper
echo "=== Dev CLI Wrapper ==="
test_command "dev status" "./dev status"
test_command "dev opencode version" "./dev opencode --version"
echo ""

# 3. Test service endpoints
echo "=== Service Endpoints ==="
test_command "LiteLLM API" "curl -sf http://localhost:4000/v1/models -H 'Authorization: Bearer sk-litellm-master-2025' | jq -e '.data | length > 0'"
test_command "MCP Memory health" "curl -sf http://localhost:8081/health"
test_command "MCP Memory sessions" "curl -sf http://localhost:8081/sessions"
test_command "MCP Filesystem health" "curl -sf http://localhost:8082/health"
test_command "MCP Git health" "curl -sf http://localhost:8084/health"
test_command "Redis ping" "redis-cli -p 6379 ping"
echo ""

# 4. Test environment
echo "=== Environment Configuration ==="
test_command ".env.master exists" "[ -f .env.master ]"
test_command ".env.master permissions" "[ $(stat -f %Lp .env.master) -eq 600 ]"
test_command "MCP_DEV_BYPASS set" "grep -q '^MCP_DEV_BYPASS=true' .env.master"
test_command "Config symlink" "[ -L ~/.config/sophia/env ]"
echo ""

# 5. Test Cursor MCP config
echo "=== Cursor Integration ==="
test_command "Cursor MCP config exists" "[ -f .cursor/mcp.json ]"
test_command "Cursor MCP valid JSON" "jq -e . .cursor/mcp.json"
echo ""

# 6. Test AI command routing (basic check)
echo "=== AI Command Routing ==="
test_command "AI help accessible" "./dev ai --help 2>&1 | grep -q 'claude'"
echo ""

# 7. Test paths and binaries
echo "=== Paths and Binaries ==="
test_command "OpenCode in PATH" "command -v opencode"
test_command "Python3 available" "command -v python3"
test_command "LiteLLM available" "command -v litellm"
echo ""

# 8. Test memory operations
echo "=== MCP Memory Operations ==="
TEST_SESSION="test-comprehensive-$(date +%s)"
test_command "Memory write" "curl -sf -X POST http://localhost:8081/sessions/$TEST_SESSION/memory -H 'Content-Type: application/json' -d '{\"content\":\"test\",\"role\":\"user\"}'"
test_command "Memory read" "curl -sf http://localhost:8081/sessions/$TEST_SESSION/memory | jq -e '.session_id'"
test_command "Memory cleanup" "curl -sf -X DELETE http://localhost:8081/sessions/$TEST_SESSION/memory"
echo ""

# Summary
echo "======================================"
echo "TEST RESULTS"
echo "======================================"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed successfully!${NC}"
    echo "System is fully operational per START_HERE_2025.md"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed${NC}"
    echo "Please check the failed components"
    exit 1
fi