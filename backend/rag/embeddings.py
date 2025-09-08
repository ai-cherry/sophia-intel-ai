"""
Sophia AI Embedding Service
Production-ready embedding generation with caching and optimization
"""

import hashlib
import logging
import pickle
from typing import Any

from langchain_openai import OpenAIEmbeddings
from redis.asyncio import Redis

# Import Pulumi ESC configuration
from shared.core.unified_config import get_config_value

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Production embedding service with caching and batch processing"""

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=get_config_value("openai_api_key"),
        )
        self.redis = Redis.from_url(
            get_config_value("redis_url") or "redis://${REDIS_HOST}:${REDIS_PORT}",
            decode_responses=False,  # Keep binary for pickle
        )
        self.cache_ttl = 86400  # 24 hours

    async def embed_text(self, text: str, use_cache: bool = True) -> list[float]:
        """Generate embedding for a single text with caching"""

        if use_cache:
            # Check cache first
            cache_key = self._generate_cache_key(text)
            cached_embedding = await self._get_cached_embedding(cache_key)
            if cached_embedding:
                return cached_embedding

        try:
            # Generate embedding
            embedding = await self.embeddings.aembed_query(text)

            # Cache the result
            if use_cache:
                await self._cache_embedding(cache_key, embedding)

            return embedding

        except Exception as e:
            logger.error(f"Embedding generation failed for text: {text[:50]}... Error: {e}")
            raise

    async def embed_documents(self, texts: list[str], use_cache: bool = True) -> list[list[float]]:
        """Generate embeddings for multiple texts with batch optimization"""

        if not texts:
            return []

        # Check cache for each text
        cached_embeddings = {}
        uncached_texts = []

        if use_cache:
            for i, text in enumerate(texts):
                cache_key = self._generate_cache_key(text)
                cached_embedding = await self._get_cached_embedding(cache_key)
                if cached_embedding:
                    cached_embeddings[i] = cached_embedding
                else:
                    uncached_texts.append((i, text))
        else:
            uncached_texts = [(i, text) for i, text in enumerate(texts)]

        # Generate embeddings for uncached texts
        new_embeddings = {}
        if uncached_texts:
            try:
                # Batch generate embeddings
                texts_to_embed = [text for _, text in uncached_texts]
                embeddings_list = await self.embeddings.aembed_documents(texts_to_embed)

                # Store new embeddings
                for (i, text), embedding in zip(uncached_texts, embeddings_list, strict=False):
                    new_embeddings[i] = embedding

                    # Cache the new embedding
                    if use_cache:
                        cache_key = self._generate_cache_key(text)
                        await self._cache_embedding(cache_key, embedding)

            except Exception as e:
                logger.error(f"Batch embedding generation failed: {e}")
                raise

        # Combine cached and new embeddings in correct order
        result = []
        for i in range(len(texts)):
            if i in cached_embeddings:
                result.append(cached_embeddings[i])
            elif i in new_embeddings:
                result.append(new_embeddings[i])
            else:
                # This shouldn't happen, but handle gracefully
                logger.warning(f"Missing embedding for text at index {i}")
                result.append([0.0] * 1536)  # Default embedding size

        return result

    def _generate_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        # Create deterministic hash of text content
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return f"embedding:text-embedding-3-small:{text_hash}"

    async def _get_cached_embedding(self, cache_key: str) -> list[float] | None:
        """Retrieve cached embedding"""
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                return pickle.loads(cached_data)
            return None
        except Exception as e:
            logger.warning(f"Cache retrieval failed for key {cache_key}: {e}")
            return None

    async def _cache_embedding(self, cache_key: str, embedding: list[float]):
        """Cache embedding with TTL"""
        try:
            await self.redis.set(cache_key, pickle.dumps(embedding), ex=self.cache_ttl)
        except Exception as e:
            logger.warning(f"Cache storage failed for key {cache_key}: {e}")

    async def clear_cache(self, pattern: str = "embedding:*"):
        """Clear embedding cache with optional pattern"""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Cleared {len(keys)} cached embeddings")
        except Exception as e:
            logger.error(f"Cache clearing failed: {e}")

    async def get_cache_stats(self) -> dict[str, Any]:
        """Get cache performance statistics"""
        try:
            keys = await self.redis.keys("embedding:*")
            memory_usage = await self.redis.memory_usage("embedding:*") if keys else 0

            return {
                "cached_embeddings": len(keys),
                "memory_usage_bytes": memory_usage,
                "cache_ttl_seconds": self.cache_ttl,
            }
        except Exception as e:
            logger.error(f"Cache stats retrieval failed: {e}")
            return {
                "cached_embeddings": 0,
                "memory_usage_bytes": 0,
                "cache_ttl_seconds": self.cache_ttl,
            }
