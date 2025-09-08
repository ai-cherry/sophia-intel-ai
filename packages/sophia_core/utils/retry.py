"""Retry logic with exponential backoff and jitter."""

import asyncio
import logging
import random
import time
from functools import wraps
from typing import Any, Callable, Optional, Tuple, Type

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.exceptions = exceptions


def calculate_backoff(
    attempt: int,
    initial_delay: float,
    exponential_base: float,
    max_delay: float,
    jitter: bool
) -> float:
    """Calculate the backoff delay for a given attempt."""
    delay = min(initial_delay * (exponential_base ** attempt), max_delay)

    if jitter:
        # Add jitter: random value between 0 and delay
        delay = random.uniform(0, delay)

    return delay


def retry(config: Optional[RetryConfig] = None):
    """Decorator for adding retry logic to functions."""

    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except config.exceptions as e:
                    last_exception = e

                    if attempt < config.max_attempts - 1:
                        delay = calculate_backoff(
                            attempt,
                            config.initial_delay,
                            config.exponential_base,
                            config.max_delay,
                            config.jitter
                        )

                        logger.warning(
                            f"Attempt {attempt + 1}/{config.max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )

                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_attempts} attempts failed for {func.__name__}: {e}"
                        )

            raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except config.exceptions as e:
                    last_exception = e

                    if attempt < config.max_attempts - 1:
                        delay = calculate_backoff(
                            attempt,
                            config.initial_delay,
                            config.exponential_base,
                            config.max_delay,
                            config.jitter
                        )

                        logger.warning(
                            f"Attempt {attempt + 1}/{config.max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )

                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_attempts} attempts failed for {func.__name__}: {e}"
                        )

            raise last_exception

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class RetryManager:
    """Manages retry logic with more control."""

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.attempt_count = 0

    async def execute_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute an async function with retry logic."""
        last_exception = None

        for attempt in range(self.config.max_attempts):
            self.attempt_count = attempt + 1

            try:
                result = await func(*args, **kwargs)
                return result
            except self.config.exceptions as e:
                last_exception = e

                if attempt < self.config.max_attempts - 1:
                    delay = calculate_backoff(
                        attempt,
                        self.config.initial_delay,
                        self.config.exponential_base,
                        self.config.max_delay,
                        self.config.jitter
                    )

                    logger.warning(
                        f"Attempt {attempt + 1}/{self.config.max_attempts} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )

                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"All {self.config.max_attempts} attempts failed: {e}"
                    )

        raise last_exception

    def execute_sync(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a sync function with retry logic."""
        last_exception = None

        for attempt in range(self.config.max_attempts):
            self.attempt_count = attempt + 1

            try:
                result = func(*args, **kwargs)
                return result
            except self.config.exceptions as e:
                last_exception = e

                if attempt < self.config.max_attempts - 1:
                    delay = calculate_backoff(
                        attempt,
                        self.config.initial_delay,
                        self.config.exponential_base,
                        self.config.max_delay,
                        self.config.jitter
                    )

                    logger.warning(
                        f"Attempt {attempt + 1}/{self.config.max_attempts} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )

                    time.sleep(delay)
                else:
                    logger.error(
                        f"All {self.config.max_attempts} attempts failed: {e}"
                    )

        raise last_exception
