"""
Enhanced Circuit Breaker Implementation
Provides resilience for all external service calls
Addresses critical reliability issues identified in architectural audit
"""

import asyncio
import time
import logging
from typing import Callable, Optional, Dict, Any, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import functools

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Blocking calls due to failures
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5          # Failures before opening
    success_threshold: int = 2          # Successes in half-open before closing
    timeout: float = 60.0               # Seconds before trying half-open
    expected_exception: type = Exception  # Exception types to catch
    exclude_exceptions: tuple = ()       # Exceptions to not catch
    
    # Advanced settings
    failure_rate_threshold: float = 0.5  # Failure rate to open circuit
    slow_call_duration: float = 5.0     # Seconds to consider call slow
    slow_call_rate_threshold: float = 0.5  # Slow call rate to open
    minimum_calls: int = 10             # Min calls before calculating rates
    sliding_window_size: int = 100      # Size of sliding window


@dataclass
class CallMetrics:
    """Metrics for a single call"""
    timestamp: datetime
    duration: float
    success: bool
    exception: Optional[Exception] = None


class CircuitBreaker(Generic[T]):
    """
    Advanced circuit breaker with sliding window and multiple failure conditions
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_state_change: datetime = datetime.now()
        
        # Sliding window for metrics
        self.call_metrics: deque[CallMetrics] = deque(maxlen=self.config.sliding_window_size)
        
        # Statistics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection"""
        async with self._lock:
            # Check if circuit should be opened
            if self.state == CircuitState.OPEN:
                if await self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
                else:
                    raise CircuitOpenException(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Retry after {self._time_until_retry():.1f} seconds"
                    )
        
        # Execute the function
        start_time = time.monotonic()
        try:
            # Handle both sync and async functions
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = await asyncio.to_thread(func, *args, **kwargs)
            
            duration = time.monotonic() - start_time
            await self._on_success(duration)
            return result
            
        except self.config.exclude_exceptions:
            # Don't count excluded exceptions as failures
            raise
            
        except self.config.expected_exception as e:
            duration = time.monotonic() - start_time
            await self._on_failure(e, duration)
            raise
    
    async def _on_success(self, duration: float):
        """Handle successful call"""
        async with self._lock:
            self.total_calls += 1
            self.total_successes += 1
            self.consecutive_successes += 1
            self.consecutive_failures = 0
            
            # Add to metrics
            self.call_metrics.append(CallMetrics(
                timestamp=datetime.now(),
                duration=duration,
                success=True
            ))
            
            # State transitions
            if self.state == CircuitState.HALF_OPEN:
                if self.consecutive_successes >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    logger.info(f"Circuit breaker '{self.name}' closed after recovery")
            
            elif self.state == CircuitState.CLOSED:
                # Check if we should open based on slow calls
                if await self._should_open_for_slow_calls():
                    self._open_circuit("slow call rate exceeded")
    
    async def _on_failure(self, exception: Exception, duration: float):
        """Handle failed call"""
        async with self._lock:
            self.total_calls += 1
            self.total_failures += 1
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            self.last_failure_time = time.time()
            
            # Add to metrics
            self.call_metrics.append(CallMetrics(
                timestamp=datetime.now(),
                duration=duration,
                success=False,
                exception=exception
            ))
            
            # State transitions
            if self.state == CircuitState.HALF_OPEN:
                self._open_circuit("failure in half-open state")
            
            elif self.state == CircuitState.CLOSED:
                self.failure_count += 1
                
                # Check multiple failure conditions
                if self.consecutive_failures >= self.config.failure_threshold:
                    self._open_circuit("consecutive failure threshold exceeded")
                elif await self._should_open_for_failure_rate():
                    self._open_circuit("failure rate threshold exceeded")
    
    def _open_circuit(self, reason: str):
        """Open the circuit breaker"""
        self.state = CircuitState.OPEN
        self.last_state_change = datetime.now()
        self.failure_count = 0
        self.success_count = 0
        self.consecutive_successes = 0
        logger.warning(f"Circuit breaker '{self.name}' opened: {reason}")
    
    async def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try half-open"""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.config.timeout
    
    async def _should_open_for_failure_rate(self) -> bool:
        """Check if failure rate exceeds threshold"""
        if len(self.call_metrics) < self.config.minimum_calls:
            return False
        
        recent_metrics = list(self.call_metrics)
        failures = sum(1 for m in recent_metrics if not m.success)
        failure_rate = failures / len(recent_metrics)
        
        return failure_rate >= self.config.failure_rate_threshold
    
    async def _should_open_for_slow_calls(self) -> bool:
        """Check if slow call rate exceeds threshold"""
        if len(self.call_metrics) < self.config.minimum_calls:
            return False
        
        recent_metrics = list(self.call_metrics)
        slow_calls = sum(
            1 for m in recent_metrics 
            if m.duration >= self.config.slow_call_duration
        )
        slow_rate = slow_calls / len(recent_metrics)
        
        return slow_rate >= self.config.slow_call_rate_threshold
    
    def _time_until_retry(self) -> float:
        """Calculate seconds until retry is allowed"""
        if self.last_failure_time is None:
            return 0.0
        
        time_since_failure = time.time() - self.last_failure_time
        return max(0, self.config.timeout - time_since_failure)
    
    # Manual control methods
    
    async def open(self):
        """Manually open the circuit"""
        async with self._lock:
            self._open_circuit("manual open")
    
    async def close(self):
        """Manually close the circuit"""
        async with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.consecutive_failures = 0
            self.consecutive_successes = 0
            logger.info(f"Circuit breaker '{self.name}' manually closed")
    
    async def reset(self):
        """Reset all statistics"""
        async with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.total_calls = 0
            self.total_failures = 0
            self.total_successes = 0
            self.consecutive_failures = 0
            self.consecutive_successes = 0
            self.call_metrics.clear()
            self.last_failure_time = None
            logger.info(f"Circuit breaker '{self.name}' reset")
    
    # Monitoring methods
    
    def get_state(self) -> Dict[str, Any]:
        """Get current state and metrics"""
        success_rate = (
            self.total_successes / self.total_calls 
            if self.total_calls > 0 else 0
        )
        
        return {
            "name": self.name,
            "state": self.state.value,
            "total_calls": self.total_calls,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "success_rate": success_rate,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "last_state_change": self.last_state_change.isoformat(),
            "metrics_window_size": len(self.call_metrics)
        }


class CircuitOpenException(Exception):
    """Exception raised when circuit is open"""
    pass


class CircuitBreakerManager:
    """
    Manages multiple circuit breakers for different services
    """
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._default_config = CircuitBreakerConfig()
    
    def get_or_create(
        self, 
        name: str, 
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Get existing or create new circuit breaker"""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                name, 
                config or self._default_config
            )
        return self._breakers[name]
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        return self._breakers.get(name)
    
    async def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self._breakers.values():
            await breaker.reset()
    
    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all circuit breakers"""
        return {
            name: breaker.get_state() 
            for name, breaker in self._breakers.items()
        }
    
    def get_open_circuits(self) -> List[str]:
        """Get list of open circuits"""
        return [
            name for name, breaker in self._breakers.items()
            if breaker.state == CircuitState.OPEN
        ]


# Global circuit breaker manager
_circuit_manager = CircuitBreakerManager()


def get_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None
) -> CircuitBreaker:
    """Get or create a circuit breaker"""
    return _circuit_manager.get_or_create(name, config)


# Decorator for adding circuit breaker to functions
def with_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None
):
    """Decorator to add circuit breaker protection to a function"""
    def decorator(func):
        breaker = get_circuit_breaker(name, config)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return asyncio.run(breaker.call(func, *args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Pre-configured circuit breakers for common services

def get_llm_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker for LLM API calls"""
    return get_circuit_breaker("llm", CircuitBreakerConfig(
        failure_threshold=3,
        timeout=30,
        slow_call_duration=10,
        expected_exception=(Exception,)
    ))


def get_weaviate_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker for Weaviate queries"""
    return get_circuit_breaker("weaviate", CircuitBreakerConfig(
        failure_threshold=5,
        timeout=20,
        slow_call_duration=3,
        expected_exception=(Exception,)
    ))


def get_redis_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker for Redis operations"""  
    return get_circuit_breaker("redis", CircuitBreakerConfig(
        failure_threshold=10,
        timeout=10,
        slow_call_duration=1,
        expected_exception=(Exception,)
    ))


def get_webhook_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker for webhook calls"""
    return get_circuit_breaker("webhook", CircuitBreakerConfig(
        failure_threshold=3,
        timeout=60,
        slow_call_duration=5,
        expected_exception=(Exception,)
    ))