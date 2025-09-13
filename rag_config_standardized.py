#!/usr/bin/env python3
"""
Standardized RAG Configuration for Sophia AI
Eliminates vector dimension inconsistencies and similarity threshold variations
"""
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any
class VectorProvider(Enum):
    """Supported vector database providers"""
    QDRANT = "qdrant"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    UNIFIED_MEMORY = "unified_memory"
class EmbeddingModel(Enum):
    """Standardized embedding models with consistent dimensions"""
    OPENAI_ADA_002 = ("text-embedding-ada-002", 1536)
    OPENAI_3_SMALL = ("text-embedding-3-small", 1536)
    OPENAI_3_LARGE = ("text-embedding-3-large", 3072)
    VERTEX_GECKO = ("textembedding-gecko@003", 768)
    HUGGINGFACE_MINI = ("all-MiniLM-L6-v2", 384)
@dataclass
class StandardRAGConfig:
    """Standardized RAG configuration to eliminate inconsistencies"""
    # Vector Configuration (STANDARDIZED)
    vector_dimension: int = 1536  # OpenAI standard
    similarity_threshold: float = 0.8  # Consistent across all components
    max_results: int = 10
    # Embedding Configuration
    embedding_model: EmbeddingModel = EmbeddingModel.OPENAI_ADA_002
    embedding_batch_size: int = 100
    # Vector Database Configuration
    vector_provider: VectorProvider = VectorProvider.QDRANT
    collection_name: str = "sophia_vectors"
    distance_metric: str = "cosine"
    # Redis Cache Configuration (STANDARDIZED TTL)
    redis_hot_cache_ttl: int = 10  # 10 seconds for hot queries (<100ms target)
    redis_warm_cache_ttl: int = 300  # 5 minutes for warm queries
    redis_cold_cache_ttl: int = 86400  # 24 hours for cold queries
    # Performance Configuration
    hot_query_target_ms: int = 100  # <100ms for hot queries
    warm_query_target_ms: int = 500  # <500ms for warm queries
    cold_query_target_ms: int = 2000  # <2s for cold queries
    # Pathway Configuration
    pathway_batch_size: int = 1000
    pathway_throughput_target: float = 1000.0  # docs/second
    # Vertex AI Configuration
    vertex_project_id: str | None = None
    vertex_location: str = "us-central1"
    # Business Intelligence Configuration
    apartment_data_shards: int = 5
    apartment_data_limit: int = 1000000
    qdrant_shard_count: int = 5
    postgres_shard_count: int = 3
class RAGConfigManager:
    """Centralized RAG configuration management"""
    def __init__(self, config: StandardRAGConfig | None = None):
        self.config = config or StandardRAGConfig()
        self._validate_config()
    def _validate_config(self):
        """Validate configuration consistency"""
        # Ensure vector dimensions match embedding model
        model_name, expected_dim = self.config.embedding_model.value
        if self.config.vector_dimension != expected_dim:
            raise ValueError(
                f"Vector dimension {self.config.vector_dimension} doesn't match "
                f"embedding model {model_name} expected dimension {expected_dim}"
            )
        # Validate similarity threshold
        if not 0.0 <= self.config.similarity_threshold <= 1.0:
            raise ValueError("Similarity threshold must be between 0.0 and 1.0")
        # Validate TTL values
        if self.config.redis_hot_cache_ttl >= self.config.redis_warm_cache_ttl:
            raise ValueError("Hot cache TTL must be less than warm cache TTL")
    def get_qdrant_config(self) -> dict[str, Any]:
        """Get standardized Qdrant configuration"""
        return {
            "collection_name": self.config.collection_name,
            "vector_size": self.config.vector_dimension,
            "distance": self.config.distance_metric.upper(),
            "shard_number": self.config.qdrant_shard_count,
            "replication_factor": 1,
            "write_consistency_factor": 1,
            "on_disk_payload": True,
            "hnsw_config": {"m": 16, "ef_construct": 100, "full_scan_threshold": 10000},
        }
    def get_redis_config(self) -> dict[str, Any]:
        """Get standardized Redis configuration"""
        return {
            "hot_cache_ttl": self.config.redis_hot_cache_ttl,
            "warm_cache_ttl": self.config.redis_warm_cache_ttl,
            "cold_cache_ttl": self.config.redis_cold_cache_ttl,
            "key_prefix": "sophia_rag:",
            "compression": True,
            "serialization": "json",
        }
    def get_embedding_config(self) -> dict[str, Any]:
        """Get standardized embedding configuration"""
        model_name, dimension = self.config.embedding_model.value
        return {
            "model": model_name,
            "dimension": dimension,
            "batch_size": self.config.embedding_batch_size,
            "normalize": True,
            "timeout": 30,
        }
    def get_performance_targets(self) -> dict[str, Any]:
        """Get performance targets for monitoring"""
        return {
            "hot_query_ms": self.config.hot_query_target_ms,
            "warm_query_ms": self.config.warm_query_target_ms,
            "cold_query_ms": self.config.cold_query_target_ms,
            "pathway_throughput": self.config.pathway_throughput_target,
            "similarity_threshold": self.config.similarity_threshold,
        }
    def get_apartment_data_config(self) -> dict[str, Any]:
        """Get apartment data processing configuration"""
        return {
            "data_shards": self.config.apartment_data_shards,
            "data_limit": self.config.apartment_data_limit,
            "qdrant_shards": self.config.qdrant_shard_count,
            "postgres_shards": self.config.postgres_shard_count,
            "batch_size": 10000,
            "parallel_workers": self.config.apartment_data_shards,
        }
    @classmethod
    def from_environment(cls) -> "RAGConfigManager":
        """Create configuration from environment variables"""
        config = StandardRAGConfig()
        # Override from environment if available
        config.vector_dimension = int(
            os.getenv("RAG_VECTOR_DIMENSION", config.vector_dimension)
        )
        config.similarity_threshold = float(
            os.getenv("RAG_SIMILARITY_THRESHOLD", config.similarity_threshold)
        )
        config.max_results = int(os.getenv("RAG_MAX_RESULTS", config.max_results))
        # Redis TTL configuration
        config.redis_hot_cache_ttl = int(
            os.getenv("REDIS_HOT_CACHE_TTL", config.redis_hot_cache_ttl)
        )
        config.redis_warm_cache_ttl = int(
            os.getenv("REDIS_WARM_CACHE_TTL", config.redis_warm_cache_ttl)
        )
        config.redis_cold_cache_ttl = int(
            os.getenv("REDIS_COLD_CACHE_TTL", config.redis_cold_cache_ttl)
        )
        # Apartment data configuration
        config.apartment_data_shards = int(
            os.getenv("APARTMENT_DATA_SHARDS", config.apartment_data_shards)
        )
        config.apartment_data_limit = int(
            os.getenv("APARTMENT_DATA_LIMIT", config.apartment_data_limit)
        )
        config.qdrant_shard_count = int(
            os.getenv("QDRANT_SHARD_COUNT", config.qdrant_shard_count)
        )
        config.postgres_shard_count = int(
            os.getenv("POSTGRES_SHARD_COUNT", config.postgres_shard_count)
        )
        return cls(config)
# Global standardized configuration instance
STANDARD_RAG_CONFIG = RAGConfigManager.from_environment()
VECTOR_DIMENSION = STANDARD_RAG_CONFIG.config.vector_dimension
SIMILARITY_THRESHOLD = STANDARD_RAG_CONFIG.config.similarity_threshold
HOT_CACHE_TTL = STANDARD_RAG_CONFIG.config.redis_hot_cache_ttl
WARM_CACHE_TTL = STANDARD_RAG_CONFIG.config.redis_warm_cache_ttl
COLD_CACHE_TTL = STANDARD_RAG_CONFIG.config.redis_cold_cache_ttl
if __name__ == "__main__":
    # Configuration validation and display
    config_manager = RAGConfigManager.from_environment()
    print("🔧 Standardized RAG Configuration")
    print("=" * 50)
    print(f"Vector Dimension: {config_manager.config.vector_dimension}")
    print(f"Similarity Threshold: {config_manager.config.similarity_threshold}")
    print(f"Embedding Model: {config_manager.config.embedding_model.value[0]}")
    print(f"Hot Cache TTL: {config_manager.config.redis_hot_cache_ttl}s")
    print(f"Warm Cache TTL: {config_manager.config.redis_warm_cache_ttl}s")
    print(f"Cold Cache TTL: {config_manager.config.redis_cold_cache_ttl}s")
    print(f"Apartment Data Shards: {config_manager.config.apartment_data_shards}")
    print(f"Qdrant Shard Count: {config_manager.config.qdrant_shard_count}")
    print("=" * 50)
    print("✅ Configuration validated and ready for use")
