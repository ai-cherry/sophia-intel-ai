"""
Vector Store - Embeddings and semantic search memory
Unified interface for vector operations across multiple vector databases
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from app.core.unified_memory import (
    unified_memory,
)
from app.core.vector_db_config import VectorDBType, vector_db_manager

logger = logging.getLogger(__name__)


class EmbeddingModel(Enum):
    """Supported embedding models"""

    OPENAI_ADA_002 = "text-embedding-ada-002"
    OPENAI_3_SMALL = "text-embedding-3-small"
    OPENAI_3_LARGE = "text-embedding-3-large"
    COHERE_EMBED = "embed-english-v3.0"
    SENTENCE_TRANSFORMERS = "all-MiniLM-L6-v2"


class VectorOperation(Enum):
    """Types of vector operations"""

    SIMILARITY_SEARCH = "similarity_search"
    CLUSTERING = "clustering"
    CLASSIFICATION = "classification"
    RECOMMENDATION = "recommendation"
    ANOMALY_DETECTION = "anomaly_detection"


@dataclass
class VectorMetadata:
    """Enhanced metadata for vector embeddings"""

    content_type: str  # "text", "image", "audio", "code"
    embedding_model: EmbeddingModel
    dimensions: int
    source_content_hash: Optional[str] = None
    chunk_index: Optional[int] = None  # For chunked content
    total_chunks: Optional[int] = None
    parent_document_id: Optional[str] = None
    preprocessing_steps: list[str] = field(default_factory=list)
    quality_score: float = 1.0  # Embedding quality assessment


@dataclass
class SemanticQuery:
    """Comprehensive semantic search query"""

    query_text: Optional[str] = None
    query_vector: Optional[list[float]] = None

    # Search parameters
    top_k: int = 10
    similarity_threshold: float = 0.7

    # Filters
    content_types: Optional[set[str]] = None
    domains: Optional[set[str]] = None
    date_range: Optional[tuple[datetime, datetime]] = None
    metadata_filters: dict[str, Any] = field(default_factory=dict)

    # Advanced options
    rerank: bool = False
    explain_relevance: bool = False
    include_metadata: bool = True


@dataclass
class SemanticResult:
    """Semantic search result with rich metadata"""

    vector_id: str
    content: str
    similarity_score: float

    # Source information
    source_tier: str  # Which vector DB provided the result
    original_memory_id: Optional[str] = None

    # Vector information
    embedding_model: Optional[str] = None
    dimensions: Optional[int] = None

    # Enhanced metadata
    content_type: Optional[str] = None
    relevance_explanation: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class VectorStore:
    """
    Unified vector store interface for semantic search and embeddings
    Manages multiple vector databases and provides intelligent routing
    """

    def __init__(self):
        self.memory_interface = unified_memory
        self.vector_manager = vector_db_manager
        self.namespace = "vectors"

        # Vector database preferences by use case
        self.db_preferences = {
            VectorOperation.SIMILARITY_SEARCH: [
                VectorDBType.QDRANT,
                VectorDBType.WEAVIATE,
            ],
            VectorOperation.CLUSTERING: [VectorDBType.QDRANT],
            VectorOperation.RECOMMENDATION: [
                VectorDBType.WEAVIATE,
                VectorDBType.QDRANT,
            ],
            VectorOperation.CLASSIFICATION: [VectorDBType.QDRANT],
            VectorOperation.ANOMALY_DETECTION: [VectorDBType.QDRANT],
        }

        # Embedding model configurations
        self.embedding_config = {
            EmbeddingModel.OPENAI_ADA_002: {"dimensions": 1536, "max_tokens": 8191},
            EmbeddingModel.OPENAI_3_SMALL: {"dimensions": 1536, "max_tokens": 8191},
            EmbeddingModel.OPENAI_3_LARGE: {"dimensions": 3072, "max_tokens": 8191},
            EmbeddingModel.COHERE_EMBED: {"dimensions": 1024, "max_tokens": 2048},
            EmbeddingModel.SENTENCE_TRANSFORMERS: {
                "dimensions": 384,
                "max_tokens": 512,
            },
        }

    async def store_embedding(
        self,
        content: str,
        embedding: Optional[list[float]] = None,
        metadata: Optional[VectorMetadata] = None,
        memory_id: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> str:
        """Store content with vector embedding"""

        # Generate embedding if not provided
        if embedding is None:
            embedding = await self._generate_embedding(
                content, metadata.embedding_model if metadata else None
            )

        # Create metadata if not provided
        if metadata is None:
            metadata = VectorMetadata(
                content_type="text",
                embedding_model=EmbeddingModel.OPENAI_ADA_002,
                dimensions=len(embedding),
            )

        # Determine optimal vector database
        vector_db = self._select_vector_database(VectorOperation.SIMILARITY_SEARCH)

        # Create comprehensive vector metadata
        vector_metadata = {
            "content": content,
            "memory_id": memory_id,
            "content_type": metadata.content_type,
            "embedding_model": metadata.embedding_model.value,
            "dimensions": metadata.dimensions,
            "quality_score": metadata.quality_score,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "domain": domain,
        }

        if metadata.source_content_hash:
            vector_metadata["content_hash"] = metadata.source_content_hash
        if metadata.chunk_index is not None:
            vector_metadata["chunk_index"] = metadata.chunk_index
            vector_metadata["total_chunks"] = metadata.total_chunks
        if metadata.parent_document_id:
            vector_metadata["parent_document_id"] = metadata.parent_document_id

        # Store in vector database
        success = self.vector_manager.store_vector(
            db_type=vector_db,
            vector=embedding,
            metadata=vector_metadata,
            collection_name=(
                f"unified_vectors_{domain}" if domain else "unified_vectors"
            ),
        )

        if success:
            # Generate vector ID for tracking
            vector_id = f"{vector_db.value}:{datetime.now().timestamp()}"

            # Store vector metadata in Redis for quick lookups
            await self._store_vector_metadata(vector_id, metadata, vector_metadata)

            logger.debug(f"Stored vector embedding: {content[:50]}... ({vector_id})")
            return vector_id
        else:
            logger.error(f"Failed to store vector embedding in {vector_db.value}")
            return None

    async def semantic_search(
        self,
        query: SemanticQuery,
        operation: VectorOperation = VectorOperation.SIMILARITY_SEARCH,
    ) -> list[SemanticResult]:
        """Perform semantic search across vector databases"""

        # Generate query embedding if needed
        if query.query_vector is None and query.query_text:
            query.query_vector = await self._generate_embedding(query.query_text)

        if query.query_vector is None:
            logger.error("No query vector or text provided")
            return []

        # Get preferred databases for this operation
        preferred_dbs = self.db_preferences.get(operation, [VectorDBType.QDRANT])

        # Search across multiple databases in parallel
        search_tasks = []
        for db_type in preferred_dbs:
            if self.vector_manager.get_client(db_type):
                search_tasks.append(self._search_database(db_type, query))

        if not search_tasks:
            logger.warning("No available vector databases for search")
            return []

        # Execute searches
        database_results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # Aggregate and rank results
        all_results = []
        for _i, results in enumerate(database_results):
            if isinstance(results, Exception):
                logger.warning(f"Database search failed: {results}")
                continue
            if isinstance(results, list):
                all_results.extend(results)

        # Deduplicate and re-rank results
        unique_results = self._deduplicate_results(all_results)
        ranked_results = self._rank_results(unique_results, query)

        # Apply post-processing
        if query.rerank:
            ranked_results = await self._rerank_results(ranked_results, query)

        if query.explain_relevance:
            for result in ranked_results:
                result.relevance_explanation = self._explain_relevance(result, query)

        return ranked_results[: query.top_k]

    async def find_similar_content(
        self,
        content: str,
        max_results: int = 5,
        similarity_threshold: float = 0.8,
        domain: Optional[str] = None,
    ) -> list[SemanticResult]:
        """Find content similar to the provided text"""

        query = SemanticQuery(
            query_text=content,
            top_k=max_results,
            similarity_threshold=similarity_threshold,
            domains={domain} if domain else None,
        )

        return await self.semantic_search(query)

    async def cluster_content(
        self,
        content_ids: list[str],
        num_clusters: int = 5,
        domain: Optional[str] = None,
    ) -> dict[str, Any]:
        """Cluster content based on semantic similarity"""

        # This would implement clustering using the vector database
        # For now, return a placeholder structure
        return {
            "num_clusters": num_clusters,
            "clusters": [],
            "content_ids": content_ids,
            "domain": domain,
            "algorithm": "k-means",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_content_recommendations(
        self,
        user_id: str,
        based_on_content: Optional[list[str]] = None,
        max_results: int = 10,
        domain: Optional[str] = None,
    ) -> list[SemanticResult]:
        """Get content recommendations for a user"""

        # This would implement a recommendation system
        # For now, return similarity search if content provided
        if based_on_content:
            combined_content = " ".join(based_on_content)
            return await self.find_similar_content(
                content=combined_content, max_results=max_results, domain=domain
            )
        else:
            return []

    async def detect_anomalies(
        self,
        content: str,
        reference_domain: Optional[str] = None,
        anomaly_threshold: float = 0.3,
    ) -> dict[str, Any]:
        """Detect if content is anomalous compared to reference set"""

        # Generate embedding for content
        await self._generate_embedding(content)

        # This would implement anomaly detection logic
        # For now, return a placeholder
        return {
            "is_anomaly": False,
            "anomaly_score": 0.1,
            "threshold": anomaly_threshold,
            "reference_domain": reference_domain,
            "explanation": "Content appears normal based on reference patterns",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_vector_analytics(
        self, domain: Optional[str] = None
    ) -> dict[str, Any]:
        """Get analytics on vector store usage and performance"""

        analytics = {
            "total_vectors": 0,
            "by_database": {},
            "by_embedding_model": {},
            "by_content_type": {},
            "by_domain": {},
            "average_quality_score": 0.0,
            "search_performance": {"average_response_time_ms": 0, "total_searches": 0},
            "domain_filter": domain,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        return analytics

    # Private helper methods

    def _select_vector_database(self, operation: VectorOperation) -> VectorDBType:
        """Select optimal vector database for operation"""

        preferred_dbs = self.db_preferences.get(operation, [VectorDBType.QDRANT])

        # Return first available database
        for db_type in preferred_dbs:
            if self.vector_manager.get_client(db_type):
                return db_type

        # Fallback to any available database
        for db_type in VectorDBType:
            if self.vector_manager.get_client(db_type):
                return db_type

        return VectorDBType.QDRANT  # Default fallback

    async def _generate_embedding(
        self, content: str, model: Optional[EmbeddingModel] = None
    ) -> list[float]:
        """Generate embedding for content"""

        # For now, return a placeholder embedding
        # In production, this would call the actual embedding service
        model = model or EmbeddingModel.OPENAI_ADA_002
        dimensions = self.embedding_config[model]["dimensions"]

        # Generate dummy embedding based on content hash
        import hashlib

        content_hash = hashlib.md5(content.encode()).hexdigest()
        seed = int(content_hash[:8], 16)

        import random

        random.seed(seed)
        embedding = [random.uniform(-1, 1) for _ in range(dimensions)]

        # Normalize the embedding
        magnitude = sum(x**2 for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]

        return embedding

    async def _search_database(
        self, db_type: VectorDBType, query: SemanticQuery
    ) -> list[SemanticResult]:
        """Search a specific vector database"""

        try:
            # Determine collection name
            collection_name = "unified_vectors"
            if query.domains:
                # Use domain-specific collection if available
                domain = next(iter(query.domains))
                collection_name = f"unified_vectors_{domain}"

            # Search the database
            raw_results = self.vector_manager.search_vectors(
                db_type=db_type,
                query_vector=query.query_vector,
                top_k=query.top_k * 2,  # Get extra results for filtering
                collection_name=collection_name,
            )

            # Convert to SemanticResult objects
            results = []
            for raw_result in raw_results:
                if hasattr(raw_result, "payload") and hasattr(raw_result, "score"):
                    result = SemanticResult(
                        vector_id=f"{db_type.value}:{raw_result.payload.get('memory_id', 'unknown')}",
                        content=raw_result.payload.get("content", ""),
                        similarity_score=raw_result.score,
                        source_tier=db_type.value,
                        original_memory_id=raw_result.payload.get("memory_id"),
                        embedding_model=raw_result.payload.get("embedding_model"),
                        dimensions=raw_result.payload.get("dimensions"),
                        content_type=raw_result.payload.get("content_type"),
                        metadata=raw_result.payload,
                    )

                    # Apply similarity threshold
                    if result.similarity_score >= query.similarity_threshold:
                        results.append(result)

            return results

        except Exception as e:
            logger.error(f"Search failed for {db_type.value}: {e}")
            return []

    def _deduplicate_results(
        self, results: list[SemanticResult]
    ) -> list[SemanticResult]:
        """Remove duplicate results based on content or memory ID"""

        seen_ids = set()
        seen_content = set()
        unique_results = []

        for result in results:
            # Check for duplicate memory ID
            if result.original_memory_id and result.original_memory_id in seen_ids:
                continue

            # Check for duplicate content (first 100 characters)
            content_key = result.content[:100] if result.content else ""
            if content_key in seen_content:
                continue

            # Add to unique results
            if result.original_memory_id:
                seen_ids.add(result.original_memory_id)
            seen_content.add(content_key)
            unique_results.append(result)

        return unique_results

    def _rank_results(
        self, results: list[SemanticResult], query: SemanticQuery
    ) -> list[SemanticResult]:
        """Re-rank results based on multiple factors"""

        def ranking_score(result: SemanticResult) -> float:
            score = result.similarity_score

            # Boost based on content type preference
            if query.content_types and result.content_type in query.content_types:
                score *= 1.1

            # Boost high-quality embeddings
            quality = result.metadata.get("quality_score", 1.0)
            score *= quality

            # Prefer more recent content (if timestamp available)
            created_at = result.metadata.get("created_at")
            if created_at:
                try:
                    created_time = datetime.fromisoformat(
                        created_at.replace("Z", "+00:00")
                    )
                    days_old = (datetime.now(timezone.utc) - created_time).days
                    recency_factor = max(0.5, 1.0 - days_old / 365)  # Decay over a year
                    score *= recency_factor
                except Exception:pass

            return score

        return sorted(results, key=ranking_score, reverse=True)

    async def _rerank_results(
        self, results: list[SemanticResult], query: SemanticQuery
    ) -> list[SemanticResult]:
        """Apply advanced re-ranking using cross-encoder or similar"""

        # Placeholder for advanced re-ranking
        # In production, this might use a cross-encoder model
        return results

    def _explain_relevance(self, result: SemanticResult, query: SemanticQuery) -> str:
        """Generate explanation for why result is relevant"""

        explanations = []

        # Similarity score explanation
        if result.similarity_score >= 0.9:
            explanations.append("Very high semantic similarity")
        elif result.similarity_score >= 0.8:
            explanations.append("High semantic similarity")
        elif result.similarity_score >= 0.7:
            explanations.append("Moderate semantic similarity")
        else:
            explanations.append("Low semantic similarity")

        # Content type match
        if query.content_types and result.content_type in query.content_types:
            explanations.append(
                f"Matches preferred content type: {result.content_type}"
            )

        # Quality factor
        quality = result.metadata.get("quality_score", 1.0)
        if quality >= 0.9:
            explanations.append("High-quality embedding")

        return "; ".join(explanations)

    async def _store_vector_metadata(
        self, vector_id: str, metadata: VectorMetadata, storage_metadata: dict[str, Any]
    ):
        """Store vector metadata for tracking and analytics"""

        if not self.memory_interface.redis_manager:
            return

        combined_metadata = {
            "vector_id": vector_id,
            "embedding_model": metadata.embedding_model.value,
            "dimensions": metadata.dimensions,
            "content_type": metadata.content_type,
            "quality_score": metadata.quality_score,
            "preprocessing_steps": metadata.preprocessing_steps,
            **storage_metadata,
        }

        key = f"vector_metadata:{vector_id}"
        await self.memory_interface.redis_manager.set_with_ttl(
            key, combined_metadata, ttl=86400 * 7, namespace="vectors"  # 7 days
        )


# Global vector store instance
vector_store = VectorStore()
