"""
Enhanced Memory System with Weaviate Vector Database
Combines SQLite for metadata with Weaviate for semantic search.
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import hashlib
import redis
from contextlib import asynccontextmanager

# Vector database imports
try:
    import weaviate
    import weaviate.classes as wvc
    WEAVIATE_AVAILABLE = True
except ImportError:
    WEAVIATE_AVAILABLE = False

from app.memory.types import MemoryEntry, MemoryType
from app.llm.real_executor import real_executor

logger = logging.getLogger(__name__)


class EnhancedMemoryConfig:
    """Configuration for enhanced memory system."""
    
    # SQLite for metadata
    SQLITE_PATH = "tmp/enhanced_memory.db"
    
    # Weaviate configuration  
    WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
    
    # Redis for caching
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/1")
    CACHE_TTL = 3600  # 1 hour
    
    # Performance settings
    MAX_RESULTS = 50
    EMBEDDING_BATCH_SIZE = 100
    SEARCH_TIMEOUT = 5.0


@dataclass
class SearchResult:
    """Enhanced search result with multiple score types."""
    entry: MemoryEntry
    vector_score: Optional[float] = None
    fts_score: Optional[float] = None
    rerank_score: Optional[float] = None
    combined_score: Optional[float] = None


class EnhancedMemoryStore:
    """Enhanced memory store with vector search and caching."""
    
    def __init__(self, config: Optional[EnhancedMemoryConfig] = None):
        self.config = config or EnhancedMemoryConfig()
        self.sqlite_conn = None
        self.weaviate_client = None
        self.redis_client = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize all storage backends."""
        if self._initialized:
            return
            
        # Initialize SQLite
        await self._init_sqlite()
        
        # Initialize Weaviate if available
        if WEAVIATE_AVAILABLE:
            await self._init_weaviate()
        else:
            logger.warning("Weaviate not available, falling back to FTS only")
        
        # Initialize Redis if available
        try:
            import redis.asyncio as aioredis
            self.redis_client = aioredis.from_url(self.config.REDIS_URL)
            await self.redis_client.ping()
            logger.info("Redis cache initialized")
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
            
        self._initialized = True
        
    async def _init_sqlite(self):
        """Initialize SQLite with FTS5."""
        Path(self.config.SQLITE_PATH).parent.mkdir(parents=True, exist_ok=True)
        
        self.sqlite_conn = sqlite3.connect(self.config.SQLITE_PATH)
        self.sqlite_conn.row_factory = sqlite3.Row
        
        cursor = self.sqlite_conn.cursor()
        
        # Create main table
        cursor.execute("""
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
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create FTS5 index with better tokenization
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
                topic, content, tags,
                content='memory_entries',
                content_rowid='id',
                tokenize='porter unicode61'
            )
        """)
        
        # Create triggers for FTS sync
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS memory_fts_insert AFTER INSERT ON memory_entries
            BEGIN
                INSERT INTO memory_fts(rowid, topic, content, tags) 
                VALUES (new.id, new.topic, new.content, new.tags);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS memory_fts_delete AFTER DELETE ON memory_entries
            BEGIN
                INSERT INTO memory_fts(memory_fts, rowid, topic, content, tags) 
                VALUES('delete', old.id, old.topic, old.content, old.tags);
            END
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hash_id ON memory_entries(hash_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_entries(memory_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source ON memory_entries(source)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON memory_entries(created_at)")
        
        self.sqlite_conn.commit()
        logger.info("SQLite memory store initialized with FTS5")
        
    async def _init_weaviate(self):
        """Initialize Weaviate vector database."""
        try:
            if self.config.WEAVIATE_API_KEY:
                auth = weaviate.auth.AuthApiKey(self.config.WEAVIATE_API_KEY)
                self.weaviate_client = weaviate.connect_to_wcs(
                    cluster_url=self.config.WEAVIATE_URL,
                    auth_credentials=auth
                )
            else:
                self.weaviate_client = weaviate.connect_to_local(
                    host=self.config.WEAVIATE_URL.replace("http://", "").replace("https://", "").split(":")[0],
                    port=int(self.config.WEAVIATE_URL.split(":")[-1]) if ":" in self.config.WEAVIATE_URL else 8080
                )
            
            # Check if collection exists, create if not
            collection_name = "MemoryEntries"
            
            if not self.weaviate_client.collections.exists(collection_name):
                memory_collection = self.weaviate_client.collections.create(
                    name=collection_name,
                    vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_transformers(
                        model="sentence-transformers/all-MiniLM-L6-v2"
                    ),
                    properties=[
                        wvc.config.Property(
                            name="hash_id",
                            data_type=wvc.config.DataType.TEXT,
                            skip_vectorization=True
                        ),
                        wvc.config.Property(
                            name="topic", 
                            data_type=wvc.config.DataType.TEXT
                        ),
                        wvc.config.Property(
                            name="content",
                            data_type=wvc.config.DataType.TEXT
                        ),
                        wvc.config.Property(
                            name="source",
                            data_type=wvc.config.DataType.TEXT,
                            skip_vectorization=True
                        ),
                        wvc.config.Property(
                            name="memory_type",
                            data_type=wvc.config.DataType.TEXT,
                            skip_vectorization=True
                        ),
                        wvc.config.Property(
                            name="tags",
                            data_type=wvc.config.DataType.TEXT_ARRAY,
                            skip_vectorization=True
                        ),
                        wvc.config.Property(
                            name="created_at",
                            data_type=wvc.config.DataType.DATE,
                            skip_vectorization=True
                        )
                    ]
                )
                logger.info(f"Created Weaviate collection: {collection_name}")
            else:
                logger.info(f"Using existing Weaviate collection: {collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Weaviate: {e}")
            self.weaviate_client = None
    
    async def add_memory(self, entry: MemoryEntry) -> str:
        """Add memory entry to all storage backends."""
        await self.initialize()
        
        try:
            cursor = self.sqlite_conn.cursor()
            
            # Check for duplicates
            cursor.execute("SELECT id FROM memory_entries WHERE hash_id = ?", (entry.hash_id,))
            if cursor.fetchone():
                logger.info(f"Memory entry {entry.hash_id} already exists, skipping")
                return entry.hash_id
            
            # Insert to SQLite
            cursor.execute("""
                INSERT INTO memory_entries 
                (hash_id, topic, content, source, tags, memory_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                entry.hash_id,
                entry.topic,
                entry.content,
                entry.source,
                json.dumps(entry.tags),
                entry.memory_type.value
            ))
            
            self.sqlite_conn.commit()
            
            # Add to Weaviate if available
            if self.weaviate_client:
                try:
                    collection = self.weaviate_client.collections.get("MemoryEntries")
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
            
            # Invalidate cache for this topic/content
            if self.redis_client:
                try:
                    await self._invalidate_search_cache(entry.topic)
                except Exception as e:
                    logger.warning(f"Cache invalidation failed: {e}")
            
            logger.info(f"Added memory entry: {entry.hash_id}")
            return entry.hash_id
            
        except Exception as e:
            logger.error(f"Failed to add memory entry: {e}")
            raise
    
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
                    logger.info("Search results from cache")
                    return [SearchResult(**json.loads(item)) for item in json.loads(cached)]
            except Exception as e:
                logger.warning(f"Cache retrieval failed: {e}")
        
        results = []
        
        # Vector search if available
        if use_vector and self.weaviate_client:
            try:
                vector_results = await self._vector_search(query, limit, memory_type)
                results.extend(vector_results)
                logger.info(f"Vector search returned {len(vector_results)} results")
            except Exception as e:
                logger.error(f"Vector search failed: {e}")
        
        # FTS search
        if use_fts:
            try:
                fts_results = await self._fts_search(query, limit, memory_type)
                results.extend(fts_results)
                logger.info(f"FTS search returned {len(fts_results)} results")
            except Exception as e:
                logger.error(f"FTS search failed: {e}")
        
        # Combine and deduplicate results
        results = self._combine_results(results, limit)
        
        # Re-rank if requested
        if rerank and len(results) > 1:
            try:
                results = await self._rerank_results(query, results)
                logger.info("Results re-ranked")
            except Exception as e:
                logger.warning(f"Re-ranking failed: {e}")
        
        # Update access statistics
        await self._update_access_stats([r.entry.hash_id for r in results])
        
        # Cache results
        if self.redis_client and results:
            try:
                cache_data = json.dumps([asdict(r) for r in results])
                await self.redis_client.setex(cache_key, self.config.CACHE_TTL, cache_data)
            except Exception as e:
                logger.warning(f"Cache storage failed: {e}")
        
        return results[:limit]
    
    async def _vector_search(
        self,
        query: str,
        limit: int,
        memory_type: Optional[MemoryType]
    ) -> List[SearchResult]:
        """Perform vector similarity search."""
        if not self.weaviate_client:
            return []
            
        try:
            collection = self.weaviate_client.collections.get("MemoryEntries")
            
            # Build where clause
            where_filter = None
            if memory_type:
                where_filter = wvc.query.Filter.by_property("memory_type").equal(memory_type.value)
            
            # Perform search
            response = collection.query.near_text(
                query=query,
                limit=limit * 2,  # Get more for deduplication
                where=where_filter,
                return_metadata=wvc.query.MetadataQuery(distance=True)
            )
            
            results = []
            for obj in response.objects:
                # Convert to MemoryEntry
                entry = MemoryEntry(
                    topic=obj.properties["topic"],
                    content=obj.properties["content"],
                    source=obj.properties["source"],
                    tags=obj.properties["tags"] or [],
                    memory_type=MemoryType(obj.properties["memory_type"]),
                    hash_id=obj.properties["hash_id"],
                    timestamp=datetime.fromisoformat(obj.properties["created_at"])
                )
                
                # Calculate score (Weaviate returns distance, convert to similarity)
                vector_score = 1.0 - obj.metadata.distance
                
                results.append(SearchResult(
                    entry=entry,
                    vector_score=vector_score
                ))
                
            return results
            
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []
    
    async def _fts_search(
        self,
        query: str,
        limit: int,
        memory_type: Optional[MemoryType]
    ) -> List[SearchResult]:
        """Perform FTS search with improved error handling."""
        try:
            cursor = self.sqlite_conn.cursor()
            
            # Escape query for FTS5
            escaped_query = self._escape_fts_query(query)
            
            # Build SQL with optional memory_type filter
            base_query = """
                SELECT m.*, fts.rank
                FROM memory_fts fts
                JOIN memory_entries m ON fts.rowid = m.id
                WHERE memory_fts MATCH ?
            """
            
            params = [escaped_query]
            
            if memory_type:
                base_query += " AND m.memory_type = ?"
                params.append(memory_type.value)
            
            base_query += " ORDER BY fts.rank LIMIT ?"
            params.append(limit * 2)
            
            cursor.execute(base_query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                entry = MemoryEntry(
                    topic=row["topic"],
                    content=row["content"],
                    source=row["source"],
                    tags=json.loads(row["tags"]) if row["tags"] else [],
                    memory_type=MemoryType(row["memory_type"]),
                    hash_id=row["hash_id"],
                    timestamp=datetime.fromisoformat(row["created_at"])
                )
                
                # FTS5 rank is negative (lower is better), convert to positive score
                fts_score = abs(row["rank"]) if row["rank"] else 0.0
                
                results.append(SearchResult(
                    entry=entry,
                    fts_score=fts_score
                ))
                
            return results
            
        except Exception as e:
            logger.error(f"FTS search error: {e}")
            # Fallback to LIKE search
            return await self._like_search(query, limit, memory_type)
    
    def _escape_fts_query(self, query: str) -> str:
        """Escape query for FTS5 to prevent syntax errors."""
        # Remove or escape special FTS5 characters
        special_chars = ['"', "'", "(", ")", "*", ":", "-", "+"]
        escaped = query
        
        for char in special_chars:
            escaped = escaped.replace(char, f" {char} ")
        
        # Clean up multiple spaces
        escaped = " ".join(escaped.split())
        
        # If query looks safe, use phrase search for exact matches
        if escaped.isalnum() or " " not in escaped:
            return f'"{escaped}"'
        else:
            return escaped
    
    async def _like_search(
        self,
        query: str,
        limit: int,
        memory_type: Optional[MemoryType]
    ) -> List[SearchResult]:
        """Fallback LIKE search when FTS fails."""
        try:
            cursor = self.sqlite_conn.cursor()
            
            base_query = """
                SELECT * FROM memory_entries
                WHERE (topic LIKE ? OR content LIKE ?)
            """
            
            params = [f"%{query}%", f"%{query}%"]
            
            if memory_type:
                base_query += " AND memory_type = ?"
                params.append(memory_type.value)
                
            base_query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(base_query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                entry = MemoryEntry(
                    topic=row["topic"],
                    content=row["content"],
                    source=row["source"],
                    tags=json.loads(row["tags"]) if row["tags"] else [],
                    memory_type=MemoryType(row["memory_type"]),
                    hash_id=row["hash_id"],
                    timestamp=datetime.fromisoformat(row["created_at"])
                )
                
                results.append(SearchResult(entry=entry, fts_score=0.5))
                
            logger.info(f"LIKE search fallback returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"LIKE search fallback failed: {e}")
            return []
    
    def _combine_results(self, results: List[SearchResult], limit: int) -> List[SearchResult]:
        """Combine and deduplicate search results."""
        # Deduplicate by hash_id
        seen = set()
        unique_results = []
        
        for result in results:
            if result.entry.hash_id not in seen:
                seen.add(result.entry.hash_id)
                unique_results.append(result)
        
        # Calculate combined scores
        for result in unique_results:
            scores = []
            if result.vector_score is not None:
                scores.append(result.vector_score)
            if result.fts_score is not None:
                scores.append(result.fts_score)
            if result.rerank_score is not None:
                scores.append(result.rerank_score)
                
            result.combined_score = sum(scores) / len(scores) if scores else 0.0
        
        # Sort by combined score
        unique_results.sort(key=lambda x: x.combined_score or 0.0, reverse=True)
        
        return unique_results[:limit]
    
    async def _rerank_results(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        """Re-rank results using LLM for relevance."""
        try:
            # Build re-ranking prompt
            entries_text = "\n".join([
                f"{i}. {r.entry.topic}: {r.entry.content[:200]}..."
                for i, r in enumerate(results)
            ])
            
            rerank_prompt = f"""
            Query: {query}
            
            Rank these memory entries from most relevant (1) to least relevant:
            {entries_text}
            
            Return only the ranking as numbers: 1,2,3,4,5...
            """
            
            # Get LLM ranking
            response = await real_executor.execute(
                prompt=rerank_prompt,
                model_pool="fast",
                stream=False
            )
            
            if response["success"]:
                # Parse ranking
                ranking_str = response["content"].strip()
                try:
                    rankings = [int(x.strip()) - 1 for x in ranking_str.split(",")]
                    
                    # Apply re-ranking scores
                    for i, orig_idx in enumerate(rankings):
                        if 0 <= orig_idx < len(results):
                            results[orig_idx].rerank_score = (len(rankings) - i) / len(rankings)
                    
                    logger.info("Results successfully re-ranked")
                    
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse ranking: {e}")
            
        except Exception as e:
            logger.warning(f"Re-ranking failed: {e}")
            
        return results
    
    async def _update_access_stats(self, hash_ids: List[str]):
        """Update access statistics for retrieved entries."""
        if not hash_ids:
            return
            
        try:
            cursor = self.sqlite_conn.cursor()
            placeholders = ",".join(["?"] * len(hash_ids))
            
            cursor.execute(f"""
                UPDATE memory_entries 
                SET access_count = access_count + 1,
                    last_accessed = CURRENT_TIMESTAMP
                WHERE hash_id IN ({placeholders})
            """, hash_ids)
            
            self.sqlite_conn.commit()
            
        except Exception as e:
            logger.warning(f"Failed to update access stats: {e}")
    
    async def _invalidate_search_cache(self, topic: str):
        """Invalidate search cache for a topic."""
        if not self.redis_client:
            return
            
        try:
            # Get all search cache keys and delete matching ones
            pattern = f"search:*{topic.lower()}*"
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
                
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {e}")
    
    async def close(self):
        """Close all connections."""
        if self.sqlite_conn:
            self.sqlite_conn.close()
            
        if self.weaviate_client:
            self.weaviate_client.close()
            
        if self.redis_client:
            await self.redis_client.close()


# Global instance
enhanced_memory = EnhancedMemoryStore()


async def get_enhanced_memory_instance() -> EnhancedMemoryStore:
    """Get the global enhanced memory instance."""
    await enhanced_memory.initialize()
    return enhanced_memory