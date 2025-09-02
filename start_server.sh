#!/bin/bash

# Sophia Intel AI - Production Deployment Script
echo "🚀 Starting Sophia Intel AI System..."

# Export required environment variables
export OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-"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"}
export PORTKEY_API_KEY=${PORTKEY_API_KEY:-"nYraiE8dOR9A1gDwaRNpSSXRkXBc"}
export TOGETHER_API_KEY=${TOGETHER_API_KEY:-"together-ai-670469"}
export AGNO_API_KEY="phi-0cnOaV2N-MKID0LJTszPjAdj7XhunqMQFG4IwLPG9dI"
export VK_OPENROUTER="vkj-openrouter-cc4151"
export VK_TOGETHER="together-ai-670469"
export LOCAL_DEV_MODE=true
export AGENT_API_PORT=${AGENT_API_PORT:-8005}
export WEAVIATE_URL="http://localhost:8080"
export REDIS_URL="redis://localhost:6379"
export MCP_SERVER_URL="http://localhost:8003"

# Kill any existing servers on the ports
echo "⚠️  Cleaning up existing processes..."
lsof -ti:8005 | xargs kill -9 2>/dev/null
lsof -ti:8003 | xargs kill -9 2>/dev/null
sleep 1

# Start the unified server
echo "📡 Starting Unified API Server on port $AGENT_API_PORT..."
python3 -m app.api.unified_server &
SERVER_PID=$!

# Wait for server to start
echo "⏳ Waiting for server to initialize..."
sleep 3

# Check if server is running
if curl -s http://localhost:$AGENT_API_PORT/health > /dev/null; then
    echo "✅ API Server is running at http://localhost:$AGENT_API_PORT"
    echo "📊 API Documentation: http://localhost:$AGENT_API_PORT/docs"
    echo "🔍 Health Check: http://localhost:$AGENT_API_PORT/health"
    echo ""
    echo "Available endpoints:"
    echo "  - /api/portkey-routing/ - Unified model routing"
    echo "  - /api/ws/ - WebSocket connections"
    echo "  - /api/memory/ - Memory operations"
    echo "  - /hub/ - Agent hub interface"
    echo ""
    echo "Press Ctrl+C to stop the server"
    
    # Keep the script running
    wait $SERVER_PID
else
    echo "❌ Failed to start API server"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi