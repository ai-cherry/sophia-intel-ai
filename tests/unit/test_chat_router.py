"""
Unit tests for Chat Router
Tests intelligent backend selection and routing logic
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from backend.chat_router import ChatRouter, EnhancedChatRequest


class TestChatRouter:
    """Test cases for ChatRouter"""
    
    @pytest.fixture
    def chat_router(self):
        """Create ChatRouter instance for testing"""
        return ChatRouter()
    
    @pytest.fixture
    def sample_request(self):
        """Sample chat request for testing"""
        return EnhancedChatRequest(
            message="What is Python?",
            session_id="test_session_123",
            use_swarm=None,
            web_access=False,
            deep_research=False,
            training=False,
            user_id="test_user",
            model="gpt-4",
            temperature=0.7
        )
    
    def test_analyze_message_for_swarm_keywords(self, chat_router):
        """Test swarm keyword detection"""
        # Swarm keywords should trigger swarm
        swarm_messages = [
            "Build a comprehensive web application",
            "Create a project with multiple components",
            "Analyze this architecture thoroughly",
            "I need a comprehensive workflow solution"
        ]
        
        for message in swarm_messages:
            result = chat_router._analyze_message_for_backend(message)
            assert result["recommended_backend"] == "swarm"
            assert result["confidence"] > 0.6
    
    def test_analyze_message_for_orchestrator_keywords(self, chat_router):
        """Test orchestrator keyword detection"""
        # Simple questions should go to orchestrator
        orchestrator_messages = [
            "What is Python?",
            "How do I write a function?",
            "Help me fix this code error",
            "Can you assist with this problem?"
        ]
        
        for message in orchestrator_messages:
            result = chat_router._analyze_message_for_backend(message)
            assert result["recommended_backend"] == "orchestrator"
            assert result["confidence"] > 0.5
    
    def test_analyze_message_complexity(self, chat_router):
        """Test message complexity analysis"""
        # Long, complex messages should prefer swarm
        complex_message = """
        I need you to analyze the current market trends in artificial intelligence,
        create a comprehensive business plan for a new AI startup,
        design the technical architecture including microservices,
        and provide a detailed implementation roadmap with timelines.
        Please also include risk analysis and mitigation strategies.
        """
        
        result = chat_router._analyze_message_for_backend(complex_message)
        assert result["recommended_backend"] == "swarm"
        assert result["confidence"] > 0.7
        assert result["factors"]["complexity_score"] > 0.8
    
    def test_explicit_swarm_flag(self, chat_router, sample_request):
        """Test explicit use_swarm flag override"""
        sample_request.use_swarm = True
        
        result = chat_router._determine_backend(sample_request)
        assert result["backend"] == "swarm"
        assert result["reason"] == "explicit_flag"
    
    def test_explicit_orchestrator_flag(self, chat_router, sample_request):
        """Test explicit use_swarm=False flag"""
        sample_request.use_swarm = False
        
        result = chat_router._determine_backend(sample_request)
        assert result["backend"] == "orchestrator"
        assert result["reason"] == "explicit_flag"
    
    @pytest.mark.asyncio
    async def test_route_to_orchestrator(self, chat_router, sample_request):
        """Test routing to orchestrator"""
        with patch('backend.chat_router.ChatRouter._call_orchestrator') as mock_orchestrator:
            mock_orchestrator.return_value = {"response": "Test response", "backend": "orchestrator"}
            
            result = await chat_router.route_chat(sample_request)
            
            assert result["backend_used"] == "orchestrator"
            assert "response" in result
            mock_orchestrator.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_route_to_swarm(self, chat_router):
        """Test routing to swarm"""
        swarm_request = EnhancedChatRequest(
            message="Build a comprehensive web application",
            session_id="test_session_123",
            use_swarm=True
        )
        
        with patch('backend.chat_router.ChatRouter._call_swarm') as mock_swarm:
            mock_swarm.return_value = {"response": "Swarm response", "backend": "swarm"}
            
            result = await chat_router.route_chat(swarm_request)
            
            assert result["backend_used"] == "swarm"
            assert "response" in result
            mock_swarm.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fallback_on_error(self, chat_router, sample_request):
        """Test fallback when primary backend fails"""
        with patch('backend.chat_router.ChatRouter._call_orchestrator') as mock_orchestrator:
            mock_orchestrator.side_effect = Exception("Orchestrator failed")
            
            with patch('backend.chat_router.ChatRouter._call_swarm') as mock_swarm:
                mock_swarm.return_value = {"response": "Fallback response", "backend": "swarm"}
                
                result = await chat_router.route_chat(sample_request)
                
                assert result["backend_used"] == "swarm"
                assert result["fallback_used"] == True
                assert "error" in result["metadata"]
    
    def test_backend_selection_factors(self, chat_router):
        """Test backend selection factor calculation"""
        message = "Create a comprehensive project with testing and deployment"
        
        result = chat_router._analyze_message_for_backend(message)
        factors = result["factors"]
        
        # Should detect multiple factors
        assert "swarm_keywords" in factors
        assert "orchestrator_keywords" in factors
        assert "complexity_score" in factors
        assert "question_indicators" in factors
        
        # Complexity should be high for this message
        assert factors["complexity_score"] > 0.5
    
    def test_confidence_calculation(self, chat_router):
        """Test confidence score calculation"""
        # High confidence swarm case
        swarm_message = "Build comprehensive architecture with testing workflow"
        result = chat_router._analyze_message_for_backend(swarm_message)
        assert result["confidence"] > 0.8
        
        # High confidence orchestrator case
        orchestrator_message = "What is the capital of France?"
        result = chat_router._analyze_message_for_backend(orchestrator_message)
        assert result["confidence"] > 0.7
        
        # Ambiguous case should have lower confidence
        ambiguous_message = "Help me with this"
        result = chat_router._analyze_message_for_backend(ambiguous_message)
        assert result["confidence"] < 0.6
    
    @pytest.mark.asyncio
    async def test_analytics_tracking(self, chat_router, sample_request):
        """Test that analytics are properly tracked"""
        with patch('backend.chat_router.ChatRouter._call_orchestrator') as mock_orchestrator:
            mock_orchestrator.return_value = {"response": "Test response", "backend": "orchestrator"}
            
            with patch('backend.chat_router.track_backend_usage') as mock_track:
                result = await chat_router.route_chat(sample_request)
                
                # Should track backend usage
                mock_track.assert_called()
    
    def test_message_preprocessing(self, chat_router):
        """Test message preprocessing and normalization"""
        # Test with various message formats
        messages = [
            "  What is Python?  ",  # Whitespace
            "WHAT IS PYTHON?",      # Uppercase
            "What is Python???",    # Multiple punctuation
            "What\nis\nPython?",    # Newlines
        ]
        
        for message in messages:
            result = chat_router._analyze_message_for_backend(message)
            assert result is not None
            assert "recommended_backend" in result
    
    @pytest.mark.asyncio
    async def test_session_context_integration(self, chat_router, sample_request):
        """Test integration with session context"""
        with patch('backend.chat_router.ChatRouter._get_session_context') as mock_context:
            mock_context.return_value = {
                "previous_backend": "swarm",
                "conversation_type": "technical",
                "message_count": 5
            }
            
            with patch('backend.chat_router.ChatRouter._call_orchestrator') as mock_orchestrator:
                mock_orchestrator.return_value = {"response": "Test response", "backend": "orchestrator"}
                
                result = await chat_router.route_chat(sample_request)
                
                # Should consider session context
                mock_context.assert_called_with(sample_request.session_id)
    
    def test_error_handling(self, chat_router):
        """Test error handling in backend analysis"""
        # Test with None message
        result = chat_router._analyze_message_for_backend(None)
        assert result["recommended_backend"] == "orchestrator"  # Default fallback
        
        # Test with empty message
        result = chat_router._analyze_message_for_backend("")
        assert result["recommended_backend"] == "orchestrator"  # Default fallback
        
        # Test with very long message
        long_message = "test " * 10000
        result = chat_router._analyze_message_for_backend(long_message)
        assert result is not None  # Should handle gracefully


@pytest.mark.asyncio
class TestChatRouterIntegration:
    """Integration tests for ChatRouter with real components"""
    
    @pytest.fixture
    def chat_router(self):
        """Create ChatRouter with mocked dependencies"""
        router = ChatRouter()
        # Mock external dependencies
        router.orchestrator_client = AsyncMock()
        router.swarm_client = AsyncMock()
        return router
    
    async def test_end_to_end_orchestrator_flow(self, chat_router):
        """Test complete flow through orchestrator"""
        request = EnhancedChatRequest(
            message="What is 2+2?",
            session_id="test_session"
        )
        
        chat_router.orchestrator_client.chat.return_value = {
            "response": "2+2 equals 4",
            "metadata": {"tokens": 10}
        }
        
        result = await chat_router.route_chat(request)
        
        assert result["backend_used"] == "orchestrator"
        assert "2+2 equals 4" in result["response"]
        assert result["success"] == True
    
    async def test_end_to_end_swarm_flow(self, chat_router):
        """Test complete flow through swarm"""
        request = EnhancedChatRequest(
            message="Build a comprehensive web application with testing",
            session_id="test_session"
        )
        
        chat_router.swarm_client.process.return_value = {
            "response": "I'll help you build a comprehensive web application...",
            "agents_used": ["architect", "developer", "tester"],
            "metadata": {"complexity": "high"}
        }
        
        result = await chat_router.route_chat(request)
        
        assert result["backend_used"] == "swarm"
        assert "comprehensive web application" in result["response"]
        assert result["success"] == True
        assert "agents_used" in result["metadata"]

