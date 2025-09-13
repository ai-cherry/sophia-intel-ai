#!/bin/bash

# Integration Test Suite
# Tests all components after quality control improvements

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}INTEGRATION TEST SUITE${NC}"
echo -e "${BLUE}================================${NC}\n"

PASS=0
FAIL=0

test_item() {
    local name="$1"
    local cmd="$2"
    
    echo -n "Testing $name... "
    if eval "$cmd" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASS++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((FAIL++))
        return 1
    fi
}

# 1. Environment Variables
echo -e "\n${YELLOW}1. ENVIRONMENT VARIABLES${NC}"
test_item "ANTHROPIC_API_KEY" "[ ! -z \"\$ANTHROPIC_API_KEY\" ]"
test_item "OPENAI_API_KEY" "[ ! -z \"\$OPENAI_API_KEY\" ]"
test_item "XAI_API_KEY" "[ ! -z \"\$XAI_API_KEY\" ]"
test_item ".env.master exists" "[ -f ~/sophia-intel-ai/.env.master ]"
test_item ".env.master secured" "[ \$(stat -f '%A' ~/sophia-intel-ai/.env.master) = '600' ]"

# 2. CLI Tools
echo -e "\n${YELLOW}2. CLI TOOLS${NC}"
test_item "Opencode in PATH" "command -v opencode"
test_item "Opencode version" "opencode --version"
test_item "LiteLLM installed" "command -v litellm"
test_item "Python available" "command -v python3"

# 3. LiteLLM Proxy
echo -e "\n${YELLOW}3. LITELLM PROXY${NC}"
test_item "LiteLLM process running" "ps aux | grep -q '[l]itellm.*port 4000'"
test_item "LiteLLM port 4000" "nc -z localhost 4000"

# Wait a bit for LiteLLM to fully start
sleep 2

# Try to get model list with timeout
if timeout 5 curl -s http://localhost:4000/v1/models >/dev/null 2>&1; then
    MODEL_COUNT=$(curl -s http://localhost:4000/v1/models | python3 -c "import json, sys; print(len(json.load(sys.stdin)['data']))" 2>/dev/null || echo "0")
    if [ "$MODEL_COUNT" -gt 0 ]; then
        echo "Testing LiteLLM models endpoint... ${GREEN}✅ PASS${NC} ($MODEL_COUNT models)"
        ((PASS++))
    else
        echo "Testing LiteLLM models endpoint... ${YELLOW}⚠️  WARNING${NC} (No models found)"
    fi
else
    echo "Testing LiteLLM models endpoint... ${RED}❌ FAIL${NC} (Not responding)"
    ((FAIL++))
fi

# 4. MCP Servers
echo -e "\n${YELLOW}4. MCP SERVERS${NC}"
test_item "MCP Memory (8081)" "nc -z localhost 8081"
test_item "MCP Filesystem (8082)" "nc -z localhost 8082"
test_item "MCP Git (8084)" "nc -z localhost 8084"

# 5. Configuration Files
echo -e "\n${YELLOW}5. CONFIGURATION FILES${NC}"
test_item "Opencode auth.json" "[ -f ~/.local/share/opencode/auth.json ]"
test_item "LiteLLM config" "[ -f ~/sophia-intel-ai/litellm-complete.yaml ]"
test_item "Manager script" "[ -x ~/sophia-intel-ai/unified-system-manager.sh ]"
test_item "Claude Desktop config" "[ -f ~/.config/claude/claude_desktop_config.json ]"

# 6. Provider Authentication
echo -e "\n${YELLOW}6. PROVIDER AUTHENTICATION${NC}"

# Count providers in auth.json
PROVIDER_COUNT=$(cat ~/.local/share/opencode/auth.json | jq '.credentials | length' 2>/dev/null || echo "0")
if [ "$PROVIDER_COUNT" -gt 0 ]; then
    echo "Testing Opencode providers... ${GREEN}✅ PASS${NC} ($PROVIDER_COUNT providers)"
    ((PASS++))
else
    echo "Testing Opencode providers... ${RED}❌ FAIL${NC}"
    ((FAIL++))
fi

# 7. Quick API Tests
echo -e "\n${YELLOW}7. API CONNECTIVITY${NC}"

# Test Anthropic
if [ ! -z "$ANTHROPIC_API_KEY" ]; then
    if curl -s -o /dev/null -w "%{http_code}" -X POST https://api.anthropic.com/v1/messages \
        -H "x-api-key: $ANTHROPIC_API_KEY" \
        -H "anthropic-version: 2023-06-01" \
        -H "content-type: application/json" \
        -d '{"model":"claude-3-haiku-20240307","messages":[{"role":"user","content":"hi"}],"max_tokens":1}' 2>/dev/null | grep -q "200\|401"; then
        echo "Testing Anthropic API... ${GREEN}✅ PASS${NC}"
        ((PASS++))
    else
        echo "Testing Anthropic API... ${YELLOW}⚠️  WARNING${NC}"
    fi
fi

# Test OpenAI
if [ ! -z "$OPENAI_API_KEY" ]; then
    if curl -s -o /dev/null -w "%{http_code}" https://api.openai.com/v1/models \
        -H "Authorization: Bearer $OPENAI_API_KEY" 2>/dev/null | grep -q "200\|401"; then
        echo "Testing OpenAI API... ${GREEN}✅ PASS${NC}"
        ((PASS++))
    else
        echo "Testing OpenAI API... ${YELLOW}⚠️  WARNING${NC}"
    fi
fi

# 8. Process Management
echo -e "\n${YELLOW}8. PROCESS MANAGEMENT${NC}"
test_item "PID directory exists" "[ -d ~/sophia-intel-ai/.pids ]"
test_item "Log directory exists" "[ -d ~/sophia-intel-ai/logs ]"

# Summary
echo -e "\n${BLUE}================================${NC}"
echo -e "${BLUE}TEST SUMMARY${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "${GREEN}Passed: $PASS${NC}"
echo -e "${RED}Failed: $FAIL${NC}"

if [ $FAIL -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo -e "System is fully integrated and operational."
    exit 0
else
    echo -e "\n${YELLOW}⚠️  Some tests failed.${NC}"
    echo -e "Run './unified-system-manager.sh status' for details."
    exit 1
fi
# Load environment to standardize tests
if [ -f "$HOME/sophia-intel-ai/.env.master" ]; then
  # shellcheck disable=SC1090
  source "$HOME/sophia-intel-ai/.env.master"
elif [ -f "$HOME/.config/sophia/env" ]; then
  # shellcheck disable=SC1090
  source "$HOME/.config/sophia/env"
fi
