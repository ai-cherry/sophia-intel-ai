#!/usr/bin/env bash
set -euo pipefail

# Thin wrapper to the canonical local startup.
# Follows AGENTS.md: use scripts/dev/start_local_unified.sh or `make dev-native`.

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "== Launching Sophia Intel (canonical) =="
echo "Tip: prefer 'make dev-native' per AGENTS.md"

if [ -f infra/ports.env ]; then
  set -a; source infra/ports.env; set +a
fi

export NEXT_PUBLIC_API_BASE=${NEXT_PUBLIC_API_BASE:-http://localhost:${PORT_API:-8000}}

bash scripts/dev/start_local_unified.sh

echo "OK: UI http://localhost:${PORT_UI:-3000} | API http://localhost:${PORT_API:-8000}/api/health"
