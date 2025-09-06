"""
Enhanced Integration Connectors with Stuck Account Detection
Provides operational intelligence and stuck account detection for Asana, Linear, and Slack integrations
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from app.core.websocket_manager import WebSocketManager
from app.integrations.asana_client import AsanaClient
from app.integrations.linear_client import LinearClient
from app.integrations.slack_integration import SlackIntegration

logger = logging.getLogger(__name__)


class StuckAccountSeverity(Enum):
    """Severity levels for stuck account conditions"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StuckAccountType(Enum):
    """Types of stuck account conditions"""

    OVERDUE_TASKS = "overdue_tasks"
    NO_ACTIVITY = "no_activity"
    MISSED_DEADLINES = "missed_deadlines"
    LOW_VELOCITY = "low_velocity"
    BLOCKED_DEPENDENCIES = "blocked_dependencies"
    COMMUNICATION_GAP = "communication_gap"


@dataclass
class StuckAccountAlert:
    """Alert for stuck account condition"""

    account_id: str
    account_type: str  # "asana_project", "linear_issue", "slack_channel"
    alert_type: StuckAccountType
    severity: StuckAccountSeverity
    title: str
    description: str
    detected_at: datetime
    last_activity: Optional[datetime] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    recommended_actions: List[str] = field(default_factory=list)
    affected_stakeholders: List[str] = field(default_factory=list)


@dataclass
class OperationalIntelligence:
    """Operational intelligence insight"""

    insight_type: str
    title: str
    description: str
    confidence: float
    impact_score: float
    data: Dict[str, Any]
    recommendations: List[str]
    generated_at: datetime


class AsanaEnhancedConnector:
    """Enhanced Asana connector with stuck account detection"""

    def __init__(self, websocket_manager: WebSocketManager):
        self.asana_client = AsanaClient()
        self.websocket_manager = websocket_manager
        self.stuck_account_cache: Dict[str, StuckAccountAlert] = {}

    async def detect_stuck_accounts(self, workspace_gid: str) -> List[StuckAccountAlert]:
        """Detect stuck accounts across Asana projects and tasks"""
        alerts = []

        try:
            # Get all projects and analyze health
            projects = await self.asana_client.get_projects(workspace_gid)

            for project in projects:
                project_alerts = await self._analyze_project_for_stuck_conditions(project)
                alerts.extend(project_alerts)

                # Get project tasks and analyze
                tasks = await self.asana_client.get_project_tasks(project["gid"])
                task_alerts = await self._analyze_tasks_for_stuck_conditions(tasks, project)
                alerts.extend(task_alerts)

        except Exception as e:
            logger.error(f"Failed to detect stuck Asana accounts: {e}")

        # Broadcast new alerts
        for alert in alerts:
            if alert.account_id not in self.stuck_account_cache:
                await self._broadcast_stuck_account_alert(alert)
                self.stuck_account_cache[alert.account_id] = alert

        return alerts

    async def _analyze_project_for_stuck_conditions(
        self, project: Dict[str, Any]
    ) -> List[StuckAccountAlert]:
        """Analyze individual project for stuck conditions"""
        alerts = []
        now = datetime.utcnow()

        # Check for overdue projects
        if project.get("due_date"):
            due_date = datetime.fromisoformat(project["due_date"].replace("Z", "+00:00"))
            if due_date < now:
                days_overdue = (now - due_date).days

                severity = StuckAccountSeverity.LOW
                if days_overdue > 14:
                    severity = StuckAccountSeverity.CRITICAL
                elif days_overdue > 7:
                    severity = StuckAccountSeverity.HIGH
                elif days_overdue > 3:
                    severity = StuckAccountSeverity.MEDIUM

                alerts.append(
                    StuckAccountAlert(
                        account_id=f"asana_project_{project['gid']}",
                        account_type="asana_project",
                        alert_type=StuckAccountType.OVERDUE_TASKS,
                        severity=severity,
                        title=f"Overdue Project: {project['name']}",
                        description=f"Project is {days_overdue} days overdue",
                        detected_at=now,
                        metrics={"days_overdue": days_overdue, "due_date": project["due_date"]},
                        recommended_actions=[
                            "Review project timeline and dependencies",
                            "Reassign resources if needed",
                            "Update stakeholders on revised timeline",
                            "Break down remaining work into smaller tasks",
                        ],
                        affected_stakeholders=[
                            m.get("name", "Unknown") for m in project.get("members", [])
                        ],
                    )
                )

        # Check for projects without owners
        if not project.get("owner"):
            alerts.append(
                StuckAccountAlert(
                    account_id=f"asana_project_{project['gid']}",
                    account_type="asana_project",
                    alert_type=StuckAccountType.NO_ACTIVITY,
                    severity=StuckAccountSeverity.MEDIUM,
                    title=f"Unowned Project: {project['name']}",
                    description="Project has no assigned owner",
                    detected_at=now,
                    recommended_actions=[
                        "Assign project owner immediately",
                        "Review project priority and scope",
                        "Establish clear accountability",
                    ],
                )
            )

        return alerts

    async def _analyze_tasks_for_stuck_conditions(
        self, tasks: List[Dict[str, Any]], project: Dict[str, Any]
    ) -> List[StuckAccountAlert]:
        """Analyze tasks for stuck conditions"""
        alerts = []
        now = datetime.utcnow()

        for task in tasks:
            if task.get("completed"):
                continue

            # Check for overdue tasks
            if task.get("due_date"):
                due_date = datetime.fromisoformat(task["due_date"].replace("Z", "+00:00"))
                if due_date < now:
                    days_overdue = (now - due_date).days

                    severity = StuckAccountSeverity.LOW
                    if days_overdue > 7:
                        severity = StuckAccountSeverity.HIGH
                    elif days_overdue > 3:
                        severity = StuckAccountSeverity.MEDIUM

                    alerts.append(
                        StuckAccountAlert(
                            account_id=f"asana_task_{task['gid']}",
                            account_type="asana_task",
                            alert_type=StuckAccountType.OVERDUE_TASKS,
                            severity=severity,
                            title=f"Overdue Task: {task['name']}",
                            description=f"Task is {days_overdue} days overdue in project {project['name']}",
                            detected_at=now,
                            metrics={"days_overdue": days_overdue, "project": project["name"]},
                            recommended_actions=[
                                "Reassess task priority and deadline",
                                "Check for blockers with assignee",
                                "Consider breaking down into smaller subtasks",
                            ],
                            affected_stakeholders=[
                                task.get("assignee", {}).get("name", "Unassigned")
                            ],
                        )
                    )

            # Check for tasks with no recent activity
            if task.get("modified_at"):
                modified_date = datetime.fromisoformat(task["modified_at"].replace("Z", "+00:00"))
                days_since_activity = (now - modified_date).days

                if days_since_activity > 3 and not task.get("completed"):
                    severity = StuckAccountSeverity.LOW
                    if days_since_activity > 7:
                        severity = StuckAccountSeverity.MEDIUM

                    alerts.append(
                        StuckAccountAlert(
                            account_id=f"asana_task_{task['gid']}",
                            account_type="asana_task",
                            alert_type=StuckAccountType.NO_ACTIVITY,
                            severity=severity,
                            title=f"Stale Task: {task['name']}",
                            description=f"No activity for {days_since_activity} days",
                            detected_at=now,
                            last_activity=modified_date,
                            metrics={"days_since_activity": days_since_activity},
                            recommended_actions=[
                                "Check in with assignee on progress",
                                "Identify and remove blockers",
                                "Consider reassigning if needed",
                            ],
                        )
                    )

        return alerts

    async def _broadcast_stuck_account_alert(self, alert: StuckAccountAlert):
        """Broadcast stuck account alert via WebSocket"""
        await self.websocket_manager.broadcast_stuck_account_alert(
            alert.account_id,
            alert.alert_type.value,
            {
                "account_type": alert.account_type,
                "severity": alert.severity.value,
                "title": alert.title,
                "description": alert.description,
                "metrics": alert.metrics,
                "recommended_actions": alert.recommended_actions,
                "affected_stakeholders": alert.affected_stakeholders,
                "detected_at": alert.detected_at.isoformat(),
                "last_activity": alert.last_activity.isoformat() if alert.last_activity else None,
            },
        )


class LinearEnhancedConnector:
    """Enhanced Linear connector with stuck account detection"""

    def __init__(self, websocket_manager: WebSocketManager):
        self.linear_client = LinearClient()
        self.websocket_manager = websocket_manager
        self.velocity_history: Dict[str, List[Dict[str, Any]]] = {}

    async def detect_stuck_accounts(self) -> List[StuckAccountAlert]:
        """Detect stuck accounts in Linear issues and projects"""
        alerts = []

        try:
            # Get teams and analyze velocity
            teams = await self.linear_client.get_teams()

            for team in teams:
                team_alerts = await self._analyze_team_velocity(team)
                alerts.extend(team_alerts)

                # Get team issues and analyze
                issues = await self._get_team_issues(team["id"])
                issue_alerts = await self._analyze_issues_for_stuck_conditions(issues, team)
                alerts.extend(issue_alerts)

        except Exception as e:
            logger.error(f"Failed to detect stuck Linear accounts: {e}")

        return alerts

    async def _analyze_team_velocity(self, team: Dict[str, Any]) -> List[StuckAccountAlert]:
        """Analyze team velocity for stuck conditions"""
        alerts = []

        try:
            # Get team velocity data
            velocity_data = await self.linear_client.analyze_development_velocity()
            team_velocity = velocity_data.get("teams", {}).get(team["id"], {})

            current_velocity = team_velocity.get("current_velocity", 0)
            historical_avg = team_velocity.get("historical_average", 0)

            # Check for significant velocity drop
            if historical_avg > 0 and current_velocity < (historical_avg * 0.6):
                velocity_drop = ((historical_avg - current_velocity) / historical_avg) * 100

                alerts.append(
                    StuckAccountAlert(
                        account_id=f"linear_team_{team['id']}",
                        account_type="linear_team",
                        alert_type=StuckAccountType.LOW_VELOCITY,
                        severity=(
                            StuckAccountSeverity.HIGH
                            if velocity_drop > 50
                            else StuckAccountSeverity.MEDIUM
                        ),
                        title=f"Low Velocity: {team['name']}",
                        description=f"Team velocity dropped by {velocity_drop:.1f}% from historical average",
                        detected_at=datetime.utcnow(),
                        metrics={
                            "current_velocity": current_velocity,
                            "historical_average": historical_avg,
                            "velocity_drop_percent": velocity_drop,
                        },
                        recommended_actions=[
                            "Review team workload and capacity",
                            "Identify process bottlenecks",
                            "Check for team blockers or dependencies",
                            "Consider sprint planning adjustments",
                        ],
                    )
                )

        except Exception as e:
            logger.error(f"Failed to analyze team velocity: {e}")

        return alerts

    async def _get_team_issues(self, team_id: str) -> List[Dict[str, Any]]:
        """Get issues for a specific team"""
        # This would use Linear's GraphQL API to get team issues
        # For now, return empty list as placeholder
        return []

    async def _analyze_issues_for_stuck_conditions(
        self, issues: List[Dict[str, Any]], team: Dict[str, Any]
    ) -> List[StuckAccountAlert]:
        """Analyze Linear issues for stuck conditions"""
        alerts = []
        now = datetime.utcnow()

        for issue in issues:
            # Check for issues in "In Progress" state too long
            if issue.get("state", {}).get("type") == "started":
                updated_at = datetime.fromisoformat(issue["updatedAt"].replace("Z", "+00:00"))
                days_in_progress = (now - updated_at).days

                if days_in_progress > 5:
                    alerts.append(
                        StuckAccountAlert(
                            account_id=f"linear_issue_{issue['id']}",
                            account_type="linear_issue",
                            alert_type=StuckAccountType.NO_ACTIVITY,
                            severity=(
                                StuckAccountSeverity.MEDIUM
                                if days_in_progress > 7
                                else StuckAccountSeverity.LOW
                            ),
                            title=f"Stalled Issue: {issue['title']}",
                            description=f"Issue has been in progress for {days_in_progress} days with no updates",
                            detected_at=now,
                            last_activity=updated_at,
                            metrics={"days_in_progress": days_in_progress, "team": team["name"]},
                            recommended_actions=[
                                "Check with assignee on progress",
                                "Identify blockers or dependencies",
                                "Break down into smaller tasks if needed",
                            ],
                            affected_stakeholders=[
                                issue.get("assignee", {}).get("name", "Unassigned")
                            ],
                        )
                    )

        return alerts


class SlackEnhancedConnector:
    """Enhanced Slack connector with communication gap detection"""

    def __init__(self, websocket_manager: WebSocketManager):
        self.slack_client = SlackIntegration()
        self.websocket_manager = websocket_manager

    async def detect_communication_gaps(self) -> List[StuckAccountAlert]:
        """Detect communication gaps and inactive channels"""
        alerts = []

        try:
            # Get channels and analyze activity
            channels = await self._get_active_channels()

            for channel in channels:
                channel_alerts = await self._analyze_channel_activity(channel)
                alerts.extend(channel_alerts)

        except Exception as e:
            logger.error(f"Failed to detect Slack communication gaps: {e}")

        return alerts

    async def _get_active_channels(self) -> List[Dict[str, Any]]:
        """Get active Slack channels"""
        # Placeholder - would use Slack API to get channels
        return []

    async def _analyze_channel_activity(self, channel: Dict[str, Any]) -> List[StuckAccountAlert]:
        """Analyze channel for communication gaps"""
        alerts = []

        # This would analyze message frequency, response times,
        # and identify channels with significant communication gaps

        return alerts


class EnhancedIntegrationOrchestrator:
    """Orchestrator for enhanced integration connectors with operational intelligence"""

    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.asana_connector = AsanaEnhancedConnector(websocket_manager)
        self.linear_connector = LinearEnhancedConnector(websocket_manager)
        self.slack_connector = SlackEnhancedConnector(websocket_manager)

        # Operational intelligence cache
        self.intelligence_cache: List[OperationalIntelligence] = []

    async def run_stuck_account_detection(self) -> Dict[str, Any]:
        """Run comprehensive stuck account detection across all integrations"""
        logger.info("🔍 Running comprehensive stuck account detection...")

        start_time = datetime.utcnow()
        all_alerts = []

        try:
            # Run detection across all connectors in parallel
            detection_tasks = [
                self.asana_connector.detect_stuck_accounts(
                    "your_workspace_gid"
                ),  # Replace with actual workspace
                self.linear_connector.detect_stuck_accounts(),
                self.slack_connector.detect_communication_gaps(),
            ]

            results = await asyncio.gather(*detection_tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, list):
                    all_alerts.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Detection failed: {result}")

            # Generate operational intelligence
            intelligence = await self._generate_operational_intelligence(all_alerts)

            # Broadcast summary
            await self._broadcast_detection_summary(all_alerts, intelligence)

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            return {
                "status": "completed",
                "execution_time_seconds": execution_time,
                "total_alerts": len(all_alerts),
                "alerts_by_severity": self._group_alerts_by_severity(all_alerts),
                "alerts_by_type": self._group_alerts_by_type(all_alerts),
                "operational_intelligence": [intel.__dict__ for intel in intelligence],
                "timestamp": start_time.isoformat(),
            }

        except Exception as e:
            logger.error(f"Stuck account detection failed: {e}")
            return {"status": "failed", "error": str(e), "timestamp": start_time.isoformat()}

    async def _generate_operational_intelligence(
        self, alerts: List[StuckAccountAlert]
    ) -> List[OperationalIntelligence]:
        """Generate operational intelligence from stuck account alerts"""
        intelligence = []

        # Analyze alert patterns
        if len(alerts) > 5:
            intelligence.append(
                OperationalIntelligence(
                    insight_type="systemic_issues",
                    title="High Volume of Stuck Accounts Detected",
                    description=f"Detected {len(alerts)} stuck account conditions, indicating potential systemic issues",
                    confidence=0.8,
                    impact_score=0.9,
                    data={"alert_count": len(alerts)},
                    recommendations=[
                        "Review overall project management processes",
                        "Analyze resource allocation and capacity",
                        "Consider process automation opportunities",
                        "Implement proactive monitoring workflows",
                    ],
                    generated_at=datetime.utcnow(),
                )
            )

        # Analyze overdue task patterns
        overdue_alerts = [a for a in alerts if a.alert_type == StuckAccountType.OVERDUE_TASKS]
        if len(overdue_alerts) > 3:
            intelligence.append(
                OperationalIntelligence(
                    insight_type="deadline_management",
                    title="Recurring Deadline Misses",
                    description="Multiple overdue tasks detected across projects",
                    confidence=0.7,
                    impact_score=0.8,
                    data={"overdue_count": len(overdue_alerts)},
                    recommendations=[
                        "Review estimation and planning processes",
                        "Implement deadline buffer strategies",
                        "Strengthen dependency management",
                    ],
                    generated_at=datetime.utcnow(),
                )
            )

        # Store intelligence in cache
        self.intelligence_cache.extend(intelligence)

        return intelligence

    def _group_alerts_by_severity(self, alerts: List[StuckAccountAlert]) -> Dict[str, int]:
        """Group alerts by severity level"""
        severity_counts = {severity.value: 0 for severity in StuckAccountSeverity}
        for alert in alerts:
            severity_counts[alert.severity.value] += 1
        return severity_counts

    def _group_alerts_by_type(self, alerts: List[StuckAccountAlert]) -> Dict[str, int]:
        """Group alerts by type"""
        type_counts = {alert_type.value: 0 for alert_type in StuckAccountType}
        for alert in alerts:
            type_counts[alert.alert_type.value] += 1
        return type_counts

    async def _broadcast_detection_summary(
        self, alerts: List[StuckAccountAlert], intelligence: List[OperationalIntelligence]
    ):
        """Broadcast detection summary to subscribers"""
        await self.websocket_manager.broadcast_operational_intelligence(
            "stuck_account_detection_complete",
            {
                "total_alerts": len(alerts),
                "severity_breakdown": self._group_alerts_by_severity(alerts),
                "type_breakdown": self._group_alerts_by_type(alerts),
                "intelligence_insights": len(intelligence),
                "confidence": sum(intel.confidence for intel in intelligence)
                / max(len(intelligence), 1),
                "high_priority_alerts": len(
                    [
                        a
                        for a in alerts
                        if a.severity in [StuckAccountSeverity.HIGH, StuckAccountSeverity.CRITICAL]
                    ]
                ),
            },
        )

    async def get_operational_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive operational dashboard data"""
        return {
            "active_alerts": len(
                [alert for alert in self.asana_connector.stuck_account_cache.values()]
            ),
            "recent_intelligence": [intel.__dict__ for intel in self.intelligence_cache[-10:]],
            "system_health": await self._calculate_system_health(),
            "recommendations": await self._get_top_recommendations(),
            "last_scan": datetime.utcnow().isoformat(),
        }

    async def _calculate_system_health(self) -> Dict[str, Any]:
        """Calculate overall system health score"""
        # Simple health calculation based on alert severity
        total_alerts = len(self.asana_connector.stuck_account_cache)
        if total_alerts == 0:
            health_score = 100
        else:
            critical_weight = (
                sum(
                    1
                    for alert in self.asana_connector.stuck_account_cache.values()
                    if alert.severity == StuckAccountSeverity.CRITICAL
                )
                * 4
            )
            high_weight = (
                sum(
                    1
                    for alert in self.asana_connector.stuck_account_cache.values()
                    if alert.severity == StuckAccountSeverity.HIGH
                )
                * 2
            )
            medium_weight = (
                sum(
                    1
                    for alert in self.asana_connector.stuck_account_cache.values()
                    if alert.severity == StuckAccountSeverity.MEDIUM
                )
                * 1
            )

            total_weight = critical_weight + high_weight + medium_weight
            health_score = max(0, 100 - (total_weight * 5))

        return {
            "score": health_score,
            "status": (
                "healthy" if health_score > 80 else "warning" if health_score > 60 else "critical"
            ),
            "total_alerts": total_alerts,
        }

    async def _get_top_recommendations(self) -> List[str]:
        """Get top recommendations based on current intelligence"""
        recommendations = set()

        for intel in self.intelligence_cache[-5:]:  # Last 5 intelligence insights
            recommendations.update(intel.recommendations[:2])  # Top 2 recommendations each

        return list(recommendations)[:10]  # Return top 10
