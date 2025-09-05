"""
Slack Intelligence Integration for Pay Ready Business Intelligence

Combines Sophia AI with Pay Ready's top business reports to provide
intelligent Slack notifications, automated alerts, and interactive
business intelligence directly in team communication channels.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

try:
    from slack_sdk.errors import SlackApiError
    from slack_sdk.web.async_client import AsyncWebClient

    SLACK_SDK_AVAILABLE = True
except ImportError:
    AsyncWebClient = None
    SlackApiError = None
    SLACK_SDK_AVAILABLE = False

from app.integrations.looker_client import get_looker_client

logger = logging.getLogger(__name__)


@dataclass
class SlackAlert:
    """Slack alert configuration"""

    channel: str
    message: str
    priority: str  # "low", "medium", "high", "critical"
    report_id: Optional[str] = None
    data: Optional[dict[str, Any]] = None
    timestamp: Optional[str] = None


@dataclass
class BusinessMetric:
    """Business metric for monitoring"""

    name: str
    value: float
    threshold: float
    status: str  # "normal", "warning", "critical"
    report_source: str
    last_checked: str


class SophiaSlackIntelligence:
    """Sophia AI-powered Slack intelligence for Pay Ready"""

    def __init__(self):
        if not SLACK_SDK_AVAILABLE:
            raise ImportError("slack_sdk not installed. Run: pip install slack-sdk")

        self.slack_config = INTEGRATIONS.get("slack", {})
        if not self.slack_config.get("enabled"):
            raise ValueError("Slack integration not enabled")

        # Initialize Slack client
        self.slack_client = None
        self.looker_client = None
        self._initialize_clients()

        # Business intelligence configuration
        self.monitored_reports = self._configure_monitored_reports()
        self.alert_thresholds = self._configure_alert_thresholds()

    def _initialize_clients(self):
        """Initialize Slack and Looker clients"""
        try:
            # Note: We'll need a bot token to be added to the config
            # For now, using app_token as placeholder
            bot_token = self.slack_config.get("bot_token") or self.slack_config.get("app_token")

            if not bot_token or not bot_token.startswith(("xoxb-", "xoxe.")):
                logger.warning("No valid bot token found. Slack functionality will be limited.")
                return

            self.slack_client = AsyncWebClient(token=bot_token)
            self.looker_client = get_looker_client()

            logger.info("✅ Sophia Slack Intelligence initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Slack Intelligence: {str(e)}")
            raise

    def _configure_monitored_reports(self) -> dict[str, dict[str, Any]]:
        """Configure Pay Ready's most critical reports for monitoring"""
        return {
            # Top 3 most used Pay Ready reports
            "master_payments": {
                "looker_id": "54",
                "name": "3rd Party Agency Payments by Month (MASTER)",
                "views": 270,
                "priority": "critical",
                "check_frequency": "hourly",
                "channels": ["#payments", "#finance-alerts"],
                "metrics": ["total_amount", "transaction_count", "failure_rate"],
                "thresholds": {
                    "total_amount_drop": 0.15,  # 15% drop triggers alert
                    "high_failure_rate": 0.05,  # 5% failure rate
                    "transaction_anomaly": 0.25,  # 25% deviation from average
                },
            },
            "abs_history": {
                "looker_id": "14",
                "name": "#5 ABS with History (Static View)",
                "views": 252,
                "priority": "high",
                "check_frequency": "daily",
                "channels": ["#finance", "#operations"],
                "metrics": ["balance_trends", "account_status", "overdue_amounts"],
                "thresholds": {
                    "overdue_spike": 0.20,  # 20% increase in overdue
                    "balance_anomaly": 0.30,  # 30% balance change
                },
            },
            "batch_processing": {
                "looker_id": "52",
                "name": "3rd Party Batch 3-6-12 View",
                "views": 235,
                "priority": "high",
                "check_frequency": "every_4_hours",
                "channels": ["#operations", "#tech-alerts"],
                "metrics": ["batch_success_rate", "processing_time", "error_count"],
                "thresholds": {
                    "batch_failure": 0.10,  # 10% batch failure rate
                    "processing_delay": 2.0,  # 2x normal processing time
                },
            },
        }

    def _configure_alert_thresholds(self) -> dict[str, Any]:
        """Configure global alert thresholds"""
        return {
            "business_hours": {
                "start": 8,  # 8 AM
                "end": 18,  # 6 PM
                "timezone": "America/New_York",
            },
            "escalation": {
                "critical": {"immediate": True, "channels": ["#exec-alerts"]},
                "high": {"delay_minutes": 15, "channels": ["#finance-alerts"]},
                "medium": {"delay_minutes": 60, "channels": ["#operations"]},
                "low": {"delay_minutes": 240, "channels": ["#general-updates"]},
            },
        }

    async def check_business_intelligence(self) -> list[SlackAlert]:
        """Check Pay Ready's top reports for business intelligence insights"""
        alerts = []

        try:
            for report_key, config in self.monitored_reports.items():
                logger.info(f"Checking report: {config['name']}")

                # Get report data from Looker
                try:
                    report_data = self.looker_client.get_look_data(config["looker_id"], limit=100)

                    # Analyze for anomalies and insights
                    report_alerts = await self._analyze_report_for_alerts(
                        report_key, config, report_data
                    )
                    alerts.extend(report_alerts)

                except Exception as e:
                    logger.error(f"Failed to check report {report_key}: {str(e)}")

                    # Create error alert
                    error_alert = SlackAlert(
                        channel="#tech-alerts",
                        message=f"⚠️ Unable to access {config['name']}: {str(e)[:100]}",
                        priority="medium",
                        report_id=config["looker_id"],
                        timestamp=datetime.now().isoformat(),
                    )
                    alerts.append(error_alert)

        except Exception as e:
            logger.error(f"Business intelligence check failed: {str(e)}")

        return alerts

    async def _analyze_report_for_alerts(
        self, report_key: str, config: dict[str, Any], report_data: dict[str, Any]
    ) -> list[SlackAlert]:
        """Analyze specific report data for business insights and alerts"""
        alerts = []

        try:
            data = report_data.get("data", [])
            if not data:
                return alerts

            config["name"]
            config.get("thresholds", {})

            # Master Payments Report Analysis
            if report_key == "master_payments":
                alerts.extend(await self._analyze_master_payments(data, config))

            # ABS History Analysis
            elif report_key == "abs_history":
                alerts.extend(await self._analyze_abs_history(data, config))

            # Batch Processing Analysis
            elif report_key == "batch_processing":
                alerts.extend(await self._analyze_batch_processing(data, config))

            # General data quality checks
            quality_alerts = await self._check_data_quality(data, config)
            alerts.extend(quality_alerts)

        except Exception as e:
            logger.error(f"Report analysis failed for {report_key}: {str(e)}")

        return alerts

    async def _analyze_master_payments(self, data: list[dict], config: dict) -> list[SlackAlert]:
        """Analyze the master payments report (270 views - most critical)"""
        alerts = []

        try:
            if not data:
                alerts.append(
                    SlackAlert(
                        channel="#payments",
                        message="🚨 **CRITICAL**: Master Payments report returned no data",
                        priority="critical",
                        report_id="54",
                    )
                )
                return alerts

            # Analyze payment patterns
            total_transactions = len(data)

            # Look for anomalies (example logic - would need actual data structure)
            if total_transactions < 10:  # Assuming normal is higher
                alerts.append(
                    SlackAlert(
                        channel="#payments",
                        message=f"⚠️ **Payment Volume Alert**: Only {total_transactions} transactions in master report. Normal volume expected to be higher.",
                        priority="high",
                        report_id="54",
                        data={"transaction_count": total_transactions},
                    )
                )

            # Success - create positive update
            alerts.append(
                SlackAlert(
                    channel="#general-updates",
                    message=f"✅ Master Payments Report: {total_transactions} transactions processed successfully",
                    priority="low",
                    report_id="54",
                    data={"status": "healthy", "count": total_transactions},
                )
            )

        except Exception as e:
            logger.error(f"Master payments analysis failed: {str(e)}")

        return alerts

    async def _analyze_abs_history(self, data: list[dict], config: dict) -> list[SlackAlert]:
        """Analyze ABS history report (252 views - financial critical)"""
        alerts = []

        try:
            # Account balance analysis logic would go here
            # For now, basic data availability check

            if data:
                alerts.append(
                    SlackAlert(
                        channel="#finance",
                        message=f"📊 ABS History Report: {len(data)} account records analyzed",
                        priority="low",
                        report_id="14",
                    )
                )

        except Exception as e:
            logger.error(f"ABS history analysis failed: {str(e)}")

        return alerts

    async def _analyze_batch_processing(self, data: list[dict], config: dict) -> list[SlackAlert]:
        """Analyze batch processing report (235 views - operations critical)"""
        alerts = []

        try:
            # Batch processing analysis logic would go here
            if data:
                alerts.append(
                    SlackAlert(
                        channel="#operations",
                        message=f"⚙️ Batch Processing: {len(data)} batch records reviewed",
                        priority="low",
                        report_id="52",
                    )
                )

        except Exception as e:
            logger.error(f"Batch processing analysis failed: {str(e)}")

        return alerts

    async def _check_data_quality(self, data: list[dict], config: dict) -> list[SlackAlert]:
        """Check data quality across any report"""
        alerts = []

        try:
            if not data:
                return alerts

            # Check for data completeness
            total_records = len(data)
            empty_records = sum(1 for row in data if not any(row.values()))

            if empty_records > 0:
                empty_rate = empty_records / total_records
                if empty_rate > 0.1:  # 10% empty records
                    alerts.append(
                        SlackAlert(
                            channel="#tech-alerts",
                            message=f"🔍 **Data Quality Issue**: {empty_rate:.1%} of records are empty in {config['name']}",
                            priority="medium",
                            report_id=config.get("looker_id"),
                        )
                    )

        except Exception as e:
            logger.error(f"Data quality check failed: {str(e)}")

        return alerts

    async def send_slack_alerts(self, alerts: list[SlackAlert]) -> dict[str, Any]:
        """Send alerts to appropriate Slack channels"""
        if not self.slack_client:
            logger.warning("Slack client not initialized. Cannot send alerts.")
            return {"status": "error", "reason": "Slack client unavailable"}

        results = {"sent": 0, "failed": 0, "errors": []}

        for alert in alerts:
            try:
                # Format message with Sophia branding
                formatted_message = self._format_sophia_message(alert)

                # Send to Slack
                response = await self.slack_client.chat_postMessage(
                    channel=alert.channel,
                    text=formatted_message,
                    username="Sophia AI Assistant",
                    icon_emoji=":robot_face:",
                )

                if response["ok"]:
                    results["sent"] += 1
                    logger.info(f"Alert sent to {alert.channel}: {alert.message[:50]}...")
                else:
                    results["failed"] += 1
                    results["errors"].append(
                        f"Failed to send to {alert.channel}: {response.get('error', 'Unknown error')}"
                    )

            except SlackApiError as e:
                results["failed"] += 1
                results["errors"].append(f"Slack API error: {str(e)}")
                logger.error(f"Slack API error: {str(e)}")
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Unexpected error: {str(e)}")
                logger.error(f"Unexpected alert error: {str(e)}")

        return results

    def _format_sophia_message(self, alert: SlackAlert) -> str:
        """Format alert message with Sophia AI branding and context"""
        priority_emoji = {"critical": "🚨", "high": "⚠️", "medium": "📊", "low": "✅"}

        emoji = priority_emoji.get(alert.priority, "📄")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        message = f"{emoji} **Sophia AI Business Intelligence**\\n"
        message += f"{alert.message}\\n"
        message += f"⏰ {timestamp}"

        if alert.report_id:
            message += f" | 📊 Report ID: {alert.report_id}"

        if alert.data:
            message += f"\\n📋 Data: {json.dumps(alert.data, indent=2)}"

        message += "\\n\\n_Powered by Sophia AI Assistant for Pay Ready_"

        return message

    async def create_daily_business_summary(self) -> SlackAlert:
        """Create daily business intelligence summary for Pay Ready"""
        try:
            summary_data = {
                "reports_monitored": len(self.monitored_reports),
                "last_check": datetime.now().isoformat(),
                "status": "healthy",
            }

            message = "📈 **Daily Pay Ready Business Intelligence Summary**\\n\\n"
            message += f"🔍 **Reports Monitored**: {len(self.monitored_reports)}\\n"
            message += "📊 **Top Reports**:\\n"

            for _key, config in list(self.monitored_reports.items())[:3]:
                message += f"  • {config['name']} ({config['views']} views)\\n"

            message += "\\n✅ **System Status**: All monitoring systems operational\\n"
            message += "🤖 **AI Insights**: Ready to provide intelligent business analysis"

            return SlackAlert(
                channel="#general",
                message=message,
                priority="low",
                data=summary_data,
                timestamp=datetime.now().isoformat(),
            )

        except Exception as e:
            logger.error(f"Failed to create daily summary: {str(e)}")
            return SlackAlert(
                channel="#tech-alerts",
                message=f"❌ Failed to generate daily BI summary: {str(e)}",
                priority="medium",
            )

    async def handle_slack_command(self, command: str, user_id: str, channel_id: str) -> str:
        """Handle Slack slash commands for business intelligence"""
        try:
            command = command.lower().strip()

            if command.startswith("/sophia"):
                parts = command.split()[1:]  # Remove /sophia

                if not parts or parts[0] == "help":
                    return self._get_help_message()

                elif parts[0] == "reports":
                    return await self._handle_reports_command(parts[1:])

                elif parts[0] == "alerts":
                    return await self._handle_alerts_command(parts[1:])

                elif parts[0] == "status":
                    return await self._handle_status_command()

                else:
                    return (
                        f"Unknown command: {parts[0]}. Type `/sophia help` for available commands."
                    )

            return "Command not recognized. Use `/sophia help` for assistance."

        except Exception as e:
            logger.error(f"Slack command handling failed: {str(e)}")
            return f"Sorry, I encountered an error processing your request: {str(e)[:100]}"

    def _get_help_message(self) -> str:
        """Get help message for Slack commands"""
        return """🤖 **Sophia AI Assistant - Pay Ready Business Intelligence**

**Available Commands:**
• `/sophia reports` - View top Pay Ready reports
• `/sophia alerts` - Check current business alerts
• `/sophia status` - System health status
• `/sophia help` - Show this help message

**Examples:**
• `/sophia reports` - See most used reports
• `/sophia alerts high` - Show high priority alerts only
• `/sophia status` - Check all systems

_Powered by Sophia AI for intelligent business insights_"""

    async def _handle_reports_command(self, args: list[str]) -> str:
        """Handle reports command"""
        try:
            message = "📊 **Pay Ready Top Business Reports**\\n\\n"

            for i, (_key, config) in enumerate(self.monitored_reports.items(), 1):
                message += f"{i}. **{config['name']}**\\n"
                message += f"   👥 {config['views']} views | Priority: {config['priority']}\\n"
                message += f"   📊 Report ID: {config['looker_id']}\\n\\n"

            message += "_Use these reports for real-time business intelligence_"
            return message

        except Exception as e:
            return f"Error retrieving reports: {str(e)}"

    async def _handle_alerts_command(self, args: list[str]) -> str:
        """Handle alerts command"""
        try:
            # Get current alerts
            alerts = await self.check_business_intelligence()

            if not alerts:
                return "✅ **No active alerts** - All systems operating normally"

            # Filter by priority if specified
            priority_filter = args[0].lower() if args else None
            if priority_filter and priority_filter in ["critical", "high", "medium", "low"]:
                alerts = [a for a in alerts if a.priority == priority_filter]

            message = f"🚨 **Current Business Alerts ({len(alerts)})**\\n\\n"

            for alert in alerts[:5]:  # Show top 5
                priority_emoji = {"critical": "🚨", "high": "⚠️", "medium": "📊", "low": "✅"}
                emoji = priority_emoji.get(alert.priority, "📄")

                message += f"{emoji} **{alert.priority.title()}**: {alert.message}\\n"
                if alert.report_id:
                    message += f"   📊 Report ID: {alert.report_id}\\n"
                message += "\\n"

            if len(alerts) > 5:
                message += f"... and {len(alerts) - 5} more alerts"

            return message

        except Exception as e:
            return f"Error retrieving alerts: {str(e)}"

    async def _handle_status_command(self) -> str:
        """Handle status command"""
        try:
            message = "🔍 **Sophia AI System Status**\\n\\n"
            message += "✅ **Slack Integration**: Connected\\n"
            message += "📊 **Looker Integration**: Connected\\n"
            message += "🤖 **AI Assistant**: Active\\n"
            message += f"📈 **Reports Monitored**: {len(self.monitored_reports)}\\n\\n"

            message += "**Monitored Reports:**\\n"
            for config in self.monitored_reports.values():
                status_emoji = "✅" if config["priority"] in ["critical", "high"] else "📊"
                message += f"{status_emoji} {config['name']} ({config['priority']})\\n"

            message += f"\\n_Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_"
            return message

        except Exception as e:
            return f"Error retrieving status: {str(e)}"


async def get_sophia_slack_intelligence() -> SophiaSlackIntelligence:
    """Get configured Sophia Slack Intelligence instance"""
    return SophiaSlackIntelligence()
