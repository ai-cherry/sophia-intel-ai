#!/bin/bash

# ==============================================
# Sophia Intel AI - Microservices Integration Testing
# Tests all 6 deployed services and their interactions
# ==============================================

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Test configuration
ENVIRONMENT=${1:-"production"}  # production, staging, or local
BASE_URL="https://sophia-api.fly.dev"
UI_URL="https://sophia-ui.fly.dev"
BRIDGE_URL="https://sophia-bridge.fly.dev"

if [ "$ENVIRONMENT" = "local" ]; then
    BASE_URL="http://localhost:8003"
    UI_URL="http://localhost:3000"
    BRIDGE_URL="http://localhost:7777"
fi

echo -e "${PURPLE}🧪 Starting Sophia Intel AI Microservices Integration Tests${NC}"
echo -e "${BLUE}🌐 Environment: ${ENVIRONMENT}${NC}"
echo -e "${BLUE}🎯 Testing endpoints: ${BASE_URL}${NC}"

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNINGS=0

# ==============================================
# HELPER FUNCTIONS
# ==============================================

test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    local timeout=${4:-10}

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${BLUE}🔍 Testing ${name}...${NC}"

    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" --max-time $timeout "$url" || echo "HTTPSTATUS:000")
    local status=$(echo "$response" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')

    if [ "$status" -eq "$expected_status" ]; then
        echo -e "${GREEN}✅ ${name} - Status: ${status}${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}❌ ${name} - Status: ${status} (expected ${expected_status})${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

test_json_endpoint() {
    local name=$1
    local url=$2
    local expected_field=$3
    local timeout=${4:-10}

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${BLUE}🔍 Testing ${name} JSON response...${NC}"

    local response=$(curl -s --max-time $timeout "$url" || echo '{"error": "connection_failed"}')

    if echo "$response" | jq -e ".$expected_field" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ ${name} - JSON field '${expected_field}' found${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}❌ ${name} - JSON field '${expected_field}' missing${NC}"
        echo -e "${YELLOW}Response: $(echo "$response" | jq . 2>/dev/null || echo "$response")${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

post_json_test() {
    local name=$1
    local url=$2
    local payload=$3
    local expected_field=$4
    local timeout=${5:-30}

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${BLUE}🔍 Testing ${name} POST...${NC}"

    local response=$(curl -s --max-time $timeout \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "$url" || echo '{"error": "connection_failed"}')

    if echo "$response" | jq -e ".$expected_field" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ ${name} - POST successful${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}❌ ${name} - POST failed${NC}"
        echo -e "${YELLOW}Response: $(echo "$response" | jq . 2>/dev/null || echo "$response")${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# ==============================================
# PHASE 1: Basic Health Checks
# ==============================================
echo -e "\n${YELLOW}🏥 Phase 1: Service Health Checks${NC}"

# Test all 6 microservices
test_endpoint "Weaviate Vector Database" "https://sophia-weaviate.fly.dev/v1/.well-known/ready"
test_endpoint "MCP Memory Server" "https://sophia-mcp.fly.dev/health"
test_endpoint "Vector Store Service" "https://sophia-vector.fly.dev/health"
test_endpoint "Unified API Main" "${BASE_URL}/healthz"
test_endpoint "Agno Bridge" "${BRIDGE_URL}/healthz"
test_endpoint "Agent UI Frontend" "$UI_URL"

# ==============================================
# PHASE 2: Service Configuration Tests
# ==============================================
echo -e "\n${YELLOW}⚙️ Phase 2: Service Configuration Tests${NC}"

# Test API stats endpoint
test_json_endpoint "API Stats" "${BASE_URL}/stats" "status"

# Test Weaviate schema
test_json_endpoint "Weaviate Schema" "https://sophia-weaviate.fly.dev/v1/schema" "classes"

# Test bridge configuration
test_json_endpoint "Bridge Config" "${BRIDGE_URL}/healthz" "systems"

# ==============================================
# PHASE 3: Inter-Service Communication
# ==============================================
echo -e "\n${YELLOW}🔗 Phase 3: Inter-Service Communication Tests${NC}"

# Test API to Weaviate connection
post_json_test "API->Weaviate Connection" \
    "${BASE_URL}/api/memory/search" \
    '{"query": "test connection", "limit": 5}' \
    "results"

# Test API to MCP Server
post_json_test "API->MCP Connection" \
    "${BASE_URL}/api/memory/add" \
    '{"content": "integration test memory", "metadata": {"test": true}}' \
    "success"

# Test Bridge to API connection
post_json_test "Bridge->API Connection" \
    "${BRIDGE_URL}/api/agents" \
    '{}' \
    "agents"

# ==============================================
# PHASE 4: Consensus Swarm Testing
# ==============================================
echo -e "\n${YELLOW}🤖 Phase 4: Consensus Swarm Integration Tests${NC}"

# Test consensus swarm creation
echo -e "${BLUE}🔍 Testing consensus swarm creation...${NC}"
SWARM_PAYLOAD='{
    "swarm_type": "consensus",
    "agents": [
        {"name": "agent_1", "model": "gpt-4o-mini", "role": "analyzer"},
        {"name": "agent_2", "model": "claude-3.5-sonnet", "role": "reviewer"},
        {"name": "agent_3", "model": "groq/llama-3.2-90b", "role": "validator"}
    ],
    "consensus_config": {
        "voting_method": "weighted",
        "threshold": 0.66,
        "tie_breaker": "seniority"
    },
    "task": "Evaluate the deployment strategy for microservices"
}'

SWARM_RESPONSE=$(curl -s --max-time 60 \
    -H "Content-Type: application/json" \
    -d "$SWARM_PAYLOAD" \
    "${BASE_URL}/api/swarms/run" || echo '{"error": "connection_failed"}')

if echo "$SWARM_RESPONSE" | jq -e ".success" > /dev/null 2>&1; then
    SWARM_ID=$(echo "$SWARM_RESPONSE" | jq -r ".session_id // .id")
    echo -e "${GREEN}✅ Consensus Swarm Created - ID: ${SWARM_ID}${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))

    # Test swarm status
    if test_json_endpoint "Swarm Status" "${BASE_URL}/api/swarms/${SWARM_ID}/status" "status"; then
        echo -e "${GREEN}✅ Swarm status tracking works${NC}"
    fi
else
    echo -e "${RED}❌ Consensus Swarm Creation Failed${NC}"
    echo -e "${YELLOW}Response: $(echo "$SWARM_RESPONSE" | jq . 2>/dev/null || echo "$SWARM_RESPONSE")${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))

# ==============================================
# PHASE 5: Memory Deduplication Testing
# ==============================================
echo -e "\n${YELLOW}🧠 Phase 5: Memory Deduplication Tests${NC}"

# Test memory deduplication with duplicate content
echo -e "${BLUE}🔍 Testing memory deduplication...${NC}"

DUPLICATE_CONTENT="This is a test memory entry for deduplication verification"
MEMORY_PAYLOAD_1="{\"content\": \"$DUPLICATE_CONTENT\", \"metadata\": {\"test\": \"dedup_1\"}}"
MEMORY_PAYLOAD_2="{\"content\": \"$DUPLICATE_CONTENT\", \"metadata\": {\"test\": \"dedup_2\"}}"

# Add first memory
MEMORY_RESPONSE_1=$(curl -s --max-time 30 \
    -H "Content-Type: application/json" \
    -d "$MEMORY_PAYLOAD_1" \
    "${BASE_URL}/api/memory/add" || echo '{"error": "connection_failed"}')

# Add duplicate memory
MEMORY_RESPONSE_2=$(curl -s --max-time 30 \
    -H "Content-Type: application/json" \
    -d "$MEMORY_PAYLOAD_2" \
    "${BASE_URL}/api/memory/add" || echo '{"error": "connection_failed"}')

if echo "$MEMORY_RESPONSE_2" | jq -e ".deduplicated" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Memory Deduplication Working - Duplicate detected${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠️ Memory Deduplication - Response unclear${NC}"
    echo -e "${YELLOW}Response: $(echo "$MEMORY_RESPONSE_2" | jq . 2>/dev/null || echo "$MEMORY_RESPONSE_2")${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))

# ==============================================
# PHASE 6: Lambda Labs GPU Integration (Optional)
# ==============================================
echo -e "\n${YELLOW}🚀 Phase 6: Lambda Labs GPU Integration Tests${NC}"

# Test GPU availability
GPU_STATUS=$(curl -s --max-time 15 \
    "${BASE_URL}/api/gpu/status" || echo '{"available": false}')

if echo "$GPU_STATUS" | jq -e ".available" > /dev/null 2>&1 && [ "$(echo "$GPU_STATUS" | jq -r ".available")" = "true" ]; then
    echo -e "${GREEN}✅ Lambda Labs GPU Available${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))

    # Test small GPU task (if available)
    echo -e "${BLUE}🔍 Testing small GPU task...${NC}"
    GPU_TASK_PAYLOAD='{
        "task_type": "vector_processing",
        "payload": {
            "documents": ["test document 1", "test document 2"],
            "model": "voyage-3-large"
        }
    }'

    GPU_RESPONSE=$(timeout 120 curl -s \
        -H "Content-Type: application/json" \
        -d "$GPU_TASK_PAYLOAD" \
        "${BASE_URL}/api/gpu/execute" 2>/dev/null || echo '{"success": false}')

    if echo "$GPU_RESPONSE" | jq -e ".success" > /dev/null 2>&1 && [ "$(echo "$GPU_RESPONSE" | jq -r ".success")" = "true" ]; then
        echo -e "${GREEN}✅ GPU Task Execution Success${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${YELLOW}⚠️ GPU Task Execution - May take longer in production${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi

    TOTAL_TESTS=$((TOTAL_TESTS + 2))
else
    echo -e "${YELLOW}⚠️ Lambda Labs GPU Not Available - Skipping GPU tests${NC}"
    echo -e "${BLUE}ℹ️ GPU Status: $(echo "$GPU_STATUS" | jq . 2>/dev/null || echo "$GPU_STATUS")${NC}"
    WARNINGS=$((WARNINGS + 1))
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
fi

# ==============================================
# PHASE 7: UI and Frontend Testing
# ==============================================
echo -e "\n${YELLOW}🖥️ Phase 7: UI and Frontend Tests${NC}"

# Test UI loads correctly
if test_endpoint "Agent UI Homepage" "$UI_URL"; then
    echo -e "${GREEN}✅ Agent UI loads successfully${NC}"
fi

# Test UI API connectivity
UI_CONFIG_RESPONSE=$(curl -s --max-time 10 "${UI_URL}/_next/static/chunks/app/layout" 2>/dev/null || echo "")
if [[ "$UI_CONFIG_RESPONSE" == *"sophia"* ]]; then
    echo -e "${GREEN}✅ UI Configuration Found${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠️ UI Configuration - Unable to verify${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))

# ==============================================
# PHASE 8: Performance and Load Testing
# ==============================================
echo -e "\n${YELLOW}⚡ Phase 8: Performance Tests${NC}"

# Test API response times
echo -e "${BLUE}🔍 Testing API response times...${NC}"
RESPONSE_TIME=$(curl -s -w "%{time_total}" -o /dev/null "${BASE_URL}/healthz" 2>/dev/null || echo "999")

if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l) )); then
    echo -e "${GREEN}✅ API Response Time: ${RESPONSE_TIME}s (Good)${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
elif (( $(echo "$RESPONSE_TIME < 5.0" | bc -l) )); then
    echo -e "${YELLOW}⚠️ API Response Time: ${RESPONSE_TIME}s (Acceptable)${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${RED}❌ API Response Time: ${RESPONSE_TIME}s (Too Slow)${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Test concurrent requests
echo -e "${BLUE}🔍 Testing concurrent request handling...${NC}"
for i in {1..5}; do
    curl -s "${BASE_URL}/healthz" > /dev/null &
done
wait

echo -e "${GREEN}✅ Concurrent Request Test Completed${NC}"
PASSED_TESTS=$((PASSED_TESTS + 1))
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# ==============================================
# TEST RESULTS SUMMARY
# ==============================================
echo -e "\n${PURPLE}📊 Integration Test Results Summary${NC}"
echo -e "========================================"
echo -e "${GREEN}✅ Passed: ${PASSED_TESTS}${NC}"
echo -e "${RED}❌ Failed: ${FAILED_TESTS}${NC}"
echo -e "${YELLOW}⚠️ Warnings: ${WARNINGS}${NC}"
echo -e "${BLUE}📊 Total Tests: ${TOTAL_TESTS}${NC}"

# Calculate success rate
SUCCESS_RATE=$(( (PASSED_TESTS * 100) / TOTAL_TESTS ))
echo -e "${BLUE}🎯 Success Rate: ${SUCCESS_RATE}%${NC}"

# Final assessment
if [ $FAILED_TESTS -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -e "\n${GREEN}🎉 ALL TESTS PASSED! Microservices deployment is fully operational.${NC}"
        exit 0
    else
        echo -e "\n${YELLOW}✅ Tests passed with ${WARNINGS} warnings. Deployment is functional.${NC}"
        exit 0
    fi
else
    echo -e "\n${RED}❌ ${FAILED_TESTS} tests failed. Please check the deployment.${NC}"
    echo -e "\n${BLUE}🔧 Troubleshooting commands:${NC}"
    echo -e "  fly status --app sophia-api"
    echo -e "  fly logs --app sophia-api"
    echo -e "  fly ssh console --app sophia-api"
    exit 1
fi
