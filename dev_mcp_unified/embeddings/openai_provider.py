from __future__ import annotations
import os
from typing import List
from .provider import EmbeddingProvider


class OpenAIEmbedding(EmbeddingProvider):
    """
    Thin wrapper. Implementation placeholder to avoid network in sandbox.
    When enabled, call OpenAI embeddings API with model in env EMBEDDING_MODEL or default.
    """

    def __init__(self, api_key: str | None, model: str = "text-embedding-3-small", dims: int = 1536):
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._model = os.getenv("EMBEDDING_MODEL", model)
        self._dims = int(os.getenv("EMBEDDING_DIMS", str(dims)))

    @property
    def dims(self) -> int:
        return self._dims

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        # Stub fallback: return zero vectors if no api key; real call enabled by developer later.
        if not self._api_key:
            return [[0.0] * self._dims for _ in texts]
        # Real call is intentionally omitted in this scaffold to avoid leaking keys during setup.
        # Replace this with OpenAI client usage as needed.
        return [[0.0] * self._dims for _ in texts]

