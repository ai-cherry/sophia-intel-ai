from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(prefix="/api/observability", tags=["observability"]) 


@router.get("/slo")
async def slo_dashboard() -> Dict[str, Any]:
    """Expose SLO dashboard data if available.

    Falls back to a minimal structure when the otel module isn't configured.
    """
    try:
        from app.observability.otel import get_slo_dashboard_data  # type: ignore

        data = get_slo_dashboard_data()
        return {"status": "ok", "slo": data}
    except Exception:
        return {"status": "partial", "slo": {"message": "SLO data unavailable"}}


@router.get("/summary")
async def observability_summary() -> Dict[str, Any]:
    """High-level observability snapshot if metrics collector is present."""
    try:
        from app.observability.metrics_collector import (  # type: ignore
            MetricsCollector,
        )

        collector = MetricsCollector()
        data = collector.get_dashboard_data()
        return {"status": "ok", "summary": data}
    except Exception:
        return {"status": "partial", "summary": {"message": "Metrics collector unavailable"}}

