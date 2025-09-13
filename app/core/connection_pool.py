"""
Database Connection Pooling Manager
Provides efficient connection management for PostgreSQL, Redis, and Weaviate
"""
import asyncio
import logging
from typing import Any, Optional, Dict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import asyncpg
import redis.asyncio as aioredis
from app.core.feature_flags import FeatureFlags

logger = logging.getLogger(__name__)


class PostgresPool:
    """PostgreSQL connection pool manager"""
    
    def __init__(self, dsn: str, min_size: int = 2, max_size: int = 10):
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[asyncpg.Pool] = None
        self._lock = asyncio.Lock()
        self.stats = {
            "connections_created": 0,
            "connections_closed": 0,
            "queries_executed": 0,
            "errors": 0
        }
    
    async def initialize(self):
        """Initialize the connection pool"""
        if self.pool is not None:
            return
        
        async with self._lock:
            if self.pool is None:
                try:
                    self.pool = await asyncpg.create_pool(
                        self.dsn,
                        min_size=self.min_size,
                        max_size=self.max_size,
                        command_timeout=60,
                        max_queries=50000,
                        max_inactive_connection_lifetime=300
                    )
                    logger.info(f"PostgreSQL pool initialized with {self.min_size}-{self.max_size} connections")
                except Exception as e:
                    logger.error(f"Failed to initialize PostgreSQL pool: {e}")
                    raise
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool"""
        if self.pool is None:
            await self.initialize()
        
        try:
            async with self.pool.acquire() as connection:
                self.stats["connections_created"] += 1
                yield connection
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"PostgreSQL connection error: {e}")
            raise
        finally:
            self.stats["connections_closed"] += 1
    
    async def execute(self, query: str, *args, timeout: float = None):
        """Execute a query using a pooled connection"""
        async with self.acquire() as conn:
            self.stats["queries_executed"] += 1
            return await conn.execute(query, *args, timeout=timeout)
    
    async def fetch(self, query: str, *args, timeout: float = None):
        """Fetch results using a pooled connection"""
        async with self.acquire() as conn:
            self.stats["queries_executed"] += 1
            return await conn.fetch(query, *args, timeout=timeout)
    
    async def fetchrow(self, query: str, *args, timeout: float = None):
        """Fetch a single row using a pooled connection"""
        async with self.acquire() as conn:
            self.stats["queries_executed"] += 1
            return await conn.fetchrow(query, *args, timeout=timeout)
    
    async def close(self):
        """Close the connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("PostgreSQL pool closed")
    
    def get_stats(self) -> dict:
        """Get pool statistics"""
        if self.pool:
            return {
                **self.stats,
                "pool_size": self.pool.get_size(),
                "pool_free": self.pool.get_idle_size(),
                "pool_used": self.pool.get_size() - self.pool.get_idle_size()
            }
        return self.stats


class RedisPool:
    """Redis connection pool manager with circuit breaker"""
    
    def __init__(self, url: str, max_connections: int = 50):
        self.url = url
        self.max_connections = max_connections
        self.pool: Optional[aioredis.ConnectionPool] = None
        self.client: Optional[aioredis.Redis] = None
        self._lock = asyncio.Lock()
        self.circuit_open = False
        self.last_failure = None
        self.failure_count = 0
        self.stats = {
            "commands_executed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0
        }
    
    async def initialize(self):
        """Initialize Redis connection pool"""
        if self.client is not None:
            return
        
        async with self._lock:
            if self.client is None:
                try:
                    self.pool = aioredis.ConnectionPool.from_url(
                        self.url,
                        max_connections=self.max_connections,
                        decode_responses=True,
                        socket_keepalive=True,
                        socket_connect_timeout=5,
                        retry_on_timeout=True
                    )
                    self.client = aioredis.Redis(connection_pool=self.pool)
                    await self.client.ping()
                    logger.info(f"Redis pool initialized with max {self.max_connections} connections")
                    self.circuit_open = False
                    self.failure_count = 0
                except Exception as e:
                    logger.error(f"Failed to initialize Redis pool: {e}")
                    self.failure_count += 1
                    self.last_failure = datetime.now()
                    if self.failure_count >= 3:
                        self.circuit_open = True
                    raise
    
    def is_healthy(self) -> bool:
        """Check if Redis connection is healthy"""
        if self.circuit_open and self.last_failure:
            # Try to recover after 30 seconds
            if datetime.now() - self.last_failure > timedelta(seconds=30):
                self.circuit_open = False
                self.failure_count = 0
        return not self.circuit_open and self.client is not None
    
    async def get(self, key: str, default=None):
        """Get value from Redis"""
        if not self.is_healthy():
            return default
        
        try:
            if self.client is None:
                await self.initialize()
            
            self.stats["commands_executed"] += 1
            value = await self.client.get(key)
            if value is not None:
                self.stats["cache_hits"] += 1
            else:
                self.stats["cache_misses"] += 1
            return value if value is not None else default
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Redis GET error: {e}")
            self.failure_count += 1
            if self.failure_count >= 3:
                self.circuit_open = True
                self.last_failure = datetime.now()
            return default
    
    async def set(self, key: str, value: Any, ex: int = None) -> bool:
        """Set value in Redis"""
        if not self.is_healthy():
            return False
        
        try:
            if self.client is None:
                await self.initialize()
            
            self.stats["commands_executed"] += 1
            return await self.client.set(key, value, ex=ex)
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Redis SET error: {e}")
            return False
    
    async def delete(self, *keys):
        """Delete keys from Redis"""
        if not self.is_healthy():
            return 0
        
        try:
            if self.client is None:
                await self.initialize()
            
            self.stats["commands_executed"] += 1
            return await self.client.delete(*keys)
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Redis DELETE error: {e}")
            return 0
    
    async def close(self):
        """Close Redis connection pool"""
        if self.client:
            await self.client.close()
            self.client = None
        if self.pool:
            await self.pool.disconnect()
            self.pool = None
        logger.info("Redis pool closed")
    
    def get_stats(self) -> dict:
        """Get pool statistics"""
        stats = self.stats.copy()
        stats["circuit_open"] = self.circuit_open
        stats["failure_count"] = self.failure_count
        if self.pool:
            stats["connections_created"] = self.pool.connection_kwargs.get("max_connections", 0)
        return stats


class WeaviatePool:
    """Weaviate connection pool manager"""
    
    def __init__(self, url: str, max_connections: int = 10):
        self.url = url
        self.max_connections = max_connections
        self.semaphore = asyncio.Semaphore(max_connections)
        self.connections = []
        self.available = asyncio.Queue(maxsize=max_connections)
        self._lock = asyncio.Lock()
        self.stats = {
            "vectors_stored": 0,
            "searches_performed": 0,
            "errors": 0
        }
    
    async def initialize(self):
        """Initialize Weaviate connection pool"""
        async with self._lock:
            if not self.connections:
                try:
                    # Import here to avoid circular dependency
                    from app.weaviate.weaviate_client import WeaviateClient
                    
                    for _ in range(min(3, self.max_connections)):
                        client = WeaviateClient(url=self.url)
                        self.connections.append(client)
                        await self.available.put(client)
                    
                    logger.info(f"Weaviate pool initialized with {len(self.connections)} connections")
                except Exception as e:
                    logger.error(f"Failed to initialize Weaviate pool: {e}")
                    raise
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a Weaviate client from the pool"""
        async with self.semaphore:
            if self.available.empty() and len(self.connections) < self.max_connections:
                # Create a new connection if needed
                from app.weaviate.weaviate_client import WeaviateClient
                client = WeaviateClient(url=self.url)
                self.connections.append(client)
            else:
                client = await self.available.get()
            
            try:
                yield client
            finally:
                await self.available.put(client)
    
    async def store_embedding(self, embedding: list, text: str, metadata: dict):
        """Store embedding using pooled connection"""
        async with self.acquire() as client:
            try:
                await client.store_embedding(embedding, text, metadata)
                self.stats["vectors_stored"] += 1
            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"Weaviate store error: {e}")
                raise
    
    async def search(self, query_embedding: list, top_k: int = 5):
        """Search using pooled connection"""
        async with self.acquire() as client:
            try:
                results = await client.search_by_vector(query_embedding, top_k)
                self.stats["searches_performed"] += 1
                return results
            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"Weaviate search error: {e}")
                raise
    
    def get_stats(self) -> dict:
        """Get pool statistics"""
        return {
            **self.stats,
            "pool_size": len(self.connections),
            "available_connections": self.available.qsize()
        }


class ConnectionPoolManager:
    """Central manager for all connection pools"""
    
    def __init__(self):
        self.postgres_pool: Optional[PostgresPool] = None
        self.redis_pool: Optional[RedisPool] = None
        self.weaviate_pool: Optional[WeaviatePool] = None
        self.enabled = FeatureFlags.ENABLE_CONNECTION_POOLING
    
    async def initialize_postgres(self, dsn: str, **kwargs):
        """Initialize PostgreSQL pool"""
        if not self.enabled:
            logger.info("Connection pooling disabled, using direct connections")
            return
        
        self.postgres_pool = PostgresPool(dsn, **kwargs)
        await self.postgres_pool.initialize()
    
    async def initialize_redis(self, url: str, **kwargs):
        """Initialize Redis pool"""
        if not self.enabled:
            logger.info("Connection pooling disabled, using direct connections")
            return
        
        self.redis_pool = RedisPool(url, **kwargs)
        await self.redis_pool.initialize()
    
    async def initialize_weaviate(self, url: str, **kwargs):
        """Initialize Weaviate pool"""
        if not self.enabled:
            logger.info("Connection pooling disabled, using direct connections")
            return
        
        self.weaviate_pool = WeaviatePool(url, **kwargs)
        await self.weaviate_pool.initialize()
    
    def get_postgres(self) -> Optional[PostgresPool]:
        """Get PostgreSQL pool"""
        return self.postgres_pool if self.enabled else None
    
    def get_redis(self) -> Optional[RedisPool]:
        """Get Redis pool"""
        return self.redis_pool if self.enabled else None
    
    def get_weaviate(self) -> Optional[WeaviatePool]:
        """Get Weaviate pool"""
        return self.weaviate_pool if self.enabled else None
    
    async def close_all(self):
        """Close all connection pools"""
        if self.postgres_pool:
            await self.postgres_pool.close()
        if self.redis_pool:
            await self.redis_pool.close()
        # Weaviate pool doesn't need explicit closing
    
    def get_stats(self) -> dict:
        """Get statistics from all pools"""
        stats = {"pooling_enabled": self.enabled}
        
        if self.postgres_pool:
            stats["postgres"] = self.postgres_pool.get_stats()
        if self.redis_pool:
            stats["redis"] = self.redis_pool.get_stats()
        if self.weaviate_pool:
            stats["weaviate"] = self.weaviate_pool.get_stats()
        
        return stats


# Global instance
_pool_manager = None

def get_pool_manager() -> ConnectionPoolManager:
    """Get global connection pool manager"""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = ConnectionPoolManager()
    return _pool_manager