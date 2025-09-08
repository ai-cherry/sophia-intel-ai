# Auto-added by pre-commit hook
import sys, os
try:
    sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    from core.environment_enforcer import enforce_environment
    enforce_environment()
except ImportError:
    pass

"""
Comprehensive Tests for Artemis Swarm Orchestrator
Testing all 5 agents and advanced integrations
"""

import asyncio
import json
import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Import the modules to test
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from swarm_orchestrator import (
    ArtemisSwarm,
    PlannerAgent,
    CoderAgent,
    TesterAgent,
    DeployerAgent,
    EvolverAgent,
    SwarmState,
    AgentRole,
    create_artemis_swarm
)

class TestArtemisAgents:
    """Test individual Artemis agents"""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing"""
        return {
            "openai_api_key": "test-key",
            "cost_optimization": True,
            "register_on_blockchain": False
        }

    @pytest.mark.asyncio
    async def test_planner_agent_execution(self, mock_config):
        """Test PlannerAgent execution"""
        planner = PlannerAgent(mock_config)

        intent = "Create a REST API for user management"
        context = {"execution_id": "test-123"}

        result = await planner.execute(intent, context)

        assert result["success"] is True
        assert "plan" in result
        assert "execution_time" in result
        assert result["agent"] == "planner"

        plan = result["plan"]
        assert "requirements" in plan
        assert "architecture" in plan
        assert "steps" in plan
        assert "agents_needed" in plan

    @pytest.mark.asyncio
    async def test_coder_agent_execution(self, mock_config):
        """Test CoderAgent execution"""
        coder = CoderAgent(mock_config)

        intent = "Create a simple FastAPI endpoint"
        context = {
            "execution_id": "test-456",
            "plan": {
                "requirements": ["Create FastAPI endpoint"],
                "architecture": "REST API",
                "steps": ["Setup FastAPI", "Create endpoint", "Add validation"]
            }
        }

        result = await coder.execute(intent, context)

        assert result["success"] is True
        assert "code" in result
        assert "execution_result" in result
        assert result["agent"] == "coder"

        # Check that code was generated
        assert len(result["code"]) > 0
        assert result["execution_result"]["syntax_valid"] is True

    @pytest.mark.asyncio
    async def test_tester_agent_execution(self, mock_config):
        """Test TesterAgent execution"""
        tester = TesterAgent(mock_config)

        intent = "Test the FastAPI endpoint"
        context = {
            "execution_id": "test-789",
            "code": "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef read_root():\n    return {'Hello': 'World'}"
        }

        result = await tester.execute(intent, context)

        assert result["success"] is True
        assert "test_results" in result
        assert "coverage" in result
        assert result["agent"] == "tester"

        test_results = result["test_results"]
        assert "syntax_test" in test_results
        assert "unit_tests" in test_results
        assert "security_scan" in test_results
        assert "performance_test" in test_results

    @pytest.mark.asyncio
    async def test_deployer_agent_execution(self, mock_config):
        """Test DeployerAgent execution"""
        deployer = DeployerAgent(mock_config)

        intent = "Deploy the FastAPI application"
        context = {
            "execution_id": "test-101",
            "code": "from fastapi import FastAPI\napp = FastAPI()",
            "test_results": {
                "syntax_test": {"passed": True},
                "unit_tests": {"passed": True},
                "security_scan": {"passed": True},
                "performance_test": {"passed": True}
            }
        }

        result = await deployer.execute(intent, context)

        assert result["success"] is True
        assert "deployment_result" in result
        assert result["agent"] == "deployer"

        deployment = result["deployment_result"]
        assert "lambda_arn" in deployment
        assert "api_url" in deployment

    @pytest.mark.asyncio
    async def test_evolver_agent_execution(self, mock_config):
        """Test EvolverAgent execution"""
        evolver = EvolverAgent(mock_config)

        intent = "Learn from the execution"
        context = {
            "execution_id": "test-202",
            "result": {"success": True, "execution_time": 5.2},
            "agents_used": ["planner", "coder", "tester", "deployer"]
        }

        result = await evolver.execute(intent, context)

        assert result["success"] is True
        assert "insights" in result
        assert "strategy_updates" in result
        assert result["agent"] == "evolver"

        insights = result["insights"]
        assert "intent_complexity" in insights
        assert "success_rate" in insights
        assert "execution_efficiency" in insights

class TestArtemisSwarm:
    """Test the complete Artemis swarm"""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing"""
        return {
            "openai_api_key": "test-key",
            "anthropic_api_key": "test-key",
            "cost_optimization": True,
            "register_on_blockchain": False
        }

    @pytest.fixture
    def swarm(self, mock_config):
        """Create Artemis swarm for testing"""
        return create_artemis_swarm(mock_config)

    @pytest.mark.asyncio
    async def test_swarm_initialization(self, swarm):
        """Test swarm initialization"""
        assert len(swarm.agents) == 5
        assert AgentRole.PLANNER in swarm.agents
        assert AgentRole.CODER in swarm.agents
        assert AgentRole.TESTER in swarm.agents
        assert AgentRole.DEPLOYER in swarm.agents
        assert AgentRole.EVOLVER in swarm.agents

    @pytest.mark.asyncio
    async def test_process_intent_success(self, swarm):
        """Test successful intent processing"""
        intent = "Create a simple web API with authentication"

        result = await swarm.process_intent(intent)

        assert result["success"] is True
        assert "plan" in result
        assert "code" in result
        assert "test" in result
        assert "deploy" in result
        assert "evolution" in result
        assert "execution_time" in result
        assert "agents_used" in result

        # Check that all agents were used
        agents_used = result["agents_used"]
        assert "planner" in agents_used
        assert "coder" in agents_used
        assert "tester" in agents_used
        assert "deployer" in agents_used
        assert "evolver" in agents_used

    @pytest.mark.asyncio
    async def test_process_intent_with_test_failure(self, swarm):
        """Test intent processing when tests fail"""
        # Mock the tester to fail
        original_execute = swarm.agents[AgentRole.TESTER].execute

        async def mock_failing_test(intent, context):
            result = await original_execute(intent, context)
            result["success"] = False
            result["test_results"] = {
                "syntax_test": {"passed": False, "message": "Syntax error"},
                "unit_tests": {"passed": False},
                "security_scan": {"passed": True},
                "performance_test": {"passed": True}
            }
            return result

        swarm.agents[AgentRole.TESTER].execute = mock_failing_test

        intent = "Create a buggy API"
        result = await swarm.process_intent(intent)

        # Should still complete but deployment should fail
        assert "test" in result
        assert result["test"]["success"] is False
        assert "deploy" in result
        assert result["deploy"]["success"] is False
        assert "skipping deployment" in result["deploy"]["error"].lower()

    @pytest.mark.asyncio
    async def test_get_execution_status(self, swarm):
        """Test getting execution status"""
        intent = "Create a test API"
        result = await swarm.process_intent(intent)

        # Get the execution ID from the result
        execution_id = None
        for exec_id, execution in swarm.executions.items():
            if execution.intent == intent:
                execution_id = exec_id
                break

        assert execution_id is not None

        status = await swarm.get_execution_status(execution_id)

        assert status is not None
        assert status["execution_id"] == execution_id
        assert status["intent"] == intent
        assert status["state"] == "completed"
        assert "agents_used" in status
        assert "started_at" in status
        assert "completed_at" in status

    @pytest.mark.asyncio
    async def test_get_swarm_metrics(self, swarm):
        """Test getting swarm metrics"""
        # Process a few intents to generate metrics
        intents = [
            "Create a user registration API",
            "Build a data processing pipeline",
            "Develop a notification service"
        ]

        for intent in intents:
            await swarm.process_intent(intent)

        metrics = await swarm.get_swarm_metrics()

        assert "total_executions" in metrics
        assert "successful_executions" in metrics
        assert "success_rate" in metrics
        assert "avg_execution_time" in metrics
        assert "agents_available" in metrics
        assert "frameworks_available" in metrics

        assert metrics["total_executions"] == 3
        assert metrics["agents_available"] == 5
        assert metrics["success_rate"] >= 0
        assert metrics["avg_execution_time"] >= 0

class TestIntegrations:
    """Test advanced integrations"""

    @pytest.mark.asyncio
    async def test_memory_system_integration(self):
        """Test memory system integration"""
        config = {
            "memory_enabled": True,
            "register_on_blockchain": False
        }

        swarm = create_artemis_swarm(config)

        # Process an intent that should create memories
        intent = "Create a machine learning model training API"
        result = await swarm.process_intent(intent)

        assert result["success"] is True

        # Check if memory IDs were created
        if "memory_ids" in result and result["memory_ids"]:
            assert len(result["memory_ids"]) > 0

    @pytest.mark.asyncio
    async def test_zk_proof_integration(self):
        """Test zero-knowledge proof integration"""
        config = {
            "zk_proofs_enabled": True,
            "register_on_blockchain": False
        }

        swarm = create_artemis_swarm(config)

        # Process an intent that should generate proofs
        intent = "Create a secure payment processing API"
        result = await swarm.process_intent(intent)

        assert result["success"] is True

        # Check if proof IDs were created
        if "proof_ids" in result and result["proof_ids"]:
            assert len(result["proof_ids"]) > 0

    @pytest.mark.asyncio
    async def test_cost_optimization_integration(self):
        """Test cost optimization integration"""
        config = {
            "cost_optimization": True,
            "openai_api_key": "test-key",
            "anthropic_api_key": "test-key"
        }

        swarm = create_artemis_swarm(config)

        # Process an intent that should track costs
        intent = "Create a data analytics dashboard"
        result = await swarm.process_intent(intent)

        assert result["success"] is True

        # Check if cost information was tracked
        if "cost_info" in result and result["cost_info"]:
            cost_info = result["cost_info"]
            assert "total_cost" in cost_info
            assert "savings" in cost_info
            assert "requests" in cost_info

class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_agent_failure_handling(self):
        """Test handling of agent failures"""
        config = {"test_mode": True}
        swarm = create_artemis_swarm(config)

        # Mock planner to fail
        async def failing_planner(intent, context):
            raise Exception("Planner failed for testing")

        swarm.agents[AgentRole.PLANNER].execute = failing_planner

        intent = "This should fail at planning"
        result = await swarm.process_intent(intent)

        assert result["success"] is False
        assert "error" in result
        assert "Planner failed" in result["error"]

    @pytest.mark.asyncio
    async def test_invalid_execution_id(self, mock_config):
        """Test handling of invalid execution ID"""
        swarm = create_artemis_swarm(mock_config)

        status = await swarm.get_execution_status("invalid-id")
        assert status is None

    @pytest.mark.asyncio
    async def test_empty_intent(self, mock_config):
        """Test handling of empty intent"""
        swarm = create_artemis_swarm(mock_config)

        result = await swarm.process_intent("")

        # Should still process but may have different behavior
        assert "success" in result
        assert "execution_time" in result

class TestPerformance:
    """Test performance characteristics"""

    @pytest.mark.asyncio
    async def test_concurrent_executions(self, mock_config):
        """Test concurrent intent processing"""
        swarm = create_artemis_swarm(mock_config)

        intents = [
            "Create API endpoint 1",
            "Create API endpoint 2", 
            "Create API endpoint 3"
        ]

        # Process intents concurrently
        tasks = [swarm.process_intent(intent) for intent in intents]
        results = await asyncio.gather(*tasks)

        # All should succeed
        for result in results:
            assert result["success"] is True

        # Check that all executions are tracked
        assert len(swarm.executions) == 3

    @pytest.mark.asyncio
    async def test_execution_time_tracking(self, mock_config):
        """Test execution time tracking"""
        swarm = create_artemis_swarm(mock_config)

        intent = "Create a simple API"
        result = await swarm.process_intent(intent)

        assert "execution_time" in result
        assert result["execution_time"] > 0
        assert result["execution_time"] < 60  # Should complete within 60 seconds

# Fixtures for pytest
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
