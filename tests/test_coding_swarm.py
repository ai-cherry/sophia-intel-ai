"""
Comprehensive tests for the Coding Swarm system.

This module tests all components of the coding swarm including team creation,
orchestration, validation, memory integration, and error handling.
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.swarms import SwarmOrchestrator
from app.swarms.coding.models import (
    CriticOutput,
    CriticVerdict,
    DebateResult,
    GateDecision,
    JudgeDecision,
    JudgeOutput,
    PoolType,
    RiskLevel,
    SwarmConfiguration,
    SwarmRequest,
)
from app.swarms.coding.team import (
    execute_swarm_request,
    make_coding_swarm,
    make_coding_swarm_pool,
    run_coding_debate,
)
from app.swarms.coding.team_factory import TeamFactory


class TestModels:
    """Test Pydantic models for type validation."""

    def test_critic_output_validation(self):
        """Test CriticOutput model validation."""
        # Valid critic output
        critic = CriticOutput(
            verdict=CriticVerdict.PASS,
            findings={"security": ["No issues found"]},
            must_fix=[],
            nice_to_have=["Add more comments"],
            confidence_score=0.9
        )
        assert critic.verdict == CriticVerdict.PASS
        assert critic.confidence_score == 0.9

        # Test alias for nice_to_haves
        critic2 = CriticOutput(
            verdict=CriticVerdict.REVISE,
            nice_to_haves=["Improve naming"]  # Using alias
        )
        assert critic2.nice_to_have == ["Improve naming"]

    def test_judge_output_validation(self):
        """Test JudgeOutput model validation."""
        judge = JudgeOutput(
            decision=JudgeDecision.ACCEPT,
            runner_instructions=["Apply patch", "Run tests"],
            rationale="Code meets all requirements",
            confidence_score=0.95,
            risk_assessment=RiskLevel.LOW
        )
        assert judge.decision == JudgeDecision.ACCEPT
        assert len(judge.runner_instructions) == 2
        assert judge.risk_assessment == RiskLevel.LOW

    def test_gate_decision_validation(self):
        """Test GateDecision model validation."""
        gate = GateDecision(
            allowed=True,
            reason="All checks passed",
            accuracy_score=8.5,
            reliability_passed=True,
            risk_level=RiskLevel.MEDIUM,
            requires_approval=False
        )
        assert gate.allowed is True
        assert gate.accuracy_score == 8.5

        # Test score bounds
        with pytest.raises(ValueError):
            GateDecision(
                allowed=False,
                reason="Invalid",
                accuracy_score=11.0,  # Out of bounds
                reliability_passed=True,
                risk_level=RiskLevel.LOW
            )

    def test_swarm_configuration_validation(self):
        """Test SwarmConfiguration model validation."""
        config = SwarmConfiguration(
            pool=PoolType.HEAVY,
            concurrent_models=["gpt-4", "claude-3"],
            max_generators=6,
            accuracy_threshold=8.0,
            enable_file_write=True
        )
        assert config.pool == PoolType.HEAVY
        assert len(config.concurrent_models) == 2
        assert config.max_generators == 6

        # Test bounds
        with pytest.raises(ValueError):
            SwarmConfiguration(max_generators=0)  # Too low

        with pytest.raises(ValueError):
            SwarmConfiguration(max_generators=11)  # Too high

    def test_debate_result_structure(self):
        """Test DebateResult model structure."""
        result = DebateResult(
            task="Implement feature X",
            team_id="coding-swarm",
            session_id="session-123"
        )
        assert result.task == "Implement feature X"
        assert result.errors == []
        assert result.runner_approved is False
        assert isinstance(result.timestamp, datetime)


class TestTeamFactory:
    """Test the TeamFactory for team creation."""

    @patch('app.swarms.coding.team_factory.make_lead')
    @patch('app.swarms.coding.team_factory.make_critic')
    @patch('app.swarms.coding.team_factory.make_judge')
    def test_create_basic_team(self, mock_judge, mock_critic, mock_lead):
        """Test creating a basic team."""
        mock_lead.return_value = Mock(name="Lead")
        mock_critic.return_value = Mock(name="Critic")
        mock_judge.return_value = Mock(name="Judge")

        config = SwarmConfiguration(
            pool=PoolType.FAST,
            include_default_pair=False,
            include_runner=False
        )

        team = TeamFactory.create_team(config)

        assert team is not None
        mock_lead.assert_called_once()
        mock_critic.assert_called_once()
        mock_judge.assert_called_once()

    def test_validate_configuration(self):
        """Test configuration validation."""
        # Valid config
        config = SwarmConfiguration(
            max_generators=5,
            accuracy_threshold=7.5
        )
        TeamFactory.validate_configuration(config)  # Should not raise

        # Invalid configs
        with pytest.raises(ValueError, match="max_generators"):
            invalid_config = SwarmConfiguration()
            invalid_config.max_generators = 0
            TeamFactory.validate_configuration(invalid_config)

        with pytest.raises(ValueError, match="accuracy_threshold"):
            invalid_config = SwarmConfiguration()
            invalid_config.accuracy_threshold = -1
            TeamFactory.validate_configuration(invalid_config)

    @patch('app.swarms.coding.team_factory.make_generator')
    def test_build_generators(self, mock_generator):
        """Test generator building logic."""
        mock_generator.return_value = Mock(name="Generator")

        config = SwarmConfiguration(
            include_default_pair=True,
            concurrent_models=["model1", "model2"],
            max_generators=3
        )

        generators = TeamFactory._build_generators(config)

        # Should create default pair + 1 custom (limited by max_generators=3)
        assert len(generators) <= 3

    def test_team_instructions_generation(self):
        """Test team instruction generation."""
        config = SwarmConfiguration(
            pool=PoolType.BALANCED,
            max_generators=4,
            accuracy_threshold=8.0,
            include_runner=True
        )

        instructions = TeamFactory._get_team_instructions(config)

        assert "Pool: balanced" in instructions
        assert "Max Generators: 4" in instructions
        assert "Accuracy Threshold: 8.0" in instructions
        assert "Runner executes approved changes" in instructions


class TestSwarmOrchestrator:
    """Test the SwarmOrchestrator for debate execution."""

    @pytest.fixture
    def mock_team(self):
        """Create a mock team."""
        team = Mock()
        team.name = "test-team"
        team.run = AsyncMock()
        team.print_response = AsyncMock()
        return team

    @pytest.fixture
    def mock_memory(self):
        """Create a mock memory service."""
        memory = AsyncMock()
        memory.search_memory = AsyncMock(return_value=[])
        memory.add_to_memory = AsyncMock(return_value="memory-id")
        return memory

    @pytest.mark.asyncio
    async def test_run_debate_success(self, mock_team, mock_memory):
        """Test successful debate execution."""
        config = SwarmConfiguration()
        orchestrator = SwarmOrchestrator(mock_team, config, mock_memory)

        # Mock team responses
        mock_team.run.side_effect = [
            Mock(content=json.dumps({
                "verdict": "pass",
                "findings": {},
                "must_fix": [],
                "confidence_score": 0.9
            })),
            Mock(content=json.dumps({
                "decision": "accept",
                "runner_instructions": ["Apply changes"],
                "rationale": "Good to go",
                "confidence_score": 0.95
            }))
        ]

        result = await orchestrator.run_debate("Test task")

        assert result.task == "Test task"
        assert result.critic is not None
        assert result.judge is not None
        assert result.critic.verdict == CriticVerdict.PASS
        assert result.judge.decision == JudgeDecision.ACCEPT
        assert result.execution_time_ms > 0

    @pytest.mark.asyncio
    async def test_run_debate_with_revision(self, mock_team, mock_memory):
        """Test debate with revision round."""
        config = SwarmConfiguration()
        orchestrator = SwarmOrchestrator(mock_team, config, mock_memory)

        # First critic requires revision
        mock_team.run.side_effect = [
            Mock(content=json.dumps({
                "verdict": "revise",
                "must_fix": ["Fix issue 1", "Fix issue 2"],
                "confidence_score": 0.6
            })),
            # Second critic after revision
            Mock(content=json.dumps({
                "verdict": "pass",
                "findings": {},
                "must_fix": [],
                "confidence_score": 0.9
            })),
            # Judge
            Mock(content=json.dumps({
                "decision": "accept",
                "runner_instructions": ["Apply"],
                "confidence_score": 0.9
            }))
        ]

        result = await orchestrator.run_debate("Test with revision")

        assert result.critic.verdict == CriticVerdict.PASS  # After revision
        assert mock_team.print_response.call_count >= 2  # Proposal + revision

    @pytest.mark.asyncio
    async def test_run_debate_timeout(self, mock_team, mock_memory):
        """Test debate timeout handling."""
        config = SwarmConfiguration(timeout_seconds=1)
        orchestrator = SwarmOrchestrator(mock_team, config, mock_memory)

        # Make team.print_response hang
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(10)

        mock_team.print_response = slow_response

        result = await orchestrator.run_debate("Timeout test")

        assert len(result.errors) > 0
        assert "timed out" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_gate_decision_computation(self, mock_team, mock_memory):
        """Test gate decision logic."""
        config = SwarmConfiguration(
            accuracy_threshold=7.0,
            auto_approve_low_risk=True
        )
        orchestrator = SwarmOrchestrator(mock_team, config, mock_memory)

        result = DebateResult(task="Test")
        result.critic = CriticOutput(verdict=CriticVerdict.PASS)
        result.judge = JudgeOutput(
            decision=JudgeDecision.ACCEPT,
            runner_instructions=["Do it"],
            risk_assessment=RiskLevel.LOW
        )

        await orchestrator._compute_gate_decision(result)

        assert result.gate_decision is not None
        assert result.gate_decision.allowed is True
        assert "Auto-approved" in result.gate_decision.reason
        assert result.runner_approved is True

    @pytest.mark.asyncio
    async def test_memory_integration(self, mock_team, mock_memory):
        """Test memory storage integration."""
        config = SwarmConfiguration(
            use_memory=True,
            store_results=True
        )
        orchestrator = SwarmOrchestrator(mock_team, config, mock_memory)

        # Setup successful debate
        mock_team.run.side_effect = [
            Mock(content='{"verdict": "pass"}'),
            Mock(content='{"decision": "accept", "runner_instructions": ["Apply"]}')
        ]

        result = await orchestrator.run_debate("Memory test")

        # Check memory was called
        assert mock_memory.search_memory.called
        assert mock_memory.add_to_memory.call_count >= 2  # Critic + Judge
        assert len(result.memory_entries_created) > 0


class TestPublicInterface:
    """Test the public API functions."""

    @patch('app.swarms.coding.team.TeamFactory')
    def test_make_coding_swarm(self, mock_factory):
        """Test make_coding_swarm function."""
        mock_team = Mock()
        mock_factory.create_team.return_value = mock_team

        team = make_coding_swarm(
            concurrent_models=["model1"],
            include_runner=True,
            pool="heavy"
        )

        assert team == mock_team
        mock_factory.validate_configuration.assert_called_once()
        mock_factory.create_team.assert_called_once()

    @patch('app.swarms.coding.team.SwarmOrchestrator')
    @pytest.mark.asyncio
    async def test_run_coding_debate(self, mock_orchestrator_class):
        """Test run_coding_debate function."""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.run_debate.return_value = DebateResult(
            task="Test",
            runner_approved=True
        )
        mock_orchestrator_class.return_value = mock_orchestrator

        team = Mock()
        result = await run_coding_debate(team, "Test task")

        assert result.task == "Test"
        assert result.runner_approved is True
        mock_orchestrator.run_debate.assert_called_once()

    @patch('app.swarms.coding.team.TeamFactory')
    def test_make_coding_swarm_pool(self, mock_factory):
        """Test make_coding_swarm_pool function."""
        mock_team = Mock()
        mock_factory.create_team.return_value = mock_team

        team = make_coding_swarm_pool("fast")

        assert team == mock_team
        # Check that configuration was created with fast pool
        call_args = mock_factory.create_team.call_args[0][0]
        assert call_args.pool == PoolType.FAST
        assert call_args.include_default_pair is False

    @patch('app.swarms.coding.team.TeamFactory')
    @patch('app.swarms.coding.team.SwarmOrchestrator')
    @pytest.mark.asyncio
    async def test_execute_swarm_request(self, mock_orchestrator_class, mock_factory):
        """Test execute_swarm_request function."""
        mock_team = Mock()
        mock_team.name = "test-team"
        mock_factory.create_team.return_value = mock_team

        mock_orchestrator = AsyncMock()
        mock_orchestrator.run_debate.return_value = DebateResult(task="Test")
        mock_orchestrator_class.return_value = mock_orchestrator

        request = SwarmRequest(
            task="Test task",
            session_id="session-123"
        )

        result = await execute_swarm_request(request)

        assert result.task == "Test"
        assert result.session_id == "session-123"
        assert result.team_id == "test-team"


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_invalid_json_from_critic(self):
        """Test handling of invalid JSON from critic."""
        team = Mock()
        team.name = "test"
        team.run = AsyncMock(return_value=Mock(content="Not JSON"))
        team.print_response = AsyncMock()

        config = SwarmConfiguration()
        orchestrator = SwarmOrchestrator(team, config)

        result = await orchestrator.run_debate("Test")

        assert result.critic is None or len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_memory_failure_handling(self):
        """Test graceful handling of memory service failures."""
        team = Mock()
        team.name = "test"
        team.run = AsyncMock(return_value=Mock(content='{"verdict": "pass"}'))
        team.print_response = AsyncMock()

        # Memory that fails
        memory = AsyncMock()
        memory.search_memory.side_effect = Exception("Memory error")

        config = SwarmConfiguration(use_memory=True)
        orchestrator = SwarmOrchestrator(team, config, memory)

        result = await orchestrator.run_debate("Test")

        # Should complete despite memory failure
        assert "Memory search failed" in str(result.warnings)

    def test_deprecated_function_warning(self):
        """Test that deprecated functions emit warnings."""
        with pytest.warns(DeprecationWarning, match="create_coding_team"):
            from app.swarms.coding.team import create_coding_team
            with patch('app.swarms.coding.team.TeamFactory') as mock_factory:
                mock_factory.create_team.return_value = Mock()
                team = create_coding_team()
                assert team is not None


class TestIntegration:
    """Integration tests with real components."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_flow(self):
        """Test complete flow from request to result."""
        request = SwarmRequest(
            task="Write a function to calculate fibonacci numbers",
            configuration=SwarmConfiguration(
                pool=PoolType.FAST,
                max_generators=2,
                use_memory=False,  # Disable memory for test
                timeout_seconds=30
            )
        )

        # This would run with real agents in integration environment
        # For unit tests, we mock the components
        with patch('app.swarms.coding.team.TeamFactory') as mock_factory:
            mock_team = Mock()
            mock_team.name = "test-swarm"
            mock_team.run = AsyncMock()
            mock_team.print_response = AsyncMock()
            mock_factory.create_team.return_value = mock_team

            with patch('app.swarms.coding.team.SwarmOrchestrator') as mock_orch:
                mock_instance = AsyncMock()
                mock_instance.run_debate.return_value = DebateResult(
                    task=request.task,
                    runner_approved=True,
                    gate_decision=GateDecision(
                        allowed=True,
                        reason="Test passed",
                        accuracy_score=8.0,
                        reliability_passed=True,
                        risk_level=RiskLevel.LOW
                    )
                )
                mock_orch.return_value = mock_instance

                result = await execute_swarm_request(request)

                assert result.task == request.task
                assert result.runner_approved is True
                assert result.gate_decision.allowed is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
