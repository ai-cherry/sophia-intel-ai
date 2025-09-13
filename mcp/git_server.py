"""
MCP Git Server with repository indexing.
Provides repo indexing, symbol search, and dependency graph for agents.
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException, BackgroundTasks

# Import our indexer
import sys
sys.path.append(str(Path(__file__).parent.parent))
from builder_cli.lib.indexer import RepoIndexer, AgentIndexAccess

app = FastAPI(title="MCP Git Server")

# Environment
WORKSPACE_PATH = os.getenv("GIT_REPO_PATH", "/workspace")
INDEX_ENABLED = os.getenv("INDEX_ENABLED", "true").lower() in ("1", "true", "yes")


class RepoInfo(BaseModel):
    """Repository information."""
    path: str
    name: str
    branch: str = "main"
    indexed: bool = False
    files: int = 0
    symbols: int = 0
    last_updated: float = 0.0


class IndexRequest(BaseModel):
    """Repository index request."""
    path: str
    force: bool = False


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "server": "git",
        "indexing": "enabled" if INDEX_ENABLED else "disabled",
        "workspace": WORKSPACE_PATH
    }


@app.get("/repos")
async def list_repos() -> List[RepoInfo]:
    """List repositories with index status."""
    if not INDEX_ENABLED:
        return []
    
    access = AgentIndexAccess()
    indexed = access.get_indexed_repos()
    
    repos = []
    for repo in indexed:
        repos.append(RepoInfo(
            path=repo["path"],
            name=Path(repo["path"]).name,
            indexed=True,
            files=repo.get("files", 0),
            symbols=repo.get("symbols", 0),
            last_updated=repo.get("updated", 0.0)
        ))
    
    # Also check workspace for unindexed repos
    workspace = Path(WORKSPACE_PATH)
    if workspace.exists():
        for item in workspace.iterdir():
            if item.is_dir() and (item / ".git").exists():
                # Check if already indexed
                if not any(r.path == str(item) for r in repos):
                    repos.append(RepoInfo(
                        path=str(item),
                        name=item.name,
                        indexed=False
                    ))
    
    return repos


@app.post("/index")
async def index_repository(request: IndexRequest, background_tasks: BackgroundTasks):
    """Index a repository for searching."""
    if not INDEX_ENABLED:
        raise HTTPException(status_code=400, detail="Indexing is disabled")
    
    repo_path = Path(request.path)
    if not repo_path.exists():
        raise HTTPException(status_code=404, detail=f"Repository not found: {request.path}")
    
    if not (repo_path / ".git").exists():
        raise HTTPException(status_code=400, detail=f"Not a git repository: {request.path}")
    
    # Run indexing in background
    def do_index():
        indexer = RepoIndexer(repo_path)
        indexer.refresh()
    
    background_tasks.add_task(do_index)
    
    return {"status": "indexing", "path": str(repo_path)}


@app.get("/index/{repo_id}/status")
async def get_index_status(repo_id: str):
    """Get indexing status for a repository."""
    access = AgentIndexAccess()
    repos = access.get_indexed_repos()
    
    for repo in repos:
        if repo["id"] == repo_id:
            return {
                "indexed": True,
                "files": repo.get("files", 0),
                "symbols": repo.get("symbols", 0),
                "deps": repo.get("deps", 0),
                "updated": repo.get("updated", 0)
            }
    
    return {"indexed": False}


@app.get("/search/symbols")
async def search_symbols(q: str, limit: int = 50):
    """Search for symbols across indexed repositories."""
    if not INDEX_ENABLED:
        return {"results": [], "query": q}
    
    access = AgentIndexAccess()
    results = access.find_symbol(q)
    
    return {
        "results": results[:limit],
        "query": q,
        "total": len(results)
    }


@app.get("/search/files")
async def search_files(pattern: str, limit: int = 100):
    """Search for files by pattern."""
    if not INDEX_ENABLED:
        return {"results": [], "pattern": pattern}
    
    access = AgentIndexAccess()
    results = access.search_files(pattern)
    
    return {
        "results": results[:limit],
        "pattern": pattern,
        "total": len(results)
    }


@app.get("/repos/{repo_id}/dependencies")
async def get_dependencies(repo_id: str, file_path: str):
    """Get dependencies for a file."""
    access = AgentIndexAccess()
    repos = access.get_indexed_repos()
    
    repo_path = None
    for repo in repos:
        if repo["id"] == repo_id:
            repo_path = repo["path"]
            break
    
    if not repo_path:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    deps = access.get_dependencies(repo_path, file_path)
    
    return {
        "file": file_path,
        "dependencies": deps,
        "repo_id": repo_id
    }


@app.get("/repos/{repo_id}/files")
async def list_repo_files(repo_id: str):
    """List all files in an indexed repository."""
    access = AgentIndexAccess()
    repos = access.get_indexed_repos()
    
    repo_path = None
    for repo in repos:
        if repo["id"] == repo_id:
            repo_path = repo["path"]
            break
    
    if not repo_path:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Get files from index
    import redis
    r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/2"), decode_responses=True)
    files = r.hgetall(f"repo:{repo_id}:files")
    
    file_list = []
    for file_path, meta_json in files.items():
        meta = json.loads(meta_json) if meta_json else {}
        file_list.append({
            "path": file_path,
            **meta
        })
    
    return {
        "repo_id": repo_id,
        "files": file_list,
        "total": len(file_list)
    }


@app.post("/repos/{repo_id}/refresh")
async def refresh_index(repo_id: str, background_tasks: BackgroundTasks):
    """Refresh the index for a repository."""
    if not INDEX_ENABLED:
        raise HTTPException(status_code=400, detail="Indexing is disabled")
    
    access = AgentIndexAccess()
    repos = access.get_indexed_repos()
    
    repo_path = None
    for repo in repos:
        if repo["id"] == repo_id:
            repo_path = repo["path"]
            break
    
    if not repo_path:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Run refresh in background
    def do_refresh():
        indexer = RepoIndexer(Path(repo_path))
        indexer.refresh()
    
    background_tasks.add_task(do_refresh)
    
    return {"status": "refreshing", "repo_id": repo_id}


@app.get("/git/status")
async def git_status(repo_path: Optional[str] = None):
    """Get git status for a repository."""
    path = repo_path or WORKSPACE_PATH
    
    if not Path(path).exists():
        raise HTTPException(status_code=404, detail="Repository not found")
    
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        files = []
        for line in result.stdout.strip().split("\n"):
            if line:
                status = line[:2]
                file = line[3:]
                files.append({"status": status.strip(), "file": file})
        
        return {
            "repo": path,
            "files": files,
            "clean": len(files) == 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/git/log")
async def git_log(repo_path: Optional[str] = None, limit: int = 20):
    """Get git log for a repository."""
    path = repo_path or WORKSPACE_PATH
    
    if not Path(path).exists():
        raise HTTPException(status_code=404, detail="Repository not found")
    
    try:
        result = subprocess.run(
            ["git", "log", f"-{limit}", "--oneline"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        commits = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split(" ", 1)
                if len(parts) == 2:
                    commits.append({
                        "hash": parts[0],
                        "message": parts[1]
                    })
        
        return {
            "repo": path,
            "commits": commits,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)