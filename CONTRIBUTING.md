# Contributing to Sophia Intel AI

Thank you for your interest in contributing to Sophia Intel AI! This guide will help you get started with development, testing, and submitting contributions to our AI Swarm Orchestration Platform.

## Quick Start

### Using the Development Script (Recommended)

```bash
# Clone and setup
git clone https://github.com/ai-cherry/sophia-intel-ai.git
cd sophia-intel-ai

# Setup development environment
python3 dev.py setup

# Start all services
python3 dev.py start
```

### Using Make (Alternative)

```bash
# Initialize development environment
make init

# Start development servers
make dev

# Check status
make status
```

### Manual Setup

```bash
# Clone and setup
git clone https://github.com/ai-cherry/sophia-intel-ai.git
cd sophia-intel-ai

# Create environment file
cp .env.example .env.local
# Add your API keys to .env.local

# Install dependencies
pip3 install -e .
cd agent-ui && npm install && cd ..

# Start services
make api    # In terminal 1
make frontend    # In terminal 2
```

## Development Workflow

### Available Commands

**Python Development Script:**
```bash
python3 dev.py help      # Show all commands
python3 dev.py setup     # Setup development environment
python3 dev.py start     # Start all services
python3 dev.py status    # Check service health
python3 dev.py test      # Run tests
python3 dev.py build     # Build project
python3 dev.py lint      # Lint and format code
python3 dev.py clean     # Clean build artifacts
python3 dev.py logs      # Show logs
```

**Make Commands:**
```bash
make help               # Show all commands
make dev                # Start development servers
make test               # Run all tests
make lint               # Lint and format code
make build              # Build project
make clean              # Clean artifacts
make status             # Check service status
make info               # Show project info
```

### Key Services

- **API Server**: http://localhost:8003
  - Health: `/healthz`
  - Docs: `/docs`
  - Config: `/config`
  - Cost Tracking: `/costs/summary`
  - Embeddings: `/embeddings`
  
- **Frontend**: http://localhost:3000
  - Cost Dashboard available in UI
  - Swarm execution interface
  
- **Features**:
  - 🔍 **Trace Middleware**: All requests tracked with trace IDs
  - 💰 **Cost Tracking**: LLM usage analytics and dashboards
  - 🧠 **Embeddings**: Together AI via Portkey with caching
  - 🚦 **Rate Limiting**: API-key based rate limits
  - 📊 **Observability**: Request/response logging

## Code Standards

- **Type Hints**: All functions must have type annotations
- **Docstrings**: Google style for all public functions/classes
- **Formatting**: Black (100 char line length)
- **Linting**: Ruff + MyPy
- **Testing**: Minimum 80% coverage
- **Trace IDs**: All API endpoints must support trace ID propagation

## Project Structure

```
app/                  # Main package
├── api/             # API endpoints and routers
│   ├── unified_server.py    # Main FastAPI application
│   ├── health.py           # Health check endpoints
│   └── routers/            # Modular API routers
├── config/          # Configuration management
│   └── env_loader.py       # Environment configuration
├── embeddings/      # Together AI embedding service
│   ├── together_embeddings.py
│   └── embedding_cli.py
├── observability/   # Monitoring and analytics
│   └── cost_tracker.py     # Cost tracking system
├── orchestration/   # Swarm orchestration
│   └── execution_timeline.py
├── memory/          # Memory and context systems
├── swarms/          # Agent implementations
└── llm/             # LLM response models

agent-ui/            # React frontend
├── src/
│   ├── components/
│   │   ├── analytics/      # Cost dashboard
│   │   ├── playground/     # Chat interface
│   │   └── swarm/          # Swarm visualization
│   ├── hooks/              # React hooks
│   │   └── useServiceConfig.ts  # Service discovery
│   └── api/
│       └── routes.ts       # API route definitions

data/                # Data storage
├── cost_tracking/   # Cost tracking data
├── memory/          # Shared memory storage
└── logs/            # Application logs
```

## Testing and Debugging

### Running Tests

```bash
# Run all tests
python3 dev.py test
make test

# Run specific test suites
pytest tests/ -v
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest --cov=app            # With coverage report
```

### Testing API Endpoints

```bash
# Test cost tracking
curl http://localhost:8003/costs/summary?days=7

# Test embeddings
curl -X POST http://localhost:8003/embeddings \
  -H "Content-Type: application/json" \
  -d '{"texts": ["test text"], "model": "m2-bert-8k"}'

# Test health
curl http://localhost:8003/healthz
```

### Debugging

```bash
# Start API in debug mode
make debug

# Monitor logs
make logs
python3 dev.py logs

# Check service health
make status
python3 dev.py status
```

### Cost Tracking

All LLM and embedding operations are automatically tracked. View analytics at:
- API: http://localhost:8003/costs/summary
- Dashboard: Available in frontend UI
- Data: Stored in `data/cost_tracking/`

### Trace IDs

Every request gets a trace ID for debugging:
- Automatically generated for each request
- Propagated through all services
- Visible in logs and response headers
- Use `X-Trace-ID` header to specify custom trace ID

## Environment Variables

Required in `.env.local`:
```bash
# API Keys
OPENROUTER_API_KEY=your_openrouter_key
PORTKEY_API_KEY=your_portkey_key

# Model Configuration
ORCHESTRATOR_MODEL=openai/gpt-5
AGENT_SWARM_MODELS=x-ai/grok-code-fast-1,google/gemini-2.5-flash,...
EMBEDDING_PRIMARY_MODEL=togethercomputer/m2-bert-80M-8k-retrieval

# Features
EMBEDDINGS_ENABLED=true
COST_TRACKING_ENABLED=true
TRACING_ENABLED=true

# Rate Limiting
API_RATE_LIMIT=100
API_RATE_WINDOW=60
```

## Submitting Changes

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Make changes and add tests
4. Run quality checks: `make qa`
5. Ensure all tests pass: `make test`
6. Commit with conventional commits: `git commit -m "feat: your feature"`
7. Push and create PR

## Quality Assurance

Before submitting:

```bash
# Full QA pipeline
make qa

# Individual steps
make lint      # Format and lint code
make test      # Run all tests
make build     # Ensure project builds
make security  # Security checks
```

## Adding Features

See detailed guide in docs/development.md

## Support

- Issues: https://github.com/ai-cherry/sophia-intel-ai/issues
- Discord: Join our community server
- Email: team@sophia-intel.ai
