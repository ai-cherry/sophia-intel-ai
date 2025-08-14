#!/usr/bin/env bash
set -euo pipefail

echo "=== Stopping MCP Servers ==="

# Check for manually started code_context MCP server
if [[ -f .pids/mcp_code_context.pid ]]; then
  PID=$(cat .pids/mcp_code_context.pid || true)
  if [[ -n "${PID}" ]] && kill -0 "${PID}" 2>/dev/null; then
    kill "${PID}" || true
    echo "stopped code-context (${PID})"
  fi
  rm -f .pids/mcp_code_context.pid
fi

echo "nothing else to stop."
echo
echo "MCP servers have been stopped."
echo
echo "MCP servers have been stopped."
