"""
Hierarchical Memory System for Sophia AI
========================================

4-Tier memory architecture with intelligent routing based on query characteristics,
domain-specific isolation, and performance optimization.

Tiers:
- L1: Redis (Hot cache, < 1ms access)
- L2: Mem0/Weaviate (Vector search, < 10ms)
- L3: Neon (Structured data, < 100ms)
- L4: S3 (Cold storage, < 1s)

AI Context:
- Intelligent query routing based on content analysis
- Domain isolation for Sophia/Artemis personas
- Integration with meta-tagging and embeddings
- Adaptive caching strategies
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, TypeVar
from uuid import uuid4

import asyncpg
import boto3
import redis.asyncio as redis
import weaviate

from app.personas.persona_manager import PersonaType
from app.scaffolding.embedding_system import EmbeddingType, EmbeddingVector

# Import existing infrastructure
from app.scaffolding.meta_tagging import MetaTag

logger = logging.getLogger(__name__)

T = TypeVar("T")


class MemoryTier(Enum):
    """Memory tier classification"""

    L1_HOT_CACHE = "l1_hot_cache"  # Redis: < 1ms, frequently accessed
    L2_VECTOR_SEARCH = "l2_vector_search"  # Weaviate/Mem0: < 10ms, semantic search
    L3_STRUCTURED = "l3_structured"  # Neon: < 100ms, complex queries
    L4_COLD_STORAGE = "l4_cold_storage"  # S3: < 1s, archival data


class QueryType(Enum):
    """Query type classification for routing"""

    EXACT_MATCH = "exact_match"  # Key-value lookups → L1
    SEMANTIC_SEARCH = "semantic_search"  # Vector similarity → L2
    ANALYTICAL = "analytical"  # Complex joins → L3
    BULK_RETRIEVAL = "bulk_retrieval"  # Large data sets → L4


class AccessPattern(Enum):
    """Access pattern for optimization"""

    HOT = "hot"  # Frequent access (< 1 hour)
    WARM = "warm"  # Regular access (< 24 hours)
    COOL = "cool"  # Occasional access (< 7 days)
    COLD = "cold"  # Rare access (> 7 days)


@dataclass
class QueryContext:
    """Context for memory query routing"""

    query_type: QueryType
    persona_domain: PersonaType
    embedding_type: Optional[EmbeddingType] = None
    meta_tags: list[MetaTag] = field(default_factory=list)
    priority: int = 5  # 1 (high) to 10 (low)
    max_latency_ms: Optional[int] = None
    expected_result_size: Optional[int] = None


@dataclass
class MemoryEntry:
    """Universal memory entry structure"""

    id: str
    content: Any
    tier: MemoryTier
    persona_domain: PersonaType
    embedding_vector: Optional[EmbeddingVector] = None
    meta_tags: list[MetaTag] = field(default_factory=list)
    access_pattern: AccessPattern = AccessPattern.COOL
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    expiry: Optional[datetime] = None
    size_bytes: Optional[int] = None


@dataclass
class QueryResult:
    """Result from hierarchical memory query"""

    entries: list[MemoryEntry]
    total_count: int
    tiers_accessed: list[MemoryTier]
    latency_ms: float
    cache_hit_ratio: float
    query_context: QueryContext


class MemoryTierAdapter:
    """Base adapter for memory tier implementations"""

    async def get(self, key: str, context: QueryContext) -> Optional[MemoryEntry]:
        """Retrieve entry by key"""
        raise NotImplementedError

    async def set(self, key: str, entry: MemoryEntry, context: QueryContext) -> bool:
        """Store entry"""
        raise NotImplementedError

    async def search(self, query: str, context: QueryContext, limit: int = 10) -> list[MemoryEntry]:
        """Search entries"""
        raise NotImplementedError

    async def delete(self, key: str, context: QueryContext) -> bool:
        """Delete entry"""
        raise NotImplementedError

    async def health_check(self) -> dict[str, Any]:
        """Check tier health"""
        raise NotImplementedError


class L1RedisAdapter(MemoryTierAdapter):
    """L1 Hot Cache using Redis"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.tier = MemoryTier.L1_HOT_CACHE

    async def connect(self):
        """Initialize Redis connection"""
        self.redis_client = redis.from_url(self.redis_url)
        await self.redis_client.ping()
        logger.info("L1 Redis adapter connected")

    async def get(self, key: str, context: QueryContext) -> Optional[MemoryEntry]:
        """Get from Redis cache"""
        if not self.redis_client:
            await self.connect()

        # Domain isolation via key prefixing
        prefixed_key = f"{context.persona_domain.value}:{key}"

        try:
            data = await self.redis_client.get(prefixed_key)
            if data:
                entry_dict = json.loads(data)
                entry = MemoryEntry(**entry_dict)

                # Update access tracking
                entry.last_accessed = datetime.utcnow()
                entry.access_count += 1

                # Re-store with updated access info
                await self.redis_client.setex(
                    prefixed_key,
                    3600,  # 1 hour TTL for hot cache
                    json.dumps(asdict(entry), default=str),
                )

                return entry
        except Exception as e:
            logger.error(f"L1 Redis get error: {e}")

        return None

    async def set(self, key: str, entry: MemoryEntry, context: QueryContext) -> bool:
        """Set in Redis cache"""
        if not self.redis_client:
            await self.connect()

        prefixed_key = f"{context.persona_domain.value}:{key}"

        try:
            # Determine TTL based on access pattern
            ttl_map = {
                AccessPattern.HOT: 3600,  # 1 hour
                AccessPattern.WARM: 1800,  # 30 minutes
                AccessPattern.COOL: 900,  # 15 minutes
                AccessPattern.COLD: 300,  # 5 minutes
            }
            ttl = ttl_map.get(entry.access_pattern, 900)

            await self.redis_client.setex(prefixed_key, ttl, json.dumps(asdict(entry), default=str))
            return True
        except Exception as e:
            logger.error(f"L1 Redis set error: {e}")
            return False

    async def search(self, query: str, context: QueryContext, limit: int = 10) -> list[MemoryEntry]:
        """Limited search via key patterns"""
        if not self.redis_client:
            await self.connect()

        try:
            pattern = f"{context.persona_domain.value}:*{query}*"
            keys = await self.redis_client.keys(pattern)

            results = []
            for key in keys[:limit]:
                data = await self.redis_client.get(key)
                if data:
                    entry_dict = json.loads(data)
                    results.append(MemoryEntry(**entry_dict))

            return results
        except Exception as e:
            logger.error(f"L1 Redis search error: {e}")
            return []

    async def delete(self, key: str, context: QueryContext) -> bool:
        """Delete from Redis"""
        if not self.redis_client:
            await self.connect()

        prefixed_key = f"{context.persona_domain.value}:{key}"

        try:
            deleted = await self.redis_client.delete(prefixed_key)
            return deleted > 0
        except Exception as e:
            logger.error(f"L1 Redis delete error: {e}")
            return False

    async def health_check(self) -> dict[str, Any]:
        """Redis health check"""
        try:
            if not self.redis_client:
                await self.connect()

            info = await self.redis_client.info("memory")
            return {
                "tier": self.tier.value,
                "status": "healthy",
                "memory_usage": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "latency_ms": 1,  # Target < 1ms
            }
        except Exception as e:
            return {"tier": self.tier.value, "status": "unhealthy", "error": str(e)}


class L2VectorAdapter(MemoryTierAdapter):
    """L2 Vector Search using Weaviate"""

    def __init__(self, weaviate_url: str = "http://localhost:8080"):
        self.weaviate_url = weaviate_url
        self.client: Optional[weaviate.Client] = None
        self.tier = MemoryTier.L2_VECTOR_SEARCH

    async def connect(self):
        """Initialize Weaviate connection"""
        self.client = weaviate.Client(self.weaviate_url)
        logger.info("L2 Weaviate adapter connected")

    async def get(self, key: str, context: QueryContext) -> Optional[MemoryEntry]:
        """Get by ID from Weaviate"""
        if not self.client:
            await self.connect()

        try:
            class_name = f"Memory_{context.persona_domain.value.title()}"

            result = self.client.data_object.get_by_id(key, class_name=class_name)

            if result:
                return self._weaviate_to_entry(result)
        except Exception as e:
            logger.error(f"L2 Weaviate get error: {e}")

        return None

    async def set(self, key: str, entry: MemoryEntry, context: QueryContext) -> bool:
        """Store in Weaviate with vector"""
        if not self.client:
            await self.connect()

        try:
            class_name = f"Memory_{context.persona_domain.value.title()}"

            # Ensure class exists
            await self._ensure_schema(class_name)

            properties = {
                "content": json.dumps(entry.content, default=str),
                "persona_domain": entry.persona_domain.value,
                "access_pattern": entry.access_pattern.value,
                "created_at": entry.created_at.isoformat(),
                "last_accessed": entry.last_accessed.isoformat(),
                "access_count": entry.access_count,
                "meta_tags": json.dumps([asdict(tag) for tag in entry.meta_tags], default=str),
            }

            vector = None
            if entry.embedding_vector:
                vector = entry.embedding_vector.vector

            self.client.data_object.create(
                data_object=properties, class_name=class_name, uuid=key, vector=vector
            )

            return True
        except Exception as e:
            logger.error(f"L2 Weaviate set error: {e}")
            return False

    async def search(self, query: str, context: QueryContext, limit: int = 10) -> list[MemoryEntry]:
        """Semantic search in Weaviate"""
        if not self.client:
            await self.connect()

        try:
            class_name = f"Memory_{context.persona_domain.value.title()}"

            # Vector search if embedding provided
            if context.embedding_type:
                result = (
                    self.client.query.get(class_name)
                    .with_near_text({"concepts": [query]})
                    .with_limit(limit)
                    .do()
                )
            else:
                # Text search fallback
                result = (
                    self.client.query.get(class_name)
                    .with_where(
                        {"path": ["content"], "operator": "Like", "valueText": f"*{query}*"}
                    )
                    .with_limit(limit)
                    .do()
                )

            entries = []
            if "data" in result and "Get" in result["data"]:
                objects = result["data"]["Get"].get(class_name, [])
                for obj in objects:
                    entries.append(self._weaviate_to_entry(obj))

            return entries
        except Exception as e:
            logger.error(f"L2 Weaviate search error: {e}")
            return []

    async def delete(self, key: str, context: QueryContext) -> bool:
        """Delete from Weaviate"""
        if not self.client:
            await self.connect()

        try:
            class_name = f"Memory_{context.persona_domain.value.title()}"
            self.client.data_object.delete(key, class_name=class_name)
            return True
        except Exception as e:
            logger.error(f"L2 Weaviate delete error: {e}")
            return False

    async def _ensure_schema(self, class_name: str):
        """Ensure Weaviate class schema exists"""
        try:
            schema = {
                "class": class_name,
                "properties": [
                    {"name": "content", "dataType": ["text"]},
                    {"name": "persona_domain", "dataType": ["string"]},
                    {"name": "access_pattern", "dataType": ["string"]},
                    {"name": "created_at", "dataType": ["string"]},
                    {"name": "last_accessed", "dataType": ["string"]},
                    {"name": "access_count", "dataType": ["int"]},
                    {"name": "meta_tags", "dataType": ["text"]},
                ],
            }

            if not self.client.schema.exists(class_name):
                self.client.schema.create_class(schema)
        except Exception as e:
            logger.error(f"Schema creation error: {e}")

    def _weaviate_to_entry(self, weaviate_obj: dict) -> MemoryEntry:
        """Convert Weaviate object to MemoryEntry"""
        props = weaviate_obj.get("properties", {})

        return MemoryEntry(
            id=weaviate_obj.get("id", str(uuid4())),
            content=json.loads(props.get("content", "{}")),
            tier=self.tier,
            persona_domain=PersonaType(props.get("persona_domain", "sophia")),
            access_pattern=AccessPattern(props.get("access_pattern", "cool")),
            created_at=datetime.fromisoformat(
                props.get("created_at", datetime.utcnow().isoformat())
            ),
            last_accessed=datetime.fromisoformat(
                props.get("last_accessed", datetime.utcnow().isoformat())
            ),
            access_count=props.get("access_count", 0),
            meta_tags=[],  # Deserialize meta_tags when needed
        )

    async def health_check(self) -> dict[str, Any]:
        """Weaviate health check"""
        try:
            if not self.client:
                await self.connect()

            meta = self.client.cluster.get_nodes_status()
            return {
                "tier": self.tier.value,
                "status": "healthy" if meta else "unhealthy",
                "nodes": len(meta) if meta else 0,
                "latency_ms": 10,  # Target < 10ms
            }
        except Exception as e:
            return {"tier": self.tier.value, "status": "unhealthy", "error": str(e)}


class L3StructuredAdapter(MemoryTierAdapter):
    """L3 Structured data using Neon PostgreSQL"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool: Optional[asyncpg.Pool] = None
        self.tier = MemoryTier.L3_STRUCTURED

    async def connect(self):
        """Initialize PostgreSQL connection pool"""
        self.pool = await asyncpg.create_pool(self.connection_string)
        await self._ensure_tables()
        logger.info("L3 Neon adapter connected")

    async def _ensure_tables(self):
        """Ensure memory tables exist"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS hierarchical_memory (
                    id TEXT PRIMARY KEY,
                    persona_domain TEXT NOT NULL,
                    content JSONB NOT NULL,
                    embedding_vector FLOAT8[],
                    meta_tags JSONB DEFAULT '[]'::jsonb,
                    access_pattern TEXT DEFAULT 'cool',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    last_accessed TIMESTAMPTZ DEFAULT NOW(),
                    access_count INTEGER DEFAULT 0,
                    expiry TIMESTAMPTZ,
                    size_bytes INTEGER,
                    tier TEXT DEFAULT 'l3_structured'
                );

                CREATE INDEX IF NOT EXISTS idx_persona_domain ON hierarchical_memory(persona_domain);
                CREATE INDEX IF NOT EXISTS idx_access_pattern ON hierarchical_memory(access_pattern);
                CREATE INDEX IF NOT EXISTS idx_last_accessed ON hierarchical_memory(last_accessed);
                CREATE INDEX IF NOT EXISTS idx_meta_tags_gin ON hierarchical_memory USING GIN(meta_tags);
                CREATE INDEX IF NOT EXISTS idx_content_gin ON hierarchical_memory USING GIN(content);
            """
            )

    async def get(self, key: str, context: QueryContext) -> Optional[MemoryEntry]:
        """Get from PostgreSQL"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM hierarchical_memory
                    WHERE id = $1 AND persona_domain = $2
                """,
                    key,
                    context.persona_domain.value,
                )

                if row:
                    # Update access tracking
                    await conn.execute(
                        """
                        UPDATE hierarchical_memory
                        SET last_accessed = NOW(), access_count = access_count + 1
                        WHERE id = $1
                    """,
                        key,
                    )

                    return self._row_to_entry(row)
            except Exception as e:
                logger.error(f"L3 Neon get error: {e}")

        return None

    async def set(self, key: str, entry: MemoryEntry, context: QueryContext) -> bool:
        """Store in PostgreSQL"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO hierarchical_memory (
                        id, persona_domain, content, embedding_vector, meta_tags,
                        access_pattern, created_at, last_accessed, access_count,
                        expiry, size_bytes, tier
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        meta_tags = EXCLUDED.meta_tags,
                        last_accessed = EXCLUDED.last_accessed,
                        access_count = EXCLUDED.access_count
                """,
                    key,
                    entry.persona_domain.value,
                    json.dumps(entry.content, default=str),
                    entry.embedding_vector.vector if entry.embedding_vector else None,
                    json.dumps([asdict(tag) for tag in entry.meta_tags], default=str),
                    entry.access_pattern.value,
                    entry.created_at,
                    entry.last_accessed,
                    entry.access_count,
                    entry.expiry,
                    entry.size_bytes,
                    entry.tier.value,
                )
                return True
            except Exception as e:
                logger.error(f"L3 Neon set error: {e}")
                return False

    async def search(self, query: str, context: QueryContext, limit: int = 10) -> list[MemoryEntry]:
        """Complex search in PostgreSQL"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            try:
                # Use full-text search on JSONB content
                rows = await conn.fetch(
                    """
                    SELECT * FROM hierarchical_memory
                    WHERE persona_domain = $1
                    AND (content::text ILIKE $2 OR meta_tags::text ILIKE $2)
                    ORDER BY last_accessed DESC
                    LIMIT $3
                """,
                    context.persona_domain.value,
                    f"%{query}%",
                    limit,
                )

                return [self._row_to_entry(row) for row in rows]
            except Exception as e:
                logger.error(f"L3 Neon search error: {e}")
                return []

    async def delete(self, key: str, context: QueryContext) -> bool:
        """Delete from PostgreSQL"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            try:
                result = await conn.execute(
                    """
                    DELETE FROM hierarchical_memory
                    WHERE id = $1 AND persona_domain = $2
                """,
                    key,
                    context.persona_domain.value,
                )
                return "DELETE 1" in result
            except Exception as e:
                logger.error(f"L3 Neon delete error: {e}")
                return False

    def _row_to_entry(self, row) -> MemoryEntry:
        """Convert database row to MemoryEntry"""
        return MemoryEntry(
            id=row["id"],
            content=json.loads(row["content"]),
            tier=MemoryTier(row["tier"]),
            persona_domain=PersonaType(row["persona_domain"]),
            access_pattern=AccessPattern(row["access_pattern"]),
            created_at=row["created_at"],
            last_accessed=row["last_accessed"],
            access_count=row["access_count"],
            expiry=row["expiry"],
            size_bytes=row["size_bytes"],
            meta_tags=[],  # Deserialize meta_tags when needed
        )

    async def health_check(self) -> dict[str, Any]:
        """PostgreSQL health check"""
        try:
            if not self.pool:
                await self.connect()

            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SELECT COUNT(*) FROM hierarchical_memory")
                return {
                    "tier": self.tier.value,
                    "status": "healthy",
                    "record_count": result,
                    "latency_ms": 100,  # Target < 100ms
                }
        except Exception as e:
            return {"tier": self.tier.value, "status": "unhealthy", "error": str(e)}


class L4ColdStorageAdapter(MemoryTierAdapter):
    """L4 Cold Storage using S3"""

    def __init__(self, bucket_name: str, aws_region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.aws_region = aws_region
        self.s3_client = boto3.client("s3", region_name=aws_region)
        self.tier = MemoryTier.L4_COLD_STORAGE

    async def get(self, key: str, context: QueryContext) -> Optional[MemoryEntry]:
        """Get from S3"""
        try:
            s3_key = f"{context.persona_domain.value}/{key}.json"

            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)

            content = response["Body"].read().decode("utf-8")
            entry_dict = json.loads(content)
            entry = MemoryEntry(**entry_dict)

            # Update access tracking (stored back to S3)
            entry.last_accessed = datetime.utcnow()
            entry.access_count += 1
            await self.set(key, entry, context)

            return entry
        except Exception as e:
            logger.error(f"L4 S3 get error: {e}")
            return None

    async def set(self, key: str, entry: MemoryEntry, context: QueryContext) -> bool:
        """Store in S3"""
        try:
            s3_key = f"{context.persona_domain.value}/{key}.json"

            # Add metadata
            metadata = {
                "persona-domain": entry.persona_domain.value,
                "access-pattern": entry.access_pattern.value,
                "tier": entry.tier.value,
                "created-at": entry.created_at.isoformat(),
                "last-accessed": entry.last_accessed.isoformat(),
            }

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json.dumps(asdict(entry), default=str),
                Metadata=metadata,
                StorageClass=(
                    "STANDARD_IA" if entry.access_pattern == AccessPattern.COLD else "STANDARD"
                ),
            )

            return True
        except Exception as e:
            logger.error(f"L4 S3 set error: {e}")
            return False

    async def search(self, query: str, context: QueryContext, limit: int = 10) -> list[MemoryEntry]:
        """Limited search in S3 via listing and filtering"""
        try:
            prefix = f"{context.persona_domain.value}/"

            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix, MaxKeys=limit * 2  # Get more to filter
            )

            entries = []
            for obj in response.get("Contents", []):
                if query.lower() in obj["Key"].lower():
                    key = obj["Key"].replace(prefix, "").replace(".json", "")
                    entry = await self.get(key, context)
                    if entry:
                        entries.append(entry)

                    if len(entries) >= limit:
                        break

            return entries
        except Exception as e:
            logger.error(f"L4 S3 search error: {e}")
            return []

    async def delete(self, key: str, context: QueryContext) -> bool:
        """Delete from S3"""
        try:
            s3_key = f"{context.persona_domain.value}/{key}.json"

            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)

            return True
        except Exception as e:
            logger.error(f"L4 S3 delete error: {e}")
            return False

    async def health_check(self) -> dict[str, Any]:
        """S3 health check"""
        try:
            # Check bucket accessibility
            self.s3_client.head_bucket(Bucket=self.bucket_name)

            # Count objects
            self.s3_client.list_objects_v2(Bucket=self.bucket_name, MaxKeys=1)

            return {
                "tier": self.tier.value,
                "status": "healthy",
                "bucket": self.bucket_name,
                "latency_ms": 1000,  # Target < 1s
            }
        except Exception as e:
            return {"tier": self.tier.value, "status": "unhealthy", "error": str(e)}


class QueryRouter:
    """Intelligent query routing based on context analysis"""

    def __init__(self):
        self.routing_rules = {
            # Exact key lookups → L1 Redis
            QueryType.EXACT_MATCH: [MemoryTier.L1_HOT_CACHE],
            # Semantic searches → L2 Vector first, then L3
            QueryType.SEMANTIC_SEARCH: [MemoryTier.L2_VECTOR_SEARCH, MemoryTier.L3_STRUCTURED],
            # Complex analytics → L3 Structured, fallback to L4
            QueryType.ANALYTICAL: [MemoryTier.L3_STRUCTURED, MemoryTier.L4_COLD_STORAGE],
            # Bulk data → L4 Cold Storage
            QueryType.BULK_RETRIEVAL: [MemoryTier.L4_COLD_STORAGE],
        }

    def route_query(self, context: QueryContext) -> list[MemoryTier]:
        """Determine which tiers to query based on context"""
        base_tiers = self.routing_rules.get(context.query_type, [])

        # Apply optimizations based on context
        optimized_tiers = []

        # High priority queries check hot cache first
        if context.priority <= 3 and MemoryTier.L1_HOT_CACHE not in base_tiers:
            optimized_tiers.append(MemoryTier.L1_HOT_CACHE)

        optimized_tiers.extend(base_tiers)

        # Latency constraints
        if context.max_latency_ms:
            if context.max_latency_ms < 10:
                # Only L1
                optimized_tiers = [MemoryTier.L1_HOT_CACHE]
            elif context.max_latency_ms < 100:
                # L1 + L2 only
                optimized_tiers = [
                    t
                    for t in optimized_tiers
                    if t in [MemoryTier.L1_HOT_CACHE, MemoryTier.L2_VECTOR_SEARCH]
                ]

        return optimized_tiers or [MemoryTier.L1_HOT_CACHE]  # Fallback

    def classify_query_type(self, query: str, context: QueryContext) -> QueryType:
        """Automatically classify query type"""
        # Simple heuristics - could be enhanced with ML
        if len(query.split()) <= 2 and not any(c in query for c in [" ", "?", "*"]):
            return QueryType.EXACT_MATCH

        if any(keyword in query.lower() for keyword in ["similar", "like", "find", "search"]):
            return QueryType.SEMANTIC_SEARCH

        if any(
            keyword in query.lower()
            for keyword in ["analyze", "aggregate", "group", "sum", "count"]
        ):
            return QueryType.ANALYTICAL

        if any(keyword in query.lower() for keyword in ["all", "bulk", "export", "download"]):
            return QueryType.BULK_RETRIEVAL

        # Default to semantic search
        return QueryType.SEMANTIC_SEARCH


class HierarchicalMemorySystem:
    """Main hierarchical memory system orchestrator"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        weaviate_url: str = "http://localhost:8080",
        neon_connection: str = "postgresql://user:pass@localhost/db",  # pragma: allowlist secret
        s3_bucket: str = "sophia-memory",
        aws_region: str = "us-east-1",
    ):
        # Initialize adapters
        self.adapters = {
            MemoryTier.L1_HOT_CACHE: L1RedisAdapter(redis_url),
            MemoryTier.L2_VECTOR_SEARCH: L2VectorAdapter(weaviate_url),
            MemoryTier.L3_STRUCTURED: L3StructuredAdapter(neon_connection),
            MemoryTier.L4_COLD_STORAGE: L4ColdStorageAdapter(s3_bucket, aws_region),
        }

        self.router = QueryRouter()
        self.metrics = {
            "queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "tier_access_counts": {tier.value: 0 for tier in MemoryTier},
        }

    async def initialize(self):
        """Initialize all tier adapters"""
        for tier, adapter in self.adapters.items():
            try:
                await adapter.connect()
                logger.info(f"Initialized {tier.value}")
            except Exception as e:
                logger.error(f"Failed to initialize {tier.value}: {e}")

    async def get(self, key: str, context: QueryContext) -> Optional[MemoryEntry]:
        """Get entry with intelligent tier routing"""
        time.time()
        self.metrics["queries"] += 1

        # Route query to appropriate tiers
        tiers_to_check = self.router.route_query(context)

        for tier in tiers_to_check:
            self.metrics["tier_access_counts"][tier.value] += 1

            adapter = self.adapters[tier]
            entry = await adapter.get(key, context)

            if entry:
                self.metrics["cache_hits"] += 1

                # Promote to higher tier if frequently accessed
                if entry.access_count > 10 and tier != MemoryTier.L1_HOT_CACHE:
                    await self._promote_entry(key, entry, context)

                return entry

        self.metrics["cache_misses"] += 1
        return None

    async def set(self, key: str, entry: MemoryEntry, context: QueryContext) -> bool:
        """Store entry in appropriate tier"""
        # Determine target tier based on access pattern
        target_tier = self._select_storage_tier(entry, context)
        entry.tier = target_tier

        adapter = self.adapters[target_tier]
        success = await adapter.set(key, entry, context)

        # Also store in L1 cache if high priority or hot access
        if target_tier != MemoryTier.L1_HOT_CACHE and (
            context.priority <= 3 or entry.access_pattern == AccessPattern.HOT
        ):
            l1_adapter = self.adapters[MemoryTier.L1_HOT_CACHE]
            await l1_adapter.set(key, entry, context)

        return success

    async def search(self, query: str, context: QueryContext, limit: int = 10) -> QueryResult:
        """Comprehensive search across tiers"""
        start_time = time.time()
        self.metrics["queries"] += 1

        # Auto-classify query type if not specified
        if not hasattr(context, "query_type") or context.query_type is None:
            context.query_type = self.router.classify_query_type(query, context)

        tiers_accessed = []
        all_entries = []
        cache_hits = 0

        # Route and search tiers
        tiers_to_search = self.router.route_query(context)

        for tier in tiers_to_search:
            tiers_accessed.append(tier)
            self.metrics["tier_access_counts"][tier.value] += 1

            adapter = self.adapters[tier]
            entries = await adapter.search(query, context, limit)

            if entries:
                cache_hits += len(entries)
                all_entries.extend(entries)

                # If we have enough results from a fast tier, stop
                if len(all_entries) >= limit and tier in [
                    MemoryTier.L1_HOT_CACHE,
                    MemoryTier.L2_VECTOR_SEARCH,
                ]:
                    break

        # Sort by relevance and access frequency
        all_entries.sort(key=lambda e: (e.access_count, e.last_accessed), reverse=True)

        latency_ms = (time.time() - start_time) * 1000
        cache_hit_ratio = cache_hits / max(1, len(all_entries))

        return QueryResult(
            entries=all_entries[:limit],
            total_count=len(all_entries),
            tiers_accessed=tiers_accessed,
            latency_ms=latency_ms,
            cache_hit_ratio=cache_hit_ratio,
            query_context=context,
        )

    async def delete(self, key: str, context: QueryContext) -> bool:
        """Delete from all tiers"""
        success_count = 0

        for adapter in self.adapters.values():
            if await adapter.delete(key, context):
                success_count += 1

        return success_count > 0

    async def health_check(self) -> dict[str, Any]:
        """Comprehensive system health check"""
        health_status = {
            "status": "healthy",
            "tiers": {},
            "metrics": self.metrics,
            "timestamp": datetime.utcnow().isoformat(),
        }

        all_healthy = True
        for tier, adapter in self.adapters.items():
            tier_health = await adapter.health_check()
            health_status["tiers"][tier.value] = tier_health

            if tier_health.get("status") != "healthy":
                all_healthy = False

        health_status["status"] = "healthy" if all_healthy else "degraded"
        return health_status

    def _select_storage_tier(self, entry: MemoryEntry, context: QueryContext) -> MemoryTier:
        """Select optimal storage tier for new entry"""
        # High-priority or hot access → L1/L2
        if context.priority <= 3 or entry.access_pattern == AccessPattern.HOT:
            return MemoryTier.L1_HOT_CACHE

        # Semantic content with embeddings → L2
        if entry.embedding_vector:
            return MemoryTier.L2_VECTOR_SEARCH

        # Structured data → L3
        if isinstance(entry.content, dict) and len(entry.content) > 5:
            return MemoryTier.L3_STRUCTURED

        # Large or cold data → L4
        if (
            entry.size_bytes and entry.size_bytes > 10000
        ) or entry.access_pattern == AccessPattern.COLD:
            return MemoryTier.L4_COLD_STORAGE

        # Default to L2
        return MemoryTier.L2_VECTOR_SEARCH

    async def _promote_entry(self, key: str, entry: MemoryEntry, context: QueryContext):
        """Promote frequently accessed entry to higher tier"""
        current_tier_index = list(MemoryTier).index(entry.tier)

        # Promote one tier up (lower index = higher tier)
        if current_tier_index > 0:
            target_tier = list(MemoryTier)[current_tier_index - 1]
            entry.tier = target_tier

            adapter = self.adapters[target_tier]
            await adapter.set(key, entry, context)

            logger.info(f"Promoted entry {key} from {entry.tier.value} to {target_tier.value}")


# Factory function for easy instantiation
async def create_hierarchical_memory(
    config: Optional[dict[str, str]] = None,
) -> HierarchicalMemorySystem:
    """Create and initialize hierarchical memory system"""

    # Default configuration
    default_config = {
        "redis_url": "redis://localhost:6379",
        "weaviate_url": "http://localhost:8080",
        "neon_connection": "postgresql://user:pass@localhost/db",
        "s3_bucket": "sophia-memory",
        "aws_region": "us-east-1",
    }

    if config:
        default_config.update(config)

    memory_system = HierarchicalMemorySystem(**default_config)
    await memory_system.initialize()

    return memory_system


# Usage Example
async def main():
    """Example usage of hierarchical memory system"""

    # Create system
    memory = await create_hierarchical_memory()

    # Create query context
    context = QueryContext(
        query_type=QueryType.SEMANTIC_SEARCH, persona_domain=PersonaType.SOPHIA, priority=5
    )

    # Store entry
    entry = MemoryEntry(
        id="test_123",
        content={"message": "Hello from Sophia", "analysis": "Business Intelligence Query"},
        tier=MemoryTier.L2_VECTOR_SEARCH,
        persona_domain=PersonaType.SOPHIA,
        access_pattern=AccessPattern.HOT,
    )

    await memory.set("test_123", entry, context)

    # Retrieve entry
    retrieved = await memory.get("test_123", context)
    print(f"Retrieved: {retrieved}")

    # Search
    results = await memory.search("business intelligence", context)
    print(f"Search results: {len(results.entries)} entries found")

    # Health check
    health = await memory.health_check()
    print(f"System status: {health['status']}")


if __name__ == "__main__":
    asyncio.run(main())
