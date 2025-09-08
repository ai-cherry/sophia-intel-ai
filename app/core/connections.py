"""
Centralized Connection Manager
Provides connection pooling for HTTP, Redis, and database connections
Addresses critical performance bottlenecks identified in architectural audit
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Optional

import aiohttp
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


@dataclass
class ConnectionConfig:
    """Configuration for connection pools"""

    # HTTP settings
    http_pool_size: int = 100
    http_timeout: int = 30
    http_keepalive_timeout: int = 15

    # Redis settings
    redis_pool_size: int = 50
    redis_max_connections: int = 100
    redis_url: str = "redis://localhost:6379"

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 0.5


class ConnectionManager:
    """
    Singleton connection manager for all external connections.
    Ensures proper connection pooling and resource management.
    """

    _instance: Optional["ConnectionManager"] = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: Optional[ConnectionConfig] = None):
        if not hasattr(self, "_initialized"):
            self.config = config or ConnectionConfig()
            self._http_session: aiohttp.Optional[ClientSession] = None
            self._redis_pool: aioredis.Optional[Redis] = None
            self._initialized = False
            self._metrics = {
                "http_requests": 0,
                "redis_operations": 0,
                "connection_errors": 0,
                "pool_exhaustion": 0,
            }

    async def initialize(self):
        """Initialize all connection pools"""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            try:
                # Initialize HTTP session with connection pooling
                connector = aiohttp.TCPConnector(
                    limit=self.config.http_pool_size,
                    limit_per_host=30,
                    ttl_dns_cache=300,
                    keepalive_timeout=self.config.http_keepalive_timeout,
                )

                timeout = aiohttp.ClientTimeout(
                    total=self.config.http_timeout, connect=5, sock_read=10
                )

                self._http_session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers={
                        "User-Agent": "Sophia-Intel-AI/2.1.0",
                        "Accept": "application/json",
                    },
                )

                # Initialize Redis connection pool
                self._redis_pool = await aioredis.from_url(
                    "redis://localhost:6379", decode_responses=True
                )

                # Test connections
                await self._redis_pool.ping()

                self._initialized = True
                logger.info("✅ Connection pools initialized successfully")

            except Exception as e:
                logger.error(f"❌ Failed to initialize connection pools: {e}")
                raise

    async def close(self):
        """Close all connection pools"""
        async with self._lock:
            if self._http_session:
                await self._http_session.close()
                self._http_session = None

            if self._redis_pool:
                await self._redis_pool.close()
                self._redis_pool = None

            self._initialized = False
            logger.info("Connection pools closed")

    # HTTP Methods

    async def get_http_session(self) -> aiohttp.ClientSession:
        """Get HTTP session with connection pooling"""
        if not self._initialized:
            await self.initialize()
        return self._http_session

    async def http_get(self, url: str, **kwargs) -> dict[str, Any]:
        """Perform HTTP GET with connection pooling and retry"""
        return await self._http_request("GET", url, **kwargs)

    async def http_post(self, url: str, **kwargs) -> dict[str, Any]:
        """Perform HTTP POST with connection pooling and retry"""
        return await self._http_request("POST", url, **kwargs)

    async def _http_request(self, method: str, url: str, **kwargs) -> dict[str, Any]:
        """Internal HTTP request with retry logic"""
        session = await self.get_http_session()
        self._metrics["http_requests"] += 1

        for attempt in range(self.config.max_retries):
            try:
                async with session.request(method, url, **kwargs) as response:
                    response.raise_for_status()
                    return await response

            except aiohttp.ClientError as e:
                self._metrics["connection_errors"] += 1
                if attempt == self.config.max_retries - 1:
                    logger.error(
                        f"HTTP request failed after {self.config.max_retries} attempts: {e}"
                    )
                    raise
                await asyncio.sleep(self.config.retry_delay * (2**attempt))

    # Redis Methods

    async def get_redis(self) -> aioredis.Redis:
        """Get Redis connection from pool"""
        if not self._initialized:
            await self.initialize()
        self._metrics["redis_operations"] += 1
        return self._redis_pool

    async def redis_get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        redis = await self.get_redis()
        return await redis.get(key)

    async def redis_set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set value in Redis with optional expiration"""
        redis = await self.get_redis()
        return await redis.set(key, value, ex=ex)

    async def redis_delete(self, key: str) -> int:
        """Delete key from Redis"""
        redis = await self.get_redis()
        return await redis.delete(key)

    async def redis_exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        redis = await self.get_redis()
        return bool(await redis.exists(key))

    # Context Managers

    @asynccontextmanager
    async def http_session_context(self):
        """Context manager for HTTP session"""
        session = await self.get_http_session()
        try:
            yield session
        except Exception as e:
            self._metrics["connection_errors"] += 1
            raise e

    @asynccontextmanager
    async def redis_context(self):
        """Context manager for Redis operations"""
        redis = await self.get_redis()
        try:
            yield redis
        except Exception as e:
            self._metrics["connection_errors"] += 1
            raise e

    # Metrics

    def get_metrics(self) -> dict[str, Any]:
        """Get connection pool metrics"""
        metrics = self._metrics.copy()

        if self._http_session:
            connector = self._http_session.connector
            if connector:
                metrics["http_connections"] = len(connector._conns)
                metrics["http_limit"] = connector.limit

        return metrics

    def reset_metrics(self):
        """Reset metrics counters"""
        for key in self._metrics:
            if isinstance(self._metrics[key], int):
                self._metrics[key] = 0


# Global instance
_connection_manager: Optional[ConnectionManager] = None


async def get_connection_manager() -> ConnectionManager:
    """Get or create the global connection manager"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
        await _connection_manager.initialize()
    return _connection_manager


# Convenience functions


async def http_get(url: str, **kwargs) -> dict[str, Any]:
    """Convenience function for HTTP GET"""
    manager = await get_connection_manager()
    return await manager.http_get(url, **kwargs)


async def http_post(url: str, **kwargs) -> dict[str, Any]:
    """Convenience function for HTTP POST"""
    manager = await get_connection_manager()
    return await manager.http_post(url, **kwargs)


async def redis_get(key: str) -> Optional[str]:
    """Convenience function for Redis GET"""
    manager = await get_connection_manager()
    return await manager.redis_get(key)


async def redis_set(key: str, value: str, ex: Optional[int] = None) -> bool:
    """Convenience function for Redis SET"""
    manager = await get_connection_manager()
    return await manager.redis_set(key, value, ex=ex)


# Migration helpers for existing code


class MigrationHelper:
    """Helper class to migrate existing synchronous code"""

    @staticmethod
    async def replace_requests_with_async(code: str) -> str:
        """Replace requests.get/post with async equivalents"""
        replacements = [
            ("await http_get(", "await http_get("),
            ("await http_post(", "await http_post("),
            ("await get_connection_manager().get_redis().get_redis("),
        ]

        for old, new in replacements:
            code = code.replace(old, new)

        return code

    @staticmethod
    async def wrap_sync_redis(sync_redis_client) -> aioredis.Redis:
        """Wrap synchronous Redis client with async pool"""
        manager = await get_connection_manager()
        return await manager.get_redis()
