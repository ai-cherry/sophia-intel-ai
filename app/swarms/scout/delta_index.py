from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from app.mcp.clients.stdio_client import StdioMCPClient
from app.memory.unified_memory_router import DocChunk, MemoryDomain, get_memory_router

CACHE_PATH = Path("tmp/scout_index_cache.json")


def _load_cache() -> Dict[str, int]:
    try:
        if CACHE_PATH.exists():
            return json.loads(CACHE_PATH.read_text())
    except Exception:
        pass
    return {}


def _save_cache(cache: Dict[str, int]) -> None:
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(cache, indent=2))
    except Exception:
        pass


async def delta_index(
    repo_root: str = ".", max_total_bytes: int = 500_000, max_bytes_per_file: int = 50_000
) -> dict[str, Any]:
    """Index changed/new files since last run using a simple size-based cache.

    - Uses stdio MCP repo.index to get (path, bytes)
    - Compares against last cache of sizes; indexes new/changed files only
    - Upserts DocChunks to memory router (Weaviate if present)
    - Feature flag: SCOUT_DELTA_INDEX_ENABLED
    """
    if os.getenv("SCOUT_DELTA_INDEX_ENABLED", "true").lower() in {"0", "false", "no"}:
        return {"ok": True, "skipped": True, "reason": "SCOUT_DELTA_INDEX_ENABLED=false"}

    client = StdioMCPClient(Path.cwd())
    router = get_memory_router()

    listing = await asyncio.to_thread(
        client.repo_index, root=repo_root, max_bytes_per_file=max_bytes_per_file
    )
    prev = _load_cache()
    candidates: List[Dict[str, Any]] = []
    total = 0
    for it in (listing.get("files") if isinstance(listing, dict) else []) or []:
        p = it.get("path")
        size = int(it.get("bytes", 0)) if isinstance(it, dict) else 0
        if not p or size <= 0:
            continue
        if "/node_modules/" in p or any(
            p.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".pdf")
        ):
            continue
        # consider code/docs only
        if not p.endswith((".py", ".md", ".ts", ".tsx")):
            continue
        if prev.get(p) != size:
            candidates.append({"path": p, "bytes": size})
            total += min(size, max_bytes_per_file)
            if total >= max_total_bytes:
                break

    chunks: List[DocChunk] = []
    new_cache = {k: v for k, v in prev.items()}
    for c in candidates:
        p = c["path"]
        try:
            fr = await asyncio.to_thread(client.fs_read, p, max_bytes=max_bytes_per_file)
            content = fr.get("content", "") if isinstance(fr, dict) else str(fr)
            if not content:
                continue
            chunks.append(
                DocChunk(
                    content=content[:max_bytes_per_file],
                    source_uri=f"file://{p}",
                    domain=MemoryDomain.ARTEMIS,
                    metadata={"delta_index": True, "path": p},
                    confidence=0.9,
                )
            )
            new_cache[p] = c["bytes"]
        except Exception:
            continue

    try:
        rep = await router.upsert_chunks(chunks, MemoryDomain.ARTEMIS)
        _save_cache(new_cache)
        return {
            "ok": True,
            "upserted": rep.chunks_stored,
            "processed": rep.chunks_processed,
            "candidates": len(candidates),
        }
    except Exception as e:
        # Save cache anyway so we don't re-process endlessly
        _save_cache(new_cache)
        return {"ok": False, "error": str(e), "candidates": len(candidates)}
