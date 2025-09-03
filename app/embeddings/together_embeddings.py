"""
Together AI Embeddings via Portkey Gateway
Production-ready embedding service with caching, fallbacks, and observability.
"""

import asyncio
import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

import numpy as np
from openai import OpenAI

logger = logging.getLogger(__name__)


class EmbeddingModel(Enum):
    """Available Together AI embedding models."""
    # Long-context models
    M2_BERT_32K = "togethercomputer/m2-bert-80M-32k-retrieval"  # 32K tokens, best for long docs
    M2_BERT_8K = "togethercomputer/m2-bert-80M-8k-retrieval"    # 8K tokens, balanced
    M2_BERT_2K = "togethercomputer/m2-bert-80M-2k-retrieval"    # 2K tokens, fast

    # General purpose
    BGE_LARGE = "BAAI/bge-large-en-v1.5"      # 512 tokens, high quality
    BGE_BASE = "BAAI/bge-base-en-v1.5"        # 512 tokens, fast

    # Specialized
    UAE_LARGE = "WhereIsAI/UAE-Large-V1"      # 512 tokens, maximum accuracy
    GTE_MODERNBERT = "Alibaba-NLP/gte-modernbert-base"  # 8192 tokens, modern architecture
    E5_MULTILINGUAL = "intfloat/multilingual-e5-large-instruct"  # 514 tokens, 100+ languages


@dataclass
class EmbeddingConfig:
    """Configuration for embedding service."""
    # API Keys
    portkey_api_key: str = field(default_factory=lambda: os.getenv("PORTKEY_API_KEY", ""))
    together_api_key: str = field(default_factory=lambda: os.getenv("TOGETHER_API_KEY", ""))
    virtual_key: Optional[str] = field(default_factory=lambda: os.getenv("PORTKEY_TOGETHER_VK", "together-ai-670469"))

    # Model selection
    primary_model: EmbeddingModel = EmbeddingModel.M2_BERT_8K
    fallback_models: list[EmbeddingModel] = field(default_factory=lambda: [
        EmbeddingModel.BGE_LARGE,
        EmbeddingModel.BGE_BASE
    ])

    # Cache settings
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour
    similarity_threshold: float = 0.95

    # Batch settings
    batch_size: int = 32
    max_retries: int = 3
    timeout_seconds: int = 30

    # Gateway settings
    use_portkey: bool = True
    portkey_base_url: str = "https://api.portkey.ai/v1"
    together_base_url: str = "https://api.together.xyz/v1"


@dataclass
class EmbeddingResult:
    """Result from embedding operation."""
    embeddings: list[list[float]]
    model: str
    dimensions: int
    tokens_used: int
    latency_ms: float
    cached: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class TogetherEmbeddingService:
    """
    Production-ready embedding service using Together AI via Portkey.
    Features semantic caching, automatic fallbacks, and batch processing.
    """

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        self._cache: dict[str, tuple[list[float], datetime]] = {}
        self._setup_clients()

    def _setup_clients(self):
        """Initialize Portkey and direct Together clients."""
        if self.config.use_portkey and self.config.portkey_api_key:
            # Portkey gateway client with virtual key
            self.portkey_client = OpenAI(
                api_key="dummy-key",  # Virtual key is passed in headers
                base_url=self.config.portkey_base_url,
                default_headers={
                    "x-portkey-api-key": self.config.portkey_api_key,
                    "x-portkey-virtual-key": self.config.virtual_key or "together-ai-670469",
                    "x-portkey-provider": "together-ai",
                    "x-portkey-config": json.dumps(self._get_portkey_config())
                }
            )
            self.primary_client = self.portkey_client
            logger.info(f"Initialized Portkey gateway for Together AI embeddings (VK: {self.config.virtual_key})")
        else:
            # Direct Together AI client
            self.together_client = OpenAI(
                api_key=self.config.together_api_key,
                base_url=self.config.together_base_url
            )
            self.primary_client = self.together_client
            logger.info("Initialized direct Together AI client for embeddings")

    def _get_portkey_config(self) -> dict[str, Any]:
        """Generate Portkey gateway configuration."""
        return {
            "cache": {
                "enabled": self.config.cache_enabled,
                "ttl": self.config.cache_ttl_seconds,
                "mode": "semantic",
                "similarity_threshold": self.config.similarity_threshold
            },
            "retry": {
                "attempts": self.config.max_retries,
                "on_status_codes": [429, 500, 502, 503],
                "exponential_backoff": True
            },
            "strategy": {
                "mode": "fallback",
                "targets": [
                    {
                        "provider": "together-ai",
                        "model": self.config.primary_model.value,
                        "weight": 1.0
                    }
                ] + [
                    {
                        "provider": "together-ai",
                        "model": model.value,
                        "weight": 0.8 - i * 0.1
                    }
                    for i, model in enumerate(self.config.fallback_models)
                ]
            }
        }

    def _get_cache_key(self, text: str, model: str) -> str:
        """Generate cache key for text and model."""
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _check_cache(self, texts: list[str], model: str) -> tuple[list[list[float]], list[int]]:
        """Check cache for embeddings. Returns cached embeddings and indices of cache misses."""
        if not self.config.cache_enabled:
            return [], list(range(len(texts)))

        cached_embeddings = []
        miss_indices = []
        now = datetime.now()

        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text, model)

            if cache_key in self._cache:
                embedding, timestamp = self._cache[cache_key]
                if now - timestamp < timedelta(seconds=self.config.cache_ttl_seconds):
                    cached_embeddings.append(embedding)
                else:
                    # Expired
                    del self._cache[cache_key]
                    miss_indices.append(i)
            else:
                miss_indices.append(i)

        return cached_embeddings, miss_indices

    def _update_cache(self, texts: list[str], embeddings: list[list[float]], model: str):
        """Update cache with new embeddings."""
        if not self.config.cache_enabled:
            return

        now = datetime.now()
        for text, embedding in zip(texts, embeddings, strict=False):
            cache_key = self._get_cache_key(text, model)
            self._cache[cache_key] = (embedding, now)

    async def embed_async(
        self,
        texts: list[str],
        model: Optional[EmbeddingModel] = None,
        use_cache: bool = True
    ) -> EmbeddingResult:
        """
        Asynchronously generate embeddings for texts.
        
        Args:
            texts: List of texts to embed
            model: Embedding model to use (defaults to primary)
            use_cache: Whether to use cache
            
        Returns:
            EmbeddingResult with embeddings and metadata
        """
        import time
        start_time = time.time()

        model = model or self.config.primary_model
        model_name = model.value

        # Check cache
        if use_cache:
            cached_embeddings, miss_indices = self._check_cache(texts, model_name)

            if not miss_indices:
                # All cached
                return EmbeddingResult(
                    embeddings=cached_embeddings,
                    model=model_name,
                    dimensions=len(cached_embeddings[0]),
                    tokens_used=0,
                    latency_ms=0,
                    cached=True
                )

            # Get texts that need embedding
            texts_to_embed = [texts[i] for i in miss_indices]
        else:
            texts_to_embed = texts
            cached_embeddings = []
            miss_indices = list(range(len(texts)))

        # Batch processing
        all_new_embeddings = []
        for i in range(0, len(texts_to_embed), self.config.batch_size):
            batch = texts_to_embed[i:i + self.config.batch_size]

            # Try primary and fallback models
            last_error = None
            for attempt_model in [model] + self.config.fallback_models:
                try:
                    response = await asyncio.to_thread(
                        self.primary_client.embeddings.create,
                        model=attempt_model.value,
                        input=batch
                    )

                    batch_embeddings = [e.embedding for e in response.data]
                    all_new_embeddings.extend(batch_embeddings)

                    # Update cache
                    self._update_cache(batch, batch_embeddings, attempt_model.value)

                    # Use this model for remaining batches
                    model_name = attempt_model.value
                    break

                except Exception as e:
                    logger.warning(f"Model {attempt_model.value} failed: {e}")
                    last_error = e
                    continue
            else:
                # All models failed
                raise last_error or Exception("All embedding models failed")

        # Combine cached and new embeddings in correct order
        final_embeddings = []
        cached_idx = 0
        new_idx = 0

        for i in range(len(texts)):
            if i in miss_indices:
                final_embeddings.append(all_new_embeddings[new_idx])
                new_idx += 1
            else:
                final_embeddings.append(cached_embeddings[cached_idx])
                cached_idx += 1

        latency_ms = (time.time() - start_time) * 1000

        return EmbeddingResult(
            embeddings=final_embeddings,
            model=model_name,
            dimensions=len(final_embeddings[0]),
            tokens_used=sum(len(text.split()) for text in texts_to_embed),
            latency_ms=latency_ms,
            cached=len(cached_embeddings) > 0,
            metadata={
                "cache_hits": len(cached_embeddings),
                "cache_misses": len(miss_indices),
                "batch_size": self.config.batch_size
            }
        )

    def embed(
        self,
        texts: list[str],
        model: Optional[EmbeddingModel] = None,
        use_cache: bool = True
    ) -> EmbeddingResult:
        """
        Synchronous wrapper for embed_async.
        """
        return asyncio.run(self.embed_async(texts, model, use_cache))

    def similarity(self, embedding1: list[float], embedding2: list[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    def search(
        self,
        query: str,
        documents: list[str],
        top_k: int = 5,
        model: Optional[EmbeddingModel] = None
    ) -> list[tuple[int, float, str]]:
        """
        Search documents using semantic similarity.
        
        Returns:
            List of (index, similarity_score, document) tuples
        """
        # Embed query and documents
        query_result = self.embed([query], model)
        docs_result = self.embed(documents, model)

        query_embedding = query_result.embeddings[0]

        # Calculate similarities
        similarities = []
        for i, doc_embedding in enumerate(docs_result.embeddings):
            sim = self.similarity(query_embedding, doc_embedding)
            similarities.append((i, sim, documents[i]))

        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    @staticmethod
    def recommend_model(
        text_length: int,
        use_case: str = "general",
        language: str = "en"
    ) -> EmbeddingModel:
        """
        Recommend best model based on text characteristics.
        
        Args:
            text_length: Approximate token count
            use_case: One of 'rag', 'search', 'clustering', 'classification'
            language: Language code (e.g., 'en', 'zh', 'multi')
            
        Returns:
            Recommended EmbeddingModel
        """
        # Multilingual
        if language != "en" or language == "multi":
            return EmbeddingModel.E5_MULTILINGUAL

        # Long documents
        if text_length > 8192:
            return EmbeddingModel.M2_BERT_32K
        elif text_length > 2048:
            return EmbeddingModel.M2_BERT_8K

        # Use case specific
        if use_case == "rag":
            return EmbeddingModel.M2_BERT_8K
        elif use_case == "search":
            return EmbeddingModel.BGE_LARGE
        elif use_case == "clustering":
            return EmbeddingModel.UAE_LARGE
        elif use_case == "classification":
            return EmbeddingModel.GTE_MODERNBERT

        # Default
        return EmbeddingModel.BGE_BASE


# Global singleton instance
_embedding_service: Optional[TogetherEmbeddingService] = None


def get_embedding_service(config: Optional[EmbeddingConfig] = None) -> TogetherEmbeddingService:
    """Get or create global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = TogetherEmbeddingService(config)
    return _embedding_service
