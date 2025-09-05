"""
Micro-Swarm Scheduler
Advanced scheduling system for automated swarm executions with intelligent timing,
resource management, and adaptive scheduling
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from app.core.secrets_manager import get_secret
from app.integrations.slack_integration import SlackIntegration
from app.memory.unified_memory_router import MemoryDomain, get_memory_router
from app.swarms.artemis.technical_agents import ArtemisSwarmFactory
from app.swarms.core.micro_swarm_base import CoordinationPattern, MicroSwarmCoordinator, SwarmResult
from app.swarms.sophia.mythology_agents import SophiaMythologySwarmFactory

logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    """Types of scheduling"""

    ONCE = "once"  # One-time execution
    RECURRING = "recurring"  # Repeated execution
    CRON = "cron"  # Cron-based scheduling
    TRIGGERED = "triggered"  # Event-triggered
    ADAPTIVE = "adaptive"  # AI-determined optimal timing


class Priority(Enum):
    """Task priority levels"""

    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


class ScheduleStatus(Enum):
    """Schedule execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    """A scheduled swarm execution task"""

    task_id: str
    name: str
    description: str
    swarm_type: str  # e.g., "sophia.business_intelligence"
    task_content: str
    schedule_type: ScheduleType

    # Scheduling parameters
    execute_at: Optional[datetime] = None
    cron_expression: Optional[str] = None
    interval_minutes: Optional[int] = None

    # Execution parameters
    priority: Priority = Priority.NORMAL
    max_cost_usd: float = 2.0
    timeout_minutes: int = 10
    retry_attempts: int = 2

    # Filtering and conditions
    business_hours_only: bool = False
    weekdays_only: bool = False
    min_gap_minutes: int = 30  # Minimum gap between executions

    # Metadata
    created_by: str = "system"
    tags: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    # State tracking
    status: ScheduleStatus = ScheduleStatus.PENDING
    last_execution: Optional[datetime] = None
    next_execution: Optional[datetime] = None
    execution_count: int = 0
    failure_count: int = 0
    total_cost: float = 0.0

    # Results
    last_result: Optional[SwarmResult] = None
    execution_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SchedulerConfig:
    """Configuration for the scheduler"""

    max_concurrent_tasks: int = 5
    default_timeout_minutes: int = 15
    max_daily_cost: float = 50.0
    enable_slack_notifications: bool = True
    enable_adaptive_scheduling: bool = True
    business_hours_start: int = 9  # 9 AM
    business_hours_end: int = 17  # 5 PM
    weekend_execution: bool = False
    execution_buffer_minutes: int = 2  # Buffer between executions


@dataclass
class ExecutionResult:
    """Result of a scheduled task execution"""

    task_id: str
    execution_id: str
    started_at: datetime
    completed_at: datetime
    success: bool
    swarm_result: Optional[SwarmResult]
    error_message: Optional[str] = None
    cost_usd: float = 0.0
    duration_minutes: float = 0.0


class MicroSwarmScheduler:
    """
    Advanced scheduler for micro-swarm executions with intelligent resource management
    """

    def __init__(self, config: SchedulerConfig):
        self.config = config
        self.memory = get_memory_router()

        # Task management
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.active_executions: Dict[str, asyncio.Task] = {}
        self.execution_queue: List[ScheduledTask] = []

        # Resource tracking
        self.daily_cost_tracker = 0.0
        self.last_reset_date = datetime.now().date()

        # Swarm factories
        self.sophia_factory = SophiaMythologySwarmFactory()
        self.artemis_factory = ArtemisSwarmFactory()

        # Notifications
        self.slack = None
        if config.enable_slack_notifications:
            try:
                self.slack = SlackIntegration()
            except Exception as e:
                logger.warning(f"Failed to initialize Slack notifications: {e}")

        # Scheduler state
        self.running = False
        self.scheduler_task: Optional[asyncio.Task] = None

        logger.info("Micro-swarm scheduler initialized")

    async def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Scheduler already running")
            return

        self.running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Scheduler started")

    async def stop(self):
        """Stop the scheduler gracefully"""
        self.running = False

        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass

        # Cancel active executions
        for task_id, execution_task in list(self.active_executions.items()):
            execution_task.cancel()
            try:
                await execution_task
            except asyncio.CancelledError:
                pass

        logger.info("Scheduler stopped")

    def schedule_task(self, task: ScheduledTask) -> str:
        """Schedule a new task"""

        # Validate task
        self._validate_task(task)

        # Calculate next execution time
        task.next_execution = self._calculate_next_execution(task)

        # Store task
        self.scheduled_tasks[task.task_id] = task

        logger.info(f"Scheduled task '{task.name}' (ID: {task.task_id}) for {task.next_execution}")

        return task.task_id

    def unschedule_task(self, task_id: str) -> bool:
        """Unschedule a task"""
        if task_id in self.scheduled_tasks:
            task = self.scheduled_tasks[task_id]
            task.status = ScheduleStatus.CANCELLED

            # Cancel active execution if running
            if task_id in self.active_executions:
                self.active_executions[task_id].cancel()

            del self.scheduled_tasks[task_id]
            logger.info(f"Unscheduled task {task_id}")
            return True

        return False

    def pause_task(self, task_id: str) -> bool:
        """Pause a scheduled task"""
        if task_id in self.scheduled_tasks:
            self.scheduled_tasks[task_id].status = ScheduleStatus.PAUSED
            logger.info(f"Paused task {task_id}")
            return True
        return False

    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task"""
        if task_id in self.scheduled_tasks:
            task = self.scheduled_tasks[task_id]
            if task.status == ScheduleStatus.PAUSED:
                task.status = ScheduleStatus.PENDING
                task.next_execution = self._calculate_next_execution(task)
                logger.info(f"Resumed task {task_id}")
                return True
        return False

    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                # Reset daily cost tracker if needed
                self._reset_daily_cost_if_needed()

                # Check for tasks ready to execute
                ready_tasks = self._get_ready_tasks()

                # Execute ready tasks (respecting concurrency limits)
                for task in ready_tasks:
                    if len(self.active_executions) < self.config.max_concurrent_tasks:
                        await self._start_task_execution(task)
                    else:
                        break  # Hit concurrency limit

                # Clean up completed executions
                await self._cleanup_completed_executions()

                # Update next execution times for recurring tasks
                self._update_recurring_schedules()

                # Adaptive scheduling adjustments
                if self.config.enable_adaptive_scheduling:
                    await self._adaptive_schedule_adjustments()

                # Sleep before next iteration
                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    def _get_ready_tasks(self) -> List[ScheduledTask]:
        """Get tasks ready for execution"""
        now = datetime.now()
        ready_tasks = []

        for task in self.scheduled_tasks.values():
            if (
                task.status == ScheduleStatus.PENDING
                and task.next_execution
                and task.next_execution <= now
                and task.task_id not in self.active_executions
            ):

                # Check business hours constraint
                if task.business_hours_only and not self._is_business_hours(now):
                    continue

                # Check weekdays constraint
                if task.weekdays_only and now.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    continue

                # Check daily cost limit
                if self.daily_cost_tracker + task.max_cost_usd > self.config.max_daily_cost:
                    logger.warning(f"Skipping task {task.task_id} due to daily cost limit")
                    continue

                ready_tasks.append(task)

        # Sort by priority and next execution time
        ready_tasks.sort(key=lambda t: (t.priority.value, t.next_execution))

        return ready_tasks

    async def _start_task_execution(self, task: ScheduledTask):
        """Start executing a task"""

        task.status = ScheduleStatus.RUNNING
        task.execution_count += 1
        task.last_execution = datetime.now()

        # Create execution task
        execution_task = asyncio.create_task(self._execute_task(task))
        self.active_executions[task.task_id] = execution_task

        logger.info(f"Started execution of task '{task.name}' (ID: {task.task_id})")

        # Send notification
        if self.slack:
            await self._notify_execution_started(task)

    async def _execute_task(self, task: ScheduledTask) -> ExecutionResult:
        """Execute a swarm task"""

        execution_id = f"{task.task_id}_{int(datetime.now().timestamp())}"
        start_time = datetime.now()

        try:
            # Create swarm coordinator
            coordinator = await self._create_swarm_coordinator(task)

            # Execute swarm
            swarm_result = await asyncio.wait_for(
                coordinator.execute(task.task_content, task.context),
                timeout=task.timeout_minutes * 60,
            )

            # Calculate execution time
            end_time = datetime.now()
            duration_minutes = (end_time - start_time).total_seconds() / 60

            # Create execution result
            result = ExecutionResult(
                task_id=task.task_id,
                execution_id=execution_id,
                started_at=start_time,
                completed_at=end_time,
                success=swarm_result.success,
                swarm_result=swarm_result,
                cost_usd=swarm_result.total_cost,
                duration_minutes=duration_minutes,
            )

            # Update task state
            task.status = (
                ScheduleStatus.COMPLETED if swarm_result.success else ScheduleStatus.FAILED
            )
            task.last_result = swarm_result
            task.total_cost += swarm_result.total_cost
            self.daily_cost_tracker += swarm_result.total_cost

            # Add to execution history
            task.execution_history.append(
                {
                    "execution_id": execution_id,
                    "timestamp": start_time.isoformat(),
                    "success": swarm_result.success,
                    "cost": swarm_result.total_cost,
                    "duration_minutes": duration_minutes,
                    "confidence": swarm_result.confidence,
                }
            )

            # Keep only last 20 executions
            if len(task.execution_history) > 20:
                task.execution_history = task.execution_history[-20:]

            # Store result in memory
            await self._store_execution_result(task, result)

            # Send success notification
            if self.slack and swarm_result.success:
                await self._notify_execution_completed(task, result)

            logger.info(
                f"Task '{task.name}' completed successfully in {duration_minutes:.2f} minutes"
            )

            return result

        except asyncio.TimeoutError:
            error_msg = f"Task execution timed out after {task.timeout_minutes} minutes"
            logger.error(error_msg)

            task.status = ScheduleStatus.FAILED
            task.failure_count += 1

            result = ExecutionResult(
                task_id=task.task_id,
                execution_id=execution_id,
                started_at=start_time,
                completed_at=datetime.now(),
                success=False,
                swarm_result=None,
                error_message=error_msg,
                duration_minutes=(datetime.now() - start_time).total_seconds() / 60,
            )

            # Send failure notification
            if self.slack:
                await self._notify_execution_failed(task, error_msg)

            return result

        except Exception as e:
            error_msg = f"Task execution failed: {str(e)}"
            logger.error(error_msg)

            task.status = ScheduleStatus.FAILED
            task.failure_count += 1

            result = ExecutionResult(
                task_id=task.task_id,
                execution_id=execution_id,
                started_at=start_time,
                completed_at=datetime.now(),
                success=False,
                swarm_result=None,
                error_message=error_msg,
                duration_minutes=(datetime.now() - start_time).total_seconds() / 60,
            )

            # Send failure notification
            if self.slack:
                await self._notify_execution_failed(task, error_msg)

            return result

    async def _create_swarm_coordinator(self, task: ScheduledTask) -> MicroSwarmCoordinator:
        """Create appropriate swarm coordinator for task"""

        swarm_parts = task.swarm_type.split(".")
        domain = swarm_parts[0]  # sophia or artemis
        swarm_name = swarm_parts[1] if len(swarm_parts) > 1 else "default"

        if domain == "sophia":
            if swarm_name == "business_intelligence":
                return self.sophia_factory.create_business_intelligence_swarm()
            elif swarm_name == "strategic_planning":
                return self.sophia_factory.create_strategic_planning_swarm()
            elif swarm_name == "business_health":
                return self.sophia_factory.create_business_health_swarm()
            elif swarm_name == "comprehensive_analysis":
                return self.sophia_factory.create_comprehensive_analysis_swarm()
            else:
                return self.sophia_factory.create_business_intelligence_swarm()

        elif domain == "artemis":
            if swarm_name == "architecture_review":
                return self.artemis_factory.create_architecture_review_swarm()
            elif swarm_name == "code_review":
                return self.artemis_factory.create_code_review_swarm()
            elif swarm_name == "technical_strategy":
                return self.artemis_factory.create_technical_strategy_swarm()
            elif swarm_name == "security_assessment":
                return self.artemis_factory.create_security_assessment_swarm()
            elif swarm_name == "full_technical":
                return self.artemis_factory.create_full_technical_swarm()
            else:
                return self.artemis_factory.create_code_review_swarm()
        else:
            raise ValueError(f"Unknown swarm domain: {domain}")

    async def _cleanup_completed_executions(self):
        """Clean up completed execution tasks"""

        completed_tasks = []
        for task_id, execution_task in self.active_executions.items():
            if execution_task.done():
                completed_tasks.append(task_id)

        for task_id in completed_tasks:
            execution_task = self.active_executions.pop(task_id)

            # Handle task result or exception
            try:
                result = await execution_task
                logger.debug(f"Cleaned up completed execution for task {task_id}")
            except Exception as e:
                logger.error(f"Execution task {task_id} failed with exception: {e}")

    def _update_recurring_schedules(self):
        """Update next execution times for recurring tasks"""

        for task in self.scheduled_tasks.values():
            if (
                task.schedule_type == ScheduleType.RECURRING
                and task.status in [ScheduleStatus.COMPLETED, ScheduleStatus.FAILED]
                and task.interval_minutes
            ):

                # Calculate next execution
                if task.last_execution:
                    next_time = task.last_execution + timedelta(minutes=task.interval_minutes)

                    # Respect minimum gap
                    min_next_time = datetime.now() + timedelta(minutes=task.min_gap_minutes)
                    task.next_execution = max(next_time, min_next_time)
                else:
                    task.next_execution = datetime.now() + timedelta(minutes=task.interval_minutes)

                task.status = ScheduleStatus.PENDING

    async def _adaptive_schedule_adjustments(self):
        """Make adaptive adjustments to scheduling based on performance"""

        # Analyze execution patterns and adjust timing for better performance
        for task in self.scheduled_tasks.values():
            if len(task.execution_history) >= 3:
                # Analyze success patterns
                recent_executions = task.execution_history[-5:]
                success_rate = sum(1 for ex in recent_executions if ex["success"]) / len(
                    recent_executions
                )
                avg_duration = sum(ex["duration_minutes"] for ex in recent_executions) / len(
                    recent_executions
                )

                # Adjust interval based on success rate and performance
                if task.schedule_type == ScheduleType.RECURRING and task.interval_minutes:
                    if success_rate < 0.5:  # Low success rate
                        # Increase interval to reduce failure frequency
                        task.interval_minutes = min(
                            task.interval_minutes * 1.2, 1440
                        )  # Max 24 hours
                        logger.info(
                            f"Increased interval for task {task.task_id} due to low success rate"
                        )
                    elif success_rate > 0.9 and avg_duration < task.timeout_minutes * 0.5:
                        # High success rate and fast execution - could run more frequently
                        task.interval_minutes = max(
                            task.interval_minutes * 0.8, task.min_gap_minutes
                        )
                        logger.info(
                            f"Decreased interval for task {task.task_id} due to good performance"
                        )

    def _calculate_next_execution(self, task: ScheduledTask) -> datetime:
        """Calculate next execution time for a task"""

        now = datetime.now()

        if task.schedule_type == ScheduleType.ONCE:
            return task.execute_at or now

        elif task.schedule_type == ScheduleType.RECURRING:
            if not task.interval_minutes:
                raise ValueError("Recurring task must have interval_minutes set")

            base_time = task.last_execution or now
            next_time = base_time + timedelta(minutes=task.interval_minutes)

            # Ensure minimum gap
            min_time = now + timedelta(minutes=task.min_gap_minutes)
            return max(next_time, min_time)

        elif task.schedule_type == ScheduleType.CRON:
            # Simple cron implementation - could be enhanced with croniter library
            if not task.cron_expression:
                raise ValueError("CRON task must have cron_expression set")

            # For now, return next hour (simplified)
            return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

        elif task.schedule_type == ScheduleType.ADAPTIVE:
            # AI-determined optimal timing based on historical data and patterns
            return self._calculate_adaptive_timing(task)
        else:
            return now

    def _calculate_adaptive_timing(self, task: ScheduledTask) -> datetime:
        """Calculate optimal timing using adaptive algorithms"""

        now = datetime.now()

        # Base interval from configuration or history
        if task.execution_history:
            # Analyze historical patterns
            recent_successes = [ex for ex in task.execution_history[-10:] if ex["success"]]

            if recent_successes:
                # Find optimal time patterns
                success_hours = [
                    datetime.fromisoformat(ex["timestamp"]).hour for ex in recent_successes
                ]
                optimal_hour = max(set(success_hours), key=success_hours.count)

                # Schedule for optimal hour tomorrow if too late today
                target_time = now.replace(hour=optimal_hour, minute=0, second=0, microsecond=0)
                if target_time <= now:
                    target_time += timedelta(days=1)

                return target_time

        # Default to business hours if no history
        next_business_hour = now.replace(
            hour=self.config.business_hours_start, minute=0, second=0, microsecond=0
        )
        if next_business_hour <= now or next_business_hour.hour >= self.config.business_hours_end:
            next_business_hour = next_business_hour.replace(
                hour=self.config.business_hours_start
            ) + timedelta(days=1)

        return next_business_hour

    def _validate_task(self, task: ScheduledTask):
        """Validate a scheduled task"""

        if not task.task_id:
            raise ValueError("Task ID is required")

        if not task.name:
            raise ValueError("Task name is required")

        if not task.swarm_type:
            raise ValueError("Swarm type is required")

        if not task.task_content:
            raise ValueError("Task content is required")

        if task.schedule_type == ScheduleType.RECURRING and not task.interval_minutes:
            raise ValueError("Recurring tasks must have interval_minutes")

        if task.schedule_type == ScheduleType.CRON and not task.cron_expression:
            raise ValueError("CRON tasks must have cron_expression")

        if task.max_cost_usd <= 0:
            raise ValueError("Max cost must be positive")

        if task.timeout_minutes <= 0:
            raise ValueError("Timeout must be positive")

    def _is_business_hours(self, dt: datetime) -> bool:
        """Check if datetime is within business hours"""
        return (
            dt.weekday() < 5  # Monday = 0, Friday = 4
            and self.config.business_hours_start <= dt.hour < self.config.business_hours_end
        )

    def _reset_daily_cost_if_needed(self):
        """Reset daily cost tracker if it's a new day"""
        today = datetime.now().date()
        if today > self.last_reset_date:
            self.daily_cost_tracker = 0.0
            self.last_reset_date = today
            logger.info("Reset daily cost tracker for new day")

    async def _store_execution_result(self, task: ScheduledTask, result: ExecutionResult):
        """Store execution result in memory"""
        try:
            # Create memory entry
            memory_content = {
                "task_name": task.name,
                "swarm_type": task.swarm_type,
                "execution_result": {
                    "success": result.success,
                    "duration_minutes": result.duration_minutes,
                    "cost_usd": result.cost_usd,
                    "timestamp": result.started_at.isoformat(),
                },
            }

            if result.swarm_result:
                memory_content["swarm_output"] = result.swarm_result.final_output[:1000]  # Truncate
                memory_content["confidence"] = result.swarm_result.confidence

            # Store in structured memory
            await self.memory.record_fact(
                table="scheduled_executions",
                data={
                    "task_id": task.task_id,
                    "execution_id": result.execution_id,
                    "success": result.success,
                    "cost_usd": result.cost_usd,
                    "duration_minutes": result.duration_minutes,
                    "swarm_type": task.swarm_type,
                },
            )

        except Exception as e:
            logger.error(f"Failed to store execution result: {e}")

    # Notification methods
    async def _notify_execution_started(self, task: ScheduledTask):
        """Send notification that task execution started"""
        try:
            await self.slack.send_message(
                channel="#swarm-executions",
                message=f"🚀 Started execution of '{task.name}' (Type: {task.swarm_type})",
            )
        except Exception as e:
            logger.error(f"Failed to send start notification: {e}")

    async def _notify_execution_completed(self, task: ScheduledTask, result: ExecutionResult):
        """Send notification that task execution completed"""
        try:
            swarm_result = result.swarm_result
            message = f"""✅ '{task.name}' completed successfully!

Duration: {result.duration_minutes:.1f} minutes
Cost: ${result.cost_usd:.3f}
Confidence: {swarm_result.confidence:.2f}

Output: {swarm_result.final_output[:300]}..."""

            await self.slack.send_message(channel="#swarm-executions", message=message)
        except Exception as e:
            logger.error(f"Failed to send completion notification: {e}")

    async def _notify_execution_failed(self, task: ScheduledTask, error_msg: str):
        """Send notification that task execution failed"""
        try:
            await self.slack.send_message(
                channel="#swarm-executions",
                message=f"❌ '{task.name}' execution failed: {error_msg}",
            )
        except Exception as e:
            logger.error(f"Failed to send failure notification: {e}")

    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        return {
            "running": self.running,
            "total_scheduled_tasks": len(self.scheduled_tasks),
            "active_executions": len(self.active_executions),
            "daily_cost_used": self.daily_cost_tracker,
            "daily_cost_limit": self.config.max_daily_cost,
            "concurrency_limit": self.config.max_concurrent_tasks,
            "pending_tasks": len(
                [t for t in self.scheduled_tasks.values() if t.status == ScheduleStatus.PENDING]
            ),
            "failed_tasks": len(
                [t for t in self.scheduled_tasks.values() if t.status == ScheduleStatus.FAILED]
            ),
            "paused_tasks": len(
                [t for t in self.scheduled_tasks.values() if t.status == ScheduleStatus.PAUSED]
            ),
        }

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        if task_id not in self.scheduled_tasks:
            return None

        task = self.scheduled_tasks[task_id]
        return {
            "task_id": task.task_id,
            "name": task.name,
            "status": task.status.value,
            "next_execution": task.next_execution.isoformat() if task.next_execution else None,
            "last_execution": task.last_execution.isoformat() if task.last_execution else None,
            "execution_count": task.execution_count,
            "failure_count": task.failure_count,
            "total_cost": task.total_cost,
            "last_success": task.last_result.success if task.last_result else None,
            "last_confidence": task.last_result.confidence if task.last_result else None,
        }


# Factory functions for common scheduled tasks
def create_daily_business_intelligence_task(task_content: str) -> ScheduledTask:
    """Create daily business intelligence analysis task"""
    return ScheduledTask(
        task_id=f"daily_bi_{int(datetime.now().timestamp())}",
        name="Daily Business Intelligence Analysis",
        description="Daily comprehensive business intelligence and market analysis",
        swarm_type="sophia.business_intelligence",
        task_content=task_content,
        schedule_type=ScheduleType.RECURRING,
        interval_minutes=1440,  # Daily
        business_hours_only=True,
        weekdays_only=True,
        max_cost_usd=3.0,
        timeout_minutes=15,
        tags=["daily", "business", "intelligence"],
        priority=Priority.HIGH,
    )


def create_weekly_code_review_task(repository_path: str) -> ScheduledTask:
    """Create weekly code review task"""
    return ScheduledTask(
        task_id=f"weekly_code_review_{int(datetime.now().timestamp())}",
        name="Weekly Code Quality Review",
        description="Weekly comprehensive code quality and security review",
        swarm_type="artemis.code_review",
        task_content=f"Review code quality and security for repository: {repository_path}",
        schedule_type=ScheduleType.RECURRING,
        interval_minutes=10080,  # Weekly
        business_hours_only=True,
        weekdays_only=True,
        max_cost_usd=5.0,
        timeout_minutes=30,
        tags=["weekly", "code", "review", "security"],
        priority=Priority.NORMAL,
        context={"repository": repository_path},
    )


# Global scheduler instance
_scheduler = None


def get_scheduler(config: Optional[SchedulerConfig] = None) -> MicroSwarmScheduler:
    """Get global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        if config is None:
            config = SchedulerConfig()
        _scheduler = MicroSwarmScheduler(config)
    return _scheduler
