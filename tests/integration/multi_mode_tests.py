#!/usr/bin/env python3
"""
Integration tests for multi-mode workflows
Tests coordination between different modes using the ModeFactory
"""

import asyncio
import unittest
import json
from unittest.mock import AsyncMock, patch, MagicMock

from agents.core.mode_factory import ModeFactory
from agents.core.mode_framework import ModeConfig
from agents.specialized.genetic_algorithm_agent import OptimizationTarget

class TestMultiModeWorkflow(unittest.IsolatedAsyncioTestCase):
    """Integration tests for multi-mode orchestration"""
    
    async def asyncSetUp(self):
        """Set up test fixtures"""
        # Mock MCP client for integration tests
        self.mock_mcp = MagicMock()
        self.mock_mcp.store = AsyncMock()
        self.mock_mcp.retrieve = AsyncMock(return_value=json.dumps({"mock_data": True}))
        self.mock_mcp.search = AsyncMock(return_value=[{"mock_entry": True}])
        
        # Mock workflow engine
        self.mock_workflow = MagicMock()
        self.mock_workflow.execute_workflow = AsyncMock(return_value={"mock_result": True})
        
        # Patch dependencies
        patcher1 = patch('agents.core.mode_framework.MCPClient', return_value=self.mock_mcp)
        patcher2 = patch('agents.core.mode_framework.WorkflowEngine', return_value=self.mock_workflow)
        self.addAsyncCleanup(patcher1.stop)
        self.addAsyncCleanup(patcher2.stop)
        patcher1.start()
        patcher2.start()

    async def test_genetic_to_prophecy_orchestration(self):
        """Test orchestration: Genetic Algorithm → Prophecy Mode"""
        # Create primary mode (Genetic Algorithm)
        ga_config = ModeFactory.generate_config(
            mode_id="genetic-algorithm",
            mode_name="Genetic Algorithm Mode",
            workflow_steps=["initialization", "evolution", "synthesis"],
            parameters={"generations": 5}
        )
        
        # Create secondary mode (Prophecy)
        prophecy_config = ModeFactory.generate_config(
            mode_id="prophecy",
            mode_name="Prophecy Mode",
            workflow_steps=["trend_analysis", "prediction_generation"],
            parameters={"prediction_horizon": 15}
        )
        
        # Test orchestration
        task_data = {
            "code_snippet": "def simple_function(): pass",
            "optimization_target": "performance"
        }
        
        # Execute primary mode
        ga_agent = ModeFactory.create_mode_agent(ga_config)
        ga_result = await ga_agent._process_task_impl("ga_test", task_data)
        self.assertIn("workflow_result", ga_result)
        self.assertEqual(ga_result["mode"], "genetic-algorithm")
        
        # Execute secondary mode with GA output
        prophecy_input = {**task_data, **ga_result["workflow_result"]}
        prophecy_agent = ModeFactory.create_mode_agent(prophecy_config)
        prophecy_result = await prophecy_agent._process_task_impl("prophecy_test", prophecy_input)
        self.assertIn("workflow_result", prophecy_result)
        self.assertEqual(prophecy_result["mode"], "prophecy")
        
        # Verify orchestration result
        orchestration_result = ModeFactory.orchestrate_modes(
            primary_mode_id="genetic-algorithm",
            secondary_modes=["prophecy"],
            task_data=task_data
        )
        self.assertIn("primary", orchestration_result["orchestration"]["overall_result"])
        self.assertIn("prophecy", orchestration_result["orchestration"]["overall_result"])
        
        # Verify MCP interactions
        self.mock_mcp.store.assert_called()
        self.assertGreater(len(self.mock_mcp.store.call_args_list), 0)

    async def test_socratic_to_cascade_orchestration(self):
        """Test orchestration: Socratic → Cascade Mode"""
        # Create primary mode (Socratic)
        socratic_config = ModeFactory.generate_config(
            mode_id="socratic",
            mode_name="Socratic Mode",
            workflow_steps=["question_generation", "refinement_iteration"],
            parameters={"max_iterations": 3}
        )
        
        # Create secondary mode (Cascade)
        cascade_config = ModeFactory.generate_config(
            mode_id="cascade",
            mode_name="Cascade Mode",
            workflow_steps=["coarse_analysis", "fine_grained_refinement"],
            parameters={"layers": 2}
        )
        
        # Test orchestration
        task_data = {
            "code_snippet": """
def process_data(items):
    result = []
    for item in items:
        result.append(item * 2)
    return result
""",
            "context": "code_refinement"
        }
        
        # Execute primary mode
        socratic_agent = ModeFactory.create_mode_agent(socratic_config)
        socratic_result = await socratic_agent._process_task_impl("socratic_test", task_data)
        self.assertIn("workflow_result", socratic_result)
        self.assertEqual(socratic_result["mode"], "socratic")
        
        # Execute secondary mode with Socratic output
        cascade_input = {**task_data, **socratic_result["workflow_result"]}
        cascade_agent = ModeFactory.create_mode_agent(cascade_config)
        cascade_result = await cascade_agent._process_task_impl("cascade_test", cascade_input)
        self.assertIn("workflow_result", cascade_result)
        self.assertEqual(cascade_result["mode"], "cascade")
        
        # Verify orchestration result
        orchestration_result = ModeFactory.orchestrate_modes(
            primary_mode_id="socratic",
            secondary_modes=["cascade"],
            task_data=task_data
        )
        self.assertIn("primary", orchestration_result["orchestration"]["overall_result"])
        self.assertIn("cascade", orchestration_result["orchestration"]["overall_result"])
        
        # Verify workflow execution
        self.mock_workflow.execute_workflow.assert_called()
        self.assertGreater(len(self.mock_workflow.execute_workflow.call_args_list), 0)

    async def test_full_mode_orchestration_chain(self):
        """Test full chain: Socratic → Prophecy → Genetic Algorithm → Cascade"""
        task_data = {
            "code_snippet": """
import time

def slow_function(data):
    result = []
    for item in data:
        time.sleep(0.01)  # Simulate slow operation
        result.append(item * 2)
    return result
""",
            "context": "performance_optimization",
            "optimization_target": "performance"
        }
        
        # Orchestrate full chain
        orchestration_result = ModeFactory.orchestrate_modes(
            primary_mode_id="socratic",
            secondary_modes=["prophecy", "genetic-algorithm", "cascade"],
            task_data=task_data
        )
        
        # Verify all modes were executed
        results = orchestration_result["orchestration"]["overall_result"]
        self.assertIn("primary", results)  # Socratic
        self.assertIn("prophecy", results)
        self.assertIn("genetic-algorithm", results)
        self.assertIn("cascade", results)
        
        # Verify sequential data flow
        socratic_result = results["primary"]
        prophecy_result = results["prophecy"]
        ga_result = results["genetic-algorithm"]
        cascade_result = results["cascade"]
        
        # Check that each mode received previous results
        self.assertIn("workflow_result", socratic_result)
        self.assertIn("workflow_result", prophecy_result)
        self.assertIn("workflow_result", ga_result)
        self.assertIn("workflow_result", cascade_result)
        
        # Verify final result has comprehensive output
        final_result = orchestration_result["orchestration"]
        self.assertIn("overall_result", final_result)
        self.assertEqual(len(final_result["secondary_modes"]), 3)

    async def test_mode_factory_configuration_generation(self):
        """Test mode factory configuration generation"""
        # Generate config for new mode
        config = ModeFactory.generate_config(
            mode_id="test-orchestration",
            mode_name="Test Orchestration Mode",
            workflow_steps=[
                "preparation",
                "execution",
                "validation",
                "documentation"
            ],
            model_phases={
                "preparation": "claude-opus-4.1",
                "execution": "grok-5",
                "validation": "deepseek-v3",
                "documentation": "claude-opus-4.1"
            },
            parameters={
                "test_mode": True,
                "mock_data": True
            }
        )
        
        # Validate generated config
        validation = ModeFactory.validate_config(config)
        self.assertTrue(validation["valid"])
        self.assertEqual(validation["issues"], [])
        
        # Verify all required fields present
        required_fields = ["mode_id", "mode_name", "workflow_steps", "model_phases"]
        for field in required_fields:
            self.assertIn(field, config.__dict__)
            self.assertTrue(getattr(config, field))
        
        # Verify model phases cover all workflow steps
        for step in config.workflow_steps:
            self.assertIn(step, config.model_phases)
        
        # Test JSON serialization
        config_json = json.dumps(config.__dict__, indent=2)
        self.assertIn(config.mode_id, config_json)
        self.assertIn(config.mode_name, config_json)

    async def test_mode_validation_with_errors(self):
        """Test mode factory validation with invalid configurations"""
        # Test missing required fields
        invalid_config = ModeConfig(
            mode_id="invalid_mode",
            mode_name="Invalid Mode",
            # Missing workflow_steps
            model_phases={"analysis": "claude-opus-4.1"},
            parameters={"invalid_param": -1}
        )
        
        validation = ModeFactory.validate_config(invalid_config)
        self.assertFalse(validation["valid"])
        self.assertIn("Missing required field: workflow_steps", str(validation["issues"]))
        self.assertIn("Parameter 'invalid_param' has negative value", str(validation["warnings"]))
        
        # Test invalid model phases
        invalid_config.workflow_steps = ["invalid_step"]
        validation = ModeFactory.validate_config(invalid_config)
        self.assertIn("No model specified for step 'invalid_step'", str(validation["warnings"]))

    async def test_cross_mode_data_persistence(self):
        """Test that mode results persist across different mode executions"""
        # Create test task data
        task_data = {"initial_data": "test_value"}
        
        # Execute first mode and store result
        config1 = ModeFactory.generate_config("genetic-algorithm", "GA Test", parameters={"test": True})
        agent1 = ModeFactory.create_mode_agent(config1)
        result1 = await agent1._process_task_impl("test1", task_data)
        
        # Verify MCP store was called
        self.mock_mcp.store.assert_called_once()
        stored_key = self.mock_mcp.store.call_args[1]["key"]
        self.assertIn("genetic-algorithm", stored_key)
        
        # Execute second mode and retrieve previous result
        config2 = ModeFactory.generate_config("prophecy", "Prophecy Test", parameters={"test": True})
        agent2 = ModeFactory.create_mode_agent(config2)
        task_data2 = {"retrieve_previous": stored_key}
        result2 = await agent2._process_task_impl("test2", task_data2)
        
        # Verify retrieval worked
        self.mock_mcp.retrieve.assert_called_once()
        self.assertEqual(self.mock_mcp.retrieve.call_args[1]["key"], stored_key)
        
        # Verify data flow between modes
        self.assertIn("mock_data", str(result2))  # From MCP mock

    async def test_mode_orchestration_error_handling(self):
        """Test error handling in mode orchestration"""
        # Mock failure in secondary mode
        self.mock_workflow.execute_workflow.side_effect = Exception("Mock orchestration failure")
        
        task_data = {"code_snippet": "def test(): pass"}
        
        with self.assertRaises(Exception):
            await ModeFactory.orchestrate_modes(
                primary_mode_id="genetic-algorithm",
                secondary_modes=["prophecy"],
                task_data=task_data
            )
        
        # Verify error was logged to MCP
        self.mock_mcp.store.assert_called()
        self.assertIn("error", self.mock_mcp.store.call_args[1]["value"].lower())

    async def test_factory_json_serialization(self):
        """Test factory JSON serialization and deserialization"""
        # Generate config
        config = ModeFactory.generate_config(
            mode_id="serialization_test",
            mode_name="Serialization Test Mode",
            workflow_steps=["step1", "step2"],
            parameters={"test_param": 42}
        )
        
        # Serialize to JSON
        config_json = json.dumps(config.__dict__, indent=2)
        
        # Deserialize back
        deserialized_dict = json.loads(config_json)
        deserialized_config = ModeConfig(**deserialized_dict)
        
        # Verify round-trip integrity
        self.assertEqual(config.mode_id, deserialized_config.mode_id)
        self.assertEqual(config.mode_name, deserialized_config.mode_name)
        self.assertEqual(config.workflow_steps, deserialized_config.workflow_steps)
        self.assertEqual(config.parameters, deserialized_config.parameters)
        
        # Test config file generation
        temp_config_path = "temp_test_config.json"
        generated_json = ModeFactory.generate_config_json(
            mode_id=config.mode_id,
            output_path=temp_config_path,
            workflow_steps=config.workflow_steps,
            model_phases=config.model_phases,
            parameters=config.parameters
        )
        
        # Verify file was created
        self.assertTrue(os.path.exists(temp_config_path))
        
        # Clean up
        os.remove(temp_config_path)

    async def test_mode_factory_available_modes(self):
        """Test listing available modes and templates"""
        available_modes = ModeFactory.list_available_modes()
        self.assertIn("genetic-algorithm", available_modes)
        self.assertIn("prophecy", available_modes)
        self.assertIn("socratic", available_modes)
        self.assertIn("cascade", available_modes)
        
        # Test getting template
        template = ModeFactory.get_mode_template("genetic-algorithm")
        self.assertIn("workflow_steps", template)
        self.assertIn("default_parameters", template)
        
        # Test unknown mode
        unknown_template = ModeFactory.get_mode_template("unknown_mode")
        self.assertEqual(unknown_template, {})


if __name__ == "__main__":
    # Run tests
    unittest.main()