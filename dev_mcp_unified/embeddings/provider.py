from __future__ import annotations
from typing import List


class EmbeddingProvider:
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    @property
    def dims(self) -> int:
        raise NotImplementedError

