#!/bin/bash
# Start MCP Memory Server
# Uses system Python - no virtual environment

echo "Starting MCP Memory Server..."

# Set up environment variables
export REDIS_HOST="${REDIS_HOST:-localhost}"
export REDIS_PORT="${REDIS_PORT:-6379}"
export QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
export PORT="${PORT:-8765}"

# Check for required dependencies (no inline pip install)
deps_status=$(python3 - <<'PY' 2>&1
try:
    import fastapi, uvicorn, redis, qdrant_client, dotenv
    print('deps_ok')
except Exception as e:
    print(f'deps_missing')
PY
)

if [[ "$deps_status" != "deps_ok" ]]; then
    echo "ERROR: Missing dependencies for MCP Memory Server"
    echo "Install with: pip3 install --user fastapi uvicorn redis qdrant-client python-dotenv"
    exit 1
fi

# Start the MCP Memory Server with system Python
cd "$(dirname "$0")"
python3 server.py