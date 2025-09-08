# Simple Local Deployment Guide

## 🚀 Quick Start (5 minutes)

### 1. Prerequisites Check
```bash
# Required software
docker --version  # Need Docker Desktop
python3 --version # Need Python 3.11+
git --version     # Need Git
```

### 2. Setup Environment (One Time)
```bash
# Clone repository
cd ~
git clone git@github.com:ai-cherry/sophia-intel-ai.git
cd sophia-intel-ai

# Copy environment template
cp .env.template .env

# Create local environment overrides
cat > .env.local << 'EOF'
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
PORTKEY_API_KEY=your_portkey_key_here
EOF

# Load environment
source scripts/env.sh
```

### 3. Start Everything (One Command)
```bash
# This starts Redis, Postgres, Weaviate, and dev environment
bash scripts/dev.sh all
```

Expected output:
```
✓ Redis OK
✓ Postgres port open
✓ Weaviate ready
✓ Dev environment is up
```

### 4. Verify Installation
```bash
# Check running services
docker ps

# You should see:
# - sophia-redis (port 6379)
# - sophia-postgres (port 5432)
# - sophia-weaviate (port 8080)
```

## 💻 Development Workflow

### Open Development Shell
```bash
# Enter the development container
docker compose -f docker-compose.dev.yml exec agent-dev bash

# Inside container, you can:
cd /workspace/sophia
python3 --version
pip list
```

### Run Tests
```bash
# From your host machine
pytest tests/test_basic.py -v -k "not artemis"
```

### Check Service Health
```bash
# Quick health check
make health-infra

# MCP endpoints check (if running)
make mcp-test
```

## 🔧 Common Tasks

### Stop Everything
```bash
docker compose -f docker-compose.dev.yml down
```

### Restart Services
```bash
# Stop
docker compose -f docker-compose.dev.yml down

# Start again
bash scripts/dev.sh all
```

### View Logs
```bash
# All services
docker compose -f docker-compose.dev.yml logs -f

# Specific service
docker logs sophia-redis -f
```

### Clean Everything
```bash
# Stop and remove containers
docker compose -f docker-compose.dev.yml down -v

# Remove all Docker resources (careful!)
docker system prune -a
```

## 🏭 Production API Deployment

### Build and Start API
```bash
# Build production API image
make api-build

# Start API service (port 8003)
make api-up

# Or rebuild + start in one command
make api-restart
```

### Verify API
```bash
# Wait 20 seconds for startup
sleep 20

# Check API docs
curl http://localhost:8003/docs

# Check health
curl http://localhost:8003/openapi.json
```

## ⚠️ Troubleshooting

### Port Already in Use
```bash
# Find what's using port 6379 (Redis)
lsof -i :6379

# Kill the process
kill -9 <PID>
```

### Docker Network Issues
```bash
# Clean up networks
docker network prune -f

# Restart Docker Desktop
# Mac: Click Docker icon → Restart
```

### Environment Variables Not Loading
```bash
# Check your keys are set
make keys-check

# Verify env files exist
ls -la .env*

# Re-source environment
source scripts/env.sh
```

### Weaviate Not Starting
```bash
# Check logs
docker logs sophia-weaviate

# May need more memory - increase Docker Desktop resources:
# Docker Desktop → Settings → Resources → Memory: 8GB minimum
```

## 📁 Project Structure

```
sophia-intel-ai/
├── scripts/
│   ├── dev.sh          # Main startup script
│   ├── env.sh          # Environment loader
│   └── env_doctor.py   # Environment checker
├── docker-compose.dev.yml  # Development services
├── docker-compose.yml      # Production services
├── .env.template           # Environment template
├── .env                    # Your local config (from template)
├── .env.local             # Your API keys (create this)
└── ~/.config/artemis/env  # Secure keys (optional)
```

## 🔑 API Keys Required

Minimum required keys in `.env.local`:
- `OPENAI_API_KEY` - Get from https://platform.openai.com/api-keys
- `ANTHROPIC_API_KEY` - Get from https://console.anthropic.com/
- `PORTKEY_API_KEY` - Get from https://portkey.ai/

Optional but recommended:
- `XAI_API_KEY` - For Grok
- `GROQ_API_KEY` - For Groq models
- `GITHUB_TOKEN` - For GitHub integration

## ✅ Success Indicators

You know it's working when:
1. `docker ps` shows 3+ containers running
2. `make health-infra` shows all green checks
3. No error messages in `docker logs sophia-redis`
4. You can enter dev shell with `docker compose -f docker-compose.dev.yml exec agent-dev bash`

## 🆘 Getting Help

1. Check logs: `docker compose -f docker-compose.dev.yml logs`
2. Run diagnostics: `make health`
3. Check environment: `make env.doctor`
4. File issue: https://github.com/ai-cherry/sophia-intel-ai/issues

---

**That's it!** You should have a working local development environment in under 5 minutes.