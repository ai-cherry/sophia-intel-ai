from __future__ import annotations
import httpx
from typing import List
from .provider import EmbeddingProvider


class OllamaEmbedding(EmbeddingProvider):
    def __init__(self, model: str = "nomic-embed-text", base_url: str = "http://127.0.0.1:11434"):
        self.model = model
        self.base_url = base_url
        self._dims = 768  # typical; may vary by model

    @property
    def dims(self) -> int:
        return self._dims

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        # Synchronous call for simplicity
        out: List[List[float]] = []
        for t in texts:
            r = httpx.post(f"{self.base_url}/api/embeddings", json={"model": self.model, "prompt": t}, timeout=30.0)
            data = r.json()
            vec = data.get("embedding") or [0.0] * self._dims
            out.append(vec)
        return out

