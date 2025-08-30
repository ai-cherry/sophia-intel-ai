# Agno 1.8.1 Migration Guide

## Overview

This guide details the migration from our custom swarm implementation to Agno 1.8.1 with Portkey gateway integration.

## Key Improvements

### 1. **Unified LLM Gateway (Portkey)**
- Single endpoint for all LLM providers
- Automatic failover and load balancing
- Cost tracking and budgets
- Request caching and optimization

### 2. **Native Teams API (Agno 1.8.1)**
- Built-in team orchestration
- Parallel agent execution
- Automatic judge-based consensus
- Memory sharing across agents

### 3. **Agent UI Integration**
- Modern chat interface
- Real-time agent visualization
- Team selection UI
- Memory inspection tools

## Migration Steps

### Step 1: Install Dependencies

```bash
pip3 install -U agno==1.8.1 portkey-ai 'fastapi[standard]'
```

### Step 2: Environment Configuration

Replace individual provider keys with Portkey configuration:

**Before (Multiple Providers):**
```python
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk-...
```

**After (Portkey Gateway):**
```python
OPENAI_API_BASE=https://api.portkey.ai/v1/openai
OPENAI_API_KEY=pk_live_YOUR_PORTKEY_KEY
```

### Step 3: Agent Definition Migration

**Before (Custom Agent):**
```python
from app.swarms.coding.agents import make_generator

agent = make_generator(
    name="Coder",
    model_key="qwen_coder",
    tools=[CodeSearch()],
    role_note="Implement with tests"
)
```

**After (Agno 1.8.1):**
```python
from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGo

agent = Agent(
    name="Coder",
    model="openrouter/qwen/qwen-2.5-coder-32b-instruct",
    tools=[DuckDuckGo(), CodeSearch()],
    system_prompt="Implement with comprehensive tests",
    reasoning=True,  # Enable chain-of-thought
    memory=Memory()  # Shared memory
)
```

### Step 4: Team Migration

**Before (Custom Team):**
```python
class CodingTeam:
    def __init__(self):
        self.agents = [make_lead(), make_generator(), make_critic()]
    
    async def solve(self, problem):
        # Custom orchestration logic
        pass
```

**After (Agno Teams):**
```python
from agno.teams import Team

team = Team(
    name="Coding Team",
    agents=[planner, coder, critic, tester],
    judge=judge,  # Automatic consensus
    description="Standard development team"
)

# Simple execution
result = await team.run("Implement user authentication")
```

### Step 5: Swarm to Teams Mapping

| Old Swarm | New Agno Team | Agents | Use Case |
|-----------|---------------|---------|----------|
| CodingTeam (5) | standard_team | planner, coder, critic, tester, judge | Regular tasks |
| CodingSwarm (10+) | advanced_team | planner, 2 coders, critic, security, judge | Complex features |
| FastSwarm (3) | fast_team | coder_fast, critic, judge | Quick fixes |
| GENESIS (30+) | genesis_team | All specialists + judge | Critical features |

### Step 6: Tool Migration

**Custom Tools Integration:**

```python
# Your existing tools work with Agno
from app.tools.code_search import CodeSearch
from app.tools.repo_fs import ReadFile, WriteFile

agent = Agent(
    name="Developer",
    tools=[
        CodeSearch(),      # Your custom tool
        ReadFile(),        # Your custom tool
        DuckDuckGo(),      # Agno built-in
    ]
)
```

### Step 7: API Migration

**Before (Custom Endpoints):**
```python
@app.post("/teams/run")
async def run_team(problem: str):
    team = CodingTeam()
    return await team.solve(problem)
```

**After (Agno FastAPI):**
```python
from agno.apps.fastapi import create_fastapi_app

app = create_fastapi_app(
    agents={
        "coder": coder_agent,
        "team": coding_team,
    }
)
# Automatic endpoints:
# POST /agents/{agent_id}/run
# POST /teams/{team_id}/run
# GET /agents
# GET /memory/search
```

## Portkey Configuration

### Virtual Keys Setup

1. Go to [Portkey Dashboard](https://app.portkey.ai)
2. Create Virtual Keys for each provider:
   - OpenRouter → Multiple models
   - OpenAI → GPT-4, GPT-4o
   - Anthropic → Claude models
   - Groq → Fast inference

### Routing Rules

Configure in `portkey_config.json`:

```json
{
  "routing_rules": [
    {
      "name": "Code Generation",
      "pattern": "coder",
      "load_balance": [
        {"model": "qwen-2.5-coder", "weight": 0.5},
        {"model": "deepseek-coder", "weight": 0.5}
      ]
    }
  ]
}
```

## Testing the Migration

### 1. Start Services

```bash
# Terminal 1: Playground
python app/agno_v2/playground.py

# Terminal 2: Agent UI
cd agent-ui && npm run dev
```

### 2. Test Endpoints

```python
import httpx

# Test agent
response = httpx.post(
    "http://127.0.0.1:7777/agents/coder/run",
    json={"query": "Write a factorial function"}
)

# Test team
response = httpx.post(
    "http://127.0.0.1:7777/teams/standard_team/run",
    json={"query": "Implement user authentication"}
)
```

### 3. Verify in Agent UI

Open http://localhost:3000 and test:
- Individual agents
- Team collaboration
- Memory persistence
- Real-time streaming

## Rollback Plan

If issues arise, rollback by:

1. Stop new services: `pkill -f playground.py`
2. Restore previous environment: `git checkout main -- .env`
3. Restart old server: `python3 -m app.api.unified_server`

## Benefits Summary

| Feature | Before | After |
|---------|--------|-------|
| Provider Management | Multiple API keys | Single Portkey key |
| Failover | Manual | Automatic |
| Cost Tracking | None | Built-in |
| Team Orchestration | Custom code | Native API |
| UI | None | Agent UI |
| Memory | Custom | Native Memory API |
| Observability | Limited | Full traces |

## Next Steps

1. **Enhance Routing**: Add more sophisticated routing rules
2. **Custom Tools**: Migrate all custom tools to Agno format
3. **Memory Persistence**: Upgrade to PostgreSQL-backed memory
4. **Production Deploy**: Use Pulumi for cloud deployment
5. **Monitoring**: Integrate Langfuse for production observability

## Support

- [Agno Docs](https://docs.agno.com)
- [Portkey Docs](https://portkey.ai/docs)
- [Agent UI Repo](https://github.com/agno-agi/agent-ui)

## Troubleshooting

### Common Issues

**Issue**: "API key not found"
**Solution**: Ensure `.env.portkey` is sourced

**Issue**: "Model not available"
**Solution**: Check Portkey virtual key configuration

**Issue**: "Agent UI can't connect"
**Solution**: Verify playground is running on port 7777

**Issue**: "Memory not persisting"
**Solution**: Upgrade to persistent Memory backend

---

## Conclusion

The migration to Agno 1.8.1 provides:
- ✅ Simplified multi-provider management
- ✅ Built-in team orchestration
- ✅ Modern UI out of the box
- ✅ Better observability and debugging
- ✅ Cost optimization and controls

The system is now more maintainable, scalable, and feature-rich while preserving all custom functionality.