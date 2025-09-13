"""
Gong Intelligence API router

Deep analysis on call transcripts and emails, exposing endpoints used by the Sophia dashboards
and chat. Integrates cleanly with existing Gong ingestion and RAG pipelines when available.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any
import logging
from fastapi import Query
from app.api.utils.simple_cache import TTLCache

from fastapi import APIRouter, HTTPException
from app.api.models.gong_models import GongCallsResponse, GongClientHealth

router = APIRouter(prefix="/api/gong", tags=["gong"])
logger = logging.getLogger(__name__)
_cache = TTLCache(default_ttl=120)


def _gong_configured() -> bool:
    return bool(os.getenv("GONG_ACCESS_KEY") and os.getenv("GONG_CLIENT_SECRET"))


@router.get("/calls", response_model=GongCallsResponse)
async def list_recent_calls(
    limit: int = Query(20, ge=1, le=100),
    days: int = Query(14, ge=1, le=90),
) -> dict[str, Any]:
    """Return recent Gong calls with light analysis if available.

    Falls back to a minimal structure when credentials are missing.
    """
    # Serve cached on configured systems
    cache_key = f"gong_calls_{limit}_{days}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    if not _gong_configured():
        return {
            "configured": False,
            "calls": [],
            "message": "Gong credentials missing. Set GONG_ACCESS_KEY and GONG_CLIENT_SECRET.",
        }

    try:
        # Use connector registry for standardization
        from app.connectors.registry import ConnectorRegistry
        start = datetime.utcnow() - timedelta(days=days)
        _ = start  # placeholder for future connector filters
        reg = ConnectorRegistry()
        gong = reg.get("gong")
        calls = await gong.fetch_recent() if gong else []
        # Shape a standard payload
        shaped = []
        for c in calls:
            shaped.append(
                {
                    "id": c.get("id"),
                    "title": c.get("title") or c.get("subject"),
                    "start_time": c.get("startTime"),
                    "duration_seconds": c.get("durationSeconds"),
                    "participants": c.get("participants", []),
                    "sentiment": c.get("sentiment", "unknown"),
                }
            )
        result = {"configured": True, "calls": shaped}
        _cache.set(cache_key, result, ttl=120)
        return result
    except Exception as e:  # noqa: BLE001
        # Non-fatal failure to keep the UI responsive
        logger.warning("Gong calls fetch failed: %s", e)
        return {"configured": True, "error": str(e), "calls": []}


@router.get("/client-health", response_model=GongClientHealth)
async def client_health_summary(days: int = Query(30, ge=1, le=180)) -> dict[str, Any]:
    """Client health summary derived from Gong call analytics + CRM signals when available.

    This endpoint is intentionally conservative and avoids failing when underlying data is absent.
    """
    summary: dict[str, Any] = {
        "generated_at": datetime.utcnow().isoformat(),
        "window_days": days,
        "accounts": [],
        "notes": [],
    }

    # Try to pull from RAG/analytics if present
    try:
        from app.integrations.gong_rag_pipeline import GongRAGPipeline  # type: ignore

        pipeline = GongRAGPipeline()
        # Hypothetical API: derive account-level health; fall back if unavailable
        if hasattr(pipeline, "summarize_client_health"):
            data = await pipeline.summarize_client_health(days=days)  # type: ignore[attr-defined]
            if isinstance(data, dict):
                summary.update(data)
                return summary
    except Exception as e:  # noqa: BLE001
        summary["notes"].append(f"RAG health unavailable: {e}")

    # Conservative fallback summary structure
    summary["notes"].append("Using fallback health summary; integrate CRM for richer signals.")
    return summary
