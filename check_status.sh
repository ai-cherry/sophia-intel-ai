#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Checking Sophia Intel AI Status"
echo "=================================="

check() {
  local name=$1 url=$2
  if curl -fsS "$url" >/dev/null 2>&1; then
    echo "✅ $name: OK"
  else
    echo "❌ $name: Not responding ($url)"
  fi
}

check "API" "http://localhost:8000/api/health"
check "UI" "http://localhost:3000"

echo
echo "Ports in use:"
lsof -nP -iTCP:8000 -sTCP:LISTEN 2>/dev/null || echo "  8000: free"
lsof -nP -iTCP:8083 -sTCP:LISTEN 2>/dev/null || echo "  8083: free"
lsof -nP -iTCP:3000 -sTCP:LISTEN 2>/dev/null || echo "  3000: free"
