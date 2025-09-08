#!/bin/bash
set -euo pipefail

trap "echo '⛔ Stopping all child processes'; kill 0 2>/dev/null || true" EXIT

echo "🚀 LAUNCHING SOPHIA UNIFIED SYSTEM"

# Config
BRIDGE_PORT="${BRIDGE_PORT:-8003}"
UI_PORT="${UI_PORT:-3000}"

# Start Agno-UI Bridge
if command -v python3 >/dev/null 2>&1; then
  echo "▶ Starting Agno Bridge on :$BRIDGE_PORT"
  BRIDGE_PORT="$BRIDGE_PORT" python3 agno_ui_bridge.py &
else
  echo "(warn) python3 not found; cannot start bridge"
fi

# Start Next.js UI if present
if [ -d agent-ui ]; then
  echo "▶ Starting agent-ui on :$UI_PORT"
  (
    cd agent-ui && \
    if command -v pnpm >/dev/null 2>&1; then pnpm dev; \
    elif command -v npm >/dev/null 2>&1; then npm run dev; \
    else echo "(warn) neither npm nor pnpm found"; fi
  ) &
else
  echo "(warn) agent-ui not found; skipping"
fi

# Basic health wait (non-fatal)
for i in {1..10}; do
  ok=0
  curl -fsS "http://localhost:$BRIDGE_PORT/health" >/dev/null && ok=1 || true
  if [ $ok -eq 1 ]; then
    echo "✅ Bridge healthy at :$BRIDGE_PORT"
    break
  fi
  echo "… waiting for bridge health ($i)"
  sleep 2
done

echo "✅ READY: UI at :$UI_PORT (if started), Bridge at :$BRIDGE_PORT"
wait

