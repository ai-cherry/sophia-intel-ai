#!/bin/bash
set -e
echo "Starting MCP Servers..."
for server in memory fs git vector graph; do
  pkill -f "mcp_servers/working_servers.py $server" 2>/dev/null || true
  python3 mcp_servers/working_servers.py $server >/dev/null 2>&1 &
  echo "Started MCP $server"
done
echo "All MCP servers started"

