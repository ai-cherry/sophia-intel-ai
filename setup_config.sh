#!/usr/bin/env bash
set -euo pipefail

echo "⚙️ Phase 4: Setting up configuration"

# Do not overwrite if present
if [ -f .env.local ]; then
  echo ".env.local already exists. Skipping creation."
  exit 0
fi

cat > .env.local << 'EOF'
# Sophia Intel AI - Local Development Configuration

# UI expects these values
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8083
NEXT_PUBLIC_API_HOST=localhost
NEXT_PUBLIC_API_PORT=8000
NEXT_PUBLIC_WS_HOST=localhost
NEXT_PUBLIC_WS_PORT=8000

# Backend services
REDIS_URL=redis://localhost:6379/0
# Leave DATABASE_URL unset unless you have Postgres running locally
# DATABASE_URL=postgresql+asyncpg://sophia:sophia@localhost:5432/sophia
WEAVIATE_URL=http://localhost:8080

# Model keys (set your own values or keep loaded from ~/.config/sophia/env)
# OPENAI_API_KEY=...
# ANTHROPIC_API_KEY=...
# PORTKEY_API_KEY=...

# Security (optional)
# JWT_SECRET=...
EOF

echo "✅ Configuration complete! Created .env.local"
