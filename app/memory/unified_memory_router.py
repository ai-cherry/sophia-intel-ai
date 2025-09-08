"""
Unified Memory Router - Multi-tiered Memory Architecture
Coordinates Redis (L1), Weaviate/Milvus (L2), Neon (L3), and S3 (L4)
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# Optional imports for different storage backends
try:
    import aioboto3

    HAS_S3 = True
except ImportError:
    HAS_S3 = False

try:
    import asyncpg

    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

try:
    import redis.asyncio as aioredis

    HAS_REDIS = True
except ImportError:
    import redis as aioredis  # Fallback to sync redis

    HAS_REDIS = True

try:
    import weaviate
    from weaviate.auth import AuthApiKey

    HAS_WEAVIATE = True
except ImportError:
    HAS_WEAVIATE = False

try:
    from mem0 import Memory

    HAS_MEM0 = True
except ImportError:
    HAS_MEM0 = False

import yaml

from app.core.portkey_manager import TaskType, get_portkey_manager
from app.core.secrets_manager import get_secret

logger = logging.getLogger(__name__)


class MemoryDomain(Enum):
    """Memory domains for isolation"""

    SOPHIA = "sophia"  # Business Intelligence
    ARTEMIS = "artemis"  # Coding Excellence
    SHARED = "shared"  # Cross-domain knowledge


class MemoryTier(Enum):
    """Memory storage tiers"""

    L1_EPHEMERAL = "L1"  # Redis/Mem0 - Hot cache
    L2_VECTOR = "L2"  # Weaviate/Milvus - Semantic
    L3_STRUCTURED = "L3"  # Neon PostgreSQL - Facts
    L4_COLD = "L4"  # S3/GCS - Archives


@dataclass
class DocChunk:
    """Document chunk for vector storage"""

    content: str
    source_uri: str
    domain: MemoryDomain
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: Optional[list[float]] = None
    chunk_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0


@dataclass
class SearchHit:
    """Search result"""

    content: str
    score: float
    source_uri: str
    metadata: dict[str, Any]
    tier: MemoryTier
    domain: MemoryDomain


@dataclass
class UpsertReport:
    """Report from upsert operation"""

    success: bool
    chunks_processed: int
    chunks_stored: int
    duplicates_found: int
    errors: list[str]
    tier: MemoryTier


@dataclass
class AuditReport:
    """Memory audit report"""

    orphans: list[str]
    duplicates: list[str]
    pii_violations: list[str]
    total_chunks: int
    total_size_bytes: int


@dataclass
class PurgeReport:
    """Purge operation report"""

    purged: dict[str, int]
    success: bool
    errors: list[str]


class MemoryMetrics:
    """Track memory system performance"""

    def __init__(self):
        self.operations = {
            "reads": 0,
            "writes": 0,
            "searches": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }
        self.latencies = []

    def record_read(self, tier: str, cache_hit: bool):
        self.operations["reads"] += 1
        if cache_hit:
            self.operations["cache_hits"] += 1
        else:
            self.operations["cache_misses"] += 1

    def record_write(self, tier: str, size: int):
        self.operations["writes"] += 1

    def record_search(self, tier: str, results: int):
        self.operations["searches"] += 1

    def record_upsert(self, tier: str, chunks: int):
        self.operations["writes"] += chunks

    def get_cache_hit_rate(self) -> float:
        total = self.operations["cache_hits"] + self.operations["cache_misses"]
        if total == 0:
            return 0.0
        return self.operations["cache_hits"] / total


class UnifiedMemoryRouter:
    """
    Unified memory interface for all agents.
    Routes operations to appropriate storage tiers based on policy.
    """

    def __init__(self, policy_path: Optional[Path] = None):
        """
        Initialize memory router

        Args:
            policy_path: Path to memory policy YAML file
        """
        self.policy_path = policy_path or Path("app/memory/policy.yaml")
        self.policy = self._load_policy()
        self.metrics = MemoryMetrics()

        # Initialize adapters (lazy loading)
        self._redis = None
        self._mem0 = None
        self._weaviate = None
        self._neon = None
        self._s3 = None

        # Caching
        self._cache = {}
        self._embedding_cache = {}

        # Portkey manager for embeddings
        self.portkey = get_portkey_manager()

    def _load_policy(self) -> dict[str, Any]:
        """Load memory policy configuration"""
        if self.policy_path.exists():
            with open(self.policy_path) as f:
                return yaml.safe_load(f)
        else:
            return self._get_default_policy()

    def _get_default_policy(self) -> dict[str, Any]:
        """Get default memory policy"""
        return {
            "namespaces": {
                "sophia": {
                    "patterns": ["sophia/*", "bi/*", "sales/*"],
                    "isolation": "strict",
                    "cross_read": ["shared/*"],
                },
                "artemis": {
                    "patterns": ["artemis/*", "code/*", "tech/*"],
                    "isolation": "strict",
                    "cross_read": ["shared/*"],
                },
                "shared": {
                    "patterns": ["shared/*", "company/*"],
                    "isolation": "none",
                    "cross_read": ["*"],
                },
            },
            "tiers": {
                "L1_ephemeral": {"primary": "redis", "ttl_default": 3600},
                "L2_vector": {"primary": "weaviate", "hybrid_alpha": 0.65},
                "L3_structured": {"primary": "neon"},
                "L4_cold": {"primary": "s3"},
            },
            "performance": {
                "batch_sizes": {"embedding": 32, "upsert": 100, "search": 10},
                "cache": {"search_ttl": 300, "fact_ttl": 3600, "embedding_ttl": 86400},
            },
        }

    # ========== L1: Ephemeral Operations ==========

    async def put_ephemeral(self, key: str, value: Any, ttl_s: int = 3600) -> None:
        """Store in fast cache with TTL"""
        redis = await self._get_redis()

        # Serialize value
        serialized = json.dumps(value) if not isinstance(value, (str, bytes)) else value

        # Store with TTL
        await redis.set(key, serialized, ex=ttl_s)

        # Update local cache
        self._cache[key] = (value, datetime.now() + timedelta(seconds=ttl_s))

        self.metrics.record_write("L1", len(str(serialized)))

    async def get_ephemeral(self, key: str) -> Optional[Any]:
        """Retrieve from fast cache"""
        # Check local cache first
        if key in self._cache:
            value, expiry = self._cache[key]
            if datetime.now() < expiry:
                self.metrics.record_read("L1", cache_hit=True)
                return value
            else:
                del self._cache[key]

        # Check Redis
        redis = await self._get_redis()
        value = await redis.get(key)

        if value:
            try:
                deserialized = json.loads(value) if isinstance(value, bytes) else value
                self._cache[key] = (
                    deserialized,
                    datetime.now() + timedelta(seconds=300),
                )
                self.metrics.record_read("L1", cache_hit=True)
                return deserialized
            except Exception:self.metrics.record_read("L1", cache_hit=True)
                return value

        self.metrics.record_read("L1", cache_hit=False)
        return None

    # ========== L2: Vector Operations ==========

    async def upsert_chunks(
        self, chunks: list[DocChunk], domain: MemoryDomain
    ) -> UpsertReport:
        """Store document chunks with embeddings"""
        report = UpsertReport(
            success=False,
            chunks_processed=0,
            chunks_stored=0,
            duplicates_found=0,
            errors=[],
            tier=MemoryTier.L2_VECTOR,
        )

        try:
            # Deduplication
            unique_chunks = await self._deduplicate(chunks)
            report.duplicates_found = len(chunks) - len(unique_chunks)

            # Batch embedding
            embedded_chunks = await self._batch_embed(unique_chunks)

            # Get Weaviate client
            weaviate_client = await self._get_weaviate()
            if weaviate_client is None:
                report.errors.append("Weaviate unavailable; skipping L2 upsert")
                logger.warning(
                    "L2 upsert fallback: Weaviate unavailable; skipping upsert"
                )
                return report

            # Ensure schema (DocChunk class) exists when using local/unauth Weaviate
            try:
                self._ensure_weaviate_schema(weaviate_client)
            except Exception as e:
                logger.warning(f"Schema bootstrap skipped/failed: {e}")

            # Prepare batch
            batch = []
            from datetime import timezone

            for chunk in embedded_chunks:
                # Ensure RFC3339 timestamp with 'Z' (UTC) suffix for Weaviate
                try:
                    dt = chunk.timestamp
                    if getattr(dt, "tzinfo", None) is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    else:
                        dt = dt.astimezone(timezone.utc)
                    ts = dt.isoformat().replace("+00:00", "Z")
                except Exception:
                    # Fallback to current UTC time if anything goes wrong
                    from datetime import datetime
                    from datetime import timezone as _tz

                    ts = datetime.now(_tz.utc).isoformat().replace("+00:00", "Z")
                data_object = {
                    "content": chunk.content,
                    "source_uri": chunk.source_uri,
                    "domain": domain.value,
                    "timestamp": ts,
                    "confidence": chunk.confidence,
                    "metadata": json.dumps(chunk.metadata),
                }

                batch.append(
                    {
                        "class": "DocChunk",
                        "properties": data_object,
                        "vector": chunk.embedding,
                    }
                )

            # Batch upsert
            weaviate_client.batch.configure(
                batch_size=self.policy["performance"]["batch_sizes"]["upsert"]
            )

            with weaviate_client.batch as batch_writer:
                for item in batch:
                    batch_writer.add_data_object(
                        data_object=item["properties"],
                        class_name=item["class"],
                        vector=item["vector"],
                    )
                    report.chunks_stored += 1

            report.chunks_processed = len(unique_chunks)
            report.success = True

            # Record lineage in L3
            await self._record_lineage(domain, unique_chunks)

            self.metrics.record_upsert("L2", len(unique_chunks))

        except Exception as e:
            report.errors.append(str(e))
            logger.error(f"Upsert failed: {e}")

        return report

    def _ensure_weaviate_schema(self, client) -> None:
        """Best-effort schema bootstrap for local Weaviate.

        - If class DocChunk missing and WEAVIATE_AUTO_BOOTSTRAP is not disabled,
          create class with vectorizer='none'.
        - No-op for remote/authenticated clouds to avoid surprises.
        """
        import os

        try:
            # Detect local URL and no API key
            url = os.getenv("WEAVIATE_URL", "http://localhost:8081")
            is_local = url.startswith("http://localhost") or url.startswith(
                "http://127.0.0.1"
            )
            if os.getenv("WEAVIATE_AUTO_BOOTSTRAP", "true").lower() not in {
                "1",
                "true",
                "yes",
            }:
                return
            # If cloud (https) and API key present, skip auto-bootstrap
            if url.startswith("https://") and os.getenv("WEAVIATE_API_KEY"):
                return
            # Read schema
            schema = client.schema.get()
            classes = [c.get("class") for c in schema.get("classes", [])]
            if any(c == "DocChunk" for c in classes):
                return
            # Create DocChunk class
            body = {
                "class": "DocChunk",
                "vectorizer": "none",
                "properties": [
                    {"name": "content", "dataType": ["text"]},
                    {"name": "source_uri", "dataType": ["text"]},
                    {"name": "domain", "dataType": ["text"]},
                    {"name": "timestamp", "dataType": ["date"]},
                    {"name": "confidence", "dataType": ["number"]},
                    {"name": "metadata", "dataType": ["text"]},
                ],
            }
            client.schema.create_class(body)
            logger.info("Weaviate: auto-created DocChunk class")
        except Exception as e:
            # Don't block upserts; just log
            logger.debug(f"Weaviate schema ensure skipped: {e}")

    async def search(
        self,
        query: str,
        domain: MemoryDomain,
        k: int = 12,
        alpha: float = 0.65,
        filters: Optional[dict] = None,
        rerank: bool = False,
    ) -> list[SearchHit]:
        """Hybrid search with optional reranking"""

        # Check cache first
        cache_key = self._hash_query(query, domain, filters)
        cached = await self.get_ephemeral(f"search:{cache_key}")
        if cached:
            try:
                obj = cached
                if isinstance(cached, str):
                    obj = json.loads(cached)
                if isinstance(obj, list) and obj and isinstance(obj[0], dict):
                    return [
                        SearchHit(
                            content=it.get("content", ""),
                            score=float(it.get("score", 0.0)),
                            source_uri=it.get("source_uri", ""),
                            metadata=it.get("metadata", {}) or {},
                            tier=MemoryTier(it.get("tier", MemoryTier.L2_VECTOR.value)),
                            domain=MemoryDomain(
                                it.get("domain", MemoryDomain.SHARED.value)
                            ),
                        )
                        for it in obj
                    ]
                # If already a list[SearchHit], just return
                if isinstance(obj, list) and (not obj or isinstance(obj[0], SearchHit)):
                    return obj
            except Exception:
                # Ignore cache parse errors
                pass

        # Get Weaviate client
        weaviate_client = await self._get_weaviate()
        if weaviate_client is None:
            logger.warning(
                "L2 search fallback: Weaviate unavailable; returning no results"
            )
            return []

        # Build query
        query_builder = (
            weaviate_client.query.get(
                "DocChunk",
                ["content", "source_uri", "domain", "confidence", "metadata"],
            )
            .with_hybrid(query=query, alpha=alpha)
            .with_limit(k * 2 if rerank else k)
        )

        # Add filters
        if filters or domain != MemoryDomain.SHARED:
            where_filter = {
                "path": ["domain"],
                "operator": "Equal",
                "valueString": domain.value,
            }
            query_builder = query_builder.with_where(where_filter)

        # Execute search
        results = query_builder.do()

        # Convert to SearchHits
        hits: list[SearchHit] = []
        try:
            doc_items = (results or {}).get("data", {}).get("Get", {}).get(
                "DocChunk"
            ) or []
        except Exception:
            doc_items = []

        for item in doc_items:
            hit = SearchHit(
                content=item["content"],
                score=(item.get("_additional", {}) or {}).get("score", 0.0),
                source_uri=item["source_uri"],
                metadata=json.loads(item.get("metadata", "{}")),
                tier=MemoryTier.L2_VECTOR,
                domain=MemoryDomain(item["domain"]),
            )
            hits.append(hit)

        # Optional reranking
        if rerank and len(hits) > 5:
            hits = await self._rerank(query, hits[:20])[:k]
        else:
            hits = hits[:k]

        # Cache results in a JSON-friendly form
        serializable_hits = [
            {
                "content": h.content,
                "score": h.score,
                "source_uri": h.source_uri,
                "metadata": h.metadata,
                "tier": h.tier.value,
                "domain": h.domain.value,
            }
            for h in hits
        ]
        await self.put_ephemeral(
            f"search:{cache_key}",
            json.dumps(serializable_hits),
            ttl_s=self.policy["performance"]["cache"]["search_ttl"],
        )

        self.metrics.record_search("L2", len(hits))
        return hits

    # ========== L3: Structured Operations ==========

    async def record_fact(self, table: str, data: dict[str, Any]) -> str:
        """Store structured fact in PostgreSQL"""
        conn = await self._get_neon()
        if not conn:
            logger.warning("Structured store (Neon) unavailable; skipping record_fact")
            # Return a deterministic id without DB storage
            fact_id = hashlib.sha256(
                json.dumps(data, sort_keys=True).encode()
            ).hexdigest()[:16]
            return fact_id

        # Generate fact ID
        fact_id = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[
            :16
        ]

        # Prepare insert query
        columns = ", ".join(data.keys())
        placeholders = ", ".join([f"${i+1}" for i in range(len(data))])
        query = f"""
            INSERT INTO {table} (fact_id, {columns}, created_at)
            VALUES ('{fact_id}', {placeholders}, NOW())
            ON CONFLICT (fact_id) DO NOTHING
            RETURNING fact_id
        """

        # Execute insert
        async with conn.transaction():
            result = await conn.fetchval(query, *data.values())

        self.metrics.record_write("L3", 1)
        return result or fact_id

    async def query_facts(self, sql: str, params: dict = None) -> list[dict]:
        """Query structured data"""
        conn = await self._get_neon()

        # Execute query
        if params:
            rows = await conn.fetch(sql, *params.values())
        else:
            rows = await conn.fetch(sql)

        # Convert to dicts
        results = [dict(row) for row in rows]

        self.metrics.record_read("L3", len(results) > 0)
        return results

    # ========== L4: Cold Storage Operations ==========

    async def archive(self, key: str, data: bytes, metadata: dict = None) -> str:
        """Store in cold storage (S3)"""
        if not HAS_S3:
            logger.warning("S3 not available, skipping archive")
            return key

        session = aioboto3.Session()

        async with session.client(
            "s3",
            region_name=get_secret("AWS_REGION"),
            aws_access_key_id=get_secret("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=get_secret("AWS_SECRET_ACCESS_KEY"),
        ) as s3:
            bucket = get_secret("S3_BUCKET", "sophia-intel-archive")

            # Add metadata
            s3_metadata = metadata or {}
            s3_metadata["timestamp"] = datetime.now().isoformat()

            # Upload to S3
            await s3.put_object(Bucket=bucket, Key=key, Body=data, Metadata=s3_metadata)

            uri = f"s3://{bucket}/{key}"

            self.metrics.record_write("L4", len(data))
            return uri

    # ========== Helper Methods ==========

    async def _get_redis(self) -> aioredis.Redis:
        """Get or create Redis connection"""
        if self._redis is None:
            redis_url = get_secret("REDIS_URL", "redis://localhost:6379")
            self._redis = await aioredis.from_url(
                redis_url, encoding="utf-8", decode_responses=True
            )
        return self._redis

    async def _get_weaviate(self):
        """Get or create Weaviate client"""
        if not HAS_WEAVIATE:
            logger.warning("Weaviate not available")
            return None

        if self._weaviate is None:
            url = get_secret("WEAVIATE_URL", "http://localhost:8080")
            api_key = get_secret("WEAVIATE_API_KEY")

            if api_key:
                auth = AuthApiKey(api_key)
                self._weaviate = weaviate.Client(url=url, auth_client_secret=auth)
            else:
                self._weaviate = weaviate.Client(url=url)

        return self._weaviate

    async def _get_neon(self):
        """Get or create Neon PostgreSQL connection"""
        if not HAS_POSTGRES:
            logger.warning("PostgreSQL not available")
            return None

        if self._neon is None:
            dsn = get_secret("NEON_DATABASE_URL")
            if not dsn:
                dsn = get_secret("POSTGRES_URL", "postgresql://localhost/sophia")

            self._neon = await asyncpg.connect(dsn)

        return self._neon

    async def _get_mem0(self):
        """Get or create Mem0 client"""
        if not HAS_MEM0:
            logger.warning("Mem0 not available")
            return None

        if self._mem0 is None:
            api_key = get_secret("MEM0_API_KEY")
            organization = get_secret("MEM0_ORG")

            if api_key:
                self._mem0 = Memory(api_key=api_key, org_id=organization)
            else:
                # Use local memory
                self._mem0 = Memory()

        return self._mem0

    async def _deduplicate(self, chunks: list[DocChunk]) -> list[DocChunk]:
        """Remove duplicate chunks"""
        seen = set()
        unique = []

        for chunk in chunks:
            # Create hash of content
            chunk_hash = hashlib.sha256(chunk.content.encode()).hexdigest()
            if chunk_hash not in seen:
                seen.add(chunk_hash)
                unique.append(chunk)

        return unique

    async def _batch_embed(self, chunks: list[DocChunk]) -> list[DocChunk]:
        """Generate embeddings for chunks in batches"""
        batch_size = self.policy["performance"]["batch_sizes"]["embedding"]

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [chunk.content for chunk in batch]

            # Check embedding cache
            embeddings = []
            texts_to_embed = []
            cache_indices = []

            for idx, text in enumerate(texts):
                text_hash = hashlib.sha256(text.encode()).hexdigest()
                if text_hash in self._embedding_cache:
                    embeddings.append(self._embedding_cache[text_hash])
                else:
                    texts_to_embed.append(text)
                    cache_indices.append(idx)
                    embeddings.append(None)

            # Generate new embeddings
            if texts_to_embed:
                try:
                    new_embeddings = await self.portkey.embed_texts(texts_to_embed)
                    # Ensure pure python floats
                    new_embeddings = [
                        [float(x) for x in (emb or [])]
                        for emb in (new_embeddings or [])
                    ]
                except Exception as e:
                    logger.error(f"Embedding generation failed: {e}")
                    new_embeddings = []

                # Update cache and results
                for idx, embedding in zip(cache_indices, new_embeddings):
                    text_hash = hashlib.sha256(texts[idx].encode()).hexdigest()
                    self._embedding_cache[text_hash] = embedding
                    embeddings[idx] = embedding

            # Update chunks with embeddings
            for chunk, embedding in zip(batch, embeddings):
                chunk.embedding = embedding

        return chunks

    async def _rerank(self, query: str, hits: list[SearchHit]) -> list[SearchHit]:
        """Rerank search results using cross-encoder"""
        # Use Portkey for reranking
        documents = [hit.content for hit in hits]

        # Call reranking model
        await self.portkey.execute_with_fallback(
            task_type=TaskType.RERANKING,
            messages=[{"role": "user", "content": query}],
            documents=documents,
        )

        # Sort by new scores
        # (Implementation would depend on actual reranking API)
        return sorted(hits, key=lambda x: x.score, reverse=True)

    def _hash_query(
        self, query: str, domain: MemoryDomain, filters: Optional[dict]
    ) -> str:
        """Create hash key for query caching"""
        key_parts = [query, domain.value]
        if filters:
            key_parts.append(json.dumps(filters, sort_keys=True))

        combined = "|".join(key_parts)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    async def _record_lineage(
        self, domain: MemoryDomain, chunks: list[DocChunk]
    ) -> None:
        """Record chunk lineage in L3"""
        conn = await self._get_neon()

        # Create lineage records
        for chunk in chunks:
            await conn.execute(
                """
                INSERT INTO chunk_lineage (
                    chunk_id, source_uri, domain, created_at
                ) VALUES ($1, $2, $3, NOW())
                ON CONFLICT (chunk_id) DO NOTHING
            """,
                chunk.chunk_id,
                chunk.source_uri,
                domain.value,
            )

    async def close(self) -> None:
        """Clean up connections"""
        if self._redis:
            await self._redis.close()
        if self._neon:
            await self._neon.close()

    # ========== Audit & Management ==========

    async def audit(self, namespace: str = "*", fix: bool = False) -> AuditReport:
        """Audit memory for issues"""
        report = AuditReport(
            orphans=[],
            duplicates=[],
            pii_violations=[],
            total_chunks=0,
            total_size_bytes=0,
        )

        # Implementation would check for:
        # - Orphaned chunks without sources
        # - Duplicate content
        # - PII violations using presidio or similar

        return report

    async def purge(self, source_uri: str, hard: bool = False) -> PurgeReport:
        """Remove data from all tiers"""
        report = PurgeReport(
            purged={"L1": 0, "L2": 0, "L3": 0, "L4": 0}, success=True, errors=[]
        )

        # Purge from each tier
        # Implementation would delete from Redis, Weaviate, Neon, S3

        return report


# Global instance
_memory_router = None


def get_memory_router() -> UnifiedMemoryRouter:
    """Get global memory router instance"""
    global _memory_router
    if _memory_router is None:
        _memory_router = UnifiedMemoryRouter()
    return _memory_router
