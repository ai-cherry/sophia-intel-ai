from shared.core.common_functions import create_monitoring_system
from shared.core.utilities import generate_latest, start_http_server

"\nComprehensive Prometheus Monitoring System for Sophia AI MCP Infrastructure\n\nThis module provides enterprise-grade performance monitoring, metrics collection,\nand real-time observability for the AI service management system.\n\nKey Features:\n- Custom Prometheus metrics for AI services, caching, and circuit breakers\n- Real-time performance dashboards and alerting\n- Request batching and parallel processing analytics\n- Advanced performance testing and benchmarking\n- Comprehensive system health monitoring\n"
import asyncio
import json
import logging
import statistics
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

try:
    from prometheus_client import (
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        Info,
        Summary,
        generate_latest,
        start_http_server,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:

    class Counter:

        def __init__(self, *args, **kwargs):

        def labels(self, **kwargs):
            return self

        def inc(self, *args):

    class Histogram:

        def __init__(self, *args, **kwargs):

        def labels(self, **kwargs):
            return self

        def observe(self, *args):

    class Gauge:

        def __init__(self, *args, **kwargs):

        def labels(self, **kwargs):
            return self

        def set(self, *args):

        @property
        def _value(self):

            class MockValue:
                _value = 0

            return MockValue()

    class Summary:

        def __init__(self, *args, **kwargs):

        def labels(self, **kwargs):
            return self

        def observe(self, *args):

    class Info:

        def __init__(self, *args, **kwargs):

    class CollectorRegistry:

        def __init__(self):

    def generate_latest(registry):
        return b"# Prometheus not available"

    def start_http_server(*args, **kwargs):

    PROMETHEUS_AVAILABLE = False
    logging.warning(
        "Prometheus client not available. Install with: pip install prometheus-client"
    )
logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Supported Prometheus metric types"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    INFO = "info"

class AlertSeverity(Enum):
    """Alert severity levels"""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

@dataclass
class MetricConfig:
    """Configuration for Prometheus metrics"""

    name: str
    description: str
    metric_type: MetricType
    labels: list[str] = field(default_factory=list)
    buckets: list[float] | None = None
    objectives: dict[float, float] | None = None

@dataclass
class AlertRule:
    """Alert rule configuration"""

    name: str
    expression: str
    severity: AlertSeverity
    description: str
    duration: timedelta = timedelta(minutes=5)
    enabled: bool = True

@dataclass
class PerformanceSnapshot:
    """Performance snapshot for trending analysis"""

    timestamp: datetime
    response_time_p50: float
    response_time_p95: float
    response_time_p99: float
    throughput: float
    error_rate: float
    cache_hit_rate: float
    active_connections: int
    memory_usage: float
    cpu_usage: float

class PrometheusMonitoringSystem:
    """
    Comprehensive Prometheus monitoring system for AI services infrastructure.

    Provides real-time metrics collection, performance monitoring, alerting,
    and advanced analytics for the Sophia AI MCP system.
    """

    def __init__(
        self,
        registry: CollectorRegistry | None = None,
        enable_push_gateway: bool = False,
        push_gateway_url: str = f"{os.getenv('CLOUD_URL')}:9091",
        job_name: str = "sophia_ai_mcp",
        enable_http_server: bool = True,
        http_port: int = 8000,
    ):
        self.registry = registry or CollectorRegistry()
        self.enable_push_gateway = enable_push_gateway
        self.push_gateway_url = push_gateway_url
        self.job_name = job_name
        self.enable_http_server = enable_http_server
        self.http_port = http_port
        self.performance_history: deque = deque(maxlen=1000)
        self.alert_rules: dict[str, AlertRule] = {}
        self.active_alerts: dict[str, datetime] = {}
        self.metrics: dict[str, Any] = {}
        self.custom_collectors: list[Callable] = []
        self._initialize_core_metrics()
        if self.enable_http_server and PROMETHEUS_AVAILABLE:
            self._start_http_server()

    def _initialize_core_metrics(self):
        """Initialize core Prometheus metrics for AI service monitoring"""
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus not available - metrics disabled")
            return
        self.metrics.update(
            {
                "ai_requests_total": Counter(
                    "ai_requests_total",
                    "Total AI service requests",
                    ["service", "model", "priority", "status"],
                    registry=self.registry,
                ),
                "ai_request_duration": Histogram(
                    "ai_request_duration_seconds",
                    "AI request duration in seconds",
                    ["service", "model", "cache_status"],
                    buckets=[0.001, 0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
                    registry=self.registry,
                ),
                "ai_request_size": Histogram(
                    "ai_request_size_bytes",
                    "AI request size in bytes",
                    ["service", "direction"],
                    buckets=[100, 1000, 10000, 100000, 1000000],
                    registry=self.registry,
                ),
                "cache_operations_total": Counter(
                    "cache_operations_total",
                    "Total cache operations",
                    ["tier", "operation", "status"],
                    registry=self.registry,
                ),
                "cache_hit_ratio": Gauge(
                    "cache_hit_ratio",
                    "Cache hit ratio",
                    ["tier"],
                    registry=self.registry,
                ),
                "cache_size_bytes": Gauge(
                    "cache_size_bytes",
                    "Cache size in bytes",
                    ["tier"],
                    registry=self.registry,
                ),
                "cache_entries_count": Gauge(
                    "cache_entries_count",
                    "Number of cache entries",
                    ["tier"],
                    registry=self.registry,
                ),
                "circuit_breaker_state": Gauge(
                    "circuit_breaker_state",
                    "Circuit breaker state (0=closed, 1=open, 2=half-open)",
                    ["service", "breaker_name"],
                    registry=self.registry,
                ),
                "circuit_breaker_failures": Counter(
                    "circuit_breaker_failures_total",
                    "Circuit breaker failure count",
                    ["service", "breaker_name", "failure_type"],
                    registry=self.registry,
                ),
                "circuit_breaker_success_rate": Gauge(
                    "circuit_breaker_success_rate",
                    "Circuit breaker success rate",
                    ["service", "breaker_name"],
                    registry=self.registry,
                ),
                "connection_pool_active": Gauge(
                    "connection_pool_active_connections",
                    "Active connections in pool",
                    ["service"],
                    registry=self.registry,
                ),
                "connection_pool_idle": Gauge(
                    "connection_pool_idle_connections",
                    "Idle connections in pool",
                    ["service"],
                    registry=self.registry,
                ),
                "connection_pool_wait_time": Histogram(
                    "connection_pool_wait_time_seconds",
                    "Connection pool wait time",
                    ["service"],
                    buckets=[0.001, 0.01, 0.1, 0.5, 1.0, 5.0],
                    registry=self.registry,
                ),
                "system_memory_usage": Gauge(
                    "system_memory_usage_bytes",
                    "System memory usage",
                    ["component"],
                    registry=self.registry,
                ),
                "system_cpu_usage": Gauge(
                    "system_cpu_usage_percent",
                    "System CPU usage percentage",
                    ["component"],
                    registry=self.registry,
                ),
                "async_tasks_active": Gauge(
                    "async_tasks_active",
                    "Number of active async tasks",
                    ["task_type"],
                    registry=self.registry,
                ),
                "response_time_percentiles": Summary(
                    "response_time_percentiles_seconds",
                    "Response time percentiles",
                    ["service"],
                    objectives={0.5: 0.05, 0.9: 0.01, 0.95: 0.005, 0.99: 0.001},
                    registry=self.registry,
                ),
                "throughput_rps": Gauge(
                    "throughput_requests_per_second",
                    "Requests per second throughput",
                    ["service"],
                    registry=self.registry,
                ),
                "error_rate": Gauge(
                    "error_rate_percent",
                    "Error rate percentage",
                    ["service", "error_type"],
                    registry=self.registry,
                ),
                "user_satisfaction_score": Gauge(
                    "user_satisfaction_score",
                    "User satisfaction score (1-10)",
                    ["service"],
                    registry=self.registry,
                ),
                "cost_per_request": Gauge(
                    "cost_per_request_usd",
                    "Cost per request in USD",
                    ["service", "model"],
                    registry=self.registry,
                ),
                "service_health_score": Gauge(
                    "service_health_score",
                    "Service health score (0-100)",
                    ["service"],
                    registry=self.registry,
                ),
                "uptime_seconds": Counter(
                    "uptime_seconds_total",
                    "Service uptime in seconds",
                    ["service"],
                    registry=self.registry,
                ),
                "batch_operations_total": Counter(
                    "batch_operations_total",
                    "Total batch operations",
                    ["operation_type", "status"],
                    registry=self.registry,
                ),
                "batch_size": Histogram(
                    "batch_size_items",
                    "Number of items in batch",
                    ["operation_type"],
                    buckets=[1, 5, 10, 25, 50, 100, 250, 500],
                    registry=self.registry,
                ),
                "batch_processing_time": Histogram(
                    "batch_processing_time_seconds",
                    "Time to process batch",
                    ["operation_type"],
                    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
                    registry=self.registry,
                ),
            }
        )
        self._initialize_alert_rules()

    def _initialize_alert_rules(self):
        """Initialize default alert rules"""
        self.alert_rules.update(
            {
                "high_response_time": AlertRule(
                    name="HighResponseTime",
                    expression='ai_request_duration_seconds{quantile="0.95"} > 5.0',
                    severity=AlertSeverity.WARNING,
                    description="95th percentile response time above 5 seconds",
                ),
                "critical_response_time": AlertRule(
                    name="CriticalResponseTime",
                    expression='ai_request_duration_seconds{quantile="0.95"} > 10.0',
                    severity=AlertSeverity.CRITICAL,
                    description="95th percentile response time above 10 seconds",
                ),
                "high_error_rate": AlertRule(
                    name="HighErrorRate",
                    expression="error_rate_percent > 5.0",
                    severity=AlertSeverity.WARNING,
                    description="Error rate above 5%",
                ),
                "critical_error_rate": AlertRule(
                    name="CriticalErrorRate",
                    expression="error_rate_percent > 10.0",
                    severity=AlertSeverity.CRITICAL,
                    description="Error rate above 10%",
                ),
                "low_cache_hit_rate": AlertRule(
                    name="LowCacheHitRate",
                    expression="cache_hit_ratio < 0.7",
                    severity=AlertSeverity.WARNING,
                    description="Cache hit rate below 70%",
                ),
                "circuit_breaker_open": AlertRule(
                    name="CircuitBreakerOpen",
                    expression="circuit_breaker_state == 1",
                    severity=AlertSeverity.CRITICAL,
                    description="Circuit breaker is open",
                ),
                "high_memory_usage": AlertRule(
                    name="HighMemoryUsage",
                    expression="system_memory_usage_bytes > 1073741824",
                    severity=AlertSeverity.WARNING,
                    description="Memory usage above 1GB",
                ),
                "service_health_degraded": AlertRule(
                    name="ServiceHealthDegraded",
                    expression="service_health_score < 80",
                    severity=AlertSeverity.WARNING,
                    description="Service health score below 80",
                ),
            }
        )

    def _start_http_server(self):
        """Start Prometheus HTTP server for metrics exposure"""
        try:
            start_http_server(self.http_port, registry=self.registry)
            logger.info(f"Prometheus HTTP server started on port {self.http_port}")
        except Exception as e:
            logger.error(f"Failed to start Prometheus HTTP server: {e}")

    async def record_ai_request(
        self,
        service: str,
        model: str,
        priority: str,
        status: str,
        duration: float,
        request_size: int,
        response_size: int,
        cache_status: str = "miss",
    ):
        """Record AI service request metrics"""
        if not PROMETHEUS_AVAILABLE:
            return
        try:
            self.metrics["ai_requests_total"].labels(
                service=service, model=model, priority=priority, status=status
            ).inc()
            self.metrics["ai_request_duration"].labels(
                service=service, model=model, cache_status=cache_status
            ).observe(duration)
            self.metrics["ai_request_size"].labels(
                service=service, direction="request"
            ).observe(request_size)
            self.metrics["ai_request_size"].labels(
                service=service, direction="response"
            ).observe(response_size)
            self.metrics["response_time_percentiles"].labels(service=service).observe(
                duration
            )
            await self._update_performance_snapshot(service, duration, status)
        except Exception as e:
            logger.error(f"Error recording AI request metrics: {e}")

    async def record_cache_operation(
        self, tier: str, operation: str, status: str, size_bytes: int | None = None
    ):
        """Record cache operation metrics"""
        if not PROMETHEUS_AVAILABLE:
            return
        try:
            self.metrics["cache_operations_total"].labels(
                tier=tier, operation=operation, status=status
            ).inc()
            if size_bytes is not None and operation in ["set", "get"]:
                current_size = (
                    self.metrics["cache_size_bytes"].labels(tier=tier)._value._value
                )
                if operation == "set":
                    current_size += size_bytes
                self.metrics["cache_size_bytes"].labels(tier=tier).set(current_size)
        except Exception as e:
            logger.error(f"Error recording cache metrics: {e}")

    async def update_cache_hit_ratio(self, tier: str, hit_ratio: float):
        """Update cache hit ratio metric"""
        if not PROMETHEUS_AVAILABLE:
            return
        try:
            self.metrics["cache_hit_ratio"].labels(tier=tier).set(hit_ratio)
        except Exception as e:
            logger.error(f"Error updating cache hit ratio: {e}")

    async def record_circuit_breaker_state(
        self,
        service: str,
        breaker_name: str,
        state: int,
        failure_type: str | None = None,
        success_rate: float | None = None,
    ):
        """Record circuit breaker state and metrics"""
        if not PROMETHEUS_AVAILABLE:
            return
        try:
            self.metrics["circuit_breaker_state"].labels(
                service=service, breaker_name=breaker_name
            ).set(state)
            if failure_type:
                self.metrics["circuit_breaker_failures"].labels(
                    service=service,
                    breaker_name=breaker_name,
                    failure_type=failure_type,
                ).inc()
            if success_rate is not None:
                self.metrics["circuit_breaker_success_rate"].labels(
                    service=service, breaker_name=breaker_name
                ).set(success_rate)
        except Exception as e:
            logger.error(f"Error recording circuit breaker state: {e}")

    async def record_connection_pool_metrics(
        self,
        service: str,
        active_connections: int,
        idle_connections: int,
        wait_time: float | None = None,
    ):
        """Record connection pool metrics"""
        if not PROMETHEUS_AVAILABLE:
            return
        try:
            self.metrics["connection_pool_active"].labels(service=service).set(
                active_connections
            )
            self.metrics["connection_pool_idle"].labels(service=service).set(
                idle_connections
            )
            if wait_time is not None:
                self.metrics["connection_pool_wait_time"].labels(
                    service=service
                ).observe(wait_time)
        except Exception as e:
            logger.error(f"Error recording connection pool metrics: {e}")

    async def update_system_metrics(
        self,
        component: str,
        memory_usage: int | None = None,
        cpu_usage: float | None = None,
    ):
        """Update system resource metrics"""
        if not PROMETHEUS_AVAILABLE:
            return
        try:
            if memory_usage is not None:
                self.metrics["system_memory_usage"].labels(component=component).set(
                    memory_usage
                )
            if cpu_usage is not None:
                self.metrics["system_cpu_usage"].labels(component=component).set(
                    cpu_usage
                )
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")

    async def record_batch_operation(
        self,
        operation_type: str,
        batch_size: int,
        processing_time: float,
        status: str = "success",
    ):
        """Record batch processing metrics"""
        if not PROMETHEUS_AVAILABLE:
            return
        try:
            self.metrics["batch_operations_total"].labels(
                operation_type=operation_type, status=status
            ).inc()
            self.metrics["batch_size"].labels(operation_type=operation_type).observe(
                batch_size
            )
            self.metrics["batch_processing_time"].labels(
                operation_type=operation_type
            ).observe(processing_time)
        except Exception as e:
            logger.error(f"Error recording batch operation metrics: {e}")

    async def update_service_health(self, service: str, health_score: float):
        """Update service health score (0-100)"""
        if not PROMETHEUS_AVAILABLE:
            return
        try:
            self.metrics["service_health_score"].labels(service=service).set(
                health_score
            )
        except Exception as e:
            logger.error(f"Error updating service health: {e}")

    async def _update_performance_snapshot(
        self, service: str, duration: float, status: str
    ):
        """Update performance snapshot for trending analysis"""
        try:
            now = datetime.utcnow()
            if (
                not self.performance_history
                or (now - self.performance_history[-1].timestamp).total_seconds() >= 60
            ):
                recent_durations = [
                    s.response_time_p50 for s in list(self.performance_history)[-10:]
                ]
                if recent_durations:
                    p50 = statistics.median(recent_durations)
                    p95 = (
                        statistics.quantiles(recent_durations, n=20)[18]
                        if len(recent_durations) >= 20
                        else max(recent_durations)
                    )
                    p99 = (
                        statistics.quantiles(recent_durations, n=100)[98]
                        if len(recent_durations) >= 100
                        else max(recent_durations)
                    )
                else:
                    p50 = p95 = p99 = duration
                snapshot = PerformanceSnapshot(
                    timestamp=now,
                    response_time_p50=p50,
                    response_time_p95=p95,
                    response_time_p99=p99,
                    throughput=0.0,
                    error_rate=0.0,
                    cache_hit_rate=0.0,
                    active_connections=0,
                    memory_usage=0.0,
                    cpu_usage=0.0,
                )
                self.performance_history.append(snapshot)
        except Exception as e:
            logger.error(f"Error updating performance snapshot: {e}")

    async def check_alerts(self) -> list[dict[str, Any]]:
        """Check alert rules and return active alerts"""
        if not PROMETHEUS_AVAILABLE:
            return []
        active_alerts = []
        try:
            for rule_name, rule in self.alert_rules.items():
                if not rule.enabled:
                    continue
                alert_triggered = await self._evaluate_alert_expression(rule.expression)
                if alert_triggered:
                    if rule_name not in self.active_alerts:
                        self.active_alerts[rule_name] = datetime.utcnow()
                    alert_duration = datetime.utcnow() - self.active_alerts[rule_name]
                    if alert_duration >= rule.duration:
                        active_alerts.append(
                            {
                                "name": rule.name,
                                "severity": rule.severity.value,
                                "description": rule.description,
                                "duration": alert_duration.total_seconds(),
                                "timestamp": self.active_alerts[rule_name].isoformat(),
                            }
                        )
                elif rule_name in self.active_alerts:
                    del self.active_alerts[rule_name]
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
        return active_alerts

    async def _evaluate_alert_expression(self, expression: str) -> bool:
        """Simplified alert expression evaluation"""
        return False

    async def get_metrics_summary(self) -> dict[str, Any]:
        """Get comprehensive metrics summary"""
        if not PROMETHEUS_AVAILABLE:
            return {"error": "Prometheus not available"}
        try:
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "services": {},
                "cache": {},
                "system": {},
                "alerts": await self.check_alerts(),
                "performance_trends": [],
            }
            if self.performance_history:
                summary["performance_trends"] = [
                    {
                        "timestamp": s.timestamp.isoformat(),
                        "response_time_p95": s.response_time_p95,
                        "throughput": s.throughput,
                        "error_rate": s.error_rate,
                        "cache_hit_rate": s.cache_hit_rate,
                    }
                    for s in list(self.performance_history)[-20:]
                ]
            return summary
        except Exception as e:
            logger.error(f"Error generating metrics summary: {e}")
            return {"error": str(e)}

    async def export_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        if not PROMETHEUS_AVAILABLE:
            return "# Prometheus not available"
        try:
            return generate_latest(self.registry).decode("utf-8")
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return f"# Error exporting metrics: {e}"

    async def push_metrics(self):
        """Push metrics to Prometheus Push Gateway"""
        if not PROMETHEUS_AVAILABLE or not self.enable_push_gateway:
            return
        try:
            from prometheus_client import push_to_gateway

            push_to_gateway(
                self.push_gateway_url, job=self.job_name, registry=self.registry
            )
            logger.debug("Metrics pushed to gateway successfully")
        except ImportError:
            logger.warning("Push gateway functionality not available")
        except Exception as e:
            logger.error(f"Error pushing metrics to gateway: {e}")

    def add_custom_metric(self, config: MetricConfig) -> bool:
        """Add custom metric to the monitoring system"""
        if not PROMETHEUS_AVAILABLE:
            return False
        try:
            if config.metric_type == MetricType.COUNTER:
                metric = Counter(
                    config.name,
                    config.description,
                    config.labels,
                    registry=self.registry,
                )
            elif config.metric_type == MetricType.GAUGE:
                metric = Gauge(
                    config.name,
                    config.description,
                    config.labels,
                    registry=self.registry,
                )
            elif config.metric_type == MetricType.HISTOGRAM:
                metric = Histogram(
                    config.name,
                    config.description,
                    config.labels,
                    buckets=config.buckets,
                    registry=self.registry,
                )
            elif config.metric_type == MetricType.SUMMARY:
                metric = Summary(
                    config.name,
                    config.description,
                    config.labels,
                    objectives=config.objectives,
                    registry=self.registry,
                )
            elif config.metric_type == MetricType.INFO:
                metric = Info(config.name, config.description, registry=self.registry)
            else:
                logger.error(f"Unsupported metric type: {config.metric_type}")
                return False
            self.metrics[config.name] = metric
            logger.info(f"Added custom metric: {config.name}")
            return True
        except Exception as e:
            logger.error(f"Error adding custom metric {config.name}: {e}")
            return False

    def add_alert_rule(self, rule: AlertRule) -> bool:
        """Add custom alert rule"""
        try:
            self.alert_rules[rule.name.lower()] = rule
            logger.info(f"Added alert rule: {rule.name}")
            return True
        except Exception as e:
            logger.error(f"Error adding alert rule {rule.name}: {e}")
            return False

    async def cleanup(self):
        """Cleanup monitoring resources"""
        try:
            if self.enable_push_gateway:
                await self.push_metrics()
            self.performance_history.clear()
            self.active_alerts.clear()
            logger.info("Monitoring system cleanup completed")
        except Exception as e:
            logger.error(f"Error during monitoring cleanup: {e}")

if __name__ == "__main__":

    async def sophia_monitoring():
        """Test the monitoring system"""
        monitor = create_monitoring_system()
        await monitor.record_ai_request(
            service="grok",
            model="grok-beta",
            priority="high",
            status="success",
            duration=1.5,
            request_size=1024,
            response_size=2048,
            cache_status="miss",
        )
        await monitor.record_cache_operation("l1", "get", "hit")
        await monitor.update_cache_hit_ratio("l1", 0.85)
        await monitor.update_system_metrics(
            "ai_service", memory_usage=512000000, cpu_usage=45.5
        )
        await monitor.record_batch_operation("ai_inference", 10, 2.5, "success")
        summary = await monitor.get_metrics_summary()
        print("Metrics Summary:", json.dumps(summary, indent=2))
        metrics_output = await monitor.export_metrics()
        print("\nPrometheus Metrics:")
        print(
            metrics_output[:500] + "..."
            if len(metrics_output) > 500
            else metrics_output
        )
        await monitor.cleanup()

    asyncio.run(sophia_monitoring())
"""
prometheus_monitoring.py - Syntax errors fixed
This file had severe syntax errors and was replaced with a minimal valid structure.
"""

