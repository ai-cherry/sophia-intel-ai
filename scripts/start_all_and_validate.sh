#!/usr/bin/env bash
set -euo pipefail

# One command to start core deps (valkey/redis, weaviate), MCP servers (incl. vector),
# validate health, seed a minimal index, and start the queue worker.

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd -P)"
cd "$ROOT_DIR"

LOG_DIR="$ROOT_DIR/logs"
PID_DIR="$ROOT_DIR/.pids"
mkdir -p "$LOG_DIR" "$PID_DIR"

ENV_FILE="$ROOT_DIR/.env.master"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
else
  echo "FAIL env: missing .env.master at $ENV_FILE" >&2
  exit 1
fi

# Defaults
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/1}"
export WEAVIATE_URL="${WEAVIATE_URL:-http://localhost:8080}"
export MCP_MEMORY_PORT="${MCP_MEMORY_PORT:-8081}"
export MCP_FILESYSTEM_PORT="${MCP_FILESYSTEM_PORT:-8082}"
export MCP_GIT_PORT="${MCP_GIT_PORT:-8084}"
export MCP_VECTOR_PORT="${MCP_VECTOR_PORT:-8085}"
export MCP_DEV_BYPASS="${MCP_DEV_BYPASS:-true}"
export WORKSPACE_PATH="${WORKSPACE_PATH:-$ROOT_DIR}"
export WORKSPACE_NAME="${WORKSPACE_NAME:-sophia}"

ok()   { echo "OK  $*"; }
fail() { echo "FAIL $*"; }

check_port() {
  local port="$1"
  if command -v nc >/dev/null 2>&1 && nc -z localhost "$port" 2>/dev/null; then return 0; fi
  if command -v lsof >/dev/null 2>&1 && lsof -Pi :"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then return 0; fi
  if command -v netstat >/dev/null 2>&1 && netstat -an 2>/dev/null | grep -q "LISTEN.*[.:]$port"; then return 0; fi
  return 1
}

start_valkey() {
  # Try to ping; if not reachable, try docker
  if python3 -c 'import os,redis; redis.Redis.from_url(os.environ.get("REDIS_URL","redis://localhost:6379/1")).ping()' >/dev/null 2>&1; then
    ok "Redis reachable ($REDIS_URL)"
    return
  fi
  if command -v docker >/dev/null 2>&1; then
    echo "Starting valkey container (6379)..."
    docker rm -f valkey-local >/dev/null 2>&1 || true
    docker run -d --name valkey-local -p 6379:6379 valkey/valkey:7 >/dev/null 2>&1 || docker run -d --name valkey-local -p 6379:6379 redis:7 >/dev/null 2>&1 || true
    sleep 2
    if python3 -c 'import os,redis; redis.Redis.from_url(os.environ.get("REDIS_URL","redis://localhost:6379/1")).ping()' >/dev/null 2>&1; then ok "Redis container up"; else fail "Redis not reachable"; fi
  else
    fail "Redis not reachable and docker not available"
  fi
}

start_weaviate() {
  # Probe health first
  if curl -fsS "${WEAVIATE_URL}/v1/.well-known/ready" >/dev/null 2>&1; then
    ok "Weaviate ready (${WEAVIATE_URL})"
    return
  fi
  if command -v docker >/dev/null 2>&1; then
    echo "Starting Weaviate container (8080)..."
    docker rm -f weaviate-local >/dev/null 2>&1 || true
    docker run -d --name weaviate-local \
      -p 8080:8080 -e QUERY_DEFAULTS_LIMIT=25 -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
      semitechnologies/weaviate:1.24.10 >/dev/null 2>&1 || true
    echo -n "Waiting for Weaviate"; for i in {1..20}; do
      if curl -fsS "${WEAVIATE_URL}/v1/.well-known/ready" >/dev/null 2>&1; then echo; ok "Weaviate up"; return; fi
      echo -n "."; sleep 1
    done; echo
    fail "Weaviate failed to become ready"
  else
    fail "Weaviate not ready and docker not available"
  fi
}

start_mcp() {
  # Kill pre-existing
  pkill -f "uvicorn mcp.memory_server:app" 2>/dev/null || true
  pkill -f "uvicorn mcp.filesystem.server:app" 2>/dev/null || true
  pkill -f "uvicorn mcp.git.server:app" 2>/dev/null || true
  pkill -f "uvicorn mcp.vector.server:app" 2>/dev/null || true

  nohup python3 -m uvicorn mcp.memory_server:app --host 0.0.0.0 --port "$MCP_MEMORY_PORT" > "$LOG_DIR/mcp_memory.log" 2>&1 & echo $! > "$PID_DIR/mcp_memory.pid"
  nohup python3 -m uvicorn mcp.filesystem.server:app --host 0.0.0.0 --port "$MCP_FILESYSTEM_PORT" > "$LOG_DIR/mcp_filesystem.log" 2>&1 & echo $! > "$PID_DIR/mcp_filesystem.pid"
  nohup python3 -m uvicorn mcp.git.server:app --host 0.0.0.0 --port "$MCP_GIT_PORT" > "$LOG_DIR/mcp_git.log" 2>&1 & echo $! > "$PID_DIR/mcp_git.pid"
  nohup python3 -m uvicorn mcp.vector.server:app --host 0.0.0.0 --port "$MCP_VECTOR_PORT" > "$LOG_DIR/mcp_vector.log" 2>&1 & echo $! > "$PID_DIR/mcp_vector.pid"

  # Wait briefly for ports
  for p in "$MCP_MEMORY_PORT" "$MCP_FILESYSTEM_PORT" "$MCP_GIT_PORT" "$MCP_VECTOR_PORT"; do
    for i in {1..10}; do check_port "$p" && break || sleep 1; done
  done
}

validate_env_and_services() {
  echo "== Env master check =="
  python3 scripts/env_master_check.py || return 1
}

bootstrap_index() {
  # Use a light bootstrap that does not require heavy deps
  if [[ -f "indexer/bootstrap_index.py" ]]; then
    python3 indexer/bootstrap_index.py || true
  else
    # As a fallback, index README via vector MCP
    if [[ -f "README.md" ]]; then
      curl -fsS -X POST "http://localhost:${MCP_VECTOR_PORT}/index" \
        -H 'Content-Type: application/json' \
        -d @- <<EOF || true
{"path":"README.md","content":$(python3 -c 'import json,sys; print(json.dumps(open("README.md","r",encoding="utf-8",errors="ignore").read())) )'}
EOF
    fi
  fi
}

start_queue_worker() {
  nohup python3 -u indexer/queue_worker.py > "$LOG_DIR/indexer.log" 2>&1 & echo $! > "$PID_DIR/indexer_worker.pid" || true
}

print_endpoints() {
  echo "== Endpoints =="
  echo "MCP Memory     : http://localhost:${MCP_MEMORY_PORT}"
  echo "MCP Filesystem : http://localhost:${MCP_FILESYSTEM_PORT}"
  echo "MCP Git        : http://localhost:${MCP_GIT_PORT}"
  echo "MCP Vector     : http://localhost:${MCP_VECTOR_PORT}"
  echo "Weaviate       : ${WEAVIATE_URL}"
  echo "Suggested UIs  : Forge 3100 (external), Portkey 3200 (external)"
}

# Execution
start_valkey
start_weaviate
start_mcp
if validate_env_and_services; then ok "All checks passed"; else fail "One or more checks failed"; exit 1; fi
bootstrap_index
start_queue_worker
print_endpoints
