#!/bin/bash
# Start MCP Memory Server
# Uses system Python - no virtual environment

# Source shared environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/scripts/env.sh"

# Check for required dependencies
python3 - <<'PY'
try:
    import fastapi, uvicorn, redis, qdrant_client
    print('deps_ok')
except Exception as e:
    print(f'deps_missing: {e}')
PY

deps_status=$(python3 - <<'PY' 2>&1
try:
    import fastapi, uvicorn, redis, qdrant_client
    print('deps_ok')
except Exception as e:
    print(f'deps_missing')
PY
)

if [[ "$deps_status" != "deps_ok" ]]; then
    log_error "Missing dependencies for MCP Memory Server"
    log_info "Install with: pip3 install --user fastapi uvicorn redis qdrant-client python-dotenv"
    exit 1
fi

# Start the MCP memory server
log_info "Starting MCP Memory Server on port ${MCP_MEMORY_PORT:-8765}..."

if [ -f "mcp_memory_server/main.py" ]; then
    python3 mcp_memory_server/main.py --port ${MCP_MEMORY_PORT:-8765} &
elif [ -f "mcp_memory_server/server.py" ]; then
    python3 mcp_memory_server/server.py --port ${MCP_MEMORY_PORT:-8765} &
elif [ -f "mcp_memory/server.py" ]; then
    python3 mcp_memory/server.py --port ${MCP_MEMORY_PORT:-8765} &
else
    log_error "MCP Memory Server script not found"
    exit 1
fi

log_success "MCP Memory Server started. Check logs for details."