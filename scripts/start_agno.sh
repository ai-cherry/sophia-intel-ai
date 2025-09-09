#!/usr/bin/env bash
set -euo pipefail

# Start the Agno bridge (FastAPI) used by the UI
# Defaults align with the UI's unified endpoint on :8003

: "${BRIDGE_HOST:=0.0.0.0}"
: "${BRIDGE_PORT:=8003}"

echo "▶ Ensuring Agno core scaffold exists"
if [ -f setup_agno_core.py ]; then
  python3 setup_agno_core.py >/dev/null 2>&1 || true
fi

if [ ! -f agno_ui_bridge.py ]; then
  echo "⛔ agno_ui_bridge.py not found. Aborting."
  exit 1
fi

echo "▶ Starting Agno bridge on ${BRIDGE_HOST}:${BRIDGE_PORT}"
BRIDGE_HOST="$BRIDGE_HOST" BRIDGE_PORT="$BRIDGE_PORT" python3 agno_ui_bridge.py &
bridge_pid=$!
trap "echo '⛔ Stopping Agno bridge'; kill ${bridge_pid} 2>/dev/null || true" EXIT

echo "… waiting for /health"
for i in {1..20}; do
  if curl -fsS "http://localhost:${BRIDGE_PORT}/health" >/dev/null 2>&1; then
    echo "✅ Agno bridge healthy at http://localhost:${BRIDGE_PORT}/health"
    break
  fi
  sleep 0.5
done

echo "ℹ️ If using the UI, ensure NEXT_PUBLIC_API_URL points to http://localhost:${BRIDGE_PORT}"
echo "   Example: export NEXT_PUBLIC_API_URL=http://localhost:${BRIDGE_PORT}"
echo "   Then start the UI (e.g., cd agent-ui && npm run dev)"

wait ${bridge_pid}

