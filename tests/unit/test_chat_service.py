"""
Unit tests for SOPHIA Intel Chat Service
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from backend.domains.chat.service import ChatService
from backend.domains.chat.models import ChatRequest, ChatMessage, ChatResponse
from backend.config.settings import Settings


class TestChatService:
    """Test cases for ChatService"""
    
    @pytest.fixture
    def chat_service(self, mock_config, mock_openrouter_client, mock_memory_client):
        """Create ChatService instance for testing"""
        with patch('backend.domains.chat.service.get_openrouter_client', return_value=mock_openrouter_client), \
             patch('backend.domains.chat.service.get_memory_client', return_value=mock_memory_client):
            service = ChatService(mock_config)
            return service
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_chat_request_basic(self, chat_service, sample_chat_request):
        """Test basic chat request processing"""
        request = ChatRequest(**sample_chat_request)
        
        response = await chat_service.process_chat_request(request)
        
        assert isinstance(response, ChatResponse)
        assert response.message is not None
        assert response.session_id == request.session_id
        assert response.backend_used in ["orchestrator", "swarm"]
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_message_for_backend_selection(self, chat_service):
        """Test backend selection analysis"""
        # Test cases for different message types
        test_cases = [
            {
                "message": "What is Python?",
                "expected_backend": "orchestrator",
                "expected_confidence": 0.8
            },
            {
                "message": "Build a comprehensive web application with authentication, database, and API",
                "expected_backend": "swarm",
                "expected_confidence": 0.9
            },
            {
                "message": "Help me fix this code error",
                "expected_backend": "orchestrator",
                "expected_confidence": 0.7
            },
            {
                "message": "Analyze the market trends and create a detailed report with multiple data sources",
                "expected_backend": "swarm",
                "expected_confidence": 0.85
            }
        ]
        
        for case in test_cases:
            analysis = await chat_service.analyze_message_for_backend(case["message"])
            
            assert analysis["recommended_backend"] == case["expected_backend"]
            assert analysis["confidence"] >= case["expected_confidence"]
            assert "reasoning" in analysis
            assert isinstance(analysis["keywords_found"], list)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_streaming_response(self, chat_service, sample_chat_request):
        """Test streaming chat response"""
        request = ChatRequest(**sample_chat_request)
        request.stream = True
        
        chunks = []
        async for chunk in chat_service.stream_chat_response(request):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        assert all(hasattr(chunk, 'content') for chunk in chunks)
        
        # Verify final chunk has completion info
        final_chunk = chunks[-1]
        assert hasattr(final_chunk, 'finish_reason')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_web_research_integration(self, chat_service, sample_chat_request):
        """Test web research integration"""
        request = ChatRequest(**sample_chat_request)
        request.web_access = True
        request.message = "What are the latest developments in AI?"
        
        with patch('backend.domains.chat.service.EnhancedWebResearch') as mock_research:
            mock_research_instance = AsyncMock()
            mock_research_instance.research.return_value = {
                "results": [
                    {
                        "title": "Latest AI Developments",
                        "content": "Recent advances in AI include...",
                        "url": "https://example.com/ai-news",
                        "relevance_score": 0.9
                    }
                ],
                "summary": "Recent AI developments focus on...",
                "confidence": 0.85
            }
            mock_research.return_value = mock_research_instance
            
            response = await chat_service.process_chat_request(request)
            
            assert response.research_context is not None
            assert "results" in response.research_context
            mock_research_instance.research.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_persona_integration(self, chat_service, sample_chat_request):
        """Test persona integration"""
        request = ChatRequest(**sample_chat_request)
        request.persona = "technical_expert"
        
        with patch('backend.domains.chat.service.PersonaService') as mock_persona:
            mock_persona_instance = AsyncMock()
            mock_persona_instance.apply_persona.return_value = {
                "enhanced_message": "As a technical expert, I'll help you with: " + request.message,
                "system_prompt": "You are a technical expert...",
                "voice_settings": {"voice_id": "expert_voice"}
            }
            mock_persona.return_value = mock_persona_instance
            
            response = await chat_service.process_chat_request(request)
            
            assert response.persona_applied == "technical_expert"
            mock_persona_instance.apply_persona.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_voice_generation(self, chat_service, sample_chat_request):
        """Test voice generation"""
        request = ChatRequest(**sample_chat_request)
        request.voice_enabled = True
        
        with patch('backend.domains.chat.service.PersonaService') as mock_persona:
            mock_persona_instance = AsyncMock()
            mock_persona_instance.generate_voice.return_value = {
                "audio_url": "https://example.com/audio.mp3",
                "duration": 15.5,
                "voice_id": "default_voice"
            }
            mock_persona.return_value = mock_persona_instance
            
            response = await chat_service.process_chat_request(request)
            
            assert response.voice_audio is not None
            assert "audio_url" in response.voice_audio
            mock_persona_instance.generate_voice.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_memory_integration(self, chat_service, sample_chat_request, mock_memory_client):
        """Test memory integration"""
        request = ChatRequest(**sample_chat_request)
        
        # Mock conversation history
        mock_memory_client.get_conversation_history.return_value = [
            {
                "role": "user",
                "content": "Previous question",
                "timestamp": 1234567890
            },
            {
                "role": "assistant",
                "content": "Previous answer",
                "timestamp": 1234567891
            }
        ]
        
        response = await chat_service.process_chat_request(request)
        
        # Verify memory was accessed
        mock_memory_client.get_conversation_history.assert_called_with(
            session_id=request.session_id,
            limit=50
        )
        
        # Verify new message was stored
        mock_memory_client.store_message.assert_called()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_error_handling(self, chat_service, sample_chat_request):
        """Test error handling in chat service"""
        request = ChatRequest(**sample_chat_request)
        
        # Test OpenRouter API failure
        with patch('backend.domains.chat.service.get_openrouter_client') as mock_client:
            mock_client.return_value.chat_completion.side_effect = Exception("API Error")
            
            response = await chat_service.process_chat_request(request)
            
            assert response.error is not None
            assert "API Error" in response.error
            assert response.message is not None  # Should have fallback message
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_rate_limiting(self, chat_service, sample_chat_request):
        """Test rate limiting functionality"""
        request = ChatRequest(**sample_chat_request)
        
        # Simulate multiple rapid requests
        tasks = []
        for i in range(10):
            task = chat_service.process_chat_request(request)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Some requests should succeed, some might be rate limited
        successful_responses = [r for r in responses if isinstance(r, ChatResponse)]
        assert len(successful_responses) > 0
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_context_optimization(self, chat_service, sample_chat_request, mock_memory_client):
        """Test context optimization for long conversations"""
        request = ChatRequest(**sample_chat_request)
        
        # Mock long conversation history
        long_history = []
        for i in range(100):
            long_history.extend([
                {
                    "role": "user",
                    "content": f"User message {i}",
                    "timestamp": 1234567890 + i
                },
                {
                    "role": "assistant",
                    "content": f"Assistant response {i}",
                    "timestamp": 1234567890 + i + 1
                }
            ])
        
        mock_memory_client.get_conversation_history.return_value = long_history
        
        response = await chat_service.process_chat_request(request)
        
        # Verify context was optimized (should not include all 200 messages)
        assert response.context_optimized is True
        assert response.context_length < len(long_history)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_backend_performance_tracking(self, chat_service, sample_chat_request):
        """Test backend performance tracking"""
        request = ChatRequest(**sample_chat_request)
        
        response = await chat_service.process_chat_request(request)
        
        assert response.performance_metrics is not None
        assert "response_time" in response.performance_metrics
        assert "backend_used" in response.performance_metrics
        assert "token_usage" in response.performance_metrics
    
    @pytest.mark.unit
    def test_chat_request_validation(self):
        """Test chat request validation"""
        # Valid request
        valid_request = {
            "message": "Hello",
            "session_id": "test-session",
            "user_id": "test-user"
        }
        request = ChatRequest(**valid_request)
        assert request.message == "Hello"
        
        # Invalid request - missing message
        with pytest.raises(ValueError):
            ChatRequest(session_id="test", user_id="test")
        
        # Invalid request - empty message
        with pytest.raises(ValueError):
            ChatRequest(message="", session_id="test", user_id="test")
    
    @pytest.mark.unit
    def test_chat_message_model(self):
        """Test ChatMessage model"""
        message = ChatMessage(
            role="user",
            content="Test message",
            timestamp=1234567890
        )
        
        assert message.role == "user"
        assert message.content == "Test message"
        assert message.timestamp == 1234567890
        
        # Test serialization
        message_dict = message.dict()
        assert "role" in message_dict
        assert "content" in message_dict
        assert "timestamp" in message_dict
    
    @pytest.mark.unit
    def test_chat_response_model(self):
        """Test ChatResponse model"""
        response = ChatResponse(
            message="Test response",
            session_id="test-session",
            backend_used="orchestrator"
        )
        
        assert response.message == "Test response"
        assert response.session_id == "test-session"
        assert response.backend_used == "orchestrator"
        
        # Test optional fields
        response.research_context = {"results": []}
        response.voice_audio = {"audio_url": "test.mp3"}
        
        assert response.research_context is not None
        assert response.voice_audio is not None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, chat_service, sample_chat_request):
        """Test handling concurrent chat requests"""
        request = ChatRequest(**sample_chat_request)
        
        # Create multiple concurrent requests
        tasks = []
        for i in range(5):
            modified_request = request.copy()
            modified_request.session_id = f"session-{i}"
            tasks.append(chat_service.process_chat_request(modified_request))
        
        responses = await asyncio.gather(*tasks)
        
        assert len(responses) == 5
        assert all(isinstance(r, ChatResponse) for r in responses)
        
        # Verify each response has unique session_id
        session_ids = [r.session_id for r in responses]
        assert len(set(session_ids)) == 5
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_swarm_backend_selection(self, chat_service):
        """Test explicit swarm backend selection"""
        request = ChatRequest(
            message="Build a complex web application",
            session_id="test-session",
            user_id="test-user",
            use_swarm=True
        )
        
        with patch('backend.domains.chat.service.SwarmChatInterface') as mock_swarm:
            mock_swarm_instance = AsyncMock()
            mock_swarm_instance.process_request.return_value = {
                "response": "Swarm response",
                "agents_used": ["architect", "developer", "tester"]
            }
            mock_swarm.return_value = mock_swarm_instance
            
            response = await chat_service.process_chat_request(request)
            
            assert response.backend_used == "swarm"
            assert response.agents_used is not None
            mock_swarm_instance.process_request.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_deep_research_mode(self, chat_service, sample_chat_request):
        """Test deep research mode"""
        request = ChatRequest(**sample_chat_request)
        request.deep_research = True
        request.message = "Analyze the current state of quantum computing"
        
        with patch('backend.domains.chat.service.EnhancedWebResearch') as mock_research:
            mock_research_instance = AsyncMock()
            mock_research_instance.deep_research.return_value = {
                "comprehensive_analysis": "Detailed quantum computing analysis...",
                "sources": ["academic", "news", "technical"],
                "confidence": 0.92,
                "research_depth": "comprehensive"
            }
            mock_research.return_value = mock_research_instance
            
            response = await chat_service.process_chat_request(request)
            
            assert response.research_depth == "comprehensive"
            assert response.research_context is not None
            mock_research_instance.deep_research.assert_called_once()

