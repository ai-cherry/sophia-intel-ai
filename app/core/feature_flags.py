"""
Lightweight feature flags for controlled rollouts.
Reads from environment variables with sane defaults.
"""
import os


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class FeatureFlags:
    # Integration Intelligence router enablement
    INTEGRATION_INTELLIGENCE_ENABLED: bool = _as_bool(
        os.getenv("FF_INTEGRATION_INTEL"), False
    )
    # Allow mock embeddings when real client not configured
    USE_MOCK_EMBEDDINGS: bool = _as_bool(os.getenv("FF_MOCK_EMBEDDINGS"), False)
    # If true, fail on missing Weaviate instead of gracefully degrading
    WEAVIATE_REQUIRED: bool = _as_bool(os.getenv("FF_WEAVIATE_REQUIRED"), False)
    
    # Additional feature flags for services
    ENABLE_WEBSOCKETS: bool = _as_bool(os.getenv("FF_ENABLE_WEBSOCKETS"), True)
    USE_REDIS_CACHE: bool = _as_bool(os.getenv("FF_USE_REDIS_CACHE"), True)
    ENABLE_METRICS: bool = _as_bool(os.getenv("FF_ENABLE_METRICS"), True)
    API_V2_ENABLED: bool = _as_bool(os.getenv("FF_API_V2"), True)
    GRACEFUL_DEGRADATION: bool = _as_bool(os.getenv("FF_GRACEFUL_DEGRADATION"), True)
    ENABLE_CONNECTION_POOLING: bool = _as_bool(os.getenv("FF_CONNECTION_POOLING"), True)
    ENABLE_HEALTH_CHECKS: bool = _as_bool(os.getenv("FF_HEALTH_CHECKS"), True)


__all__ = ["FeatureFlags"]

