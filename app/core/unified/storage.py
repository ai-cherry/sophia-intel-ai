"""
Unified Storage - Single interface for ALL storage operations
Replaces 63+ direct Redis/Weaviate/PostgreSQL accesses
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import hashlib

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
import weaviate
from weaviate.client import Client as WeaviateClient
import asyncpg
from asyncpg.pool import Pool

logger = logging.getLogger(__name__)


class StorageType:
    """Storage type hints for intelligent routing"""
    CACHE = "cache"  # Temporary, fast access (Redis)
    VECTOR = "vector"  # Embeddings, similarity search (Weaviate)
    RELATIONAL = "relational"  # Structured, ACID (PostgreSQL)
    DOCUMENT = "document"  # JSON documents (Redis with persistence)


class UnifiedStorage:
    """
    Single interface for ALL storage operations.
    No more direct database access anywhere else.
    """
    
    _instance: Optional['UnifiedStorage'] = None
    _initialized: bool = False
    
    def __new__(cls):
        """Singleton pattern - only ONE storage manager"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize connections (once)"""
        if not self._initialized:
            # Connection pools (not yet connected)
            self._redis_pool: Optional[ConnectionPool] = None
            self._redis_client: Optional[redis.Redis] = None
            
            self._weaviate_client: Optional[WeaviateClient] = None
            
            self._pg_pool: Optional[Pool] = None
            
            # Configuration
            self.config = self._load_config()
            
            UnifiedStorage._initialized = True
            logger.info("UnifiedStorage initialized (singleton)")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load storage configuration from environment"""
        import os
        
        return {
            'redis': {
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', 6379)),
                'db': int(os.getenv('REDIS_DB', 0)),
                'password': os.getenv('REDIS_PASSWORD'),
                'max_connections': 50
            },
            'weaviate': {
                'host': os.getenv('WEAVIATE_HOST', 'localhost'),
                'port': int(os.getenv('WEAVIATE_PORT', 8080)),
                'scheme': os.getenv('WEAVIATE_SCHEME', 'http')
            },
            'postgres': {
                'host': os.getenv('POSTGRES_HOST', 'localhost'),
                'port': int(os.getenv('POSTGRES_PORT', 5432)),
                'database': os.getenv('POSTGRES_DB', 'sophia'),
                'user': os.getenv('POSTGRES_USER', 'postgres'),
                'password': os.getenv('POSTGRES_PASSWORD'),
                'min_size': 10,
                'max_size': 20
            }
        }
    
    async def initialize(self):
        """Initialize all storage connections"""
        await self._init_redis()
        await self._init_weaviate()
        await self._init_postgres()
        logger.info("All storage connections initialized")
    
    async def shutdown(self):
        """Clean shutdown of all connections"""
        if self._redis_client:
            await self._redis_client.close()
        
        if self._weaviate_client:
            # Weaviate client doesn't have async close
            pass
        
        if self._pg_pool:
            await self._pg_pool.close()
        
        logger.info("All storage connections closed")
    
    # ==================== Redis Operations ====================
    
    async def _init_redis(self):
        """Initialize Redis connection pool"""
        self._redis_pool = ConnectionPool(
            **self.config['redis'],
            decode_responses=True
        )
        self._redis_client = redis.Redis(connection_pool=self._redis_pool)
        
        # Test connection
        await self._redis_client.ping()
        logger.info("Redis connection established")
    
    async def cache_set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: str = "default"
    ) -> bool:
        """Set cache value with optional TTL"""
        if not self._redis_client:
            await self._init_redis()
        
        full_key = f"{namespace}:{key}"
        
        # Serialize value
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        try:
            if ttl:
                await self._redis_client.setex(full_key, ttl, value)
            else:
                await self._redis_client.set(full_key, value)
            return True
        except Exception as e:
            logger.error(f"Cache set failed: {e}")
            return False
    
    async def cache_get(
        self,
        key: str,
        namespace: str = "default"
    ) -> Optional[Any]:
        """Get cache value"""
        if not self._redis_client:
            await self._init_redis()
        
        full_key = f"{namespace}:{key}"
        
        try:
            value = await self._redis_client.get(full_key)
            
            # Try to deserialize JSON
            if value:
                try:
                    return json.loads(value)
                except:
                    return value
            
            return None
        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            return None
    
    async def cache_delete(
        self,
        key: str,
        namespace: str = "default"
    ) -> bool:
        """Delete cache value"""
        if not self._redis_client:
            await self._init_redis()
        
        full_key = f"{namespace}:{key}"
        
        try:
            await self._redis_client.delete(full_key)
            return True
        except Exception as e:
            logger.error(f"Cache delete failed: {e}")
            return False
    
    async def cache_exists(
        self,
        key: str,
        namespace: str = "default"
    ) -> bool:
        """Check if cache key exists"""
        if not self._redis_client:
            await self._init_redis()
        
        full_key = f"{namespace}:{key}"
        
        try:
            return await self._redis_client.exists(full_key) > 0
        except Exception as e:
            logger.error(f"Cache exists check failed: {e}")
            return False
    
    # ==================== Weaviate Operations ====================
    
    async def _init_weaviate(self):
        """Initialize Weaviate client"""
        try:
            self._weaviate_client = weaviate.Client(
                url=f"{self.config['weaviate']['scheme']}://{self.config['weaviate']['host']}:{self.config['weaviate']['port']}"
            )
            
            # Test connection
            self._weaviate_client.schema.get()
            logger.info("Weaviate connection established")
        except Exception as e:
            logger.warning(f"Weaviate connection failed: {e}")
            self._weaviate_client = None
    
    async def vector_upsert(
        self,
        id: str,
        vector: List[float],
        metadata: Dict[str, Any],
        class_name: str = "Document"
    ) -> bool:
        """Upsert vector with metadata"""
        if not self._weaviate_client:
            logger.warning("Weaviate not available")
            return False
        
        try:
            # Weaviate operations are sync, run in executor
            loop = asyncio.get_event_loop()
            
            def _upsert():
                return self._weaviate_client.data_object.create(
                    data_object=metadata,
                    class_name=class_name,
                    uuid=id,
                    vector=vector
                )
            
            await loop.run_in_executor(None, _upsert)
            return True
        except Exception as e:
            logger.error(f"Vector upsert failed: {e}")
            return False
    
    async def vector_search(
        self,
        query_vector: List[float],
        limit: int = 10,
        class_name: str = "Document",
        where_filter: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Search vectors by similarity"""
        if not self._weaviate_client:
            logger.warning("Weaviate not available")
            return []
        
        try:
            loop = asyncio.get_event_loop()
            
            def _search():
                query = self._weaviate_client.query.get(
                    class_name,
                    ["*"]
                ).with_near_vector({
                    "vector": query_vector
                }).with_limit(limit)
                
                if where_filter:
                    query = query.with_where(where_filter)
                
                return query.do()
            
            result = await loop.run_in_executor(None, _search)
            
            if result and "data" in result and "Get" in result["data"]:
                return result["data"]["Get"].get(class_name, [])
            
            return []
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    async def search_similar(
        self,
        text: str,
        limit: int = 5,
        class_name: str = "Document"
    ) -> List[Dict[str, Any]]:
        """Search similar documents by text (creates embedding internally)"""
        # In production, use actual embedding service
        # For now, create mock embedding
        mock_embedding = [0.1] * 384  # Mock 384-dim vector
        
        return await self.vector_search(
            query_vector=mock_embedding,
            limit=limit,
            class_name=class_name
        )
    
    # ==================== PostgreSQL Operations ====================
    
    async def _init_postgres(self):
        """Initialize PostgreSQL connection pool"""
        try:
            self._pg_pool = await asyncpg.create_pool(
                **self.config['postgres']
            )
            
            # Test connection
            async with self._pg_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            
            logger.info("PostgreSQL connection established")
        except Exception as e:
            logger.warning(f"PostgreSQL connection failed: {e}")
            self._pg_pool = None
    
    async def sql_execute(
        self,
        query: str,
        params: Optional[tuple] = None
    ) -> Optional[List[asyncpg.Record]]:
        """Execute SQL query"""
        if not self._pg_pool:
            logger.warning("PostgreSQL not available")
            return None
        
        try:
            async with self._pg_pool.acquire() as conn:
                if params:
                    result = await conn.fetch(query, *params)
                else:
                    result = await conn.fetch(query)
                return result
        except Exception as e:
            logger.error(f"SQL execute failed: {e}")
            return None
    
    async def sql_execute_one(
        self,
        query: str,
        params: Optional[tuple] = None
    ) -> Optional[asyncpg.Record]:
        """Execute SQL query returning one record"""
        if not self._pg_pool:
            logger.warning("PostgreSQL not available")
            return None
        
        try:
            async with self._pg_pool.acquire() as conn:
                if params:
                    result = await conn.fetchrow(query, *params)
                else:
                    result = await conn.fetchrow(query)
                return result
        except Exception as e:
            logger.error(f"SQL execute one failed: {e}")
            return None
    
    async def sql_execute_many(
        self,
        query: str,
        params_list: List[tuple]
    ) -> bool:
        """Execute SQL query with multiple parameter sets"""
        if not self._pg_pool:
            logger.warning("PostgreSQL not available")
            return False
        
        try:
            async with self._pg_pool.acquire() as conn:
                await conn.executemany(query, params_list)
            return True
        except Exception as e:
            logger.error(f"SQL execute many failed: {e}")
            return False
    
    # ==================== Unified Operations ====================
    
    async def store(
        self,
        key: str,
        value: Any,
        storage_type: str = StorageType.CACHE,
        ttl: Optional[int] = None,
        **kwargs
    ) -> bool:
        """
        Store data in appropriate storage based on type
        
        Args:
            key: Unique identifier
            value: Data to store
            storage_type: One of StorageType constants
            ttl: Time to live in seconds (for cache)
            **kwargs: Additional storage-specific parameters
        """
        if storage_type == StorageType.CACHE:
            return await self.cache_set(key, value, ttl, **kwargs)
        
        elif storage_type == StorageType.VECTOR:
            if not isinstance(value, dict) or 'vector' not in value:
                logger.error("Vector storage requires dict with 'vector' key")
                return False
            
            return await self.vector_upsert(
                id=key,
                vector=value['vector'],
                metadata=value.get('metadata', {}),
                **kwargs
            )
        
        elif storage_type == StorageType.RELATIONAL:
            # Store as JSON in PostgreSQL
            query = """
                INSERT INTO unified_storage (key, value, created_at)
                VALUES ($1, $2, $3)
                ON CONFLICT (key) DO UPDATE
                SET value = $2, updated_at = $3
            """
            
            json_value = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            
            result = await self.sql_execute_one(
                query,
                (key, json_value, datetime.now())
            )
            return result is not None
        
        elif storage_type == StorageType.DOCUMENT:
            # Store as persistent Redis with backup
            success = await self.cache_set(key, value, ttl=None, namespace="documents")
            
            # Also backup to PostgreSQL
            if success and self._pg_pool:
                await self.store(key, value, StorageType.RELATIONAL)
            
            return success
        
        else:
            logger.error(f"Unknown storage type: {storage_type}")
            return False
    
    async def retrieve(
        self,
        key: str,
        storage_type: str = StorageType.CACHE,
        **kwargs
    ) -> Optional[Any]:
        """
        Retrieve data from appropriate storage
        
        Args:
            key: Unique identifier
            storage_type: One of StorageType constants
            **kwargs: Additional storage-specific parameters
        """
        if storage_type == StorageType.CACHE:
            return await self.cache_get(key, **kwargs)
        
        elif storage_type == StorageType.VECTOR:
            # Vector storage doesn't support direct key retrieval
            # Use search instead
            logger.warning("Use vector_search for vector storage retrieval")
            return None
        
        elif storage_type == StorageType.RELATIONAL:
            query = "SELECT value FROM unified_storage WHERE key = $1"
            result = await self.sql_execute_one(query, (key,))
            
            if result:
                try:
                    return json.loads(result['value'])
                except:
                    return result['value']
            
            return None
        
        elif storage_type == StorageType.DOCUMENT:
            # Try cache first
            value = await self.cache_get(key, namespace="documents")
            
            # Fallback to PostgreSQL
            if value is None and self._pg_pool:
                value = await self.retrieve(key, StorageType.RELATIONAL)
            
            return value
        
        else:
            logger.error(f"Unknown storage type: {storage_type}")
            return None
    
    async def delete(
        self,
        key: str,
        storage_type: str = StorageType.CACHE,
        **kwargs
    ) -> bool:
        """Delete data from storage"""
        if storage_type == StorageType.CACHE:
            return await self.cache_delete(key, **kwargs)
        
        elif storage_type == StorageType.RELATIONAL:
            query = "DELETE FROM unified_storage WHERE key = $1"
            result = await self.sql_execute(query, (key,))
            return result is not None
        
        elif storage_type == StorageType.DOCUMENT:
            # Delete from both cache and PostgreSQL
            cache_success = await self.cache_delete(key, namespace="documents")
            
            if self._pg_pool:
                db_success = await self.delete(key, StorageType.RELATIONAL)
                return cache_success and db_success
            
            return cache_success
        
        else:
            logger.error(f"Unknown storage type: {storage_type}")
            return False
    
    # ==================== Specialized Methods ====================
    
    async def store_result(self, task_id: str, result: Any) -> bool:
        """Store task execution result"""
        return await self.store(
            f"task_result:{task_id}",
            result,
            StorageType.DOCUMENT,
            ttl=86400  # 24 hours
        )
    
    async def get_business_metrics(self) -> Dict[str, Any]:
        """Get cached business metrics"""
        metrics = await self.cache_get("business_metrics", namespace="metrics")
        
        if not metrics:
            # Fetch from database if not cached
            query = """
                SELECT 
                    COUNT(*) as total_clients,
                    AVG(health_score) as avg_health,
                    SUM(revenue) as total_revenue
                FROM clients
                WHERE active = true
            """
            result = await self.sql_execute_one(query)
            
            if result:
                metrics = dict(result)
                # Cache for 5 minutes
                await self.cache_set(
                    "business_metrics",
                    metrics,
                    ttl=300,
                    namespace="metrics"
                )
        
        return metrics or {}
    
    async def get_code_snippets(self) -> List[str]:
        """Get recent code snippets"""
        snippets = await self.cache_get("recent_code", namespace="code")
        
        if not snippets:
            # Fetch from database
            query = """
                SELECT code FROM code_generations
                ORDER BY created_at DESC
                LIMIT 10
            """
            results = await self.sql_execute(query)
            
            if results:
                snippets = [r['code'] for r in results]
                # Cache for 10 minutes
                await self.cache_set(
                    "recent_code",
                    snippets,
                    ttl=600,
                    namespace="code"
                )
        
        return snippets or []
    
    # ==================== Health Checks ====================
    
    async def is_healthy(self) -> bool:
        """Check if storage systems are healthy"""
        checks = []
        
        # Check Redis
        if self._redis_client:
            try:
                await self._redis_client.ping()
                checks.append(True)
            except:
                checks.append(False)
        
        # Check PostgreSQL
        if self._pg_pool:
            try:
                async with self._pg_pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                checks.append(True)
            except:
                checks.append(False)
        
        # Check Weaviate (optional)
        if self._weaviate_client:
            try:
                self._weaviate_client.schema.get()
                checks.append(True)
            except:
                checks.append(False)
        
        # At least Redis and PostgreSQL should be healthy
        return len([c for c in checks if c]) >= 2
    
    # ==================== Context Manager ====================
    
    @asynccontextmanager
    async def transaction(self):
        """PostgreSQL transaction context manager"""
        if not self._pg_pool:
            raise RuntimeError("PostgreSQL not available")
        
        async with self._pg_pool.acquire() as conn:
            async with conn.transaction():
                yield conn


# ==================== Module-level singleton ====================

_storage: Optional[UnifiedStorage] = None


def get_storage() -> UnifiedStorage:
    """Get the singleton storage instance"""
    global _storage
    if _storage is None:
        _storage = UnifiedStorage()
    return _storage