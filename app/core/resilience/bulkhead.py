"""
Bulkhead Pattern Implementation
Implements resource isolation to prevent cascading failures
Includes semaphore-based and thread-pool-based bulkheads
"""

import asyncio
import logging
import threading
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BulkheadType(Enum):
    """Types of bulkhead implementations"""

    SEMAPHORE = "semaphore"  # Limit concurrent executions
    THREAD_POOL = "thread_pool"  # Isolate in separate thread pool
    ASYNC_SEMAPHORE = "async_semaphore"  # Async semaphore for coroutines


class BulkheadState(Enum):
    """Bulkhead operational states"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"  # High utilization
    SATURATED = "saturated"  # At capacity


@dataclass
class BulkheadConfig:
    """Configuration for bulkhead behavior"""

    # Resource limits
    max_concurrent: int = 10  # Maximum concurrent executions
    max_wait_duration: float = 30.0  # Maximum time to wait for slot (seconds)

    # Thread pool configuration (for THREAD_POOL type)
    thread_pool_size: Optional[int] = None  # Defaults to max_concurrent
    thread_name_prefix: str = "bulkhead"

    # Queue configuration
    max_queue_size: int = 100  # Maximum waiting requests
    queue_timeout: float = 60.0  # Queue timeout in seconds

    # Monitoring thresholds
    degraded_threshold: float = 0.7  # Usage threshold for degraded state
    saturated_threshold: float = 0.9  # Usage threshold for saturated state

    # Callbacks
    on_accept: Optional[Callable[[], None]] = None
    on_reject: Optional[Callable[[], None]] = None
    on_timeout: Optional[Callable[[], None]] = None
    on_release: Optional[Callable[[], None]] = None

    def __post_init__(self):
        """Validate configuration"""
        if self.max_concurrent < 1:
            raise ValueError("max_concurrent must be at least 1")

        if self.thread_pool_size is None:
            self.thread_pool_size = self.max_concurrent

        if self.max_queue_size < 0:
            raise ValueError("max_queue_size must be non-negative")

        if self.degraded_threshold < 0 or self.degraded_threshold > 1:
            raise ValueError("degraded_threshold must be between 0 and 1")

        if self.saturated_threshold < self.degraded_threshold:
            raise ValueError("saturated_threshold must be >= degraded_threshold")


class BulkheadBase(ABC):
    """Base class for bulkhead implementations"""

    def __init__(self, name: str, config: BulkheadConfig):
        """
        Initialize bulkhead

        Args:
            name: Name of the bulkhead
            config: Bulkhead configuration
        """
        self.name = name
        self.config = config

        # Statistics
        self.total_calls = 0
        self.accepted_calls = 0
        self.rejected_calls = 0
        self.timeout_calls = 0
        self.completed_calls = 0
        self.failed_calls = 0
        self.active_calls = 0
        self.queued_calls = 0

        # Timing statistics
        self.total_execution_time = 0.0
        self.min_execution_time = float("inf")
        self.max_execution_time = 0.0

        # State tracking
        self.state = BulkheadState.HEALTHY
        self.state_changed_at = datetime.utcnow()

    @abstractmethod
    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire a slot in the bulkhead

        Args:
            timeout: Optional timeout in seconds

        Returns:
            True if slot acquired, False otherwise
        """
        pass

    @abstractmethod
    async def release(self):
        """Release a slot in the bulkhead"""
        pass

    @abstractmethod
    async def execute(
        self, func: Callable[..., T], *args, timeout: Optional[float] = None, **kwargs
    ) -> T:
        """
        Execute function within bulkhead protection

        Args:
            func: Function to execute
            *args: Arguments for function
            timeout: Optional execution timeout
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            BulkheadRejectedException: If bulkhead is full
            TimeoutError: If execution times out
        """
        pass

    def _update_state(self):
        """Update bulkhead state based on utilization"""
        utilization = self.active_calls / self.config.max_concurrent

        new_state = BulkheadState.HEALTHY
        if utilization >= self.config.saturated_threshold:
            new_state = BulkheadState.SATURATED
        elif utilization >= self.config.degraded_threshold:
            new_state = BulkheadState.DEGRADED

        if new_state != self.state:
            self.state = new_state
            self.state_changed_at = datetime.utcnow()
            logger.info(f"Bulkhead '{self.name}' state changed to {new_state.value}")

    def get_stats(self) -> dict[str, Any]:
        """Get bulkhead statistics"""
        avg_execution_time = (
            (self.total_execution_time / max(self.completed_calls, 1))
            if self.completed_calls > 0
            else 0.0
        )

        return {
            "name": self.name,
            "state": self.state.value,
            "active_calls": self.active_calls,
            "queued_calls": self.queued_calls,
            "max_concurrent": self.config.max_concurrent,
            "utilization": self.active_calls / self.config.max_concurrent,
            "total_calls": self.total_calls,
            "accepted_calls": self.accepted_calls,
            "rejected_calls": self.rejected_calls,
            "timeout_calls": self.timeout_calls,
            "completed_calls": self.completed_calls,
            "failed_calls": self.failed_calls,
            "accept_rate": (
                (self.accepted_calls / max(self.total_calls, 1)) if self.total_calls > 0 else 0.0
            ),
            "avg_execution_time": avg_execution_time,
            "min_execution_time": self.min_execution_time if self.completed_calls > 0 else 0,
            "max_execution_time": self.max_execution_time,
            "state_duration": (datetime.utcnow() - self.state_changed_at).total_seconds(),
        }


class SemaphoreBulkhead(BulkheadBase):
    """
    Semaphore-based bulkhead implementation
    Limits concurrent executions using a semaphore
    """

    def __init__(self, name: str, config: Optional[BulkheadConfig] = None):
        """
        Initialize semaphore bulkhead

        Args:
            name: Name of the bulkhead
            config: Bulkhead configuration
        """
        super().__init__(name, config or BulkheadConfig())

        # Create semaphore
        self.semaphore = threading.Semaphore(self.config.max_concurrent)
        self.queue: list[threading.Event] = []
        self._lock = threading.Lock()

        logger.info(
            f"Semaphore bulkhead '{name}' initialized with "
            f"max_concurrent={self.config.max_concurrent}"
        )

    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """Acquire a slot in the bulkhead"""
        timeout = timeout or self.config.max_wait_duration

        with self._lock:
            self.total_calls += 1

            # Check queue size
            if len(self.queue) >= self.config.max_queue_size:
                self.rejected_calls += 1
                if self.config.on_reject:
                    self.config.on_reject()
                logger.warning(f"Bulkhead '{self.name}' queue full")
                return False

        # Try to acquire semaphore
        acquired = self.semaphore.acquire(timeout=timeout)

        if acquired:
            with self._lock:
                self.accepted_calls += 1
                self.active_calls += 1
                self._update_state()

            if self.config.on_accept:
                self.config.on_accept()

            return True
        else:
            with self._lock:
                self.timeout_calls += 1

            if self.config.on_timeout:
                self.config.on_timeout()

            logger.warning(f"Bulkhead '{self.name}' acquisition timeout")
            return False

    async def release(self):
        """Release a slot in the bulkhead"""
        self.semaphore.release()

        with self._lock:
            self.active_calls -= 1
            self._update_state()

        if self.config.on_release:
            self.config.on_release()

    async def execute(
        self, func: Callable[..., T], *args, timeout: Optional[float] = None, **kwargs
    ) -> T:
        """Execute function within bulkhead protection"""
        # Acquire slot
        if not await self.acquire(timeout):
            raise BulkheadRejectedException(f"Bulkhead '{self.name}' rejected execution")

        start_time = datetime.utcnow()

        try:
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                # Run sync function in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, func, *args, **kwargs)

            # Update statistics
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            with self._lock:
                self.completed_calls += 1
                self.total_execution_time += execution_time
                self.min_execution_time = min(self.min_execution_time, execution_time)
                self.max_execution_time = max(self.max_execution_time, execution_time)

            return result

        except Exception as e:
            with self._lock:
                self.failed_calls += 1
            raise e

        finally:
            await self.release()


class AsyncSemaphoreBulkhead(BulkheadBase):
    """
    Async semaphore-based bulkhead implementation
    Optimized for async/await code
    """

    def __init__(self, name: str, config: Optional[BulkheadConfig] = None):
        """
        Initialize async semaphore bulkhead

        Args:
            name: Name of the bulkhead
            config: Bulkhead configuration
        """
        super().__init__(name, config or BulkheadConfig())

        # Create async semaphore
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self.queue_semaphore = asyncio.Semaphore(self.config.max_queue_size)
        self._lock = asyncio.Lock()

        logger.info(
            f"Async semaphore bulkhead '{name}' initialized with "
            f"max_concurrent={self.config.max_concurrent}"
        )

    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """Acquire a slot in the bulkhead"""
        timeout = timeout or self.config.max_wait_duration

        async with self._lock:
            self.total_calls += 1

            # Check if we can queue
            if self.queued_calls >= self.config.max_queue_size:
                self.rejected_calls += 1
                if self.config.on_reject:
                    self.config.on_reject()
                logger.warning(f"Bulkhead '{self.name}' queue full")
                return False

            self.queued_calls += 1

        try:
            # Try to acquire semaphore with timeout
            try:
                await asyncio.wait_for(self.semaphore.acquire(), timeout=timeout)

                async with self._lock:
                    self.queued_calls -= 1
                    self.accepted_calls += 1
                    self.active_calls += 1
                    self._update_state()

                if self.config.on_accept:
                    self.config.on_accept()

                return True

            except asyncio.TimeoutError:
                async with self._lock:
                    self.queued_calls -= 1
                    self.timeout_calls += 1

                if self.config.on_timeout:
                    self.config.on_timeout()

                logger.warning(f"Bulkhead '{self.name}' acquisition timeout")
                return False

        except Exception as e:
            async with self._lock:
                self.queued_calls -= 1
            raise e

    async def release(self):
        """Release a slot in the bulkhead"""
        self.semaphore.release()

        async with self._lock:
            self.active_calls -= 1
            self._update_state()

        if self.config.on_release:
            self.config.on_release()

    async def execute(
        self, func: Callable[..., T], *args, timeout: Optional[float] = None, **kwargs
    ) -> T:
        """Execute function within bulkhead protection"""
        # Acquire slot
        if not await self.acquire(timeout):
            raise BulkheadRejectedException(f"Bulkhead '{self.name}' rejected execution")

        start_time = datetime.utcnow()

        try:
            # Execute function
            if asyncio.iscoroutinefunction(func):
                if timeout:
                    result = await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
                else:
                    result = await func(*args, **kwargs)
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                if timeout:
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, func, *args, **kwargs), timeout=timeout
                    )
                else:
                    result = await loop.run_in_executor(None, func, *args, **kwargs)

            # Update statistics
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            async with self._lock:
                self.completed_calls += 1
                self.total_execution_time += execution_time
                self.min_execution_time = min(self.min_execution_time, execution_time)
                self.max_execution_time = max(self.max_execution_time, execution_time)

            return result

        except Exception as e:
            async with self._lock:
                self.failed_calls += 1
            raise e

        finally:
            await self.release()


class ThreadPoolBulkhead(BulkheadBase):
    """
    Thread pool-based bulkhead implementation
    Isolates executions in a separate thread pool
    """

    def __init__(self, name: str, config: Optional[BulkheadConfig] = None):
        """
        Initialize thread pool bulkhead

        Args:
            name: Name of the bulkhead
            config: Bulkhead configuration
        """
        super().__init__(name, config or BulkheadConfig())

        # Create thread pool
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.thread_pool_size,
            thread_name_prefix=f"{self.config.thread_name_prefix}-{name}",
        )

        self._lock = threading.Lock()
        self._futures: list[Any] = []

        logger.info(
            f"Thread pool bulkhead '{name}' initialized with "
            f"pool_size={self.config.thread_pool_size}"
        )

    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """Check if thread pool has capacity"""
        with self._lock:
            self.total_calls += 1

            # Clean completed futures
            self._futures = [f for f in self._futures if not f.done()]

            # Check capacity
            if len(self._futures) >= self.config.thread_pool_size:
                self.rejected_calls += 1
                if self.config.on_reject:
                    self.config.on_reject()
                return False

            self.accepted_calls += 1
            self.active_calls = len(self._futures)
            self._update_state()

            if self.config.on_accept:
                self.config.on_accept()

            return True

    async def release(self):
        """Update statistics after execution"""
        with self._lock:
            self._futures = [f for f in self._futures if not f.done()]
            self.active_calls = len(self._futures)
            self._update_state()

        if self.config.on_release:
            self.config.on_release()

    async def execute(
        self, func: Callable[..., T], *args, timeout: Optional[float] = None, **kwargs
    ) -> T:
        """Execute function in thread pool"""
        # Check capacity
        if not await self.acquire():
            raise BulkheadRejectedException(f"Thread pool bulkhead '{self.name}' at capacity")

        start_time = datetime.utcnow()

        try:
            # Submit to thread pool
            if asyncio.iscoroutinefunction(func):
                # For async functions, run in event loop
                loop = asyncio.get_event_loop()
                future = loop.create_task(func(*args, **kwargs))
            else:
                future = self.executor.submit(func, *args, **kwargs)

            with self._lock:
                self._futures.append(future)

            # Wait for result
            if asyncio.iscoroutinefunction(func):
                if timeout:
                    result = await asyncio.wait_for(future, timeout=timeout)
                else:
                    result = await future
            else:
                # Convert concurrent.futures.Future to asyncio
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, future.result, timeout)

            # Update statistics
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            with self._lock:
                self.completed_calls += 1
                self.total_execution_time += execution_time
                self.min_execution_time = min(self.min_execution_time, execution_time)
                self.max_execution_time = max(self.max_execution_time, execution_time)

            return result

        except (asyncio.TimeoutError, FutureTimeoutError):
            with self._lock:
                self.timeout_calls += 1
            raise TimeoutError(f"Execution timeout in bulkhead '{self.name}'")

        except Exception as e:
            with self._lock:
                self.failed_calls += 1
            raise e

        finally:
            await self.release()

    def shutdown(self, wait: bool = True):
        """Shutdown the thread pool"""
        self.executor.shutdown(wait=wait)
        logger.info(f"Thread pool bulkhead '{self.name}' shutdown")


class BulkheadRejectedException(Exception):
    """Exception raised when bulkhead rejects execution"""

    pass


class BulkheadRegistry:
    """
    Registry for managing multiple bulkheads
    Provides centralized monitoring and management
    """

    def __init__(self):
        """Initialize bulkhead registry"""
        self.bulkheads: dict[str, BulkheadBase] = {}
        self._lock = threading.Lock()
        logger.info("Bulkhead registry initialized")

    def register(
        self, name: str, bulkhead_type: BulkheadType, config: Optional[BulkheadConfig] = None
    ) -> BulkheadBase:
        """
        Register a new bulkhead

        Args:
            name: Name of the bulkhead
            bulkhead_type: Type of bulkhead to create
            config: Bulkhead configuration

        Returns:
            Created bulkhead instance
        """
        with self._lock:
            if name in self.bulkheads:
                raise ValueError(f"Bulkhead '{name}' already registered")

            # Create bulkhead based on type
            if bulkhead_type == BulkheadType.SEMAPHORE:
                bulkhead = SemaphoreBulkhead(name, config)
            elif bulkhead_type == BulkheadType.ASYNC_SEMAPHORE:
                bulkhead = AsyncSemaphoreBulkhead(name, config)
            elif bulkhead_type == BulkheadType.THREAD_POOL:
                bulkhead = ThreadPoolBulkhead(name, config)
            else:
                raise ValueError(f"Unknown bulkhead type: {bulkhead_type}")

            self.bulkheads[name] = bulkhead
            logger.info(f"Bulkhead '{name}' registered with type {bulkhead_type.value}")

            return bulkhead

    def get(self, name: str) -> Optional[BulkheadBase]:
        """Get a bulkhead by name"""
        return self.bulkheads.get(name)

    def remove(self, name: str) -> bool:
        """
        Remove a bulkhead from registry

        Args:
            name: Name of the bulkhead

        Returns:
            True if removed, False if not found
        """
        with self._lock:
            if name in self.bulkheads:
                bulkhead = self.bulkheads.pop(name)

                # Shutdown thread pool if applicable
                if isinstance(bulkhead, ThreadPoolBulkhead):
                    bulkhead.shutdown()

                logger.info(f"Bulkhead '{name}' removed from registry")
                return True

            return False

    def get_all_stats(self) -> dict[str, Any]:
        """Get statistics for all bulkheads"""
        return {
            "bulkheads": {name: bulkhead.get_stats() for name, bulkhead in self.bulkheads.items()},
            "summary": {
                "total_bulkheads": len(self.bulkheads),
                "healthy": sum(
                    1 for b in self.bulkheads.values() if b.state == BulkheadState.HEALTHY
                ),
                "degraded": sum(
                    1 for b in self.bulkheads.values() if b.state == BulkheadState.DEGRADED
                ),
                "saturated": sum(
                    1 for b in self.bulkheads.values() if b.state == BulkheadState.SATURATED
                ),
                "total_active_calls": sum(b.active_calls for b in self.bulkheads.values()),
                "total_queued_calls": sum(b.queued_calls for b in self.bulkheads.values()),
            },
        }

    def shutdown_all(self, wait: bool = True):
        """Shutdown all thread pool bulkheads"""
        for bulkhead in self.bulkheads.values():
            if isinstance(bulkhead, ThreadPoolBulkhead):
                bulkhead.shutdown(wait=wait)

        logger.info("All thread pool bulkheads shutdown")


# Global registry instance
bulkhead_registry = BulkheadRegistry()
