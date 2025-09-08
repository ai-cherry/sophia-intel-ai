"""
Slack Business Intelligence Router

Provides REST endpoints for Sophia AI-powered Slack integration
with Pay Ready's business intelligence and reporting systems.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from app.integrations.slack_intelligence import (
    SophiaSlackIntelligence,
    get_sophia_slack_intelligence,
)

logger = logging.getLogger(__name__)

# Provide a safe default for INTEGRATIONS if not imported from a central config
try:
    INTEGRATIONS  # type: ignore[name-defined]
except NameError:
    INTEGRATIONS = {}

router = APIRouter(prefix="/api/slack", tags=["slack", "business-intelligence", "sophia-ai"])


def get_sophia_slack() -> SophiaSlackIntelligence:
    """Dependency to get Sophia Slack Intelligence instance"""
    try:
        # Note: This would normally be async, but FastAPI dependencies need sync
        # In production, consider using a singleton pattern or dependency injection
        return SophiaSlackIntelligence()
    except Exception as e:
        logger.error(f"Failed to get Sophia Slack Intelligence: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Slack service unavailable: {str(e)}")


@router.post("/webhook", summary="Slack Events Webhook")
async def slack_webhook(request: Request):
    """
    Handle Slack events and slash commands from the Sophia AI Assistant app

    This endpoint receives webhooks from Slack when users interact with
    the Sophia AI Assistant through slash commands or app mentions.
    """
    try:
        # Parse request
        if request.headers.get("content-type") == "application/x-www-form-urlencoded":
            # Slash command
            form_data = await request.form()
            return await handle_slash_command(dict(form_data))
        else:
            # Event API
            body = await request.json()
            return await handle_slack_event(body)

    except Exception as e:
        logger.error(f"Slack webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_slash_command(form_data: dict[str, Any]) -> dict[str, Any]:
    """Handle Slack slash commands"""
    try:
        command = form_data.get("command", "")
        text = form_data.get("text", "")
        user_id = form_data.get("user_id", "")
        channel_id = form_data.get("channel_id", "")

        logger.info(f"Slash command received: {command} {text}")

        # Get Sophia Slack Intelligence
        sophia_slack = await get_sophia_slack_intelligence()

        # Handle the command
        full_command = f"{command} {text}".strip()
        response_text = await sophia_slack.handle_slack_command(full_command, user_id, channel_id)

        return {"response_type": "in_channel", "text": response_text}

    except Exception as e:
        logger.error(f"Slash command error: {str(e)}")
        return {
            "response_type": "ephemeral",
            "text": f"Sorry, I encountered an error: {str(e)[:100]}",
        }


async def handle_slack_event(event_data: dict[str, Any]) -> dict[str, Any]:
    """Handle Slack Event API events"""
    try:
        # Handle URL verification challenge
        if event_data.get("type") == "url_verification":
            return {"challenge": event_data.get("challenge")}

        # Handle actual events
        event = event_data.get("event", {})
        event_type = event.get("type")

        logger.info(f"Slack event received: {event_type}")

        if event_type == "app_mention":
            await handle_app_mention(event)
        elif event_type == "message":
            await handle_message_event(event)

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Event handling error: {str(e)}")
        return {"status": "error", "message": str(e)}


async def handle_app_mention(event: dict[str, Any]):
    """Handle when Sophia AI is mentioned in Slack"""
    try:
        text = event.get("text", "")
        user = event.get("user", "")
        channel = event.get("channel", "")

        sophia_slack = await get_sophia_slack_intelligence()

        # Extract command from mention
        # Example: "@sophia reports" -> "reports"
        command_text = text.replace("<@", "").split(">", 1)
        command = command_text[1].strip() if len(command_text) > 1 else "help"

        response = await sophia_slack.handle_slack_command(f"/sophia {command}", user, channel)

        # Send response back to channel (would need proper bot token)
        logger.info(f"App mention response: {response[:100]}...")

    except Exception as e:
        logger.error(f"App mention handling error: {str(e)}")


async def handle_message_event(event: dict[str, Any]):
    """Handle direct messages to Sophia AI"""
    try:
        # Filter out bot messages
        if event.get("bot_id"):
            return

        text = event.get("text", "")
        user = event.get("user", "")
        event.get("channel", "")

        logger.info(f"Direct message from {user}: {text[:50]}...")

        # For now, just log. In production, could trigger AI response

    except Exception as e:
        logger.error(f"Message event handling error: {str(e)}")


@router.get("/business-intelligence", summary="Get Business Intelligence Summary")
async def get_business_intelligence(
    sophia_slack: SophiaSlackIntelligence = Depends(get_sophia_slack),
) -> dict[str, Any]:
    """
    Get current business intelligence summary for Pay Ready's top reports

    Returns insights from the most used reports including alerts,
    metrics, and recommendations.
    """
    try:
        # Get current business intelligence
        alerts = await sophia_slack.check_business_intelligence()

        # Create summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_alerts": len(alerts),
            "alerts_by_priority": {},
            "monitored_reports": len(sophia_slack.monitored_reports),
            "system_status": "healthy",
            "alerts": [],
        }

        # Group alerts by priority
        for alert in alerts:
            priority = alert.priority
            if priority not in summary["alerts_by_priority"]:
                summary["alerts_by_priority"][priority] = 0
            summary["alerts_by_priority"][priority] += 1

            # Add alert details
            summary["alerts"].append(
                {
                    "priority": alert.priority,
                    "message": alert.message,
                    "channel": alert.channel,
                    "report_id": alert.report_id,
                    "timestamp": alert.timestamp,
                    "data": alert.data,
                }
            )

        # Determine overall system status
        if any(alert.priority == "critical" for alert in alerts):
            summary["system_status"] = "critical"
        elif any(alert.priority == "high" for alert in alerts):
            summary["system_status"] = "warning"

        return summary

    except Exception as e:
        logger.error(f"Business intelligence summary failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-alerts", summary="Send Business Intelligence Alerts")
async def send_business_alerts(
    priority_filter: Optional[str] = None,
    sophia_slack: SophiaSlackIntelligence = Depends(get_sophia_slack),
) -> dict[str, Any]:
    """
    Check business intelligence and send alerts to appropriate Slack channels

    Args:
        priority_filter: Optional filter for alert priority (critical, high, medium, low)

    Returns:
        Summary of alerts sent including success/failure counts
    """
    try:
        # Check business intelligence
        alerts = await sophia_slack.check_business_intelligence()

        # Filter alerts by priority if specified
        if priority_filter:
            priority_filter = priority_filter.lower()
            if priority_filter in ["critical", "high", "medium", "low"]:
                alerts = [a for a in alerts if a.priority == priority_filter]

        # Send alerts
        results = await sophia_slack.send_slack_alerts(alerts)

        return {
            "timestamp": datetime.now().isoformat(),
            "alerts_checked": len(alerts),
            "priority_filter": priority_filter,
            "results": results,
            "status": "completed",
        }

    except Exception as e:
        logger.error(f"Send business alerts failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily-summary", summary="Generate Daily Business Summary")
async def generate_daily_summary(
    sophia_slack: SophiaSlackIntelligence = Depends(get_sophia_slack),
) -> dict[str, Any]:
    """
    Generate and optionally send daily business intelligence summary

    Creates a comprehensive daily summary of Pay Ready's business
    intelligence including report statuses, key metrics, and insights.
    """
    try:
        # Generate daily summary
        summary_alert = await sophia_slack.create_daily_business_summary()

        # Optionally send to Slack
        send_results = await sophia_slack.send_slack_alerts([summary_alert])

        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "message": summary_alert.message,
                "priority": summary_alert.priority,
                "channel": summary_alert.channel,
                "data": summary_alert.data,
            },
            "slack_delivery": send_results,
            "status": "completed",
        }

    except Exception as e:
        logger.error(f"Daily summary generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports-status", summary="Get Monitored Reports Status")
async def get_reports_status(
    sophia_slack: SophiaSlackIntelligence = Depends(get_sophia_slack),
) -> dict[str, Any]:
    """
    Get status of all monitored Pay Ready reports

    Returns comprehensive status of the top business reports
    including view counts, monitoring frequency, and health status.
    """
    try:
        reports_status = []

        for report_key, config in sophia_slack.monitored_reports.items():
            status_info = {
                "key": report_key,
                "name": config["name"],
                "looker_id": config["looker_id"],
                "views": config["views"],
                "priority": config["priority"],
                "check_frequency": config["check_frequency"],
                "channels": config["channels"],
                "metrics": config["metrics"],
                "thresholds": config.get("thresholds", {}),
                "status": "monitoring",
            }
            reports_status.append(status_info)

        return {
            "timestamp": datetime.now().isoformat(),
            "total_reports": len(reports_status),
            "reports": sorted(reports_status, key=lambda x: x["views"], reverse=True),
            "system_status": "operational",
        }

    except Exception as e:
        logger.error(f"Reports status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-integration", summary="Test Slack Integration")
async def test_slack_integration(
    channel: str = "#general", sophia_slack: SophiaSlackIntelligence = Depends(get_sophia_slack)
) -> dict[str, Any]:
    """
    Test the Slack integration by sending a test message

    Args:
        channel: Slack channel to send test message to

    Returns:
        Test results including success/failure status
    """
    try:
        from app.integrations.slack_intelligence import SlackAlert

        # Create test alert
        test_alert = SlackAlert(
            channel=channel,
            message="🧪 **Sophia AI Integration Test**\\n\\nThis is a test message to verify the Slack integration is working properly.\\n\\n✅ If you see this message, the integration is successful!",
            priority="low",
            timestamp=datetime.now().isoformat(),
        )

        # Send test alert
        results = await sophia_slack.send_slack_alerts([test_alert])

        return {
            "timestamp": datetime.now().isoformat(),
            "test_channel": channel,
            "results": results,
            "status": "completed" if results.get("sent", 0) > 0 else "failed",
        }

    except Exception as e:
        logger.error(f"Slack integration test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="Check Slack Integration Health")
async def check_slack_health() -> dict[str, Any]:
    """
    Check the health status of the Slack integration

    Returns comprehensive health information including
    configuration status and connectivity.
    """
    try:
        slack_config = INTEGRATIONS.get("slack", {})

        health_status = {
            "timestamp": datetime.now().isoformat(),
            "integration_enabled": slack_config.get("enabled", False),
            "app_configured": bool(slack_config.get("app_id")),
            "credentials_present": {
                "client_id": bool(slack_config.get("client_id")),
                "client_secret": bool(slack_config.get("client_secret")),
                "signing_secret": bool(slack_config.get("signing_secret")),
                "app_token": bool(slack_config.get("app_token")),
            },
            "app_info": {
                "app_id": slack_config.get("app_id"),
                "app_name": slack_config.get("app_name"),
                "workspace": slack_config.get("stats", {}).get("workspace"),
            },
            "status": "healthy" if slack_config.get("enabled") else "disabled",
        }

        return health_status

    except Exception as e:
        logger.error(f"Slack health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
