"""
MCP Connection Manager with Circuit Breakers, Retry Logic, and Health Monitoring
Centralizes connection management for the Sophia-Artemis consolidated system
"""

import asyncio
import logging
import random
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Connection states for circuit breaker"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit broken, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class RetryStrategy(Enum):
    """Retry strategies for failed connections"""

    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIBONACCI = "fibonacci"
    RANDOM_JITTER = "random_jitter"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""

    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: int = 60  # seconds
    half_open_requests: int = 3
    failure_rate_threshold: float = 0.5  # 50% failure rate
    monitoring_window: int = 60  # seconds


@dataclass
class RetryConfig:
    """Configuration for retry logic"""

    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: bool = True


@dataclass
class ConnectionPoolConfig:
    """Configuration for connection pool"""

    min_size: int = 2
    max_size: int = 10
    acquire_timeout: float = 30.0
    idle_timeout: float = 300.0
    max_lifetime: float = 3600.0
    validation_interval: float = 60.0


@dataclass
class Connection:
    """Represents an MCP connection"""

    id: str
    server_name: str
    endpoint: str
    created_at: datetime
    last_used: datetime
    state: str = "idle"
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self, max_lifetime: float) -> bool:
        """Check if connection has exceeded max lifetime"""
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age > max_lifetime

    def is_idle_timeout(self, idle_timeout: float) -> bool:
        """Check if connection has been idle too long"""
        idle_time = (datetime.utcnow() - self.last_used).total_seconds()
        return idle_time > idle_timeout


class CircuitBreaker:
    """
    Circuit breaker implementation for fault tolerance
    """

    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = ConnectionState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.half_open_attempts = 0
        self.request_history = deque(maxlen=100)

    def call(self, func: Callable) -> Any:
        """
        Execute function with circuit breaker protection

        Args:
            func: Function to execute

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == ConnectionState.OPEN:
            if self._should_attempt_reset():
                self.state = ConnectionState.HALF_OPEN
                self.half_open_attempts = 0
            else:
                raise Exception(f"Circuit breaker {self.name} is OPEN")

        try:
            result = func()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    async def async_call(self, func: Callable) -> Any:
        """
        Execute async function with circuit breaker protection

        Args:
            func: Async function to execute

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == ConnectionState.OPEN:
            if self._should_attempt_reset():
                self.state = ConnectionState.HALF_OPEN
                self.half_open_attempts = 0
            else:
                raise Exception(f"Circuit breaker {self.name} is OPEN")

        try:
            result = await func()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """Handle successful call"""
        self.request_history.append((datetime.utcnow(), True))

        if self.state == ConnectionState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = ConnectionState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info(f"Circuit breaker {self.name} CLOSED (recovered)")
        elif self.state == ConnectionState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)

    def _on_failure(self):
        """Handle failed call"""
        self.request_history.append((datetime.utcnow(), False))
        self.last_failure_time = datetime.utcnow()
        self.failure_count += 1

        if self.state == ConnectionState.HALF_OPEN:
            self.state = ConnectionState.OPEN
            logger.warning(f"Circuit breaker {self.name} OPEN (half-open test failed)")
        elif self.state == ConnectionState.CLOSED:
            if self._should_open_circuit():
                self.state = ConnectionState.OPEN
                logger.warning(f"Circuit breaker {self.name} OPEN (threshold exceeded)")

    def _should_open_circuit(self) -> bool:
        """Determine if circuit should open"""
        if self.failure_count >= self.config.failure_threshold:
            return True

        # Check failure rate
        recent_requests = [
            success
            for timestamp, success in self.request_history
            if (datetime.utcnow() - timestamp).total_seconds() <= self.config.monitoring_window
        ]

        if len(recent_requests) > 0:
            failure_rate = recent_requests.count(False) / len(recent_requests)
            return failure_rate >= self.config.failure_rate_threshold

        return False

    def _should_attempt_reset(self) -> bool:
        """Determine if circuit should attempt reset"""
        if not self.last_failure_time:
            return True

        time_since_failure = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return time_since_failure >= self.config.timeout

    def get_status(self) -> dict[str, Any]:
        """Get circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
        }


class RetryManager:
    """
    Manages retry logic with different strategies
    """

    def __init__(self, config: RetryConfig):
        self.config = config
        self.fibonacci_cache = [1, 1]

    async def execute_with_retry(
        self, func: Callable, context: Optional[dict[str, Any]] = None
    ) -> Any:
        """
        Execute function with retry logic

        Args:
            func: Function to execute
            context: Optional context for logging

        Returns:
            Function result

        Raises:
            Exception: If all retries exhausted
        """
        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func()
                else:
                    return func()
            except Exception as e:
                last_exception = e

                if attempt < self.config.max_attempts - 1:
                    delay = self._calculate_delay(attempt)

                    if self.config.jitter:
                        delay = self._add_jitter(delay)

                    logger.warning(
                        f"Retry attempt {attempt + 1}/{self.config.max_attempts} "
                        f"after {delay:.2f}s delay. Error: {e}"
                    )

                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All retry attempts exhausted. Last error: {e}")

        raise last_exception

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay based on retry strategy"""
        if self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.initial_delay * (2**attempt)
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.initial_delay * (attempt + 1)
        elif self.config.strategy == RetryStrategy.FIBONACCI:
            delay = self.config.initial_delay * self._get_fibonacci(attempt)
        else:  # RANDOM_JITTER
            delay = random.uniform(self.config.initial_delay, self.config.max_delay)

        return min(delay, self.config.max_delay)

    def _get_fibonacci(self, n: int) -> int:
        """Get nth Fibonacci number"""
        while len(self.fibonacci_cache) <= n:
            self.fibonacci_cache.append(self.fibonacci_cache[-1] + self.fibonacci_cache[-2])
        return self.fibonacci_cache[n]

    def _add_jitter(self, delay: float) -> float:
        """Add random jitter to delay"""
        jitter_range = delay * 0.1  # 10% jitter
        return delay + random.uniform(-jitter_range, jitter_range)


class ConnectionPool:
    """
    Connection pool for MCP servers
    """

    def __init__(self, name: str, config: ConnectionPoolConfig):
        self.name = name
        self.config = config
        self.connections: list[Connection] = []
        self.available_connections: asyncio.Queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(config.max_size)
        self.lock = asyncio.Lock()
        self.connection_counter = 0
        self.closed = False

        # Start background tasks
        asyncio.create_task(self._maintain_pool())
        asyncio.create_task(self._validate_connections())

    async def acquire(self) -> Connection:
        """
        Acquire a connection from the pool

        Returns:
            Connection object

        Raises:
            TimeoutError: If acquire timeout exceeded
        """
        if self.closed:
            raise Exception(f"Connection pool {self.name} is closed")

        try:
            # Try to get an available connection
            connection = await asyncio.wait_for(
                self.available_connections.get(), timeout=self.config.acquire_timeout
            )

            # Update last used time
            connection.last_used = datetime.utcnow()
            connection.state = "active"

            return connection

        except asyncio.TimeoutError:
            # Try to create a new connection if under max size
            async with self.lock:
                if len(self.connections) < self.config.max_size:
                    connection = await self._create_connection()
                    return connection

            raise TimeoutError(
                f"Failed to acquire connection from pool {self.name} "
                f"within {self.config.acquire_timeout}s"
            )

    async def release(self, connection: Connection):
        """
        Release a connection back to the pool

        Args:
            connection: Connection to release
        """
        if self.closed:
            await self._close_connection(connection)
            return

        connection.state = "idle"
        connection.last_used = datetime.utcnow()

        # Check if connection is still valid
        if connection.is_expired(self.config.max_lifetime) or connection.is_idle_timeout(
            self.config.idle_timeout
        ):
            await self._close_connection(connection)
            await self._ensure_min_connections()
        else:
            await self.available_connections.put(connection)

    async def _create_connection(self) -> Connection:
        """Create a new connection"""
        self.connection_counter += 1
        connection = Connection(
            id=f"{self.name}_{self.connection_counter}",
            server_name=self.name,
            endpoint="ws://localhost:8000/mcp",  # Placeholder
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow(),
            state="active",
        )

        self.connections.append(connection)
        logger.debug(f"Created connection {connection.id} for pool {self.name}")

        return connection

    async def _close_connection(self, connection: Connection):
        """Close and remove a connection"""
        try:
            # Actual connection closing logic would go here
            self.connections.remove(connection)
            logger.debug(f"Closed connection {connection.id}")
        except ValueError:
            pass  # Connection already removed

    async def _maintain_pool(self):
        """Maintain minimum pool size"""
        while not self.closed:
            await self._ensure_min_connections()
            await asyncio.sleep(10)  # Check every 10 seconds

    async def _ensure_min_connections(self):
        """Ensure minimum number of connections"""
        async with self.lock:
            current_size = len(self.connections)

            if current_size < self.config.min_size:
                for _ in range(self.config.min_size - current_size):
                    connection = await self._create_connection()
                    connection.state = "idle"
                    await self.available_connections.put(connection)

    async def _validate_connections(self):
        """Periodically validate connections"""
        while not self.closed:
            await asyncio.sleep(self.config.validation_interval)

            async with self.lock:
                invalid_connections = []

                for connection in self.connections:
                    if connection.is_expired(self.config.max_lifetime) or (
                        connection.state == "idle"
                        and connection.is_idle_timeout(self.config.idle_timeout)
                    ):
                        invalid_connections.append(connection)

                for connection in invalid_connections:
                    await self._close_connection(connection)

                await self._ensure_min_connections()

    async def close(self):
        """Close the connection pool"""
        self.closed = True

        async with self.lock:
            for connection in self.connections:
                await self._close_connection(connection)

            self.connections.clear()

        logger.info(f"Connection pool {self.name} closed")

    def get_stats(self) -> dict[str, Any]:
        """Get pool statistics"""
        active_count = sum(1 for c in self.connections if c.state == "active")
        idle_count = sum(1 for c in self.connections if c.state == "idle")

        return {
            "name": self.name,
            "total_connections": len(self.connections),
            "active_connections": active_count,
            "idle_connections": idle_count,
            "available_connections": self.available_connections.qsize(),
            "max_size": self.config.max_size,
            "min_size": self.config.min_size,
        }


class MCPConnectionManager:
    """
    Centralized MCP Connection Manager with circuit breakers,
    retry logic, connection pooling, and health monitoring
    """

    def __init__(self):
        # Connection pools
        self.pools: dict[str, ConnectionPool] = {}

        # Circuit breakers
        self.circuit_breakers: dict[str, CircuitBreaker] = {}

        # Retry managers
        self.retry_managers: dict[str, RetryManager] = {}

        # Health monitoring
        self.health_status: dict[str, bool] = {}
        self.health_check_tasks: dict[str, asyncio.Task] = {}

        # Metrics
        self.connection_metrics: dict[str, dict[str, Any]] = {}

        # Initialize manager
        self._initialize_manager()

    def _initialize_manager(self):
        """Initialize connection manager components"""

        # Create default configurations
        default_pool_config = ConnectionPoolConfig(
            min_size=2, max_size=10, acquire_timeout=30.0, idle_timeout=300.0
        )

        default_breaker_config = CircuitBreakerConfig(
            failure_threshold=5, timeout=60, half_open_requests=3
        )

        default_retry_config = RetryConfig(
            max_attempts=3, initial_delay=1.0, strategy=RetryStrategy.EXPONENTIAL
        )

        # Initialize pools for key servers
        server_names = [
            "artemis_filesystem",
            "artemis_code_analysis",
            "sophia_web_search",
            "sophia_analytics",
            "shared_database",
            "shared_indexing",
            "shared_embedding",
        ]

        for server_name in server_names:
            # Create connection pool
            self.pools[server_name] = ConnectionPool(server_name, default_pool_config)

            # Create circuit breaker
            self.circuit_breakers[server_name] = CircuitBreaker(server_name, default_breaker_config)

            # Create retry manager
            self.retry_managers[server_name] = RetryManager(default_retry_config)

            # Initialize health status
            self.health_status[server_name] = True

            # Start health monitoring
            self.health_check_tasks[server_name] = asyncio.create_task(
                self._monitor_health(server_name)
            )

    async def get_connection(self, server_name: str, domain: Optional[str] = None) -> Connection:
        """
        Get a connection with circuit breaker and retry protection

        Args:
            server_name: Name of the server
            domain: Optional domain context

        Returns:
            Connection object

        Raises:
            Exception: If unable to get connection
        """
        if server_name not in self.pools:
            raise ValueError(f"Unknown server: {server_name}")

        # Check health status
        if not self.health_status.get(server_name, False):
            raise Exception(f"Server {server_name} is unhealthy")

        # Get circuit breaker and retry manager
        circuit_breaker = self.circuit_breakers[server_name]
        retry_manager = self.retry_managers[server_name]

        # Define connection acquisition function
        async def acquire_connection():
            return await circuit_breaker.async_call(lambda: self.pools[server_name].acquire())

        # Execute with retry logic
        try:
            connection = await retry_manager.execute_with_retry(
                acquire_connection, context={"server": server_name, "domain": domain}
            )

            # Track metrics
            self._track_connection_acquired(server_name, domain)

            return connection

        except Exception as e:
            logger.error(f"Failed to get connection for {server_name}: {e}")
            self._track_connection_failed(server_name, domain)
            raise

    async def release_connection(self, connection: Connection, domain: Optional[str] = None):
        """
        Release a connection back to the pool

        Args:
            connection: Connection to release
            domain: Optional domain context
        """
        server_name = connection.server_name

        if server_name in self.pools:
            await self.pools[server_name].release(connection)
            self._track_connection_released(server_name, domain)
        else:
            logger.warning(f"Unknown pool for connection: {server_name}")

    async def _monitor_health(self, server_name: str):
        """
        Monitor health of a server

        Args:
            server_name: Server to monitor
        """
        while True:
            try:
                # Perform health check (placeholder implementation)
                health_check_passed = await self._perform_health_check(server_name)

                # Update health status
                old_status = self.health_status[server_name]
                self.health_status[server_name] = health_check_passed

                # Log status changes
                if old_status != health_check_passed:
                    if health_check_passed:
                        logger.info(f"Server {server_name} is now healthy")
                    else:
                        logger.warning(f"Server {server_name} is now unhealthy")

                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Health check error for {server_name}: {e}")
                self.health_status[server_name] = False
                await asyncio.sleep(30)

    async def _perform_health_check(self, server_name: str) -> bool:
        """
        Perform actual health check (placeholder)

        Args:
            server_name: Server to check

        Returns:
            True if healthy
        """
        # This would contain actual health check logic
        # For now, simulate with random success
        return random.random() > 0.1  # 90% success rate

    def _track_connection_acquired(self, server_name: str, domain: Optional[str]):
        """Track connection acquisition metrics"""
        if server_name not in self.connection_metrics:
            self.connection_metrics[server_name] = {
                "acquired": 0,
                "released": 0,
                "failed": 0,
                "by_domain": {},
            }

        self.connection_metrics[server_name]["acquired"] += 1

        if domain:
            if domain not in self.connection_metrics[server_name]["by_domain"]:
                self.connection_metrics[server_name]["by_domain"][domain] = {
                    "acquired": 0,
                    "released": 0,
                    "failed": 0,
                }
            self.connection_metrics[server_name]["by_domain"][domain]["acquired"] += 1

    def _track_connection_released(self, server_name: str, domain: Optional[str]):
        """Track connection release metrics"""
        if server_name in self.connection_metrics:
            self.connection_metrics[server_name]["released"] += 1

            if domain and domain in self.connection_metrics[server_name]["by_domain"]:
                self.connection_metrics[server_name]["by_domain"][domain]["released"] += 1

    def _track_connection_failed(self, server_name: str, domain: Optional[str]):
        """Track connection failure metrics"""
        if server_name in self.connection_metrics:
            self.connection_metrics[server_name]["failed"] += 1

            if domain and domain in self.connection_metrics[server_name]["by_domain"]:
                self.connection_metrics[server_name]["by_domain"][domain]["failed"] += 1

    def get_status(self) -> dict[str, Any]:
        """Get overall connection manager status"""
        return {
            "pools": {name: pool.get_stats() for name, pool in self.pools.items()},
            "circuit_breakers": {
                name: breaker.get_status() for name, breaker in self.circuit_breakers.items()
            },
            "health_status": self.health_status,
            "metrics": self.connection_metrics,
        }

    async def shutdown(self):
        """Shutdown connection manager"""
        # Cancel health check tasks
        for task in self.health_check_tasks.values():
            task.cancel()

        # Close all connection pools
        for pool in self.pools.values():
            await pool.close()

        logger.info("MCP Connection Manager shutdown complete")
