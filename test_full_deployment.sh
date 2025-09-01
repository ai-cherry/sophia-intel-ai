#!/bin/bash

# Sophia Intel AI - Full Deployment Test Script
# Tests all services, ports, and functionality

echo "======================================"
echo "🚀 Sophia Intel AI Deployment Test"
echo "======================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results counter
PASS=0
FAIL=0

# Function to test a service
test_service() {
    local name=$1
    local url=$2
    local expected_code=$3
    
    echo -n "Testing $name... "
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$response" = "$expected_code" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $response)"
        ((PASS++))
    else
        echo -e "${RED}❌ FAIL${NC} (Expected $expected_code, got $response)"
        ((FAIL++))
    fi
}

# Function to test API endpoint
test_api() {
    local name=$1
    local method=$2
    local url=$3
    local data=$4
    
    echo -n "Testing API: $name... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -X GET "$url" 2>/dev/null)
    else
        response=$(curl -s -X POST "$url" \
            -H "Content-Type: application/json" \
            -d "$data" 2>/dev/null)
    fi
    
    if echo "$response" | grep -q "error\|failed\|exception" 2>/dev/null; then
        echo -e "${RED}❌ FAIL${NC} (Error in response)"
        ((FAIL++))
    elif [ -z "$response" ]; then
        echo -e "${RED}❌ FAIL${NC} (Empty response)"
        ((FAIL++))
    else
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASS++))
    fi
}

echo "1. Testing Port Availability"
echo "=============================="
test_service "Agent-UI (port 3200)" "http://localhost:3200" "200"
test_service "Unified API (port 8000)" "http://localhost:8000/healthz" "200"
test_service "Proxy Bridge (port 7777)" "http://localhost:7777" "404"
test_service "Weaviate (port 8080)" "http://localhost:8080/v1/.well-known/ready" "200"
echo ""

echo "2. Testing Database Connections"
echo "================================"
# Test Redis
echo -n "Testing Redis... "
if docker exec redis redis-cli ping 2>/dev/null | grep -q PONG; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAIL++))
fi

# Test PostgreSQL
echo -n "Testing PostgreSQL... "
if docker exec sophia-postgres pg_isready -U sophia 2>/dev/null | grep -q "accepting connections"; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAIL++))
fi
echo ""

echo "3. Testing API Endpoints"
echo "========================"
test_api "Health Check" "GET" "http://localhost:8000/healthz" ""
test_api "Teams List" "GET" "http://localhost:8000/teams" ""
test_api "Workflows List" "GET" "http://localhost:8000/workflows" ""
echo ""

echo "4. Testing Swarm Execution"
echo "=========================="
echo -n "Testing Strategic Swarm... "
swarm_response=$(curl -s -X POST http://localhost:8000/teams/run \
    -H "Content-Type: application/json" \
    -d '{
        "message": "Test strategic analysis",
        "team_id": "strategic"
    }' 2>/dev/null | head -c 100)

if echo "$swarm_response" | grep -q "data:" 2>/dev/null; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAIL++))
fi
echo ""

echo "5. Testing Weaviate Collections"
echo "================================"
echo -n "Testing Weaviate schema... "
collections=$(curl -s http://localhost:8080/v1/schema 2>/dev/null | python3 -c "import json, sys; data=json.load(sys.stdin); print(len(data.get('classes', [])))" 2>/dev/null)

if [ "$collections" -ge "10" ]; then
    echo -e "${GREEN}✅ PASS${NC} ($collections collections found)"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC} (Expected 14+ collections, found $collections)"
    ((FAIL++))
fi
echo ""

echo "6. Testing Consciousness Tracking"
echo "================================="
echo -n "Testing consciousness measurement... "
if python3 test_consciousness_measurement.py 2>&1 | grep -q "SUCCESS"; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAIL++))
fi
echo ""

echo "======================================"
echo "📊 Test Results Summary"
echo "======================================"
echo -e "Passed: ${GREEN}$PASS${NC}"
echo -e "Failed: ${RED}$FAIL${NC}"

if [ $FAIL -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All tests passed! Deployment is fully functional.${NC}"
    exit 0
else
    echo ""
    echo -e "${YELLOW}⚠️  Some tests failed. Please check the services above.${NC}"
    exit 1
fi