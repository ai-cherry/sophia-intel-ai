from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def init_tracing(service_name: str = "sophia-intel-ai"):
    """Initialize OpenTelemetry tracing with Jaeger and Tempo exporters"""
    # Configure resource attributes
    resource = Resource.create({
        SERVICE_NAME: service_name,
        "deployment.environment": "production"
    })

    # Create tracer provider
    trace.set_tracer_provider(TracerProvider(resource=resource))

    # Configure OTLP exporters for Jaeger and Tempo
    jaeger_exporter = OTLPSpanExporter(
        endpoint="http://jaeger:14250/v1/trace",
        insecure=True
    )

    tempo_exporter = OTLPSpanExporter(
        endpoint="http://tempo:3200/otlp/v1/traces",
        insecure=True
    )

    # Add span processors
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(tempo_exporter)
    )

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=trace.get_tracer_provider(),
        excluded_urls="health,metrics"
    )

    # Instrument HTTP clients
    HTTPInstrumentor().instrument()
    RequestsInstrumentor().instrument()

    return trace.get_tracer_provider()
