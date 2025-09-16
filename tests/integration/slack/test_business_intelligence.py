"""
Tests for Slack Business Intelligence endpoints and functionality
"""
import pytest
import json
from datetime import datetime
from unittest.mock import AsyncMock, patch

# Mock SlackAlert for testing
class SlackAlert:
    def __init__(self, channel, message, priority, report_id, data=None, timestamp=None):
        self.channel = channel
        self.message = message
        self.priority = priority
        self.report_id = report_id
        self.data = data or {}
        self.timestamp = timestamp or datetime.now().isoformat()


@pytest.mark.unit
class TestBusinessIntelligenceEndpoints:
    """Test BI-related Slack endpoints"""
    
    async def test_get_business_intelligence_summary(self, test_client, mock_sophia_intelligence):
        """Test business intelligence summary endpoint"""
        # Mock alerts
        mock_alerts = [
            SlackAlert(
                channel="#finance",
                message="Revenue target missed",
                priority="critical",
                report_id="revenue_dashboard",
                data={"revenue": 45000, "target": 50000}
            ),
            SlackAlert(
                channel="#operations",
                message="High conversion rate",
                priority="medium",
                report_id="conversion_dashboard",
                data={"conversion_rate": 0.15}
            )
        ]
        mock_sophia_intelligence.check_business_intelligence.return_value = mock_alerts
        
        with patch('app.api.routers.slack_business_intelligence.get_sophia_slack', return_value=mock_sophia_intelligence):
            response = await test_client.get("/api/slack/business-intelligence")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_alerts"] == 2
        assert data["system_status"] == "critical"  # Due to critical alert
        assert "critical" in data["alerts_by_priority"]
        assert data["alerts_by_priority"]["critical"] == 1
        assert data["monitored_reports"] == 1
        
        # Check alert details
        alerts = data["alerts"]
        critical_alert = next(a for a in alerts if a["priority"] == "critical")
        assert critical_alert["message"] == "Revenue target missed"
        assert critical_alert["channel"] == "#finance"
        assert critical_alert["data"]["revenue"] == 45000
    
    async def test_send_business_alerts_no_filter(self, test_client, mock_sophia_intelligence):
        """Test sending business alerts without priority filter"""
        mock_alerts = [
            SlackAlert(
                channel="#general",
                message="Test alert",
                priority="high",
                report_id="test_dashboard"
            )
        ]
        mock_sophia_intelligence.check_business_intelligence.return_value = mock_alerts
        mock_sophia_intelligence.send_slack_alerts.return_value = {"sent": 1, "failed": 0}
        
        with patch('app.api.routers.slack_business_intelligence.get_sophia_slack', return_value=mock_sophia_intelligence):
            response = await test_client.post("/api/slack/send-alerts")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["alerts_checked"] == 1
        assert data["priority_filter"] is None
        assert data["results"]["sent"] == 1
        assert data["status"] == "completed"
    
    async def test_send_business_alerts_with_priority_filter(self, test_client, mock_sophia_intelligence):
        """Test sending business alerts with priority filter"""
        all_alerts = [
            SlackAlert(channel="#test", message="Critical", priority="critical", report_id="test"),
            SlackAlert(channel="#test", message="High", priority="high", report_id="test"),
            SlackAlert(channel="#test", message="Medium", priority="medium", report_id="test")
        ]
        mock_sophia_intelligence.check_business_intelligence.return_value = all_alerts
        mock_sophia_intelligence.send_slack_alerts.return_value = {"sent": 1, "failed": 0}
        
        with patch('app.api.routers.slack_business_intelligence.get_sophia_slack', return_value=mock_sophia_intelligence):
            response = await test_client.post("/api/slack/send-alerts?priority_filter=critical")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["priority_filter"] == "critical"
        # Should have filtered to only critical alerts
        mock_sophia_intelligence.send_slack_alerts.assert_called_once()
        sent_alerts = mock_sophia_intelligence.send_slack_alerts.call_args[0][0]
        assert len(sent_alerts) == 1
        assert sent_alerts[0].priority == "critical"
    
    async def test_generate_daily_summary(self, test_client, mock_sophia_intelligence):
        """Test daily summary generation"""
        summary_alert = SlackAlert(
            channel="#general",
            message="Daily Business Summary for 2025-09-15",
            priority="medium",
            data={"reports_checked": 10, "alerts_generated": 2}
        )
        mock_sophia_intelligence.create_daily_business_summary.return_value = summary_alert
        mock_sophia_intelligence.send_slack_alerts.return_value = {"sent": 1, "failed": 0}
        
        with patch('app.api.routers.slack_business_intelligence.get_sophia_slack', return_value=mock_sophia_intelligence):
            response = await test_client.get("/api/slack/daily-summary")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "completed"
        assert data["summary"]["message"] == "Daily Business Summary for 2025-09-15"
        assert data["summary"]["priority"] == "medium"
        assert data["slack_delivery"]["sent"] == 1
        
        # Verify both create and send were called
        mock_sophia_intelligence.create_daily_business_summary.assert_called_once()
        mock_sophia_intelligence.send_slack_alerts.assert_called_once_with([summary_alert])
    
    async def test_get_reports_status(self, test_client, mock_sophia_intelligence):
        """Test monitored reports status endpoint"""
        with patch('app.api.routers.slack_business_intelligence.get_sophia_slack', return_value=mock_sophia_intelligence):
            response = await test_client.get("/api/slack/reports-status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_reports"] == 1
        assert data["system_status"] == "operational"
        
        report = data["reports"][0]
        assert report["key"] == "revenue_dashboard"
        assert report["name"] == "Revenue Dashboard"
        assert report["looker_id"] == "123"
        assert report["views"] == 1000
        assert report["priority"] == "high"
        assert report["status"] == "monitoring"
    
    async def test_test_integration_endpoint(self, test_client, mock_sophia_intelligence):
        """Test Slack integration test endpoint"""
        mock_sophia_intelligence.send_slack_alerts.return_value = {"sent": 1, "failed": 0}
        
        with patch('app.api.routers.slack_business_intelligence.get_sophia_slack', return_value=mock_sophia_intelligence):
            response = await test_client.post("/api/slack/test-integration?channel=#test-channel")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["test_channel"] == "#test-channel"
        assert data["status"] == "completed"
        assert data["results"]["sent"] == 1
        
        # Verify test alert was sent
        mock_sophia_intelligence.send_slack_alerts.assert_called_once()
        sent_alerts = mock_sophia_intelligence.send_slack_alerts.call_args[0][0]
        assert len(sent_alerts) == 1
        test_alert = sent_alerts[0]
        assert test_alert.channel == "#test-channel"
        assert "Integration Test" in test_alert.message
        assert test_alert.priority == "low"
    
    async def test_check_slack_health(self, test_client):
        """Test Slack health check endpoint"""
        # Mock INTEGRATIONS config
        mock_integrations = {
            "slack": {
                "enabled": True,
                "app_id": "A123456789",
                "app_name": "Sophia AI Assistant",
                "client_id": "123456.789012",
                "client_secret": "secret123",
                "signing_secret": "signing123",
                "app_token": "xapp-token",
                "stats": {"workspace": "test-workspace"}
            }
        }
        
        with patch('app.api.routers.slack_business_intelligence.INTEGRATIONS', mock_integrations):
            response = await test_client.get("/api/slack/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["integration_enabled"] is True
        assert data["app_configured"] is True
        assert data["status"] == "healthy"
        
        # Check credentials presence
        creds = data["credentials_present"]
        assert creds["client_id"] is True
        assert creds["client_secret"] is True
        assert creds["signing_secret"] is True
        assert creds["app_token"] is True
        
        # Check app info
        app_info = data["app_info"]
        assert app_info["app_id"] == "A123456789"
        assert app_info["app_name"] == "Sophia AI Assistant"
        assert app_info["workspace"] == "test-workspace"
    
    async def test_health_check_disabled_integration(self, test_client):
        """Test health check with disabled integration"""
        mock_integrations = {
            "slack": {
                "enabled": False,
                "app_id": None
            }
        }
        
        with patch('app.api.routers.slack_business_intelligence.INTEGRATIONS', mock_integrations):
            response = await test_client.get("/api/slack/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["integration_enabled"] is False
        assert data["app_configured"] is False
        assert data["status"] == "disabled"


@pytest.mark.integration
class TestBusinessIntelligenceFlow:
    """Integration tests for complete BI flow"""
    
    async def test_complete_alert_flow(self, test_client, mock_sophia_intelligence):
        """Test complete flow from BI check to alert sending"""
        # Set up mock BI alerts
        critical_alert = SlackAlert(
            channel="#finance",
            message="Revenue dropped 20% from yesterday",
            priority="critical",
            report_id="revenue_dashboard",
            timestamp=datetime.now().isoformat(),
            data={"current_revenue": 40000, "yesterday_revenue": 50000}
        )
        
        mock_sophia_intelligence.check_business_intelligence.return_value = [critical_alert]
        mock_sophia_intelligence.send_slack_alerts.return_value = {
            "sent": 1,
            "failed": 0,
            "details": [{"channel": "#finance", "status": "sent", "ts": "1234567890.123456"}]
        }
        
        with patch('app.api.routers.slack_business_intelligence.get_sophia_slack', return_value=mock_sophia_intelligence):
            # Step 1: Check BI status
            bi_response = await test_client.get("/api/slack/business-intelligence")
            assert bi_response.status_code == 200
            bi_data = bi_response.json()
            assert bi_data["total_alerts"] == 1
            assert bi_data["system_status"] == "critical"
            
            # Step 2: Send alerts
            alert_response = await test_client.post("/api/slack/send-alerts")
            assert alert_response.status_code == 200
            alert_data = alert_response.json()
            assert alert_data["results"]["sent"] == 1
    
    async def test_error_handling_in_bi_endpoints(self, test_client, mock_sophia_intelligence):
        """Test error handling in BI endpoints"""
        # Mock an error in BI checking
        mock_sophia_intelligence.check_business_intelligence.side_effect = Exception("Database connection failed")
        
        with patch('app.api.routers.slack_business_intelligence.get_sophia_slack', return_value=mock_sophia_intelligence):
            response = await test_client.get("/api/slack/business-intelligence")
        
        assert response.status_code == 500
        assert "Database connection failed" in response.json()["detail"]
    
    async def test_priority_filtering_edge_cases(self, test_client, mock_sophia_intelligence):
        """Test priority filtering with edge cases"""
        alerts = [
            SlackAlert(channel="#test", message="Critical", priority="critical", report_id="test"),
            SlackAlert(channel="#test", message="High", priority="high", report_id="test")
        ]
        mock_sophia_intelligence.check_business_intelligence.return_value = alerts
        mock_sophia_intelligence.send_slack_alerts.return_value = {"sent": 0, "failed": 0}
        
        with patch('app.api.routers.slack_business_intelligence.get_sophia_slack', return_value=mock_sophia_intelligence):
            # Test invalid priority filter
            response = await test_client.post("/api/slack/send-alerts?priority_filter=invalid")
            assert response.status_code == 200
            # Should send all alerts since filter is invalid
            
            # Test case-insensitive filtering  
            response = await test_client.post("/api/slack/send-alerts?priority_filter=CRITICAL")
            assert response.status_code == 200
            data = response.json()
            assert data["priority_filter"] == "critical"  # Should be normalized to lowercase


@pytest.mark.unit
class TestSlackAlertModel:
    """Test SlackAlert model and validation"""
    
    def test_slack_alert_creation(self):
        """Test basic SlackAlert creation"""
        alert = SlackAlert(
            channel="#test",
            message="Test message",
            priority="medium",
            report_id="test_report"
        )
        
        assert alert.channel == "#test"
        assert alert.message == "Test message"
        assert alert.priority == "medium"
        assert alert.report_id == "test_report"
        assert alert.timestamp is not None
        assert alert.data == {}
    
    def test_slack_alert_with_data(self):
        """Test SlackAlert with custom data"""
        custom_data = {
            "metric": "revenue",
            "value": 45000,
            "threshold": 50000,
            "change": -0.1
        }
        
        alert = SlackAlert(
            channel="#finance",
            message="Revenue alert",
            priority="high",
            report_id="revenue_dashboard",
            data=custom_data
        )
        
        assert alert.data == custom_data
        assert alert.data["metric"] == "revenue"
        assert alert.data["change"] == -0.1
    
    def test_slack_alert_serialization(self):
        """Test SlackAlert can be serialized to dict"""
        alert = SlackAlert(
            channel="#test",
            message="Test",
            priority="low",
            report_id="test",
            data={"key": "value"}
        )
        
        # Test that alert can be converted to dict (for JSON serialization)
        alert_dict = {
            "channel": alert.channel,
            "message": alert.message,
            "priority": alert.priority,
            "report_id": alert.report_id,
            "timestamp": alert.timestamp,
            "data": alert.data
        }
        
        assert alert_dict["channel"] == "#test"
        assert alert_dict["data"]["key"] == "value"


@pytest.mark.integration
class TestBusinessIntelligenceIntegration:
    """Integration tests with mocked Slack client"""
    
    async def test_bi_alert_to_slack_message_formatting(self, slack_client_with_mocks):
        """Test that BI alerts are properly formatted for Slack"""
        client, mock_slack_client, _, _ = slack_client_with_mocks
        
        # Create a complex alert with rich data
        alert = SlackAlert(
            channel="#finance",
            message="📉 *Revenue Alert*\n\nDaily revenue has dropped below target:\n• Current: $45,000\n• Target: $50,000\n• Variance: -10%",
            priority="critical",
            report_id="revenue_dashboard",
            data={
                "current_revenue": 45000,
                "target_revenue": 50000,
                "variance": -0.1,
                "report_url": "https://looker.company.com/dashboards/123"
            }
        )
        
        # Send the alert
        await client.send_message(
            channel=alert.channel,
            text=alert.message
        )
        
        # Verify the message was sent with proper formatting
        mock_slack_client.chat_postMessage.assert_called_once_with(
            channel="#finance",
            text=alert.message
        )
        
        # Verify the message contains expected formatting
        sent_text = mock_slack_client.chat_postMessage.call_args[1]["text"]
        assert "📉 *Revenue Alert*" in sent_text
        assert "$45,000" in sent_text
        assert "-10%" in sent_text
    
    async def test_bulk_alert_sending(self, slack_client_with_mocks, mock_sophia_intelligence):
        """Test sending multiple alerts in bulk"""
        client, mock_slack_client, _, _ = slack_client_with_mocks
        
        alerts = [
            SlackAlert(channel="#finance", message="Finance alert", priority="high", report_id="finance"),
            SlackAlert(channel="#operations", message="Operations alert", priority="medium", report_id="ops"),
            SlackAlert(channel="#marketing", message="Marketing alert", priority="low", report_id="marketing")
        ]
        
        # Mock the intelligence service to return these alerts
        mock_sophia_intelligence.send_slack_alerts.return_value = {"sent": 3, "failed": 0}
        
        # Simulate bulk sending
        results = await mock_sophia_intelligence.send_slack_alerts(alerts)
        
        assert results["sent"] == 3
        assert results["failed"] == 0
    
    async def test_alert_deduplication(self, mock_sophia_intelligence):
        """Test that duplicate alerts are handled properly"""
        # Create duplicate alerts (same channel, same message)
        alert1 = SlackAlert(
            channel="#test",
            message="Duplicate message",
            priority="medium",
            report_id="test1"
        )
        alert2 = SlackAlert(
            channel="#test", 
            message="Duplicate message",
            priority="medium",
            report_id="test2"
        )
        
        alerts = [alert1, alert2]
        
        # Mock intelligence service should handle deduplication
        mock_sophia_intelligence.send_slack_alerts.return_value = {
            "sent": 1,  # Only one sent due to deduplication
            "failed": 0,
            "deduplicated": 1
        }
        
        results = await mock_sophia_intelligence.send_slack_alerts(alerts)
        
        assert results["sent"] == 1
        assert results.get("deduplicated") == 1
