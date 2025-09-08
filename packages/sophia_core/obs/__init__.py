"""
Observability Module

Provides structured logging, metrics collection, and monitoring capabilities
for AI agents and swarms with support for redaction and privacy protection.
"""

from .logging import (
    StructuredLogger,
    RedactingFormatter,
    LogLevel,
    LogRecord,
    setup_logging,
    get_logger,
    log_agent_activity,
    log_swarm_activity,
    log_tool_execution,
    log_memory_operation
)

from .metrics import (
    MetricsCollector,
    Counter,
    Gauge,
    Histogram,
    Timer,
    MetricType,
    MetricValue,
    PrometheusExporter,
    setup_metrics,
    get_metrics_collector,
    agent_metrics,
    swarm_metrics,
    tool_metrics,
    memory_metrics
)

__all__ = [
    # Logging
    "StructuredLogger",
    "RedactingFormatter",
    "LogLevel",
    "LogRecord",
    "setup_logging",
    "get_logger",
    "log_agent_activity",
    "log_swarm_activity", 
    "log_tool_execution",
    "log_memory_operation",
    
    # Metrics
    "MetricsCollector",
    "Counter",
    "Gauge", 
    "Histogram",
    "Timer",
    "MetricType",
    "MetricValue",
    "PrometheusExporter",
    "setup_metrics",
    "get_metrics_collector",
    "agent_metrics",
    "swarm_metrics",
    "tool_metrics", 
    "memory_metrics"
]