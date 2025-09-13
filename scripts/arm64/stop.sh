#!/bin/bash
# stop.sh - Clean shutdown for ARM64-native deploy
set -e

# Resolve repo root relative to this script
ROOT_DIR="$(cd "$(dirname "$0")"/../.. && pwd)"
cd "$ROOT_DIR"

echo "Stopping Sophia services..."

# Kill tracked processes
if [ -d "$ROOT_DIR/.pids" ]; then
  for pidfile in "$ROOT_DIR"/.pids/*.pid; do
    [ -f "$pidfile" ] || continue
    kill $(cat "$pidfile") >/dev/null 2>&1 || true
    rm -f "$pidfile"
  done
fi

# Stop services (best-effort)
brew services stop redis >/dev/null 2>&1 || true
brew services stop postgresql@15 >/dev/null 2>&1 || true
pkill -f weaviate >/dev/null 2>&1 || true
pkill -f "uvicorn app\.main_unified:app" >/dev/null 2>&1 || true
pkill -f "npm run dev" >/dev/null 2>&1 || true

echo "✅ All services stopped"
