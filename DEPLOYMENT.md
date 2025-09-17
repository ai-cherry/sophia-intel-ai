# Builder Stack Deployment Guide

## Table of Contents
- [Local Development (M3/ARM64)](#local-development-m3arm64)
- [Fly.io Production (AMD64)](#flyio-production-amd64)
- [Environment Configuration](#environment-configuration)
- [Troubleshooting](#troubleshooting)

## Local Development (M3/ARM64)

### Prerequisites

1. **Apple Silicon Mac (M1/M2/M3)**
2. **Colima** for Docker virtualization
3. **Docker** and **Docker Compose**
4. **Python 3.11+**

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/builder-stack.git
cd builder-stack

# 2. Copy environment file
cp .env.template .env
# Edit .env with your API keys

# 3. Start the stack
make dev-up

# 4. Verify services
make ps
```

### Colima Setup for M3

Colima provides optimized virtualization for Apple Silicon:

```bash
# Install Colima
brew install colima

# Start with ARM64 support
colima start --arch aarch64 --cpu 4 --memory 8 --vm-type vz --network-driver slirp

# Set Docker context
docker context use colima
```

### Service URLs

After running `make dev-up`, services are available at:

- **Bridge API**: http://localhost:8004
- **PostgreSQL**: localhost:5432
- **Valkey (Redis)**: localhost:6379
- **Weaviate**: http://localhost:8080
- **Neo4j Browser**: http://localhost:7474
- **MCP Filesystem**: http://localhost:8082
- **MCP Git**: http://localhost:8083
- **MCP Memory**: http://localhost:8084

### Development Workflow

```bash
# Start development stack
make dev-up

# Run tests
make test

# Check model router
make router-check

# Run swarm demo
make swarm-demo

# View logs
make dev-logs

# Stop stack
make dev-down
```

## Fly.io Production (AMD64)

### Prerequisites

1. **Fly CLI** installed
2. **Fly account** with payment method
3. **Docker buildx** for multi-arch builds

### Initial Setup

```bash
# 1. Install Fly CLI
curl -L https://fly.io/install.sh | sh

# 2. Login to Fly
fly auth login

# 3. Create app
fly apps create builder-stack

# 4. Set regions
fly regions add ord lax fra
```

### Database Setup

```bash
# Create PostgreSQL cluster
fly postgres create --name builder-db --region ord
fly postgres attach builder-db

# Create Redis cluster
fly redis create --name builder-cache --region ord
```

### Secrets Configuration

```bash
# Set all required secrets
fly secrets set \
  OPENROUTER_API_KEY=sk-or-v1-xxx \
  POSTGRES_URL=postgres://... \
  NEO4J_URI=bolt://... \
  NEO4J_USER=neo4j \
  NEO4J_PASSWORD=xxx \
  REDIS_URL=redis://... \
  SENTRY_DSN=https://... \
  MCP_SECRET_KEY=xxx \
  JWT_SECRET=xxx
```

### Deployment

```bash
# Build multi-arch images
make build-multi

# Deploy to Fly
make fly-deploy

# Check status
fly status

# View logs
fly logs

# Scale instances
fly scale count api=2 worker=2 --region ord
```

### Process Groups

The deployment uses multiple process groups:

| Process | Purpose | Instances | Memory |
|---------|---------|-----------|--------|
| `api` | Bridge API server | 2 | 2048MB |
| `worker` | Background tasks | 2 | 1024MB |
| `scheduler` | Model refresh | 1 | 1024MB |
| `mcp` | MCP servers | 1 | 512MB |

### Monitoring

```bash
# View metrics
fly metrics

# SSH into instance
fly ssh console --process api

# Check health
curl https://builder-stack.fly.dev/health
```

## Environment Configuration

### Required Variables

```env
# API Keys
OPENROUTER_API_KEY=sk-or-v1-...  # Required
PORTKEY_API_KEY=...               # Optional

# Database
POSTGRES_URL=postgresql://...     # Required
NEO4J_URI=bolt://...             # Required
NEO4J_PASSWORD=...                # Required
REDIS_URL=redis://...             # Required

# Monitoring
SENTRY_DSN=https://...            # Recommended
AGNO_TELEMETRY=on                 # Recommended
```

### Optional Variables

```env
# Performance
MAX_WORKERS=4
MAX_MEMORY_MB=2048
MAX_TOKENS_PER_REQUEST=8000

# Security
JWT_SECRET=...
CORS_ORIGINS=http://localhost:3000

# Features
ENABLE_STREAMING=true
ENABLE_CACHE=true
ENABLE_METRICS=true
```

## Troubleshooting

### Common Issues

#### 1. Colima Not Starting

```bash
# Reset Colima
colima delete
colima start --arch aarch64 --cpu 4 --memory 8

# Check status
colima status
```

#### 2. Port Conflicts

```bash
# Check ports in use
lsof -i :8000
lsof -i :5432
lsof -i :6379

# Kill processes if needed
kill -9 <PID>
```

#### 3. Docker Build Failures

```bash
# Clear builder cache
docker buildx prune -af

# Rebuild with no cache
docker compose build --no-cache
```

#### 4. Database Connection Issues

```bash
# Check PostgreSQL
docker compose exec postgres pg_isready

# Check Redis/Valkey
docker compose exec valkey redis-cli ping

# Reset databases
make db-reset
```

#### 5. Model Router Issues

```bash
# Check cache
docker compose exec valkey redis-cli
> GET openrouter:top25:models

# Force refresh
make router-refresh
```

### Performance Tuning

#### Local (M3)

```yaml
# Adjust in docker-compose.yml
services:
  postgres:
    environment:
      POSTGRES_MAX_CONNECTIONS: 100
      POSTGRES_SHARED_BUFFERS: 256MB
  
  valkey:
    command: valkey-server --maxmemory 1gb
```

#### Production (Fly)

```toml
# Adjust in fly.toml
[[vm]]
  cpu_kind = "performance"  # For critical services
  cpus = 4
  memory_mb = 4096
```

### Logs and Debugging

```bash
# Local logs
docker compose logs -f bridge
docker compose logs -f mcp-filesystem

# Production logs
fly logs --process api
fly logs --process worker

# Debug mode
LOG_LEVEL=DEBUG make dev-up
```

### Health Checks

All services expose health endpoints:

```bash
# Local
curl http://localhost:8003/healthz
curl http://localhost:8082/health

# Production
curl https://builder-stack.fly.dev/health
```

## Support

For issues or questions:

1. Check the [troubleshooting guide](#troubleshooting)
2. Review logs with `make dev-logs` or `fly logs`
3. Open an issue on GitHub
4. Contact the team in Discord

## Next Steps

1. [Configure Agent UI](./AGENT_UI.md)
2. [Set up monitoring](./MONITORING.md)
3. [Create custom teams](./TEAMS.md)
4. [Integrate MCP servers](./MCP.md)
