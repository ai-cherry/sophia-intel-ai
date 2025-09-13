#!/bin/bash
# Stop all Sophia Intel App services

echo "Stopping all Sophia Intel App services..."

# Kill processes on specific ports
kill $(lsof -t -i:8000) 2>/dev/null && echo "✅ Stopped Sophia BI Server"
kill $(lsof -t -i:8004) 2>/dev/null && echo "✅ Stopped Bridge API"
kill $(lsof -t -i:8081) 2>/dev/null && echo "✅ Stopped Memory MCP"
kill $(lsof -t -i:8084) 2>/dev/null && echo "✅ Stopped Git MCP"
kill $(lsof -t -i:8085) 2>/dev/null && echo "✅ Stopped Sophia Intel MCP"

# Kill any Python processes related to sophia
pkill -f "sophia_server" 2>/dev/null
pkill -f "run_sophia" 2>/dev/null
pkill -f "mcp.*server" 2>/dev/null

echo "All services stopped."
