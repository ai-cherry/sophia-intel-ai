#!/usr/bin/env bash
set -euo pipefail

# Colors for output
info() { echo -e "\033[1;34m›\033[0m $*"; }
ok() { echo -e "\033[0;32m✓\033[0m $*"; }
warn() { echo -e "\033[0;33m!\033[0m $*"; }
err() { echo -e "\033[0;31m✗\033[0m $*"; }

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
cd "$ROOT_DIR"

# Kill any existing UI servers
info "Stopping any existing UI servers..."
pkill -f "http.server 8085" 2>/dev/null || true
pkill -f "http.server 8086" 2>/dev/null || true
pkill -f "agent_factory.py" 2>/dev/null || true
sleep 2

# Start Agent Factory Dashboard (Sophia)
info "Starting Agent Factory Dashboard on port 8085..."
cd "$ROOT_DIR/app/agents/ui"
python3 -m http.server 8085 > /tmp/agent_factory_ui.log 2>&1 &
UI_PID=$!
ok "Agent Factory UI started (PID: $UI_PID)"

# Start Factory Backend (if exists)
if [ -f "$ROOT_DIR/app/factory/agent_factory.py" ]; then
    info "Starting Agent Factory Backend on port 8091..."
    cd "$ROOT_DIR"
    python3 app/factory/agent_factory.py > /tmp/agent_factory_backend.log 2>&1 &
    BACKEND_PID=$!
    ok "Agent Factory Backend started (PID: $BACKEND_PID)"
fi

# Start Agno Teams (if needed)
if [ -f "$ROOT_DIR/app/swarms/agno_teams.py" ]; then
    info "Agno Teams module available at app/swarms/agno_teams.py"
fi

# Wait and verify
sleep 3

info "Verifying UI services..."
if curl -s http://localhost:8085/agent_factory_dashboard.html > /dev/null; then
    ok "Agent Factory Dashboard: http://localhost:8085/agent_factory_dashboard.html"
else
    err "Agent Factory Dashboard not responding"
fi

echo ""
info "UI Services Summary:"
echo "  • Agent Factory Dashboard: http://localhost:8085/agent_factory_dashboard.html"
echo "  • Logs: tail -f /tmp/agent_factory_ui.log"
echo ""
info "To stop all UI services:"
echo "  pkill -f 'http.server 808[56]'"
echo "  pkill -f 'agent_factory.py'"