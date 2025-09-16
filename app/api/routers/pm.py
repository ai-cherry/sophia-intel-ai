from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(prefix="/api/pm", tags=["pm", "project-management"]) 


def _has_asana() -> bool:
    return bool(os.getenv("ASANA_PAT") or os.getenv("ASANA_PAT_TOKEN") or os.getenv("ASANA_API_TOKEN"))


def _has_linear() -> bool:
    return bool(os.getenv("LINEAR_API_KEY"))


@router.get("/summary")
async def pm_summary() -> Dict[str, Any]:
    """Consolidated PM snapshot (Asana + Linear) if credentials available.

    Returns counts of projects/issues and a minimal status when providers are not configured.
    """
    out: Dict[str, Any] = {"status": "partial", "asana": {"enabled": _has_asana()}, "linear": {"enabled": _has_linear()}}

    # Best-effort lightweight calls behind flags in the future. For now, return env-driven status.
    # Placeholder structure for UI to render.
    out["asana"].update({
        "projects": None,
        "open_tasks": None,
        "recent_activity": None,
    })
    out["linear"].update({
        "teams": None,
        "open_issues": None,
        "recent_activity": None,
    })

    if out["asana"]["enabled"] or out["linear"]["enabled"]:
        out["status"] = "ok"
    return out

