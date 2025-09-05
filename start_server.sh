#!/bin/bash

# Sophia Intel AI - Production Deployment Script
echo "🚀 Starting Sophia Intel AI System..."

# Export required environment variables (no credentials here)
export LOCAL_DEV_MODE=true
export AGENT_API_PORT=${AGENT_API_PORT:-8003}
export WEAVIATE_URL="http://localhost:8080"
export REDIS_URL="redis://localhost:6379"
export MCP_SERVER_URL="http://localhost:8003"

# Kill any existing servers on the ports
echo "⚠️  Cleaning up existing processes..."
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
if curl -s http://localhost:$AGENT_API_PORT/healthz > /dev/null; then
    echo "✅ API Server is running at http://localhost:$AGENT_API_PORT"
    echo "📊 API Documentation: http://localhost:$AGENT_API_PORT/docs"
    echo "🔍 Health Check: http://localhost:$AGENT_API_PORT/healthz"
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
