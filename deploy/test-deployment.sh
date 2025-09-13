#!/bin/bash
# Comprehensive deployment testing script
# Tests both local and cloud deployment configurations

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_MODE="${1:-local}"

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# Test helper functions
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "${BLUE}Testing: $test_name${NC}"
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $test_name passed${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ $test_name failed${NC}"
        ((TESTS_FAILED++))
        FAILED_TESTS+=("$test_name")
        return 1
    fi
}

check_port() {
    local port="$1"
    local service="$2"
    
    if nc -z localhost "$port" 2>/dev/null; then
        echo -e "${GREEN}✅ Port $port ($service) is open${NC}"
        return 0
    else
        echo -e "${RED}❌ Port $port ($service) is not accessible${NC}"
        return 1
    fi
}

test_http_endpoint() {
    local url="$1"
    local expected_status="${2:-200}"
    local description="$3"
    
    echo -e "${BLUE}Testing HTTP: $description${NC}"
    
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ $description (HTTP $status_code)${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ $description (Expected: $expected_status, Got: $status_code)${NC}"
        ((TESTS_FAILED++))
        FAILED_TESTS+=("$description")
        return 1
    fi
}

# Test environment setup
test_environment() {
    echo -e "\n${BLUE}=== Testing Environment Setup ===${NC}\n"
    
    # Check Python version
    run_test "Python 3.10+" "python3 -c 'import sys; exit(0 if sys.version_info >= (3,10) else 1)'"
    
    # Check Node.js
    run_test "Node.js installed" "command -v node"
    
    # Check Docker
    run_test "Docker installed" "command -v docker"
    
    # Check environment file
    ENV_FILE="${SOPHIA_ENV_FILE:-$HOME/.config/sophia/env}"
    run_test "Environment file exists" "test -f '$ENV_FILE'"
    
    # Check required environment variables
    if [ -f "$ENV_FILE" ]; then
        export $(grep -v '^#' "$ENV_FILE" | xargs)
        run_test "OPENROUTER_API_KEY set" "test -n '$OPENROUTER_API_KEY'"
    fi
}

# Test local deployment
test_local_deployment() {
    echo -e "\n${BLUE}=== Testing Local Deployment ===${NC}\n"
    
    # Start local deployment
    echo -e "${BLUE}Starting local deployment...${NC}"
    "$SCRIPT_DIR/local-m3.sh" deploy > /dev/null 2>&1 &
    DEPLOY_PID=$!
    
    # Wait for services to start
    echo "Waiting for services to start..."
    sleep 30
    
    # Test port availability
    echo -e "\n${BLUE}Testing port availability:${NC}"
    check_port 6379 "Redis"
    check_port 5432 "PostgreSQL"
    check_port 8081 "MCP Memory"
    check_port 8082 "MCP Filesystem"
    check_port 8084 "MCP Git"
    check_port 8003 "Bridge API"
    check_port 3000 "Agent UI"
    
    # Test health endpoints
    echo -e "\n${BLUE}Testing health endpoints:${NC}"
    test_http_endpoint "http://localhost:8003/health" 200 "Bridge API health"
    test_http_endpoint "http://localhost:8081/health" 200 "MCP Memory health"
    test_http_endpoint "http://localhost:8082/health" 200 "MCP Filesystem health"
    test_http_endpoint "http://localhost:8084/health" 200 "MCP Git health"
    test_http_endpoint "http://localhost:3000" 200 "Agent UI"
    
    # Test API functionality
    echo -e "\n${BLUE}Testing API functionality:${NC}"
    
    # Test Bridge API models endpoint
    run_test "Bridge API /models" "curl -sf http://localhost:8003/models | grep -q 'models'"
    
    # Test MCP Memory session creation
    SESSION_ID=$(uuidgen || echo "test-session-123")
    run_test "MCP Memory session" "curl -sf -X POST http://localhost:8081/sessions/$SESSION_ID"
    
    # Test MCP Filesystem listing
    run_test "MCP Filesystem list" "curl -sf 'http://localhost:8082/files?path=/'"
    
    # Test MCP Git status
    run_test "MCP Git status" "curl -sf http://localhost:8084/status | grep -q 'branch'"
    
    # Cleanup
    echo -e "\n${BLUE}Stopping local deployment...${NC}"
    "$SCRIPT_DIR/local-m3.sh" stop > /dev/null 2>&1
}

# Test Docker build
test_docker_build() {
    echo -e "\n${BLUE}=== Testing Docker Builds ===${NC}\n"
    
    cd "$PROJECT_ROOT"
    
    # Test Bridge API Docker build
    echo -e "${BLUE}Building Bridge API Docker image...${NC}"
    if docker build -f infra/Dockerfile.bridge -t sophia-bridge:test . > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Bridge API Docker build successful${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ Bridge API Docker build failed${NC}"
        ((TESTS_FAILED++))
        FAILED_TESTS+=("Bridge API Docker build")
    fi
    
    # Test MCP Docker build
    echo -e "${BLUE}Building MCP Docker image...${NC}"
    if docker build -f infra/Dockerfile.mcp -t sophia-mcp:test . > /dev/null 2>&1; then
        echo -e "${GREEN}✅ MCP Docker build successful${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ MCP Docker build failed${NC}"
        ((TESTS_FAILED++))
        FAILED_TESTS+=("MCP Docker build")
    fi
    
    # Test Agent UI Docker build
    echo -e "${BLUE}Building Agent UI Docker image...${NC}"
    if docker build -f infra/Dockerfile.sophia-intel-app -t sophia-ui:test sophia-intel-app/ > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Agent UI Docker build successful${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ Agent UI Docker build failed${NC}"
        ((TESTS_FAILED++))
        FAILED_TESTS+=("Agent UI Docker build")
    fi
}

# Test Kubernetes manifests
test_kubernetes() {
    echo -e "\n${BLUE}=== Testing Kubernetes Manifests ===${NC}\n"
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        echo -e "${YELLOW}⚠️  kubectl not found, skipping Kubernetes tests${NC}"
        return
    fi
    
    # Validate manifests
    echo -e "${BLUE}Validating Kubernetes manifests...${NC}"
    if kubectl apply --dry-run=client -f "$PROJECT_ROOT/deploy/k8s/" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Kubernetes manifests are valid${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ Kubernetes manifests validation failed${NC}"
        ((TESTS_FAILED++))
        FAILED_TESTS+=("Kubernetes manifests")
    fi
}

# Test performance
test_performance() {
    echo -e "\n${BLUE}=== Testing Performance ===${NC}\n"
    
    # Start minimal services for performance testing
    echo -e "${BLUE}Starting services for performance test...${NC}"
    "$SCRIPT_DIR/local-m3.sh" deploy > /dev/null 2>&1 &
    sleep 30
    
    # Test Bridge API response time
    echo -e "${BLUE}Testing Bridge API response time...${NC}"
    response_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8003/health 2>/dev/null || echo "999")
    
    if (( $(echo "$response_time < 1.0" | bc -l) )); then
        echo -e "${GREEN}✅ Bridge API response time: ${response_time}s${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ Bridge API response time too slow: ${response_time}s${NC}"
        ((TESTS_FAILED++))
        FAILED_TESTS+=("Bridge API performance")
    fi
    
    # Test concurrent connections
    echo -e "${BLUE}Testing concurrent connections...${NC}"
    if command -v ab &> /dev/null; then
        # Apache Bench test
        ab_output=$(ab -n 100 -c 10 -t 5 http://localhost:8003/health 2>&1 | grep "Requests per second" | awk '{print $4}')
        
        if (( $(echo "$ab_output > 50" | bc -l) )); then
            echo -e "${GREEN}✅ Concurrent requests: ${ab_output} req/s${NC}"
            ((TESTS_PASSED++))
        else
            echo -e "${RED}❌ Low throughput: ${ab_output} req/s${NC}"
            ((TESTS_FAILED++))
            FAILED_TESTS+=("Concurrent connections")
        fi
    else
        echo -e "${YELLOW}⚠️  Apache Bench not found, skipping concurrency test${NC}"
    fi
    
    # Cleanup
    "$SCRIPT_DIR/local-m3.sh" stop > /dev/null 2>&1
}

# Test health monitoring
test_health_monitoring() {
    echo -e "\n${BLUE}=== Testing Health Monitoring ===${NC}\n"
    
    # Start health monitor
    echo -e "${BLUE}Starting health monitor...${NC}"
    python3 "$SCRIPT_DIR/health-monitor.py" > /dev/null 2>&1 &
    MONITOR_PID=$!
    
    sleep 5
    
    # Check if monitor is running
    if ps -p $MONITOR_PID > /dev/null; then
        echo -e "${GREEN}✅ Health monitor started${NC}"
        ((TESTS_PASSED++))
        
        # Kill monitor
        kill $MONITOR_PID 2>/dev/null || true
    else
        echo -e "${RED}❌ Health monitor failed to start${NC}"
        ((TESTS_FAILED++))
        FAILED_TESTS+=("Health monitor")
    fi
}

# Test cloud deployment configs
test_cloud_configs() {
    echo -e "\n${BLUE}=== Testing Cloud Deployment Configs ===${NC}\n"
    
    # Test Fly.io config
    if [ -f "$PROJECT_ROOT/fly.toml" ]; then
        echo -e "${GREEN}✅ Fly.io config exists${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${YELLOW}⚠️  Fly.io config not found${NC}"
    fi
    
    # Test AWS CloudFormation template
    if [ -f "$PROJECT_ROOT/deploy/aws/ecs-stack.yaml" ]; then
        echo -e "${GREEN}✅ AWS CloudFormation template exists${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${YELLOW}⚠️  AWS CloudFormation template not found${NC}"
    fi
}

# Main test runner
run_tests() {
    echo -e "${BLUE}🧪 Sophia Intel AI Deployment Testing${NC}"
    echo "====================================="
    echo "Test Mode: $TEST_MODE"
    echo ""
    
    # Run tests based on mode
    case "$TEST_MODE" in
        env)
            test_environment
            ;;
        local)
            test_environment
            test_local_deployment
            ;;
        docker)
            test_docker_build
            ;;
        k8s)
            test_kubernetes
            ;;
        perf)
            test_performance
            ;;
        health)
            test_health_monitoring
            ;;
        cloud)
            test_cloud_configs
            ;;
        all)
            test_environment
            test_docker_build
            test_local_deployment
            test_kubernetes
            test_performance
            test_health_monitoring
            test_cloud_configs
            ;;
        *)
            echo "Usage: $0 {env|local|docker|k8s|perf|health|cloud|all}"
            exit 1
            ;;
    esac
    
    # Print summary
    echo ""
    echo -e "${BLUE}=== Test Summary ===${NC}"
    echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
    
    if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
        echo -e "\n${RED}Failed Tests:${NC}"
        for test in "${FAILED_TESTS[@]}"; do
            echo "  - $test"
        done
        exit 1
    else
        echo -e "\n${GREEN}🎉 All tests passed!${NC}"
        exit 0
    fi
}

# Handle interrupts
trap 'echo -e "\n${YELLOW}Tests interrupted${NC}"; exit 130' INT TERM

# Run tests
run_tests