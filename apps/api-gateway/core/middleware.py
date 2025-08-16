"""Middleware for request tracking, CORS, and rate limiting"""
import uuid
import time
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import structlog

logger = structlog.get_logger()

class RequestMiddleware(BaseHTTPMiddleware):
    """Middleware for request ID, timing, and structured logging"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        
        # Start timing
        start_time = time.time()
        
        # Log request start
        logger.info(
            "request_start",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=get_remote_address(request)
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful response
            logger.info(
                "request_complete",
                request_id=request_id,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2)
            )
            
            # Add request ID to response headers
            response.headers["x-request-id"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration for error case
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            logger.error(
                "request_error",
                request_id=request_id,
                error=str(e),
                duration_ms=round(duration_ms, 2)
            )
            
            raise

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)
