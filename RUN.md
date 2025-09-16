# 🚀 Sophia Intel AI - Local Deployment Guide

**One-command deployment with full UI dashboard and MCP integration for AI coding workflows.**

## Quick Start

### Option 1: Automated Script (Recommended)
```bash
# Clone and start everything
git clone <repo-url>
cd sophia-intel-ai
./scripts/start_all_and_validate.sh
```

### Option 2: Make Commands
```bash
# Setup environment and start
make env-setup  # Creates .env.master template
make dev        # Start all services locally
make ui         # Open dashboard in browser
```

### Option 3: Docker
```bash
# Docker deployment
make env-setup
make up         # Start with docker-compose
make health     # Verify all services
```

## What You Get

| Service | URL | Purpose |
|---------|-----|---------|
| **Dashboard** | http://localhost:8000/dashboard | Full AI platform UI with chat, metrics, monitoring |
| **API Docs** | http://localhost:8000/docs | OpenAPI/Swagger documentation |
| **MCP Memory** | http://localhost:8081 | Memory server for AI context |
| **MCP Filesystem** | http://localhost:8082 | File operations for coding |
| **MCP Git** | http://localhost:8084 | Git integration for version control |

## Prerequisites

- **Python 3.11+** (for non-Docker)
- **Docker + Docker Compose** (for Docker deployment)
- **API Keys**: Portkey, OpenRouter, or Together AI

## Environment Setup

The system uses a single `.env.master` file for all configuration:

```bash
# Required: AI Gateway
PORTKEY_API_KEY=your_portkey_key

# Optional: Direct provider keys  
OPENROUTER_API_KEY=your_openrouter_key
TOGETHER_API_KEY=your_together_key

# Environment
ENVIRONMENT=development
```

**Security**: `.env.master` is git-ignored and auto-secured with 600 permissions.

## Local Development (Non-Docker)

### Automated Startup
```bash
./scripts/start_all_and_validate.sh
```

### Manual Control
```bash
# Individual services
make api        # API server only
make mcp        # MCP servers only
make dev        # Everything with auto-reload

# Health checks
make health     # Check all services
make smoke      # Quick validation
```

### Background Process Management
The startup script manages processes automatically:
- Creates `.pids/` directory for process tracking
- Handles cleanup on Ctrl+C
- Validates all endpoints before completion

## Docker Deployment

### Full Stack
```bash
make up         # Starts: API, MCP servers, Redis, Weaviate
make logs       # Monitor logs
make down       # Stop everything
```

### Services Included
- **API + Dashboard**: Main application server
- **MCP Trio**: Memory, Filesystem, Git servers
- **Redis**: Caching and sessions  
- **Weaviate**: Vector database
- **PostgreSQL**: Optional structured data (profile: full)

## Architecture

```
┌─────────────────────────────────────────┐
│  Dashboard UI (React-based)            │
│  http://localhost:8000/dashboard       │
├─────────────────────────────────────────┤
│  FastAPI Server (8000)                 │
│  ├── /docs (OpenAPI)                   │
│  ├── /health (Status)                  │
│  └── /api/* (REST endpoints)           │
├─────────────────────────────────────────┤
│  MCP Servers (AI Coding Integration)   │
│  ├── Memory (8081)    ├── FS (8082)    │
│  └── Git (8084)       └── Vector (opt) │
├─────────────────────────────────────────┤
│  Infrastructure (Optional)             │
│  ├── Redis (6379)     └── Weaviate     │
│  └── PostgreSQL       (8080)           │
└─────────────────────────────────────────┘
```

## Key Features

### Dashboard UI (`/dashboard`)
- **Overview**: System status, model availability, cost tracking
- **Chat Interface**: Direct AI interaction with streaming
- **Repository Browser**: File navigation with git status
- **API Documentation**: Embedded Swagger UI
- **Metrics Dashboard**: Performance and health monitoring
- **MCP Memory**: Memory management interface
- **WebSocket Tools**: Real-time connection testing

### API Endpoints
- **Chat**: `/api/chat` - AI completions with streaming
- **Memory**: `/api/memory` - Context storage and retrieval  
- **Orchestration**: `/api/orchestration` - Multi-agent workflows
- **Models**: `/api/models` - Available AI model information
- **Health**: `/health`, `/ready` - Service status

### MCP Integration
- **VSCode/Cursor**: Auto-configured endpoints for AI coding
- **Memory Persistence**: Context across coding sessions
- **Git Integration**: Version control aware operations
- **File System**: Secure repository access

## Health Monitoring

### Automatic Validation
```bash
# All services
make health

# Individual checks
curl http://localhost:8000/health      # API
curl http://localhost:8081/health      # MCP Memory
curl http://localhost:8082/health      # MCP Filesystem  
curl http://localhost:8084/health      # MCP Git
```

### Dashboard Status
The dashboard shows real-time status indicators for all services with auto-refresh.

## Common Commands

```bash
# Environment
make env-check                    # Validate configuration
make env-setup                    # Create .env.master template

# Development  
make dev                         # Start with hot reload
make api                         # API server only
make mcp                         # MCP servers only

# Docker
make up                          # Start all containers
make build                       # Rebuild images
make logs                        # Follow logs
make down                        # Stop containers

# Testing & Health
make health                      # Check all services
make smoke                       # Quick validation  
make test                        # Run integration tests
make ui                          # Open dashboard

# Cleanup
make clean                       # Remove containers/volumes
make reset                       # Full reset
```

## Troubleshooting

### Port Conflicts
Default ports: 8000 (API), 8081-8084 (MCP), 6379 (Redis), 8080 (Weaviate)
```bash
# Check what's running
lsof -i :8000
make health  # Shows status of all ports
```

### Environment Issues
```bash
# Check configuration
make env-check

# Recreate environment  
rm .env.master
make env-setup
```

### Service Failures
```bash
# View logs
make logs                        # Docker
tail -f .pids/*.log             # Local (if logging enabled)

# Restart services
make down && make up             # Docker
./scripts/start_all_and_validate.sh --stop && make dev  # Local
```

### Missing Static Files
Ensure `app/static/` and `app/templates/` directories exist:
```bash
mkdir -p app/static/css app/static/js
ls -la app/templates/hub.html    # Should exist
```

## OAuth Callbacks (Business Integrations)

For Slack, HubSpot, etc. integrations in local development:
```bash
# Use ngrok or similar for HTTPS tunnels
ngrok http 8000

# Update OAuth callback URLs to:
# https://your-ngrok-domain.ngrok.io/api/slack/callback
# https://your-ngrok-domain.ngrok.io/api/hubspot/callback
```

## Production Considerations

- **Environment**: Set `ENVIRONMENT=production` in `.env.master`
- **Database**: Enable PostgreSQL with `--profile full`
- **Secrets**: Use proper secret management (not `.env.master`)
- **TLS**: Add reverse proxy (nginx/traefik) for HTTPS
- **Monitoring**: Enable Prometheus metrics at `/metrics`

## Development Workflow

1. **Start**: `make dev` or `./scripts/start_all_and_validate.sh`
2. **Code**: Edit files with hot-reload enabled
3. **Test**: Access dashboard at http://localhost:8000/dashboard
4. **API**: Use http://localhost:8000/docs for API exploration
5. **MCP**: Connect VSCode/Cursor to MCP endpoints for AI coding

## Support

- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8000/dashboard
- **Make Commands**: `make help`

---

**🎯 Goal**: One command to full AI platform with dashboard UI and MCP integration for seamless AI-powered development.
