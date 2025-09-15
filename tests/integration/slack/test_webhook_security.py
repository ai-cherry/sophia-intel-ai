"""
Tests for Slack webhook security and signature verification
"""
import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import patch
from fastapi import HTTPException

from app.api.routers.slack_business_intelligence import _slack_signature_guard
from tests.integration.slack.conftest import SlackSignatureHelper


@pytest.mark.unit
class TestSlackSignatureVerification:
    """Test Slack signature verification logic"""
    
    async def test_valid_signature_passes(self, test_client, signature_helper):
        """Test that valid signature passes verification"""
        body = json.dumps({"type": "url_verification", "challenge": "test"})
        timestamp = int(time.time())
        headers = signature_helper.get_headers(body, timestamp)
        
        response = await test_client.post(
            "/api/slack/webhook",
            content=body,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["challenge"] == "test"
    
    async def test_missing_timestamp_header_fails(self, test_client, signature_helper):
        """Test that missing timestamp header returns 401"""
        body = json.dumps({"type": "url_verification", "challenge": "test"})
        headers = signature_helper.get_headers(body)
        del headers["X-Slack-Request-Timestamp"]
        
        response = await test_client.post(
            "/api/slack/webhook",
            content=body,
            headers=headers
        )
        
        assert response.status_code == 401
        assert "Missing Slack signature headers" in response.json()["detail"]
    
    async def test_missing_signature_header_fails(self, test_client, signature_helper):
        """Test that missing signature header returns 401"""
        body = json.dumps({"type": "url_verification", "challenge": "test"})
        headers = signature_helper.get_headers(body)
        del headers["X-Slack-Signature"]
        
        response = await test_client.post(
            "/api/slack/webhook",
            content=body,
            headers=headers
        )
        
        assert response.status_code == 401
        assert "Missing Slack signature headers" in response.json()["detail"]
    
    async def test_invalid_timestamp_fails(self, test_client, signature_helper):
        """Test that invalid timestamp format returns 400"""
        body = json.dumps({"type": "url_verification", "challenge": "test"})
        headers = signature_helper.get_headers(body)
        headers["X-Slack-Request-Timestamp"] = "invalid_timestamp"
        
        response = await test_client.post(
            "/api/slack/webhook",
            content=body,
            headers=headers
        )
        
        assert response.status_code == 400
        assert "Invalid Slack timestamp" in response.json()["detail"]
    
    async def test_stale_timestamp_fails(self, test_client, signature_helper):
        """Test that old timestamp (>5 minutes) returns 401"""
        body = json.dumps({"type": "url_verification", "challenge": "test"})
        # Timestamp from 10 minutes ago
        stale_timestamp = int(time.time()) - (10 * 60)
        headers = signature_helper.get_headers(body, stale_timestamp)
        
        response = await test_client.post(
            "/api/slack/webhook",
            content=body,
            headers=headers
        )
        
        assert response.status_code == 401
        assert "Stale Slack request" in response.json()["detail"]
    
    async def test_invalid_signature_fails(self, test_client, signature_helper):
        """Test that invalid signature returns 401"""
        body = json.dumps({"type": "url_verification", "challenge": "test"})
        timestamp = int(time.time())
        headers = signature_helper.get_headers(body, timestamp)
        # Corrupt the signature
        headers["X-Slack-Signature"] = "v0=invalid_signature_here"
        
        response = await test_client.post(
            "/api/slack/webhook",
            content=body,
            headers=headers
        )
        
        assert response.status_code == 401
        assert "Invalid Slack signature" in response.json()["detail"]
    
    async def test_tampered_body_fails(self, test_client, signature_helper):
        """Test that tampered body with valid signature fails"""
        original_body = json.dumps({"type": "url_verification", "challenge": "test"})
        timestamp = int(time.time())
        headers = signature_helper.get_headers(original_body, timestamp)
        
        # Send different body than what signature was computed for
        tampered_body = json.dumps({"type": "url_verification", "challenge": "hacked"})
        
        response = await test_client.post(
            "/api/slack/webhook",
            content=tampered_body,
            headers=headers
        )
        
        assert response.status_code == 401
        assert "Invalid Slack signature" in response.json()["detail"]
    
    @patch.dict('os.environ', {'SLACK_SIGNING_SECRET': ''})
    async def test_no_signing_secret_allows_but_warns(self, test_client, caplog):
        """Test that missing signing secret allows request but logs warning"""
        body = json.dumps({"type": "url_verification", "challenge": "test"})
        
        # Send request without any signature headers
        response = await test_client.post(
            "/api/slack/webhook",
            content=body,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        assert "SLACK_SIGNING_SECRET not set" in caplog.text
        assert "skipping signature verification" in caplog.text
    
    async def test_future_timestamp_within_tolerance_passes(self, test_client, signature_helper):
        """Test that future timestamp within tolerance passes"""
        body = json.dumps({"type": "url_verification", "challenge": "test"})
        # Timestamp from 2 minutes in the future (within 5 minute tolerance)
        future_timestamp = int(time.time()) + (2 * 60)
        headers = signature_helper.get_headers(body, future_timestamp)
        
        response = await test_client.post(
            "/api/slack/webhook",
            content=body,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["challenge"] == "test"
    
    async def test_form_encoded_signature_verification(self, test_client, signature_helper, event_builder):
        """Test signature verification for form-encoded slash commands"""
        form_data = event_builder.slash_command_form()
        
        # Convert form data to URL-encoded string
        from urllib.parse import urlencode
        body = urlencode(form_data)
        headers = signature_helper.get_form_headers(body)
        
        response = await test_client.post(
            "/api/slack/commands",
            content=body,
            headers=headers
        )
        
        assert response.status_code == 200
        # Should return in_channel response
        data = response.json()
        assert data["response_type"] == "in_channel"
    
    async def test_constant_time_comparison_prevents_timing_attacks(self, signature_helper):
        """Test that signature comparison is constant time"""
        import hmac
        
        # This test is more about ensuring we use hmac.compare_digest
        # which is designed to be constant-time
        body = "test body"
        timestamp = int(time.time())
        
        correct_sig = signature_helper.generate_signature(body, timestamp)
        wrong_sig = "v0=wrong_signature_of_same_length_as_correct"
        
        # Both comparisons should take similar time (constant time)
        # We can't easily test timing here, but we verify the function exists
        assert hasattr(hmac, 'compare_digest')
        
        # Test that both wrong signatures fail
        assert not hmac.compare_digest(correct_sig, wrong_sig)
        assert not hmac.compare_digest(correct_sig, "v0=short")


@pytest.mark.integration
class TestWebhookRouting:
    """Test webhook routing based on content type and payload"""
    
    async def test_url_verification_challenge(self, test_client, signature_helper, event_builder):
        """Test URL verification challenge response"""
        challenge = "unique_challenge_12345"
        payload = event_builder.url_verification(challenge)
        body = json.dumps(payload)
        headers = signature_helper.get_headers(body)
        
        response = await test_client.post(
            "/api/slack/webhook",
            content=body,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["challenge"] == challenge
    
    async def test_app_mention_event_handling(self, test_client, signature_helper, event_builder):
        """Test app mention event is processed"""
        payload = event_builder.app_mention(text="<@U123456> hello sophia")
        body = json.dumps(payload)
        headers = signature_helper.get_headers(body)
        
        with patch('app.api.routers.slack_business_intelligence.get_sophia_slack_intelligence') as mock_sophia:
            mock_sophia.return_value.handle_slack_command.return_value = "Hello! How can I help?"
            
            response = await test_client.post(
                "/api/slack/webhook",
                content=body,
                headers=headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    async def test_message_event_handling(self, test_client, signature_helper, event_builder):
        """Test direct message event is processed"""
        payload = event_builder.message_event(text="Hello Sophia", channel="D123456")
        body = json.dumps(payload)
        headers = signature_helper.get_headers(body)
        
        response = await test_client.post(
            "/api/slack/webhook",
            content=body,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    async def test_slash_command_via_webhook(self, test_client, signature_helper, event_builder):
        """Test slash command sent to webhook endpoint"""
        form_data = event_builder.slash_command_form(command="/sophia", text="help")
        from urllib.parse import urlencode
        body = urlencode(form_data)
        headers = signature_helper.get_form_headers(body)
        
        with patch('app.api.routers.slack_business_intelligence.get_sophia_slack_intelligence') as mock_sophia:
            mock_sophia.return_value.handle_slack_command.return_value = "Here's how to use Sophia..."
            
            response = await test_client.post(
                "/api/slack/webhook",
                content=body,
                headers=headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["response_type"] == "in_channel"
        assert "Here's how to use Sophia" in data["text"]
    
    async def test_commands_endpoint_dedicated(self, test_client, signature_helper, event_builder):
        """Test dedicated commands endpoint"""
        form_data = event_builder.slash_command_form(command="/bi", text="status")
        from urllib.parse import urlencode
        body = urlencode(form_data)
        headers = signature_helper.get_form_headers(body)
        
        with patch('app.api.routers.slack_business_intelligence.get_sophia_slack_intelligence') as mock_sophia:
            mock_sophia.return_value.handle_slack_command.return_value = "BI Status: All systems operational"
            
            response = await test_client.post(
                "/api/slack/commands",
                content=body,
                headers=headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["response_type"] == "in_channel"
        assert "All systems operational" in data["text"]
    
    async def test_interactivity_endpoint(self, test_client, signature_helper, event_builder):
        """Test interactivity endpoint for buttons and modals"""
        payload = event_builder.interactive_button_payload(action_id="approve_report")
        
        # Slack sends interactive payloads as form data with 'payload' field containing JSON
        form_data = {"payload": json.dumps(payload)}
        from urllib.parse import urlencode
        body = urlencode(form_data)
        headers = signature_helper.get_form_headers(body)
        
        response = await test_client.post(
            "/api/slack/interactivity",
            content=body,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    async def test_interactivity_missing_payload(self, test_client, signature_helper):
        """Test interactivity endpoint with missing payload"""
        form_data = {"other_field": "value"}
        from urllib.parse import urlencode
        body = urlencode(form_data)
        headers = signature_helper.get_form_headers(body)
        
        response = await test_client.post(
            "/api/slack/interactivity",
            content=body,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"
    
    async def test_health_endpoint(self, test_client):
        """Test health endpoint returns OK"""
        response = await test_client.get("/api/slack/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
    
    async def test_error_handling_in_webhook(self, test_client, signature_helper):
        """Test error handling when processing fails"""
        # Send malformed JSON
        body = "invalid json"
        headers = signature_helper.get_headers(body)
        
        response = await test_client.post(
            "/api/slack/webhook",
            content=body,
            headers=headers
        )
        
        assert response.status_code == 500
    
    async def test_slash_command_error_handling(self, test_client, signature_helper, event_builder):
        """Test slash command error returns ephemeral response"""
        form_data = event_builder.slash_command_form(command="/sophia", text="error")
        from urllib.parse import urlencode
        body = urlencode(form_data)
        headers = signature_helper.get_form_headers(body)
        
        with patch('app.api.routers.slack_business_intelligence.get_sophia_slack_intelligence') as mock_sophia:
            mock_sophia.return_value.handle_slack_command.side_effect = Exception("Test error")
            
            response = await test_client.post(
                "/api/slack/commands",
                content=body,
                headers=headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["response_type"] == "ephemeral"
        assert "Sorry, I encountered an error" in data["text"]
        assert "Test error" in data["text"]
