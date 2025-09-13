#!/usr/bin/env bash
set -euo pipefail
cd "$(cd "$(dirname "$0")/.." && pwd)"

if [ -d .pids ]; then
  for f in .pids/*.pid; do
    [ -f "$f" ] || continue
    pid=$(cat "$f" 2>/dev/null || true)
    if [ -n "${pid:-}" ]; then
      kill $pid 2>/dev/null || true
      echo "killed $(basename "$f") ($pid)"
    fi
    rm -f "$f"
  done
else
  echo "No .pids directory found."
fi

echo "✅ Native stack stopped"

