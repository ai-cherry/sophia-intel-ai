# Sophia Intel - AI Agent Platform

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "GitHub Codespaces Environment"
        subgraph "Frontend Layer"
            UI[Agent UI - React :3000]
        end
        
        subgraph "API Layer"
            API[FastAPI Backend :8000]
            MCP[MCP Server :8001]
            AGENT[Coding Agent API :7777]
        end
        
        subgraph "Service Layer"
            ORCH[Orchestrator Service]
            LAMBDA[Lambda Labs Client]
        end
        
        subgraph "Agent Layer"
            CODING[Coding Agent - Agno]
            BASE[Base Agent System]
        end
        
        subgraph "Storage Layer"
            MEM[Memory Service]
            QDRANT[(Qdrant Vector DB)]
            SQLITE[(SQLite - Agno)]
        end
    end
    
    UI --> API
    API --> ORCH
    MCP --> MEM
    CODING --> MCP
    CODING --> SQLITE
    MEM --> QDRANT
```

## 🚀 Quickstart (GitHub Codespaces)

### Step 1: Environment Setup

1. **Copy environment configuration:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your API keys:**
   ```bash
   # Required API keys for full functionality
   OPENROUTER_API_KEY=sk-or-v1-your-openrouter-key-here
   LAMBDA_CLOUD_API_KEY=ll-your-lambda-labs-key-here  # Optional for GPU features
   
   # Update Qdrant URL if using cloud instance
   QDRANT_URL=https://your-cluster-id.us-east1-0.gcp.cloud.qdrant.io:6333
   QDRANT_API_KEY=your-qdrant-cloud-api-key
   ```

### Step 2: Install Dependencies

```bash
# Install Python dependencies using uv
uv pip install -r requirements.txt

# Verify installation
python -c "from config.config import settings; print(f'✅ Config loaded: {settings.ENVIRONMENT}')"
```

### Step 3: Start Infrastructure Services

Choose one of these options:

**Option A: Local Services (Docker)**
```bash
# Start PostgreSQL, Redis, and Qdrant locally
docker-compose up -d

# Verify services are healthy
docker-compose ps
```

**Option B: Cloud Services**
If using cloud services, update your `.env` with production URLs and skip docker-compose.

### Step 4: Start Application Services

Start each service in a separate terminal (or use tmux/screen):

**Terminal 1: MCP Memory Server**
```bash
# Start the MCP server for context storage and retrieval
uvicorn mcp_servers.unified_mcp_server:app --host 0.0.0.0 --port 8001 --reload

# Should show: "Uvicorn running on http://0.0.0.0:8001"
```

**Terminal 2: Backend API**
```bash
# Start the main FastAPI backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Should show: "Uvicorn running on http://0.0.0.0:8000"
```

**Terminal 3: Coding Agent API**
```bash
# Start the Agno-powered coding agent server
python scripts/agno_api.py

# Should show: "Uvicorn running on http://0.0.0.0:7777"
```

**Terminal 4: Frontend (Optional)**
```bash
cd frontend
npm install
npm start

# Should show: "Local: http://localhost:3000"
```

### Step 5: Verify Installation

Test all services are running correctly:

```bash
# Test backend health
curl http://localhost:8000/health
# Expected: {"status":"ok","env":"development"}

# Test MCP server
curl http://localhost:8001/health
# Expected: {"status":"healthy","timestamp":...}

# Test coding agent
curl http://localhost:7777/health
# Expected: {"status":"healthy","agents":{...}}

# View API documentation
open http://localhost:8001/docs  # MCP API docs
open http://localhost:7777/docs  # Agent API docs
```

### Step 6: Test Agent Functionality

Send a test request to the coding agent:

```bash
curl -X POST http://localhost:7777/agent/coding \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "quickstart-test",
    "code": "def greet(name):\n    print(f\"Hello {name}\")",
    "query": "Add type hints and docstring to this function"
  }'
```

Expected response format:
```json
{
  "success": true,
  "result": {
    "summary": "Added type hints and comprehensive docstring",
    "patch": "--- a/file\n+++ b/file\n@@ -1,2 +1,7 @@\n-def greet(name):\n-    print(f\"Hello {name}\")\n+def greet(name: str) -> None:\n+    \"\"\"Greet a person by name.\n+    \n+    Args:\n+        name: The person's name to greet\n+    \"\"\"\n+    print(f\"Hello {name}\")"
  },
  "duration": 2.34,
  "agent": "CodingAgent"
}
```

## 📁 Project Structure

```
sophia-intel/
├── .devcontainer/              # GitHub Codespaces configuration
│   └── devcontainer.json      # Container setup with Python 3.11 + Node.js
├── .github/                    # CI/CD and development workflows
│   ├── workflows/ci.yml        # Comprehensive CI pipeline with uv
│   ├── copilot-instructions.md # Development standards for GitHub Copilot
│   └── pull_request_template.md # PR template with checklist
├── .prompts/                   # Reusable prompt templates
│   ├── debug-issue.md          # MCP-based debugging workflow
│   └── deploy-infra.md         # Infrastructure deployment with Pulumi
├── .vscode/                    # VS Code configuration
│   ├── settings.json           # Editor settings and environment variables
│   └── mcp.json               # MCP server configuration for Lambda gateway
├── agents/                     # Agent implementations
│   ├── base_agent.py          # Base agent with concurrency and error handling
│   └── coding_agent.py        # Agno-powered coding agent with MCP integration
├── backend/                    # FastAPI main API
│   └── main.py                # Health and metrics endpoints
├── config/                     # Configuration management
│   ├── config.py              # Pydantic settings with YAML + env loading
│   └── sophia.yaml            # Default configuration (cloud-ready)
├── docs/                       # Documentation
│   └── AGENT_UI.md            # Comprehensive Agent UI setup guide
├── frontend/                   # React-based Agent UI
│   ├── src/                   # React components and logic
│   ├── public/                # Static assets
│   └── package.json           # Node.js dependencies
├── mcp_servers/                # Memory & Context Protocol servers
│   ├── memory_service.py      # Async Qdrant vector storage with health checks
│   └── unified_mcp_server.py  # FastAPI MCP server with full API spec
├── services/                   # External service clients
│   ├── lambda_client.py       # GPU resource management client
│   └── orchestrator.py        # Request routing with circuit breakers
├── scripts/                    # Utility scripts
│   └── agno_api.py            # FastAPI server for agent endpoints
├── tests/                      # Test suite
│   ├── __init__.py
│   └── test_health.py         # Basic health endpoint tests
├── data/                       # Local data storage (gitignored)
├── docker-compose.yml          # Local services (Qdrant, Redis, PostgreSQL)
├── Dockerfile                  # Python 3.11 + uv container
├── requirements.txt            # Python dependencies including pytest
├── .env.example               # Environment template with placeholders
├── .gitignore                 # Comprehensive ignore patterns
└── README.md                  # This file
```

## ⚙️ Configuration System

The platform uses a sophisticated configuration system with multiple override layers:

### Configuration Priority (highest to lowest):
1. **Environment variables** (`.env` file in Codespaces, GitHub Secrets in CI)
2. **YAML defaults** ([`config/sophia.yaml`](config/sophia.yaml))

### Key Settings

| Category | Setting | Description | Default |
|----------|---------|-------------|---------|
| **Environment** | `ENVIRONMENT` | Runtime environment | `development` |
| **Database** | `DATABASE_URL` | PostgreSQL connection string | Local Docker |
| | `REDIS_URL` | Redis connection string | Local Docker |
| | `QDRANT_URL` | Qdrant vector database URL | Cloud instance |
| **LLM** | `OPENROUTER_API_KEY` | OpenRouter API access | Required |
| | `TEMPERATURE` | LLM sampling temperature | `0.7` |
| | `MAX_TOKENS` | Maximum tokens per request | `4096` |
| **Agent** | `AGENT_CONCURRENCY` | Max concurrent agent tasks | `2` |
| | `AGENT_TIMEOUT_SECONDS` | Task timeout | `300` |
| | `AGNO_STORAGE_DB` | SQLite database for conversations | `data/agents.db` |
| **Memory** | `MEMORY_COLLECTION_NAME` | Qdrant collection name | `code_memory` |
| | `EMBEDDING_DIMENSION` | Vector dimension | `384` |

### Environment-Specific Overrides

**Development (`.env`):**
```bash
ENVIRONMENT=development
QDRANT_URL=http://localhost:6333
DATABASE_URL=postgresql+asyncpg://sophia:devpass@localhost:5432/sophia
LOG_LEVEL=DEBUG
```

**Production (GitHub Secrets):**
```bash
ENVIRONMENT=production
QDRANT_URL=https://prod-cluster.qdrant.tech:6333
QDRANT_API_KEY=prod-api-key
DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/sophia
LOG_LEVEL=INFO
```

## 🤖 Agent System

### Architecture Overview
The agent system is built on a layered architecture:

```
┌─────────────────────────────────────────┐
│           Agent API (FastAPI)           │  ← HTTP interface
├─────────────────────────────────────────┤
│        Coding Agent (Agno-based)        │  ← Specific implementations
├─────────────────────────────────────────┤
│         Base Agent Framework            │  ← Common functionality
├─────────────────────────────────────────┤
│  Memory Integration (MCP Protocol)      │  ← Context management
└─────────────────────────────────────────┘
```

### Base Agent Framework

[`BaseAgent`](agents/base_agent.py) provides:
- **Async execution** with proper timeout handling
- **Concurrency control** via semaphores (configurable)
- **Status tracking** (`READY`, `BUSY`, `ERROR`, `TIMEOUT`)
- **Performance metrics** (success rate, response time)
- **Error handling** with structured responses

```python
# Agent initialization with custom concurrency
agent = CodingAgent(concurrency=4, timeout_seconds=600)

# Execution returns standardized response
result = await agent.execute("task-123", {
    "session_id": "user-session",
    "code": "def example(): pass",
    "query": "Add comprehensive docstring"
})
```

### Coding Agent

The [`CodingAgent`](agents/coding_agent.py) specializes in code analysis and modification:

**Features:**
- **Agno framework integration** for conversation history
- **MCP memory integration** for context-aware responses
- **Structured JSON output** with `summary` and `patch` fields
- **Unified diff format** for code changes
- **Async implementation** with proper error handling

**Response Format:**
```json
{
  "success": true,
  "task_id": "coding_1704380400123456",
  "result": {
    "summary": "Added type hints and comprehensive docstring with examples",
    "patch": "--- a/example.py\n+++ b/example.py\n@@ -1,2 +1,10 @@\n-def example():\n-    pass\n+def example() -> None:\n+    \"\"\"Example function demonstrating proper documentation.\n+    \n+    This function serves as a template for other functions.\n+    \n+    Examples:\n+        >>> example()\n+        # Function executes successfully\n+    \"\"\"\n+    pass"
  },
  "duration": 2.45,
  "agent": "CodingAgent"
}
```

### Agent API Endpoints

The [`agno_api.py`](scripts/agno_api.py) server provides HTTP access:

- `POST /agent/coding` - Execute coding tasks
- `GET /agent/coding/stats` - Get agent performance statistics
- `GET /health` - Health check with agent status
- `GET /agents` - List all available agents

## 🧠 Memory & Context (MCP)

### Model Context Protocol Overview

The MCP (Model Context Protocol) system provides persistent, searchable memory for agents:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Agent Request  │───▶│  MCP Server     │───▶│ Qdrant Vector  │
│                 │    │  (FastAPI)      │    │   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Features

**Semantic Search:**
- Vector-based similarity search using embeddings
- Session-based context isolation
- Global search across all sessions
- Configurable similarity thresholds

**Rich Metadata:**
- Context type tagging (`debug_step`, `agent_interaction`, etc.)
- Timestamp tracking
- Custom metadata fields

**Async Performance:**
- Non-blocking operations using `asyncio`
- Thread pool execution for Qdrant operations
- Circuit breaker pattern for reliability

### API Endpoints

**Store Context:**
```bash
curl -X POST http://localhost:8001/context/store \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "coding-session-123",
    "content": "User wants to optimize database queries for better performance",
    "metadata": {
      "context_type": "user_preference",
      "priority": "high",
      "domain": "database"
    }
  }'
```

**Query Context:**
```bash
curl -X POST http://localhost:8001/context/query \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "coding-session-123",
    "query": "database optimization techniques",
    "top_k": 5,
    "threshold": 0.8
  }'
```

**Session Management:**
```bash
# Get session statistics
curl http://localhost:8001/context/session/coding-session-123/stats

# Clear session context
curl -X DELETE http://localhost:8001/context/session/coding-session-123
```

## 🔌 External Integrations

**Features:**
- **Async implementation** with proper timeout handling
- **Automatic retries** with exponential backoff
- **Usage tracking** and performance metrics
- **Model routing** through OpenRouter's unified API

**Usage Example:**
```python

response = await client.chat(
    messages=[{"role": "user", "content": "Explain async/await"}],
    model="anthropic/claude-3-sonnet",
    temperature=0.7,
    max_tokens=1000
)
```

### Lambda Labs Integration

For GPU-accelerated workloads:

```python
from services.lambda_client import LambdaClient

lambda_client = LambdaClient()
quota_info = await lambda_client.quota()
```

### Service Orchestration

The [`Orchestrator`](services/orchestrator.py) coordinates requests across services:

- **Circuit breaker pattern** for service reliability
- **Request routing** based on request type
- **Performance monitoring** and statistics
- **Automatic failover** and retry logic

## 🧪 Development Workflow

### Non-negotiable Standards

These rules are enforced by GitHub Actions and documented in [`.github/copilot-instructions.md`](.github/copilot-instructions.md):

1. **Branch-based development** - Never push directly to `main`
2. **Conventional commits** - Use `feat:`, `fix:`, `docs:`, etc.
3. **Test coverage** - All new features must include tests
4. **Secrets management** - Use `.env` locally, GitHub Secrets in CI
5. **Type hints** - Required for all function signatures
6. **Structured responses** - All agents return `{"summary": str, "patch": str}`

### Development Commands

**Setup development environment:**
```bash
# Install dependencies
uv pip install -r requirements.txt

# Start local services
docker-compose up -d

# Verify setup
python -c "from config.config import settings; print(settings.get_stats())"
```

**Run tests:**
```bash
# Basic syntax check
python -m compileall .

# Run test suite
pytest tests/ -v

# Test specific components
pytest tests/test_health.py -v
```

**Code quality:**
```bash
# Format code
black .

# Type checking (if mypy installed)
mypy . --ignore-missing-imports
```

### Branch Workflow

```bash
# 1. Create feature branch
git checkout -b feat/enhance-memory-search

# 2. Make changes
# ... edit files ...

# 3. Test changes
pytest tests/ -v
python -m compileall .

# 4. Commit with conventional format
git add .
git commit -m "feat: add semantic similarity threshold to memory search

- Add configurable threshold parameter to query_context
- Include similarity scores in search results
- Update API documentation with threshold examples"

# 5. Push and create PR
git push -u origin feat/enhance-memory-search
# Create PR via GitHub UI with provided template
```

## 🚧 Testing & Validation

### Automated Testing Pipeline

The GitHub Actions CI pipeline ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) includes:

**Lint Job:**
- Code compilation check
- Black formatting verification
- Type checking (optional)

**Test Job:**
- PostgreSQL and Redis test services
- Full pytest suite execution
- Integration tests with mock services

**Security Job:**
- Bandit security analysis
- Dependency vulnerability scanning

**Integration Job:**
- End-to-end configuration loading
- Agent instantiation testing
- Service connectivity verification

### Manual Testing

**Health Checks:**
```bash
# Test all service endpoints
curl http://localhost:8000/health  # Backend
curl http://localhost:8001/health  # MCP Server
curl http://localhost:7777/health  # Agent API

# Test agent functionality
curl -X POST http://localhost:7777/agent/coding \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test",
    "code": "print(\"hello\")",
    "query": "Convert to function with parameters"
  }'
```

**Performance Testing:**
```bash
# Load test health endpoints
for i in {1..100}; do
  curl -s http://localhost:8000/health > /dev/null &
done
wait

# Memory service performance
for i in {1..10}; do
  curl -X POST http://localhost:8001/context/store \
    -H "Content-Type: application/json" \
    -d "{\"session_id\":\"perf-test\",\"content\":\"Test context $i\"}"
done
```

## 📊 Monitoring & Observability

### Built-in Metrics

**Prometheus Metrics:**
- Request counters by endpoint
- Response time histograms
- Agent task success/failure rates
- Circuit breaker state tracking

**Health Endpoints:**
- `/health` - Basic service health
- `/metrics` - Prometheus-format metrics
- `/agent/{name}/health` - Agent-specific health

**Performance Statistics:**
```bash
# Agent performance stats
curl http://localhost:7777/agent/coding/stats

# Orchestrator statistics
curl http://localhost:8000/orchestrator/stats

# MCP server statistics
curl http://localhost:8001/context/session/global/stats
```

### Logging

Structured logging with [`loguru`](https://github.com/Delgan/loguru):

```python
from loguru import logger

logger.info("Agent task completed",
           task_id="task-123",
           duration=2.34,
           success=True)
```

### Alerting Recommendations

For production deployments, monitor:
- Agent task failure rates > 5%
- MCP server response times > 2s
- Qdrant connection failures
- OpenRouter API quota usage

## 🔧 Troubleshooting

### Common Issues & Solutions

**1. Services won't start:**
```bash
# Check port conflicts
netstat -tulpn | grep -E "(8000|8001|7777)"

# Check Docker services
docker-compose ps
docker-compose logs qdrant postgres redis

# Restart services
docker-compose restart
```

**2. Configuration errors:**
```bash
# Validate configuration loading
python -c "
from config.config import settings
print(f'Environment: {settings.ENVIRONMENT}')
print(f'Database: {settings.DATABASE_URL}')
print(f'Qdrant: {settings.QDRANT_URL}')
"

# Check environment variables
```

**3. Agent execution failures:**
```bash
# Check Agno database
ls -la data/
file data/agents.db

# Test MCP connectivity
curl -f http://localhost:8001/health

# Check agent logs
# (Logs appear in terminal where agno_api.py is running)
```

**4. Memory service issues:**
```bash
# Test Qdrant directly
curl http://localhost:6333/health

# For Qdrant cloud
curl -H "api-key: your-api-key" https://your-cluster.qdrant.io:6333/collections

# Test memory service
curl -X POST http://localhost:8001/context/store \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "content": "test content"}'
```

### Debug Workflows

Use the [MCP-based debugging template](.prompts/debug-issue.md) for systematic troubleshooting:

1. **Store issue context** in MCP memory
2. **Query similar issues** from historical data
3. **Document debugging steps** for future reference
4. **Share solutions** via structured JSON responses

## 🚀 Production Deployment

### Infrastructure Requirements

**Minimum Requirements:**
- **CPU**: 2 cores, 4GB RAM per service
- **Storage**: 20GB persistent storage
- **Network**: Load balancer with SSL termination
- **Database**: PostgreSQL 15+ with connection pooling
- **Cache**: Redis 7+ with persistence
- **Vector DB**: Qdrant cloud or self-hosted cluster

**Recommended Architecture:**
- **Kubernetes** with horizontal pod autoscaling
- **Managed databases** (AWS RDS, GCP Cloud SQL)
- **Container registry** for image management
- **Secrets management** (Vault, AWS Secrets Manager)
- **Monitoring** (Prometheus + Grafana)
- **Log aggregation** (ELK stack, DataDog)

### Deployment Guide

See [Infrastructure Deployment Template](.prompts/deploy-infra.md) for:
- **Pulumi infrastructure** code
- **Kubernetes manifests**
- **CI/CD pipeline** configuration
- **Monitoring setup**
- **Security best practices**

### Environment Configuration

**Production `.env`:**
```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
ENABLE_METRICS=true

# Use managed services
DATABASE_URL=postgresql+asyncpg://user:pass@prod-postgres:5432/sophia
REDIS_URL=redis://prod-redis:6379/0
QDRANT_URL=https://prod-cluster.qdrant.tech:6333

# Production API keys (via secrets management)
OPENROUTER_API_KEY=${SECRET_OPENROUTER_KEY}

# Enhanced security
SECRET_KEY=${SECRET_APP_KEY}
JWT_SECRET=${SECRET_JWT_KEY}
ENCRYPTION_KEY=${SECRET_ENCRYPTION_KEY}
```

## 🎯 Next Steps & Roadmap

### Immediate Improvements (Phase 2)

**1. Enhanced Memory System:**
- Replace hash-based embeddings with OpenAI or Sentence Transformers
- Implement memory summarization and context pruning
- Add semantic clustering for better context organization

**2. Advanced Agent Capabilities:**
- Multi-agent orchestration and collaboration
- Specialized agents (debugging, testing, documentation)
- Agent memory sharing and knowledge transfer

**3. Production Features:**
- Authentication and authorization system
- Rate limiting and quota management
- Advanced monitoring and alerting
- Performance optimization and caching

### Future Enhancements

**1. Agent UI Improvements:**
- Real-time collaboration features
- Visual code diff rendering
- Session management and history
- Agent performance dashboards

**2. Integration Expansions:**
- Additional LLM providers (Anthropic, Google)
- GitHub integration for automatic PR creation
- IDE plugins (VS Code, JetBrains)
- Slack/Discord bot interfaces

**3. Advanced Memory Features:**
- Cross-session knowledge graphs
- Automatic context summarization
- Knowledge base integration
- Collaborative memory sharing

## 🤝 Contributing

### Getting Started

1. **Fork** the repository
2. **Set up development environment:**
   ```bash
   git clone https://github.com/your-username/sophia-intel.git
   cd sophia-intel
   cp .env.example .env
   # Edit .env with your API keys
   uv pip install -r requirements.txt
   ```
3. **Read contribution guidelines:**
   - [GitHub Copilot Instructions](.github/copilot-instructions.md)
   - [PR Template](.github/pull_request_template.md)

### Development Guidelines

**Code Standards:**
- Use **type hints** for all functions
- Write **comprehensive docstrings**
- Follow **async/await** patterns
- Include **error handling**
- Add **tests** for new features

**Commit Format:**
```
type(scope): brief description

Detailed explanation of changes and motivation.

- Specific change 1
- Specific change 2
- Breaking changes (if any)
```

**Pull Request Process:**
1. Create feature branch with descriptive name
2. Implement changes with tests
3. Update documentation if needed
4. Ensure CI pipeline passes
5. Submit PR with completed template

### Community

- **Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas
- **PRs**: Contribute code improvements
- **Documentation**: Help improve guides and examples

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ for GitHub Codespaces**

*Sophia Intel - Intelligent AI Agent Platform for Modern Development*