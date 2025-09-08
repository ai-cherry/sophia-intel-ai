#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
cd "$ROOT_DIR"

# Load environment quietly
if [ -f scripts/env.sh ]; then
  # shellcheck disable=SC1091
  source scripts/env.sh --quiet || true
fi

COMPOSE_DEV="docker-compose.dev.yml"

info() { echo -e "\033[1;34m›\033[0m $*"; }
ok() { echo -e "\033[0;32m✓\033[0m $*"; }
warn() { echo -e "\033[0;33m!\033[0m $*"; }
err() { echo -e "\033[0;31m✗\033[0m $*"; }

start_services() {
  info "Starting core infrastructure (redis, postgres, weaviate)"
  docker compose -f "$COMPOSE_DEV" up -d redis postgres weaviate
  sleep 5

  info "Starting MCP servers (memory, filesystem, git)"
  docker compose -f "$COMPOSE_DEV" up -d mcp-memory mcp-filesystem-sophia mcp-git
  sleep 3

  if [ -n "${ARTEMIS_PATH:-}" ] && [ -d "${ARTEMIS_PATH}" ]; then
    info "Enabling Artemis profile with ARTEMIS_PATH=${ARTEMIS_PATH}"
    docker compose -f "$COMPOSE_DEV" --profile artemis up -d mcp-filesystem-artemis || warn "Artemis FS failed (optional)"
  else
    warn "ARTEMIS_PATH not set or missing; skipping Artemis profile"
  fi

  info "Starting dev shell container (agent-dev)"
  docker compose -f "$COMPOSE_DEV" up -d agent-dev
}

health_checks() {
  info "Checking Redis (6379)"
  if command -v redis-cli >/dev/null 2>&1; then
    redis-cli -h localhost -p ${REDIS_PORT:-6379} ping >/dev/null && ok "Redis OK" || err "Redis not ready"
  else
    (nc -z localhost ${REDIS_PORT:-6379} && ok "Redis port open") || err "Redis port closed"
  fi

  info "Checking Postgres (5432)"
  if command -v pg_isready >/dev/null 2>&1; then
    pg_isready -h localhost -p ${POSTGRES_PORT:-5432} || true
  else
    (nc -z localhost ${POSTGRES_PORT:-5432} && ok "Postgres port open") || warn "Postgres port closed"
  fi

  info "Checking Weaviate (8080)"
  curl -sf http://localhost:${WEAVIATE_REST_PORT:-8080}/v1/.well-known/ready >/dev/null && ok "Weaviate ready" || err "Weaviate not ready"

  info "Checking MCP health"
  curl -sf http://localhost:${MCP_MEMORY_PORT:-8081}/health >/dev/null && ok "Memory MCP OK" || err "Memory MCP"
  curl -sf http://localhost:${MCP_FS_SOPHIA_PORT:-8082}/health >/dev/null && ok "FS MCP (Sophia) OK" || err "FS MCP Sophia"
  curl -sf http://localhost:${MCP_GIT_PORT:-8084}/health >/dev/null && ok "Git MCP OK" || err "Git MCP"
}

case "${1:-all}" in
  all)
    info "Verifying required keys"
    python3 scripts/env_doctor.py | sed -n '/Required keys status:/,/Optional keys/p' || true
    start_services
    health_checks
    ok "Dev environment is up. Open a shell: docker compose -f $COMPOSE_DEV exec agent-dev bash"
    ;;
  up)
    start_services
    ;;
  health)
    health_checks
    ;;
  *)
    echo "Usage: scripts/dev.sh [all|up|health]"; exit 1;
    ;;
esac

