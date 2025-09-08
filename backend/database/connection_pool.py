"\nAsync Database Connection Pool Manager for Sophia AI\nIntegrates with pgBouncer for high-performance connection pooling\n"

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import wraps
from typing import Any, AsyncContextManager

import asyncpg
import redis.asyncio as aioredis
from qdrant_client import AsyncQdrantClient

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database connection configuration"""

    host: str
    port: int
    database: str
    username: str
    password: str
    pool_min_size: int = 10
    pool_max_size: int = 100
    timeout: float = 30.0
    command_timeout: float = 60.0
    ssl_mode: str = "require"

@dataclass
class RedisConfig:
    """Redis cluster configuration"""

    nodes: list
    password: str | None = None
    max_connections: int = 100
    retry_on_timeout: bool = True
    health_check_interval: int = 30

@dataclass
class QdrantConfig:
    """Qdrant configuration"""

    host: str
    port: int = 6333
    api_key: str | None = None
    https: bool = False
    timeout: float = 30.0

class CircuitBreaker:
    """Circuit breaker pattern for database connections"""

    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "closed"

    def call(self, func):

        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == "open":
                if time.time() - self.last_failure_time > self.timeout:
                    self.state = "half_open"
                else:
                    raise Exception("Circuit breaker is open")
            try:
                result = await func(*args, **kwargs)
                if self.state == "half_open":
                    self.state = "closed"
                    self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                if self.failure_count >= self.failure_threshold:
                    self.state = "open"
                raise e

        return wrapper

class ConnectionPoolManager:
    """Manages all database connections with circuit breakers and health checks"""

    def __init__(self):
        self.postgres_pool: asyncpg.Pool | None = None
        self.redis_client: aioredis.Redis | None = None
        self.qdrant_client: AsyncQdrantClient | None = None
        self.postgres_circuit_breaker = CircuitBreaker()
        self.redis_circuit_breaker = CircuitBreaker()
        self.qdrant_circuit_breaker = CircuitBreaker()
        self._health_check_task: asyncio.Task | None = None

    async def initialize(
        self,
        postgres_config: DatabaseConfig,
        redis_config: RedisConfig,
        qdrant_config: QdrantConfig,
    ):
        """Initialize all database connections"""
        logger.info("Initializing database connection pools...")
        await self._init_postgres(postgres_config)
        await self._init_redis(redis_config)
        await self._init_qdrant(qdrant_config)
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("All database connections initialized successfully")

    async def _init_postgres(self, config: DatabaseConfig):
        """Initialize PostgreSQL connection pool via pgBouncer"""
        try:
            dsn = f"postgresql://${DB_USER}:${DB_PASSWORD}@{config.host}:6432/{config.database}?sslmode={config.ssl_mode}&application_name=sophia_ai"
            self.postgres_pool = await asyncpg.create_pool(
                dsn,
                min_size=config.pool_min_size,
                max_size=config.pool_max_size,
                command_timeout=config.command_timeout,
                server_settings={
                    "application_name": "sophia_ai_backend",
                    "timezone": "UTC",
                },
            )
            async with self.postgres_pool.acquire() as conn:
                await conn.execute("SELECT 1")
            logger.info(
                f"PostgreSQL pool initialized with {config.pool_min_size}-{config.pool_max_size} connections"
            )
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL pool: {e}")
            raise

    async def _init_redis(self, config: RedisConfig):
        """Initialize Redis cluster connection"""
        try:
            startup_nodes = [
                {"host": node["host"], "port": node["port"]} for node in config.nodes
            ]
            self.redis_client = aioredis.RedisCluster(
                startup_nodes=startup_nodes,
                password=config.password,
                max_connections=config.max_connections,
                retry_on_timeout=config.retry_on_timeout,
                health_check_interval=config.health_check_interval,
                decode_responses=True,
            )
            await self.redis_client.ping()
            logger.info(f"Redis cluster initialized with {len(config.nodes)} nodes")
        except Exception as e:
            logger.error(f"Failed to initialize Redis cluster: {e}")
            raise

    async def _init_qdrant(self, config: QdrantConfig):
        """Initialize Qdrant client"""
        try:
            self.qdrant_client = AsyncQdrantClient(
                host=config.host,
                port=config.port,
                api_key=config.api_key,
                https=config.https,
                timeout=config.timeout,
            )
            collections = await self.qdrant_client.get_collections()
            logger.info(
                f"Qdrant client initialized, found {len(collections.collections)} collections"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise

    @asynccontextmanager
    async def get_postgres_connection(self) -> AsyncContextManager[asyncpg.Connection]:
        """Get PostgreSQL connection with circuit breaker"""

        @self.postgres_circuit_breaker.call
        async def get_connection():
            if not self.postgres_pool:
                raise Exception("PostgreSQL pool not initialized")
            return await self.postgres_pool.acquire()

        conn = await get_connection()
        try:
            yield conn
        finally:
            await self.postgres_pool.release(conn)

    @asynccontextmanager
    async def get_redis_connection(self) -> AsyncContextManager[aioredis.Redis]:
        """Get Redis connection with circuit breaker"""

        @self.redis_circuit_breaker.call
        async def get_connection():
            if not self.redis_client:
                raise Exception("Redis client not initialized")
            return self.redis_client

        client = await get_connection()
        yield client

    @asynccontextmanager
    async def get_qdrant_connection(self) -> AsyncContextManager[AsyncQdrantClient]:
        """Get Qdrant connection with circuit breaker"""

        @self.qdrant_circuit_breaker.call
        async def get_connection():
            if not self.qdrant_client:
                raise Exception("Qdrant client not initialized")
            return self.qdrant_client

        client = await get_connection()
        yield client

    async def _health_check_loop(self):
        """Periodic health checks for all connections"""
        while True:
            try:
                await asyncio.sleep(30)
                try:
                    async with self.get_postgres_connection() as conn:
                        await conn.execute("SELECT 1")
                    logger.debug("PostgreSQL health check: OK")
                except Exception as e:
                    logger.warning(f"PostgreSQL health check failed: {e}")
                try:
                    async with self.get_redis_connection() as client:
                        await client.ping()
                    logger.debug("Redis health check: OK")
                except Exception as e:
                    logger.warning(f"Redis health check failed: {e}")
                try:
                    async with self.get_qdrant_connection() as client:
                        await client.get_collections()
                    logger.debug("Qdrant health check: OK")
                except Exception as e:
                    logger.warning(f"Qdrant health check failed: {e}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")

    async def get_connection_stats(self) -> dict[str, Any]:
        """Get connection pool statistics"""
        stats = {}
        if self.postgres_pool:
            stats["postgres"] = {
                "size": self.postgres_pool.get_size(),
                "min_size": self.postgres_pool.get_min_size(),
                "max_size": self.postgres_pool.get_max_size(),
                "idle_size": self.postgres_pool.get_idle_size(),
                "circuit_breaker_state": self.postgres_circuit_breaker.state,
                "circuit_breaker_failures": self.postgres_circuit_breaker.failure_count,
            }
        if self.redis_client:
            stats["redis"] = {
                "circuit_breaker_state": self.redis_circuit_breaker.state,
                "circuit_breaker_failures": self.redis_circuit_breaker.failure_count,
            }
        if self.qdrant_client:
            stats["qdrant"] = {
                "circuit_breaker_state": self.qdrant_circuit_breaker.state,
                "circuit_breaker_failures": self.qdrant_circuit_breaker.failure_count,
            }
        return stats

    async def close(self):
        """Close all connections"""
        logger.info("Closing database connections...")
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        if self.postgres_pool:
            await self.postgres_pool.close()
        if self.redis_client:
            await self.redis_client.close()
        if self.qdrant_client:
            await self.qdrant_client.close()
        logger.info("All database connections closed")

connection_manager = ConnectionPoolManager()

async def init_database_connections(
    postgres_config: DatabaseConfig,
    redis_config: RedisConfig,
    qdrant_config: QdrantConfig,
):
    """Initialize the global connection manager"""
    await connection_manager.initialize(postgres_config, redis_config, qdrant_config)

async def get_postgres() -> AsyncContextManager[asyncpg.Connection]:
    """Get PostgreSQL connection"""
    return connection_manager.get_postgres_connection()

async def get_redis() -> AsyncContextManager[aioredis.Redis]:
    """Get Redis connection"""
    return connection_manager.get_redis_connection()

async def get_qdrant() -> AsyncContextManager[AsyncQdrantClient]:
    """Get Qdrant connection"""
    return connection_manager.get_qdrant_connection()

async def close_database_connections():
    """Close all database connections"""
    await connection_manager.close()
