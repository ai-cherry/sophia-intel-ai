from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Dict, List
from dev_mcp_unified.embeddings.provider import EmbeddingProvider
from dev_mcp_unified.storage.vector_store import VectorStore
from .chunker import iter_files, simple_chunks


def content_hash(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def index_path(root: str, embedder: EmbeddingProvider, store: VectorStore, max_chars: int = 2000, overlap: int = 200) -> Dict[str, int]:
    added = 0
    for file in iter_files(root):
        try:
            text = file.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        chunks = simple_chunks(text, max_chars=max_chars, overlap=overlap)
        ids = [f"{file}:{i}" for i,_ in enumerate(chunks)]
        vecs = embedder.embed_batch(chunks)
        items = []
        for cid, chunk, vec in zip(ids, chunks, vecs):
            items.append({
                "id": cid,
                "text": chunk,
                "vector": vec,
                "path": str(file),
                "hash": content_hash(chunk),
            })
        if items:
            store.upsert(items)
            added += len(items)
    return {"added": added}

