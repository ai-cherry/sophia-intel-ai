"""
Slack Integration Test Fixtures and Configuration
"""
import asyncio
import hmac
import hashlib
import json
import os
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import fakeredis.aioredis as fake_aioredis
from fastapi.testclient import TestClient
from httpx import AsyncClient
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.socket_mode.aiohttp import SocketModeClient

# Mock FastAPI app for testing (avoids import issues)
from fastapi import FastAPI
app = FastAPI()

from app.integrations.slack_optimized_client import SlackOptimizedClient
# Mock the Slack intelligence import to avoid dependencies
from unittest.mock import AsyncMock

class MockSophiaSlackIntelligence:
    async def handle_slack_command(self, *args, **kwargs):
        return "Mock response"
    
    async def check_business_intelligence(self, *args, **kwargs):
        return []
    
    async def send_slack_alerts(self, *args, **kwargs):
        return {"sent": 1, "failed": 0}

SophiaSlackIntelligence = MockSophiaSlackIntelligence


@pytest.fixture
def slack_signing_secret():
    """Test Slack signing secret"""
    return "test_signing_secret_12345"


@pytest.fixture
def slack_bot_token():
    """Test Slack bot token"""
    return "xoxb-test-bot-token-12345"


@pytest.fixture
def slack_app_token():
    """Test Slack app token"""
    return "xapp-test-app-token-12345"


@pytest.fixture
def slack_user_token():
    """Test Slack user token"""
    return "xoxp-test-user-token-12345"


@pytest.fixture
def test_env_vars(slack_signing_secret, slack_bot_token, slack_app_token, slack_user_token):
    """Set up test environment variables"""
    env_vars = {
        "SLACK_SIGNING_SECRET": slack_signing_secret,
        "SLACK_BOT_TOKEN": slack_bot_token,
        "SLACK_APP_TOKEN": slack_app_token,
        "SLACK_USER_TOKEN": slack_user_token,
        "REDIS_URL": "redis://localhost:6379/1",  # Test DB
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def fake_redis():
    """Fake Redis instance for testing"""
    return fake_aioredis.FakeRedis(decode_responses=True)


class SlackSignatureHelper:
    """Helper for generating valid Slack signatures"""
    
    def __init__(self, signing_secret: str):
        self.signing_secret = signing_secret
    
    def generate_signature(self, body: str, timestamp: int) -> str:
        """Generate v0 signature for given body and timestamp"""
        basestring = f"v0:{timestamp}:{body}".encode()
        signature = hmac.new(
            self.signing_secret.encode(),
            basestring,
            hashlib.sha256
        ).hexdigest()
        return f"v0={signature}"
    
    def get_headers(self, body: str, timestamp: Optional[int] = None) -> Dict[str, str]:
        """Get complete headers for Slack request"""
        if timestamp is None:
            timestamp = int(datetime.now().timestamp())
        
        return {
            "X-Slack-Request-Timestamp": str(timestamp),
            "X-Slack-Signature": self.generate_signature(body, timestamp),
            "Content-Type": "application/json"
        }
    
    def get_form_headers(self, body: str, timestamp: Optional[int] = None) -> Dict[str, str]:
        """Get headers for form-encoded Slack request"""
        headers = self.get_headers(body, timestamp)
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        return headers


@pytest.fixture
def signature_helper(slack_signing_secret):
    """Slack signature helper instance"""
    return SlackSignatureHelper(slack_signing_secret)


class SlackEventBuilder:
    """Builder for Slack event payloads"""
    
    @staticmethod
    def url_verification(challenge: str = "test_challenge_123") -> Dict[str, Any]:
        """Build URL verification challenge"""
        return {
            "type": "url_verification",
            "token": "verification_token",
            "challenge": challenge
        }
    
    @staticmethod
    def app_mention(
        text: str = "<@U123456> hello",
        user: str = "U987654",
        channel: str = "C111111",
        ts: str = "1234567890.123456"
    ) -> Dict[str, Any]:
        """Build app mention event"""
        return {
            "type": "event_callback",
            "event": {
                "type": "app_mention",
                "text": text,
                "user": user,
                "channel": channel,
                "ts": ts,
                "event_ts": ts
            },
            "team_id": "T123456",
            "api_app_id": "A123456"
        }
    
    @staticmethod
    def message_event(
        text: str = "Hello Sophia",
        user: str = "U987654",
        channel: str = "D111111",  # DM channel
        ts: str = "1234567890.123456"
    ) -> Dict[str, Any]:
        """Build message event"""
        return {
            "type": "event_callback",
            "event": {
                "type": "message",
                "text": text,
                "user": user,
                "channel": channel,
                "ts": ts,
                "event_ts": ts
            },
            "team_id": "T123456",
            "api_app_id": "A123456"
        }
    
    @staticmethod
    def slash_command_form(
        command: str = "/sophia",
        text: str = "help",
        user_id: str = "U987654",
        channel_id: str = "C111111",
        response_url: str = "https://hooks.slack.com/commands/123/456"
    ) -> Dict[str, str]:
        """Build slash command form data"""
        return {
            "command": command,
            "text": text,
            "user_id": user_id,
            "channel_id": channel_id,
            "response_url": response_url,
            "trigger_id": "123456.789012.abcdef",
            "team_id": "T123456",
            "api_app_id": "A123456"
        }
    
    @staticmethod
    def interactive_button_payload(
        action_id: str = "approve_request",
        block_id: str = "actions_block",
        action_type: str = "button",
        value: str = "approve"
    ) -> Dict[str, Any]:
        """Build interactive button payload"""
        return {
            "type": "block_actions",
            "user": {"id": "U987654", "name": "testuser"},
            "api_app_id": "A123456",
            "team": {"id": "T123456"},
            "channel": {"id": "C111111", "name": "general"},
            "response_url": "https://hooks.slack.com/actions/123/456",
            "actions": [{
                "action_id": action_id,
                "block_id": block_id,
                "type": action_type,
                "value": value,
                "action_ts": "1234567890.123456"
            }]
        }
    
    @staticmethod
    def view_submission_payload(
        callback_id: str = "feedback_modal",
        values: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Build modal view submission payload"""
        if values is None:
            values = {
                "feedback_block": {
                    "feedback_input": {
                        "type": "plain_text_input",
                        "value": "Great feature!"
                    }
                }
            }
        
        return {
            "type": "view_submission",
            "user": {"id": "U987654", "name": "testuser"},
            "api_app_id": "A123456",
            "team": {"id": "T123456"},
            "view": {
                "id": "V123456",
                "callback_id": callback_id,
                "state": {"values": values},
                "title": {"type": "plain_text", "text": "Test Modal"}
            }
        }


@pytest.fixture
def event_builder():
    """Slack event builder instance"""
    return SlackEventBuilder()


class MockSlackClient:
    """Mock Slack client for testing"""
    
    def __init__(self):
        self.chat_postMessage = AsyncMock()
        self.views_open = AsyncMock()
        self.chat_update = AsyncMock()
        self.conversations_list = AsyncMock()
        self.conversations_history = AsyncMock()
        self.users_list = AsyncMock()
        self.search_messages = AsyncMock()
        
        # Set up default responses
        self.chat_postMessage.return_value = AsyncMock(
            data={"ok": True, "channel": "C111111", "ts": "1234567890.123456"}
        )
        self.conversations_list.return_value = AsyncMock(
            data={"ok": True, "channels": [
                {"id": "C111111", "name": "general", "is_private": False},
                {"id": "C222222", "name": "random", "is_private": False}
            ]}
        )
        self.users_list.return_value = AsyncMock(
            data={"ok": True, "members": [
                {"id": "U123456", "name": "sophia", "is_bot": True},
                {"id": "U987654", "name": "testuser", "is_bot": False}
            ]}
        )
        self.conversations_history.return_value = AsyncMock(
            data={"ok": True, "messages": [
                {
                    "text": "TODO: Fix the bug",
                    "user": "U987654",
                    "ts": "1234567890.123456",
                    "type": "message"
                }
            ]}
        )


@pytest.fixture
def mock_slack_client():
    """Mock Slack client instance"""
    return MockSlackClient()


@pytest.fixture
def mock_socket_client():
    """Mock Socket Mode client"""
    client = AsyncMock(spec=SocketModeClient)
    client.connect_async = AsyncMock()
    client.disconnect_async = AsyncMock()
    client.send_socket_mode_response = AsyncMock()
    client.socket_mode_request_listeners = []
    return client


@pytest.fixture
def mock_sophia_intelligence():
    """Mock Sophia Slack Intelligence"""
    intelligence = AsyncMock()
    intelligence.handle_slack_command.return_value = "Mock response from Sophia"
    intelligence.check_business_intelligence.return_value = []
    intelligence.send_slack_alerts.return_value = {"sent": 1, "failed": 0}
    
    # Create a mock object for the daily summary return value
    mock_summary = MagicMock()
    mock_summary.channel = "#general"
    mock_summary.message = "Daily summary"
    mock_summary.priority = "medium"
    mock_summary.data = {}
    intelligence.create_daily_business_summary.return_value = mock_summary
    
    intelligence.monitored_reports = {
        "revenue_dashboard": {
            "name": "Revenue Dashboard",
            "looker_id": "123",
            "views": 1000,
            "priority": "high",
            "check_frequency": "hourly",
            "channels": ["#finance"],
            "metrics": ["revenue", "conversion"],
            "thresholds": {"revenue": {"min": 50000}}
        }
    }
    return intelligence


@pytest.fixture
async def test_client(test_env_vars):
    """FastAPI test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sync_test_client(test_env_vars):
    """Synchronous FastAPI test client"""
    return TestClient(app)


@pytest.fixture
async def slack_client_with_mocks(
    test_env_vars, 
    fake_redis, 
    mock_slack_client, 
    mock_socket_client
):
    """Slack client with all dependencies mocked"""
    with patch('redis.asyncio.from_url', return_value=fake_redis), \
         patch('slack_sdk.web.async_client.AsyncWebClient') as mock_web_client, \
         patch('slack_sdk.socket_mode.aiohttp.SocketModeClient', return_value=mock_socket_client):
        
        # Configure the mock web client to return our mock
        mock_web_client.return_value = mock_slack_client
        
        client = SlackOptimizedClient()
        await client.setup()
        
        yield client, mock_slack_client, mock_socket_client, fake_redis
        
        await client.stop()


# Shared test data
SAMPLE_CONVERSATIONS = [
    {"id": "C111111", "name": "general", "is_private": False, "num_members": 50},
    {"id": "C222222", "name": "dev-team", "is_private": True, "num_members": 10},
    {"id": "C333333", "name": "announcements", "is_private": False, "num_members": 100}
]

SAMPLE_USERS = [
    {"id": "U123456", "name": "sophia", "real_name": "Sophia AI", "is_bot": True},
    {"id": "U987654", "name": "testuser", "real_name": "Test User", "is_bot": False},
    {"id": "U555555", "name": "admin", "real_name": "Admin User", "is_bot": False, "is_admin": True}
]

SAMPLE_MESSAGES = [
    {
        "text": "TODO: Review the quarterly report",
        "user": "U987654",
        "ts": "1234567890.123456",
        "type": "message"
    },
    {
        "text": "We decided to go with option A for the new feature",
        "user": "U555555", 
        "ts": "1234567890.234567",
        "type": "message"
    },
    {
        "text": "Please update the documentation by Friday",
        "user": "U555555",
        "ts": "1234567890.345678", 
        "type": "message"
    }
]


@pytest.fixture
def sample_data():
    """Sample Slack data for tests"""
    return {
        "conversations": SAMPLE_CONVERSATIONS,
        "users": SAMPLE_USERS,
        "messages": SAMPLE_MESSAGES
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end (requires real Slack tokens)"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_runtest_setup(item):
    """Skip e2e tests if tokens not available"""
    if item.get_closest_marker("e2e"):
        required_tokens = [
            "SLACK_BOT_TOKEN",
            "SLACK_SIGNING_SECRET", 
            "SLACK_APP_TOKEN"
        ]
        missing = [token for token in required_tokens if not os.getenv(token)]
        if missing:
            pytest.skip(f"E2E tests require tokens: {', '.join(missing)}")
