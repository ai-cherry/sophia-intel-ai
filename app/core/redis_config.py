"""
Redis Configuration for Sophia-Intel-AI
Provides production-ready Redis configuration with memory limits, TTL strategies,
and Pay Ready business cycle optimization.
"""

import os
from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, Field


class RedisPoolConfig(BaseModel):
    """Redis connection pool configuration"""

    max_connections: int = Field(default=50, description="Maximum connections in pool")
    min_connections: int = Field(default=5, description="Minimum connections in pool")
    retry_on_timeout: bool = Field(default=True, description="Retry on connection timeout")
    socket_keepalive: bool = Field(default=True, description="Enable socket keepalive")
    socket_keepalive_options: dict[str, int] = Field(
        default_factory=lambda: {}  # Let Redis handle platform-specific keepalive options
    )
    connection_timeout: float = Field(default=5.0, description="Connection timeout in seconds")
    socket_timeout: float = Field(default=30.0, description="Socket timeout in seconds")


class RedisStreamConfig(BaseModel):
    """Redis streams configuration with bounded memory"""

    max_len: int = Field(default=10000, description="Maximum stream length (MAXLEN)")
    trim_strategy: str = Field(default="~", description="Trim strategy (~=approximate, =exact)")
    consumer_group_timeout: int = Field(default=3600000, description="Consumer group timeout in ms")
    block_timeout: int = Field(default=5000, description="Block timeout for XREAD in ms")
    batch_size: int = Field(default=10, description="Batch size for stream processing")


class RedisTTLConfig(BaseModel):
    """TTL configuration for different data types"""

    # Cache TTLs
    cache_short: int = Field(default=300, description="Short-term cache TTL (5 minutes)")
    cache_medium: int = Field(default=1800, description="Medium cache TTL (30 minutes)")
    cache_long: int = Field(default=3600, description="Long cache TTL (1 hour)")
    cache_daily: int = Field(default=86400, description="Daily cache TTL (24 hours)")

    # Session and temporary data
    session_data: int = Field(default=1800, description="Session data TTL (30 minutes)")
    temp_results: int = Field(default=600, description="Temporary results TTL (10 minutes)")
    websocket_state: int = Field(default=300, description="WebSocket state TTL (5 minutes)")

    # Business cycle specific
    pay_ready_snapshot: int = Field(default=7200, description="Pay Ready snapshot TTL (2 hours)")
    monthly_analytics: int = Field(default=604800, description="Monthly analytics TTL (7 days)")
    team_performance: int = Field(default=3600, description="Team performance TTL (1 hour)")

    # Message bus
    message_retention: int = Field(default=86400, description="Message retention TTL (24 hours)")
    agent_inbox: int = Field(default=1800, description="Agent inbox TTL (30 minutes)")

    # Memory management
    memory_embeddings: int = Field(default=7200, description="Memory embeddings TTL (2 hours)")
    search_results: int = Field(default=1800, description="Search results TTL (30 minutes)")


class RedisMemoryConfig(BaseModel):
    """Redis memory management configuration"""

    # Memory thresholds (percentage of max memory)
    warning_threshold: float = Field(default=0.8, description="Memory warning threshold (80%)")
    critical_threshold: float = Field(default=0.9, description="Memory critical threshold (90%)")
    emergency_threshold: float = Field(default=0.95, description="Memory emergency threshold (95%)")

    # Eviction policies
    default_policy: str = Field(default="allkeys-lru", description="Default eviction policy")
    cache_policy: str = Field(default="volatile-lru", description="Cache-specific eviction policy")

    # Memory limits
    max_memory_mb: Optional[int] = Field(default=1024, description="Max memory in MB")
    sample_size: int = Field(default=5, description="Sample size for LRU eviction")


@dataclass
class RedisCircuitBreakerConfig:
    """Circuit breaker configuration for Redis resilience"""

    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    expected_exception: tuple = (ConnectionError, TimeoutError, OSError)
    name: str = "redis_circuit_breaker"


class RedisMonitoringConfig(BaseModel):
    """Redis monitoring and alerting configuration"""

    # Health check intervals
    health_check_interval: float = Field(
        default=30.0, description="Health check interval in seconds"
    )
    connection_check_timeout: float = Field(default=5.0, description="Connection check timeout")

    # Metrics collection
    collect_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_interval: float = Field(default=60.0, description="Metrics collection interval")

    # Alerting thresholds
    slow_query_threshold: float = Field(default=1.0, description="Slow query threshold in seconds")
    high_memory_threshold: float = Field(default=0.85, description="High memory usage threshold")
    connection_pool_threshold: float = Field(
        default=0.8, description="Connection pool usage threshold"
    )


class RedisConfig(BaseModel):
    """Complete Redis configuration"""

    # Connection details
    url: str = Field(default="redis://localhost:6379", description="Redis connection URL")
    db: int = Field(default=0, description="Redis database number")

    # Configuration sections
    pool: RedisPoolConfig = Field(default_factory=RedisPoolConfig)
    streams: RedisStreamConfig = Field(default_factory=RedisStreamConfig)
    ttl: RedisTTLConfig = Field(default_factory=RedisTTLConfig)
    memory: RedisMemoryConfig = Field(default_factory=RedisMemoryConfig)
    monitoring: RedisMonitoringConfig = Field(default_factory=RedisMonitoringConfig)

    # Circuit breaker
    circuit_breaker: RedisCircuitBreakerConfig = Field(default_factory=RedisCircuitBreakerConfig)

    # Environment overrides
    @classmethod
    def from_environment(cls) -> "RedisConfig":
        """Create config from environment variables"""

        # Get base URL from environment
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

        # Override with environment-specific settings
        config = cls(url=redis_url)

        # Production optimizations for Pay Ready
        if os.getenv("ENVIRONMENT") == "production":
            config.pool.max_connections = int(os.getenv("REDIS_MAX_CONNECTIONS", 100))
            config.streams.max_len = int(os.getenv("REDIS_STREAM_MAX_LEN", 50000))
            config.memory.max_memory_mb = int(os.getenv("REDIS_MAX_MEMORY_MB", 2048))

            # Extended TTLs for production caching
            config.ttl.pay_ready_snapshot = int(os.getenv("PAY_READY_TTL", 14400))  # 4 hours
            config.ttl.monthly_analytics = int(
                os.getenv("MONTHLY_ANALYTICS_TTL", 1209600)
            )  # 14 days

        # Development settings
        elif os.getenv("ENVIRONMENT") == "development":
            config.pool.max_connections = 20
            config.streams.max_len = 1000
            config.memory.max_memory_mb = 512

        # Test environment settings
        elif os.getenv("ENVIRONMENT") == "test":
            config.pool.max_connections = 5
            config.streams.max_len = 100
            config.ttl.cache_short = 30  # Shorter TTLs for testing
            config.memory.max_memory_mb = 256

        return config

    def get_stream_config(self, stream_name: str) -> dict[str, any]:
        """Get stream-specific configuration"""

        base_config = {
            "maxlen": self.streams.max_len,
            "approximate": self.streams.trim_strategy == "~",
        }

        # Customize based on stream type
        if "message_bus" in stream_name or "swarm" in stream_name:
            # Higher limits for critical message streams
            base_config["maxlen"] = self.streams.max_len * 2

        elif "temp" in stream_name or "cache" in stream_name:
            # Lower limits for temporary streams
            base_config["maxlen"] = self.streams.max_len // 2

        elif "pay_ready" in stream_name:
            # Optimized for month-end spikes
            base_config["maxlen"] = self.streams.max_len * 3

        return base_config

    def get_ttl_for_key_pattern(self, key_pattern: str) -> int:
        """Get appropriate TTL based on key pattern"""

        # Cache patterns
        if key_pattern.startswith("cache:"):
            if "daily" in key_pattern:
                return self.ttl.cache_daily
            elif "long" in key_pattern:
                return self.ttl.cache_long
            elif "short" in key_pattern:
                return self.ttl.cache_short
            else:
                return self.ttl.cache_medium

        # Session patterns
        elif key_pattern.startswith("session:"):
            return self.ttl.session_data

        # Pay Ready patterns
        elif "pay_ready" in key_pattern:
            return self.ttl.pay_ready_snapshot

        # Message patterns
        elif "message" in key_pattern or "inbox" in key_pattern:
            return self.ttl.message_retention

        # Memory patterns
        elif "embedding" in key_pattern or "vector" in key_pattern:
            return self.ttl.memory_embeddings

        # Default TTL
        else:
            return self.ttl.cache_medium


# Global configuration instance
redis_config = RedisConfig.from_environment()


# Specific configurations for common use cases
class RedisNamespaces:
    """Redis key namespaces for organization"""

    CACHE = "cache"
    SESSION = "session"
    MESSAGE_BUS = "msg_bus"
    WEBSOCKET = "ws"
    PAY_READY = "pay_ready"
    TEAM_PERF = "team_perf"
    MEMORY = "memory"
    TEMP = "temp"
    HEALTH = "health"
    METRICS = "metrics"

    @classmethod
    def format_key(cls, namespace: str, key: str) -> str:
        """Format a namespaced key"""
        return f"{namespace}:{key}"


# Pay Ready specific optimization settings
PAY_READY_REDIS_CONFIG = {
    "month_end_multiplier": 5,  # 5x capacity during month-end
    "spike_detection_window": 300,  # 5 minute window for spike detection
    "auto_scale_threshold": 0.7,  # Auto-scale at 70% capacity
    "priority_queues": ["urgent", "normal", "batch"],
    "circuit_breaker_settings": {
        "failure_threshold": 3,
        "recovery_timeout": 10.0,
        "half_open_max_calls": 5,
    },
}
