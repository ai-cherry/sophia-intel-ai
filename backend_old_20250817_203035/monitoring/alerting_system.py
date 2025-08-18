"""
Comprehensive Alerting System for SOPHIA Intel
Multi-channel alerting with intelligent escalation
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import aiohttp
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import sentry_sdk

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertChannel(Enum):
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"
    WEBHOOK = "webhook"
    SENTRY = "sentry"
    SMS = "sms"

class AlertStatus(Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    condition: str
    severity: AlertSeverity
    channels: List[AlertChannel]
    threshold: float
    duration: int  # seconds
    cooldown: int = 300  # 5 minutes default
    escalation_time: int = 1800  # 30 minutes
    enabled: bool = True
    tags: Dict[str, str] = None

@dataclass
class Alert:
    """Alert instance"""
    id: str
    rule_name: str
    severity: AlertSeverity
    title: str
    description: str
    timestamp: float
    status: AlertStatus = AlertStatus.ACTIVE
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[float] = None
    resolved_at: Optional[float] = None
    metadata: Dict[str, Any] = None
    escalation_level: int = 0

class AlertingSystem:
    """Comprehensive alerting system with multiple channels"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.alert_rules = self._initialize_alert_rules()
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.suppression_rules: List[Dict[str, Any]] = []
        
        # Channel configurations
        self.email_config = config.get("email", {})
        self.slack_config = config.get("slack", {})
        self.discord_config = config.get("discord", {})
        self.sms_config = config.get("sms", {})
        
        logger.info("Alerting System initialized")
    
    def _initialize_alert_rules(self) -> List[AlertRule]:
        """Initialize default alert rules"""
        return [
            # System Performance Alerts
            AlertRule(
                name="high_response_time",
                condition="avg_response_time > threshold",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
                threshold=2.0,  # 2 seconds
                duration=300,   # 5 minutes
                cooldown=600,   # 10 minutes
                tags={"category": "performance", "component": "api"}
            ),
            AlertRule(
                name="critical_response_time",
                condition="avg_response_time > threshold",
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.SLACK, AlertChannel.EMAIL, AlertChannel.SMS],
                threshold=5.0,  # 5 seconds
                duration=180,   # 3 minutes
                cooldown=300,   # 5 minutes
                escalation_time=900,  # 15 minutes
                tags={"category": "performance", "component": "api"}
            ),
            
            # Error Rate Alerts
            AlertRule(
                name="high_error_rate",
                condition="error_rate > threshold",
                severity=AlertSeverity.ERROR,
                channels=[AlertChannel.SLACK, AlertChannel.SENTRY],
                threshold=0.05,  # 5%
                duration=300,    # 5 minutes
                cooldown=600,    # 10 minutes
                tags={"category": "reliability", "component": "api"}
            ),
            AlertRule(
                name="critical_error_rate",
                condition="error_rate > threshold",
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.SLACK, AlertChannel.EMAIL, AlertChannel.SENTRY],
                threshold=0.15,  # 15%
                duration=120,    # 2 minutes
                cooldown=300,    # 5 minutes
                escalation_time=600,  # 10 minutes
                tags={"category": "reliability", "component": "api"}
            ),
            
            # Infrastructure Alerts
            AlertRule(
                name="lambda_server_down",
                condition="lambda_server_health == false",
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.SLACK, AlertChannel.EMAIL, AlertChannel.SMS],
                threshold=1,
                duration=60,     # 1 minute
                cooldown=300,    # 5 minutes
                escalation_time=600,  # 10 minutes
                tags={"category": "infrastructure", "component": "lambda_labs"}
            ),
            AlertRule(
                name="database_connection_failure",
                condition="database_health == false",
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.SLACK, AlertChannel.EMAIL, AlertChannel.SENTRY],
                threshold=1,
                duration=30,     # 30 seconds
                cooldown=180,    # 3 minutes
                escalation_time=300,  # 5 minutes
                tags={"category": "infrastructure", "component": "database"}
            ),
            
            # Resource Usage Alerts
            AlertRule(
                name="high_memory_usage",
                condition="memory_usage > threshold",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.SLACK],
                threshold=0.85,  # 85%
                duration=600,    # 10 minutes
                cooldown=1800,   # 30 minutes
                tags={"category": "resources", "component": "system"}
            ),
            AlertRule(
                name="disk_space_low",
                condition="disk_usage > threshold",
                severity=AlertSeverity.ERROR,
                channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
                threshold=0.90,  # 90%
                duration=300,    # 5 minutes
                cooldown=3600,   # 1 hour
                tags={"category": "resources", "component": "storage"}
            ),
            
            # AI/ML Specific Alerts
            AlertRule(
                name="ai_inference_failure",
                condition="ai_inference_success_rate < threshold",
                severity=AlertSeverity.ERROR,
                channels=[AlertChannel.SLACK, AlertChannel.SENTRY],
                threshold=0.95,  # 95%
                duration=300,    # 5 minutes
                cooldown=600,    # 10 minutes
                tags={"category": "ai", "component": "inference"}
            ),
            AlertRule(
                name="model_loading_failure",
                condition="model_load_failures > threshold",
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
                threshold=3,     # 3 failures
                duration=180,    # 3 minutes
                cooldown=300,    # 5 minutes
                tags={"category": "ai", "component": "models"}
            ),
            
            # Security Alerts
            AlertRule(
                name="authentication_failures",
                condition="auth_failure_rate > threshold",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.SLACK, AlertChannel.SENTRY],
                threshold=0.10,  # 10%
                duration=300,    # 5 minutes
                cooldown=600,    # 10 minutes
                tags={"category": "security", "component": "auth"}
            ),
            AlertRule(
                name="suspicious_activity",
                condition="suspicious_requests > threshold",
                severity=AlertSeverity.ERROR,
                channels=[AlertChannel.SLACK, AlertChannel.EMAIL, AlertChannel.SENTRY],
                threshold=50,    # 50 requests
                duration=300,    # 5 minutes
                cooldown=900,    # 15 minutes
                tags={"category": "security", "component": "requests"}
            )
        ]
    
    async def evaluate_alert_rules(self, metrics: Dict[str, Any]) -> List[Alert]:
        """Evaluate all alert rules against current metrics"""
        triggered_alerts = []
        
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            
            try:
                if await self._evaluate_rule_condition(rule, metrics):
                    alert = await self._create_alert(rule, metrics)
                    if alert:
                        triggered_alerts.append(alert)
            except Exception as e:
                logger.error(f"Error evaluating alert rule {rule.name}: {e}")
        
        return triggered_alerts
    
    async def _evaluate_rule_condition(self, rule: AlertRule, metrics: Dict[str, Any]) -> bool:
        """Evaluate if rule condition is met"""
        try:
            if rule.condition == "avg_response_time > threshold":
                return metrics.get("avg_response_time", 0) > rule.threshold
            elif rule.condition == "error_rate > threshold":
                return metrics.get("error_rate", 0) > rule.threshold
            elif rule.condition == "lambda_server_health == false":
                return not metrics.get("lambda_server_health", True)
            elif rule.condition == "database_health == false":
                return not metrics.get("database_health", True)
            elif rule.condition == "memory_usage > threshold":
                return metrics.get("memory_usage", 0) > rule.threshold
            elif rule.condition == "disk_usage > threshold":
                return metrics.get("disk_usage", 0) > rule.threshold
            elif rule.condition == "ai_inference_success_rate < threshold":
                return metrics.get("ai_inference_success_rate", 1.0) < rule.threshold
            elif rule.condition == "model_load_failures > threshold":
                return metrics.get("model_load_failures", 0) > rule.threshold
            elif rule.condition == "auth_failure_rate > threshold":
                return metrics.get("auth_failure_rate", 0) > rule.threshold
            elif rule.condition == "suspicious_requests > threshold":
                return metrics.get("suspicious_requests", 0) > rule.threshold
            else:
                logger.warning(f"Unknown condition: {rule.condition}")
                return False
        except Exception as e:
            logger.error(f"Error evaluating condition {rule.condition}: {e}")
            return False
    
    async def _create_alert(self, rule: AlertRule, metrics: Dict[str, Any]) -> Optional[Alert]:
        """Create alert if conditions are met"""
        # Check if alert is already active
        existing_alert = next((alert for alert in self.active_alerts.values() 
                             if alert.rule_name == rule.name and alert.status == AlertStatus.ACTIVE), None)
        
        if existing_alert:
            # Update existing alert
            existing_alert.timestamp = time.time()
            return None
        
        # Check cooldown period
        last_alert = next((alert for alert in reversed(self.alert_history) 
                          if alert.rule_name == rule.name), None)
        
        if last_alert and (time.time() - last_alert.timestamp) < rule.cooldown:
            return None
        
        # Create new alert
        alert_id = f"{rule.name}_{int(time.time())}"
        alert = Alert(
            id=alert_id,
            rule_name=rule.name,
            severity=rule.severity,
            title=self._generate_alert_title(rule, metrics),
            description=self._generate_alert_description(rule, metrics),
            timestamp=time.time(),
            metadata={"metrics": metrics, "rule": asdict(rule)}
        )
        
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Send alert notifications
        await self._send_alert_notifications(alert, rule)
        
        logger.info(f"Alert created: {alert.title} ({alert.id})")
        return alert
    
    def _generate_alert_title(self, rule: AlertRule, metrics: Dict[str, Any]) -> str:
        """Generate alert title"""
        titles = {
            "high_response_time": f"High Response Time: {metrics.get('avg_response_time', 0):.2f}s",
            "critical_response_time": f"CRITICAL Response Time: {metrics.get('avg_response_time', 0):.2f}s",
            "high_error_rate": f"High Error Rate: {metrics.get('error_rate', 0)*100:.1f}%",
            "critical_error_rate": f"CRITICAL Error Rate: {metrics.get('error_rate', 0)*100:.1f}%",
            "lambda_server_down": "Lambda Labs Server Down",
            "database_connection_failure": "Database Connection Failure",
            "high_memory_usage": f"High Memory Usage: {metrics.get('memory_usage', 0)*100:.1f}%",
            "disk_space_low": f"Low Disk Space: {metrics.get('disk_usage', 0)*100:.1f}%",
            "ai_inference_failure": f"AI Inference Failures: {metrics.get('ai_inference_success_rate', 1)*100:.1f}% success rate",
            "model_loading_failure": f"Model Loading Failures: {metrics.get('model_load_failures', 0)} failures",
            "authentication_failures": f"Authentication Failures: {metrics.get('auth_failure_rate', 0)*100:.1f}%",
            "suspicious_activity": f"Suspicious Activity: {metrics.get('suspicious_requests', 0)} requests"
        }
        
        return titles.get(rule.name, f"Alert: {rule.name}")
    
    def _generate_alert_description(self, rule: AlertRule, metrics: Dict[str, Any]) -> str:
        """Generate alert description"""
        base_description = f"Alert triggered for rule: {rule.name}\n"
        base_description += f"Severity: {rule.severity.value.upper()}\n"
        base_description += f"Threshold: {rule.threshold}\n"
        base_description += f"Current value: {metrics.get(rule.name.split('_')[0], 'N/A')}\n"
        base_description += f"Duration: {rule.duration}s\n"
        
        if rule.tags:
            base_description += f"Tags: {', '.join(f'{k}={v}' for k, v in rule.tags.items())}\n"
        
        return base_description
    
    async def _send_alert_notifications(self, alert: Alert, rule: AlertRule) -> None:
        """Send alert notifications to configured channels"""
        for channel in rule.channels:
            try:
                if channel == AlertChannel.EMAIL:
                    await self._send_email_alert(alert)
                elif channel == AlertChannel.SLACK:
                    await self._send_slack_alert(alert)
                elif channel == AlertChannel.DISCORD:
                    await self._send_discord_alert(alert)
                elif channel == AlertChannel.SENTRY:
                    await self._send_sentry_alert(alert)
                elif channel == AlertChannel.SMS:
                    await self._send_sms_alert(alert)
                elif channel == AlertChannel.WEBHOOK:
                    await self._send_webhook_alert(alert)
            except Exception as e:
                logger.error(f"Failed to send alert via {channel.value}: {e}")
    
    async def _send_email_alert(self, alert: Alert) -> None:
        """Send email alert"""
        if not self.email_config.get("enabled", False):
            return
        
        smtp_server = self.email_config.get("smtp_server")
        smtp_port = self.email_config.get("smtp_port", 587)
        username = self.email_config.get("username")
        password = self.email_config.get("password")
        from_email = self.email_config.get("from_email")
        to_emails = self.email_config.get("to_emails", [])
        
        if not all([smtp_server, username, password, from_email, to_emails]):
            logger.warning("Email configuration incomplete")
            return
        
        # Create email message
        msg = MimeMultipart()
        msg['From'] = from_email
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = f"[SOPHIA Intel] {alert.severity.value.upper()}: {alert.title}"
        
        body = f"""
SOPHIA Intel Alert

Title: {alert.title}
Severity: {alert.severity.value.upper()}
Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(alert.timestamp))}
Alert ID: {alert.id}

Description:
{alert.description}

Status: {alert.status.value}

---
This is an automated alert from SOPHIA Intel monitoring system.
        """.strip()
        
        msg.attach(MimeText(body, 'plain'))
        
        # Send email
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
            server.quit()
            logger.info(f"Email alert sent for {alert.id}")
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def _send_slack_alert(self, alert: Alert) -> None:
        """Send Slack alert"""
        webhook_url = self.slack_config.get("webhook_url")
        if not webhook_url:
            logger.warning("Slack webhook URL not configured")
            return
        
        # Determine color based on severity
        colors = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ff9500",
            AlertSeverity.ERROR: "#ff0000",
            AlertSeverity.CRITICAL: "#8B0000"
        }
        
        payload = {
            "username": "SOPHIA Intel",
            "icon_emoji": ":warning:",
            "attachments": [
                {
                    "color": colors.get(alert.severity, "#ff0000"),
                    "title": f"{alert.severity.value.upper()}: {alert.title}",
                    "text": alert.description,
                    "fields": [
                        {
                            "title": "Alert ID",
                            "value": alert.id,
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(alert.timestamp)),
                            "short": True
                        },
                        {
                            "title": "Status",
                            "value": alert.status.value,
                            "short": True
                        }
                    ],
                    "footer": "SOPHIA Intel Monitoring",
                    "ts": int(alert.timestamp)
                }
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status == 200:
                    logger.info(f"Slack alert sent for {alert.id}")
                else:
                    logger.error(f"Failed to send Slack alert: {response.status}")
    
    async def _send_discord_alert(self, alert: Alert) -> None:
        """Send Discord alert"""
        webhook_url = self.discord_config.get("webhook_url")
        if not webhook_url:
            logger.warning("Discord webhook URL not configured")
            return
        
        # Determine color based on severity
        colors = {
            AlertSeverity.INFO: 0x36a64f,
            AlertSeverity.WARNING: 0xff9500,
            AlertSeverity.ERROR: 0xff0000,
            AlertSeverity.CRITICAL: 0x8B0000
        }
        
        payload = {
            "username": "SOPHIA Intel",
            "embeds": [
                {
                    "title": f"{alert.severity.value.upper()}: {alert.title}",
                    "description": alert.description,
                    "color": colors.get(alert.severity, 0xff0000),
                    "fields": [
                        {
                            "name": "Alert ID",
                            "value": alert.id,
                            "inline": True
                        },
                        {
                            "name": "Time",
                            "value": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(alert.timestamp)),
                            "inline": True
                        },
                        {
                            "name": "Status",
                            "value": alert.status.value,
                            "inline": True
                        }
                    ],
                    "footer": {
                        "text": "SOPHIA Intel Monitoring"
                    },
                    "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(alert.timestamp))
                }
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status in [200, 204]:
                    logger.info(f"Discord alert sent for {alert.id}")
                else:
                    logger.error(f"Failed to send Discord alert: {response.status}")
    
    async def _send_sentry_alert(self, alert: Alert) -> None:
        """Send Sentry alert"""
        try:
            with sentry_sdk.push_scope() as scope:
                scope.set_tag("alert_id", alert.id)
                scope.set_tag("alert_rule", alert.rule_name)
                scope.set_tag("severity", alert.severity.value)
                scope.set_level(alert.severity.value)
                
                if alert.metadata:
                    for key, value in alert.metadata.items():
                        scope.set_extra(key, value)
                
                sentry_sdk.capture_message(
                    f"Alert: {alert.title}",
                    level=alert.severity.value
                )
                
            logger.info(f"Sentry alert sent for {alert.id}")
        except Exception as e:
            logger.error(f"Failed to send Sentry alert: {e}")
    
    async def _send_sms_alert(self, alert: Alert) -> None:
        """Send SMS alert (placeholder - would integrate with SMS service)"""
        # This would integrate with services like Twilio, AWS SNS, etc.
        logger.info(f"SMS alert would be sent for {alert.id}")
    
    async def _send_webhook_alert(self, alert: Alert) -> None:
        """Send webhook alert"""
        webhook_url = self.config.get("webhook", {}).get("url")
        if not webhook_url:
            return
        
        payload = {
            "alert_id": alert.id,
            "rule_name": alert.rule_name,
            "severity": alert.severity.value,
            "title": alert.title,
            "description": alert.description,
            "timestamp": alert.timestamp,
            "status": alert.status.value,
            "metadata": alert.metadata
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status == 200:
                    logger.info(f"Webhook alert sent for {alert.id}")
                else:
                    logger.error(f"Failed to send webhook alert: {response.status}")
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        if alert_id not in self.active_alerts:
            return False
        
        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = time.time()
        
        logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
        return True
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        if alert_id not in self.active_alerts:
            return False
        
        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = time.time()
        
        # Remove from active alerts
        del self.active_alerts[alert_id]
        
        logger.info(f"Alert resolved: {alert_id}")
        return True
    
    async def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    async def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        return self.alert_history[-limit:]
    
    async def get_alert_statistics(self, time_range: int = 86400) -> Dict[str, Any]:
        """Get alert statistics for time range (seconds)"""
        cutoff_time = time.time() - time_range
        recent_alerts = [alert for alert in self.alert_history if alert.timestamp >= cutoff_time]
        
        severity_counts = {}
        for severity in AlertSeverity:
            severity_counts[severity.value] = len([a for a in recent_alerts if a.severity == severity])
        
        rule_counts = {}
        for alert in recent_alerts:
            rule_counts[alert.rule_name] = rule_counts.get(alert.rule_name, 0) + 1
        
        return {
            "time_range": time_range,
            "total_alerts": len(recent_alerts),
            "active_alerts": len(self.active_alerts),
            "severity_breakdown": severity_counts,
            "top_alert_rules": sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "average_resolution_time": self._calculate_average_resolution_time(recent_alerts)
        }
    
    def _calculate_average_resolution_time(self, alerts: List[Alert]) -> float:
        """Calculate average resolution time for alerts"""
        resolved_alerts = [a for a in alerts if a.resolved_at]
        if not resolved_alerts:
            return 0.0
        
        total_time = sum(a.resolved_at - a.timestamp for a in resolved_alerts)
        return total_time / len(resolved_alerts)

# Global alerting system
_alerting_system: Optional[AlertingSystem] = None

def get_alerting_system() -> AlertingSystem:
    """Get global alerting system"""
    if _alerting_system is None:
        raise RuntimeError("Alerting system not initialized")
    return _alerting_system

def initialize_alerting_system(config: Dict[str, Any]) -> AlertingSystem:
    """Initialize global alerting system"""
    global _alerting_system
    _alerting_system = AlertingSystem(config)
    return _alerting_system

