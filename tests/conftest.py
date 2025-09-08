"""
Pytest Configuration and Shared Fixtures
Provides common fixtures and configuration for all tests
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import test fixtures
from tests.fixtures.mock_mcp_servers import (
    MockMCPServer,
    MockMCPServerCluster,
    create_artemis_mock_servers,
    create_shared_mock_server_cluster,
    create_sophia_mock_servers,
)
from tests.fixtures.test_agents import (
    MockAgent,
    create_artemis_test_swarm,
    create_failing_agent,
    create_mixed_test_swarm,
    create_rate_limited_agent,
    create_slow_agent,
    create_sophia_test_swarm,
    create_test_agent,
)

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


# ============= Event Loop Configuration =============


@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for Windows compatibility"""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    return asyncio.get_event_loop_policy()


@pytest.fixture
def event_loop(event_loop_policy):
    """Create event loop for async tests"""
    loop = event_loop_policy.new_event_loop()
    yield loop
    loop.close()


# ============= Domain Factories =============


@pytest.fixture
def artemis_factory():
    """Mock Artemis unified factory"""
    with patch("app.artemis.unified_factory.ArtemisUnifiedFactory") as MockFactory:
        factory = MockFactory.return_value

        # Configure factory methods
        factory.create_agent = AsyncMock()
        factory.create_swarm = AsyncMock()
        factory.create_tactical_swarm = AsyncMock()
        factory.get_concurrent_limit = MagicMock(return_value=8)
        factory.domain = "artemis"

        # Configure agent creation
        async def create_agent_impl(name, personality):
            return create_test_agent(name, "artemis", personality)

        factory.create_agent.side_effect = create_agent_impl

        # Configure swarm creation
        factory.create_swarm.return_value = create_artemis_test_swarm()
        factory.create_tactical_swarm.return_value = create_artemis_test_swarm()

        yield factory


@pytest.fixture
def sophia_factory():
    """Mock Sophia unified factory"""
    with patch("app.sophia.unified_factory.SophiaUnifiedFactory") as MockFactory:
        factory = MockFactory.return_value

        # Configure factory methods
        factory.create_agent = AsyncMock()
        factory.create_swarm = AsyncMock()
        factory.create_mythology_swarm = AsyncMock()
        factory.get_concurrent_limit = MagicMock(return_value=8)
        factory.domain = "sophia"

        # Configure agent creation
        async def create_agent_impl(name, personality):
            return create_test_agent(name, "sophia", personality)

        factory.create_agent.side_effect = create_agent_impl

        # Configure swarm creation
        factory.create_swarm.return_value = create_sophia_test_swarm()
        factory.create_mythology_swarm.return_value = create_sophia_test_swarm()

        yield factory


# ============= Domain Enforcer =============


@pytest.fixture
def domain_enforcer():
    """Mock domain enforcer"""
    with patch("app.core.domain_enforcer.DomainEnforcer") as MockEnforcer:
        enforcer = MockEnforcer.return_value

        # Configure enforcer methods
        enforcer.check_access = MagicMock(return_value=True)
        enforcer.validate_cross_domain = MagicMock(return_value=False)
        enforcer.request_approval = AsyncMock(return_value=True)
        enforcer.audit_log = MagicMock()

        # Configure access matrix
        enforcer.access_matrix = {
            "artemis": {"sophia": False, "shared": True},
            "sophia": {"artemis": False, "shared": True},
            "shared": {"artemis": True, "sophia": True},
        }

        yield enforcer


# ============= MCP Servers =============


@pytest.fixture
def artemis_mcp_servers() -> Dict[str, MockMCPServer]:
    """Create mock MCP servers for Artemis domain"""
    return create_artemis_mock_servers()


@pytest.fixture
def sophia_mcp_servers() -> Dict[str, MockMCPServer]:
    """Create mock MCP servers for Sophia domain"""
    return create_sophia_mock_servers()


@pytest.fixture
def shared_mcp_cluster() -> MockMCPServerCluster:
    """Create shared MCP server cluster"""
    return create_shared_mock_server_cluster()


@pytest.fixture
def mcp_router():
    """Mock MCP router"""
    with patch("app.mcp.router_config.MCPRouter") as MockRouter:
        router = MockRouter.return_value

        # Configure router methods
        router.route_request = AsyncMock()
        router.get_server = MagicMock()
        router.get_servers_for_domain = MagicMock()
        router.register_server = MagicMock()
        router.unregister_server = MagicMock()

        # Configure routing rules
        router.routing_rules = {
            "artemis": ["FILESYSTEM", "CODE_ANALYSIS"],
            "sophia": ["WEB_SEARCH"],
            "shared": ["DATABASE", "NOTIFICATION"],
        }

        yield router


@pytest.fixture
def mcp_connection_manager():
    """Mock MCP connection manager"""
    with patch("app.mcp.connection_manager.MCPConnectionManager") as MockManager:
        manager = MockManager.return_value

        # Configure manager methods
        manager.connect = AsyncMock(return_value=True)
        manager.disconnect = AsyncMock()
        manager.execute = AsyncMock()
        manager.get_connection = MagicMock()
        manager.is_connected = MagicMock(return_value=True)
        manager.reconnect = AsyncMock(return_value=True)

        # Configure connection pool
        manager.max_connections = 10
        manager.active_connections = 0
        manager.connection_pool = {}

        yield manager


# ============= Test Agents =============


@pytest.fixture
def artemis_test_agents() -> List[MockAgent]:
    """Create Artemis test agents"""
    return create_artemis_test_swarm()


@pytest.fixture
def sophia_test_agents() -> List[MockAgent]:
    """Create Sophia test agents"""
    return create_sophia_test_swarm()


@pytest.fixture
def mixed_test_agents() -> List[MockAgent]:
    """Create mixed domain test agents"""
    return create_mixed_test_swarm()


@pytest.fixture
def failing_agent() -> MockAgent:
    """Create an agent that always fails"""
    return create_failing_agent()


@pytest.fixture
def slow_agent() -> MockAgent:
    """Create an agent with slow responses"""
    return create_slow_agent(delay_seconds=2.0)


@pytest.fixture
def rate_limited_agent() -> MockAgent:
    """Create an agent with rate limiting"""
    return create_rate_limited_agent(max_requests=3)


# ============= Orchestrators =============


@pytest.fixture
def artemis_orchestrator(artemis_factory, domain_enforcer, mcp_router):
    """Mock Artemis orchestrator"""
    with patch(
        "app.artemis.artemis_orchestrator.ArtemisOrchestrator"
    ) as MockOrchestrator:
        orchestrator = MockOrchestrator.return_value

        # Set dependencies
        orchestrator.factory = artemis_factory
        orchestrator.domain_enforcer = domain_enforcer
        orchestrator.mcp_router = mcp_router

        # Configure methods
        orchestrator.execute_mission = AsyncMock()
        orchestrator.coordinate_swarm = AsyncMock()
        orchestrator.analyze_repository = AsyncMock()
        orchestrator.get_status = MagicMock()

        # Configure concurrent tasks
        orchestrator.concurrent_tasks = []
        orchestrator.max_concurrent = 8

        yield orchestrator


@pytest.fixture
def sophia_orchestrator(sophia_factory, domain_enforcer, mcp_router):
    """Mock Sophia orchestrator"""
    with patch("app.sophia.sophia_orchestrator.SophiaOrchestrator") as MockOrchestrator:
        orchestrator = MockOrchestrator.return_value

        # Set dependencies
        orchestrator.factory = sophia_factory
        orchestrator.domain_enforcer = domain_enforcer
        orchestrator.mcp_router = mcp_router

        # Configure methods
        orchestrator.execute_strategy = AsyncMock()
        orchestrator.coordinate_council = AsyncMock()
        orchestrator.analyze_market = AsyncMock()
        orchestrator.track_kpis = AsyncMock()
        orchestrator.get_metrics = MagicMock()

        # Configure concurrent tasks
        orchestrator.concurrent_tasks = []
        orchestrator.max_concurrent = 8

        yield orchestrator


# ============= Resilience Components =============


@pytest.fixture
def circuit_breaker():
    """Create test circuit breaker"""
    from app.core.resilience import CircuitBreaker, CircuitBreakerConfig

    config = CircuitBreakerConfig(failure_threshold=3, timeout=1, monitoring_window=10)

    breaker = CircuitBreaker("test_breaker", config)
    yield breaker
    breaker.reset()


@pytest.fixture
def retry_policy():
    """Create test retry policy"""
    from app.core.resilience import RetryConfig, RetryPolicy, RetryStrategy

    config = RetryConfig(
        max_attempts=3,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        initial_delay=0.1,
        max_delay=1.0,
        jitter=True,
    )

    policy = RetryPolicy(config)
    return policy


@pytest.fixture
def bulkhead():
    """Create test bulkhead"""
    from app.core.resilience import AsyncSemaphoreBulkhead, BulkheadConfig

    config = BulkheadConfig(max_concurrent=5, max_wait_duration=2.0, max_queue_size=10)

    bulkhead = AsyncSemaphoreBulkhead("test_bulkhead", config)
    return bulkhead


# ============= Test Data =============


@pytest.fixture
def sample_repository_data():
    """Sample repository data for testing"""
    return {
        "name": "test-repo",
        "url": "https://github.com/test/repo",
        "branch": "main",
        "files": ["src/main.py", "tests/test_main.py", "README.md"],
        "languages": ["Python"],
        "size": 1024,
        "last_commit": "abc123",
    }


@pytest.fixture
def sample_business_data():
    """Sample business data for testing"""
    return {
        "company": "Test Corp",
        "revenue": 1000000,
        "expenses": 750000,
        "profit_margin": 0.25,
        "growth_rate": 0.15,
        "market_share": 0.10,
        "kpis": {
            "customer_acquisition": 100,
            "customer_retention": 0.85,
            "average_order_value": 150,
        },
        "okrs": [
            {
                "objective": "Increase market share",
                "key_results": ["10% growth", "New product launch"],
            }
        ],
    }


@pytest.fixture
def sample_mission_data():
    """Sample mission data for Artemis testing"""
    return {
        "mission_id": "MISSION-001",
        "type": "reconnaissance",
        "priority": "high",
        "objectives": [
            "Scan repository",
            "Identify vulnerabilities",
            "Generate report",
        ],
        "resources": {"agents": 4, "time_limit": 300, "clearance": "secret"},
        "status": "pending",
    }


@pytest.fixture
def sample_strategy_data():
    """Sample strategy data for Sophia testing"""
    return {
        "strategy_id": "STRAT-001",
        "type": "growth",
        "timeline": "Q1-Q2",
        "goals": [
            "Expand market presence",
            "Launch new product line",
            "Improve customer satisfaction",
        ],
        "resources": {"budget": 500000, "team_size": 20, "duration_months": 6},
        "expected_roi": 1.5,
    }


# ============= Test Utilities =============


@pytest.fixture
def mock_async_sleep():
    """Mock asyncio.sleep for faster tests"""
    with patch("asyncio.sleep") as mock_sleep:
        mock_sleep.return_value = None
        yield mock_sleep


@pytest.fixture
def mock_datetime():
    """Mock datetime for consistent timestamps"""
    with patch("datetime.datetime") as mock_dt:
        mock_dt.utcnow.return_value = "2024-01-01T00:00:00Z"
        yield mock_dt


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create temporary directory for test files"""
    test_dir = tmp_path / "test_workspace"
    test_dir.mkdir()

    # Create some test files
    (test_dir / "test_file.txt").write_text("Test content")
    (test_dir / "config.yaml").write_text("test: true")

    src_dir = test_dir / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("print('Hello')")

    return test_dir


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set test environment variables"""
    test_env = {
        "TEST_MODE": "true",
        "LOG_LEVEL": "DEBUG",
        "MAX_CONCURRENT": "8",
        "DOMAIN": "test",
    }

    for key, value in test_env.items():
        monkeypatch.setenv(key, value)

    return test_env


# ============= Cleanup Fixtures =============


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests"""
    # Reset any global state or singletons
    yield

    # Cleanup after test
    # Add any necessary cleanup code here


@pytest.fixture(autouse=True)
def clear_caches():
    """Clear any caches between tests"""
    # Clear function caches, memoization, etc.
    yield

    # Clear after test
    # Add cache clearing code here


# ============= Performance Fixtures =============


@pytest.fixture
def benchmark_timer():
    """Simple benchmark timer for performance tests"""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.elapsed = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()
            self.elapsed = self.end_time - self.start_time
            return self.elapsed

        def __enter__(self):
            self.start()
            return self

        def __exit__(self, *args):
            self.stop()

    return Timer()


# ============= Markers =============


def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
    config.addinivalue_line("markers", "load: marks tests as load/performance tests")
    config.addinivalue_line(
        "markers", "artemis: marks tests specific to Artemis domain"
    )
    config.addinivalue_line("markers", "sophia: marks tests specific to Sophia domain")
    config.addinivalue_line(
        "markers", "resilience: marks tests for resilience patterns"
    )
