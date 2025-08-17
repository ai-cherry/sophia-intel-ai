"""
Correlation ID middleware for SOPHIA Intel API
Implements request correlation IDs for distributed tracing and logging
"""

import uuid
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Add correlation ID to requests and responses for tracing"""
    
    async def dispatch(self, request: Request, call_next):
        # Get correlation ID from header or generate new one
        correlation_id = request.headers.get("x-correlation-id")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Store correlation ID in request state
        request.state.correlation_id = correlation_id
        
        # Add to logging context
        logger.info(f"Request started", extra={
            "correlation_id": correlation_id,
            "method": request.method,
            "url": str(request.url),
            "user_agent": request.headers.get("user-agent", "unknown")
        })
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        # Log response
        logger.info(f"Request completed", extra={
            "correlation_id": correlation_id,
            "status_code": response.status_code,
            "response_time": getattr(request.state, "response_time", 0)
        })
        
        return response

def get_correlation_id(request: Request) -> str:
    """Get correlation ID from request state"""
    return getattr(request.state, "correlation_id", "unknown")

def setup_correlation_logging():
    """Setup logging with correlation ID support"""
    import structlog
    
    # Configure structured logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

# Custom log formatter with correlation ID
class CorrelationLogFormatter(logging.Formatter):
    """Custom log formatter that includes correlation ID"""
    
    def format(self, record):
        # Add correlation ID to log record if available
        correlation_id = getattr(record, "correlation_id", "unknown")
        record.correlation_id = correlation_id
        
        return super().format(record)

def setup_logging_with_correlation():
    """Setup logging configuration with correlation ID support"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('sophia-intel.log')
        ]
    )
    
    # Set custom formatter for all handlers
    formatter = CorrelationLogFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s'
    )
    
    for handler in logging.root.handlers:
        handler.setFormatter(formatter)

