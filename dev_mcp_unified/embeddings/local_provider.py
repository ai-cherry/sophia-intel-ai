from __future__ import annotations
import hashlib
import struct
from typing import List
from .provider import EmbeddingProvider


class LocalDeterministicEmbedding(EmbeddingProvider):
    """
    Simple deterministic embedding based on hashing. Not semantically meaningful,
    but allows vector store plumbing and testing offline without network.
    """

    def __init__(self, dims: int = 256):
        self._dims = dims

    @property
    def dims(self) -> int:
        return self._dims

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        out: List[List[float]] = []
        for t in texts:
            vec = [0.0] * self._dims
            # rolling hash into buckets
            for token in t.split():
                h = hashlib.sha256(token.encode('utf-8')).digest()
                # take first 4 bytes as uint for index, next 4 bytes for value
                idx = struct.unpack('>I', h[:4])[0] % self._dims
                val_raw = struct.unpack('>I', h[4:8])[0]
                val = (val_raw / 2**32) * 2 - 1  # [-1,1]
                vec[idx] += val
            out.append(vec)
        return out

