"""
Unified Embedding Coordinator

Provides a single entry point for generating embeddings with strategy selection:
- performance: fast, frequent use (Tier B)
- accuracy: high-accuracy, long-context (Tier A)
- hybrid: combine providers for improved robustness
- auto: per-text model selection based on content length/language/priority

Backed by the existing embed_router (Portkey Virtual Keys) with SQLite cache.
"""

from __future__ import annotations

import logging
import math
import os
from datetime import datetime
from typing import Any, Optional, Union

from app.core.circuit_breaker import with_circuit_breaker

# Reuse existing dual-tier router and cache
from app.memory.embed_router import (
    DIM_A,
    DIM_B,
    MODEL_A,
    MODEL_B,
    choose_model_for_chunk,
    embed_with_cache,
)

logger = logging.getLogger(__name__)


def _l2_normalize(vec: list[float]) -> list[float]:
    """L2-normalize a vector to unit length to stabilize ensemble combination."""
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0.0:
        return vec
    return [v / norm for v in vec]


def _average_vectors(a: list[float], b: list[float]) -> list[float]:
    """Average two vectors (assumes same dimension)."""
    if len(a) != len(b):
        # Pad the smaller to the larger with zeros
        if len(a) < len(b):
            a = a + [0.0] * (len(b) - len(a))
        else:
            b = b + [0.0] * (len(a) - len(b))
    return [(x + y) / 2.0 for x, y in zip(a, b, strict=False)]


class UnifiedEmbeddingCoordinator:
    """
    Unified embedding coordinator that routes requests to the appropriate provider/model
    using the existing embed_router & cache, and supports multiple strategies.
    """

    def __init__(self):
        # Strategy defaults can be overridden via environment
        self.default_strategy = os.getenv("EMBEDDING_STRATEGY_DEFAULT", "auto").lower()
        self.strategies = ["performance", "accuracy", "hybrid", "auto"]

    def _batch_by_model(
        self, texts: list[str], langs: list[Optional[str]] | None = None, priorities: list[Optional[str]] | None = None
    ) -> dict[str, list[tuple[int, str]]]:
        """
        Partition texts into batches by the selected model using choose_model_for_chunk.
        Returns dict[model_name] = list of (index, text).
        """
        batches: dict[str, list[tuple[int, str]]] = {}
        for i, text in enumerate(texts):
            lang = (langs[i] if langs and i < len(langs) else None)
            pri = (priorities[i] if priorities and i < len(priorities) else None)
            model, _dim = choose_model_for_chunk(text, lang=lang, priority=pri)
            batches.setdefault(model, []).append((i, text))
        return batches

    def _embed_model(self, model: str, batch: list[str]) -> list[list[float]]:
        """Embed a batch of texts using a specific model with caching."""
        return embed_with_cache(batch, model=model)

    def _combine_hybrid(self, texts: list[str]) -> list[list[float]]:
        """
        Hybrid: compute both Tier A and Tier B, normalize, then average.
        """
        v_a = embed_with_cache(texts, model=MODEL_A)
        v_b = embed_with_cache(texts, model=MODEL_B)
        out: list[list[float]] = []
        for a_vec, b_vec in zip(v_a, v_b, strict=False):
            a_norm = _l2_normalize(a_vec)
            b_norm = _l2_normalize(b_vec)
            out.append(_average_vectors(a_norm, b_norm))
        return out

    @with_circuit_breaker("llm")
    def generate_embeddings(
        self,
        texts: list[str],
        strategy: Optional[str] = None,
        langs: list[Optional[str]] | None = None,
        priorities: list[Optional[str]] | None = None,
    ) -> dict[str, Any]:
        """
        Generate embeddings with a selected strategy.

        Args:
            texts: list of input strings
            strategy: "performance" | "accuracy" | "hybrid" | "auto" (default)
            langs: optional per-text language hint
            priorities: optional per-text priority hint

        Returns:
            {
              "embeddings": List[List[float]],
              "dimension": int,
              "strategy_used": str,
              "provider_models": Dict[index, model_name],
              "timestamp": iso_str
            }
        """
        if not texts:
            return {
                "embeddings": [],
                "dimension": 0,
                "strategy_used": strategy or self.default_strategy,
                "provider_models": {},
                "timestamp": datetime.now().isoformat(),
            }

        use_strategy = (strategy or self.default_strategy).lower()
        provider_models: dict[int, str] = {}

        if use_strategy == "performance":
            # Tier B only
            embs = self._embed_model(MODEL_B, texts)
            for i in range(len(texts)):
                provider_models[i] = MODEL_B
            return {
                "embeddings": embs,
                "dimension": DIM_B,
                "strategy_used": "performance",
                "provider_models": provider_models,
                "timestamp": datetime.now().isoformat(),
            }

        if use_strategy == "accuracy":
            # Tier A only
            embs = self._embed_model(MODEL_A, texts)
            for i in range(len(texts)):
                provider_models[i] = MODEL_A
            return {
                "embeddings": embs,
                "dimension": DIM_A,
                "strategy_used": "accuracy",
                "provider_models": provider_models,
                "timestamp": datetime.now().isoformat(),
            }

        if use_strategy == "hybrid":
            # Ensemble both
            embs = self._combine_hybrid(texts)
            # Hybrid dimension is max of both
            for i in range(len(texts)):
                provider_models[i] = f"{MODEL_A}+{MODEL_B}"
            return {
                "embeddings": embs,
                "dimension": max(DIM_A, DIM_B),
                "strategy_used": "hybrid",
                "provider_models": provider_models,
                "timestamp": datetime.now().isoformat(),
            }

        # Default: auto (per-text model selection)
        batches = self._batch_by_model(texts, langs=langs, priorities=priorities)
        # Prepare output buffer
        outputs: Optional[list[list[float]]] = [None] * len(texts)

        for model, pairs in batches.items():
            idxs = [i for i, _t in pairs]
            chunk_texts = [t for _i, t in pairs]
            vecs = self._embed_model(model, chunk_texts)
            for local_i, vec in enumerate(vecs):
                idx = idxs[local_i]
                outputs[idx] = vec
                provider_models[idx] = model

        # Fill any remaining Nones with zeros (shouldn't happen, but safe)
        filled = [v if v is not None else [0.0] * (DIM_B) for v in outputs]

        # Determine final dimension (prefer most common)
        dims = [len(v) for v in filled if v]
        final_dim = max(dims) if dims else DIM_B

        return {
            "embeddings": filled,
            "dimension": final_dim,
            "strategy_used": "auto",
            "provider_models": provider_models,
            "timestamp": datetime.now().isoformat(),
        }


# Singleton accessor
_coordinator_singleton: Optional[UnifiedEmbeddingCoordinator] = None


def get_embedding_coordinator() -> UnifiedEmbeddingCoordinator:
    global _coordinator_singleton
    if _coordinator_singleton is None:
        _coordinator_singleton = UnifiedEmbeddingCoordinator()
    return _coordinator_singleton
