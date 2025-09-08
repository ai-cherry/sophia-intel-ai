"""
Base Swarm Interfaces

Defines abstract base classes and data structures for AI agent swarms,
including coordination patterns, task distribution, and collective decision making.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from pydantic import BaseModel, Field, validator

from ..agents.base import AgentMessage, BaseAgent, TaskStatus
from ..memory.base import MemoryManager

logger = logging.getLogger(__name__)


class SwarmState(str, Enum):
    """Swarm lifecycle states."""

    INITIALIZING = "initializing"
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    COORDINATING = "coordinating"
    LEARNING = "learning"
    PAUSED = "paused"
    ERROR = "error"
    TERMINATED = "terminated"


class SwarmTopology(str, Enum):
    """Swarm organization topology patterns."""

    HIERARCHICAL = "hierarchical"  # Tree structure with leader/followers
    PEER_TO_PEER = "peer_to_peer"  # Flat network, all agents equal
    RING = "ring"  # Circular communication pattern
    STAR = "star"  # Central coordinator with spokes
    MESH = "mesh"  # Fully connected network
    HYBRID = "hybrid"  # Combination of patterns


class SwarmRole(str, Enum):
    """Roles agents can play in swarms."""

    COORDINATOR = "coordinator"  # Manages and coordinates other agents
    EXECUTOR = "executor"  # Executes assigned tasks
    SPECIALIST = "specialist"  # Domain expert for specific tasks
    COMMUNICATOR = "communicator"  # Handles external communications
    ANALYST = "analyst"  # Analyzes data and provides insights
    MONITOR = "monitor"  # Monitors swarm performance and health
    LEARNER = "learner"  # Focuses on learning and adaptation


class SwarmMember(BaseModel):
    """
    Represents an agent's membership in a swarm.
    """

    agent_id: str
    role: SwarmRole
    capabilities: List[str] = Field(default_factory=list)

    # Status and participation
    status: str = "active"  # active, inactive, busy, error
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)

    # Performance tracking
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_response_time: float = 0.0

    # Relationships
    reports_to: Optional[str] = None  # Agent ID of supervisor
    supervises: List[str] = Field(default_factory=list)  # Agent IDs
    collaborates_with: Set[str] = Field(default_factory=set)  # Agent IDs

    # Resource allocation
    max_concurrent_tasks: int = 3
    current_task_count: int = 0

    @validator("collaborates_with", pre=True)
    def convert_collaborates_to_set(cls, v):
        if isinstance(v, list):
            return set(v)
        return v

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def can_accept_task(self) -> bool:
        """Check if member can accept additional tasks."""
        return (
            self.status == "active"
            and self.current_task_count < self.max_concurrent_tasks
        )

    def assign_task(self) -> None:
        """Record task assignment."""
        self.current_task_count += 1
        self.update_activity()

    def complete_task(self, success: bool, response_time: float) -> None:
        """Record task completion."""
        self.current_task_count = max(0, self.current_task_count - 1)

        if success:
            self.tasks_completed += 1
        else:
            self.tasks_failed += 1

        # Update average response time
        total_tasks = self.tasks_completed + self.tasks_failed
        if total_tasks > 1:
            self.average_response_time = (
                self.average_response_time * (total_tasks - 1) + response_time
            ) / total_tasks
        else:
            self.average_response_time = response_time

        self.update_activity()

    @property
    def success_rate(self) -> float:
        """Calculate task success rate."""
        total_tasks = self.tasks_completed + self.tasks_failed
        return self.tasks_completed / total_tasks if total_tasks > 0 else 0.0

    @property
    def is_available(self) -> bool:
        """Check if member is available for new work."""
        return self.status == "active" and self.current_task_count == 0


class SwarmTask(BaseModel):
    """
    Task to be executed by the swarm.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str
    task_type: str

    # Task requirements
    required_capabilities: List[str] = Field(default_factory=list)
    preferred_roles: List[SwarmRole] = Field(default_factory=list)
    complexity_level: int = Field(1, ge=1, le=10)  # 1=simple, 10=very complex

    # Task parameters and context
    parameters: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)

    # Execution details
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: Optional[str] = None  # Agent ID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deadline: Optional[datetime] = None

    # Dependencies and relationships
    depends_on: List[str] = Field(default_factory=list)  # Task IDs
    blocks: List[str] = Field(default_factory=list)  # Task IDs
    parent_task: Optional[str] = None
    subtasks: List[str] = Field(default_factory=list)

    # Results and feedback
    result: Optional[Any] = None
    error: Optional[str] = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    feedback: Optional[str] = None

    # Priority and resource requirements
    priority: int = Field(5, ge=1, le=10)  # 1=low, 10=critical
    estimated_duration: Optional[int] = None  # seconds
    max_retries: int = 3
    retry_count: int = 0

    def assign_to_agent(self, agent_id: str) -> None:
        """Assign task to specific agent."""
        self.assigned_to = agent_id
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()

    def complete_with_result(self, result: Any, confidence: float = 1.0) -> None:
        """Mark task as completed with result."""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.confidence = confidence
        self.completed_at = datetime.utcnow()

    def fail_with_error(self, error: str) -> None:
        """Mark task as failed with error."""
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.utcnow()
        self.retry_count += 1

    @property
    def execution_time(self) -> Optional[float]:
        """Get task execution time in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.status == TaskStatus.FAILED and self.retry_count < self.max_retries

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        return (
            self.deadline is not None
            and self.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]
            and datetime.utcnow() > self.deadline
        )

    def can_be_executed_by(self, member: SwarmMember) -> bool:
        """Check if task can be executed by specific member."""
        # Check role requirements
        if self.preferred_roles and member.role not in self.preferred_roles:
            return False

        # Check capability requirements
        if self.required_capabilities:
            member_caps = set(member.capabilities)
            required_caps = set(self.required_capabilities)
            if not required_caps.issubset(member_caps):
                return False

        return True


class SwarmMessage(BaseModel):
    """
    Message for communication within swarm.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    sender_id: str
    recipient_id: Optional[str] = None  # None for broadcast
    message_type: str  # coordination, task_assignment, status_update, etc.
    content: str

    # Message routing
    routing_info: Dict[str, Any] = Field(default_factory=dict)
    broadcast_to_roles: List[SwarmRole] = Field(default_factory=list)

    # Priority and delivery
    priority: int = Field(5, ge=1, le=10)
    requires_response: bool = False
    response_timeout: Optional[int] = None  # seconds

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # Content metadata
    task_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)

    def mark_delivered(self) -> None:
        """Mark message as delivered."""
        self.delivered_at = datetime.utcnow()

    @property
    def is_expired(self) -> bool:
        """Check if message has expired."""
        return self.expires_at is not None and datetime.utcnow() > self.expires_at

    @property
    def is_broadcast(self) -> bool:
        """Check if message is broadcast."""
        return self.recipient_id is None


class SwarmConfig(BaseModel):
    """
    Configuration for swarm initialization and operation.
    """

    swarm_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str = ""

    # Swarm structure
    topology: SwarmTopology = SwarmTopology.HIERARCHICAL
    max_members: Optional[int] = None
    min_members: int = 1

    # Task management
    task_queue_size: int = 100
    task_timeout_seconds: int = 300
    max_concurrent_tasks: int = 10

    # Communication settings
    message_queue_size: int = 1000
    message_timeout_seconds: int = 30
    enable_broadcast: bool = True

    # Coordination settings
    coordination_interval: int = 60  # seconds
    health_check_interval: int = 30  # seconds
    enable_auto_scaling: bool = False

    # Learning and adaptation
    enable_collective_learning: bool = True
    learning_update_interval: int = 300  # seconds
    memory_sharing_enabled: bool = True

    # Performance settings
    load_balancing_enabled: bool = True
    failover_enabled: bool = True
    redundancy_factor: int = 1

    # Resource limits
    max_memory_mb: Optional[int] = None
    max_cpu_percent: Optional[float] = None

    def validate_config(self) -> List[str]:
        """
        Validate swarm configuration.

        Returns:
            List[str]: List of validation issues
        """
        issues = []

        if not self.name.strip():
            issues.append("Swarm name cannot be empty")

        if self.min_members < 1:
            issues.append("min_members must be at least 1")

        if self.max_members and self.max_members < self.min_members:
            issues.append("max_members must be >= min_members")

        if self.task_timeout_seconds <= 0:
            issues.append("task_timeout_seconds must be positive")

        if self.coordination_interval <= 0:
            issues.append("coordination_interval must be positive")

        return issues


# Exception classes
class SwarmError(Exception):
    """Base class for swarm errors."""

    pass


class SwarmInitializationError(SwarmError):
    """Raised when swarm initialization fails."""

    pass


class SwarmCoordinationError(SwarmError):
    """Raised when swarm coordination fails."""

    pass


class BaseSwarm(ABC):
    """
    Abstract base class for AI agent swarms.
    """

    def __init__(
        self, config: SwarmConfig, memory_manager: Optional[MemoryManager] = None
    ):
        """
        Initialize swarm with configuration.

        Args:
            config: Swarm configuration
            memory_manager: Optional shared memory manager
        """
        # Validate configuration
        config_issues = config.validate_config()
        if config_issues:
            raise SwarmInitializationError(f"Configuration issues: {config_issues}")

        self.config = config
        self.memory_manager = memory_manager

        # Swarm state
        self.state = SwarmState.INITIALIZING
        self.members: Dict[str, SwarmMember] = {}
        self.agents: Dict[str, BaseAgent] = {}

        # Task and message management
        self.task_queue: List[SwarmTask] = []
        self.active_tasks: Dict[str, SwarmTask] = {}
        self.completed_tasks: Dict[str, SwarmTask] = {}
        self.message_queue: List[SwarmMessage] = []

        # Performance tracking
        self.metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "messages_sent": 0,
            "coordination_cycles": 0,
            "uptime_seconds": 0,
        }

        # Coordination state
        self._coordination_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._start_time = datetime.utcnow()

        logger.info(f"Initialized swarm {config.name} ({config.swarm_id})")

    @abstractmethod
    async def coordinate(self) -> None:
        """
        Execute coordination cycle for the swarm.

        This method should be overridden by specific swarm implementations
        to define their coordination behavior.
        """
        pass

    @abstractmethod
    async def distribute_task(self, task: SwarmTask) -> bool:
        """
        Distribute task to appropriate agent(s).

        Args:
            task: Task to distribute

        Returns:
            bool: True if task was successfully distributed
        """
        pass

    async def initialize(self) -> None:
        """
        Initialize the swarm and prepare for operation.

        Raises:
            SwarmInitializationError: If initialization fails
        """
        try:
            self.state = SwarmState.INITIALIZING

            # Start coordination and health check loops
            self._coordination_task = asyncio.create_task(self._coordination_loop())
            self._health_check_task = asyncio.create_task(self._health_check_loop())

            self.state = SwarmState.IDLE
            logger.info(f"Swarm {self.config.name} initialized successfully")

        except Exception as e:
            self.state = SwarmState.ERROR
            logger.error(f"Swarm {self.config.name} initialization failed: {e}")
            raise SwarmInitializationError(f"Initialization failed: {e}")

    async def shutdown(self) -> None:
        """
        Gracefully shutdown the swarm.
        """
        try:
            # Cancel coordination and health check tasks
            if self._coordination_task:
                self._coordination_task.cancel()
                try:
                    await self._coordination_task
                except asyncio.CancelledError:
                    pass

            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass

            # Cancel active tasks
            for task in self.active_tasks.values():
                task.status = TaskStatus.CANCELLED

            # Shutdown all agents
            for agent in self.agents.values():
                try:
                    await agent.shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down agent: {e}")

            self.state = SwarmState.TERMINATED
            logger.info(f"Swarm {self.config.name} shutdown completed")

        except Exception as e:
            logger.error(f"Swarm {self.config.name} shutdown error: {e}")
            self.state = SwarmState.ERROR

    async def add_member(self, agent: BaseAgent, role: SwarmRole) -> bool:
        """
        Add agent as swarm member.

        Args:
            agent: Agent to add
            role: Role for the agent in swarm

        Returns:
            bool: True if agent was added successfully
        """
        if self.config.max_members and len(self.members) >= self.config.max_members:
            logger.warning("Cannot add agent - swarm at maximum capacity")
            return False

        agent_id = agent.config.agent_id

        if agent_id in self.members:
            logger.warning(f"Agent {agent_id} already in swarm")
            return False

        # Create swarm member
        member = SwarmMember(
            agent_id=agent_id,
            role=role,
            capabilities=list(
                agent.config.available_tools
            ),  # Use tools as capabilities
        )

        self.members[agent_id] = member
        self.agents[agent_id] = agent

        logger.info(f"Added agent {agent.config.name} to swarm with role {role.value}")
        return True

    async def remove_member(self, agent_id: str) -> bool:
        """
        Remove agent from swarm.

        Args:
            agent_id: Agent ID to remove

        Returns:
            bool: True if agent was removed successfully
        """
        if agent_id not in self.members:
            return False

        # Cancel any active tasks assigned to this agent
        for task in self.active_tasks.values():
            if task.assigned_to == agent_id:
                task.status = TaskStatus.CANCELLED
                self.task_queue.append(task)  # Re-queue for reassignment

        # Remove from members and agents
        member = self.members.pop(agent_id)
        self.agents.pop(agent_id, None)

        logger.info(f"Removed agent {agent_id} from swarm")
        return True

    async def submit_task(self, task: SwarmTask) -> None:
        """
        Submit task to swarm for execution.

        Args:
            task: Task to submit
        """
        if len(self.task_queue) >= self.config.task_queue_size:
            raise SwarmError("Task queue is full")

        self.task_queue.append(task)
        logger.info(f"Submitted task {task.id} to swarm {self.config.name}")

        # Trigger coordination if swarm is idle
        if self.state == SwarmState.IDLE:
            await self.coordinate()

    async def send_message(self, message: SwarmMessage) -> None:
        """
        Send message within swarm.

        Args:
            message: Message to send
        """
        if len(self.message_queue) >= self.config.message_queue_size:
            logger.warning("Message queue is full, dropping oldest message")
            self.message_queue.pop(0)

        self.message_queue.append(message)
        self.metrics["messages_sent"] += 1

        # Deliver message immediately if possible
        await self._deliver_message(message)

    async def broadcast_message(self, message: SwarmMessage) -> None:
        """
        Broadcast message to all appropriate members.

        Args:
            message: Message to broadcast
        """
        if not self.config.enable_broadcast:
            logger.warning("Broadcasting is disabled")
            return

        recipients = []

        if message.broadcast_to_roles:
            # Send to specific roles
            for member in self.members.values():
                if member.role in message.broadcast_to_roles:
                    recipients.append(member.agent_id)
        else:
            # Send to all members
            recipients = list(self.members.keys())

        for recipient_id in recipients:
            if recipient_id != message.sender_id:  # Don't send to sender
                recipient_message = SwarmMessage(
                    sender_id=message.sender_id,
                    recipient_id=recipient_id,
                    message_type=message.message_type,
                    content=message.content,
                    context=message.context.copy(),
                )
                await self.send_message(recipient_message)

    def get_available_members(
        self,
        required_capabilities: List[str] = None,
        preferred_roles: List[SwarmRole] = None,
    ) -> List[SwarmMember]:
        """
        Get available members matching criteria.

        Args:
            required_capabilities: Required capabilities
            preferred_roles: Preferred roles

        Returns:
            List[SwarmMember]: Available members
        """
        available = []

        for member in self.members.values():
            if not member.can_accept_task():
                continue

            # Check role requirements
            if preferred_roles and member.role not in preferred_roles:
                continue

            # Check capability requirements
            if required_capabilities:
                member_caps = set(member.capabilities)
                required_caps = set(required_capabilities)
                if not required_caps.issubset(member_caps):
                    continue

            available.append(member)

        # Sort by availability and performance
        available.sort(
            key=lambda m: (
                m.current_task_count,  # Prefer less busy members
                -m.success_rate,  # Prefer higher success rate
                m.average_response_time,  # Prefer faster members
            )
        )

        return available

    async def _coordination_loop(self) -> None:
        """Background coordination loop."""
        while True:
            try:
                await asyncio.sleep(self.config.coordination_interval)

                if self.state not in [SwarmState.TERMINATED, SwarmState.ERROR]:
                    await self.coordinate()
                    self.metrics["coordination_cycles"] += 1

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Coordination loop error: {e}")
                self.state = SwarmState.ERROR

    async def _health_check_loop(self) -> None:
        """Background health check loop."""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)

                if self.state not in [SwarmState.TERMINATED, SwarmState.ERROR]:
                    await self._perform_health_checks()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")

    async def _perform_health_checks(self) -> None:
        """Perform health checks on swarm components."""
        # Check member health
        inactive_members = []
        current_time = datetime.utcnow()

        for member in self.members.values():
            time_since_activity = (current_time - member.last_activity).total_seconds()

            # Mark as inactive if no activity for too long
            if time_since_activity > 300:  # 5 minutes
                member.status = "inactive"
                inactive_members.append(member.agent_id)

        if inactive_members:
            logger.warning(f"Found {len(inactive_members)} inactive members")

        # Check for overdue tasks
        overdue_tasks = [task for task in self.active_tasks.values() if task.is_overdue]

        if overdue_tasks:
            logger.warning(f"Found {len(overdue_tasks)} overdue tasks")
            # Could implement timeout handling here

        # Update uptime metric
        self.metrics["uptime_seconds"] = (
            current_time - self._start_time
        ).total_seconds()

    async def _deliver_message(self, message: SwarmMessage) -> None:
        """Deliver message to recipient(s)."""
        if message.is_broadcast:
            await self.broadcast_message(message)
        else:
            recipient_id = message.recipient_id
            if recipient_id in self.agents:
                # Convert to agent message format
                agent_message = AgentMessage(
                    sender_id=message.sender_id,
                    recipient_id=recipient_id,
                    content=message.content,
                    message_type=message.message_type,
                    context=message.context,
                )

                # This would integrate with agent messaging system
                message.mark_delivered()
                logger.debug(f"Delivered message {message.id} to {recipient_id}")

    def get_swarm_status(self) -> Dict[str, Any]:
        """
        Get current swarm status.

        Returns:
            Dict[str, Any]: Swarm status information
        """
        members_by_role = {}
        members_by_status = {}

        for member in self.members.values():
            # Count by role
            role = member.role.value
            members_by_role[role] = members_by_role.get(role, 0) + 1

            # Count by status
            status = member.status
            members_by_status[status] = members_by_status.get(status, 0) + 1

        return {
            "swarm_id": self.config.swarm_id,
            "name": self.config.name,
            "state": self.state.value,
            "topology": self.config.topology.value,
            "members": {
                "total": len(self.members),
                "by_role": members_by_role,
                "by_status": members_by_status,
            },
            "tasks": {
                "queued": len(self.task_queue),
                "active": len(self.active_tasks),
                "completed": len(self.completed_tasks),
            },
            "messages": {"queued": len(self.message_queue)},
            "metrics": self.metrics.copy(),
        }


class SwarmCoordinator(BaseSwarm):
    """
    Swarm that uses a centralized coordinator pattern.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.coordinator_id: Optional[str] = None

    async def coordinate(self) -> None:
        """Centralized coordination logic."""
        self.state = SwarmState.COORDINATING

        try:
            # Ensure we have a coordinator
            await self._ensure_coordinator()

            # Process pending tasks
            await self._process_task_queue()

            # Check active task status
            await self._check_active_tasks()

            # Balance workload if needed
            await self._balance_workload()

        except Exception as e:
            logger.error(f"Coordination error in {self.config.name}: {e}")
            raise SwarmCoordinationError(f"Coordination failed: {e}")
        finally:
            self.state = SwarmState.IDLE

    async def distribute_task(self, task: SwarmTask) -> bool:
        """Distribute task using coordinator pattern."""
        if not self.coordinator_id:
            await self._ensure_coordinator()

        if not self.coordinator_id:
            logger.error("No coordinator available for task distribution")
            return False

        # Find best member for task
        available_members = self.get_available_members(
            task.required_capabilities, task.preferred_roles
        )

        if not available_members:
            logger.warning(f"No available members for task {task.id}")
            return False

        # Select best member (first in sorted list)
        selected_member = available_members[0]

        # Assign task
        task.assign_to_agent(selected_member.agent_id)
        selected_member.assign_task()

        self.active_tasks[task.id] = task

        logger.info(f"Assigned task {task.id} to agent {selected_member.agent_id}")
        return True

    async def _ensure_coordinator(self) -> None:
        """Ensure swarm has an active coordinator."""
        if self.coordinator_id and self.coordinator_id in self.members:
            coordinator = self.members[self.coordinator_id]
            if coordinator.status == "active":
                return

        # Find new coordinator
        coordinators = [
            m
            for m in self.members.values()
            if m.role == SwarmRole.COORDINATOR and m.status == "active"
        ]

        if coordinators:
            # Select coordinator with best performance
            coordinators.sort(key=lambda m: (-m.success_rate, m.average_response_time))
            self.coordinator_id = coordinators[0].agent_id
            logger.info(f"Selected coordinator: {self.coordinator_id}")
        else:
            logger.warning("No active coordinators available")
            self.coordinator_id = None

    async def _process_task_queue(self) -> None:
        """Process queued tasks."""
        while (
            self.task_queue
            and len(self.active_tasks) < self.config.max_concurrent_tasks
        ):
            task = self.task_queue.pop(0)

            success = await self.distribute_task(task)
            if not success:
                # Put task back in queue if couldn't distribute
                self.task_queue.insert(0, task)
                break

    async def _check_active_tasks(self) -> None:
        """Check status of active tasks."""
        completed_tasks = []

        for task_id, task in self.active_tasks.items():
            if task.status in [
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
            ]:
                completed_tasks.append(task_id)

                # Update member statistics
                if task.assigned_to in self.members:
                    member = self.members[task.assigned_to]
                    success = task.status == TaskStatus.COMPLETED
                    exec_time = task.execution_time or 0.0
                    member.complete_task(success, exec_time)

                # Update swarm metrics
                if task.status == TaskStatus.COMPLETED:
                    self.metrics["tasks_completed"] += 1
                else:
                    self.metrics["tasks_failed"] += 1

        # Move completed tasks
        for task_id in completed_tasks:
            task = self.active_tasks.pop(task_id)
            self.completed_tasks[task_id] = task

    async def _balance_workload(self) -> None:
        """Balance workload across members."""
        if not self.config.load_balancing_enabled:
            return

        # Simple load balancing: reassign tasks from overloaded members
        overloaded_members = [
            m
            for m in self.members.values()
            if m.current_task_count > m.max_concurrent_tasks
        ]

        underloaded_members = [
            m
            for m in self.members.values()
            if m.can_accept_task() and m.current_task_count == 0
        ]

        if overloaded_members and underloaded_members:
            logger.info("Balancing workload across members")
            # Implementation would reassign tasks here


class SwarmExecutor(BaseSwarm):
    """
    Swarm focused on efficient task execution with minimal coordination overhead.
    """

    async def coordinate(self) -> None:
        """Lightweight coordination for execution focus."""
        self.state = SwarmState.COORDINATING

        try:
            # Quick task distribution
            await self._quick_task_distribution()

            # Fast status check
            await self._quick_status_check()

        except Exception as e:
            logger.error(f"Execution coordination error: {e}")
        finally:
            self.state = SwarmState.IDLE

    async def distribute_task(self, task: SwarmTask) -> bool:
        """Fast task distribution with minimal overhead."""
        available_members = self.get_available_members(
            task.required_capabilities, task.preferred_roles
        )

        if not available_members:
            return False

        # Quick selection - just pick first available
        selected_member = available_members[0]

        task.assign_to_agent(selected_member.agent_id)
        selected_member.assign_task()
        self.active_tasks[task.id] = task

        return True

    async def _quick_task_distribution(self) -> None:
        """Distribute tasks with minimal processing."""
        distributed = 0
        max_to_distribute = min(
            len(self.task_queue),
            self.config.max_concurrent_tasks - len(self.active_tasks),
        )

        while distributed < max_to_distribute and self.task_queue:
            task = self.task_queue.pop(0)
            if await self.distribute_task(task):
                distributed += 1
            else:
                self.task_queue.insert(0, task)
                break

    async def _quick_status_check(self) -> None:
        """Quick check of active tasks."""
        completed_task_ids = []

        for task_id, task in self.active_tasks.items():
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                completed_task_ids.append(task_id)

        for task_id in completed_task_ids:
            task = self.active_tasks.pop(task_id)
            self.completed_tasks[task_id] = task


class HierarchicalSwarm(SwarmCoordinator):
    """
    Swarm with hierarchical organization and clear command structure.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.hierarchy_levels: Dict[int, List[str]] = {}  # level -> agent_ids

    async def add_member(
        self, agent: BaseAgent, role: SwarmRole, level: int = 0
    ) -> bool:
        """Add member with hierarchy level."""
        success = await super().add_member(agent, role)

        if success:
            agent_id = agent.config.agent_id
            if level not in self.hierarchy_levels:
                self.hierarchy_levels[level] = []
            self.hierarchy_levels[level].append(agent_id)

            # Set up reporting relationships
            await self._setup_hierarchy_relationships(agent_id, level)

        return success

    async def _setup_hierarchy_relationships(self, agent_id: str, level: int) -> None:
        """Set up reporting relationships in hierarchy."""
        if level > 0 and level - 1 in self.hierarchy_levels:
            # Find supervisor in level above
            supervisors = self.hierarchy_levels[level - 1]
            if supervisors:
                supervisor_id = supervisors[0]  # Simple assignment to first supervisor

                # Update member relationships
                if agent_id in self.members:
                    self.members[agent_id].reports_to = supervisor_id

                if supervisor_id in self.members:
                    if agent_id not in self.members[supervisor_id].supervises:
                        self.members[supervisor_id].supervises.append(agent_id)


class PeerToPeerSwarm(BaseSwarm):
    """
    Swarm with peer-to-peer organization and distributed coordination.
    """

    async def coordinate(self) -> None:
        """Distributed coordination among peers."""
        self.state = SwarmState.COORDINATING

        try:
            # Each peer can contribute to coordination
            await self._distributed_task_assignment()
            await self._peer_status_sharing()

        except Exception as e:
            logger.error(f"P2P coordination error: {e}")
        finally:
            self.state = SwarmState.IDLE

    async def distribute_task(self, task: SwarmTask) -> bool:
        """Distribute task using peer consensus."""
        available_members = self.get_available_members(
            task.required_capabilities, task.preferred_roles
        )

        if not available_members:
            return False

        # Use simple random selection for P2P
        import random

        selected_member = random.choice(available_members)

        task.assign_to_agent(selected_member.agent_id)
        selected_member.assign_task()
        self.active_tasks[task.id] = task

        return True

    async def _distributed_task_assignment(self) -> None:
        """Distribute task assignment across peers."""
        # Each active member can claim tasks
        active_members = [
            m
            for m in self.members.values()
            if m.status == "active" and m.can_accept_task()
        ]

        for i, task in enumerate(list(self.task_queue)):
            if i >= len(active_members):
                break

            member = active_members[i]
            if task.can_be_executed_by(member):
                self.task_queue.remove(task)
                task.assign_to_agent(member.agent_id)
                member.assign_task()
                self.active_tasks[task.id] = task

    async def _peer_status_sharing(self) -> None:
        """Share status information among peers."""
        # Broadcast status updates to all peers
        status_message = SwarmMessage(
            sender_id="swarm_system",
            message_type="status_update",
            content=json.dumps(self.get_swarm_status()),
        )

        await self.broadcast_message(status_message)


class SwarmRegistry:
    """
    Registry for managing multiple swarms.
    """

    def __init__(self):
        self._swarms: Dict[str, BaseSwarm] = {}
        logger.info("Initialized swarm registry")

    def register_swarm(self, swarm: BaseSwarm) -> None:
        """
        Register a swarm.

        Args:
            swarm: Swarm to register
        """
        swarm_id = swarm.config.swarm_id
        self._swarms[swarm_id] = swarm
        logger.info(f"Registered swarm {swarm.config.name} ({swarm_id})")

    def unregister_swarm(self, swarm_id: str) -> bool:
        """
        Unregister a swarm.

        Args:
            swarm_id: Swarm ID to unregister

        Returns:
            bool: True if swarm was unregistered
        """
        if swarm_id in self._swarms:
            swarm = self._swarms.pop(swarm_id)
            logger.info(f"Unregistered swarm {swarm.config.name} ({swarm_id})")
            return True
        return False

    def get_swarm(self, swarm_id: str) -> Optional[BaseSwarm]:
        """
        Get swarm by ID.

        Args:
            swarm_id: Swarm ID

        Returns:
            Optional[BaseSwarm]: Swarm if found
        """
        return self._swarms.get(swarm_id)

    def list_swarms(self) -> List[str]:
        """
        List all registered swarm IDs.

        Returns:
            List[str]: Swarm IDs
        """
        return list(self._swarms.keys())

    async def shutdown_all_swarms(self) -> None:
        """Shutdown all registered swarms."""
        for swarm in self._swarms.values():
            try:
                await swarm.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down swarm {swarm.config.name}: {e}")

    def get_registry_status(self) -> Dict[str, Any]:
        """
        Get registry status.

        Returns:
            Dict[str, Any]: Registry status information
        """
        swarms_by_state = {}
        swarms_by_topology = {}

        for swarm in self._swarms.values():
            # Count by state
            state = swarm.state.value
            swarms_by_state[state] = swarms_by_state.get(state, 0) + 1

            # Count by topology
            topology = swarm.config.topology.value
            swarms_by_topology[topology] = swarms_by_topology.get(topology, 0) + 1

        return {
            "total_swarms": len(self._swarms),
            "swarms_by_state": swarms_by_state,
            "swarms_by_topology": swarms_by_topology,
            "swarm_details": {
                swarm_id: swarm.get_swarm_status()
                for swarm_id, swarm in self._swarms.items()
            },
        }
