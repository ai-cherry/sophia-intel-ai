from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

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

# Load git policy
_git_policy = {"protected_branches": ["main", "production"], "force_push_allowed": False}
try:
    policy_path = Path(__file__).resolve().parent.parent / "policies" / "git.yml"
    if policy_path.exists():
        with open(policy_path) as f:
            loaded = yaml.safe_load(f) or {}
            _git_policy.update(loaded)
except Exception:
    pass


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
    tpl = _git_policy.get("commit_template")
    message = tpl.replace("{message}", req.message) if tpl else req.message
    out = run(["git", "commit", "-m", message], repo)
    return {"ok": True, "output": out}


@app.post("/git/push")
async def git_push(req: GitPushRequest) -> Dict[str, Any]:
    # Policy: handle protected branches and force push
    if req.branch in _git_policy.get("protected_branches", []):
        if req.force and not _git_policy.get("force_push_allowed", False):
            raise HTTPException(403, detail="force push to protected branch disabled by policy")
    else:
        if req.force and not _git_policy.get("force_push_allowed", False):
            raise HTTPException(403, detail="force push disabled by policy")
    repo = REPOS.get(req.repo)
    if not repo or not repo.exists():
        raise HTTPException(400, detail="unknown repo")
    args = ["git", "push", "origin", req.branch]
    if req.force and _git_policy.get("force_push_allowed", False):
        args.insert(2, "--force")
    out = run(args, repo)
    return {"ok": True, "output": out}
