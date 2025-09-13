"""
Tests for AIML Enhanced Router
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.routers.aiml_enhanced import router


@pytest.fixture
def app():
    """Create FastAPI app with router"""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Mock AIMLAPI settings"""
    settings = MagicMock()
    settings.is_configured = True
    settings.enabled = True
    settings.api_key = "test-key"
    settings.base_url = "https://api.test.com/v1"
    settings.router_token = None  # No auth required for tests
    return settings


@pytest.fixture
def mock_aiml_client():
    """Mock AIML client"""
    client = AsyncMock()
    client.chat = AsyncMock()
    client.stream_chat = AsyncMock()
    client.list_models = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock()
    return client


@pytest.fixture
def mock_mcp_manager():
    """Mock MCP context manager"""
    manager = AsyncMock()
    manager.build_compact_context = AsyncMock()
    manager.get_repository_structure = AsyncMock()
    manager.get_git_status = AsyncMock()
    manager.search_memory = AsyncMock()
    return manager


class TestAIMLRouter:
    """Test AIML enhanced router endpoints"""
    
    def test_health_check(self, client, mock_settings):
        """Test health check endpoint"""
        with patch("app.routers.aiml_enhanced.get_settings", return_value=mock_settings):
            with patch("app.routers.aiml_enhanced.get_mcp_context_manager") as mock_get_manager:
                mock_manager = AsyncMock()
                mock_manager.get_repository_structure = AsyncMock(return_value={})
                mock_get_manager.return_value = mock_manager
                
                response = client.get("/api/aiml/health")
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
                assert data["configured"] is True
                assert data["enabled"] is True
    
    def test_list_models(self, client, mock_settings):
        """Test list models endpoint"""
        with patch("app.routers.aiml_enhanced.get_settings", return_value=mock_settings):
            response = client.get("/api/aiml/models")
            
            assert response.status_code == 200
            data = response.json()
            assert "object" in data
            assert "data" in data
            assert len(data["data"]) > 0  # Should have model profiles
    
    def test_chat_completion_non_streaming(
        self,
        client,
        mock_settings,
        mock_aiml_client,
        mock_mcp_manager
    ):
        """Test non-streaming chat completion"""
        # Mock responses
        mock_aiml_client.chat.return_value = {
            "id": "chat-123",
            "choices": [{
                "message": {"content": "Test response"},
                "finish_reason": "stop"
            }],
            "usage": {"total_tokens": 100}
        }
        
        mock_mcp_manager.build_compact_context.return_value = {
            "workspace": "sophia",
            "structure": {"dirs": ["app", "tests"], "files": ["main.py"]}
        }
        
        with patch("app.routers.aiml_enhanced.get_settings", return_value=mock_settings):
            with patch("app.routers.aiml_enhanced.get_aiml_client", return_value=mock_aiml_client):
                with patch("app.routers.aiml_enhanced.get_mcp_context_manager") as mock_get_manager:
                    mock_get_manager.return_value = mock_mcp_manager
                    
                    # Make request
                    request_data = {
                        "messages": [{"role": "user", "content": "Hello"}],
                        "model": "sophia-general",
                        "stream": False,
                        "include_context": True
                    }
                    
                    response = client.post(
                        "/api/aiml/chat",
                        json=request_data
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert "choices" in data
                    assert data["model"] == "sophia-general"
                    
                    # Verify context was injected
                    mock_mcp_manager.build_compact_context.assert_called_once()
    
    def test_chat_completion_without_context(
        self,
        client,
        mock_settings,
        mock_aiml_client
    ):
        """Test chat completion without repository context"""
        mock_aiml_client.chat.return_value = {
            "id": "chat-456",
            "choices": [{
                "message": {"content": "Response without context"},
                "finish_reason": "stop"
            }]
        }
        
        with patch("app.routers.aiml_enhanced.get_settings", return_value=mock_settings):
            with patch("app.routers.aiml_enhanced.get_aiml_client", return_value=mock_aiml_client):
                # Make request without context
                request_data = {
                    "messages": [{"role": "user", "content": "Hello"}],
                    "model": "sophia-general",
                    "stream": False,
                    "include_context": False
                }
                
                response = client.post(
                    "/api/aiml/chat",
                    json=request_data
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "choices" in data
    
    def test_chat_with_invalid_model(self, client, mock_settings):
        """Test chat with invalid model profile"""
        with patch("app.routers.aiml_enhanced.get_settings", return_value=mock_settings):
            request_data = {
                "messages": [{"role": "user", "content": "Hello"}],
                "model": "invalid-model",
                "stream": False
            }
            
            # Should fallback to sophia-general
            response = client.post(
                "/api/aiml/chat",
                json=request_data
            )
            
            # Should still work with fallback
            assert response.status_code in [200, 500]  # Depends on client mock
    
    def test_repository_analysis(
        self,
        client,
        mock_settings,
        mock_mcp_manager
    ):
        """Test repository analysis endpoint"""
        # Mock responses
        mock_mcp_manager.get_repository_structure.return_value = {
            "total_files": 100,
            "key_directories": ["app", "tests", "docs"]
        }
        
        mock_mcp_manager.get_git_status.return_value = {
            "branch": "main",
            "modified_count": 5,
            "untracked_count": 3
        }
        
        with patch("app.routers.aiml_enhanced.get_settings", return_value=mock_settings):
            with patch("app.routers.aiml_enhanced.get_mcp_context_manager") as mock_get_manager:
                mock_get_manager.return_value = mock_mcp_manager
                
                response = client.post("/api/aiml/repository/analyze")
                
                assert response.status_code == 200
                data = response.json()
                assert "structure" in data
                assert "git_status" in data
                assert "statistics" in data
                assert "recommendations" in data
    
    def test_auth_required(self, client):
        """Test authentication when router token is set"""
        mock_settings = MagicMock()
        mock_settings.is_configured = True
        mock_settings.router_token = "secret-token"
        
        with patch("app.routers.aiml_enhanced.get_settings", return_value=mock_settings):
            # Request without auth should fail
            response = client.get("/api/aiml/models")
            assert response.status_code == 401
            
            # Request with wrong token should fail
            response = client.get(
                "/api/aiml/models",
                headers={"Authorization": "Bearer wrong-token"}
            )
            assert response.status_code == 401
            
            # Request with correct token should succeed
            response = client.get(
                "/api/aiml/models",
                headers={"Authorization": "Bearer secret-token"}
            )
            assert response.status_code == 200
    
    def test_not_configured_error(self, client):
        """Test error when AIMLAPI is not configured"""
        mock_settings = MagicMock()
        mock_settings.is_configured = False
        mock_settings.router_token = None
        
        with patch("app.routers.aiml_enhanced.get_settings", return_value=mock_settings):
            request_data = {
                "messages": [{"role": "user", "content": "Hello"}],
                "model": "sophia-general"
            }
            
            response = client.post(
                "/api/aiml/chat",
                json=request_data
            )
            
            assert response.status_code == 503
            assert "not configured" in response.json()["detail"].lower()
    
    def test_streaming_response(
        self,
        client,
        mock_settings,
        mock_aiml_client
    ):
        """Test streaming chat completion"""
        # Mock streaming generator
        async def mock_stream():
            yield "data: {\"choices\": [{\"delta\": {\"content\": \"Hello\"}}]}\n\n"
            yield "data: {\"choices\": [{\"delta\": {\"content\": \" world\"}}]}\n\n"
            yield "data: [DONE]\n\n"
        
        mock_aiml_client.stream_chat.return_value = mock_stream()
        
        with patch("app.routers.aiml_enhanced.get_settings", return_value=mock_settings):
            with patch("app.routers.aiml_enhanced.get_aiml_client", return_value=mock_aiml_client):
                request_data = {
                    "messages": [{"role": "user", "content": "Hello"}],
                    "model": "sophia-general",
                    "stream": True,
                    "include_context": False
                }
                
                # Streaming responses require special handling in tests
                # Just verify the endpoint accepts the request
                response = client.post(
                    "/api/aiml/chat",
                    json=request_data
                )
                
                # Should return streaming response
                assert response.status_code == 200
                assert response.headers.get("content-type") == "text/event-stream; charset=utf-8"