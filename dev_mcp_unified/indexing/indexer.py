from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Dict, List
from dev_mcp_unified.embeddings.provider import EmbeddingProvider
from dev_mcp_unified.storage.vector_store import VectorStore
from .chunker import iter_files, simple_chunks


def content_hash(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def _file_summary(text: str) -> str:
    # crude summary: top docstring/comment lines
    lines = [l.strip() for l in text.splitlines()[:120]]
    return "\n".join(lines)


def index_path(root: str, embedder: EmbeddingProvider, store: VectorStore, max_chars: int = 2000, overlap: int = 200) -> Dict[str, int]:
    added = 0
    for file in iter_files(root):
        try:
            text = file.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        # create a summary chunk for fast recall
        summary = _file_summary(text)
        chunks = [summary] + simple_chunks(text, max_chars=max_chars, overlap=overlap)
        ids = [f"{file}:{i}" for i,_ in enumerate(chunks)]
        vecs = embedder.embed_batch(chunks)
        items = []
        for i, (cid, chunk, vec) in enumerate(zip(ids, chunks, vecs)):
            items.append({
                "id": cid,
                "text": chunk,
                "vector": vec,
                "path": str(file),
                "hash": content_hash(chunk),
                "level": "summary" if i == 0 else "chunk",
                "type": file.suffix.lower(),
            })
        if items:
            store.upsert(items)
            added += len(items)
    return {"added": added}
