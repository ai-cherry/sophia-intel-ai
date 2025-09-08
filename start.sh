#!/bin/bash
# Unified startup script for Sophia Intel AI (no virtualenvs)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/scripts/env.sh"

# Parse arguments
SERVICES="${1:-core}"
SKIP_RAG=false

for arg in "$@"; do
    case $arg in
        --skip-rag)
            SKIP_RAG=true
            ;;
        --with-rag)
            SKIP_RAG=false
            ;;
        --help)
            echo "Usage: $0 [core|all|rag] [--skip-rag|--with-rag]"
            echo "  core: Start only core services (MCP, API)"
            echo "  all:  Start all services including RAG"
            echo "  rag:  Start only RAG services"
            exit 0
            ;;
    esac
done

# Start services based on selection
if [[ "$SERVICES" == "core" ]] || [[ "$SERVICES" == "all" ]]; then
    log_info "Starting MCP Memory Server"
    bash "$SCRIPT_DIR/scripts/mcp_bootstrap.sh" || log_warn "MCP bootstrap reported warnings"
    
    log_info "Starting API server (development)"
    nohup python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > "$SCRIPT_DIR/logs/api_dev.log" 2>&1 &
    echo $! > "$SCRIPT_DIR/.pids/api.pid"
fi

# Start RAG services if requested
if [[ "$SERVICES" == "rag" ]] || ([[ "$SERVICES" == "all" ]] && [[ "$SKIP_RAG" == "false" ]]); then
    log_info "Starting RAG Memory Services"
    bash "$SCRIPT_DIR/scripts/start_rag_services.sh" start
fi

sleep 2
log_success "Startup complete"
echo "Active services:"
echo "- API: http://localhost:8000 (docs at /docs)"
echo "- MCP: http://localhost:${MCP_MEMORY_PORT:-8001}"

if [[ "$SKIP_RAG" == "false" ]]; then
    echo "- Sophia RAG: http://localhost:8767 (Business Intelligence)"
    echo "- Artemis RAG: http://localhost:8768 (Code Intelligence)"
fi

