#!/usr/bin/env python3
"""
Minimal stdio MCP-style server for local tools.

Capabilities:
- initialize, ping
- fs.read, fs.write, fs.list, fs.search
- memory.add, memory.search (via SupermemoryStore)
- repo.index (index repo files into Supermemory)
- git.status, git.diff

Protocol: newline-delimited JSON requests and responses, with fields:
  {"id": "1", "method": "fs.list", "params": {"path": "."}}
Outputs a single JSON response per request with matching id.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[2]

# Supermemory store (SQLite FTS) for memory.* and repo.index
try:
    # Prefer in-repo store (may fail if env lacks deps)
    sys.path.insert(0, str(REPO_ROOT))
    from app.memory.supermemory_mcp import MemoryEntry as _MemoryEntry
    from app.memory.supermemory_mcp import MemoryType as _MemoryType
    from app.memory.supermemory_mcp import SupermemoryStore as _SupermemoryStore

    HAVE_SUPERMEMORY = True
except Exception:
    _SupermemoryStore = None  # type: ignore
    _MemoryEntry = None  # type: ignore
    _MemoryType = None  # type: ignore
    HAVE_SUPERMEMORY = False

import sqlite3
from datetime import datetime


class LocalMemoryStore:
    """Lightweight SQLite FTS store used if Supermemory isn't importable."""

    def __init__(
        self, db_path: str = str(REPO_ROOT / "tmp/supermemory_lite.db")
    ) -> None:
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory (
                    id TEXT PRIMARY KEY,
                    topic TEXT,
                    content TEXT,
                    source TEXT,
                    tags TEXT,
                    ts TEXT,
                    type TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
                    id UNINDEXED,
                    topic,
                    content,
                    tags,
                    content=memory,
                    content_rowid=rowid
                )
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS memory_ins AFTER INSERT ON memory BEGIN
                    INSERT INTO memory_fts(id, topic, content, tags)
                    VALUES (new.id, new.topic, new.content, new.tags);
                END
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS memory_upd AFTER UPDATE ON memory BEGIN
                    UPDATE memory_fts SET topic=new.topic, content=new.content, tags=new.tags
                    WHERE id=new.id;
                END
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS memory_del AFTER DELETE ON memory BEGIN
                    DELETE FROM memory_fts WHERE id=old.id;
                END
                """
            )
            conn.commit()

    def add_to_memory(
        self, topic: str, content: str, source: str, tags: List[str], mtype: str
    ) -> Dict[str, Any]:
        hid = (topic + "|" + source)[:240]
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO memory(id, topic, content, source, tags, ts, type) VALUES(?,?,?,?,?,?,?)",
                (
                    hid,
                    topic,
                    content,
                    source,
                    json.dumps(tags),
                    datetime.utcnow().isoformat(),
                    mtype,
                ),
            )
            conn.commit()
        return {"status": "ok", "id": hid}

    def search_memory(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """
                SELECT m.id, m.topic, m.content, m.source, m.tags, m.ts, m.type
                FROM memory m
                JOIN memory_fts f ON m.rowid = f.rowid
                WHERE f.memory_fts MATCH ?
                LIMIT ?
                """,
                (query, limit),
            )
            rows = cur.fetchall()
        out: List[Dict[str, Any]] = []
        for hid, topic, content, source, tags, ts, typ in rows:
            out.append(
                {
                    "topic": topic,
                    "content": content,
                    "source": source,
                    "tags": json.loads(tags) if tags else [],
                    "timestamp": ts,
                    "memory_type": typ,
                }
            )
        return out


TEXT_EXTS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".md",
    ".txt",
    ".ini",
    ".cfg",
    ".sh",
    ".env",
    ".sql",
}

IGNORE_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "__pycache__",
    ".venv",
    "venv",
    "tmp",
    "logs",
}


def is_text_file(path: Path) -> bool:
    if path.is_dir():
        return False
    if path.suffix.lower() in TEXT_EXTS:
        return True
    # Heuristic: treat small files without NUL bytes as text
    try:
        with open(path, "rb") as f:
            chunk = f.read(1024)
        return b"\x00" not in chunk
    except Exception:
        return False


class FsMemoryServer:
    def __init__(self) -> None:
        if HAVE_SUPERMEMORY:
            self.memory = _SupermemoryStore()
        else:
            self.memory = LocalMemoryStore()
        self.capabilities = [
            "initialize",
            "ping",
            "fs.read",
            "fs.write",
            "fs.list",
            "fs.search",
            "memory.add",
            "memory.search",
            "repo.index",
            "git.status",
            "git.diff",
        ]

    # ---------------
    # Core methods
    # ---------------
    def initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "server": "fs-memory-stdio",
            "cwd": str(REPO_ROOT),
            "capabilities": self.capabilities,
        }

    def ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"ok": True, "time": time.time()}

    # ---------------
    # Filesystem ops
    # ---------------
    def fs_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        rel = params.get("path")
        if not rel:
            raise ValueError("Missing 'path'")
        max_bytes = int(params.get("max_bytes", 500_000))
        path = (REPO_ROOT / rel).resolve()
        if not str(path).startswith(str(REPO_ROOT)):
            raise ValueError("Path outside repository")
        data: str
        with open(path, "rb") as f:
            raw = f.read(max_bytes)
        try:
            data = raw.decode("utf-8")
        except UnicodeDecodeError:
            data = raw.decode("latin-1", errors="replace")
        return {"path": str(path.relative_to(REPO_ROOT)), "content": data}

    def fs_write(self, params: Dict[str, Any]) -> Dict[str, Any]:
        rel = params.get("path")
        content = params.get("content", "")
        if not rel:
            raise ValueError("Missing 'path'")
        path = (REPO_ROOT / rel).resolve()
        if not str(path).startswith(str(REPO_ROOT)):
            raise ValueError("Path outside repository")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return {
            "path": str(path.relative_to(REPO_ROOT)),
            "bytes": len(content.encode("utf-8")),
        }

    def fs_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        rel = params.get("path", ".")
        path = (REPO_ROOT / rel).resolve()
        if not str(path).startswith(str(REPO_ROOT)):
            raise ValueError("Path outside repository")
        items = []
        for child in sorted(path.iterdir(), key=lambda p: p.name):
            items.append(
                {
                    "name": child.name,
                    "path": str(child.relative_to(REPO_ROOT)),
                    "type": "dir" if child.is_dir() else "file",
                    "size": child.stat().st_size if child.is_file() else None,
                }
            )
        return {"items": items}

    def fs_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "").strip()
        root = (REPO_ROOT / params.get("root", ".")).resolve()
        max_results = int(params.get("max_results", 200))
        if not query:
            raise ValueError("Missing 'query'")
        if not str(root).startswith(str(REPO_ROOT)):
            raise ValueError("Path outside repository")

        pattern = re.compile(re.escape(query), re.IGNORECASE)
        results: List[Dict[str, Any]] = []
        for fp in root.rglob("*"):
            if any(part in IGNORE_DIRS for part in fp.parts):
                continue
            if not is_text_file(fp):
                continue
            try:
                with open(fp, encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, start=1):
                        if pattern.search(line):
                            results.append(
                                {
                                    "path": str(fp.relative_to(REPO_ROOT)),
                                    "lineno": i,
                                    "line": line.rstrip(),
                                }
                            )
                            if len(results) >= max_results:
                                return {"results": results}
            except Exception:
                continue
        return {"results": results}

    # ---------------
    # Memory ops
    # ---------------
    def memory_add(self, params: Dict[str, Any]) -> Dict[str, Any]:
        topic = params.get("topic", "note")
        content = params.get("content", "")
        source = params.get("source", "mcp")
        tags = list(params.get("tags", []))
        mtype = params.get("memory_type", "semantic")
        if HAVE_SUPERMEMORY and _MemoryEntry and _MemoryType:
            import asyncio

            entry = _MemoryEntry(
                topic=topic,
                content=content,
                source=source,
                tags=tags,
                memory_type=_MemoryType(mtype),
            )
            result = asyncio.get_event_loop().run_until_complete(
                self.memory.add_to_memory(entry)
            )
            return {"result": result}
        else:
            result = self.memory.add_to_memory(topic, content, source, tags, mtype)
            return {"result": result}

    def memory_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "")
        limit = int(params.get("limit", 20))
        if HAVE_SUPERMEMORY:
            import asyncio

            entries = asyncio.get_event_loop().run_until_complete(
                self.memory.search_memory(query=query, limit=limit)
            )
            out = [
                {
                    "topic": e.topic,
                    "content": e.content,
                    "source": e.source,
                    "tags": e.tags,
                    "timestamp": e.timestamp.isoformat(),
                    "memory_type": e.memory_type.value,
                }
                for e in entries
            ]
        else:
            out = self.memory.search_memory(query=query, limit=limit)
        return {"results": out, "count": len(out)}

    # ---------------
    # Repo indexing
    # ---------------
    def repo_index(self, params: Dict[str, Any]) -> Dict[str, Any]:
        root = (REPO_ROOT / params.get("root", ".")).resolve()
        max_bytes = int(params.get("max_bytes_per_file", 200_000))
        if not str(root).startswith(str(REPO_ROOT)):
            raise ValueError("Path outside repository")

        count = 0
        for fp in root.rglob("*"):
            if any(part in IGNORE_DIRS for part in fp.parts):
                continue
            if not is_text_file(fp):
                continue
            try:
                rel = str(fp.relative_to(REPO_ROOT))
                with open(fp, encoding="utf-8", errors="ignore") as f:
                    text = f.read(max_bytes)
                if HAVE_SUPERMEMORY and _MemoryEntry and _MemoryType:
                    import asyncio

                    entry = _MemoryEntry(
                        topic=f"{rel}",
                        content=text,
                        source=rel,
                        tags=["repo", "index"],
                        memory_type=_MemoryType.SEMANTIC,
                    )
                    asyncio.get_event_loop().run_until_complete(
                        self.memory.add_to_memory(entry)
                    )
                else:
                    self.memory.add_to_memory(
                        topic=f"{rel}",
                        content=text,
                        source=rel,
                        tags=["repo", "index"],
                        mtype="semantic",
                    )
                count += 1
            except Exception:
                continue
        return {"indexed": count}

    # ---------------
    # Git ops
    # ---------------
    def git_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        files: List[Dict[str, Any]] = []
        for line in res.stdout.splitlines():
            if len(line) >= 3:
                status = line[:2]
                filename = line[3:]
                files.append(
                    {
                        "file": filename,
                        "staged": status[0] != " ",
                        "modified": status[1] != " ",
                        "status": status.strip(),
                    }
                )
        return {"files": files, "clean": len(files) == 0}

    def git_diff(self, params: Dict[str, Any]) -> Dict[str, Any]:
        cmd = ["git", "diff"]
        if params.get("staged"):
            cmd.append("--cached")
        if params.get("path"):
            cmd.append(str(params["path"]))
        res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        return {"diff": res.stdout}

    # ---------------
    # Dispatcher
    # ---------------
    def handle(self, req: Dict[str, Any]) -> Dict[str, Any]:
        method = req.get("method", "")
        params = req.get("params", {}) or {}

        mapping = {
            "initialize": self.initialize,
            "ping": self.ping,
            "fs.read": self.fs_read,
            "fs.write": self.fs_write,
            "fs.list": self.fs_list,
            "fs.search": self.fs_search,
            "memory.add": self.memory_add,
            "memory.search": self.memory_search,
            "repo.index": self.repo_index,
            "git.status": self.git_status,
            "git.diff": self.git_diff,
        }

        if method not in mapping:
            raise ValueError(f"Unknown method: {method}")
        return mapping[method](params)


def main() -> int:
    server = FsMemoryServer()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            rid = req.get("id")
            result = server.handle(req)
            resp = {"id": rid, "result": result}
        except Exception as e:
            resp = {"id": None, "error": str(e)}
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
