"""
Single-Flight Request Deduplication
Prevents duplicate requests for the same resource from overwhelming backends
"""

import asyncio
import hashlib
import time
import logging
from typing import Any, Dict, Optional, Callable, Awaitable, TypeVar, Generic
from dataclasses import dataclass, field
import json
import weakref
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

T = TypeVar('T')

@dataclass
class FlightMetrics:
    total_requests: int = 0
    deduplicated_requests: int = 0
    active_flights: int = 0
    completed_flights: int = 0
    failed_flights: int = 0
    total_wait_time_ms: float = 0
    max_concurrent_flights: int = 0

    def get_deduplication_rate(self) -> float:
        """Calculate percentage of requests that were deduplicated"""
        if self.total_requests == 0:
            return 0.0
        return (self.deduplicated_requests / self.total_requests) * 100

    def get_average_wait_time_ms(self) -> float:
        """Calculate average wait time for deduplicated requests"""
        if self.deduplicated_requests == 0:
            return 0.0
        return self.total_wait_time_ms / self.deduplicated_requests

@dataclass
class FlightInfo(Generic[T]):
    """Information about an in-flight request"""
    future: asyncio.Future[T]
    start_time: float
    waiters: int = 0
    key: str = ""

    def add_waiter(self):
        """Add a waiter to this flight"""
        self.waiters += 1

    def get_duration_ms(self) -> float:
        """Get current duration of this flight in milliseconds"""
        return (time.time() - self.start_time) * 1000

class SingleFlightGroup(Generic[T]):
    """
    Single-flight group for request deduplication

    Features:
    - Automatic request deduplication based on key
    - Comprehensive metrics collection
    - Memory-efficient weak references
    - Timeout handling for stuck requests
    - Context manager support for cleanup
    """

    def __init__(
        self,
        name: str = "default",
        default_timeout: float = 30.0,
        max_concurrent_flights: int = 1000,
        enable_metrics: bool = True
    ):
        self.name = name
        self.default_timeout = default_timeout
        self.max_concurrent_flights = max_concurrent_flights
        self.enable_metrics = enable_metrics

        # In-flight requests tracking
        self._flights: Dict[str, FlightInfo[T]] = {}
        self._lock = asyncio.Lock()

        # Metrics
        self._metrics = FlightMetrics() if enable_metrics else None

        # Cleanup task for stuck requests
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()

    async def do(
        self,
        key: str,
        fn: Callable[[], Awaitable[T]],
        timeout: Optional[float] = None
    ) -> T:
        """
        Execute function with single-flight deduplication

        Args:
            key: Unique key for request deduplication
            fn: Async function to execute
            timeout: Optional timeout override

        Returns:
            Result of the function execution
        """
        if self.enable_metrics:
            self._metrics.total_requests += 1

        # Normalize key for consistent hashing
        normalized_key = self._normalize_key(key)
        effective_timeout = timeout or self.default_timeout

        async with self._lock:
            # Check if request is already in flight
            if normalized_key in self._flights:
                flight_info = self._flights[normalized_key]
                flight_info.add_waiter()

                if self.enable_metrics:
                    self._metrics.deduplicated_requests += 1

                logger.debug(f"Joining existing flight for key: {key} (waiters: {flight_info.waiters})")

                # Wait for existing request to complete
                start_wait = time.time()
                try:
                    result = await asyncio.wait_for(flight_info.future, timeout=effective_timeout)

                    if self.enable_metrics:
                        wait_time = (time.time() - start_wait) * 1000
                        self._metrics.total_wait_time_ms += wait_time

                    return result

                except asyncio.TimeoutError:
                    logger.warning(f"Timeout waiting for flight: {key}")
                    raise
                except Exception as e:
                    logger.warning(f"Flight failed for key {key}: {e}")
                    raise

            # Check concurrent flight limit
            if len(self._flights) >= self.max_concurrent_flights:
                raise Exception(f"Too many concurrent flights ({len(self._flights)}) for group {self.name}")

            # Create new flight
            future = asyncio.get_event_loop().create_future()
            flight_info = FlightInfo(
                future=future,
                start_time=time.time(),
                key=normalized_key
            )

            self._flights[normalized_key] = flight_info

            if self.enable_metrics:
                self._metrics.active_flights += 1
                self._metrics.max_concurrent_flights = max(
                    self._metrics.max_concurrent_flights,
                    len(self._flights)
                )

        # Execute the function outside the lock
        try:
            logger.debug(f"Starting new flight for key: {key}")

            # Execute with timeout
            result = await asyncio.wait_for(fn(), timeout=effective_timeout)

            # Set result for all waiters
            if not future.done():
                future.set_result(result)

            if self.enable_metrics:
                self._metrics.completed_flights += 1

            logger.debug(f"Flight completed successfully for key: {key}")
            return result

        except Exception as e:
            # Set exception for all waiters
            if not future.done():
                future.set_exception(e)

            if self.enable_metrics:
                self._metrics.failed_flights += 1

            logger.warning(f"Flight failed for key {key}: {e}")
            raise

        finally:
            # Clean up flight tracking
            async with self._lock:
                if normalized_key in self._flights:
                    del self._flights[normalized_key]

                if self.enable_metrics:
                    self._metrics.active_flights -= 1

    async def do_with_context(
        self,
        key: str,
        fn: Callable[[], Awaitable[T]],
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> T:
        """
        Execute function with additional context for key generation

        Args:
            key: Base key for request
            fn: Async function to execute
            context: Additional context for key generation
            timeout: Optional timeout override

        Returns:
            Result of the function execution
        """
        # Generate context-aware key
        if context:
            context_key = self._generate_context_key(key, context)
        else:
            context_key = key

        return await self.do(context_key, fn, timeout)

    def _normalize_key(self, key: str) -> str:
        """Normalize key for consistent hashing"""
        # Use SHA-256 for consistent, collision-resistant hashing
        return hashlib.sha256(key.encode('utf-8')).hexdigest()

    def _generate_context_key(self, base_key: str, context: Dict[str, Any]) -> str:
        """Generate key that includes context information"""
        # Sort context for deterministic key generation
        context_str = json.dumps(context, sort_keys=True, default=str)
        combined = f"{base_key}:{context_str}"
        return combined

    def _start_cleanup_task(self):
        """Start background task to clean up stuck requests"""
        async def cleanup_stuck_flights():
            while True:
                try:
                    await asyncio.sleep(60)  # Check every minute

                    current_time = time.time()
                    stuck_keys = []

                    async with self._lock:
                        for key, flight_info in self._flights.items():
                            # Consider flight stuck if running for more than 5 minutes
                            if current_time - flight_info.start_time > 300:
                                stuck_keys.append(key)

                    # Cancel stuck flights
                    for key in stuck_keys:
                        async with self._lock:
                            if key in self._flights:
                                flight_info = self._flights[key]
                                if not flight_info.future.done():
                                    flight_info.future.cancel()
                                del self._flights[key]

                                if self.enable_metrics:
                                    self._metrics.active_flights -= 1
                                    self._metrics.failed_flights += 1

                                logger.warning(f"Cleaned up stuck flight: {key}")

                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")

        self._cleanup_task = asyncio.create_task(cleanup_stuck_flights())

    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """Get comprehensive single-flight metrics"""
        if not self.enable_metrics or not self._metrics:
            return None

        return {
            'group_name': self.name,
            'total_requests': self._metrics.total_requests,
            'deduplicated_requests': self._metrics.deduplicated_requests,
            'deduplication_rate_percent': self._metrics.get_deduplication_rate(),
            'active_flights': len(self._flights),
            'completed_flights': self._metrics.completed_flights,
            'failed_flights': self._metrics.failed_flights,
            'max_concurrent_flights': self._metrics.max_concurrent_flights,
            'average_wait_time_ms': self._metrics.get_average_wait_time_ms(),
            'current_flight_keys': list(self._flights.keys())[:10]  # First 10 for debugging
        }

    def get_active_flights(self) -> Dict[str, Dict[str, Any]]:
        """Get information about currently active flights"""
        result = {}

        for key, flight_info in self._flights.items():
            result[key] = {
                'waiters': flight_info.waiters,
                'duration_ms': flight_info.get_duration_ms(),
                'is_done': flight_info.future.done()
            }

        return result

    async def cancel_flight(self, key: str) -> bool:
        """
        Cancel a specific flight

        Args:
            key: Key of the flight to cancel

        Returns:
            True if flight was cancelled, False if not found
        """
        normalized_key = self._normalize_key(key)

        async with self._lock:
            if normalized_key in self._flights:
                flight_info = self._flights[normalized_key]
                if not flight_info.future.done():
                    flight_info.future.cancel()

                del self._flights[normalized_key]

                if self.enable_metrics:
                    self._metrics.active_flights -= 1
                    self._metrics.failed_flights += 1

                logger.info(f"Cancelled flight for key: {key}")
                return True

        return False

    async def cancel_all_flights(self):
        """Cancel all active flights"""
        async with self._lock:
            for flight_info in self._flights.values():
                if not flight_info.future.done():
                    flight_info.future.cancel()

            cancelled_count = len(self._flights)
            self._flights.clear()

            if self.enable_metrics:
                self._metrics.active_flights = 0
                self._metrics.failed_flights += cancelled_count

            logger.info(f"Cancelled {cancelled_count} flights in group {self.name}")

    async def close(self):
        """Clean shutdown of single-flight group"""
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:

        # Cancel all active flights
        await self.cancel_all_flights()

        logger.info(f"Single-flight group {self.name} closed")

class SingleFlightManager:
    """
    Manager for multiple single-flight groups
    Provides centralized management and metrics aggregation
    """

    def __init__(self):
        self._groups: Dict[str, SingleFlightGroup] = {}
        self._lock = asyncio.Lock()

    def get_group(
        self,
        name: str,
        default_timeout: float = 30.0,
        max_concurrent_flights: int = 1000,
        enable_metrics: bool = True
    ) -> SingleFlightGroup:
        """Get or create a single-flight group"""
        if name not in self._groups:
            self._groups[name] = SingleFlightGroup(
                name=name,
                default_timeout=default_timeout,
                max_concurrent_flights=max_concurrent_flights,
                enable_metrics=enable_metrics
            )

        return self._groups[name]

    async def do(
        self,
        group_name: str,
        key: str,
        fn: Callable[[], Awaitable[T]],
        timeout: Optional[float] = None
    ) -> T:
        """Execute function in specified group with single-flight deduplication"""
        group = self.get_group(group_name)
        return await group.do(key, fn, timeout)

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics from all groups"""
        all_metrics = {}

        for name, group in self._groups.items():
            group_metrics = group.get_metrics()
            if group_metrics:
                all_metrics[name] = group_metrics

        # Calculate aggregate statistics
        total_requests = sum(m.get('total_requests', 0) for m in all_metrics.values())
        total_deduplicated = sum(m.get('deduplicated_requests', 0) for m in all_metrics.values())

        all_metrics['_aggregate'] = {
            'total_groups': len(self._groups),
            'total_requests': total_requests,
            'total_deduplicated': total_deduplicated,
            'overall_deduplication_rate': (
                (total_deduplicated / total_requests * 100) if total_requests > 0 else 0
            )
        }

        return all_metrics

    async def close_all(self):
        """Close all single-flight groups"""
        for group in self._groups.values():
            await group.close()

        self._groups.clear()
        logger.info("All single-flight groups closed")

# Global manager instance
_global_manager = SingleFlightManager()

def get_global_manager() -> SingleFlightManager:
    """Get the global single-flight manager"""
    return _global_manager

# Convenience functions for common usage patterns
async def single_flight_do(
    key: str,
    fn: Callable[[], Awaitable[T]],
    group: str = "default",
    timeout: Optional[float] = None
) -> T:
    """Execute function with single-flight deduplication using global manager"""
    return await _global_manager.do(group, key, fn, timeout)

@asynccontextmanager
async def single_flight_context(group_name: str = "default"):
    """Context manager for single-flight operations"""
    group = _global_manager.get_group(group_name)
    try:
        yield group
    finally:
        # Group cleanup is handled by the manager
        pass

# Decorator for automatic single-flight deduplication
def single_flight(
    key_fn: Optional[Callable[..., str]] = None,
    group: str = "default",
    timeout: Optional[float] = None
):
    """
    Decorator to automatically apply single-flight deduplication to async functions

    Args:
        key_fn: Function to generate key from arguments (default: str representation)
        group: Single-flight group name
        timeout: Request timeout
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        async def wrapper(*args, **kwargs) -> T:
            # Generate key from arguments
            if key_fn:
                key = key_fn(*args, **kwargs)
            else:
                key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"

            # Execute with single-flight deduplication
            async def execute():
                return await func(*args, **kwargs)

            return await single_flight_do(key, execute, group, timeout)

        return wrapper
    return decorator
