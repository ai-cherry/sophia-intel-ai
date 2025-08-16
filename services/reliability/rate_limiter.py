"""
SOPHIA Intel - Rate Limiter
Stage B: Harden for Reliability - Protect API edge during voice/rapid inputs
"""
import time
import asyncio
from typing import Dict, Tuple
from dataclasses import dataclass
from flask import request, jsonify
from functools import wraps

@dataclass
class RateLimitConfig:
    rate: float = 5.0  # requests per second
    burst: int = 10    # burst capacity
    window: int = 60   # time window in seconds

class TokenBucket:
    """Token bucket rate limiter implementation"""
    
    def __init__(self, rate: float, burst: int):
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()
    
    def allow(self) -> bool:
        """Check if request is allowed"""
        now = time.time()
        
        # Add tokens based on elapsed time
        elapsed = now - self.last_update
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.last_update = now
        
        # Check if we have tokens available
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        
        return False
    
    def time_until_available(self) -> float:
        """Time until next token is available"""
        if self.tokens >= 1:
            return 0.0
        return (1 - self.tokens) / self.rate

class RateLimiter:
    """Rate limiter for SOPHIA Intel API"""
    
    def __init__(self):
        self.buckets: Dict[str, TokenBucket] = {}
        self.configs: Dict[str, RateLimitConfig] = {
            'default': RateLimitConfig(rate=5.0, burst=10),
            'voice': RateLimitConfig(rate=2.0, burst=5),  # Stricter for voice
            'orchestration': RateLimitConfig(rate=10.0, burst=20),  # More lenient for orchestration
            'health': RateLimitConfig(rate=30.0, burst=50),  # Very lenient for health checks
        }
    
    def get_client_id(self) -> str:
        """Get client identifier (IP address)"""
        # Try to get real IP from headers (for proxy/load balancer)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.remote_addr or 'unknown'
    
    def get_bucket_key(self, client_id: str, endpoint_type: str) -> str:
        """Generate bucket key for client and endpoint type"""
        return f"{client_id}:{endpoint_type}"
    
    def get_bucket(self, client_id: str, endpoint_type: str) -> TokenBucket:
        """Get or create token bucket for client and endpoint"""
        bucket_key = self.get_bucket_key(client_id, endpoint_type)
        
        if bucket_key not in self.buckets:
            config = self.configs.get(endpoint_type, self.configs['default'])
            self.buckets[bucket_key] = TokenBucket(config.rate, config.burst)
        
        return self.buckets[bucket_key]
    
    def is_allowed(self, endpoint_type: str = 'default') -> Tuple[bool, float]:
        """Check if request is allowed"""
        client_id = self.get_client_id()
        bucket = self.get_bucket(client_id, endpoint_type)
        
        allowed = bucket.allow()
        retry_after = bucket.time_until_available() if not allowed else 0.0
        
        return allowed, retry_after
    
    def cleanup_old_buckets(self, max_age: int = 3600):
        """Clean up old unused buckets"""
        now = time.time()
        to_remove = []
        
        for key, bucket in self.buckets.items():
            if now - bucket.last_update > max_age:
                to_remove.append(key)
        
        for key in to_remove:
            del self.buckets[key]

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(endpoint_type: str = 'default'):
    """Decorator for rate limiting endpoints"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            allowed, retry_after = rate_limiter.is_allowed(endpoint_type)
            
            if not allowed:
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests for {endpoint_type} endpoint',
                    'retry_after': retry_after,
                    'endpoint_type': endpoint_type
                })
                response.status_code = 429
                response.headers['Retry-After'] = str(int(retry_after) + 1)
                response.headers['X-RateLimit-Limit'] = str(rate_limiter.configs.get(endpoint_type, rate_limiter.configs['default']).rate)
                response.headers['X-RateLimit-Remaining'] = '0'
                return response
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Middleware for automatic cleanup
def setup_rate_limit_cleanup():
    """Set up periodic cleanup of old buckets"""
    def cleanup_task():
        while True:
            time.sleep(300)  # Clean up every 5 minutes
            rate_limiter.cleanup_old_buckets()
    
    import threading
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()

# Rate limit configurations for different endpoint types
ENDPOINT_CONFIGS = {
    'health': RateLimitConfig(rate=30.0, burst=50),
    'orchestration': RateLimitConfig(rate=10.0, burst=20),
    'voice_stt': RateLimitConfig(rate=2.0, burst=5),
    'voice_tts': RateLimitConfig(rate=2.0, burst=5),
    'voice_health': RateLimitConfig(rate=10.0, burst=15),
    'default': RateLimitConfig(rate=5.0, burst=10),
}

