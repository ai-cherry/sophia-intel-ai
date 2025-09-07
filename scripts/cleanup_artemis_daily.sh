#!/usr/bin/env bash
set -euo pipefail

cd "/Users/lynnmusil/sophia-intel-ai"
if [ -f .env.artemis.local ]; then
  # shellcheck disable=SC1091
  source .env.artemis.local
fi

# Minimal, recommended cleanup calls
./bin/artemis-run cleanup collab --type expired --json || true
./bin/artemis-run cleanup collab --type stale --older-than 7d --json || true
./bin/artemis-run cleanup backups --older-than 30d --json || true

echo "Artemis daily cleanup completed."
exit 0
