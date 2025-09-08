from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any


class StdioMCPClient:
    """
    Minimal stdio MCP client.

    Spawns the stdio server per call for simplicity and safety.
    Expects the stdio server to output exactly one JSON line per request.
    """

    def __init__(self, repo_root: Path | None = None, cmd_path: Path | None = None) -> None:
        self.repo_root = repo_root or Path.cwd()
        default_cmd = self.repo_root / "bin/mcp-fs-memory"
        self.cmd_path = cmd_path or default_cmd
        if not self.cmd_path.exists():
            raise FileNotFoundError(f"MCP stdio server not found at {self.cmd_path}")

    def _call(self, method: str, params: dict[str, Any] | None = None, req_id: str = "1") -> Any:
        req = {"id": req_id, "method": method, "params": params or {}}
        p = subprocess.run(
            [str(self.cmd_path)],
            input=(json.dumps(req) + "\n").encode("utf-8"),
            cwd=str(self.repo_root),
            capture_output=True,
        )
        if p.returncode != 0:
            raise RuntimeError(
                f"MCP process failed: rc={p.returncode}, stderr={p.stderr.decode('utf-8', 'ignore')}"
            )
        # Expect first line of stdout to be the response
        out = p.stdout.decode("utf-8", "ignore").strip().splitlines()
        if not out:
            raise RuntimeError("Empty response from MCP server")
        resp = json.loads(out[0])
        if resp.get("error"):
            raise RuntimeError(str(resp["error"]))
        return resp.get("result") or resp.get("data")

    # Convenience wrappers
    def initialize(self) -> Any:
        return self._call("initialize", {})

    def ping(self) -> Any:
        return self._call("ping", {})

    def fs_list(self, path: str = ".") -> Any:
        return self._call("fs.list", {"path": path})

    def fs_read(self, path: str, max_bytes: int = 500_000) -> Any:
        return self._call("fs.read", {"path": path, "max_bytes": max_bytes})

    def fs_write(self, path: str, content: str) -> Any:
        return self._call("fs.write", {"path": path, "content": content})

    def fs_search(self, query: str, root: str = ".", max_results: int = 200) -> Any:
        return self._call("fs.search", {"query": query, "root": root, "max_results": max_results})

    def memory_add(
        self,
        topic: str,
        content: str,
        source: str = "artemis",
        tags: list[str] | None = None,
        memory_type: str = "semantic",
    ) -> Any:
        return self._call(
            "memory.add",
            {
                "topic": topic,
                "content": content,
                "source": source,
                "tags": tags or [],
                "memory_type": memory_type,
            },
        )

    def memory_search(self, query: str, limit: int = 20) -> Any:
        return self._call("memory.search", {"query": query, "limit": limit})

    def repo_index(self, root: str = ".", max_bytes_per_file: int = 200_000) -> Any:
        return self._call("repo.index", {"root": root, "max_bytes_per_file": max_bytes_per_file})

    def git_status(self) -> Any:
        return self._call("git.status", {})

    def git_diff(self, path: str | None = None, staged: bool = False) -> Any:
        p: dict[str, Any] = {}
        if path:
            p["path"] = path
        if staged:
            p["staged"] = True
        return self._call("git.diff", p)


def detect_stdio_mcp(repo_root: Path | None = None) -> StdioMCPClient | None:
    root = repo_root or Path.cwd()
    cmd = root / "bin/mcp-fs-memory"
    if cmd.exists() and os.access(cmd, os.X_OK):
        try:
            client = StdioMCPClient(root, cmd)
            client.initialize()
            return client
        except Exception:
            return None
    return None
