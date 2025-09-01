"""
Middleware for Rate Limiting, Error Handling, and Resilience
Provides production-ready middleware for the Sophia Intel AI system.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import httpx
from typing import Callable
import time
import asyncio
import logging
import traceback
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict
from circuitbreaker import circuit

from app.core.config import settings
from app.core.circuit_breaker import with_circuit_breaker, get_llm_circuit_breaker, get_weaviate_circuit_breaker, get_redis_circuit_breaker, get_webhook_circuit_breaker

logger = logging.getLogger(__name__)

# ============================================
# Rate Limiting
# ============================================

# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],
    storage_uri=settings.redis_url if settings.redis_url else None,
    strategy="fixed-window"
)

# Custom rate limit configurations
RATE_LIMITS = {
    "/teams/run": f"{settings.streaming_rate_limit_rpm} per minute",
    "/workflows/run": f"{settings.streaming_rate_limit_rpm} per minute",
    "/memory/add": "100 per minute",
    "/memory/search": "200 per minute",
    "/index/update": "10 per hour",
    "/v1/playground/agents/*/runs": "30 per minute",
}

class RateLimitMiddleware:
    """Enhanced rate limiting middleware with per-endpoint limits."""
    
    def __init__(self, app):
        self.app = app
        self.limits = defaultdict(lambda: "100 per minute")
        self.limits.update(RATE_LIMITS)
        
        # Track request counts for analytics
        self.request_counts = defaultdict(lambda: defaultdict(int))
    
    async def __call__(self, request: Request, call_next):
        # Skip rate limiting for health checks and metrics
        if request.url.path in ["/healthz", "/metrics", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Check if rate limiting is enabled
        if not settings.rate_limit_enabled:
            return await call_next(request)
        
        # Get client identifier
        client_id = get_remote_address(request)
        endpoint = request.url.path
        
        # Check rate limit
        if self.is_rate_limited(client_id, endpoint):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": self.get_retry_after(client_id, endpoint)
                },
                headers={
                    "Retry-After": str(self.get_retry_after(client_id, endpoint)),
                    "X-RateLimit-Limit": self.limits[endpoint],
                    "X-RateLimit-Remaining": "0"
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = self.limits[endpoint]
        response.headers["X-RateLimit-Remaining"] = str(self.get_remaining_requests(client_id, endpoint))
        
        return response
    
    def is_rate_limited(self, client_id: str, endpoint: str) -> bool:
        """Check if client is rate limited."""
        # Implementation depends on storage backend
        # This is a simplified in-memory version
        current_minute = datetime.now().replace(second=0, microsecond=0)
        key = f"{client_id}:{endpoint}:{current_minute}"
        
        self.request_counts[key]["count"] += 1
        
        # Parse limit (e.g., "100 per minute")
        limit_str = self.limits[endpoint]
        limit = int(limit_str.split()[0])
        
        return self.request_counts[key]["count"] > limit
    
    def get_retry_after(self, client_id: str, endpoint: str) -> int:
        """Get seconds until rate limit resets."""
        # Next minute
        next_minute = (datetime.now() + timedelta(minutes=1)).replace(second=0, microsecond=0)
        return int((next_minute - datetime.now()).total_seconds())
    
    def get_remaining_requests(self, client_id: str, endpoint: str) -> int:
        """Get remaining requests in current window."""
        current_minute = datetime.now().replace(second=0, microsecond=0)
        key = f"{client_id}:{endpoint}:{current_minute}"
        
        limit_str = self.limits[endpoint]
        limit = int(limit_str.split()[0])
        
        used = self.request_counts[key]["count"]
        return max(0, limit - used)

# ============================================
# Error Handling
# ============================================

class ErrorHandlingMiddleware:
    """Comprehensive error handling middleware."""
    
    def __init__(self, app):
        self.app = app
        self.error_counts = defaultdict(int)
    
    async def __call__(self, request: Request, call_next):
        try:
            # Process request
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            # Handle known HTTP exceptions
            self.error_counts[e.status_code] += 1
            
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": e.detail,
                    "status": e.status_code,
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": str(request.url.path)
                }
            )
            
        except RateLimitExceeded:
            # Handle rate limit exceptions
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": 60,
                    "timestamp": datetime.utcnow().isoformat()
                },
                headers={"Retry-After": "60"}
            )
            
        except Exception as e:
            # Handle unexpected errors
            self.error_counts[500] += 1
            
            # Log full traceback
            logger.error(f"Unhandled exception: {traceback.format_exc()}")
            
            # Determine if we should expose error details
            if settings.debug:
                error_detail = str(e)
                trace = traceback.format_exc()
            else:
                error_detail = "Internal server error"
                trace = None
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": error_detail,
                    "status": 500,
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": str(request.url.path),
                    "trace": trace
                }
            )

# ============================================
# Circuit Breaker
# ============================================

class CircuitBreakerMiddleware:
    """Circuit breaker for external services."""
    
    def __init__(self, app):
        self.app = app
        self.breakers = {}
        
        # Configure circuit breakers for external services
        self.configure_breakers()
    
    @with_circuit_breaker("external_api")
    def configure_breakers(self):
        """Configure circuit breakers for known services."""
        
        # Weaviate circuit breaker
        @circuit(failure_threshold=5, recovery_timeout=60, expected_exception=Exception)
        def weaviate_breaker():
            pass
        self.breakers['weaviate'] = weaviate_breaker
        
        # OpenAI/OpenRouter circuit breaker
        @circuit(failure_threshold=3, recovery_timeout=30, expected_exception=Exception)
        def openai_breaker():
            pass
        self.breakers['openai'] = openai_breaker
        
        # Redis circuit breaker
        @circuit(failure_threshold=10, recovery_timeout=20, expected_exception=Exception)
        def redis_breaker():
            pass
        self.breakers['redis'] = redis_breaker
    
    async def __call__(self, request: Request, call_next):
        # Check circuit breakers for relevant endpoints
        endpoint = request.url.path
        
        # Check if any breakers are open
        open_breakers = []
        for name, breaker in self.breakers.items():
            if breaker.current_state == 'open':
                open_breakers.append(name)
        
        if open_breakers and endpoint.startswith('/teams/run'):
            # Service degradation - return cached or default response
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": "Service temporarily unavailable",
                    "services": open_breakers,
                    "retry_after": 30,
                    "timestamp": datetime.utcnow().isoformat()
                },
                headers={"Retry-After": "30"}
            )
        
        return await call_next(request)

# ============================================
# Retry Logic
# ============================================

class RetryableHTTPClient:
    """HTTP client with automatic retry logic."""
    
    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        timeout: float = 30.0
    ):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout
        
        # Configure transport with retries
        self.transport = httpx.AsyncHTTPTransport(
            retries=max_retries,
        )
        
        self.client = httpx.AsyncClient(
            transport=self.transport,
            timeout=httpx.Timeout(timeout)
        )
    
    async def request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """Make request with exponential backoff retry."""
        
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                response = await self.client.request(method, url, **kwargs)
                
                # Check if we should retry based on status code
                if response.status_code in [502, 503, 504]:
                    if attempt < self.max_retries - 1:
                        await self._backoff(attempt)
                        continue
                
                return response
                
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_exception = e
                
                if attempt < self.max_retries - 1:
                    logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                    await self._backoff(attempt)
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts: {e}")
        
        if last_exception:
            raise last_exception
        
        raise Exception("Max retries exceeded")
    
    async def _backoff(self, attempt: int):
        """Exponential backoff with jitter."""
        delay = self.backoff_factor * (2 ** attempt)
        # Add jitter
        import random
        delay *= (0.5 + random.random())
        await asyncio.sleep(delay)
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

# ============================================
# Timeout Middleware
# ============================================

class TimeoutMiddleware:
    """Request timeout middleware."""
    
    def __init__(self, app, default_timeout: int = 300):
        self.app = app
        self.default_timeout = default_timeout
        
        # Custom timeouts for specific endpoints
        self.endpoint_timeouts = {
            "/teams/run": 600,  # 10 minutes for team execution
            "/workflows/run": 600,
            "/index/update": 3600,  # 1 hour for indexing
        }
    
    async def __call__(self, request: Request, call_next):
        endpoint = request.url.path
        timeout = self.endpoint_timeouts.get(endpoint, self.default_timeout)
        
        try:
            # Run request with timeout
            response = await asyncio.wait_for(
                call_next(request),
                timeout=timeout
            )
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"Request timeout: {endpoint} after {timeout}s")
            
            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content={
                    "error": "Request timeout",
                    "timeout": timeout,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

# ============================================
# Resilience Decorators
# ============================================

def with_retry(
    max_attempts: int = 3,
    backoff: float = 1.0,
    exceptions: tuple = (Exception,)
):
    """Decorator for automatic retry with exponential backoff."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        delay = backoff * (2 ** attempt)
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        delay = backoff * (2 ** attempt)
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )
            
            raise last_exception
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

def with_timeout(seconds: int):
    """Decorator to add timeout to async functions."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds
                )
            except asyncio.TimeoutError:
                logger.error(f"{func.__name__} timed out after {seconds}s")
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail=f"Operation timed out after {seconds} seconds"
                )
        
        return wrapper
    
    return decorator

# ============================================
# Setup Function
# ============================================

def setup_middleware(app):
    """Setup all middleware for the application."""
    
    # Add error handling (outermost)
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Add timeout handling
    app.add_middleware(TimeoutMiddleware)
    
    # Add circuit breaker
    app.add_middleware(CircuitBreakerMiddleware)
    
    # Add rate limiting
    if settings.rate_limit_enabled:
        app.add_middleware(RateLimitMiddleware)
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    logger.info("Middleware stack configured")

# Export components
__all__ = [
    "setup_middleware",
    "RateLimitMiddleware",
    "ErrorHandlingMiddleware",
    "CircuitBreakerMiddleware",
    "TimeoutMiddleware",
    "RetryableHTTPClient",
    "with_retry",
    "with_timeout",
    "limiter"
]