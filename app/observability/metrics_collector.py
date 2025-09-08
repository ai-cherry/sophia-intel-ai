"""Comprehensive observability system for MCP tools and agents."""

import asyncio
import contextlib
import json
import logging
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

import psutil

from app.core.ai_logger import logger

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Single metric data point."""

    timestamp: datetime
    value: float
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class ToolExecutionTrace:
    """Detailed trace of tool execution."""

    tool_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    input_size: int = 0
    output_size: int = 0
    memory_before: int = 0
    memory_after: int = 0
    context: dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Collects and aggregates system metrics."""

    def __init__(self, retention_hours: int = 24):
        self.metrics: dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.retention_hours = retention_hours
        self.start_time = datetime.now()
        self._cleanup_task = None

    async def start(self):
        """Start metrics collection."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Metrics collector started")

    async def stop(self):
        """Stop metrics collection."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task

    def record(self, name: str, value: float, labels: dict[str, str] = None):
        """Record a metric value."""
        point = MetricPoint(timestamp=datetime.now(), value=value, labels=labels or {})
        self.metrics[name].append(point)

    def increment(self, name: str, value: float = 1.0, labels: dict[str, str] = None):
        """Increment a counter metric."""
        current = self.get_latest(name)
        new_value = (current or 0) + value
        self.record(name, new_value, labels)

    def get_latest(self, name: str) -> Optional[float]:
        """Get the latest value for a metric."""
        if name in self.metrics and self.metrics[name]:
            return self.metrics[name][-1].value
        return None

    def get_stats(self, name: str, window_minutes: int = 60) -> dict[str, float]:
        """Get statistics for a metric over time window."""
        if name not in self.metrics:
            return {}

        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        values = [p.value for p in self.metrics[name] if p.timestamp > cutoff]

        if not values:
            return {}

        return {
            "count": len(values),
            "sum": sum(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "latest": values[-1],
        }

    async def _cleanup_loop(self):
        """Periodically clean up old metrics."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                self._cleanup_old_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    def _cleanup_old_metrics(self):
        """Remove metrics older than retention period."""
        cutoff = datetime.now() - timedelta(hours=self.retention_hours)

        for name in list(self.metrics.keys()):
            # Filter out old points
            self.metrics[name] = deque(
                (p for p in self.metrics[name] if p.timestamp > cutoff), maxlen=10000
            )

            # Remove empty metrics
            if not self.metrics[name]:
                del self.metrics[name]

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []

        for name, points in self.metrics.items():
            if not points:
                continue

            latest = points[-1]
            metric_name = name.replace(".", "_").replace("-", "_")

            # Add labels if present
            if latest.labels:
                labels = ",".join(f'{k}="{v}"' for k, v in latest.labels.items())
                lines.append(f"{metric_name}{{{labels}}} {latest.value}")
            else:
                lines.append(f"{metric_name} {latest.value}")

        return "\n".join(lines)


class TraceCollector:
    """Collects execution traces for debugging."""

    def __init__(self, max_traces: int = 1000):
        self.traces: deque = deque(maxlen=max_traces)
        self.active_traces: dict[str, ToolExecutionTrace] = {}

    def start_trace(
        self, trace_id: str, tool_name: str, context: dict[str, Any] = None
    ) -> ToolExecutionTrace:
        """Start a new trace."""
        trace = ToolExecutionTrace(
            tool_name=tool_name,
            start_time=datetime.now(),
            context=context or {},
            memory_before=psutil.Process().memory_info().rss,
        )
        self.active_traces[trace_id] = trace
        return trace

    def end_trace(
        self, trace_id: str, success: bool = True, error: str = None, output_size: int = 0
    ):
        """End an active trace."""
        if trace_id not in self.active_traces:
            logger.warning(f"Trace {trace_id} not found")
            return

        trace = self.active_traces.pop(trace_id)
        trace.end_time = datetime.now()
        trace.duration_ms = (trace.end_time - trace.start_time).total_seconds() * 1000
        trace.success = success
        trace.error = error
        trace.output_size = output_size
        trace.memory_after = psutil.Process().memory_info().rss

        self.traces.append(trace)

    def get_recent_traces(self, count: int = 100) -> list[ToolExecutionTrace]:
        """Get recent execution traces."""
        return list(self.traces)[-count:]

    def get_slow_traces(self, threshold_ms: float = 1000) -> list[ToolExecutionTrace]:
        """Get traces that exceeded duration threshold."""
        return [t for t in self.traces if t.duration_ms and t.duration_ms > threshold_ms]

    def get_failed_traces(self) -> list[ToolExecutionTrace]:
        """Get failed execution traces."""
        return [t for t in self.traces if not t.success]

    def export_json(self) -> str:
        """Export traces as JSON."""
        traces_data = []
        for trace in self.traces:
            traces_data.append(
                {
                    "tool": trace.tool_name,
                    "start": trace.start_time.isoformat(),
                    "end": trace.end_time.isoformat() if trace.end_time else None,
                    "duration_ms": trace.duration_ms,
                    "success": trace.success,
                    "error": trace.error,
                    "memory_delta": (
                        trace.memory_after - trace.memory_before if trace.memory_after else 0
                    ),
                    "context": trace.context,
                }
            )
        return json.dumps(traces_data, indent=2)


class AlertManager:
    """Manages alerts based on metrics thresholds."""

    def __init__(self):
        self.alerts: list[dict[str, Any]] = []
        self.alert_rules: dict[str, dict[str, Any]] = {}
        self.alert_callbacks: list[Callable] = []

    def add_rule(
        self,
        name: str,
        metric: str,
        condition: str,
        threshold: float,
        window_minutes: int = 5,
        cooldown_minutes: int = 15,
    ):
        """Add an alert rule."""
        self.alert_rules[name] = {
            "metric": metric,
            "condition": condition,  # "gt", "lt", "eq"
            "threshold": threshold,
            "window_minutes": window_minutes,
            "cooldown_minutes": cooldown_minutes,
            "last_fired": None,
        }

    def register_callback(self, callback: Callable):
        """Register a callback for alerts."""
        self.alert_callbacks.append(callback)

    async def check_alerts(self, metrics: MetricsCollector):
        """Check all alert rules."""
        now = datetime.now()

        for name, rule in self.alert_rules.items():
            # Check cooldown
            if rule["last_fired"]:
                cooldown_end = rule["last_fired"] + timedelta(minutes=rule["cooldown_minutes"])
                if now < cooldown_end:
                    continue

            # Get metric stats
            stats = metrics.get_stats(rule["metric"], rule["window_minutes"])
            if not stats:
                continue

            # Check condition
            value = stats.get("avg", 0)
            should_fire = False

            if (
                rule["condition"] == "gt"
                and value > rule["threshold"]
                or rule["condition"] == "lt"
                and value < rule["threshold"]
                or rule["condition"] == "eq"
                and value == rule["threshold"]
            ):
                should_fire = True

            if should_fire:
                await self._fire_alert(name, rule, value)

    async def _fire_alert(self, name: str, rule: dict[str, Any], value: float):
        """Fire an alert."""
        alert = {
            "name": name,
            "timestamp": datetime.now(),
            "metric": rule["metric"],
            "value": value,
            "threshold": rule["threshold"],
            "condition": rule["condition"],
        }

        self.alerts.append(alert)
        rule["last_fired"] = datetime.now()

        # Call callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")

        logger.warning(
            f"ALERT: {name} - {rule['metric']} {rule['condition']} {rule['threshold']} (value: {value})"
        )


class ObservabilitySystem:
    """Main observability system integrating all components."""

    def __init__(self):
        self.metrics = MetricsCollector()
        self.traces = TraceCollector()
        self.alerts = AlertManager()
        self._monitoring_task = None

        # Setup default alert rules
        self._setup_default_alerts()

    def _setup_default_alerts(self):
        """Setup default alert rules."""
        # High error rate
        self.alerts.add_rule(
            "high_error_rate", "tool_errors_per_minute", "gt", threshold=10, window_minutes=5
        )

        # High memory usage
        self.alerts.add_rule(
            "high_memory", "memory_usage_mb", "gt", threshold=1000, window_minutes=5
        )

        # Slow tool execution
        self.alerts.add_rule(
            "slow_execution", "tool_duration_ms", "gt", threshold=5000, window_minutes=10
        )

        # Low success rate
        self.alerts.add_rule(
            "low_success_rate", "tool_success_rate", "lt", threshold=0.8, window_minutes=15
        )

    async def start(self):
        """Start observability system."""
        await self.metrics.start()
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Observability system started")

    async def stop(self):
        """Stop observability system."""
        await self.metrics.stop()
        if self._monitoring_task:
            self._monitoring_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitoring_task

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while True:
            try:
                # Collect system metrics
                self._collect_system_metrics()

                # Check alerts
                await self.alerts.check_alerts(self.metrics)

                await asyncio.sleep(60)  # Run every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")

    def _collect_system_metrics(self):
        """Collect system-level metrics."""
        try:
            # CPU usage
            self.metrics.record("system_cpu_percent", psutil.cpu_percent())

            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics.record("system_memory_percent", memory.percent)
            self.metrics.record("memory_usage_mb", psutil.Process().memory_info().rss / 1024 / 1024)

            # Disk usage
            disk = psutil.disk_usage("/")
            self.metrics.record("system_disk_percent", disk.percent)

            # Network connections
            connections = len(psutil.net_connections())
            self.metrics.record("system_connections", connections)

        except Exception as e:
            logger.error(f"System metrics collection error: {e}")

    def tool_execution_context(self, tool_name: str, trace_id: str = None):
        """Context manager for tool execution monitoring."""
        if not trace_id:
            trace_id = f"{tool_name}_{int(time.time() * 1000)}"

        class ToolContext:
            def __init__(ctx_self):
                ctx_self.trace_id = trace_id
                ctx_self.tool_name = tool_name
                ctx_self.trace = None

            def __enter__(ctx_self):
                ctx_self.trace = self.traces.start_trace(trace_id, tool_name)
                self.metrics.increment(f"tool_{tool_name}_executions")
                return ctx_self

            def __exit__(ctx_self, exc_type, exc_val, exc_tb):
                success = exc_type is None
                error = str(exc_val) if exc_val else None

                self.traces.end_trace(trace_id, success, error)

                if success:
                    self.metrics.increment(f"tool_{tool_name}_success")
                else:
                    self.metrics.increment(f"tool_{tool_name}_errors")
                    self.metrics.increment("tool_errors_per_minute")

                if ctx_self.trace.duration_ms:
                    self.metrics.record(f"tool_{tool_name}_duration_ms", ctx_self.trace.duration_ms)
                    self.metrics.record("tool_duration_ms", ctx_self.trace.duration_ms)

                # Calculate success rate
                success_count = self.metrics.get_latest(f"tool_{tool_name}_success") or 0
                total_count = self.metrics.get_latest(f"tool_{tool_name}_executions") or 1
                success_rate = success_count / total_count if total_count > 0 else 0
                self.metrics.record(f"tool_{tool_name}_success_rate", success_rate)
                self.metrics.record("tool_success_rate", success_rate)

        return ToolContext()

    def get_dashboard_data(self) -> dict[str, Any]:
        """Get data for monitoring dashboard."""
        return {
            "uptime_hours": (datetime.now() - self.metrics.start_time).total_seconds() / 3600,
            "metrics": {
                name: self.metrics.get_stats(name, 60)
                for name in list(self.metrics.metrics.keys())[:20]  # Limit to 20 metrics
            },
            "recent_traces": [
                {
                    "tool": t.tool_name,
                    "duration_ms": t.duration_ms,
                    "success": t.success,
                    "error": t.error,
                }
                for t in self.traces.get_recent_traces(10)
            ],
            "alerts": [
                {"name": a["name"], "timestamp": a["timestamp"].isoformat(), "value": a["value"]}
                for a in self.alerts.alerts[-10:]
            ],
            "system": {
                "cpu_percent": self.metrics.get_latest("system_cpu_percent"),
                "memory_percent": self.metrics.get_latest("system_memory_percent"),
                "disk_percent": self.metrics.get_latest("system_disk_percent"),
            },
        }

    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format."""
        if format == "prometheus":
            return self.metrics.export_prometheus()
        elif format == "json":
            data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": {},
                "traces": json.loads(self.traces.export_json()),
            }

            for name in self.metrics.metrics:
                stats = self.metrics.get_stats(name)
                if stats:
                    data["metrics"][name] = stats

            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unknown format: {format}")


# Global observability instance
observability = ObservabilitySystem()


async def main():
    """Test observability system."""
    await observability.start()

    try:
        # Simulate tool executions
        for i in range(5):
            with observability.tool_execution_context("test_tool"):
                await asyncio.sleep(0.1)
                if i == 3:
                    raise ValueError("Test error")

        # Get dashboard data
        dashboard = observability.get_dashboard_data()
        logger.info(json.dumps(dashboard, indent=2, default=str))

        # Export metrics
        logger.info("\nPrometheus format:")
        logger.info(observability.export_metrics("prometheus"))

    finally:
        await observability.stop()


if __name__ == "__main__":
    asyncio.run(main())
