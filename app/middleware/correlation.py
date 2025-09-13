"""
Request correlation middleware for distributed tracing
"""

import uuid
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


async def correlation_middleware(request: Request, call_next):
    """
    Add X-Request-ID header for request correlation across services.
    
    - If incoming request has X-Request-ID, use it
    - Otherwise generate a new one
    - Add to response headers
    - Add to logging context
    """
    # Get or generate request ID
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())
    
    # Store in request state for access in endpoints
    request.state.request_id = request_id
    
    # Add to logging context (if using structlog)
    try:
        import structlog
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            path=request.url.path,
            method=request.method
        )
    except ImportError:
        # Fall back to standard logging
        logger.info(f"Request {request_id}: {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    
    # Clear logging context
    try:
        import structlog
        structlog.contextvars.clear_contextvars()
    except ImportError:
        pass
    
    return response


class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    Alternative class-based middleware for correlation IDs.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Store in request state
        request.state.request_id = request_id
        
        # Process request with added headers
        response = await call_next(request)
        
        # Add to response
        response.headers["X-Request-ID"] = request_id
        
        return response


def get_request_id(request: Request) -> str:
    """
    Helper to get request ID from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Request ID string
    """
    return getattr(request.state, "request_id", "unknown")