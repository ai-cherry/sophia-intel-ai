#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ -f "$SCRIPT_DIR/.env.local" ]]; then
  set -a; source "$SCRIPT_DIR/.env.local"; set +a
fi

cd "$SCRIPT_DIR/.."
python3 -m uvicorn dev_mcp_unified.core.mcp_server:app --host 127.0.0.1 --port 3333 &
PID=$!
trap "kill $PID 2>/dev/null || true" EXIT

sleep 1
echo "[health]" && curl -s http://127.0.0.1:3333/healthz || true

for llm in claude openai qwen deepseek openrouter; do
  echo "[query:$llm]" && curl -s -X POST http://127.0.0.1:3333/query \
    -H 'Content-Type: application/json' \
    -d "{\"task\":\"general\",\"question\":\"hello from $llm\",\"llm\":\"$llm\"}" || true
  echo
done

kill $PID 2>/dev/null || true
echo "OK"
