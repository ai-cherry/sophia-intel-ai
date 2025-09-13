"""
Prometheus Metrics Exporter for Sophia Intel AI
Provides comprehensive metrics for cost tracking, caching, LLM performance, and system health.
"""
import logging
import time
from functools import wraps
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from app.core.ai_logger import logger
from app.core.circuit_breaker import with_circuit_breaker
logger = logging.getLogger(__name__)
# Create a custom registry for our metrics
registry = CollectorRegistry()
# Cost Monitoring Metrics
llm_api_cost_total = Counter(
    "llm_api_cost_total",
    "Total API costs in USD",
    ["provider", "model", "task_type"],
    registry=registry,
)
llm_cost_per_request = Histogram(
    "llm_cost_per_request",
    "Cost per LLM request in USD",
    ["provider", "model"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
    registry=registry,
)
# Cache Performance Metrics
llm_cache_hits_total = Counter(
    "llm_cache_hits_total",
    "Total number of cache hits",
    ["cache_type", "model"],
    registry=registry,
)
llm_cache_misses_total = Counter(
    "llm_cache_misses_total",
    "Total number of cache misses",
    ["cache_type", "model"],
    registry=registry,
)
llm_cache_errors_total = Counter(
    "llm_cache_errors_total",
    "Total number of cache errors",
    ["error_type"],
    registry=registry,
)
llm_cache_cost_saved_total = Counter(
    "llm_cache_cost_saved_total",
    "Total cost saved through caching in USD",
    registry=registry,
)
cache_hit_rate = Gauge(
    "cache_hit_rate", "Current cache hit rate percentage", registry=registry
)
# LLM Performance Metrics
llm_request_duration_seconds = Histogram(
    "llm_request_duration_seconds",
    "LLM request duration in seconds",
    ["provider", "model", "task_type"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
    registry=registry,
)
llm_tokens_total = Counter(
    "llm_tokens_total",
    "Total tokens processed",
    ["model", "token_type"],  # token_type: input/output
    registry=registry,
)
llm_tokens_remaining = Gauge(
    "llm_tokens_remaining",
    "Tokens remaining before rate limit",
    ["provider"],
    registry=registry,
)
llm_fallback_triggers_total = Counter(
    "llm_fallback_triggers_total",
    "Number of times fallback models were triggered",
    ["primary_model", "fallback_model", "reason"],
    registry=registry,
)
# Swarm Performance Metrics
consensus_swarm_success_rate = Gauge(
    "consensus_swarm_success_rate",
    "Success rate of consensus swarm operations",
    registry=registry,
)
agent_execution_duration_seconds = Histogram(
    "agent_execution_duration_seconds",
    "Agent execution duration by role",
    ["role", "task_type"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
    registry=registry,
)
swarm_consensus_duration_seconds = Histogram(
    "swarm_consensus_duration_seconds",
    "Time to reach consensus in swarm",
    ["swarm_type"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0],
    registry=registry,
)
# GPU Metrics
lambda_gpu_utilization_percent = Gauge(
    "lambda_gpu_utilization_percent",
    "GPU utilization percentage",
    ["gpu_instance"],
    registry=registry,
)
lambda_gpu_queue_length = Gauge(
    "lambda_gpu_queue_length",
    "Number of tasks waiting for GPU processing",
    registry=registry,
)
# Memory System Metrics
memory_deduplication_rate = Gauge(
    "memory_deduplication_rate",
    "Memory deduplication effectiveness rate",
    registry=registry,
)
vector_store_query_duration_seconds = Histogram(
    "vector_store_query_duration_seconds",
    "Vector store query duration",
    ["operation", "collection"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0],
    registry=registry,
)
# Database Metrics
weaviate_database_available = Gauge(
    "weaviate_database_available",
    "Weaviate database availability (1=available, 0=unavailable)",
    registry=registry,
)
postgresql_query_duration_seconds = Histogram(
    "postgresql_query_duration_seconds",
    "PostgreSQL query duration",
    ["query_type"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
    registry=registry,
)
redis_connected_clients = Gauge(
    "redis_connected_clients", "Number of connected Redis clients", registry=registry
)
# Security Metrics
request_blocked_total = Counter(
    "request_blocked_total",
    "Total number of blocked requests",
    ["reason", "source"],
    registry=registry,
)
jwt_invalid_total = Counter(
    "jwt_invalid_total",
    "Total number of invalid JWT attempts",
    ["error_type"],
    registry=registry,
)
rate_limit_exceeded_total = Counter(
    "rate_limit_exceeded_total",
    "Total number of rate limit exceeded events",
    ["endpoint", "client"],
    registry=registry,
)
# HTTP Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
    registry=registry,
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=registry,
)
class MetricsTracker:
    """Helper class to track and update metrics."""
    def __init__(self):
        self.start_times: dict[str, float] = {}
    def track_llm_request(
        self,
        provider: str,
        model: str,
        task_type: str,
        cost: float,
        tokens_in: int,
        tokens_out: int,
        duration: float,
        cache_hit: bool = False,
    ):
        """Track metrics for an LLM request."""
        # Cost metrics
        llm_api_cost_total.labels(
            provider=provider, model=model, task_type=task_type
        ).inc(cost)
        llm_cost_per_request.labels(provider=provider, model=model).observe(cost)
        # Performance metrics
        llm_request_duration_seconds.labels(
            provider=provider, model=model, task_type=task_type
        ).observe(duration)
        # Token metrics
        llm_tokens_total.labels(model=model, token_type="input").inc(tokens_in)
        llm_tokens_total.labels(model=model, token_type="output").inc(tokens_out)
        # Cache metrics
        if cache_hit:
            llm_cache_hits_total.labels(cache_type="semantic", model=model).inc()
            llm_cache_cost_saved_total.inc(cost)
        else:
            llm_cache_misses_total.labels(cache_type="semantic", model=model).inc()
    def track_http_request(
        self, method: str, endpoint: str, status: int, duration: float
    ):
        """Track HTTP request metrics."""
        http_requests_total.labels(
            method=method, endpoint=endpoint, status=str(status)
        ).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(
            duration
        )
    def track_agent_execution(
        self, role: str, task_type: str, duration: float, success: bool
    ):
        """Track agent execution metrics."""
        agent_execution_duration_seconds.labels(role=role, task_type=task_type).observe(
            duration
        )
        if role == "consensus":
            consensus_swarm_success_rate.set(1.0 if success else 0.0)
    def track_cache_performance(self, hits: int, misses: int):
        """Update cache hit rate gauge."""
        total = hits + misses
        if total > 0:
            cache_hit_rate.set((hits / total) * 100)
    def track_gpu_metrics(
        self, utilization: float, queue_length: int, instance: str = "default"
    ):
        """Track GPU utilization metrics."""
        lambda_gpu_utilization_percent.labels(gpu_instance=instance).set(utilization)
        lambda_gpu_queue_length.set(queue_length)
    def track_database_health(self, weaviate_available: bool, redis_clients: int):
        """Track database health metrics."""
        weaviate_database_available.set(1.0 if weaviate_available else 0.0)
        redis_connected_clients.set(redis_clients)
    def track_fallback(self, primary_model: str, fallback_model: str, reason: str):
        """Track model fallback events."""
        llm_fallback_triggers_total.labels(
            primary_model=primary_model, fallback_model=fallback_model, reason=reason
        ).inc()
# Global metrics tracker instance
metrics_tracker = MetricsTracker()
def track_request_metrics(method: str = "GET", endpoint: str = "/"):
    """Decorator to track HTTP request metrics."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                status = getattr(result, "status_code", 200)
            except Exception as e:
                status = 500
                raise e
            finally:
                duration = time.time() - start_time
                metrics_tracker.track_http_request(method, endpoint, status, duration)
            return result
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                status = getattr(result, "status_code", 200)
            except Exception as e:
                status = 500
                raise e
            finally:
                duration = time.time() - start_time
                metrics_tracker.track_http_request(method, endpoint, status, duration)
            return result
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator
def track_llm_metrics(provider: str, model: str, task_type: str = "general"):
    """Decorator to track LLM call metrics."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                # Extract metrics from result
                cost = result.get("cost", 0.001)  # Default cost if not provided
                tokens_in = result.get("input_tokens", 0)
                tokens_out = result.get("output_tokens", 0)
                cache_hit = result.get("cache_hit", False)
                metrics_tracker.track_llm_request(
                    provider,
                    model,
                    task_type,
                    cost,
                    tokens_in,
                    tokens_out,
                    duration,
                    cache_hit,
                )
                return result
            except Exception as e:
                llm_cache_errors_total.labels(error_type=type(e).__name__).inc()
                raise e
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                # Extract metrics from result
                cost = result.get("cost", 0.001)
                tokens_in = result.get("input_tokens", 0)
                tokens_out = result.get("output_tokens", 0)
                cache_hit = result.get("cache_hit", False)
                metrics_tracker.track_llm_request(
                    provider,
                    model,
                    task_type,
                    cost,
                    tokens_in,
                    tokens_out,
                    duration,
                    cache_hit,
                )
                return result
            except Exception as e:
                llm_cache_errors_total.labels(error_type=type(e).__name__).inc()
                raise e
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator
def get_metrics() -> bytes:
    """Generate Prometheus metrics in text format."""
    return generate_latest(registry)
def get_metrics_content_type() -> str:
    """Get the content type for Prometheus metrics."""
    return CONTENT_TYPE_LATEST
# Example usage functions
@with_circuit_breaker("external_api")
async def update_system_metrics():
    """Periodically update system metrics."""
    while True:
        try:
            # Update cache hit rate (example values)
            hits = llm_cache_hits_total._value.sum()
            misses = llm_cache_misses_total._value.sum()
            metrics_tracker.track_cache_performance(int(hits), int(misses))
            # Update GPU metrics (example values - replace with actual GPU monitoring)
            metrics_tracker.track_gpu_metrics(
                utilization=75.5,
                queue_length=3,
                instance="lambda-h100",  # Get from Lambda Labs API
            )
            # Update database health (example values - replace with actual health checks)
            metrics_tracker.track_database_health(
                weaviate_available=True,  # Check Weaviate health
                redis_clients=5,  # Get from Redis INFO command
            )
            # Update memory deduplication rate (example)
            memory_deduplication_rate.set(0.92)
            # Update remaining tokens (example - replace with actual API limits)
            llm_tokens_remaining.labels(provider="openrouter").set(95000)
            llm_tokens_remaining.labels(provider="together").set(180000)
            await asyncio.sleep(30)  # Update every 30 seconds
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
            await asyncio.sleep(60)
if __name__ == "__main__":
    # Example: Track a sample LLM request
    metrics_tracker.track_llm_request(
        provider="openrouter",
        model="anthropic/claude-3.5-sonnet",
        task_type="coding",
        cost=0.015,
        tokens_in=500,
        tokens_out=1200,
        duration=2.5,
        cache_hit=False,
    )
    # Example: Track HTTP request
    metrics_tracker.track_http_request(
        method="POST", endpoint="/api/v1/chat", status=200, duration=1.2
    )
    # Print metrics
    logger.info(get_metrics().decode("utf-8"))
def record_cost(
    provider: str,
    model: str,
    task_type: str = "general",
    cost: float = 0.0,
    tokens_in: int = 0,
    tokens_out: int = 0,
    duration: float = 0.0,
    cache_hit: bool = False,
):
    metrics_tracker.track_llm_request(
        provider, model, task_type, cost, tokens_in, tokens_out, duration, cache_hit
    )
# Additional metrics for audit swarm
def observe_agent_vote(agent_id: str, vote: str):
    """Record agent vote in debate"""
    pass
def observe_consensus_reached(debate_id: str, rounds: int):
    """Record consensus achievement"""
    pass
def observe_debate_round(debate_id: str, round_num: int):
    """Record debate round completion"""
    pass
