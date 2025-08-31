"""
Isolated tests for Coding Swarm components.
Tests models, factory, and orchestrator without full server dependencies.
"""

import unittest
import asyncio
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

# Test models
class TestSwarmModels(unittest.TestCase):
    """Test Pydantic models for type safety and validation."""
    
    def test_swarm_configuration_defaults(self):
        """Test SwarmConfiguration default values."""
        from app.swarms.coding.models import SwarmConfiguration, PoolType
        
        config = SwarmConfiguration()
        self.assertEqual(config.pool, PoolType.BALANCED)
        self.assertEqual(config.max_generators, 4)
        self.assertEqual(config.accuracy_threshold, 7.0)
        self.assertTrue(config.use_memory)
        self.assertFalse(config.enable_file_write)
    
    def test_swarm_configuration_validation(self):
        """Test SwarmConfiguration validation constraints."""
        from app.swarms.coding.models import SwarmConfiguration
        from pydantic import ValidationError
        
        # Test max_generators constraint
        with self.assertRaises(ValidationError):
            SwarmConfiguration(max_generators=11)  # Max is 10
        
        # Test accuracy_threshold constraint
        with self.assertRaises(ValidationError):
            SwarmConfiguration(accuracy_threshold=11.0)  # Max is 10.0
    
    def test_debate_result_structure(self):
        """Test DebateResult model structure."""
        from app.swarms.coding.models import DebateResult
        
        result = DebateResult(task="Test task")
        self.assertEqual(result.task, "Test task")
        self.assertIsNone(result.critic)
        self.assertIsNone(result.judge)
        self.assertFalse(result.runner_approved)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.warnings), 0)
    
    def test_critic_output_verdict(self):
        """Test CriticOutput verdict enum."""
        from app.swarms.coding.models import CriticOutput, CriticVerdict
        
        critic = CriticOutput(
            verdict=CriticVerdict.PASS,
            findings={"security": [], "logic": []},
            must_fix=[],
            confidence_score=0.85
        )
        self.assertEqual(critic.verdict, CriticVerdict.PASS)
        self.assertIsInstance(critic.findings, dict)
    
    def test_judge_output_decision(self):
        """Test JudgeOutput decision enum."""
        from app.swarms.coding.models import JudgeOutput, JudgeDecision, RiskLevel
        
        judge = JudgeOutput(
            decision=JudgeDecision.ACCEPT,
            runner_instructions=["Step 1", "Step 2"],
            rationale="Test rationale",
            confidence_score=0.9,
            risk_assessment=RiskLevel.LOW
        )
        self.assertEqual(judge.decision, JudgeDecision.ACCEPT)
        self.assertEqual(len(judge.runner_instructions), 2)


class TestTeamFactory(unittest.TestCase):
    """Test TeamFactory for proper team construction."""
    
    @patch('app.swarms.coding.team_factory.agno_chat_model')
    @patch('app.swarms.coding.team_factory.Team')
    def test_create_team_with_default_config(self, mock_team, mock_model):
        """Test team creation with default configuration."""
        from app.swarms.coding.team_factory import TeamFactory
        from app.swarms.coding.models import SwarmConfiguration
        
        # Setup mocks
        mock_team.return_value = MagicMock(name="Test Team")
        mock_model.return_value = MagicMock()
        
        # Create team
        config = SwarmConfiguration()
        team = TeamFactory.create_team(config)
        
        # Verify Team was called
        mock_team.assert_called_once()
        self.assertIsNotNone(team)
    
    def test_validate_configuration(self):
        """Test configuration validation."""
        from app.swarms.coding.team_factory import TeamFactory
        from app.swarms.coding.models import SwarmConfiguration
        
        # Valid configuration should not raise
        config = SwarmConfiguration(max_generators=5)
        try:
            TeamFactory.validate_configuration(config)
        except ValueError:
            self.fail("Valid configuration raised ValueError")
        
        # Invalid configuration should raise
        config = SwarmConfiguration(max_generators=0)
        with self.assertRaises(ValueError):
            TeamFactory.validate_configuration(config)


class TestSwarmOrchestrator(unittest.TestCase):
    """Test SwarmOrchestrator for debate management."""
    
    def setUp(self):
        """Set up test fixtures."""
        from app.swarms.coding.models import SwarmConfiguration
        
        self.config = SwarmConfiguration()
        self.mock_team = MagicMock()
        self.mock_team.name = "Test Team"
        self.mock_memory = MagicMock()
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        from app.swarms.coding.swarm_orchestrator import SwarmOrchestrator
        
        orchestrator = SwarmOrchestrator(
            team=self.mock_team,
            config=self.config,
            memory=self.mock_memory
        )
        
        self.assertEqual(orchestrator.team, self.mock_team)
        self.assertEqual(orchestrator.config, self.config)
        self.assertEqual(orchestrator.memory, self.mock_memory)
    
    @patch('asyncio.wait_for')
    async def test_run_debate_async(self, mock_wait_for):
        """Test async debate execution."""
        from app.swarms.coding.swarm_orchestrator import SwarmOrchestrator
        from app.swarms.coding.models import DebateResult
        
        # Setup
        orchestrator = SwarmOrchestrator(
            team=self.mock_team,
            config=self.config,
            memory=None  # No memory for this test
        )
        
        # Mock team responses
        mock_wait_for.return_value = MagicMock(content="Test response")
        
        # Run debate
        result = await orchestrator.run_debate("Test task")
        
        # Verify result
        self.assertIsInstance(result, DebateResult)
        self.assertEqual(result.task, "Test task")
        self.assertEqual(result.team_id, "Test Team")


class TestPublicInterface(unittest.TestCase):
    """Test the public interface functions."""
    
    @patch('app.swarms.coding.team.TeamFactory')
    def test_make_coding_swarm(self, mock_factory):
        """Test make_coding_swarm function."""
        from app.swarms.coding.team import make_coding_swarm
        
        # Setup mock
        mock_team = MagicMock(name="Coding Swarm")
        mock_factory.create_team.return_value = mock_team
        
        # Create swarm
        swarm = make_coding_swarm(
            concurrent_models=["gpt-4"],
            include_runner=True,
            pool="heavy"
        )
        
        # Verify
        self.assertEqual(swarm, mock_team)
        mock_factory.create_team.assert_called_once()
    
    @patch('app.swarms.coding.team.TeamFactory')
    def test_make_coding_swarm_pool(self, mock_factory):
        """Test make_coding_swarm_pool function."""
        from app.swarms.coding.team import make_coding_swarm_pool
        
        # Setup mock
        mock_team = MagicMock(name="Pool Swarm")
        mock_factory.create_team.return_value = mock_team
        
        # Create pool-based swarm
        swarm = make_coding_swarm_pool(pool="fast")
        
        # Verify
        self.assertEqual(swarm, mock_team)
        mock_factory.create_team.assert_called_once()
    
    @patch('app.swarms.coding.team.warnings')
    @patch('app.swarms.coding.team.TeamFactory')
    def test_deprecated_create_coding_team(self, mock_factory, mock_warnings):
        """Test deprecated create_coding_team function."""
        from app.swarms.coding.team import create_coding_team
        
        # Setup mock
        mock_team = MagicMock()
        mock_factory.create_team.return_value = mock_team
        
        # Call deprecated function
        team = create_coding_team()
        
        # Verify deprecation warning
        mock_warnings.warn.assert_called_once()
        warning_message = mock_warnings.warn.call_args[0][0]
        self.assertIn("deprecated", warning_message)
        self.assertIn("v2.0.0", warning_message)


class TestAPIRouter(unittest.TestCase):
    """Test the API router endpoints."""
    
    def test_router_imports(self):
        """Test that router can be imported."""
        try:
            from app.api.routers.swarms import router
            self.assertIsNotNone(router)
            self.assertEqual(router.prefix, "/swarms")
        except ImportError as e:
            self.fail(f"Failed to import router: {e}")
    
    def test_router_endpoints(self):
        """Test that router has expected endpoints."""
        from app.api.routers.swarms import router
        
        # Get all routes
        routes = [route.path for route in router.routes]
        
        # Check expected endpoints exist
        expected_endpoints = [
            "/coding/execute",
            "/coding/stream",
            "/coding/pools",
            "/coding/configuration",
            "/coding/validate",
            "/coding/history",
            "/coding/quick"
        ]
        
        for endpoint in expected_endpoints:
            self.assertIn(endpoint, routes, f"Missing endpoint: {endpoint}")


def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSwarmModels))
    suite.addTests(loader.loadTestsFromTestCase(TestTeamFactory))
    suite.addTests(loader.loadTestsFromTestCase(TestSwarmOrchestrator))
    suite.addTests(loader.loadTestsFromTestCase(TestPublicInterface))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIRouter))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    # Run async tests with asyncio
    result = run_tests()
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)