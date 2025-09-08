#!/bin/bash
# Start MCP Memory Server

# Check if Python virtual environment exists and activate it
if [ -d "/workspace/.venv" ]; then
    source /workspace/.venv/bin/activate
fi

# Start the MCP memory server
echo "Starting MCP Memory Server on port 8001..."
python /workspace/mcp_memory/server.py --port 8001 &

echo "MCP Memory Server started. Check logs for details."
