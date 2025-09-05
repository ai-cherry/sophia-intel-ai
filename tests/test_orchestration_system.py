"""Tests for the AI Orchestration System.

This module tests the factory-aware orchestrator, evaluation swarm,
and micro-swarm configurations.
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.learning.evaluation_swarm import (
    GradeLevel,
    PerformanceAnalyst,
    QualityAuditor,
    RetrospectiveSwarm,
    SwarmGrade,
)
from app.orchestration.factory_aware_orchestrator import (
    AgentSpawnEvent,
    ComplexityAnalyzer,
    EventBroadcaster,
    FactoryAwareOrchestrator,
    OrchestratorRequest,
    RequestType,
)
from app.swarms.micro_swarms import (
    ConfidenceBasedRouter,
    MicroSwarmExecutor,
    MicroSwarmLibrary,
    SwarmPurpose,
)


class TestComplexityAnalyzer:
    """Test the complexity analyzer."""

    def test_simple_request_analysis(self):
        """Test analysis of a simple request."""
        analyzer = ComplexityAnalyzer()
        request = OrchestratorRequest(
            id="test-1",
            type=RequestType.BUSINESS_ANALYSIS,
            content="What are our sales numbers?",
            context={},
            user_id="user1",
            session_id="session1",
        )

        result = analyzer.analyze(request)

        assert result["category"] == "low"
        assert result["recommended_agents"] == 1
        assert 0 <= result["score"] <= 1.0

    def test_complex_request_analysis(self):
        """Test analysis of a complex request."""
        analyzer = ComplexityAnalyzer()
        request = OrchestratorRequest(
            id="test-2",
            type=RequestType.SECURITY_AUDIT,
            content=" ".join(["word"] * 600),  # Long content
            context={"multi_source": True, "critical": True},
            user_id="user1",
            session_id="session1",
        )

        result = analyzer.analyze(request)

        assert result["category"] == "high"
        assert result["recommended_agents"] == 3
        assert result["score"] >= 0.7


@pytest.mark.asyncio
class TestFactoryAwareOrchestrator:
    """Test the factory-aware orchestrator."""

    async def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        orchestrator = FactoryAwareOrchestrator()

        assert orchestrator.sophia_factory is not None
        assert orchestrator.artemis_factory is not None
        assert orchestrator.event_broadcaster is not None
        assert orchestrator.memory_router is not None

    async def test_factory_determination(self):
        """Test correct factory selection based on request type."""
        orchestrator = FactoryAwareOrchestrator()

        # Business request should use Sophia
        business_request = OrchestratorRequest(
            id="test-1",
            type=RequestType.BUSINESS_ANALYSIS,
            content="Analyze sales",
            context={},
            user_id="user1",
            session_id="session1",
        )
        assert orchestrator._determine_factory(business_request) == "sophia"

        # Code request should use Artemis
        code_request = OrchestratorRequest(
            id="test-2",
            type=RequestType.CODE_REVIEW,
            content="Review this code",
            context={},
            user_id="user1",
            session_id="session1",
        )
        assert orchestrator._determine_factory(code_request) == "artemis"

        # Hybrid request should use both
        hybrid_request = OrchestratorRequest(
            id="test-3",
            type=RequestType.HYBRID,
            content="Mixed request",
            context={},
            user_id="user1",
            session_id="session1",
        )
        assert orchestrator._determine_factory(hybrid_request) == "hybrid"

    async def test_cost_estimation(self):
        """Test cost estimation calculation."""
        orchestrator = FactoryAwareOrchestrator()

        agents = [{"id": "agent1", "template": "test1"}, {"id": "agent2", "template": "test2"}]
        complexity = {"category": "medium"}

        cost = orchestrator._estimate_cost(agents, complexity)

        assert cost > 0
        assert cost == 2 * 0.01 * 2.0  # 2 agents * base_cost * medium_multiplier

    @patch("app.orchestration.factory_aware_orchestrator.EventBroadcaster.publish")
    async def test_event_broadcasting(self, mock_publish):
        """Test that events are broadcast correctly."""
        mock_publish.return_value = asyncio.Future()
        mock_publish.return_value.set_result(None)

        orchestrator = FactoryAwareOrchestrator()

        request = OrchestratorRequest(
            id="test-1",
            type=RequestType.BUSINESS_ANALYSIS,
            content="Test content",
            context={},
            user_id="user1",
            session_id="session1",
        )

        # Mock the factory methods
        with patch.object(orchestrator, "_spawn_sophia_agents", return_value=[{"id": "agent1"}]):
            with patch.object(
                orchestrator, "_execute_with_streaming", return_value={"result": "success"}
            ):
                with patch.object(orchestrator, "_store_execution", return_value=None):
                    result = await orchestrator.process_request(request)

        # Verify events were published
        assert mock_publish.called
        call_args = [call[0][0] for call in mock_publish.call_args_list]
        assert "request_received" in call_args
        assert "agents_spawned" in call_args


class TestSwarmGrade:
    """Test the swarm grading system."""

    def test_grade_calculation(self):
        """Test grade calculation from scores."""
        grade = SwarmGrade(
            accuracy_score=95,
            completeness_score=90,
            clarity_score=85,
            speed_score=80,
            cost_efficiency=85,
            token_efficiency=75,
        )

        assert grade.overall_score > 80
        assert grade.grade == GradeLevel.A

    def test_failing_grade(self):
        """Test failing grade calculation."""
        grade = SwarmGrade(
            accuracy_score=50,
            completeness_score=45,
            clarity_score=40,
            speed_score=30,
            cost_efficiency=35,
            token_efficiency=25,
        )

        assert grade.overall_score < 60
        assert grade.grade == GradeLevel.F


@pytest.mark.asyncio
class TestEvaluationSwarm:
    """Test the evaluation swarm."""

    async def test_performance_analyst(self):
        """Test performance analysis."""
        analyst = PerformanceAnalyst()

        executions = [
            {"execution_time": 10, "total_tokens": 500},
            {"execution_time": 15, "total_tokens": 750},
            {"execution_time": 25, "total_tokens": 1000},  # Bottleneck
        ]

        result = await analyst.analyze(executions)

        assert result["total_executions"] == 3
        assert result["avg_execution_time"] == 50 / 3
        assert len(result["bottlenecks"]) >= 1  # Should identify slow execution
        assert result["recommendations"] is not None

    async def test_quality_auditor(self):
        """Test quality auditing."""
        auditor = QualityAuditor()

        executions = [
            {
                "execution_id": "exec1",
                "result": {
                    "synthesized_response": "Complete response",
                    "individual_results": {"agent1": {"confidence": 0.9}},
                },
            },
            {"execution_id": "exec2", "result": {}},  # Missing synthesized response
        ]

        result = await auditor.audit(executions)

        assert result["total_issues"] == 1
        assert result["avg_quality_score"] > 0
        assert result["avg_completeness_score"] > 0

    async def test_empty_project_evaluation(self):
        """Test evaluation with no data."""
        swarm = RetrospectiveSwarm()

        with patch.object(swarm, "_gather_executions", return_value=[]):
            report = await swarm.evaluate_project("empty-project")

        assert report.project_id == "empty-project"
        assert report.grade is not None
        assert "No data available" in report.recommendations[0]


class TestMicroSwarms:
    """Test micro-swarm configurations."""

    def test_library_configurations(self):
        """Test that all configurations are valid."""
        configs = MicroSwarmLibrary.get_all_configs()

        assert len(configs) > 0

        for name, config in configs.items():
            assert config.name is not None
            assert config.purpose is not None
            assert len(config.agents) > 0
            assert config.max_time > 0
            assert config.cost_limit > 0

    def test_get_by_purpose(self):
        """Test filtering configs by purpose."""
        configs = MicroSwarmLibrary.get_configs_by_purpose(SwarmPurpose.QUICK_ANALYSIS)

        assert len(configs) > 0
        assert all(c.purpose == SwarmPurpose.QUICK_ANALYSIS for c in configs)

    def test_get_under_cost(self):
        """Test filtering configs by cost."""
        configs = MicroSwarmLibrary.get_configs_under_cost(0.01)

        assert len(configs) > 0
        assert all(c.cost_limit <= 0.01 for c in configs)


@pytest.mark.asyncio
class TestConfidenceBasedRouter:
    """Test confidence-based routing."""

    async def test_no_escalation_high_confidence(self):
        """Test that high confidence doesn't trigger escalation."""
        router = ConfidenceBasedRouter()

        # Mock to return high confidence
        with patch.object(router, "_execute_tier", return_value={"confidence": 0.9, "cost": 0.01}):
            result = await router.route_request("Simple query")

        assert result["escalated"] is False
        assert result["final_tier"] == "tier1"
        assert len(result["attempts"]) == 1

    async def test_escalation_low_confidence(self):
        """Test that low confidence triggers escalation."""
        router = ConfidenceBasedRouter()

        # Mock to return low then high confidence
        async def mock_execute(request, models):
            if "gpt-4o-mini" in models[0]:
                return {"confidence": 0.5, "cost": 0.005}
            elif "gpt-4o" in models[0]:
                return {"confidence": 0.75, "cost": 0.02}
            else:
                return {"confidence": 0.85, "cost": 0.05}

        with patch.object(router, "_execute_tier", side_effect=mock_execute):
            result = await router.route_request("Complex query")

        assert result["escalated"] is True
        assert len(result["attempts"]) >= 2


@pytest.mark.asyncio
class TestMicroSwarmExecutor:
    """Test micro-swarm executor."""

    async def test_execute_valid_config(self):
        """Test execution with valid configuration."""
        executor = MicroSwarmExecutor()

        with patch.object(executor, "_execute_fixed", return_value={"success": True}):
            result = await executor.execute("quick_analysis", "Test request")

        assert result["success"] is True

    async def test_execute_invalid_config(self):
        """Test execution with invalid configuration."""
        executor = MicroSwarmExecutor()

        with pytest.raises(ValueError):
            await executor.execute("non_existent_config", "Test request")

    async def test_compare_configs(self):
        """Test A/B testing of configurations."""
        executor = MicroSwarmExecutor()

        with patch.object(
            executor,
            "execute",
            side_effect=[{"cost": 0.01, "execution_time": 5}, {"cost": 0.02, "execution_time": 3}],
        ):
            result = await executor.compare_configs(
                ["quick_analysis", "deep_analysis"], "Test request"
            )

        assert "winner" in result
        assert "scores" in result
        assert len(result["results"]) == 2


class TestIntegration:
    """Integration tests for the full system."""

    @pytest.mark.asyncio
    async def test_end_to_end_flow(self):
        """Test complete flow from request to evaluation."""
        # Create orchestrator
        orchestrator = FactoryAwareOrchestrator()

        # Create request
        request = OrchestratorRequest(
            id="integration-test",
            type=RequestType.BUSINESS_ANALYSIS,
            content="Analyze Q4 sales performance",
            context={"quarter": "Q4", "year": 2024},
            user_id="test-user",
            session_id="test-session",
        )

        # Mock the dependencies
        with patch.object(
            orchestrator,
            "_spawn_sophia_agents",
            return_value=[{"id": "agent1", "template": "sales_analyst"}],
        ):
            with patch.object(
                orchestrator,
                "_execute_with_streaming",
                return_value={
                    "execution_id": "test-exec",
                    "synthesized_response": "Analysis complete",
                    "total_tokens": 500,
                    "execution_time": 10.5,
                },
            ):
                with patch.object(orchestrator, "_store_execution", return_value=None):
                    # Process request
                    result = await orchestrator.process_request(request)

        assert result["request_id"] == "integration-test"
        assert result["factory"] == "sophia"
        assert "result" in result

        # Now evaluate the execution
        swarm = RetrospectiveSwarm()

        with patch.object(
            swarm,
            "_gather_executions",
            return_value=[
                {
                    "execution_id": result["result"]["execution_id"],
                    "result": result["result"],
                    "agents": result["agents_used"],
                    "status": "complete",
                }
            ],
        ):
            with patch.object(swarm, "_store_report", return_value=None):
                report = await swarm.evaluate_project("integration-test")

        assert report.project_id == "integration-test"
        assert report.grade is not None
        assert len(report.recommendations) > 0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
