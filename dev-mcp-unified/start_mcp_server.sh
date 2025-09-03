#!/bin/bash

# Start MCP server with environment variables

cd /Users/lynnmusil/sophia-intel-ai

# Load environment variables
set -a
source dev-mcp-unified/.env.local
set +a

# Start the server
echo "🚀 Starting MCP Server at http://localhost:3333"
echo "📊 Available UIs:"
echo "   - Artemis Multi-Model Chat: file:///Users/lynnmusil/sophia-intel-ai/dev-mcp-unified/ui/multi-chat-six.html"
echo ""

python3 -m uvicorn dev_mcp_unified.core.mcp_server:app --host 127.0.0.1 --port 3333