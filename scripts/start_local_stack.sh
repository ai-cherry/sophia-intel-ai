#!/usr/bin/env bash
set -euo pipefail

# Unified local stack helper (non-destructive, non-blocking)
# - Loads env, standardizes ports, starts telemetry service
# - Prints next-step commands for MCP + UI

HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/.." && pwd)

source "$ROOT/scripts/env.sh" --quiet || true

export AGENT_API_PORT=${AGENT_API_PORT:-8003}
export NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-http://localhost:${AGENT_API_PORT}}

echo "[start] Using AGENT_API_PORT=$AGENT_API_PORT"

# Start telemetry endpoint if not already running
if ! lsof -Pi :5003 -sTCP:LISTEN -t >/dev/null 2>&1; then
  if command -v python3 >/dev/null 2>&1; then
    echo "[start] Launching telemetry endpoint on 5003..."
    (python3 "$ROOT/webui/telemetry_endpoint.py" >/dev/null 2>&1 & echo $! > "$ROOT/tmp.telemetry.pid") || true
    sleep 1
  else
    echo "[start] Python3 not found; skipping telemetry service"
  fi
else
  echo "[start] Telemetry endpoint already running on 5003"
fi

echo "\n=== Next steps ==="
echo "1) Start MCP servers:       make dev-mcp-up"
echo "2) Check MCP health:         make mcp-test"
echo "3) Start API (dev):          make api-dev      # http://localhost:${AGENT_API_PORT}"
echo "4) Start Next.js UI:         make next-ui-up   # http://localhost:3000/unified"
echo "\nTelemetry: http://localhost:5003/api/telemetry/health (optional)"
