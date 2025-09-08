from shared.core.common_functions import create_circuit_breaker_config

"\nAdvanced Resilience System - Critical Infrastructure Component\nLocation: mcp_servers/base/resilience_system.py\n\nWeek 1 Critical Infrastructure Component:\n- Advanced circuit breaker pattern with multiple states\n- Intelligent retry logic with exponential backoff and jitter\n- Bulkhead pattern for resource isolation\n- Timeout management with adaptive thresholds\n- Health monitoring and auto-recovery\n- Fallback mechanisms and graceful degradation\n"
import asyncio
import logging
import random
import statistics
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, TypeVar

T = TypeVar("T")

class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class RetryStrategy(Enum):
    """Retry strategy types"""

    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    FIBONACCI_BACKOFF = "fibonacci_backoff"
    CUSTOM = "custom"

class FailureType(Enum):
    """Types of failures for different handling strategies"""

    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    HTTP_ERROR = "http_error"
    RATE_LIMIT = "rate_limit"
    SERVICE_UNAVAILABLE = "service_unavailable"
    AUTHENTICATION_ERROR = "authentication_error"
    UNKNOWN = "unknown"

@dataclass
class FailureWindow:
    """Sliding window for failure tracking"""

    failures: deque = field(default_factory=lambda: deque(maxlen=100))
    window_size_seconds: int = 60

    def add_failure(self, failure_type: FailureType, timestamp: datetime | None = None):
        """Add a failure to the window"""
        timestamp = timestamp or datetime.utcnow()
        self.failures.append({"timestamp": timestamp, "type": failure_type})

    def get_failure_rate(self, window_seconds: int | None = None) -> float:
        """Get failure rate within the specified window"""
        window_seconds = window_seconds or self.window_size_seconds
        cutoff_time = datetime.utcnow() - timedelta(seconds=window_seconds)
        recent_failures = [f for f in self.failures if f["timestamp"] > cutoff_time]
        total_requests = len(self.failures) if self.failures else 1
        return len(recent_failures) / total_requests if total_requests > 0 else 0.0

    def get_failure_count(self, window_seconds: int | None = None) -> int:
        """Get failure count within the specified window"""
        window_seconds = window_seconds or self.window_size_seconds
        cutoff_time = datetime.utcnow() - timedelta(seconds=window_seconds)
        return len([f for f in self.failures if f["timestamp"] > cutoff_time])

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""

    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_seconds: int = 60
    max_retry_attempts: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    jitter_enabled: bool = True
    failure_window_seconds: int = 60
    half_open_max_requests: int = 5
    adaptive_timeout: bool = True
    health_check_interval: int = 30
    bulkhead_max_concurrent: int = 10
    enable_fallback: bool = True

@dataclass
class ResilienceMetrics:
    """Comprehensive resilience metrics"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    circuit_breaker_opens: int = 0
    circuit_breaker_closes: int = 0
    total_retries: int = 0
    fallback_executions: int = 0
    bulkhead_rejections: int = 0
    timeout_errors: int = 0
    average_response_time: float = 0.0
    p95_response_time: float = 0.0
    current_state: CircuitState = CircuitState.CLOSED
    last_state_change: datetime = field(default_factory=datetime.utcnow)

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        return (
            self.successful_requests / self.total_requests * 100
            if self.total_requests > 0
            else 0.0
        )

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate percentage"""
        return (
            self.failed_requests / self.total_requests * 100
            if self.total_requests > 0
            else 0.0
        )

class RetryManager:
    """Advanced retry management with multiple strategies"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.fibonacci_cache = [1, 1]

    def calculate_delay(self, attempt: int, base_delay: float | None = None) -> float:
        """Calculate delay for retry attempt"""
        base_delay = base_delay or self.config.base_delay_seconds
        if self.config.retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = base_delay * 2**attempt
        elif self.config.retry_strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = base_delay * attempt
        elif self.config.retry_strategy == RetryStrategy.FIXED_DELAY:
            delay = base_delay
        elif self.config.retry_strategy == RetryStrategy.FIBONACCI_BACKOFF:
            delay = base_delay * self._get_fibonacci(attempt)
        else:
            delay = base_delay
        delay = min(delay, self.config.max_delay_seconds)
        if self.config.jitter_enabled:
            jitter = random.uniform(0.0, 0.3) * delay
            delay += jitter
        return delay

    def _get_fibonacci(self, n: int) -> int:
        """Get nth Fibonacci number with caching"""
        while len(self.fibonacci_cache) <= n:
            next_fib = self.fibonacci_cache[-1] + self.fibonacci_cache[-2]
            self.fibonacci_cache.append(next_fib)
        return (
            self.fibonacci_cache[n]
            if n < len(self.fibonacci_cache)
            else self.fibonacci_cache[-1]
        )

    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """Determine if request should be retried"""
        if attempt >= self.config.max_retry_attempts:
            return False
        failure_type = self._classify_failure(exception)
        non_retryable = {FailureType.AUTHENTICATION_ERROR}
        return failure_type not in non_retryable

    def _classify_failure(self, exception: Exception) -> FailureType:
        """Classify the type of failure"""
        exception_str = str(exception).lower()
        if "timeout" in exception_str:
            return FailureType.TIMEOUT
        elif "connection" in exception_str:
            return FailureType.CONNECTION_ERROR
        elif "rate limit" in exception_str or "429" in exception_str:
            return FailureType.RATE_LIMIT
        elif "503" in exception_str or "unavailable" in exception_str:
            return FailureType.SERVICE_UNAVAILABLE
        elif "401" in exception_str or "403" in exception_str:
            return FailureType.AUTHENTICATION_ERROR
        elif any(code in exception_str for code in ["400", "404", "500", "502", "504"]):
            return FailureType.HTTP_ERROR
        else:
            return FailureType.UNKNOWN

class BulkheadManager:
    """Bulkhead pattern implementation for resource isolation"""

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_requests = 0
        self.rejected_requests = 0

    async def acquire(self) -> bool:
        """Try to acquire a slot in the bulkhead"""
        if self.semaphore.locked():
            self.rejected_requests += 1
            return False
        await self.semaphore.acquire()
        self.active_requests += 1
        return True

    def release(self):
        """Release a slot in the bulkhead"""
        if self.active_requests > 0:
            self.active_requests -= 1
            self.semaphore.release()

    @property
    def utilization(self) -> float:
        """Get current utilization percentage"""
        return (
            self.active_requests / self.max_concurrent * 100
            if self.max_concurrent > 0
            else 0.0
        )

class AdaptiveTimeoutManager:
    """Adaptive timeout management based on historical performance"""

    def __init__(self, initial_timeout: float = 30.0, percentile: float = 95.0):
        self.initial_timeout = initial_timeout
        self.percentile = percentile
        self.response_times: deque = deque(maxlen=1000)
        self.current_timeout = initial_timeout
        self.min_timeout = 1.0
        self.max_timeout = 120.0

    def record_response_time(self, response_time: float):
        """Record a response time for timeout calculation"""
        self.response_times.append(response_time)
        self._update_timeout()

    def _update_timeout(self):
        """Update timeout based on historical response times"""
        if len(self.response_times) < 10:
            return
        p_value = statistics.quantiles(self.response_times, n=100)[
            int(self.percentile) - 1
        ]
        new_timeout = p_value * 2
        new_timeout = max(self.min_timeout, min(new_timeout, self.max_timeout))
        self.current_timeout = self.current_timeout * 0.7 + new_timeout * 0.3

    def get_timeout(self) -> float:
        """Get current adaptive timeout"""
        return self.current_timeout

class CircuitBreaker:
    """
    Advanced circuit breaker implementation with comprehensive resilience features.

    Features:
    - Multiple circuit states with intelligent transitions
    - Advanced retry strategies with jitter
    - Bulkhead pattern for resource isolation
    - Adaptive timeout management
    - Health monitoring and auto-recovery
    - Comprehensive metrics and monitoring
    """

    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_window = FailureWindow(
            window_size_seconds=config.failure_window_seconds
        )
        self.metrics = ResilienceMetrics()
        self.retry_manager = RetryManager(config)
        self.bulkhead = BulkheadManager(config.bulkhead_max_concurrent)
        self.timeout_manager = AdaptiveTimeoutManager(config.timeout_seconds)
        self.last_failure_time = None
        self.consecutive_successes = 0
        self.consecutive_failures = 0
        self.half_open_requests = 0
        self.fallback_functions: dict[str, Callable] = {}
        self._health_check_task: asyncio.Task | None = None
        self.logger = logging.getLogger(f"circuit_breaker.{name}")

    async def call(
        self, func: Callable[..., T], *args, fallback_key: str | None = None, **kwargs
    ) -> T:
        """Execute function with circuit breaker protection"""
        if not await self._can_make_request():
            if fallback_key and self.config.enable_fallback:
                return await self._execute_fallback(fallback_key, *args, **kwargs)
            else:
                raise CircuitBreakerOpenException(
                    f"Circuit breaker {self.name} is OPEN"
                )
        if not await self.bulkhead.acquire():
            self.metrics.bulkhead_rejections += 1
            raise BulkheadFullException(f"Bulkhead for {self.name} is full")
        start_time = time.time()
        attempt = 0
        last_exception = None
        try:
            while attempt <= self.config.max_retry_attempts:
                try:
                    self.metrics.total_requests += 1
                    timeout = self.timeout_manager.get_timeout()
                    result = await asyncio.wait_for(
                        func(*args, **kwargs), timeout=timeout
                    )
                    response_time = time.time() - start_time
                    self.timeout_manager.record_response_time(response_time)
                    await self._on_success(response_time)
                    return result
                except TimeoutError as e:
                    self.metrics.timeout_errors += 1
                    last_exception = e
                    await self._on_failure(FailureType.TIMEOUT)
                except Exception as e:
                    last_exception = e
                    failure_type = self.retry_manager._classify_failure(e)
                    await self._on_failure(failure_type)
                if not self.retry_manager.should_retry(attempt, last_exception):
                    break
                if attempt < self.config.max_retry_attempts:
                    delay = self.retry_manager.calculate_delay(attempt)
                    await asyncio.sleep(delay)
                    self.metrics.total_retries += 1
                attempt += 1
            if fallback_key and self.config.enable_fallback:
                return await self._execute_fallback(fallback_key, *args, **kwargs)
            else:
                raise last_exception
        finally:
            self.bulkhead.release()

    async def _can_make_request(self) -> bool:
        """Check if request can be made based on circuit state"""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            if (
                self.last_failure_time
                and datetime.utcnow() - self.last_failure_time
                > timedelta(seconds=self.config.timeout_seconds)
            ):
                await self._transition_to_half_open()
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            if self.half_open_requests < self.config.half_open_max_requests:
                self.half_open_requests += 1
                return True
            return False
        return False

    async def _on_success(self, response_time: float):
        """Handle successful request"""
        self.metrics.successful_requests += 1
        self.consecutive_successes += 1
        self.consecutive_failures = 0
        self._update_response_time_metrics(response_time)
        if self.state == CircuitState.HALF_OPEN:
            if self.consecutive_successes >= self.config.success_threshold:
                await self._transition_to_closed()
        self.logger.debug(f"Success recorded for {self.name}")

    async def _on_failure(self, failure_type: FailureType):
        """Handle failed request"""
        self.metrics.failed_requests += 1
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        self.last_failure_time = datetime.utcnow()
        self.failure_window.add_failure(failure_type)
        if self.state == CircuitState.CLOSED:
            if self.consecutive_failures >= self.config.failure_threshold:
                await self._transition_to_open()
        elif self.state == CircuitState.HALF_OPEN:
            await self._transition_to_open()
        self.logger.warning(f"Failure recorded for {self.name}: {failure_type.value}")

    async def _transition_to_open(self):
        """Transition circuit breaker to OPEN state"""
        self.state = CircuitState.OPEN
        self.metrics.circuit_breaker_opens += 1
        self.metrics.current_state = CircuitState.OPEN
        self.metrics.last_state_change = datetime.utcnow()
        self.half_open_requests = 0
        self.logger.warning(f"Circuit breaker {self.name} transitioned to OPEN")

    async def _transition_to_half_open(self):
        """Transition circuit breaker to HALF_OPEN state"""
        self.state = CircuitState.HALF_OPEN
        self.metrics.current_state = CircuitState.HALF_OPEN
        self.metrics.last_state_change = datetime.utcnow()
        self.half_open_requests = 0
        self.logger.info(f"Circuit breaker {self.name} transitioned to HALF_OPEN")

    async def _transition_to_closed(self):
        """Transition circuit breaker to CLOSED state"""
        self.state = CircuitState.CLOSED
        self.metrics.circuit_breaker_closes += 1
        self.metrics.current_state = CircuitState.CLOSED
        self.metrics.last_state_change = datetime.utcnow()
        self.consecutive_failures = 0
        self.half_open_requests = 0
        self.logger.info(f"Circuit breaker {self.name} transitioned to CLOSED")

    def _update_response_time_metrics(self, response_time: float):
        """Update response time metrics"""
        if self.metrics.average_response_time == 0:
            self.metrics.average_response_time = response_time
        else:
            self.metrics.average_response_time = (
                self.metrics.average_response_time * 0.9 + response_time * 0.1
            )

    async def _execute_fallback(self, fallback_key: str, *args, **kwargs):
        """Execute fallback function"""
        if fallback_key in self.fallback_functions:
            self.metrics.fallback_executions += 1
            fallback_func = self.fallback_functions[fallback_key]
            try:
                if asyncio.iscoroutinefunction(fallback_func):
                    return await fallback_func(*args, **kwargs)
                else:
                    return fallback_func(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Fallback execution failed: {e}")
                raise
        else:
            raise FallbackNotFound(
                f"No fallback function registered for key: {fallback_key}"
            )

    def register_fallback(self, key: str, fallback_func: Callable):
        """Register a fallback function"""
        self.fallback_functions[key] = fallback_func
        self.logger.info(f"Registered fallback function for key: {key}")

    def force_open(self):
        """Manually force circuit breaker to OPEN state"""
        asyncio.create_task(self._transition_to_open())
        self.logger.warning(f"Circuit breaker {self.name} manually forced to OPEN")

    def force_close(self):
        """Manually force circuit breaker to CLOSED state"""
        asyncio.create_task(self._transition_to_closed())
        self.logger.info(f"Circuit breaker {self.name} manually forced to CLOSED")

    def get_status(self) -> dict[str, Any]:
        """Get comprehensive circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "success_rate": self.metrics.success_rate,
                "failure_rate": self.metrics.failure_rate,
                "circuit_breaker_opens": self.metrics.circuit_breaker_opens,
                "total_retries": self.metrics.total_retries,
                "fallback_executions": self.metrics.fallback_executions,
                "bulkhead_rejections": self.metrics.bulkhead_rejections,
                "timeout_errors": self.metrics.timeout_errors,
                "average_response_time": self.metrics.average_response_time,
            },
            "configuration": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout_seconds": self.config.timeout_seconds,
                "max_retry_attempts": self.config.max_retry_attempts,
                "retry_strategy": self.config.retry_strategy.value,
            },
            "current_state": {
                "consecutive_successes": self.consecutive_successes,
                "consecutive_failures": self.consecutive_failures,
                "failure_rate_window": self.failure_window.get_failure_rate(),
                "last_failure_time": (
                    self.last_failure_time.isoformat()
                    if self.last_failure_time
                    else None
                ),
                "adaptive_timeout": self.timeout_manager.get_timeout(),
                "bulkhead_utilization": self.bulkhead.utilization,
            },
        }

class ResilienceManager:
    """
    Centralized resilience management for all circuit breakers.

    Provides:
    - Circuit breaker registry and management
    - Global resilience policies
    - Cross-service coordination
    - Comprehensive monitoring and alerting
    """

    def __init__(self):
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.global_config = CircuitBreakerConfig()
        self.logger = logging.getLogger("resilience_manager")

    def create_circuit_breaker(
        self, name: str, config: CircuitBreakerConfig | None = None
    ) -> CircuitBreaker:
        """Create and register a new circuit breaker"""
        config = config or self.global_config
        if name in self.circuit_breakers:
            self.logger.warning(
                f"Circuit breaker {name} already exists, returning existing instance"
            )
            return self.circuit_breakers[name]
        circuit_breaker = CircuitBreaker(name, config)
        self.circuit_breakers[name] = circuit_breaker
        self.logger.info(f"Created circuit breaker: {name}")
        return circuit_breaker

    def get_circuit_breaker(self, name: str) -> CircuitBreaker | None:
        """Get circuit breaker by name"""
        return self.circuit_breakers.get(name)

    def remove_circuit_breaker(self, name: str) -> bool:
        """Remove circuit breaker"""
        if name in self.circuit_breakers:
            del self.circuit_breakers[name]
            self.logger.info(f"Removed circuit breaker: {name}")
            return True
        return False

    def get_global_status(self) -> dict[str, Any]:
        """Get global resilience system status"""
        total_requests = sum(
            cb.metrics.total_requests for cb in self.circuit_breakers.values()
        )
        total_failures = sum(
            cb.metrics.failed_requests for cb in self.circuit_breakers.values()
        )
        open_breakers = [
            name
            for name, cb in self.circuit_breakers.items()
            if cb.state == CircuitState.OPEN
        ]
        return {
            "circuit_breakers_count": len(self.circuit_breakers),
            "open_circuit_breakers": open_breakers,
            "global_metrics": {
                "total_requests": total_requests,
                "total_failures": total_failures,
                "global_success_rate": (
                    (total_requests - total_failures) / total_requests * 100
                    if total_requests > 0
                    else 0
                ),
                "total_circuit_opens": sum(
                    cb.metrics.circuit_breaker_opens
                    for cb in self.circuit_breakers.values()
                ),
                "total_fallback_executions": sum(
                    cb.metrics.fallback_executions
                    for cb in self.circuit_breakers.values()
                ),
            },
            "circuit_breakers": {
                name: cb.get_status() for name, cb in self.circuit_breakers.items()
            },
        }

    async def health_check_all(self) -> dict[str, bool]:
        """Perform health check on all circuit breakers"""
        health_status = {}
        for name, cb in self.circuit_breakers.items():
            is_healthy = (
                cb.state != CircuitState.OPEN
                and cb.metrics.success_rate > 50.0
                and (cb.consecutive_failures < cb.config.failure_threshold)
            )
            health_status[name] = is_healthy
        return health_status

class CircuitBreakerException(Exception):
    """Base exception for circuit breaker errors"""


class CircuitBreakerOpenException(CircuitBreakerException):
    """Exception raised when circuit breaker is open"""


class BulkheadFullException(CircuitBreakerException):
    """Exception raised when bulkhead is full"""


class FallbackNotFound(CircuitBreakerException):
    """Exception raised when fallback function is not found"""


__all__ = [
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "ResilienceManager",
    "CircuitState",
    "RetryStrategy",
    "FailureType",
    "ResilienceMetrics",
    "CircuitBreakerException",
    "CircuitBreakerOpenException",
    "BulkheadFullException",
    "create_circuit_breaker_config",
]
"""
resilience_system.py - Syntax errors fixed
This file had severe syntax errors and was replaced with a minimal valid structure.
"""

