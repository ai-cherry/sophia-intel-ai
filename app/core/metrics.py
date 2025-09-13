"""
Prometheus metrics helpers
"""

from prometheus_client import Counter, Histogram, Gauge
import time
from typing import Optional

# Define metrics
aiml_requests = Counter("aiml_requests_total", "Total AIML API requests", ["model"])
aiml_duration = Histogram("aiml_request_duration_seconds", "AIML request duration", ["model"])
aiml_errors = Counter("aiml_errors_total", "AIML API errors", ["model", "error_type"])

mcp_requests = Counter("mcp_requests_total", "Total MCP requests", ["service", "method"])
mcp_duration = Histogram("mcp_request_duration_seconds", "MCP request duration", ["service", "method"])
mcp_errors = Counter("mcp_errors_total", "MCP errors", ["service", "error_type"])

http_requests = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
http_duration = Histogram("http_request_duration_seconds", "HTTP request duration", ["method", "endpoint"])

active_connections = Gauge("active_websocket_connections", "Active WebSocket connections")


def inc_counter(metric_name: str, label: Optional[str] = None, **labels):
    """Increment a counter metric"""
    if metric_name == "aiml_requests_total" and label:
        aiml_requests.labels(model=label).inc()
    elif metric_name == "mcp_requests_total" and "service" in labels and "method" in labels:
        mcp_requests.labels(service=labels["service"], method=labels["method"]).inc()
    elif metric_name == "http_requests_total" and all(k in labels for k in ["method", "endpoint", "status"]):
        http_requests.labels(
            method=labels["method"], 
            endpoint=labels["endpoint"], 
            status=labels["status"]
        ).inc()


def observe_duration(metric_name: str, duration: float, **labels):
    """Record a duration metric"""
    if metric_name == "aiml_request_duration" and "model" in labels:
        aiml_duration.labels(model=labels["model"]).observe(duration)
    elif metric_name == "mcp_request_duration" and "service" in labels and "method" in labels:
        mcp_duration.labels(service=labels["service"], method=labels["method"]).observe(duration)
    elif metric_name == "http_request_duration" and "method" in labels and "endpoint" in labels:
        http_duration.labels(method=labels["method"], endpoint=labels["endpoint"]).observe(duration)


def inc_error(metric_name: str, error_type: str, **labels):
    """Increment an error counter"""
    if metric_name == "aiml_errors" and "model" in labels:
        aiml_errors.labels(model=labels["model"], error_type=error_type).inc()
    elif metric_name == "mcp_errors" and "service" in labels:
        mcp_errors.labels(service=labels["service"], error_type=error_type).inc()


class MetricsTimer:
    """Context manager for timing operations"""
    
    def __init__(self, metric_name: str, **labels):
        self.metric_name = metric_name
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            observe_duration(self.metric_name, duration, **self.labels)