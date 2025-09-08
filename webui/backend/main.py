from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


class CreateSessionRequest(BaseModel):
    agent: str
    repo_scope: str = "sophia"


@dataclass
class ChatSession:
    id: str
    agent: str
    repo_scope: str
    messages: List[Dict[str, Any]] = field(default_factory=list)


class WebUIServer:
    MAX_SESSIONS = 6

    def __init__(self) -> None:
        self.app = FastAPI(title="Sophia WebUI Backend", version="0.1.0")

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.sessions: Dict[str, ChatSession] = {}
        self._routes()

    def _routes(self) -> None:
        app = self.app

        @app.get("/health")
        async def health() -> Dict[str, Any]:
            return {"status": "ok", "sessions": len(self.sessions)}

        @app.post("/sessions")
        async def create_session(req: CreateSessionRequest) -> Dict[str, str]:
            if len(self.sessions) >= self.MAX_SESSIONS:
                raise HTTPException(status_code=429, detail="Maximum sessions reached")
            sid = str(uuid.uuid4())
            self.sessions[sid] = ChatSession(id=sid, agent=req.agent, repo_scope=req.repo_scope)
            return {"session_id": sid}

        @app.websocket("/ws")
        async def ws_endpoint(ws: WebSocket, session_id: Optional[str] = None) -> None:
            await ws.accept()
            sid = session_id or ""
            if not sid or sid not in self.sessions:
                await ws.send_json({"type": "error", "message": "session not found"})
                await ws.close(code=4004)
                return
            await ws.send_json({"type": "status", "message": "connected", "session_id": sid})
            try:
                while True:
                    data = await ws.receive_text()
                    # Echo back as a minimal placeholder for streaming
                    await ws.send_json({"type": "message", "agent": self.sessions[sid].agent, "text": data})
                    await asyncio.sleep(0.01)
            except WebSocketDisconnect:
                return


server = WebUIServer()
app = server.app

