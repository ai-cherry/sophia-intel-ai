#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

echo "== Sophia Intel - Local Unified Start (API:8000, UI:3000, MCP:8081/8082/8084) =="

mkdir -p .pids logs || true

echo "-- Load port assignments"
if [ -f infra/ports.env ]; then
  set -a; source infra/ports.env; set +a
fi

echo "-- Python venv + deps"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip >/dev/null 2>&1 || true
if [ -f requirements.txt ]; then
  echo "   (pip installing requirements.txt — this may take a while)"
  if ! pip install -r requirements.txt; then
    echo "   ⚠️ pip install failed (offline or locked). API may not start; continuing with MCP/UI."
  fi
fi

# Pre-clean any old API process to avoid port conflicts
pkill -f "uvicorn app.api.unified_server:app" 2>/dev/null || true

# Choose API port with simple fallback if busy
API_PORT=${PORT_API:-8000}
if [ "$(python3 - <<'PY'
import socket,os
port=int(os.environ.get('PORT_API',os.environ.get('API_PORT','8000')))
try:
    s=socket.socket(); s.bind(('127.0.0.1',port)); s.close(); print('FREE')
except OSError:
    print('BUSY')
PY
)" = "BUSY" ]; then
  API_PORT=8010
fi

echo "-- Check API Python deps"
if python3 - <<'PY'
import importlib,sys
missing=[]
for m in ('fastapi','uvicorn','msgpack','jinja2','aiofiles','email_validator'):
    try: importlib.import_module(m)
    except Exception: missing.append(m)
sys.exit(0 if not missing else 1)
PY
then
  echo "-- Start API (${API_PORT})"
  nohup bash -lc "source .venv/bin/activate; PYTHONPATH=$PWD python -m uvicorn app.api.unified_server:app --host 0.0.0.0 --port ${API_PORT} --reload" > logs/api.log 2>&1 &
  echo $! > .pids/api.pid
else
  echo "   ⚠️ Skipping API start due to missing deps (see pip output above)."
fi

echo "-- Start MCP servers (${PORT_MCP_MEMORY:-8081}/${PORT_MCP_FILESYSTEM:-8082}/${PORT_MCP_GIT:-8084})"
nohup bash -lc 'bash scripts/start_all_mcp.sh' > logs/mcp.log 2>&1 &
echo $! > .pids/mcp.pid

echo "-- Start UI (${PORT_UI:-3000})"
export NEXT_PUBLIC_API_BASE=${NEXT_PUBLIC_API_BASE:-http://localhost:${API_PORT}}
if command -v pnpm >/dev/null 2>&1; then
  nohup bash -lc "cd sophia-intel-app && pnpm install >/dev/null 2>&1; pnpm dev --port ${PORT_UI:-3000}" > logs/ui.log 2>&1 &
else
  nohup bash -lc "cd sophia-intel-app && npm install --no-fund >/dev/null 2>&1; npm run dev -- --port ${PORT_UI:-3000}" > logs/ui.log 2>&1 &
fi
echo $! > .pids/ui.pid

sleep 2
echo "-- Listening ports"
if command -v lsof >/dev/null 2>&1; then
  lsof -nP -iTCP:${API_PORT},${PORT_UI:-3000},${PORT_MCP_MEMORY:-8081},${PORT_MCP_FILESYSTEM:-8082},${PORT_MCP_GIT:-8084} -sTCP:LISTEN || true
else
  echo "   (install lsof to see listening ports)"
fi

echo "Ready: UI http://localhost:${PORT_UI:-3000}"
echo "API:  http://localhost:${API_PORT}/api/health (if started)"
