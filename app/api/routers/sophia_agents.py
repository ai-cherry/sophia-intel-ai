"""Sophia BI Agents API (Agno v2 ready, BI-only).

Parallels the Builder endpoints while keeping BI domain isolation.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.sophia_agno2.factory import SophiaAgentFactory
from app.agents.agno2.swarms.orchestrator import SwarmOrchestrator

router = APIRouter(prefix="/api/sophia/agents", tags=["sophia-agents"])


class SystemStatus(BaseModel):
    status: str
    agno_v2_available: bool
    domain: str = "sophia"


class TeamInfo(BaseModel):
    id: str
    name: str
    roles: List[str]
    description: Optional[str] = None


class TeamRunRequest(BaseModel):
    team_id: str
    task: str
    context: Optional[Dict[str, Any]] = None


class TeamRunResponse(BaseModel):
    success: bool
    team_id: str
    task: str
    result: Dict[str, Any]
    latency_ms: float


@router.get("/status", response_model=SystemStatus)
async def status() -> SystemStatus:
    try:
        import agno  # type: ignore

        available = hasattr(agno, "Agent")
    except Exception:
        available = False
    return SystemStatus(status="healthy" if available else "degraded", agno_v2_available=available)


@router.get("/team/list", response_model=List[TeamInfo])
async def team_list() -> List[TeamInfo]:
    registry = Path("app/agents/sophia_agno2/registry")
    factory = SophiaAgentFactory(registry)
    teams: List[TeamInfo] = []
    for p in sorted(registry.glob("team.*.json")):
        try:
            data = factory.load_team_spec(p.stem.split("team.", 1)[-1])
            roles = [a.get("role", "agent") for a in data.get("agents", [])]
            teams.append(
                TeamInfo(
                    id=data["id"],
                    name=data["name"],
                    roles=roles,
                    description=data.get("description"),
                )
            )
        except Exception:
            continue
    return teams


@router.post("/team/run", response_model=TeamRunResponse)
async def team_run(req: TeamRunRequest) -> TeamRunResponse:
    start = time.perf_counter()
    registry = Path("app/agents/sophia_agno2/registry")
    factory = SophiaAgentFactory(registry)
    # Reuse the generic orchestrator (it uses the passed factory)
    orchestrator = SwarmOrchestrator(factory)  # type: ignore[arg-type]
    try:
        data = factory.load_team_spec(req.team_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown team_id: {req.team_id}")

    # Adapt to TeamSpec-like structure expected by orchestrator
    from dataclasses import dataclass
    from typing import List as _List
    from app.agents.agno2.factory import AgentSpec, TeamSpec

    agents: _List[AgentSpec] = [
        AgentSpec(
            id=a.get("id", "agent"),
            role=a.get("role", "agent"),
            instructions=a.get("instructions", []),
            tools=a.get("tools", []),
            model_policy=a.get("model_policy", "balanced"),
        )
        for a in data.get("agents", [])
    ]
    team_spec = TeamSpec(id=data["id"], name=data["name"], agents=agents, description=data.get("description", ""))

    result = await orchestrator.run_team(team_spec, req.task, req.context or {})
    latency_ms = (time.perf_counter() - start) * 1000
    return TeamRunResponse(success=True, team_id=req.team_id, task=req.task, result=result, latency_ms=latency_ms)

