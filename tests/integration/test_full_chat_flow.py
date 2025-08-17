"""
Integration tests for full SOPHIA Intel chat flow
"""

import pytest
import asyncio
import json
from typing import Dict, Any
from unittest.mock import patch, AsyncMock

from backend.domains.chat.service import ChatService
from backend.domains.chat.models import ChatRequest
from backend.services.infrastructure_automation import InfrastructureAutomationService
from backend.monitoring.distributed_tracing import DistributedTracingSystem


class TestFullChatFlow:
    """Integration tests for complete chat workflow"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_chat_flow(self, mock_config, sample_chat_request):
        """Test complete end-to-end chat flow"""
        # Setup all required services
        with patch('backend.domains.chat.service.get_openrouter_client') as mock_openrouter, \
             patch('backend.domains.chat.service.get_memory_client') as mock_memory, \
             patch('backend.domains.chat.service.EnhancedWebResearch') as mock_research:
            
            # Configure mocks
            mock_openrouter.return_value.chat_completion.return_value = {
                "choices": [{"message": {"role": "assistant", "content": "Integration test response"}}],
                "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30}
            }
            
            mock_memory.return_value.get_conversation_history.return_value = []
            mock_memory.return_value.store_message.return_value = {"success": True}
            
            mock_research.return_value.research.return_value = {
                "results": [{"title": "Test Result", "content": "Test content"}],
                "summary": "Test research summary"
            }
            
            # Create chat service
            chat_service = ChatService(mock_config)
            
            # Process request
            request = ChatRequest(**sample_chat_request)
            response = await chat_service.process_chat_request(request)
            
            # Verify response
            assert response is not None
            assert response.message is not None
            assert response.session_id == request.session_id
            assert response.performance_metrics is not None
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_chat_with_infrastructure_automation(self, mock_config, mock_lambda_labs_client):
        """Test chat integration with infrastructure automation"""
        request_data = {
            "message": "Scale up the Lambda Labs servers to handle increased load",
            "session_id": "infra-test-session",
            "user_id": "admin-user",
            "use_swarm": False
        }
        
        with patch('backend.services.infrastructure_automation.LambdaLabsClient', return_value=mock_lambda_labs_client):
            # Setup infrastructure automation
            infra_service = InfrastructureAutomationService(mock_config)
            
            # Setup chat service with infrastructure integration
            with patch('backend.domains.chat.service.get_openrouter_client') as mock_openrouter, \
                 patch('backend.domains.chat.service.get_memory_client') as mock_memory:
                
                mock_openrouter.return_value.chat_completion.return_value = {
                    "choices": [{"message": {"role": "assistant", "content": "I'll scale up the Lambda Labs servers for you."}}],
                    "usage": {"prompt_tokens": 25, "completion_tokens": 15, "total_tokens": 40}
                }
                
                mock_memory.return_value.get_conversation_history.return_value = []
                mock_memory.return_value.store_message.return_value = {"success": True}
                
                chat_service = ChatService(mock_config)
                
                # Process infrastructure request
                request = ChatRequest(**request_data)
                response = await chat_service.process_chat_request(request)
                
                # Verify infrastructure action was triggered
                assert response is not None
                assert "scale" in response.message.lower() or "lambda" in response.message.lower()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_chat_with_distributed_tracing(self, mock_config, sample_chat_request):
        """Test chat flow with distributed tracing"""
        tracing_config = {
            "sentry": {
                "dsn": "https://test@sentry.io/test",
                "traces_sample_rate": 1.0
            },
            "jaeger": {
                "enabled": True,
                "endpoint": "http://localhost:14268/api/traces"
            }
        }
        
        with patch('backend.monitoring.distributed_tracing.sentry_sdk') as mock_sentry:
            # Setup tracing system
            tracing_system = DistributedTracingSystem(tracing_config)
            
            # Setup chat service with tracing
            with patch('backend.domains.chat.service.get_openrouter_client') as mock_openrouter, \
                 patch('backend.domains.chat.service.get_memory_client') as mock_memory:
                
                mock_openrouter.return_value.chat_completion.return_value = {
                    "choices": [{"message": {"role": "assistant", "content": "Traced response"}}],
                    "usage": {"prompt_tokens": 15, "completion_tokens": 8, "total_tokens": 23}
                }
                
                mock_memory.return_value.get_conversation_history.return_value = []
                mock_memory.return_value.store_message.return_value = {"success": True}
                
                chat_service = ChatService(mock_config)
                
                # Process request with tracing
                request = ChatRequest(**sample_chat_request)
                
                with tracing_system.start_span("chat_request") as span:
                    response = await chat_service.process_chat_request(request)
                    tracing_system.add_span_tag(span, "session_id", request.session_id)
                
                # Verify tracing was used
                assert response is not None
                mock_sentry.start_span.assert_called()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multi_backend_conversation(self, mock_config):
        """Test conversation that uses multiple backends"""
        conversation_flow = [
            {
                "message": "What is machine learning?",
                "expected_backend": "orchestrator"
            },
            {
                "message": "Now build a complete ML pipeline with data preprocessing, model training, and deployment",
                "expected_backend": "swarm"
            },
            {
                "message": "Explain the model architecture you chose",
                "expected_backend": "orchestrator"
            }
        ]
        
        with patch('backend.domains.chat.service.get_openrouter_client') as mock_openrouter, \
             patch('backend.domains.chat.service.get_memory_client') as mock_memory, \
             patch('backend.domains.chat.service.SwarmChatInterface') as mock_swarm:
            
            # Configure mocks
            mock_openrouter.return_value.chat_completion.return_value = {
                "choices": [{"message": {"role": "assistant", "content": "Backend response"}}],
                "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30}
            }
            
            mock_swarm.return_value.process_request.return_value = {
                "response": "Swarm response",
                "agents_used": ["architect", "developer"]
            }
            
            conversation_history = []
            mock_memory.return_value.get_conversation_history.return_value = conversation_history
            mock_memory.return_value.store_message.return_value = {"success": True}
            
            chat_service = ChatService(mock_config)
            session_id = "multi-backend-session"
            
            # Process conversation flow
            for i, step in enumerate(conversation_flow):
                request = ChatRequest(
                    message=step["message"],
                    session_id=session_id,
                    user_id="test-user"
                )
                
                response = await chat_service.process_chat_request(request)
                
                # Verify backend selection
                backend_analysis = await chat_service.analyze_message_for_backend(step["message"])
                assert backend_analysis["recommended_backend"] == step["expected_backend"]
                
                # Add to conversation history for next iteration
                conversation_history.extend([
                    {"role": "user", "content": step["message"], "timestamp": 1234567890 + i},
                    {"role": "assistant", "content": response.message, "timestamp": 1234567891 + i}
                ])
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_chat_with_web_research_and_memory(self, mock_config):
        """Test chat with both web research and memory integration"""
        session_id = "research-memory-session"
        
        with patch('backend.domains.chat.service.get_openrouter_client') as mock_openrouter, \
             patch('backend.domains.chat.service.get_memory_client') as mock_memory, \
             patch('backend.domains.chat.service.EnhancedWebResearch') as mock_research:
            
            # Configure mocks
            mock_openrouter.return_value.chat_completion.return_value = {
                "choices": [{"message": {"role": "assistant", "content": "Research-enhanced response"}}],
                "usage": {"prompt_tokens": 30, "completion_tokens": 20, "total_tokens": 50}
            }
            
            mock_research.return_value.research.return_value = {
                "results": [
                    {
                        "title": "Latest AI Research",
                        "content": "Recent developments in AI...",
                        "url": "https://example.com/ai-research",
                        "relevance_score": 0.9
                    }
                ],
                "summary": "AI research summary",
                "confidence": 0.85
            }
            
            # Simulate existing conversation history
            existing_history = [
                {"role": "user", "content": "Tell me about AI", "timestamp": 1234567880},
                {"role": "assistant", "content": "AI is...", "timestamp": 1234567881}
            ]
            mock_memory.return_value.get_conversation_history.return_value = existing_history
            mock_memory.return_value.store_message.return_value = {"success": True}
            
            chat_service = ChatService(mock_config)
            
            # Process request with web research
            request = ChatRequest(
                message="What are the latest developments in AI research?",
                session_id=session_id,
                user_id="test-user",
                web_access=True
            )
            
            response = await chat_service.process_chat_request(request)
            
            # Verify research was performed
            mock_research.return_value.research.assert_called_once()
            
            # Verify memory was accessed and updated
            mock_memory.return_value.get_conversation_history.assert_called_with(
                session_id=session_id,
                limit=50
            )
            mock_memory.return_value.store_message.assert_called()
            
            # Verify response includes research context
            assert response.research_context is not None
            assert "results" in response.research_context
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_recovery_flow(self, mock_config, sample_chat_request):
        """Test error recovery in chat flow"""
        with patch('backend.domains.chat.service.get_openrouter_client') as mock_openrouter, \
             patch('backend.domains.chat.service.get_memory_client') as mock_memory:
            
            # Configure primary service to fail
            mock_openrouter.return_value.chat_completion.side_effect = Exception("Primary service failed")
            
            # Configure memory to work
            mock_memory.return_value.get_conversation_history.return_value = []
            mock_memory.return_value.store_message.return_value = {"success": True}
            
            chat_service = ChatService(mock_config)
            
            # Process request (should handle error gracefully)
            request = ChatRequest(**sample_chat_request)
            response = await chat_service.process_chat_request(request)
            
            # Verify error was handled
            assert response is not None
            assert response.error is not None
            assert "failed" in response.error.lower()
            
            # Verify fallback response was provided
            assert response.message is not None
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_streaming_integration(self, mock_config, sample_chat_request):
        """Test streaming response integration"""
        with patch('backend.domains.chat.service.get_openrouter_client') as mock_openrouter, \
             patch('backend.domains.chat.service.get_memory_client') as mock_memory:
            
            # Configure streaming response
            async def mock_stream():
                chunks = [
                    {"choices": [{"delta": {"content": "Hello"}}]},
                    {"choices": [{"delta": {"content": " there!"}}]},
                    {"choices": [{"delta": {}}], "finish_reason": "stop"}
                ]
                for chunk in chunks:
                    yield chunk
            
            mock_openrouter.return_value.stream_chat_completion.return_value = mock_stream()
            mock_memory.return_value.get_conversation_history.return_value = []
            mock_memory.return_value.store_message.return_value = {"success": True}
            
            chat_service = ChatService(mock_config)
            
            # Process streaming request
            request = ChatRequest(**sample_chat_request)
            request.stream = True
            
            chunks = []
            async for chunk in chat_service.stream_chat_response(request):
                chunks.append(chunk)
            
            # Verify streaming worked
            assert len(chunks) >= 2  # At least content chunks + final chunk
            assert any(hasattr(chunk, 'content') and chunk.content for chunk in chunks)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, mock_config):
        """Test handling multiple concurrent chat sessions"""
        with patch('backend.domains.chat.service.get_openrouter_client') as mock_openrouter, \
             patch('backend.domains.chat.service.get_memory_client') as mock_memory:
            
            mock_openrouter.return_value.chat_completion.return_value = {
                "choices": [{"message": {"role": "assistant", "content": "Concurrent response"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
            }
            
            mock_memory.return_value.get_conversation_history.return_value = []
            mock_memory.return_value.store_message.return_value = {"success": True}
            
            chat_service = ChatService(mock_config)
            
            # Create multiple concurrent sessions
            sessions = []
            for i in range(5):
                request = ChatRequest(
                    message=f"Message from session {i}",
                    session_id=f"session-{i}",
                    user_id=f"user-{i}"
                )
                sessions.append(chat_service.process_chat_request(request))
            
            # Process all sessions concurrently
            responses = await asyncio.gather(*sessions)
            
            # Verify all sessions completed successfully
            assert len(responses) == 5
            assert all(isinstance(r, type(responses[0])) for r in responses)
            
            # Verify each session maintained its identity
            session_ids = [r.session_id for r in responses]
            assert len(set(session_ids)) == 5
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self, mock_config, sample_chat_request):
        """Test integration with performance monitoring"""
        with patch('backend.domains.chat.service.get_openrouter_client') as mock_openrouter, \
             patch('backend.domains.chat.service.get_memory_client') as mock_memory, \
             patch('backend.monitoring.observability_service.ObservabilityService') as mock_observability:
            
            mock_openrouter.return_value.chat_completion.return_value = {
                "choices": [{"message": {"role": "assistant", "content": "Monitored response"}}],
                "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30}
            }
            
            mock_memory.return_value.get_conversation_history.return_value = []
            mock_memory.return_value.store_message.return_value = {"success": True}
            
            mock_observability_instance = AsyncMock()
            mock_observability.return_value = mock_observability_instance
            
            chat_service = ChatService(mock_config)
            
            # Process request with monitoring
            request = ChatRequest(**sample_chat_request)
            response = await chat_service.process_chat_request(request)
            
            # Verify response includes performance metrics
            assert response.performance_metrics is not None
            assert "response_time" in response.performance_metrics
            assert "token_usage" in response.performance_metrics
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_sophia_awareness_integration(self, mock_config):
        """Test integration with SOPHIA's self-awareness system"""
        request_data = {
            "message": "What are your capabilities and authority levels?",
            "session_id": "awareness-test-session",
            "user_id": "test-user"
        }
        
        with patch('backend.domains.chat.service.get_openrouter_client') as mock_openrouter, \
             patch('backend.domains.chat.service.get_memory_client') as mock_memory, \
             patch('backend.domains.intelligence.sophia_awareness.SophiaAwarenessSystem') as mock_awareness:
            
            mock_openrouter.return_value.chat_completion.return_value = {
                "choices": [{"message": {"role": "assistant", "content": "I have supreme authority over infrastructure..."}}],
                "usage": {"prompt_tokens": 25, "completion_tokens": 50, "total_tokens": 75}
            }
            
            mock_memory.return_value.get_conversation_history.return_value = []
            mock_memory.return_value.store_message.return_value = {"success": True}
            
            mock_awareness_instance = AsyncMock()
            mock_awareness_instance.get_capability_summary.return_value = {
                "infrastructure_authority": "supreme",
                "service_control": "complete",
                "decision_making": "autonomous"
            }
            mock_awareness.return_value = mock_awareness_instance
            
            chat_service = ChatService(mock_config)
            
            # Process awareness request
            request = ChatRequest(**request_data)
            response = await chat_service.process_chat_request(request)
            
            # Verify SOPHIA's awareness was integrated
            assert response is not None
            assert "authority" in response.message.lower() or "capabilities" in response.message.lower()
            mock_awareness_instance.get_capability_summary.assert_called_once()

