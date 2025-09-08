from __future__ import annotations

import base64
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class FSListRequest(BaseModel):
    path: str = "."


class FSReadRequest(BaseModel):
    path: str
    as_base64: bool = False


class FSWriteRequest(BaseModel):
    path: str
    content: str
    create_dirs: bool = True


class FSDeleteRequest(BaseModel):
    path: str
    recursive: bool = False


@dataclass
class Policy:
    write_allowed: List[str]
    write_denied: List[str]
    backup_on_write: bool


def load_policy(workspace_name: str, root: Path) -> Policy:
    cfg = root / "mcp" / "policies" / "filesystem.yml"
    data = {}
    if cfg.exists():
        data = yaml.safe_load(cfg.read_text()) or {}
    fs = (data.get("filesystem_policies") or {}).get(workspace_name, {})
    return Policy(
        write_allowed=list(fs.get("write_allowed_paths", [])),
        write_denied=list(fs.get("write_denied_paths", [])),
        backup_on_write=bool(fs.get("backup_on_write", True)),
    )


def within(sub: Path, parent: Path) -> bool:
    try:
        sub.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def allowed_to_write(path: Path, policy: Policy) -> bool:
    p = str(path)
    for deny in policy.write_denied:
        if p.startswith(deny):
            return False
    if not policy.write_allowed:
        return True
    return any(p.startswith(allow) for allow in policy.write_allowed)


WORKSPACE_PATH = Path(os.getenv("WORKSPACE_PATH", "/workspace"))
WORKSPACE_NAME = os.getenv("WORKSPACE_NAME", "sophia")
READ_ONLY = os.getenv("READ_ONLY", "false").lower() == "true"

app = FastAPI(title=f"MCP Filesystem Server ({WORKSPACE_NAME})")
_policy = load_policy(WORKSPACE_NAME, Path("/app"))


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "workspace": str(WORKSPACE_PATH),
        "name": WORKSPACE_NAME,
        "read_only": READ_ONLY,
    }


@app.post("/fs/list")
async def fs_list(req: FSListRequest) -> Dict[str, Any]:
    target = (WORKSPACE_PATH / req.path).resolve()
    if not within(target, WORKSPACE_PATH):
        raise HTTPException(400, detail="path escapes workspace")
    if not target.exists():
        return {"entries": []}
    entries = []
    for child in sorted(target.iterdir()):
        entries.append(
            {
                "name": child.name,
                "path": str(child.relative_to(WORKSPACE_PATH)),
                "type": "dir" if child.is_dir() else "file",
                "size": child.stat().st_size,
            }
        )
    return {"entries": entries}


@app.post("/fs/read")
async def fs_read(req: FSReadRequest) -> Dict[str, Any]:
    target = (WORKSPACE_PATH / req.path).resolve()
    if not within(target, WORKSPACE_PATH) or not target.exists() or target.is_dir():
        raise HTTPException(400, detail="invalid path")
    data = target.read_bytes()
    if req.as_base64:
        return {"content_base64": base64.b64encode(data).decode("ascii")}
    try:
        return {"content": data.decode("utf-8")}
    except UnicodeDecodeError:
        return {"content_base64": base64.b64encode(data).decode("ascii")}


@app.post("/fs/write")
async def fs_write(req: FSWriteRequest) -> Dict[str, Any]:
    if READ_ONLY:
        raise HTTPException(403, detail="server is read-only")
    target = (WORKSPACE_PATH / req.path).resolve()
    if not within(target, WORKSPACE_PATH):
        raise HTTPException(400, detail="path escapes workspace")
    if not allowed_to_write(target, _policy):
        raise HTTPException(403, detail="write blocked by policy")
    if req.create_dirs:
        target.parent.mkdir(parents=True, exist_ok=True)
    if _policy.backup_on_write and target.exists():
        backup = target.with_suffix(target.suffix + ".bak")
        shutil.copy2(target, backup)
    target.write_text(req.content)
    return {"ok": True, "path": str(target.relative_to(WORKSPACE_PATH))}


@app.post("/fs/delete")
async def fs_delete(req: FSDeleteRequest) -> Dict[str, Any]:
    if READ_ONLY:
        raise HTTPException(403, detail="server is read-only")
    target = (WORKSPACE_PATH / req.path).resolve()
    if not within(target, WORKSPACE_PATH):
        raise HTTPException(400, detail="path escapes workspace")
    if not allowed_to_write(target, _policy):
        raise HTTPException(403, detail="delete blocked by policy")
    if target.is_dir():
        if req.recursive:
            shutil.rmtree(target)
        else:
            target.rmdir()
    else:
        target.unlink(missing_ok=True)
    return {"ok": True}

