#!/usr/bin/env bash
set -euo pipefail
# Start all MCP servers for Sophia Intel App (no lsof dependency)

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ -f infra/ports.env ]; then
  set -a; source infra/ports.env; set +a
fi

PORT_MCP_MEMORY=${PORT_MCP_MEMORY:-8081}
PORT_MCP_FILESYSTEM=${PORT_MCP_FILESYSTEM:-8082}
PORT_MCP_GIT=${PORT_MCP_GIT:-8084}

# Centralized env (tokens/paths)
export MCP_TOKEN=${MCP_TOKEN:-$MCP_SECRET_KEY}
export MCP_DEV_BYPASS=${MCP_DEV_BYPASS:-true}
export WORKSPACE_PATH="${WORKSPACE_PATH:-$ROOT_DIR}"
export WORKSPACE_NAME="${WORKSPACE_NAME:-sophia}"

echo "🚀 Starting Sophia Intel App MCP Servers"
echo "========================================"

echo "Cleaning up old processes..."
# Best-effort clean by name instead of ports (portable)
pkill -f "uvicorn mcp.memory_server:app" 2>/dev/null || true
pkill -f "uvicorn mcp.filesystem.server:app" 2>/dev/null || true
pkill -f "uvicorn mcp.git.server:app" 2>/dev/null || true
pkill -f "sophia_intel_mcp.py" 2>/dev/null || true

sleep 1

# Ensure PYTHONPATH includes repo root
export PYTHONPATH="${ROOT_DIR}:${PYTHONPATH:-}"

echo "Starting Memory Server on port ${PORT_MCP_MEMORY}..."
nohup python3 -m uvicorn mcp.memory_server:app --host 0.0.0.0 --port ${PORT_MCP_MEMORY} > /tmp/mcp_memory.log 2>&1 &
echo "Memory Server PID: $!"

echo "Starting Filesystem Server on port ${PORT_MCP_FILESYSTEM}..."
export WORKSPACE_PATH="${WORKSPACE_PATH:-$ROOT_DIR}"
nohup python3 -m uvicorn mcp.filesystem.server:app --host 0.0.0.0 --port ${PORT_MCP_FILESYSTEM} > /tmp/mcp_filesystem.log 2>&1 &
echo "Filesystem Server PID: $!"

echo "Starting Git Server on port ${PORT_MCP_GIT}..."
nohup python3 -m uvicorn mcp.git.server:app --host 0.0.0.0 --port ${PORT_MCP_GIT} > /tmp/mcp_git.log 2>&1 &
echo "Git Server PID: $!"

# Optional: custom Sophia MCP wrapper (non-HTTP)
if [ -f mcp_servers/sophia_intel_mcp.py ]; then
  echo "Starting Sophia Intel MCP (stdio script)..."
  nohup python3 mcp_servers/sophia_intel_mcp.py > /tmp/mcp_sophia.log 2>&1 &
  echo "Sophia Intel MCP PID: $!"
fi

sleep 2

echo ""
echo "Verifying MCP servers..."
echo "------------------------"
curl -sf "http://localhost:${PORT_MCP_MEMORY}/health" >/dev/null 2>&1 && echo "✅ Memory Server: http://localhost:${PORT_MCP_MEMORY}/health" || echo "❌ Memory Server: not responding"
curl -sf "http://localhost:${PORT_MCP_FILESYSTEM}/health" >/dev/null 2>&1 && echo "✅ Filesystem Server: http://localhost:${PORT_MCP_FILESYSTEM}/health" || echo "❌ Filesystem Server: not responding"
curl -sf "http://localhost:${PORT_MCP_GIT}/health" >/dev/null 2>&1 && echo "✅ Git Server: http://localhost:${PORT_MCP_GIT}/health" || echo "❌ Git Server: not responding"

echo ""
echo "MCP Servers started. Logs:"
echo "  Memory: /tmp/mcp_memory.log"
echo "  Filesystem: /tmp/mcp_filesystem.log"
echo "  Git: /tmp/mcp_git.log"
if [ -f /tmp/mcp_sophia.log ]; then echo "  Sophia: /tmp/mcp_sophia.log"; fi
