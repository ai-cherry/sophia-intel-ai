"""
Live Slack API integration tests

Tests actual Slack Web API calls using slack_sdk directly.
Requires SLACK_BOT_TOKEN in environment or .env.local.
Optional: SLACK_TEST_CHANNEL for posting test messages.
"""
import os
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.slack]


def _has_slack_env() -> bool:
    """Check if Slack credentials are available."""
    return bool(os.getenv("SLACK_BOT_TOKEN"))


def _get_channel_by_name(client, channel_name: str) -> str | None:
    """Helper to resolve channel name to ID."""
    try:
        response = client.conversations_list(types="public_channel,private_channel", limit=100)
        if not response.get("ok"):
            return None
            
        for channel in response.get("channels", []):
            if channel.get("name") == channel_name:
                return channel.get("id")
        return None
    except Exception:
        return None


@pytest.mark.asyncio
async def test_slack_auth():
    """Test Slack authentication with auth.test endpoint."""
    if not _has_slack_env():
        pytest.skip("SLACK_BOT_TOKEN not configured")

    from slack_sdk import WebClient
    
    client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    
    # Test authentication
    auth_response = client.auth_test()
    assert auth_response.get("ok") is True
    assert "user_id" in auth_response
    assert "team_id" in auth_response
    assert "team" in auth_response


@pytest.mark.asyncio 
async def test_slack_conversations_list():
    """Test Slack conversations.list endpoint."""
    if not _has_slack_env():
        pytest.skip("SLACK_BOT_TOKEN not configured")

    from slack_sdk import WebClient
    
    client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    
    # List public channels
    response = client.conversations_list(types="public_channel", limit=10)
    assert response.get("ok") is True
    assert "channels" in response
    assert isinstance(response["channels"], list)
    
    # If channels exist, verify structure
    if response["channels"]:
        channel = response["channels"][0]
        assert "id" in channel
        assert "name" in channel
        assert "is_channel" in channel


@pytest.mark.asyncio
async def test_slack_post_message_optional():
    """Test Slack message posting (optional - requires test channel)."""
    if not _has_slack_env():
        pytest.skip("SLACK_BOT_TOKEN not configured")
    
    from slack_sdk import WebClient
    
    client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    
    # Get test channel from env (ID or name)
    test_channel = os.getenv("SLACK_TEST_CHANNEL") or os.getenv("SLACK_TEST_CHANNEL_NAME")
    
    if not test_channel:
        pytest.skip("SLACK_TEST_CHANNEL or SLACK_TEST_CHANNEL_NAME not set")
    
    # If channel name provided, resolve to ID
    channel_id = test_channel
    if not test_channel.startswith("C"):  # Not a channel ID, try as name
        channel_id = _get_channel_by_name(client, test_channel)
        if not channel_id:
            pytest.skip(f"Channel '{test_channel}' not found or not accessible")
    
    # Post test message
    test_message = "🧪 Sophia integration test: Slack live API working!"
    response = client.chat_postMessage(
        channel=channel_id,
        text=test_message,
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Integration Test Result*\n✅ {test_message}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn", 
                        "text": f"Test run: `pytest tests/integration/slack/test_live_api.py::test_slack_post_message_optional`"
                    }
                ]
            }
        ]
    )
    
    assert response.get("ok") is True
    assert "ts" in response  # Message timestamp
    assert response.get("channel") == channel_id


@pytest.mark.asyncio
async def test_slack_users_list():
    """Test Slack users.list endpoint."""
    if not _has_slack_env():
        pytest.skip("SLACK_BOT_TOKEN not configured")

    from slack_sdk import WebClient
    
    client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    
    # List users (limited to avoid large responses)
    response = client.users_list(limit=5)
    assert response.get("ok") is True
    assert "members" in response
    assert isinstance(response["members"], list)
    
    # If users exist, verify structure
    if response["members"]:
        user = response["members"][0]
        assert "id" in user
        assert "name" in user or "real_name" in user


@pytest.mark.asyncio
async def test_slack_channel_resolution():
    """Test channel name to ID resolution helper."""
    if not _has_slack_env():
        pytest.skip("SLACK_BOT_TOKEN not configured")

    from slack_sdk import WebClient
    
    client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    
    # Get channels to test with
    response = client.conversations_list(types="public_channel", limit=5)
    assert response.get("ok") is True
    
    channels = response.get("channels", [])
    if not channels:
        pytest.skip("No public channels available for testing")
    
    # Test name resolution for first channel
    test_channel = channels[0]
    channel_name = test_channel.get("name")
    expected_id = test_channel.get("id")
    
    # Our helper should resolve name to ID
    resolved_id = _get_channel_by_name(client, channel_name)
    assert resolved_id == expected_id
    
    # Test non-existent channel
    fake_id = _get_channel_by_name(client, "non-existent-channel-12345")
    assert fake_id is None
