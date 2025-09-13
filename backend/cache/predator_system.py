"""
Sophia AI Cache Optimization Predator - 5-Tier System
97% hit rate target with intelligent prefetching and normalization
"""
import asyncio
import hashlib
import logging
import pickle
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import lz4.frame
import orjson
from cachetools import TTLCache, LRUCache
import redis.asyncio as redis
import psutil
import numpy as np
from collections import defaultdict, deque
# Import Pulumi ESC configuration
from shared.core.unified_config import get_config_value
logger = logging.getLogger(__name__)
@dataclass
class CacheMetrics:
    """Performance metrics for cache system"""
    l1_hits: int = 0
    l2_hits: int = 0
    l3_hits: int = 0
    l4_hits: int = 0
    l5_hits: int = 0
    total_misses: int = 0
    prefetch_hits: int = 0
    prefetch_misses: int = 0
    evictions: int = 0
    compression_ratio: float = 0.0
    avg_retrieval_time_ms: float = 0.0
@dataclass
class CacheEntry:
    """Enhanced cache entry with metadata"""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    size_bytes: int = 0
    tier: int = 1
    compressed: bool = False
    prediction_score: float = 0.0
    def __post_init__(self):
        if not self.size_bytes:
            self.size_bytes = len(str(self.value))
class PredictivePrefetcher:
    """AI-powered cache prefetching system"""
    def __init__(self, max_patterns: int = 10000):
        self.access_patterns = defaultdict(list)  # key -> [access_times]
        self.sequence_patterns = defaultdict(int)  # (key1, key2) -> frequency
        self.prediction_cache = TTLCache(maxsize=1000, ttl=300)  # 5-minute predictions
        self.max_patterns = max_patterns
    def record_access(self, key: str, timestamp: float = None):
        """Record cache access for pattern learning"""
        if timestamp is None:
            timestamp = time.time()
        # Record access time
        self.access_patterns[key].append(timestamp)
        # Keep only recent accesses (last 24 hours)
        cutoff = timestamp - 86400
        self.access_patterns[key] = [t for t in self.access_patterns[key] if t > cutoff]
        # Limit pattern storage
        if len(self.access_patterns) > self.max_patterns:
            # Remove oldest patterns
            oldest_key = min(
                self.access_patterns.keys(),
                key=lambda k: (
                    max(self.access_patterns[k]) if self.access_patterns[k] else 0
                ),
            )
            del self.access_patterns[oldest_key]
    def predict_next_keys(
        self, current_key: str, limit: int = 5
    ) -> List[Tuple[str, float]]:
        """Predict next likely cache keys with confidence scores"""
        cache_key = f"predict:{current_key}:{limit}"
        if cache_key in self.prediction_cache:
            return self.prediction_cache[cache_key]
        predictions = []
        current_time = time.time()
        # Pattern-based prediction
        for key, access_times in self.access_patterns.items():
            if key == current_key or not access_times:
                continue
            # Calculate access frequency
            recent_accesses = [
                t for t in access_times if t > current_time - 3600
            ]  # Last hour
            frequency = len(recent_accesses) / 60  # Accesses per minute
            # Calculate time-based prediction
            if len(access_times) >= 2:
                intervals = [
                    access_times[i] - access_times[i - 1]
                    for i in range(1, len(access_times))
                ]
                avg_interval = sum(intervals) / len(intervals)
                time_since_last = current_time - access_times[-1]
                # Predict based on interval pattern
                if time_since_last >= avg_interval * 0.8:
                    time_score = min(1.0, time_since_last / avg_interval)
                    confidence = frequency * time_score
                    predictions.append((key, confidence))
        # Sort by confidence and limit results
        predictions.sort(key=lambda x: x[1], reverse=True)
        predictions = predictions[:limit]
        # Cache predictions
        self.prediction_cache[cache_key] = predictions
        return predictions
class CacheNormalizer:
    """Advanced cache key normalization for better hit rates"""
    def __init__(self):
        self.normalization_cache = LRUCache(maxsize=50000)
        self.hash_buckets = defaultdict(set)  # hash -> set of normalized keys
    def normalize_key(self, key: str) -> str:
        """Normalize cache key for better collision detection"""
        if key in self.normalization_cache:
            return self.normalization_cache[key]
        # Convert to lowercase and strip whitespace
        normalized = key.lower().strip()
        # Remove common variations
        normalized = normalized.replace(" ", "_")
        normalized = normalized.replace("-", "_")
        normalized = normalized.replace("__", "_")
        # Sort query parameters if present
        if "?" in normalized:
            base, params = normalized.split("?", 1)
            if "&" in params:
                param_list = params.split("&")
                param_list.sort()
                normalized = f"{base}?{'&'.join(param_list)}"
        # Generate hash bucket for collision detection
        key_hash = hashlib.md5(normalized.encode()).hexdigest()[:8]
        self.hash_buckets[key_hash].add(normalized)
        # Cache normalization
        self.normalization_cache[key] = normalized
        return normalized
    def find_similar_keys(self, key: str, threshold: float = 0.8) -> List[str]:
        """Find similar cache keys for potential hits"""
        normalized = self.normalize_key(key)
        key_hash = hashlib.md5(normalized.encode()).hexdigest()[:8]
        similar_keys = []
        bucket_keys = self.hash_buckets.get(key_hash, set())
        for bucket_key in bucket_keys:
            if bucket_key != normalized:
                # Simple similarity check (can be enhanced with more sophisticated algorithms)
                similarity = self._calculate_similarity(normalized, bucket_key)
                if similarity >= threshold:
                    similar_keys.append(bucket_key)
        return similar_keys
    def _calculate_similarity(self, key1: str, key2: str) -> float:
        """Calculate similarity between two keys"""
        # Simple Jaccard similarity on character n-grams
        def get_ngrams(s: str, n: int = 3) -> Set[str]:
            return set(s[i : i + n] for i in range(len(s) - n + 1))
        ngrams1 = get_ngrams(key1)
        ngrams2 = get_ngrams(key2)
        if not ngrams1 and not ngrams2:
            return 1.0
        if not ngrams1 or not ngrams2:
            return 0.0
        intersection = len(ngrams1 & ngrams2)
        union = len(ngrams1 | ngrams2)
        return intersection / union if union > 0 else 0.0
class CachePredatorSystem:
    """5-tier cache optimization system targeting 97% hit rate"""
    def __init__(self, target_hit_rate: float = 0.97):
        self.target_hit_rate = target_hit_rate
        self.metrics = CacheMetrics()
        # Tier 1: Ultra-fast memory cache (most frequently accessed)
        self.l1_cache = LRUCache(maxsize=1000)  # Hot data
        # Tier 2: Application memory cache (recently accessed)
        self.l2_cache = TTLCache(maxsize=10000, ttl=3600)  # 1 hour TTL
        # Tier 3: Redis cache (distributed/persistent)
        self.redis_client = None
        self.l3_ttl = 86400  # 24 hours
        # Tier 4: Predictive cache (AI-prefetched data)
        self.l4_cache = TTLCache(maxsize=5000, ttl=1800)  # 30 minutes
        # Tier 5: Compressed storage cache (large/infrequent data)
        self.l5_cache = TTLCache(maxsize=2000, ttl=7200)  # 2 hours
        # Optimization components
        self.prefetcher = PredictivePrefetcher()
        self.normalizer = CacheNormalizer()
        # Performance tracking
        self.access_history = deque(maxlen=10000)
        self.performance_samples = deque(maxlen=1000)
    async def initialize(self):
        """Initialize cache system components"""
        # Initialize Redis connection
        redis_url = get_config_value("redis_url") or "${REDIS_URL}"
        self.redis_client = redis.from_url(
            redis_url,
            decode_responses=False,  # Keep binary for compression
            socket_keepalive=True,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        # Test Redis connection
        try:
            await self.redis_client.ping()
            logger.info("Redis connection established for L3 cache")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise
        # Start background optimization tasks
        asyncio.create_task(self._background_optimizer())
        asyncio.create_task(self._predictive_prefetcher())
        logger.info("Cache Predator System initialized with 97% hit rate target")
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from 5-tier cache system"""
        start_time = time.perf_counter_ns()
        normalized_key = self.normalizer.normalize_key(key)
        # Record access for pattern learning
        self.prefetcher.record_access(normalized_key)
        self.access_history.append((normalized_key, time.time()))
        try:
            # Tier 1: Ultra-fast memory cache
            if normalized_key in self.l1_cache:
                value = self.l1_cache[normalized_key]
                self.metrics.l1_hits += 1
                self._record_performance(start_time, "L1")
                return value
            # Tier 2: Application memory cache
            if normalized_key in self.l2_cache:
                value = self.l2_cache[normalized_key]
                # Promote to L1 if frequently accessed
                self.l1_cache[normalized_key] = value
                self.metrics.l2_hits += 1
                self._record_performance(start_time, "L2")
                return value
            # Tier 3: Redis distributed cache
            redis_value = await self._get_from_redis(normalized_key)
            if redis_value is not None:
                # Promote to L2
                self.l2_cache[normalized_key] = redis_value
                self.metrics.l3_hits += 1
                self._record_performance(start_time, "L3")
                return redis_value
            # Tier 4: Predictive cache
            if normalized_key in self.l4_cache:
                value = self.l4_cache[normalized_key]
                # Promote to L2
                self.l2_cache[normalized_key] = value
                self.metrics.l4_hits += 1
                self._record_performance(start_time, "L4")
                return value
            # Tier 5: Compressed storage cache
            if normalized_key in self.l5_cache:
                compressed_value = self.l5_cache[normalized_key]
                # Decompress and promote
                value = self._decompress_value(compressed_value)
                self.l2_cache[normalized_key] = value
                self.metrics.l5_hits += 1
                self._record_performance(start_time, "L5")
                return value
            # Check for similar keys (fuzzy matching)
            similar_keys = self.normalizer.find_similar_keys(normalized_key)
            for similar_key in similar_keys:
                similar_value = await self.get(similar_key)
                if similar_value is not None:
                    # Cache under original key
                    await self.set(normalized_key, similar_value)
                    self._record_performance(start_time, "SIMILAR")
                    return similar_value
            # Cache miss
            self.metrics.total_misses += 1
            self._record_performance(start_time, "MISS")
            return default
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self.metrics.total_misses += 1
            return default
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in optimal cache tier"""
        normalized_key = self.normalizer.normalize_key(key)
        value_size = len(str(value))
        try:
            # Determine optimal tier based on value characteristics
            if value_size < 1024:  # Small values go to L1/L2
                self.l1_cache[normalized_key] = value
                self.l2_cache[normalized_key] = value
            # Always store in Redis (L3) for persistence
            await self._set_in_redis(normalized_key, value, ttl or self.l3_ttl)
            # Large values get compressed in L5
            if value_size > 10240:  # 10KB threshold
                compressed_value = self._compress_value(value)
                self.l5_cache[normalized_key] = compressed_value
            logger.debug(f"Cached key {normalized_key} in appropriate tiers")
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
    async def _get_from_redis(self, key: str) -> Any:
        """Get value from Redis with error handling"""
        try:
            data = await self.redis_client.get(f"cache:{key}")
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Redis get failed for {key}: {e}")
            return None
    async def _set_in_redis(self, key: str, value: Any, ttl: int) -> None:
        """Set value in Redis with compression"""
        try:
            # Serialize and optionally compress
            serialized = pickle.dumps(value)
            if len(serialized) > 1024:  # Compress large values
                compressed = lz4.frame.compress(serialized)
                if len(compressed) < len(serialized):
                    await self.redis_client.set(f"cache:{key}", compressed, ex=ttl)
                    self.metrics.compression_ratio = len(compressed) / len(serialized)
                else:
                    await self.redis_client.set(f"cache:{key}", serialized, ex=ttl)
            else:
                await self.redis_client.set(f"cache:{key}", serialized, ex=ttl)
        except Exception as e:
            logger.warning(f"Redis set failed for {key}: {e}")
    def _compress_value(self, value: Any) -> bytes:
        """Compress value for L5 storage"""
        serialized = pickle.dumps(value)
        return lz4.frame.compress(serialized)
    def _decompress_value(self, compressed_data: bytes) -> Any:
        """Decompress value from L5 storage"""
        decompressed = lz4.frame.decompress(compressed_data)
        return pickle.loads(decompressed)
    def _record_performance(self, start_time_ns: int, tier: str) -> None:
        """Record performance metrics"""
        latency_ms = (time.perf_counter_ns() - start_time_ns) / 1_000_000
        self.performance_samples.append((tier, latency_ms))
        # Update average
        if self.performance_samples:
            total_latency = sum(sample[1] for sample in self.performance_samples)
            self.metrics.avg_retrieval_time_ms = total_latency / len(
                self.performance_samples
            )
    async def _background_optimizer(self):
        """Background task for cache optimization"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                # Calculate current hit rate
                total_hits = (
                    self.metrics.l1_hits
                    + self.metrics.l2_hits
                    + self.metrics.l3_hits
                    + self.metrics.l4_hits
                    + self.metrics.l5_hits
                )
                total_requests = total_hits + self.metrics.total_misses
                if total_requests > 0:
                    current_hit_rate = total_hits / total_requests
                    logger.info(
                        f"Cache hit rate: {current_hit_rate:.3f} (target: {self.target_hit_rate:.3f})"
                    )
                    # Optimize if below target
                    if current_hit_rate < self.target_hit_rate:
                        await self._optimize_cache_distribution()
            except Exception as e:
                logger.error(f"Background optimizer error: {e}")
    async def _predictive_prefetcher(self):
        """Background predictive prefetching"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                # Get recent access patterns
                recent_keys = [
                    key
                    for key, timestamp in self.access_history
                    if time.time() - timestamp < 300
                ]  # Last 5 minutes
                # Predict and prefetch
                for key in set(recent_keys[-100:]):  # Last 100 unique keys
                    predictions = self.prefetcher.predict_next_keys(key, limit=3)
                    for predicted_key, confidence in predictions:
                        if confidence > 0.5 and predicted_key not in self.l4_cache:
                            # Try to prefetch from lower tiers
                            value = await self._get_from_redis(predicted_key)
                            if value is not None:
                                self.l4_cache[predicted_key] = value
                                self.metrics.prefetch_hits += 1
                            else:
                                self.metrics.prefetch_misses += 1
            except Exception as e:
                logger.error(f"Predictive prefetcher error: {e}")
    async def _optimize_cache_distribution(self):
        """Optimize cache tier distribution"""
        # Analyze access patterns
        tier_performance = defaultdict(list)
        for tier, latency in self.performance_samples:
            tier_performance[tier].append(latency)
        # Adjust cache sizes based on performance
        if len(tier_performance["L1"]) > 0:
            avg_l1_latency = sum(tier_performance["L1"]) / len(tier_performance["L1"])
            if avg_l1_latency > 1.0:  # If L1 is slow, increase size
                self.l1_cache = LRUCache(maxsize=min(2000, self.l1_cache.maxsize * 2))
        logger.info("Cache distribution optimized")
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive cache performance metrics"""
        total_hits = (
            self.metrics.l1_hits
            + self.metrics.l2_hits
            + self.metrics.l3_hits
            + self.metrics.l4_hits
            + self.metrics.l5_hits
        )
        total_requests = total_hits + self.metrics.total_misses
        hit_rate = total_hits / total_requests if total_requests > 0 else 0
        # Memory usage
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        return {
            "hit_rate": hit_rate,
            "target_hit_rate": self.target_hit_rate,
            "target_achieved": hit_rate >= self.target_hit_rate,
            "tier_breakdown": {
                "l1_hits": self.metrics.l1_hits,
                "l2_hits": self.metrics.l2_hits,
                "l3_hits": self.metrics.l3_hits,
                "l4_hits": self.metrics.l4_hits,
                "l5_hits": self.metrics.l5_hits,
                "total_misses": self.metrics.total_misses,
            },
            "prefetch_performance": {
                "prefetch_hits": self.metrics.prefetch_hits,
                "prefetch_misses": self.metrics.prefetch_misses,
                "prefetch_accuracy": (
                    self.metrics.prefetch_hits
                    / (self.metrics.prefetch_hits + self.metrics.prefetch_misses)
                    if (self.metrics.prefetch_hits + self.metrics.prefetch_misses) > 0
                    else 0
                ),
            },
            "performance": {
                "avg_retrieval_time_ms": self.metrics.avg_retrieval_time_ms,
                "compression_ratio": self.metrics.compression_ratio,
                "memory_usage_mb": memory_mb,
            },
            "cache_sizes": {
                "l1_size": len(self.l1_cache),
                "l2_size": len(self.l2_cache),
                "l4_size": len(self.l4_cache),
                "l5_size": len(self.l5_cache),
            },
            "optimization_status": "97% hit rate predator active",
        }
    async def clear_all_caches(self):
        """Clear all cache tiers"""
        self.l1_cache.clear()
        self.l2_cache.clear()
        self.l4_cache.clear()
        self.l5_cache.clear()
        # Clear Redis cache
        try:
            keys = await self.redis_client.keys("cache:*")
            if keys:
                await self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis clear failed: {e}")
        logger.info("All cache tiers cleared")
    async def shutdown(self):
        """Shutdown cache system"""
        if self.redis_client:
            await self.redis_client.close()
        logger.info("Cache Predator System shutdown complete")
# Factory function
async def create_cache_predator(target_hit_rate: float = 0.97) -> CachePredatorSystem:
    """Create and initialize cache predator system"""
    system = CachePredatorSystem(target_hit_rate=target_hit_rate)
    await system.initialize()
    return system
