"""
Prometheus metrics for SOPHIA Intel monitoring
"""

import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from typing import Callable
import logging

logger = logging.getLogger(__name__)

# Define metrics
REQUEST_COUNT = Counter(
    'sophia_intel_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'sophia_intel_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'sophia_intel_active_connections',
    'Number of active connections'
)

ORCHESTRATOR_TASKS = Counter(
    'sophia_intel_orchestrator_tasks_total',
    'Total number of orchestrator tasks',
    ['task_type', 'status']
)

ORCHESTRATOR_DURATION = Histogram(
    'sophia_intel_orchestrator_duration_seconds',
    'Orchestrator task duration in seconds',
    ['task_type']
)

AI_MODEL_REQUESTS = Counter(
    'sophia_intel_ai_model_requests_total',
    'Total number of AI model requests',
    ['model', 'status']
)

AI_MODEL_DURATION = Histogram(
    'sophia_intel_ai_model_duration_seconds',
    'AI model request duration in seconds',
    ['model']
)

MEMORY_USAGE = Gauge(
    'sophia_intel_memory_usage_bytes',
    'Memory usage in bytes'
)

class PrometheusMiddleware:
    """
    FastAPI middleware for Prometheus metrics collection
    """
    
    def __init__(self, app_name: str = "sophia-intel"):
        self.app_name = app_name
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics endpoint
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Record active connections
        ACTIVE_CONNECTIONS.inc()
        
        # Start timing
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            return response
            
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=500
            ).inc()
            
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            logger.error(f"Request failed: {str(e)}")
            raise
            
        finally:
            # Decrement active connections
            ACTIVE_CONNECTIONS.dec()

def record_orchestrator_task(task_type: str, status: str, duration: float = None):
    """
    Record orchestrator task metrics
    """
    ORCHESTRATOR_TASKS.labels(task_type=task_type, status=status).inc()
    
    if duration is not None:
        ORCHESTRATOR_DURATION.labels(task_type=task_type).observe(duration)

def record_ai_model_request(model: str, status: str, duration: float = None):
    """
    Record AI model request metrics
    """
    AI_MODEL_REQUESTS.labels(model=model, status=status).inc()
    
    if duration is not None:
        AI_MODEL_DURATION.labels(model=model).observe(duration)

def update_memory_usage(memory_bytes: int):
    """
    Update memory usage metric
    """
    MEMORY_USAGE.set(memory_bytes)

def get_metrics():
    """
    Get Prometheus metrics in the expected format
    """
    return generate_latest()

def get_metrics_content_type():
    """
    Get the content type for metrics endpoint
    """
    return CONTENT_TYPE_LATEST

