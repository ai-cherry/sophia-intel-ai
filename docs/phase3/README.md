# Phase 3: Agent Implementation

## Overview

Phase 3 introduces four specialized AI agents integrated with the smart routing, budget management, and circuit breaker systems from Phase 2. Each agent has specific capabilities and is exposed via MCP (Model Context Protocol) servers.

## 🤖 Agents

### 1. Coder Agent
- **Purpose**: Code generation, refactoring, test creation
- **Cost Tier**: Premium (uses powerful models)
- **Capabilities**:
  - Generate code in multiple languages
  - Refactor existing code
  - Create unit tests
  - Generate documentation
  - Fix bugs

### 2. Architect Agent
- **Purpose**: System design and architecture planning
- **Cost Tier**: Premium (requires reasoning)
- **Capabilities**:
  - Design system architecture
  - Create API specifications
  - Design database schemas
  - Analyze scalability
  - Review architectural decisions

### 3. Reviewer Agent
- **Purpose**: Code review and quality analysis
- **Cost Tier**: Standard (mid-tier models)
- **Capabilities**:
  - Review code quality
  - Identify security issues
  - Detect bugs
  - Check best practices
  - Analyze performance

### 4. Researcher Agent
- **Purpose**: Information gathering and research
- **Cost Tier**: Economy (simpler models)
- **Capabilities**:
  - Search documentation
  - Find best practices
  - Research libraries
  - Gather API information
  - Compile technical summaries

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│         Client Layer                 │
│  (UI, REST API, WebSocket)          │
└─────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│      Agent Coordinator              │
│  (Orchestration & Strategy)         │
└─────────────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ Router  │ │ Budget  │ │Circuit  │
│         │ │ Manager │ │Breaker  │
└─────────┘ └─────────┘ └─────────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│  Coder  │ │Architect│ │Reviewer │
│  Agent  │ │  Agent  │ │  Agent  │
└─────────┘ └─────────┘ └─────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│         MCP Servers                 │
│    (External Tool Integration)      │
└─────────────────────────────────────┘
```

## 💻 Implementation

### Base Agent Class
All agents inherit from `BaseAgent` which provides:
- Router integration for model selection
- Budget checking before execution
- Circuit breaker protection
- Telemetry emission
- Fallback handling

```python
from agno_core.agents.base import BaseAgent

class CustomAgent(BaseAgent):
    async def _execute_impl(self, task, model, context):
        # Agent-specific implementation
        pass
```

### Agent Coordinator
Orchestrates multiple agents with different strategies:
- **Sequential**: Execute agents one after another
- **Parallel**: Execute all agents simultaneously
- **Pipeline**: Transform data through agent stages
- **Consensus**: Multiple agents vote on result

```python
coordinator = AgentCoordinator(router, budget, telemetry)
result = await coordinator.execute_task(
    task="Build a REST API",
    agent_names=["architect", "coder", "reviewer"],
    strategy="sequential"
)
```

## 🔌 MCP Integration

Each agent is exposed as an MCP server:

| Agent | Port | Endpoint |
|-------|------|----------|
| Coder | 8001 | localhost:8001 |
| Architect | 8002 | localhost:8002 |
| Reviewer | 8003 | localhost:8003 |
| Researcher | 8004 | localhost:8004 |

### Starting MCP Servers
```bash
# Start all agent MCP servers
make mcp-agents-start

# Or individually
python mcp_servers/coder_mcp.py &
python mcp_servers/architect_mcp.py &
python mcp_servers/reviewer_mcp.py &
python mcp_servers/researcher_mcp.py &
```

## 📊 Monitoring

### Telemetry Events
Each agent execution emits telemetry:
- `agent_execution` - Task started
- `route_decision` - Model selected
- `budget_check` - Budget verified
- `execution_complete` - Task finished

### Budget Tracking
Agents respect budget limits:
- Soft cap: Warning issued
- Hard cap: Execution blocked

### Circuit Breaker
Automatic protection from failures:
- 3 failures trigger circuit open
- 2-minute cooldown period
- Automatic fallback to secondary models

## 🚀 Usage Examples

### Simple Code Generation
```python
coder = CoderAgent(router, telemetry)
result = await coder.execute(
    task="Create a Python class for user authentication",
    context={"framework": "FastAPI"}
)
```

### Multi-Agent Workflow
```python
# Design, implement, and review
result = await coordinator.execute_task(
    task="Build a microservice for payment processing",
    agent_names=["architect", "coder", "reviewer"],
    strategy="sequential",
    context={
        "requirements": "Handle Stripe payments",
        "language": "Python",
        "framework": "FastAPI"
    }
)
```

### Research and Implementation
```python
# Research best practices then implement
result = await coordinator.execute_task(
    task="Implement rate limiting for API",
    agent_names=["researcher", "coder"],
    strategy="sequential",
    context={
        "api_framework": "Express.js",
        "requirements": "100 requests per minute per user"
    }
)
```

## 🔧 Configuration

### Agent Configuration
Edit `config/agents.yaml`:
```yaml
agents:
  coder:
    enabled: true
    default_model: gpt-4-turbo
    fallback_models: [claude-3-opus, gpt-3.5-turbo]
    max_tokens: 4096
    temperature: 0.2
```

### Cost Categories
Edit `config/models.yaml`:
```yaml
cost_categories:
  simple:
    models: [gpt-3.5-turbo, claude-3-haiku]
  code_generation:
    models: [gpt-4-turbo, claude-3-opus]
  reasoning:
    models: [gpt-4, claude-3-opus]
```

## 📈 Performance

### Optimization Tips
1. Use appropriate agents for tasks
2. Configure proper fallback chains
3. Set reasonable timeout values
4. Monitor budget usage regularly
5. Use caching for repeated queries

### Benchmarks
- Simple task: < 5 seconds
- Complex multi-agent: < 30 seconds
- Research task: < 10 seconds
- Full pipeline: < 45 seconds

## 🐛 Troubleshooting

### Agent Not Responding
```bash
# Check MCP server status
curl http://localhost:8001/health

# View agent logs
docker logs sophia-coder-agent

# Restart agent
docker restart sophia-coder-agent
```

### Budget Exceeded
```bash
# Check current usage
curl http://localhost:5003/api/telemetry/budgets

# Reset budget (development only)
python scripts/reset_budgets.py
```

### Circuit Breaker Open
```bash
# Check circuit status
curl http://localhost:5003/api/telemetry/circuits

# Wait for cooldown or manually reset
python scripts/reset_circuits.py
```

## 📚 Additional Resources

- [Full Architecture Plan](../PHASE_3_AGENT_WIRING_PLAN.md)
- [Agent Contracts](../AGENTS_CONTRACT.md)
- [MCP Integration Guide](../SWARM_MCP_INTEGRATION.md)
- [API Reference](../API_REFERENCE.md)

---

*Phase 3 Implementation - September 2025*