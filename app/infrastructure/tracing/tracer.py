"""
Distributed Tracing with OpenTelemetry
Provides distributed tracing capabilities for the AI Orchestra system
"""

import os
from collections.abc import Callable
from contextlib import contextmanager
from functools import wraps
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.propagate import extract, inject
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

# Global tracer instance
_tracer: trace.Tracer | None = None

def initialize_tracing(
    service_name: str = "ai-orchestra",
    jaeger_endpoint: str = None,
    enable_console_export: bool = False
) -> trace.Tracer:
    """
    Initialize OpenTelemetry tracing
    
    Args:
        service_name: Name of the service
        jaeger_endpoint: Jaeger collector endpoint
        enable_console_export: Enable console span export for debugging
        
    Returns:
        Configured tracer instance
    """
    global _tracer

    # Create resource
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "1.0.0",
        "deployment.environment": os.getenv("ENVIRONMENT", "development")
    })

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Add exporters
    if enable_console_export:
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(
            BatchSpanProcessor(console_exporter)
        )

    if jaeger_endpoint:
        jaeger_exporter = JaegerExporter(
            agent_host_name=jaeger_endpoint.split(':')[0] if ':' in jaeger_endpoint else jaeger_endpoint,
            agent_port=int(jaeger_endpoint.split(':')[1]) if ':' in jaeger_endpoint else 6831,
            max_tag_value_length=256
        )
        provider.add_span_processor(
            BatchSpanProcessor(jaeger_exporter)
        )

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    # Get tracer
    _tracer = trace.get_tracer(__name__)

    # Auto-instrument libraries
    FastAPIInstrumentor.instrument(tracer_provider=provider)
    RedisInstrumentor.instrument(tracer_provider=provider)
    RequestsInstrumentor.instrument(tracer_provider=provider)

    return _tracer

def get_tracer() -> trace.Tracer:
    """Get the global tracer instance"""
    global _tracer
    if not _tracer:
        _tracer = initialize_tracing()
    return _tracer

@contextmanager
def create_span(
    name: str,
    attributes: dict[str, Any] | None = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL
):
    """
    Create a trace span context manager
    
    Args:
        name: Span name
        attributes: Span attributes
        kind: Span kind
        
    Yields:
        Active span
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(
        name,
        kind=kind,
        attributes=attributes or {}
    ) as span:
        try:
            yield span
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise

def trace_method(
    component: str,
    operation: str,
    span_kind: trace.SpanKind = trace.SpanKind.INTERNAL
):
    """
    Decorator to trace a method
    
    Args:
        component: Component name
        operation: Operation name
        span_kind: Type of span
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            span_name = f"{component}.{operation}"

            with create_span(
                name=span_name,
                attributes={
                    "component": component,
                    "operation": operation,
                    "function": func.__name__
                },
                kind=span_kind
            ) as span:
                # Add function arguments as attributes
                if args and hasattr(args[0], '__class__'):
                    span.set_attribute("class", args[0].__class__.__name__)

                # Add relevant kwargs
                for key, value in kwargs.items():
                    if key in ['session_id', 'request_id', 'user_id']:
                        span.set_attribute(key, str(value))

                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            span_name = f"{component}.{operation}"

            with create_span(
                name=span_name,
                attributes={
                    "component": component,
                    "operation": operation,
                    "function": func.__name__
                },
                kind=span_kind
            ) as span:
                # Add function arguments as attributes
                if args and hasattr(args[0], '__class__'):
                    span.set_attribute("class", args[0].__class__.__name__)

                # Add relevant kwargs
                for key, value in kwargs.items():
                    if key in ['session_id', 'request_id', 'user_id']:
                        span.set_attribute(key, str(value))

                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

class TracingMiddleware:
    """Middleware to add tracing to HTTP requests"""

    def __init__(self, app):
        self.app = app
        self.tracer = get_tracer()
        self.propagator = TraceContextTextMapPropagator()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Extract trace context from headers
            headers = dict(scope["headers"])
            carrier = {}
            for key, value in headers.items():
                carrier[key.decode()] = value.decode()

            ctx = extract(carrier)

            # Create span for request
            with self.tracer.start_as_current_span(
                f"{scope['method']} {scope['path']}",
                context=ctx,
                kind=trace.SpanKind.SERVER,
                attributes={
                    "http.method": scope["method"],
                    "http.url": scope["path"],
                    "http.scheme": scope["scheme"],
                    "http.host": dict(scope["headers"]).get(b"host", b"").decode(),
                    "http.user_agent": dict(scope["headers"]).get(b"user-agent", b"").decode()
                }
            ) as span:
                # Track response status
                async def send_wrapper(message):
                    if message["type"] == "http.response.start":
                        span.set_attribute("http.status_code", message["status"])
                        if message["status"] >= 400:
                            span.set_status(
                                Status(StatusCode.ERROR, f"HTTP {message['status']}")
                            )
                    await send(message)

                await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)

# WebSocket tracing support
class WebSocketTracer:
    """Tracer for WebSocket connections"""

    def __init__(self):
        self.tracer = get_tracer()
        self.active_spans = {}

    def start_connection_span(
        self,
        connection_key: str,
        client_id: str,
        session_id: str
    ) -> trace.Span:
        """Start a span for WebSocket connection"""
        span = self.tracer.start_span(
            "websocket.connection",
            kind=trace.SpanKind.SERVER,
            attributes={
                "connection_key": connection_key,
                "client_id": client_id,
                "session_id": session_id,
                "transport": "websocket"
            }
        )
        self.active_spans[connection_key] = span
        return span

    def add_message_event(
        self,
        connection_key: str,
        message_type: str,
        direction: str = "inbound"
    ):
        """Add message event to connection span"""
        if connection_key in self.active_spans:
            span = self.active_spans[connection_key]
            span.add_event(
                f"websocket.message.{direction}",
                attributes={
                    "message_type": message_type,
                    "direction": direction
                }
            )

    def end_connection_span(
        self,
        connection_key: str,
        status: Status | None = None
    ):
        """End connection span"""
        if connection_key in self.active_spans:
            span = self.active_spans[connection_key]
            if status:
                span.set_status(status)
            else:
                span.set_status(Status(StatusCode.OK))
            span.end()
            del self.active_spans[connection_key]

# Batch operation tracing
@contextmanager
def trace_batch_operation(
    operation_name: str,
    batch_size: int,
    component: str = "batch_processor"
):
    """
    Trace a batch operation
    
    Args:
        operation_name: Name of the batch operation
        batch_size: Size of the batch
        component: Component performing the operation
    """
    with create_span(
        name=f"{component}.{operation_name}",
        attributes={
            "batch.size": batch_size,
            "component": component,
            "operation": operation_name
        },
        kind=trace.SpanKind.INTERNAL
    ) as span:
        processed = 0
        failed = 0

        def record_item_processed():
            nonlocal processed
            processed += 1
            span.set_attribute("batch.processed", processed)

        def record_item_failed():
            nonlocal failed
            failed += 1
            span.set_attribute("batch.failed", failed)

        span.record_item_processed = record_item_processed
        span.record_item_failed = record_item_failed

        try:
            yield span
            span.set_attribute("batch.success_rate",
                             (processed - failed) / batch_size if batch_size > 0 else 0)
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise

# Context propagation helpers
def inject_trace_context(carrier: dict[str, str]) -> dict[str, str]:
    """Inject trace context into carrier for propagation"""
    inject(carrier)
    return carrier

def extract_trace_context(carrier: dict[str, str]):
    """Extract trace context from carrier"""
    return extract(carrier)

# Export
__all__ = [
    'initialize_tracing',
    'get_tracer',
    'create_span',
    'trace_method',
    'TracingMiddleware',
    'WebSocketTracer',
    'trace_batch_operation',
    'inject_trace_context',
    'extract_trace_context'
]
