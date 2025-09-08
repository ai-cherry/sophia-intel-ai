"""
Sophia Integrations summary endpoints (lightweight)
Provides minimal read endpoints for Asana, Linear, and Gong to power the UI.
Falls back to demo data when credentials are not configured.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.core.env import load_env_once

load_env_once()

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


def _demo_task(_src: str, idx: int) -> Dict[str, Any]:
    return {
        "id": f"{_src}-demo-{idx}",
        "title": "Follow up enterprise onboarding" if idx == 1 else "Resolve billing bug",
        "assignee": "Alex" if idx == 1 else "Jamie",
        "status": "stuck" if idx == 1 else "in_progress",
        "source": _src,
        "updated_at": datetime.utcnow().isoformat(),
        "demo": True,
    }


def _demo_call(idx: int) -> Dict[str, Any]:
    return {
        "id": f"gong-demo-{idx}",
        "title": "QBR with ACME" if idx == 1 else "Demo with Globex",
        "when": (datetime.utcnow() - timedelta(days=idx)).isoformat(),
        "risk": "MEDIUM" if idx == 1 else "LOW",
        "rep": "Taylor" if idx == 1 else "Jordan",
        "demo": True,
    }


@router.get("/asana/tasks")
async def list_asana_tasks() -> Dict[str, Any]:
    token = os.getenv("ASANA_ACCESS_TOKEN") or os.getenv("ASANA_API_TOKEN")
    if not token:
        return {"items": [_demo_task("asana", 1), _demo_task("asana", 2)], "demo": True}
    try:
        from app.integrations.asana_client import AsanaClient  # type: ignore

        client = AsanaClient()
        # Minimal sample: fetch my tasks (placeholder until full wiring)
        items: List[Dict[str, Any]] = []
        # Real calls could be: await client.list_tasks(...)
        return {"items": items, "demo": False}
    except Exception as e:
        # Fall back to demo if SDK not configured
        return {"items": [_demo_task("asana", 1), _demo_task("asana", 2)], "demo": True, "error": str(e)}


@router.get("/linear/issues")
async def list_linear_issues() -> Dict[str, Any]:
    token = os.getenv("LINEAR_API_KEY")
    if not token:
        return {"items": [_demo_task("linear", 1), _demo_task("linear", 2)], "demo": True}
    try:
        from app.integrations.linear_client import LinearClient  # type: ignore

        client = LinearClient()
        items: List[Dict[str, Any]] = []
        return {"items": items, "demo": False}
    except Exception as e:
        return {"items": [_demo_task("linear", 1), _demo_task("linear", 2)], "demo": True, "error": str(e)}


@router.get("/gong/calls")
async def list_gong_calls() -> Dict[str, Any]:
    key = os.getenv("GONG_ACCESS_KEY") and os.getenv("GONG_CLIENT_SECRET")
    if not key:
        return {"items": [_demo_call(1), _demo_call(2)], "demo": True}
    try:
        # Minimal placeholder. Full wiring would use Gong client.
        items: List[Dict[str, Any]] = []
        return {"items": items, "demo": False}
    except Exception as e:
        return {"items": [_demo_call(1), _demo_call(2)], "demo": True, "error": str(e)}

