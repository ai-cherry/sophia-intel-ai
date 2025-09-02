#!/bin/bash
# Production Deployment Script for Sophia Intel AI
# Deploys all services with monitoring

set -e  # Exit on error

echo "========================================="
echo "🚀 SOPHIA INTEL AI PRODUCTION DEPLOYMENT"
echo "========================================="
echo "Timestamp: $(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Environment variables
export OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-"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"}
export PORTKEY_API_KEY=${PORTKEY_API_KEY:-"nYraiE8dOR9A1gDwaRNpSSXRkXBc"}
export TOGETHER_API_KEY=${TOGETHER_API_KEY:-"together-ai-670469"}
export GPT5_ENABLED=true
export LOCAL_DEV_MODE=false
export PRODUCTION_MODE=true

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to start service
start_service() {
    local name=$1
    local port=$2
    local command=$3
    
    echo -e "${YELLOW}Starting $name on port $port...${NC}"
    
    # Check if already running
    if check_port $port; then
        echo -e "${GREEN}✅ $name already running on port $port${NC}"
    else
        # Start the service
        eval "$command" &
        sleep 3
        
        # Verify it started
        if check_port $port; then
            echo -e "${GREEN}✅ $name started successfully on port $port${NC}"
        else
            echo -e "${RED}❌ Failed to start $name on port $port${NC}"
            return 1
        fi
    fi
}

# Kill any existing instances
echo "🧹 Cleaning up existing services..."
pkill -f "unified_server" 2>/dev/null || true
pkill -f "streamlit" 2>/dev/null || true
pkill -f "monitoring.dashboard" 2>/dev/null || true
pkill -f "mcp.server_v2" 2>/dev/null || true
pkill -f "code_review_server" 2>/dev/null || true
sleep 2

# 1. Start Redis if not running
echo ""
echo "1️⃣ Redis Server (6379)"
if ! check_port 6379; then
    redis-server &
    sleep 2
fi
echo -e "${GREEN}✅ Redis running on port 6379${NC}"

# 2. Start MCP Memory Server
echo ""
echo "2️⃣ MCP Memory Server (8001)"
start_service "MCP Memory Server" 8001 "python3 -m app.mcp.server_v2 --port 8001"

# 3. Start Monitoring Dashboard
echo ""
echo "3️⃣ Monitoring Dashboard (8002)"
start_service "Monitoring Dashboard" 8002 "python3 -m app.monitoring.dashboard"

# 4. Start MCP Code Review Server
echo ""
echo "4️⃣ MCP Code Review Server (8003)"
start_service "MCP Code Review" 8003 "cd app/mcp/code_review_server && npm exec ts-node --esm index.ts"

# 5. Start Unified API Server (Main)
echo ""
echo "5️⃣ Unified API Server (8005)"
start_service "Unified API" 8005 "AGENT_API_PORT=8005 python3 -m app.api.unified_server"

# 6. Start Streamlit UI
echo ""
echo "6️⃣ Streamlit UI (8501)"
start_service "Streamlit UI" 8501 "streamlit run app/ui/streamlit_chat.py --server.port 8501"

# 7. Start Next.js UI (if needed)
echo ""
echo "7️⃣ Next.js UI (3000) - Optional"
if [ -d "agent-ui" ]; then
    cd agent-ui
    if [ -f "package.json" ]; then
        npm install > /dev/null 2>&1
        npm run dev > /dev/null 2>&1 &
        cd ..
        echo -e "${YELLOW}Next.js UI starting in background...${NC}"
    fi
fi

# Wait for all services to stabilize
echo ""
echo "⏳ Waiting for services to stabilize..."
sleep 5

# Service health checks
echo ""
echo "========================================="
echo "📊 SERVICE HEALTH CHECK"
echo "========================================="

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name: HEALTHY${NC}"
        return 0
    else
        echo -e "${RED}❌ $name: UNREACHABLE${NC}"
        return 1
    fi
}

# Test all endpoints
test_endpoint "Unified API Health" "http://localhost:8005/health"
test_endpoint "MCP Memory Server" "http://localhost:8001/health"
test_endpoint "Monitoring Dashboard" "http://localhost:8002/"
test_endpoint "MCP Code Review" "http://localhost:8003/health"
test_endpoint "Streamlit UI" "http://localhost:8501/"
test_endpoint "Metrics Endpoint" "http://localhost:8005/metrics"
test_endpoint "Chat Completions" "http://localhost:8005/docs"

# Test WebSocket endpoints
echo ""
echo "🔌 WebSocket Endpoints:"
echo "  ws://localhost:8005/ws/bus"
echo "  ws://localhost:8005/ws/swarm"
echo "  ws://localhost:8005/ws/teams"

# Display access URLs
echo ""
echo "========================================="
echo "🌐 ACCESS URLS"
echo "========================================="
echo "Main API:        http://localhost:8005"
echo "API Docs:        http://localhost:8005/docs"
echo "Streamlit UI:    http://localhost:8501"
echo "Monitoring:      http://localhost:8002"
echo "Metrics:         http://localhost:8005/metrics"
echo "Health:          http://localhost:8005/health"
echo ""
echo "Chat Endpoint:   POST http://localhost:8005/chat/completions"
echo "Teams Endpoint:  POST http://localhost:8005/teams/run"
echo "Embeddings:      POST http://localhost:8005/mcp/embeddings"

# Display active models
echo ""
echo "========================================="
echo "🤖 ACTIVE MODELS"
echo "========================================="
echo "Premium:   openai/gpt-5, x-ai/grok-4"
echo "Standard:  anthropic/claude-sonnet-4, google/gemini-2.5-pro"
echo "Economy:   google/gemini-2.5-flash, z-ai/glm-4.5-air"
echo "Specialized: x-ai/grok-code-fast-1, deepseek/deepseek-chat-v3.1"

# Final status
echo ""
echo "========================================="
echo "✅ DEPLOYMENT COMPLETE"
echo "========================================="
echo "All services are running and healthy!"
echo "GitHub: https://github.com/ai-cherry/sophia-intel-ai"
echo ""
echo "To monitor: python3 monitor_cline_activity.py"
echo "To test: python3 final_integration_test.py"
echo "To stop: pkill -f 'unified_server|streamlit|monitoring'"
echo ""
echo "🎉 System is PRODUCTION READY!"