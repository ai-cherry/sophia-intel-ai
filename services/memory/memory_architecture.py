"""
SOPHIA Intel - Memory Architecture
Stage C: Scale Safely - Memory & data consistency with multi-tenant filtering
"""
import asyncio
import json
import hashlib
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging

# Database imports (would be real in production)
try:
    import asyncpg
    import redis.asyncio as redis
    import qdrant_client
    from qdrant_client.models import Distance, VectorParams, PointStruct
    DATABASES_AVAILABLE = True
except ImportError:
    print("Database libraries not available, using mock implementations")
    DATABASES_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class MemoryEntry:
    id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]
    tenant_id: str
    session_id: str
    created_at: datetime
    updated_at: datetime
    content_type: str = "text"
    source: str = "user"
    importance: float = 1.0

@dataclass
class MemoryQuery:
    query_text: str
    tenant_id: str
    session_id: Optional[str] = None
    limit: int = 10
    similarity_threshold: float = 0.7
    content_types: Optional[List[str]] = None
    time_range: Optional[Tuple[datetime, datetime]] = None

class MemoryArchitecture:
    """
    SOPHIA Intel Memory Architecture
    - PostgreSQL: Metadata, relationships, structured data
    - Qdrant: Vector embeddings for semantic search
    - Redis: Hot cache, session state, real-time data
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.postgres_pool = None
        self.redis_client = None
        self.qdrant_client = None
        self.collection_name = "sophia_memory"
        
    async def initialize(self):
        """Initialize all database connections"""
        if not DATABASES_AVAILABLE:
            logger.warning("Database libraries not available, using mock mode")
            return
            
        try:
            # Initialize PostgreSQL
            self.postgres_pool = await asyncpg.create_pool(
                self.config.get('postgres_url'),
                min_size=2,
                max_size=10
            )
            
            # Initialize Redis
            self.redis_client = redis.from_url(
                self.config.get('redis_url', 'redis://localhost:6379'),
                decode_responses=True
            )
            
            # Initialize Qdrant
            self.qdrant_client = qdrant_client.QdrantClient(
                url=self.config.get('qdrant_url', 'http://localhost:6333'),
                api_key=self.config.get('qdrant_api_key')
            )
            
            # Ensure collection exists
            await self._ensure_collection()
            
            logger.info("Memory architecture initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize memory architecture: {e}")
            raise
    
    async def _ensure_collection(self):
        """Ensure Qdrant collection exists with proper configuration"""
        if not DATABASES_AVAILABLE:
            return
            
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # OpenAI embedding size
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to ensure Qdrant collection: {e}")
            raise
    
    async def store_memory(self, entry: MemoryEntry) -> str:
        """Store memory entry across all systems"""
        try:
            # Store in PostgreSQL (metadata)
            if self.postgres_pool:
                async with self.postgres_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO memory_entries 
                        (id, content, metadata, tenant_id, session_id, created_at, updated_at, 
                         content_type, source, importance)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        metadata = EXCLUDED.metadata,
                        updated_at = EXCLUDED.updated_at,
                        importance = EXCLUDED.importance
                    """, 
                    entry.id, entry.content, json.dumps(entry.metadata),
                    entry.tenant_id, entry.session_id, entry.created_at, 
                    entry.updated_at, entry.content_type, entry.source, entry.importance
                    )
            
            # Store in Qdrant (vectors)
            if self.qdrant_client and entry.embedding:
                point = PointStruct(
                    id=entry.id,
                    vector=entry.embedding,
                    payload={
                        "tenant_id": entry.tenant_id,
                        "session_id": entry.session_id,
                        "content_type": entry.content_type,
                        "source": entry.source,
                        "importance": entry.importance,
                        "created_at": entry.created_at.isoformat(),
                        "content_preview": entry.content[:200]  # First 200 chars for preview
                    }
                )
                
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=[point]
                )
            
            # Cache in Redis (hot data)
            if self.redis_client:
                cache_key = f"memory:{entry.tenant_id}:{entry.id}"
                cache_data = {
                    "content": entry.content,
                    "metadata": entry.metadata,
                    "session_id": entry.session_id,
                    "content_type": entry.content_type,
                    "importance": entry.importance,
                    "created_at": entry.created_at.isoformat()
                }
                
                await self.redis_client.setex(
                    cache_key, 
                    3600,  # 1 hour TTL
                    json.dumps(cache_data)
                )
            
            logger.info(f"Stored memory entry: {entry.id}")
            return entry.id
            
        except Exception as e:
            logger.error(f"Failed to store memory entry: {e}")
            raise
    
    async def query_memory(self, query: MemoryQuery) -> List[Dict[str, Any]]:
        """Query memory with multi-tenant filtering"""
        try:
            results = []
            
            # First try Redis cache for recent/hot data
            if self.redis_client:
                cache_results = await self._query_redis_cache(query)
                results.extend(cache_results)
            
            # If we need more results, query Qdrant
            remaining_limit = query.limit - len(results)
            if remaining_limit > 0 and self.qdrant_client and hasattr(query, 'query_embedding'):
                vector_results = await self._query_qdrant(query, remaining_limit)
                results.extend(vector_results)
            
            # Ensure tenant filtering (security critical)
            results = [r for r in results if r.get('tenant_id') == query.tenant_id]
            
            # Apply additional filters
            if query.session_id:
                results = [r for r in results if r.get('session_id') == query.session_id]
            
            if query.content_types:
                results = [r for r in results if r.get('content_type') in query.content_types]
            
            if query.time_range:
                start_time, end_time = query.time_range
                results = [r for r in results 
                          if start_time <= datetime.fromisoformat(r.get('created_at', '')) <= end_time]
            
            # Sort by relevance/importance
            results.sort(key=lambda x: x.get('score', 0) * x.get('importance', 1), reverse=True)
            
            return results[:query.limit]
            
        except Exception as e:
            logger.error(f"Failed to query memory: {e}")
            return []
    
    async def _query_redis_cache(self, query: MemoryQuery) -> List[Dict[str, Any]]:
        """Query Redis cache for hot data"""
        if not self.redis_client:
            return []
            
        try:
            # Get recent entries for this tenant
            pattern = f"memory:{query.tenant_id}:*"
            keys = await self.redis_client.keys(pattern)
            
            results = []
            for key in keys[:query.limit]:  # Limit Redis scan
                data = await self.redis_client.get(key)
                if data:
                    entry = json.loads(data)
                    entry['source'] = 'cache'
                    entry['score'] = 1.0  # Cache entries get high score
                    results.append(entry)
            
            return results
            
        except Exception as e:
            logger.error(f"Redis cache query failed: {e}")
            return []
    
    async def _query_qdrant(self, query: MemoryQuery, limit: int) -> List[Dict[str, Any]]:
        """Query Qdrant for vector similarity"""
        if not self.qdrant_client or not hasattr(query, 'query_embedding'):
            return []
            
        try:
            # Build filter for tenant isolation (CRITICAL for security)
            filter_conditions = {
                "must": [
                    {"key": "tenant_id", "match": {"value": query.tenant_id}}
                ]
            }
            
            if query.session_id:
                filter_conditions["must"].append({
                    "key": "session_id", 
                    "match": {"value": query.session_id}
                })
            
            if query.content_types:
                filter_conditions["must"].append({
                    "key": "content_type",
                    "match": {"any": query.content_types}
                })
            
            # Perform vector search
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query.query_embedding,
                query_filter=filter_conditions,
                limit=limit,
                score_threshold=query.similarity_threshold
            )
            
            results = []
            for result in search_results:
                entry = {
                    "id": result.id,
                    "score": result.score,
                    "source": "vector_search",
                    **result.payload
                }
                results.append(entry)
            
            return results
            
        except Exception as e:
            logger.error(f"Qdrant query failed: {e}")
            return []
    
    async def get_session_context(self, tenant_id: str, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent context for a session"""
        query = MemoryQuery(
            query_text="",
            tenant_id=tenant_id,
            session_id=session_id,
            limit=limit
        )
        
        # Get from PostgreSQL for complete session history
        if self.postgres_pool:
            try:
                async with self.postgres_pool.acquire() as conn:
                    rows = await conn.fetch("""
                        SELECT id, content, metadata, content_type, source, importance, created_at
                        FROM memory_entries 
                        WHERE tenant_id = $1 AND session_id = $2
                        ORDER BY created_at DESC
                        LIMIT $3
                    """, tenant_id, session_id, limit)
                    
                    return [dict(row) for row in rows]
                    
            except Exception as e:
                logger.error(f"Failed to get session context: {e}")
        
        return []
    
    async def cleanup_old_memories(self, retention_days: int = 90):
        """Clean up old memories based on retention policy"""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        try:
            # Clean PostgreSQL
            if self.postgres_pool:
                async with self.postgres_pool.acquire() as conn:
                    deleted_count = await conn.fetchval("""
                        DELETE FROM memory_entries 
                        WHERE created_at < $1 AND importance < 0.5
                        RETURNING COUNT(*)
                    """, cutoff_date)
                    
                    logger.info(f"Cleaned up {deleted_count} old memory entries")
            
            # Note: Qdrant cleanup would need to be coordinated with PostgreSQL
            # Redis entries expire automatically via TTL
            
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")

# Chunking utilities for memory ingestion
class MemoryChunker:
    """Chunk content for optimal memory storage (300-800 tokens)"""
    
    @staticmethod
    def chunk_text(text: str, max_tokens: int = 800, overlap_tokens: int = 100) -> List[str]:
        """Chunk text into optimal sizes for memory storage"""
        # Simple word-based chunking (in production, use proper tokenizer)
        words = text.split()
        chunks = []
        
        # Approximate tokens as words * 0.75
        max_words = int(max_tokens * 0.75)
        overlap_words = int(overlap_tokens * 0.75)
        
        for i in range(0, len(words), max_words - overlap_words):
            chunk_words = words[i:i + max_words]
            chunk = " ".join(chunk_words)
            chunks.append(chunk)
            
            if i + max_words >= len(words):
                break
        
        return chunks
    
    @staticmethod
    def create_memory_entries(
        content: str, 
        tenant_id: str, 
        session_id: str,
        source: str = "user",
        content_type: str = "text"
    ) -> List[MemoryEntry]:
        """Create memory entries from content with proper chunking"""
        chunks = MemoryChunker.chunk_text(content)
        entries = []
        
        for i, chunk in enumerate(chunks):
            entry_id = hashlib.md5(f"{tenant_id}:{session_id}:{chunk}".encode()).hexdigest()
            
            entry = MemoryEntry(
                id=entry_id,
                content=chunk,
                embedding=[],  # Would be generated by embedding service
                metadata={
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "original_length": len(content)
                },
                tenant_id=tenant_id,
                session_id=session_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                content_type=content_type,
                source=source,
                importance=1.0
            )
            
            entries.append(entry)
        
        return entries

# Global memory architecture instance
memory_architecture = None

async def get_memory_architecture() -> MemoryArchitecture:
    """Get or create global memory architecture instance"""
    global memory_architecture
    
    if memory_architecture is None:
        config = {
            'postgres_url': os.environ.get('POSTGRES_URL'),
            'redis_url': os.environ.get('REDIS_URL', 'redis://localhost:6379'),
            'qdrant_url': os.environ.get('QDRANT_URL', 'http://localhost:6333'),
            'qdrant_api_key': os.environ.get('QDRANT_API_KEY')
        }
        
        memory_architecture = MemoryArchitecture(config)
        await memory_architecture.initialize()
    
    return memory_architecture

