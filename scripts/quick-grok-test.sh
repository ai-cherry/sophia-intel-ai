#!/usr/bin/env bash
set -euo pipefail

# Quick one-off Grok test in a clean python:3.11-slim container

echo "🧪 Running quick Grok test..."

# Try env var, then fall back to .env if present
if [[ -z "${XAI_API_KEY:-}" && -f .env ]]; then
  export XAI_API_KEY="$(grep -E '^XAI_API_KEY=' .env | head -n1 | cut -d'=' -f2- || true)"
fi

if [[ -z "${XAI_API_KEY:-}" ]]; then
  echo "❌ XAI_API_KEY not found in environment or .env"
  exit 1
fi

docker run --rm -it \
  -v "$PWD":/workspace -w /workspace \
  -e XAI_API_KEY="$XAI_API_KEY" \
  python:3.11-slim bash -lc \
  "python3 -m pip install -q --no-cache-dir -r requirements.txt && \
   python3 scripts/sophia.py agent grok --mode code --task 'Create simple REST API endpoint' --provider xai"

echo "✅ Grok test completed"

