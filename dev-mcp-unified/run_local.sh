#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ -f "$SCRIPT_DIR/.env.local" ]]; then
  set -a; source "$SCRIPT_DIR/.env.local"; set +a
fi

# run from repo root so package imports resolve
cd "$SCRIPT_DIR/.."
exec python3 -m uvicorn dev_mcp_unified.core.mcp_server:app --host 127.0.0.1 --port 3333
