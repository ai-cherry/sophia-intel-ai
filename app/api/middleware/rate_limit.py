"""
Rate limiting middleware for FastAPI
Implements per-endpoint and global rate limiting using in-memory storage.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from functools import wraps
from typing import Dict, Optional, Tuple

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.ai_logger import logger
from app.core.config import settings


class InMemoryRateLimiter:
    """
    In-memory rate limiter using sliding window algorithm
    """

    def __init__(self):
        # Structure: {client_id: {endpoint: deque of timestamps}}
        self.requests: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        self.global_requests: deque = deque()
        self.lock = asyncio.Lock()

    async def is_allowed(
        self, client_id: str, endpoint: str, limit: int, window_seconds: int = 60
    ) -> Tuple[bool, int, int]:
        """
        Check if request is allowed based on rate limit
        Returns (is_allowed, requests_made, reset_time)
        """
        async with self.lock:
            now = time.time()
            window_start = now - window_seconds

            # Clean old requests for this client/endpoint
            client_endpoint_requests = self.requests[client_id][endpoint]
            while client_endpoint_requests and client_endpoint_requests[0] < window_start:
                client_endpoint_requests.popleft()

            current_requests = len(client_endpoint_requests)

            if current_requests >= limit:
                # Calculate reset time (when oldest request expires)
                reset_time = (
                    int(client_endpoint_requests[0] + window_seconds)
                    if client_endpoint_requests
                    else int(now + window_seconds)
                )
                return False, current_requests, reset_time

            # Allow request and record it
            client_endpoint_requests.append(now)
            reset_time = int(now + window_seconds)
            return True, current_requests + 1, reset_time

    async def check_global_limit(self, limit: int, window_seconds: int = 60) -> Tuple[bool, int]:
        """
        Check global rate limit across all clients
        Returns (is_allowed, current_global_requests)
        """
        async with self.lock:
            now = time.time()
            window_start = now - window_seconds

            # Clean old global requests
            while self.global_requests and self.global_requests[0] < window_start:
                self.global_requests.popleft()

            current_global = len(self.global_requests)

            if current_global >= limit:
                return False, current_global

            # Record global request
            self.global_requests.append(now)
            return True, current_global + 1


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting
    """

    def __init__(self, app, rate_limiter: Optional[InMemoryRateLimiter] = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or InMemoryRateLimiter()
        self.enabled = settings.rate_limit_enabled
        self.default_limit = settings.rate_limit_requests_per_minute
        self.max_concurrent = settings.max_concurrent_requests

        # Endpoint-specific limits
        self.endpoint_limits = {
            "/api/knowledge/search": 30,  # Lower limit for search
            "/api/knowledge/": 60,  # Standard CRUD operations
            "/api/knowledge/sync": 5,  # Very limited for sync operations
            "/health": 120,  # Higher limit for health checks
        }

    def get_client_id(self, request: Request) -> str:
        """Extract client identifier from request"""
        # Try to get from X-Forwarded-For header first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in case of multiple proxies
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        # Include user agent for better identification
        user_agent = request.headers.get("User-Agent", "unknown")
        return f"{client_ip}:{hash(user_agent) % 10000}"

    def get_endpoint_key(self, request: Request) -> str:
        """Get endpoint key for rate limiting"""
        path = request.url.path
        method = request.method
        return f"{method}:{path}"

    def get_rate_limit(self, endpoint_key: str) -> int:
        """Get rate limit for specific endpoint"""
        # Check exact matches first
        for pattern, limit in self.endpoint_limits.items():
            if pattern in endpoint_key:
                return limit

        return self.default_limit

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        if not self.enabled:
            return await call_next(request)

        client_id = self.get_client_id(request)
        endpoint_key = self.get_endpoint_key(request)
        rate_limit = self.get_rate_limit(endpoint_key)

        # Check global concurrent requests
        global_allowed, global_count = await self.rate_limiter.check_global_limit(
            self.max_concurrent, window_seconds=1  # 1 second window for concurrent requests
        )

        if not global_allowed:
            logger.warning(f"Global rate limit exceeded: {global_count}/{self.max_concurrent}")
            return self._create_rate_limit_response(
                "Too many concurrent requests globally",
                rate_limit,
                global_count,
                int(time.time() + 1),
            )

        # Check endpoint-specific rate limit
        allowed, requests_made, reset_time = await self.rate_limiter.is_allowed(
            client_id, endpoint_key, rate_limit
        )

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {client_id} on {endpoint_key}: {requests_made}/{rate_limit}"
            )
            return self._create_rate_limit_response(
                "Rate limit exceeded", rate_limit, requests_made, reset_time
            )

        # Process request
        start_time = time.time()
        try:
            response = await call_next(request)

            # Add rate limiting headers
            response.headers["X-RateLimit-Limit"] = str(rate_limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, rate_limit - requests_made))
            response.headers["X-RateLimit-Reset"] = str(reset_time)
            response.headers["X-RateLimit-Window"] = "60"

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error processing request from {client_id}: {e} (took {process_time:.2f}s)"
            )
            raise

    def _create_rate_limit_response(
        self, message: str, limit: int, current: int, reset_time: int
    ) -> Response:
        """Create rate limit exceeded response"""
        headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(reset_time),
            "X-RateLimit-Window": "60",
            "Retry-After": str(max(1, reset_time - int(time.time()))),
        }

        return Response(
            content=f'{{"detail": "{message}", "limit": {limit}, "current": {current}, "reset_time": {reset_time}}}',
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers=headers,
            media_type="application/json",
        )


# Global instance
rate_limiter = InMemoryRateLimiter()


def rate_limit(limit: int = None, window_seconds: int = 60):
    """
    Decorator for endpoint-specific rate limiting
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                # If no request object, skip rate limiting
                return await func(*args, **kwargs)

            if not settings.rate_limit_enabled:
                return await func(*args, **kwargs)

            client_id = f"{request.client.host if request.client else 'unknown'}:{hash(request.headers.get('User-Agent', 'unknown')) % 10000}"
            endpoint_key = f"{request.method}:{request.url.path}"
            effective_limit = limit or settings.rate_limit_requests_per_minute

            allowed, requests_made, reset_time = await rate_limiter.is_allowed(
                client_id, endpoint_key, effective_limit, window_seconds
            )

            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: {requests_made}/{effective_limit} requests in {window_seconds}s window",
                    headers={
                        "X-RateLimit-Limit": str(effective_limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_time),
                        "Retry-After": str(max(1, reset_time - int(time.time()))),
                    },
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
