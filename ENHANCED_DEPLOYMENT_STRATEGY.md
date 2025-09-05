# Enhanced Deployment Strategy for AI Agent Swarm System

## Executive Summary

This document combines immediate local deployment fixes with strategic repository improvements to create a comprehensive deployment and development strategy for the AI Agent Swarm system.

## Current State Analysis

### Immediate Issues (From Local Deployment)

1. **Port/URL Configuration Drift**
   - UI persists old endpoints (8000/7777) in localStorage
   - Needs Zustand migration to force 8003
2. **UI/API Integration Problems**

   - Select component crashes on empty values
   - API returns "No solution generated" due to nested response structures
   - Route path misalignment (/v1/playground/\* vs direct paths)

3. **Development Environment Issues**
   - Node.js OOM errors during Next.js development
   - Duplicate files (endpointUtils vs endpointutils)
   - Legacy UI directory causing confusion

### Repository Architecture Insights

#### Strengths

- Unified FastAPI server structured for MCP servers, hybrid search, and swarm orchestration
- Modern embedding pipeline with tiered strategy (ModernBERT/Voyage/Cohere)
- Async Git tooling implemented as Tool classes
- Docker Compose for local deployment
- Pulumi/Fly.io for cloud deployment

#### Placeholders Requiring Implementation

- Supermemory store (core memory persistence)
- Search engine implementations
- Repository indexing pipeline
- MCP protocol endpoints
- Swarm orchestrator completion
- Evaluation gates and decision memory

## Phase 1: Immediate Stabilization (1-2 days)

### 1.1 Fix Local Development Environment

```bash
# Create start-local.sh with health checks
#!/bin/bash
set -e

echo "🚀 Starting AI Agent Swarm Local Development"

# Kill any existing processes
pkill -f "unified_server" || true
pkill -f "next dev" || true

# Start services with proper configuration
docker-compose -f docker-compose.minimal.yml up -d

# Wait for backend health
until curl -sf http://localhost:8003/healthz; do
  echo "Waiting for API..."
  sleep 1
done

# Start UI with memory allocation
cd agent-ui
rm -rf .next
NODE_OPTIONS="--max-old-space-size=4096" npm run dev &

echo "✅ Environment ready at http://localhost:3000"
```

### 1.2 Apply Critical Fixes

1. **Zustand Migration** (agent-ui/src/store.ts)

   ```typescript
   persist: {
     version: 2,
     migrate: (state: any) => {
       if (state.selectedEndpoint?.includes(':8000') ||
           state.selectedEndpoint?.includes(':7777')) {
         state.selectedEndpoint = 'http://localhost:8003';
       }
       return state;
     }
   }
   ```

2. **API Response Normalization** (app/api/unified_server.py)

   ```python
   def _extract_solution(result: dict) -> str:
       """Extract content from nested structures"""
       paths = [
           lambda r: r.get('content'),
           lambda r: r.get('result', {}).get('content'),
           lambda r: r.get('choices', [{}])[0].get('message', {}).get('content')
       ]
       for path in paths:
           try:
               content = path(result)
               if content: return content
           except: continue
       return "Error: Unable to extract solution"
   ```

3. **Next.js Rewrites** (agent-ui/next.config.ts)

   ```typescript
   async rewrites() {
     return [{
       source: '/api/:path*',
       destination: 'http://localhost:8003/:path*'
     }];
   }
   ```

## Phase 2: Core Infrastructure (1 week)

### 2.1 Implement Supermemory Store

```python
# app/memory/supermemory_store.py
class SupermemoryStore:
    """Persistent cross-task memory with vector search"""

    def __init__(self, weaviate_client, redis_client):
        self.weaviate = weaviate_client
        self.redis = redis_client
        self.embedder = ModernBERTEmbedder()

    async def add_memory(self, content: str, metadata: dict):
        # Embed content
        embedding = await self.embedder.embed(content)

        # Store in Weaviate
        memory_id = str(uuid.uuid4())
        self.weaviate.data_object.create({
            "content": content,
            "metadata": metadata,
            "embedding": embedding
        }, class_name="Memory")

        # Cache in Redis
        await self.redis.set(f"memory:{memory_id}", content, ex=3600)

        return memory_id

    async def search_memory(self, query: str, limit: int = 10):
        query_embedding = await self.embedder.embed(query)
        results = self.weaviate.query.get("Memory").with_near_vector({
            "vector": query_embedding
        }).with_limit(limit).do()
        return results
```

### 2.2 Wire MCP Integration

```python
# app/mcp/unified_mcp_server.py
class UnifiedMCPServer:
    """Expose filesystem, git, and memory operations via MCP"""

    def __init__(self):
        self.filesystem = FilesystemMCP()
        self.git = GitMCP()
        self.memory = MemoryMCP()

    @mcp_method("filesystem/read")
    async def read_file(self, path: str):
        return await self.filesystem.read(path)

    @mcp_method("git/status")
    async def git_status(self):
        return await self.git.status()

    @mcp_method("memory/search")
    async def search_memory(self, query: str):
        return await self.memory.search(query)
```

### 2.3 Repository Indexing Pipeline

```python
# app/memory/repo_indexer.py
class RepositoryIndexer:
    """Incremental repository embedding and indexing"""

    async def index_repository(self, repo_path: str):
        # Get changed files since last index
        changed_files = await self.get_changed_files(repo_path)

        for file_path in changed_files:
            # Chunk file content
            chunks = self.chunk_file(file_path)

            # Embed and store each chunk
            for chunk in chunks:
                embedding = await self.embedder.embed(chunk.content)
                await self.store_chunk(chunk, embedding)

        # Update index metadata
        await self.update_index_metadata()
```

## Phase 3: Swarm Orchestration (2 weeks)

### 3.1 Complete UnifiedSwarmOrchestrator

```python
# app/swarms/unified_orchestrator.py
class UnifiedSwarmOrchestrator:
    """Full swarm orchestration with patterns and evaluation"""

    def __init__(self):
        self.teams = self.load_team_configs()
        self.memory = SupermemoryStore()
        self.evaluator = SwarmEvaluator()

    async def execute_task(self, task: str, pattern: str = "consensus"):
        # Plan execution strategy
        plan = await self.create_execution_plan(task, pattern)

        # Execute with selected pattern
        if pattern == "consensus":
            result = await self.consensus_pattern(plan)
        elif pattern == "adversarial":
            result = await self.adversarial_pattern(plan)
        elif pattern == "hierarchical":
            result = await self.hierarchical_pattern(plan)

        # Evaluate and store results
        evaluation = await self.evaluator.evaluate(result)
        await self.memory.add_memory(result, {"evaluation": evaluation})

        return result
```

### 3.2 Agent Role Definitions

```yaml
# app/config/agent_roles.yaml
roles:
  strategic_planner:
    model: "google/gemini-2.5-pro"
    temperature: 0.7
    prompts:
      - "Analyze repository structure and dependencies"
      - "Create high-level implementation strategy"

  primary_coder:
    model: "deepseek/deepseek-chat-v3"
    temperature: 0.3
    prompts:
      - "Implement code following best practices"
      - "Use type hints and comprehensive docstrings"

  code_critic:
    model: "anthropic/claude-3-5-sonnet"
    temperature: 0.5
    prompts:
      - "Review code for bugs and vulnerabilities"
      - "Suggest performance optimizations"
```

## Phase 4: Cloud Deployment (1 week)

### 4.1 Enhanced Pulumi Configuration

```typescript
// pulumi/agent-orchestrator/index.ts
import * as pulumi from "@pulumi/pulumi";
import { FlyApp } from "../shared/fly-app";

const orchestrator = new FlyApp("agent-orchestrator", {
  appName: "sophia-intel-orchestrator",
  image: "ghcr.io/sophia-intel/orchestrator:latest",

  // Enhanced configuration
  env: {
    NODE_ENV: "production",
    API_URL: "https://api.sophia-intel.ai",
    OPENROUTER_API_KEY: pulumi.secret(process.env.OPENROUTER_API_KEY),
    PORTKEY_API_KEY: pulumi.secret(process.env.PORTKEY_API_KEY),
  },

  // Auto-scaling configuration
  services: [
    {
      ports: [{ port: 8003, handlers: ["http", "tls"] }],
      internal_port: 8003,
      protocol: "tcp",

      // Scaling policies
      min_machines_running: 2,
      max_machines: 10,
      auto_scale_policy: {
        type: "connections",
        hard_limit: 1000,
        soft_limit: 500,
      },
    },
  ],

  // Health checks
  checks: {
    health: {
      type: "http",
      port: 8003,
      path: "/healthz",
      interval: "10s",
      timeout: "2s",
    },
  },

  // Persistent volumes for memory
  volumes: [
    {
      source: "sophia_memory",
      destination: "/data",
      size_gb: 10,
    },
  ],

  // Observability
  metrics: {
    enabled: true,
    port: 9090,
    path: "/metrics",
  },
});
```

### 4.2 Secrets Management

```bash
# Setup Pulumi ESC for secrets
pulumi env init sophia-intel/production
pulumi env set sophia-intel/production --secret OPENROUTER_API_KEY $OPENROUTER_API_KEY
pulumi env set sophia-intel/production --secret PORTKEY_API_KEY $PORTKEY_API_KEY
pulumi env set sophia-intel/production --secret DATABASE_URL $DATABASE_URL

# Use in deployment
pulumi up --env production
```

### 4.3 Disaster Recovery

```yaml
# fly.backup.yaml
backup:
  schedule: "0 2 * * *" # Daily at 2 AM
  retention: 7 # Keep 7 days
  targets:
    - volume: sophia_memory
      destination: s3://sophia-backups/memory/
    - database: sophia_postgres
      destination: s3://sophia-backups/db/

  restore:
    script: scripts/restore.sh
    verification: scripts/verify-restore.sh
```

## Phase 5: Production Readiness (1 week)

### 5.1 Monitoring & Observability

```yaml
# monitoring/prometheus.yml
scrape_configs:
  - job_name: "agent-orchestrator"
    static_configs:
      - targets: ["orchestrator.fly.dev:9090"]
    metrics_path: "/metrics"

  - job_name: "memory-service"
    static_configs:
      - targets: ["memory.fly.dev:9090"]

  - job_name: "ui-dashboard"
    static_configs:
      - targets: ["ui.fly.dev:9090"]

alerts:
  - name: high_memory_usage
    expr: memory_usage_percent > 90
    for: 5m
    annotations:
      summary: "High memory usage detected"

  - name: api_errors
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
    annotations:
      summary: "High error rate detected"
```

### 5.2 CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          npm test
          python -m pytest

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build Docker images
        run: |
          docker build -t ghcr.io/sophia-intel/orchestrator:${{ github.sha }} .
          docker push ghcr.io/sophia-intel/orchestrator:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy with Pulumi
        env:
          PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
        run: |
          pulumi up --yes --stack production
```

## Implementation Priority Matrix

| Priority | Component                  | Timeline | Dependencies    | Impact                          |
| -------- | -------------------------- | -------- | --------------- | ------------------------------- |
| P0       | Local deployment fixes     | 1-2 days | None            | Critical - Unblocks development |
| P0       | Supermemory implementation | 3 days   | Weaviate, Redis | Critical - Core functionality   |
| P1       | MCP integration            | 3 days   | Supermemory     | High - Enables agent operations |
| P1       | Repository indexing        | 2 days   | Embeddings      | High - Context awareness        |
| P2       | Swarm orchestrator         | 1 week   | Memory, MCP     | Medium - Advanced patterns      |
| P2       | Cloud deployment           | 1 week   | Core features   | Medium - Scalability            |
| P3       | UI consolidation           | 3 days   | API stability   | Low - UX improvement            |
| P3       | Monitoring setup           | 2 days   | Deployment      | Low - Observability             |

## Risk Mitigation

### Technical Risks

1. **Memory leaks in Node.js**: Use NODE_OPTIONS and implement proper cleanup
2. **Embedding pipeline performance**: Implement caching and batch processing
3. **Swarm coordination failures**: Add circuit breakers and fallback strategies

### Security Risks

1. **API key exposure**: Use Pulumi ESC and Fly secrets
2. **Unauthorized Git operations**: Implement approval workflows
3. **Memory injection attacks**: Sanitize all inputs before embedding

### Operational Risks

1. **Service dependencies**: Health checks and graceful degradation
2. **Data loss**: Regular backups and point-in-time recovery
3. **Cost overruns**: Implement cost monitoring and alerts

## Success Metrics

### Development Metrics

- Local environment startup time < 30 seconds
- Zero crashes in 24-hour development sessions
- API response time < 200ms for standard operations

### Production Metrics

- 99.9% uptime SLA
- < 1% error rate
- < 500ms p95 latency
- Successful auto-scaling under load

### Business Metrics

- Repository analysis completion < 5 minutes
- Swarm task success rate > 80%
- Memory retrieval accuracy > 90%

## Next Steps

1. **Immediate (Today)**

   - Apply local deployment fixes
   - Test UI/API connectivity
   - Document current placeholder locations

2. **This Week**

   - Implement Supermemory store
   - Wire MCP endpoints
   - Begin repository indexing

3. **Next Week**

   - Complete swarm orchestrator
   - Setup cloud deployment
   - Implement monitoring

4. **This Month**
   - Full production deployment
   - Performance optimization
   - Security audit

## Conclusion

This enhanced deployment strategy addresses both immediate stabilization needs and long-term architectural goals. By following this phased approach, the AI Agent Swarm system can evolve from its current state with placeholders to a production-ready, scalable platform capable of intelligent code analysis and autonomous development operations.

The key is to maintain momentum by fixing critical issues first while building toward the comprehensive vision of a fully autonomous AI development system.
