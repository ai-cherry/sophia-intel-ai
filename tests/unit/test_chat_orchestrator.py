"""
Unit Tests for ChatOrchestrator
Tests core functionality, error handling, and circuit breakers
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any

from app.ui.unified.chat_orchestrator import (
    ChatOrchestrator,
    ConnectionState,
    WebSocketErrorBoundary,
    CircuitBreaker,
    ConnectionTimeoutManager
)
from app.api.contracts import (
    ChatRequestV1,
    ChatRequestV2,
    ChatResponseV1,
    ChatResponseV2,
    StreamTokenV1
)
from app.infrastructure.dependency_injection import ServiceConfig

# ==================== Fixtures ====================

@pytest.fixture
def service_config():
    """Service configuration for testing"""
    return ServiceConfig(
        ollama_url="http://test-ollama:11434",
        redis_url="redis://test-redis:6379",
        mcp_server_url="http://test-mcp:8004",
        n8n_url="http://test-n8n:5678",
        max_websocket_connections=10,
        connection_idle_timeout_seconds=60
    )

@pytest.fixture
async def chat_orchestrator(service_config):
    """Create ChatOrchestrator instance for testing"""
    orchestrator = ChatOrchestrator(
        ollama_url=service_config.ollama_url,
        redis_url=service_config.redis_url,
        mcp_server_url=service_config.mcp_server_url,
        n8n_url=service_config.n8n_url
    )
    
    # Mock dependencies
    orchestrator.command_dispatcher = AsyncMock()
    orchestrator.unified_orchestrator = AsyncMock()
    orchestrator.orchestra_manager = Mock()
    orchestrator.manager_integration = Mock()
    
    await orchestrator.initialize()
    yield orchestrator
    await orchestrator.shutdown()

@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection"""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.send_text = AsyncMock()
    ws.receive_text = AsyncMock()
    ws.close = AsyncMock()
    return ws

@pytest.fixture
def connection_state(mock_websocket):
    """Create ConnectionState for testing"""
    return ConnectionState(
        client_id="test-client",
        session_id="test-session",
        websocket=mock_websocket
    )

# ==================== ChatOrchestrator Tests ====================

class TestChatOrchestrator:
    """Test ChatOrchestrator functionality"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, chat_orchestrator):
        """Test orchestrator initialization"""
        assert chat_orchestrator.initialized
        assert chat_orchestrator.circuit_breakers is not None
        assert len(chat_orchestrator.circuit_breakers) > 0
    
    @pytest.mark.asyncio
    async def test_handle_chat_v1_success(self, chat_orchestrator):
        """Test successful V1 chat request handling"""
        request = ChatRequestV1(
            message="Test message",
            session_id="test-123"
        )
        
        # Mock command dispatcher response
        mock_result = Mock()
        mock_result.success = True
        mock_result.response = "Test response"
        mock_result.execution_mode = Mock(value="balanced")
        mock_result.quality_score = 0.9
        mock_result.execution_time = 0.5
        mock_result.error = None
        mock_result.metadata = {}
        
        chat_orchestrator.command_dispatcher.process_command.return_value = mock_result
        
        # Mock manager integration
        chat_orchestrator.manager_integration.process_message.return_value = {
            "intent": "test_intent",
            "parameters": {},
            "confidence": 0.95,
            "response": "Manager response"
        }
        
        chat_orchestrator.manager_integration.process_result.return_value = "Final response"
        
        # Execute
        response = await chat_orchestrator.handle_chat(request)
        
        # Verify
        assert isinstance(response, (ChatResponseV1, ChatResponseV2))
        assert response.success
        assert response.session_id == "test-123"
        assert response.quality_score == 0.9
    
    @pytest.mark.asyncio
    async def test_handle_chat_v2_with_features(self, chat_orchestrator):
        """Test V2 chat request with enhanced features"""
        request = ChatRequestV2(
            message="Test message",
            session_id="test-456",
            optimization_mode="quality",
            swarm_type="coding-debate",
            use_memory=True
        )
        
        # Mock responses
        mock_result = Mock()
        mock_result.success = True
        mock_result.response = {"data": "response"}
        mock_result.execution_mode = Mock(value="quality")
        mock_result.quality_score = 0.95
        mock_result.execution_time = 1.2
        mock_result.error = None
        mock_result.metadata = {"swarm": "coding-debate"}
        
        chat_orchestrator.command_dispatcher.process_command.return_value = mock_result
        
        chat_orchestrator.manager_integration.process_message.return_value = {
            "intent": "code_generation",
            "parameters": {"language": "python"},
            "confidence": 0.92,
            "response": "I'll help you with that code"
        }
        
        chat_orchestrator.manager_integration.process_result.return_value = "Code generated successfully"
        
        # Execute
        response = await chat_orchestrator.handle_chat(request)
        
        # Verify V2-specific fields
        assert isinstance(response, ChatResponseV2)
        assert response.manager_response == "Code generated successfully"
        assert response.intent == "code_generation"
        assert response.confidence == 0.92
    
    @pytest.mark.asyncio
    async def test_handle_chat_error(self, chat_orchestrator):
        """Test chat request error handling"""
        request = ChatRequestV1(
            message="Error message",
            session_id="test-error"
        )
        
        # Mock error
        chat_orchestrator.command_dispatcher.process_command.side_effect = Exception("Test error")
        
        # Execute
        response = await chat_orchestrator.handle_chat(request)
        
        # Verify error response
        assert not response.success
        assert response.error == "Test error"
        assert response.quality_score == 0.0
    
    @pytest.mark.asyncio
    async def test_websocket_connection_limit(self, chat_orchestrator, mock_websocket):
        """Test WebSocket connection pool limits"""
        # Mock connection pool
        mock_pool = Mock()
        mock_pool.acquire_connection = AsyncMock(return_value=False)
        chat_orchestrator.connection_pool = mock_pool
        
        # Try to connect when pool is full
        await chat_orchestrator.websocket_endpoint(
            mock_websocket,
            "client-1",
            "session-1"
        )
        
        # Verify rejection
        mock_websocket.accept.assert_called_once()
        mock_websocket.send_json.assert_called_with({
            "type": "error",
            "error": "Connection limit reached. Please try again later."
        })
        mock_websocket.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stream_tokens(self, chat_orchestrator):
        """Test token streaming"""
        # Mock command dispatcher result
        mock_result = Mock()
        mock_result.success = True
        mock_result.response = {"message": "Hello world"}
        mock_result.execution_mode = Mock(value="balanced")
        mock_result.quality_score = 0.8
        mock_result.execution_time = 0.3
        mock_result.error = None
        
        chat_orchestrator.command_dispatcher.process_command.return_value = mock_result
        
        # Collect streamed tokens
        tokens = []
        async for token in chat_orchestrator.stream_tokens(
            message="Test",
            session_id="test-stream",
            user_context={}
        ):
            tokens.append(token)
        
        # Verify tokens
        assert len(tokens) > 0
        assert any(t.type == "token" for t in tokens)
        assert any(t.type == "complete" for t in tokens)
    
    def test_calculate_health(self, chat_orchestrator):
        """Test health calculation"""
        chat_orchestrator.metrics = {
            "total_messages": 100,
            "errors": 5
        }
        
        health = chat_orchestrator._calculate_health()
        assert health == 0.95
    
    def test_get_component_status(self, chat_orchestrator):
        """Test component status checking"""
        status = chat_orchestrator._get_component_status()
        
        assert "dispatcher" in status
        assert "orchestrator" in status
        assert "manager" in status

# ==================== Circuit Breaker Tests ====================

class TestCircuitBreaker:
    """Test CircuitBreaker functionality"""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state"""
        cb = CircuitBreaker("test", failure_threshold=3, timeout_seconds=1)
        
        # Successful call
        async def success_func():
            return "success"
        
        result = await cb.call(success_func)
        assert result == "success"
        assert cb.state == "CLOSED"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after threshold failures"""
        cb = CircuitBreaker("test", failure_threshold=2, timeout_seconds=1)
        
        # Failing function
        async def fail_func():
            raise Exception("Test failure")
        
        # First failure
        with pytest.raises(Exception):
            await cb.call(fail_func)
        assert cb.state == "CLOSED"
        
        # Second failure - should open
        with pytest.raises(Exception):
            await cb.call(fail_func)
        assert cb.state == "OPEN"
        
        # Should reject calls when open
        with pytest.raises(Exception, match="Circuit breaker test is OPEN"):
            await cb.call(fail_func)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery through half-open state"""
        cb = CircuitBreaker("test", failure_threshold=1, timeout_seconds=0.1)
        
        # Open the circuit
        async def fail_func():
            raise Exception("Fail")
        
        with pytest.raises(Exception):
            await cb.call(fail_func)
        assert cb.state == "OPEN"
        
        # Wait for timeout
        await asyncio.sleep(0.15)
        
        # Should enter half-open
        async def success_func():
            return "recovered"
        
        result = await cb.call(success_func)
        assert result == "recovered"
        assert cb.state == "CLOSED"

# ==================== WebSocket Error Boundary Tests ====================

class TestWebSocketErrorBoundary:
    """Test WebSocketErrorBoundary functionality"""
    
    @pytest.mark.asyncio
    async def test_error_boundary_catches_exceptions(self, connection_state):
        """Test error boundary catches and handles exceptions"""
        boundary = WebSocketErrorBoundary(connection_state, "Test error occurred")
        
        # Use error boundary
        async with boundary:
            raise ValueError("Test exception")
        
        # Verify error was sent
        connection_state.websocket.send_json.assert_called_once()
        call_args = connection_state.websocket.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["error"] == "Test error occurred"
    
    @pytest.mark.asyncio
    async def test_error_boundary_success_case(self, connection_state):
        """Test error boundary with successful execution"""
        boundary = WebSocketErrorBoundary(connection_state)
        
        async with boundary:
            pass  # No exception
        
        # Should not send error
        connection_state.websocket.send_json.assert_not_called()

# ==================== Connection Timeout Manager Tests ====================

class TestConnectionTimeoutManager:
    """Test ConnectionTimeoutManager functionality"""
    
    @pytest.mark.asyncio
    async def test_timeout_manager_cleanup(self, connection_state):
        """Test connection timeout and cleanup"""
        manager = ConnectionTimeoutManager(
            idle_timeout_seconds=0.1,
            check_interval_seconds=0.05
        )
        
        # Set last activity in the past
        connection_state.last_activity = datetime.utcnow()
        
        # Add connection
        manager.add_connection("test-key", connection_state)
        assert "test-key" in manager.connections
        
        # Wait for cleanup
        await asyncio.sleep(0.2)
        
        # Connection should be removed
        assert "test-key" not in manager.connections
    
    @pytest.mark.asyncio
    async def test_timeout_manager_ping(self, connection_state):
        """Test timeout manager sends pings"""
        manager = ConnectionTimeoutManager(
            idle_timeout_seconds=0.2,
            check_interval_seconds=0.05
        )
        
        manager.add_connection("test-key", connection_state)
        
        # Wait for half timeout (should trigger ping)
        await asyncio.sleep(0.15)
        
        # Should have sent ping
        connection_state.websocket.send_json.assert_called()
        call_args = connection_state.websocket.send_json.call_args[0][0]
        assert call_args["type"] == "ping"

# ==================== Integration Tests ====================

class TestIntegration:
    """Integration tests for complete flows"""
    
    @pytest.mark.asyncio
    async def test_full_chat_flow_with_manager(self, chat_orchestrator):
        """Test complete chat flow with manager integration"""
        request = ChatRequestV2(
            message="Write a Python function",
            session_id="integration-test",
            optimization_mode="balanced"
        )
        
        # Setup mocks for full flow
        chat_orchestrator.manager_integration.process_message.return_value = {
            "intent": "code_generation",
            "parameters": {"language": "python"},
            "confidence": 0.9,
            "response": "I'll write that function for you"
        }
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.response = "def example(): pass"
        mock_result.execution_mode = Mock(value="balanced")
        mock_result.quality_score = 0.85
        mock_result.execution_time = 0.7
        mock_result.error = None
        mock_result.metadata = {}
        
        chat_orchestrator.command_dispatcher.process_command.return_value = mock_result
        chat_orchestrator.manager_integration.process_result.return_value = "Function created successfully"
        
        # Execute
        response = await chat_orchestrator.handle_chat(request)
        
        # Verify complete flow
        assert response.success
        assert response.intent == "code_generation"
        assert response.manager_response == "Function created successfully"
        chat_orchestrator.command_dispatcher.process_command.assert_called_once()
        chat_orchestrator.manager_integration.process_message.assert_called_once()
        chat_orchestrator.manager_integration.process_result.assert_called_once()

# ==================== Run Tests ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])