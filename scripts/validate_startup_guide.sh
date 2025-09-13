#!/usr/bin/env bash
# Sophia Intel AI - STARTUP_GUIDE validator
# Goal: Validate that the system can run and core services respond, without relying on .env.master.
# This script is safe to run multiple times. By default it does NOT start services; use --start to start them.
# It focuses on running and working (developer convenience over security).

set -euo pipefail

# ---------- Styling ----------
RED="$(tput setaf 1 || true)"; GREEN="$(tput setaf 2 || true)"; YELLOW="$(tput setaf 3 || true)"; BLUE="$(tput setaf 4 || true)"; BOLD="$(tput bold || true)"; RESET="$(tput sgr0 || true)"

log() { printf "%s%s%s\n" "${BLUE}[validator]${RESET}" " $*" ""; }
ok() { printf "%s%s%s\n" "${GREEN}✔${RESET}" " $*" ""; }
warn() { printf "%s%s%s\n" "${YELLOW}⚠${RESET}" " $*" ""; }
err() { printf "%s%s%s\n" "${RED}✖${RESET}" " $*" ""; }

# ---------- Usage ----------
usage() {
  cat <<'USAGE'
Usage: scripts/validate_startup_guide.sh [--start] [--timeout N] [--lite-token TOKEN]

Options:
  --start            Attempt to start services via ./sophia start (or ./dev start) before checks.
  --timeout N        Seconds to wait for ports to open (default: 20).
  --lite-token TOKEN Override LiteLLM bearer token (default: sk-litellm-master-2025 if unset).
  --help             Show this help.

Checks performed:
  - Preflight: required tools (curl), optional tools (redis-cli).
  - Presence of ./sophia (or ./dev) scripts and status output.
  - Service health:
      * LiteLLM on :4000 (/v1/models) — accept 200/401 as "up".
      * MCP Memory on :8081 (/health or /) — accept 200.
      * MCP Filesystem on :8082 (/health or /) — accept 200.
      * MCP Git on :8084 (/health or /) — accept 200.
  - Summary: overall pass if at least one core service is up (LiteLLM or any MCP).

Notes:
  - No dependency on .env.master; you can export keys manually if needed.
  - If services are not running, pass --start to launch them.
USAGE
}

# ---------- Args ----------
START_SERVICES=0
TIMEOUT=20
LITELLM_TOKEN="${LITELLM_MASTER_KEY:-sk-litellm-master-2025}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --start) START_SERVICES=1; shift ;;
    --timeout) TIMEOUT="${2:-20}"; shift 2 ;;
    --lite-token) LITELLM_TOKEN="${2:-$LITELLM_TOKEN}"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) err "Unknown arg: $1"; usage; exit 1 ;;
  esac
done

# ---------- Helpers ----------
cmd_exists() { command -v "$1" >/dev/null 2>&1; }

wait_for_port() {
  # wait_for_port host port timeout_seconds
  local host="$1" port="$2" timeout="${3:-15}" elapsed=0
  while ! (echo >/dev/tcp/"$host"/"$port") >/dev/null 2>&1; do
    sleep 1
    elapsed=$((elapsed+1))
    if [ "$elapsed" -ge "$timeout" ]; then
      return 1
    fi
  done
  return 0
}

http_status() {
  # http_status url [header...] -> prints status code or 000 on failure
  local url="$1"; shift || true
  curl -s -o /dev/null -w "%{http_code}" "$@" "$url" || echo "000"
}

# ---------- Preflight ----------
ROOT_DIR="$(pwd)"
log "Repository: ${ROOT_DIR}"

if ! cmd_exists curl; then
  err "curl is required. Install curl and retry."
  exit 1
fi

SOPHIA_SCRIPT=""
if [ -x "./sophia" ]; then
  SOPHIA_SCRIPT="./sophia"
elif [ -x "./dev" ]; then
  SOPHIA_SCRIPT="./dev"
else
  warn "Neither ./sophia nor ./dev found as executable; will only run passive checks."
fi

# ---------- Optional: start services ----------
if [ "$START_SERVICES" -eq 1 ]; then
  if [ -n "$SOPHIA_SCRIPT" ]; then
    log "Attempting to start services via ${SOPHIA_SCRIPT} start ..."
    if "$SOPHIA_SCRIPT" start; then
      ok "Start command executed"
    else
      warn "${SOPHIA_SCRIPT} start returned non-zero; continuing with checks"
    fi
  else
    warn "No start script found; skipping start"
  fi
fi

# ---------- Status (best-effort) ----------
if [ -n "$SOPHIA_SCRIPT" ]; then
  log "Checking status via ${SOPHIA_SCRIPT} status (best-effort) ..."
  if "$SOPHIA_SCRIPT" status || true; then
    ok "Status command executed"
  fi
fi

# ---------- Wait for ports (best-effort) ----------
log "Waiting for known ports to be open (timeout: ${TIMEOUT}s each) ..."
for port in 4000 8081 8082 8084; do
  if wait_for_port 127.0.0.1 "$port" "$TIMEOUT"; then
    ok "Port $port is open"
  else
    warn "Port $port not open after ${TIMEOUT}s"
  fi
done

# ---------- Health Checks ----------
# Portkey Gateway
if [[ -n "${PORTKEY_API_KEY:-}" ]]; then
  PK_STATUS="$(http_status "https://api.portkey.ai/v1/health" -H "x-portkey-api-key: ${PORTKEY_API_KEY}")"
  if [[ "$PK_STATUS" == "200" ]]; then ok "Portkey Gateway healthy"; else warn "Portkey health status: ${PK_STATUS}"; fi
else
  warn "PORTKEY_API_KEY not set; skipping gateway health"
fi

# MCP Memory
MEM_URL_HEALTH="http://127.0.0.1:8081/health"
MEM_URL_ROOT="http://127.0.0.1:8081/"
MEM_STATUS="$(http_status "$MEM_URL_HEALTH")"
if [[ "$MEM_STATUS" != "200" ]]; then
  MEM_STATUS="$(http_status "$MEM_URL_ROOT")"
fi
if [[ "$MEM_STATUS" == "200" ]]; then
  ok "MCP Memory responding (200) at :8081"
else
  warn "MCP Memory not healthy (status ${MEM_STATUS})"
fi

# MCP Filesystem
FS_URL_HEALTH="http://127.0.0.1:8082/health"
FS_URL_ROOT="http://127.0.0.1:8082/"
FS_STATUS="$(http_status "$FS_URL_HEALTH")"
if [[ "$FS_STATUS" != "200" ]]; then
  FS_STATUS="$(http_status "$FS_URL_ROOT")"
fi
if [[ "$FS_STATUS" == "200" ]]; then
  ok "MCP Filesystem responding (200) at :8082"
else
  warn "MCP Filesystem not healthy (status ${FS_STATUS})"
fi

# MCP Git
GIT_URL_HEALTH="http://127.0.0.1:8084/health"
GIT_URL_ROOT="http://127.0.0.1:8084/"
GIT_STATUS="$(http_status "$GIT_URL_HEALTH")"
if [[ "$GIT_STATUS" != "200" ]]; then
  GIT_STATUS="$(http_status "$GIT_URL_ROOT")"
fi
if [[ "$GIT_STATUS" == "200" ]]; then
  ok "MCP Git responding (200) at :8084"
else
  warn "MCP Git not healthy (status ${GIT_STATUS})"
fi

# Redis (optional)
if cmd_exists redis-cli; then
  if redis-cli ping >/dev/null 2>&1; then
    ok "Redis responding to PING"
  else
    warn "Redis CLI present but ping failed"
  fi
else
  warn "redis-cli not installed; skipping Redis ping"
fi

# ---------- Summary ----------
UP_COUNT=0
if [[ "$LITELLM_STATUS" == "200" || "$LITELLM_STATUS" == "401" ]]; then UP_COUNT=$((UP_COUNT+1)); fi
if [[ "$MEM_STATUS" == "200" ]]; then UP_COUNT=$((UP_COUNT+1)); fi
if [[ "$FS_STATUS" == "200" ]]; then UP_COUNT=$((UP_COUNT+1)); fi
if [[ "$GIT_STATUS" == "200" ]]; then UP_COUNT=$((UP_COUNT+1)); fi

echo
if [[ "$UP_COUNT" -ge 1 ]]; then
  ok "Validation complete: ${UP_COUNT} core service(s) responding."
  echo "Tips:"
  echo "  - If LiteLLM returned 401, token likely missing; export LITELLM_MASTER_KEY or use --lite-token."
  echo "  - Use ${SOPHIA_SCRIPT:-'./sophia'} logs to inspect issues if a service is down."
  exit 0
else
  err "No core services responded. Try: ${SOPHIA_SCRIPT:-'./sophia'} start  or rerun with  --start --timeout 30"
  exit 2
fi
