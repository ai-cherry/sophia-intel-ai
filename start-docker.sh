#!/usr/bin/env bash
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Install Docker and retry." >&2
  exit 1
fi
if ! command -v docker compose >/dev/null 2>&1; then
  echo "Docker Compose is required (v2). Install and retry." >&2
  exit 1
fi

source scripts/env.sh --quiet || true

for p in 3000 5003 8003 8081 8082 8084; do
  if lsof -Pi :$p -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Port $p is in use. Free it or adjust docker.env before proceeding." >&2
    exit 1
  fi
done

echo "Building images (no-cache) …"
docker compose build --no-cache

echo "Starting stack …"
docker compose up -d

echo "Tailing logs (press Ctrl+C to detach) …"
docker compose logs -f --tail=200

