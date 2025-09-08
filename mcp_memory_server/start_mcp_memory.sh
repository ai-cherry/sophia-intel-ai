#!/bin/bash

echo "Starting MCP Memory Server..."

# Set up environment variables
export REDIS_HOST="localhost"
export REDIS_PORT=6379
export QDRANT_URL="http://localhost:6333"
export PORT=8001

# Check if Python virtual environment exists and activate it
if [ -d "/workspace/.venv" ]; then
    source /workspace/.venv/bin/activate
fi

# Install required dependencies if not already installed
pip install -q fastapi uvicorn redis qdrant-client python-dotenv

# Start the MCP Memory Server
cd /workspace/mcp_memory_server
python server.py
