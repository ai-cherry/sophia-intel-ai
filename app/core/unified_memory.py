"""
Unified Memory Interface for Sophia Intel AI
Single interface for all memory operations with intelligent routing and tiered storage
"""
import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4
from app.core.mem0_config import mem0_manager
from app.core.redis_manager import RedisNamespaces, redis_manager
from app.core.vector_db_config import VectorDBType, vector_db_manager
logger = logging.getLogger(__name__)
class MemoryTier(Enum):
    """Memory storage tiers for intelligent routing"""
    L1_CACHE = "l1_cache"  # Redis hot cache - sub-100ms
    L2_SEMANTIC = "l2_semantic"  # Vector DB - semantic search
    L3_PERSISTENT = "l3_persistent"  # Mem0/PostgreSQL - long-term
    L4_ARCHIVE = "l4_archive"  # Cold storage
class MemoryContext(Enum):
    """Memory context types for intelligent categorization"""
    INTELLIGENCE = "intelligence"  # High-level reasoning and insights
    EXECUTION = "execution"  # Task execution history and context
    PATTERN = "pattern"  # Behavioral patterns and trends
    KNOWLEDGE = "knowledge"  # Structured knowledge and facts
    CONVERSATION = "conversation"  # Chat and interaction history
    SYSTEM = "system"  # System state and configuration
class MemoryPriority(Enum):
    """Memory access priority levels"""
    CRITICAL = 1  # Sub-10ms access required
    HIGH = 2  # Sub-100ms access required
    STANDARD = 3  # Sub-1s access acceptable
    LOW = 4  # Multi-second access acceptable
@dataclass
class MemoryMetadata:
    """Enhanced memory metadata for intelligent routing"""
    memory_id: str = field(default_factory=lambda: str(uuid4()))
    context: MemoryContext = MemoryContext.KNOWLEDGE
    priority: MemoryPriority = MemoryPriority.STANDARD
    tags: set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    accessed_count: int = 0
    last_accessed: Optional[datetime] = None
    ttl_seconds: Optional[int] = None
    source: str = "unified_memory"
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    domain: Optional[str] = None  # , sophia, shared
    confidence_score: float = 1.0
    embedding_model: Optional[str] = None
    vector_dimensions: Optional[int] = None
@dataclass
class MemoryEntry:
    """Unified memory entry structure"""
    content: str
    metadata: MemoryMetadata
    embedding: Optional[list[float]] = None
    tier_locations: dict[MemoryTier, str] = field(default_factory=dict)
@dataclass
class MemorySearchRequest:
    """Memory search request specification"""
    query: str
    context_filter: Optional[list[MemoryContext]] = None
    tag_filter: Optional[set[str]] = None
    domain_filter: Optional[str] = None
    user_filter: Optional[str] = None
    priority_threshold: MemoryPriority = MemoryPriority.LOW
    max_results: int = 10
    similarity_threshold: float = 0.7
    include_system: bool = False
@dataclass
class MemorySearchResult:
    """Memory search result with relevance scoring"""
    memory_id: str
    content: str
    metadata: MemoryMetadata
    relevance_score: float
    access_time_ms: float
    source_tier: MemoryTier
class UnifiedMemoryInterface:
    """
    Unified Memory Interface - Single point of access for all memory operations
    Provides intelligent routing, caching, and cross-tier search capabilities
    """
    def __init__(self):
        self.redis_manager = redis_manager
        self.vector_manager = vector_db_manager
        self.mem0_manager = mem0_manager
        self._initialized = False
        self._lock = asyncio.Lock()
        # Performance metrics
        self.metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_response_time_ms": 0,
            "tier_usage": {tier.value: 0 for tier in MemoryTier},
            "last_metrics_reset": datetime.now(timezone.utc),
        }
        # Memory router configuration
        self.tier_config = {
            MemoryTier.L1_CACHE: {
                "max_size_mb": 128,
                "ttl_default": 300,  # 5 minutes
                "ttl_by_priority": {
                    MemoryPriority.CRITICAL: 60,  # 1 minute
                    MemoryPriority.HIGH: 300,  # 5 minutes
                    MemoryPriority.STANDARD: 900,  # 15 minutes
                    MemoryPriority.LOW: 3600,  # 1 hour
                },
            },
            MemoryTier.L2_SEMANTIC: {
                "preferred_vector_db": VectorDBType.QDRANT,
                "fallback_vector_db": VectorDBType.WEAVIATE,
                "embedding_model": "text-embedding-ada-002",
                "index_threshold": 100,  # Auto-index after 100 entries
            },
        }
    async def initialize(self) -> bool:
        """Initialize all memory subsystems"""
        if self._initialized:
            return True
        async with self._lock:
            if self._initialized:
                return True
            try:
                logger.info("Initializing Unified Memory Interface...")
                # Initialize Redis manager for L1 cache
                if self.redis_manager:
                    await self.redis_manager.initialize()
                    logger.info("✓ L1 Cache (Redis) initialized")
                else:
                    logger.warning("✗ Redis manager not available")
                # Initialize vector databases for L2 semantic storage
                if self.vector_manager:
                    # Test primary vector DB
                    primary_db = self.tier_config[MemoryTier.L2_SEMANTIC][
                        "preferred_vector_db"
                    ]
                    if self.vector_manager.test_connection(primary_db):
                        logger.info(f"✓ L2 Semantic ({primary_db.value}) initialized")
                    else:
                        logger.warning(
                            f"✗ Primary vector DB ({primary_db.value}) unavailable"
                        )
                else:
                    logger.warning("✗ Vector manager not available")
                # Initialize Mem0 for L3 persistent storage
                if self.mem0_manager:
                    if self.mem0_manager.test_connection():
                        logger.info("✓ L3 Persistent (Mem0) initialized")
                    else:
                        logger.warning("✗ Mem0 connection failed")
                else:
                    logger.warning("✗ Mem0 manager not available")
                self._initialized = True
                logger.info("Unified Memory Interface initialization complete")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize Unified Memory Interface: {e}")
                return False
    async def store(
        self,
        content: str,
        metadata: Optional[MemoryMetadata] = None,
        embedding: Optional[list[float]] = None,
    ) -> str:
        """
        Store memory entry with intelligent tier allocation
        Returns memory_id for future retrieval
        """
        if not self._initialized:
            await self.initialize()
        start_time = time.time()
        try:
            # Create metadata if not provided
            if metadata is None:
                metadata = MemoryMetadata()
            # Create memory entry
            entry = MemoryEntry(content=content, metadata=metadata, embedding=embedding)
            # Determine optimal storage tiers based on metadata
            target_tiers = await self._determine_storage_tiers(entry)
            # Store in each tier
            for tier in target_tiers:
                location = await self._store_in_tier(tier, entry)
                if location:
                    entry.tier_locations[tier] = location
                    self.metrics["tier_usage"][tier.value] += 1
            # Update metrics
            self.metrics["total_requests"] += 1
            response_time = (time.time() - start_time) * 1000
            self._update_response_time_metric(response_time)
            logger.debug(
                f"Stored memory {metadata.memory_id} in tiers: {list(entry.tier_locations.keys())}"
            )
            return metadata.memory_id
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise
    async def retrieve(
        self, memory_id: str, priority: MemoryPriority = MemoryPriority.STANDARD
    ) -> Optional[MemoryEntry]:
        """Retrieve memory by ID with tier-optimized access"""
        if not self._initialized:
            await self.initialize()
        start_time = time.time()
        try:
            # Try tiers in performance order
            tier_order = self._get_tier_access_order(priority)
            for tier in tier_order:
                entry = await self._retrieve_from_tier(tier, memory_id)
                if entry:
                    # Update access metadata
                    entry.metadata.accessed_count += 1
                    entry.metadata.last_accessed = datetime.now(timezone.utc)
                    # Cache in L1 for future fast access if not already there
                    if tier != MemoryTier.L1_CACHE:
                        await self._store_in_tier(MemoryTier.L1_CACHE, entry)
                        self.metrics["cache_misses"] += 1
                    else:
                        self.metrics["cache_hits"] += 1
                    # Update metrics
                    response_time = (time.time() - start_time) * 1000
                    self._update_response_time_metric(response_time)
                    return entry
            logger.debug(f"Memory {memory_id} not found in any tier")
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve memory {memory_id}: {e}")
            return None
    async def search(self, request: MemorySearchRequest) -> list[MemorySearchResult]:
        """
        Cross-tier semantic search with intelligent result fusion
        """
        if not self._initialized:
            await self.initialize()
        start_time = time.time()
        results = []
        try:
            # Parallel search across appropriate tiers
            search_tasks = []
            # L1 Cache search (text-based)
            if self.redis_manager:
                search_tasks.append(self._search_l1_cache(request))
            # L2 Semantic search (vector-based)
            if self.vector_manager:
                search_tasks.append(self._search_l2_semantic(request))
            # L3 Persistent search (Mem0)
            if self.mem0_manager:
                search_tasks.append(self._search_l3_persistent(request))
            # Execute searches in parallel
            tier_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            # Aggregate and rank results
            for tier_result in tier_results:
                if isinstance(tier_result, Exception):
                    logger.warning(f"Tier search failed: {tier_result}")
                    continue
                if isinstance(tier_result, list):
                    results.extend(tier_result)
            # Deduplicate and rank by relevance
            unique_results = self._deduplicate_results(results)
            ranked_results = sorted(
                unique_results, key=lambda x: x.relevance_score, reverse=True
            )[: request.max_results]
            # Update metrics
            response_time = (time.time() - start_time) * 1000
            self._update_response_time_metric(response_time)
            logger.debug(
                f"Search returned {len(ranked_results)} results in {response_time:.2f}ms"
            )
            return ranked_results
        except Exception as e:
            logger.error(f"Failed to search memory: {e}")
            return []
    async def update(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[MemoryMetadata] = None,
    ) -> bool:
        """Update existing memory entry across all tiers"""
        if not self._initialized:
            await self.initialize()
        try:
            # First retrieve the existing entry
            existing_entry = await self.retrieve(memory_id)
            if not existing_entry:
                logger.warning(f"Memory {memory_id} not found for update")
                return False
            # Update content and metadata
            if content is not None:
                existing_entry.content = content
            if metadata is not None:
                existing_entry.metadata = metadata
            existing_entry.metadata.updated_at = datetime.now(timezone.utc)
            # Update in all tiers where it exists
            update_tasks = []
            for tier, _location in existing_entry.tier_locations.items():
                update_tasks.append(self._update_in_tier(tier, existing_entry))
            results = await asyncio.gather(*update_tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)
            logger.debug(
                f"Updated memory {memory_id} in {success_count}/{len(update_tasks)} tiers"
            )
            return success_count > 0
        except Exception as e:
            logger.error(f"Failed to update memory {memory_id}: {e}")
            return False
    async def delete(self, memory_id: str) -> bool:
        """Delete memory entry from all tiers"""
        if not self._initialized:
            await self.initialize()
        try:
            # Delete from all possible tiers
            delete_tasks = []
            for tier in MemoryTier:
                delete_tasks.append(self._delete_from_tier(tier, memory_id))
            results = await asyncio.gather(*delete_tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)
            logger.debug(f"Deleted memory {memory_id} from {success_count} tiers")
            return success_count > 0
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            return False
    async def get_health_status(self) -> dict[str, Any]:
        """Get comprehensive health status of all memory tiers"""
        status = {
            "unified_memory_available": self._initialized,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tiers": {},
            "metrics": self.metrics.copy(),
        }
        # Check each tier
        for tier in MemoryTier:
            tier_status = await self._get_tier_health(tier)
            status["tiers"][tier.value] = tier_status
        return status
    async def get_metrics(self) -> dict[str, Any]:
        """Get performance metrics"""
        return self.metrics.copy()
    # Private methods for tier-specific operations
    async def _determine_storage_tiers(self, entry: MemoryEntry) -> list[MemoryTier]:
        """Determine which tiers to store the entry in based on metadata"""
        tiers = []
        # Always store in L1 cache for fast access
        if entry.metadata.priority in [MemoryPriority.CRITICAL, MemoryPriority.HIGH]:
            tiers.append(MemoryTier.L1_CACHE)
        # Store in L2 semantic if content is suitable for vector search
        if len(entry.content) > 50 and entry.metadata.context != MemoryContext.SYSTEM:
            tiers.append(MemoryTier.L2_SEMANTIC)
        # Store in L3 persistent for long-term retention
        if not entry.metadata.ttl_seconds or entry.metadata.ttl_seconds > 3600:
            tiers.append(MemoryTier.L3_PERSISTENT)
        # Default to at least L1 cache
        if not tiers:
            tiers.append(MemoryTier.L1_CACHE)
        return tiers
    def _get_tier_access_order(self, priority: MemoryPriority) -> list[MemoryTier]:
        """Get tier access order based on priority"""
        if priority == MemoryPriority.CRITICAL or priority == MemoryPriority.HIGH:
            return [
                MemoryTier.L1_CACHE,
                MemoryTier.L2_SEMANTIC,
                MemoryTier.L3_PERSISTENT,
            ]
        else:
            return [
                MemoryTier.L1_CACHE,
                MemoryTier.L3_PERSISTENT,
                MemoryTier.L2_SEMANTIC,
            ]
    async def _store_in_tier(
        self, tier: MemoryTier, entry: MemoryEntry
    ) -> Optional[str]:
        """Store entry in specific tier"""
        try:
            if tier == MemoryTier.L1_CACHE:
                return await self._store_l1_cache(entry)
            elif tier == MemoryTier.L2_SEMANTIC:
                return await self._store_l2_semantic(entry)
            elif tier == MemoryTier.L3_PERSISTENT:
                return await self._store_l3_persistent(entry)
            else:
                logger.warning(f"Tier {tier} not implemented")
                return None
        except Exception as e:
            logger.error(f"Failed to store in tier {tier}: {e}")
            return None
    async def _retrieve_from_tier(
        self, tier: MemoryTier, memory_id: str
    ) -> Optional[MemoryEntry]:
        """Retrieve entry from specific tier"""
        try:
            if tier == MemoryTier.L1_CACHE:
                return await self._retrieve_l1_cache(memory_id)
            elif tier == MemoryTier.L2_SEMANTIC:
                return await self._retrieve_l2_semantic(memory_id)
            elif tier == MemoryTier.L3_PERSISTENT:
                return await self._retrieve_l3_persistent(memory_id)
            else:
                return None
        except Exception as e:
            logger.error(f"Failed to retrieve from tier {tier}: {e}")
            return None
    async def _store_l1_cache(self, entry: MemoryEntry) -> str:
        """Store in L1 Redis cache"""
        if not self.redis_manager:
            return None
        # Serialize entry
        cache_data = {
            "content": entry.content,
            "metadata": {
                "memory_id": entry.metadata.memory_id,
                "context": entry.metadata.context.value,
                "priority": entry.metadata.priority.value,
                "tags": list(entry.metadata.tags),
                "created_at": entry.metadata.created_at.isoformat(),
                "updated_at": entry.metadata.updated_at.isoformat(),
                "accessed_count": entry.metadata.accessed_count,
                "source": entry.metadata.source,
                "user_id": entry.metadata.user_id,
                "session_id": entry.metadata.session_id,
                "domain": entry.metadata.domain,
                "confidence_score": entry.metadata.confidence_score,
            },
            "embedding": entry.embedding,
        }
        # Determine TTL
        ttl = self.tier_config[MemoryTier.L1_CACHE]["ttl_by_priority"][
            entry.metadata.priority
        ]
        if entry.metadata.ttl_seconds:
            ttl = min(ttl, entry.metadata.ttl_seconds)
        # Store with namespace
        key = f"unified_memory:{entry.metadata.memory_id}"
        await self.redis_manager.set_with_ttl(
            key, json.dumps(cache_data), ttl=ttl, namespace=RedisNamespaces.MEMORY
        )
        return key
    async def _retrieve_l1_cache(self, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve from L1 Redis cache"""
        if not self.redis_manager:
            return None
        try:
            key = f"unified_memory:{memory_id}"
            cached_data = await self.redis_manager.get(
                key, namespace=RedisNamespaces.MEMORY
            )
            if not cached_data:
                return None
            data = json.loads(
                cached_data.decode() if isinstance(cached_data, bytes) else cached_data
            )
            # Reconstruct metadata
            metadata = MemoryMetadata(
                memory_id=data["metadata"]["memory_id"],
                context=MemoryContext(data["metadata"]["context"]),
                priority=MemoryPriority(data["metadata"]["priority"]),
                tags=set(data["metadata"]["tags"]),
                created_at=datetime.fromisoformat(data["metadata"]["created_at"]),
                updated_at=datetime.fromisoformat(data["metadata"]["updated_at"]),
                accessed_count=data["metadata"]["accessed_count"],
                source=data["metadata"]["source"],
                user_id=data["metadata"].get("user_id"),
                session_id=data["metadata"].get("session_id"),
                domain=data["metadata"].get("domain"),
                confidence_score=data["metadata"]["confidence_score"],
            )
            return MemoryEntry(
                content=data["content"],
                metadata=metadata,
                embedding=data.get("embedding"),
                tier_locations={MemoryTier.L1_CACHE: key},
            )
        except Exception as e:
            logger.error(f"Failed to retrieve from L1 cache: {e}")
            return None
    async def _store_l2_semantic(self, entry: MemoryEntry) -> str:
        """Store in L2 vector database"""
        if not self.vector_manager:
            return None
        try:
            primary_db = self.tier_config[MemoryTier.L2_SEMANTIC]["preferred_vector_db"]
            # Generate embedding if not provided
            if not entry.embedding:
                # For now, use a placeholder - in production, integrate with embedding service
                entry.embedding = [0.1] * 1536  # OpenAI embedding dimension
            # Prepare metadata for vector storage
            vector_metadata = {
                "memory_id": entry.metadata.memory_id,
                "content": entry.content,
                "context": entry.metadata.context.value,
                "priority": entry.metadata.priority.value,
                "tags": list(entry.metadata.tags),
                "created_at": entry.metadata.created_at.isoformat(),
                "domain": entry.metadata.domain,
                "user_id": entry.metadata.user_id,
            }
            # Store in vector database
            success = self.vector_manager.store_vector(
                db_type=primary_db,
                vector=entry.embedding,
                metadata=vector_metadata,
                collection_name="unified_memory",
            )
            if success:
                return f"{primary_db.value}:unified_memory:{entry.metadata.memory_id}"
            else:
                return None
        except Exception as e:
            logger.error(f"Failed to store in L2 semantic: {e}")
            return None
    async def _retrieve_l2_semantic(self, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve from L2 vector database by ID"""
        # Vector databases typically don't support direct ID lookup efficiently
        # This would need to be implemented with metadata filtering
        # For now, return None and rely on search functionality
        return None
    async def _store_l3_persistent(self, entry: MemoryEntry) -> str:
        """Store in L3 persistent storage (Mem0)"""
        if not self.mem0_manager:
            return None
        try:
            # Mem0 API call would go here
            # For now, return a placeholder
            return f"mem0:{entry.metadata.memory_id}"
        except Exception as e:
            logger.error(f"Failed to store in L3 persistent: {e}")
            return None
    async def _retrieve_l3_persistent(self, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve from L3 persistent storage"""
        if not self.mem0_manager:
            return None
        # Mem0 retrieval would go here
        return None
    async def _search_l1_cache(
        self, request: MemorySearchRequest
    ) -> list[MemorySearchResult]:
        """Search L1 cache with text matching"""
        results = []
        if not self.redis_manager:
            return results
        try:
            # Scan for memory keys
            pattern = f"{RedisNamespaces.MEMORY}:unified_memory:*"
            # Use the Redis manager's scan functionality
            async for key in self.redis_manager.redis.scan_iter(
                match=pattern, count=100
            ):
                cached_data = await self.redis_manager.redis.get(key)
                if cached_data:
                    try:
                        data = json.loads(cached_data)
                        content = data.get("content", "")
                        metadata = data.get("metadata", {})
                        # Simple text matching
                        if request.query.lower() in content.lower():
                            # Apply filters
                            if self._matches_search_filters(metadata, request):
                                result = MemorySearchResult(
                                    memory_id=metadata.get("memory_id"),
                                    content=content,
                                    metadata=self._dict_to_metadata(metadata),
                                    relevance_score=0.8,  # Text matching score
                                    access_time_ms=5.0,  # Fast cache access
                                    source_tier=MemoryTier.L1_CACHE,
                                )
                                results.append(result)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"L1 cache search failed: {e}")
        return results[: request.max_results]
    async def _search_l2_semantic(
        self, request: MemorySearchRequest
    ) -> list[MemorySearchResult]:
        """Search L2 vector database with semantic similarity"""
        results = []
        if not self.vector_manager:
            return results
        try:
            primary_db = self.tier_config[MemoryTier.L2_SEMANTIC]["preferred_vector_db"]
            # Generate query embedding (placeholder for now)
            query_embedding = [0.1] * 1536
            # Search vector database
            search_results = self.vector_manager.search_vectors(
                db_type=primary_db,
                query_vector=query_embedding,
                top_k=request.max_results,
                collection_name="unified_memory",
            )
            for vector_result in search_results:
                # Convert vector result to MemorySearchResult
                if hasattr(vector_result, "payload"):
                    metadata = vector_result.payload
                    result = MemorySearchResult(
                        memory_id=metadata.get("memory_id"),
                        content=metadata.get("content", ""),
                        metadata=self._dict_to_metadata(metadata),
                        relevance_score=(
                            vector_result.score
                            if hasattr(vector_result, "score")
                            else 0.7
                        ),
                        access_time_ms=50.0,  # Vector search time
                        source_tier=MemoryTier.L2_SEMANTIC,
                    )
                    results.append(result)
        except Exception as e:
            logger.error(f"L2 semantic search failed: {e}")
        return results
    async def _search_l3_persistent(
        self, request: MemorySearchRequest
    ) -> list[MemorySearchResult]:
        """Search L3 persistent storage"""
        results = []
        if not self.mem0_manager:
            return results
        try:
            # Mem0 search would go here
            pass
        except Exception as e:
            logger.error(f"L3 persistent search failed: {e}")
        return results
    def _matches_search_filters(
        self, metadata: dict[str, Any], request: MemorySearchRequest
    ) -> bool:
        """Check if metadata matches search filters"""
        # Context filter
        if request.context_filter:
            context = metadata.get("context")
            if context not in [c.value for c in request.context_filter]:
                return False
        # Tag filter
        if request.tag_filter:
            entry_tags = set(metadata.get("tags", []))
            if not entry_tags.intersection(request.tag_filter):
                return False
        # Domain filter
        if request.domain_filter and metadata.get("domain") != request.domain_filter:
            return False
        # User filter
        return not (
            request.user_filter and metadata.get("user_id") != request.user_filter
        )
    def _dict_to_metadata(self, metadata_dict: dict[str, Any]) -> MemoryMetadata:
        """Convert dictionary to MemoryMetadata object"""
        return MemoryMetadata(
            memory_id=metadata_dict.get("memory_id", str(uuid4())),
            context=MemoryContext(metadata_dict.get("context", "knowledge")),
            priority=MemoryPriority(metadata_dict.get("priority", 3)),
            tags=set(metadata_dict.get("tags", [])),
            created_at=datetime.fromisoformat(
                metadata_dict.get("created_at", datetime.now(timezone.utc).isoformat())
            ),
            updated_at=datetime.fromisoformat(
                metadata_dict.get("updated_at", datetime.now(timezone.utc).isoformat())
            ),
            accessed_count=metadata_dict.get("accessed_count", 0),
            source=metadata_dict.get("source", "unified_memory"),
            user_id=metadata_dict.get("user_id"),
            session_id=metadata_dict.get("session_id"),
            domain=metadata_dict.get("domain"),
            confidence_score=metadata_dict.get("confidence_score", 1.0),
        )
    def _deduplicate_results(
        self, results: list[MemorySearchResult]
    ) -> list[MemorySearchResult]:
        """Remove duplicate results and merge scores"""
        seen_ids = set()
        unique_results = []
        for result in results:
            if result.memory_id not in seen_ids:
                seen_ids.add(result.memory_id)
                unique_results.append(result)
        return unique_results
    def _update_response_time_metric(self, response_time_ms: float):
        """Update average response time metric"""
        current_avg = self.metrics["avg_response_time_ms"]
        total_requests = self.metrics["total_requests"]
        if total_requests <= 1:
            self.metrics["avg_response_time_ms"] = response_time_ms
        else:
            # Exponential moving average
            alpha = 0.1
            self.metrics["avg_response_time_ms"] = (
                alpha * response_time_ms + (1 - alpha) * current_avg
            )
    async def _get_tier_health(self, tier: MemoryTier) -> dict[str, Any]:
        """Get health status for a specific tier"""
        if tier == MemoryTier.L1_CACHE:
            if self.redis_manager:
                health = await self.redis_manager.health_check()
                return {
                    "available": health.get("healthy", False),
                    "status": "healthy" if health.get("healthy") else "unhealthy",
                    "details": health,
                }
            else:
                return {"available": False, "status": "unavailable"}
        elif tier == MemoryTier.L2_SEMANTIC:
            if self.vector_manager:
                primary_db = self.tier_config[tier]["preferred_vector_db"]
                connected = self.vector_manager.test_connection(primary_db)
                return {
                    "available": connected,
                    "status": "healthy" if connected else "unhealthy",
                    "primary_db": primary_db.value,
                }
            else:
                return {"available": False, "status": "unavailable"}
        elif tier == MemoryTier.L3_PERSISTENT:
            if self.mem0_manager:
                connected = self.mem0_manager.test_connection()
                return {
                    "available": connected,
                    "status": "healthy" if connected else "unhealthy",
                }
            else:
                return {"available": False, "status": "unavailable"}
        else:
            return {"available": False, "status": "not_implemented"}
    async def _update_in_tier(self, tier: MemoryTier, entry: MemoryEntry) -> bool:
        """Update entry in specific tier"""
        try:
            if tier == MemoryTier.L1_CACHE:
                location = await self._store_l1_cache(entry)
                return location is not None
            elif tier == MemoryTier.L2_SEMANTIC:
                # Vector databases typically require delete and re-insert for updates
                await self._delete_from_tier(tier, entry.metadata.memory_id)
                location = await self._store_l2_semantic(entry)
                return location is not None
            elif tier == MemoryTier.L3_PERSISTENT:
                # Mem0 update would go here
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Failed to update in tier {tier}: {e}")
            return False
    async def _delete_from_tier(self, tier: MemoryTier, memory_id: str) -> bool:
        """Delete entry from specific tier"""
        try:
            if tier == MemoryTier.L1_CACHE:
                if self.redis_manager:
                    key = f"unified_memory:{memory_id}"
                    result = await self.redis_manager.delete(
                        key, namespace=RedisNamespaces.MEMORY
                    )
                    return result > 0
                return False
            elif tier == MemoryTier.L2_SEMANTIC:
                # Vector database deletion would require collection-specific logic
                return True
            elif tier == MemoryTier.L3_PERSISTENT:
                # Mem0 deletion would go here
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Failed to delete from tier {tier}: {e}")
            return False
# Global unified memory interface instance
unified_memory = UnifiedMemoryInterface()
# Convenience functions for common operations
async def store_memory(
    content: str,
    context: MemoryContext = MemoryContext.KNOWLEDGE,
    priority: MemoryPriority = MemoryPriority.STANDARD,
    tags: Optional[set[str]] = None,
    user_id: Optional[str] = None,
    domain: Optional[str] = None,
) -> str:
    """Store memory with simplified interface"""
    metadata = MemoryMetadata(
        context=context,
        priority=priority,
        tags=tags or set(),
        user_id=user_id,
        domain=domain,
    )
    return await unified_memory.store(content, metadata)
async def search_memory(
    query: str,
    max_results: int = 10,
    context_filter: Optional[list[MemoryContext]] = None,
    domain: Optional[str] = None,
    user_id: Optional[str] = None,
) -> list[MemorySearchResult]:
    """Search memory with simplified interface"""
    request = MemorySearchRequest(
        query=query,
        max_results=max_results,
        context_filter=context_filter,
        domain_filter=domain,
        user_filter=user_id,
    )
    return await unified_memory.search(request)
async def get_memory(memory_id: str) -> Optional[MemoryEntry]:
    """Retrieve memory by ID"""
    return await unified_memory.retrieve(memory_id)
async def update_memory(memory_id: str, content: str) -> bool:
    """Update memory content"""
    return await unified_memory.update(memory_id, content=content)
async def delete_memory(memory_id: str) -> bool:
    """Delete memory entry"""
    return await unified_memory.delete(memory_id)
