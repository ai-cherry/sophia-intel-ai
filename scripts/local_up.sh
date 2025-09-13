#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== Sophia Intel AI - Local Native Deployment ===${NC}"

# Load environment from preferred path; do NOT echo secrets
SOPHIA_ENV="$HOME/.config/sophia/env"
ARTEMIS_ENV="$HOME/.config/sophia/env"
if [ -f "$SOPHIA_ENV" ]; then
  set -a; source "$SOPHIA_ENV"; set +a
elif [ -f "$ARTEMIS_ENV" ]; then
  set -a; source "$ARTEMIS_ENV"; set +a
else
  echo -e "${YELLOW}⚠ No env found at ~/.config/sophia/env or ~/.config/sophia/env${NC}"
  echo -e "   Create ~/.config/sophia/env with: PORTKEY_API_KEY, OPENROUTER_API_KEY, REDIS_URL, WEAVIATE_URL"
fi

# Defaults for local
export REDIS_URL=${REDIS_URL:-redis://localhost:6379}
export WEAVIATE_URL=${WEAVIATE_URL:-http://localhost:8080}
export AGENT_API_PORT=${AGENT_API_PORT:-8003}

mkdir -p .pids logs || true

check_port() { lsof -Pi :"$1" -sTCP:LISTEN -t >/dev/null 2>&1; }
wait_http() {
  local url="$1" name="$2" max="${3:-30}"; local i=0
  echo -n "Waiting for $name"
  while [ $i -lt $max ]; do
    if curl -sf "$url" >/dev/null 2>&1; then echo -e " ${GREEN}✓${NC}"; return 0; fi
    echo -n "."; sleep 1; i=$((i+1))
  done
  echo -e " ${RED}✗${NC}"; return 1
}

echo -e "${BLUE}1) Starting infra containers (Redis, Weaviate)${NC}"
if ! docker ps --format '{{.Names}}' | grep -q '^redis$'; then
  docker run -d --name redis -p 6379:6379 redis:7-alpine >/dev/null
else
  echo "Redis already running"
fi
if ! docker ps --format '{{.Names}}' | grep -q '^weaviate$'; then
  docker run -d --name weaviate -p 8080:8080 \
    -e QUERY_DEFAULTS_LIMIT=25 \
    -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
    -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
    -e DEFAULT_VECTORIZER_MODULE=none \
    -e CLUSTER_HOSTNAME=node1 \
    semitechnologies/weaviate:1.32.1 >/dev/null || true
else
  echo "Weaviate already running"
fi

wait_http "http://localhost:8080/v1/.well-known/ready" "Weaviate" 45 || true

echo -e "${BLUE}2) Python env + API (FastAPI)${NC}"
if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
pip install --upgrade pip >/dev/null 2>&1 || true
pip install -r requirements.txt >/dev/null

if check_port "$AGENT_API_PORT"; then
  echo -e "${YELLOW}API port $AGENT_API_PORT already in use; skipping start${NC}"
else
  nohup bash -lc \
    "source .venv/bin/activate; uvicorn app.api.unified_server:app --host 0.0.0.0 --port $AGENT_API_PORT --reload" \
    > logs/api.log 2>&1 & echo $! > .pids/api.pid
fi

wait_http "http://localhost:${AGENT_API_PORT}/health" "API" 45 || true

echo -e "${BLUE}3) UI (Next.js dev)${NC}"
if check_port 3000; then
  echo -e "${YELLOW}UI port 3000 already in use; skipping start${NC}"
else
  if command -v pnpm >/dev/null 2>&1; then
    nohup bash -lc 'cd sophia-intel-app && pnpm install >/dev/null 2>&1 || true; pnpm dev --port 3000 --host' \
      > logs/ui.log 2>&1 & echo $! > .pids/ui.pid
  else
    nohup bash -lc 'cd sophia-intel-app && npm install --no-fund >/dev/null 2>&1 || true; npm run dev -- --port 3000 --host' \
      > logs/ui.log 2>&1 & echo $! > .pids/ui.pid
  fi
fi

sleep 2
echo
echo -e "${GREEN}✅ Local stack started${NC}"
echo "- API:   http://localhost:${AGENT_API_PORT}/health"
echo "- UI:    http://localhost:3000"
echo "- Weaviate: http://localhost:8080/v1/.well-known/ready"
echo
echo "Logs: logs/api.log, logs/ui.log"
echo "PIDs: .pids/api.pid, .pids/ui.pid"

