#!/usr/bin/env python3
"""
Sophia AI Agent Registry - Agent Discovery and Management
Provides centralized agent registration, discovery, and metadata management
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from .base_agent import AgentCapability, AgentStatus, BaseAgent

logger = logging.getLogger(__name__)

class RegistrationStatus(Enum):
    """Agent registration status"""

    REGISTERED = "registered"
    UNREGISTERED = "unregistered"
    SUSPENDED = "suspended"
    MAINTENANCE = "maintenance"

@dataclass
class AgentRegistration:
    """Agent registration information"""

    agent_id: str
    agent_name: str
    agent_type: str
    capabilities: set[AgentCapability]
    version: str
    endpoint: str | None = None
    mcp_port: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    registration_status: RegistrationStatus = RegistrationStatus.REGISTERED
    registered_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime | None = None
    health_check_interval: int = 30  # seconds
    max_concurrent_tasks: int = 5
    tags: set[str] = field(default_factory=set)

    def __post_init__(self):
        if isinstance(self.capabilities, list):
            self.capabilities = set(self.capabilities)
        if isinstance(self.tags, list):
            self.tags = set(self.tags)

    @property
    def is_healthy(self) -> bool:
        """Check if agent is considered healthy based on heartbeat"""
        if not self.last_heartbeat:
            return False

        max_age = timedelta(seconds=self.health_check_interval * 3)  # 3x interval
        return datetime.now() - self.last_heartbeat < max_age

    @property
    def uptime_seconds(self) -> float:
        """Calculate agent uptime in seconds"""
        return (datetime.now() - self.registered_at).total_seconds()

class AgentRegistry:
    """
    Centralized registry for agent discovery and management
    Provides registration, discovery, health monitoring, and metadata management
    """

    def __init__(self, enable_health_monitoring: bool = True):
        self.agents: dict[str, AgentRegistration] = {}
        self.agent_instances: dict[str, BaseAgent] = {}  # Optional agent instances
        self.enable_health_monitoring = enable_health_monitoring
        self.registry_id = str(uuid.uuid4())
        self.is_running = False
        self.health_monitor_task = None

        logger.info(f"Agent Registry initialized [{self.registry_id[:8]}]")

    async def start(self) -> None:
        """Start the registry and health monitoring"""
        if self.is_running:
            logger.warning("Registry is already running")
            return

        self.is_running = True

        if self.enable_health_monitoring:
            self.health_monitor_task = asyncio.create_task(self._health_monitor_loop())

        logger.info("Agent Registry started")

    async def stop(self) -> None:
        """Stop the registry"""
        if not self.is_running:
            return

        self.is_running = False

        if self.health_monitor_task:
            self.health_monitor_task.cancel()
            try:
                await self.health_monitor_task
            except asyncio.CancelledError:

        logger.info("Agent Registry stopped")

    def register_agent(
        self,
        agent_id: str,
        agent_name: str,
        agent_type: str,
        capabilities: list[AgentCapability],
        version: str = "1.0.0",
        endpoint: str | None = None,
        mcp_port: int | None = None,
        metadata: dict[str, Any] | None = None,
        max_concurrent_tasks: int = 5,
        tags: list[str] | None = None,
        agent_instance: BaseAgent | None = None,
    ) -> bool:
        """Register an agent with the registry"""
        try:
            if agent_id in self.agents:
                logger.warning(f"Agent {agent_id} is already registered")
                return False

            registration = AgentRegistration(
                agent_id=agent_id,
                agent_name=agent_name,
                agent_type=agent_type,
                capabilities=set(capabilities),
                version=version,
                endpoint=endpoint,
                mcp_port=mcp_port,
                metadata=metadata or {},
                max_concurrent_tasks=max_concurrent_tasks,
                tags=set(tags or []),
                last_heartbeat=datetime.now(),
            )

            self.agents[agent_id] = registration

            if agent_instance:
                self.agent_instances[agent_id] = agent_instance

            logger.info(
                f"Registered agent {agent_name} [{agent_id[:8]}] with capabilities: {[cap.value for cap in capabilities]}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to register agent {agent_id}: {str(e)}")
            return False

    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the registry"""
        try:
            if agent_id not in self.agents:
                logger.warning(f"Agent {agent_id} is not registered")
                return False

            registration = self.agents[agent_id]
            registration.registration_status = RegistrationStatus.UNREGISTERED

            # Remove from active registrations
            del self.agents[agent_id]

            # Remove agent instance if present
            if agent_id in self.agent_instances:
                del self.agent_instances[agent_id]

            logger.info(
                f"Unregistered agent {registration.agent_name} [{agent_id[:8]}]"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to unregister agent {agent_id}: {str(e)}")
            return False

    def heartbeat(
        self, agent_id: str, status_data: dict[str, Any] | None = None
    ) -> bool:
        """Record a heartbeat from an agent"""
        try:
            if agent_id not in self.agents:
                logger.warning(f"Heartbeat from unregistered agent {agent_id}")
                return False

            registration = self.agents[agent_id]
            registration.last_heartbeat = datetime.now()

            # Update metadata with status data if provided
            if status_data:
                registration.metadata.update(
                    {
                        "last_status": status_data,
                        "status_updated_at": datetime.now().isoformat(),
                    }
                )

            return True

        except Exception as e:
            logger.error(f"Failed to process heartbeat from agent {agent_id}: {str(e)}")
            return False

    def find_agents_by_capability(
        self, capability: AgentCapability
    ) -> list[AgentRegistration]:
        """Find all agents with a specific capability"""
        return [
            registration
            for registration in self.agents.values()
            if capability in registration.capabilities
            and registration.registration_status == RegistrationStatus.REGISTERED
            and registration.is_healthy
        ]

    def find_agents_by_type(self, agent_type: str) -> list[AgentRegistration]:
        """Find all agents of a specific type"""
        return [
            registration
            for registration in self.agents.values()
            if registration.agent_type == agent_type
            and registration.registration_status == RegistrationStatus.REGISTERED
            and registration.is_healthy
        ]

    def find_agents_by_tag(self, tag: str) -> list[AgentRegistration]:
        """Find all agents with a specific tag"""
        return [
            registration
            for registration in self.agents.values()
            if tag in registration.tags
            and registration.registration_status == RegistrationStatus.REGISTERED
            and registration.is_healthy
        ]

    def find_best_agent(
        self,
        required_capabilities: list[AgentCapability],
        agent_type: str | None = None,
        tags: list[str] | None = None,
        exclude_agents: list[str] | None = None,
    ) -> AgentRegistration | None:
        """Find the best agent matching the criteria"""
        candidates = []
        exclude_set = set(exclude_agents or [])

        for registration in self.agents.values():
            # Skip if excluded, unhealthy, or not registered
            if (
                registration.agent_id in exclude_set
                or not registration.is_healthy
                or registration.registration_status != RegistrationStatus.REGISTERED
            ):
                continue

            # Check required capabilities
            if not all(
                cap in registration.capabilities for cap in required_capabilities
            ):
                continue

            # Check agent type if specified
            if agent_type and registration.agent_type != agent_type:
                continue

            # Check tags if specified
            if tags and not any(tag in registration.tags for tag in tags):
                continue

            candidates.append(registration)

        if not candidates:
            return None

        # Score candidates based on various factors
        def score_agent(registration: AgentRegistration) -> float:
            score = 0.0

            # Capability match score (higher is better)
            capability_match = len(
                registration.capabilities.intersection(required_capabilities)
            )
            score += capability_match * 10

            # Load score (lower concurrent tasks is better)
            if registration.agent_id in self.agent_instances:
                agent = self.agent_instances[registration.agent_id]
                status = agent.get_status()
                active_tasks = status.get("active_tasks", 0)
                load_factor = active_tasks / registration.max_concurrent_tasks
                score += (1.0 - load_factor) * 5

            # Health score (more recent heartbeat is better)
            if registration.last_heartbeat:
                heartbeat_age = (
                    datetime.now() - registration.last_heartbeat
                ).total_seconds()
                health_score = max(0, 1.0 - (heartbeat_age / 300))  # 5 minute decay
                score += health_score * 3

            # Version score (prefer newer versions)
            try:
                version_parts = registration.version.split(".")
                version_score = sum(
                    int(part) * (10 ** (2 - i))
                    for i, part in enumerate(version_parts[:3])
                )
                score += version_score * 0.01
            except:

            return score

        return max(candidates, key=score_agent)

    def get_agent_info(self, agent_id: str) -> dict[str, Any] | None:
        """Get detailed information about a specific agent"""
        if agent_id not in self.agents:
            return None

        registration = self.agents[agent_id]
        info = {
            "agent_id": registration.agent_id,
            "agent_name": registration.agent_name,
            "agent_type": registration.agent_type,
            "capabilities": [cap.value for cap in registration.capabilities],
            "version": registration.version,
            "endpoint": registration.endpoint,
            "mcp_port": registration.mcp_port,
            "registration_status": registration.registration_status.value,
            "registered_at": registration.registered_at.isoformat(),
            "last_heartbeat": (
                registration.last_heartbeat.isoformat()
                if registration.last_heartbeat
                else None
            ),
            "is_healthy": registration.is_healthy,
            "uptime_seconds": registration.uptime_seconds,
            "max_concurrent_tasks": registration.max_concurrent_tasks,
            "tags": list(registration.tags),
            "metadata": registration.metadata,
        }

        # Add live status if agent instance is available
        if agent_id in self.agent_instances:
            try:
                agent = self.agent_instances[agent_id]
                live_status = agent.get_status()
                info["live_status"] = live_status
            except Exception as e:
                logger.error(
                    f"Failed to get live status for agent {agent_id}: {str(e)}"
                )

        return info

    def get_registry_status(self) -> dict[str, Any]:
        """Get registry status and statistics"""
        now = datetime.now()

        # Calculate statistics
        total_agents = len(self.agents)
        healthy_agents = sum(1 for reg in self.agents.values() if reg.is_healthy)
        registered_agents = sum(
            1
            for reg in self.agents.values()
            if reg.registration_status == RegistrationStatus.REGISTERED
        )

        # Capability distribution
        capability_counts = {}
        for registration in self.agents.values():
            for capability in registration.capabilities:
                capability_counts[capability.value] = (
                    capability_counts.get(capability.value, 0) + 1
                )

        # Agent type distribution
        type_counts = {}
        for registration in self.agents.values():
            type_counts[registration.agent_type] = (
                type_counts.get(registration.agent_type, 0) + 1
            )

        return {
            "registry_id": self.registry_id,
            "is_running": self.is_running,
            "enable_health_monitoring": self.enable_health_monitoring,
            "statistics": {
                "total_agents": total_agents,
                "healthy_agents": healthy_agents,
                "registered_agents": registered_agents,
                "unhealthy_agents": total_agents - healthy_agents,
                "capability_distribution": capability_counts,
                "type_distribution": type_counts,
            },
            "agents": [
                {
                    "agent_id": reg.agent_id,
                    "agent_name": reg.agent_name,
                    "agent_type": reg.agent_type,
                    "status": reg.registration_status.value,
                    "is_healthy": reg.is_healthy,
                    "capabilities": [cap.value for cap in reg.capabilities],
                    "last_heartbeat": (
                        reg.last_heartbeat.isoformat() if reg.last_heartbeat else None
                    ),
                }
                for reg in self.agents.values()
            ],
            "timestamp": now.isoformat(),
        }

    def update_agent_metadata(self, agent_id: str, metadata: dict[str, Any]) -> bool:
        """Update agent metadata"""
        try:
            if agent_id not in self.agents:
                logger.warning(
                    f"Cannot update metadata for unregistered agent {agent_id}"
                )
                return False

            registration = self.agents[agent_id]
            registration.metadata.update(metadata)
            registration.metadata["metadata_updated_at"] = datetime.now().isoformat()

            return True

        except Exception as e:
            logger.error(f"Failed to update metadata for agent {agent_id}: {str(e)}")
            return False

    def suspend_agent(self, agent_id: str, reason: str = "") -> bool:
        """Suspend an agent (temporarily disable)"""
        try:
            if agent_id not in self.agents:
                logger.warning(f"Cannot suspend unregistered agent {agent_id}")
                return False

            registration = self.agents[agent_id]
            registration.registration_status = RegistrationStatus.SUSPENDED
            registration.metadata["suspension_reason"] = reason
            registration.metadata["suspended_at"] = datetime.now().isoformat()

            logger.info(
                f"Suspended agent {registration.agent_name} [{agent_id[:8]}]: {reason}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to suspend agent {agent_id}: {str(e)}")
            return False

    def resume_agent(self, agent_id: str) -> bool:
        """Resume a suspended agent"""
        try:
            if agent_id not in self.agents:
                logger.warning(f"Cannot resume unregistered agent {agent_id}")
                return False

            registration = self.agents[agent_id]
            registration.registration_status = RegistrationStatus.REGISTERED
            registration.metadata["resumed_at"] = datetime.now().isoformat()
            registration.metadata.pop("suspension_reason", None)

            logger.info(f"Resumed agent {registration.agent_name} [{agent_id[:8]}]")
            return True

        except Exception as e:
            logger.error(f"Failed to resume agent {agent_id}: {str(e)}")
            return False

    async def _health_monitor_loop(self) -> None:
        """Health monitoring loop"""
        while self.is_running:
            try:
                await self._check_agent_health()
                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in health monitoring loop: {str(e)}")
                await asyncio.sleep(60)  # Longer delay on error

    async def _check_agent_health(self) -> None:
        """Check health of all registered agents"""
        unhealthy_agents = []

        for agent_id, registration in self.agents.items():
            if (
                not registration.is_healthy
                and registration.registration_status == RegistrationStatus.REGISTERED
            ):
                unhealthy_agents.append((agent_id, registration))

        for agent_id, registration in unhealthy_agents:
            logger.warning(
                f"Agent {registration.agent_name} [{agent_id[:8]}] is unhealthy "
                f"(last heartbeat: {registration.last_heartbeat})"
            )

            # Optionally suspend unhealthy agents after a grace period
            if registration.last_heartbeat:
                unhealthy_duration = datetime.now() - registration.last_heartbeat
                if unhealthy_duration > timedelta(minutes=5):  # 5 minute grace period
                    self.suspend_agent(
                        agent_id, "Health check failed - no heartbeat for 5+ minutes"
                    )
