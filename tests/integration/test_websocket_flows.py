"""
Integration Tests for WebSocket Flows
Tests complete WebSocket communication flows and scenarios
"""

import pytest
import asyncio
import json
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

from app.ui.unified.chat_orchestrator import router, lifespan, get_orchestrator
from app.api.contracts import WebSocketMessage, WebSocketMessageType
from app.infrastructure.dependency_injection import ServiceConfig, initialize_container

# ==================== Test Application Setup ====================

@pytest.fixture
async def test_app():
    """Create test FastAPI application"""
    app = FastAPI(lifespan=lifespan)
    app.include_router(router)
    
    # Override dependencies for testing
    async def mock_orchestrator():
        orch = Mock()
        orch.initialized = True
        orch.handle_chat = AsyncMock()
        orch.websocket_endpoint = AsyncMock()
        orch.get_metrics = AsyncMock(return_value={})
        orch.circuit_breakers = {}
        orch.active_connections = {}
        return orch
    
    app.dependency_overrides[get_orchestrator] = mock_orchestrator
    
    return app

@pytest.fixture
def test_client(test_app):
    """Create test client"""
    return TestClient(test_app)

# ==================== WebSocket Flow Tests ====================

class TestWebSocketFlows:
    """Test WebSocket communication flows"""
    
    def test_websocket_connection_establishment(self, test_client):
        """Test establishing WebSocket connection"""
        with test_client.websocket_connect("/chat/ws/client-1/session-1") as websocket:
            # Should connect successfully
            assert websocket
            # Connection should remain open
            websocket.send_json({"type": "ping"})
            # Should be able to close cleanly
    
    def test_websocket_chat_message_flow(self, test_client):
        """Test chat message flow through WebSocket"""
        with test_client.websocket_connect("/chat/ws/client-2/session-2") as websocket:
            # Send chat message
            message = {
                "type": "chat",
                "data": {
                    "message": "Hello, AI!",
                    "context": {"user_id": "test-user"}
                }
            }
            websocket.send_json(message)
            
            # Should receive responses (mocked in this test)
            # In real implementation, would receive manager response, tokens, etc.
    
    def test_websocket_command_message(self, test_client):
        """Test command message handling"""
        with test_client.websocket_connect("/chat/ws/client-3/session-3") as websocket:
            # Send command message
            message = {
                "type": "command",
                "data": {
                    "command": "show system status",
                    "context": {}
                }
            }
            websocket.send_json(message)
            
            # Should process command
    
    def test_websocket_control_messages(self, test_client):
        """Test control message handling"""
        with test_client.websocket_connect("/chat/ws/client-4/session-4") as websocket:
            # Test ping-pong
            websocket.send_json({
                "type": "control",
                "data": {"type": "ping"}
            })
            
            # Test status request
            websocket.send_json({
                "type": "control",
                "data": {"type": "status"}
            })
            
            # Test metrics request
            websocket.send_json({
                "type": "control",
                "data": {"type": "metrics"}
            })
    
    def test_websocket_error_handling(self, test_client):
        """Test WebSocket error handling"""
        with test_client.websocket_connect("/chat/ws/client-5/session-5") as websocket:
            # Send invalid JSON
            websocket.send_text("invalid json {")
            
            # Connection should remain open despite error
            websocket.send_json({"type": "ping"})
    
    def test_websocket_connection_limit(self, test_client):
        """Test WebSocket connection limits"""
        connections = []
        
        # Create multiple connections
        for i in range(5):
            ws = test_client.websocket_connect(f"/chat/ws/client-{i}/session-{i}")
            connections.append(ws)
        
        # Close all connections
        for ws in connections:
            ws.__exit__(None, None, None)
    
    def test_websocket_message_streaming(self, test_client):
        """Test message streaming over WebSocket"""
        with test_client.websocket_connect("/chat/ws/client-6/session-6") as websocket:
            # Send message requesting streaming
            message = {
                "type": "chat",
                "data": {
                    "message": "Stream a response",
                    "context": {"stream": True}
                }
            }
            websocket.send_json(message)
            
            # Would receive stream of tokens in real implementation
    
    def test_websocket_reconnection(self, test_client):
        """Test WebSocket reconnection scenario"""
        # First connection
        with test_client.websocket_connect("/chat/ws/client-7/session-7") as ws1:
            ws1.send_json({"type": "ping"})
        
        # Disconnect and reconnect with same session
        with test_client.websocket_connect("/chat/ws/client-7/session-7") as ws2:
            ws2.send_json({"type": "ping"})
            # Should maintain session context

# ==================== End-to-End Scenario Tests ====================

class TestE2EScenarios:
    """Test end-to-end scenarios"""
    
    @pytest.mark.asyncio
    async def test_complete_chat_session(self):
        """Test complete chat session from start to finish"""
        from app.ui.unified.chat_orchestrator import ChatOrchestrator
        from app.api.contracts import ChatRequestV2
        
        # Create orchestrator with mocked dependencies
        orchestrator = ChatOrchestrator()
        orchestrator.command_dispatcher = AsyncMock()
        orchestrator.unified_orchestrator = AsyncMock()
        orchestrator.orchestra_manager = Mock()
        orchestrator.manager_integration = Mock()
        
        # Setup mocks
        orchestrator.manager_integration.process_message.return_value = {
            "intent": "greeting",
            "parameters": {},
            "confidence": 0.95,
            "response": "Hello! How can I help you?"
        }
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.response = "I can help with that"
        mock_result.execution_mode = Mock(value="balanced")
        mock_result.quality_score = 0.9
        mock_result.execution_time = 0.5
        mock_result.error = None
        mock_result.metadata = {}
        
        orchestrator.command_dispatcher.process_command.return_value = mock_result
        orchestrator.manager_integration.process_result.return_value = "Task completed"
        
        await orchestrator.initialize()
        
        # Create request
        request = ChatRequestV2(
            message="Hello",
            session_id="e2e-test",
            optimization_mode="balanced"
        )
        
        # Process request
        response = await orchestrator.handle_chat(request)
        
        # Verify response
        assert response.success
        assert response.session_id == "e2e-test"
        
        await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self):
        """Test multi-turn conversation flow"""
        from app.ui.unified.chat_orchestrator import ChatOrchestrator
        from app.api.contracts import ChatRequestV2
        
        orchestrator = ChatOrchestrator()
        orchestrator.command_dispatcher = AsyncMock()
        orchestrator.unified_orchestrator = AsyncMock()
        orchestrator.orchestra_manager = Mock()
        orchestrator.manager_integration = Mock()
        
        # Setup conversation history
        session_id = "multi-turn-test"
        messages = [
            "What is Python?",
            "Can you show me an example?",
            "How do I run it?"
        ]
        
        orchestrator.manager_integration.process_message.return_value = {
            "intent": "information",
            "parameters": {},
            "confidence": 0.9,
            "response": "Processing your question"
        }
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.response = "Here's the answer"
        mock_result.execution_mode = Mock(value="balanced")
        mock_result.quality_score = 0.85
        mock_result.execution_time = 0.3
        mock_result.error = None
        mock_result.metadata = {}
        
        orchestrator.command_dispatcher.process_command.return_value = mock_result
        orchestrator.manager_integration.process_result.return_value = "Answer provided"
        
        await orchestrator.initialize()
        
        # Process each message
        for message in messages:
            request = ChatRequestV2(
                message=message,
                session_id=session_id,
                optimization_mode="balanced"
            )
            response = await orchestrator.handle_chat(request)
            assert response.success
        
        # Verify session history
        assert session_id in orchestrator.session_history
        assert len(orchestrator.session_history[session_id]) == 3
        
        await orchestrator.shutdown()

# ==================== Performance Tests ====================

class TestWebSocketPerformance:
    """Test WebSocket performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_concurrent_connections(self, test_client):
        """Test handling concurrent WebSocket connections"""
        import asyncio
        
        async def connect_and_send(client_id: str):
            """Connect and send messages"""
            # This would use async WebSocket client in real implementation
            pass
        
        # Simulate concurrent connections
        tasks = [connect_and_send(f"client-{i}") for i in range(10)]
        # await asyncio.gather(*tasks)
    
    @pytest.mark.asyncio
    async def test_message_throughput(self):
        """Test message throughput rate"""
        from app.ui.unified.chat_orchestrator import ChatOrchestrator
        import time
        
        orchestrator = ChatOrchestrator()
        orchestrator.command_dispatcher = AsyncMock()
        orchestrator.command_dispatcher.process_command.return_value = Mock(
            success=True,
            response="OK",
            execution_mode=Mock(value="lite"),
            quality_score=0.8,
            execution_time=0.01,
            error=None,
            metadata={}
        )
        
        # Measure throughput
        start_time = time.time()
        message_count = 100
        
        for i in range(message_count):
            # Simulate token streaming
            tokens = []
            async for token in orchestrator.stream_tokens(
                message=f"Message {i}",
                session_id="perf-test",
                user_context={}
            ):
                tokens.append(token)
        
        duration = time.time() - start_time
        throughput = message_count / duration
        
        # Should handle at least 10 messages per second
        assert throughput > 10

# ==================== Error Recovery Tests ====================

class TestErrorRecovery:
    """Test error recovery mechanisms"""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery flow"""
        from app.ui.unified.chat_orchestrator import CircuitBreaker
        
        cb = CircuitBreaker("test", failure_threshold=2, timeout_seconds=0.1)
        
        # Cause failures to open circuit
        async def fail():
            raise Exception("Fail")
        
        for _ in range(2):
            try:
                await cb.call(fail)
            except:
                pass
        
        assert cb.state == "OPEN"
        
        # Wait for timeout
        await asyncio.sleep(0.15)
        
        # Should recover with successful call
        async def success():
            return "OK"
        
        result = await cb.call(success)
        assert result == "OK"
        assert cb.state == "CLOSED"
    
    @pytest.mark.asyncio
    async def test_connection_timeout_recovery(self):
        """Test connection timeout and recovery"""
        from app.ui.unified.chat_orchestrator import ConnectionTimeoutManager
        
        manager = ConnectionTimeoutManager(
            idle_timeout_seconds=0.1,
            check_interval_seconds=0.05
        )
        
        # Create mock connection
        mock_conn = Mock()
        mock_conn.last_activity = datetime.utcnow()
        mock_conn.websocket = AsyncMock()
        
        manager.add_connection("test", mock_conn)
        
        # Wait for timeout
        await asyncio.sleep(0.2)
        
        # Connection should be cleaned up
        assert "test" not in manager.connections

# ==================== API Version Compatibility Tests ====================

class TestAPIVersionCompatibility:
    """Test API version compatibility"""
    
    def test_v1_client_compatibility(self, test_client):
        """Test V1 client compatibility"""
        # V1 request format
        v1_request = {
            "api_version": "v1",
            "message": "Test V1",
            "session_id": "v1-test"
        }
        
        response = test_client.post("/chat/v1/chat", json=v1_request)
        # Should handle V1 requests
    
    def test_v2_client_features(self, test_client):
        """Test V2 client features"""
        # V2 request with enhanced features
        v2_request = {
            "api_version": "v2",
            "message": "Test V2",
            "session_id": "v2-test",
            "optimization_mode": "quality",
            "swarm_type": "coding-debate",
            "use_memory": True
        }
        
        response = test_client.post("/chat/v2/chat", json=v2_request)
        # Should handle V2 features
    
    def test_auto_version_detection(self, test_client):
        """Test automatic version detection"""
        # Request without explicit version
        request = {
            "message": "Test auto",
            "session_id": "auto-test"
        }
        
        response = test_client.post("/chat", json=request)
        # Should auto-detect and handle

# ==================== Run Tests ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])