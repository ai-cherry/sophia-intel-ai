from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
import os
from typing import Any

router = APIRouter(prefix="/api/microsoft", tags=["microsoft", "graph"]) 


def _get_env(name: str, alt: str) -> str | None:
    return os.getenv(name) or os.getenv(alt)


def _configured() -> bool:
    return bool(
        _get_env("MS_TENANT_ID", "MICROSOFT_TENANT_ID")
        and _get_env("MS_CLIENT_ID", "MICROSOFT_CLIENT_ID")
        and _get_env("MS_CLIENT_SECRET", "MICROSOFT_SECRET_KEY")
    )


@router.get("/health")
async def health() -> dict[str, Any]:
    ok = _configured()
    return {
        "ok": ok,
        "timestamp": datetime.utcnow().isoformat(),
        "details": {
            "tenant_id_present": bool(_get_env("MS_TENANT_ID", "MICROSOFT_TENANT_ID")),
            "client_id_present": bool(_get_env("MS_CLIENT_ID", "MICROSOFT_CLIENT_ID")),
            "scopes": ["ChannelMessage.Read.All", "Team.ReadBasic.All", "Files.Read.All", "Sites.Read.All"],
        },
    }


@router.get("/oauth/start")
async def oauth_start() -> dict[str, Any]:
    if not _configured():
        raise HTTPException(400, "Microsoft Graph env not configured")
    return {"status": "redirect_required", "authorize_url": "<microsoft_authorize_url>"}


@router.get("/oauth/callback")
async def oauth_callback(code: Optional[str] = None, state: Optional[str] = None) -> dict[str, Any]:
    return {"status": "received", "code": bool(code), "state": state}


@router.post("/notifications")
async def notifications(request: Request) -> dict[str, Any]:
    # Graph change notifications (validation + events)
    # Validation: Graph sends validationToken on GET; but our router is POST-only for now.
    try:
        body = await request.json()
    except Exception:
        body = {}
    return {"status": "ok", "received": True, "value_count": len(body.get("value", []))}


@router.post("/ingest")
async def ingest() -> dict[str, Any]:
    return {"status": "started", "source": "microsoft_graph"}


@router.get("/sync-status")
async def sync_status() -> dict[str, Any]:
    return {"status": "idle", "last_run": None, "last_error": None}


# ---------------- Real Graph endpoints (app-only) ----------------

def _make_client():
    from app.integrations.microsoft_graph_client import MicrosoftGraphClient

    return MicrosoftGraphClient()


@router.get("/users")
async def list_users(top: int = 5) -> dict[str, Any]:
    if not _configured():
        raise HTTPException(400, "Microsoft Graph env not configured")
    client = _make_client()
    data = await client.list_users(top=top)
    return {"ok": True, "count": len(data.get("value", [])), "value": data.get("value", [])}


@router.get("/teams")
async def list_teams(top: int = 5) -> dict[str, Any]:
    if not _configured():
        raise HTTPException(400, "Microsoft Graph env not configured")
    client = _make_client()
    data = await client.list_teams(top=top)
    return {"ok": True, "count": len(data.get("value", [])), "value": data.get("value", [])}


@router.get("/drive-root")
async def drive_root() -> dict[str, Any]:
    if not _configured():
        raise HTTPException(400, "Microsoft Graph env not configured")
    client = _make_client()
    data = await client.drive_root()
    return {"ok": True, "drive": data}
