"""
Tests for SOPHIABusinessMaster action-taking capabilities
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from sophia.core.business_master import SOPHIABusinessMaster


@pytest.fixture
def business_master():
    """Create business master instance for testing."""
    return SOPHIABusinessMaster()


@pytest.fixture
def mock_slack_response():
    """Mock successful Slack API response."""
    return {
        "ok": True,
        "ts": "1234567890.123456",
        "channel": "C1234567890",
        "message": {
            "text": "Test message",
            "user": "U1234567890"
        }
    }


@pytest.fixture
def mock_hubspot_contact_response():
    """Mock successful HubSpot contact response."""
    return {
        "id": "12345",
        "properties": {
            "email": "test@example.com",
            "firstname": "John",
            "lastname": "Doe"
        },
        "createdAt": "2023-01-01T00:00:00.000Z",
        "updatedAt": "2023-01-01T00:00:00.000Z"
    }


@pytest.fixture
def mock_hubspot_deal_response():
    """Mock successful HubSpot deal response."""
    return {
        "id": "67890",
        "properties": {
            "dealname": "Test Deal",
            "amount": "10000",
            "dealstage": "appointmentscheduled"
        },
        "createdAt": "2023-01-01T00:00:00.000Z",
        "updatedAt": "2023-01-01T00:00:00.000Z"
    }


@pytest.fixture
def mock_salesforce_response():
    """Mock successful Salesforce response."""
    return {
        "id": "003XX000004TmiQQAS",
        "success": True,
        "errors": []
    }


class TestBusinessActionTaking:
    """Test business action-taking capabilities."""
    
    @pytest.mark.asyncio
    async def test_post_slack_message_success(self, business_master, mock_slack_response):
        """Test successful Slack message posting."""
        with patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'xoxb-test-token'}):
            with patch('aiohttp.ClientSession') as mock_session:
                mock_response = AsyncMock()
                mock_response.json = AsyncMock(return_value=mock_slack_response)
                mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
                
                result = await business_master.post_slack_message(
                    channel="#general",
                    message="Test message"
                )
                
                assert result["ok"] is True
                assert result["ts"] == "1234567890.123456"
                assert len(business_master.action_history) == 1
                assert business_master.action_history[0]["action_type"] == "post_message"
                assert business_master.action_history[0]["service"] == "slack"
                assert business_master.action_history[0]["success"] is True
    
    @pytest.mark.asyncio
    async def test_post_slack_message_with_blocks(self, business_master, mock_slack_response):
        """Test Slack message with blocks."""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Hello from SOPHIA!"
                }
            }
        ]
        
        with patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'xoxb-test-token'}):
            with patch('aiohttp.ClientSession') as mock_session:
                mock_response = AsyncMock()
                mock_response.json = AsyncMock(return_value=mock_slack_response)
                mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
                
                result = await business_master.post_slack_message(
                    channel="#general",
                    message="Test message",
                    blocks=blocks
                )
                
                assert result["ok"] is True
                # Check that blocks were included in action history
                action = business_master.action_history[0]
                assert action["details"]["has_blocks"] is True
    
    @pytest.mark.asyncio
    async def test_post_slack_message_no_token(self, business_master):
        """Test Slack message without token."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(RuntimeError, match="SLACK_BOT_TOKEN not configured"):
                await business_master.post_slack_message(
                    channel="#general",
                    message="Test message"
                )
    
    @pytest.mark.asyncio
    async def test_post_slack_message_api_error(self, business_master):
        """Test Slack API error handling."""
        error_response = {
            "ok": False,
            "error": "channel_not_found"
        }
        
        with patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'xoxb-test-token'}):
            with patch('aiohttp.ClientSession') as mock_session:
                mock_response = AsyncMock()
                mock_response.json = AsyncMock(return_value=error_response)
                mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
                
                with pytest.raises(RuntimeError, match="Slack API error: channel_not_found"):
                    await business_master.post_slack_message(
                        channel="#nonexistent",
                        message="Test message"
                    )
                
                # Check error was logged
                assert len(business_master.action_history) == 1
                assert business_master.action_history[0]["success"] is False
    
    @pytest.mark.asyncio
    async def test_update_hubspot_contact_success(self, business_master, mock_hubspot_contact_response):
        """Test successful HubSpot contact update."""
        properties = {
            "firstname": "Jane",
            "lastname": "Smith",
            "company": "ACME Corp"
        }
        
        with patch.dict('os.environ', {'HUBSPOT_ACCESS_TOKEN': 'test-token'}):
            with patch('aiohttp.ClientSession') as mock_session:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json = AsyncMock(return_value=mock_hubspot_contact_response)
                mock_session.return_value.__aenter__.return_value.patch.return_value.__aenter__.return_value = mock_response
                
                result = await business_master.update_hubspot_contact(
                    contact_id="12345",
                    properties=properties
                )
                
                assert result["id"] == "12345"
                assert len(business_master.action_history) == 1
                action = business_master.action_history[0]
                assert action["action_type"] == "update_contact"
                assert action["service"] == "hubspot"
                assert action["details"]["property_count"] == 3
    
    @pytest.mark.asyncio
    async def test_update_hubspot_contact_no_token(self, business_master):
        """Test HubSpot contact update without token."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(RuntimeError, match="HUBSPOT_ACCESS_TOKEN not configured"):
                await business_master.update_hubspot_contact(
                    contact_id="12345",
                    properties={"firstname": "Jane"}
                )
    
    @pytest.mark.asyncio
    async def test_create_hubspot_deal_success(self, business_master, mock_hubspot_deal_response):
        """Test successful HubSpot deal creation."""
        with patch.dict('os.environ', {'HUBSPOT_ACCESS_TOKEN': 'test-token'}):
            with patch('aiohttp.ClientSession') as mock_session:
                mock_response = AsyncMock()
                mock_response.status = 201
                mock_response.json = AsyncMock(return_value=mock_hubspot_deal_response)
                mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
                
                result = await business_master.create_hubspot_deal(
                    deal_name="Test Deal",
                    amount=10000.0,
                    close_date="2024-12-31",
                    associated_contacts=["12345"]
                )
                
                assert result["id"] == "67890"
                assert len(business_master.action_history) == 1
                action = business_master.action_history[0]
                assert action["action_type"] == "create_deal"
                assert action["details"]["deal_name"] == "Test Deal"
                assert action["details"]["amount"] == 10000.0
                assert action["details"]["associated_contacts"] == 1
    
    @pytest.mark.asyncio
    async def test_create_hubspot_deal_minimal(self, business_master, mock_hubspot_deal_response):
        """Test HubSpot deal creation with minimal data."""
        with patch.dict('os.environ', {'HUBSPOT_ACCESS_TOKEN': 'test-token'}):
            with patch('aiohttp.ClientSession') as mock_session:
                mock_response = AsyncMock()
                mock_response.status = 201
                mock_response.json = AsyncMock(return_value=mock_hubspot_deal_response)
                mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
                
                result = await business_master.create_hubspot_deal(
                    deal_name="Minimal Deal"
                )
                
                assert result["id"] == "67890"
                action = business_master.action_history[0]
                assert action["details"]["associated_contacts"] == 0
    
    @pytest.mark.asyncio
    async def test_create_salesforce_record_success(self, business_master, mock_salesforce_response):
        """Test successful Salesforce record creation."""
        fields = {
            "Name": "ACME Corp",
            "Type": "Customer",
            "Industry": "Technology"
        }
        
        with patch.dict('os.environ', {
            'SALESFORCE_INSTANCE_URL': 'https://test.salesforce.com',
            'SALESFORCE_ACCESS_TOKEN': 'test-token'
        }):
            with patch('aiohttp.ClientSession') as mock_session:
                mock_response = AsyncMock()
                mock_response.status = 201
                mock_response.json = AsyncMock(return_value=mock_salesforce_response)
                mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
                
                result = await business_master.create_salesforce_record(
                    object_type="Account",
                    fields=fields
                )
                
                assert result["id"] == "003XX000004TmiQQAS"
                assert result["success"] is True
                assert len(business_master.action_history) == 1
                action = business_master.action_history[0]
                assert action["action_type"] == "create_record"
                assert action["service"] == "salesforce"
                assert action["details"]["object_type"] == "Account"
    
    @pytest.mark.asyncio
    async def test_create_salesforce_record_no_credentials(self, business_master):
        """Test Salesforce record creation without credentials."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(RuntimeError, match="Salesforce credentials not configured"):
                await business_master.create_salesforce_record(
                    object_type="Account",
                    fields={"Name": "Test"}
                )
    
    @pytest.mark.asyncio
    async def test_update_salesforce_record_success(self, business_master):
        """Test successful Salesforce record update."""
        fields = {
            "Name": "Updated ACME Corp",
            "Industry": "Software"
        }
        
        with patch.dict('os.environ', {
            'SALESFORCE_INSTANCE_URL': 'https://test.salesforce.com',
            'SALESFORCE_ACCESS_TOKEN': 'test-token'
        }):
            with patch('aiohttp.ClientSession') as mock_session:
                mock_response = AsyncMock()
                mock_response.status = 204  # Salesforce returns 204 for successful updates
                mock_session.return_value.__aenter__.return_value.patch.return_value.__aenter__.return_value = mock_response
                
                result = await business_master.update_salesforce_record(
                    object_type="Account",
                    record_id="003XX000004TmiQQAS",
                    fields=fields
                )
                
                assert result is True
                assert len(business_master.action_history) == 1
                action = business_master.action_history[0]
                assert action["action_type"] == "update_record"
                assert action["details"]["record_id"] == "003XX000004TmiQQAS"
    
    @pytest.mark.asyncio
    async def test_send_automated_email_success(self, business_master):
        """Test successful automated email sending."""
        email_response = {
            "statusId": "SENT",
            "sendResult": "SENT"
        }
        
        with patch.dict('os.environ', {
            'HUBSPOT_ACCESS_TOKEN': 'test-token',
            'HUBSPOT_FROM_EMAIL': 'noreply@sophia-ai.com'
        }):
            with patch('aiohttp.ClientSession') as mock_session:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json = AsyncMock(return_value=email_response)
                mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
                
                result = await business_master.send_automated_email(
                    recipient_email="test@example.com",
                    subject="Test Email",
                    content="<p>Hello from SOPHIA!</p>",
                    personalization={"first_name": "John"}
                )
                
                assert result["statusId"] == "SENT"
                assert len(business_master.action_history) == 1
                action = business_master.action_history[0]
                assert action["action_type"] == "send_email"
                assert action["details"]["recipient"] == "test@example.com"
                assert action["details"]["has_personalization"] is True
    
    @pytest.mark.asyncio
    async def test_send_automated_email_no_service(self, business_master):
        """Test automated email without configured service."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(RuntimeError, match="No email service configured"):
                await business_master.send_automated_email(
                    recipient_email="test@example.com",
                    subject="Test Email",
                    content="Hello!"
                )
    
    @pytest.mark.asyncio
    async def test_action_logging(self, business_master):
        """Test action logging functionality."""
        # Test successful action logging
        await business_master._log_action(
            action_type="test_action",
            service="test_service",
            details={"key": "value"},
            success=True
        )
        
        assert len(business_master.action_history) == 1
        action = business_master.action_history[0]
        assert action["action_type"] == "test_action"
        assert action["service"] == "test_service"
        assert action["details"]["key"] == "value"
        assert action["success"] is True
        assert "timestamp" in action
    
    @pytest.mark.asyncio
    async def test_action_logging_with_mcp(self, business_master):
        """Test action logging with MCP storage."""
        mock_mcp_client = AsyncMock()
        
        with patch.object(business_master, '_get_mcp_client', return_value=mock_mcp_client):
            await business_master._log_action(
                action_type="test_action",
                service="test_service",
                details={"key": "value"}
            )
            
            # Verify MCP client was called
            mock_mcp_client.store_context.assert_called_once()
            call_args = mock_mcp_client.store_context.call_args
            assert call_args[1]["context_type"] == "business_action"
            assert "business" in call_args[1]["tags"]
            assert "action" in call_args[1]["tags"]


class TestBusinessActionIntegration:
    """Integration tests for business actions."""
    
    @pytest.mark.asyncio
    async def test_slack_hubspot_workflow(self, business_master):
        """Test workflow combining Slack and HubSpot actions."""
        # Mock responses
        slack_response = {"ok": True, "ts": "1234567890.123456"}
        hubspot_response = {"id": "12345", "properties": {"firstname": "John"}}
        
        with patch.dict('os.environ', {
            'SLACK_BOT_TOKEN': 'slack-token',
            'HUBSPOT_ACCESS_TOKEN': 'hubspot-token'
        }):
            with patch('aiohttp.ClientSession') as mock_session:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json = AsyncMock(side_effect=[slack_response, hubspot_response])
                mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
                mock_session.return_value.__aenter__.return_value.patch.return_value.__aenter__.return_value = mock_response
                
                # Post to Slack
                slack_result = await business_master.post_slack_message(
                    channel="#sales",
                    message="New lead: John Doe"
                )
                
                # Update HubSpot contact
                hubspot_result = await business_master.update_hubspot_contact(
                    contact_id="12345",
                    properties={"lead_source": "slack_notification"}
                )
                
                assert slack_result["ok"] is True
                assert hubspot_result["id"] == "12345"
                assert len(business_master.action_history) == 2
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, business_master):
        """Test error handling and recovery in action workflows."""
        with patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'test-token'}):
            with patch('aiohttp.ClientSession') as mock_session:
                # First call fails
                mock_response_fail = AsyncMock()
                mock_response_fail.json = AsyncMock(return_value={"ok": False, "error": "rate_limited"})
                
                # Second call succeeds
                mock_response_success = AsyncMock()
                mock_response_success.json = AsyncMock(return_value={"ok": True, "ts": "1234567890.123456"})
                
                mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response_fail
                
                # First attempt should fail
                with pytest.raises(RuntimeError, match="Slack API error: rate_limited"):
                    await business_master.post_slack_message(
                        channel="#general",
                        message="Test message"
                    )
                
                # Verify failure was logged
                assert len(business_master.action_history) == 1
                assert business_master.action_history[0]["success"] is False
                
                # Second attempt should succeed
                mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response_success
                
                result = await business_master.post_slack_message(
                    channel="#general",
                    message="Test message retry"
                )
                
                assert result["ok"] is True
                assert len(business_master.action_history) == 2
                assert business_master.action_history[1]["success"] is True

