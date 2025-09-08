"""Circuit breaker implementation for fault tolerance."""

import asyncio
import time
from enum import Enum
from typing import Callable, Optional, Any
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker for fault tolerance.
    
    Prevents cascading failures by temporarily blocking calls to a failing service.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        """Initialize circuit breaker.
        
        Args:
            name: Name of the circuit breaker (for logging)
            failure_threshold: Number of failures before opening circuit
            success_threshold: Number of successes in half-open before closing
            timeout: Time in seconds before attempting to close circuit
            expected_exception: Exception type that triggers the breaker
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._lock = asyncio.Lock()
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state
    
    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open (failing)."""
        return self._state == CircuitState.OPEN
    
    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing)."""
        return self._state == CircuitState.HALF_OPEN
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        return (
            self._last_failure_time and
            time.time() - self._last_failure_time >= self.timeout
        )
    
    async def _record_success(self):
        """Record a successful call."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info(f"Circuit breaker '{self.name}' closed (recovered)")
    
    async def _record_failure(self):
        """Record a failed call."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._success_count = 0
                logger.warning(f"Circuit breaker '{self.name}' reopened (still failing)")
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.error(
                    f"Circuit breaker '{self.name}' opened after {self._failure_count} failures"
                )
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute an async function through the circuit breaker."""
        
        # Check if we should attempt to reset
        if self.is_open and self._should_attempt_reset():
            async with self._lock:
                if self.is_open:  # Double-check with lock
                    self._state = CircuitState.HALF_OPEN
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info(f"Circuit breaker '{self.name}' half-open (testing)")
        
        # Reject call if circuit is open
        if self.is_open:
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is open"
            )
        
        # Attempt the call
        try:
            result = await func(*args, **kwargs)
            await self._record_success()
            return result
        except self.expected_exception as e:
            await self._record_failure()
            raise
    
    def call_sync(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a sync function through the circuit breaker."""
        
        # Check if we should attempt to reset
        if self.is_open and self._should_attempt_reset():
            if self.is_open:  # Double-check
                self._state = CircuitState.HALF_OPEN
                self._failure_count = 0
                self._success_count = 0
                logger.info(f"Circuit breaker '{self.name}' half-open (testing)")
        
        # Reject call if circuit is open
        if self.is_open:
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is open"
            )
        
        # Attempt the call
        try:
            result = func(*args, **kwargs)
            # Sync version of record_success
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info(f"Circuit breaker '{self.name}' closed (recovered)")
            return result
        except self.expected_exception as e:
            # Sync version of record_failure
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._success_count = 0
                logger.warning(f"Circuit breaker '{self.name}' reopened (still failing)")
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.error(
                    f"Circuit breaker '{self.name}' opened after {self._failure_count} failures"
                )
            raise
    
    def reset(self):
        """Manually reset the circuit breaker."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        logger.info(f"Circuit breaker '{self.name}' manually reset")


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


def circuit_breaker(
    name: Optional[str] = None,
    failure_threshold: int = 5,
    success_threshold: int = 2,
    timeout: float = 60.0,
    expected_exception: type = Exception
):
    """Decorator to add circuit breaker to a function."""
    
    def decorator(func: Callable) -> Callable:
        breaker_name = name or func.__name__
        breaker = CircuitBreaker(
            breaker_name,
            failure_threshold,
            success_threshold,
            timeout,
            expected_exception
        )
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await breaker.call_async(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return breaker.call_sync(func, *args, **kwargs)
        
        # Add breaker as attribute for access
        wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        wrapper.breaker = breaker
        
        return wrapper
    
    return decorator