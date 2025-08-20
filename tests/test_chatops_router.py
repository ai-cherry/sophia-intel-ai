"""
Tests for ChatOps Router
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from sophia.core.chatops_router import (
    SOPHIAChatOpsRouter, 
    ChatMode, 
    ExecutionPlan, 
    ParsedIntent
)
from sophia.core.ultimate_model_router import UltimateModelRouter


class TestSOPHIAChatOpsRouter:
    """Test suite for SOPHIAChatOpsRouter"""
    
    @pytest.fixture
    def mock_model_router(self):
        router = MagicMock(spec=UltimateModelRouter)
        router.select_model.return_value = "claude-sonnet-4"
        router.call_model = AsyncMock(return_value='{"intent": "deploy", "confidence": 0.9, "parameters": {"service": "api", "environment": "production"}, "suggested_action": "create deployment plan"}')
        return router
    
    @pytest.fixture
    def chatops_router(self, mock_model_router):
        return SOPHIAChatOpsRouter(model_router=mock_model_router)
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test router initialization"""
        router = SOPHIAChatOpsRouter()
        assert router.mode == ChatMode.HYBRID
        assert len(router.pending_plans) == 0
        assert isinstance(router.model_router, UltimateModelRouter)
    
    def test_set_mode(self, chatops_router):
        """Test mode setting"""
        # Test natural mode
        response = chatops_router.set_mode(ChatMode.NATURAL)
        assert chatops_router.mode == ChatMode.NATURAL
        assert "Natural language mode" in response
        
        # Test command mode
        response = chatops_router.set_mode(ChatMode.COMMAND)
        assert chatops_router.mode == ChatMode.COMMAND
        assert "Command mode" in response
        
        # Test hybrid mode
        response = chatops_router.set_mode(ChatMode.HYBRID)
        assert chatops_router.mode == ChatMode.HYBRID
        assert "Hybrid mode" in response
    
    @pytest.mark.asyncio
    async def test_parse_explicit_commands(self, chatops_router):
        """Test parsing of explicit commands"""
        # Test /mode command
        response_type, intent = await chatops_router.parse_input("/mode natural")
        assert response_type == "success"
        assert intent.intent_type == "mode_change"
        assert intent.parameters["mode"] == "natural"
        
        # Test /help command
        response_type, intent = await chatops_router.parse_input("/help")
        assert response_type == "help"
        assert intent.intent_type == "help"
        assert "Available Commands" in intent.parameters["content"]
        
        # Test /status command
        response_type, intent = await chatops_router.parse_input("/status api")
        assert response_type == "status"
        assert intent.intent_type == "status_check"
        assert intent.parameters["service"] == "api"
    
    @pytest.mark.asyncio
    async def test_parse_invalid_command_in_command_mode(self, chatops_router):
        """Test invalid command in command-only mode"""
        chatops_router.set_mode(ChatMode.COMMAND)
        
        response_type, intent = await chatops_router.parse_input("deploy the api")
        assert response_type == "error"
        assert intent.intent_type == "invalid_command"
    
    @pytest.mark.asyncio
    async def test_parse_natural_language_patterns(self, chatops_router):
        """Test natural language pattern matching"""
        # Test deployment pattern
        response_type, plan = await chatops_router.parse_input("deploy the api service to production")
        assert response_type == "plan"
        assert isinstance(plan, ExecutionPlan)
        assert "Deploy api to production" in plan.title
        assert plan.affected_services == ["api", "api-production"]
        
        # Test Gong summary pattern
        response_type, plan = await chatops_router.parse_input("summarize yesterday's gong calls")
        assert response_type == "plan"
        assert isinstance(plan, ExecutionPlan)
        assert "Gong" in plan.title
        assert "gong" in plan.affected_services
        
        # Test research pattern
        response_type, plan = await chatops_router.parse_input("research AI orchestration patterns")
        assert response_type == "plan"
        assert isinstance(plan, ExecutionPlan)
        assert "Research" in plan.title
        assert "AI orchestration patterns" in plan.title
    
    @pytest.mark.asyncio
    async def test_ai_intent_classification(self, chatops_router, mock_model_router):
        """Test AI-powered intent classification"""
        # Mock AI response for deployment intent
        mock_model_router.call_model.return_value = '{"intent": "deploy", "confidence": 0.9, "parameters": {"service": "api", "environment": "staging"}, "suggested_action": "create deployment plan"}'
        
        response_type, plan = await chatops_router.parse_input("I need to ship the API to staging environment")
        
        # Verify AI model was called
        mock_model_router.select_model.assert_called_with("reasoning", ["intent_classification"])
        mock_model_router.call_model.assert_called_once()
        
        # Verify plan creation
        assert response_type == "plan"
        assert isinstance(plan, ExecutionPlan)
    
    @pytest.mark.asyncio
    async def test_ai_intent_classification_unclear(self, chatops_router, mock_model_router):
        """Test AI classification with unclear intent"""
        mock_model_router.call_model.return_value = '{"intent": "unclear", "confidence": 0.3, "parameters": {}, "suggested_action": "ask for clarification"}'
        
        response_type, intent = await chatops_router.parse_input("something confusing")
        
        assert response_type == "clarification"
        assert intent.intent_type == "unclear"
        assert intent.confidence == 0.3
    
    @pytest.mark.asyncio
    async def test_ai_intent_classification_error(self, chatops_router, mock_model_router):
        """Test AI classification error handling"""
        mock_model_router.call_model.side_effect = Exception("API Error")
        
        response_type, intent = await chatops_router.parse_input("deploy something")
        
        assert response_type == "error"
        assert intent.intent_type == "classification_error"
        assert "API Error" in intent.parameters["error"]
    
    @pytest.mark.asyncio
    async def test_create_deployment_plan(self, chatops_router):
        """Test deployment plan creation"""
        response_type, plan = await chatops_router._create_deployment_plan("api", "production", "deploy api to production")
        
        assert response_type == "plan"
        assert isinstance(plan, ExecutionPlan)
        assert plan.title == "Deploy api to production"
        assert len(plan.operations) == 4  # github, commit, deploy, health_check
        assert plan.operations[0]["type"] == "github"
        assert plan.operations[1]["type"] == "github"
        assert plan.operations[2]["type"] == "fly"
        assert plan.operations[3]["type"] == "monitoring"
        assert plan.affected_services == ["api", "api-production"]
        assert plan.requires_approval == True
    
    @pytest.mark.asyncio
    async def test_create_gong_summary_plan(self, chatops_router):
        """Test Gong summary plan creation"""
        response_type, plan = await chatops_router._create_gong_summary_plan("summarize recent gong calls")
        
        assert response_type == "plan"
        assert isinstance(plan, ExecutionPlan)
        assert "Gong" in plan.title
        assert len(plan.operations) == 4  # list, summarize, store, optional
        assert plan.operations[0]["type"] == "gong"
        assert plan.operations[1]["type"] == "ai"
        assert plan.operations[2]["type"] == "memory"
        assert plan.operations[3]["type"] == "optional"
        assert "gong" in plan.affected_services
    
    @pytest.mark.asyncio
    async def test_create_asana_task_plan(self, chatops_router):
        """Test Asana task plan creation"""
        response_type, plan = await chatops_router._create_asana_task_plan("create an asana task for follow-up")
        
        assert response_type == "plan"
        assert isinstance(plan, ExecutionPlan)
        assert "Asana" in plan.title
        assert len(plan.operations) == 4
        assert plan.operations[0]["type"] == "asana"
        assert plan.operations[1]["type"] == "ai"
        assert plan.operations[2]["type"] == "asana"
        assert plan.operations[3]["type"] == "memory"
        assert "asana" in plan.affected_services
    
    @pytest.mark.asyncio
    async def test_create_research_plan(self, chatops_router):
        """Test research plan creation"""
        response_type, plan = await chatops_router._create_research_plan("AI trends", "research AI trends")
        
        assert response_type == "plan"
        assert isinstance(plan, ExecutionPlan)
        assert "Research: AI trends" in plan.title
        assert len(plan.operations) == 4
        assert plan.operations[0]["type"] == "research"
        assert plan.operations[1]["type"] == "ai"
        assert plan.operations[2]["type"] == "memory"
        assert plan.operations[3]["type"] == "optional"
        assert "research_apis" in plan.affected_services
    
    @pytest.mark.asyncio
    async def test_plan_approval_workflow(self, chatops_router):
        """Test plan approval workflow"""
        # Create a plan first
        response_type, plan = await chatops_router._create_deployment_plan("api", "staging", "deploy api")
        plan_id = plan.id
        
        # Approve the plan
        response_type, intent = await chatops_router._approve_plan(plan_id)
        assert response_type == "approved"
        assert intent.intent_type == "plan_approved"
        assert intent.parameters["plan_id"] == plan_id
        assert intent.parameters["plan"] == plan
    
    @pytest.mark.asyncio
    async def test_plan_execution_workflow(self, chatops_router):
        """Test plan execution workflow"""
        # Create a plan first
        response_type, plan = await chatops_router._create_deployment_plan("api", "staging", "deploy api")
        plan_id = plan.id
        
        # Execute the plan
        response_type, intent = await chatops_router._execute_plan(plan_id)
        assert response_type == "executing"
        assert intent.intent_type == "plan_executing"
        assert intent.parameters["plan_id"] == plan_id
        
        # Plan should be removed from pending
        assert plan_id not in chatops_router.pending_plans
    
    @pytest.mark.asyncio
    async def test_plan_cancellation_workflow(self, chatops_router):
        """Test plan cancellation workflow"""
        # Create a plan first
        response_type, plan = await chatops_router._create_deployment_plan("api", "staging", "deploy api")
        plan_id = plan.id
        
        # Cancel the plan
        response_type, intent = await chatops_router._cancel_plan(plan_id)
        assert response_type == "cancelled"
        assert intent.intent_type == "plan_cancelled"
        assert intent.parameters["plan_id"] == plan_id
        
        # Plan should be removed from pending
        assert plan_id not in chatops_router.pending_plans
    
    @pytest.mark.asyncio
    async def test_plan_operations_without_id(self, chatops_router):
        """Test plan operations without specifying plan ID (uses most recent)"""
        # Create two plans
        response_type, plan1 = await chatops_router._create_deployment_plan("api", "staging", "deploy api")
        await asyncio.sleep(0.01)  # Ensure different timestamps
        response_type, plan2 = await chatops_router._create_gong_summary_plan("gong summary")
        
        # Approve without ID should use most recent (plan2)
        response_type, intent = await chatops_router._approve_plan(None)
        assert response_type == "approved"
        assert intent.parameters["plan_id"] == plan2.id
    
    @pytest.mark.asyncio
    async def test_plan_operations_no_plans(self, chatops_router):
        """Test plan operations when no plans exist"""
        # Try to approve when no plans exist
        response_type, intent = await chatops_router._approve_plan(None)
        assert response_type == "error"
        assert intent.intent_type == "no_plans"
        
        # Try to execute when no plans exist
        response_type, intent = await chatops_router._execute_plan(None)
        assert response_type == "error"
        assert intent.intent_type == "no_plans"
        
        # Try to cancel when no plans exist
        response_type, intent = await chatops_router._cancel_plan(None)
        assert response_type == "error"
        assert intent.intent_type == "no_plans"
    
    @pytest.mark.asyncio
    async def test_plan_operations_invalid_id(self, chatops_router):
        """Test plan operations with invalid plan ID"""
        response_type, intent = await chatops_router._approve_plan("invalid_id")
        assert response_type == "error"
        assert intent.intent_type == "plan_not_found"
        assert "invalid_id" in intent.parameters["error"]
    
    @pytest.mark.asyncio
    async def test_get_status(self, chatops_router):
        """Test status checking"""
        response_type, intent = await chatops_router._get_status("api")
        assert response_type == "status"
        assert intent.intent_type == "status_check"
        assert intent.parameters["service"] == "api"
        
        # Test status for all services
        response_type, intent = await chatops_router._get_status(None)
        assert intent.parameters["service"] == "all"
    
    @pytest.mark.asyncio
    async def test_get_help(self, chatops_router):
        """Test help system"""
        # Test general help
        response_type, intent = await chatops_router._get_help(None)
        assert response_type == "help"
        assert intent.intent_type == "help"
        assert "Available Commands" in intent.parameters["content"]
        
        # Test specific help topics
        response_type, intent = await chatops_router._get_help("modes")
        assert "Chat Modes" in intent.parameters["content"]
        
        response_type, intent = await chatops_router._get_help("examples")
        assert "Example Interactions" in intent.parameters["content"]
    
    def test_get_pending_plans(self, chatops_router):
        """Test getting pending plans"""
        # Initially empty
        plans = chatops_router.get_pending_plans()
        assert len(plans) == 0
        
        # Add a plan
        plan = ExecutionPlan(
            id="test123",
            title="Test Plan",
            description="Test",
            operations=[],
            risks=[],
            costs={},
            affected_services=[],
            estimated_duration="1 min"
        )
        chatops_router.pending_plans["test123"] = plan
        
        plans = chatops_router.get_pending_plans()
        assert len(plans) == 1
        assert plans[0] == plan
    
    def test_clear_pending_plans(self, chatops_router):
        """Test clearing pending plans"""
        # Add some plans
        for i in range(3):
            plan = ExecutionPlan(
                id=f"test{i}",
                title=f"Test Plan {i}",
                description="Test",
                operations=[],
                risks=[],
                costs={},
                affected_services=[],
                estimated_duration="1 min"
            )
            chatops_router.pending_plans[f"test{i}"] = plan
        
        # Clear and verify count
        count = chatops_router.clear_pending_plans()
        assert count == 3
        assert len(chatops_router.pending_plans) == 0
    
    @pytest.mark.asyncio
    async def test_invalid_mode_command(self, chatops_router):
        """Test invalid mode command"""
        response_type, intent = await chatops_router.parse_input("/mode invalid")
        assert response_type == "error"
        assert intent.intent_type == "invalid_mode"
        assert "Invalid mode: invalid" in intent.parameters["error"]
    
    @pytest.mark.asyncio
    async def test_pattern_matching_edge_cases(self, chatops_router):
        """Test edge cases in pattern matching"""
        # Deploy without environment (should default to production)
        response_type, plan = await chatops_router.parse_input("deploy the api")
        assert response_type == "plan"
        assert "production" in plan.title.lower()
        
        # Create task without specifying system
        response_type, plan = await chatops_router.parse_input("create a task for follow-up")
        assert response_type == "plan"
        assert "Task/Issue" in plan.title
        
        # Research with complex query
        response_type, plan = await chatops_router.parse_input("research machine learning trends in 2025")
        assert response_type == "plan"
        assert "machine learning trends in 2025" in plan.title

