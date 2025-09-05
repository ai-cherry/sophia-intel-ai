#!/bin/bash
# Minimal deployment for MCP server only
set -e

echo "🚀 Starting MCP Server (Minimal Deployment)"
echo "============================================"

# Load environment
if [ -f .env.local ]; then
    source .env.local
fi

# Kill any existing MCP server
pkill -f mcp_server 2>/dev/null || true
sleep 1

# Start MCP server
echo "Starting MCP Unified Server on port ${MCP_PORT:-3333}..."
OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-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} \
PORTKEY_API_KEY=${PORTKEY_API_KEY:-nYraiE8dOR9A1gDwaRNpSSXRkXBc} \
TOGETHER_API_KEY=${TOGETHER_API_KEY:-together-ai-670469} \
OPENAI_API_KEY=${OPENAI_API_KEY:-dummy} \
LOCAL_DEV_MODE=true \
AGENT_API_PORT=${MCP_PORT:-3333} \
RBAC_ENABLED=true \
DB_TYPE=sqlite \
DB_PATH=sophia_rbac.db \
python3.12 -m uvicorn dev_mcp_unified.core.mcp_server:app \
    --host 127.0.0.1 \
    --port ${MCP_PORT:-3333} \
    --reload \
    > logs/mcp_server.log 2>&1 &

echo "MCP Server PID: $!"

# Wait for service
echo -n "Waiting for MCP Server..."
for i in {1..30}; do
    if curl -s "http://localhost:${MCP_PORT:-3333}/docs" > /dev/null 2>&1; then
        echo " ✅"
        echo ""
        echo "✅ MCP Server is running!"
        echo "📍 API Documentation: http://localhost:${MCP_PORT:-3333}/docs"
        echo "📍 Health Check: http://localhost:${MCP_PORT:-3333}/health"
        echo ""
        echo "To check logs: tail -f logs/mcp_server.log"
        echo "To stop: pkill -f mcp_server"
        exit 0
    fi
    echo -n "."
    sleep 1
done

echo " ❌"
echo "Failed to start MCP Server. Check logs/mcp_server.log"
exit 1
