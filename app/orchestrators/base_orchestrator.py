"""
Base Orchestrator Pattern
Foundation for all domain-specific orchestrators (Sophia, Artemis)
"""

import asyncio
import json
import logging
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from app.core.portkey_manager import TaskType, get_portkey_manager
from app.core.secrets_manager import get_secrets_manager
from app.memory.unified_memory_router import DocChunk, MemoryDomain, get_memory_router
from app.observability.metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)


class ExecutionPriority(Enum):
    """Task execution priority"""

    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


class TaskStatus(Enum):
    """Task execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Represents a task to be executed"""

    id: str
    type: TaskType
    content: str
    priority: ExecutionPriority = ExecutionPriority.NORMAL
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    retries: int = 0
    max_retries: int = 3
    budget: dict[str, float] = field(default_factory=lambda: {"cost_usd": 1.0, "tokens": 10000})


@dataclass
class Result:
    """Result of task execution"""

    success: bool
    content: Any
    metadata: dict[str, Any] = field(default_factory=dict)
    citations: list[dict[str, str]] = field(default_factory=list)
    confidence: float = 1.0
    cost: float = 0.0
    tokens_used: int = 0
    execution_time_ms: float = 0.0
    errors: list[str] = field(default_factory=list)


@dataclass
class OrchestratorConfig:
    """Configuration for orchestrator"""

    domain: MemoryDomain
    name: str
    description: str
    max_concurrent_tasks: int = 10
    default_timeout_s: int = 120
    enable_caching: bool = True
    enable_monitoring: bool = True
    enable_memory: bool = True
    budget_limits: dict[str, float] = field(
        default_factory=lambda: {
            "hourly_cost_usd": 100.0,
            "daily_cost_usd": 1000.0,
            "monthly_cost_usd": 20000.0,
        }
    )


class BaseOrchestrator(ABC):
    """
    Unified base orchestrator for all domain-specific orchestrators.
    Provides common functionality for memory, model routing, monitoring, and execution.
    """

    def __init__(self, config: OrchestratorConfig):
        """
        Initialize base orchestrator

        Args:
            config: Orchestrator configuration
        """
        self.config = config
        self.domain = config.domain

        # Core services
        self.memory = get_memory_router() if config.enable_memory else None
        self.portkey = get_portkey_manager()
        self.secrets = get_secrets_manager()
        self.metrics = MetricsCollector() if config.enable_monitoring else None

        # Circuit breaker for fault tolerance
        self.circuit_breaker = CircuitBreaker(
            name=f"{self.config.name}.orchestrator",
            config=CircuitBreakerConfig(
                failure_threshold=5,
                success_threshold=2,
                timeout=60.0,
                expected_exception=Exception,
            ),
        )

        # Task management
        self._task_queue = asyncio.Queue()
        self._active_tasks = {}
        self._task_history = []
        self._semaphore = asyncio.Semaphore(config.max_concurrent_tasks)

        # Cost tracking
        self._cost_tracker = {"hourly": 0.0, "daily": 0.0, "monthly": 0.0, "total": 0.0}

        logger.info(f"Initialized {self.config.name} orchestrator for {self.domain.value} domain")

    async def execute(self, task: Task) -> Result:
        """
        Unified execution pattern for all orchestrators

        Args:
            task: Task to execute

        Returns:
            Execution result
        """
        # Start timing
        start_time = datetime.now()
        task.started_at = start_time
        task.status = TaskStatus.RUNNING

        # Store in active tasks
        self._active_tasks[task.id] = task

        result = Result(success=False, content=None)

        try:
            # Pre-execution hooks
            await self._pre_execute(task)

            # Check budget
            if not self._check_budget(task):
                result.errors.append("Budget limit exceeded")
                task.status = TaskStatus.FAILED
                return result

            # Route to appropriate model
            routing = self.portkey.route_request(
                task_type=task.type,
                estimated_tokens=task.budget.get("tokens", 1000),
                max_cost_usd=task.budget.get("cost_usd", 1.0),
            )

            # Execute with monitoring and circuit breaker
            async with self._semaphore:
                if self.metrics and hasattr(self.metrics, "timer"):
                    with self.metrics.timer(f"{self.domain.value}.execution"):
                        result = await self._execute_with_circuit_breaker(task, routing)
                else:
                    result = await self._execute_with_circuit_breaker(task, routing)

            # Post-execution hooks
            await self._post_execute(task, result)

            # Update task status
            task.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
            task.completed_at = datetime.now()

            # Calculate execution time
            result.execution_time_ms = (task.completed_at - start_time).total_seconds() * 1000

            # Track costs
            self._update_cost_tracking(result.cost)

        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}\n{traceback.format_exc()}")
            result.success = False
            result.errors.append(str(e))
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()

            # Retry logic
            if task.retries < task.max_retries:
                task.retries += 1
                task.status = TaskStatus.PENDING
                await self._task_queue.put(task)
                logger.info(f"Retrying task {task.id} (attempt {task.retries}/{task.max_retries})")

        finally:
            # Clean up
            if task.id in self._active_tasks:
                del self._active_tasks[task.id]

            # Store in history
            self._task_history.append({"task": task, "result": result, "timestamp": datetime.now()})

            # Emit basic metrics (collector exposes generic record/increment)
            if self.metrics:
                labels = {"domain": self.domain.value, "task_type": task.type.value}
                status_label = {"status": "success" if result.success else "failure"}
                self.metrics.increment("tasks.total", 1.0, labels={**labels, **status_label})
                self.metrics.record("tasks.duration_ms", result.execution_time_ms, labels=labels)
                self.metrics.record("tasks.cost_usd", result.cost, labels=labels)

        return result

    async def _execute_with_circuit_breaker(self, task: Task, routing: Any) -> Result:
        """Execute task with circuit breaker protection"""

        async def _execute():
            return await self._execute_core(task, routing)

        return await self.circuit_breaker.call(_execute)

    @abstractmethod
    async def _execute_core(self, task: Task, routing: Any) -> Result:
        """
        Core execution logic - must be implemented by subclasses

        Args:
            task: Task to execute
            routing: Model routing decision

        Returns:
            Execution result
        """
        pass

    async def _pre_execute(self, task: Task) -> None:
        """
        Pre-execution hook for setup and validation

        Args:
            task: Task about to be executed
        """
        # Load relevant context from memory
        if self.memory and self.config.enable_memory:
            context = await self._load_context(task)
            task.metadata["context"] = context

        # Validate task requirements
        await self._validate_task(task)

        # Log execution start
        logger.info(f"Starting execution of task {task.id} ({task.type.value})")

    async def _post_execute(self, task: Task, result: Result) -> None:
        """
        Post-execution hook for cleanup and storage

        Args:
            task: Completed task
            result: Execution result
        """
        # Store results in memory
        if self.memory and self.config.enable_memory and result.success:
            await self._store_results(task, result)

        # Cache successful results (store a lightweight, serializable summary)
        if self.config.enable_caching and result.success:
            cache_key = self._generate_cache_key(task)
            summary = {
                "success": result.success,
                "confidence": result.confidence,
                "cost": result.cost,
                "execution_time_ms": result.execution_time_ms,
            }
            await self.memory.put_ephemeral(cache_key, summary, ttl_s=3600)  # 1 hour cache

        # Log execution completion
        status = "succeeded" if result.success else "failed"
        logger.info(f"Task {task.id} {status} in {result.execution_time_ms:.2f}ms")

    async def _load_context(self, task: Task) -> dict[str, Any]:
        """
        Load relevant context from memory

        Args:
            task: Task to get context for

        Returns:
            Context dictionary
        """
        context = {}

        # Search for relevant information
        if task.content:
            hits = await self.memory.search(query=task.content, domain=self.domain, k=5)

            context["related_info"] = [
                {"content": hit.content, "source": hit.source_uri, "score": hit.score}
                for hit in hits
            ]

        # Load recent history
        context["recent_tasks"] = self._get_recent_tasks(limit=3)

        return context

    async def _store_results(self, task: Task, result: Result) -> None:
        """
        Store task results in memory

        Args:
            task: Completed task
            result: Execution result
        """
        # Create document chunk from result
        chunk = DocChunk(
            content=json.dumps(
                {
                    "task": task.content,
                    "result": (
                        result.content if isinstance(result.content, str) else str(result.content)
                    ),
                }
            ),
            source_uri=f"task://{task.id}",
            domain=self.domain,
            metadata={
                "task_type": task.type.value,
                "timestamp": datetime.now().isoformat(),
                "success": result.success,
            },
            confidence=result.confidence,
        )

        # Store in vector memory
        await self.memory.upsert_chunks([chunk], self.domain)

        # Store fact in structured memory
        await self.memory.record_fact(
            table="task_results",
            data={
                "task_id": task.id,
                "task_type": task.type.value,
                "success": result.success,
                "cost_usd": result.cost,
                "tokens_used": result.tokens_used,
                "execution_time_ms": result.execution_time_ms,
            },
        )

    async def _validate_task(self, task: Task) -> None:
        """
        Validate task requirements

        Args:
            task: Task to validate

        Raises:
            ValueError: If task is invalid
        """
        if not task.content:
            raise ValueError("Task content cannot be empty")

        if task.budget.get("cost_usd", 0) <= 0:
            raise ValueError("Task must have a positive cost budget")

        if task.budget.get("tokens", 0) <= 0:
            raise ValueError("Task must have a positive token budget")

    def _check_budget(self, task: Task) -> bool:
        """
        Check if task fits within budget limits

        Args:
            task: Task to check

        Returns:
            True if within budget, False otherwise
        """
        task_cost = task.budget.get("cost_usd", 0)

        # Check hourly limit
        if self._cost_tracker["hourly"] + task_cost > self.config.budget_limits["hourly_cost_usd"]:
            logger.warning(f"Task {task.id} would exceed hourly budget limit")
            return False

        # Check daily limit
        if self._cost_tracker["daily"] + task_cost > self.config.budget_limits["daily_cost_usd"]:
            logger.warning(f"Task {task.id} would exceed daily budget limit")
            return False

        return True

    def _update_cost_tracking(self, cost: float) -> None:
        """
        Update cost tracking

        Args:
            cost: Cost to add
        """
        self._cost_tracker["hourly"] += cost
        self._cost_tracker["daily"] += cost
        self._cost_tracker["monthly"] += cost
        self._cost_tracker["total"] += cost

        # Note: Time-based resets (hourly/daily/monthly) will be implemented in future versions

    def _generate_cache_key(self, task: Task) -> str:
        """
        Generate cache key for task

        Args:
            task: Task to generate key for

        Returns:
            Cache key string
        """
        import hashlib

        key_parts = [self.domain.value, task.type.value, task.content[:100]]  # First 100 chars

        combined = "|".join(key_parts)
        return f"task_cache:{hashlib.sha256(combined.encode()).hexdigest()[:16]}"

    def _get_recent_tasks(self, limit: int = 5) -> list[dict[str, Any]]:
        """
        Get recent task history

        Args:
            limit: Maximum number of tasks to return

        Returns:
            List of recent task summaries
        """
        recent = self._task_history[-limit:] if self._task_history else []

        return [
            {
                "task_id": entry["task"].id,
                "type": entry["task"].type.value,
                "success": entry["result"].success,
                "timestamp": entry["timestamp"].isoformat(),
            }
            for entry in recent
        ]

    # ========== Task Queue Management ==========

    async def submit_task(self, task: Task) -> str:
        """
        Submit a task to the queue

        Args:
            task: Task to submit

        Returns:
            Task ID
        """
        await self._task_queue.put(task)
        logger.info(f"Task {task.id} submitted to queue")
        return task.id

    async def process_tasks(self) -> None:
        """Process tasks from the queue continuously"""
        while True:
            try:
                # Get next task
                task = await self._task_queue.get()

                # Execute task
                await self.execute(task)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing task: {e}")
                await asyncio.sleep(1)

    def get_status(self) -> dict[str, Any]:
        """
        Get orchestrator status

        Returns:
            Status dictionary
        """
        return {
            "name": self.config.name,
            "domain": self.domain.value,
            "active_tasks": len(self._active_tasks),
            "queue_size": self._task_queue.qsize(),
            "total_processed": len(self._task_history),
            "cost_tracking": self._cost_tracker,
            "circuit_breaker_state": self.circuit_breaker.state,
            "cache_hit_rate": self.memory.metrics.get_cache_hit_rate() if self.memory else 0.0,
        }

    async def shutdown(self) -> None:
        """Graceful shutdown"""
        logger.info(f"Shutting down {self.config.name} orchestrator")

        # Cancel pending tasks
        while not self._task_queue.empty():
            task = await self._task_queue.get()
            task.status = TaskStatus.CANCELLED

        # Wait for active tasks
        while self._active_tasks:
            await asyncio.sleep(0.1)

        # Close connections
        if self.memory:
            await self.memory.close()

        logger.info(f"{self.config.name} orchestrator shutdown complete")
