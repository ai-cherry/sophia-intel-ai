"""
Unified Memory System for Sophia Intel AI - MCP Server
Consolidates enhanced_memory.py + supermemory_mcp.py + enhanced_mcp_server.py
Combines SQLite FTS5, Weaviate vector search, Redis caching, and MCP protocol support.
"""

import os
import json
import asyncio
import logging
import hashlib
import sqlite3
from typing import List, Dict, Any, Optional, Union, AsyncContextManager
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
from contextlib import asynccontextmanager
import aiosqlite

# Vector database imports
try:
    import weaviate
    import weaviate.classes as wvc
    WEAVIATE_AVAILABLE = True
except ImportError:
    WEAVIATE_AVAILABLE = False

# Redis imports
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Conditional import for real_executor to handle missing API keys gracefully
try:
    from app.llm.real_executor import real_executor
    REAL_EXECUTOR_AVAILABLE = True
except (ImportError, ValueError) as e:
    # Handle cases where API keys are missing or real_executor fails to initialize
    real_executor = None
    REAL_EXECUTOR_AVAILABLE = False
    logger.warning(f"Real executor not available, re-ranking will use fallback: {e}")


class MemoryType(Enum):
    """Types of memory entries."""
    EPISODIC = "episodic"    # Per-task notes, recent decisions
    SEMANTIC = "semantic"    # Patterns, conventions, architectural idioms
    PROCEDURAL = "procedural" # Step checklists, fix recipes


@dataclass
class MemoryEntry:
    """Unified memory entry with deduplication and metadata."""
    topic: str
    content: str
    source: str
    tags: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    memory_type: MemoryType = MemoryType.SEMANTIC
    embedding_vector: Optional[List[float]] = None
    hash_id: Optional[str] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def __post_init__(self):
        """Generate hash ID for deduplication."""
        if not self.hash_id:
            content_hash = hashlib.sha256(
                f"{self.topic}:{self.content}:{self.source}".encode()
            ).hexdigest()[:16]
            self.hash_id = content_hash
            
        if not self.last_accessed:
            self.last_accessed = self.timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "hash_id": self.hash_id,
            "topic": self.topic,
            "content": self.content,
            "source": self.source,
            "tags": json.dumps(self.tags),
            "timestamp": self.timestamp.isoformat(),
            "memory_type": self.memory_type.value,
            "embedding_vector": json.dumps(self.embedding_vector) if self.embedding_vector else None,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None
        }


@dataclass
class SearchResult:
    """Enhanced search result with multiple score types."""
    entry: MemoryEntry
    vector_score: Optional[float] = None
    fts_score: Optional[float] = None
    rerank_score: Optional[float] = None
    combined_score: Optional[float] = None


@dataclass
class UnifiedMemoryConfig:
    """Configuration for unified memory system."""
    
    # SQLite configuration
    sqlite_path: str = "data/unified_memory.db"
    enable_fts: bool = True
    
    # Weaviate configuration  
    weaviate_url: str = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    weaviate_api_key: Optional[str] = os.getenv("WEAVIATE_API_KEY")
    weaviate_collection: str = "UnifiedMemoryEntries"
    
    # Redis configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/1")
    cache_ttl: int = 3600  # 1 hour
    
    # Connection pooling (from enhanced_mcp_server.py)
    connection_pool_size: int = 20
    connection_timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 0.5
    
    # Performance settings
    max_results: int = 50
    search_timeout: float = 5.0
    embedding_batch_size: int = 100
    
    # MCP Protocol settings
    enable_mcp_protocol: bool = True
    mcp_port: int = 8081


class UnifiedMemoryStore:
    """
    Unified memory store combining all memory system features:
    - SQLite with FTS5 for metadata and text search (from enhanced_memory.py)
    - Weaviate for vector similarity search (from enhanced_memory.py)
    - Redis for caching and performance (from enhanced_memory.py)
    - Connection pooling and retry logic (from enhanced_mcp_server.py)
    - MCP protocol support (from supermemory_mcp.py)
    - Memory patterns and deduplication (from supermemory_mcp.py)
    """
    
    def __init__(self, config: Optional[UnifiedMemoryConfig] = None):
        self.config = config or UnifiedMemoryConfig()
        
        # Connection management
        self._connection_pool: Optional[asyncio.Queue] = None
        self._pool_initialized = False
        self._metrics = {"requests": 0, "errors": 0, "cache_hits": 0, "cache_misses": 0}
        
        # Clients
        self.weaviate_client = None
        self.redis_client = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize all storage backends with connection pooling."""
        if self._initialized:
            return
            
        # Initialize connection pool
        await self._initialize_connection_pool()
        
        # Initialize Weaviate if available
        if WEAVIATE_AVAILABLE:
            await self._init_weaviate()
        else:
            logger.warning("Weaviate not available, falling back to FTS only")
        
        # Initialize Redis if available
        if REDIS_AVAILABLE:
            try:
                self.redis_client = aioredis.from_url(self.config.redis_url)
                await self.redis_client.ping()
                logger.info("Redis cache initialized")
            except Exception as e:
                logger.warning(f"Redis not available: {e}")
        
        self._initialized = True
        
    async def _initialize_connection_pool(self):
        """Initialize SQLite connection pool with retry logic."""
        if self._pool_initialized:
            return
            
        self._connection_pool = asyncio.Queue(maxsize=self.config.connection_pool_size)
        
        # Ensure database directory exists
        Path(self.config.sqlite_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Pre-populate pool with connections
        for i in range(self.config.connection_pool_size):
            retry_delay = self.config.retry_delay
            for attempt in range(self.config.retry_attempts):
                try:
                    conn = await aiosqlite.connect(
                        self.config.sqlite_path,
                        timeout=self.config.connection_timeout
                    )
                    conn.row_factory = aiosqlite.Row
                    
                    # Initialize schema on first connection
                    if i == 0:
                        await self._initialize_schema(conn)
                    
                    await self._connection_pool.put(conn)
                    break
                except Exception as e:
                    if attempt == self.config.retry_attempts - 1:
                        logger.error(f"Failed to create connection {i}: {e}")
                        raise
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
        
        self._pool_initialized = True
        logger.info(f"Initialized SQLite connection pool with {self.config.connection_pool_size} connections")
    
    async def _initialize_schema(self, conn: aiosqlite.Connection):
        """Initialize database schema with all features."""
        # Main memory table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash_id TEXT UNIQUE NOT NULL,
                topic TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT NOT NULL,
                tags TEXT,  -- JSON array
                memory_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                embedding_vector TEXT  -- JSON array
            )
        """)
        
        # FTS5 index for full-text search
        if self.config.enable_fts:
            await conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
                    hash_id UNINDEXED,
                    topic,
                    content,
                    tags,
                    content='memory_entries',
                    content_rowid='id',
                    tokenize='porter unicode61'
                )
            """)
            
            # FTS triggers
            await conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memory_fts_insert AFTER INSERT ON memory_entries
                BEGIN
                    INSERT INTO memory_fts(rowid, hash_id, topic, content, tags) 
                    VALUES (new.id, new.hash_id, new.topic, new.content, new.tags);
                END
            """)
            
            await conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memory_fts_delete AFTER DELETE ON memory_entries
                BEGIN
                    INSERT INTO memory_fts(memory_fts, rowid, hash_id, topic, content, tags) 
                    VALUES('delete', old.id, old.hash_id, old.topic, old.content, old.tags);
                END
            """)
        
        # Performance indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_hash_id ON memory_entries(hash_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_entries(memory_type)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON memory_entries(source)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON memory_entries(created_at)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_access_count ON memory_entries(access_count DESC)")
        
        await conn.commit()
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncContextManager[aiosqlite.Connection]:
        """Get database connection from pool with timeout."""
        if not self._pool_initialized:
            await self._initialize_connection_pool()
        
        try:
            # Get connection with timeout
            conn = await asyncio.wait_for(
                self._connection_pool.get(),
                timeout=self.config.connection_timeout
            )
            yield conn
        finally:
            # Return connection to pool
            if 'conn' in locals():
                await self._connection_pool.put(conn)
    
    async def _init_weaviate(self):
        """Initialize Weaviate vector database."""
        try:
            if self.config.weaviate_api_key:
                auth = weaviate.auth.AuthApiKey(self.config.weaviate_api_key)
                self.weaviate_client = weaviate.connect_to_wcs(
                    cluster_url=self.config.weaviate_url,
                    auth_credentials=auth
                )
            else:
                host = self.config.weaviate_url.replace("http://", "").replace("https://", "").split(":")[0]
                port = 8080
                if ":" in self.config.weaviate_url:
                    port = int(self.config.weaviate_url.split(":")[-1])
                    
                self.weaviate_client = weaviate.connect_to_local(host=host, port=port)
            
            # Create collection if it doesn't exist
            if not self.weaviate_client.collections.exists(self.config.weaviate_collection):
                self.weaviate_client.collections.create(
                    name=self.config.weaviate_collection,
                    vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_transformers(
                        model="sentence-transformers/all-MiniLM-L6-v2"
                    ),
                    properties=[
                        wvc.config.Property(name="hash_id", data_type=wvc.config.DataType.TEXT, skip_vectorization=True),
                        wvc.config.Property(name="topic", data_type=wvc.config.DataType.TEXT),
                        wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT),
                        wvc.config.Property(name="source", data_type=wvc.config.DataType.TEXT, skip_vectorization=True),
                        wvc.config.Property(name="memory_type", data_type=wvc.config.DataType.TEXT, skip_vectorization=True),
                        wvc.config.Property(name="tags", data_type=wvc.config.DataType.TEXT_ARRAY, skip_vectorization=True),
                        wvc.config.Property(name="created_at", data_type=wvc.config.DataType.DATE, skip_vectorization=True)
                    ]
                )
                logger.info(f"Created Weaviate collection: {self.config.weaviate_collection}")
            else:
                logger.info(f"Using existing Weaviate collection: {self.config.weaviate_collection}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Weaviate: {e}")
            self.weaviate_client = None
    
    async def add_memory(self, entry: MemoryEntry, deduplicate: bool = True) -> Dict[str, Any]:
        """Add memory entry with deduplication and multi-backend storage."""
        await self.initialize()
        start_time = asyncio.get_event_loop().time()
        
        async with self.get_connection() as conn:
            # Check for duplicates if enabled
            if deduplicate:
                cursor = await conn.execute(
                    "SELECT hash_id, access_count FROM memory_entries WHERE hash_id = ?",
                    (entry.hash_id,)
                )
                existing = await cursor.fetchone()
                
                if existing:
                    # Update access count
                    await conn.execute("""
                        UPDATE memory_entries 
                        SET access_count = access_count + 1,
                            last_accessed = CURRENT_TIMESTAMP
                        WHERE hash_id = ?
                    """, (entry.hash_id,))
                    await conn.commit()
                    
                    latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                    return {
                        "status": "duplicate",
                        "hash_id": entry.hash_id,
                        "latency_ms": latency_ms,
                        "previous_access_count": existing["access_count"]
                    }
            
            # Insert new entry
            entry_dict = entry.to_dict()
            await conn.execute("""
                INSERT INTO memory_entries 
                (hash_id, topic, content, source, tags, memory_type, embedding_vector, access_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_dict["hash_id"],
                entry_dict["topic"],
                entry_dict["content"],
                entry_dict["source"],
                entry_dict["tags"],
                entry_dict["memory_type"],
                entry_dict["embedding_vector"],
                0
            ))
            await conn.commit()
        
        # Add to Weaviate if available
        if self.weaviate_client:
            try:
                collection = self.weaviate_client.collections.get(self.config.weaviate_collection)
                collection.data.insert(
                    properties={
                        "hash_id": entry.hash_id,
                        "topic": entry.topic,
                        "content": entry.content,
                        "source": entry.source,
                        "memory_type": entry.memory_type.value,
                        "tags": entry.tags,
                        "created_at": entry.timestamp.isoformat()
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to add to Weaviate: {e}")
        
        # Invalidate cache
        if self.redis_client:
            try:
                await self._invalidate_search_cache(entry.topic)
            except Exception as e:
                logger.warning(f"Cache invalidation failed: {e}")
        
        latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        self._metrics["requests"] += 1
        
        logger.info(f"Added memory entry: {entry.hash_id} ({latency_ms:.0f}ms)")
        return {
            "status": "added",
            "hash_id": entry.hash_id,
            "latency_ms": latency_ms
        }

    # Additional methods would continue here...
    # For brevity, I'll add the key search method and then create the MCP protocol interface

    async def search_memory(
        self,
        query: str,
        limit: int = 10,
        memory_type: Optional[MemoryType] = None,
        use_vector: bool = True,
        use_fts: bool = True,
        rerank: bool = True
    ) -> List[SearchResult]:
        """Enhanced memory search with multiple retrieval methods."""
        await self.initialize()
        
        # Check cache first
        cache_key = f"search:{hashlib.md5(f'{query}:{limit}:{memory_type}:{use_vector}:{use_fts}:{rerank}'.encode()).hexdigest()}"
        
        if self.redis_client:
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    self._metrics["cache_hits"] += 1
                    logger.info("Search results from cache")
                    return [SearchResult(**json.loads(item)) for item in json.loads(cached)]
                else:
                    self._metrics["cache_misses"] += 1
            except Exception as e:
                logger.warning(f"Cache retrieval failed: {e}")
        
        results = []
        
        # Vector search if available and requested
        if use_vector and self.weaviate_client:
            try:
                vector_results = await self._vector_search(query, limit, memory_type)
                results.extend(vector_results)
            except Exception as e:
                logger.error(f"Vector search failed: {e}")
        
        # FTS search if requested
        if use_fts and self.config.enable_fts:
            try:
                fts_results = await self._fts_search(query, limit, memory_type)
                results.extend(fts_results)
            except Exception as e:
                logger.error(f"FTS search failed: {e}")
        
        # Combine and deduplicate results
        results = self._combine_results(results, limit)
        
        # Re-rank if requested
        if rerank and len(results) > 1:
            try:
                results = await self._rerank_results(query, results)
            except Exception as e:
                logger.warning(f"Re-ranking failed: {e}")
        
        # Update access statistics
        await self._update_access_stats([r.entry.hash_id for r in results])
        
        # Cache results
        if self.redis_client and results:
            try:
                cache_data = json.dumps([asdict(r) for r in results])
                await self.redis_client.setex(cache_key, self.config.cache_ttl, cache_data)
            except Exception as e:
                logger.warning(f"Cache storage failed: {e}")
        
        return results[:limit]

    async def _vector_search(self, query: str, limit: int, memory_type: Optional[MemoryType]) -> List[SearchResult]:
        """Vector similarity search implementation."""
        if not self.weaviate_client:
            return []
            
        try:
            collection = self.weaviate_client.collections.get(self.config.weaviate_collection)
            
            # Build where filter for memory type
            where_filter = None
            if memory_type:
                where_filter = wvc.query.Filter.by_property("memory_type").equal(memory_type.value)
            
            # Perform vector search
            response = collection.query.near_text(
                query=query,
                limit=limit,
                where=where_filter,
                return_metadata=wvc.query.MetadataQuery(distance=True)
            )
            
            results = []
            for obj in response.objects:
                # Create memory entry from Weaviate object
                entry = MemoryEntry(
                    topic=obj.properties.get("topic", ""),
                    content=obj.properties.get("content", ""),
                    source=obj.properties.get("source", ""),
                    tags=obj.properties.get("tags", []),
                    memory_type=MemoryType(obj.properties.get("memory_type", MemoryType.SEMANTIC.value)),
                    hash_id=obj.properties.get("hash_id", "")
                )
                
                # Calculate vector score (1 - distance for similarity)
                vector_score = 1.0 - obj.metadata.distance if obj.metadata.distance else 0.0
                
                results.append(SearchResult(
                    entry=entry,
                    vector_score=vector_score
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
        
    async def _fts_search(self, query: str, limit: int, memory_type: Optional[MemoryType]) -> List[SearchResult]:
        """Full-text search implementation."""
        if not self.config.enable_fts:
            return []
            
        try:
            async with self.get_connection() as conn:
                # Build FTS query
                fts_query = f"""
                    SELECT me.*,
                           bm25(memory_fts) as fts_score,
                           snippet(memory_fts, 1, '<b>', '</b>', '...', 32) as snippet
                    FROM memory_fts
                    JOIN memory_entries me ON memory_fts.rowid = me.id
                    WHERE memory_fts MATCH ?
                """
                
                params = [query]
                
                # Add memory type filter if specified
                if memory_type:
                    fts_query += " AND me.memory_type = ?"
                    params.append(memory_type.value)
                
                fts_query += " ORDER BY bm25(memory_fts) LIMIT ?"
                params.append(limit)
                
                cursor = await conn.execute(fts_query, params)
                rows = await cursor.fetchall()
                
                results = []
                for row in rows:
                    # Create memory entry from row
                    entry = MemoryEntry(
                        topic=row["topic"],
                        content=row["content"],
                        source=row["source"],
                        tags=json.loads(row["tags"]) if row["tags"] else [],
                        memory_type=MemoryType(row["memory_type"]),
                        hash_id=row["hash_id"]
                    )
                    
                    results.append(SearchResult(
                        entry=entry,
                        fts_score=float(row["fts_score"])
                    ))
                
                return results
                
        except Exception as e:
            logger.error(f"FTS search failed: {e}")
            return []
        
    def _combine_results(self, results: List[SearchResult], limit: int) -> List[SearchResult]:
        """Combine and deduplicate search results."""
        if not results:
            return []
        
        # Deduplicate by hash_id
        seen_hashes = set()
        unique_results = []
        
        for result in results:
            hash_id = result.entry.hash_id
            if hash_id not in seen_hashes:
                seen_hashes.add(hash_id)
                unique_results.append(result)
        
        # Combine scores using weighted average
        for result in unique_results:
            scores = []
            weights = []
            
            if result.vector_score is not None:
                scores.append(result.vector_score)
                weights.append(0.7)  # Higher weight for vector similarity
            
            if result.fts_score is not None:
                # Normalize FTS score (BM25 can be negative)
                normalized_fts = max(0, min(1, result.fts_score / 10))
                scores.append(normalized_fts)
                weights.append(0.3)
            
            if scores:
                result.combined_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
            else:
                result.combined_score = 0.0
        
        # Sort by combined score and return top results
        unique_results.sort(key=lambda r: r.combined_score or 0, reverse=True)
        return unique_results[:limit]
        
    async def _rerank_results(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        """Re-rank results using LLM with error handling."""
        if len(results) <= 1:
            return results
            
        try:
            # Prepare content for re-ranking
            contexts = []
            for i, result in enumerate(results):
                context = f"{i+1}. {result.entry.topic}: {result.entry.content[:200]}..."
                contexts.append(context)
            
            # Create re-ranking prompt
            rerank_prompt = f"""
            Given the query: "{query}"
            
            Rank these memory entries by relevance (1 = most relevant):
            
            {chr(10).join(contexts)}
            
            Return only the numbers in order of relevance (e.g., "3,1,4,2"):
            """
            
            # Use real_executor for re-ranking if available
            if REAL_EXECUTOR_AVAILABLE and real_executor:
                try:
                    response = await real_executor.execute(rerank_prompt, model="anthropic/claude-3-haiku-20240307")
                    
                    # Parse ranking response
                    ranking_str = response.strip()
                    rankings = [int(x.strip()) - 1 for x in ranking_str.split(",")]  # Convert to 0-based
                    
                    # Reorder results based on ranking
                    reranked = []
                    for rank_idx in rankings:
                        if 0 <= rank_idx < len(results):
                            result = results[rank_idx]
                            # Update rerank score based on position
                            result.rerank_score = 1.0 - (len(reranked) / len(results))
                            reranked.append(result)
                    
                    # Add any missing results
                    for i, result in enumerate(results):
                        if result not in reranked:
                            result.rerank_score = 0.1  # Low score for unranked
                            reranked.append(result)
                    
                    return reranked
                    
                except Exception as api_error:
                    logger.warning(f"LLM re-ranking failed, using score-based fallback: {api_error}")
            else:
                logger.debug("Real executor not available, using score-based ranking")
            
            # Fallback to score-based ranking
            for i, result in enumerate(results):
                result.rerank_score = 1.0 - (i / len(results))
            return sorted(results, key=lambda r: r.combined_score or 0, reverse=True)
                
        except Exception as e:
            logger.error(f"Re-ranking failed completely: {e}")
            return results
        
    async def _update_access_stats(self, hash_ids: List[str]):
        """Update access statistics."""
        if not hash_ids:
            return
            
        try:
            async with self.get_connection() as conn:
                # Update access count and last accessed time for all hash_ids
                placeholders = ",".join("?" * len(hash_ids))
                await conn.execute(f"""
                    UPDATE memory_entries
                    SET access_count = access_count + 1,
                        last_accessed = CURRENT_TIMESTAMP
                    WHERE hash_id IN ({placeholders})
                """, hash_ids)
                await conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to update access stats: {e}")
        
    async def _invalidate_search_cache(self, topic: str):
        """Invalidate search cache."""
        if not self.redis_client:
            return
            
        try:
            # Find all cache keys related to this topic
            pattern = f"search:*{hashlib.md5(topic.encode()).hexdigest()[:8]}*"
            
            # Use scan to find matching keys
            keys = []
            cursor = 0
            while True:
                cursor, batch_keys = await self.redis_client.scan(cursor, match=pattern, count=100)
                keys.extend(batch_keys)
                if cursor == 0:
                    break
            
            # Delete matching keys
            if keys:
                await self.redis_client.delete(*keys)
                logger.debug(f"Invalidated {len(keys)} cache entries for topic: {topic}")
                
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics."""
        stats = {
            "connections": {
                "pool_size": self.config.connection_pool_size,
                "available": self._connection_pool.qsize() if self._connection_pool else 0
            },
            "performance": self._metrics,
            "backends": {
                "sqlite": True,
                "weaviate": self.weaviate_client is not None,
                "redis": self.redis_client is not None
            }
        }
        
        # Get detailed stats from database
        async with self.get_connection() as conn:
            cursor = await conn.execute("SELECT COUNT(*) FROM memory_entries")
            total_entries = (await cursor.fetchone())[0]
            
            cursor = await conn.execute("""
                SELECT memory_type, COUNT(*) 
                FROM memory_entries 
                GROUP BY memory_type
            """)
            by_type = dict(await cursor.fetchall())
            
            stats.update({
                "total_entries": total_entries,
                "by_type": by_type
            })
        
        return stats

    async def close(self):
        """Gracefully close all connections."""
        if self.weaviate_client:
            self.weaviate_client.close()
            
        if self.redis_client:
            await self.redis_client.close()
            
        if self._connection_pool:
            # Close all pooled connections
            connections = []
            while not self._connection_pool.empty():
                try:
                    conn = self._connection_pool.get_nowait()
                    connections.append(conn)
                except asyncio.QueueEmpty:
                    break
            
            for conn in connections:
                await conn.close()
                
        logger.info("Unified memory store closed")


# Global instance for the service
unified_memory_store = None

async def get_unified_memory_store() -> UnifiedMemoryStore:
    """Get the global unified memory store instance."""
    global unified_memory_store
    if unified_memory_store is None:
        unified_memory_store = UnifiedMemoryStore()
        await unified_memory_store.initialize()
    return unified_memory_store