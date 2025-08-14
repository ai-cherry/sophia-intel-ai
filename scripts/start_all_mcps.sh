#!/usr/bin/env bash

set -e

echo "=== Starting MCP Servers ==="

# Directory for PID files
PIDDIR="./.mcp_pids"
mkdir -p "$PIDDIR"

# Start code_context MCP server
echo "Starting code_context MCP server..."
python -m mcp.code_context.server > ./code_context_mcp.log 2>&1 &
CODE_CONTEXT_PID=$!
echo $CODE_CONTEXT_PID > "$PIDDIR/code_context.pid"
echo "✅ Started code_context MCP server (PID: $CODE_CONTEXT_PID)"
echo "   Logs: ./code_context_mcp.log"

# Start docs_search MCP server
echo "Starting docs_search MCP server..."
python -m mcp.docs_search.server --config mcp/docs-mcp.config.json > ./docs_search_mcp.log 2>&1 &
DOCS_SEARCH_PID=$!
echo $DOCS_SEARCH_PID > "$PIDDIR/docs_search.pid"
echo "✅ Started docs_search MCP server (PID: $DOCS_SEARCH_PID)"
echo "   Logs: ./docs_search_mcp.log"

echo
echo "MCP servers are now running."
echo "To stop servers: bash scripts/stop_all_mcps.sh"
echo 
echo "NOTE: VS Code can also manage these servers via the MCP view."
