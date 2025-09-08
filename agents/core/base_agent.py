#!/usr/bin/env python3
"""
Sophia AI BaseAgent - Unified Foundation for All Sophia AI Agents
Provides standardized lifecycle, error handling, logging, and MCP integration
"""

import asyncio
import contextlib
import logging
import os
import traceback
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent lifecycle status"""

    INITIALIZING = "initializing"
    READY = "ready"
    PROCESSING = "processing"
    ERROR = "error"
    STOPPING = "stopping"
    STOPPED = "stopped"


class AgentCapability(Enum):
    """Standard agent capabilities"""

    ANALYSIS = "analysis"
    GENERATION = "generation"
    OPTIMIZATION = "optimization"
    VALIDATION = "validation"
    INTEGRATION = "integration"
    MONITORING = "monitoring"
    RECOVERY = "recovery"
    ALERTING = "alerting"
    MAINTENANCE = "maintenance"


@dataclass
class ResilienceConfig:
    """Optional resilience configuration for agents"""

    enabled: bool = False
    max_retries: int = 3
    retry_delay: float = 1.0
    exponential_backoff: bool = True
    checkpoint_interval: int = 0  # seconds
    health_check_interval: int = 0  # seconds
    guardian_enabled: bool = False
    auto_recovery: bool = False


@dataclass
class AgentConfig:
    """Standardized agent configuration"""

    agent_id: str
    agent_name: str
    agent_type: str
    capabilities: list[AgentCapability]
    max_concurrent_tasks: int = 5
    timeout_seconds: int = 300
    retry_attempts: int = 3
    log_level: str = "INFO"
    enable_metrics: bool = True
    enable_mcp: bool = True
    mcp_port: int | None = None
    environment: str = "development"
    resilience: ResilienceConfig | None = None

    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.agent_id:
            self.agent_id = str(uuid.uuid4())
        if self.max_concurrent_tasks < 1:
            self.max_concurrent_tasks = 1
        if self.timeout_seconds < 1:
            self.timeout_seconds = 300


@dataclass
class AgentMetrics:
    """Agent performance and health metrics"""

    agent_id: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0
    last_activity: datetime | None = None
    error_rate: float = 0.0
    uptime_seconds: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

    def update_task_completion(self, processing_time: float, success: bool = True):
        """Update metrics after task completion"""
        if success:
            self.tasks_completed += 1
        else:
            self.tasks_failed += 1

        self.total_processing_time += processing_time
        total_tasks = self.tasks_completed + self.tasks_failed
        if total_tasks > 0:
            self.average_processing_time = self.total_processing_time / total_tasks
            self.error_rate = self.tasks_failed / total_tasks

        self.last_activity = datetime.now()


class BaseAgent(ABC):
    """
    Unified base class for all Sophia AI agents
    Provides standardized lifecycle, error handling, logging, and MCP integration
    """

    def __init__(self, config: AgentConfig):
        """Initialize base agent with configuration"""
        self.config = config
        self.agent_id = config.agent_id
        self.status = AgentStatus.INITIALIZING
        self.metrics = AgentMetrics(agent_id=self.agent_id)
        self.start_time = datetime.now()
        self.active_tasks: dict[str, asyncio.Task] = {}
        self.mcp_server = None
        self.resilience_config = config.resilience or ResilienceConfig()
        self._background_tasks: list[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()

        # Configure logging
        self.logger = logging.getLogger(
            f"{self.__class__.__name__}[{self.agent_id[:8]}]"
        )
        self.logger.setLevel(getattr(logging, config.log_level.upper()))

        self.logger.info(f"Initializing {config.agent_name} ({config.agent_type})")

    async def initialize(self) -> bool:
        """Initialize the agent with all dependencies"""
        try:
            self.logger.info("Starting agent initialization...")

            # Validate configuration
            await self._validate_configuration()

            # Setup dependencies
            await self._setup_dependencies()

            # Initialize agent-specific components
            await self._initialize_agent_specific()

            # Setup MCP server if enabled
            if self.config.enable_mcp:
                await self._setup_mcp_server()

            # Start resilience features
            if self.resilience_config.enabled:
                await self._start_resilience_features()

            self.status = AgentStatus.READY
            self.logger.info("Agent initialization completed successfully")
            return True

        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"Agent initialization failed: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return False

    async def shutdown(self) -> bool:
        """Gracefully shutdown the agent"""
        try:
            self.logger.info("Starting agent shutdown...")
            self.status = AgentStatus.STOPPING

            # Cancel active tasks
            await self._cancel_active_tasks()

            # Cleanup agent-specific resources
            await self._cleanup_agent_specific()

            # Cleanup dependencies
            await self._cleanup_dependencies()

            # Stop MCP server
            if self.mcp_server:
                await self._stop_mcp_server()

            # Stop resilience background tasks
            self._shutdown_event.set()
            for task in self._background_tasks:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

            self.status = AgentStatus.STOPPED
            self.logger.info("Agent shutdown completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Agent shutdown failed: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return False

    async def process_task(
        self, task_id: str, task_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Process a task with standardized error handling and metrics"""
        start_time = datetime.now()

        try:
            self.logger.info(f"Starting task {task_id}")
            self.status = AgentStatus.PROCESSING

            # Validate task data
            await self._validate_task_data(task_data)

            # Process the task (implemented by subclass)
            result = await self._process_task_impl(task_id, task_data)

            # Update metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            self.metrics.update_task_completion(processing_time, success=True)

            self.logger.info(
                f"Task {task_id} completed successfully in {processing_time:.2f}s"
            )
            self.status = AgentStatus.READY

            return {
                "task_id": task_id,
                "status": "success",
                "result": result,
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            # Update metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            self.metrics.update_task_completion(processing_time, success=False)

            self.logger.error(f"Task {task_id} failed: {str(e)}")
            self.logger.debug(traceback.format_exc())
            self.status = AgentStatus.READY

            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e),
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat(),
            }

    def get_status(self) -> dict[str, Any]:
        """Get current agent status and metrics"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        self.metrics.uptime_seconds = uptime

        return {
            "agent_id": self.agent_id,
            "agent_name": self.config.agent_name,
            "agent_type": self.config.agent_type,
            "status": self.status.value,
            "capabilities": [cap.value for cap in self.config.capabilities],
            "metrics": {
                "tasks_completed": self.metrics.tasks_completed,
                "tasks_failed": self.metrics.tasks_failed,
                "error_rate": self.metrics.error_rate,
                "average_processing_time": self.metrics.average_processing_time,
                "uptime_seconds": self.metrics.uptime_seconds,
                "last_activity": (
                    self.metrics.last_activity.isoformat()
                    if self.metrics.last_activity
                    else None
                ),
            },
            "active_tasks": len(self.active_tasks),
            "timestamp": datetime.now().isoformat(),
        }

    # Abstract methods that must be implemented by subclasses
    @abstractmethod
    async def _initialize_agent_specific(self) -> None:
        """Initialize agent-specific components (implemented by subclass)"""

    @abstractmethod
    async def _process_task_impl(self, task_id: str, task_data: dict[str, Any]) -> Any:
        """Process a specific task (implemented by subclass)"""

    @abstractmethod
    async def _cleanup_agent_specific(self) -> None:
        """Cleanup agent-specific resources (implemented by subclass)"""

    # Protected methods for common functionality
    async def _validate_configuration(self) -> None:
        """Validate agent configuration"""
        if not self.config.agent_name:
            raise ValueError("Agent name is required")
        if not self.config.agent_type:
            raise ValueError("Agent type is required")
        if not self.config.capabilities:
            raise ValueError("At least one capability is required")

        # Validate environment variables if needed
        required_env_vars = self._get_required_env_vars()
        for var in required_env_vars:
            if not os.getenv(var):
                raise ValueError(f"Required environment variable {var} is not set")

    async def _setup_dependencies(self) -> None:
        """Setup common dependencies (database, cache, etc.)"""
        try:
            # Database connection
            if hasattr(self, "_setup_database"):
                await self._setup_database()

            # Cache connection
            if hasattr(self, "_setup_cache"):
                await self._setup_cache()

            # External service clients
            if hasattr(self, "_setup_external_clients"):
                await self._setup_external_clients()

            # Message queue
            if hasattr(self, "_setup_message_queue"):
                await self._setup_message_queue()

        except Exception as e:
            self.logger.error(f"Failed to setup dependencies: {str(e)}")
            raise

    async def _cleanup_dependencies(self) -> None:
        """Cleanup common dependencies"""
        try:
            # Cleanup database connections
            if hasattr(self, "_cleanup_database"):
                await self._cleanup_database()

            # Cleanup cache connections
            if hasattr(self, "_cleanup_cache"):
                await self._cleanup_cache()

            # Cleanup external clients
            if hasattr(self, "_cleanup_external_clients"):
                await self._cleanup_external_clients()

            # Cleanup message queue
            if hasattr(self, "_cleanup_message_queue"):
                await self._cleanup_message_queue()

        except Exception as e:
            self.logger.error(f"Failed to cleanup dependencies: {str(e)}")

    async def _validate_task_data(self, task_data: dict[str, Any]) -> None:
        """Validate task data (can be overridden by subclasses)"""
        if not isinstance(task_data, dict):
            raise ValueError("Task data must be a dictionary")

    async def _cancel_active_tasks(self) -> None:
        """Cancel all active tasks"""
        if self.active_tasks:
            self.logger.info(f"Cancelling {len(self.active_tasks)} active tasks")
            for task_id, task in self.active_tasks.items():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    self.logger.debug(f"Task {task_id} cancelled")
            self.active_tasks.clear()

    async def _setup_mcp_server(self) -> None:
        """Setup MCP server for agent communication"""
        try:
            # MCP server setup would go here
            # This is a placeholder for the actual MCP integration
            self.logger.info("MCP server setup completed")
        except Exception as e:
            self.logger.error(f"Failed to setup MCP server: {str(e)}")
            raise

    async def _stop_mcp_server(self) -> None:
        """Stop MCP server"""
        try:
            if self.mcp_server:
                # Stop MCP server
                self.logger.info("MCP server stopped")
        except Exception as e:
            self.logger.error(f"Failed to stop MCP server: {str(e)}")

    def _get_required_env_vars(self) -> list[str]:
        """Get list of required environment variables (can be overridden)"""
        return []

    # Utility methods for common operations
    async def _retry_operation(
        self, operation, max_attempts: int | None = None, delay: float = 1.0
    ):
        """Retry an operation with exponential backoff"""
        attempts = max_attempts or self.config.retry_attempts

        for attempt in range(attempts):
            try:
                return await operation()
            except Exception as e:
                if attempt == attempts - 1:  # Last attempt
                    raise

                wait_time = delay * (2**attempt)
                self.logger.warning(
                    f"Operation failed (attempt {attempt + 1}/{attempts}): {str(e)}. Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)

    def _log_performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics"""
        self.logger.info(
            f"Performance: {operation} completed in {duration:.3f}s", extra=kwargs
        )

    def _log_error(self, operation: str, error: Exception, **kwargs):
        """Log errors with context"""
        self.logger.error(f"Error in {operation}: {str(error)}", extra=kwargs)
        self.logger.debug(traceback.format_exc())

    async def _start_resilience_features(self) -> None:
        """Start background tasks for resilience features"""
        if self.resilience_config.checkpoint_interval > 0:
            self._background_tasks.append(asyncio.create_task(self._checkpoint_loop()))
        if self.resilience_config.health_check_interval > 0:
            self._background_tasks.append(
                asyncio.create_task(self._health_check_loop())
            )
        await self._load_checkpoint()

    async def _checkpoint_loop(self) -> None:
        """Periodically save agent checkpoints"""
        while not self._shutdown_event.is_set():
            await asyncio.sleep(self.resilience_config.checkpoint_interval)
            try:
                await self._save_checkpoint()
            except Exception as e:
                self.logger.warning(f"Checkpoint failed: {e}")

    async def _health_check_loop(self) -> None:
        """Periodically run health checks"""
        while not self._shutdown_event.is_set():
            await asyncio.sleep(self.resilience_config.health_check_interval)
            try:
                await self._health_check()
            except Exception as e:
                self.logger.warning(f"Health check failed: {e}")

    async def _save_checkpoint(self) -> None:
        """Persist agent state (override for custom behavior)"""
        pass

    async def _load_checkpoint(self) -> None:
        """Load agent state if available"""
        pass

    async def _health_check(self) -> None:
        """Perform custom health check"""
        pass
