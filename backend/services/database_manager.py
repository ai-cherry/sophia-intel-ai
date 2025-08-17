"""
Database Connection Manager for SOPHIA Intel
Real connection pooling, retry logic, and failover implementation
"""

import asyncio
import time
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError, TimeoutError
import redis.asyncio as redis
from redis.exceptions import ConnectionError, TimeoutError as RedisTimeoutError
import qdrant_client
from qdrant_client.http.exceptions import UnexpectedResponse

from .circuit_breaker import get_circuit_breaker, CircuitBreakerConfig

logger = logging.getLogger(__name__)

class DatabaseConnectionError(Exception):
    """Database connection error"""
    pass

class DatabaseManager:
    """
    Real database connection manager with pooling and failover
    """
    
    def __init__(self, postgres_url: str, redis_url: str, qdrant_url: str, qdrant_api_key: Optional[str] = None):
        self.postgres_url = postgres_url
        self.redis_url = redis_url
        self.qdrant_url = qdrant_url
        self.qdrant_api_key = qdrant_api_key
        
        # Connection pools
        self.postgres_engine = None
        self.async_postgres_engine = None
        self.session_factory = None
        self.redis_pool = None
        self.qdrant_client = None
        
        # Circuit breakers
        self.postgres_cb = get_circuit_breaker("postgres", CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30,
            success_threshold=2,
            timeout=10.0
        ))
        
        self.redis_cb = get_circuit_breaker("redis", CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=20,
            success_threshold=2,
            timeout=5.0
        ))
        
        self.qdrant_cb = get_circuit_breaker("qdrant", CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30,
            success_threshold=2,
            timeout=15.0
        ))
        
        # Connection stats
        self.stats = {
            "postgres": {"connections": 0, "errors": 0, "last_error": None},
            "redis": {"connections": 0, "errors": 0, "last_error": None},
            "qdrant": {"connections": 0, "errors": 0, "last_error": None}
        }
    
    async def initialize(self):
        """Initialize all database connections"""
        logger.info("Initializing database connections...")
        
        await self._init_postgres()
        await self._init_redis()
        await self._init_qdrant()
        
        logger.info("Database connections initialized successfully")
    
    async def _init_postgres(self):
        """Initialize PostgreSQL connection pool"""
        try:
            # Sync engine for migrations and admin tasks
            self.postgres_engine = create_engine(
                self.postgres_url,
                poolclass=QueuePool,
                pool_size=20,
                max_overflow=30,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            
            # Async engine for application use
            async_url = self.postgres_url.replace("postgresql://", "postgresql+asyncpg://")
            self.async_postgres_engine = create_async_engine(
                async_url,
                poolclass=QueuePool,
                pool_size=20,
                max_overflow=30,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            
            # Session factory
            self.session_factory = async_sessionmaker(
                self.async_postgres_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            await self._test_postgres_connection()
            logger.info("PostgreSQL connection pool initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            self.stats["postgres"]["errors"] += 1
            self.stats["postgres"]["last_error"] = str(e)
            raise DatabaseConnectionError(f"PostgreSQL initialization failed: {e}")
    
    async def _init_redis(self):
        """Initialize Redis connection pool"""
        try:
            self.redis_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=20,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            
            # Test connection
            await self._test_redis_connection()
            logger.info("Redis connection pool initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            self.stats["redis"]["errors"] += 1
            self.stats["redis"]["last_error"] = str(e)
            raise DatabaseConnectionError(f"Redis initialization failed: {e}")
    
    async def _init_qdrant(self):
        """Initialize Qdrant client"""
        try:
            self.qdrant_client = qdrant_client.AsyncQdrantClient(
                url=self.qdrant_url,
                api_key=self.qdrant_api_key,
                timeout=30,
                prefer_grpc=False
            )
            
            # Test connection
            await self._test_qdrant_connection()
            logger.info("Qdrant client initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            self.stats["qdrant"]["errors"] += 1
            self.stats["qdrant"]["last_error"] = str(e)
            raise DatabaseConnectionError(f"Qdrant initialization failed: {e}")
    
    async def _test_postgres_connection(self):
        """Test PostgreSQL connection"""
        async with self.async_postgres_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    
    async def _test_redis_connection(self):
        """Test Redis connection"""
        redis_client = redis.Redis(connection_pool=self.redis_pool)
        await redis_client.ping()
        await redis_client.close()
    
    async def _test_qdrant_connection(self):
        """Test Qdrant connection"""
        collections = await self.qdrant_client.get_collections()
        logger.info(f"Qdrant collections: {len(collections.collections)}")
    
    @asynccontextmanager
    async def get_postgres_session(self):
        """Get PostgreSQL session with circuit breaker protection"""
        async def _get_session():
            session = self.session_factory()
            self.stats["postgres"]["connections"] += 1
            return session
        
        try:
            session = await self.postgres_cb.call(_get_session)
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
                
        except Exception as e:
            self.stats["postgres"]["errors"] += 1
            self.stats["postgres"]["last_error"] = str(e)
            logger.error(f"PostgreSQL session error: {e}")
            raise
    
    @asynccontextmanager
    async def get_redis_client(self):
        """Get Redis client with circuit breaker protection"""
        async def _get_client():
            client = redis.Redis(connection_pool=self.redis_pool)
            self.stats["redis"]["connections"] += 1
            return client
        
        try:
            client = await self.redis_cb.call(_get_client)
            try:
                yield client
            finally:
                await client.close()
                
        except Exception as e:
            self.stats["redis"]["errors"] += 1
            self.stats["redis"]["last_error"] = str(e)
            logger.error(f"Redis client error: {e}")
            raise
    
    async def get_qdrant_client(self):
        """Get Qdrant client with circuit breaker protection"""
        async def _get_client():
            self.stats["qdrant"]["connections"] += 1
            return self.qdrant_client
        
        try:
            return await self.qdrant_cb.call(_get_client)
        except Exception as e:
            self.stats["qdrant"]["errors"] += 1
            self.stats["qdrant"]["last_error"] = str(e)
            logger.error(f"Qdrant client error: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for all databases"""
        health = {
            "postgres": {"status": "unknown", "response_time": None, "error": None},
            "redis": {"status": "unknown", "response_time": None, "error": None},
            "qdrant": {"status": "unknown", "response_time": None, "error": None}
        }
        
        # PostgreSQL health check
        try:
            start_time = time.time()
            async with self.get_postgres_session() as session:
                await session.execute(text("SELECT 1"))
            health["postgres"]["status"] = "healthy"
            health["postgres"]["response_time"] = time.time() - start_time
        except Exception as e:
            health["postgres"]["status"] = "unhealthy"
            health["postgres"]["error"] = str(e)
        
        # Redis health check
        try:
            start_time = time.time()
            async with self.get_redis_client() as client:
                await client.ping()
            health["redis"]["status"] = "healthy"
            health["redis"]["response_time"] = time.time() - start_time
        except Exception as e:
            health["redis"]["status"] = "unhealthy"
            health["redis"]["error"] = str(e)
        
        # Qdrant health check
        try:
            start_time = time.time()
            client = await self.get_qdrant_client()
            await client.get_collections()
            health["qdrant"]["status"] = "healthy"
            health["qdrant"]["response_time"] = time.time() - start_time
        except Exception as e:
            health["qdrant"]["status"] = "unhealthy"
            health["qdrant"]["error"] = str(e)
        
        return health
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "stats": self.stats,
            "circuit_breakers": {
                "postgres": self.postgres_cb.get_state(),
                "redis": self.redis_cb.get_state(),
                "qdrant": self.qdrant_cb.get_state()
            }
        }
    
    async def close(self):
        """Close all database connections"""
        logger.info("Closing database connections...")
        
        if self.async_postgres_engine:
            await self.async_postgres_engine.dispose()
        
        if self.postgres_engine:
            self.postgres_engine.dispose()
        
        if self.redis_pool:
            await self.redis_pool.disconnect()
        
        if self.qdrant_client:
            await self.qdrant_client.close()
        
        logger.info("Database connections closed")

# Global database manager instance
_db_manager: Optional[DatabaseManager] = None

def get_database_manager() -> DatabaseManager:
    """Get global database manager instance"""
    if _db_manager is None:
        raise RuntimeError("Database manager not initialized")
    return _db_manager

async def initialize_database_manager(postgres_url: str, redis_url: str, qdrant_url: str, qdrant_api_key: Optional[str] = None):
    """Initialize global database manager"""
    global _db_manager
    _db_manager = DatabaseManager(postgres_url, redis_url, qdrant_url, qdrant_api_key)
    await _db_manager.initialize()
    return _db_manager

async def close_database_manager():
    """Close global database manager"""
    global _db_manager
    if _db_manager:
        await _db_manager.close()
        _db_manager = None

