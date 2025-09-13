from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
import os

router = APIRouter(prefix="/api/salesforce", tags=["salesforce"]) 


def _configured() -> bool:
    return bool(
        os.getenv("SALESFORCE_CLIENT_ID")
        and os.getenv("SALESFORCE_CLIENT_SECRET")
    )


@router.get("/health")
async def health() -> dict[str, Any]:
    ok = _configured()
    return {
        "ok": ok,
        "timestamp": datetime.utcnow().isoformat(),
        "details": {
            "client_id_present": bool(os.getenv("SALESFORCE_CLIENT_ID")),
            "refresh_token_present": bool(os.getenv("SALESFORCE_REFRESH_TOKEN")),
            "login_url": os.getenv("SALESFORCE_LOGIN_URL", "unset"),
        },
    }


@router.get("/oauth/start")
async def oauth_start() -> dict[str, Any]:
    if not _configured():
        raise HTTPException(400, "Salesforce env not configured")
    # Stub: UI should redirect to Salesforce authorize URL with proper params
    return {"status": "redirect_required", "authorize_url": "<salesforce_authorize_url>"}


@router.get("/oauth/callback")
async def oauth_callback(code: Optional[str] = None, state: Optional[str] = None) -> dict[str, Any]:
    # Stub: exchange code for tokens and persist securely (not in repo)
    return {"status": "received", "code": bool(code), "state": state}


@router.post("/cdc")
async def cdc(request: Request) -> dict[str, Any]:
    # Change Data Capture notifications receiver
    try:
        body = await request.json()
    except Exception:
        body = {}
    return {"status": "ok", "received": True, "events": len(body.get("events", []))}


@router.post("/ingest")
async def ingest() -> dict[str, Any]:
    # Stub: trigger background sync (batch SOQL or Bulk API)
    return {"status": "started", "source": "salesforce"}


@router.get("/sync-status")
async def sync_status() -> dict[str, Any]:
    # Stub: surface last run stats from DB if available
    return {"status": "idle", "last_run": None, "last_error": None}

