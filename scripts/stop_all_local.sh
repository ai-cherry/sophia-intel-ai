#!/usr/bin/env bash
set -euo pipefail

# Thin wrapper to canonical stop for native dev.

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "== Stopping Sophia Intel (native) =="

bash scripts/stop-native.sh

echo "OK: native processes signaled via .pids"
