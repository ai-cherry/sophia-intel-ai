from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

import hashlib
import hmac
import base64
import os
from fastapi import APIRouter, HTTPException, Request
from prometheus_client import Counter

router = APIRouter(prefix="/api/asana", tags=["asana"]) 

# Prometheus metrics
ASANA_WEBHOOK_REQUESTS = Counter(
    "asana_webhook_requests_total", "Asana webhook requests", ["type"]
)
ASANA_WEBHOOK_VERIFIED = Counter(
    "asana_webhook_verified_total", "Asana webhook signature verification", ["status"]
)


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
    """Handle Asana webhook handshake and event deliveries with signature verification.

    - Handshake: Asana sends X-Hook-Secret; we must echo it back as a response header.
    - Events: Asana sends X-Hook-Secret and X-Hook-Signature. We verify HMAC-SHA256.
    """
    secret_hdr = request.headers.get("X-Hook-Secret")
    sig_hdr = request.headers.get("X-Hook-Signature")
    raw = await request.body()

    # Handshake: echo back X-Hook-Secret and return 200
    if secret_hdr and not raw:
        ASANA_WEBHOOK_REQUESTS.labels(type="handshake").inc()
        from fastapi.responses import Response
        resp = Response(content="", status_code=200)
        resp.headers["X-Hook-Secret"] = secret_hdr
        return resp  # type: ignore[return-value]

    ASANA_WEBHOOK_REQUESTS.labels(type="event").inc()

    # Verify signature if headers present
    if not secret_hdr or not sig_hdr:
        ASANA_WEBHOOK_VERIFIED.labels(status="missing_headers").inc()
        raise HTTPException(status_code=401, detail="Missing Asana webhook headers")

    if not _verify_asana_signature(secret_hdr, sig_hdr, raw):
        ASANA_WEBHOOK_VERIFIED.labels(status="invalid").inc()
        raise HTTPException(status_code=401, detail="Invalid Asana webhook signature")

    ASANA_WEBHOOK_VERIFIED.labels(status="valid").inc()

    # Parse events
    try:
        body = await request.json()
    except Exception:
        body = {}

    return {"status": "ok", "received": True, "events": len(body.get("events", []))}


def _verify_asana_signature(secret_hdr: str, sig_hdr: str, body: bytes) -> bool:
    """Verify Asana webhook signature.

    Asana computes HMAC-SHA256 over the raw request body using X-Hook-Secret as the key.
    The signature may be hex or base64; we support common formats.
    """
    key = secret_hdr.encode()
    digest = hmac.new(key, body, hashlib.sha256).digest()

    # Normalize provided signature (strip known prefixes)
    sig = sig_hdr
    if sig.startswith("sha256="):
        sig = sig[len("sha256=") :]
    # Compare against hex or base64 encodings
    provided_hex = sig.lower()
    computed_hex = digest.hex()
    if hmac.compare_digest(provided_hex, computed_hex):
        return True
    try:
        provided_bytes = base64.b64decode(sig, validate=True)
        return hmac.compare_digest(provided_bytes, digest)
    except Exception:
        return False


@router.post("/ingest")
async def ingest() -> dict[str, Any]:
    return {"status": "started", "source": "asana"}


@router.get("/sync-status")
async def sync_status() -> dict[str, Any]:
    return {"status": "idle", "last_run": None, "last_error": None}
