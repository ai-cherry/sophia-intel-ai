#!/usr/bin/env python3
"""
Vector layer smoke test

Validates Weaviate adapter and UnifiedMemoryRouter L2 behavior:
 - Upsert a simple DocChunk via router (embeds + vector upsert)
 - Search back the inserted content

Requires:
 - WEAVIATE_URL (local or cloud) and optional WEAVIATE_API_KEY
 - Portkey embeddings configured in the environment used by the router
"""
import asyncio
import os
import sys
from datetime import datetime


async def main():
    try:
        from app.memory.unified_memory_router import (
            DocChunk,
            MemoryDomain,
            get_memory_router,
        )
    except Exception as e:
        print(f"Import error: {e}")
        sys.exit(1)

    router = get_memory_router()
    text = f"smoke test vector {datetime.utcnow().isoformat()}"
    chunk = DocChunk(
        content=text,
        source_uri="smoke://vector#1",
        domain=MemoryDomain.SHARED,
        metadata={"title": "smoke", "repo_path": "/tmp"},
    )

    print("Upserting chunk via router (will embed + L2 upsert if available)...")
    rep = await router.upsert_chunks([chunk], MemoryDomain.SHARED)
    print(f"Upsert success: {rep.success}, stored: {rep.chunks_stored}, errors: {rep.errors}")

    print("Searching for the chunk...")
    hits = await router.search(text, domain=MemoryDomain.SHARED, k=3)
    for h in hits:
        print({"score": h.score, "source": h.source_uri})
    if not hits:
        print("No hits found (L2 may be unavailable or embeddings misconfigured)")


if __name__ == "__main__":
    asyncio.run(main())

