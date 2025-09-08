from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from app.llm.provider_router import EnhancedProviderRouter
import httpx
import os


class CreateSessionRequest(BaseModel):
    agent: str
    repo_scope: str = "sophia"


class ProposalChange(BaseModel):
    capability: str = "fs"  # currently only fs
    scope: str = "sophia"  # sophia|artemis
    path: str
    content: str


class CreateProposalRequest(BaseModel):
    changes: List[ProposalChange]
    commit_message: str | None = None
    auto_commit: bool = False


@dataclass
class ChatSession:
    id: str
    agent: str
    repo_scope: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    proposals: Dict[str, Dict[str, Any]] = field(default_factory=dict)


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
        self.mcp_urls = {
            "fs_sophia": os.getenv(
                "MCP_FILESYSTEM_SOPHIA_URL", "http://mcp-filesystem-sophia:8000"
            ),
            "fs_artemis": os.getenv(
                "MCP_FILESYSTEM_ARTEMIS_URL", "http://mcp-filesystem-artemis:8000"
            ),
            "git": os.getenv("MCP_GIT_URL", "http://mcp-git:8000"),
            "memory": os.getenv("MCP_MEMORY_URL", "http://mcp-memory:8000"),
        }
        self.router = EnhancedProviderRouter()
        self._routes()

    def _routes(self) -> None:
        app = self.app

        @app.get("/health")
        async def health() -> Dict[str, Any]:
            return {"status": "ok", "sessions": len(self.sessions)}

        # Serve minimal frontend
        static_dir = Path(__file__).resolve().parents[1] / "frontend"
        if static_dir.exists():
            app.mount("/ui", StaticFiles(directory=static_dir, html=True), name="ui")
        
        @app.get("/tactical")
        async def tactical_command_center():
            """Serve the tactical command center interface"""
            tactical_file = Path(__file__).resolve().parents[1] / "frontend" / "tactical-command.html"
            if tactical_file.exists():
                return FileResponse(tactical_file)
            raise HTTPException(404, detail="Tactical interface not found")

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

        @app.post("/tools/invoke")
        async def tools_invoke(payload: Dict[str, Any]) -> Dict[str, Any]:
            """Proxy minimal tool calls to MCP services.
            Expected payload:
              {"capability":"fs|git|memory", "scope":"sophia|artemis", "action":"list|read|write|...", "params":{...}}
            """
            capability = payload.get("capability")
            action = payload.get("action")
            params = payload.get("params", {})
            scope = payload.get("scope", "sophia")

            if capability == "fs":
                base = self.mcp_urls["fs_sophia" if scope == "sophia" else "fs_artemis"]
                url = f"{base}/fs/{action}"
            elif capability == "git":
                base = self.mcp_urls["git"]
                url = f"{base}/git/{action}"
            elif capability == "memory":
                base = self.mcp_urls["memory"]
                url = f"{base}/memory/{action}"
            else:
                raise HTTPException(400, detail="unknown capability")

            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(url, json=params)
                r.raise_for_status()
                return r.json()

        @app.post("/agents/complete")
        async def agent_complete(payload: Dict[str, Any]) -> Dict[str, Any]:
            """Agent completion with simple streaming behavior.
            Payload:
              {session_id?, task_type, messages, provider?, model?}
            """
            sid = payload.get("session_id")
            task_type = payload.get("task_type", "generation")
            messages = payload.get("messages", [])
            provider = payload.get("provider")
            model = payload.get("model")

            text = await self.router.complete(
                task_type=task_type,
                messages=messages,
                provider_override=provider,
                model_override=model,
            )
            # Future: stream tokens via per-session queue; for now, return full text
            r = self.router._route_for(task_type)
            route_meta = {"provider": provider or r.provider, "model": model or r.model}
            return {"text": text, "route": route_meta}

        @app.post("/sessions/{session_id}/proposals")
        async def create_proposal(session_id: str, req: CreateProposalRequest) -> Dict[str, Any]:
            if session_id not in self.sessions:
                raise HTTPException(404, detail="session not found")
            pid = str(uuid.uuid4())
            self.sessions[session_id].proposals[pid] = {
                "id": pid,
                "changes": [c.dict() for c in req.changes],
                "commit_message": req.commit_message,
                "auto_commit": req.auto_commit,
                "status": "pending",
            }
            return {"proposal_id": pid}

        @app.get("/sessions/{session_id}/proposals")
        async def list_proposals(session_id: str) -> Dict[str, Any]:
            if session_id not in self.sessions:
                raise HTTPException(404, detail="session not found")
            return {"proposals": list(self.sessions[session_id].proposals.values())}

        @app.post("/sessions/{session_id}/proposals/{proposal_id}/approve")
        async def approve_proposal(session_id: str, proposal_id: str) -> Dict[str, Any]:
            sess = self.sessions.get(session_id)
            if not sess:
                raise HTTPException(404, detail="session not found")
            prop = sess.proposals.get(proposal_id)
            if not prop:
                raise HTTPException(404, detail="proposal not found")

            # Apply FS changes
            async with httpx.AsyncClient(timeout=60) as client:
                for ch in prop["changes"]:
                    if ch["capability"] != "fs":
                        raise HTTPException(400, detail="only fs changes supported")
                    base = self.mcp_urls[
                        "fs_sophia" if ch.get("scope", "sophia") == "sophia" else "fs_artemis"
                    ]
                    url = f"{base}/fs/write"
                    payload = {"path": ch["path"], "content": ch["content"], "create_dirs": True}
                    r = await client.post(url, json=payload)
                    r.raise_for_status()

                # Optional commit
                if prop.get("auto_commit") and prop.get("commit_message"):
                    repo = "sophia" if sess.repo_scope == "sophia" else "artemis"
                    r = await client.post(
                        f"{self.mcp_urls['git']}/git/commit",
                        json={"repo": repo, "message": prop["commit_message"], "add_all": True},
                    )
                    r.raise_for_status()

            prop["status"] = "approved"
            return {"ok": True}

        @app.post("/sessions/{session_id}/proposals/{proposal_id}/reject")
        async def reject_proposal(session_id: str, proposal_id: str) -> Dict[str, Any]:
            sess = self.sessions.get(session_id)
            if not sess:
                raise HTTPException(404, detail="session not found")
            prop = sess.proposals.get(proposal_id)
            if not prop:
                raise HTTPException(404, detail="proposal not found")
            prop["status"] = "rejected"
            return {"ok": True}
            await ws.send_json({"type": "status", "message": "connected", "session_id": sid})
            try:
                while True:
                    data = await ws.receive_text()
                    # Echo back as a minimal placeholder for streaming
                    await ws.send_json(
                        {"type": "message", "agent": self.sessions[sid].agent, "text": data}
                    )
                    await asyncio.sleep(0.01)
            except WebSocketDisconnect:
                return


server = WebUIServer()
app = server.app
