"""
OpenTelemetry Configuration for Sophia Intel AI.
Sets up AI-specific tracing, metrics, and logging for observability.
"""

import logging
import socket
from typing import Any, Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.semconv.ai import SpanAttributes as AiSpanAttributes
from opentelemetry.semconv.resource import ResourceAttributes

from app.core.circuit_breaker import with_circuit_breaker
from app.core.connections import http_get

logger = logging.getLogger(__name__)

# Get service name and version from environment variables or a central config
SERVICE_NAME_VALUE = "sophia-intel-ai-api"
SERVICE_VERSION_VALUE = "3.0.0"


def configure_opentelemetry(
    app: Any,
    enable_console_exporter: bool = False,
    otel_endpoint: str = "grpc://localhost:4317",
) -> None:
    """
    Configures OpenTelemetry for the FastAPI application.

    Args:
        app: The FastAPI application instance.
        enable_console_exporter: If True, also export traces and metrics to console.
        otel_endpoint: The OTLP endpoint to send telemetry data (e.g., "http://localhost:4318").
    """
    logger.info(
        f"Configuring OpenTelemetry for service: {SERVICE_NAME_VALUE} (version: {SERVICE_VERSION_VALUE})"
    )

    # 1. Resource configuration
    from app.core.config import settings
    deployment_env = settings.environment
    hostname = socket.gethostname()
    resource = Resource.create(
        {
            SERVICE_NAME: SERVICE_NAME_VALUE,
            ResourceAttributes.SERVICE_VERSION: SERVICE_VERSION_VALUE,
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: deployment_env,
            ResourceAttributes.HOST_NAME: hostname,
            "ai.orchestrator.version": SERVICE_VERSION_VALUE,
            "ai.framework": "agno",  # Example AI framework attribution
        }
    )

    # 2. Trace Provider configuration
    trace_provider = TracerProvider(resource=resource)

    # OTLP gRPC Exporter for traces
    otlp_trace_exporter = OTLPSpanExporter(endpoint=otel_endpoint)
    trace_provider.add_span_processor(SimpleSpanProcessor(otlp_trace_exporter))

    if enable_console_exporter:
        # Console Exporter for traces (for local development/debugging)
        trace_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        logger.info("OpenTelemetry console trace exporter enabled.")

    trace.set_tracer_provider(trace_provider)

    # 3. Metrics Provider configuration
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=otel_endpoint)
    )
    if enable_console_exporter:
        metric_reader.add_metrics_exporter(ConsoleMetricExporter())
        logger.info("OpenTelemetry console metric exporter enabled.")

    MeterProvider(resource=resource, metric_readers=[metric_reader])

    # Add global meter provider
    # metrics.set_meter_provider(meter_provider)

    # 4. Instrumentation
    # Instrument FastAPI applications
    FastAPIInstrumentor.instrument_app(app)
    logger.info("FastAPI instrumentation enabled.")

    # Instrument HTTPX client (used by many LLM SDKs and internal calls)
    HTTPXClientInstrumentor().instrument()
    logger.info("HTTPX client instrumentation enabled.")

    # Instrument Redis client
    RedisInstrumentor().instrument()
    logger.info("Redis client instrumentation enabled.")

    # Instrument standard Python logging
    LoggingInstrumentor().instrument(set_logging_format=True)
    logger.info("Logging instrumentation enabled.")

    logger.info("OpenTelemetry configuration complete.")


def get_tracer():
    """Returns the OpenTelemetry tracer instance."""
    return trace.get_tracer(SERVICE_NAME_VALUE, SERVICE_VERSION_VALUE)


def trace_llm_call(
    provider: str,
    model: str,
    prompt: str,
    response: str,
    input_tokens: int,
    output_tokens: int,
    temperature: Optional[float] = None,
    latency_ms: Optional[int] = None,
    tool_calls: Optional[list[dict[str, Any]]] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> None:
    """
    Creates a custom span for an LLM API call with AI-specific attributes.
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(f"llm.call.{provider}.{model}") as span:
        span.set_attribute(AiSpanAttributes.LLM_VENDOR, provider)
        span.set_attribute(AiSpanAttributes.LLM_MODEL, model)
        span.set_attribute(AiSpanAttributes.LLM_PROMPT_LENGTH, input_tokens)
        span.set_attribute(AiSpanAttributes.LLM_COMPLETION_LENGTH, output_tokens)

        # Optional attributes
        if temperature is not None:
            span.set_attribute(AiSpanAttributes.LLM_TEMPERATURE, temperature)
        if latency_ms is not None:
            span.set_attribute(
                AiSpanAttributes.LLM_FINISH_REASON, "success"
            )  # Determine finish reason
            span.set_attribute("latency.ms", latency_ms)
        if user_id:
            span.set_attribute("enduser.id", user_id)
        if session_id:
            span.set_attribute("session.id", session_id)
        if tool_calls:
            span.set_attribute("llm.tool_calls.count", len(tool_calls))
            for i, tool_call in enumerate(tool_calls):
                span.set_attribute(f"llm.tool_calls.{i}.name", tool_call.get("name"))
                span.set_attribute(
                    f"llm.tool_calls.{i}.arguments",
                    json.dumps(tool_call.get("arguments")),
                )

        # Log input/output, but be cautious with sensitive data
        span.set_attribute(AiSpanAttributes.LLM_PROMPT, prompt)
        span.set_attribute(
            AiSpanAttributes.LLM_COMPLETION, response
        )  # Use LLM_RESPONSE if appropriate in future
        logger.debug(f"Traced LLM call: {provider}/{model}")


if __name__ == "__main__":
    # Example usage for local testing
    import uvicorn
    from fastapi import FastAPI

    app = FastAPI(title="OTel Test App")
    configure_opentelemetry(app, enable_console_exporter=True)

    @app.get("/test_endpoint")
    @with_circuit_breaker("external_api")
    async def test_endpoint():
        # Example of tracing an internal HTTP call
        with get_tracer().start_as_current_span("custom_internal_work"):
            await http_get("https://www.example.com")  # This HTTPX call will be traced

            # Simulate an LLM call with custom tracing
            trace_llm_call(
                provider="openai",
                model="gpt-4o-mini",
                prompt="Tell me a joke",
                response="Why did the scarecrow win an award? Because he was outstanding in his field!",
                input_tokens=50,
                output_tokens=200,
                latency_ms=150,
                user_id="testuser",
            )
        return {"message": "Telemetry sent!"}

    logger.info("Run this script and access http://localhost:8000/test_endpoint")
    logger.warn(
        "Remember to have an OTLP collector running (e.g., Jaeger) or use `enable_console_exporter=True`"
    )
    uvicorn.run(app, host="0.0.0.0", port=8000)
