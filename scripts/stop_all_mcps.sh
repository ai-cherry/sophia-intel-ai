#!/usr/bin/env bash

set -e

echo "=== Stopping MCP Servers ==="

# Directory for PID files
PIDDIR="./.mcp_pids"

# Stop code_context MCP server
if [ -f "$PIDDIR/code_context.pid" ]; then
    PID=$(cat "$PIDDIR/code_context.pid")
    if ps -p $PID > /dev/null; then
        echo "Stopping code_context MCP server (PID: $PID)..."
        kill $PID
        echo "✅ Stopped code_context MCP server"
    else
        echo "⚠️ code_context MCP server not running"
    fi
    rm "$PIDDIR/code_context.pid"
else
    echo "⚠️ No PID file found for code_context MCP server"
fi

# Stop docs_search MCP server
if [ -f "$PIDDIR/docs_search.pid" ]; then
    PID=$(cat "$PIDDIR/docs_search.pid")
    if ps -p $PID > /dev/null; then
        echo "Stopping docs_search MCP server (PID: $PID)..."
        kill $PID
        echo "✅ Stopped docs_search MCP server"
    else
        echo "⚠️ docs_search MCP server not running"
    fi
    rm "$PIDDIR/docs_search.pid"
else
    echo "⚠️ No PID file found for docs_search MCP server"
fi

echo
echo "MCP servers have been stopped."
