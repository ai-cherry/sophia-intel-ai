#!/usr/bin/env bash
set -euo pipefail

# Sophia Intel AI — One‑shot local bootstrap (MCP + Unified API + UI)
#
# What it does
# - Loads centralized env (~/.config/sophia/env) without overriding existing env
# - Starts MCP servers (8081/8082/8084)
# - Starts Unified API (8000) and Sophia Intel UI (3000)
# - Prints connection info for CLIs and agents (MCP + API URLs + token)
# - Verifies health for each service and exits non‑zero if anything is down
#
# Usage
#   bash scripts/dev/bootstrap_all.sh

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

echo "== Sophia Intel AI :: Local Bootstrap =="

# 1) Load centralized env (non‑destructive)
CENTRAL_ENV="${XDG_CONFIG_HOME:-$HOME/.config}/sophia/env"
if [[ -f "$CENTRAL_ENV" ]]; then
  echo "-- Loading centralized env: $CENTRAL_ENV"
  # shellcheck disable=SC1090
  set -a; source "$CENTRAL_ENV"; set +a
else
  echo "!! Centralized env not found at $CENTRAL_ENV (continuing)."
  echo "   Create it to avoid scattered secrets."
fi

# 2) Canonical ports
if [[ -f infra/ports.env ]]; then
  # shellcheck disable=SC1091
  set -a; source infra/ports.env; set +a
fi
PORT_API=${PORT_API:-8000}
PORT_UI=${PORT_UI:-3000}
PORT_MCP_MEMORY=${PORT_MCP_MEMORY:-8081}
PORT_MCP_FILESYSTEM=${PORT_MCP_FILESYSTEM:-8082}
PORT_MCP_GIT=${PORT_MCP_GIT:-8084}

# 3) Sensible MCP defaults (dev friendly)
export MCP_TOKEN=${MCP_TOKEN:-${MCP_SECRET_KEY:-dev-token}}
export MCP_DEV_BYPASS=${MCP_DEV_BYPASS:-true}
export WORKSPACE_PATH=${WORKSPACE_PATH:-$ROOT_DIR}
export WORKSPACE_NAME=${WORKSPACE_NAME:-sophia}

mkdir -p .pids logs >/dev/null 2>&1 || true

# 4) Start MCP servers
echo "-- Starting MCP servers ($PORT_MCP_MEMORY/$PORT_MCP_FILESYSTEM/$PORT_MCP_GIT)"
nohup bash -lc 'bash scripts/start_all_mcp.sh' > logs/mcp.log 2>&1 &
echo $! > .pids/mcp.pid

# 5) Start Unified API + UI (single script)
echo "-- Starting Unified API ($PORT_API) + UI ($PORT_UI)"
nohup bash -lc 'bash scripts/dev/start_local_unified.sh' > logs/bootstrap.log 2>&1 &
echo $! > .pids/bootstrap.pid

# 6) Health checks with retries
function wait_http() {
  local url=$1; local name=$2; local tries=${3:-30}
  local i=0
  while (( i < tries )); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "   ✓ $name: $url"
      return 0
    fi
    sleep 1; i=$((i+1))
  done
  echo "   ✗ $name: $url (timeout)"; return 1
}

echo "-- Waiting for health"
ok=0; fail=0
wait_http "http://localhost:${PORT_API}/api/health" "Unified API" || fail=$((fail+1))
wait_http "http://localhost:${PORT_UI}" "UI (Next.js)" || fail=$((fail+1))
wait_http "http://localhost:${PORT_MCP_MEMORY}/health" "MCP Memory" || fail=$((fail+1))
wait_http "http://localhost:${PORT_MCP_FILESYSTEM}/health" "MCP Filesystem" || fail=$((fail+1))
wait_http "http://localhost:${PORT_MCP_GIT}/health" "MCP Git" || fail=$((fail+1))

if (( fail > 0 )); then
  echo "!! One or more services failed health checks. See logs/ (mcp.log, ui.log, api.log)"
  exit 1
fi

# 7) Connection info for CLIs and agents
cat <<EOF

== Connection Info (export these for any CLI/agent) ==
export SOPHIA_API_URL="http://localhost:${PORT_API}"
export MCP_FS_URL="http://localhost:${PORT_MCP_FILESYSTEM}"
export MCP_GIT_URL="http://localhost:${PORT_MCP_GIT}"
export MCP_MEMORY_URL="http://localhost:${PORT_MCP_MEMORY}"
export MCP_TOKEN="${MCP_TOKEN}"

Examples:
  curl -s \
    -H "Authorization: Bearer \$MCP_TOKEN" \
    -H 'Content-Type: application/json' \
    -d '{"paths":["."],"languages":["python","ts","tsx","js","jsx"]}' \
    "$MCP_FS_URL/symbols/index"

  curl -s "$SOPHIA_API_URL/api/voice/health"

Logs:
  tail -f logs/mcp.log logs/api.log logs/ui.log

All set. 💪
EOF

exit 0

