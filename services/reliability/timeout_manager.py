"""
SOPHIA Intel - Timeout and Retry Manager
Stage B: Harden for Reliability
"""
import asyncio
import httpx
import time
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    backoff_factor: float = 2.0
    timeout: float = 15.0

class CircuitBreaker:
    """Simple circuit breaker for downstream services"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise RuntimeError("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            
            raise e

class TimeoutManager:
    """Manages timeouts, retries, and circuit breakers for SOPHIA Intel"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.default_config = RetryConfig()
    
    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()
        return self.circuit_breakers[service_name]
    
    async def call_with_retry(
        self, 
        func: Callable,
        service_name: str,
        config: Optional[RetryConfig] = None,
        *args, 
        **kwargs
    ) -> Any:
        """Call function with retry logic and circuit breaker"""
        config = config or self.default_config
        circuit_breaker = self.get_circuit_breaker(service_name)
        
        for attempt in range(config.max_attempts):
            try:
                # Use circuit breaker
                result = circuit_breaker.call(func, *args, **kwargs)
                return result
                
            except Exception as e:
                if attempt == config.max_attempts - 1:
                    logger.error(f"All {config.max_attempts} attempts failed for {service_name}: {e}")
                    raise e
                
                # Calculate backoff delay
                delay = min(
                    config.base_delay * (config.backoff_factor ** attempt),
                    config.max_delay
                )
                
                logger.warning(f"Attempt {attempt + 1} failed for {service_name}, retrying in {delay}s: {e}")
                await asyncio.sleep(delay)
    
    async def http_call(
        self,
        method: str,
        url: str,
        service_name: str,
        config: Optional[RetryConfig] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP call with timeout and retry"""
        config = config or self.default_config
        
        async def _make_request():
            async with httpx.AsyncClient(timeout=config.timeout) as client:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
        
        return await self.call_with_retry(_make_request, service_name, config)

# Global timeout manager instance
timeout_manager = TimeoutManager()

def with_timeout(service_name: str, config: Optional[RetryConfig] = None):
    """Decorator for adding timeout and retry to functions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await timeout_manager.call_with_retry(func, service_name, config, *args, **kwargs)
        return wrapper
    return decorator

# Specific configurations for different services
OPENROUTER_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=2.0,
    max_delay=10.0,
    timeout=30.0  # LLM calls can take longer
)

QDRANT_CONFIG = RetryConfig(
    max_attempts=2,
    base_delay=0.5,
    max_delay=5.0,
    timeout=10.0  # Vector DB should be fast
)

MCP_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=15.0,
    timeout=20.0  # MCP services moderate timeout
)

VOICE_CONFIG = RetryConfig(
    max_attempts=2,
    base_delay=1.0,
    max_delay=8.0,
    timeout=25.0  # Voice processing can take time
)

