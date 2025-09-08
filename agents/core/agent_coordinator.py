#!/usr/bin/env python3
"""
Sophia AI Agent Coordinator - Orchestrates Multiple Agents
Provides intelligent task routing, load balancing, and agent lifecycle management
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .base_agent import AgentCapability, AgentStatus, BaseAgent

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    """Task execution status"""

    PENDING = "pending"
    ASSIGNED = "assigned"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Task representation for agent coordination"""

    task_id: str
    task_type: str
    data: dict[str, Any]
    required_capabilities: list[AgentCapability]
    priority: TaskPriority = TaskPriority.NORMAL
    timeout_seconds: int = 300
    retry_attempts: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    assigned_agent_id: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    result: dict[str, Any] | None = None
    error: str | None = None
    processing_start: datetime | None = None
    processing_end: datetime | None = None

    def __post_init__(self):
        if not self.task_id:
            self.task_id = str(uuid.uuid4())


@dataclass
class AgentInfo:
    """Agent information for coordination"""

    agent: BaseAgent
    capabilities: set[AgentCapability]
    max_concurrent_tasks: int
    current_task_count: int = 0
    last_activity: datetime | None = None
    health_score: float = 1.0
    average_processing_time: float = 0.0

    @property
    def is_available(self) -> bool:
        """Check if agent is available for new tasks"""
        return (
            self.agent.status == AgentStatus.READY
            and self.current_task_count < self.max_concurrent_tasks
            and self.health_score > 0.5
        )

    @property
    def load_factor(self) -> float:
        """Calculate current load factor (0.0 to 1.0)"""
        if self.max_concurrent_tasks == 0:
            return 1.0
        return self.current_task_count / self.max_concurrent_tasks


class AgentCoordinator:
    """
    Coordinates multiple agents for intelligent task distribution
    Provides load balancing, health monitoring, and task routing
    """

    def __init__(self, max_queue_size: int = 1000):
        self.agents: dict[str, AgentInfo] = {}
        self.task_queue: list[Task] = []
        self.active_tasks: dict[str, Task] = {}
        self.completed_tasks: dict[str, Task] = {}
        self.max_queue_size = max_queue_size
        self.coordinator_id = str(uuid.uuid4())
        self.is_running = False
        self.processing_task = None

        logger.info(f"Agent Coordinator initialized [{self.coordinator_id[:8]}]")

    async def start(self) -> None:
        """Start the coordinator"""
        if self.is_running:
            logger.warning("Coordinator is already running")
            return

        self.is_running = True
        self.processing_task = asyncio.create_task(self._process_tasks())
        logger.info("Agent Coordinator started")

    async def stop(self) -> None:
        """Stop the coordinator"""
        if not self.is_running:
            return

        self.is_running = False

        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        # Cancel all active tasks
        for task in self.active_tasks.values():
            task.status = TaskStatus.CANCELLED

        logger.info("Agent Coordinator stopped")

    def register_agent(self, agent: BaseAgent) -> bool:
        """Register an agent with the coordinator"""
        try:
            if agent.agent_id in self.agents:
                logger.warning(f"Agent {agent.agent_id} is already registered")
                return False

            agent_info = AgentInfo(
                agent=agent,
                capabilities=set(agent.config.capabilities),
                max_concurrent_tasks=agent.config.max_concurrent_tasks,
            )

            self.agents[agent.agent_id] = agent_info
            logger.info(f"Registered agent {agent.config.agent_name} [{agent.agent_id[:8]}]")
            return True

        except Exception as e:
            logger.error(f"Failed to register agent: {str(e)}")
            return False

    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the coordinator"""
        try:
            if agent_id not in self.agents:
                logger.warning(f"Agent {agent_id} is not registered")
                return False

            agent_info = self.agents[agent_id]

            # Cancel any active tasks for this agent
            tasks_to_cancel = [
                task for task in self.active_tasks.values() if task.assigned_agent_id == agent_id
            ]

            for task in tasks_to_cancel:
                task.status = TaskStatus.CANCELLED
                task.error = "Agent unregistered"
                self.active_tasks.pop(task.task_id, None)
                self.completed_tasks[task.task_id] = task

            del self.agents[agent_id]
            logger.info(f"Unregistered agent {agent_info.agent.config.agent_name} [{agent_id[:8]}]")
            return True

        except Exception as e:
            logger.error(f"Failed to unregister agent: {str(e)}")
            return False

    async def submit_task(self, task: Task) -> str:
        """Submit a task for processing"""
        try:
            if len(self.task_queue) >= self.max_queue_size:
                raise ValueError("Task queue is full")

            # Sort queue by priority
            self.task_queue.append(task)
            self.task_queue.sort(key=lambda t: t.priority.value, reverse=True)

            logger.info(f"Task {task.task_id} submitted (priority: {task.priority.value})")
            return task.task_id

        except Exception as e:
            logger.error(f"Failed to submit task: {str(e)}")
            raise

    async def get_task_status(self, task_id: str) -> dict[str, Any] | None:
        """Get the status of a specific task"""
        # Check active tasks
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return self._task_to_dict(task)

        # Check completed tasks
        if task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
            return self._task_to_dict(task)

        # Check pending tasks
        for task in self.task_queue:
            if task.task_id == task_id:
                return self._task_to_dict(task)

        return None

    def get_coordinator_status(self) -> dict[str, Any]:
        """Get coordinator status and metrics"""
        return {
            "coordinator_id": self.coordinator_id,
            "is_running": self.is_running,
            "registered_agents": len(self.agents),
            "pending_tasks": len(self.task_queue),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "agents": {
                agent_id: {
                    "name": info.agent.config.agent_name,
                    "status": info.agent.status.value,
                    "capabilities": [cap.value for cap in info.capabilities],
                    "current_tasks": info.current_task_count,
                    "max_tasks": info.max_concurrent_tasks,
                    "load_factor": info.load_factor,
                    "health_score": info.health_score,
                    "is_available": info.is_available,
                }
                for agent_id, info in self.agents.items()
            },
            "timestamp": datetime.now().isoformat(),
        }

    async def _process_tasks(self) -> None:
        """Main task processing loop"""
        while self.is_running:
            try:
                await self._process_pending_tasks()
                await self._check_active_tasks()
                await self._update_agent_health()
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting

            except Exception as e:
                logger.error(f"Error in task processing loop: {str(e)}")
                await asyncio.sleep(1.0)  # Longer delay on error

    async def _process_pending_tasks(self) -> None:
        """Process pending tasks by assigning them to available agents"""
        while self.task_queue and self.is_running:
            task = self.task_queue[0]

            # Find best agent for this task
            best_agent = self._find_best_agent(task)

            if best_agent is None:
                # No available agents, wait
                break

            # Remove task from queue and assign to agent
            self.task_queue.pop(0)
            task.assigned_agent_id = best_agent.agent.agent_id
            task.status = TaskStatus.ASSIGNED
            task.processing_start = datetime.now()

            # Start processing
            asyncio.create_task(self._execute_task(task, best_agent))

            self.active_tasks[task.task_id] = task
            best_agent.current_task_count += 1

            logger.info(
                f"Assigned task {task.task_id} to agent {best_agent.agent.config.agent_name}"
            )

    async def _execute_task(self, task: Task, agent_info: AgentInfo) -> None:
        """Execute a task on a specific agent"""
        try:
            task.status = TaskStatus.PROCESSING

            # Execute the task
            result = await agent_info.agent.process_task(task.task_id, task.data)

            # Update task with result
            task.result = result
            task.status = (
                TaskStatus.COMPLETED if result.get("status") == "success" else TaskStatus.FAILED
            )
            task.error = result.get("error")
            task.processing_end = datetime.now()

            # Update agent info
            if task.processing_start and task.processing_end:
                processing_time = (task.processing_end - task.processing_start).total_seconds()
                agent_info.average_processing_time = (agent_info.average_processing_time * 0.8) + (
                    processing_time * 0.2
                )

            agent_info.last_activity = datetime.now()

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.processing_end = datetime.now()
            logger.error(f"Task {task.task_id} failed: {str(e)}")

        finally:
            # Move task to completed and update agent
            self.active_tasks.pop(task.task_id, None)
            self.completed_tasks[task.task_id] = task
            agent_info.current_task_count = max(0, agent_info.current_task_count - 1)

    async def _check_active_tasks(self) -> None:
        """Check for timed out active tasks"""
        current_time = datetime.now()
        timed_out_tasks = []

        for task in self.active_tasks.values():
            if task.processing_start:
                elapsed = (current_time - task.processing_start).total_seconds()
                if elapsed > task.timeout_seconds:
                    timed_out_tasks.append(task)

        for task in timed_out_tasks:
            task.status = TaskStatus.FAILED
            task.error = "Task timed out"
            task.processing_end = current_time

            # Update agent info
            if task.assigned_agent_id and task.assigned_agent_id in self.agents:
                agent_info = self.agents[task.assigned_agent_id]
                agent_info.current_task_count = max(0, agent_info.current_task_count - 1)
                agent_info.health_score *= 0.9  # Reduce health score for timeout

            self.active_tasks.pop(task.task_id, None)
            self.completed_tasks[task.task_id] = task

            logger.warning(f"Task {task.task_id} timed out after {task.timeout_seconds}s")

    async def _update_agent_health(self) -> None:
        """Update agent health scores based on performance"""
        for agent_info in self.agents.values():
            try:
                # Get agent status
                status = agent_info.agent.get_status()
                metrics = status.get("metrics", {})

                # Calculate health score based on error rate and responsiveness
                error_rate = metrics.get("error_rate", 0.0)
                health_score = max(0.1, 1.0 - error_rate)

                # Factor in agent status
                if agent_info.agent.status != AgentStatus.READY:
                    health_score *= 0.5

                # Smooth health score changes
                agent_info.health_score = (agent_info.health_score * 0.8) + (health_score * 0.2)

            except Exception as e:
                logger.error(
                    f"Failed to update health for agent {agent_info.agent.agent_id}: {str(e)}"
                )
                agent_info.health_score *= 0.9  # Reduce health on error

    def _find_best_agent(self, task: Task) -> AgentInfo | None:
        """Find the best available agent for a task"""
        suitable_agents = []

        for agent_info in self.agents.values():
            # Check if agent is available and has required capabilities
            if agent_info.is_available and all(
                cap in agent_info.capabilities for cap in task.required_capabilities
            ):
                suitable_agents.append(agent_info)

        if not suitable_agents:
            return None

        # Score agents based on load, health, and performance
        def agent_score(agent_info: AgentInfo) -> float:
            load_score = 1.0 - agent_info.load_factor  # Lower load is better
            health_score = agent_info.health_score
            performance_score = 1.0 / (1.0 + agent_info.average_processing_time)  # Faster is better

            return (load_score * 0.4) + (health_score * 0.4) + (performance_score * 0.2)

        # Return agent with highest score
        return max(suitable_agents, key=agent_score)

    def _task_to_dict(self, task: Task) -> dict[str, Any]:
        """Convert task to dictionary representation"""
        return {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "status": task.status.value,
            "priority": task.priority.value,
            "assigned_agent_id": task.assigned_agent_id,
            "created_at": task.created_at.isoformat(),
            "processing_start": (
                task.processing_start.isoformat() if task.processing_start else None
            ),
            "processing_end": (task.processing_end.isoformat() if task.processing_end else None),
            "result": task.result,
            "error": task.error,
            "required_capabilities": [cap.value for cap in task.required_capabilities],
        }
