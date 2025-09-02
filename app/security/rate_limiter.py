"""
Rate limiting middleware for API protection
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import time
import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta
import os
from typing import Dict, Deque, Tuple

class RateLimiter:
    def __init__(
        self, 
        requests_per_minute: int = None,
        requests_per_hour: int = None,
        burst_size: int = None
    ):
        """
        Initialize rate limiter with configurable limits
        
        Args:
            requests_per_minute: Max requests per minute per IP
            requests_per_hour: Max requests per hour per IP
            burst_size: Max burst requests allowed
        """
        self.requests_per_minute = requests_per_minute or int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
        self.requests_per_hour = requests_per_hour or int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
        self.burst_size = burst_size or int(os.getenv("RATE_LIMIT_BURST", "10"))
        
        # Storage for request tracking
        self.minute_requests: Dict[str, Deque[float]] = defaultdict(deque)
        self.hour_requests: Dict[str, Deque[float]] = defaultdict(deque)
        self.burst_tokens: Dict[str, int] = defaultdict(lambda: self.burst_size)
        self.last_refill: Dict[str, float] = defaultdict(time.time)
        
        # Cleanup task
        self.cleanup_task = None
        
    async def __call__(self, request: Request):
        """
        Check if request should be rate limited
        
        Args:
            request: FastAPI request object
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Check burst limit (token bucket algorithm)
        if not self._check_burst_limit(client_ip, current_time):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded - burst limit reached",
                headers={"Retry-After": "1"}
            )
        
        # Check minute limit
        if not self._check_minute_limit(client_ip, current_time):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded - max {self.requests_per_minute} requests per minute",
                headers={"Retry-After": "60"}
            )
        
        # Check hour limit
        if not self._check_hour_limit(client_ip, current_time):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded - max {self.requests_per_hour} requests per hour",
                headers={"Retry-After": "3600"}
            )
        
        # Record this request
        self.minute_requests[client_ip].append(current_time)
        self.hour_requests[client_ip].append(current_time)
        
        return True
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for proxy headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _check_burst_limit(self, client_ip: str, current_time: float) -> bool:
        """Check burst limit using token bucket algorithm"""
        # Refill tokens based on time passed
        time_passed = current_time - self.last_refill[client_ip]
        tokens_to_add = int(time_passed * (self.burst_size / 60))  # Refill rate: burst_size per minute
        
        if tokens_to_add > 0:
            self.burst_tokens[client_ip] = min(
                self.burst_size, 
                self.burst_tokens[client_ip] + tokens_to_add
            )
            self.last_refill[client_ip] = current_time
        
        # Check if we have tokens available
        if self.burst_tokens[client_ip] > 0:
            self.burst_tokens[client_ip] -= 1
            return True
        
        return False
    
    def _check_minute_limit(self, client_ip: str, current_time: float) -> bool:
        """Check per-minute rate limit"""
        minute_ago = current_time - 60
        
        # Clean old requests
        while self.minute_requests[client_ip] and self.minute_requests[client_ip][0] < minute_ago:
            self.minute_requests[client_ip].popleft()
        
        # Check limit
        return len(self.minute_requests[client_ip]) < self.requests_per_minute
    
    def _check_hour_limit(self, client_ip: str, current_time: float) -> bool:
        """Check per-hour rate limit"""
        hour_ago = current_time - 3600
        
        # Clean old requests
        while self.hour_requests[client_ip] and self.hour_requests[client_ip][0] < hour_ago:
            self.hour_requests[client_ip].popleft()
        
        # Check limit
        return len(self.hour_requests[client_ip]) < self.requests_per_hour
    
    async def cleanup_old_data(self):
        """Periodic cleanup of old tracking data"""
        while True:
            await asyncio.sleep(300)  # Run every 5 minutes
            
            current_time = time.time()
            hour_ago = current_time - 3600
            
            # Clean up IPs that haven't made requests in the last hour
            ips_to_remove = []
            
            for ip in list(self.hour_requests.keys()):
                if not self.hour_requests[ip] or self.hour_requests[ip][-1] < hour_ago:
                    ips_to_remove.append(ip)
            
            for ip in ips_to_remove:
                del self.hour_requests[ip]
                if ip in self.minute_requests:
                    del self.minute_requests[ip]
                if ip in self.burst_tokens:
                    del self.burst_tokens[ip]
                if ip in self.last_refill:
                    del self.last_refill[ip]
    
    def get_limits_for_ip(self, client_ip: str) -> dict:
        """Get current limits and usage for an IP"""
        current_time = time.time()
        minute_ago = current_time - 60
        hour_ago = current_time - 3600
        
        minute_count = sum(1 for t in self.minute_requests[client_ip] if t > minute_ago)
        hour_count = sum(1 for t in self.hour_requests[client_ip] if t > hour_ago)
        
        return {
            "ip": client_ip,
            "minute_usage": minute_count,
            "minute_limit": self.requests_per_minute,
            "hour_usage": hour_count,
            "hour_limit": self.requests_per_hour,
            "burst_tokens": self.burst_tokens[client_ip],
            "burst_limit": self.burst_size
        }


# Global rate limiter instance
rate_limiter = RateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    """
    FastAPI middleware for rate limiting
    """
    try:
        await rate_limiter(request)
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail},
            headers=e.headers
        )
    
    response = await call_next(request)
    
    # Add rate limit headers
    client_ip = rate_limiter._get_client_ip(request)
    limits = rate_limiter.get_limits_for_ip(client_ip)
    
    response.headers["X-RateLimit-Limit"] = str(rate_limiter.requests_per_minute)
    response.headers["X-RateLimit-Remaining"] = str(
        max(0, rate_limiter.requests_per_minute - limits["minute_usage"])
    )
    response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
    
    return response