"""
Metrics Collection and Export

Provides Prometheus-compatible metrics collection for AI agents and swarms
with automatic labeling and efficient aggregation.
"""

import asyncio
import time
import threading
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Callable, Set, Tuple
from datetime import datetime, timedelta

from pydantic import BaseModel, Field


class MetricType(str, Enum):
    """Types of metrics."""
    COUNTER = "counter"        # Monotonically increasing value
    GAUGE = "gauge"           # Arbitrary value that can go up or down  
    HISTOGRAM = "histogram"   # Distribution of values with buckets
    SUMMARY = "summary"       # Distribution with quantiles


@dataclass
class MetricValue:
    """
    Represents a metric value with timestamp and labels.
    """
    value: Union[int, float]
    timestamp: float
    labels: Dict[str, str]
    
    def __post_init__(self):
        """Ensure timestamp is set."""
        if not self.timestamp:
            self.timestamp = time.time()


class BaseMetric(ABC):
    """
    Abstract base class for metrics.
    """
    
    def __init__(
        self,
        name: str,
        description: str = "",
        labels: Optional[List[str]] = None
    ):
        """
        Initialize metric.
        
        Args:
            name: Metric name
            description: Metric description
            labels: Label names for this metric
        """
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._lock = threading.Lock()
        self._samples: Dict[str, Any] = {}
        
        # Validate metric name
        if not self.name.replace('_', '').replace(':', '').isalnum():
            raise ValueError(f"Invalid metric name: {name}")
    
    @abstractmethod
    def collect(self) -> List[MetricValue]:
        """
        Collect current metric values.
        
        Returns:
            List[MetricValue]: Current metric values
        """
        pass
    
    def _make_label_key(self, labels: Dict[str, str]) -> str:
        """Create consistent key from labels."""
        # Validate labels
        for label_name in labels.keys():
            if label_name not in self.label_names:
                raise ValueError(f"Unknown label: {label_name}")
        
        # Create sorted key
        sorted_labels = sorted(labels.items())
        return ','.join(f"{k}={v}" for k, v in sorted_labels)
    
    def get_prometheus_type(self) -> str:
        """Get Prometheus metric type."""
        type_mapping = {
            MetricType.COUNTER: "counter",
            MetricType.GAUGE: "gauge",
            MetricType.HISTOGRAM: "histogram",
            MetricType.SUMMARY: "summary"
        }
        return type_mapping.get(self.metric_type, "gauge")


class Counter(BaseMetric):
    """
    Counter metric - monotonically increasing value.
    """
    
    metric_type = MetricType.COUNTER
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._values: Dict[str, float] = defaultdict(float)
    
    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Increment counter.
        
        Args:
            amount: Amount to increment by
            labels: Label values
        """
        if amount < 0:
            raise ValueError("Counter increments must be non-negative")
        
        labels = labels or {}
        label_key = self._make_label_key(labels)
        
        with self._lock:
            self._values[label_key] += amount
    
    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """
        Get current counter value.
        
        Args:
            labels: Label values
            
        Returns:
            float: Current value
        """
        labels = labels or {}
        label_key = self._make_label_key(labels)
        
        with self._lock:
            return self._values[label_key]
    
    def collect(self) -> List[MetricValue]:
        """Collect counter values."""
        with self._lock:
            values = []
            for label_key, value in self._values.items():
                # Parse labels back from key
                labels = {}
                if label_key:
                    for pair in label_key.split(','):
                        k, v = pair.split('=', 1)
                        labels[k] = v
                
                values.append(MetricValue(
                    value=value,
                    timestamp=time.time(),
                    labels=labels
                ))
            
            return values


class Gauge(BaseMetric):
    """
    Gauge metric - arbitrary value that can go up or down.
    """
    
    metric_type = MetricType.GAUGE
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._values: Dict[str, float] = {}
    
    def set(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Set gauge value.
        
        Args:
            value: Value to set
            labels: Label values
        """
        labels = labels or {}
        label_key = self._make_label_key(labels)
        
        with self._lock:
            self._values[label_key] = value
    
    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Increment gauge value.
        
        Args:
            amount: Amount to increment by
            labels: Label values
        """
        labels = labels or {}
        label_key = self._make_label_key(labels)
        
        with self._lock:
            self._values[label_key] = self._values.get(label_key, 0) + amount
    
    def dec(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Decrement gauge value.
        
        Args:
            amount: Amount to decrement by
            labels: Label values
        """
        self.inc(-amount, labels)
    
    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """
        Get current gauge value.
        
        Args:
            labels: Label values
            
        Returns:
            float: Current value
        """
        labels = labels or {}
        label_key = self._make_label_key(labels)
        
        with self._lock:
            return self._values.get(label_key, 0.0)
    
    def collect(self) -> List[MetricValue]:
        """Collect gauge values."""
        with self._lock:
            values = []
            for label_key, value in self._values.items():
                # Parse labels back from key
                labels = {}
                if label_key:
                    for pair in label_key.split(','):
                        k, v = pair.split('=', 1)
                        labels[k] = v
                
                values.append(MetricValue(
                    value=value,
                    timestamp=time.time(),
                    labels=labels
                ))
            
            return values


class Histogram(BaseMetric):
    """
    Histogram metric - distribution of values with configurable buckets.
    """
    
    metric_type = MetricType.HISTOGRAM
    
    def __init__(
        self,
        *args,
        buckets: Optional[List[float]] = None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        
        # Default buckets for response times (in seconds)
        self.buckets = buckets or [
            0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 
            0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float('inf')
        ]
        self.buckets = sorted(self.buckets)
        
        # Track bucket counts and total
        self._bucket_counts: Dict[str, Dict[float, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self._counts: Dict[str, int] = defaultdict(int)
        self._sums: Dict[str, float] = defaultdict(float)
    
    def observe(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Observe a value.
        
        Args:
            value: Value to observe
            labels: Label values
        """
        labels = labels or {}
        label_key = self._make_label_key(labels)
        
        with self._lock:
            self._counts[label_key] += 1
            self._sums[label_key] += value
            
            # Update bucket counts
            for bucket in self.buckets:
                if value <= bucket:
                    self._bucket_counts[label_key][bucket] += 1
    
    def get_count(self, labels: Optional[Dict[str, str]] = None) -> int:
        """
        Get total count of observations.
        
        Args:
            labels: Label values
            
        Returns:
            int: Total count
        """
        labels = labels or {}
        label_key = self._make_label_key(labels)
        
        with self._lock:
            return self._counts[label_key]
    
    def get_sum(self, labels: Optional[Dict[str, str]] = None) -> float:
        """
        Get sum of all observed values.
        
        Args:
            labels: Label values
            
        Returns:
            float: Sum of values
        """
        labels = labels or {}
        label_key = self._make_label_key(labels)
        
        with self._lock:
            return self._sums[label_key]
    
    def collect(self) -> List[MetricValue]:
        """Collect histogram values."""
        with self._lock:
            values = []
            
            for label_key in self._counts.keys():
                # Parse labels back from key
                labels = {}
                if label_key:
                    for pair in label_key.split(','):
                        k, v = pair.split('=', 1)
                        labels[k] = v
                
                # Add bucket counts
                for bucket in self.buckets:
                    bucket_labels = labels.copy()
                    bucket_labels['le'] = str(bucket) if bucket != float('inf') else '+Inf'
                    
                    cumulative_count = sum(
                        count for b, count in self._bucket_counts[label_key].items()
                        if b <= bucket
                    )
                    
                    values.append(MetricValue(
                        value=cumulative_count,
                        timestamp=time.time(),
                        labels=bucket_labels
                    ))
                
                # Add count and sum
                count_labels = labels.copy()
                count_labels['__name__'] = f"{self.name}_count"
                values.append(MetricValue(
                    value=self._counts[label_key],
                    timestamp=time.time(),
                    labels=count_labels
                ))
                
                sum_labels = labels.copy()
                sum_labels['__name__'] = f"{self.name}_sum"
                values.append(MetricValue(
                    value=self._sums[label_key],
                    timestamp=time.time(),
                    labels=sum_labels
                ))
            
            return values


class Timer:
    """
    Timer utility for measuring execution time with automatic metric recording.
    """
    
    def __init__(
        self,
        histogram: Histogram,
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Initialize timer.
        
        Args:
            histogram: Histogram to record timing to
            labels: Label values
        """
        self.histogram = histogram
        self.labels = labels or {}
        self.start_time: Optional[float] = None
    
    def start(self) -> 'Timer':
        """Start timing."""
        self.start_time = time.time()
        return self
    
    def stop(self) -> float:
        """
        Stop timing and record duration.
        
        Returns:
            float: Elapsed time in seconds
        """
        if self.start_time is None:
            raise RuntimeError("Timer not started")
        
        duration = time.time() - self.start_time
        self.histogram.observe(duration, self.labels)
        self.start_time = None
        
        return duration
    
    def __enter__(self) -> 'Timer':
        """Context manager entry."""
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()


class MetricsCollector:
    """
    Central metrics collector and registry.
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self.metrics: Dict[str, BaseMetric] = {}
        self._lock = threading.Lock()
    
    def register(self, metric: BaseMetric) -> BaseMetric:
        """
        Register a metric.
        
        Args:
            metric: Metric to register
            
        Returns:
            BaseMetric: The registered metric
            
        Raises:
            ValueError: If metric name already exists
        """
        with self._lock:
            if metric.name in self.metrics:
                raise ValueError(f"Metric {metric.name} already registered")
            
            self.metrics[metric.name] = metric
            return metric
    
    def counter(
        self,
        name: str,
        description: str = "",
        labels: Optional[List[str]] = None
    ) -> Counter:
        """
        Create or get counter metric.
        
        Args:
            name: Metric name
            description: Metric description
            labels: Label names
            
        Returns:
            Counter: Counter metric
        """
        if name in self.metrics:
            metric = self.metrics[name]
            if not isinstance(metric, Counter):
                raise ValueError(f"Metric {name} is not a counter")
            return metric
        
        counter = Counter(name, description, labels)
        return self.register(counter)
    
    def gauge(
        self,
        name: str,
        description: str = "",
        labels: Optional[List[str]] = None
    ) -> Gauge:
        """
        Create or get gauge metric.
        
        Args:
            name: Metric name
            description: Metric description
            labels: Label names
            
        Returns:
            Gauge: Gauge metric
        """
        if name in self.metrics:
            metric = self.metrics[name]
            if not isinstance(metric, Gauge):
                raise ValueError(f"Metric {name} is not a gauge")
            return metric
        
        gauge = Gauge(name, description, labels)
        return self.register(gauge)
    
    def histogram(
        self,
        name: str,
        description: str = "",
        labels: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None
    ) -> Histogram:
        """
        Create or get histogram metric.
        
        Args:
            name: Metric name
            description: Metric description
            labels: Label names
            buckets: Histogram buckets
            
        Returns:
            Histogram: Histogram metric
        """
        if name in self.metrics:
            metric = self.metrics[name]
            if not isinstance(metric, Histogram):
                raise ValueError(f"Metric {name} is not a histogram")
            return metric
        
        histogram = Histogram(name, description, labels, buckets=buckets)
        return self.register(histogram)
    
    def timer(
        self,
        histogram: Histogram,
        labels: Optional[Dict[str, str]] = None
    ) -> Timer:
        """
        Create timer for histogram.
        
        Args:
            histogram: Histogram to record to
            labels: Label values
            
        Returns:
            Timer: Timer instance
        """
        return Timer(histogram, labels)
    
    def collect_all(self) -> Dict[str, List[MetricValue]]:
        """
        Collect all metric values.
        
        Returns:
            Dict[str, List[MetricValue]]: All metric values by name
        """
        with self._lock:
            all_values = {}
            for name, metric in self.metrics.items():
                all_values[name] = metric.collect()
            return all_values
    
    def get_metric(self, name: str) -> Optional[BaseMetric]:
        """
        Get metric by name.
        
        Args:
            name: Metric name
            
        Returns:
            Optional[BaseMetric]: Metric if found
        """
        with self._lock:
            return self.metrics.get(name)
    
    def list_metrics(self) -> List[str]:
        """
        List all metric names.
        
        Returns:
            List[str]: Metric names
        """
        with self._lock:
            return list(self.metrics.keys())
    
    def clear(self) -> None:
        """Clear all metrics."""
        with self._lock:
            self.metrics.clear()


class PrometheusExporter:
    """
    Exports metrics in Prometheus text format.
    """
    
    def __init__(self, collector: MetricsCollector):
        """
        Initialize Prometheus exporter.
        
        Args:
            collector: Metrics collector
        """
        self.collector = collector
    
    def export(self) -> str:
        """
        Export metrics in Prometheus text format.
        
        Returns:
            str: Prometheus format metrics
        """
        output_lines = []
        all_values = self.collector.collect_all()
        
        for metric_name, values in all_values.items():
            if not values:
                continue
            
            metric = self.collector.get_metric(metric_name)
            if not metric:
                continue
            
            # Add HELP and TYPE comments
            if metric.description:
                output_lines.append(f"# HELP {metric_name} {metric.description}")
            
            output_lines.append(f"# TYPE {metric_name} {metric.get_prometheus_type()}")
            
            # Add metric values
            for value in values:
                if value.labels:
                    label_str = ','.join(f'{k}="{v}"' for k, v in value.labels.items())
                    line = f"{metric_name}{{{label_str}}} {value.value}"
                else:
                    line = f"{metric_name} {value.value}"
                
                output_lines.append(line)
            
            output_lines.append("")  # Empty line between metrics
        
        return '\n'.join(output_lines)
    
    async def serve_http(self, host: str = "0.0.0.0", port: int = 9090) -> None:
        """
        Serve metrics over HTTP.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        try:
            from aiohttp import web
        except ImportError:
            raise ImportError("aiohttp required for HTTP metrics server")
        
        async def metrics_handler(request):
            """Handle metrics request."""
            metrics_text = self.export()
            return web.Response(text=metrics_text, content_type='text/plain')
        
        app = web.Application()
        app.router.add_get('/metrics', metrics_handler)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        print(f"Metrics server started on http://{host}:{port}/metrics")


# Global metrics collector
_metrics_collector: Optional[MetricsCollector] = None


def setup_metrics() -> MetricsCollector:
    """
    Set up global metrics collector.
    
    Returns:
        MetricsCollector: Global metrics collector
    """
    global _metrics_collector
    
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    
    return _metrics_collector


def get_metrics_collector() -> MetricsCollector:
    """
    Get global metrics collector.
    
    Returns:
        MetricsCollector: Global metrics collector
    """
    if _metrics_collector is None:
        return setup_metrics()
    
    return _metrics_collector


# Pre-defined metric sets for common components

class AgentMetrics:
    """Metrics for AI agents."""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        
        # Agent lifecycle metrics
        self.agents_total = collector.counter(
            "sophia_agents_total",
            "Total number of agents created",
            ["agent_type"]
        )
        
        self.agents_active = collector.gauge(
            "sophia_agents_active",
            "Number of currently active agents",
            ["agent_type", "state"]
        )
        
        # Message processing metrics
        self.messages_processed_total = collector.counter(
            "sophia_agent_messages_processed_total",
            "Total messages processed by agents",
            ["agent_id", "message_type", "status"]
        )
        
        self.message_processing_duration = collector.histogram(
            "sophia_agent_message_processing_seconds",
            "Time spent processing messages",
            ["agent_id", "message_type"],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, float('inf')]
        )
        
        # Task execution metrics
        self.tasks_executed_total = collector.counter(
            "sophia_agent_tasks_executed_total",
            "Total tasks executed by agents",
            ["agent_id", "task_type", "status"]
        )
        
        self.task_execution_duration = collector.histogram(
            "sophia_agent_task_execution_seconds",
            "Time spent executing tasks",
            ["agent_id", "task_type"]
        )
        
        # Error metrics
        self.errors_total = collector.counter(
            "sophia_agent_errors_total",
            "Total agent errors",
            ["agent_id", "error_type"]
        )


class SwarmMetrics:
    """Metrics for agent swarms."""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        
        # Swarm lifecycle metrics
        self.swarms_total = collector.counter(
            "sophia_swarms_total",
            "Total number of swarms created",
            ["topology"]
        )
        
        self.swarms_active = collector.gauge(
            "sophia_swarms_active",
            "Number of currently active swarms",
            ["topology", "state"]
        )
        
        # Member metrics
        self.swarm_members = collector.gauge(
            "sophia_swarm_members",
            "Number of members in swarms",
            ["swarm_id", "role", "status"]
        )
        
        # Task distribution metrics
        self.tasks_distributed_total = collector.counter(
            "sophia_swarm_tasks_distributed_total",
            "Total tasks distributed in swarms",
            ["swarm_id", "task_type", "status"]
        )
        
        self.task_distribution_duration = collector.histogram(
            "sophia_swarm_task_distribution_seconds",
            "Time spent distributing tasks",
            ["swarm_id"]
        )
        
        # Coordination metrics
        self.coordination_cycles_total = collector.counter(
            "sophia_swarm_coordination_cycles_total",
            "Total coordination cycles executed",
            ["swarm_id"]
        )
        
        self.coordination_duration = collector.histogram(
            "sophia_swarm_coordination_seconds",
            "Time spent in coordination",
            ["swarm_id"]
        )


class ToolMetrics:
    """Metrics for tools."""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        
        # Tool execution metrics
        self.executions_total = collector.counter(
            "sophia_tool_executions_total",
            "Total tool executions",
            ["tool_name", "status"]
        )
        
        self.execution_duration = collector.histogram(
            "sophia_tool_execution_seconds",
            "Tool execution duration",
            ["tool_name"]
        )
        
        # Tool registry metrics
        self.tools_registered = collector.gauge(
            "sophia_tools_registered",
            "Number of registered tools",
            ["category"]
        )
        
        # Error metrics
        self.execution_errors_total = collector.counter(
            "sophia_tool_execution_errors_total",
            "Total tool execution errors",
            ["tool_name", "error_type"]
        )


class MemoryMetrics:
    """Metrics for memory systems."""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        
        # Memory storage metrics
        self.entries_total = collector.gauge(
            "sophia_memory_entries_total",
            "Total memory entries",
            ["memory_type"]
        )
        
        self.memory_usage_bytes = collector.gauge(
            "sophia_memory_usage_bytes",
            "Memory usage in bytes",
            ["memory_type"]
        )
        
        # Memory operations
        self.operations_total = collector.counter(
            "sophia_memory_operations_total",
            "Total memory operations",
            ["memory_type", "operation", "status"]
        )
        
        self.operation_duration = collector.histogram(
            "sophia_memory_operation_seconds",
            "Memory operation duration",
            ["memory_type", "operation"]
        )
        
        # Query metrics
        self.queries_total = collector.counter(
            "sophia_memory_queries_total",
            "Total memory queries",
            ["memory_type", "strategy"]
        )
        
        self.query_results = collector.histogram(
            "sophia_memory_query_results",
            "Number of results per query",
            ["memory_type", "strategy"],
            buckets=[0, 1, 5, 10, 25, 50, 100, float('inf')]
        )


# Convenience functions to get pre-configured metric sets
def agent_metrics() -> AgentMetrics:
    """Get agent metrics."""
    return AgentMetrics(get_metrics_collector())


def swarm_metrics() -> SwarmMetrics:
    """Get swarm metrics."""
    return SwarmMetrics(get_metrics_collector())


def tool_metrics() -> ToolMetrics:
    """Get tool metrics."""
    return ToolMetrics(get_metrics_collector())


def memory_metrics() -> MemoryMetrics:
    """Get memory metrics."""
    return MemoryMetrics(get_metrics_collector())