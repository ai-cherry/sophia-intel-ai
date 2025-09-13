from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
import os

router = APIRouter(prefix="/api/asana", tags=["asana"]) 


def _configured() -> bool:
    return bool(os.getenv("ASANA_CLIENT_ID") and os.getenv("ASANA_CLIENT_SECRET")) or bool(os.getenv("ASANA_PAT"))


@router.get("/health")
async def health() -> dict[str, Any]:
    ok = _configured()
    return {
        "ok": ok,
        "timestamp": datetime.utcnow().isoformat(),
        "details": {
            "client_id_present": bool(os.getenv("ASANA_CLIENT_ID")),
            "pat_present": bool(os.getenv("ASANA_PAT")),
            "workspace": os.getenv("ASANA_WORKSPACE_ID", "unset"),
        },
    }


@router.get("/oauth/start")
async def oauth_start() -> dict[str, Any]:
    if not (os.getenv("ASANA_CLIENT_ID") and os.getenv("ASANA_CLIENT_SECRET")):
        raise HTTPException(400, "Asana OAuth env not configured")
    return {"status": "redirect_required", "authorize_url": "<asana_authorize_url>"}


@router.get("/oauth/callback")
async def oauth_callback(code: Optional[str] = None, state: Optional[str] = None) -> dict[str, Any]:
    return {"status": "received", "code": bool(code), "state": state}


@router.post("/webhooks")
async def webhooks(request: Request) -> dict[str, Any]:
    # Asana webhook handshake + events
    try:
        body = await request.json()
    except Exception:
        body = {}
    return {"status": "ok", "received": True, "events": len(body.get("events", []))}


@router.post("/ingest")
async def ingest() -> dict[str, Any]:
    return {"status": "started", "source": "asana"}


@router.get("/sync-status")
async def sync_status() -> dict[str, Any]:
    return {"status": "idle", "last_run": None, "last_error": None}

