"""
Enhanced Observability Metrics

This module expands OpenTelemetry and metrics coverage for reasoning loops,
tool execution, and agent performance monitoring.
"""

import logging
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Optional

from opentelemetry import trace
from opentelemetry.exporter.jaeger import JaegerExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.metrics import get_meter_provider, set_meter_provider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode, get_tracer_provider, set_tracer_provider
from prometheus_client import Counter, Gauge, Histogram, Summary

logger = logging.getLogger(__name__)

# Resource definition
resource = Resource.create({
    "service.name": "sophia-ai-agents",
    "service.version": "2.0.0",
    "deployment.environment": "production"
})

# Tracer setup
tracer_provider = TracerProvider(resource=resource)
set_tracer_provider(tracer_provider)

# Meter setup
meter_provider = MeterProvider(resource=resource)
set_meter_provider(meter_provider)

# Get tracer and meter
tracer = trace.get_tracer("sophia.agents", "1.0.0")
meter = get_meter_provider().get_meter("sophia.metrics", "1.0.0")

# Prometheus Metrics
# Agent Metrics
agent_requests_total = Counter(
    'agent_requests_total',
    'Total number of agent requests',
    ['agent_id', 'role', 'status']
)

agent_request_duration = Histogram(
    'agent_request_duration_seconds',
    'Agent request duration in seconds',
    ['agent_id', 'role'],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60]
)

agent_active_sessions = Gauge(
    'agent_active_sessions',
    'Number of active agent sessions',
    ['agent_id', 'role']
)

# Reasoning Metrics
reasoning_steps_total = Counter(
    'reasoning_steps_total',
    'Total number of reasoning steps',
    ['agent_id', 'strategy', 'step_type']
)

reasoning_duration = Histogram(
    'reasoning_duration_seconds',
    'Reasoning process duration',
    ['agent_id', 'strategy'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10]
)

reasoning_confidence = Summary(
    'reasoning_confidence',
    'Reasoning step confidence scores',
    ['agent_id', 'step_type']
)

reasoning_loops_detected = Counter(
    'reasoning_loops_detected_total',
    'Number of infinite loops detected in reasoning',
    ['agent_id']
)

# Tool Execution Metrics
tool_executions_total = Counter(
    'tool_executions_total',
    'Total number of tool executions',
    ['tool_name', 'category', 'status']
)

tool_execution_duration = Histogram(
    'tool_execution_duration_seconds',
    'Tool execution duration',
    ['tool_name', 'category'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10, 30]
)

tool_failures = Counter(
    'tool_failures_total',
    'Total number of tool execution failures',
    ['tool_name', 'error_type']
)

tool_retries = Counter(
    'tool_retries_total',
    'Total number of tool execution retries',
    ['tool_name']
)

# Model Metrics
model_requests_total = Counter(
    'model_requests_total',
    'Total model API requests',
    ['model', 'provider', 'status']
)

model_tokens_used = Counter(
    'model_tokens_used_total',
    'Total tokens consumed',
    ['model', 'provider', 'token_type']
)

model_cost_usd = Counter(
    'model_cost_usd_total',
    'Total cost in USD',
    ['model', 'provider']
)

model_latency = Histogram(
    'model_latency_seconds',
    'Model API latency',
    ['model', 'provider'],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30]
)

# Memory and Cache Metrics
memory_operations = Counter(
    'memory_operations_total',
    'Memory store operations',
    ['operation', 'status']
)

cache_hits = Counter(
    'cache_hits_total',
    'Cache hit count',
    ['cache_type']
)

cache_misses = Counter(
    'cache_misses_total',
    'Cache miss count',
    ['cache_type']
)

memory_size_bytes = Gauge(
    'memory_size_bytes',
    'Memory store size in bytes',
    ['store_type']
)

# Guardrail Metrics
guardrail_violations = Counter(
    'guardrail_violations_total',
    'Guardrail violations',
    ['violation_type', 'severity']
)

guardrail_checks = Counter(
    'guardrail_checks_total',
    'Guardrail checks performed',
    ['check_type', 'result']
)

# Error Metrics
errors_total = Counter(
    'errors_total',
    'Total errors',
    ['category', 'severity']
)

error_recovery_attempts = Counter(
    'error_recovery_attempts_total',
    'Error recovery attempts',
    ['error_type', 'strategy', 'success']
)


class ObservabilityManager:
    """Central observability management"""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.initialized = False
    
    def initialize(self):
        """Initialize observability components"""
        if self.initialized:
            return
        
        # Setup Jaeger exporter if configured
        if self.config.get('enable_jaeger', False):
            jaeger_exporter = JaegerExporter(
                agent_host_name=self.config.get('jaeger_host', 'localhost'),
                agent_port=self.config.get('jaeger_port', 6831),
            )
            span_processor = BatchSpanProcessor(jaeger_exporter)
            tracer_provider.add_span_processor(span_processor)
        
        # Setup Prometheus metrics endpoint
        if self.config.get('enable_prometheus', True):
            # Prometheus endpoint will be exposed by FastAPI
            pass
        
        self.initialized = True
        logger.info("Observability initialized")
    
    @contextmanager
    def trace_operation(
        self,
        name: str,
        attributes: Optional[dict] = None,
        record_exception: bool = True
    ):
        """Context manager for tracing operations"""
        with tracer.start_as_current_span(name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            
            try:
                yield span
            except Exception as e:
                if record_exception:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
            else:
                span.set_status(Status(StatusCode.OK))
    
    def record_agent_request(
        self,
        agent_id: str,
        role: str,
        duration: float,
        success: bool
    ):
        """Record agent request metrics"""
        status = "success" if success else "failure"
        agent_requests_total.labels(
            agent_id=agent_id,
            role=role,
            status=status
        ).inc()
        
        agent_request_duration.labels(
            agent_id=agent_id,
            role=role
        ).observe(duration)
    
    def record_reasoning_step(
        self,
        agent_id: str,
        strategy: str,
        step_type: str,
        duration: float,
        confidence: float
    ):
        """Record reasoning step metrics"""
        reasoning_steps_total.labels(
            agent_id=agent_id,
            strategy=strategy,
            step_type=step_type
        ).inc()
        
        reasoning_duration.labels(
            agent_id=agent_id,
            strategy=strategy
        ).observe(duration)
        
        reasoning_confidence.labels(
            agent_id=agent_id,
            step_type=step_type
        ).observe(confidence)
    
    def record_tool_execution(
        self,
        tool_name: str,
        category: str,
        duration: float,
        success: bool,
        retries: int = 0
    ):
        """Record tool execution metrics"""
        status = "success" if success else "failure"
        tool_executions_total.labels(
            tool_name=tool_name,
            category=category,
            status=status
        ).inc()
        
        tool_execution_duration.labels(
            tool_name=tool_name,
            category=category
        ).observe(duration)
        
        if retries > 0:
            tool_retries.labels(tool_name=tool_name).inc(retries)
        
        if not success:
            tool_failures.labels(
                tool_name=tool_name,
                error_type="execution_error"
            ).inc()
    
    def record_model_usage(
        self,
        model: str,
        provider: str,
        tokens: dict,
        cost: float,
        latency: float,
        success: bool
    ):
        """Record model usage metrics"""
        status = "success" if success else "failure"
        model_requests_total.labels(
            model=model,
            provider=provider,
            status=status
        ).inc()
        
        # Record token usage
        for token_type, count in tokens.items():
            model_tokens_used.labels(
                model=model,
                provider=provider,
                token_type=token_type
            ).inc(count)
        
        # Record cost
        model_cost_usd.labels(
            model=model,
            provider=provider
        ).inc(cost)
        
        # Record latency
        model_latency.labels(
            model=model,
            provider=provider
        ).observe(latency)
    
    def record_memory_operation(
        self,
        operation: str,
        success: bool,
        size_bytes: Optional[int] = None
    ):
        """Record memory operation metrics"""
        status = "success" if success else "failure"
        memory_operations.labels(
            operation=operation,
            status=status
        ).inc()
        
        if size_bytes is not None:
            memory_size_bytes.labels(store_type="main").set(size_bytes)
    
    def record_cache_access(self, cache_type: str, hit: bool):
        """Record cache access metrics"""
        if hit:
            cache_hits.labels(cache_type=cache_type).inc()
        else:
            cache_misses.labels(cache_type=cache_type).inc()
    
    def record_guardrail_check(
        self,
        check_type: str,
        passed: bool,
        violation_type: Optional[str] = None,
        severity: Optional[str] = None
    ):
        """Record guardrail check metrics"""
        result = "passed" if passed else "failed"
        guardrail_checks.labels(
            check_type=check_type,
            result=result
        ).inc()
        
        if not passed and violation_type:
            guardrail_violations.labels(
                violation_type=violation_type,
                severity=severity or "medium"
            ).inc()
    
    def record_error(
        self,
        category: str,
        severity: str,
        recovery_attempted: bool = False,
        recovery_success: bool = False
    ):
        """Record error metrics"""
        errors_total.labels(
            category=category,
            severity=severity
        ).inc()
        
        if recovery_attempted:
            error_recovery_attempts.labels(
                error_type=category,
                strategy="automatic",
                success=str(recovery_success).lower()
            ).inc()


# Decorators for automatic instrumentation

def trace_agent_operation(operation_name: str):
    """Decorator for tracing agent operations"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            # Extract agent info from self if available
            agent_info = {}
            if args and hasattr(args[0], 'agent_id'):
                agent_info['agent_id'] = args[0].agent_id
            if args and hasattr(args[0], 'role'):
                agent_info['agent.role'] = args[0].role
            
            with tracer.start_as_current_span(
                f"agent.{operation_name}",
                attributes=agent_info
            ) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
        
        def sync_wrapper(*args, **kwargs):
            # Extract agent info from self if available
            agent_info = {}
            if args and hasattr(args[0], 'agent_id'):
                agent_info['agent.id'] = args[0].agent_id
            if args and hasattr(args[0], 'role'):
                agent_info['agent.role'] = args[0].role
            
            with tracer.start_as_current_span(
                f"agent.{operation_name}",
                attributes=agent_info
            ) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def measure_reasoning(strategy: str):
    """Decorator for measuring reasoning performance"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Extract agent ID if available
            agent_id = "unknown"
            if args and hasattr(args[0], 'agent_id'):
                agent_id = args[0].agent_id
            
            with tracer.start_as_current_span(
                "reasoning.step",
                attributes={
                    "reasoning.strategy": strategy,
                    "agent.id": agent_id
                }
            ) as span:
                try:
                    result = await func(*args, **kwargs)
                    
                    # Record metrics
                    duration = time.time() - start_time
                    if hasattr(result, 'step_type') and hasattr(result, 'confidence'):
                        global_observability.record_reasoning_step(
                            agent_id=agent_id,
                            strategy=strategy,
                            step_type=result.step_type,
                            duration=duration,
                            confidence=result.confidence
                        )
                    
                    span.set_status(Status(StatusCode.OK))
                    return result
                    
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
        
        return wrapper
    return decorator


def measure_tool_execution(category: str):
    """Decorator for measuring tool execution"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Extract tool name if available
            tool_name = func.__name__
            if args and hasattr(args[0], 'name'):
                tool_name = args[0].name
            
            with tracer.start_as_current_span(
                f"tool.{tool_name}",
                attributes={
                    "tool.name": tool_name,
                    "tool.category": category
                }
            ) as span:
                retries = 0
                last_error = None
                
                for attempt in range(3):  # Max 3 attempts
                    try:
                        result = await func(*args, **kwargs)
                        
                        # Record success metrics
                        duration = time.time() - start_time
                        global_observability.record_tool_execution(
                            tool_name=tool_name,
                            category=category,
                            duration=duration,
                            success=True,
                            retries=retries
                        )
                        
                        span.set_status(Status(StatusCode.OK))
                        return result
                        
                    except Exception as e:
                        retries += 1
                        last_error = e
                        if attempt < 2:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                
                # All retries failed
                duration = time.time() - start_time
                global_observability.record_tool_execution(
                    tool_name=tool_name,
                    category=category,
                    duration=duration,
                    success=False,
                    retries=retries
                )
                
                span.record_exception(last_error)
                span.set_status(Status(StatusCode.ERROR, str(last_error)))
                raise last_error
        
        return wrapper
    return decorator


# Global observability instance
global_observability = ObservabilityManager()


# FastAPI instrumentation helper
def instrument_fastapi(app):
    """Instrument FastAPI application"""
    FastAPIInstrumentor.instrument_app(app)
    logger.info("FastAPI instrumentation enabled")