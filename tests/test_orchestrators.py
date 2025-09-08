"""
Test suite for Sophia and Artemis orchestrators
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.artemis.artemis_orchestrator import ArtemisOrchestrator
from app.orchestrators.base_orchestrator import ExecutionPriority, Result, Task, TaskStatus
from app.sophia.sophia_orchestrator import SophiaOrchestrator


@pytest.fixture
def mock_portkey_manager():
    """Mock Portkey manager"""
    with patch("app.orchestrators.base_orchestrator.get_portkey_manager") as mock:
        manager = MagicMock()
        manager.execute_with_fallback = AsyncMock(
            return_value={
                "choices": [{"message": {"content": "Test response", "role": "assistant"}}]
            }
        )
        mock.return_value = manager
        yield manager


@pytest.fixture
def mock_memory_router():
    """Mock memory router"""
    with patch("app.orchestrators.base_orchestrator.get_memory_router") as mock:
        router = MagicMock()
        router.get_ephemeral = AsyncMock(return_value=None)
        router.put_ephemeral = AsyncMock()
        router.upsert_chunks = AsyncMock()
        mock.return_value = router
        yield router


@pytest.fixture
def mock_secrets_manager():
    """Mock secrets manager"""
    with patch("app.orchestrators.base_orchestrator.get_secrets_manager") as mock:
        manager = MagicMock()
        manager.get_secret = MagicMock(return_value="test_secret")
        mock.return_value = manager
        yield manager


class TestBaseOrchestrator:
    """Test base orchestrator functionality"""

    @pytest.mark.asyncio
    async def test_task_creation(self):
        """Test task creation and validation"""
        task = Task(
            id="test-123",
            type="analysis",
            description="Test task",
            priority=ExecutionPriority.HIGH,
        )

        assert task.id == "test-123"
        assert task.type == "analysis"
        assert task.status == TaskStatus.PENDING
        assert task.priority == ExecutionPriority.HIGH

    @pytest.mark.asyncio
    async def test_result_creation(self):
        """Test result creation"""
        result = Result(
            task_id="test-123", success=True, data={"output": "test"}, execution_time=1.5
        )

        assert result.task_id == "test-123"
        assert result.success is True
        assert result.data["output"] == "test"
        assert result.execution_time == 1.5


class TestSophiaOrchestrator:
    """Test Sophia BI orchestrator"""

    @pytest.mark.asyncio
    async def test_initialization(self, mock_portkey_manager, mock_memory_router):
        """Test Sophia orchestrator initialization"""
        orchestrator = SophiaOrchestrator()

        assert orchestrator.domain == "business_intelligence"
        assert orchestrator._circuit_breaker is not None

    @pytest.mark.asyncio
    async def test_sales_forecast(self, mock_portkey_manager, mock_memory_router):
        """Test sales forecast generation"""
        orchestrator = SophiaOrchestrator()

        # Mock connector
        with patch.object(orchestrator, "connectors", {}):
            result = await orchestrator.generate_sales_forecast(period="Q1")

            assert "forecast" in result
            assert "period" in result
            assert result["period"] == "Q1"
            mock_portkey_manager.execute_with_fallback.assert_called()

    @pytest.mark.asyncio
    async def test_customer_health_analysis(self, mock_portkey_manager, mock_memory_router):
        """Test customer health analysis"""
        orchestrator = SophiaOrchestrator()

        with patch.object(orchestrator, "connectors", {}):
            result = await orchestrator.analyze_customer_health(account_ids=["acc1", "acc2"])

            assert "health_scores" in result
            assert "at_risk" in result
            mock_portkey_manager.execute_with_fallback.assert_called()

    @pytest.mark.asyncio
    async def test_competitive_analysis(self, mock_portkey_manager, mock_memory_router):
        """Test competitive analysis"""
        orchestrator = SophiaOrchestrator()

        result = await orchestrator.competitive_analysis(competitors=["Competitor1", "Competitor2"])

        assert "analysis" in result
        assert "competitors" in result
        assert len(result["competitors"]) == 2

    @pytest.mark.asyncio
    async def test_task_execution(
        self, mock_portkey_manager, mock_memory_router, mock_secrets_manager
    ):
        """Test task execution through orchestrator"""
        orchestrator = SophiaOrchestrator()

        task = Task(id="test-123", type="analysis", description="Analyze sales data")

        result = await orchestrator.execute(task)

        assert result.success is True
        assert result.task_id == "test-123"
        assert result.execution_time > 0


class TestArtemisOrchestrator:
    """Test Artemis code orchestrator"""

    @pytest.mark.asyncio
    async def test_initialization(self, mock_portkey_manager, mock_memory_router):
        """Test Artemis orchestrator initialization"""
        orchestrator = ArtemisOrchestrator()

        assert orchestrator.domain == "code_excellence"
        assert orchestrator._circuit_breaker is not None

    @pytest.mark.asyncio
    async def test_code_generation(self, mock_portkey_manager, mock_memory_router):
        """Test code generation"""
        orchestrator = ArtemisOrchestrator()

        mock_portkey_manager.execute_with_fallback.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "def test_function():\n    return 'test'",
                        "role": "assistant",
                    }
                }
            ]
        }

        result = await orchestrator.generate_code(
            specification="Create a function that returns 'test'", language="python"
        )

        assert "code" in result
        assert "language" in result
        assert result["language"] == "python"
        assert "def test_function" in result["code"]

    @pytest.mark.asyncio
    async def test_code_review(self, mock_portkey_manager, mock_memory_router):
        """Test code review"""
        orchestrator = ArtemisOrchestrator()

        code = """
        def bad_function():
            x = 1
            y = 2
            return x + y
        """

        mock_portkey_manager.execute_with_fallback.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "issues": ["Unused variable"],
                                "suggestions": ["Remove unused variables"],
                                "security": [],
                                "performance": [],
                            }
                        ),
                        "role": "assistant",
                    }
                }
            ]
        }

        result = await orchestrator.review_code(code=code, language="python")

        assert "review" in result
        assert "issues" in result["review"]
        assert len(result["review"]["issues"]) > 0

    @pytest.mark.asyncio
    async def test_code_refactor(self, mock_portkey_manager, mock_memory_router):
        """Test code refactoring"""
        orchestrator = ArtemisOrchestrator()

        original_code = """
        def messy_function():
            x=1;y=2
            return x+y
        """

        mock_portkey_manager.execute_with_fallback.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "refactored_code": "def clean_function():\n    x = 1\n    y = 2\n    return x + y",
                                "changes": ["Improved formatting", "Added proper spacing"],
                            }
                        ),
                        "role": "assistant",
                    }
                }
            ]
        }

        result = await orchestrator.refactor_code(
            code=original_code, goals=["improve readability", "follow PEP8"]
        )

        assert "refactored" in result
        assert "changes" in result
        assert len(result["changes"]) > 0

    @pytest.mark.asyncio
    async def test_generate_tests(self, mock_portkey_manager, mock_memory_router):
        """Test test generation"""
        orchestrator = ArtemisOrchestrator()

        code = """
        def add(a, b):
            return a + b
        """

        mock_portkey_manager.execute_with_fallback.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "def test_add():\n    assert add(1, 2) == 3\n    assert add(-1, 1) == 0",
                        "role": "assistant",
                    }
                }
            ]
        }

        result = await orchestrator.generate_tests(code=code, language="python")

        assert "tests" in result
        assert "test_add" in result["tests"]
        assert "assert" in result["tests"]


class TestIntegration:
    """Integration tests"""

    @pytest.mark.asyncio
    async def test_sophia_artemis_collaboration(
        self, mock_portkey_manager, mock_memory_router, mock_secrets_manager
    ):
        """Test collaboration between Sophia and Artemis"""
        sophia = SophiaOrchestrator()
        artemis = ArtemisOrchestrator()

        # Sophia generates requirements from BI analysis
        bi_task = Task(id="bi-123", type="analysis", description="Analyze customer churn patterns")

        bi_result = await sophia.execute(bi_task)
        assert bi_result.success

        # Artemis generates code based on requirements
        code_task = Task(
            id="code-123",
            type="code_generation",
            description="Generate churn prediction model",
            context=bi_result.data,
        )

        code_result = await artemis.execute(code_task)
        assert code_result.success

    @pytest.mark.asyncio
    async def test_circuit_breaker(self, mock_portkey_manager, mock_memory_router):
        """Test circuit breaker functionality"""
        orchestrator = SophiaOrchestrator()

        # Simulate failures
        mock_portkey_manager.execute_with_fallback.side_effect = Exception("API Error")

        # First few failures should be allowed
        for _ in range(3):
            task = Task(id=f"test-{_}", type="analysis", description="Test")
            result = await orchestrator.execute(task)
            assert not result.success

        # Circuit should be open now
        task = Task(id="test-final", type="analysis", description="Test")
        result = await orchestrator.execute(task)
        assert not result.success
        assert "circuit breaker" in result.error.lower()

    @pytest.mark.asyncio
    async def test_caching(self, mock_portkey_manager, mock_memory_router):
        """Test result caching"""
        orchestrator = ArtemisOrchestrator()

        # First call should execute
        task = Task(id="cache-test", type="code_review", description="Review code")
        result1 = await orchestrator.execute(task)

        # Set up cache hit
        mock_memory_router.get_ephemeral.return_value = json.dumps(
            {"task_id": task.id, "success": True, "data": {"cached": True}}
        )

        # Second call should use cache
        result2 = await orchestrator.execute(task)

        # Verify cache was checked
        assert mock_memory_router.get_ephemeral.called


@pytest.mark.asyncio
async def test_rate_limiting():
    """Test rate limiting across orchestrators"""
    # This would test actual rate limiting with time delays
    pass


@pytest.mark.asyncio
async def test_cost_tracking():
    """Test cost tracking functionality"""
    orchestrator = SophiaOrchestrator()

    # Reset costs
    orchestrator._reset_costs()

    # Track some costs
    orchestrator._track_cost(0.01)
    orchestrator._track_cost(0.02)

    costs = orchestrator.get_cost_summary()
    assert costs["session"] == 0.03
    assert costs["total"] >= 0.03


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
