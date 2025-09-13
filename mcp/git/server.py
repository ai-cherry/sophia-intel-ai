from __future__ import annotations
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
class GitStatusRequest(BaseModel):
    repo: str = "sophia"  # sophia|
class GitCommitRequest(BaseModel):
    repo: str = "sophia"
    message: str
    add_all: bool = True
class GitPushRequest(BaseModel):
    repo: str = "sophia"
    branch: str = "main"
    force: bool = False

class GitLogRequest(BaseModel):
    repo: str = "sophia"
    limit: int = 10
    pretty: bool = True
# Resolve workspace root from environment (aligns with filesystem MCP)
WORKSPACE_PATH = Path(os.getenv("WORKSPACE_PATH", str(Path.cwd()))).resolve()

# Default repo mapping points to current workspace
REPOS = {
    "sophia": WORKSPACE_PATH,
    "": WORKSPACE_PATH.parent,
}
SSH_AUTH_SOCK = os.getenv("SSH_AUTH_SOCK", "")
app = FastAPI(title="MCP Git Server")
_mcp_token = os.getenv("MCP_TOKEN")
_dev_bypass = os.getenv("MCP_DEV_BYPASS", "false").lower() in ("1", "true", "yes")


@app.middleware("http")
async def mcp_auth(request: Request, call_next):
    if request.url.path == "/health":
        return await call_next(request)
    if not _mcp_token:
        if _dev_bypass:
            return await call_next(request)
        return JSONResponse({"error": "MCP_TOKEN not set"}, status_code=401)
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    token = auth.split(" ", 1)[1]
    if token != _mcp_token:
        return JSONResponse({"error": "Invalid token"}, status_code=401)
    return await call_next(request)
# Load git policy
_git_policy = {
    "protected_branches": ["main", "production"],
    "force_push_allowed": False,
}
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
        out = subprocess.check_output(
            cmd, cwd=str(cwd), env=env, stderr=subprocess.STDOUT
        )
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
            raise HTTPException(
                403, detail="force push to protected branch disabled by policy"
            )
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

@app.post("/git/log")
async def git_log(req: GitLogRequest) -> Dict[str, Any]:
    """Return recent commits for the repo.

    - limit: number of commits (1-100)
    - pretty: if true, parse into structured entries; otherwise return raw text
    """
    repo = REPOS.get(req.repo)
    if not repo or not repo.exists():
        raise HTTPException(400, detail="unknown repo")
    limit = max(1, min(int(req.limit or 10), 100))
    fmt = "%h%x09%an%x09%ad%x09%s"
    out = run(["git", "log", f"-n{limit}", f"--pretty=format:{fmt}", "--date=iso"], repo)
    if not req.pretty:
        return {"raw": out}
    entries = []
    for line in out.splitlines():
        parts = line.split("\t", 3)
        if len(parts) != 4:
            # Fallback: put the whole line as message
            entries.append({"hash": "", "author": "", "date": "", "message": line.strip()})
            continue
        sh, author, date, msg = parts
        entries.append({
            "hash": sh,
            "author": author,
            "date": date,
            "message": msg,
        })
    return {"commits": entries}
