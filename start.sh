#!/bin/bash
# Unified startup script for Sophia Intel AI (no virtualenvs)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/scripts/env.sh"

log_info "Starting MCP Memory Server"
bash "$SCRIPT_DIR/scripts/mcp_bootstrap.sh" || log_warn "MCP bootstrap reported warnings"

log_info "Starting API server (development)"
nohup python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > "$SCRIPT_DIR/logs/api_dev.log" 2>&1 &
echo $! > "$SCRIPT_DIR/.pids/api.pid"

sleep 2
log_success "Startup complete"
echo "- API: http://localhost:8000 (docs at /docs)"
echo "- MCP: http://localhost:${MCP_MEMORY_PORT:-8001}"

