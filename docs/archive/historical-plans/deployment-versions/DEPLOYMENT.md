# 🚀 Sophia Intel AI - Production Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Sophia Intel AI system with all enhancements including unified configuration, turnkey Docker deployment, memory/search endpoints, observability, background indexing, and rate limiting.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture](#architecture)
3. [Configuration](#configuration)
4. [Deployment Options](#deployment-options)
5. [API Endpoints](#api-endpoints)
6. [Monitoring & Observability](#monitoring--observability)
7. [Troubleshooting](#troubleshooting)

## Quick Start

### One-Command Deployment

```bash
# Clone the repository
git clone https://github.com/ai-cherry/sophia-intel-ai.git
cd sophia-intel-ai

# Create .env file with your API keys
cat > .env << EOF
OPENROUTER_API_KEY=your_key_here
PORTKEY_API_KEY=your_key_here
TOGETHER_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
AGNO_API_KEY=phi-0cnOaV2N-MKID0LJTszPjAdj7XhunqMQFG4IwLPG9dI
EOF

# Deploy everything with Docker Compose
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f api
```

Your complete system is now running at:
- **API Server**: http://localhost:8000
- **Agent UI**: http://localhost:3002
- **Main UI**: http://localhost:3001
- **Agno Bridge**: http://localhost:7777
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3005

## Architecture

```mermaid
graph TB
    UI[Agent UI :3002] --> Bridge[Agno Bridge :7777]
    UI --> API[API Server :8000]
    Bridge --> API
    
    API --> Weaviate[Weaviate :8080]
    API --> Redis[Redis :6379]
    API --> Postgres[PostgreSQL :5432]
    
    API --> Celery[Celery Workers]
    Celery --> Redis
    
    Prometheus[Prometheus :9090] --> API
    Grafana[Grafana :3005] --> Prometheus
    
    API --> MCP1[MCP Filesystem]
    API --> MCP2[MCP Git]
    API --> MCP3[MCP Supermemory]
```

## Configuration

### Unified Configuration System

All configuration is centralized in `app/core/config.py` using Pydantic:

```python
from app.core.config import settings

# Access any setting
print(settings.api_port)  # 8000
print(settings.weaviate_url)  # http://localhost:8080
print(settings.rate_limit_enabled)  # True
```

### Environment Variables

Key environment variables (set in `.env`):

```bash
# Server Configuration
ENVIRONMENT=production
API_PORT=8000
LOCAL_DEV_MODE=false

# Database & Storage
WEAVIATE_URL=http://weaviate:8080
REDIS_URL=redis://redis:6379
POSTGRES_URL=postgresql://sophia:password@postgres:5432/sophia_intel
SUPERMEMORY_DB=/app/data/supermemory.db

# API Keys (Required)
OPENROUTER_API_KEY=xxx
PORTKEY_API_KEY=xxx
TOGETHER_API_KEY=xxx
ANTHROPIC_API_KEY=xxx
AGNO_API_KEY=xxx

# Features
GRAPHRAG_ENABLED=true
HYBRID_SEARCH_ENABLED=true
EVALUATION_GATES_ENABLED=true
METRICS_ENABLED=true
RATE_LIMIT_ENABLED=true

# Rate Limiting
RATE_LIMIT_RPM=60
STREAMING_RATE_LIMIT_RPM=30

# Monitoring
METRICS_PORT=9090
TRACING_ENABLED=true
JAEGER_ENDPOINT=jaeger:6831
```

## Deployment Options

### Option 1: Docker Compose (Recommended)

```bash
# Production deployment with all services
docker-compose -f docker-compose.production.yml up -d

# Development deployment (with hot reload)
docker-compose -f docker-compose.yml up -d

# Scale workers
docker-compose -f docker-compose.production.yml up -d --scale celery-worker=4
```

### Option 2: Kubernetes

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment
kubectl get pods -n sophia-intel

# Access via port-forward
kubectl port-forward -n sophia-intel svc/api 8000:8000
```

### Option 3: Manual Deployment

```bash
# Install dependencies
pip install -r requirements.txt
npm install --prefix ui
npm install --prefix agent-ui

# Start services
./deploy_local.sh

# Or manually:
python -m app.api.unified_server  # API on :8000
python -m app.agno_bridge  # Bridge on :7777
celery -A app.tasks.indexing worker  # Background tasks
npm run dev --prefix ui  # UI on :3001
npm run dev --prefix agent-ui  # Agent UI on :3002
```

## API Endpoints

### Memory Management (Agno-Compatible)

```bash
# Add memory
curl -X POST http://localhost:8000/memory/add \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Project Architecture",
    "content": "The system uses a microservices architecture...",
    "tags": ["architecture", "design"],
    "memory_type": "procedural"
  }'

# Search memory
curl -X POST http://localhost:8000/memory/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "microservices",
    "limit": 10,
    "hybrid": true,
    "rerank": true
  }'

# Get memory stats
curl http://localhost:8000/memory/stats
```

### Agent/Team Execution

```bash
# List agents/teams
curl http://localhost:8000/agents

# Run team (streaming)
curl -X POST http://localhost:8000/run/team \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "development-swarm",
    "message": "Implement a REST API for user management",
    "stream": true
  }'

# Agno Playground compatible
curl -X POST http://localhost:7777/v1/playground/agents/development-swarm/runs \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a Python function for data validation"
  }'
```

### Background Indexing

```bash
# Start indexing
curl -X POST http://localhost:8000/index/update \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/app/src",
    "recursive": true,
    "file_patterns": ["*.py", "*.js"],
    "force": false
  }'

# Check indexing status
curl http://localhost:8000/index/status/{task_id}

# List active indexing tasks
curl http://localhost:8000/index/tasks
```

### Search Endpoints

```bash
# Unified search (hybrid/vector/BM25/GraphRAG)
curl -X POST http://localhost:8000/memory/search/unified \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication implementation",
    "mode": "hybrid",
    "limit": 20,
    "stream": false
  }'
```

## Monitoring & Observability

### Prometheus Metrics

Access metrics at http://localhost:9090/metrics

Key metrics:
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency
- `memory_operations_total` - Memory operations
- `search_latency_seconds` - Search performance
- `swarm_executions_total` - Swarm execution count
- `embedding_cache_size` - Current cache size
- `system_health` - Overall system health (0/1)

### Grafana Dashboards

Access dashboards at http://localhost:3005 (admin/admin)

Pre-configured dashboards:
- System Overview
- API Performance
- Memory System
- Search Analytics
- Swarm Execution
- Error Rates

### Health Checks

```bash
# Overall health
curl http://localhost:8000/healthz

# Detailed component health
curl http://localhost:8000/health/detailed

# Prometheus metrics
curl http://localhost:8000/metrics
```

### Distributed Tracing

If Jaeger is enabled:
```bash
# View traces at
http://localhost:16686
```

## Rate Limiting

Default limits:
- General endpoints: 100 requests/minute
- Streaming endpoints: 30 requests/minute
- Memory operations: 100 requests/minute
- Search operations: 200 requests/minute
- Indexing: 10 requests/hour

Headers returned:
- `X-RateLimit-Limit` - Request limit
- `X-RateLimit-Remaining` - Remaining requests
- `Retry-After` - Seconds until reset (on 429)

## Troubleshooting

### Common Issues

#### 1. UI Chat Not Working

```bash
# Check API is running
curl http://localhost:8000/healthz

# Check bridge is running
curl http://localhost:7777/v1/playground/status

# Verify agent-ui configuration
cat agent-ui/.env.local
# Should show: NEXT_PUBLIC_DEFAULT_ENDPOINT=http://localhost:7777
```

#### 2. Memory Search Issues

```bash
# Check Supermemory database
sqlite3 tmp/supermemory.db "SELECT COUNT(*) FROM memory_entries;"

# Check Weaviate
curl http://localhost:8080/v1/.well-known/ready

# Rebuild indices
curl -X POST http://localhost:8000/memory/reindex
```

#### 3. Rate Limiting Issues

```bash
# Temporarily disable rate limiting
export RATE_LIMIT_ENABLED=false
docker-compose restart api

# Or increase limits in .env
RATE_LIMIT_RPM=200
STREAMING_RATE_LIMIT_RPM=60
```

#### 4. Service Discovery

```bash
# Check all services
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs api
docker-compose -f docker-compose.production.yml logs celery-worker

# Restart specific service
docker-compose -f docker-compose.production.yml restart api
```

### Debug Mode

Enable debug mode for detailed error messages:

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
docker-compose -f docker-compose.production.yml up
```

### Performance Tuning

```bash
# Increase worker pool
export INDEX_WORKERS=8

# Increase batch size
export INDEX_BATCH_SIZE=200

# Adjust cache settings
export REDIS_TTL=7200  # 2 hours

# Scale Celery workers
docker-compose -f docker-compose.production.yml up -d --scale celery-worker=8
```

## Security Considerations

1. **API Keys**: Never commit API keys. Use environment variables or secrets management.

2. **Rate Limiting**: Always enable in production to prevent abuse.

3. **CORS**: Configure allowed origins appropriately:
   ```python
   CORS_ORIGINS=["https://yourdomain.com"]
   ```

4. **Database Passwords**: Use strong passwords and rotate regularly.

5. **Network Isolation**: Use Docker networks to isolate services.

6. **TLS/SSL**: Use nginx proxy with SSL certificates in production.

## Support

- GitHub Issues: https://github.com/ai-cherry/sophia-intel-ai/issues
- Documentation: https://docs.sophia-intel.ai
- Discord: https://discord.gg/sophia-intel

---

## Summary of Improvements

✅ **Unified Configuration** - Single source of truth with Pydantic  
✅ **Turnkey Deployment** - One-command Docker Compose setup  
✅ **Memory/Search Endpoints** - Full Agno compatibility  
✅ **Observability** - Prometheus metrics + Grafana dashboards  
✅ **Background Indexing** - Celery-based async processing  
✅ **Rate Limiting** - Per-endpoint limits with Redis backend  
✅ **Error Handling** - Comprehensive middleware stack  
✅ **Circuit Breakers** - Resilience for external services  
✅ **Health Checks** - Component-level health monitoring  
✅ **Local-First Design** - Everything runs locally, no external dependencies  

The system is now **production-ready** with enterprise-grade features while maintaining full compatibility with the Agno ecosystem! 🎉