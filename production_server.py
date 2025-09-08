#!/usr/bin/env python3
"""Production-ready Sophia server with core endpoints and docs.

Exposes:
- GET /health
- GET /api/agents
- POST /api/agents/execute {"agent":<name>, "prompt":<text>}
"""

from __future__ import annotations
import os
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agno_core.agents.working_agents import agents
from agno_core.telemetry_wire import telemetry


API_PORT = int(os.getenv("API_PORT", "8000"))
API_HOST = os.getenv("API_HOST", "0.0.0.0")
UI_ORIGINS = os.getenv("UI_ORIGINS", "http://localhost:3000")

app = FastAPI(title="Sophia Production API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in UI_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "agents": list(agents.keys())}


@app.get("/api/agents")
async def list_agents():
    return {"agents": list(agents.keys())}


@app.post("/api/agents/execute")
async def execute_agent(payload: Dict[str, Any]):
    name = payload.get("agent")
    prompt = payload.get("prompt", "")
    if not name or name not in agents:
        raise HTTPException(400, f"Unknown or missing agent: {name}")

    # Basic telemetry timings are handled in the agent client side; here record event
    telemetry.record("agent.execute", {"category": "agent", "agent": name})

    result = await agents[name].execute({"prompt": prompt})
    return result


def run():  # pragma: no cover
    import uvicorn

    uvicorn.run(app, host=API_HOST, port=API_PORT, reload=False)


if __name__ == "__main__":  # pragma: no cover
    run()

