"""
Metrics Collection for Monitoring
Provides Prometheus metrics collection for the AI Orchestra system
"""

import time
from collections.abc import Callable
from contextlib import contextmanager
from functools import wraps

from fastapi import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Summary,
    generate_latest,
)
from prometheus_client.core import GaugeMetricFamily

# Create registry
registry = CollectorRegistry()

# ==================== Application Metrics ====================

# Request metrics
request_count = Counter(
    "ai_orchestra_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status"],
    registry=registry,
)

request_duration = Histogram(
    "ai_orchestra_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"],
    registry=registry,
)

# WebSocket metrics
websocket_connections = Gauge(
    "ai_orchestra_websocket_connections_active",
    "Number of active WebSocket connections",
    registry=registry,
)

websocket_messages = Counter(
    "ai_orchestra_websocket_messages_total",
    "Total WebSocket messages",
    ["direction", "message_type"],
    registry=registry,
)

# Circuit breaker metrics
circuit_breaker_state = Gauge(
    "ai_orchestra_circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half-open)",
    ["circuit_name"],
    registry=registry,
)

circuit_breaker_failures = Counter(
    "ai_orchestra_circuit_breaker_failures_total",
    "Total circuit breaker failures",
    ["circuit_name"],
    registry=registry,
)

# Error metrics
error_count = Counter(
    "ai_orchestra_errors_total",
    "Total number of errors",
    ["component", "error_type"],
    registry=registry,
)

# Token generation metrics
token_generation_rate = Summary(
    "ai_orchestra_token_generation_rate",
    "Token generation rate per second",
    registry=registry,
)

token_count = Counter(
    "ai_orchestra_tokens_generated_total",
    "Total tokens generated",
    ["session_id"],
    registry=registry,
)

# ==================== Business Metrics ====================

# Chat session metrics
chat_sessions = Gauge(
    "ai_orchestra_chat_sessions_active",
    "Number of active chat sessions",
    registry=registry,
)

chat_messages = Counter(
    "ai_orchestra_chat_messages_total",
    "Total chat messages processed",
    ["session_id", "execution_mode"],
    registry=registry,
)

# Swarm execution metrics
swarm_executions = Counter(
    "ai_orchestra_swarm_executions_total",
    "Total swarm executions",
    ["swarm_type", "status"],
    registry=registry,
)

swarm_duration = Histogram(
    "ai_orchestra_swarm_duration_seconds",
    "Swarm execution duration",
    ["swarm_type"],
    registry=registry,
)

# Manager intent metrics
manager_intent_detections = Counter(
    "ai_orchestra_manager_intent_detections_total",
    "Total intent detections",
    ["intent", "confidence_bucket"],
    registry=registry,
)

manager_accuracy = Summary(
    "ai_orchestra_manager_accuracy",
    "Manager intent detection accuracy",
    registry=registry,
)

# API version usage
api_version_usage = Counter(
    "ai_orchestra_api_version_usage_total",
    "API version usage",
    ["version", "endpoint"],
    registry=registry,
)

# Connection pool metrics
connection_pool_size = Gauge(
    "ai_orchestra_connection_pool_size",
    "Current connection pool size",
    registry=registry,
)

connection_pool_utilization = Gauge(
    "ai_orchestra_connection_pool_utilization",
    "Connection pool utilization percentage",
    registry=registry,
)

# Session memory metrics
session_memory_usage = Gauge(
    "ai_orchestra_session_memory_bytes",
    "Session memory usage in bytes",
    ["session_id"],
    registry=registry,
)

# ==================== Metric Decorators ====================


def track_request(method: str, endpoint: str):
    """Decorator to track HTTP request metrics"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                error_count.labels(component="http", error_type=type(e).__name__).inc()
                raise
            finally:
                duration = time.time() - start_time
                request_count.labels(
                    method=method, endpoint=endpoint, status=status
                ).inc()
                request_duration.labels(method=method, endpoint=endpoint).observe(
                    duration
                )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                error_count.labels(component="http", error_type=type(e).__name__).inc()
                raise
            finally:
                duration = time.time() - start_time
                request_count.labels(
                    method=method, endpoint=endpoint, status=status
                ).inc()
                request_duration.labels(method=method, endpoint=endpoint).observe(
                    duration
                )

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def track_swarm_execution(swarm_type: str):
    """Decorator to track swarm execution metrics"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception:
                status = "failed"
                raise
            finally:
                duration = time.time() - start_time
                swarm_executions.labels(swarm_type=swarm_type, status=status).inc()
                swarm_duration.labels(swarm_type=swarm_type).observe(duration)

        return wrapper

    return decorator


@contextmanager
def track_operation_time(metric: Histogram, **labels):
    """Context manager to track operation time"""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        metric.labels(**labels).observe(duration)


# ==================== Custom Collectors ====================


class SystemMetricsCollector:
    """Custom collector for system metrics"""

    def collect(self):
        import psutil

        # CPU usage
        yield GaugeMetricFamily(
            "ai_orchestra_cpu_usage_percent",
            "CPU usage percentage",
            value=psutil.cpu_percent(),
        )

        # Memory usage
        memory = psutil.virtual_memory()
        yield GaugeMetricFamily(
            "ai_orchestra_memory_usage_bytes",
            "Memory usage in bytes",
            value=memory.used,
        )
        yield GaugeMetricFamily(
            "ai_orchestra_memory_usage_percent",
            "Memory usage percentage",
            value=memory.percent,
        )

        # Disk usage
        disk = psutil.disk_usage("/")
        yield GaugeMetricFamily(
            "ai_orchestra_disk_usage_bytes", "Disk usage in bytes", value=disk.used
        )
        yield GaugeMetricFamily(
            "ai_orchestra_disk_usage_percent",
            "Disk usage percentage",
            value=disk.percent,
        )


# Register custom collector
registry.register(SystemMetricsCollector())

# ==================== Metrics Aggregator ====================


class MetricsAggregator:
    """Aggregates and manages metrics"""

    def __init__(self):
        self.start_time = time.time()

    def update_websocket_connections(self, count: int):
        """Update WebSocket connection count"""
        websocket_connections.set(count)

    def record_websocket_message(self, direction: str, message_type: str):
        """Record WebSocket message"""
        websocket_messages.labels(direction=direction, message_type=message_type).inc()

    def update_circuit_breaker(self, name: str, state: str, failures: int = 0):
        """Update circuit breaker metrics"""
        state_map = {"CLOSED": 0, "OPEN": 1, "HALF_OPEN": 2}
        circuit_breaker_state.labels(circuit_name=name).set(state_map.get(state, 0))
        if failures > 0:
            circuit_breaker_failures.labels(circuit_name=name).inc(failures)

    def record_error(self, component: str, error_type: str):
        """Record error occurrence"""
        error_count.labels(component=component, error_type=error_type).inc()

    def record_token_generation(self, session_id: str, token_count_value: int):
        """Record token generation"""
        token_count.labels(session_id=session_id).inc(token_count_value)
        token_generation_rate.observe(token_count_value)

    def update_chat_sessions(self, count: int):
        """Update active chat sessions"""
        chat_sessions.set(count)

    def record_chat_message(self, session_id: str, execution_mode: str):
        """Record chat message"""
        chat_messages.labels(session_id=session_id, execution_mode=execution_mode).inc()

    def record_intent_detection(self, intent: str, confidence: float):
        """Record manager intent detection"""
        confidence_bucket = (
            "high" if confidence > 0.8 else "medium" if confidence > 0.5 else "low"
        )
        manager_intent_detections.labels(
            intent=intent, confidence_bucket=confidence_bucket
        ).inc()
        manager_accuracy.observe(confidence)

    def record_api_usage(self, version: str, endpoint: str):
        """Record API version usage"""
        api_version_usage.labels(version=version, endpoint=endpoint).inc()

    def update_connection_pool(self, size: int, utilization: float):
        """Update connection pool metrics"""
        connection_pool_size.set(size)
        connection_pool_utilization.set(utilization * 100)

    def update_session_memory(self, session_id: str, memory_bytes: int):
        """Update session memory usage"""
        session_memory_usage.labels(session_id=session_id).set(memory_bytes)

    def get_uptime(self) -> float:
        """Get service uptime in seconds"""
        return time.time() - self.start_time

    def export_metrics(self) -> bytes:
        """Export metrics in Prometheus format"""
        return generate_latest(registry)


# ==================== FastAPI Integration ====================

# Global aggregator instance
metrics_aggregator = MetricsAggregator()


async def metrics_endpoint() -> Response:
    """
    Prometheus metrics endpoint

    Returns:
        Metrics in Prometheus format
    """
    metrics_data = metrics_aggregator.export_metrics()
    return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)


# ==================== Metrics Middleware ====================


class MetricsMiddleware:
    """Middleware to collect request metrics"""

    def __init__(self, app):
        self.app = app
        self.aggregator = metrics_aggregator

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = time.time()
            method = scope["method"]
            path = scope["path"]

            # Skip metrics endpoint to avoid recursion
            if path == "/metrics":
                await self.app(scope, receive, send)
                return

            status_code = 200

            async def send_wrapper(message):
                nonlocal status_code
                if message["type"] == "http.response.start":
                    status_code = message["status"]
                await send(message)

            try:
                await self.app(scope, receive, send_wrapper)
                status = "success"
            except Exception as e:
                status = "error"
                self.aggregator.record_error("http", type(e).__name__)
                raise
            finally:
                duration = time.time() - start_time
                request_count.labels(method=method, endpoint=path, status=status).inc()
                request_duration.labels(method=method, endpoint=path).observe(duration)
        else:
            await self.app(scope, receive, send)


# ==================== Export ====================

# Alias for backward compatibility
MetricsCollector = SystemMetricsCollector

__all__ = [
    # Classes
    "MetricsCollector",
    "SystemMetricsCollector",
    "MetricsAggregator",
    "MetricsMiddleware",
    # Metrics
    "request_count",
    "request_duration",
    "websocket_connections",
    "websocket_messages",
    "circuit_breaker_state",
    "circuit_breaker_failures",
    "error_count",
    "token_generation_rate",
    "token_count",
    "chat_sessions",
    "chat_messages",
    "swarm_executions",
    "swarm_duration",
    "manager_intent_detections",
    "manager_accuracy",
    "api_version_usage",
    "connection_pool_size",
    "connection_pool_utilization",
    "session_memory_usage",
    # Decorators and utilities
    "track_request",
    "track_swarm_execution",
    "track_operation_time",
    # Classes
    "MetricsAggregator",
    "MetricsMiddleware",
    "SystemMetricsCollector",
    # Functions
    "metrics_endpoint",
    "metrics_aggregator",
]
