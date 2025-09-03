"""
SuperOrchestrator Enhancements - Complete Visibility & Control
This module extends SuperOrchestrator with comprehensive control over all AI systems
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SystemType(Enum):
    """All AI system types under orchestrator control"""
    AGENT = "agent"
    SWARM = "swarm"
    MICRO_SWARM = "micro_swarm"
    BACKGROUND_AGENT = "background_agent"
    EMBEDDING_AGENT = "embedding_agent"
    MCP_SERVER = "mcp_server"
    TOOL = "tool"
    SERVICE = "service"
    MODEL = "model"


class SystemStatus(Enum):
    """System operational status"""
    IDLE = "idle"
    ACTIVE = "active"
    PROCESSING = "processing"
    ERROR = "error"
    DEGRADED = "degraded"
    OFFLINE = "offline"


@dataclass
class RegisteredSystem:
    """Complete representation of any AI system"""
    id: str
    name: str
    type: SystemType
    status: SystemStatus
    capabilities: list[str]
    metrics: dict[str, Any] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)
    connections: set[str] = field(default_factory=set)  # Connected system IDs
    last_activity: datetime = field(default_factory=datetime.now)
    error_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class UniversalRegistry:
    """
    Universal registry for ALL AI systems.
    Single source of truth for what's running.
    """

    def __init__(self):
        self.systems: dict[str, RegisteredSystem] = {}
        self.type_index: dict[SystemType, set[str]] = {t: set() for t in SystemType}
        self.capability_index: dict[str, set[str]] = {}
        self.status_index: dict[SystemStatus, set[str]] = {s: set() for s in SystemStatus}

    async def register(self, system: RegisteredSystem) -> bool:
        """Register any AI system"""
        self.systems[system.id] = system

        # Update indices for fast lookup
        self.type_index[system.type].add(system.id)
        self.status_index[system.status].add(system.id)

        for capability in system.capabilities:
            if capability not in self.capability_index:
                self.capability_index[capability] = set()
            self.capability_index[capability].add(system.id)

        return True

    async def update_status(self, system_id: str, status: SystemStatus) -> bool:
        """Update system status"""
        if system_id in self.systems:
            old_status = self.systems[system_id].status

            # Update indices
            self.status_index[old_status].discard(system_id)
            self.status_index[status].add(system_id)

            self.systems[system_id].status = status
            self.systems[system_id].last_activity = datetime.now()
            return True
        return False

    def get_by_type(self, system_type: SystemType) -> list[RegisteredSystem]:
        """Get all systems of a specific type"""
        return [self.systems[sid] for sid in self.type_index.get(system_type, [])]

    def get_by_capability(self, capability: str) -> list[RegisteredSystem]:
        """Get all systems with a specific capability"""
        return [self.systems[sid] for sid in self.capability_index.get(capability, [])]

    def get_active_systems(self) -> list[RegisteredSystem]:
        """Get all active systems"""
        active_statuses = [SystemStatus.ACTIVE, SystemStatus.PROCESSING]
        result = []
        for status in active_statuses:
            result.extend([self.systems[sid] for sid in self.status_index.get(status, [])])
        return result

    def get_health_report(self) -> dict[str, Any]:
        """Get comprehensive health report"""
        total = len(self.systems)
        by_type = {t.value: len(ids) for t, ids in self.type_index.items()}
        by_status = {s.value: len(ids) for s, ids in self.status_index.items()}

        return {
            "total_systems": total,
            "by_type": by_type,
            "by_status": by_status,
            "health_score": self._calculate_health_score(),
            "timestamp": datetime.now().isoformat()
        }

    def _calculate_health_score(self) -> float:
        """Calculate overall system health (0-100)"""
        if not self.systems:
            return 100.0

        active = len(self.status_index.get(SystemStatus.ACTIVE, []))
        idle = len(self.status_index.get(SystemStatus.IDLE, []))
        error = len(self.status_index.get(SystemStatus.ERROR, []))
        offline = len(self.status_index.get(SystemStatus.OFFLINE, []))

        total = len(self.systems)
        healthy = active + idle

        score = (healthy / total) * 100
        score -= (error * 10)  # Penalty for errors
        score -= (offline * 5)  # Penalty for offline

        return max(0, min(100, score))


class NaturalLanguageController:
    """
    Natural language interface for complete system control.
    Understands complex commands and orchestrates accordingly.
    """

    def __init__(self, registry: UniversalRegistry):
        self.registry = registry
        self.command_patterns = self._build_command_patterns()

    def _build_command_patterns(self) -> dict[str, Any]:
        """Build NLP command patterns"""
        return {
            # Status queries
            "status": ["show", "status", "health", "what's running"],
            "list": ["list", "show all", "get all"],

            # Control commands
            "start": ["start", "launch", "spawn", "create", "deploy"],
            "stop": ["stop", "kill", "terminate", "shutdown"],
            "restart": ["restart", "reboot", "refresh"],
            "scale": ["scale", "resize", "expand", "shrink"],

            # Micro-swarm specific
            "swarm": ["swarm", "micro-swarm", "task force"],

            # Analysis
            "analyze": ["analyze", "inspect", "debug", "diagnose"],
            "optimize": ["optimize", "improve", "enhance", "tune"],

            # Coordination
            "coordinate": ["coordinate", "orchestrate", "manage"],
            "connect": ["connect", "link", "integrate"],
        }

    async def process_command(self, natural_language: str) -> dict[str, Any]:
        """
        Process natural language command.
        This is where the magic happens - understanding intent and executing.
        """

        # Lowercase for matching
        command_lower = natural_language.lower()

        # Detect intent
        intent = self._detect_intent(command_lower)
        entities = self._extract_entities(command_lower)

        # Execute based on intent
        if intent == "status":
            return await self._handle_status_query(entities)
        elif intent == "start":
            return await self._handle_start_command(entities)
        elif intent == "stop":
            return await self._handle_stop_command(entities)
        elif intent == "swarm":
            return await self._handle_swarm_command(entities)
        elif intent == "analyze":
            return await self._handle_analysis_command(entities)
        elif intent == "coordinate":
            return await self._handle_coordination_command(entities)
        else:
            return await self._handle_generic_command(natural_language)

    def _detect_intent(self, command: str) -> str:
        """Detect command intent from natural language"""
        for intent, patterns in self.command_patterns.items():
            for pattern in patterns:
                if pattern in command:
                    return intent
        return "unknown"

    def _extract_entities(self, command: str) -> dict[str, Any]:
        """Extract entities from command"""
        entities = {}

        # Extract system types
        for sys_type in SystemType:
            if sys_type.value in command:
                entities["system_type"] = sys_type

        # Extract specific names (simplified - in production use NER)
        words = command.split()
        if "named" in command or "called" in command:
            idx = words.index("named") if "named" in words else words.index("called")
            if idx < len(words) - 1:
                entities["name"] = words[idx + 1]

        # Extract numbers for scaling
        import re
        numbers = re.findall(r'\d+', command)
        if numbers:
            entities["count"] = int(numbers[0])

        return entities

    async def _handle_status_query(self, entities: dict) -> dict:
        """Handle status queries"""
        if "system_type" in entities:
            systems = self.registry.get_by_type(entities["system_type"])
            return {
                "response": f"Found {len(systems)} {entities['system_type'].value} systems",
                "systems": [self._system_to_dict(s) for s in systems],
                "success": True
            }
        else:
            report = self.registry.get_health_report()
            return {
                "response": f"System health: {report['health_score']:.1f}%",
                "report": report,
                "success": True
            }

    async def _handle_start_command(self, entities: dict) -> dict:
        """Handle start/launch commands"""
        system_type = entities.get("system_type", SystemType.AGENT)
        name = entities.get("name", f"{system_type.value}_auto")

        # This would actually start the system
        # For now, we'll simulate registration
        new_system = RegisteredSystem(
            id=f"{system_type.value}_{datetime.now().timestamp()}",
            name=name,
            type=system_type,
            status=SystemStatus.ACTIVE,
            capabilities=self._get_default_capabilities(system_type)
        )

        await self.registry.register(new_system)

        return {
            "response": f"Started {system_type.value}: {name}",
            "system_id": new_system.id,
            "success": True
        }

    async def _handle_stop_command(self, entities: dict) -> dict:
        """Handle stop commands"""
        if "name" in entities:
            # Find and stop specific system
            for system in self.registry.systems.values():
                if system.name == entities["name"]:
                    await self.registry.update_status(system.id, SystemStatus.OFFLINE)
                    return {
                        "response": f"Stopped {system.name}",
                        "system_id": system.id,
                        "success": True
                    }

        return {
            "response": "System not found",
            "success": False
        }

    async def _handle_swarm_command(self, entities: dict) -> dict:
        """Handle micro-swarm specific commands"""
        # This integrates with the micro-swarm plan
        return {
            "response": "Micro-swarm command processing",
            "entities": entities,
            "success": True
        }

    async def _handle_analysis_command(self, entities: dict) -> dict:
        """Handle analysis commands"""
        active = self.registry.get_active_systems()

        analysis = {
            "active_systems": len(active),
            "total_systems": len(self.registry.systems),
            "health_score": self.registry.get_health_report()["health_score"],
            "recommendations": self._generate_recommendations()
        }

        return {
            "response": "System analysis complete",
            "analysis": analysis,
            "success": True
        }

    async def _handle_coordination_command(self, entities: dict) -> dict:
        """Handle coordination between systems"""
        # This would coordinate multiple systems
        return {
            "response": "Coordination initiated",
            "entities": entities,
            "success": True
        }

    async def _handle_generic_command(self, command: str) -> dict:
        """Handle unknown commands with AI interpretation"""
        return {
            "response": f"Processing: {command}",
            "interpreted_as": "generic_command",
            "success": True
        }

    def _get_default_capabilities(self, system_type: SystemType) -> list[str]:
        """Get default capabilities for a system type"""
        defaults = {
            SystemType.AGENT: ["execute", "respond", "learn"],
            SystemType.SWARM: ["coordinate", "parallel_execute", "consensus"],
            SystemType.MICRO_SWARM: ["specialized_task", "rapid_execution"],
            SystemType.EMBEDDING_AGENT: ["embed", "vectorize", "similarity"],
            SystemType.MCP_SERVER: ["mcp_protocol", "tool_serving", "api"],
        }
        return defaults.get(system_type, ["generic"])

    def _system_to_dict(self, system: RegisteredSystem) -> dict:
        """Convert system to dict for response"""
        return {
            "id": system.id,
            "name": system.name,
            "type": system.type.value,
            "status": system.status.value,
            "capabilities": system.capabilities,
            "last_activity": system.last_activity.isoformat()
        }

    def _generate_recommendations(self) -> list[str]:
        """Generate system optimization recommendations"""
        recommendations = []

        # Check for idle resources
        idle_count = len(self.registry.status_index.get(SystemStatus.IDLE, []))
        if idle_count > 5:
            recommendations.append(f"Consider deallocating {idle_count} idle systems")

        # Check for errors
        error_count = len(self.registry.status_index.get(SystemStatus.ERROR, []))
        if error_count > 0:
            recommendations.append(f"Investigate {error_count} systems in error state")

        # Check system balance
        swarm_count = len(self.registry.type_index.get(SystemType.SWARM, []))
        agent_count = len(self.registry.type_index.get(SystemType.AGENT, []))
        if swarm_count > 0 and agent_count / swarm_count < 3:
            recommendations.append("Consider spawning more agents for swarm capacity")

        return recommendations


class RealTimeMonitor:
    """
    Real-time monitoring system with WebSocket updates.
    Provides live visibility into all AI systems.
    """

    def __init__(self, registry: UniversalRegistry):
        self.registry = registry
        self.subscribers: set[Any] = set()  # WebSocket connections
        self.metrics_buffer = []
        self.alert_thresholds = {
            "error_rate": 0.1,  # 10% error rate
            "response_time": 1000,  # 1 second
            "memory_usage": 0.8,  # 80% memory
        }

    async def start_monitoring(self):
        """Start the monitoring loop"""
        while True:
            metrics = await self.collect_metrics()
            alerts = self.check_alerts(metrics)

            # Broadcast to all subscribers
            await self.broadcast_update({
                "type": "metrics_update",
                "metrics": metrics,
                "alerts": alerts,
                "timestamp": datetime.now().isoformat()
            })

            await asyncio.sleep(1)  # Update every second

    async def collect_metrics(self) -> dict[str, Any]:
        """Collect metrics from all systems"""
        metrics = {
            "systems": {},
            "aggregate": {
                "total_active": 0,
                "total_requests": 0,
                "avg_response_time": 0,
                "error_count": 0
            }
        }

        for system in self.registry.systems.values():
            system_metrics = {
                "status": system.status.value,
                "last_activity": system.last_activity.isoformat(),
                "error_count": system.error_count,
                **system.metrics
            }
            metrics["systems"][system.id] = system_metrics

            # Update aggregates
            if system.status == SystemStatus.ACTIVE:
                metrics["aggregate"]["total_active"] += 1
            metrics["aggregate"]["error_count"] += system.error_count

        return metrics

    def check_alerts(self, metrics: dict) -> list[dict]:
        """Check for alert conditions"""
        alerts = []

        # Check error rate
        total_systems = len(self.registry.systems)
        if total_systems > 0:
            error_systems = len([s for s in self.registry.systems.values()
                               if s.status == SystemStatus.ERROR])
            error_rate = error_systems / total_systems

            if error_rate > self.alert_thresholds["error_rate"]:
                alerts.append({
                    "level": "critical",
                    "message": f"High error rate: {error_rate:.1%}",
                    "metric": "error_rate",
                    "value": error_rate
                })

        return alerts

    async def broadcast_update(self, update: dict):
        """Broadcast update to all subscribers"""
        for subscriber in self.subscribers:
            try:
                await subscriber.send_json(update)
            except:
                self.subscribers.discard(subscriber)

    def subscribe(self, websocket):
        """Subscribe to monitoring updates"""
        self.subscribers.add(websocket)

    def unsubscribe(self, websocket):
        """Unsubscribe from monitoring updates"""
        self.subscribers.discard(websocket)


# Export enhanced components
__all__ = [
    "SystemType",
    "SystemStatus",
    "RegisteredSystem",
    "UniversalRegistry",
    "NaturalLanguageController",
    "RealTimeMonitor"
]
