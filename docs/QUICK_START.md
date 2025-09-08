# SOPHIA Quick Start Guide

Get SOPHIA up and running in 5 minutes!

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- API Keys (OpenAI, Anthropic, etc.)
- 8GB RAM minimum
- macOS or Linux (Windows WSL2 supported)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/sophia-intel-ai.git
cd sophia-intel-ai
```

### 2. Set Up Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

Required API keys:
- `OPENAI_API_KEY` - OpenAI GPT models
- `ANTHROPIC_API_KEY` - Claude models
- `PORTKEY_API_KEY` - (Optional) LLM gateway
- `PORTKEY_VIRTUAL_KEYS` - (Optional) Virtual keys

### 3. Install Dependencies
```bash
# Python dependencies
pip install -r requirements.txt

# Node dependencies for UI
cd agent-ui && npm install && cd ..
```

### 4. Start Core Services
```bash
# Start all services with Docker Compose
docker-compose up -d

# Or use the Makefile
make full-start
```

### 5. Start Telemetry Service
```bash
# Start telemetry endpoint (port 5003)
python webui/telemetry_endpoint.py &
```

### 6. Verify Installation
```bash
# Check service health
curl http://localhost:5003/api/telemetry/health

# Expected response:
# {"status": "healthy", "success": true, "timestamp": "..."}
```

## First Agent Task

### Example 1: Code Generation
```python
# test_agent.py
from agno_core.coordinator import AgentCoordinator
from agno_core.adapters.router import SmartRouter
from agno_core.adapters.budget import BudgetManager
from agno_core.adapters.telemetry import Telemetry

# Initialize components
router = SmartRouter()
budget = BudgetManager()
telemetry = Telemetry()
coordinator = AgentCoordinator(router, budget, telemetry)

# Execute a coding task
result = await coordinator.execute_task(
    task="Create a Python function to calculate fibonacci numbers",
    agent_names=["coder", "reviewer"],
    strategy="sequential"
)

print(result)
```

### Example 2: Using the REST API
```bash
# Generate code via API
curl -X POST http://localhost:5000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create a REST API endpoint for user authentication",
    "agents": ["architect", "coder"],
    "strategy": "sequential"
  }'
```

### Example 3: Check Budget Status
```bash
# View current budget usage
curl http://localhost:5003/api/telemetry/budgets | jq
```

## UI Access

### Start the Agent UI
```bash
cd agent-ui
npm run dev
```

Access at: http://localhost:3000

### Available Dashboards
- **Command Center** - Main control panel
- **Agent Status** - View agent availability
- **Budget Monitor** - Track spending
- **Telemetry View** - Real-time metrics

## Common Operations

### Monitor Telemetry
```bash
# View recent events
curl http://localhost:5003/api/telemetry/snapshot | jq

# Check circuit breaker status
curl http://localhost:5003/api/telemetry/circuits | jq

# View routing metrics
curl http://localhost:5003/api/telemetry/metrics | jq
```

### Simulate Failures (Testing)
```bash
# Trigger circuit breaker
curl -X POST http://localhost:5003/api/telemetry/simulate/failure/gpt-4-turbo

# Simulate budget spend
curl -X POST http://localhost:5003/api/telemetry/simulate/spend/gpt-4-turbo/10.50
```

### Stop Services
```bash
# Stop all Docker services
docker-compose down

# Or use Makefile
make stop-all

# Kill telemetry service
pkill -f telemetry_endpoint.py
```

## Configuration

### Model Selection
Edit `config/models.yaml`:
```yaml
models:
  gpt-4-turbo:
    provider: openai
    max_tokens: 4096
    temperature: 0.7
```

### Budget Limits
Edit `config/budgets.yaml`:
```yaml
vk_budgets:
  gpt-4-turbo:
    soft_cap_usd: 10.0
    hard_cap_usd: 50.0
```

### Agent Configuration
Edit `config/agents.yaml`:
```yaml
agents:
  coder:
    default_model: gpt-4-turbo
    fallback_models: [claude-3-opus, gpt-3.5-turbo]
```

## Troubleshooting

### Issue: Services won't start
```bash
# Check Docker status
docker ps -a

# View logs
docker-compose logs -f

# Reset everything
make clean && make full-start
```

### Issue: API key errors
```bash
# Verify environment variables
source scripts/env.sh --check

# Test API keys
python scripts/test_api_keys.py
```

### Issue: Port conflicts
```bash
# Find process using port
lsof -i :5003

# Kill process
kill -9 <PID>
```

## Next Steps

1. **Read the Architecture** - [System Architecture](ARCHITECTURE.md)
2. **Explore Agents** - [Phase 3 Agent Plan](PHASE_3_AGENT_WIRING_PLAN.md)
3. **Learn the API** - [API Reference](API_REFERENCE.md)
4. **Configure Production** - [Runbook](RUNBOOK_SOPHIA.md)

## Support

- Documentation: [docs/INDEX.md](INDEX.md)
- Issues: [GitHub Issues](https://github.com/yourusername/sophia-intel-ai/issues)
- Troubleshooting: [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)

---

*Happy coding with SOPHIA! 🚀*