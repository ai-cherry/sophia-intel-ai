#!/usr/bin/env bash
set -e

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PID_DIR="$ROOT_DIR/.pids"
LOG_DIR="$ROOT_DIR/logs"
ENV_FILE="$ROOT_DIR/.env.master"

mkdir -p "$PID_DIR" "$LOG_DIR"

if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

API_PORT="${PORT:-8000}"
UI_PORT="${SOPHIA_UI_PORT:-3000}"

start_mcp() {
  "$ROOT_DIR/unified-system-manager.sh" mcp-start || true
}

start_api() {
  if lsof -Pi :"$API_PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "API already listening on :$API_PORT"
    return 0
  fi
  echo "Starting API on :$API_PORT"
  nohup uvicorn backend.main:app --host 0.0.0.0 --port "$API_PORT" \
    > "$LOG_DIR/api.log" 2>&1 & echo $! > "$PID_DIR/api.pid"
}

start_ui() {
  if lsof -Pi :"$UI_PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "UI already listening on :$UI_PORT"
    return 0
  fi
  if [ ! -d "$ROOT_DIR/sophia-intel-app" ]; then
    echo "sophia-intel-app not found; skipping UI"
    return 0
  fi
  echo "Starting UI on :$UI_PORT"
  ( cd "$ROOT_DIR/sophia-intel-app" && nohup npm run dev -- --port "$UI_PORT" \
      > "$LOG_DIR/ui.log" 2>&1 & echo $! > "$PID_DIR/ui.pid" )
}

stop_proc() {
  local name=$1 pidfile=$2
  if [ -f "$pidfile" ]; then
    local pid=$(cat "$pidfile")
    if kill -0 "$pid" 2>/dev/null; then
      echo "Stopping $name (PID $pid)"
      kill "$pid" 2>/dev/null || true
    fi
    rm -f "$pidfile"
  fi
}

status() {
  echo "=== Status ==="
  for p in 8081 8082 8084; do
    if curl -s --max-time 2 "http://localhost:$p/health" >/dev/null 2>&1; then
      echo "MCP $( [ "$p" = 8081 ] && echo Memory || ([ "$p" = 8082 ] && echo Filesystem || echo Git) ): OK (:${p})"
    else
      echo "MCP :$p not healthy"
    fi
  done
  curl -s --max-time 2 "http://localhost:$API_PORT/health" >/dev/null 2>&1 \
    && echo "API :$API_PORT healthy" || echo "API :$API_PORT not responding"
  curl -s --max-time 2 "http://localhost:$UI_PORT" >/dev/null 2>&1 \
    && echo "UI :$UI_PORT responding" || echo "UI :$UI_PORT not responding"
}

case "${1:-}" in
  up)
    start_mcp
    start_api
    start_ui
    status
    ;;
  down)
    stop_proc api "$PID_DIR/api.pid"
    stop_proc ui "$PID_DIR/ui.pid"
    "$ROOT_DIR/unified-system-manager.sh" mcp-stop || true
    ;;
  status)
    status
    ;;
  logs)
    tail -n 100 -f "$LOG_DIR"/*.log
    ;;
  *)
    echo "Usage: $0 {up|down|status|logs}"
    exit 1
    ;;
esac

