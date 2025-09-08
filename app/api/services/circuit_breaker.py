"""
Sophia AI Platform v4.0 - Circuit Breaker Implementation
Intelligent circuit breaker for external services with smart recovery
"""

import asyncio
import json
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""

    failure_threshold: int = 5
    recovery_timeout: int = 60
    success_threshold: int = 3  # For half-open state
    timeout: float = 30.0
    expected_exception: type = Exception


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics"""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    circuit_opens: int = 0
    last_failure_time: Optional[float] = None
    current_state: CircuitState = CircuitState.CLOSED
    failures: deque = field(default_factory=lambda: deque(maxlen=10))


class CircuitBreakerError(Exception):
    """Circuit breaker specific exception"""


class CircuitOpenError(CircuitBreakerError):
    """Raised when circuit is open"""


class CircuitBreaker:
    """
    Intelligent circuit breaker with adaptive recovery and comprehensive monitoring
    """

    def __init__(
        self, name: str = "default", config: Optional[CircuitBreakerConfig] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()

        logger.info(f"🔌 Circuit breaker '{name}' initialized")

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitOpenError: When circuit is open
            Original exception: When function fails
        """
        async with self._lock:
            self.stats.total_calls += 1

            # Check circuit state
            if self.stats.current_state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.stats.current_state = CircuitState.HALF_OPEN
                    logger.info(f"🔄 Circuit '{self.name}' moving to HALF_OPEN")
                else:
                    self.stats.failed_calls += 1
                    raise CircuitOpenError(f"Circuit '{self.name}' is OPEN")

            try:
                # Execute function with timeout
                result = await asyncio.wait_for(
                    self._execute_function(func, *args, **kwargs),
                    timeout=self.config.timeout,
                )

                # Handle success
                await self._on_success()
                return result

            except asyncio.TimeoutError as e:
                await self._on_failure(e)
                raise
            except self.config.expected_exception as e:
                await self._on_failure(e)
                raise
            except Exception as e:
                # Unexpected exception, don't count as circuit failure
                logger.warning(f"Unexpected exception in circuit '{self.name}': {e}")
                raise

    async def _execute_function(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function, handling both sync and async"""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, *args, **kwargs)

    async def _on_success(self):
        """Handle successful function execution"""
        self.stats.successful_calls += 1

        if self.stats.current_state == CircuitState.HALF_OPEN:
            # Check if we should close the circuit
            recent_successes = self._count_recent_successes()
            if recent_successes >= self.config.success_threshold:
                self.stats.current_state = CircuitState.CLOSED
                self.stats.failures.clear()
                logger.info(f"✅ Circuit '{self.name}' CLOSED after recovery")

    async def _on_failure(self, exception: Exception):
        """Handle failed function execution"""
        self.stats.failed_calls += 1
        self.stats.last_failure_time = time.time()
        self.stats.failures.append(
            {
                "timestamp": time.time(),
                "exception": str(exception),
                "type": type(exception).__name__,
            }
        )

        if self.stats.current_state == CircuitState.CLOSED:
            # Check if we should open the circuit
            if len(self.stats.failures) >= self.config.failure_threshold:
                self.stats.current_state = CircuitState.OPEN
                self.stats.circuit_opens += 1
                logger.warning(
                    f"🔴 Circuit '{self.name}' OPENED after {len(self.stats.failures)} failures"
                )

        elif self.stats.current_state == CircuitState.HALF_OPEN:
            # Failure in half-open state, go back to open
            self.stats.current_state = CircuitState.OPEN
            logger.warning(f"🔴 Circuit '{self.name}' back to OPEN from HALF_OPEN")

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset"""
        if self.stats.last_failure_time is None:
            return True

        time_since_failure = time.time() - self.stats.last_failure_time
        return time_since_failure >= self.config.recovery_timeout

    def _count_recent_successes(self) -> int:
        """Count recent successful calls (placeholder implementation)"""
        # In a real implementation, you'd track recent successes
        # For now, we'll use a simple heuristic
        return self.stats.successful_calls % 10

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self.stats.current_state.value,
            "total_calls": self.stats.total_calls,
            "successful_calls": self.stats.successful_calls,
            "failed_calls": self.stats.failed_calls,
            "circuit_opens": self.stats.circuit_opens,
            "success_rate": (
                self.stats.successful_calls / max(self.stats.total_calls, 1) * 100
            ),
            "last_failure_time": self.stats.last_failure_time,
            "recent_failures": list(self.stats.failures),
        }

    def reset(self):
        """Manually reset circuit breaker"""
        self.stats.current_state = CircuitState.CLOSED
        self.stats.failures.clear()
        logger.info(f"🔄 Circuit '{self.name}' manually reset")


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers"""

    _instances: Dict[str, CircuitBreaker] = {}

    @classmethod
    def get_circuit_breaker(
        cls, name: str, config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Get or create circuit breaker instance"""
        if name not in cls._instances:
            cls._instances[name] = CircuitBreaker(name, config)
        return cls._instances[name]

    @classmethod
    def get_all_stats(cls) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers"""
        return {name: cb.get_stats() for name, cb in cls._instances.items()}

    @classmethod
    def reset_all(cls):
        """Reset all circuit breakers"""
        for cb in cls._instances.values():
            cb.reset()
        logger.info("🔄 All circuit breakers reset")


# Decorator for easy circuit breaker usage
def circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None):
    """Decorator to add circuit breaker to a function"""

    def decorator(func):
        cb = CircuitBreakerRegistry.get_circuit_breaker(name, config)

        async def wrapper(*args, **kwargs):
            return await cb.call(func, *args, **kwargs)

        wrapper.circuit_breaker = cb
        return wrapper

    return decorator


# Example usage
if __name__ == "__main__":
    import random

    async def unreliable_service():
        """Simulate unreliable external service"""
        if random.random() < 0.7:  # 70% failure rate
            raise Exception("Service unavailable")
        return "Success!"

    async def sophia_circuit_breaker():
        """Test circuit breaker functionality"""
        cb = CircuitBreaker("sophia_service")

        for i in range(20):
            try:
                result = await cb.call(unreliable_service)
                print(f"Call {i+1}: {result}")
            except Exception as e:
                print(f"Call {i+1}: Failed - {e}")

            # Print stats every 5 calls
            if (i + 1) % 5 == 0:
                stats = cb.get_stats()
                print(f"Stats: {json.dumps(stats, indent=2)}")
                print("-" * 50)

    # Run test
    asyncio.run(sophia_circuit_breaker())
