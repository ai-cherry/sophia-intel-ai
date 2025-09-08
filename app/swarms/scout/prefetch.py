from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, List

from app.mcp.clients.stdio_client import StdioMCPClient
from app.memory.unified_memory_router import DocChunk, MemoryDomain, get_memory_router


async def prefetch_and_index(
    repo_root: str = ".", max_files: int = 50, max_bytes_per_file: int = 20000
) -> dict[str, Any]:
    """Prefetch a small sample of repository files and index into memory.

    - Uses stdio MCP to list/read files (bounded)
    - Generates lightweight DocChunks and upserts to L2 (Weaviate) if available
    - Falls back to storing a brief summary in L1 if vectors unavailable
    """
    if os.getenv("SCOUT_PREFETCH_ENABLED", "true").lower() in {"0", "false", "no"}:
        return {"ok": True, "skipped": True, "reason": "SCOUT_PREFETCH_ENABLED=false"}

    try:
        max_files = int(os.getenv("SCOUT_PREFETCH_MAX_FILES", str(max_files)))
    except Exception:
        pass
    try:
        max_bytes_per_file = int(os.getenv("SCOUT_PREFETCH_MAX_BYTES", str(max_bytes_per_file)))
    except Exception:
        pass

    client = StdioMCPClient(Path.cwd())
    router = get_memory_router()

    listing = await asyncio.to_thread(
        client.repo_index, root=repo_root, max_bytes_per_file=max_bytes_per_file
    )
    files: List[str] = []
    for it in (listing.get("files") if isinstance(listing, dict) else []) or []:
        p = it.get("path")
        if not p:
            continue
        if "/node_modules/" in p or any(
            p.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".pdf")
        ):
            continue
        if p.endswith((".py", ".md", ".ts", ".tsx")):
            files.append(p)
        if len(files) >= max_files:
            break

    chunks: List[DocChunk] = []
    for p in files:
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
                    metadata={"prefetch": True, "path": p},
                    confidence=0.9,
                )
            )
        except Exception:
            continue

    try:
        report = await router.upsert_chunks(chunks, MemoryDomain.ARTEMIS)
        return {
            "ok": True,
            "upserted": report.chunks_stored,
            "processed": report.chunks_processed,
            "files_considered": len(files),
        }
    except Exception as e:
        try:
            client.memory_add(
                topic="scout_prefetch_summary",
                content=f"Prefetched {len(chunks)} files for context.",
                source="artemis-run",
                tags=["scout", "prefetch", "fallback"],
                memory_type="semantic",
            )
        except Exception:
            pass
        return {"ok": False, "error": str(e), "fallback": True, "files": len(chunks)}
