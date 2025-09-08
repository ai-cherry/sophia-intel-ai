from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class GitStatusRequest(BaseModel):
    repo: str = "sophia"  # sophia|artemis


class GitCommitRequest(BaseModel):
    repo: str = "sophia"
    message: str
    add_all: bool = True


class GitPushRequest(BaseModel):
    repo: str = "sophia"
    branch: str = "main"
    force: bool = False


REPOS = {
    "sophia": Path("/workspace/sophia"),
    "artemis": Path("/workspace/artemis"),
}

SSH_AUTH_SOCK = os.getenv("SSH_AUTH_SOCK", "")

app = FastAPI(title="MCP Git Server")


def run(cmd: List[str], cwd: Path) -> str:
    env = os.environ.copy()
    if SSH_AUTH_SOCK:
        env["SSH_AUTH_SOCK"] = SSH_AUTH_SOCK
    try:
        out = subprocess.check_output(cmd, cwd=str(cwd), env=env, stderr=subprocess.STDOUT)
        return out.decode("utf-8", errors="replace")
    except subprocess.CalledProcessError as e:
        raise HTTPException(500, detail=e.output.decode("utf-8", errors="replace"))


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok", "ssh_agent": bool(SSH_AUTH_SOCK)}


@app.post("/git/status")
async def git_status(req: GitStatusRequest) -> Dict[str, Any]:
    repo = REPOS.get(req.repo)
    if not repo or not repo.exists():
        raise HTTPException(400, detail="unknown repo")
    porcelain = run(["git", "status", "--porcelain"], repo)
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo).strip()
    return {"branch": branch, "porcelain": porcelain}


@app.post("/git/commit")
async def git_commit(req: GitCommitRequest) -> Dict[str, Any]:
    repo = REPOS.get(req.repo)
    if not repo or not repo.exists():
        raise HTTPException(400, detail="unknown repo")
    if req.add_all:
        run(["git", "add", "-A"], repo)
    out = run(["git", "commit", "-m", req.message], repo)
    return {"ok": True, "output": out}


@app.post("/git/push")
async def git_push(req: GitPushRequest) -> Dict[str, Any]:
    if req.force:
        # Policy: disallow force-push by default
        raise HTTPException(403, detail="force push disabled by policy")
    repo = REPOS.get(req.repo)
    if not repo or not repo.exists():
        raise HTTPException(400, detail="unknown repo")
    out = run(["git", "push", "origin", req.branch], repo)
    return {"ok": True, "output": out}

