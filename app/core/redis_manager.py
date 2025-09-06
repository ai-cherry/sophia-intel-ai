"""
Enhanced Redis Manager for Sophia-Intel-AI
Provides production-ready Redis operations with connection pooling,
bounded streams, TTL management, and circuit breaker protection.
"""

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import redis.asyncio as aioredis
from redis.asyncio.client import Pipeline
from redis.exceptions import ConnectionError, RedisError, TimeoutError

from app.core.redis_config import PAY_READY_REDIS_CONFIG, RedisConfig, RedisNamespaces, redis_config

logger = logging.getLogger(__name__)


class RedisCircuitBreaker:
    """Circuit breaker for Redis operations"""

    def __init__(self, config):
        self.failure_threshold = config.failure_threshold
        self.recovery_timeout = config.recovery_timeout
        self.expected_exception = config.expected_exception
        self.name = config.name

        self._failure_count = 0
        self._last_failure_time = None
        self._state = "closed"  # closed, open, half_open

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""

        if self._state == "open":
            if self._should_attempt_reset():
                self._state = "half_open"
            else:
                raise ConnectionError(f"Circuit breaker {self.name} is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self._last_failure_time is None:
            return True
        return time.time() - self._last_failure_time >= self.recovery_timeout

    def _on_success(self):
        """Reset circuit breaker on successful operation"""
        self._failure_count = 0
        self._state = "closed"

    def _on_failure(self):
        """Handle failure and potentially open circuit"""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._failure_count >= self.failure_threshold:
            self._state = "open"
            logger.warning(
                f"Circuit breaker {self.name} opened after {self._failure_count} failures"
            )


class RedisHealthMonitor:
    """Redis health monitoring and metrics collection"""

    def __init__(self, redis_manager):
        self.redis_manager = redis_manager
        self.metrics = {
            "total_operations": 0,
            "failed_operations": 0,
            "slow_operations": 0,
            "memory_usage": 0,
            "connected_clients": 0,
            "connection_pool_usage": 0,
            "last_health_check": None,
            "avg_response_time": 0.0,
        }
        self._response_times = []

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        start_time = time.time()

        try:
            # Basic connectivity test
            await self.redis_manager.redis.ping()

            # Get Redis info
            info = await self.redis_manager.redis.info()

            # Update metrics
            self.metrics.update(
                {
                    "memory_usage": info.get("used_memory", 0),
                    "connected_clients": info.get("connected_clients", 0),
                    "last_health_check": datetime.utcnow().isoformat(),
                    "redis_version": info.get("redis_version", "unknown"),
                    "uptime_seconds": info.get("uptime_in_seconds", 0),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                }
            )

            # Calculate hit ratio
            hits = self.metrics["keyspace_hits"]
            misses = self.metrics["keyspace_misses"]
            total = hits + misses
            hit_ratio = hits / total if total > 0 else 0
            self.metrics["cache_hit_ratio"] = hit_ratio

            # Check memory thresholds
            max_memory = info.get("maxmemory", 0)
            if max_memory > 0:
                memory_usage_percent = self.metrics["memory_usage"] / max_memory
                self.metrics["memory_usage_percent"] = memory_usage_percent

                # Alert on high memory usage
                config = self.redis_manager.config.memory
                if memory_usage_percent >= config.critical_threshold:
                    logger.error(f"Redis memory usage critical: {memory_usage_percent:.2%}")
                elif memory_usage_percent >= config.warning_threshold:
                    logger.warning(f"Redis memory usage high: {memory_usage_percent:.2%}")

            response_time = time.time() - start_time
            self._record_response_time(response_time)

            return {"healthy": True, "response_time": response_time, "metrics": self.metrics}

        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {"healthy": False, "error": str(e), "response_time": time.time() - start_time}

    def _record_response_time(self, response_time: float):
        """Record response time for averaging"""
        self._response_times.append(response_time)

        # Keep only last 100 measurements
        if len(self._response_times) > 100:
            self._response_times = self._response_times[-100:]

        self.metrics["avg_response_time"] = sum(self._response_times) / len(self._response_times)

        # Track slow operations
        if response_time > self.redis_manager.config.monitoring.slow_query_threshold:
            self.metrics["slow_operations"] += 1


class RedisManager:
    """Enhanced Redis manager with production optimizations"""

    def __init__(self, config: Optional[RedisConfig] = None):
        self.config = config or redis_config
        self.redis: Optional[aioredis.Redis] = None
        self.circuit_breaker = RedisCircuitBreaker(self.config.circuit_breaker)
        self.health_monitor = RedisHealthMonitor(self)
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize Redis connection with optimized pool"""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:  # Double-check
                return

            try:
                # Create connection pool with optimized settings
                pool = aioredis.ConnectionPool.from_url(
                    self.config.url,
                    max_connections=self.config.pool.max_connections,
                    retry_on_timeout=self.config.pool.retry_on_timeout,
                    socket_keepalive=self.config.pool.socket_keepalive,
                    socket_keepalive_options=self.config.pool.socket_keepalive_options,
                    socket_connect_timeout=self.config.pool.connection_timeout,
                    socket_timeout=self.config.pool.socket_timeout,
                    decode_responses=False,  # Handle binary data properly
                )

                self.redis = aioredis.Redis(connection_pool=pool, db=self.config.db)

                # Test connection
                await self.circuit_breaker.call(self.redis.ping)

                # Configure memory management
                if self.config.memory.max_memory_mb:
                    max_memory = f"{self.config.memory.max_memory_mb}mb"
                    await self.redis.config_set("maxmemory", max_memory)
                    await self.redis.config_set(
                        "maxmemory-policy", self.config.memory.default_policy
                    )

                self._initialized = True
                logger.info(
                    f"Redis manager initialized with pool size {self.config.pool.max_connections}"
                )

            except Exception as e:
                logger.error(f"Failed to initialize Redis manager: {e}")
                raise

    async def close(self):
        """Close Redis connections gracefully"""
        if self.redis:
            await self.redis.close()
            await self.redis.connection_pool.disconnect()
            self._initialized = False
            logger.info("Redis manager closed")

    @asynccontextmanager
    async def get_connection(self):
        """Get Redis connection with circuit breaker protection"""
        if not self._initialized:
            await self.initialize()

        try:
            yield self.redis
        except (ConnectionError, TimeoutError, OSError) as e:
            await self._handle_connection_error(e)
            raise

    async def _handle_connection_error(self, error):
        """Handle connection errors and potentially reinitialize"""
        logger.warning(f"Redis connection error: {error}")
        self.health_monitor.metrics["failed_operations"] += 1

        # Try to reinitialize connection
        try:
            await self.close()
            await self.initialize()
        except Exception as e:
            logger.error(f"Failed to reinitialize Redis connection: {e}")

    # Cache operations with TTL management

    async def set_with_ttl(
        self, key: str, value: Any, ttl: Optional[int] = None, namespace: str = None
    ) -> bool:
        """Set key with automatic TTL based on pattern"""
        full_key = RedisNamespaces.format_key(namespace, key) if namespace else key

        if ttl is None:
            ttl = self.config.get_ttl_for_key_pattern(full_key)

        async with self.get_connection() as redis:
            return await self.circuit_breaker.call(redis.setex, full_key, ttl, value)

    async def get(self, key: str, namespace: str = None) -> Any:
        """Get value with namespace support"""
        full_key = RedisNamespaces.format_key(namespace, key) if namespace else key

        async with self.get_connection() as redis:
            return await self.circuit_breaker.call(redis.get, full_key)

    async def delete(self, key: str, namespace: str = None) -> int:
        """Delete key with namespace support"""
        full_key = RedisNamespaces.format_key(namespace, key) if namespace else key

        async with self.get_connection() as redis:
            return await self.circuit_breaker.call(redis.delete, full_key)

    async def exists(self, key: str, namespace: str = None) -> bool:
        """Check if key exists"""
        full_key = RedisNamespaces.format_key(namespace, key) if namespace else key

        async with self.get_connection() as redis:
            result = await self.circuit_breaker.call(redis.exists, full_key)
            return bool(result)

    # Bounded stream operations

    async def stream_add(
        self,
        stream: str,
        fields: Dict[str, Any],
        message_id: str = "*",
        maxlen: Optional[int] = None,
        approximate: bool = True,
    ) -> str:
        """Add to stream with bounded length"""

        if maxlen is None:
            stream_config = self.config.get_stream_config(stream)
            maxlen = stream_config["maxlen"]
            approximate = stream_config["approximate"]

        async with self.get_connection() as redis:
            return await self.circuit_breaker.call(
                redis.xadd, stream, fields, id=message_id, maxlen=maxlen, approximate=approximate
            )

    async def stream_read(
        self, streams: Dict[str, str], count: Optional[int] = None, block: Optional[int] = None
    ) -> List[Any]:
        """Read from streams with configurable blocking"""

        if count is None:
            count = self.config.streams.batch_size

        if block is None:
            block = self.config.streams.block_timeout

        async with self.get_connection() as redis:
            return await self.circuit_breaker.call(
                redis.xread, streams=streams, count=count, block=block
            )

    async def stream_create_group(
        self, stream: str, group: str, id: str = "0-0", mkstream: bool = True
    ) -> bool:
        """Create consumer group for stream"""
        async with self.get_connection() as redis:
            try:
                await self.circuit_breaker.call(
                    redis.xgroup_create, stream, group, id=id, mkstream=mkstream
                )
                return True
            except aioredis.ResponseError as e:
                if "BUSYGROUP" in str(e):
                    return True  # Group already exists
                raise

    async def stream_read_group(
        self,
        group: str,
        consumer: str,
        streams: Dict[str, str],
        count: Optional[int] = None,
        block: Optional[int] = None,
        noack: bool = False,
    ) -> List[Any]:
        """Read from stream as consumer group member"""

        if count is None:
            count = self.config.streams.batch_size

        if block is None:
            block = self.config.streams.block_timeout

        async with self.get_connection() as redis:
            return await self.circuit_breaker.call(
                redis.xreadgroup,
                group,
                consumer,
                streams=streams,
                count=count,
                block=block,
                noack=noack,
            )

    async def stream_ack(self, stream: str, group: str, message_ids: List[str]) -> int:
        """Acknowledge processed messages"""
        async with self.get_connection() as redis:
            return await self.circuit_breaker.call(redis.xack, stream, group, *message_ids)

    async def stream_trim(self, stream: str, maxlen: int, approximate: bool = True) -> int:
        """Trim stream to specified length"""
        async with self.get_connection() as redis:
            return await self.circuit_breaker.call(
                redis.xtrim, stream, maxlen=maxlen, approximate=approximate
            )

    # Pay Ready business cycle optimizations

    async def pay_ready_cache_set(self, account_id: str, data: Dict[str, Any]) -> bool:
        """Cache Pay Ready account data with business cycle TTL"""
        key = f"account:{account_id}"
        ttl = self.config.ttl.pay_ready_snapshot

        # Extend TTL during month-end processing
        if self._is_month_end_period():
            ttl *= PAY_READY_REDIS_CONFIG["month_end_multiplier"]

        return await self.set_with_ttl(key, data, ttl, namespace=RedisNamespaces.PAY_READY)

    async def pay_ready_bulk_cache(self, accounts: Dict[str, Dict[str, Any]]) -> int:
        """Bulk cache Pay Ready accounts for efficiency"""
        async with self.get_connection() as redis:
            async with redis.pipeline() as pipe:
                count = 0
                for account_id, data in accounts.items():
                    key = RedisNamespaces.format_key(
                        RedisNamespaces.PAY_READY, f"account:{account_id}"
                    )
                    ttl = self.config.ttl.pay_ready_snapshot

                    if self._is_month_end_period():
                        ttl *= PAY_READY_REDIS_CONFIG["month_end_multiplier"]

                    pipe.setex(key, ttl, data)
                    count += 1

                await pipe.execute()
                return count

    def _is_month_end_period(self) -> bool:
        """Check if we're in month-end processing period"""
        now = datetime.utcnow()
        # Last 3 days of month and first 2 days of next month
        return now.day >= 28 or now.day <= 2

    # WebSocket support

    async def websocket_state_set(self, client_id: str, state: Dict[str, Any]) -> bool:
        """Set WebSocket client state with appropriate TTL"""
        return await self.set_with_ttl(
            f"client:{client_id}",
            state,
            self.config.ttl.websocket_state,
            namespace=RedisNamespaces.WEBSOCKET,
        )

    async def websocket_state_get(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get WebSocket client state"""
        return await self.get(f"client:{client_id}", namespace=RedisNamespaces.WEBSOCKET)

    # Memory management

    async def cleanup_expired_keys(self, pattern: str = "*", scan_count: int = 100) -> int:
        """Clean up expired keys matching pattern"""
        count = 0
        async with self.get_connection() as redis:
            async for key in redis.scan_iter(match=pattern, count=scan_count):
                ttl = await redis.ttl(key)
                if ttl == -1:  # Key without expiration
                    # Set default TTL based on pattern
                    default_ttl = self.config.get_ttl_for_key_pattern(
                        key.decode() if isinstance(key, bytes) else key
                    )
                    await redis.expire(key, default_ttl)
                    count += 1
        return count

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get detailed memory usage statistics"""
        async with self.get_connection() as redis:
            info = await redis.info(section="memory")
            keyspace = await redis.info(section="keyspace")

            return {
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "used_memory_rss": info.get("used_memory_rss", 0),
                "used_memory_peak": info.get("used_memory_peak", 0),
                "maxmemory": info.get("maxmemory", 0),
                "keyspace_info": keyspace,
                "memory_usage_percent": self.health_monitor.metrics.get("memory_usage_percent", 0),
            }

    # Pipeline operations for bulk processing

    @asynccontextmanager
    async def pipeline(self):
        """Get Redis pipeline for bulk operations"""
        async with self.get_connection() as redis:
            async with redis.pipeline() as pipe:
                yield pipe

    # Health and monitoring

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return await self.health_monitor.health_check()

    async def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.health_monitor.metrics.copy()


# Global Redis manager instance
redis_manager = RedisManager()


# Convenience functions for common patterns
async def get_cached(key: str, namespace: str = RedisNamespaces.CACHE) -> Any:
    """Get cached value"""
    return await redis_manager.get(key, namespace=namespace)


async def set_cached(
    key: str, value: Any, ttl: Optional[int] = None, namespace: str = RedisNamespaces.CACHE
) -> bool:
    """Set cached value with TTL"""
    return await redis_manager.set_with_ttl(key, value, ttl, namespace=namespace)


async def cache_or_compute(
    key: str,
    compute_func,
    ttl: Optional[int] = None,
    namespace: str = RedisNamespaces.CACHE,
    *args,
    **kwargs,
) -> Any:
    """Get from cache or compute and cache the result"""
    # Try to get from cache first
    cached_value = await get_cached(key, namespace=namespace)
    if cached_value is not None:
        return cached_value

    # Compute the value
    computed_value = await compute_func(*args, **kwargs)

    # Cache the result
    await set_cached(key, computed_value, ttl, namespace=namespace)

    return computed_value
