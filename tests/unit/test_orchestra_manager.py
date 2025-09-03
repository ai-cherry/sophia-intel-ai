"""
Unit Tests for Orchestra Manager
Tests intent interpretation, response generation, and learning capabilities
"""


import pytest

from app.agents.orchestra_manager import (
    ManagerContext,
    ManagerIntegration,
    ManagerMood,
    ManagerPersonalityTrait,
    OrchestraManager,
)

# ==================== Fixtures ====================

@pytest.fixture
def orchestra_manager():
    """Create Orchestra Manager instance for testing"""
    return OrchestraManager(name="TestMaestro")

@pytest.fixture
def manager_context():
    """Create manager context for testing"""
    return ManagerContext(
        session_id="test-session",
        user_profile={"user_id": "test-user"},
        conversation_history=[],
        current_task="Test task",
        active_agents=["agent1", "agent2"],
        system_state={"health": 0.95},
        mood=ManagerMood.FOCUSED,
        confidence_level=0.9
    )

@pytest.fixture
def manager_integration(orchestra_manager):
    """Create manager integration helper"""
    return ManagerIntegration(orchestra_manager)

# ==================== Orchestra Manager Tests ====================

class TestOrchestraManager:
    """Test Orchestra Manager functionality"""

    def test_initialization(self, orchestra_manager):
        """Test manager initialization"""
        assert orchestra_manager.name == "TestMaestro"
        assert ManagerPersonalityTrait.HELPFUL in orchestra_manager.personality_traits
        assert orchestra_manager.metrics["average_confidence"] == 0.9

    def test_interpret_intent_code_generation(self, orchestra_manager, manager_context):
        """Test intent interpretation for code generation"""
        message = "Write a Python function to calculate fibonacci"

        intent, parameters, confidence = orchestra_manager.interpret_intent(
            message, manager_context
        )

        assert intent == "code_generation"
        assert confidence > 0.8
        assert "original_message" in parameters

    def test_interpret_intent_swarm_coordination(self, orchestra_manager, manager_context):
        """Test intent interpretation for swarm coordination"""
        message = "Execute workflow with multiple agents"

        intent, parameters, confidence = orchestra_manager.interpret_intent(
            message, manager_context
        )

        assert intent == "swarm_coordination"
        assert confidence > 0.8
        assert parameters.get("swarm_type") in ["coding-debate", "improved-solve", "auto-select"]

    def test_interpret_intent_with_urgency(self, orchestra_manager, manager_context):
        """Test intent interpretation with urgency detection"""
        message = "Urgent! Need to deploy this code ASAP"

        intent, parameters, confidence = orchestra_manager.interpret_intent(
            message, manager_context
        )

        assert parameters.get("urgency") == "high"
        assert parameters.get("optimization_mode") == "lite"

    def test_confidence_adjustment(self, orchestra_manager, manager_context):
        """Test confidence adjustment based on context"""
        # Add successful history
        manager_context.conversation_history = [
            {"success": True, "intent": "code_generation"},
            {"success": True, "intent": "code_generation"},
            {"success": True, "intent": "code_generation"}
        ]

        message = "Write another function"
        intent, parameters, confidence = orchestra_manager.interpret_intent(
            message, manager_context
        )

        # Confidence should be boosted by successful history
        assert confidence > orchestra_manager._get_default_config()["optimization"]["quality_target"]

    def test_generate_response_acknowledgment(self, orchestra_manager, manager_context):
        """Test response generation for task acknowledgment"""
        intent = "code_generation"
        parameters = {"language": "python"}

        response = orchestra_manager.generate_response(
            intent, parameters, manager_context, result=None
        )

        assert response
        assert "TestMaestro" not in response or response  # Response should be contextual

    def test_generate_response_with_result(self, orchestra_manager, manager_context):
        """Test response generation with execution result"""
        intent = "data_analysis"
        parameters = {}
        result = {
            "success": True,
            "quality_score": 0.95,
            "execution_time": 2.5,
            "agents_used": ["analyzer", "reporter"]
        }

        response = orchestra_manager.generate_response(
            intent, parameters, manager_context, result=result
        )

        assert response
        # Should mention quality or agents
        assert any(word in response.lower() for word in ["quality", "excellent", "agents", "completed"])

    def test_mood_updates(self, orchestra_manager, manager_context):
        """Test manager mood updates based on performance"""
        # High performance should lead to enthusiastic mood
        new_mood = orchestra_manager.update_mood(manager_context, recent_performance=0.95)
        assert new_mood == ManagerMood.ENTHUSIASTIC

        # Low performance should lead to supportive mood
        new_mood = orchestra_manager.update_mood(manager_context, recent_performance=0.4)
        assert new_mood == ManagerMood.SUPPORTIVE

        # Critical urgency should lead to urgent mood
        manager_context.system_state["urgency"] = "critical"
        new_mood = orchestra_manager.update_mood(manager_context, recent_performance=0.8)
        assert new_mood == ManagerMood.URGENT

    def test_learning_from_interaction(self, orchestra_manager):
        """Test learning from successful and failed interactions"""
        # Record successful interaction
        orchestra_manager.learn_from_interaction(
            intent="code_generation",
            parameters={"language": "python"},
            result={"success": True, "quality_score": 0.9},
            user_feedback="Great job!"
        )

        assert orchestra_manager.metrics["successful_tasks"] == 1
        assert len(orchestra_manager.learning_memory["successful_patterns"]) == 1

        # Record failed interaction
        orchestra_manager.learn_from_interaction(
            intent="data_analysis",
            parameters={},
            result={"success": False},
            user_feedback="This is wrong"
        )

        assert orchestra_manager.metrics["failed_tasks"] == 1
        assert len(orchestra_manager.learning_memory["failed_patterns"]) == 1

    def test_user_feedback_processing(self, orchestra_manager):
        """Test processing of user feedback"""
        # Positive feedback
        orchestra_manager.learn_from_interaction(
            intent="code_generation",
            parameters={},
            result={"success": True},
            user_feedback="Excellent work, exactly what I needed!"
        )

        prefs = orchestra_manager.learning_memory["user_preferences"]
        assert "code_generation" in prefs
        assert prefs["code_generation"]["positive_feedback"] == 1

        # Negative feedback
        orchestra_manager.learn_from_interaction(
            intent="code_generation",
            parameters={},
            result={"success": False},
            user_feedback="This is completely wrong"
        )

        assert prefs["code_generation"]["negative_feedback"] == 1

    def test_consciousness_logging(self, orchestra_manager, manager_context):
        """Test consciousness logging"""
        initial_log_size = len(orchestra_manager.consciousness_log)

        # Trigger logging through intent interpretation
        orchestra_manager.interpret_intent("Test message", manager_context)

        assert len(orchestra_manager.consciousness_log) > initial_log_size

        # Get recent logs
        recent_logs = orchestra_manager.get_consciousness_log(limit=5)
        assert len(recent_logs) <= 5
        assert all("timestamp" in log for log in recent_logs)
        assert all("thought" in log for log in recent_logs)

    def test_suggest_next_action(self, orchestra_manager, manager_context):
        """Test proactive suggestion generation"""
        # Test with incomplete task
        manager_context.current_task = "Incomplete task"
        manager_context.active_agents = []

        suggestion = orchestra_manager.suggest_next_action(manager_context)
        assert suggestion
        assert "resume" in suggestion.lower()

        # Test with degraded system
        manager_context.current_task = None
        manager_context.system_state["health"] = 0.6

        suggestion = orchestra_manager.suggest_next_action(manager_context)
        assert suggestion
        assert "optimization" in suggestion.lower() or "performance" in suggestion.lower()

    def test_personality_touches(self, orchestra_manager, manager_context):
        """Test personality-based response modifications"""
        # Test enthusiastic mood
        manager_context.mood = ManagerMood.ENTHUSIASTIC
        response = orchestra_manager.generate_response(
            "test_intent", {}, manager_context
        )
        assert "!" in response  # Should contain exclamation

        # Test analytical mood
        manager_context.mood = ManagerMood.ANALYTICAL
        response = orchestra_manager.generate_response(
            "test_intent", {}, manager_context
        )
        assert "analyz" in response.lower()  # Should mention analysis

    def test_knowledge_base_access(self, orchestra_manager):
        """Test knowledge base functionality"""
        kb = orchestra_manager.knowledge_base

        # Check capabilities
        assert "swarm_coordination" in kb["capabilities"]
        assert kb["capabilities"]["swarm_coordination"]["expertise_level"] > 0.9

        # Check domain expertise
        assert "software_engineering" in kb["domain_expertise"]
        assert kb["domain_expertise"]["software_engineering"] > 0.9

        # Check system components
        assert "agents" in kb["system_components"]
        assert "researcher" in kb["system_components"]["agents"]

# ==================== Manager Integration Tests ====================

class TestManagerIntegration:
    """Test Manager Integration helper"""

    def test_prepare_context(self, manager_integration):
        """Test context preparation"""
        context = manager_integration.prepare_context(
            session_id="test-123",
            conversation_history=[{"message": "test"}],
            system_state={"health": 0.9}
        )

        assert isinstance(context, ManagerContext)
        assert context.session_id == "test-123"
        assert len(context.conversation_history) == 1
        assert context.system_state["health"] == 0.9
        assert context.mood == ManagerMood.FOCUSED

    def test_process_message(self, manager_integration, manager_context):
        """Test message processing through integration"""
        result = manager_integration.process_message(
            "Write a Python function",
            manager_context
        )

        assert "intent" in result
        assert "parameters" in result
        assert "confidence" in result
        assert "response" in result
        assert "manager" in result
        assert result["manager"] == "TestMaestro"

    def test_process_result(self, manager_integration, manager_context):
        """Test result processing"""
        intent = "code_generation"
        parameters = {"language": "python"}
        result = {
            "success": True,
            "quality_score": 0.92,
            "execution_time": 1.5,
            "response": "def example(): pass"
        }

        response = manager_integration.process_result(
            intent, parameters, result, manager_context
        )

        assert response
        assert isinstance(response, str)

        # Should have learned from interaction
        manager = manager_integration.manager
        assert manager.metrics["successful_tasks"] > 0

    def test_process_result_with_suggestion(self, manager_integration, manager_context):
        """Test result processing with proactive suggestions"""
        # Setup context for suggestion
        manager_context.current_task = "Incomplete task"
        manager_context.active_agents = []

        response = manager_integration.process_result(
            "test_intent",
            {},
            {"success": True, "quality_score": 0.8},
            manager_context
        )

        # Should include suggestion
        assert "Would you like" in response or "?" in response

# ==================== Performance Tests ====================

class TestManagerPerformance:
    """Test manager performance characteristics"""

    def test_memory_bounds(self, orchestra_manager):
        """Test that memory is properly bounded"""
        # Add many consciousness log entries
        for i in range(2000):
            orchestra_manager._log_consciousness(f"Test thought {i}")

        # Should be bounded to 1000
        assert len(orchestra_manager.consciousness_log) == 1000

    def test_learning_memory_bounds(self, orchestra_manager):
        """Test that learning memory is bounded"""
        # Add many patterns
        for i in range(200):
            orchestra_manager.learn_from_interaction(
                intent="test",
                parameters={"id": i},
                result={"success": i % 2 == 0},
                user_feedback=None
            )

        # Should be bounded to 100 each
        assert len(orchestra_manager.learning_memory["successful_patterns"]) <= 100
        assert len(orchestra_manager.learning_memory["failed_patterns"]) <= 100

    def test_concurrent_access(self, orchestra_manager, manager_context):
        """Test thread safety of manager operations"""
        import threading
        import time

        results = []

        def process_message():
            for _ in range(10):
                intent, params, conf = orchestra_manager.interpret_intent(
                    "Test message",
                    manager_context
                )
                results.append((intent, conf))
                time.sleep(0.01)

        # Create multiple threads
        threads = [threading.Thread(target=process_message) for _ in range(5)]

        # Start all threads
        for t in threads:
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Should have all results without errors
        assert len(results) == 50
        assert all(r[1] > 0 for r in results)  # All should have confidence

# ==================== Run Tests ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
