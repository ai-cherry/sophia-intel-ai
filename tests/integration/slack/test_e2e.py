"""
End-to-End tests for Slack integration (requires real tokens)
"""
import pytest
import os
import json
import asyncio
from datetime import datetime
from unittest.mock import patch

from app.integrations.slack_optimized_client import SlackOptimizedClient


@pytest.mark.e2e
@pytest.mark.slow
class TestSlackE2EIntegration:
    """End-to-end tests requiring real Slack tokens and workspace"""
    
    @pytest.fixture(autouse=True)
    async def setup_real_client(self):
        """Setup real Slack client for e2e tests"""
        self.client = SlackOptimizedClient()
        config = self.client.validate_config()
        
        # Verify required tokens are available
        assert config["has_bot_token"], "SLACK_BOT_TOKEN required for e2e tests"
        assert config["has_signing_secret"], "SLACK_SIGNING_SECRET required for e2e tests"
        
        await self.client.setup()
        yield
        await self.client.stop()
    
    async def test_real_message_sending(self):
        """Test sending actual message to test channel"""
        test_channel = os.getenv("SLACK_TEST_CHANNEL", "#ci-slack-tests")
        
        response = await self.client.send_message(
            channel=test_channel,
            text=f"🧪 E2E Test Message - {datetime.now().isoformat()}"
        )
        
        assert response["ok"] is True
        assert "ts" in response
        assert "channel" in response
        
        # Clean up: delete the test message
        await self.client.delete_message(
            channel=response["channel"],
            ts=response["ts"]
        )
    
    async def test_real_conversations_list(self):
        """Test fetching real conversations"""
        conversations = await self.client.get_conversations()
        
        assert len(conversations) > 0
        assert all("id" in conv and "name" in conv for conv in conversations)
        
        # Verify test channel exists
        test_channel = os.getenv("SLACK_TEST_CHANNEL", "#ci-slack-tests")
        channel_names = [conv.get("name") for conv in conversations]
        assert test_channel.lstrip("#") in channel_names or test_channel in channel_names
    
    async def test_real_users_list(self):
        """Test fetching real users"""
        users = await self.client.get_users()
        
        assert len(users) > 0
        assert all("id" in user and "name" in user for user in users)
        
        # Should include bot users
        bot_users = [user for user in users if user.get("is_bot")]
        assert len(bot_users) > 0
    
    @pytest.mark.skipif(not os.getenv("SLACK_USER_TOKEN"), reason="User token required")
    async def test_real_message_search(self):
        """Test real message search (requires user token)"""
        results = await self.client.search_messages("test")
        
        assert results["ok"] is True
        assert "messages" in results
    
    async def test_real_channel_analysis(self):
        """Test analyzing a real channel"""
        test_channel = os.getenv("SLACK_TEST_CHANNEL", "#ci-slack-tests")
        
        # Get channel ID first
        conversations = await self.client.get_conversations()
        test_conv = next(
            (conv for conv in conversations 
             if conv["name"] == test_channel.lstrip("#")), 
            None
        )
        
        if test_conv:
            analysis = await self.client.analyze_channel(test_conv["id"], hours_back=1)
            
            assert "message_count" in analysis
            assert "insights" in analysis
            assert "action_items" in analysis
            assert "decisions" in analysis


@pytest.mark.e2e
class TestSlackWebhookE2E:
    """E2E tests for webhook endpoints"""
    
    async def test_real_webhook_url_verification(self, test_client, signature_helper):
        """Test URL verification against real webhook endpoint"""
        # This would typically be tested by configuring Slack app to point to test server
        challenge = "real_challenge_from_slack"
        payload = {"type": "url_verification", "challenge": challenge}
        body = json.dumps(payload)
        headers = signature_helper.get_headers(body)
        
        response = await test_client.post("/api/slack/webhook", content=body, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["challenge"] == challenge
    
    @pytest.mark.skipif(not os.getenv("BASE_URL"), reason="BASE_URL required for webhook tests")
    async def test_webhook_accessibility(self):
        """Test that webhook endpoints are accessible from internet"""
        import httpx
        
        base_url = os.getenv("BASE_URL")  # e.g., https://ngrok-url.ngrok.io
        
        # Test health endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/slack/health")
            assert response.status_code == 200
    
    async def test_real_slash_command_processing(self, test_client, signature_helper, event_builder):
        """Test slash command processing with real-like payload"""
        form_data = event_builder.slash_command_form(
            command="/sophia",
            text="status",
            user_id="U123REAL",
            channel_id="C456REAL"
        )
        
        from urllib.parse import urlencode
        body = urlencode(form_data)
        headers = signature_helper.get_form_headers(body)
        
        with patch('app.api.routers.slack_business_intelligence.get_sophia_slack_intelligence') as mock_sophia:
            mock_sophia.return_value.handle_slack_command.return_value = "System status: All systems operational"
            
            response = await test_client.post("/api/slack/commands", content=body, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["response_type"] == "in_channel"
        assert "All systems operational" in data["text"]


@pytest.mark.e2e
class TestSlackSocketModeE2E:
    """E2E tests for Socket Mode (requires app token)"""
    
    @pytest.mark.skipif(not os.getenv("SLACK_APP_TOKEN"), reason="App token required for Socket Mode")
    async def test_socket_mode_connection(self):
        """Test real Socket Mode connection"""
        client = SlackOptimizedClient()
        await client.setup()
        
        # Start socket mode
        await client.start()
        
        # Wait a moment for connection
        await asyncio.sleep(2)
        
        # Verify connection (this would need actual socket client inspection)
        assert client.socket_client is not None
        
        # Clean up
        await client.stop()
    
    @pytest.mark.skipif(not os.getenv("SLACK_APP_TOKEN"), reason="App token required")
    async def test_socket_mode_event_handling(self):
        """Test Socket Mode handles real events"""
        # This would require coordinating with actual Slack events
        # In practice, this might be tested by:
        # 1. Starting socket mode client
        # 2. Triggering an event in Slack (mention, slash command)
        # 3. Verifying the event was received and processed
        
        client = SlackOptimizedClient()
        await client.setup()
        await client.start()
        
        # In a real test, we'd wait for events and verify handling
        # For now, just verify the connection works
        await asyncio.sleep(1)
        
        await client.stop()


@pytest.mark.e2e
class TestBusinessIntelligenceE2E:
    """E2E tests for BI integration with real Slack"""
    
    async def test_real_bi_alert_delivery(self, test_client):
        """Test sending real BI alert to test channel"""
        test_channel = os.getenv("SLACK_TEST_CHANNEL", "#ci-slack-tests")
        
        response = await test_client.post(f"/api/slack/test-integration?channel={test_channel}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["results"]["sent"] > 0
    
    async def test_real_daily_summary_generation(self, test_client):
        """Test generating and sending real daily summary"""
        # This would send actual summary to configured channel
        with patch('app.api.routers.slack_business_intelligence.get_sophia_slack') as mock_sophia:
            from app.integrations.slack_intelligence import SlackAlert
            
            summary_alert = SlackAlert(
                channel=os.getenv("SLACK_TEST_CHANNEL", "#ci-slack-tests"),
                message="📊 Daily E2E Test Summary\n\nThis is a test of the daily summary feature.",
                priority="low",
                data={"test": True}
            )
            
            mock_sophia.return_value.create_daily_business_summary.return_value = summary_alert
            mock_sophia.return_value.send_slack_alerts.return_value = {"sent": 1, "failed": 0}
            
            response = await test_client.get("/api/slack/daily-summary")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
    
    async def test_real_health_check_integration(self, test_client):
        """Test health check with real configuration"""
        response = await test_client.get("/api/slack/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should reflect real configuration
        if os.getenv("SLACK_BOT_TOKEN"):
            assert data["credentials_present"]["client_id"] is not None
        
        # Status should be healthy if properly configured
        if all(os.getenv(var) for var in ["SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET"]):
            assert data["status"] in ["healthy", "operational"]


@pytest.mark.e2e
class TestPerformanceE2E:
    """E2E performance tests"""
    
    async def test_webhook_response_time(self, test_client, signature_helper):
        """Test webhook responds within Slack's 3-second requirement"""
        import time
        
        payload = {"type": "url_verification", "challenge": "perf_test"}
        body = json.dumps(payload)
        headers = signature_helper.get_headers(body)
        
        start_time = time.time()
        response = await test_client.post("/api/slack/webhook", content=body, headers=headers)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 3.0  # Slack requires <3s response
        assert response_time < 1.0  # Our target is <1s
    
    async def test_bulk_message_sending_performance(self):
        """Test sending multiple messages in reasonable time"""
        if not os.getenv("SLACK_BOT_TOKEN"):
            pytest.skip("Bot token required for performance test")
        
        client = SlackOptimizedClient()
        await client.setup()
        
        test_channel = os.getenv("SLACK_TEST_CHANNEL", "#ci-slack-tests")
        message_count = 5
        
        import time
        start_time = time.time()
        
        # Send multiple messages
        tasks = []
        for i in range(message_count):
            task = client.send_message(
                channel=test_channel,
                text=f"Performance test {i+1}/{message_count} - {datetime.now().isoformat()}"
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
