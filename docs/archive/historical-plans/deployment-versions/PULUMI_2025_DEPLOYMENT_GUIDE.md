# Pulumi 2025 Deployment Guide - Sophia Intel AI

## 🎯 Overview

This guide covers the complete deployment of the modernized Sophia Intel AI system using Pulumi 2025 best practices. The system has been restructured into microservices with proper separation of concerns, state-of-the-art infrastructure patterns, and consolidated implementations.

## 📋 Prerequisites

### Required Software
- **Pulumi CLI** v3.171+ (with AI-powered diagnostics)
- **Python** 3.11+
- **Node.js** 18+ (for UI components)
- **Docker** & Docker Compose
- **Git** for version control

### API Keys and Secrets
Ensure you have the following API keys configured:

```bash
# Core LLM Providers (via Portkey)
export PORTKEY_API_KEY="pk-live-your-portkey-key"
export PORTKEY_OPENROUTER_VK="pk-live-your-openrouter-virtual-key"
export PORTKEY_ANTHROPIC_VK="pk-live-your-anthropic-virtual-key"
export PORTKEY_OPENAI_VK="pk-live-your-openai-virtual-key"
export PORTKEY_TOGETHER_VK="pk-live-your-together-virtual-key"
export PORTKEY_GROQ_VK="pk-live-your-groq-virtual-key"

# Infrastructure
export FLY_API_TOKEN="fly-api-token"
export LAMBDA_LABS_API_KEY="lambda-labs-key"
export NEON_DATABASE_URL="postgresql://user:pass@host/db"

# Security
export JWT_SECRET="your-jwt-secret"
export ENCRYPTION_KEY="your-encryption-key"
export INTERNAL_SERVICE_API_KEY="internal-service-key"
```

## 🏗️ Architecture Overview

The modernized system follows Pulumi 2025 microservices patterns:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Sophia Intel AI - 2025 Architecture          │
├─────────────────────────────────────────────────────────────────┤
│  Client Layer: Web UI, CLI, API Clients                        │
├─────────────────────────────────────────────────────────────────┤
│  API Gateway (networking): Load balancing, authentication       │
├─────────────────────────────────────────────────────────────────┤
│  Microservices:                                                 │
│  ├── agent-orchestrator: LLM execution + swarm patterns        │
│  ├── vector-store: 3-tier embeddings + semantic search         │
│  ├── mcp-server: Unified memory + MCP protocol                 │
│  └── ui: React applications                                     │
├─────────────────────────────────────────────────────────────────┤
│  Infrastructure:                                                │
│  ├── Fly.io: Container orchestration + auto-scaling            │
│  ├── Neon PostgreSQL: Persistent data storage                  │
│  ├── Redis: Caching + session management                       │
│  ├── Weaviate: Vector database for embeddings                  │
│  └── Lambda Labs: GPU compute for heavy workloads              │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Deployment Steps

### Step 1: Initialize Pulumi Environment

```bash
# Clone and setup
git clone <repository-url>
cd sophia-intel-ai

# Set up Pulumi access token
export PULUMI_ACCESS_TOKEN="pul-your-token"
pulumi login

# Create Pulumi ESC environments
pulumi env init sophia-intel-ai/dev --file pulumi/environments/dev.yaml
pulumi env init sophia-intel-ai/staging --file pulumi/environments/staging.yaml  
pulumi env init sophia-intel-ai/prod --file pulumi/environments/prod.yaml
pulumi env init sophia-intel-ai/base --file pulumi/environments/sophia-intel-base.yaml
```

### Step 2: Deploy Infrastructure Projects

Deploy in dependency order:

#### 2.1 Shared Components
```bash
cd pulumi/shared
pip install -r requirements.txt
pulumi stack init dev
pulumi config set environment dev
pulumi up --copilot  # Use AI-powered explanations
```

#### 2.2 Database Infrastructure
```bash
cd ../database
pip install -r requirements.txt
pulumi stack init dev
pulumi config set environment dev
pulumi config set postgres_db_name sophia_intel_ai_dev
pulumi up --copilot
```

#### 2.3 Vector Store
```bash
cd ../vector-store
pip install -r requirements.txt
pulumi stack init dev
pulumi config set environment dev
pulumi config set weaviate_memory_gb 2
pulumi up --copilot
```

#### 2.4 Agent Orchestrator
```bash
cd ../agent-orchestrator
pip install -r requirements.txt
pulumi stack init dev
pulumi config set environment dev
pulumi config set lambda_labs_gpu_count 2
pulumi up --copilot
```

#### 2.5 MCP Server
```bash
cd ../mcp-server
pip install -r requirements.txt
pulumi stack init dev
pulumi config set environment dev
pulumi config set enable_mcp_protocol true
pulumi up --copilot
```

#### 2.6 API Gateway
```bash
cd ../networking
pip install -r requirements.txt
pulumi stack init dev
pulumi config set environment dev
pulumi config set domain sophia-intel-ai-dev.fly.dev
pulumi up --copilot
```

### Step 3: Verify Deployment

```bash
# Check all stack outputs
pulumi stack output --show-secrets

# Health checks
curl https://sophia-intel-ai-dev.fly.dev/healthz

# Test API endpoints
curl -X POST https://sophia-intel-ai-dev.fly.dev/api/memory/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 5}'
```

## 🔧 Configuration Management

### Pulumi ESC Environment Structure

```yaml
# Development environment
pulumi/environments/dev.yaml:
  - Lower resource allocation
  - Debug logging enabled
  - Experimental features on
  - Cost-optimized model pools

# Production environment  
pulumi/environments/prod.yaml:
  - High availability (3+ instances)
  - Auto-scaling enabled
  - Security hardened
  - Premium model pools
  - Full observability stack
```

### Service Configuration

Each service is configured via environment variables from Pulumi ESC:

```bash
# Agent Orchestrator
PORTKEY_API_KEY=<from-ESC>
MAX_CONCURRENT_SWARMS=10
LAMBDA_LABS_API_KEY=<from-ESC>

# Vector Store
EMBEDDING_TIER_S_MODEL=voyage-3-large
EMBEDDING_TIER_A_MODEL=cohere/embed-multilingual-v3.0
EMBEDDING_TIER_B_MODEL=BAAI/bge-base-en-v1.5

# MCP Server
ENABLE_MCP_PROTOCOL=true
CONNECTION_POOL_SIZE=20
UNIFIED_MEMORY_CONFIG=<from-ESC>
```

## 🔒 Security Configuration

### API Key Management
- All secrets stored in Pulumi ESC
- API keys rotated automatically (30-day cycle in prod)
- Internal service authentication via JWT

### Network Security
- TLS 1.3 minimum for all connections
- CORS configured for allowed origins only
- Rate limiting: 100 req/min (dev), 1000 req/min (prod)

### Data Protection
- Database connections use SSL mode=require
- Encryption at rest for all persistent data
- PII detection and redaction in logs

## 📊 Monitoring and Observability

### Health Checks
- All services expose `/healthz` endpoints
- Database connectivity verified
- Model provider availability checked

### Metrics Collection
- Prometheus metrics on port :9090
- Custom metrics for LLM usage, cache hit rates
- Performance tracking for embedding generation

### Logging
- Structured JSON logging
- Log levels: DEBUG (dev), INFO (staging), WARN (prod)
- Centralized via Fly.io logging

## 🔄 Scaling Configuration

### Auto-Scaling Policies

```yaml
# Development
instances: 1 per service
cpu_threshold: 80%
memory_threshold: 80%

# Production  
api_gateway: 2-10 instances
agent_orchestrator: 3-20 instances
vector_store: 2-15 instances
mcp_server: 2-12 instances
```

### Resource Allocation

```yaml
Development:
  api_gateway: 512MB RAM, 0.5 CPU
  agent_orchestrator: 2GB RAM, 1 CPU
  vector_store: 1GB RAM, 1 CPU
  mcp_server: 1GB RAM, 1 CPU

Production:
  api_gateway: 1GB RAM, 1 CPU
  agent_orchestrator: 4GB RAM, 4 CPU
  vector_store: 2GB RAM, 2 CPU
  mcp_server: 2GB RAM, 2 CPU
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Pulumi Stack Conflicts
```bash
# Check for conflicting stacks
pulumi stack ls
pulumi stack select <correct-stack>

# Use AI diagnostics for errors
pulumi up --copilot
```

#### 2. Service Discovery Issues
```bash
# Verify StackReference connections
pulumi stack output
pulumi config get <service>_url

# Check internal DNS resolution
fly ssh console -a <app-name>
nslookup service-name.internal
```

#### 3. Model Provider Errors
```bash
# Test Portkey connectivity
curl -H "Authorization: Bearer $PORTKEY_API_KEY" \
     https://api.portkey.ai/v1/models

# Verify virtual key configuration
pulumi config get --secret portkeyOpenRouterVK
```

### Performance Issues

#### High Latency
- Check model pool failover chains
- Verify embedding cache hit rates
- Monitor Lambda Labs GPU utilization

#### Memory Issues
- Review connection pool sizes
- Check Redis cache eviction policies
- Monitor Weaviate memory usage

## 📚 API Documentation

### Core Endpoints

```bash
# Health and status
GET  /healthz
GET  /stats

# Agent orchestration
POST /api/teams/execute
POST /api/swarms/run
GET  /api/agents

# Memory operations  
POST /api/memory/add
POST /api/memory/search
GET  /api/memory/stats

# Embedding services
POST /api/embeddings/generate
POST /api/search/hybrid
GET  /api/embeddings/stats

# MCP protocol
POST /mcp/memory/add
POST /mcp/memory/search
GET  /mcp/health
```

### Response Formats

All APIs return structured JSON with consistent error handling:

```json
{
  "success": true,
  "data": { ... },
  "metadata": {
    "timestamp": "2025-08-31T21:30:00Z",
    "latency_ms": 150,
    "service": "agent-orchestrator"
  }
}
```

## 🚀 Production Deployment

### Staging Environment
```bash
# Deploy to staging
pulumi stack init staging
pulumi config set environment staging
pulumi up --copilot

# Run integration tests
npm run test:integration:staging
```

### Production Deployment
```bash
# Blue-green deployment
pulumi stack init prod-blue
pulumi config set environment prod
pulumi up --copilot

# Traffic switching after validation
pulumi stack init prod  
pulumi up --copilot
```

## 📈 Performance Benchmarks

### Target Metrics
- **API Response Time**: <200ms P95
- **Memory Search**: <50ms average
- **Embedding Generation**: <100ms average
- **Swarm Execution**: <30s for 4-agent workflows
- **Cache Hit Rate**: >80% for embeddings
- **Uptime**: 99.9% availability

## 🔄 Maintenance

### Regular Tasks
- **Weekly**: Review metrics and performance
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Model performance evaluation
- **Annually**: Architecture review and optimization

### Backup Strategy
- **Database**: Daily automated backups (30-day retention)
- **Configuration**: Versioned in Git
- **Secrets**: Encrypted backups via Pulumi ESC

---

This deployment guide provides comprehensive coverage of the modernized Sophia Intel AI system using Pulumi 2025 best practices. The consolidated architecture eliminates technical debt while providing enterprise-grade scalability and reliability.