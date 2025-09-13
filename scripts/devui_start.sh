#!/usr/bin/env bash
# Start the Sophia Dev Command Center (local backend API)
# Opens FastAPI server on http://127.0.0.1:8095
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Ensure Python sees the repo
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"

# Helpful tip
echo "[devui] Starting Dev Command Center API at http://127.0.0.1:8095"
echo "[devui] Try in another terminal:"
echo "        curl -s http://127.0.0.1:8095/api/health/services | sed -n '1,40p'"

# Launch
uvicorn app.devui.server:app --host 127.0.0.1 --port 8095 --reload
