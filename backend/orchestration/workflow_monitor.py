"\nWorkflow Monitor for Sophia AI Orchestration\nTracks metrics and provides monitoring capabilities\n"

import asyncio
import logging
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from prometheus_client import Counter, Gauge, Histogram, Info

logger = logging.getLogger(__name__)


class WorkflowMonitor:
    """Monitors workflow execution with Prometheus metrics"""

    def __init__(self):
        self.task_counter = Counter(
            "sophia_workflow_tasks_total",
            "Total number of tasks processed",
            ["task_type", "status"],
        )
        self.task_duration = Histogram(
            "sophia_workflow_task_duration_seconds",
            "Task execution duration in seconds",
            ["task_type"],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0),
        )
        self.active_workflows = Gauge(
            "sophia_workflow_active_count", "Number of currently active workflows"
        )
        self.tool_usage = Counter(
            "sophia_workflow_tool_usage_total",
            "Tool usage count",
            ["tool_name", "status"],
        )
        self.step_duration = Histogram(
            "sophia_workflow_step_duration_seconds",
            "Duration of individual workflow steps",
            ["step_name"],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
        )
        self.error_counter = Counter(
            "sophia_workflow_errors_total",
            "Total number of workflow errors",
            ["error_type", "step"],
        )
        self.system_info = Info("sophia_workflow_system", "System information")
        self.system_info.info({"version": "1.0.0", "environment": "production"})
        self.memory_usage = Gauge("sophia_workflow_memory_usage_bytes", "Memory usage in bytes")
        self.task_queue_size = Gauge("sophia_workflow_queue_size", "Number of tasks in queue")
        self.task_complexity = Counter(
            "sophia_workflow_task_complexity_total",
            "Task complexity distribution",
            ["complexity"],
        )
        self.estimated_vs_actual = Histogram(
            "sophia_workflow_estimation_accuracy_ratio",
            "Ratio of actual to estimated time",
            buckets=(0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0),
        )

    @asynccontextmanager
    async def track_task(
        self, task_id: str, task_type: str
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Context manager to track task execution"""
        start_time = time.time()
        self.active_workflows.inc()
        context = {
            "task_id": task_id,
            "task_type": task_type,
            "start_time": start_time,
            "steps": {},
        }
        try:
            yield context
            duration = time.time() - start_time
            self.task_counter.labels(task_type=task_type, status="success").inc()
            self.task_duration.labels(task_type=task_type).observe(duration)
            logger.info(f"Task {task_id} completed in {duration:.2f}s")
        except Exception as e:
            duration = time.time() - start_time
            self.task_counter.labels(task_type=task_type, status="error").inc()
            self.task_duration.labels(task_type=task_type).observe(duration)
            error_type = type(e).__name__
            self.error_counter.labels(
                error_type=error_type, step=context.get("current_step", "unknown")
            ).inc()
            logger.error(f"Task {task_id} failed after {duration:.2f}s: {e}")
            raise
        finally:
            self.active_workflows.dec()

    def track_tool_usage(self, tool_name: str, success: bool = True):
        """Track tool usage"""
        status = "success" if success else "error"
        self.tool_usage.labels(tool_name=tool_name, status=status).inc()

    def track_step(self, step_name: str, duration: float):
        """Track individual step duration"""
        self.step_duration.labels(step_name=step_name).observe(duration)

    def track_complexity(self, complexity: str):
        """Track task complexity"""
        self.task_complexity.labels(complexity=complexity).inc()

    def track_estimation_accuracy(self, estimated_hours: float, actual_hours: float):
        """Track estimation accuracy"""
        if estimated_hours > 0:
            ratio = actual_hours / estimated_hours
            self.estimated_vs_actual.observe(ratio)

    def update_queue_size(self, size: int):
        """Update task queue size"""
        self.task_queue_size.set(size)

    def update_memory_usage(self):
        """Update memory usage metric"""
        try:
            import psutil

            process = psutil.Process()
            memory_bytes = process.memory_info().rss
            self.memory_usage.set(memory_bytes)
        except ImportError:
            pass

    async def start_metrics_updater(self, interval: int = 120, smart_polling: bool = True):
        """Start optimized background task to update system metrics with smart polling"""
        last_activity = time.time()
        active_polling_interval = 30
        idle_polling_interval = interval
        while True:
            try:
                current_time = time.time()
                current_active_workflows = self.active_workflows._value
                if smart_polling and current_active_workflows > 0:
                    current_interval = active_polling_interval
                    last_activity = current_time
                elif current_time - last_activity > 300:
                    current_interval = idle_polling_interval
                else:
                    current_interval = active_polling_interval
                self.update_memory_usage()
                await asyncio.sleep(current_interval)
            except Exception as e:
                logger.error(f"Error updating metrics: {e}")
                await asyncio.sleep(interval)

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get a summary of current metrics"""
        return {
            "active_workflows": self.active_workflows._value,
            "total_tasks": sum(
                self.task_counter.labels(task_type=tt, status=s)._value._value
                for tt in [
                    "bugfix",
                    "feature",
                    "refactor",
                    "test",
                    "documentation",
                    "deployment",
                    "other",
                ]
                for s in ["success", "error"]
            ),
            "timestamp": datetime.now().isoformat(),
        }

    @asynccontextmanager
    async def track_step_execution(self, step_name: str) -> AsyncGenerator[None, None]:
        """Track individual step execution time"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.track_step(step_name, duration)
            logger.debug(f"Step '{step_name}' completed in {duration:.2f}s")
