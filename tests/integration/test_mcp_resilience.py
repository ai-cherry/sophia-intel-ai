"""
Integration tests for MCP Resilience Features
Tests circuit breaker functionality, retry logic with exponential backoff,
connection pooling limits, and health monitoring with auto-reconnect
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.mcp.connection_manager import (
    CircuitBreaker,
    CircuitBreakerConfig,
    Connection,
    ConnectionPool,
    ConnectionPoolConfig,
    ConnectionState,
    MCPConnectionManager,
    RetryConfig,
    RetryManager,
    RetryStrategy,
)


class TestCircuitBreaker:
    """Test suite for Circuit Breaker functionality"""

    @pytest.fixture
    def breaker_config(self):
        """Create a circuit breaker configuration"""
        return CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout=5,  # Short timeout for testing
            half_open_requests=3,
            failure_rate_threshold=0.5,
            monitoring_window=10,
        )

    @pytest.fixture
    def circuit_breaker(self, breaker_config):
        """Create a circuit breaker instance"""
        return CircuitBreaker("test_server", breaker_config)

    def test_circuit_breaker_initial_state(self, circuit_breaker):
        """Test that circuit breaker starts in CLOSED state"""
        assert circuit_breaker.state == ConnectionState.CLOSED
        assert circuit_breaker.failure_count == 0
        assert circuit_breaker.success_count == 0
        assert circuit_breaker.last_failure_time is None

    def test_circuit_breaker_opens_on_failure_threshold(self, circuit_breaker):
        """Test that circuit breaker opens when failure threshold is reached"""

        def failing_function():
            raise Exception("Test failure")

        # First failures don't open the circuit
        for i in range(2):
            with pytest.raises(Exception):
                circuit_breaker.call(failing_function)
            assert circuit_breaker.state == ConnectionState.CLOSED

        # Third failure should open the circuit
        with pytest.raises(Exception):
            circuit_breaker.call(failing_function)

        assert circuit_breaker.state == ConnectionState.OPEN
        assert circuit_breaker.failure_count == 3

    def test_circuit_breaker_rejects_calls_when_open(self, circuit_breaker):
        """Test that circuit breaker rejects calls when in OPEN state"""
        # Force circuit to open
        circuit_breaker.state = ConnectionState.OPEN
        circuit_breaker.last_failure_time = datetime.utcnow()

        def test_function():
            return "success"

        with pytest.raises(Exception) as exc_info:
            circuit_breaker.call(test_function)

        assert "Circuit breaker test_server is OPEN" in str(exc_info.value)

    def test_circuit_breaker_half_open_state_transition(self, circuit_breaker):
        """Test transition from OPEN to HALF_OPEN after timeout"""
        # Force circuit to open
        circuit_breaker.state = ConnectionState.OPEN
        circuit_breaker.last_failure_time = datetime.utcnow() - timedelta(seconds=10)

        def test_function():
            return "success"

        # Should transition to HALF_OPEN and allow the call
        result = circuit_breaker.call(test_function)

        assert result == "success"
        assert circuit_breaker.state == ConnectionState.HALF_OPEN

    def test_circuit_breaker_closes_after_success_threshold(self, circuit_breaker):
        """Test that circuit breaker closes after success threshold in HALF_OPEN"""
        circuit_breaker.state = ConnectionState.HALF_OPEN
        circuit_breaker.config.success_threshold = 2

        def test_function():
            return "success"

        # First success
        circuit_breaker.call(test_function)
        assert circuit_breaker.state == ConnectionState.HALF_OPEN
        assert circuit_breaker.success_count == 1

        # Second success should close the circuit
        circuit_breaker.call(test_function)
        assert circuit_breaker.state == ConnectionState.CLOSED
        assert circuit_breaker.success_count == 0
        assert circuit_breaker.failure_count == 0

    def test_circuit_breaker_reopens_on_half_open_failure(self, circuit_breaker):
        """Test that circuit reopens if test fails in HALF_OPEN state"""
        circuit_breaker.state = ConnectionState.HALF_OPEN

        def failing_function():
            raise Exception("Test failure")

        with pytest.raises(Exception):
            circuit_breaker.call(failing_function)

        assert circuit_breaker.state == ConnectionState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_breaker_async_call(self, circuit_breaker):
        """Test circuit breaker with async functions"""

        async def async_success():
            return "async_success"

        async def async_failure():
            raise Exception("Async failure")

        # Test successful async call
        result = await circuit_breaker.async_call(async_success)
        assert result == "async_success"

        # Test failing async calls
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.async_call(async_failure)

        assert circuit_breaker.state == ConnectionState.OPEN

    def test_circuit_breaker_failure_rate_threshold(self, circuit_breaker):
        """Test that circuit opens based on failure rate"""
        circuit_breaker.config.failure_rate_threshold = 0.5
        circuit_breaker.config.failure_threshold = 100  # High threshold

        def success_function():
            return "success"

        def failure_function():
            raise Exception("Failure")

        # Add successful calls
        for _ in range(5):
            circuit_breaker.call(success_function)

        # Add failures to exceed 50% failure rate
        for _ in range(6):
            try:
                circuit_breaker.call(failure_function)
            except Exception:pass

        # Circuit should be open due to failure rate
        assert circuit_breaker.state == ConnectionState.OPEN

    def test_circuit_breaker_get_status(self, circuit_breaker):
        """Test getting circuit breaker status"""
        circuit_breaker.failure_count = 2
        circuit_breaker.success_count = 1
        circuit_breaker.last_failure_time = datetime.utcnow()

        status = circuit_breaker.get_status()

        assert status["name"] == "test_server"
        assert status["state"] == "closed"
        assert status["failure_count"] == 2
        assert status["success_count"] == 1
        assert status["last_failure"] is not None


class TestRetryManager:
    """Test suite for Retry Manager with various strategies"""

    @pytest.fixture
    def exponential_retry_config(self):
        """Create exponential retry configuration"""
        return RetryConfig(
            max_attempts=3,
            initial_delay=1.0,
            max_delay=10.0,
            strategy=RetryStrategy.EXPONENTIAL,
            jitter=False,
        )

    @pytest.fixture
    def linear_retry_config(self):
        """Create linear retry configuration"""
        return RetryConfig(
            max_attempts=3,
            initial_delay=1.0,
            max_delay=10.0,
            strategy=RetryStrategy.LINEAR,
            jitter=False,
        )

    @pytest.fixture
    def fibonacci_retry_config(self):
        """Create Fibonacci retry configuration"""
        return RetryConfig(
            max_attempts=3,
            initial_delay=1.0,
            max_delay=10.0,
            strategy=RetryStrategy.FIBONACCI,
            jitter=False,
        )

    @pytest.mark.asyncio
    async def test_exponential_backoff_retry(self, exponential_retry_config):
        """Test retry with exponential backoff strategy"""
        retry_manager = RetryManager(exponential_retry_config)

        attempt_count = 0
        delays = []

        async def failing_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception(f"Attempt {attempt_count} failed")
            return "success"

        # Mock sleep to capture delays
        with patch("asyncio.sleep") as mock_sleep:
            mock_sleep.side_effect = lambda d: delays.append(d)

            result = await retry_manager.execute_with_retry(failing_function)

            assert result == "success"
            assert attempt_count == 3
            assert len(delays) == 2  # Two retries

            # Check exponential delays: 1*2^0=1, 1*2^1=2
            assert delays[0] == 1.0
            assert delays[1] == 2.0

    @pytest.mark.asyncio
    async def test_linear_backoff_retry(self, linear_retry_config):
        """Test retry with linear backoff strategy"""
        retry_manager = RetryManager(linear_retry_config)

        attempt_count = 0
        delays = []

        async def failing_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception(f"Attempt {attempt_count} failed")
            return "success"

        with patch("asyncio.sleep") as mock_sleep:
            mock_sleep.side_effect = lambda d: delays.append(d)

            result = await retry_manager.execute_with_retry(failing_function)

            assert result == "success"
            assert len(delays) == 2

            # Check linear delays: 1*1=1, 1*2=2
            assert delays[0] == 1.0
            assert delays[1] == 2.0

    @pytest.mark.asyncio
    async def test_fibonacci_backoff_retry(self, fibonacci_retry_config):
        """Test retry with Fibonacci backoff strategy"""
        retry_manager = RetryManager(fibonacci_retry_config)

        attempt_count = 0
        delays = []

        async def failing_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 4:
                raise Exception(f"Attempt {attempt_count} failed")
            return "success"

        # Increase max attempts for Fibonacci test
        retry_manager.config.max_attempts = 4

        with patch("asyncio.sleep") as mock_sleep:
            mock_sleep.side_effect = lambda d: delays.append(d)

            result = await retry_manager.execute_with_retry(failing_function)

            assert result == "success"
            assert len(delays) == 3

            # Check Fibonacci delays: 1*1=1, 1*1=1, 1*2=2
            assert delays[0] == 1.0
            assert delays[1] == 1.0
            assert delays[2] == 2.0

    @pytest.mark.asyncio
    async def test_retry_with_jitter(self):
        """Test retry with jitter added to delays"""
        config = RetryConfig(
            max_attempts=3,
            initial_delay=1.0,
            max_delay=10.0,
            strategy=RetryStrategy.EXPONENTIAL,
            jitter=True,
        )
        retry_manager = RetryManager(config)

        attempt_count = 0
        delays = []

        async def failing_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception(f"Attempt {attempt_count} failed")
            return "success"

        with patch("asyncio.sleep") as mock_sleep:
            mock_sleep.side_effect = lambda d: delays.append(d)

            result = await retry_manager.execute_with_retry(failing_function)

            assert result == "success"
            assert len(delays) == 2

            # With jitter, delays should be within 10% of base delay
            assert 0.9 <= delays[0] <= 1.1  # 1.0 ± 10%
            assert 1.8 <= delays[1] <= 2.2  # 2.0 ± 10%

    @pytest.mark.asyncio
    async def test_retry_max_delay_cap(self):
        """Test that retry delays are capped at max_delay"""
        config = RetryConfig(
            max_attempts=5,
            initial_delay=1.0,
            max_delay=3.0,  # Low cap
            strategy=RetryStrategy.EXPONENTIAL,
            jitter=False,
        )
        retry_manager = RetryManager(config)

        delays = []
        attempt_count = 0

        async def failing_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 5:
                raise Exception("Failed")
            return "success"

        with patch("asyncio.sleep") as mock_sleep:
            mock_sleep.side_effect = lambda d: delays.append(d)

            result = await retry_manager.execute_with_retry(failing_function)

            # Check that no delay exceeds max_delay
            assert all(delay <= 3.0 for delay in delays)
            # Later delays should be capped at 3.0
            assert delays[-1] == 3.0

    @pytest.mark.asyncio
    async def test_retry_exhaustion_raises_last_exception(
        self, exponential_retry_config
    ):
        """Test that exhausting retries raises the last exception"""
        retry_manager = RetryManager(exponential_retry_config)

        async def always_failing():
            raise ValueError("Persistent failure")

        with patch("asyncio.sleep"):  # Skip actual delays
            with pytest.raises(ValueError) as exc_info:
                await retry_manager.execute_with_retry(always_failing)

            assert "Persistent failure" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_retry_with_sync_function(self, exponential_retry_config):
        """Test retry with synchronous function"""
        retry_manager = RetryManager(exponential_retry_config)

        attempt_count = 0

        def sync_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise Exception("Sync failure")
            return "sync_success"

        with patch("asyncio.sleep"):
            result = await retry_manager.execute_with_retry(sync_function)

            assert result == "sync_success"
            assert attempt_count == 2


class TestConnectionPool:
    """Test suite for Connection Pool functionality"""

    @pytest.fixture
    def pool_config(self):
        """Create connection pool configuration"""
        return ConnectionPoolConfig(
            min_size=2,
            max_size=5,
            acquire_timeout=1.0,
            idle_timeout=10.0,
            max_lifetime=60.0,
            validation_interval=5.0,
        )

    @pytest.fixture
    async def connection_pool(self, pool_config):
        """Create connection pool instance"""
        with patch("asyncio.create_task"):  # Prevent background tasks
            pool = ConnectionPool("test_pool", pool_config)
            yield pool
            if not pool.closed:
                await pool.close()

    @pytest.mark.asyncio
    async def test_connection_pool_initialization(self, connection_pool):
        """Test that connection pool initializes correctly"""
        assert connection_pool.name == "test_pool"
        assert connection_pool.closed is False
        assert connection_pool.connection_counter == 0
        assert len(connection_pool.connections) == 0

    @pytest.mark.asyncio
    async def test_acquire_connection(self, connection_pool):
        """Test acquiring a connection from the pool"""
        connection = await connection_pool.acquire()

        assert connection is not None
        assert connection.id == "test_pool_1"
        assert connection.state == "active"
        assert connection.server_name == "test_pool"
        assert len(connection_pool.connections) == 1

    @pytest.mark.asyncio
    async def test_release_connection(self, connection_pool):
        """Test releasing a connection back to the pool"""
        connection = await connection_pool.acquire()
        initial_last_used = connection.last_used

        await asyncio.sleep(0.1)  # Small delay
        await connection_pool.release(connection)

        assert connection.state == "idle"
        assert connection.last_used > initial_last_used

    @pytest.mark.asyncio
    async def test_connection_pool_max_size_limit(self, connection_pool):
        """Test that pool respects max_size limit"""
        connections = []

        # Acquire max connections
        for _ in range(5):  # max_size = 5
            conn = await connection_pool._create_connection()
            connections.append(conn)

        assert len(connection_pool.connections) == 5

        # Try to exceed limit - should timeout
        connection_pool.available_connections = asyncio.Queue()  # Empty queue

        with pytest.raises(asyncio.TimeoutError):
            await connection_pool.acquire()

    @pytest.mark.asyncio
    async def test_connection_expiry(self, connection_pool):
        """Test that expired connections are detected"""
        connection = Connection(
            id="test_conn",
            server_name="test_pool",
            endpoint="ws://test",
            created_at=datetime.utcnow() - timedelta(seconds=120),  # Old connection
            last_used=datetime.utcnow(),
        )

        assert connection.is_expired(60.0) is True  # max_lifetime = 60s
        assert connection.is_expired(180.0) is False

    @pytest.mark.asyncio
    async def test_connection_idle_timeout(self, connection_pool):
        """Test that idle connections are detected"""
        connection = Connection(
            id="test_conn",
            server_name="test_pool",
            endpoint="ws://test",
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow() - timedelta(seconds=20),  # Idle for 20s
        )

        assert connection.is_idle_timeout(10.0) is True  # idle_timeout = 10s
        assert connection.is_idle_timeout(30.0) is False

    @pytest.mark.asyncio
    async def test_ensure_min_connections(self, connection_pool):
        """Test that pool maintains minimum connections"""
        await connection_pool._ensure_min_connections()

        # Should create min_size connections
        assert connection_pool.available_connections.qsize() == 2  # min_size = 2

    @pytest.mark.asyncio
    async def test_connection_pool_close(self, connection_pool):
        """Test closing the connection pool"""
        # Create some connections
        conn1 = await connection_pool._create_connection()
        conn2 = await connection_pool._create_connection()

        assert len(connection_pool.connections) == 2

        await connection_pool.close()

        assert connection_pool.closed is True
        assert len(connection_pool.connections) == 0

    @pytest.mark.asyncio
    async def test_connection_pool_stats(self, connection_pool):
        """Test getting pool statistics"""
        # Create connections in different states
        active_conn = await connection_pool._create_connection()
        active_conn.state = "active"

        idle_conn = await connection_pool._create_connection()
        idle_conn.state = "idle"
        await connection_pool.available_connections.put(idle_conn)

        stats = connection_pool.get_stats()

        assert stats["name"] == "test_pool"
        assert stats["total_connections"] == 2
        assert stats["active_connections"] == 1
        assert stats["idle_connections"] == 1
        assert stats["available_connections"] == 1
        assert stats["max_size"] == 5
        assert stats["min_size"] == 2


class TestMCPConnectionManager:
    """Test suite for MCP Connection Manager with all resilience features"""

    @pytest.fixture
    async def connection_manager(self):
        """Create connection manager instance"""
        with patch("asyncio.create_task"):  # Prevent background tasks
            manager = MCPConnectionManager()
            yield manager
            await manager.shutdown()

    @pytest.mark.asyncio
    async def test_connection_manager_initialization(self, connection_manager):
        """Test that connection manager initializes with all components"""
        # Check pools created
        assert "artemis_filesystem" in connection_manager.pools
        assert "sophia_web_search" in connection_manager.pools
        assert "shared_database" in connection_manager.pools

        # Check circuit breakers created
        assert "artemis_filesystem" in connection_manager.circuit_breakers
        assert "sophia_analytics" in connection_manager.circuit_breakers

        # Check retry managers created
        assert "artemis_code_analysis" in connection_manager.retry_managers
        assert "shared_indexing" in connection_manager.retry_managers

        # Check health status initialized
        assert all(
            status is True for status in connection_manager.health_status.values()
        )

    @pytest.mark.asyncio
    async def test_get_connection_with_circuit_breaker(self, connection_manager):
        """Test getting connection with circuit breaker protection"""
        # Mock the pool's acquire method
        mock_connection = MagicMock(spec=Connection)
        mock_connection.server_name = "artemis_filesystem"

        connection_manager.pools["artemis_filesystem"].acquire = AsyncMock(
            return_value=mock_connection
        )

        connection = await connection_manager.get_connection("artemis_filesystem")

        assert connection == mock_connection
        assert (
            connection_manager.connection_metrics["artemis_filesystem"]["acquired"] == 1
        )

    @pytest.mark.asyncio
    async def test_get_connection_with_unhealthy_server(self, connection_manager):
        """Test that unhealthy servers reject connections"""
        connection_manager.health_status["artemis_filesystem"] = False

        with pytest.raises(Exception) as exc_info:
            await connection_manager.get_connection("artemis_filesystem")

        assert "artemis_filesystem is unhealthy" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_connection_with_retry_on_failure(self, connection_manager):
        """Test connection acquisition with retry on failure"""
        attempt_count = 0

        async def mock_acquire():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Connection failed")
            return MagicMock(spec=Connection, server_name="artemis_filesystem")

        connection_manager.pools["artemis_filesystem"].acquire = mock_acquire

        with patch("asyncio.sleep"):  # Skip delays
            connection = await connection_manager.get_connection("artemis_filesystem")

        assert connection is not None
        assert attempt_count == 3

    @pytest.mark.asyncio
    async def test_release_connection(self, connection_manager):
        """Test releasing connection back to pool"""
        mock_connection = MagicMock(spec=Connection)
        mock_connection.server_name = "artemis_filesystem"

        connection_manager.pools["artemis_filesystem"].release = AsyncMock()

        await connection_manager.release_connection(mock_connection, "artemis")

        connection_manager.pools["artemis_filesystem"].release.assert_called_once_with(
            mock_connection
        )
        assert (
            connection_manager.connection_metrics["artemis_filesystem"]["released"] == 1
        )

    @pytest.mark.asyncio
    async def test_health_monitoring_status_change(self, connection_manager):
        """Test health monitoring detects status changes"""
        # Mock health check to fail
        connection_manager._perform_health_check = AsyncMock(return_value=False)

        # Simulate health check
        connection_manager.health_status["test_server"] = True

        # Run one iteration of health monitoring
        await connection_manager._monitor_health("test_server")

        assert connection_manager.health_status["test_server"] is False

    @pytest.mark.asyncio
    async def test_connection_metrics_tracking(self, connection_manager):
        """Test that connection metrics are properly tracked"""
        # Track acquisition
        connection_manager._track_connection_acquired("test_server", "artemis")

        metrics = connection_manager.connection_metrics["test_server"]
        assert metrics["acquired"] == 1
        assert metrics["by_domain"]["artemis"]["acquired"] == 1

        # Track release
        connection_manager._track_connection_released("test_server", "artemis")
        assert metrics["released"] == 1
        assert metrics["by_domain"]["artemis"]["released"] == 1

        # Track failure
        connection_manager._track_connection_failed("test_server", "artemis")
        assert metrics["failed"] == 1
        assert metrics["by_domain"]["artemis"]["failed"] == 1

    @pytest.mark.asyncio
    async def test_get_status_comprehensive(self, connection_manager):
        """Test getting comprehensive status of connection manager"""
        status = connection_manager.get_status()

        assert "pools" in status
        assert "circuit_breakers" in status
        assert "health_status" in status
        assert "metrics" in status

        # Check pool status
        assert "artemis_filesystem" in status["pools"]
        pool_status = status["pools"]["artemis_filesystem"]
        assert "total_connections" in pool_status
        assert "active_connections" in pool_status

        # Check circuit breaker status
        assert "sophia_web_search" in status["circuit_breakers"]
        breaker_status = status["circuit_breakers"]["sophia_web_search"]
        assert "state" in breaker_status
        assert "failure_count" in breaker_status

    @pytest.mark.asyncio
    async def test_connection_manager_shutdown(self, connection_manager):
        """Test proper shutdown of connection manager"""
        # Create mock health check tasks
        mock_task = MagicMock()
        connection_manager.health_check_tasks = {"test_server": mock_task}

        # Mock pool close
        for pool in connection_manager.pools.values():
            pool.close = AsyncMock()

        await connection_manager.shutdown()

        # Check tasks cancelled
        mock_task.cancel.assert_called_once()

        # Check pools closed
        for pool in connection_manager.pools.values():
            pool.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self, connection_manager):
        """Test that circuit breaker opens after repeated failures"""
        breaker = connection_manager.circuit_breakers["artemis_filesystem"]

        async def failing_acquire():
            raise Exception("Connection failed")

        connection_manager.pools["artemis_filesystem"].acquire = failing_acquire

        # Attempt connections until circuit opens
        for _ in range(5):  # failure_threshold = 5
            try:
                with patch("asyncio.sleep"):  # Skip retry delays
                    await connection_manager.get_connection("artemis_filesystem")
            except Exception:pass

        # Circuit should now be open
        assert breaker.state == ConnectionState.OPEN

    @pytest.mark.asyncio
    async def test_auto_reconnect_after_circuit_recovery(self, connection_manager):
        """Test auto-reconnect after circuit breaker recovery timeout"""
        breaker = connection_manager.circuit_breakers["artemis_filesystem"]

        # Force circuit open
        breaker.state = ConnectionState.OPEN
        breaker.last_failure_time = datetime.utcnow() - timedelta(
            seconds=70
        )  # Past timeout

        # Mock successful connection
        mock_connection = MagicMock(spec=Connection, server_name="artemis_filesystem")
        connection_manager.pools["artemis_filesystem"].acquire = AsyncMock(
            return_value=mock_connection
        )

        # Should transition to HALF_OPEN and attempt connection
        connection = await connection_manager.get_connection("artemis_filesystem")

        assert connection is not None
        assert breaker.state == ConnectionState.HALF_OPEN
