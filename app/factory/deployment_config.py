"""
Deployment Configuration System for Comprehensive Swarm Factory
Handles scheduled runs, monitoring, cost management, and automated deployments
"""
import asyncio
import contextlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import Enum
from typing import Any, Callable, Optional
from uuid import uuid4
from app.factory.comprehensive_swarm_factory import (
    ExecutionContext,
    SwarmFactoryConfig,
    SwarmType,
)
from app.swarms.core.slack_delivery import DeliveryConfig, DeliveryPriority
logger = logging.getLogger(__name__)
class DeploymentEnvironment(Enum):
    """Deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
class ScheduleType(Enum):
    """Types of deployment schedules"""
    CRON = "cron"  # Cron-like scheduling
    INTERVAL = "interval"  # Fixed interval (every N minutes/hours/days)
    EVENT_DRIVEN = "event"  # Triggered by events
    MANUAL = "manual"  # Manual deployment only
    CONDITIONAL = "conditional"  # Based on conditions/rules
class DeploymentStatus(Enum):
    """Status of deployments"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"
@dataclass
class ScheduleConfig:
    """Configuration for scheduled deployments"""
    schedule_id: str
    name: str
    description: str
    schedule_type: ScheduleType
    # Timing configuration
    cron_expression: Optional[str] = None  # For cron-style scheduling
    interval_minutes: Optional[int] = None  # For interval scheduling
    start_time: Optional[time] = None  # Daily start time
    end_time: Optional[time] = None  # Daily end time
    days_of_week: list[int] = field(default_factory=list)  # 0=Monday, 6=Sunday
    # Event-driven configuration
    trigger_events: list[str] = field(default_factory=list)
    event_conditions: dict[str, Any] = field(default_factory=dict)
    # Conditional scheduling
    conditions: list[dict[str, Any]] = field(default_factory=list)
    # Execution limits
    max_concurrent_runs: int = 1
    max_daily_runs: int = 24
    timeout_minutes: int = 30
    retry_attempts: int = 2
    retry_delay_minutes: int = 5
    # Environment settings
    enabled: bool = True
    environment: DeploymentEnvironment = DeploymentEnvironment.PRODUCTION
    priority: int = 1  # 1=highest, 10=lowest
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    tags: list[str] = field(default_factory=list)
@dataclass
class DeploymentTemplate:
    """Template for swarm deployments"""
    template_id: str
    name: str
    description: str
    # Swarm configuration
    swarm_factory_config: SwarmFactoryConfig
    execution_context_template: ExecutionContext
    # Deployment settings
    schedule_config: Optional[ScheduleConfig] = None
    environment: DeploymentEnvironment = DeploymentEnvironment.PRODUCTION
    # Monitoring and alerting
    enable_monitoring: bool = True
    alert_channels: list[str] = field(default_factory=list)
    success_notifications: bool = True
    failure_notifications: bool = True
    # Cost management
    daily_cost_limit: float = 50.0
    monthly_cost_limit: float = 1000.0
    cost_alert_threshold: float = 0.8  # Alert at 80% of limit
    # Quality gates
    min_success_rate: float = 0.8
    max_avg_response_time_ms: float = 30000
    required_confidence_threshold: float = 0.7
    # Metadata
    version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    tags: list[str] = field(default_factory=list)
@dataclass
class DeploymentRun:
    """Record of a deployment run"""
    run_id: str
    template_id: str
    swarm_id: str
    schedule_id: Optional[str] = None
    # Execution details
    status: DeploymentStatus = DeploymentStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0
    # Results
    success: bool = False
    final_output: str = ""
    confidence: float = 0.0
    total_cost: float = 0.0
    tokens_used: int = 0
    # Monitoring data
    execution_context: Optional[ExecutionContext] = None
    error_message: Optional[str] = None
    warnings: list[str] = field(default_factory=list)
    notifications_sent: list[str] = field(default_factory=list)
    # Metadata
    environment: DeploymentEnvironment = DeploymentEnvironment.PRODUCTION
    triggered_by: str = "schedule"
    retry_count: int = 0
class DeploymentManager:
    """
    Manages scheduled deployments, monitoring, and cost control for swarm factory
    """
    def __init__(self):
        # Deployment configurations
        self.deployment_templates: dict[str, DeploymentTemplate] = {}
        self.schedule_configs: dict[str, ScheduleConfig] = {}
        # Runtime tracking
        self.active_runs: dict[str, DeploymentRun] = {}
        self.run_history: list[DeploymentRun] = []
        # Monitoring and metrics
        self.deployment_metrics = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "total_cost": 0.0,
            "daily_cost": 0.0,
            "monthly_cost": 0.0,
            "avg_response_time": 0.0,
            "last_reset_date": datetime.now().date(),
        }
        # Event handlers
        self.event_handlers: dict[str, list[Callable]] = {}
        # Background task for scheduling
        self.scheduler_task: Optional[asyncio.Task] = None
        self.is_running = False
        # Load default templates
        self._initialize_default_templates()
        logger.info("Deployment manager initialized")
    def _initialize_default_templates(self):
        """Initialize default deployment templates"""
        # Daily Business Intelligence Report
        daily_bi_schedule = ScheduleConfig(
            schedule_id="daily_bi_schedule",
            name="Daily Business Intelligence",
            description="Daily morning business intelligence report",
            schedule_type=ScheduleType.CRON,
            cron_expression="0 8 * * 1-5",  # 8 AM, Monday to Friday
            days_of_week=[0, 1, 2, 3, 4],  # Monday to Friday
            max_daily_runs=1,
            timeout_minutes=15,
            environment=DeploymentEnvironment.PRODUCTION,
            tags=["daily", "business", "intelligence"],
        )
        daily_bi_template = DeploymentTemplate(
            template_id="daily_business_intelligence",
            name="Daily Business Intelligence Report",
            description="Automated daily business intelligence analysis and reporting",
            swarm_factory_config=SwarmFactoryConfig(
                name="Daily BI Swarm",
                swarm_type=SwarmType.MYTHOLOGY_BUSINESS,
                max_cost_per_execution=3.0,
                auto_deliver_results=True,
                slack_delivery_config=DeliveryConfig(
                    channel="#daily-reports",
                    priority=DeliveryPriority.NORMAL,
                    auto_summarize_long_content=True,
                ),
                tags=["daily", "automated", "business_intelligence"],
            ),
            execution_context_template=ExecutionContext(
                task="Analyze current business trends, market conditions, and provide strategic insights for today's operations.",
                priority=2,
                requester="automated_system",
                context_data={"report_type": "daily_bi", "include_trends": True},
            ),
            schedule_config=daily_bi_schedule,
            daily_cost_limit=10.0,
            alert_channels=["#alerts", "#business-team"],
            tags=["daily", "automated", "business"],
        )
        self.deployment_templates["daily_business_intelligence"] = daily_bi_template
        self.schedule_configs["daily_bi_schedule"] = daily_bi_schedule
        # Weekly Strategic Planning
        weekly_strategy_schedule = ScheduleConfig(
            schedule_id="weekly_strategy_schedule",
            name="Weekly Strategic Planning",
            description="Weekly strategic analysis and planning session",
            schedule_type=ScheduleType.CRON,
            cron_expression="0 9 * * 1",  # 9 AM every Monday
            days_of_week=[0],  # Monday only
            max_daily_runs=1,
            timeout_minutes=30,
            environment=DeploymentEnvironment.PRODUCTION,
            tags=["weekly", "strategy", "planning"],
        )
        weekly_strategy_template = DeploymentTemplate(
            template_id="weekly_strategic_planning",
            name="Weekly Strategic Planning Session",
            description="Automated weekly strategic analysis and planning recommendations",
            swarm_factory_config=SwarmFactoryConfig(
                name="Weekly Strategy Swarm",
                swarm_type=SwarmType.MYTHOLOGY_STRATEGIC,
                max_cost_per_execution=5.0,
                max_execution_time_minutes=25,
                auto_deliver_results=True,
                slack_delivery_config=DeliveryConfig(
                    channel="#strategy",
                    priority=DeliveryPriority.HIGH,
                    mention_roles=["strategy-team"],
                ),
                tags=["weekly", "automated", "strategy"],
            ),
            execution_context_template=ExecutionContext(
                task="Conduct comprehensive weekly strategic analysis including market trends, competitive landscape, and strategic recommendations for the upcoming week.",
                priority=1,
                requester="automated_system",
                context_data={
                    "report_type": "weekly_strategy",
                    "include_market_analysis": True,
                },
            ),
            schedule_config=weekly_strategy_schedule,
            daily_cost_limit=20.0,
            alert_channels=["#strategy", "#executive"],
            tags=["weekly", "automated", "strategy"],
        )
        self.deployment_templates["weekly_strategic_planning"] = (
            weekly_strategy_template
        )
        self.schedule_configs["weekly_strategy_schedule"] = weekly_strategy_schedule
        # Code Quality Monitoring (Hourly during work hours)
        code_quality_schedule = ScheduleConfig(
            schedule_id="code_quality_monitor",
            name="Code Quality Monitoring",
            description="Hourly code quality checks during work hours",
            schedule_type=ScheduleType.INTERVAL,
            interval_minutes=60,
            start_time=time(9, 0),  # 9 AM
            end_time=time(17, 0),  # 5 PM
            days_of_week=[0, 1, 2, 3, 4],  # Monday to Friday
            max_daily_runs=8,
            timeout_minutes=10,
            environment=DeploymentEnvironment.PRODUCTION,
            tags=["hourly", "code_quality", "monitoring"],
        )
        code_quality_template = DeploymentTemplate(
            template_id="code_quality_monitoring",
            name="Automated Code Quality Monitoring",
            description="Hourly automated code quality assessment and alerts",
            swarm_factory_config=SwarmFactoryConfig(
                name="Code Quality Monitor",
                swarm_type=SwarmType.MILITARY_RECON,
                max_cost_per_execution=1.0,
                max_execution_time_minutes=8,
                auto_deliver_results=True,
                slack_delivery_config=DeliveryConfig(
                    channel="#dev-alerts", priority=DeliveryPriority.NORMAL
                ),
                tags=["hourly", "automated", "code_quality"],
            ),
            execution_context_template=ExecutionContext(
                task="Perform rapid code quality assessment, identify issues, and provide immediate feedback on code health.",
                priority=3,
                requester="automated_system",
                context_data={"check_type": "quality_scan", "rapid_assessment": True},
            ),
            schedule_config=code_quality_schedule,
            daily_cost_limit=8.0,
            alert_channels=["#dev-alerts"],
            success_notifications=False,  # Only notify on failures
            tags=["hourly", "automated", "monitoring"],
        )
        self.deployment_templates["code_quality_monitoring"] = code_quality_template
        self.schedule_configs["code_quality_monitor"] = code_quality_schedule
        # Emergency Response (Event-driven)
        emergency_schedule = ScheduleConfig(
            schedule_id="emergency_response",
            name="Emergency Response System",
            description="Event-driven emergency response and analysis",
            schedule_type=ScheduleType.EVENT_DRIVEN,
            trigger_events=["system_alert", "critical_error", "security_breach"],
            event_conditions={
                "severity": "critical",
                "requires_immediate_response": True,
            },
            max_concurrent_runs=3,
            max_daily_runs=10,
            timeout_minutes=5,
            retry_attempts=1,
            priority=1,  # Highest priority
            environment=DeploymentEnvironment.PRODUCTION,
            tags=["emergency", "critical", "event_driven"],
        )
        emergency_template = DeploymentTemplate(
            template_id="emergency_response_system",
            name="Emergency Response System",
            description="Immediate response system for critical issues and emergencies",
            swarm_factory_config=SwarmFactoryConfig(
                name="Emergency Response Swarm",
                swarm_type=SwarmType.HYBRID_TACTICAL,
                max_cost_per_execution=2.0,
                max_execution_time_minutes=4,
                auto_deliver_results=True,
                slack_delivery_config=DeliveryConfig(
                    channel="#emergency",
                    priority=DeliveryPriority.URGENT,
                    mention_roles=["oncall", "emergency-team"],
                ),
                tags=["emergency", "critical", "immediate"],
            ),
            execution_context_template=ExecutionContext(
                task="Immediate analysis and response to critical system event. Provide rapid assessment and recommended actions.",
                priority=1,
                requester="emergency_system",
                context_data={
                    "response_type": "emergency",
                    "immediate_action_required": True,
                },
            ),
            schedule_config=emergency_schedule,
            daily_cost_limit=20.0,
            alert_channels=["#emergency", "#oncall"],
            min_success_rate=0.95,  # High success rate required
            tags=["emergency", "critical", "automated"],
        )
        self.deployment_templates["emergency_response_system"] = emergency_template
        self.schedule_configs["emergency_response"] = emergency_schedule
        logger.info(
            f"Initialized {len(self.deployment_templates)} default deployment templates"
        )
    async def start_scheduler(self):
        """Start the background scheduler"""
        if self.scheduler_task and not self.scheduler_task.done():
            logger.warning("Scheduler already running")
            return
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Deployment scheduler started")
    async def stop_scheduler(self):
        """Stop the background scheduler"""
        self.is_running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.scheduler_task
        logger.info("Deployment scheduler stopped")
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.is_running:
            try:
                await self._check_scheduled_deployments()
                await self._cleanup_old_runs()
                await self._update_cost_tracking()
                # Sleep for 1 minute between checks
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)  # Continue after error
    async def _check_scheduled_deployments(self):
        """Check for deployments that should be triggered"""
        now = datetime.now()
        for template in self.deployment_templates.values():
            if not template.schedule_config or not template.schedule_config.enabled:
                continue
            schedule = template.schedule_config
            # Check if deployment should be triggered
            if await self._should_trigger_deployment(template, schedule, now):
                await self._trigger_deployment(template, "schedule")
    async def _should_trigger_deployment(
        self, template: DeploymentTemplate, schedule: ScheduleConfig, now: datetime
    ) -> bool:
        """Check if a deployment should be triggered now"""
        # Check daily limits
        today_runs = len(
            [
                r
                for r in self.run_history
                if r.template_id == template.template_id
                and r.started_at
                and r.started_at.date() == now.date()
            ]
        )
        if today_runs >= schedule.max_daily_runs:
            return False
        # Check concurrent runs
        active_runs = len(
            [
                r
                for r in self.active_runs.values()
                if r.template_id == template.template_id
            ]
        )
        if active_runs >= schedule.max_concurrent_runs:
            return False
        # Check cost limits
        if not await self._check_cost_limits(template):
            return False
        # Check schedule type
        if schedule.schedule_type == ScheduleType.CRON:
            return self._check_cron_schedule(schedule, now)
        elif schedule.schedule_type == ScheduleType.INTERVAL:
            return self._check_interval_schedule(template, schedule, now)
        elif schedule.schedule_type == ScheduleType.CONDITIONAL:
            return await self._check_conditional_schedule(schedule, now)
        return False
    def _check_cron_schedule(self, schedule: ScheduleConfig, now: datetime) -> bool:
        """Check if cron schedule should trigger"""
        # Simple cron checking - would need proper cron parser for production
        if schedule.cron_expression:
            # For demo purposes, check basic patterns
            if schedule.cron_expression == "0 8 * * 1-5":  # 8 AM weekdays
                return (
                    now.hour == 8
                    and now.minute == 0
                    and now.weekday() in [0, 1, 2, 3, 4]
                )
            elif schedule.cron_expression == "0 9 * * 1":  # 9 AM Monday
                return now.hour == 9 and now.minute == 0 and now.weekday() == 0
        return False
    def _check_interval_schedule(
        self, template: DeploymentTemplate, schedule: ScheduleConfig, now: datetime
    ) -> bool:
        """Check if interval schedule should trigger"""
        if not schedule.interval_minutes:
            return False
        # Check time window
        if schedule.start_time and schedule.end_time:
            current_time = now.time()
            if not (schedule.start_time <= current_time <= schedule.end_time):
                return False
        # Check days of week
        if schedule.days_of_week and now.weekday() not in schedule.days_of_week:
            return False
        # Check if enough time has passed since last run
        last_run = None
        for run in reversed(self.run_history):
            if run.template_id == template.template_id and run.started_at:
                last_run = run
                break
        if last_run and last_run.started_at:
            time_since_last = (now - last_run.started_at).total_seconds() / 60
            return time_since_last >= schedule.interval_minutes
        return True  # First run
    async def _check_conditional_schedule(
        self, schedule: ScheduleConfig, now: datetime
    ) -> bool:
        """Check conditional schedule (placeholder for complex conditions)"""
        # This would implement complex conditional logic
        # For now, return False as this requires business logic
        return False
    async def _check_cost_limits(self, template: DeploymentTemplate) -> bool:
        """Check if deployment would exceed cost limits"""
        # Check daily cost limit
        today = datetime.now().date()
        daily_cost = sum(
            r.total_cost
            for r in self.run_history
            if r.started_at and r.started_at.date() == today
        )
        if (
            daily_cost + template.swarm_factory_config.max_cost_per_execution
            > template.daily_cost_limit
        ):
            logger.warning(
                f"Daily cost limit would be exceeded for {template.template_id}"
            )
            return False
        # Check monthly cost limit (simplified)
        month_start = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        monthly_cost = sum(
            r.total_cost
            for r in self.run_history
            if r.started_at and r.started_at >= month_start
        )
        if (
            monthly_cost + template.swarm_factory_config.max_cost_per_execution
            > template.monthly_cost_limit
        ):
            logger.warning(
                f"Monthly cost limit would be exceeded for {template.template_id}"
            )
            return False
        return True
    async def _trigger_deployment(
        self, template: DeploymentTemplate, triggered_by: str = "schedule"
    ):
        """Trigger a deployment"""
        run_id = f"run_{uuid4().hex[:8]}"
        deployment_run = DeploymentRun(
            run_id=run_id,
            template_id=template.template_id,
            swarm_id="",  # Will be set after swarm creation
            status=DeploymentStatus.PENDING,
            environment=template.environment,
            triggered_by=triggered_by,
            execution_context=template.execution_context_template,
        )
        self.active_runs[run_id] = deployment_run
        try:
            # Create and execute swarm
            from app.factory.comprehensive_swarm_factory import (
                get_comprehensive_factory,
            )
            factory = get_comprehensive_factory()
            swarm_id = await factory.create_swarm(template.swarm_factory_config)
            deployment_run.swarm_id = swarm_id
            deployment_run.status = DeploymentStatus.RUNNING
            deployment_run.started_at = datetime.now()
            logger.info(
                f"Started deployment run {run_id} for template {template.template_id}"
            )
            # Execute the swarm
            result = await factory.execute_swarm(
                swarm_id, template.execution_context_template
            )
            # Update deployment run with results
            deployment_run.completed_at = datetime.now()
            deployment_run.duration_ms = (
                deployment_run.completed_at - deployment_run.started_at
            ).total_seconds() * 1000
            deployment_run.success = result.success
            deployment_run.final_output = result.final_output
            deployment_run.confidence = result.confidence
            deployment_run.total_cost = result.total_cost
            deployment_run.tokens_used = result.tokens_used
            if result.success:
                deployment_run.status = DeploymentStatus.COMPLETED
                logger.info(f"Deployment run {run_id} completed successfully")
            else:
                deployment_run.status = DeploymentStatus.FAILED
                deployment_run.error_message = (
                    "; ".join(result.errors) if result.errors else "Unknown error"
                )
                logger.error(
                    f"Deployment run {run_id} failed: {deployment_run.error_message}"
                )
            # Send notifications if configured
            await self._send_deployment_notifications(template, deployment_run, result)
        except Exception as e:
            deployment_run.status = DeploymentStatus.FAILED
            deployment_run.error_message = str(e)
            deployment_run.completed_at = datetime.now()
            deployment_run.duration_ms = (
                deployment_run.completed_at - deployment_run.started_at
            ).total_seconds() * 1000
            logger.error(f"Deployment run {run_id} failed with exception: {e}")
        finally:
            # Move from active to history
            if run_id in self.active_runs:
                del self.active_runs[run_id]
            self.run_history.append(deployment_run)
            # Update metrics
            self._update_deployment_metrics(deployment_run)
    async def _send_deployment_notifications(
        self, template: DeploymentTemplate, run: DeploymentRun, result
    ):
        """Send notifications for deployment results"""
        should_notify = (template.success_notifications and run.success) or (
            template.failure_notifications and not run.success
        )
        if should_notify and template.alert_channels:
            try:
                from app.swarms.core.slack_delivery import get_delivery_engine
                delivery_engine = get_delivery_engine()
                # Send notification to each alert channel
                for channel in template.alert_channels:
                    notification_config = DeliveryConfig(
                        channel=channel,
                        priority=(
                            DeliveryPriority.HIGH
                            if not run.success
                            else DeliveryPriority.NORMAL
                        ),
                        auto_summarize_long_content=True,
                    )
                    # Create notification context
                    notification_context = {
                        "deployment_template": template.name,
                        "run_id": run.run_id,
                        "status": run.status.value,
                        "duration": f"{run.duration_ms / 1000:.1f}s",
                        "cost": f"${run.total_cost:.3f}",
                        "triggered_by": run.triggered_by,
                    }
                    await delivery_engine.deliver_result(
                        swarm_result=result,
                        config=notification_config,
                        context=notification_context,
                    )
                    run.notifications_sent.append(channel)
            except Exception as e:
                logger.error(f"Failed to send deployment notifications: {e}")
    async def _cleanup_old_runs(self):
        """Clean up old deployment runs"""
        cutoff_date = datetime.now() - timedelta(days=7)
        # Keep only recent runs
        self.run_history = [
            r for r in self.run_history if r.started_at and r.started_at >= cutoff_date
        ]
    async def _update_cost_tracking(self):
        """Update daily/monthly cost tracking"""
        today = datetime.now().date()
        # Reset daily counter if needed
        if self.deployment_metrics["last_reset_date"] != today:
            self.deployment_metrics["daily_cost"] = 0.0
            self.deployment_metrics["last_reset_date"] = today
        # Calculate daily cost
        daily_cost = sum(
            r.total_cost
            for r in self.run_history
            if r.started_at and r.started_at.date() == today
        )
        self.deployment_metrics["daily_cost"] = daily_cost
        # Calculate monthly cost
        month_start = datetime.now().replace(day=1)
        monthly_cost = sum(
            r.total_cost
            for r in self.run_history
            if r.started_at and r.started_at >= month_start
        )
        self.deployment_metrics["monthly_cost"] = monthly_cost
    def _update_deployment_metrics(self, run: DeploymentRun):
        """Update deployment metrics"""
        self.deployment_metrics["total_runs"] += 1
        if run.success:
            self.deployment_metrics["successful_runs"] += 1
        else:
            self.deployment_metrics["failed_runs"] += 1
        self.deployment_metrics["total_cost"] += run.total_cost
        # Update average response time
        if run.duration_ms > 0:
            total_runs = self.deployment_metrics["total_runs"]
            current_avg = self.deployment_metrics["avg_response_time"]
            self.deployment_metrics["avg_response_time"] = (
                current_avg * (total_runs - 1) + run.duration_ms
            ) / total_runs
    async def trigger_event_deployment(
        self,
        event: str,
        event_data: dict[str, Any],
        priority_override: Optional[int] = None,
    ):
        """Trigger event-driven deployments"""
        triggered_templates = []
        for template in self.deployment_templates.values():
            if not template.schedule_config:
                continue
            schedule = template.schedule_config
            if (
                schedule.schedule_type == ScheduleType.EVENT_DRIVEN
                and event in schedule.trigger_events
            ):
                # Check event conditions
                meets_conditions = True
                for condition_key, condition_value in schedule.event_conditions.items():
                    if event_data.get(condition_key) != condition_value:
                        meets_conditions = False
                        break
                if meets_conditions:
                    # Override priority if specified
                    if priority_override:
                        template.execution_context_template.priority = priority_override
                    await self._trigger_deployment(template, f"event:{event}")
                    triggered_templates.append(template.template_id)
        logger.info(f"Event '{event}' triggered {len(triggered_templates)} deployments")
        return triggered_templates
    def add_deployment_template(self, template: DeploymentTemplate):
        """Add a deployment template"""
        self.deployment_templates[template.template_id] = template
        if template.schedule_config:
            self.schedule_configs[template.schedule_config.schedule_id] = (
                template.schedule_config
            )
        logger.info(f"Added deployment template: {template.name}")
    def remove_deployment_template(self, template_id: str) -> bool:
        """Remove a deployment template"""
        if template_id in self.deployment_templates:
            template = self.deployment_templates[template_id]
            del self.deployment_templates[template_id]
            if template.schedule_config:
                schedule_id = template.schedule_config.schedule_id
                if schedule_id in self.schedule_configs:
                    del self.schedule_configs[schedule_id]
            logger.info(f"Removed deployment template: {template_id}")
            return True
        return False
    def get_deployment_status(self) -> dict[str, Any]:
        """Get current deployment status"""
        success_rate = 0.0
        if self.deployment_metrics["total_runs"] > 0:
            success_rate = (
                self.deployment_metrics["successful_runs"]
                / self.deployment_metrics["total_runs"]
            )
        return {
            "overview": {
                "total_templates": len(self.deployment_templates),
                "active_schedules": len(
                    [s for s in self.schedule_configs.values() if s.enabled]
                ),
                "active_runs": len(self.active_runs),
                "total_runs": self.deployment_metrics["total_runs"],
                "success_rate": success_rate,
                "avg_response_time_ms": self.deployment_metrics["avg_response_time"],
            },
            "cost_tracking": {
                "daily_cost": self.deployment_metrics["daily_cost"],
                "monthly_cost": self.deployment_metrics["monthly_cost"],
                "total_cost": self.deployment_metrics["total_cost"],
            },
            "active_runs": [
                {
                    "run_id": run.run_id,
                    "template_id": run.template_id,
                    "status": run.status.value,
                    "started_at": (
                        run.started_at.isoformat() if run.started_at else None
                    ),
                    "duration_ms": run.duration_ms,
                }
                for run in self.active_runs.values()
            ],
            "recent_runs": [
                {
                    "run_id": run.run_id,
                    "template_id": run.template_id,
                    "status": run.status.value,
                    "success": run.success,
                    "cost": run.total_cost,
                    "duration_ms": run.duration_ms,
                    "started_at": (
                        run.started_at.isoformat() if run.started_at else None
                    ),
                }
                for run in sorted(
                    self.run_history,
                    key=lambda r: r.started_at or datetime.min,
                    reverse=True,
                )[:10]
            ],
            "scheduler_status": {
                "is_running": self.is_running,
                "scheduler_active": self.scheduler_task is not None
                and not self.scheduler_task.done(),
            },
        }
# Global deployment manager instance
_deployment_manager = None
def get_deployment_manager() -> DeploymentManager:
    """Get global deployment manager instance"""
    global _deployment_manager
    if _deployment_manager is None:
        _deployment_manager = DeploymentManager()
    return _deployment_manager
# Convenience functions
async def start_automated_deployments():
    """Start automated deployment system"""
    manager = get_deployment_manager()
    await manager.start_scheduler()
async def stop_automated_deployments():
    """Stop automated deployment system"""
    manager = get_deployment_manager()
    await manager.stop_scheduler()
async def trigger_emergency_response(event_data: dict[str, Any]):
    """Trigger emergency response deployment"""
    manager = get_deployment_manager()
    return await manager.trigger_event_deployment(
        "system_alert", event_data, priority_override=1
    )
