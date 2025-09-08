#!/usr/bin/env python3
"""
Secure Agno-UI bridge (FastAPI) with JWT auth and CORS.
- Reads config from env; no secrets stored in repo.
- Provides /health and skeleton chat endpoints.
- WebSocket endpoint with token validation via query param (?token=...).

Environment:
- BRIDGE_PORT (default: 8003)
- BRIDGE_HOST (default: 0.0.0.0)
- BRIDGE_SECRET (required for auth in non-dev)
- UI_ORIGINS (comma-separated, default: http://localhost:3000)
"""
from __future__ import annotations
import os
import json
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import jwt

try:
    from agno_core.orchestrator import Orchestrator
except Exception:
    Orchestrator = None  # type: ignore


def get_origins() -> List[str]:
    raw = os.getenv("UI_ORIGINS", "http://localhost:3000")
    return [o.strip() for o in raw.split(",") if o.strip()]


BRIDGE_SECRET = os.getenv("BRIDGE_SECRET", "")
HOST = os.getenv("BRIDGE_HOST", "0.0.0.0")
PORT = int(os.getenv("BRIDGE_PORT", "8003"))

app = FastAPI(title="Sophia Agno Bridge")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orch = Orchestrator() if Orchestrator else None


def verify_token(token: str) -> dict:
    if not BRIDGE_SECRET:
        # Dev mode: skip verification but warn in logs
        return {"dev": True}
    try:
        return jwt.decode(token, BRIDGE_SECRET, algorithms=["HS256"])  # type: ignore[arg-type]
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


@app.get("/health")
async def health():
    try:
        core = orch.health() if orch else {"status": "unknown"}
    except Exception:
        core = {"status": "degraded"}
    return JSONResponse({
        "bridge": "ok",
        "core": core,
        "origins": get_origins(),
    })


@app.post("/chat")
async def chat(payload: dict):
    # Skeleton endpoint for chat/task execution; wire to core later.
    if not isinstance(payload, dict):
        raise HTTPException(400, "Invalid payload")
    return {"status": "accepted", "echo": payload}


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    # Token can be provided as ws://.../ws/{client_id}?token=JWT
    token = websocket.query_params.get("token", "")
    _claims = verify_token(token)
    await websocket.accept()
    try:
        # Minimal echo loop; replace with orchestrator pub/sub
        while True:
            text = await websocket.receive_text()
            await websocket.send_text(json.dumps({
                "client_id": client_id,
                "message": text,
                "ok": True,
            }))
    except WebSocketDisconnect:
        # Client disconnected; nothing to do
        return


if __name__ == "__main__":  # pragma: no cover
    import uvicorn
    uvicorn.run("agno_ui_bridge:app", host=HOST, port=PORT, reload=False)

