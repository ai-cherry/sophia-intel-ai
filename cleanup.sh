#!/usr/bin/env bash
set -euo pipefail

echo "🧹 Phase 1: Complete Cleanup (safe)"

# Kill processes started by this repo (based on PID files and ports)
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
fi

echo "Stopping known ports (3000, 8003, 8083)"
for p in 3000 8003 8083; do
  pids=$(lsof -ti tcp:$p || true)
  [ -n "$pids" ] && kill -9 $pids || true
done

echo "Cleaning cache and temp files"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
rm -rf .ruff_cache .pytest_cache tmp/.mypy_cache 2>/dev/null || true

echo "Keeping .venv intact by default. To remove, run: rm -rf .venv"
echo "✅ Cleanup complete!"

