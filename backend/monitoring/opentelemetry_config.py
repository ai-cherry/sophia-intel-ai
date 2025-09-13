"""
OpenTelemetry Configuration for Sophia AI V9.7
Provides comprehensive monitoring, tracing, and metrics collection
"""
import logging
import os
from contextlib import contextmanager
from typing import Any, Dict, Optional
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
# Exporters
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.asyncio import AsyncioInstrumentor
# Instrumentation
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.semconv.resource import ResourceAttributes
# Custom exporters for production
try:
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    JAEGER_AVAILABLE = True
except ImportError:
    JAEGER_AVAILABLE = False
logger = logging.getLogger(__name__)
class SophiaAITelemetryConfig:
    """Configuration for Sophia AI telemetry"""
    def __init__(self):
        self.service_name = os.getenv("OTEL_SERVICE_NAME", "sophia-ai-v97")
        self.service_version = os.getenv("OTEL_SERVICE_VERSION", "9.7.0")
        self.environment = os.getenv("ENVIRONMENT", "development")
        # Tracing configuration
        self.enable_tracing = os.getenv("OTEL_ENABLE_TRACING", "true").lower() == "true"
        self.jaeger_endpoint = os.getenv(
            "JAEGER_ENDPOINT", "http://localhost:14268/api/traces"
        )
        self.otlp_endpoint = os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"
        )
        # Metrics configuration
        self.enable_metrics = os.getenv("OTEL_ENABLE_METRICS", "true").lower() == "true"
        self.prometheus_port = int(os.getenv("PROMETHEUS_PORT", "8000"))
        self.metrics_export_interval = int(
            os.getenv("OTEL_METRICS_EXPORT_INTERVAL", "30")
        )
        # Sampling configuration
        self.trace_sample_rate = float(os.getenv("OTEL_TRACE_SAMPLE_RATE", "1.0"))
        # Custom attributes
        self.custom_attributes = {
            "sophia.ai.version": "9.7.0",
            "sophia.ai.component": "backend",
            "sophia.ai.deployment": self.environment,
            "sophia.ai.features": "oss_premium_hybrid",
        }
class SophiaAITelemetry:
    """Main telemetry manager for Sophia AI"""
    def __init__(self, config: Optional[SophiaAITelemetryConfig] = None):
        self.config = config or SophiaAITelemetryConfig()
        self.tracer_provider = None
        self.meter_provider = None
        self.initialized = False
        # Custom metrics
        self.custom_metrics = {}
    def initialize(self):
        """Initialize OpenTelemetry with Sophia AI configuration"""
        if self.initialized:
            logger.warning("Telemetry already initialized")
            return
        try:
            # Create resource with Sophia AI attributes
            resource = Resource.create(
                {
                    ResourceAttributes.SERVICE_NAME: self.config.service_name,
                    ResourceAttributes.SERVICE_VERSION: self.config.service_version,
                    ResourceAttributes.DEPLOYMENT_ENVIRONMENT: self.config.environment,
                    **self.config.custom_attributes,
                }
            )
            # Initialize tracing
            if self.config.enable_tracing:
                self._initialize_tracing(resource)
            # Initialize metrics
            if self.config.enable_metrics:
                self._initialize_metrics(resource)
            # Initialize instrumentation
            self._initialize_instrumentation()
            # Create custom metrics
            self._create_custom_metrics()
            self.initialized = True
            logger.info(
                f"Sophia AI telemetry initialized for {self.config.service_name} v{self.config.service_version}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize telemetry: {e}")
            raise
    def _initialize_tracing(self, resource: Resource):
        """Initialize tracing with multiple exporters"""
        # Create tracer provider
        self.tracer_provider = TracerProvider(resource=resource)
        # Add exporters based on environment
        exporters = []
        # Console exporter for development
        if self.config.environment == "development":
            console_exporter = ConsoleSpanExporter()
            console_processor = BatchSpanProcessor(console_exporter)
            self.tracer_provider.add_span_processor(console_processor)
            exporters.append("console")
        # Jaeger exporter for distributed tracing
        if JAEGER_AVAILABLE and self.config.jaeger_endpoint:
            try:
                jaeger_exporter = JaegerExporter(
                    agent_host_name="localhost",
                    agent_port=6831,
                )
                jaeger_processor = BatchSpanProcessor(jaeger_exporter)
                self.tracer_provider.add_span_processor(jaeger_processor)
                exporters.append("jaeger")
            except Exception as e:
                logger.warning(f"Failed to initialize Jaeger exporter: {e}")
        # OTLP exporter for production
        if self.config.otlp_endpoint:
            try:
                otlp_exporter = OTLPSpanExporter(endpoint=self.config.otlp_endpoint)
                otlp_processor = BatchSpanProcessor(otlp_exporter)
                self.tracer_provider.add_span_processor(otlp_processor)
                exporters.append("otlp")
            except Exception as e:
                logger.warning(f"Failed to initialize OTLP exporter: {e}")
        # Set global tracer provider
        trace.set_tracer_provider(self.tracer_provider)
        logger.info(f"Tracing initialized with exporters: {exporters}")
    def _initialize_metrics(self, resource: Resource):
        """Initialize metrics with multiple readers"""
        readers = []
        # Console metrics for development
        if self.config.environment == "development":
            console_reader = PeriodicExportingMetricReader(
                ConsoleMetricExporter(),
                export_interval_millis=self.config.metrics_export_interval * 1000,
            )
            readers.append(console_reader)
        # Prometheus metrics for production monitoring
        try:
            prometheus_reader = PrometheusMetricReader()
            readers.append(prometheus_reader)
        except Exception as e:
            logger.warning(f"Failed to initialize Prometheus reader: {e}")
        # OTLP metrics for centralized collection
        if self.config.otlp_endpoint:
            try:
                otlp_reader = PeriodicExportingMetricReader(
                    OTLPMetricExporter(endpoint=self.config.otlp_endpoint),
                    export_interval_millis=self.config.metrics_export_interval * 1000,
                )
                readers.append(otlp_reader)
            except Exception as e:
                logger.warning(f"Failed to initialize OTLP metrics reader: {e}")
        # Create meter provider
        self.meter_provider = MeterProvider(resource=resource, metric_readers=readers)
        # Set global meter provider
        metrics.set_meter_provider(self.meter_provider)
        logger.info(f"Metrics initialized with {len(readers)} readers")
    def _initialize_instrumentation(self):
        """Initialize automatic instrumentation"""
        try:
            # FastAPI instrumentation
            FastAPIInstrumentor().instrument()
            # HTTP requests instrumentation
            RequestsInstrumentor().instrument()
            # SQLAlchemy instrumentation
            SQLAlchemyInstrumentor().instrument()
            # Redis instrumentation
            RedisInstrumentor().instrument()
            # Asyncio instrumentation
            AsyncioInstrumentor().instrument()
            logger.info("Automatic instrumentation initialized")
        except Exception as e:
            logger.warning(f"Some instrumentation failed: {e}")
    def _create_custom_metrics(self):
        """Create custom metrics for Sophia AI"""
        meter = metrics.get_meter(__name__)
        # Business metrics
        self.custom_metrics.update(
            {
                # Revenue and business metrics
                "sophia_rpe_optimization_score": meter.create_histogram(
                    "sophia_rpe_optimization_score",
                    description="Revenue per employee optimization score",
                    unit="score",
                ),
                "sophia_arpu_improvement": meter.create_histogram(
                    "sophia_arpu_improvement",
                    description="ARPU improvement percentage",
                    unit="percent",
                ),
                # AI and ML metrics
                "sophia_ai_agent_executions": meter.create_counter(
                    "sophia_ai_agent_executions_total",
                    description="Total AI agent executions",
                ),
                "sophia_ai_agent_latency": meter.create_histogram(
                    "sophia_ai_agent_latency_seconds",
                    description="AI agent execution latency",
                ),
                "sophia_rag_queries": meter.create_counter(
                    "sophia_rag_queries_total",
                    description="Total RAG queries processed",
                ),
                "sophia_multimodal_operations": meter.create_counter(
                    "sophia_multimodal_operations_total",
                    description="Total multimodal operations",
                ),
                # System metrics
                "sophia_mcp_server_calls": meter.create_counter(
                    "sophia_mcp_server_calls_total",
                    description="Total MCP server calls",
                ),
                "sophia_workflow_executions": meter.create_counter(
                    "sophia_workflow_executions_total",
                    description="Total workflow executions",
                ),
                "sophia_cache_operations": meter.create_counter(
                    "sophia_cache_operations_total",
                    description="Total cache operations",
                ),
                # Integration metrics
                "sophia_linear_sync_operations": meter.create_counter(
                    "sophia_linear_sync_operations_total",
                    description="Linear synchronization operations",
                ),
                "sophia_asana_sync_operations": meter.create_counter(
                    "sophia_asana_sync_operations_total",
                    description="Asana synchronization operations",
                ),
                "sophia_notion_sync_operations": meter.create_counter(
                    "sophia_notion_sync_operations_total",
                    description="Notion synchronization operations",
                ),
            }
        )
        logger.info(f"Created {len(self.custom_metrics)} custom metrics")
    def get_tracer(self, name: str) -> trace.Tracer:
        """Get tracer for a specific component"""
        return trace.get_tracer(name)
    def get_meter(self, name: str) -> metrics.Meter:
        """Get meter for a specific component"""
        return metrics.get_meter(name)
    def record_business_metric(
        self,
        metric_name: str,
        value: float,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """Record a business metric"""
        if metric_name in self.custom_metrics:
            metric = self.custom_metrics[metric_name]
            if hasattr(metric, "record"):
                metric.record(value, attributes or {})
            elif hasattr(metric, "add"):
                metric.add(value, attributes or {})
        else:
            logger.warning(f"Unknown metric: {metric_name}")
    @contextmanager
    def trace_operation(
        self, operation_name: str, attributes: Optional[Dict[str, Any]] = None
    ):
        """Context manager for tracing operations"""
        tracer = self.get_tracer(__name__)
        with tracer.start_as_current_span(operation_name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
    def shutdown(self):
        """Shutdown telemetry providers"""
        try:
            if self.tracer_provider:
                self.tracer_provider.shutdown()
            if self.meter_provider:
                self.meter_provider.shutdown()
            logger.info("Telemetry shutdown complete")
        except Exception as e:
            logger.error(f"Error during telemetry shutdown: {e}")
# Global telemetry instance
_telemetry_instance: Optional[SophiaAITelemetry] = None
def initialize_telemetry(
    config: Optional[SophiaAITelemetryConfig] = None,
) -> SophiaAITelemetry:
    """Initialize global telemetry instance"""
    global _telemetry_instance
    if _telemetry_instance is None:
        _telemetry_instance = SophiaAITelemetry(config)
        _telemetry_instance.initialize()
    return _telemetry_instance
def get_telemetry() -> Optional[SophiaAITelemetry]:
    """Get global telemetry instance"""
    return _telemetry_instance
def shutdown_telemetry():
    """Shutdown global telemetry instance"""
    global _telemetry_instance
    if _telemetry_instance:
        _telemetry_instance.shutdown()
        _telemetry_instance = None
# Convenience functions
def trace_sophia_operation(
    operation_name: str, attributes: Optional[Dict[str, Any]] = None
):
    """Decorator for tracing Sophia AI operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            telemetry = get_telemetry()
            if telemetry:
                with telemetry.trace_operation(operation_name, attributes):
                    return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator
def record_sophia_metric(
    metric_name: str, value: float, attributes: Optional[Dict[str, Any]] = None
):
    """Record a Sophia AI metric"""
    telemetry = get_telemetry()
    if telemetry:
        telemetry.record_business_metric(metric_name, value, attributes)
# Example usage
if __name__ == "__main__":
    # Initialize telemetry
    config = SophiaAITelemetryConfig()
    telemetry = initialize_telemetry(config)
    # Example tracing
    with telemetry.trace_operation("sophia_operation", {"test": "value"}):
        print("Performing traced operation")
    # Example metrics
    record_sophia_metric(
        "sophia_rpe_optimization_score", 85.5, {"department": "engineering"}
    )
    # Shutdown
    shutdown_telemetry()
