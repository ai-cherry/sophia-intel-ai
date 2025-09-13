#!/bin/bash
set -euo pipefail

echo "🚀 DevContainer Post-Start Setup..."

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Start services if needed
# docker-compose up -d || echo "No docker-compose.yml found"

echo "✅ DevContainer post-start setup complete"
