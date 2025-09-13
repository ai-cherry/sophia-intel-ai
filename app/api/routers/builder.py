"""
Builder API Router (Agno 2.0 ready)
Exposes Builder-only endpoints for agent factory, swarms, routing analytics,
and JSON validation utilities. Designed to integrate with Agno v2 when present,
and operate in a degraded-but-useful mode if only local stubs are available.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from pathlib import Path
from app.agents.agno2.factory import AgentFactory
from app.agents.agno2.swarms.orchestrator import SwarmOrchestrator

router = APIRouter(prefix="/api/builder", tags=["builder"])


# -- Lightweight in-memory state for metrics/validation ----------------------

_METRICS = {
    "total_requests": 0,
    "total_cost_usd": 0.0,
    "successful_rate": 0.0,
    "average_latency_ms": 0.0,
}

_JSON_VALIDATION = {
    "validated_count": 0,
    "invalid_count": 0,
    "last_error": None,
}


def _record_metric(latency_ms: float, success: bool, cost_usd: float = 0.0) -> None:
    _METRICS["total_requests"] += 1
    prev_avg = _METRICS["average_latency_ms"]
    n = _METRICS["total_requests"]
    _METRICS["average_latency_ms"] = (prev_avg * (n - 1) + latency_ms) / max(n, 1)
    _METRICS["total_cost_usd"] += max(cost_usd, 0.0)
    # naive rolling success rate
    prev_success_rate = _METRICS["successful_rate"]
    _METRICS["successful_rate"] = (
        (prev_success_rate * (n - 1) + (1.0 if success else 0.0)) / max(n, 1)
    )


# -- Models -------------------------------------------------------------------


class ProviderAnalytics(BaseModel):
    total_requests: int = 0
    total_cost_usd: float = 0.0
    successful_rate: float = 0.0
    average_latency_ms: float = 0.0


class SystemComponents(BaseModel):
    providers: str = Field("operational", description="providers router status")
    rag: str = Field("operational", description="memory/RAG status")
    router: str = Field("operational", description="model router status")


class SystemStatus(BaseModel):
    status: str
    components: SystemComponents
    metrics: ProviderAnalytics


class RouterModelEntry(BaseModel):
    provider: str
    model: str
    policy: str
    latency_ms: Optional[float] = None
    cost_ratio: Optional[float] = None
    status: str = "allowed"


class RouterReport(BaseModel):
    stats: Dict[str, Any]
    models: Optional[List[RouterModelEntry]] = None


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


class JSONValidateRequest(BaseModel):
    payload: Any


class JSONValidateResponse(BaseModel):
    valid: bool
    error: Optional[str] = None


# -- Helpers to detect Agno v2 availability ----------------------------------


def _is_agno_v2_available() -> bool:
    try:
        import agno  # type: ignore

        # If this is the stub in the repo, it won't expose real v2 namespaces
        return hasattr(agno, "Agent") and hasattr(agno, "Team")
    except Exception:
        return False


# -- Endpoints ----------------------------------------------------------------


@router.get("/status", response_model=SystemStatus)
async def get_status() -> SystemStatus:
    start = time.perf_counter()
    # In a full implementation, probe providers/RAG/router real health here.
    components = SystemComponents(
        providers="operational",
        rag="operational",
        router="operational",
    )
    analytics = ProviderAnalytics(**_METRICS)
    status = "healthy" if components.providers == "operational" else "degraded"
    latency_ms = (time.perf_counter() - start) * 1000
    _record_metric(latency_ms, True)
    return SystemStatus(status=status, components=components, metrics=analytics)


@router.get("/providers/analytics", response_model=ProviderAnalytics)
async def providers_analytics() -> ProviderAnalytics:
    start = time.perf_counter()
    latency_ms = (time.perf_counter() - start) * 1000
    _record_metric(latency_ms, True)
    return ProviderAnalytics(**_METRICS)


@router.get("/router/report", response_model=RouterReport)
async def router_report(verbose: bool = Query(False)) -> RouterReport:
    # Placeholder stats; wire to Portkey model router when available
    stats = {
        "policies": {
            "planner": "balanced",
            "coder": "speed",
            "reviewer": "quality",
        },
        "approved_models_2025": [
            "gpt-5",
            "claude-4.1-sonnet",
            "claude-4.1-opus",
            "grok-code-fast-1",
        ],
    }
    models = None
    if verbose:
        models = [
            RouterModelEntry(provider="openrouter", model="gpt-5", policy="balanced", status="allowed"),
            RouterModelEntry(provider="anthropic", model="claude-4.1-opus", policy="quality", status="allowed"),
        ]
    return RouterReport(stats=stats, models=models)


@router.post("/router/refresh")
async def router_refresh() -> Dict[str, Any]:
    # In a full impl, refresh Portkey cache here
    return {"refreshed": True, "timestamp": time.time()}


@router.get("/team/list", response_model=List[TeamInfo])
async def team_list() -> List[TeamInfo]:
    """List available teams from the Builder registry."""
    registry = Path("app/agents/agno2/registry")
    factory = AgentFactory(registry)
    teams: List[TeamInfo] = []
    for p in sorted(registry.glob("team.*.json")):
        try:
            spec = factory.load_team_spec(p.stem.split("team.", 1)[-1])
            teams.append(
                TeamInfo(
                    id=spec.id,
                    name=spec.name,
                    roles=[a.role for a in spec.agents],
                    description=spec.description,
                )
            )
        except Exception:
            continue
    return teams


@router.post("/team/run", response_model=TeamRunResponse)
async def team_run(req: TeamRunRequest) -> TeamRunResponse:
    """Execute a team against a task using the Agno 2.0 orchestrator if available."""
    start = time.perf_counter()
    registry = Path("app/agents/agno2/registry")
    factory = AgentFactory(registry)
    orchestrator = SwarmOrchestrator(factory)
    try:
        spec = factory.load_team_spec(req.team_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown team_id: {req.team_id}")

    result = await orchestrator.run_team(spec, req.task, req.context or {})
    latency_ms = (time.perf_counter() - start) * 1000
    # Aggregate cost if steps have metrics
    total_cost = 0.0
    try:
        for s in result.get("steps", []):
            total_cost += float(s.get("metrics", {}).get("cost_usd", 0.0))
    except Exception:
        total_cost = 0.0
    _record_metric(latency_ms, True, cost_usd=total_cost)
    return TeamRunResponse(success=True, team_id=req.team_id, task=req.task, result=result, latency_ms=latency_ms)


@router.get("/json/stats")
async def json_stats() -> Dict[str, Any]:
    return dict(_JSON_VALIDATION)


@router.post("/json/validate", response_model=JSONValidateResponse)
async def json_validate(req: JSONValidateRequest) -> JSONValidateResponse:
    try:
        # Accept anything JSON-serializable
        json.dumps(req.payload)
        _JSON_VALIDATION["validated_count"] += 1
        _JSON_VALIDATION["last_error"] = None
        return JSONValidateResponse(valid=True)
    except Exception as e:
        _JSON_VALIDATION["invalid_count"] += 1
        _JSON_VALIDATION["last_error"] = str(e)
        return JSONValidateResponse(valid=False, error=str(e))


@router.post("/json/reset-stats")
async def json_reset_stats() -> Dict[str, Any]:
    _JSON_VALIDATION.update({"validated_count": 0, "invalid_count": 0, "last_error": None})
    return dict(_JSON_VALIDATION)
