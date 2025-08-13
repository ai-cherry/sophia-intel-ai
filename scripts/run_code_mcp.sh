#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export SOPHIA_WORKDIR="${SOPHIA_WORKDIR:-$PWD}"
chmod +x mcp/code_context/server.py
echo "[sophia-code] starting MCP (stdio)…"
exec python mcp/code_context/server.py
