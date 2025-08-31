"""
Observability and Monitoring for Sophia Intel AI
Provides metrics, tracing, and logging capabilities.
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

try:
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
except ImportError:
    # Fallback - disable Jaeger if not available
    JaegerExporter = None

from fastapi import Request, Response
from fastapi.responses import PlainTextResponse
import time
import logging
import asyncio
from functools import wraps
from typing import Callable, Any, Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

# ============================================
# Prometheus Metrics
# ============================================

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Memory system metrics
memory_operations_total = Counter(
    'memory_operations_total',
    'Total memory operations',
    ['operation', 'status']
)

memory_operation_duration = Histogram(
    'memory_operation_duration_seconds',
    'Memory operation duration',
    ['operation']
)

memory_entries_total = Gauge(
    'memory_entries_total',
    'Total number of memory entries'
)

memory_cache_hits = Counter(
    'memory_cache_hits_total',
    'Memory cache hits'
)

memory_cache_misses = Counter(
    'memory_cache_misses_total',
    'Memory cache misses'
)

# Search metrics
search_requests_total = Counter(
    'search_requests_total',
    'Total search requests',
    ['mode', 'status']
)

search_latency = Histogram(
    'search_latency_seconds',
    'Search request latency',
    ['mode']
)

search_results_count = Histogram(
    'search_results_count',
    'Number of search results returned',
    ['mode']
)

# Embedding metrics
embedding_requests_total = Counter(
    'embedding_requests_total',
    'Total embedding requests',
    ['provider', 'status']
)

embedding_latency = Histogram(
    'embedding_latency_seconds',
    'Embedding generation latency',
    ['provider']
)

embedding_cache_size = Gauge(
    'embedding_cache_size',
    'Current embedding cache size'
)

# Swarm execution metrics
swarm_executions_total = Counter(
    'swarm_executions_total',
    'Total swarm executions',
    ['team_id', 'status']
)

swarm_execution_duration = Histogram(
    'swarm_execution_duration_seconds',
    'Swarm execution duration',
    ['team_id']
)

swarm_active_executions = Gauge(
    'swarm_active_executions',
    'Currently active swarm executions'
)

# Gate evaluation metrics
gate_evaluations_total = Counter(
    'gate_evaluations_total',
    'Total gate evaluations',
    ['gate_type', 'decision']
)

gate_evaluation_duration = Histogram(
    'gate_evaluation_duration_seconds',
    'Gate evaluation duration',
    ['gate_type']
)

# System health metrics
system_health = Gauge(
    'system_health',
    'Overall system health (0=unhealthy, 1=healthy)'
)

component_health = Gauge(
    'component_health',
    'Component health status',
    ['component']
)

# ============================================
# Tracing Setup
# ============================================

def setup_tracing(jaeger_endpoint: Optional[str] = None):
    """Initialize OpenTelemetry tracing with Jaeger."""
    if not jaeger_endpoint or JaegerExporter is None:
        logger.info("Tracing disabled (no Jaeger endpoint or exporter unavailable)")
        return None
    
    try:
        # Create Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=jaeger_endpoint.split(':')[0],
            agent_port=int(jaeger_endpoint.split(':')[1]) if ':' in jaeger_endpoint else 6831,
        )
        
        # Create tracer provider
        provider = TracerProvider()
        processor = BatchSpanProcessor(jaeger_exporter)
        provider.add_span_processor(processor)
        
        # Set global tracer provider
        trace.set_tracer_provider(provider)
        
        logger.info(f"Tracing enabled with Jaeger at {jaeger_endpoint}")
        return trace.get_tracer(__name__)
        
    except Exception as e:
        logger.error(f"Failed to setup tracing: {e}")
        return None

# ============================================
# Middleware
# ============================================

class MetricsMiddleware:
    """Middleware to collect request metrics."""
    
    async def __call__(self, request: Request, call_next):
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Start timer
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Record metrics
        duration = time.time() - start_time
        
        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        http_request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        # Add custom headers
        response.headers["X-Request-Duration"] = str(duration)
        
        return response

# ============================================
# Decorators
# ============================================

def track_memory_operation(operation: str):
    """Decorator to track memory operations."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                memory_operations_total.labels(operation=operation, status=status).inc()
                memory_operation_duration.labels(operation=operation).observe(duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                memory_operations_total.labels(operation=operation, status=status).inc()
                memory_operation_duration.labels(operation=operation).observe(duration)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

def track_search_operation(mode: str):
    """Decorator to track search operations."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            result_count = 0
            
            try:
                result = await func(*args, **kwargs)
                if isinstance(result, list):
                    result_count = len(result)
                elif isinstance(result, dict) and "results" in result:
                    result_count = len(result["results"])
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                search_requests_total.labels(mode=mode, status=status).inc()
                search_latency.labels(mode=mode).observe(duration)
                if result_count > 0:
                    search_results_count.labels(mode=mode).observe(result_count)
        
        return wrapper
    return decorator

def track_swarm_execution(team_id: str):
    """Decorator to track swarm executions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            swarm_active_executions.inc()
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                swarm_active_executions.dec()
                swarm_executions_total.labels(team_id=team_id, status=status).inc()
                swarm_execution_duration.labels(team_id=team_id).observe(duration)
        
        return wrapper
    return decorator

# ============================================
# Metrics Collection
# ============================================

class MetricsCollector:
    """Collects and exposes system metrics."""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
    
    async def collect_system_metrics(self, state: Any):
        """Collect metrics from system state."""
        try:
            # Memory metrics
            if state.supermemory:
                stats = await state.supermemory.get_stats()
                memory_entries_total.set(stats.get("total_entries", 0))
                embedding_cache_size.set(stats.get("embedding_cache_size", 0))
                
                # Cache hit rate
                cache_hits = stats.get("cache_hits", 0)
                cache_misses = stats.get("cache_misses", 0)
                if cache_hits > 0:
                    memory_cache_hits.inc(cache_hits)
                if cache_misses > 0:
                    memory_cache_misses.inc(cache_misses)
            
            # Component health
            components = {
                "supermemory": state.supermemory is not None,
                "embedder": state.embedder is not None,
                "search_engine": state.search_engine is not None,
                "graph_rag": state.graph_rag is not None,
                "gate_manager": state.gate_manager is not None,
                "orchestrator": state.orchestrator is not None
            }
            
            for component, healthy in components.items():
                component_health.labels(component=component).set(1 if healthy else 0)
            
            # Overall system health
            all_healthy = all(components.values())
            system_health.set(1 if all_healthy else 0)
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
    
    def get_metrics(self) -> str:
        """Generate Prometheus metrics output."""
        return generate_latest().decode('utf-8')

# ============================================
# Endpoints
# ============================================

async def metrics_endpoint(request: Request) -> Response:
    """Prometheus metrics endpoint."""
    # Collect current metrics
    from app.api.unified_server import state
    collector = MetricsCollector()
    await collector.collect_system_metrics(state)
    
    # Generate metrics
    metrics = collector.get_metrics()
    
    return PlainTextResponse(
        content=metrics,
        media_type=CONTENT_TYPE_LATEST
    )

# ============================================
# Instrumentation
# ============================================

def instrument_app(app):
    """Add instrumentation to FastAPI app."""
    
    # Add OpenTelemetry instrumentation
    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    
    # Add metrics middleware
    app.add_middleware(MetricsMiddleware)
    
    # Add metrics endpoint
    @app.get("/metrics", include_in_schema=False)
    async def get_metrics(request: Request):
        return await metrics_endpoint(request)
    
    logger.info("Observability instrumentation added")

# ============================================
# Health Checks
# ============================================

class HealthChecker:
    """Performs health checks on system components."""
    
    @staticmethod
    async def check_memory_system(state: Any) -> Dict[str, Any]:
        """Check memory system health."""
        try:
            if not state.supermemory:
                return {"healthy": False, "reason": "Not initialized"}
            
            # Try a simple operation
            stats = await state.supermemory.get_stats()
            
            return {
                "healthy": True,
                "entries": stats.get("total_entries", 0),
                "cache_size": stats.get("embedding_cache_size", 0)
            }
        except Exception as e:
            return {"healthy": False, "reason": str(e)}
    
    @staticmethod
    async def check_search_system(state: Any) -> Dict[str, Any]:
        """Check search system health."""
        try:
            if not state.search_engine:
                return {"healthy": False, "reason": "Not initialized"}
            
            # Try a test query
            results = await state.search_engine.hybrid_search(
                query="test",
                limit=1
            )
            
            return {"healthy": True, "responsive": True}
        except Exception as e:
            return {"healthy": False, "reason": str(e)}
    
    @staticmethod
    async def check_all_systems(state: Any) -> Dict[str, Any]:
        """Comprehensive health check."""
        checks = {
            "memory": await HealthChecker.check_memory_system(state),
            "search": await HealthChecker.check_search_system(state),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        all_healthy = all(
            check.get("healthy", False) 
            for check in checks.values() 
            if isinstance(check, dict)
        )
        
        return {
            "healthy": all_healthy,
            "checks": checks
        }

# Export key components
__all__ = [
    "setup_tracing",
    "MetricsMiddleware",
    "MetricsCollector",
    "track_memory_operation",
    "track_search_operation",
    "track_swarm_execution",
    "instrument_app",
    "HealthChecker"
]