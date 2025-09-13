"""
Centralized HTTP client with retries, timeouts, and circuit breaker
"""

import asyncio
import random
from typing import Optional, Dict, Any
import httpx
from pybreaker import CircuitBreaker
import logging

logger = logging.getLogger(__name__)

# Global clients per base URL
_clients: Dict[str, httpx.AsyncClient] = {}
_breakers: Dict[str, CircuitBreaker] = {}
_lock = asyncio.Lock()


class HTTPClientConfig:
    """Configuration for HTTP client"""
    connect_timeout: float = 2.0
    read_timeout: float = 6.0
    total_timeout: float = 10.0
    max_retries: int = 3
    backoff_base: float = 0.5
    backoff_max: float = 8.0
    circuit_failure_threshold: int = 5
    circuit_recovery_timeout: int = 30


async def get_client(
    base_url: Optional[str] = None,
    config: Optional[HTTPClientConfig] = None
) -> httpx.AsyncClient:
    """
    Get or create a singleton HTTP client with resilience patterns.
    
    Args:
        base_url: Optional base URL for the client
        config: Optional configuration overrides
        
    Returns:
        Configured AsyncClient with retry and circuit breaker
    """
    config = config or HTTPClientConfig()
    key = base_url or "default"
    
    async with _lock:
        if key not in _clients:
            timeout = httpx.Timeout(
                connect=config.connect_timeout,
                read=config.read_timeout,
                write=None,
                pool=config.total_timeout
            )
            
            # Create client with connection pooling
            client = httpx.AsyncClient(
                base_url=base_url,
                timeout=timeout,
                limits=httpx.Limits(
                    max_keepalive_connections=10,
                    max_connections=20,
                    keepalive_expiry=30.0
                ),
                follow_redirects=True
            )
            
            # Wrap with circuit breaker
            breaker = CircuitBreaker(
                fail_max=config.circuit_failure_threshold,
                reset_timeout=config.circuit_recovery_timeout,
                name=f"breaker_{key}"
            )
            
            # Create wrapped client with retry logic
            _clients[key] = _wrap_with_retry(client, config, breaker)
            _breakers[key] = breaker
            
        return _clients[key]


def _wrap_with_retry(
    client: httpx.AsyncClient,
    config: HTTPClientConfig,
    breaker: CircuitBreaker
) -> httpx.AsyncClient:
    """
    Wrap client methods with retry logic and circuit breaker.
    
    This creates a wrapper that intercepts common HTTP methods
    and adds exponential backoff retry with jitter.
    """
    original_request = client.request
    original_get = client.get
    original_post = client.post
    
    async def retry_request(method: str, url: str, **kwargs) -> httpx.Response:
        """Execute request with retries and circuit breaker"""
        
        # Check if this is an idempotent operation
        idempotent = method.upper() in ["GET", "HEAD", "OPTIONS", "DELETE", "PUT"]
        max_attempts = config.max_retries if idempotent else 1
        
        last_error = None
        for attempt in range(max_attempts):
            try:
                # Circuit breaker check
                if breaker.current_state == "open":
                    raise httpx.ConnectError("Circuit breaker is open")
                
                # Execute request
                response = await breaker.call_async(original_request, method, url, **kwargs)
                
                # Success - return response
                if response.status_code < 500:
                    return response
                
                # Server error - maybe retry
                if attempt < max_attempts - 1:
                    wait_time = min(
                        config.backoff_base * (2 ** attempt) + random.uniform(0, 0.1),
                        config.backoff_max
                    )
                    logger.warning(
                        f"Request {method} {url} failed with {response.status_code}, "
                        f"retrying in {wait_time:.2f}s (attempt {attempt + 1}/{max_attempts})"
                    )
                    await asyncio.sleep(wait_time)
                    last_error = httpx.HTTPStatusError(
                        f"Server error: {response.status_code}",
                        request=response.request,
                        response=response
                    )
                    continue
                    
                return response
                
            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as e:
                last_error = e
                if attempt < max_attempts - 1:
                    wait_time = min(
                        config.backoff_base * (2 ** attempt) + random.uniform(0, 0.1),
                        config.backoff_max
                    )
                    logger.warning(
                        f"Request {method} {url} failed: {e}, "
                        f"retrying in {wait_time:.2f}s (attempt {attempt + 1}/{max_attempts})"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Request {method} {url} failed after {max_attempts} attempts: {e}")
                    raise
                    
        # All retries exhausted
        if last_error:
            raise last_error
        raise httpx.ConnectError(f"Failed after {max_attempts} attempts")
    
    # Monkey-patch the client methods
    async def wrapped_get(url: str, **kwargs) -> httpx.Response:
        return await retry_request("GET", url, **kwargs)
    
    async def wrapped_post(url: str, **kwargs) -> httpx.Response:
        return await retry_request("POST", url, **kwargs)
    
    # Replace methods on the client
    client.request = retry_request
    client.get = wrapped_get
    client.post = wrapped_post
    
    return client


async def close_all_clients():
    """Close all HTTP clients gracefully"""
    async with _lock:
        for client in _clients.values():
            await client.aclose()
        _clients.clear()
        _breakers.clear()


# Ensure cleanup on shutdown
import atexit
import signal

def _cleanup():
    """Synchronous cleanup for exit handlers"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(close_all_clients())
        else:
            loop.run_until_complete(close_all_clients())
    except Exception:
        pass

atexit.register(_cleanup)
signal.signal(signal.SIGTERM, lambda *args: _cleanup())