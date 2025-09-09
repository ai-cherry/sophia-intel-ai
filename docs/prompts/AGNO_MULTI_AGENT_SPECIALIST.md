# AGNO MULTI-AGENT SYSTEM SPECIALIST PROMPT

You are an Agno framework specialist tasked with getting the complete multi-agent system operational. The Docker deployment (handled separately) provides the infrastructure. Your job is to make the AGENTS actually work end-to-end.

## Context
- Framework: Agno 1.8.1
- Models via AIML API and compatible endpoints
- Current state: Agent files exist; some agents are stubs
- Required: Working agents, orchestrator, API bridge, swarms, and tests
- Constraints: No secrets in repo; keys in `~/.config/artemis/env`. No Artemis code imports; integrate via HTTP + MCP only.

## Your Tasks

### 1) Create working Agno Core
File: `agno_core/orchestrator.py`
```python
from agno.agent import Agent, Team
from agno.memory import TeamMemory
import os
from typing import Dict

class AgnoOrchestrator:
    def __init__(self):
        self.api_key = os.getenv("AIMLAPI_KEY") or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("Missing AIMLAPI_KEY/OPENAI_API_KEY")
        self.agents = self.create_agents()
        self.teams = self.create_teams()

    def create_agents(self) -> Dict[str, Agent]:
        # Instantiate real agents with model + memory
        # Ensure each agent can execute tasks through provider API
        raise NotImplementedError

    def create_teams(self) -> Dict[str, Team]:
        # Create teams with TeamMemory to coordinate agents
        raise NotImplementedError
```

### 2) Implement Agent Bridge
File: `agno_bridge.py`
```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from agno_core.orchestrator import AgnoOrchestrator
import uvicorn

app = FastAPI(title="Agno Agent Bridge")
orch = AgnoOrchestrator()

@app.get("/health")
async def health():
    return {"status": "ok", "agents": list(orch.agents.keys())}

@app.get("/api/agents")
async def list_agents():
    return {"agents": [{"id": k, "status": "ready"} for k in orch.agents]}

@app.post("/api/agents/{agent_id}/execute")
async def execute_task(agent_id: str, task: dict):
    if agent_id not in orch.agents:
        raise HTTPException(404, "Unknown agent")
    return await orch.agents[agent_id].execute(task)

@app.websocket("/ws/agent/{agent_id}")
async def agent_websocket(ws: WebSocket, agent_id: str):
    await ws.accept()
    try:
        while True:
            payload = await ws.receive_json()
            if agent_id not in orch.agents:
                await ws.send_json({"error": "unknown agent"}); continue
            result = await orch.agents[agent_id].execute(payload)
            await ws.send_json(result)
    except WebSocketDisconnect:
        return

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("AGENT_API_PORT","8003")))
```

### 3) Create Agent Implementations
Files: `agents/coder_agent.py`, `agents/architect_agent.py`, `agents/reviewer_agent.py`
```python
class CoderAgent:
    model = "deepseek/deepseek-chat-v3-0324"
    capabilities = ["code_generation", "debugging", "refactoring"]
    async def execute(self, task: dict):
        # Call provider API via httpx; return structured response
        raise NotImplementedError

class ArchitectAgent:
    model = "anthropic/claude-opus-4-1-20250805"
    capabilities = ["system_design", "architecture", "planning"]
    async def execute(self, task: dict):
        raise NotImplementedError

class ReviewerAgent:
    model = "openai/gpt-5-mini-2025-08-07"
    capabilities = ["review", "testing", "quality"]
    async def execute(self, task: dict):
        raise NotImplementedError
```

### 4) Implement Swarms
File: `swarms/dev_swarm.py`
```python
class DevelopmentSwarm:
    def __init__(self):
        self.agents = [ArchitectAgent(), CoderAgent(), ReviewerAgent()]
    async def execute_project(self, requirements: str):
        # Architect designs -> Coder implements -> Reviewer validates
        raise NotImplementedError
```

### 5) Create Test Suite
File: `test_agents.py`
```python
import pytest, asyncio
from agno_core.orchestrator import AgnoOrchestrator

@pytest.mark.asyncio
async def test_all_agents():
    orch = AgnoOrchestrator()
    assert orch.agents
    for name, agent in orch.agents.items():
        res = await agent.execute({"prompt":"Say hi"})
        assert res and res.get("success")
```

### 6) Startup Script
File: `start_agno.sh`
```bash
#!/bin/bash
set -e
export AIMLAPI_KEY="${AIMLAPI_KEY}"
python3 -c "from agno_core.orchestrator import AgnoOrchestrator; o=AgnoOrchestrator(); print(f'Ready: {len(o.agents)} agents')"
uvicorn agno_bridge:app --host 0.0.0.0 --port ${AGENT_API_PORT:-8003}
```

## Deliverables
- `agno_core/orchestrator.py` – Orchestrator creating agents and teams
- `agno_bridge.py` – FastAPI bridge exposing endpoints + websockets
- `agents/coder_agent.py` `agents/architect_agent.py` `agents/reviewer_agent.py` – Working agents
- `swarms/dev_swarm.py` – Functional development swarm
- `test_agents.py` – Verifies agent execution works
- `start_agno.sh` – Starts the system on port 8003

## Success Criteria
```bash
# Start Agno
./start_agno.sh

# List agents
curl http://localhost:8003/api/agents

# Execute Coder task
curl -X POST http://localhost:8003/api/agents/coder/execute \
  -H 'Content-Type: application/json' -d '{"task":"Write a Python hello world"}'

# Execute swarm
curl -X POST http://localhost:8003/api/swarms/development/execute -d '{"requirements":"Build a todo app"}'
```

## Integration With UI
- UI expects:
  - `GET /api/agents`
  - `POST /api/agents/{id}/execute`
  - `WS /ws/agent/{id}`
  - `GET /health`
- Ensure these endpoints return real data and stream where appropriate.

## Testing Checklist
- Each agent instantiates and connects to provider API
- Each agent executes a task and returns a structured response
- Swarm coordinates multiple agents in sequence
- API bridge exposes endpoints and websocket streaming
- Memory persists where applicable (TeamMemory)
- Errors handled gracefully with informative messages

## Notes
- Do not commit secrets. Use `~/.config/artemis/env` + scripts/env.sh.
- Keep implementations minimal but real; avoid placeholders.

