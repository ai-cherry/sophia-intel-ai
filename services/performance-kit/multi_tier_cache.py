"""
4-Tier Caching System with Progressive Degradation and Coherency
L1: Process memory (TTLCache) -> L2: Redis hot -> L3: Redis warm (compressed) -> L4: PostgreSQL
"""
from cachetools import TTLCache
import redis.asyncio as redis
import asyncpg
import snappy  # For L3 compression
import msgpack  # For efficient serialization
import hashlib
import asyncio
from typing import Optional, Any, Dict, List, Union
from dataclasses import dataclass, field
import time
import logging
import json
from contextlib import asynccontextmanager
import re
logger = logging.getLogger(__name__)
@dataclass
class CacheConfig:
    # L1: Process memory settings
    l1_max_size: int = 10000  # Larger cache for better hit rates
    l1_ttl: int = 60  # 1 minute
    # L2: Redis hot tier (uncompressed, fast access)
    l2_ttl: int = 300  # 5 minutes
    l2_max_connections: int = 50
    # L3: Redis warm tier (compressed, space efficient)
    l3_ttl: int = 3600  # 1 hour
    l3_max_connections: int = 20
    # L4: PostgreSQL persistent
    l4_default_ttl: int = 86400  # 24 hours
    # Performance optimizations
    enable_compression: bool = True
    compression_threshold: int = 1024  # Compress if > 1KB
    # Coherency and reliability
    enable_pub_sub_invalidation: bool = True
    stale_while_revalidate: bool = True
    grace_period: int = 30  # Seconds for stale-while-revalidate
    # Redis connection settings
    redis_socket_keepalive: bool = True
    redis_socket_timeout: int = 5
@dataclass
class CacheMetrics:
    l1_hits: int = 0
    l1_misses: int = 0
    l2_hits: int = 0
    l2_misses: int = 0
    l3_hits: int = 0
    l3_misses: int = 0
    l4_hits: int = 0
    l4_misses: int = 0
    total_misses: int = 0
    redis_errors: int = 0
    postgres_errors: int = 0
    compression_saves_bytes: int = 0
    promotion_operations: int = 0
    invalidation_operations: int = 0
class OptimizedMultiTierCache:
    """
    4-tier cache with progressive degradation and coherency
    Features:
    - L1: TTLCache for hot data
    - L2: Redis uncompressed for warm data
    - L3: Redis compressed for space efficiency
    - L4: PostgreSQL for persistence
    - Stale-while-revalidate support
    - Pub/sub invalidation
    - Comprehensive metrics
    """
    def __init__(self, config: CacheConfig):
        self.config = config
        # L1: Process memory cache
        self.l1_cache = TTLCache(
            maxsize=config.l1_max_size,
            ttl=config.l1_ttl
        )
        # L2: Redis hot tier (uncompressed)
        self.redis_hot = redis.Redis(
            decode_responses=False,
            max_connections=config.l2_max_connections,
            socket_keepalive=config.redis_socket_keepalive,
            socket_timeout=config.redis_socket_timeout,
            socket_connect_timeout=config.redis_socket_timeout,
            socket_keepalive_options={
                1: 1,  # TCP_KEEPIDLE
                2: 3,  # TCP_KEEPINTVL  
                3: 5,  # TCP_KEEPCNT
            } if config.redis_socket_keepalive else {}
        )
        # L3: Redis warm tier (compressed)
        self.redis_warm = redis.Redis(
            db=1,  # Separate database
            decode_responses=False,
            max_connections=config.l3_max_connections,
            socket_keepalive=config.redis_socket_keepalive,
            socket_timeout=config.redis_socket_timeout
        )
        # L4: PostgreSQL pool (set externally)
        self.pg_pool: Optional[asyncpg.Pool] = None
        # Metrics and state
        self._metrics = CacheMetrics()
        self._invalidation_listener_task: Optional[asyncio.Task] = None
        self._background_tasks: set = set()
        # Setup invalidation listener if enabled
        if config.enable_pub_sub_invalidation:
            self._setup_invalidation_listener()
    async def initialize_postgres(self, pg_pool: asyncpg.Pool):
        """Initialize PostgreSQL connection pool and create tables"""
        self.pg_pool = pg_pool
        async with pg_pool.acquire() as conn:
            # Create cache table with optimized schema
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_kv (
                    key VARCHAR(255) PRIMARY KEY,
                    value BYTEA NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    access_count INTEGER DEFAULT 1,
                    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            # Create indexes for performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_expires_at 
                ON cache_kv (expires_at) 
                WHERE expires_at > NOW();
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_last_accessed 
                ON cache_kv (last_accessed);
            """)
            logger.info("Cache PostgreSQL tables and indexes initialized")
    async def get(
        self, 
        key: str, 
        refresh_fn: Optional[callable] = None,
        ttl_override: Optional[Dict[str, int]] = None
    ) -> Optional[Any]:
        """
        Hierarchical cache lookup with stale-while-revalidate support
        Args:
            key: Cache key
            refresh_fn: Optional function to refresh stale data
            ttl_override: Optional TTL overrides for each tier
        Returns:
            Cached value or None if not found
        """
        cache_key = self._hash_key(key)
        # L1: Hot path optimization
        if cache_key in self.l1_cache:
            self._metrics.l1_hits += 1
            logger.debug(f"L1 cache hit for key: {key}")
            return self.l1_cache[cache_key]
        self._metrics.l1_misses += 1
        # L2: Redis hot tier with TTL check for stale-while-revalidate
        try:
            async with self.redis_hot.pipeline() as pipe:
                pipe.get(f"hot:{cache_key}")
                pipe.ttl(f"hot:{cache_key}")
                results = await pipe.execute()
                value_bytes, ttl_remaining = results
                if value_bytes:
                    self._metrics.l2_hits += 1
                    deserialized = msgpack.unpackb(value_bytes)
                    # Stale-while-revalidate logic
                    if (self.config.stale_while_revalidate and 
                        refresh_fn and 
                        ttl_remaining < self.config.grace_period):
                        # Return stale data immediately, refresh in background
                        self._schedule_background_refresh(key, refresh_fn, ttl_override)
                    # Promote to L1
                    self.l1_cache[cache_key] = deserialized
                    logger.debug(f"L2 cache hit for key: {key}")
                    return deserialized
        except redis.RedisError as e:
            self._metrics.redis_errors += 1
            logger.warning(f"L2 cache error for key {key}: {e}")
        self._metrics.l2_misses += 1
        # L3: Compressed warm tier
        try:
            compressed_bytes = await self.redis_warm.get(f"warm:{cache_key}")
            if compressed_bytes:
                self._metrics.l3_hits += 1
                # Decompress and deserialize
                decompressed = snappy.decompress(compressed_bytes)
                value = msgpack.unpackb(decompressed)
                # Promote to higher tiers asynchronously
                self._schedule_promotion_to_hot(cache_key, value, ttl_override)
                logger.debug(f"L3 cache hit for key: {key}")
                return value
        except (redis.RedisError, snappy.UncompressError) as e:
            self._metrics.redis_errors += 1
            logger.warning(f"L3 cache error for key {key}: {e}")
        self._metrics.l3_misses += 1
        # L4: PostgreSQL persistent with access tracking
        if self.pg_pool:
            try:
                async with self.pg_pool.acquire() as conn:
                    # Optimized query with access count update
                    row = await conn.fetchrow("""
                        UPDATE cache_kv 
                        SET access_count = access_count + 1,
                            last_accessed = NOW()
                        WHERE key = $1 
                        AND expires_at > NOW()
                        RETURNING value, expires_at
                    """, cache_key)
                    if row:
                        self._metrics.l4_hits += 1
                        value = msgpack.unpackb(row['value'])
                        # Full promotion cascade
                        self._schedule_promotion_all_tiers(cache_key, value, ttl_override)
                        logger.debug(f"L4 cache hit for key: {key}")
                        return value
            except Exception as e:
                self._metrics.postgres_errors += 1
                logger.warning(f"L4 cache error for key {key}: {e}")
        self._metrics.l4_misses += 1
        self._metrics.total_misses += 1
        logger.debug(f"Cache miss for key: {key}")
        return None
    async def set(
        self,
        key: str,
        value: Any,
        ttl_override: Optional[Dict[str, int]] = None
    ):
        """
        Write-through caching with tier-specific TTLs and compression
        Args:
            key: Cache key
            value: Value to cache
            ttl_override: Optional TTL overrides for each tier
        """
        cache_key = self._hash_key(key)
        # Serialize once for efficiency
        serialized = msgpack.packb(value)
        # L1: Always write immediately for hot access
        self.l1_cache[cache_key] = value
        # Determine compression strategy
        should_compress = (
            self.config.enable_compression and
            len(serialized) > self.config.compression_threshold
        )
        # L2: Hot tier - uncompressed for speed
        l2_ttl = ttl_override.get('l2', self.config.l2_ttl) if ttl_override else self.config.l2_ttl
        self._schedule_background_task(
            self.redis_hot.setex(f"hot:{cache_key}", l2_ttl, serialized)
        )
        # L3: Warm tier - compressed for space efficiency
        if should_compress:
            compressed = snappy.compress(serialized)
            compression_ratio = len(serialized) / len(compressed)
            self._metrics.compression_saves_bytes += len(serialized) - len(compressed)
            l3_ttl = ttl_override.get('l3', self.config.l3_ttl) if ttl_override else self.config.l3_ttl
            self._schedule_background_task(
                self.redis_warm.setex(f"warm:{cache_key}", l3_ttl, compressed)
            )
            logger.debug(f"Compressed cache entry for {key}: {compression_ratio:.2f}x ratio")
        # L4: Persistent storage with upsert
        if self.pg_pool:
            l4_ttl = ttl_override.get('l4', self.config.l4_default_ttl) if ttl_override else self.config.l4_default_ttl
            self._schedule_background_task(
                self._upsert_to_postgres(cache_key, serialized, l4_ttl)
            )
        # Publish invalidation event for cache coherency
        if self.config.enable_pub_sub_invalidation:
            await self._publish_invalidation(cache_key, 'set')
        logger.debug(f"Cache set for key: {key}")
    async def invalidate(self, pattern: str):
        """
        Pattern-based invalidation across all cache tiers
        Args:
            pattern: Pattern to match (supports * wildcards)
        """
        self._metrics.invalidation_operations += 1
        # Convert pattern to regex for L1 matching
        regex_pattern = re.compile(pattern.replace('*', '.*'))
        # L1: Clear matching keys
        keys_to_remove = [k for k in self.l1_cache if regex_pattern.match(k)]
        for k in keys_to_remove:
            del self.l1_cache[k]
        # L2/L3: Use Redis SCAN for pattern matching
        try:
            # L2 hot tier
            async for key in self.redis_hot.scan_iter(f"hot:{pattern}"):
                await self.redis_hot.delete(key)
            # L3 warm tier
            async for key in self.redis_warm.scan_iter(f"warm:{pattern}"):
                await self.redis_warm.delete(key)
        except redis.RedisError as e:
            logger.warning(f"Redis invalidation error for pattern {pattern}: {e}")
        # L4: PostgreSQL pattern deletion
        if self.pg_pool:
            try:
                async with self.pg_pool.acquire() as conn:
                    await conn.execute(
                        "DELETE FROM cache_kv WHERE key LIKE $1",
                        pattern.replace('*', '%')
                    )
            except Exception as e:
                logger.warning(f"PostgreSQL invalidation error for pattern {pattern}: {e}")
        # Publish invalidation event
        if self.config.enable_pub_sub_invalidation:
            await self._publish_invalidation(pattern, 'invalidate')
        logger.info(f"Invalidated cache pattern: {pattern}")
    async def clear_expired(self):
        """Clean up expired entries from L4 cache"""
        if not self.pg_pool:
            return
        try:
            async with self.pg_pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM cache_kv WHERE expires_at <= NOW()"
                )
                deleted_count = int(result.split()[-1])
                logger.info(f"Cleaned up {deleted_count} expired cache entries")
        except Exception as e:
            logger.warning(f"Cache cleanup error: {e}")
    def _schedule_background_task(self, coro):
        """Schedule background task with proper cleanup"""
        task = asyncio.create_task(coro)
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
    def _schedule_background_refresh(
        self, 
        key: str, 
        refresh_fn: callable, 
        ttl_override: Optional[Dict[str, int]]
    ):
        """Schedule background refresh for stale-while-revalidate"""
        async def refresh_task():
            try:
                new_value = await refresh_fn(key)
                if new_value is not None:
                    await self.set(key, new_value, ttl_override)
                    logger.debug(f"Background refresh completed for key: {key}")
            except Exception as e:
                logger.warning(f"Background refresh failed for key {key}: {e}")
        self._schedule_background_task(refresh_task())
    def _schedule_promotion_to_hot(
        self, 
        cache_key: str, 
        value: Any, 
        ttl_override: Optional[Dict[str, int]]
    ):
        """Schedule promotion from L3 to L2 and L1"""
        async def promote_task():
            try:
                # Promote to L1
                self.l1_cache[cache_key] = value
                # Promote to L2
                serialized = msgpack.packb(value)
                l2_ttl = ttl_override.get('l2', self.config.l2_ttl) if ttl_override else self.config.l2_ttl
                await self.redis_hot.setex(f"hot:{cache_key}", l2_ttl, serialized)
                self._metrics.promotion_operations += 1
            except Exception as e:
                logger.warning(f"Cache promotion error for key {cache_key}: {e}")
        self._schedule_background_task(promote_task())
    def _schedule_promotion_all_tiers(
        self, 
        cache_key: str, 
        value: Any, 
        ttl_override: Optional[Dict[str, int]]
    ):
        """Schedule promotion from L4 to all higher tiers"""
        async def promote_all_task():
            try:
                # Promote to L1
                self.l1_cache[cache_key] = value
                # Serialize for Redis tiers
                serialized = msgpack.packb(value)
                # Promote to L2
                l2_ttl = ttl_override.get('l2', self.config.l2_ttl) if ttl_override else self.config.l2_ttl
                await self.redis_hot.setex(f"hot:{cache_key}", l2_ttl, serialized)
                # Promote to L3 with compression if beneficial
                if (self.config.enable_compression and 
                    len(serialized) > self.config.compression_threshold):
                    compressed = snappy.compress(serialized)
                    l3_ttl = ttl_override.get('l3', self.config.l3_ttl) if ttl_override else self.config.l3_ttl
                    await self.redis_warm.setex(f"warm:{cache_key}", l3_ttl, compressed)
                self._metrics.promotion_operations += 1
            except Exception as e:
                logger.warning(f"Full cache promotion error for key {cache_key}: {e}")
        self._schedule_background_task(promote_all_task())
    async def _upsert_to_postgres(self, cache_key: str, serialized: bytes, ttl_seconds: int):
        """Upsert cache entry to PostgreSQL with proper TTL"""
        if not self.pg_pool:
            return
        try:
            async with self.pg_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO cache_kv (key, value, expires_at)
                    VALUES ($1, $2, NOW() + INTERVAL '%s seconds')
                    ON CONFLICT (key) 
                    DO UPDATE SET 
                        value = EXCLUDED.value,
                        expires_at = EXCLUDED.expires_at,
                        access_count = cache_kv.access_count + 1,
                        last_accessed = NOW()
                """ % ttl_seconds, cache_key, serialized)
        except Exception as e:
            self._metrics.postgres_errors += 1
            logger.warning(f"PostgreSQL upsert error for key {cache_key}: {e}")
    def _setup_invalidation_listener(self):
        """Setup Redis pub/sub listener for cache invalidation"""
        async def invalidation_listener():
            try:
                pubsub = self.redis_hot.pubsub()
                await pubsub.subscribe('cache_invalidation')
                async for message in pubsub.listen():
                    if message['type'] == 'message':
                        try:
                            data = json.loads(message['data'])
                            pattern = data.get('pattern')
                            operation = data.get('operation', 'invalidate')
                            if operation == 'invalidate' and pattern:
                                # Only invalidate L1 for remote invalidations
                                regex_pattern = re.compile(pattern.replace('*', '.*'))
                                keys_to_remove = [k for k in self.l1_cache if regex_pattern.match(k)]
                                for k in keys_to_remove:
                                    del self.l1_cache[k]
                                logger.debug(f"Processed remote invalidation: {pattern}")
                        except Exception as e:
                            logger.warning(f"Invalidation message processing error: {e}")
            except Exception as e:
                logger.error(f"Invalidation listener error: {e}")
        self._invalidation_listener_task = asyncio.create_task(invalidation_listener())
    async def _publish_invalidation(self, pattern: str, operation: str):
        """Publish cache invalidation event"""
        try:
            message = json.dumps({
                'pattern': pattern,
                'operation': operation,
                'timestamp': time.time()
            })
            await self.redis_hot.publish('cache_invalidation', message)
        except redis.RedisError as e:
            logger.warning(f"Failed to publish invalidation for {pattern}: {e}")
    def _hash_key(self, key: str) -> str:
        """Generate consistent hash for cache key"""
        return hashlib.sha256(key.encode()).hexdigest()[:32]
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive cache metrics"""
        total_requests = (
            self._metrics.l1_hits + self._metrics.l1_misses +
            self._metrics.l2_hits + self._metrics.l2_misses +
            self._metrics.l3_hits + self._metrics.l3_misses +
            self._metrics.l4_hits + self._metrics.l4_misses
        )
        return {
            'l1_hit_rate': self._metrics.l1_hits / max(1, self._metrics.l1_hits + self._metrics.l1_misses),
            'l2_hit_rate': self._metrics.l2_hits / max(1, self._metrics.l2_hits + self._metrics.l2_misses),
            'l3_hit_rate': self._metrics.l3_hits / max(1, self._metrics.l3_hits + self._metrics.l3_misses),
            'l4_hit_rate': self._metrics.l4_hits / max(1, self._metrics.l4_hits + self._metrics.l4_misses),
            'overall_hit_rate': (
                (self._metrics.l1_hits + self._metrics.l2_hits + 
                 self._metrics.l3_hits + self._metrics.l4_hits) / max(1, total_requests)
            ),
            'total_requests': total_requests,
            'total_misses': self._metrics.total_misses,
            'redis_errors': self._metrics.redis_errors,
            'postgres_errors': self._metrics.postgres_errors,
            'compression_saves_bytes': self._metrics.compression_saves_bytes,
            'promotion_operations': self._metrics.promotion_operations,
            'invalidation_operations': self._metrics.invalidation_operations,
            'l1_cache_size': len(self.l1_cache),
            'background_tasks': len(self._background_tasks)
        }
    async def close(self):
        """Clean shutdown of cache connections and tasks"""
        # Cancel invalidation listener
        if self._invalidation_listener_task:
            self._invalidation_listener_task.cancel()
            try:
                await self._invalidation_listener_task
            except asyncio.CancelledError:
                pass
        # Wait for background tasks to complete
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        # Close Redis connections
        await self.redis_hot.close()
        await self.redis_warm.close()
        logger.info("Cache connections closed")
# Factory function for easy integration
def create_multi_tier_cache(
    l1_max_size: int = 10000,
    l2_ttl: int = 300,
    l3_ttl: int = 3600,
    enable_compression: bool = True,
    enable_pub_sub_invalidation: bool = True
) -> OptimizedMultiTierCache:
    """Factory function to create configured multi-tier cache"""
    config = CacheConfig(
        l1_max_size=l1_max_size,
        l2_ttl=l2_ttl,
        l3_ttl=l3_ttl,
        enable_compression=enable_compression,
        enable_pub_sub_invalidation=enable_pub_sub_invalidation
    )
    return OptimizedMultiTierCache(config)
