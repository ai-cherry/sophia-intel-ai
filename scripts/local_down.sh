#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${YELLOW}Stopping local API/UI...${NC}"
if [ -f .pids/api.pid ]; then
  pid=$(cat .pids/api.pid || true)
  [ -n "${pid:-}" ] && kill "$pid" 2>/dev/null || true
  rm -f .pids/api.pid || true
fi
if [ -f .pids/ui.pid ]; then
  pid=$(cat .pids/ui.pid || true)
  [ -n "${pid:-}" ] && kill "$pid" 2>/dev/null || true
  rm -f .pids/ui.pid || true
fi

echo -e "${YELLOW}Stopping containers (redis, weaviate) if present...${NC}"
docker rm -f redis >/dev/null 2>&1 || true
docker rm -f weaviate >/dev/null 2>&1 || true

echo -e "${GREEN}✅ Local stack stopped${NC}"

