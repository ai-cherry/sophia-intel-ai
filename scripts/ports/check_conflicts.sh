#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

if [ -f infra/ports.env ]; then
  set -a; source infra/ports.env; set +a
fi

ports=(
  "API:${PORT_API:-8000}"
  "UI:${PORT_UI:-3000}"
  "MCP_MEMORY:${PORT_MCP_MEMORY:-8081}"
  "MCP_FS:${PORT_MCP_FILESYSTEM:-8082}"
  "MCP_GIT:${PORT_MCP_GIT:-8084}"
  "POSTGRES:${PORT_POSTGRES:-5432}"
  "REDIS:${PORT_REDIS:-6379}"
  "WEAVIATE:${PORT_WEAVIATE:-8080}"
  "NEO4J_HTTP:${PORT_NEO4J_HTTP:-7474}"
  "NEO4J_BOLT:${PORT_NEO4J_BOLT:-7687}"
  "PROMETHEUS:${PORT_PROMETHEUS:-9090}"
  "GRAFANA:${PORT_GRAFANA:-3001}"
)

conflicts=0
printf "Checking port usage...\n"
for item in "${ports[@]}"; do
  name="${item%%:*}"
  port="${item##*:}"
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    printf "%-14s %5s  IN USE\n" "$name" "$port"
    conflicts=$((conflicts+1))
  else
    printf "%-14s %5s  free\n" "$name" "$port"
  fi
done

echo
if [ "$conflicts" -gt 0 ]; then
  echo "⚠️  $conflicts conflicts detected. Edit infra/ports.env to reassign and retry."
  exit 2
else
  echo "✅ No conflicts."
fi

