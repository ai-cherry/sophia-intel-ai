#!/usr/bin/env bash
set -euo pipefail

echo "=== Starting MCP Servers ==="

# Create directories
mkdir -p .pids logs

# Preflight: check code server import & health
python mcp/code_context/server.py --health >/dev/null
echo "✅ code-context MCP ready (VS Code will launch it via stdio)."

# Optional: standalone debug launcher (commented)
# nohup python mcp/code_context/server.py > logs/mcp_code_context.log 2>&1 &
# echo $! > .pids/mcp_code_context.pid
# echo "spawned code-context pid $(cat .pids/mcp_code_context.pid)"

echo
echo "MCP servers are ready to be used by VS Code."
echo "NOTE: VS Code will automatically launch the stdio MCP server when needed."
echo "To stop any manually started servers: bash scripts/stop_all_mcps.sh"
echo
echo "NOTE: VS Code can also manage these servers via the MCP view."
