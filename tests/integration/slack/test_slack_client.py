"""
Tests for SlackOptimizedClient (outbound/push functionality)
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from app.integrations.slack_optimized_client import SlackOptimizedClient


@pytest.mark.unit
class TestSlackClientConfiguration:
    """Test Slack client configuration and validation"""
    
    async def test_validate_config_with_all_tokens(self, test_env_vars):
        """Test configuration validation with all tokens present"""
        client = SlackOptimizedClient()
        config = await client.validate_config() if callable(getattr(client.validate_config, '__call__', None)) else client.validate_config()
        
        assert config["has_bot_token"] is True
        assert config["has_app_token"] is True
        assert config["has_user_token"] is True
        assert config["has_signing_secret"] is True
        assert config["socket_mode_available"] is True
    
    @patch.dict('os.environ', {'SLACK_BOT_TOKEN': '', 'SLACK_APP_TOKEN': ''})
    async def test_validate_config_minimal(self):
        """Test configuration validation with minimal tokens"""
        client = SlackOptimizedClient()
        config = await client.validate_config() if callable(getattr(client.validate_config, '__call__', None)) else client.validate_config()
        
        assert config["has_bot_token"] is False
        assert config["has_app_token"] is False
        assert config["socket_mode_available"] is False
    
    async def test_setup_initializes_clients(self, test_env_vars, fake_redis, mock_socket_client):
        """Test that setup properly initializes all clients"""
        with patch('redis.asyncio.from_url', return_value=fake_redis), \
             patch('slack_sdk.socket_mode.aiohttp.SocketModeClient', return_value=mock_socket_client):
            
            client = SlackOptimizedClient()
            await client.setup()
            
            assert client.redis_client is not None
            assert client.web_client is not None
            assert client.socket_client is not None
            
            await client.stop()
    
    async def test_setup_without_redis_raises_error(self, test_env_vars):
        """Test that setup fails gracefully without Redis"""
        with patch('redis.asyncio.from_url', side_effect=ConnectionError("Redis unavailable")):
            
            client = SlackOptimizedClient()
            with pytest.raises(ConnectionError):
                await client.setup()


@pytest.mark.unit 
class TestMessageSending:
    """Test message sending functionality"""
    
    async def test_send_message_basic(self, slack_client_with_mocks):
        """Test basic message sending"""
        client, mock_slack_client, _, _ = slack_client_with_mocks
        
        response = await client.send_message(
            channel="C123456",
            text="Hello from test!"
        )
        
        mock_slack_client.chat_postMessage.assert_called_once_with(
            channel="C123456",
            text="Hello from test!"
        )
        assert response["ok"] is True
        assert response["channel"] == "C111111"
    
    async def test_send_message_with_blocks(self, slack_client_with_mocks):
        """Test message sending with blocks"""
        client, mock_slack_client, _, _ = slack_client_with_mocks
        
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Hello* from blocks!"}
            }
        ]
        
        await client.send_message(
            channel="C123456",
            text="Fallback text",
            blocks=blocks
        )
        
        mock_slack_client.chat_postMessage.assert_called_once_with(
            channel="C123456",
            text="Fallback text",
            blocks=blocks
        )
    
    async def test_send_message_with_all_options(self, slack_client_with_mocks):
        """Test message sending with all options"""
        client, mock_slack_client, _, _ = slack_client_with_mocks
        
        await client.send_message(
            channel="C123456",
            text="Test message",
            thread_ts="1234567890.123456",
            reply_broadcast=True,
            unfurl_links=False,
            unfurl_media=False
        )
        
        mock_slack_client.chat_postMessage.assert_called_once_with(
            channel="C123456",
            text="Test message",
            thread_ts="1234567890.123456",
            reply_broadcast=True,
            unfurl_links=False,
            unfurl_media=False
        )
    
    async def test_update_message(self, slack_client_with_mocks):
        """Test message updating"""
        client, mock_slack_client, _, _ = slack_client_with_mocks
        
        await client.update_message(
            channel="C123456",
            ts="1234567890.123456",
            text="Updated message"
        )
        
        mock_slack_client.chat_update.assert_called_once_with(
            channel="C123456",
            ts="1234567890.123456",
            text="Updated message"
        )
    
    async def test_send_response_url_success(self, slack_client_with_mocks):
        """Test response URL posting"""
        client, _, _, _ = slack_client_with_mocks
        
        response_data = {
            "response_type": "in_channel",
            "text": "Response via webhook"
        }
        
        # Mock httpx response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        
        with patch('httpx.AsyncClient.post', return_value=mock_response) as mock_post:
            result = await client.send_response(
                "https://hooks.slack.com/commands/123/456",
                response_data
            )
            
            mock_post.assert_called_once()
            assert result["ok"] is True
    
    async def test_send_response_url_retry_on_429(self, slack_client_with_mocks):
        """Test response URL retries on rate limit"""
        client, _, _, _ = slack_client_with_mocks
        
        response_data = {"text": "Rate limited response"}
        
        # Mock rate limit then success
        mock_429 = AsyncMock()
        mock_429.status_code = 429
        mock_429.headers = {"Retry-After": "1"}
        
        mock_200 = AsyncMock()
        mock_200.status_code = 200
        mock_200.json.return_value = {"ok": True}
        
        with patch('httpx.AsyncClient.post', side_effect=[mock_429, mock_200]) as mock_post:
            with patch('asyncio.sleep') as mock_sleep:
                result = await client.send_response(
                    "https://hooks.slack.com/commands/123/456",
                    response_data
                )
                
                assert mock_post.call_count == 2
                mock_sleep.assert_called_once_with(1)
                assert result["ok"] is True


@pytest.mark.unit
class TestConversationsAndUsers:
    """Test conversations and users caching"""
    
    async def test_get_conversations_cache_miss(self, slack_client_with_mocks):
        """Test conversations fetching on cache miss"""
        client, mock_slack_client, _, fake_redis = slack_client_with_mocks
        
        # Ensure cache is empty
        await fake_redis.flushall()
        
        conversations = await client.get_conversations()
        
        mock_slack_client.conversations_list.assert_called_once()
        assert len(conversations) == 2
        assert conversations[0]["name"] == "general"
        
        # Verify cached
        cached = await fake_redis.get("slack:conversations")
        assert cached is not None
    
    async def test_get_conversations_cache_hit(self, slack_client_with_mocks):
        """Test conversations from cache"""
        client, mock_slack_client, _, fake_redis = slack_client_with_mocks
        
        # Pre-populate cache
        cached_data = [{"id": "C999", "name": "cached"}]
        await fake_redis.setex(
            "slack:conversations",
            300,  # 5 minutes TTL
            json.dumps(cached_data)
        )
        
        conversations = await client.get_conversations()
        
        # Should not call API
        mock_slack_client.conversations_list.assert_not_called()
        assert conversations == cached_data
    
    async def test_get_users_cache_behavior(self, slack_client_with_mocks):
        """Test users caching with longer TTL"""
        client, mock_slack_client, _, fake_redis = slack_client_with_mocks
        
        await fake_redis.flushall()
        
        users = await client.get_users()
        
        mock_slack_client.users_list.assert_called_once()
        assert len(users) == 2
        assert users[0]["name"] == "sophia"
        
        # Verify cached with 1 hour TTL
        ttl = await fake_redis.ttl("slack:users")
        assert ttl > 3500  # Should be close to 3600 (1 hour)
    
    async def test_search_messages_with_user_token(self, slack_client_with_mocks):
        """Test message search with user token"""
        client, mock_slack_client, _, _ = slack_client_with_mocks
        
        # Mock user client
        mock_user_client = AsyncMock()
        mock_user_client.search_messages.return_value = AsyncMock(
            data={"ok": True, "messages": {"matches": []}}
        )
        client.user_client = mock_user_client
        
        results = await client.search_messages("important")
        
        mock_user_client.search_messages.assert_called_once_with(query="important")
        assert results["ok"] is True
    
    async def test_search_messages_without_user_token(self, slack_client_with_mocks):
        """Test message search fails gracefully without user token"""
        client, _, _, _ = slack_client_with_mocks
        client.user_client = None  # No user token
        
        results = await client.search_messages("important")
        
        assert results["ok"] is False
        assert "User token required" in results["error"]


@pytest.mark.unit
class TestModalHandling:
    """Test modal creation and handling"""
    
    async def test_create_modal(self, slack_client_with_mocks):
        """Test modal creation"""
        client, mock_slack_client, _, _ = slack_client_with_mocks
        
        view = {
            "type": "modal",
            "title": {"type": "plain_text", "text": "Test Modal"},
            "blocks": []
        }
        
        await client.create_modal("123456.789", view)
        
        mock_slack_client.views_open.assert_called_once_with(
            trigger_id="123456.789",
            view=view
        )
    
    async def test_create_modal_with_callback_id(self, slack_client_with_mocks):
        """Test modal with callback ID"""
        client, mock_slack_client, _, _ = slack_client_with_mocks
        
        view = {
            "type": "modal",
            "callback_id": "feedback_modal",
            "title": {"type": "plain_text", "text": "Feedback"},
            "blocks": []
        }
        
        await client.create_modal("123456.789", view)
        
        called_view = mock_slack_client.views_open.call_args[1]["view"]
        assert called_view["callback_id"] == "feedback_modal"


@pytest.mark.unit
class TestSocketModeHandling:
    """Test Socket Mode functionality"""
    
    async def test_start_registers_listener(self, slack_client_with_mocks):
        """Test that start() registers socket mode listener"""
        client, _, mock_socket_client, _ = slack_client_with_mocks
        
        await client.start()
        
        # Verify listener was registered
        assert len(mock_socket_client.socket_mode_request_listeners) > 0
        mock_socket_client.connect_async.assert_called_once()
    
    async def test_stop_disconnects_socket(self, slack_client_with_mocks):
        """Test that stop() disconnects socket"""
        client, _, mock_socket_client, _ = slack_client_with_mocks
        
        await client.start()
        await client.stop()
        
        mock_socket_client.disconnect_async.assert_called_once()
    
    async def test_socket_mode_event_processing(self, slack_client_with_mocks):
        """Test Socket Mode event processing"""
        client, _, mock_socket_client, _ = slack_client_with_mocks
        
        # Mock socket mode request
        from slack_sdk.socket_mode.request import SocketModeRequest
        from slack_sdk.socket_mode.response import SocketModeResponse
        
        mock_request = SocketModeRequest(
            type="events_api",
            envelope_id="envelope_123",
            payload={
                "event": {
                    "type": "app_mention",
                    "text": "<@U123> hello",
                    "user": "U456",
                    "channel": "C789"
                }
            }
        )
        
        await client.start()
        
        # Get the registered handler
        handler = mock_socket_client.socket_mode_request_listeners[0]
        
        # Mock the handler dependencies
        with patch('app.api.routers.slack_business_intelligence.handle_slack_event') as mock_handler:
            mock_handler.return_value = {"status": "ok"}
            
            await handler(client.socket_client, mock_request)
            
            # Verify event was processed
            mock_handler.assert_called_once()
            mock_socket_client.send_socket_mode_response.assert_called_once()
    
    async def test_socket_mode_slash_command_processing(self, slack_client_with_mocks):
        """Test Socket Mode slash command processing"""
        client, _, mock_socket_client, _ = slack_client_with_mocks
        
        from slack_sdk.socket_mode.request import SocketModeRequest
        
        mock_request = SocketModeRequest(
            type="slash_commands",
            envelope_id="envelope_456", 
            payload={
                "command": "/sophia",
                "text": "help",
                "user_id": "U456",
                "channel_id": "C789"
            }
        )
        
        await client.start()
        handler = mock_socket_client.socket_mode_request_listeners[0]
        
        with patch('app.api.routers.slack_business_intelligence.handle_slash_command') as mock_handler:
            mock_handler.return_value = {"response_type": "in_channel", "text": "Help text"}
            
            await handler(client.socket_client, mock_request)
            
            mock_handler.assert_called_once()
            mock_socket_client.send_socket_mode_response.assert_called_once()


@pytest.mark.integration 
class TestConversationAnalyzer:
    """Test conversation analysis functionality"""
    
    async def test_analyze_channel_basic(self, slack_client_with_mocks, sample_data):
        """Test basic channel analysis"""
        client, mock_slack_client, _, _ = slack_client_with_mocks
        
        # Mock conversation history
        mock_slack_client.conversations_history.return_value = AsyncMock(
            data={"ok": True, "messages": sample_data["messages"]}
        )
        
        analysis = await client.analyze_channel("C123456", hours_back=24)
        
        assert "insights" in analysis
        assert "action_items" in analysis
        assert "decisions" in analysis
        assert "message_count" in analysis
        
        # Should detect action item from sample data
        action_items = analysis["action_items"]
        assert len(action_items) > 0
        assert any("Review the quarterly report" in item for item in action_items)
    
    async def test_extract_action_items(self, slack_client_with_mocks):
        """Test action item extraction"""
        client, _, _, _ = slack_client_with_mocks
        
        messages = [
            {"text": "TODO: Update the documentation", "user": "U123", "ts": "1234567890"},
            {"text": "Action item: Schedule the meeting", "user": "U456", "ts": "1234567891"},
            {"text": "Please review the code by Friday", "user": "U789", "ts": "1234567892"},
            {"text": "Just a regular message", "user": "U111", "ts": "1234567893"},
        ]
        
        action_items = client._extract_action_items(messages)
        
        assert len(action_items) == 3
        assert "Update the documentation" in action_items[0]
        assert "Schedule the meeting" in action_items[1]  
        assert "review the code by Friday" in action_items[2]
    
    async def test_detect_decisions(self, slack_client_with_mocks):
        """Test decision detection"""
        client, _, _, _ = slack_client_with_mocks
        
        messages = [
            {"text": "We decided to go with option A", "user": "U123", "ts": "1234567890"},
            {"text": "Let's move forward with the new design", "user": "U456", "ts": "1234567891"},
            {"text": "Not a decision message", "user": "U789", "ts": "1234567892"},
        ]
        
        decisions = client._detect_decisions(messages)
        
        assert len(decisions) == 2
        assert "decided to go with option A" in decisions[0]
        assert "move forward with the new design" in decisions[1]
    
    async def test_detect_high_activity(self, slack_client_with_mocks):
        """Test high activity pattern detection"""
        client, _, _, _ = slack_client_with_mocks
        
        # Create messages with high frequency (>10 per hour)
        base_time = 1234567890
        messages = []
        for i in range(15):
            messages.append({
                "text": f"Message {i}",
                "user": f"U{i % 3}",
                "ts": str(base_time + (i * 60))  # One message per minute
            })
        
        patterns = client._detect_patterns(messages)
        
        high_activity = [p for p in patterns if "high activity" in p]
        assert len(high_activity) > 0
        assert "15.0 messages/hour" in high_activity[0]


@pytest.mark.slow
@pytest.mark.integration
class TestRateLimitHandling:
    """Test rate limit handling and retries"""
    
    async def test_rate_limit_retry_logic(self, slack_client_with_mocks):
        """Test automatic retry on rate limits"""
        client, mock_slack_client, _, _ = slack_client_with_mocks
        
        # Mock rate limit then success
        from slack_sdk.errors import SlackApiError
        
        rate_limit_error = SlackApiError(
            message="Rate limited", 
            response={"error": "rate_limited", "headers": {"Retry-After": "1"}}
        )
        
        mock_slack_client.chat_postMessage.side_effect = [
            rate_limit_error,
            AsyncMock(data={"ok": True, "channel": "C123", "ts": "1234567890"})
        ]
        
        with patch('asyncio.sleep') as mock_sleep:
            response = await client.send_message("C123456", "Rate limited message")
            
            assert mock_slack_client.chat_postMessage.call_count == 2
            mock_sleep.assert_called_once_with(1)
            assert response["ok"] is True
    
    async def test_max_retries_exceeded(self, slack_client_with_mocks):
        """Test behavior when max retries exceeded"""
        client, mock_slack_client, _, _ = slack_client_with_mocks
        
        from slack_sdk.errors import SlackApiError
        
        rate_limit_error = SlackApiError(
            message="Rate limited",
            response={"error": "rate_limited", "headers": {"Retry-After": "1"}}
        )
        
        # Always return rate limit error
        mock_slack_client.chat_postMessage.side_effect = rate_limit_error
        
        with pytest.raises(SlackApiError):
            await client.send_message("C123456", "Always rate limited")
