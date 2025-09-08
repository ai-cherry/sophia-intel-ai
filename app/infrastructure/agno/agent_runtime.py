"""
AGNO (Agent-Orchestrated Nodes) Runtime Base Class
Provides standardized runtime for micro-agents with lifecycle management,
resource monitoring, and error isolation
"""

import asyncio
import logging
import time
import traceback
from abc import ABC, abstractmethod
from collections.abc import Callable
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import psutil

from app.swarms.communication.message_bus import MessageBus

logger = logging.getLogger(__name__)

# ==================== Agent Status Enum ====================


class AgentStatus(Enum):
    """Agent lifecycle states"""

    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    RECOVERING = "recovering"


# ==================== Resource Metrics ====================


@dataclass
class ResourceMetrics:
    """Resource usage metrics for an agent"""

    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_percent: float = 0.0
    thread_count: int = 0
    io_read_bytes: int = 0
    io_write_bytes: int = 0
    network_sent_bytes: int = 0
    network_recv_bytes: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "memory_percent": self.memory_percent,
            "thread_count": self.thread_count,
            "io_read_bytes": self.io_read_bytes,
            "io_write_bytes": self.io_write_bytes,
            "network_sent_bytes": self.network_sent_bytes,
            "network_recv_bytes": self.network_recv_bytes,
            "timestamp": self.timestamp.isoformat(),
        }


# ==================== Agent Event ====================


@dataclass
class AgentEvent:
    """Event emitted by an agent"""

    agent_id: str
    event_type: str
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "agent_id": self.agent_id,
            "event_type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }


# ==================== AGNO Agent Base Class ====================


class AGNOAgent(ABC):
    """
    Base class for all AGNO agents providing lifecycle management,
    resource monitoring, and error isolation
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str = "generic",
        config: Optional[dict[str, Any]] = None,
        event_bus: Optional[MessageBus] = None,
        max_errors: int = 3,
        recovery_delay: float = 5.0,
    ):
        """
        Initialize AGNO agent

        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of agent (watcher, learner, executor, etc.)
            config: Agent configuration
            event_bus: Message bus for event emission
            max_errors: Maximum errors before stopping
            recovery_delay: Delay before recovery attempt
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.config = config or {}
        self.event_bus = event_bus or MessageBus()
        self.max_errors = max_errors
        self.recovery_delay = recovery_delay

        # State management
        self.status = AgentStatus.INITIALIZING
        self.error_count = 0
        self.last_error: Optional[Exception] = None
        self.start_time: Optional[datetime] = None
        self.stop_time: Optional[datetime] = None

        # Resource monitoring
        self.process: psutil.Optional[Process] = None
        self.resources = ResourceMetrics()
        self.resource_history: list[ResourceMetrics] = []
        self.max_resource_history = 100

        # Lifecycle hooks
        self._running = False
        self._task: asyncio.Optional[Task] = None
        self._monitor_task: asyncio.Optional[Task] = None
        self._event_handlers: dict[str, list[Callable]] = {}

        # Performance metrics
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_execution_time = 0.0

        logger.info(f"AGNO Agent {agent_id} initialized (type: {agent_type})")

    # ==================== Abstract Methods ====================

    @abstractmethod
    async def execute(self) -> Any:
        """
        Main execution logic for the agent.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    async def validate_config(self) -> bool:
        """
        Validate agent configuration.
        Must be implemented by subclasses.
        """
        pass

    # ==================== Lifecycle Methods ====================

    async def start(self) -> None:
        """Start the agent"""
        if self.status in [AgentStatus.RUNNING, AgentStatus.RECOVERING]:
            logger.warning(f"Agent {self.agent_id} already running")
            return

        logger.info(f"Starting AGNO agent {self.agent_id}")

        # Validate configuration
        if not await self.validate_config():
            raise ValueError(f"Invalid configuration for agent {self.agent_id}")

        # Initialize process monitoring
        self.process = psutil.Process()

        # Update status
        self.status = AgentStatus.READY
        self.start_time = datetime.utcnow()
        self._running = True

        # Emit start event
        await self.emit_event("agent.start", {"agent_type": self.agent_type, "config": self.config})

        # Start execution and monitoring tasks
        self._task = asyncio.create_task(self._execution_loop())
        self._monitor_task = asyncio.create_task(self._monitor_loop())

        self.status = AgentStatus.RUNNING
        logger.info(f"AGNO agent {self.agent_id} started successfully")

    async def stop(self) -> None:
        """Stop the agent gracefully"""
        if self.status == AgentStatus.STOPPED:
            logger.warning(f"Agent {self.agent_id} already stopped")
            return

        logger.info(f"Stopping AGNO agent {self.agent_id}")

        self.status = AgentStatus.STOPPING
        self._running = False

        # Cancel tasks
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

        if self._monitor_task:
            self._monitor_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._monitor_task

        # Update status
        self.status = AgentStatus.STOPPED
        self.stop_time = datetime.utcnow()

        # Emit stop event
        await self.emit_event(
            "agent.stop",
            {
                "runtime_seconds": (
                    (self.stop_time - self.start_time).total_seconds() if self.start_time else 0
                ),
                "execution_count": self.execution_count,
                "success_count": self.success_count,
                "failure_count": self.failure_count,
            },
        )

        logger.info(f"AGNO agent {self.agent_id} stopped")

    async def pause(self) -> None:
        """Pause agent execution"""
        if self.status != AgentStatus.RUNNING:
            logger.warning(f"Cannot pause agent {self.agent_id} - not running")
            return

        self.status = AgentStatus.PAUSED
        await self.emit_event("agent.pause", {})
        logger.info(f"AGNO agent {self.agent_id} paused")

    async def resume(self) -> None:
        """Resume agent execution"""
        if self.status != AgentStatus.PAUSED:
            logger.warning(f"Cannot resume agent {self.agent_id} - not paused")
            return

        self.status = AgentStatus.RUNNING
        await self.emit_event("agent.resume", {})
        logger.info(f"AGNO agent {self.agent_id} resumed")

    # ==================== Execution Loop ====================

    async def _execution_loop(self) -> None:
        """Main execution loop with error handling and recovery"""
        while self._running:
            if self.status == AgentStatus.PAUSED:
                await asyncio.sleep(1)
                continue

            try:
                start_time = time.time()

                # Execute agent logic
                result = await self.execute()

                # Update metrics
                execution_time = time.time() - start_time
                self.execution_count += 1
                self.success_count += 1
                self.total_execution_time += execution_time

                # Emit execution event
                await self.emit_event(
                    "agent.execution",
                    {
                        "success": True,
                        "execution_time": execution_time,
                        "result": (
                            result
                            if isinstance(result, (dict, list, str, int, float, bool))
                            else str(result)
                        ),
                    },
                )

                # Reset error count on success
                self.error_count = 0

            except Exception as e:
                # Handle execution error
                self.error_count += 1
                self.failure_count += 1
                self.last_error = e

                logger.error(
                    f"Agent {self.agent_id} execution failed: {e}\n{traceback.format_exc()}"
                )

                await self.emit_event(
                    "agent.error",
                    {
                        "error": str(e),
                        "error_count": self.error_count,
                        "traceback": traceback.format_exc(),
                    },
                )

                # Check if max errors exceeded
                if self.error_count >= self.max_errors:
                    logger.error(f"Agent {self.agent_id} max errors exceeded - attempting recovery")
                    await self._attempt_recovery()
                else:
                    # Brief delay before retry
                    await asyncio.sleep(1)

            # Yield control
            await asyncio.sleep(0.1)

    async def _attempt_recovery(self) -> None:
        """Attempt to recover from errors"""
        self.status = AgentStatus.RECOVERING

        await self.emit_event(
            "agent.recovery.start",
            {"error_count": self.error_count, "last_error": str(self.last_error)},
        )

        # Wait before recovery
        await asyncio.sleep(self.recovery_delay)

        try:
            # Attempt to reinitialize
            if await self.validate_config():
                self.error_count = 0
                self.status = AgentStatus.RUNNING

                await self.emit_event("agent.recovery.success", {})
                logger.info(f"Agent {self.agent_id} recovered successfully")
            else:
                raise ValueError("Configuration validation failed during recovery")

        except Exception as e:
            # Recovery failed - stop agent
            logger.error(f"Agent {self.agent_id} recovery failed: {e}")

            await self.emit_event("agent.recovery.failed", {"error": str(e)})

            self.status = AgentStatus.ERROR
            self._running = False

    # ==================== Resource Monitoring ====================

    async def _monitor_loop(self) -> None:
        """Monitor resource usage"""
        while self._running:
            try:
                await self.monitor_resources()
                await asyncio.sleep(5)  # Monitor every 5 seconds
            except Exception as e:
                logger.error(f"Resource monitoring failed for agent {self.agent_id}: {e}")
                await asyncio.sleep(5)

    async def monitor_resources(self) -> ResourceMetrics:
        """Monitor and update resource metrics"""
        if not self.process:
            return self.resources

        try:
            # Get process info
            with self.process.oneshot():
                cpu_percent = self.process.cpu_percent()
                memory_info = self.process.memory_info()
                io_counters = (
                    self.process.io_counters() if hasattr(self.process, "io_counters") else None
                )

                # Update metrics
                self.resources = ResourceMetrics(
                    cpu_percent=cpu_percent,
                    memory_mb=memory_info.rss / 1024 / 1024,
                    memory_percent=self.process.memory_percent(),
                    thread_count=self.process.num_threads(),
                    io_read_bytes=io_counters.read_bytes if io_counters else 0,
                    io_write_bytes=io_counters.write_bytes if io_counters else 0,
                )

                # Add to history
                self.resource_history.append(self.resources)
                if len(self.resource_history) > self.max_resource_history:
                    self.resource_history.pop(0)

                # Emit resource event if significant change
                if cpu_percent > 80 or self.resources.memory_percent > 80:
                    await self.emit_event("agent.resources.high", self.resources.to_dict())

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.warning(f"Could not monitor resources for agent {self.agent_id}: {e}")

        return self.resources

    # ==================== Event Management ====================

    async def emit_event(self, event_type: str, data: dict[str, Any]) -> None:
        """
        Emit an event to the event bus

        Args:
            event_type: Type of event
            data: Event data
        """
        event = AgentEvent(agent_id=self.agent_id, event_type=event_type, data=data)

        # Emit to event bus
        if self.event_bus:
            await self.event_bus.publish(f"agno.{self.agent_type}.{event_type}", event.to_dict())

        # Call local handlers
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    await handler(event) if asyncio.iscoroutinefunction(handler) else handler(event)
                except Exception as e:
                    logger.error(f"Event handler failed for {event_type}: {e}")

    def on_event(self, event_type: str, handler: Callable) -> None:
        """
        Register an event handler

        Args:
            event_type: Type of event to handle
            handler: Handler function
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    # ==================== Status and Metrics ====================

    def get_status(self) -> dict[str, Any]:
        """Get current agent status"""
        runtime = None
        if self.start_time:
            if self.stop_time:
                runtime = (self.stop_time - self.start_time).total_seconds()
            else:
                runtime = (datetime.utcnow() - self.start_time).total_seconds()

        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "error_count": self.error_count,
            "last_error": str(self.last_error) if self.last_error else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "runtime_seconds": runtime,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "avg_execution_time": (
                self.total_execution_time / self.execution_count if self.execution_count > 0 else 0
            ),
            "resources": self.resources.to_dict(),
        }

    def get_metrics(self) -> dict[str, Any]:
        """Get performance metrics"""
        return {
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": (
                self.success_count / self.execution_count if self.execution_count > 0 else 0
            ),
            "avg_execution_time": (
                self.total_execution_time / self.execution_count if self.execution_count > 0 else 0
            ),
            "total_execution_time": self.total_execution_time,
            "error_count": self.error_count,
            "resource_history": [
                m.to_dict() for m in self.resource_history[-10:]
            ],  # Last 10 samples
        }

    # ==================== Context Manager ====================

    @asynccontextmanager
    async def run_context(self):
        """Context manager for agent execution"""
        try:
            await self.start()
            yield self
        finally:
            await self.stop()


# ==================== Example Agent Implementations ====================


class WatcherAgent(AGNOAgent):
    """Example watcher agent that monitors for specific conditions"""

    def __init__(self, agent_id: str, watch_target: str, **kwargs):
        super().__init__(agent_id, agent_type="watcher", **kwargs)
        self.watch_target = watch_target

    async def validate_config(self) -> bool:
        """Validate watcher configuration"""
        return bool(self.watch_target)

    async def execute(self) -> dict[str, Any]:
        """Execute watching logic"""
        # Simulate watching
        await asyncio.sleep(1)

        # Return mock observation
        return {
            "target": self.watch_target,
            "observation": "normal",
            "timestamp": datetime.utcnow().isoformat(),
        }


class LearnerAgent(AGNOAgent):
    """Example learner agent that learns from data"""

    def __init__(self, agent_id: str, learning_rate: float = 0.01, **kwargs):
        super().__init__(agent_id, agent_type="learner", **kwargs)
        self.learning_rate = learning_rate
        self.knowledge_base = {}

    async def validate_config(self) -> bool:
        """Validate learner configuration"""
        return 0 < self.learning_rate <= 1

    async def execute(self) -> dict[str, Any]:
        """Execute learning logic"""
        # Simulate learning
        await asyncio.sleep(0.5)

        # Update knowledge base
        new_knowledge = f"learned_{len(self.knowledge_base)}"
        self.knowledge_base[new_knowledge] = datetime.utcnow().isoformat()

        return {
            "learned": new_knowledge,
            "knowledge_size": len(self.knowledge_base),
            "learning_rate": self.learning_rate,
        }


class ExecutorAgent(AGNOAgent):
    """Example executor agent that performs actions"""

    def __init__(self, agent_id: str, action_type: str = "default", **kwargs):
        super().__init__(agent_id, agent_type="executor", **kwargs)
        self.action_type = action_type

    async def validate_config(self) -> bool:
        """Validate executor configuration"""
        return bool(self.action_type)

    async def execute(self) -> dict[str, Any]:
        """Execute action logic"""
        # Simulate action execution
        await asyncio.sleep(0.3)

        return {
            "action": self.action_type,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
        }
