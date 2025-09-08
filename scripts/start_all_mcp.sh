#!/bin/bash
# MCP QUICK START SCRIPT
# Starts all MCP servers with one command

echo "🚀 MCP MASTER STARTUP"
echo "===================="

# Change to repo directory
cd "$(dirname "$0")/.."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi

# Check if Redis is installed
if ! command -v redis-server &> /dev/null; then
    echo "⚠️ Redis not installed. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install redis
    else
        sudo apt-get install redis-server
    fi
fi

# Kill any existing servers on our ports
echo "🔧 Cleaning up existing processes..."
lsof -ti:8001 | xargs kill -9 2>/dev/null
lsof -ti:8002 | xargs kill -9 2>/dev/null
lsof -ti:8003 | xargs kill -9 2>/dev/null
lsof -ti:8004 | xargs kill -9 2>/dev/null
lsof -ti:8005 | xargs kill -9 2>/dev/null

# Start Redis if not running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "📦 Starting Redis..."
    redis-server --daemonize yes
fi

# Check if centralized startup is available
if [ -f "scripts/start_centralized_mcp.py" ]; then
    echo "🎯 Starting Centralized MCP System (Phase 2)..."
    python3 scripts/start_centralized_mcp.py
else
    echo "🎯 Starting MCP Master Controller (Phase 1)..."
    python3 scripts/mcp_master_startup.py
fi
