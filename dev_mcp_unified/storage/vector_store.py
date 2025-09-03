from __future__ import annotations
from typing import Any, Dict, List, Optional
from pathlib import Path


class VectorStore:
    def upsert(self, items: List[Dict[str, Any]]):
        raise NotImplementedError

    def query(self, query_vec: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        raise NotImplementedError


class InMemoryVectorStore(VectorStore):
    def __init__(self, dims: int):
        self._dims = dims
        self._vecs: List[List[float]] = []
        self._meta: List[Dict[str, Any]] = []

    def upsert(self, items: List[Dict[str, Any]]):
        for it in items:
            self._vecs.append(it["vector"])  # type: ignore
            self._meta.append({k: v for k, v in it.items() if k != "vector"})

    def query(self, query_vec: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        # cosine similarity
        import math
        def dot(a,b):
            return sum(x*y for x,y in zip(a,b))
        def norm(a):
            return math.sqrt(sum(x*x for x in a))
        qn = norm(query_vec) or 1.0
        scored = []
        for v, m in zip(self._vecs, self._meta):
            sim = dot(v, query_vec) / (norm(v) or 1.0) / qn
            scored.append((sim, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"score": s, **m} for s, m in scored[:top_k]]


class ChromaVectorStore(VectorStore):
    def __init__(self, dims: int, persist_dir: Optional[str] = None):
        try:
            import chromadb  # type: ignore
            from chromadb.config import Settings  # type: ignore
        except Exception as e:
            raise RuntimeError("chromadb not installed: pip install chromadb") from e
        self._dims = dims
        self._persist = persist_dir or str(Path.home() / ".mcp_chroma")
        self._client = chromadb.Client(Settings(is_persistent=True, persist_directory=self._persist))
        self._col = self._client.get_or_create_collection(name="mcp_index")

    def upsert(self, items: List[Dict[str, Any]]):
        ids = [it.get("id") or str(len(it)) for it in items]
        embeddings = [it["vector"] for it in items]
        metadatas = [{k: v for k, v in it.items() if k not in ("id","vector","text")} for it in items]
        documents = [it.get("text","") for it in items]
        self._col.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)

    def query(self, query_vec: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        res = self._col.query(query_embeddings=[query_vec], n_results=top_k)
        out: List[Dict[str, Any]] = []
        for ids, embs, metas, docs, dists in zip(
            res.get("ids", [[]]), res.get("embeddings", [[]]), res.get("metadatas", [[]]), res.get("documents", [[]]), res.get("distances", [[]])
        ):
            for i in range(len(ids)):
                out.append({
                    "id": ids[i],
                    "score": 1.0 - float(dists[i]) if i < len(dists) else 0.0,
                    "metadata": metas[i] if i < len(metas) else {},
                    "text": docs[i] if i < len(docs) else "",
                })
        return out

