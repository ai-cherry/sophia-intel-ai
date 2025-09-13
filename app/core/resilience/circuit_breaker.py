"""
Circuit Breaker Pattern Implementation
Implements circuit breaker with states (CLOSED, OPEN, HALF_OPEN)
Includes failure threshold configuration and recovery timeout
"""
import asyncio
import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional, TypeVar
logger = logging.getLogger(__name__)
T = TypeVar("T")
class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"  # Circuit broken, requests fail immediately
    HALF_OPEN = "half_open"  # Testing if service has recovered
@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    # Failure thresholds
    failure_threshold: int = 5  # Number of failures to open circuit
    success_threshold: int = 2  # Number of successes to close circuit from half-open
    failure_rate_threshold: float = 0.5  # Failure rate to open circuit
    # Timing configuration
    timeout: int = 60  # Seconds before attempting recovery
    monitoring_window: int = 60  # Seconds to monitor failure rate
    # Half-open configuration
    half_open_requests: int = 3  # Max requests in half-open state
    # Optional callbacks
    on_open: Optional[Callable[[], None]] = None
    on_close: Optional[Callable[[], None]] = None
    on_half_open: Optional[Callable[[], None]] = None
class CircuitBreaker:
    """
    Circuit breaker implementation for fault tolerance
    The circuit breaker prevents cascading failures by failing fast when a service
    is experiencing issues. It has three states:
    - CLOSED: Normal operation
    - OPEN: Service is down, fail immediately
    - HALF_OPEN: Testing if service has recovered
    """
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize circuit breaker
        Args:
            name: Name of the circuit breaker (for logging)
            config: Configuration for circuit breaker behavior
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        # State management
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.utcnow()
        # Request tracking
        self.request_history: deque = deque(maxlen=100)
        self.half_open_attempts = 0
        # Statistics
        self.total_requests = 0
        self.total_failures = 0
        self.total_successes = 0
        self.state_changes = []
        # Lock for thread safety
        self._lock = asyncio.Lock()
        logger.info(f"Circuit breaker '{name}' initialized in CLOSED state")
    async def call(
        self,
        func: Callable[..., T],
        *args,
        fallback: Optional[Callable[..., T]] = None,
        **kwargs,
    ) -> T:
        """
        Execute function through circuit breaker
        Args:
            func: Function to execute
            *args: Arguments for function
            fallback: Optional fallback function if circuit is open
            **kwargs: Keyword arguments for function
        Returns:
            Function result or fallback result
        Raises:
            Exception: If circuit is open and no fallback provided
        """
        async with self._lock:
            self.total_requests += 1
            # Check circuit state
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    logger.warning(f"Circuit breaker '{self.name}' is OPEN")
                    if fallback:
                        return await self._execute_fallback(fallback, *args, **kwargs)
                    raise CircuitBreakerOpenException(
                        f"Circuit breaker '{self.name}' is OPEN"
                    )
            # In HALF_OPEN state, limit concurrent attempts
            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_attempts >= self.config.half_open_requests:
                    logger.warning(
                        f"Circuit breaker '{self.name}' HALF_OPEN request limit reached"
                    )
                    if fallback:
                        return await self._execute_fallback(fallback, *args, **kwargs)
                    raise CircuitBreakerOpenException(
                        f"Circuit breaker '{self.name}' is testing recovery"
                    )
                self.half_open_attempts += 1
        # Execute the function
        try:
            # Support both sync and async functions
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise e
    async def _execute_fallback(self, fallback: Callable[..., T], *args, **kwargs) -> T:
        """Execute fallback function"""
        if asyncio.iscoroutinefunction(fallback):
            return await fallback(*args, **kwargs)
        return fallback(*args, **kwargs)
    async def _on_success(self):
        """Handle successful call"""
        async with self._lock:
            self.total_successes += 1
            self.request_history.append((datetime.utcnow(), True))
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                logger.debug(
                    f"Circuit breaker '{self.name}' HALF_OPEN success "
                    f"({self.success_count}/{self.config.success_threshold})"
                )
                if self.success_count >= self.config.success_threshold:
                    self._transition_to_closed()
            elif self.state == CircuitState.CLOSED:
                # Decay failure count on success
                self.failure_count = max(0, self.failure_count - 1)
    async def _on_failure(self):
        """Handle failed call"""
        async with self._lock:
            self.total_failures += 1
            self.last_failure_time = datetime.utcnow()
            self.request_history.append((self.last_failure_time, False))
            self.failure_count += 1
            logger.debug(
                f"Circuit breaker '{self.name}' failure "
                f"({self.failure_count}/{self.config.failure_threshold})"
            )
            if self.state == CircuitState.HALF_OPEN:
                # Single failure in HALF_OPEN reopens circuit
                self._transition_to_open()
            elif self.state == CircuitState.CLOSED and self._should_open_circuit():
                self._transition_to_open()
    def _should_open_circuit(self) -> bool:
        """Determine if circuit should open based on failures"""
        # Check absolute failure threshold
        if self.failure_count >= self.config.failure_threshold:
            return True
        # Check failure rate in monitoring window
        recent_requests = [
            success
            for timestamp, success in self.request_history
            if (datetime.utcnow() - timestamp).total_seconds()
            <= self.config.monitoring_window
        ]
        if len(recent_requests) >= 10:  # Minimum sample size
            failure_rate = recent_requests.count(False) / len(recent_requests)
            if failure_rate >= self.config.failure_rate_threshold:
                logger.debug(
                    f"Circuit breaker '{self.name}' failure rate {failure_rate:.2%} "
                    f"exceeds threshold {self.config.failure_rate_threshold:.2%}"
                )
                return True
        return False
    def _should_attempt_reset(self) -> bool:
        """Determine if circuit should attempt reset from OPEN state"""
        if not self.last_failure_time:
            return True
        time_since_failure = (
            datetime.utcnow() - self.last_failure_time
        ).total_seconds()
        return time_since_failure >= self.config.timeout
    def _transition_to_open(self):
        """Transition to OPEN state"""
        self.state = CircuitState.OPEN
        self.last_state_change = datetime.utcnow()
        self.state_changes.append((self.last_state_change, CircuitState.OPEN))
        logger.warning(f"Circuit breaker '{self.name}' transitioned to OPEN")
        if self.config.on_open:
            try:
                self.config.on_open()
            except Exception as e:
                logger.error(f"Error in on_open callback: {e}")
    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        self.state = CircuitState.CLOSED
        self.last_state_change = datetime.utcnow()
        self.state_changes.append((self.last_state_change, CircuitState.CLOSED))
        # Reset counters
        self.failure_count = 0
        self.success_count = 0
        self.half_open_attempts = 0
        logger.info(f"Circuit breaker '{self.name}' transitioned to CLOSED")
        if self.config.on_close:
            try:
                self.config.on_close()
            except Exception as e:
                logger.error(f"Error in on_close callback: {e}")
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        self.state = CircuitState.HALF_OPEN
        self.last_state_change = datetime.utcnow()
        self.state_changes.append((self.last_state_change, CircuitState.HALF_OPEN))
        # Reset counters for testing
        self.success_count = 0
        self.half_open_attempts = 0
        logger.info(f"Circuit breaker '{self.name}' transitioned to HALF_OPEN")
        if self.config.on_half_open:
            try:
                self.config.on_half_open()
            except Exception as e:
                logger.error(f"Error in on_half_open callback: {e}")
    def get_status(self) -> dict[str, Any]:
        """
        Get current circuit breaker status
        Returns:
            Dictionary with status information
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_requests": self.total_requests,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "last_failure": (
                self.last_failure_time.isoformat() if self.last_failure_time else None
            ),
            "last_state_change": self.last_state_change.isoformat(),
            "uptime": (datetime.utcnow() - self.last_state_change).total_seconds(),
            "success_rate": (
                (self.total_successes / max(self.total_requests, 1))
                if self.total_requests > 0
                else 0.0
            ),
        }
    def reset(self):
        """Reset circuit breaker to initial state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_attempts = 0
        self.last_failure_time = None
        self.last_state_change = datetime.utcnow()
        self.request_history.clear()
        logger.info(f"Circuit breaker '{self.name}' reset to CLOSED state")
    def force_open(self):
        """Force circuit breaker to OPEN state (for testing/maintenance)"""
        self._transition_to_open()
    def force_close(self):
        """Force circuit breaker to CLOSED state (for testing/recovery)"""
        self._transition_to_closed()
class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open"""
    pass
class CircuitBreakerGroup:
    """
    Manages a group of circuit breakers
    Useful for coordinating multiple related services
    """
    def __init__(self, name: str):
        """
        Initialize circuit breaker group
        Args:
            name: Name of the group
        """
        self.name = name
        self.breakers: dict[str, CircuitBreaker] = {}
        logger.info(f"Circuit breaker group '{name}' initialized")
    def add_breaker(
        self, name: str, config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """
        Add a circuit breaker to the group
        Args:
            name: Name of the circuit breaker
            config: Configuration for the breaker
        Returns:
            The created circuit breaker
        """
        breaker = CircuitBreaker(f"{self.name}.{name}", config)
        self.breakers[name] = breaker
        return breaker
    def get_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get a circuit breaker by name"""
        return self.breakers.get(name)
    def get_status(self) -> dict[str, Any]:
        """Get status of all circuit breakers in the group"""
        return {
            "group": self.name,
            "breakers": {
                name: breaker.get_status() for name, breaker in self.breakers.items()
            },
            "summary": {
                "total": len(self.breakers),
                "open": sum(
                    1 for b in self.breakers.values() if b.state == CircuitState.OPEN
                ),
                "closed": sum(
                    1 for b in self.breakers.values() if b.state == CircuitState.CLOSED
                ),
                "half_open": sum(
                    1
                    for b in self.breakers.values()
                    if b.state == CircuitState.HALF_OPEN
                ),
            },
        }
    def reset_all(self):
        """Reset all circuit breakers in the group"""
        for breaker in self.breakers.values():
            breaker.reset()
    def force_open_all(self):
        """Force all circuit breakers to OPEN state"""
        for breaker in self.breakers.values():
            breaker.force_open()
