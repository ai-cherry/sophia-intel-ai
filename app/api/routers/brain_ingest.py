"""
Brain Ingest API router

Accepts large document sets (e.g., Slack/Gong exports) and ingests with deduplication.
Avoids creating duplicates when overlapping with API-sourced data by using stable hash IDs.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/brain", tags=["brain"])


class IngestDocument(BaseModel):
    text: str = Field(..., description="Raw text content to ingest")
    metadata: dict[str, Any] | None = Field(default_factory=dict)


class IngestRequest(BaseModel):
    documents: list[IngestDocument]
    domain: str | None = Field(default="SOPHIA", description="Memory domain")
    deduplicate: bool = Field(default=True, description="Enable deduplication")


def _require_auth(request: Request):
    import os
    token = os.getenv("AUTH_TOKEN")
    enforce = os.getenv("ENFORCE_AUTH", "false").lower() in ("1", "true", "yes")
    if token or enforce:
        hdr = request.headers.get("authorization", "")
        provided = hdr.split(" ")[-1] if hdr else ""
        if not provided or (token and provided != token):
            raise HTTPException(401, "Unauthorized")


@router.post("/ingest")
async def ingest_documents(req: IngestRequest, request: Request) -> dict[str, Any]:
    """Ingest a batch of documents into Sophia memory with deduplication enabled."""
    _require_auth(request)
    if not req.documents:
        raise HTTPException(status_code=400, detail="No documents provided")
    # Enforce basic request size limit (~10MB)
    total_bytes = sum(len((d.text or "").encode("utf-8")) for d in req.documents)
    if total_bytes > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Ingest payload too large (limit 10MB)")

    # Defer to the unified memory store which supports deduplication
    try:
        from app.memory.supermemory_mcp import SuperMemoryStore, MemoryEntry
        from app.memory.domains import MemoryDomain

        store = SuperMemoryStore()
        entries = []
        for doc in req.documents:
            meta = doc.metadata or {}
            entries.append(
                MemoryEntry(
                    text=doc.text,
                    metadata=meta,
                )
            )
        # Domain selection
        domain = getattr(MemoryDomain, (req.domain or "SOPHIA").upper(), MemoryDomain.SOPHIA)
        stored = 0
        duplicates = 0
        for entry in entries:
            result = await store.add(entry, deduplicate=req.deduplicate)
            if result and result.get("status") == "duplicate":
                duplicates += 1
            else:
                stored += 1
        # Optional vector indexing (Weaviate)
        indexed = 0
        try:
            import weaviate
            import hashlib
            import datetime as _dt

            endpoint = os.getenv("WEAVIATE_ENDPOINT")
            api_key = os.getenv("WEAVIATE_ADMIN_API_KEY")
            if endpoint and api_key:
                client = weaviate.connect_to_weaviate_cloud(endpoint, api_key)
                try:
                    coll = client.collections.get("BusinessDocument")
                    with coll.batch.dynamic() as batch:
                        for doc in req.documents:
                            content = doc.text
                            md = doc.metadata or {}
                            uid = hashlib.sha256((content + str(sorted(md.items()))).encode()).hexdigest()
                            batch.add_object(
                                properties={
                                    "content": content,
                                    "source": md.get("source", "ingest"),
                                    "entityId": md.get("entityId", ""),
                                    "timestamp": md.get("timestamp") or _dt.datetime.utcnow().isoformat(),
                                    "metadata": md,
                                },
                                uuid=uid,
                            )
                            indexed += 1
                finally:
                    client.close()
        except Exception:
            # Indexing is optional; ignore failures here
            pass
        return {
            "stored": stored,
            "duplicates": duplicates,
            "total": len(entries),
            "indexed": indexed,
        }
    except Exception as e:  # noqa: BLE001
        # Keep this endpoint resilient; return a clear error message
        raise HTTPException(status_code=500, detail=f"Ingest failed: {e}")
