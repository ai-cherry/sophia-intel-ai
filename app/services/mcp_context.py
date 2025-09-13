from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional

import httpx
from app.core.http_client import get_client


class MCPContextManager:
    def __init__(self) -> None:
        self.fs_url = os.getenv("MCP_FS_URL", f"http://localhost:{os.getenv('MCP_FS_PORT','8082')}")
        self.git_url = os.getenv("MCP_GIT_URL", f"http://localhost:{os.getenv('MCP_GIT_PORT','8084')}")
        self.mem_url = os.getenv("MCP_MEMORY_URL", f"http://localhost:{os.getenv('MCP_MEMORY_PORT','8081')}")
        self.workspace = os.getenv("WORKSPACE_PATH", os.getcwd())
        self.mcp_token = os.getenv("MCP_TOKEN")
        self._client = None

    async def _client_async(self, request_id: str = None) -> httpx.AsyncClient:
        if self._client is None:
            self._client = await get_client()
        # Add headers (correlation and auth)
        if request_id or self.mcp_token:
            if not hasattr(self._client, "_headers_added"):
                original_request = self._client.request
                async def request_with_headers(method, url, **kwargs):
                    headers = kwargs.get("headers", {})
                    if request_id:
                        headers["X-Request-ID"] = request_id
                    if self.mcp_token:
                        headers["Authorization"] = f"Bearer {self.mcp_token}"
                    kwargs["headers"] = headers
                    return await original_request(method, url, **kwargs)
                self._client.request = request_with_headers
                self._client._headers_added = True
        return self._client

    async def get_repository_structure(self) -> Dict[str, Any]:
        try:
            body = {"root": ".", "globs": ["**/*"], "limit": 1000}
            client = await self._client_async()
            r = await client.post(f"{self.fs_url}/repo/list", json=body)
            r.raise_for_status()
            files = r.json().get("files", [])
            # Summarize
            by_ext: Dict[str, int] = {}
            for f in files:
                ext = str(f.get("lang") or "").lower() or "other"
                by_ext[ext] = by_ext.get(ext, 0) + 1
            key_dirs = [d for d in ["app", "sophia-intel-app", "mcp", "builder_cli", "tests", "scripts"] if os.path.isdir(d)]
            return {"total_files": len(files), "by_language": by_ext, "key_directories": key_dirs}
        except Exception as e:
            return {"error": str(e)}

    async def get_git_status(self) -> Dict[str, Any]:
        try:
            client = await self._client_async()
            r = await client.post(f"{self.git_url}/git/status", json={"repo": "sophia"})
            r.raise_for_status()
            data = r.json()
            porcelain = data.get("porcelain", "").splitlines()
            modified = sum(1 for l in porcelain if l and not l.startswith("??"))
            untracked = sum(1 for l in porcelain if l.startswith("??"))
            return {
                "branch": data.get("branch"),
                "modified_count": modified,
                "untracked_count": untracked,
            }
        except Exception as e:
            return {"error": str(e)}

    async def get_recent_commits(self, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            client = await self._client_async()
            r = await client.post(f"{self.git_url}/git/log", json={"repo": "sophia", "limit": limit, "pretty": True})
            r.raise_for_status()
            return r.json().get("commits", [])
        except Exception:
            return []

    async def memory_search(self, query: str, namespace: str = "sophia", limit: int = 5) -> List[Dict[str, Any]]:
        try:
            body = {"namespace": namespace, "query": query, "limit": limit}
            client = await self._client_async()
            r = await client.post(f"{self.mem_url}/memory/search", json=body)
            r.raise_for_status()
            return r.json().get("results", [])
        except Exception:
            return []

    async def build_compact_context(self, budget_chars: int = 2000) -> Dict[str, Any]:
        """Build a compact repository context under budget_chars.

        Strategy: small summaries of structure, status, and a few commit/memory snippets.
        """
        structure = await self.get_repository_structure()
        status = await self.get_git_status()
        commits = await self.get_recent_commits(limit=5)
        mem = await self.memory_search(query="design decision", limit=3)
        ctx: Dict[str, Any] = {
            "structure": structure,
            "git": status,
            "commits": commits,
            "memory_snippets": [m.get("content") for m in mem if m.get("content")],
        }

        # Enforce char budget by pruning arrays first
        def size(d: Dict[str, Any]) -> int:
            try:
                return len(json.dumps(d))
            except Exception:
                return 10**9

        if size(ctx) <= budget_chars:
            return ctx

        # Trim commits and memory_snippets progressively
        for commit_limit in (3, 2, 1, 0):
            ctx["commits"] = commits[:commit_limit]
            for mem_limit in (2, 1, 0):
                ctx["memory_snippets"] = ctx["memory_snippets"][:mem_limit]
                if size(ctx) <= budget_chars:
                    return ctx

        # As a last resort, drop structure details
        ctx["structure"] = {
            "total_files": structure.get("total_files"),
            "by_language": structure.get("by_language", {}),
        }
        return ctx


_mgr: Optional[MCPContextManager] = None


async def get_mcp_context_manager() -> MCPContextManager:
    global _mgr
    if _mgr is None:
        _mgr = MCPContextManager()
    return _mgr
