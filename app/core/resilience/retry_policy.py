"""
Retry Policy Pattern Implementation
Implements various retry strategies with exponential backoff, jitter, and custom policies
Includes retry budgets and circuit breaker integration
"""

import asyncio
import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryStrategy(Enum):
    """Available retry strategies"""

    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIBONACCI_BACKOFF = "fibonacci_backoff"
    CUSTOM = "custom"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""

    # Basic retry settings
    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF

    # Timing configuration
    initial_delay: float = 1.0  # Seconds
    max_delay: float = 60.0  # Maximum delay between retries
    multiplier: float = 2.0  # Backoff multiplier
    jitter: bool = True  # Add randomization to delays
    jitter_factor: float = 0.1  # Jitter range (0.1 = ±10%)

    # Retry conditions
    retry_on_exceptions: list[type[Exception]] = None
    retry_on_result: Optional[Callable[[Any], bool]] = None

    # Retry budget (optional)
    use_retry_budget: bool = False
    budget_percentage: float = 0.1  # 10% of requests can be retries
    budget_min_throughput: int = 10  # Minimum requests before budget applies

    # Callbacks
    on_retry: Optional[Callable[[int, Exception], None]] = None
    on_success: Optional[Callable[[int, Any], None]] = None
    on_failure: Optional[Callable[[int, Exception], None]] = None

    def __post_init__(self):
        """Validate configuration and set defaults"""
        if self.retry_on_exceptions is None:
            self.retry_on_exceptions = [Exception]

        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        if self.initial_delay < 0:
            raise ValueError("initial_delay must be non-negative")

        if self.multiplier < 1:
            raise ValueError("multiplier must be at least 1")

        if self.jitter_factor < 0 or self.jitter_factor > 1:
            raise ValueError("jitter_factor must be between 0 and 1")


class RetryPolicyBase(ABC):
    """Base class for retry policies"""

    @abstractmethod
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for the given attempt

        Args:
            attempt: Current attempt number (1-based)

        Returns:
            Delay in seconds
        """
        pass


class FixedDelayPolicy(RetryPolicyBase):
    """Fixed delay between retries"""

    def __init__(self, delay: float):
        self.delay = delay

    def calculate_delay(self, attempt: int) -> float:
        return self.delay


class ExponentialBackoffPolicy(RetryPolicyBase):
    """Exponential backoff with optional jitter"""

    def __init__(
        self,
        initial_delay: float,
        multiplier: float,
        max_delay: float,
        jitter: bool = True,
        jitter_factor: float = 0.1,
    ):
        self.initial_delay = initial_delay
        self.multiplier = multiplier
        self.max_delay = max_delay
        self.jitter = jitter
        self.jitter_factor = jitter_factor

    def calculate_delay(self, attempt: int) -> float:
        # Calculate exponential delay
        delay = min(
            self.initial_delay * (self.multiplier ** (attempt - 1)), self.max_delay
        )

        # Add jitter if enabled
        if self.jitter:
            jitter_range = delay * self.jitter_factor
            delay += random.uniform(-jitter_range, jitter_range)
            delay = max(0, delay)  # Ensure non-negative

        return delay


class LinearBackoffPolicy(RetryPolicyBase):
    """Linear backoff with optional jitter"""

    def __init__(
        self,
        initial_delay: float,
        increment: float,
        max_delay: float,
        jitter: bool = True,
        jitter_factor: float = 0.1,
    ):
        self.initial_delay = initial_delay
        self.increment = increment
        self.max_delay = max_delay
        self.jitter = jitter
        self.jitter_factor = jitter_factor

    def calculate_delay(self, attempt: int) -> float:
        # Calculate linear delay
        delay = min(
            self.initial_delay + (self.increment * (attempt - 1)), self.max_delay
        )

        # Add jitter if enabled
        if self.jitter:
            jitter_range = delay * self.jitter_factor
            delay += random.uniform(-jitter_range, jitter_range)
            delay = max(0, delay)  # Ensure non-negative

        return delay


class FibonacciBackoffPolicy(RetryPolicyBase):
    """Fibonacci sequence backoff"""

    def __init__(
        self,
        unit_delay: float,
        max_delay: float,
        jitter: bool = True,
        jitter_factor: float = 0.1,
    ):
        self.unit_delay = unit_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.jitter_factor = jitter_factor
        self._fibonacci_cache = {1: 1, 2: 1}

    def _fibonacci(self, n: int) -> int:
        """Calculate nth Fibonacci number with memoization"""
        if n in self._fibonacci_cache:
            return self._fibonacci_cache[n]

        self._fibonacci_cache[n] = self._fibonacci(n - 1) + self._fibonacci(n - 2)
        return self._fibonacci_cache[n]

    def calculate_delay(self, attempt: int) -> float:
        # Calculate Fibonacci delay
        fib_value = self._fibonacci(attempt)
        delay = min(self.unit_delay * fib_value, self.max_delay)

        # Add jitter if enabled
        if self.jitter:
            jitter_range = delay * self.jitter_factor
            delay += random.uniform(-jitter_range, jitter_range)
            delay = max(0, delay)  # Ensure non-negative

        return delay


class RetryBudget:
    """
    Retry budget to prevent retry storms
    Limits the percentage of requests that can be retries
    """

    def __init__(self, percentage: float = 0.1, min_throughput: int = 10):
        """
        Initialize retry budget

        Args:
            percentage: Maximum percentage of requests that can be retries
            min_throughput: Minimum requests before budget applies
        """
        self.percentage = percentage
        self.min_throughput = min_throughput

        # Request tracking
        self.total_requests = 0
        self.retry_requests = 0
        self.request_window: list[tuple] = []
        self.window_duration = 60  # Track last 60 seconds

        # Lock for thread safety
        self._lock = asyncio.Lock()

    async def can_retry(self) -> bool:
        """
        Check if retry is allowed within budget

        Returns:
            True if retry is allowed, False otherwise
        """
        async with self._lock:
            # Clean old entries from window
            self._clean_window()

            # Check minimum throughput
            if len(self.request_window) < self.min_throughput:
                return True

            # Calculate current retry rate
            retry_count = sum(1 for _, is_retry in self.request_window if is_retry)
            total_count = len(self.request_window)

            if total_count == 0:
                return True

            retry_rate = retry_count / total_count

            # Allow retry if under budget
            return retry_rate < self.percentage

    async def record_request(self, is_retry: bool):
        """Record a request for budget tracking"""
        async with self._lock:
            self.total_requests += 1
            if is_retry:
                self.retry_requests += 1

            self.request_window.append((datetime.utcnow(), is_retry))
            self._clean_window()

    def _clean_window(self):
        """Remove old entries from tracking window"""
        cutoff = datetime.utcnow() - timedelta(seconds=self.window_duration)
        self.request_window = [
            (timestamp, is_retry)
            for timestamp, is_retry in self.request_window
            if timestamp > cutoff
        ]

    def get_stats(self) -> dict[str, Any]:
        """Get retry budget statistics"""
        self._clean_window()

        window_retries = sum(1 for _, is_retry in self.request_window if is_retry)
        window_total = len(self.request_window)

        return {
            "total_requests": self.total_requests,
            "retry_requests": self.retry_requests,
            "overall_retry_rate": (self.retry_requests / max(self.total_requests, 1)),
            "window_retry_rate": (
                (window_retries / max(window_total, 1)) if window_total > 0 else 0.0
            ),
            "window_size": window_total,
            "budget_percentage": self.percentage,
            "min_throughput": self.min_throughput,
        }


class RetryPolicy:
    """
    Main retry policy implementation
    Coordinates retry strategy, budget, and execution
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        """
        Initialize retry policy

        Args:
            config: Configuration for retry behavior
        """
        self.config = config or RetryConfig()

        # Create retry strategy
        self.strategy = self._create_strategy()

        # Create retry budget if enabled
        self.budget = (
            RetryBudget(
                self.config.budget_percentage, self.config.budget_min_throughput
            )
            if self.config.use_retry_budget
            else None
        )

        # Statistics
        self.total_attempts = 0
        self.successful_attempts = 0
        self.failed_attempts = 0
        self.retry_counts: dict[int, int] = {}

    def _create_strategy(self) -> RetryPolicyBase:
        """Create retry strategy based on configuration"""
        if self.config.strategy == RetryStrategy.FIXED_DELAY:
            return FixedDelayPolicy(self.config.initial_delay)

        elif self.config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            return ExponentialBackoffPolicy(
                self.config.initial_delay,
                self.config.multiplier,
                self.config.max_delay,
                self.config.jitter,
                self.config.jitter_factor,
            )

        elif self.config.strategy == RetryStrategy.LINEAR_BACKOFF:
            return LinearBackoffPolicy(
                self.config.initial_delay,
                self.config.multiplier,  # Use multiplier as increment
                self.config.max_delay,
                self.config.jitter,
                self.config.jitter_factor,
            )

        elif self.config.strategy == RetryStrategy.FIBONACCI_BACKOFF:
            return FibonacciBackoffPolicy(
                self.config.initial_delay,
                self.config.max_delay,
                self.config.jitter,
                self.config.jitter_factor,
            )

        else:
            raise ValueError(f"Unsupported retry strategy: {self.config.strategy}")

    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with retry policy

        Args:
            func: Function to execute
            *args: Arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            Exception: Last exception if all retries fail
        """
        last_exception = None

        for attempt in range(1, self.config.max_attempts + 1):
            # Check retry budget if enabled
            if self.budget and attempt > 1:
                if not await self.budget.can_retry():
                    logger.warning(
                        f"Retry budget exhausted, failing after {attempt-1} attempts"
                    )
                    if last_exception:
                        raise last_exception
                    raise RetryBudgetExceededException("Retry budget exceeded")

                await self.budget.record_request(is_retry=True)
            elif self.budget:
                await self.budget.record_request(is_retry=False)

            try:
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # Check if result should trigger retry
                if self.config.retry_on_result and self.config.retry_on_result(result):
                    raise RetryableResultException(f"Result triggered retry: {result}")

                # Success!
                self.successful_attempts += 1
                self.retry_counts[attempt] = self.retry_counts.get(attempt, 0) + 1

                if self.config.on_success:
                    try:
                        self.config.on_success(attempt, result)
                    except Exception as e:
                        logger.error(f"Error in on_success callback: {e}")

                logger.debug(f"Success after {attempt} attempt(s)")
                return result

            except Exception as e:
                last_exception = e
                self.total_attempts += 1

                # Check if exception is retryable
                is_retryable = any(
                    isinstance(e, exc_type)
                    for exc_type in self.config.retry_on_exceptions
                )

                if not is_retryable:
                    logger.debug(f"Non-retryable exception: {type(e).__name__}")
                    raise

                # Check if we have attempts left
                if attempt >= self.config.max_attempts:
                    self.failed_attempts += 1

                    if self.config.on_failure:
                        try:
                            self.config.on_failure(attempt, e)
                        except Exception as callback_error:
                            logger.error(
                                f"Error in on_failure callback: {callback_error}"
                            )

                    logger.error(f"All {self.config.max_attempts} attempts failed: {e}")
                    raise

                # Calculate delay for next attempt
                delay = self.strategy.calculate_delay(attempt)

                logger.warning(
                    f"Attempt {attempt}/{self.config.max_attempts} failed: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )

                if self.config.on_retry:
                    try:
                        self.config.on_retry(attempt, e)
                    except Exception as callback_error:
                        logger.error(f"Error in on_retry callback: {callback_error}")

                # Wait before retry
                await asyncio.sleep(delay)

        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
        raise RuntimeError("Retry policy execution failed unexpectedly")

    def get_stats(self) -> dict[str, Any]:
        """Get retry policy statistics"""
        stats = {
            "total_attempts": self.total_attempts,
            "successful_attempts": self.successful_attempts,
            "failed_attempts": self.failed_attempts,
            "retry_distribution": dict(sorted(self.retry_counts.items())),
            "average_retries": sum(
                (attempts - 1) * count for attempts, count in self.retry_counts.items()
            )
            / max(sum(self.retry_counts.values()), 1),
            "success_rate": (
                self.successful_attempts
                / max(self.successful_attempts + self.failed_attempts, 1)
            ),
        }

        if self.budget:
            stats["budget"] = self.budget.get_stats()

        return stats

    def reset_stats(self):
        """Reset statistics"""
        self.total_attempts = 0
        self.successful_attempts = 0
        self.failed_attempts = 0
        self.retry_counts.clear()


class RetryableResultException(Exception):
    """Exception raised when result triggers a retry"""

    pass


class RetryBudgetExceededException(Exception):
    """Exception raised when retry budget is exceeded"""

    pass


class CompositeRetryPolicy:
    """
    Composite retry policy that combines multiple policies
    Useful for complex retry scenarios with fallback strategies
    """

    def __init__(self, policies: list[RetryPolicy]):
        """
        Initialize composite retry policy

        Args:
            policies: List of retry policies to try in order
        """
        self.policies = policies

    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with composite retry policy
        Tries each policy in order until one succeeds

        Args:
            func: Function to execute
            *args: Arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            Exception: Last exception if all policies fail
        """
        last_exception = None

        for i, policy in enumerate(self.policies):
            try:
                logger.debug(f"Trying policy {i+1}/{len(self.policies)}")
                return await policy.execute(func, *args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(f"Policy {i+1}/{len(self.policies)} failed: {e}")

        # All policies failed
        if last_exception:
            raise last_exception
        raise RuntimeError("All retry policies failed")
