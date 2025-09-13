# Sophia Intel AI - Complete Deployment Guide & System Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Repository Structure](#repository-structure)
3. [Service Architecture](#service-architecture)
4. [Local Deployment Plan](#local-deployment-plan)
5. [Cloud Deployment Plan](#cloud-deployment-plan)
6. [Service Descriptions](#service-descriptions)
7. [Configuration Management](#configuration-management)
8. [Improvement Recommendations](#improvement-recommendations)

## System Overview

Sophia Intel AI is a production-ready AI coding platform with real LLM integration, advanced memory systems, and collaborative AI swarms. The system consists of multiple interconnected services that provide a comprehensive AI development environment.

### Current State Analysis

**Working Services:**
- ✅ Sophia Unified Server (Port 8003) - Main API and orchestration
- ✅ MCP Memory Server (Port 8081) - Memory management with Redis
- ✅ MCP Filesystem Server (Port 8082) - File operations with workspace access
- ✅ MCP Git Server (Port 8084) - Git operations with indexing
- ⚠️ Agent UI (Port 3000) - Frontend interface (requires npm start)
- ⚠️ Bridge API (Port 8000) - Legacy bridge layer (optional)

**Databases & Storage:**
- ✅ Redis (Port 6379) - Caching and session management
- ✅ PostgreSQL (Port 5432) - Primary data storage
- ⚠️ Weaviate (Port 8080) - Vector database (optional)
- ⚠️ Neo4j (Port 7687) - Graph database (optional)

## Repository Structure

```
sophia-intel-ai/
├── 📁 app/                         # Core application logic
│   ├── api/                        # FastAPI routers and endpoints
│   ├── core/                       # Service orchestration & configuration
│   ├── orchestrators/              # Business logic orchestrators
│   ├── connectors/                 # External service integrations
│   ├── memory/                     # Memory management systems
│   ├── mcp/                        # Model Context Protocol services
│   ├── llm/                        # LLM integration and routing
│   ├── swarms/                     # AI agent swarms
│   └── ...                         # Additional modules
├── 📁 sophia-intel-app/                    # React/Next.js frontend (Port 3000)
├── 📁 mcp/                         # MCP server implementations
│   ├── memory_server.py            # Memory management (Port 8081)
│   ├── filesystem.py               # File operations (Port 8082)
│   ├── git_server.py               # Git operations (Port 8084)
│   └── ...
├── 📁 bridge/                      # Legacy API bridge (Port 8000)
├── 📁 sophia-squad/                # Squad orchestration system
├── 📁 config/                      # Configuration files
├── 📁 scripts/                     # Utility and management scripts
├── 📁 infra/                       # Infrastructure and deployment
├── 📁 docs/                        # Documentation
├── backend/main.py                 # Main API entry point
├── make dev-docker                 # Start full stack via Docker (canonical)
├── .env.example                    # Environment configuration template
└── docker-compose.production.yml   # Production deployment
```

## Service Architecture

### Core Services (Must Have)

#### 1. Sophia Unified Server (Port 8003)
- **Purpose**: Main API gateway and orchestration hub
- **Technology**: FastAPI with async support
- **Key Features**:
  - Chat endpoints with context awareness
  - Project management integration
  - Health monitoring and service status
  - WebSocket support for real-time updates
  - Swagger/OpenAPI documentation at `/docs`

#### 2. MCP Memory Server (Port 8081)
- **Purpose**: Distributed memory management and caching
- **Technology**: FastAPI with Redis backend
- **Key Features**:
  - Memory storage and retrieval
  - Redis-based caching
  - Health monitoring endpoint
  - Session management

#### 3. MCP Filesystem Server (Port 8082)
- **Purpose**: File system operations and workspace management
- **Technology**: FastAPI with direct file system access
- **Key Features**:
  - File read/write operations
  - Repository listing and search
  - Symbol indexing and search
  - Dependency graph analysis
  - Workspace path: `/Users/lynnmusil/sophia-intel-ai`

#### 4. MCP Git Server (Port 8084)
- **Purpose**: Git operations and version control
- **Technology**: FastAPI with git integration
- **Key Features**:
  - Git repository management
  - Indexing enabled for faster operations
  - Branch and commit operations
  - Integration with workspace

### Frontend Services

#### 5. Agent UI (Port 3000)
- **Purpose**: Web-based user interface
- **Technology**: React/Next.js with TypeScript
- **Key Features**:
  - Real-time chat interface
  - Dashboard for monitoring services
  - Project management views
  - API integration with main server

### Optional Services (Nice to Have)

#### 6. Bridge API (Port 8000)
- **Purpose**: Legacy API compatibility layer
- **Status**: Optional, being phased out
- **Technology**: FastAPI

#### 7. Vector Database (Weaviate - Port 8080)
- **Purpose**: Vector search and embeddings
- **Status**: Optional for advanced AI features
- **Use Case**: Semantic search and similarity matching

#### 8. Graph Database (Neo4j - Port 7687)
- **Purpose**: Knowledge graph management
- **Status**: Optional for advanced analytics
- **Use Case**: Relationship mapping and graph queries

## Local Deployment Plan

### Prerequisites

```bash
# System Requirements
Python 3.11+
Node.js 18+
Redis Server
PostgreSQL 15+

# Optional (for advanced features)
Docker & Docker Compose
Weaviate
Neo4j
```

### Step-by-Step Setup

#### 1. Environment Configuration

```bash
# Clone repository
git clone <repository-url>
cd sophia-intel-ai

# Create environment configuration
cp .env.example .env

# Edit .env with your credentials
vim .env
```

**Critical Environment Variables:**
```env
# Core API Configuration
SOPHIA_API_PORT=8003
SOPHIA_UI_PORT=3000
HOST=0.0.0.0

# Database Configuration
POSTGRES_URL=postgresql://user:password@localhost:5432/sophia
REDIS_URL=redis://localhost:6379/0

# MCP Service Ports
MCP_MEMORY_PORT=8081
MCP_FILESYSTEM_PORT=8082
MCP_GIT_PORT=8084

# AI Provider Keys (Required)
OPENROUTER_API_KEY=sk-or-v1-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx

# Integration Keys (Optional)
SLACK_BOT_TOKEN=xoxb-xxx
ASANA_PAT_TOKEN=xxx
LINEAR_API_KEY=lin_api_xxx
```

#### 2. Dependency Installation

```bash
# Python dependencies
pip3 install -r requirements.txt

# UI dependencies
cd sophia-intel-app
npm install
cd ..
```

#### 3. Database Setup

```bash
# Start PostgreSQL (macOS with Homebrew)
brew services start postgresql@15

# Start Redis
redis-server --port 6379 --daemonize yes

# Create database
createdb sophia
```

#### 4. Service Startup (Recommended Order)

```bash
# Method 1: Unified Startup (Recommended)
make dev-native

# Method 2: Manual Service Startup
# Start main Sophia server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# Start MCP services
python3 -m uvicorn mcp.memory_server:app --host 0.0.0.0 --port 8081 &
python3 -m uvicorn mcp.filesystem.server:app --host 0.0.0.0 --port 8082 &
python3 -m uvicorn mcp.git_server:app --host 0.0.0.0 --port 8084 &

# Start UI (in separate terminal)
cd sophia-intel-app
npm run dev
```

#### 5. Verification Steps

```bash
# Check service health
curl http://localhost:8003/api/health    # Main API
curl http://localhost:8081/health        # MCP Memory
curl http://localhost:8082/health        # MCP Filesystem
curl http://localhost:8084/health        # MCP Git
curl http://localhost:3000               # Agent UI

# Check API documentation
open http://localhost:8003/docs          # Swagger UI

# Run integration tests
python3 test_sophia_integrations.py
```

### Service Dependencies

```mermaid
graph TD
    A[PostgreSQL:5432] --> B[Sophia Server:8003]
    C[Redis:6379] --> B
    C --> D[MCP Memory:8081]
    C --> E[MCP Filesystem:8082]
    C --> F[MCP Git:8084]
    B --> G[Agent UI:3000]
    
    subgraph "Core Services"
        B
        D
        E
        F
    end
    
    subgraph "Storage"
        A
        C
    end
    
    subgraph "Frontend"
        G
    end
```

### Common Troubleshooting

#### Port Conflicts
```bash
# Check for processes using ports
ps aux | grep python | grep -E "(8003|8081|8082|8084)"

# Kill conflicting processes
pkill -f "uvicorn.*8003"
pkill -f "uvicorn.*8081"
```

#### Database Connection Issues
```bash
# Test PostgreSQL connection
psql postgresql://user:password@localhost:5432/sophia

# Test Redis connection
redis-cli ping
```

#### Environment Configuration Issues
```bash
# Validate environment
python3 -c "from dotenv import load_dotenv; load_dotenv(); import os; print('✓' if os.getenv('OPENROUTER_API_KEY') else '✗ Missing OPENROUTER_API_KEY')"
```

## Cloud Deployment Plan

### AWS Deployment

#### Architecture Overview
```yaml
# EKS Cluster Configuration
Services:
  - Sophia API: EKS Pod (LoadBalancer)
  - MCP Services: EKS Pods (ClusterIP)
  - Agent UI: CloudFront + S3 (Static)
  
Storage:
  - RDS PostgreSQL (Multi-AZ)
  - ElastiCache Redis (Cluster Mode)
  - S3 (File storage, backups)
  
Networking:
  - VPC with public/private subnets
  - Application Load Balancer
  - Route53 for DNS
```

#### Kubernetes Manifests Structure

```bash
k8s/
├── namespace.yaml
├── configmap.yaml
├── secrets.yaml
├── postgres/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── pvc.yaml
├── redis/
│   ├── deployment.yaml
│   └── service.yaml
├── sophia-api/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
├── mcp-services/
│   ├── memory-deployment.yaml
│   ├── filesystem-deployment.yaml
│   ├── git-deployment.yaml
│   └── services.yaml
└── monitoring/
    ├── prometheus.yaml
    └── grafana.yaml
```

#### Sample Kubernetes Deployment

```yaml
# sophia-api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sophia-api
  namespace: sophia
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sophia-api
  template:
    metadata:
      labels:
        app: sophia-api
    spec:
      containers:
      - name: sophia-api
        image: sophia-intel-ai:latest
        ports:
        - containerPort: 8003
        env:
        - name: POSTGRES_URL
          valueFrom:
            secretKeyRef:
              name: sophia-secrets
              key: postgres-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: sophia-secrets
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        readinessProbe:
          httpGet:
            path: /api/health
            port: 8003
          initialDelaySeconds: 30
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8003
          initialDelaySeconds: 60
          periodSeconds: 20
```

### GCP Deployment

#### Architecture Overview
```yaml
Services:
  - GKE Cluster (Autopilot mode)
  - Cloud SQL (PostgreSQL)
  - Cloud Memorystore (Redis)
  - Cloud Storage (File storage)
  - Cloud CDN (Static assets)
  
Security:
  - IAM Service Accounts
  - Workload Identity
  - Cloud KMS (Secret management)
  
Monitoring:
  - Cloud Monitoring
  - Cloud Logging
  - Cloud Trace
```

### Azure Deployment

#### Architecture Overview
```yaml
Services:
  - AKS Cluster
  - Azure Database for PostgreSQL
  - Azure Cache for Redis
  - Azure Blob Storage
  - Azure CDN
  
Security:
  - Azure AD
  - Key Vault
  - Managed Identity
  
Monitoring:
  - Azure Monitor
  - Application Insights
  - Log Analytics
```

### Container Orchestration Approach

#### Docker Images
```dockerfile
# Sophia API Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8003

CMD ["uvicorn", "backend.main:app"]
```

#### Docker Compose for Development
```yaml
# docker-compose.dev.yml
version: '3.9'
services:
  sophia-api:
    build: .
    ports:
      - "8003:8003"
    environment:
      - POSTGRES_URL=postgresql://postgres:password@postgres:5432/sophia
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
  
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: sophia
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Scaling Considerations

#### Horizontal Scaling
- **API Services**: 3-10 replicas based on load
- **MCP Services**: 2-5 replicas (stateless)
- **Database**: Read replicas for PostgreSQL
- **Cache**: Redis cluster mode for high availability

#### Vertical Scaling
```yaml
Resources:
  Sophia API:
    CPU: 250m - 2000m
    Memory: 512Mi - 4Gi
  
  MCP Services:
    CPU: 100m - 500m
    Memory: 256Mi - 1Gi
  
  Database:
    CPU: 2-8 vCPUs
    Memory: 8-32 GB
    Storage: 100GB+ SSD
```

### Security Requirements

#### Network Security
```yaml
Security Measures:
  - VPC/VNet isolation
  - Security groups/NSGs
  - SSL/TLS termination
  - WAF protection
  - Private subnets for databases
```

#### Application Security
```yaml
Security Controls:
  - API key management (AWS Secrets Manager/Azure Key Vault)
  - JWT token authentication
  - RBAC for Kubernetes
  - Container image scanning
  - Regular security updates
```

## Service Descriptions

### Sophia Intel Main App (Port 8003)

**Purpose**: Central orchestration hub and API gateway

**Key Endpoints**:
- `GET /api/health` - System health status
- `POST /api/chat` - AI chat interface
- `GET /api/projects/overview` - Project management
- `GET /api/integrations/status` - Integration status
- `GET /docs` - API documentation

**Dependencies**:
- PostgreSQL for data storage
- Redis for caching
- MCP services for operations
- External AI APIs (OpenRouter, Anthropic)

**Configuration**:
```python
# Key configuration points
CORS_ORIGINS = ["http://localhost:3000"]
API_PORT = 8003
LOG_LEVEL = "INFO"
```

### Agno Builder System

**Current Status**: Integrated into main application
**Purpose**: AI agent building and orchestration
**Location**: `/app/agno/`, `/builder-system/`

**Key Features**:
- Agent template management
- Swarm orchestration
- Model routing and selection
- Quality gates and evaluation

### Agent UI Dashboard (Port 3000)

**Technology Stack**:
- React 18 with Next.js 14
- TypeScript for type safety
- Tailwind CSS for styling
- WebSocket for real-time updates

**Key Features**:
- Real-time chat interface
- Service monitoring dashboard
- Project management views
- Integration status display

**Build Process**:
```bash
cd sophia-intel-app
npm run build    # Production build
npm run dev      # Development server
npm run start    # Production server
```

### MCP Servers

#### Memory Server (Port 8081)
```json
{
  "status": "healthy",
  "server": "memory",
  "redis": "connected",
  "features": [
    "memory.store",
    "memory.retrieve",
    "memory.search",
    "cache.management"
  ]
}
```

#### Filesystem Server (Port 8082)
```json
{
  "status": "ok",
  "workspace": "/Users/lynnmusil/sophia-intel-ai",
  "name": "sophia",
  "read_only": false,
  "capabilities": [
    "fs.list",
    "fs.read",
    "fs.write",
    "fs.delete",
    "repo.list",
    "repo.read",
    "repo.search",
    "symbols.index",
    "symbols.search",
    "dep.graph"
  ]
}
```

#### Git Server (Port 8084)
```json
{
  "status": "healthy",
  "server": "git",
  "indexing": "enabled",
  "workspace": "/workspace",
  "features": [
    "git.status",
    "git.commit",
    "git.branch",
    "git.merge",
    "indexing.files",
    "indexing.commits"
  ]
}
```

### Squad Systems

#### OpenRouter Squad
**Purpose**: Multi-model AI orchestration via OpenRouter
**Models**: 300+ LLM models including GPT-4, Claude, Gemini
**Configuration**: Handled through Portkey gateway

#### LiteLLM Squad
**Purpose**: Lightweight LLM proxy and routing
**Features**: Model fallbacks, caching, cost optimization

#### AIMLAPI Squad
**Purpose**: Enhanced AI completions with specialized models
**Status**: Optional enhancement layer

### Claude Squad Groups

**Purpose**: Specialized Claude model configurations
**Groups**:
- `claude-3-5-sonnet` - Primary reasoning model
- `claude-3-haiku` - Fast response model
- `claude-3-opus` - Complex task model

## Configuration Management

### Environment Configuration Hierarchy

1. **System Defaults**: Built into application
2. **Environment Files**: `.env`, `.env.local`
3. **Command Line**: Override via CLI arguments
4. **Environment Variables**: OS-level overrides

### Critical Configuration Files

```bash
# Configuration files priority order
1. .env                    # Local development
2. .env.example           # Template/documentation
3. config/manager.py      # Unified config management
4. app/core/unified_config.py  # Application config
```

### Configuration Validation

```python
# Built-in validation checks
- API key presence validation
- Port conflict detection
- Database connectivity
- Service dependency checks
```

## Improvement Recommendations

### Architecture Simplifications

#### 1. Service Consolidation Opportunities

**High Priority**:
- **Merge Bridge API**: Deprecate port 8000, consolidate into main API (8003)
- **Unify Configuration**: Single source of truth for all environment variables
- **Standardize Logging**: Consistent logging format across all services

**Medium Priority**:
- **MCP Service Consolidation**: Consider combining filesystem/git/memory into unified MCP gateway
- **Database Simplification**: Use PostgreSQL as primary store, Redis only for caching

#### 2. Configuration Management Improvements

```yaml
Proposed Structure:
  config/
    ├── base.yaml           # Base configuration
    ├── development.yaml    # Development overrides
    ├── production.yaml     # Production overrides
    ├── secrets.env         # Encrypted secrets
    └── validation.py       # Configuration validation
```

#### 3. Service Discovery Enhancement

```python
# Proposed service registry
class ServiceRegistry:
    def register_service(self, name: str, port: int, health_check: str)
    def discover_service(self, name: str) -> ServiceInfo
    def health_check_all(self) -> Dict[str, bool]
```

### Monitoring and Observability Enhancements

#### 1. Unified Logging
```yaml
Logging Strategy:
  - Structured JSON logging
  - Centralized log aggregation
  - Request tracing across services
  - Error correlation and alerting
```

#### 2. Metrics Collection
```yaml
Key Metrics:
  - API response times
  - MCP service utilization
  - Database connection pool status
  - AI model usage and costs
  - Error rates by service
```

#### 3. Health Monitoring
```yaml
Health Checks:
  - Deep health checks (not just HTTP 200)
  - Dependency health verification
  - Resource utilization monitoring
  - Automated recovery procedures
```

### Security Hardening Steps

#### 1. API Security
```yaml
Security Enhancements:
  - Rate limiting per endpoint
  - JWT token validation
  - API key rotation procedures
  - Input validation and sanitization
  - CORS policy refinement
```

#### 2. Network Security
```yaml
Network Hardening:
  - Service-to-service authentication
  - Network segmentation
  - TLS encryption for internal communication
  - Secret management improvements
```

#### 3. Data Protection
```yaml
Data Security:
  - Database encryption at rest
  - PII data handling procedures
  - Backup encryption
  - Audit logging for sensitive operations
```

### Performance Optimizations

#### 1. Caching Strategy
```yaml
Caching Improvements:
  - Multi-level caching (L1: in-memory, L2: Redis)
  - Cache invalidation strategies
  - Preemptive cache warming
  - Cache hit/miss monitoring
```

#### 2. Database Optimization
```yaml
Database Improvements:
  - Connection pooling optimization
  - Query performance monitoring
  - Index optimization
  - Read replica utilization
```

#### 3. API Performance
```yaml
API Optimizations:
  - Response compression
  - Async processing for heavy operations
  - Background job processing
  - API response caching
```

## Migration Path

### Phase 1: Stabilization (Immediate)
1. ✅ Complete environment configuration audit
2. ✅ Implement unified startup script
3. ✅ Add comprehensive health checks
4. 🔄 Standardize logging across services
5. 🔄 Create monitoring dashboard

### Phase 2: Consolidation (1-2 weeks)
1. Deprecate Bridge API (port 8000)
2. Implement service registry
3. Unify configuration management
4. Add automated testing pipeline
5. Implement security hardening

### Phase 3: Optimization (2-4 weeks)
1. Implement performance optimizations
2. Add comprehensive monitoring
3. Create cloud deployment automation
4. Implement CI/CD pipeline
5. Add disaster recovery procedures

### Phase 4: Enhancement (1-2 months)
1. Advanced AI features integration
2. Multi-tenant support
3. Plugin system implementation
4. Advanced analytics and reporting
5. Mobile/API client development

## Quick Start Commands

```bash
# Development Setup
git clone <repo>
cd sophia-intel-ai
cp .env.example .env
# Edit .env with your credentials
pip3 install -r requirements.txt
make dev-native

# Production Setup
docker-compose -f docker-compose.production.yml up -d

# Health Check
curl http://localhost:8003/api/health

# Stop Services
pkill -f "sophia_unified_server"
pkill -f "uvicorn.*mcp"
```

This comprehensive guide provides everything needed to understand, deploy, and improve the Sophia Intel AI platform across different environments and use cases.
