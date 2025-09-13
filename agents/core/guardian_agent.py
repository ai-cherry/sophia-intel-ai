"""
Guardian Agent - Monitors and maintains other agents in the swarm
Implements Agno v3.2 guardian pattern for resilient agent ecosystems
"""
import asyncio
import json
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
import redis
import structlog
from qdrant_client import QdrantClient
from .base_agent import (
    AgentCapability,
    AgentConfig,
    BaseAgent,
    ResilienceConfig,
)
logger = structlog.get_logger(__name__)
class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
@dataclass
class AgentAlert:
    """Agent monitoring alert"""
    agent_id: str
    alert_type: str
    level: AlertLevel
    message: str
    timestamp: datetime
    resolved: bool = False
    resolution_time: datetime | None = None
class GuardianAgent(BaseAgent):
    """
    Guardian Agent - Monitors and maintains other agents
    Provides health monitoring, automatic recovery, and alert management
    """
    def __init__(
        self,
        monitored_agent_id: str | None = None,
        redis_client: redis.Redis | None = None,
        qdrant_client: QdrantClient | None = None,
    ):
        config = AgentConfig(
            agent_id=f"guardian_{int(time.time())}",
            agent_name="Guardian Agent",
            agent_type="guardian",
            capabilities=[
                AgentCapability.MONITORING,
                AgentCapability.RECOVERY,
                AgentCapability.ALERTING,
                AgentCapability.MAINTENANCE,
            ],
            resilience=ResilienceConfig(
                enabled=True,
                max_retries=5,
                guardian_enabled=False,
                auto_recovery=True,
            ),
        )
        super().__init__(config)
        self.monitored_agent_id = monitored_agent_id
        self.monitored_agents: set[str] = set()
        if monitored_agent_id:
            self.monitored_agents.add(monitored_agent_id)
        # Use provided clients or initialize own
        if redis_client:
            self.redis_client = redis_client
        if qdrant_client:
            self.qdrant_client = qdrant_client
        # Guardian-specific state
        self.alerts: list[AgentAlert] = []
        self.recovery_actions: dict[str, list[str]] = {}
        self.monitoring_interval = 15  # seconds
        self.alert_thresholds = {
            "error_rate": 0.3,
            "inactive_time": 300,  # 5 minutes
            "memory_usage": 0.8,
            "response_time": 30.0,
        }
        logger.info(
            "Guardian agent initialized",
            guardian_id=self.agent_id,
            monitored_agent=monitored_agent_id,
        )
    async def _execute_task_impl(
        self, task: dict[str, Any], context: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Execute guardian-specific tasks"""
        task_type = task.get("type", "monitor")
        if task_type == "monitor":
            return await self._monitor_agents()
        elif task_type == "recover":
            return await self._recover_agent(task.get("agent_id"))
        elif task_type == "alert":
            return await self._handle_alert(task.get("alert"))
        elif task_type == "maintenance":
            return await self._perform_maintenance()
        else:
            raise ValueError(f"Unknown guardian task type: {task_type}")
    async def add_monitored_agent(self, agent_id: str) -> None:
        """Add an agent to monitoring list"""
        self.monitored_agents.add(agent_id)
        logger.info(
            "Added agent to monitoring",
            guardian_id=self.agent_id,
            monitored_agent=agent_id,
        )
    async def remove_monitored_agent(self, agent_id: str) -> None:
        """Remove an agent from monitoring list"""
        self.monitored_agents.discard(agent_id)
        logger.info(
            "Removed agent from monitoring",
            guardian_id=self.agent_id,
            monitored_agent=agent_id,
        )
    async def _monitor_agents(self) -> dict[str, Any]:
        """Monitor all registered agents"""
        monitoring_results = {
            "timestamp": datetime.now().isoformat(),
            "monitored_count": len(self.monitored_agents),
            "healthy_agents": [],
            "unhealthy_agents": [],
            "alerts_generated": 0,
            "recovery_actions": 0,
        }
        for agent_id in self.monitored_agents:
            try:
                health_status = await self._check_agent_health(agent_id)
                if health_status["is_healthy"]:
                    monitoring_results["healthy_agents"].append(agent_id)
                else:
                    monitoring_results["unhealthy_agents"].append(agent_id)
                    # Generate alerts for unhealthy agents
                    alerts = await self._generate_alerts(agent_id, health_status)
                    monitoring_results["alerts_generated"] += len(alerts)
                    # Attempt recovery if needed
                    if health_status["needs_recovery"]:
                        recovery_result = await self._attempt_agent_recovery(
                            agent_id, health_status
                        )
                        if recovery_result["attempted"]:
                            monitoring_results["recovery_actions"] += 1
            except Exception as e:
                logger.error(
                    "Failed to monitor agent",
                    guardian_id=self.agent_id,
                    monitored_agent=agent_id,
                    error=str(e),
                )
                # Create critical alert for monitoring failure
                await self._create_alert(
                    agent_id=agent_id,
                    alert_type="monitoring_failure",
                    level=AlertLevel.CRITICAL,
                    message=f"Failed to monitor agent: {str(e)}",
                )
        logger.info(
            "Agent monitoring completed",
            guardian_id=self.agent_id,
            results=monitoring_results,
        )
        return monitoring_results
    async def _check_agent_health(self, agent_id: str) -> dict[str, Any]:
        """Check health status of a specific agent"""
        health_status = {
            "agent_id": agent_id,
            "is_healthy": True,
            "needs_recovery": False,
            "issues": [],
            "metrics": {},
            "last_seen": None,
        }
        if not self.redis_client:
            health_status["is_healthy"] = False
            health_status["issues"].append("No Redis connection for health check")
            return health_status
        try:
            # Get agent health data from Redis
            health_data = await asyncio.to_thread(
                self.redis_client.get, f"agent_health:{agent_id}"
            )
            if not health_data:
                health_status["is_healthy"] = False
                health_status["needs_recovery"] = True
                health_status["issues"].append("No health data available")
                return health_status
            agent_health = json.loads(health_data)
            health_status["metrics"] = agent_health
            health_status["last_seen"] = agent_health.get("timestamp")
            # Check various health indicators
            await self._check_agent_responsiveness(
                agent_id, agent_health, health_status
            )
            await self._check_agent_error_rate(agent_id, agent_health, health_status)
            await self._check_agent_performance(agent_id, agent_health, health_status)
            await self._check_agent_connections(agent_id, agent_health, health_status)
            # Determine overall health
            if health_status["issues"]:
                health_status["is_healthy"] = False
                # Determine if recovery is needed
                critical_issues = [
                    issue
                    for issue in health_status["issues"]
                    if any(
                        keyword in issue.lower()
                        for keyword in ["failed", "timeout", "connection", "critical"]
                    )
                ]
                if critical_issues:
                    health_status["needs_recovery"] = True
        except Exception as e:
            health_status["is_healthy"] = False
            health_status["needs_recovery"] = True
            health_status["issues"].append(f"Health check failed: {str(e)}")
        return health_status
    async def _check_agent_responsiveness(
        self, agent_id: str, agent_health: dict[str, Any], health_status: dict[str, Any]
    ) -> None:
        """Check if agent is responsive"""
        last_activity_str = agent_health.get("timestamp")
        if last_activity_str:
            try:
                last_activity = datetime.fromisoformat(
                    last_activity_str.replace("Z", "+00:00")
                )
                inactive_time = (
                    datetime.now() - last_activity.replace(tzinfo=None)
                ).total_seconds()
                if inactive_time > self.alert_thresholds["inactive_time"]:
                    health_status["issues"].append(
                        f"Agent inactive for {inactive_time:.1f} seconds"
                    )
            except Exception as e:
                health_status["issues"].append(f"Invalid timestamp format: {str(e)}")
    async def _check_agent_error_rate(
        self, agent_id: str, agent_health: dict[str, Any], health_status: dict[str, Any]
    ) -> None:
        """Check agent error rate"""
        metrics = agent_health.get("metrics", {})
        tasks_completed = metrics.get("tasks_completed", 0)
        tasks_failed = metrics.get("tasks_failed", 0)
        if tasks_completed + tasks_failed > 0:
            error_rate = tasks_failed / (tasks_completed + tasks_failed)
            if error_rate > self.alert_thresholds["error_rate"]:
                health_status["issues"].append(f"High error rate: {error_rate:.2%}")
    async def _check_agent_performance(
        self, agent_id: str, agent_health: dict[str, Any], health_status: dict[str, Any]
    ) -> None:
        """Check agent performance metrics"""
        # Check if agent is in failed state
        state = agent_health.get("state", "unknown")
        if state == "failed":
            health_status["issues"].append("Agent is in failed state")
        # Check error count
        error_count = agent_health.get("error_count", 0)
        if error_count > 10:
            health_status["issues"].append(f"High error count: {error_count}")
    async def _check_agent_connections(
        self, agent_id: str, agent_health: dict[str, Any], health_status: dict[str, Any]
    ) -> None:
        """Check agent external connections"""
        connections = agent_health.get("connections", {})
        if not connections.get("redis", False):
            health_status["issues"].append("Redis connection lost")
        if not connections.get("qdrant", False):
            health_status["issues"].append("Qdrant connection lost")
    async def _generate_alerts(
        self, agent_id: str, health_status: dict[str, Any]
    ) -> list[AgentAlert]:
        """Generate alerts based on health status"""
        alerts = []
        for issue in health_status["issues"]:
            # Determine alert level
            if any(
                keyword in issue.lower()
                for keyword in ["critical", "failed", "connection lost"]
            ):
                level = AlertLevel.CRITICAL
            elif any(keyword in issue.lower() for keyword in ["high", "timeout"]):
                level = AlertLevel.ERROR
            elif any(keyword in issue.lower() for keyword in ["inactive", "slow"]):
                level = AlertLevel.WARNING
            else:
                level = AlertLevel.INFO
            alert = AgentAlert(
                agent_id=agent_id,
                alert_type="health_issue",
                level=level,
                message=issue,
                timestamp=datetime.now(),
            )
            alerts.append(alert)
            await self._create_alert_record(alert)
        return alerts
    async def _create_alert(
        self, agent_id: str, alert_type: str, level: AlertLevel, message: str
    ) -> None:
        """Create and store an alert"""
        alert = AgentAlert(
            agent_id=agent_id,
            alert_type=alert_type,
            level=level,
            message=message,
            timestamp=datetime.now(),
        )
        await self._create_alert_record(alert)
    async def _create_alert_record(self, alert: AgentAlert) -> None:
        """Store alert record in Redis"""
        self.alerts.append(alert)
        if self.redis_client:
            try:
                alert_data = {
                    "agent_id": alert.agent_id,
                    "alert_type": alert.alert_type,
                    "level": alert.level.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "resolved": alert.resolved,
                    "guardian_id": self.agent_id,
                }
                # Store in Redis with TTL
                await asyncio.to_thread(
                    self.redis_client.setex,
                    f"alert:{alert.agent_id}:{int(alert.timestamp.timestamp())}",
                    3600,  # TTL: 1 hour
                    json.dumps(alert_data),
                )
                # Also add to alerts list
                await asyncio.to_thread(
                    self.redis_client.lpush,
                    f"alerts:{alert.agent_id}",
                    json.dumps(alert_data),
                )
                # Trim alerts list to keep only recent ones
                await asyncio.to_thread(
                    self.redis_client.ltrim,
                    f"alerts:{alert.agent_id}",
                    0,
                    99,  # Keep last 100 alerts
                )
                logger.info(
                    "Alert created",
                    guardian_id=self.agent_id,
                    agent_id=alert.agent_id,
                    level=alert.level.value,
                    message=alert.message,
                )
            except Exception as e:
                logger.error(
                    "Failed to store alert", guardian_id=self.agent_id, error=str(e)
                )
    async def _attempt_agent_recovery(
        self, agent_id: str, health_status: dict[str, Any]
    ) -> dict[str, Any]:
        """Attempt to recover an unhealthy agent"""
        recovery_result = {
            "agent_id": agent_id,
            "attempted": False,
            "actions": [],
            "success": False,
            "error": None,
        }
        try:
            logger.info(
                "Attempting agent recovery",
                guardian_id=self.agent_id,
                target_agent=agent_id,
            )
            recovery_result["attempted"] = True
            # Recovery action 1: Send healing signal
            if self.redis_client:
                healing_signal = {
                    "action": "self_heal",
                    "timestamp": datetime.now().isoformat(),
                    "guardian_id": self.agent_id,
                    "issues": health_status["issues"],
                }
                await asyncio.to_thread(
                    self.redis_client.setex,
                    f"healing_signal:{agent_id}",
                    300,  # TTL: 5 minutes
                    json.dumps(healing_signal),
                )
                recovery_result["actions"].append("healing_signal_sent")
            # Recovery action 2: Clear error state
            if "High error count" in str(health_status["issues"]):
                await asyncio.to_thread(
                    self.redis_client.delete, f"agent_errors:{agent_id}"
                )
                recovery_result["actions"].append("error_state_cleared")
            # Recovery action 3: Refresh connections
            if any("connection" in issue.lower() for issue in health_status["issues"]):
                connection_refresh = {
                    "action": "refresh_connections",
                    "timestamp": datetime.now().isoformat(),
                    "guardian_id": self.agent_id,
                }
                await asyncio.to_thread(
                    self.redis_client.setex,
                    f"connection_refresh:{agent_id}",
                    300,
                    json.dumps(connection_refresh),
                )
                recovery_result["actions"].append("connection_refresh_requested")
            recovery_result["success"] = len(recovery_result["actions"]) > 0
            logger.info(
                "Agent recovery attempted",
                guardian_id=self.agent_id,
                target_agent=agent_id,
                actions=recovery_result["actions"],
                success=recovery_result["success"],
            )
        except Exception as e:
            recovery_result["error"] = str(e)
            logger.error(
                "Agent recovery failed",
                guardian_id=self.agent_id,
                target_agent=agent_id,
                error=str(e),
            )
        return recovery_result
    async def _recover_agent(self, agent_id: str) -> dict[str, Any]:
        """Recover a specific agent (task implementation)"""
        if not agent_id:
            raise ValueError("Agent ID required for recovery")
        health_status = await self._check_agent_health(agent_id)
        return await self._attempt_agent_recovery(agent_id, health_status)
    async def _handle_alert(self, alert_data: dict[str, Any]) -> dict[str, Any]:
        """Handle an incoming alert (task implementation)"""
        # Process and store the alert
        alert = AgentAlert(
            agent_id=alert_data.get("agent_id", "unknown"),
            alert_type=alert_data.get("alert_type", "generic"),
            level=AlertLevel(alert_data.get("level", "info")),
            message=alert_data.get("message", "No message"),
            timestamp=datetime.now(),
        )
        await self._create_alert_record(alert)
        return {
            "status": "handled",
            "alert_id": f"{alert.agent_id}_{int(alert.timestamp.timestamp())}",
            "level": alert.level.value,
        }
    async def _perform_maintenance(self) -> dict[str, Any]:
        """Perform routine maintenance tasks"""
        maintenance_results = {
            "timestamp": datetime.now().isoformat(),
            "tasks_completed": [],
            "errors": [],
        }
        try:
            # Clean up old alerts
            if self.redis_client:
                for agent_id in self.monitored_agents:
                    try:
                        # Keep only recent alerts
                        await asyncio.to_thread(
                            self.redis_client.ltrim, f"alerts:{agent_id}", 0, 99
                        )
                        maintenance_results["tasks_completed"].append(
                            f"cleaned_alerts_{agent_id}"
                        )
                    except Exception as e:
                        maintenance_results["errors"].append(
                            f"alert_cleanup_{agent_id}: {str(e)}"
                        )
            # Update guardian metrics
            self.metrics["last_maintenance"] = datetime.now()
            maintenance_results["tasks_completed"].append("metrics_updated")
            logger.info(
                "Maintenance completed",
                guardian_id=self.agent_id,
                tasks=len(maintenance_results["tasks_completed"]),
                errors=len(maintenance_results["errors"]),
            )
        except Exception as e:
            maintenance_results["errors"].append(f"maintenance_error: {str(e)}")
            logger.error("Maintenance failed", guardian_id=self.agent_id, error=str(e))
        return maintenance_results
    async def get_alerts(
        self, agent_id: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get alerts for specific agent or all agents"""
        if not self.redis_client:
            return []
        alerts = []
        try:
            if agent_id:
                # Get alerts for specific agent
                alert_data = await asyncio.to_thread(
                    self.redis_client.lrange, f"alerts:{agent_id}", 0, limit - 1
                )
                for alert_json in alert_data:
                    alerts.append(json.loads(alert_json))
            else:
                # Get alerts for all monitored agents
                for monitored_agent in self.monitored_agents:
                    agent_alerts = await asyncio.to_thread(
                        self.redis_client.lrange,
                        f"alerts:{monitored_agent}",
                        0,
                        (
                            limit // len(self.monitored_agents)
                            if self.monitored_agents
                            else limit
                        ),
                    )
                    for alert_json in agent_alerts:
                        alerts.append(json.loads(alert_json))
            # Sort by timestamp (most recent first)
            alerts.sort(key=lambda x: x["timestamp"], reverse=True)
        except Exception as e:
            logger.error(
                "Failed to retrieve alerts", guardian_id=self.agent_id, error=str(e)
            )
        return alerts[:limit]
    def get_guardian_status(self) -> dict[str, Any]:
        """Get comprehensive guardian status"""
        base_status = self.get_status()
        guardian_status = {
            **base_status,
            "monitored_agents": list(self.monitored_agents),
            "active_alerts": len(
                [alert for alert in self.alerts if not alert.resolved]
            ),
            "total_alerts": len(self.alerts),
            "monitoring_interval": self.monitoring_interval,
            "alert_thresholds": self.alert_thresholds,
            "recovery_actions": self.recovery_actions,
        }
        return guardian_status
