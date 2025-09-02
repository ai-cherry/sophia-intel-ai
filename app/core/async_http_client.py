"""
Ultra-Performance Async HTTP Client with Circuit Breakers
Part of 2025 Architecture - Complete HTTPX Migration
Replaces all blocking requests with async patterns
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List, Union, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
import httpx
from contextlib import asynccontextmanager
import orjson

# Setup logging
logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking all requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: type = httpx.HTTPError
    success_threshold: int = 2
    timeout: float = 30.0


@dataclass
class CircuitBreaker:
    """
    Circuit breaker implementation for fault tolerance
    Prevents cascading failures in distributed systems
    """
    name: str
    config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    
    def __post_init__(self):
        self._lock = asyncio.Lock()
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit {self.name} entering HALF_OPEN state")
                else:
                    raise Exception(f"Circuit breaker {self.name} is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except self.config.expected_exception as e:
            await self._on_failure()
            raise
    
    async def _on_success(self):
        """Handle successful call"""
        async with self._lock:
            self.failure_count = 0
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.success_count = 0
                    logger.info(f"Circuit {self.name} recovered to CLOSED state")
    
    async def _on_failure(self):
        """Handle failed call"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            self.success_count = 0
            
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit {self.name} tripped to OPEN state after {self.failure_count} failures")
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset"""
        if self.last_failure_time is None:
            return False
        return (time.time() - self.last_failure_time) >= self.config.recovery_timeout
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure": self.last_failure_time
        }


class AsyncHTTPClient:
    """
    Ultra-performance async HTTP client with connection pooling and circuit breakers
    Replaces all requests.get/post calls with async patterns
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        enable_circuit_breaker: bool = True
    ):
        self.base_url = base_url
        self.timeout = timeout
        
        # Connection pooling configuration
        limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
            keepalive_expiry=30.0
        )
        
        # HTTP/2 support for better performance
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout),
            limits=limits,
            http2=True,
            follow_redirects=True
        )
        
        # Circuit breakers for different services
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.enable_circuit_breaker = enable_circuit_breaker
        
        # Performance metrics
        self.metrics = {
            "total_requests": 0,
            "failed_requests": 0,
            "avg_latency_ms": 0.0,
            "circuit_trips": 0
        }
    
    def _get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for service"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker(
                name=service_name,
                config=CircuitBreakerConfig(
                    failure_threshold=5,
                    recovery_timeout=60.0,
                    timeout=self.timeout
                )
            )
        return self.circuit_breakers[service_name]
    
    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        service_name: str = "default",
        **kwargs
    ) -> httpx.Response:
        """
        Async GET request with circuit breaker
        Replaces requests.get()
        """
        start = time.perf_counter()
        
        async def _make_request():
            return await self.client.get(url, params=params, headers=headers, **kwargs)
        
        try:
            if self.enable_circuit_breaker:
                breaker = self._get_circuit_breaker(service_name)
                response = await breaker.call(_make_request)
            else:
                response = await _make_request()
            
            # Update metrics
            latency = (time.perf_counter() - start) * 1000
            self._update_metrics(latency, success=True)
            
            return response
            
        except Exception as e:
            self._update_metrics(0, success=False)
            if "Circuit breaker" in str(e):
                self.metrics["circuit_trips"] += 1
            raise
    
    async def post(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        service_name: str = "default",
        **kwargs
    ) -> httpx.Response:
        """
        Async POST request with circuit breaker
        Replaces requests.post()
        """
        start = time.perf_counter()
        
        async def _make_request():
            return await self.client.post(
                url, json=json, data=data, headers=headers, **kwargs
            )
        
        try:
            if self.enable_circuit_breaker:
                breaker = self._get_circuit_breaker(service_name)
                response = await breaker.call(_make_request)
            else:
                response = await _make_request()
            
            # Update metrics
            latency = (time.perf_counter() - start) * 1000
            self._update_metrics(latency, success=True)
            
            return response
            
        except Exception as e:
            self._update_metrics(0, success=False)
            if "Circuit breaker" in str(e):
                self.metrics["circuit_trips"] += 1
            raise
    
    async def stream(
        self,
        method: str,
        url: str,
        service_name: str = "default",
        **kwargs
    ) -> AsyncIterator[bytes]:
        """
        Stream response for large payloads
        Supports SSE and chunked responses
        """
        async with self.client.stream(method, url, **kwargs) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes(chunk_size=8192):
                yield chunk
    
    async def batch_request(
        self,
        requests: List[Dict[str, Any]],
        max_concurrent: int = 10
    ) -> List[httpx.Response]:
        """
        Execute multiple requests concurrently with rate limiting
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def _execute_request(req: Dict[str, Any]):
            async with semaphore:
                method = req.get("method", "GET")
                url = req["url"]
                
                if method.upper() == "GET":
                    return await self.get(url, **req.get("kwargs", {}))
                elif method.upper() == "POST":
                    return await self.post(url, **req.get("kwargs", {}))
                else:
                    raise ValueError(f"Unsupported method: {method}")
        
        tasks = [_execute_request(req) for req in requests]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def _update_metrics(self, latency: float, success: bool):
        """Update performance metrics"""
        self.metrics["total_requests"] += 1
        if not success:
            self.metrics["failed_requests"] += 1
        
        if latency > 0:
            # Calculate running average
            total = self.metrics["total_requests"]
            avg = self.metrics["avg_latency_ms"]
            self.metrics["avg_latency_ms"] = (avg * (total - 1) + latency) / total
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics and circuit breaker status"""
        return {
            **self.metrics,
            "circuit_breakers": {
                name: breaker.get_status()
                for name, breaker in self.circuit_breakers.items()
            }
        }
    
    async def close(self):
        """Close HTTP client and cleanup resources"""
        await self.client.aclose()


class APIClientPool:
    """
    Pool of API clients for different services
    Manages connections to OpenRouter, Together, Anthropic, etc.
    """
    
    def __init__(self):
        self.clients: Dict[str, AsyncHTTPClient] = {}
        self._lock = asyncio.Lock()
    
    @asynccontextmanager
    async def get_client(
        self,
        service: str,
        base_url: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[AsyncHTTPClient]:
        """Get or create client for service"""
        async with self._lock:
            if service not in self.clients:
                self.clients[service] = AsyncHTTPClient(
                    base_url=base_url,
                    **kwargs
                )
        
        try:
            yield self.clients[service]
        finally:
            pass  # Keep connection alive for reuse
    
    async def close_all(self):
        """Close all clients"""
        for client in self.clients.values():
            await client.close()
        self.clients.clear()


# Global client pool for singleton pattern
_client_pool = APIClientPool()


async def get_http_client(
    service: str = "default",
    base_url: Optional[str] = None
) -> AsyncHTTPClient:
    """Get HTTP client for service"""
    async with _client_pool.get_client(service, base_url) as client:
        return client


# Migration helpers for easy replacement
async def async_get(url: str, **kwargs) -> httpx.Response:
    """Drop-in replacement for requests.get()"""
    client = AsyncHTTPClient()
    try:
        return await client.get(url, **kwargs)
    finally:
        await client.close()


async def async_post(url: str, **kwargs) -> httpx.Response:
    """Drop-in replacement for requests.post()"""
    client = AsyncHTTPClient()
    try:
        return await client.post(url, **kwargs)
    finally:
        await client.close()


# Example usage showing migration from requests to httpx
if __name__ == "__main__":
    async def example_migration():
        # Old way with requests (blocking):
        # response = requests.get("https://api.example.com/data")
        # data = response.json()
        
        # New way with async httpx:
        client = AsyncHTTPClient()
        
        # Single request
        response = await client.get("https://api.example.com/data")
        data = response.json()
        
        # Batch requests with concurrency control
        batch_requests = [
            {"url": "https://api.example.com/item/1"},
            {"url": "https://api.example.com/item/2"},
            {"url": "https://api.example.com/item/3"},
        ]
        responses = await client.batch_request(batch_requests, max_concurrent=2)
        
        # Check metrics and circuit breaker status
        print(client.get_metrics())
        
        await client.close()
    
    # Run example
    asyncio.run(example_migration())