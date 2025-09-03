#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")"/.. && pwd)"

echo "🔧 Killing anything on :3333..."
if lsof -iTCP:3333 -sTCP:LISTEN -n -P >/dev/null 2>&1; then
  lsof -iTCP:3333 -sTCP:LISTEN -n -P | awk 'NR>1{print $2}' | xargs -r kill -9 || true
fi

echo "🚀 Starting MCP server on 127.0.0.1:3333"
cd "$ROOT"
nohup ./dev-mcp-unified/run_local.sh > ./dev-mcp-unified/mcp.log 2>&1 &
PID=$!
echo $PID > ./dev-mcp-unified/mcp.pid
sleep 2

echo "📄 Tail last 20 log lines:"
tail -n 20 ./dev-mcp-unified/mcp.log || true

echo "✅ Restart script complete. PID: $PID"
