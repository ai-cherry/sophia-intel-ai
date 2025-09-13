"""
Test WebSocket token envelope implementation for chat service
"""
import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from websockets.sync.client import connect as ws_connect
@pytest.mark.asyncio
async def test_websocket_envelope_structure():
    """Test that WebSocket messages follow the envelope structure"""
    from services.chat_service import main as cs
    # Create mock connection manager
    manager = cs.ChatConnectionManager()
    # Mock Redis and DB
    with patch('services.chat_service.main.redis_client') as mock_redis, \
         patch('services.chat_service.main.db_pool') as mock_db:
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock(return_value=True)
        # Create a mock WebSocket
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()
        # Connect user
        user_id = "test_user_123"
        session = await manager.connect(mock_ws, user_id)
        # Verify session created message
        mock_ws.send_json.assert_called()
        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["type"] == "session_created"
        assert "data" in call_args
@pytest.mark.asyncio
async def test_correlation_id_tracking():
    """Test that correlation IDs are properly generated and tracked"""
    from services.chat_service import main as cs
    manager = cs.ChatConnectionManager()
    # Mock components
    with patch('services.chat_service.main.redis_client') as mock_redis, \
         patch('services.chat_service.main.db_pool') as mock_db, \
         patch('services.chat_service.main.http_client') as mock_http:
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock(return_value=True)
        # Mock neural engine response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_text = AsyncMock()
        mock_response.iter_text.return_value.__aiter__.return_value = [
            'data: {"chunk": "Hello"}\n\n',
            'data: {"chunk": " world"}\n\n',
            'data: [DONE]\n\n'
        ]
        mock_http.stream = AsyncMock(return_value=mock_response)
        # Setup WebSocket
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        user_id = "test_user"
        manager.active_connections[user_id] = mock_ws
        manager.user_sessions[user_id] = "session_123"
        # Create session
        session = cs.ChatSession(id="session_123", user_id=user_id)
        # Process streaming response
        correlation_id = str(uuid.uuid4())
        await manager.process_streaming_response(
            user_id, session, "http://test", {"stream": True}, correlation_id
        )
        # Verify correlation_id in messages
        calls = mock_ws.send_json.call_args_list
        for call in calls:
            message = call[0][0]
            if message["type"] in ["status", "token", "usage"]:
                assert message.get("correlation_id") == correlation_id
@pytest.mark.asyncio
async def test_sequence_numbering():
    """Test that sequence numbers increment properly"""
    from services.chat_service import main as cs
    manager = cs.ChatConnectionManager()
    with patch('services.chat_service.main.redis_client') as mock_redis:
        mock_redis.setex = AsyncMock(return_value=True)
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        user_id = "test_user"
        manager.active_connections[user_id] = mock_ws
        # Send multiple token envelopes
        correlation_id = str(uuid.uuid4())
        sequences = []
        for i, chunk in enumerate(["Hello", " ", "world", "!"]):
            await manager.send_to_user(
                user_id,
                {
                    "type": "token",
                    "correlation_id": correlation_id,
                    "data": {
                        "chunk": chunk,
                        "sequence": i,
                        "metadata": {"model": "test-model"}
                    }
                }
            )
            sequences.append(i)
        # Verify sequences are in order
        calls = mock_ws.send_json.call_args_list
        received_sequences = []
        for call in calls:
            message = call[0][0]
            if message["type"] == "token":
                received_sequences.append(message["data"]["sequence"])
        assert received_sequences == sequences
@pytest.mark.asyncio
async def test_replay_functionality():
    """Test stream replay from cache"""
    from services.chat_service import main as cs
    manager = cs.ChatConnectionManager()
    with patch('services.chat_service.main.redis_client') as mock_redis:
        # Setup cached stream
        correlation_id = str(uuid.uuid4())
        cached_data = {
            "full_response": "This is a cached response",
            "model": "test-model",
            "timestamp": "2024-01-01T00:00:00"
        }
        mock_redis.get = AsyncMock(return_value=json.dumps(cached_data))
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        user_id = "test_user"
        manager.active_connections[user_id] = mock_ws
        # Request replay
        # Simulate the replay logic from the WebSocket handler
        cached_str = await mock_redis.get(f"stream:{correlation_id}")
        assert cached_str is not None
        payload = json.loads(cached_str)
        text = payload.get("full_response", "")
        # Send replay envelope
        await manager.send_to_user(
            user_id,
            {
                "type": "token",
                "correlation_id": correlation_id,
                "data": {
                    "chunk": text,
                    "sequence": 0,
                    "metadata": {"model": payload.get("model")}
                }
            }
        )
        # Verify replay was sent
        mock_ws.send_json.assert_called()
        last_call = mock_ws.send_json.call_args[0][0]
        assert last_call["type"] == "token"
        assert last_call["correlation_id"] == correlation_id
        assert last_call["data"]["chunk"] == "This is a cached response"
@pytest.mark.asyncio
async def test_backward_compatibility():
    """Test that old message formats are still supported"""
    from services.chat_service import main as cs
    manager = cs.ChatConnectionManager()
    mock_ws = AsyncMock()
    mock_ws.send_json = AsyncMock()
    user_id = "test_user"
    manager.active_connections[user_id] = mock_ws
    # Send old-style agent_status message
    await manager.send_to_user(
        user_id,
        {"type": "agent_status", "data": {"status": "thinking"}}
    )
    # Send old-style stream_chunk message
    await manager.send_to_user(
        user_id,
        {"type": "stream_chunk", "data": {"chunk": "Hello world"}}
    )
    # Verify both formats were sent
    calls = mock_ws.send_json.call_args_list
    assert len(calls) == 2
    assert calls[0][0][0]["type"] == "agent_status"
    assert calls[1][0][0]["type"] == "stream_chunk"
@pytest.mark.asyncio
async def test_error_envelope():
    """Test error message envelope format"""
    from services.chat_service import main as cs
    manager = cs.ChatConnectionManager()
    mock_ws = AsyncMock()
    mock_ws.send_json = AsyncMock()
    user_id = "test_user"
    manager.active_connections[user_id] = mock_ws
    # Send error envelope
    correlation_id = str(uuid.uuid4())
    await manager.send_to_user(
        user_id,
        {
            "type": "error",
            "correlation_id": correlation_id,
            "data": {
                "message": "Neural engine unavailable",
                "code": "SERVICE_UNAVAILABLE",
                "retry_after": 30
            }
        }
    )
    # Verify error format
    mock_ws.send_json.assert_called_once()
    error_msg = mock_ws.send_json.call_args[0][0]
    assert error_msg["type"] == "error"
    assert error_msg["correlation_id"] == correlation_id
    assert "message" in error_msg["data"]
if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])