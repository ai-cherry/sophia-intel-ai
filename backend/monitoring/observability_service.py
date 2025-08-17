"""
Observability Service for SOPHIA Intel
Comprehensive monitoring, logging, and observability
"""

from typing import Dict, List, Any, Optional, Callable
import logging
import asyncio
from datetime import datetime, timedelta
import json
import time
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Metric:
    name: str
    value: float
    metric_type: MetricType
    labels: Dict[str, str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
            'metric_type': self.metric_type.value
        }


@dataclass
class LogEntry:
    level: str
    message: str
    timestamp: datetime
    service: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class TraceSpan:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: Optional[float]
    labels: Dict[str, str]
    status: str = "ok"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None
        }


class ObservabilityService:
    """Comprehensive observability service"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.metrics: List[Metric] = []
        self.logs: List[LogEntry] = []
        self.traces: Dict[str, List[TraceSpan]] = {}
        self.active_spans: Dict[str, TraceSpan] = {}
        self.metric_collectors: Dict[str, Callable] = {}
        self.alert_rules: List[Dict[str, Any]] = []
        self.dashboards: Dict[str, Dict[str, Any]] = {}
        self.is_running = False
        
    async def initialize(self) -> None:
        """Initialize observability service"""
        self.is_running = True
        
        # Set up default metric collectors
        self._setup_default_collectors()
        
        # Set up default alert rules
        self._setup_default_alerts()
        
        # Set up default dashboards
        self._setup_default_dashboards()
        
        # Start background tasks
        asyncio.create_task(self._metrics_collection_loop())
        asyncio.create_task(self._log_processing_loop())
        asyncio.create_task(self._alert_processing_loop())
        
        logger.info("✅ Observability service initialized")
    
    async def shutdown(self) -> None:
        """Shutdown observability service"""
        self.is_running = False
        logger.info("🔒 Observability service shutdown")
    
    # Metrics Management
    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric"""
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            labels=labels or {},
            timestamp=datetime.now()
        )
        
        self.metrics.append(metric)
        
        # Keep only recent metrics (last 10000)
        if len(self.metrics) > 10000:
            self.metrics = self.metrics[-10000:]
    
    def increment_counter(self, name: str, labels: Optional[Dict[str, str]] = None, value: float = 1.0) -> None:
        """Increment a counter metric"""
        self.record_metric(name, value, MetricType.COUNTER, labels)
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric"""
        self.record_metric(name, value, MetricType.GAUGE, labels)
    
    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram metric"""
        self.record_metric(name, value, MetricType.HISTOGRAM, labels)
    
    def time_operation(self, name: str, labels: Optional[Dict[str, str]] = None):
        """Context manager for timing operations"""
        return TimerContext(self, name, labels)
    
    def register_metric_collector(self, name: str, collector: Callable) -> None:
        """Register a custom metric collector"""
        self.metric_collectors[name] = collector
        logger.info(f"✅ Registered metric collector: {name}")
    
    # Logging Management
    def log(
        self,
        level: str,
        message: str,
        service: str = "sophia-intel",
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Log a message"""
        log_entry = LogEntry(
            level=level,
            message=message,
            timestamp=datetime.now(),
            service=service,
            trace_id=trace_id,
            span_id=span_id,
            labels=labels
        )
        
        self.logs.append(log_entry)
        
        # Keep only recent logs (last 50000)
        if len(self.logs) > 50000:
            self.logs = self.logs[-50000:]
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message"""
        self.log("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        self.log("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message"""
        self.log("ERROR", message, **kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        self.log("DEBUG", message, **kwargs)
    
    # Distributed Tracing
    def start_trace(self, operation_name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Start a new trace"""
        trace_id = f"trace_{int(time.time() * 1000000)}"
        span_id = f"span_{int(time.time() * 1000000)}"
        
        span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=None,
            operation_name=operation_name,
            start_time=datetime.now(),
            end_time=None,
            duration_ms=None,
            labels=labels or {}
        )
        
        self.active_spans[span_id] = span
        
        if trace_id not in self.traces:
            self.traces[trace_id] = []
        
        return trace_id
    
    def start_span(
        self,
        trace_id: str,
        operation_name: str,
        parent_span_id: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> str:
        """Start a new span within a trace"""
        span_id = f"span_{int(time.time() * 1000000)}"
        
        span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=datetime.now(),
            end_time=None,
            duration_ms=None,
            labels=labels or {}
        )
        
        self.active_spans[span_id] = span
        
        if trace_id not in self.traces:
            self.traces[trace_id] = []
        
        return span_id
    
    def finish_span(self, span_id: str, status: str = "ok") -> None:
        """Finish a span"""
        if span_id in self.active_spans:
            span = self.active_spans[span_id]
            span.end_time = datetime.now()
            span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
            span.status = status
            
            # Move to completed traces
            self.traces[span.trace_id].append(span)
            del self.active_spans[span_id]
    
    def trace_operation(self, operation_name: str, labels: Optional[Dict[str, str]] = None):
        """Context manager for tracing operations"""
        return TraceContext(self, operation_name, labels)
    
    # Alerting
    def add_alert_rule(self, rule: Dict[str, Any]) -> None:
        """Add an alert rule"""
        self.alert_rules.append(rule)
        logger.info(f"✅ Added alert rule: {rule.get('name', 'unnamed')}")
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check all alert rules and return triggered alerts"""
        triggered_alerts = []
        
        for rule in self.alert_rules:
            if self._evaluate_alert_rule(rule):
                alert = {
                    "rule_name": rule.get("name", "unnamed"),
                    "severity": rule.get("severity", "warning"),
                    "message": rule.get("message", "Alert triggered"),
                    "timestamp": datetime.now().isoformat(),
                    "labels": rule.get("labels", {})
                }
                triggered_alerts.append(alert)
        
        return triggered_alerts
    
    # Dashboards
    def create_dashboard(self, name: str, config: Dict[str, Any]) -> None:
        """Create a dashboard"""
        self.dashboards[name] = {
            "name": name,
            "config": config,
            "created_at": datetime.now().isoformat()
        }
        logger.info(f"✅ Created dashboard: {name}")
    
    def get_dashboard_data(self, dashboard_name: str) -> Dict[str, Any]:
        """Get dashboard data"""
        if dashboard_name not in self.dashboards:
            return {"error": "Dashboard not found"}
        
        dashboard = self.dashboards[dashboard_name]
        config = dashboard["config"]
        
        dashboard_data = {
            "name": dashboard_name,
            "data": {},
            "last_updated": datetime.now().isoformat()
        }
        
        # Collect data for each panel
        for panel_name, panel_config in config.get("panels", {}).items():
            panel_data = self._collect_panel_data(panel_config)
            dashboard_data["data"][panel_name] = panel_data
        
        return dashboard_data
    
    # Query Interface
    def query_metrics(
        self,
        metric_name: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Query metrics"""
        filtered_metrics = self.metrics
        
        # Filter by metric name
        if metric_name:
            filtered_metrics = [m for m in filtered_metrics if m.name == metric_name]
        
        # Filter by labels
        if labels:
            filtered_metrics = [
                m for m in filtered_metrics
                if all(m.labels.get(k) == v for k, v in labels.items())
            ]
        
        # Filter by time range
        if start_time:
            filtered_metrics = [m for m in filtered_metrics if m.timestamp >= start_time]
        if end_time:
            filtered_metrics = [m for m in filtered_metrics if m.timestamp <= end_time]
        
        # Apply limit
        filtered_metrics = filtered_metrics[-limit:]
        
        return [m.to_dict() for m in filtered_metrics]
    
    def query_logs(
        self,
        level: Optional[str] = None,
        service: Optional[str] = None,
        trace_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Query logs"""
        filtered_logs = self.logs
        
        # Filter by level
        if level:
            filtered_logs = [l for l in filtered_logs if l.level == level]
        
        # Filter by service
        if service:
            filtered_logs = [l for l in filtered_logs if l.service == service]
        
        # Filter by trace ID
        if trace_id:
            filtered_logs = [l for l in filtered_logs if l.trace_id == trace_id]
        
        # Filter by time range
        if start_time:
            filtered_logs = [l for l in filtered_logs if l.timestamp >= start_time]
        if end_time:
            filtered_logs = [l for l in filtered_logs if l.timestamp <= end_time]
        
        # Apply limit
        filtered_logs = filtered_logs[-limit:]
        
        return [l.to_dict() for l in filtered_logs]
    
    def query_traces(
        self,
        trace_id: Optional[str] = None,
        operation_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query traces"""
        traces_data = []
        
        for tid, spans in self.traces.items():
            if trace_id and tid != trace_id:
                continue
            
            trace_spans = []
            for span in spans:
                if operation_name and span.operation_name != operation_name:
                    continue
                
                if start_time and span.start_time < start_time:
                    continue
                
                if end_time and span.start_time > end_time:
                    continue
                
                trace_spans.append(span.to_dict())
            
            if trace_spans:
                traces_data.append({
                    "trace_id": tid,
                    "spans": trace_spans,
                    "span_count": len(trace_spans)
                })
        
        return traces_data[-limit:]
    
    # Health Check
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return {
            "status": "healthy" if self.is_running else "unhealthy",
            "metrics_count": len(self.metrics),
            "logs_count": len(self.logs),
            "traces_count": len(self.traces),
            "active_spans_count": len(self.active_spans),
            "alert_rules_count": len(self.alert_rules),
            "dashboards_count": len(self.dashboards),
            "last_check": datetime.now().isoformat()
        }
    
    # Private Methods
    async def _metrics_collection_loop(self) -> None:
        """Background metrics collection loop"""
        while self.is_running:
            try:
                # Run custom metric collectors
                for name, collector in self.metric_collectors.items():
                    try:
                        await collector()
                    except Exception as e:
                        logger.error(f"Error in metric collector {name}: {e}")
                
                await asyncio.sleep(60)  # Collect every minute
                
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(60)
    
    async def _log_processing_loop(self) -> None:
        """Background log processing loop"""
        while self.is_running:
            try:
                # Process logs (e.g., send to external systems)
                # This is a placeholder for actual log processing
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in log processing loop: {e}")
                await asyncio.sleep(30)
    
    async def _alert_processing_loop(self) -> None:
        """Background alert processing loop"""
        while self.is_running:
            try:
                triggered_alerts = self.check_alerts()
                
                for alert in triggered_alerts:
                    # Process alert (e.g., send notifications)
                    logger.warning(f"🚨 Alert triggered: {alert['rule_name']} - {alert['message']}")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in alert processing loop: {e}")
                await asyncio.sleep(60)
    
    def _setup_default_collectors(self) -> None:
        """Set up default metric collectors"""
        async def system_metrics_collector():
            # Collect system metrics
            self.set_gauge("sophia.system.cpu_usage", 45.2, {"host": "sophia-backend"})
            self.set_gauge("sophia.system.memory_usage", 62.8, {"host": "sophia-backend"})
            self.set_gauge("sophia.system.disk_usage", 35.1, {"host": "sophia-backend"})
        
        self.register_metric_collector("system_metrics", system_metrics_collector)
    
    def _setup_default_alerts(self) -> None:
        """Set up default alert rules"""
        self.add_alert_rule({
            "name": "high_error_rate",
            "condition": "error_rate > 0.05",
            "severity": "critical",
            "message": "Error rate is above 5%",
            "labels": {"team": "platform"}
        })
        
        self.add_alert_rule({
            "name": "high_response_time",
            "condition": "avg_response_time > 2000",
            "severity": "warning",
            "message": "Average response time is above 2 seconds",
            "labels": {"team": "platform"}
        })
    
    def _setup_default_dashboards(self) -> None:
        """Set up default dashboards"""
        self.create_dashboard("sophia_overview", {
            "panels": {
                "system_health": {
                    "type": "gauge",
                    "metric": "sophia.system.health_score"
                },
                "request_rate": {
                    "type": "graph",
                    "metric": "sophia.requests.rate"
                },
                "error_rate": {
                    "type": "graph",
                    "metric": "sophia.requests.error_rate"
                },
                "response_time": {
                    "type": "histogram",
                    "metric": "sophia.requests.duration"
                }
            }
        })
    
    def _evaluate_alert_rule(self, rule: Dict[str, Any]) -> bool:
        """Evaluate an alert rule"""
        # Simplified alert evaluation
        condition = rule.get("condition", "")
        
        if "error_rate > 0.05" in condition:
            # Check recent error metrics
            recent_errors = [
                m for m in self.metrics[-100:]
                if m.name == "sophia.requests.errors" and
                m.timestamp > datetime.now() - timedelta(minutes=5)
            ]
            if recent_errors:
                error_rate = sum(m.value for m in recent_errors) / len(recent_errors)
                return error_rate > 0.05
        
        return False
    
    def _collect_panel_data(self, panel_config: Dict[str, Any]) -> Dict[str, Any]:
        """Collect data for a dashboard panel"""
        panel_type = panel_config.get("type", "gauge")
        metric_name = panel_config.get("metric", "")
        
        # Get recent metrics for this panel
        recent_metrics = [
            m for m in self.metrics[-1000:]
            if m.name == metric_name and
            m.timestamp > datetime.now() - timedelta(hours=1)
        ]
        
        if panel_type == "gauge":
            return {
                "type": "gauge",
                "value": recent_metrics[-1].value if recent_metrics else 0,
                "timestamp": recent_metrics[-1].timestamp.isoformat() if recent_metrics else None
            }
        elif panel_type == "graph":
            return {
                "type": "graph",
                "data_points": [
                    {"timestamp": m.timestamp.isoformat(), "value": m.value}
                    for m in recent_metrics
                ]
            }
        elif panel_type == "histogram":
            return {
                "type": "histogram",
                "buckets": self._create_histogram_buckets(recent_metrics)
            }
        
        return {"type": "unknown", "data": []}
    
    def _create_histogram_buckets(self, metrics: List[Metric]) -> List[Dict[str, Any]]:
        """Create histogram buckets from metrics"""
        if not metrics:
            return []
        
        values = [m.value for m in metrics]
        min_val, max_val = min(values), max(values)
        bucket_size = (max_val - min_val) / 10 if max_val > min_val else 1
        
        buckets = []
        for i in range(10):
            bucket_min = min_val + i * bucket_size
            bucket_max = min_val + (i + 1) * bucket_size
            count = len([v for v in values if bucket_min <= v < bucket_max])
            
            buckets.append({
                "min": bucket_min,
                "max": bucket_max,
                "count": count
            })
        
        return buckets


class TimerContext:
    """Context manager for timing operations"""
    
    def __init__(self, observability_service: ObservabilityService, name: str, labels: Optional[Dict[str, str]] = None):
        self.observability_service = observability_service
        self.name = name
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (time.time() - self.start_time) * 1000  # Convert to milliseconds
            self.observability_service.record_metric(
                self.name,
                duration,
                MetricType.TIMER,
                self.labels
            )


class TraceContext:
    """Context manager for tracing operations"""
    
    def __init__(self, observability_service: ObservabilityService, operation_name: str, labels: Optional[Dict[str, str]] = None):
        self.observability_service = observability_service
        self.operation_name = operation_name
        self.labels = labels
        self.trace_id = None
        self.span_id = None
    
    def __enter__(self):
        self.trace_id = self.observability_service.start_trace(self.operation_name, self.labels)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span_id:
            status = "error" if exc_type else "ok"
            self.observability_service.finish_span(self.span_id, status)

