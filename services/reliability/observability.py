"""
SOPHIA Intel - Observability Middleware
Stage B: Harden for Reliability - Request-ID, structured logs, Prometheus counters
"""
import time
import uuid
import logging
import json
from typing import Dict, Any, Optional
from flask import Flask, request, g, jsonify
from functools import wraps
from dataclasses import dataclass, asdict
from datetime import datetime

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@dataclass
class RequestMetrics:
    request_id: str
    method: str
    path: str
    client_ip: str
    user_agent: str
    start_time: float
    end_time: Optional[float] = None
    status_code: Optional[int] = None
    response_size: Optional[int] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None

class MetricsCollector:
    """Simple metrics collector for SOPHIA Intel"""
    
    def __init__(self):
        self.counters: Dict[str, int] = {}
        self.histograms: Dict[str, list] = {}
        self.gauges: Dict[str, float] = {}
    
    def increment_counter(self, name: str, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        key = self._make_key(name, labels)
        self.counters[key] = self.counters.get(key, 0) + 1
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram value"""
        key = self._make_key(name, labels)
        if key not in self.histograms:
            self.histograms[key] = []
        self.histograms[key].append(value)
        
        # Keep only last 1000 values to prevent memory issues
        if len(self.histograms[key]) > 1000:
            self.histograms[key] = self.histograms[key][-1000:]
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric"""
        key = self._make_key(name, labels)
        self.gauges[key] = value
    
    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Create metric key with labels"""
        if not labels:
            return name
        
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics for export"""
        return {
            'counters': self.counters,
            'histograms': {k: {
                'count': len(v),
                'sum': sum(v),
                'avg': sum(v) / len(v) if v else 0,
                'p50': self._percentile(v, 0.5),
                'p95': self._percentile(v, 0.95),
                'p99': self._percentile(v, 0.99),
            } for k, v in self.histograms.items()},
            'gauges': self.gauges
        }
    
    def _percentile(self, values: list, p: float) -> float:
        """Calculate percentile"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * p)
        return sorted_values[min(index, len(sorted_values) - 1)]

# Global metrics collector
metrics = MetricsCollector()

class ObservabilityMiddleware:
    """Observability middleware for SOPHIA Intel"""
    
    def __init__(self, app: Flask = None):
        self.app = app
        self.logger = logging.getLogger('sophia.observability')
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize middleware with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_appcontext(self.teardown_request)
        
        # Add metrics endpoint
        @app.route('/metrics')
        def get_metrics():
            return jsonify(metrics.get_metrics())
        
        # Add health endpoint with observability
        @app.route('/observability/health')
        def observability_health():
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'metrics_available': True,
                'request_id': g.get('request_id', 'unknown')
            })
    
    def before_request(self):
        """Called before each request"""
        # Generate or extract request ID
        request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        g.request_id = request_id
        g.start_time = time.time()
        
        # Create request metrics
        g.request_metrics = RequestMetrics(
            request_id=request_id,
            method=request.method,
            path=request.path,
            client_ip=self._get_client_ip(),
            user_agent=request.headers.get('User-Agent', 'unknown'),
            start_time=g.start_time
        )
        
        # Log request start
        self.logger.info(
            "Request started",
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.path,
                'client_ip': g.request_metrics.client_ip,
                'user_agent': g.request_metrics.user_agent
            }
        )
        
        # Increment request counter
        metrics.increment_counter('http_requests_total', {
            'method': request.method,
            'path': request.path
        })
    
    def after_request(self, response):
        """Called after each request"""
        if hasattr(g, 'request_metrics'):
            # Update metrics
            g.request_metrics.end_time = time.time()
            g.request_metrics.status_code = response.status_code
            g.request_metrics.response_size = len(response.get_data())
            g.request_metrics.duration_ms = (g.request_metrics.end_time - g.request_metrics.start_time) * 1000
            
            # Add request ID to response headers
            response.headers['X-Request-ID'] = g.request_metrics.request_id
            
            # Record metrics
            metrics.increment_counter('http_responses_total', {
                'method': request.method,
                'path': request.path,
                'status': str(response.status_code)
            })
            
            metrics.record_histogram('http_request_duration_ms', g.request_metrics.duration_ms, {
                'method': request.method,
                'path': request.path
            })
            
            # Log request completion
            self.logger.info(
                "Request completed",
                extra={
                    'request_id': g.request_metrics.request_id,
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration_ms': g.request_metrics.duration_ms,
                    'response_size': g.request_metrics.response_size
                }
            )
        
        return response
    
    def teardown_request(self, exception=None):
        """Called when request context is torn down"""
        if exception and hasattr(g, 'request_metrics'):
            g.request_metrics.error = str(exception)
            
            # Log error
            self.logger.error(
                "Request failed",
                extra={
                    'request_id': g.request_metrics.request_id,
                    'method': request.method,
                    'path': request.path,
                    'error': str(exception)
                },
                exc_info=True
            )
            
            # Increment error counter
            metrics.increment_counter('http_errors_total', {
                'method': request.method,
                'path': request.path,
                'error_type': type(exception).__name__
            })
    
    def _get_client_ip(self) -> str:
        """Get client IP address"""
        # Try to get real IP from headers (for proxy/load balancer)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.remote_addr or 'unknown'

def with_request_id(func):
    """Decorator to ensure request ID is available in function context"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not hasattr(g, 'request_id'):
            g.request_id = str(uuid.uuid4())
        return func(*args, **kwargs)
    return wrapper

def log_structured(level: str, message: str, **kwargs):
    """Log structured message with request context"""
    logger = logging.getLogger('sophia.app')
    
    extra = {
        'request_id': g.get('request_id', 'unknown'),
        **kwargs
    }
    
    getattr(logger, level.lower())(message, extra=extra)

# Convenience functions for structured logging
def log_info(message: str, **kwargs):
    log_structured('info', message, **kwargs)

def log_warning(message: str, **kwargs):
    log_structured('warning', message, **kwargs)

def log_error(message: str, **kwargs):
    log_structured('error', message, **kwargs)

# SLO tracking
class SLOTracker:
    """Track SLO metrics for SOPHIA Intel"""
    
    def __init__(self):
        self.slos = {
            'chat_p50_ms': 1500,  # Chat ≤ 1.5s P50
            'chat_p95_ms': 6000,  # Chat ≤ 6s P95
            'health_p95_ms': 100,  # Health checks ≤ 100ms P95
            'voice_p95_ms': 3000,  # Voice ≤ 3s P95
        }
    
    def check_slos(self) -> Dict[str, Any]:
        """Check current SLO compliance"""
        current_metrics = metrics.get_metrics()
        slo_status = {}
        
        for slo_name, threshold in self.slos.items():
            # Extract relevant metrics
            if 'chat' in slo_name:
                metric_key = 'http_request_duration_ms{method=POST,path=/api/orchestration}'
            elif 'health' in slo_name:
                metric_key = 'http_request_duration_ms{method=GET,path=/health}'
            elif 'voice' in slo_name:
                metric_key = 'http_request_duration_ms{method=POST,path=/api/speech/stt}'
            else:
                continue
            
            if metric_key in current_metrics['histograms']:
                hist_data = current_metrics['histograms'][metric_key]
                
                if 'p50' in slo_name:
                    current_value = hist_data['p50']
                elif 'p95' in slo_name:
                    current_value = hist_data['p95']
                else:
                    current_value = hist_data['avg']
                
                slo_status[slo_name] = {
                    'threshold': threshold,
                    'current': current_value,
                    'compliant': current_value <= threshold,
                    'breach_percentage': max(0, (current_value - threshold) / threshold * 100)
                }
        
        return slo_status

# Global SLO tracker
slo_tracker = SLOTracker()

