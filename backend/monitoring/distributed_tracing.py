"""
Distributed Tracing System for SOPHIA Intel
Enterprise-grade observability with Sentry integration
"""

import asyncio
import json
import time
import uuid
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from contextvars import ContextVar
import logging
from functools import wraps
import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
import opentelemetry
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

logger = logging.getLogger(__name__)

# Context variables for distributed tracing
trace_id_var: ContextVar[str] = ContextVar('trace_id', default='')
span_id_var: ContextVar[str] = ContextVar('span_id', default='')
user_id_var: ContextVar[str] = ContextVar('user_id', default='')

class TraceLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class SpanType(Enum):
    HTTP_REQUEST = "http.request"
    DATABASE_QUERY = "db.query"
    CACHE_OPERATION = "cache.operation"
    AI_INFERENCE = "ai.inference"
    EXTERNAL_API = "external.api"
    BACKGROUND_TASK = "background.task"
    USER_ACTION = "user.action"

@dataclass
class TraceContext:
    """Distributed trace context"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    operation: Optional[str] = None
    service: str = "sophia-intel"
    environment: str = "production"

@dataclass
class SpanData:
    """Span data for distributed tracing"""
    span_id: str
    trace_id: str
    operation_name: str
    span_type: SpanType
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    status: str = "ok"
    tags: Dict[str, Any] = None
    logs: List[Dict[str, Any]] = None
    error: Optional[str] = None

class DistributedTracingSystem:
    """Enterprise-grade distributed tracing system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.active_spans: Dict[str, SpanData] = {}
        self.tracer = None
        
        # Initialize Sentry
        self._initialize_sentry()
        
        # Initialize OpenTelemetry
        self._initialize_opentelemetry()
        
        logger.info("Distributed Tracing System initialized")
    
    def _initialize_sentry(self) -> None:
        """Initialize Sentry for error tracking and performance monitoring"""
        sentry_dsn = self.config.get("sentry", {}).get("dsn")
        if not sentry_dsn:
            logger.warning("Sentry DSN not configured, skipping Sentry initialization")
            return
        
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[
                AsyncioIntegration(auto_enable_aiohttp_integration=True),
                SqlalchemyIntegration(),
                RedisIntegration(),
                FastApiIntegration(auto_enable=True)
            ],
            traces_sample_rate=self.config.get("sentry", {}).get("traces_sample_rate", 0.1),
            profiles_sample_rate=self.config.get("sentry", {}).get("profiles_sample_rate", 0.1),
            environment=self.config.get("environment", "production"),
            release=self.config.get("version", "1.0.0"),
            attach_stacktrace=True,
            send_default_pii=False,
            max_breadcrumbs=100,
            before_send=self._sentry_before_send,
            before_send_transaction=self._sentry_before_send_transaction
        )
        
        logger.info("Sentry initialized for error tracking and performance monitoring")
    
    def _initialize_opentelemetry(self) -> None:
        """Initialize OpenTelemetry for distributed tracing"""
        # Set up tracer provider
        trace.set_tracer_provider(TracerProvider())
        
        # Configure Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=self.config.get("jaeger", {}).get("host", "localhost"),
            agent_port=self.config.get("jaeger", {}).get("port", 6831),
        )
        
        # Add span processor
        span_processor = BatchSpanProcessor(jaeger_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        
        # Get tracer
        self.tracer = trace.get_tracer(__name__)
        
        # Auto-instrument frameworks
        FastAPIInstrumentor.instrument()
        RequestsInstrumentor.instrument()
        SQLAlchemyInstrumentor.instrument()
        
        logger.info("OpenTelemetry initialized for distributed tracing")
    
    def _sentry_before_send(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Filter and enhance Sentry events before sending"""
        # Add trace context
        trace_id = trace_id_var.get('')
        if trace_id:
            event.setdefault('tags', {})['trace_id'] = trace_id
        
        # Filter out sensitive information
        if 'request' in event:
            headers = event['request'].get('headers', {})
            # Remove sensitive headers
            sensitive_headers = ['authorization', 'cookie', 'x-api-key']
            for header in sensitive_headers:
                headers.pop(header, None)
        
        return event
    
    def _sentry_before_send_transaction(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Filter and enhance Sentry transactions before sending"""
        # Add custom tags
        event.setdefault('tags', {}).update({
            'service': 'sophia-intel',
            'component': 'backend'
        })
        
        return event
    
    def create_trace_context(self, operation: str, user_id: Optional[str] = None, 
                           session_id: Optional[str] = None) -> TraceContext:
        """Create new trace context"""
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        
        context = TraceContext(
            trace_id=trace_id,
            span_id=span_id,
            user_id=user_id,
            session_id=session_id,
            operation=operation
        )
        
        # Set context variables
        trace_id_var.set(trace_id)
        span_id_var.set(span_id)
        if user_id:
            user_id_var.set(user_id)
        
        return context
    
    def start_span(self, operation_name: str, span_type: SpanType, 
                   parent_span_id: Optional[str] = None, **tags) -> str:
        """Start a new span"""
        span_id = str(uuid.uuid4())
        trace_id = trace_id_var.get() or str(uuid.uuid4())
        
        span_data = SpanData(
            span_id=span_id,
            trace_id=trace_id,
            operation_name=operation_name,
            span_type=span_type,
            start_time=time.time(),
            tags=tags or {}
        )
        
        self.active_spans[span_id] = span_data
        
        # Start Sentry transaction if it's a root span
        if not parent_span_id:
            sentry_sdk.start_transaction(
                name=operation_name,
                op=span_type.value
            )
        
        # Start OpenTelemetry span
        if self.tracer:
            with self.tracer.start_as_current_span(operation_name) as span:
                span.set_attribute("span.type", span_type.value)
                span.set_attribute("trace.id", trace_id)
                for key, value in tags.items():
                    span.set_attribute(key, str(value))
        
        logger.debug(f"Started span: {operation_name} ({span_id})")
        return span_id
    
    def finish_span(self, span_id: str, status: str = "ok", error: Optional[str] = None) -> None:
        """Finish a span"""
        if span_id not in self.active_spans:
            logger.warning(f"Span not found: {span_id}")
            return
        
        span_data = self.active_spans[span_id]
        span_data.end_time = time.time()
        span_data.duration = span_data.end_time - span_data.start_time
        span_data.status = status
        span_data.error = error
        
        # Log span completion
        logger.debug(f"Finished span: {span_data.operation_name} ({span_id}) - {span_data.duration:.3f}s")
        
        # Send to Sentry if error
        if error:
            sentry_sdk.capture_exception(Exception(error))
        
        # Remove from active spans
        del self.active_spans[span_id]
    
    def add_span_tag(self, span_id: str, key: str, value: Any) -> None:
        """Add tag to span"""
        if span_id in self.active_spans:
            if not self.active_spans[span_id].tags:
                self.active_spans[span_id].tags = {}
            self.active_spans[span_id].tags[key] = value
    
    def add_span_log(self, span_id: str, level: TraceLevel, message: str, **fields) -> None:
        """Add log entry to span"""
        if span_id in self.active_spans:
            if not self.active_spans[span_id].logs:
                self.active_spans[span_id].logs = []
            
            log_entry = {
                "timestamp": time.time(),
                "level": level.value,
                "message": message,
                **fields
            }
            
            self.active_spans[span_id].logs.append(log_entry)
    
    def trace_function(self, operation_name: str, span_type: SpanType = SpanType.USER_ACTION):
        """Decorator to trace function execution"""
        def decorator(func: Callable) -> Callable:
            if asyncio.iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    span_id = self.start_span(operation_name, span_type)
                    try:
                        result = await func(*args, **kwargs)
                        self.finish_span(span_id, "ok")
                        return result
                    except Exception as e:
                        self.finish_span(span_id, "error", str(e))
                        raise
                return async_wrapper
            else:
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    span_id = self.start_span(operation_name, span_type)
                    try:
                        result = func(*args, **kwargs)
                        self.finish_span(span_id, "ok")
                        return result
                    except Exception as e:
                        self.finish_span(span_id, "error", str(e))
                        raise
                return sync_wrapper
        return decorator
    
    def trace_ai_inference(self, model_name: str, provider: str):
        """Decorator specifically for AI inference tracing"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                span_id = self.start_span(
                    f"ai_inference_{model_name}",
                    SpanType.AI_INFERENCE,
                    model=model_name,
                    provider=provider
                )
                
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    
                    # Add inference metrics
                    self.add_span_tag(span_id, "inference.duration", time.time() - start_time)
                    self.add_span_tag(span_id, "inference.success", True)
                    
                    if hasattr(result, 'usage'):
                        self.add_span_tag(span_id, "inference.tokens.input", result.usage.prompt_tokens)
                        self.add_span_tag(span_id, "inference.tokens.output", result.usage.completion_tokens)
                        self.add_span_tag(span_id, "inference.tokens.total", result.usage.total_tokens)
                    
                    self.finish_span(span_id, "ok")
                    return result
                    
                except Exception as e:
                    self.add_span_tag(span_id, "inference.success", False)
                    self.add_span_tag(span_id, "inference.error", str(e))
                    self.finish_span(span_id, "error", str(e))
                    raise
            return wrapper
        return decorator
    
    def trace_database_operation(self, operation: str, table: str):
        """Decorator for database operation tracing"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                span_id = self.start_span(
                    f"db_{operation}_{table}",
                    SpanType.DATABASE_QUERY,
                    db_operation=operation,
                    db_table=table
                )
                
                try:
                    result = await func(*args, **kwargs)
                    
                    # Add database metrics
                    if hasattr(result, 'rowcount'):
                        self.add_span_tag(span_id, "db.rows_affected", result.rowcount)
                    
                    self.finish_span(span_id, "ok")
                    return result
                    
                except Exception as e:
                    self.add_span_tag(span_id, "db.error", str(e))
                    self.finish_span(span_id, "error", str(e))
                    raise
            return wrapper
        return decorator
    
    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """Get summary of trace"""
        spans = [span for span in self.active_spans.values() if span.trace_id == trace_id]
        
        if not spans:
            return {"error": "Trace not found"}
        
        total_duration = sum(span.duration or 0 for span in spans if span.duration)
        error_count = sum(1 for span in spans if span.status == "error")
        
        return {
            "trace_id": trace_id,
            "total_spans": len(spans),
            "total_duration": total_duration,
            "error_count": error_count,
            "status": "error" if error_count > 0 else "ok",
            "spans": [
                {
                    "span_id": span.span_id,
                    "operation": span.operation_name,
                    "type": span.span_type.value,
                    "duration": span.duration,
                    "status": span.status
                }
                for span in spans
            ]
        }
    
    async def get_performance_metrics(self, time_range: int = 3600) -> Dict[str, Any]:
        """Get performance metrics for the last time range (seconds)"""
        # This would query stored span data in a real implementation
        return {
            "time_range": time_range,
            "total_requests": 1250,
            "average_response_time": 0.245,
            "p95_response_time": 0.890,
            "p99_response_time": 1.234,
            "error_rate": 0.02,
            "throughput": 20.8,  # requests per second
            "top_operations": [
                {"operation": "chat_completion", "count": 450, "avg_duration": 0.567},
                {"operation": "web_research", "count": 230, "avg_duration": 1.234},
                {"operation": "code_generation", "count": 180, "avg_duration": 0.890}
            ],
            "error_breakdown": {
                "timeout_errors": 12,
                "api_errors": 8,
                "validation_errors": 5
            }
        }

# Global tracing system
_tracing_system: Optional[DistributedTracingSystem] = None

def get_tracing_system() -> DistributedTracingSystem:
    """Get global tracing system"""
    if _tracing_system is None:
        raise RuntimeError("Tracing system not initialized")
    return _tracing_system

def initialize_tracing_system(config: Dict[str, Any]) -> DistributedTracingSystem:
    """Initialize global tracing system"""
    global _tracing_system
    _tracing_system = DistributedTracingSystem(config)
    return _tracing_system

# Convenience decorators
def trace(operation_name: str, span_type: SpanType = SpanType.USER_ACTION):
    """Convenience decorator for tracing"""
    return get_tracing_system().trace_function(operation_name, span_type)

def trace_ai(model_name: str, provider: str):
    """Convenience decorator for AI inference tracing"""
    return get_tracing_system().trace_ai_inference(model_name, provider)

def trace_db(operation: str, table: str):
    """Convenience decorator for database tracing"""
    return get_tracing_system().trace_database_operation(operation, table)

