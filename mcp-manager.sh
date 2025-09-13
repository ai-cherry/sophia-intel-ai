#!/usr/bin/env bash
# MCP Server Manager (compat wrapper) — delegates to unified-system-manager

set -euo pipefail
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MANAGER="$ROOT_DIR/unified-system-manager.sh"

case "${1:-}" in
  status)
    ports=(8081 8082 8084)
    names=("Memory" "Filesystem" "Git")
    echo "MCP Server Status:"
    echo "=================="
    for i in ${!ports[@]}; do
      if (command -v nc >/dev/null && nc -z localhost "${ports[$i]}" >/dev/null 2>&1) || \
         (command -v lsof >/dev/null && lsof -Pi :"${ports[$i]}" -sTCP:LISTEN -t >/dev/null 2>&1); then
        printf "✅ MCP %-10s on %d\n" "${names[$i]}" "${ports[$i]}"
      else
        printf "❌ MCP %-10s down (port %d)\n" "${names[$i]}" "${ports[$i]}"
      fi
    done
    ;;
  start)
    exec "$MANAGER" mcp-start
    ;;
  stop)
    exec "$MANAGER" mcp-stop
    ;;
  restart)
    "$MANAGER" mcp-stop || true
    sleep 1
    exec "$MANAGER" mcp-start
    ;;
  *)
    echo "Usage: $0 {status|start|stop|restart}"
    exit 1
    ;;
esac
