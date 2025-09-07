"""
Multi-Modal Embedding Generation System

Generates and manages embeddings for code, documentation, semantic content, and usage patterns.
Supports multiple embedding providers through Portkey with intelligent caching and batch processing.
"""

import asyncio
import hashlib
import logging
import pickle
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import numpy as np

from app.core.portkey_manager import get_portkey_manager

logger = logging.getLogger(__name__)


class EmbeddingType(Enum):
    """Types of embeddings supported"""

    CODE = "code"
    DOCUMENTATION = "documentation"
    SEMANTIC = "semantic"
    USAGE = "usage"
    CONTEXTUAL = "contextual"


class HierarchyLevel(Enum):
    """Hierarchy levels for indexing"""

    FILE = "file"
    CLASS = "class"
    METHOD = "method"
    BLOCK = "block"


@dataclass
class EmbeddingMetadata:
    """Metadata for an embedding"""

    content_hash: str
    embedding_type: EmbeddingType
    hierarchy_level: HierarchyLevel
    file_path: str
    class_name: Optional[str] = None
    method_name: Optional[str] = None
    block_id: Optional[str] = None
    language: Optional[str] = None
    tokens: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    provider: str = "openai"
    model: str = "text-embedding-ada-002"
    extra_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CachedEmbedding:
    """Cached embedding with metadata"""

    vector: np.ndarray
    metadata: EmbeddingMetadata
    cache_key: str
    expires_at: datetime


class EmbeddingCache:
    """High-performance embedding cache with TTL support"""

    def __init__(self, cache_dir: Path, default_ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl_hours = default_ttl_hours
        self._memory_cache: dict[str, CachedEmbedding] = {}
        self._load_persistent_cache()

    def _load_persistent_cache(self):
        """Load cache from disk"""
        cache_file = self.cache_dir / "embedding_cache.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    self._memory_cache = pickle.load(f)
                logger.info(f"Loaded {len(self._memory_cache)} cached embeddings")
                self._cleanup_expired()
            except Exception as e:
                logger.warning(f"Failed to load embedding cache: {e}")
                self._memory_cache = {}

    def _save_persistent_cache(self):
        """Save cache to disk"""
        cache_file = self.cache_dir / "embedding_cache.pkl"
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(self._memory_cache, f)
        except Exception as e:
            logger.error(f"Failed to save embedding cache: {e}")

    def _cleanup_expired(self):
        """Remove expired entries"""
        now = datetime.now()
        expired_keys = [
            key for key, cached in self._memory_cache.items() if cached.expires_at < now
        ]
        for key in expired_keys:
            del self._memory_cache[key]

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

    def _generate_cache_key(
        self,
        content: str,
        embedding_type: EmbeddingType,
        provider: str = "openai",
        model: str = "text-embedding-ada-002",
    ) -> str:
        """Generate cache key from content and parameters"""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        key_data = f"{content_hash}:{embedding_type.value}:{provider}:{model}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(
        self,
        content: str,
        embedding_type: EmbeddingType,
        provider: str = "openai",
        model: str = "text-embedding-ada-002",
    ) -> Optional[CachedEmbedding]:
        """Get cached embedding"""
        cache_key = self._generate_cache_key(content, embedding_type, provider, model)
        cached = self._memory_cache.get(cache_key)

        if cached and cached.expires_at > datetime.now():
            logger.debug(f"Cache hit for {cache_key[:8]}...")
            return cached
        elif cached:
            # Expired entry
            del self._memory_cache[cache_key]
            logger.debug(f"Cache expired for {cache_key[:8]}...")

        return None

    def set(
        self,
        content: str,
        vector: np.ndarray,
        metadata: EmbeddingMetadata,
        ttl_hours: Optional[int] = None,
    ) -> str:
        """Cache embedding"""
        cache_key = self._generate_cache_key(
            content, metadata.embedding_type, metadata.provider, metadata.model
        )
        ttl = ttl_hours or self.default_ttl_hours
        expires_at = datetime.now() + timedelta(hours=ttl)

        cached = CachedEmbedding(
            vector=vector, metadata=metadata, cache_key=cache_key, expires_at=expires_at
        )

        self._memory_cache[cache_key] = cached
        logger.debug(f"Cached embedding {cache_key[:8]}...")

        # Periodic cache save
        if len(self._memory_cache) % 100 == 0:
            self._save_persistent_cache()

        return cache_key

    def clear_expired(self):
        """Clear expired entries and save"""
        self._cleanup_expired()
        self._save_persistent_cache()

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        now = datetime.now()
        active_count = sum(1 for cached in self._memory_cache.values() if cached.expires_at > now)
        expired_count = len(self._memory_cache) - active_count

        return {
            "total_entries": len(self._memory_cache),
            "active_entries": active_count,
            "expired_entries": expired_count,
            "cache_dir": str(self.cache_dir),
        }


class MultiModalEmbeddings:
    """
    Multi-modal embedding generation system with hierarchical indexing support.
    Handles code, documentation, semantic, and usage embeddings with intelligent caching.
    """

    # Provider-specific embedding configurations
    EMBEDDING_CONFIGS = {
        "openai": {
            "models": {
                "text-embedding-ada-002": {"dimensions": 1536, "max_tokens": 8192},
                "text-embedding-3-small": {"dimensions": 1536, "max_tokens": 8192},
                "text-embedding-3-large": {"dimensions": 3072, "max_tokens": 8192},
            },
            "default_model": "text-embedding-3-large",
        },
        "cohere": {
            "models": {
                "embed-english-v3.0": {"dimensions": 1024, "max_tokens": 512},
                "embed-multilingual-v3.0": {"dimensions": 1024, "max_tokens": 512},
            },
            "default_model": "embed-english-v3.0",
        },
        "huggingface": {
            "models": {
                "sentence-transformers/all-MiniLM-L6-v2": {"dimensions": 384, "max_tokens": 512},
                "sentence-transformers/all-mpnet-base-v2": {"dimensions": 768, "max_tokens": 514},
            },
            "default_model": "sentence-transformers/all-mpnet-base-v2",
        },
    }

    def __init__(
        self,
        cache_dir: str = "data/embeddings_cache",
        default_provider: str = "openai",
        batch_size: int = 50,
    ):
        """
        Initialize multi-modal embedding system

        Args:
            cache_dir: Directory for caching embeddings
            default_provider: Default embedding provider
            batch_size: Batch size for processing
        """
        self.cache_dir = Path(cache_dir)
        self.default_provider = default_provider
        self.batch_size = batch_size
        self.portkey_manager = get_portkey_manager()

        # Initialize cache
        self.cache = EmbeddingCache(self.cache_dir)

        # Provider configurations
        self.provider_configs = self.EMBEDDING_CONFIGS

        # Statistics
        self._stats = {
            "embeddings_generated": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "batch_requests": 0,
            "total_tokens": 0,
        }

    async def generate_embedding(
        self,
        content: str,
        embedding_type: EmbeddingType,
        metadata: Optional[EmbeddingMetadata] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        use_cache: bool = True,
    ) -> tuple[np.ndarray, EmbeddingMetadata]:
        """
        Generate embedding for content

        Args:
            content: Text content to embed
            embedding_type: Type of embedding
            metadata: Optional metadata
            provider: Embedding provider
            model: Specific model to use
            use_cache: Whether to use caching

        Returns:
            Tuple of (embedding_vector, metadata)
        """
        provider = provider or self.default_provider
        model = model or self.provider_configs[provider]["default_model"]

        # Check cache first
        if use_cache:
            cached = self.cache.get(content, embedding_type, provider, model)
            if cached:
                self._stats["cache_hits"] += 1
                return cached.vector, cached.metadata

        self._stats["cache_misses"] += 1

        # Generate content hash for metadata
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Create metadata if not provided
        if metadata is None:
            metadata = EmbeddingMetadata(
                content_hash=content_hash,
                embedding_type=embedding_type,
                hierarchy_level=HierarchyLevel.BLOCK,  # default
                file_path="unknown",
                tokens=len(content.split()),
                provider=provider,
                model=model,
            )
        else:
            metadata.content_hash = content_hash
            metadata.provider = provider
            metadata.model = model
            metadata.tokens = len(content.split())

        # Generate embedding
        try:
            vector = await self._call_embedding_api(content, provider, model)

            # Cache the result
            if use_cache:
                self.cache.set(content, vector, metadata)

            self._stats["embeddings_generated"] += 1
            self._stats["total_tokens"] += metadata.tokens

            logger.debug(f"Generated {embedding_type.value} embedding for {content[:50]}...")
            return vector, metadata

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    async def generate_batch_embeddings(
        self,
        contents: list[str],
        embedding_types: list[EmbeddingType],
        metadatas: Optional[list[EmbeddingMetadata]] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        use_cache: bool = True,
    ) -> list[tuple[np.ndarray, EmbeddingMetadata]]:
        """
        Generate embeddings in batches for efficiency

        Args:
            contents: List of content strings
            embedding_types: List of embedding types (same length as contents)
            metadatas: Optional list of metadata
            provider: Embedding provider
            model: Specific model
            use_cache: Whether to use caching

        Returns:
            List of (embedding_vector, metadata) tuples
        """
        if len(contents) != len(embedding_types):
            raise ValueError("Contents and embedding_types must have same length")

        if metadatas and len(metadatas) != len(contents):
            raise ValueError("If provided, metadatas must have same length as contents")

        provider = provider or self.default_provider
        model = model or self.provider_configs[provider]["default_model"]

        results = []
        uncached_items = []
        uncached_indices = []

        # Check cache for all items
        if use_cache:
            for i, (content, emb_type) in enumerate(zip(contents, embedding_types)):
                cached = self.cache.get(content, emb_type, provider, model)
                if cached:
                    results.append((cached.vector, cached.metadata))
                    self._stats["cache_hits"] += 1
                else:
                    results.append(None)  # Placeholder
                    uncached_items.append((content, emb_type, metadatas[i] if metadatas else None))
                    uncached_indices.append(i)
                    self._stats["cache_misses"] += 1
        else:
            # No cache, process all items
            for i, (content, emb_type) in enumerate(zip(contents, embedding_types)):
                uncached_items.append((content, emb_type, metadatas[i] if metadatas else None))
                uncached_indices.append(i)
                results.append(None)  # Placeholder

        # Process uncached items in batches
        if uncached_items:
            logger.info(f"Processing {len(uncached_items)} uncached embeddings in batches")

            for batch_start in range(0, len(uncached_items), self.batch_size):
                batch_end = min(batch_start + self.batch_size, len(uncached_items))
                batch_items = uncached_items[batch_start:batch_end]
                batch_indices = uncached_indices[batch_start:batch_end]

                # Generate embeddings for batch
                batch_vectors = await self._call_batch_embedding_api(
                    [item[0] for item in batch_items], provider, model
                )

                # Process batch results
                for i, ((content, emb_type, metadata), vector) in enumerate(
                    zip(batch_items, batch_vectors)
                ):
                    result_index = batch_indices[i]

                    # Create metadata if not provided
                    if metadata is None:
                        content_hash = hashlib.sha256(content.encode()).hexdigest()
                        metadata = EmbeddingMetadata(
                            content_hash=content_hash,
                            embedding_type=emb_type,
                            hierarchy_level=HierarchyLevel.BLOCK,
                            file_path="unknown",
                            tokens=len(content.split()),
                            provider=provider,
                            model=model,
                        )

                    # Cache result
                    if use_cache:
                        self.cache.set(content, vector, metadata)

                    results[result_index] = (vector, metadata)
                    self._stats["embeddings_generated"] += 1
                    self._stats["total_tokens"] += metadata.tokens

                self._stats["batch_requests"] += 1

                # Small delay between batches to respect rate limits
                if batch_end < len(uncached_items):
                    await asyncio.sleep(0.1)

        return results

    async def _call_embedding_api(self, content: str, provider: str, model: str) -> np.ndarray:
        """Call embedding API for single content"""
        try:
            client = self.portkey_manager.get_client(provider)

            response = await client.embeddings.create(
                model=model, input=content, encoding_format="float"
            )

            return np.array(response.data[0].embedding, dtype=np.float32)

        except Exception as e:
            logger.error(f"Embedding API call failed for provider {provider}: {e}")
            raise

    async def _call_batch_embedding_api(
        self, contents: list[str], provider: str, model: str
    ) -> list[np.ndarray]:
        """Call embedding API for batch of contents"""
        try:
            client = self.portkey_manager.get_client(provider)

            response = await client.embeddings.create(
                model=model, input=contents, encoding_format="float"
            )

            return [np.array(item.embedding, dtype=np.float32) for item in response.data]

        except Exception as e:
            logger.error(f"Batch embedding API call failed for provider {provider}: {e}")
            raise

    async def generate_hierarchical_embeddings(
        self, file_content: str, file_path: str, language: str = "python"
    ) -> dict[str, list[tuple[np.ndarray, EmbeddingMetadata]]]:
        """
        Generate embeddings at multiple hierarchy levels for a file

        Args:
            file_content: Full file content
            file_path: Path to the file
            language: Programming language

        Returns:
            Dictionary mapping hierarchy levels to embeddings
        """
        from .chunking_strategies import CodeChunker

        chunker = CodeChunker(language=language)
        hierarchical_chunks = chunker.create_hierarchical_chunks(file_content, file_path)

        results = {}

        for level, chunks in hierarchical_chunks.items():
            level_embeddings = []

            # Prepare batch data
            contents = [chunk.content for chunk in chunks]
            embedding_types = [EmbeddingType.CODE] * len(contents)
            metadatas = []

            for chunk in chunks:
                metadata = EmbeddingMetadata(
                    content_hash="",  # Will be set in generate_embedding
                    embedding_type=EmbeddingType.CODE,
                    hierarchy_level=HierarchyLevel(level.value),
                    file_path=file_path,
                    class_name=chunk.metadata.get("class_name"),
                    method_name=chunk.metadata.get("method_name"),
                    block_id=chunk.metadata.get("block_id"),
                    language=language,
                    extra_metadata=chunk.metadata,
                )
                metadatas.append(metadata)

            # Generate embeddings in batch
            if contents:
                level_results = await self.generate_batch_embeddings(
                    contents, embedding_types, metadatas
                )
                level_embeddings.extend(level_results)

            results[level] = level_embeddings
            logger.info(f"Generated {len(level_embeddings)} embeddings for level {level}")

        return results

    def get_provider_info(self, provider: str) -> dict[str, Any]:
        """Get information about an embedding provider"""
        config = self.provider_configs.get(provider)
        if not config:
            raise ValueError(f"Unknown provider: {provider}")

        return {
            "provider": provider,
            "models": list(config["models"].keys()),
            "default_model": config["default_model"],
            "model_configs": config["models"],
        }

    def get_stats(self) -> dict[str, Any]:
        """Get embedding generation statistics"""
        cache_stats = self.cache.get_stats()

        return {
            **self._stats,
            "cache_stats": cache_stats,
            "supported_providers": list(self.provider_configs.keys()),
            "default_provider": self.default_provider,
        }

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on embedding providers"""
        results = {}

        for provider in self.provider_configs:
            try:
                # Test with a simple embedding
                test_content = "This is a test."
                await self._call_embedding_api(
                    test_content, provider, self.provider_configs[provider]["default_model"]
                )
                results[provider] = {"status": "healthy", "error": None}
            except Exception as e:
                results[provider] = {"status": "unhealthy", "error": str(e)}

        return {
            "overall_status": (
                "healthy" if all(r["status"] == "healthy" for r in results.values()) else "degraded"
            ),
            "providers": results,
            "timestamp": datetime.now().isoformat(),
        }

    def cleanup_cache(self):
        """Clean up expired cache entries"""
        self.cache.clear_expired()
        logger.info("Cleaned up embedding cache")
