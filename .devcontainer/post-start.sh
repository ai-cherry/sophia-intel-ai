#!/bin/bash
set -euo pipefail

echo "🚀 DevContainer Post-Start Setup..."

# Environment is sourced only from <repo>/.env.master via ./sophia. Do not load .env here.

# Start services if needed
# docker-compose up -d || echo "No docker-compose.yml found"

echo "✅ DevContainer post-start setup complete"
