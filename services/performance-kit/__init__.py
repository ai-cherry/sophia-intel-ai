"""
Performance Kit - High-performance components for Sophia AI
This package provides optimized components for:
- Hedged requests with adaptive delays
- 4-tier caching with compression
- Single-flight request deduplication
- Circuit breakers and resilience patterns
"""
from .hedged_requests import (
    AdaptiveHedgedRequestManager,
    HedgeConfig,
    HedgeMetrics,
    create_hedged_request_manager,
)
from .multi_tier_cache import (
    CacheConfig,
    CacheMetrics,
    OptimizedMultiTierCache,
    create_multi_tier_cache,
)
from .single_flight import (
    FlightMetrics,
    SingleFlightGroup,
    SingleFlightManager,
    get_global_manager,
    single_flight,
    single_flight_context,
    single_flight_do,
)
__version__ = "1.0.0"
__all__ = [
    # Hedged Requests
    "AdaptiveHedgedRequestManager",
    "HedgeConfig",
    "HedgeMetrics",
    "create_hedged_request_manager",
    # Multi-Tier Cache
    "OptimizedMultiTierCache",
    "CacheConfig",
    "CacheMetrics",
    "create_multi_tier_cache",
    # Single Flight
    "SingleFlightGroup",
    "SingleFlightManager",
    "FlightMetrics",
    "single_flight_do",
    "single_flight_context",
    "single_flight",
    "get_global_manager",
]
