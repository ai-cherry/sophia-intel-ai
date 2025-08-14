"""
Comprehensive tests for Slack MCP Server
Tests the reference implementation including Swarm integration
"""
import pytest
import asyncio
import json
import os
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
import tempfile
from pathlib import Path

# Set test environment
os.environ["USE_SWARM"] = "1"
os.environ["SWARM_HANDOFFS_LOG"] = "test_handoffs.log"
os.environ["MCP_API_KEYS"] = "test_key:admin,swarm_key:swarm"

from mcp.saas.slack.slack_server import SlackMCPServer, app

class TestSlackMCPServer:
    """Test suite for Slack MCP Server"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Authentication headers for tests"""
        return {"Authorization": "Bearer test_key"}
    
    @pytest.fixture
    def swarm_headers(self):
        """Swarm authentication headers"""
        return {"Authorization": "Bearer swarm_key"}
    
    @pytest.fixture
    def cleanup_log(self):
        """Cleanup test log file after each test"""
        yield
        log_file = "test_handoffs.log"
        if os.path.exists(log_file):
            os.remove(log_file)
    
    def test_health_check(self, client):
        """Test basic health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "Slack MCP Server"
        assert "version" in data
        assert "uptime" in data
    
    def test_readiness_check(self, client):
        """Test readiness check endpoint"""
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["service"] == "Slack MCP Server"
    
    def test_store_context_success(self, client, auth_headers):
        """Test successful context storage"""
        context_data = {
            "session_id": "test_session_123",
            "content": "This is a test Slack conversation about project planning",
            "metadata": {"priority": "high", "team": "engineering"},
            "context_type": "conversation",
            "swarm_stage": "architect",
            "workspace_id": "WORKSPACE123",
            "channel_id": "C1234567890",
            "thread_ts": "1234567890.123456",
            "user_id": "U1234567890"
        }
        
        response = client.post(
            "/slack/context",
            json=context_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "id" in data
        assert data["id"].startswith("slack_WORKSPACE123_test_session_123_")
        assert "timestamp" in data
    
    def test_store_context_missing_fields(self, client, auth_headers):
        """Test context storage with missing required fields"""
        context_data = {
            "content": "Missing required fields"
        }
        
        response = client.post(
            "/slack/context",
            json=context_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_store_context_unauthorized(self, client):
        """Test context storage without authentication"""
        context_data = {
            "session_id": "test_session_123",
            "content": "Test content",
            "workspace_id": "WORKSPACE123"
        }
        
        response = client.post("/slack/context", json=context_data)
        assert response.status_code == 401
    
    def test_search_context_success(self, client, auth_headers):
        """Test successful context search"""
        # First store some context
        context_data = {
            "session_id": "search_test_session",
            "content": "Discussion about machine learning algorithms and neural networks",
            "workspace_id": "WORKSPACE123",
            "channel_id": "C1234567890",
            "context_type": "technical_discussion"
        }
        
        store_response = client.post(
            "/slack/context",
            json=context_data,
            headers=auth_headers
        )
        assert store_response.status_code == 200
        
        # Now search for it
        search_data = {
            "query": "machine learning",
            "limit": 10,
            "workspace_id": "WORKSPACE123"
        }
        
        response = client.post(
            "/slack/search",
            json=search_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert data["query"] == "machine learning"
        assert len(data["results"]) >= 1
        
        # Check result structure
        result = data["results"][0]
        assert "id" in result
        assert "content" in result
        assert "workspace_id" in result
        assert "score" in result
    
    def test_search_context_with_filters(self, client, auth_headers):
        """Test context search with various filters"""
        search_data = {
            "query": "project planning",
            "limit": 5,
            "workspace_id": "WORKSPACE123",
            "channel_id": "C1234567890",
            "session_id": "specific_session"
        }
        
        response = client.post(
            "/slack/search",
            json=search_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "project planning"
        assert data["count"] >= 0
    
    @patch('mcp.saas.slack.slack_server.SlackMCPServer.slack_client')
    def test_send_swarm_message_success(self, mock_slack_client, client, swarm_headers, cleanup_log):
        """Test successful Swarm message sending to Slack"""
        # Mock Slack API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ok": True,
            "ts": "1234567890.123456",
            "permalink": "https://workspace.slack.com/archives/C1234567890/p1234567890123456"
        }
        mock_slack_client.post = AsyncMock(return_value=mock_response)
        
        message_data = {
            "channel": "C1234567890",
            "text": "Hello from the architect stage! The system analysis is complete.",
            "swarm_stage": "architect",
            "session_id": "swarm_test_session",
            "thread_ts": "1234567890.000000"
        }
        
        response = client.post(
            "/slack/swarm/message",
            json=message_data,
            headers=swarm_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["ts"] == "1234567890.123456"
        assert data["channel"] == "C1234567890"
        assert "permalink" in data
        
        # Verify Slack API was called correctly
        mock_slack_client.post.assert_called_once_with(
            "chat.postMessage",
            json={
                "channel": "C1234567890",
                "text": "🤖 *[ARCHITECT]* Hello from the architect stage! The system analysis is complete.",
                "username": "Swarm Architect",
                "icon_emoji": ":building_construction:",
                "thread_ts": "1234567890.000000"
            }
        )
    
    @patch('mcp.saas.slack.slack_server.SlackMCPServer.slack_client')
    def test_send_swarm_message_slack_error(self, mock_slack_client, client, swarm_headers):
        """Test Swarm message sending with Slack API error"""
        # Mock Slack API error response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ok": False,
            "error": "channel_not_found"
        }
        mock_slack_client.post = AsyncMock(return_value=mock_response)
        
        message_data = {
            "channel": "INVALID_CHANNEL",
            "text": "Test message",
            "swarm_stage": "builder",
            "session_id": "test_session"
        }
        
        response = client.post(
            "/slack/swarm/message",
            json=message_data,
            headers=swarm_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_send_swarm_message_no_slack_client(self, client, swarm_headers):
        """Test Swarm message sending when Slack client is not configured"""
        message_data = {
            "channel": "C1234567890",
            "text": "Test message",
            "swarm_stage": "tester",
            "session_id": "test_session"
        }
        
        response = client.post(
            "/slack/swarm/message",
            json=message_data,
            headers=swarm_headers
        )
        
        assert response.status_code == 503
        data = response.json()
        assert "not configured" in data["error"]
    
    @patch('mcp.saas.slack.slack_server.SlackMCPServer.slack_client')
    def test_extract_conversation_context(self, mock_slack_client, client, swarm_headers, cleanup_log):
        """Test conversation context extraction for Swarm"""
        # Mock Slack conversation history
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ok": True,
            "messages": [
                {
                    "user": "U1234567890",
                    "text": "We need to implement the new feature",
                    "ts": "1234567890.123456"
                },
                {
                    "user": "U0987654321",
                    "text": "I agree, let's start with the API design",
                    "ts": "1234567891.123456"
                },
                {
                    "user": "U1234567890",
                    "text": "Task: Create API documentation by Friday",
                    "ts": "1234567892.123456"
                }
            ]
        }
        mock_slack_client.get = AsyncMock(return_value=mock_response)
        
        request_data = {
            "channel_id": "C1234567890",
            "thread_ts": "1234567890.123456",
            "session_id": "context_extraction_test",
            "swarm_stage": "architect",
            "workspace_id": "WORKSPACE123"
        }
        
        response = client.post(
            "/slack/swarm/extract-context",
            json=request_data,
            headers=swarm_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check extracted context structure
        assert "conversation_summary" in data
        assert "key_decisions" in data
        assert "action_items" in data
        assert "participants" in data
        assert "entities" in data
        assert "sentiment" in data
        assert data["channel_id"] == "C1234567890"
        assert data["message_count"] == 3
        
        # Verify action items extraction
        assert len(data["action_items"]) >= 1
        assert any("Task" in item for item in data["action_items"])
        
        # Verify participants extraction
        assert len(data["participants"]) == 2
        assert "U1234567890" in data["participants"]
        assert "U0987654321" in data["participants"]
    
    def test_extract_conversation_context_missing_channel(self, client, swarm_headers):
        """Test conversation context extraction with missing channel_id"""
        request_data = {
            "session_id": "test_session",
            "swarm_stage": "architect"
        }
        
        response = client.post(
            "/slack/swarm/extract-context",
            json=request_data,
            headers=swarm_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "channel_id is required" in data["error"]
    
    @patch('mcp.saas.slack.slack_server.SlackMCPServer.slack_client')
    def test_get_channel_history(self, mock_slack_client, client, auth_headers):
        """Test channel history retrieval"""
        # Mock Slack API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ok": True,
            "messages": [
                {"user": "U1234", "text": "Hello", "ts": "1234567890.123456"},
                {"user": "U5678", "text": "Hi there", "ts": "1234567891.123456"}
            ],
            "has_more": False
        }
        mock_slack_client.get = AsyncMock(return_value=mock_response)
        
        response = client.get(
            "/slack/channels/C1234567890/history?limit=50",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 2
        assert data["has_more"] is False
        assert "next_cursor" in data
    
    def test_list_workspaces(self, client, auth_headers):
        """Test workspace listing"""
        response = client.get("/slack/workspaces/list", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "workspaces" in data
        assert len(data["workspaces"]) >= 1
        
        workspace = data["workspaces"][0]
        assert "id" in workspace
        assert "name" in workspace
        assert "configured" in workspace
    
    def test_slack_event_url_verification(self, client):
        """Test Slack URL verification challenge"""
        event_data = {
            "type": "url_verification",
            "challenge": "test_challenge_code"
        }
        
        response = client.post("/slack/events", json=event_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["challenge"] == "test_challenge_code"
    
    def test_slack_event_message(self, client):
        """Test Slack message event handling"""
        event_data = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "user": "U1234567890",
                "text": "Hello world",
                "channel": "C1234567890",
                "ts": "1234567890.123456"
            }
        }
        
        response = client.post("/slack/events", json=event_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_swarm_handoff_integration(self, client, cleanup_log):
        """Test Swarm handoff endpoint integration"""
        handoff_data = {
            "session_id": "handoff_test_session",
            "from_stage": "architect",
            "to_stage": "builder",
            "artifact": "System design completed with 5 microservices identified. Database schema defined with user, project, and task tables. API endpoints documented for CRUD operations.",
            "metadata": {
                "service": "slack",
                "channel_id": "C1234567890"
            }
        }
        
        response = client.post("/swarm/handoff", json=handoff_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["session_id"] == "handoff_test_session"
        assert data["from_stage"] == "architect"
        assert data["to_stage"] == "builder"
    
    def test_swarm_status_tracking(self, client, cleanup_log):
        """Test Swarm status tracking"""
        # First create a handoff
        handoff_data = {
            "session_id": "status_test_session",
            "from_stage": "builder",
            "to_stage": "tester",
            "artifact": "Implementation completed with unit tests",
            "metadata": {"service": "slack"}
        }
        
        client.post("/swarm/handoff", json=handoff_data)
        
        # Now check status
        response = client.get("/swarm/status/status_test_session")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert data["session_id"] == "status_test_session"
        assert data["current_stage"] == "tester"
        assert data["hop_count"] == 1
        assert "start_time" in data
        assert "elapsed_seconds" in data
    
    def test_swarm_telemetry_history(self, client, cleanup_log):
        """Test Swarm telemetry history retrieval"""
        # Generate some telemetry data
        handoff_data = {
            "session_id": "telemetry_test_session",
            "from_stage": "architect",
            "to_stage": "builder", 
            "artifact": "Design completed",
            "metadata": {"service": "slack"}
        }
        
        client.post("/swarm/handoff", json=handoff_data)
        
        # Get telemetry history
        response = client.get("/swarm/telemetry/telemetry_test_session?limit=50")
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "telemetry_test_session"
        assert data["count"] >= 1
        assert len(data["entries"]) >= 1
        
        # Check telemetry entry structure
        entry = data["entries"][0]
        assert "timestamp" in entry
        assert "type" in entry
    
    def test_authentication_invalid_key(self, client):
        """Test authentication with invalid API key"""
        headers = {"Authorization": "Bearer invalid_key"}
        
        response = client.post(
            "/slack/context",
            json={
                "session_id": "test",
                "content": "test",
                "workspace_id": "test"
            },
            headers=headers
        )
        
        assert response.status_code == 401
    
    def test_authentication_missing_header(self, client):
        """Test authentication with missing header"""
        response = client.post(
            "/slack/context",
            json={
                "session_id": "test",
                "content": "test", 
                "workspace_id": "test"
            }
        )
        
        assert response.status_code == 401
    
    def test_stage_emoji_mapping(self):
        """Test Swarm stage emoji mapping"""
        server = SlackMCPServer()
        
        assert server._get_stage_emoji("architect") == ":building_construction:"
        assert server._get_stage_emoji("builder") == ":hammer_and_wrench:"
        assert server._get_stage_emoji("tester") == ":mag:"
        assert server._get_stage_emoji("operator") == ":rocket:"
        assert server._get_stage_emoji("unknown") == ":robot_face:"
    
    def test_entity_extraction(self):
        """Test entity extraction from text"""
        server = SlackMCPServer()
        
        text = "We need to discuss @john and #project-alpha with the engineering team"
        entities = asyncio.run(server._extract_entities(text))
        
        assert "@john" in entities
        assert "#project-alpha" in entities
        assert "engineering" in entities
    
    def test_sentiment_analysis(self):
        """Test conversation sentiment analysis"""
        server = SlackMCPServer()
        
        positive_messages = [
            {"text": "This is great work! Excellent progress."},
            {"text": "I'm happy with the results."}
        ]
        
        negative_messages = [
            {"text": "This is a terrible problem we have."},
            {"text": "Bad news about the project issues."}
        ]
        
        neutral_messages = [
            {"text": "The meeting is at 3 PM."},
            {"text": "Please review the document."}
        ]
        
        assert asyncio.run(server._analyze_sentiment(positive_messages)) == "positive"
        assert asyncio.run(server._analyze_sentiment(negative_messages)) == "negative" 
        assert asyncio.run(server._analyze_sentiment(neutral_messages)) == "neutral"
        assert asyncio.run(server._analyze_sentiment([])) == "neutral"


if __name__ == "__main__":
    pytest.main([__file__])