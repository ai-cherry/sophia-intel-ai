"""
Automated Synchronization Scheduler for Foundational Knowledge

Provides scheduled synchronization between local knowledge base and Airtable,
with configurable intervals, monitoring, and error recovery.
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.knowledge.foundational_manager import FoundationalKnowledgeManager
from app.sync.airtable_sync import AirtableSync

logger = logging.getLogger(__name__)


class SyncStatus(Enum):
    """Synchronization status states"""

    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class SyncScheduler:
    """
    Manages automated synchronization scheduling for foundational knowledge.

    Features:
    - Configurable sync intervals (hourly, daily, weekly)
    - Incremental and full sync support
    - Error recovery and retry logic
    - Sync status monitoring and history
    - Conflict detection and alerting
    """

    def __init__(self):
        """Initialize the sync scheduler"""
        self.scheduler = AsyncIOScheduler()
        self.sync_service = AirtableSync()
        self.knowledge_manager = FoundationalKnowledgeManager()

        # Sync status tracking
        self.current_status = SyncStatus.IDLE
        self.last_sync_time: Optional[datetime] = None
        self.last_sync_result: Optional[dict[str, Any]] = None
        self.sync_history: list[dict[str, Any]] = []
        self.max_history_entries = 100

        # Error tracking
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3

        # Configuration
        self.incremental_interval_minutes = getattr(
            settings, "sync_incremental_interval", 60
        )
        self.full_sync_cron = getattr(
            settings, "sync_full_cron", "0 2 * * *"
        )  # 2 AM daily
        self.enable_auto_sync = getattr(settings, "enable_auto_sync", True)

    async def initialize(self):
        """
        Initialize the scheduler and set up jobs.
        """
        if not self.enable_auto_sync:
            logger.info("Auto-sync is disabled. Scheduler will not start.")
            return

        try:
            # Schedule incremental sync
            self.scheduler.add_job(
                self._run_incremental_sync,
                trigger=IntervalTrigger(minutes=self.incremental_interval_minutes),
                id="incremental_sync",
                name="Incremental Knowledge Sync",
                misfire_grace_time=300,  # 5 minutes grace time
                coalesce=True,  # Coalesce missed jobs
                max_instances=1,  # Only one sync at a time
            )

            # Schedule full sync
            self.scheduler.add_job(
                self._run_full_sync,
                trigger=CronTrigger.from_crontab(self.full_sync_cron),
                id="full_sync",
                name="Full Knowledge Sync",
                misfire_grace_time=3600,  # 1 hour grace time
                coalesce=True,
                max_instances=1,
            )

            # Schedule cleanup job
            self.scheduler.add_job(
                self._cleanup_history,
                trigger=IntervalTrigger(hours=24),
                id="cleanup_history",
                name="Sync History Cleanup",
            )

            # Start the scheduler
            self.scheduler.start()

            logger.info(
                f"Sync scheduler initialized. Incremental: every {self.incremental_interval_minutes} minutes, Full: {self.full_sync_cron}"
            )

            # Run initial sync
            await self._run_initial_sync()

        except Exception as e:
            logger.error(f"Failed to initialize sync scheduler: {e}")
            raise

    async def shutdown(self):
        """
        Gracefully shutdown the scheduler.
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Sync scheduler shut down")

    async def _run_incremental_sync(self):
        """
        Run incremental synchronization.
        """
        if self.current_status == SyncStatus.RUNNING:
            logger.warning("Sync already in progress, skipping incremental sync")
            return

        logger.info("Starting incremental sync")
        self.current_status = SyncStatus.RUNNING
        start_time = datetime.utcnow()

        try:
            # Get last sync timestamp
            last_sync = self.last_sync_time or datetime.utcnow() - timedelta(hours=1)

            # Run incremental sync
            result = await self.sync_service.incremental_sync(since=last_sync)

            # Process results
            sync_result = {
                "type": "incremental",
                "start_time": start_time,
                "end_time": datetime.utcnow(),
                "duration_seconds": (datetime.utcnow() - start_time).total_seconds(),
                "records_synced": result.get("records_synced", 0),
                "conflicts_detected": result.get("conflicts_detected", 0),
                "errors": result.get("errors", []),
                "status": (
                    SyncStatus.SUCCESS
                    if not result.get("errors")
                    else SyncStatus.PARTIAL
                ),
            }

            # Update status
            self.current_status = sync_result["status"]
            self.last_sync_time = datetime.utcnow()
            self.last_sync_result = sync_result
            self._add_to_history(sync_result)

            # Reset failure counter on success
            if sync_result["status"] == SyncStatus.SUCCESS:
                self.consecutive_failures = 0

            logger.info(
                f"Incremental sync completed: {sync_result['records_synced']} records, {sync_result['conflicts_detected']} conflicts"
            )

            # Handle conflicts if any
            if sync_result["conflicts_detected"] > 0:
                await self._handle_conflicts(result.get("conflicts", []))

        except Exception as e:
            logger.error(f"Incremental sync failed: {e}")

            sync_result = {
                "type": "incremental",
                "start_time": start_time,
                "end_time": datetime.utcnow(),
                "duration_seconds": (datetime.utcnow() - start_time).total_seconds(),
                "error": str(e),
                "status": SyncStatus.FAILED,
            }

            self.current_status = SyncStatus.FAILED
            self.last_sync_result = sync_result
            self._add_to_history(sync_result)

            # Increment failure counter
            self.consecutive_failures += 1

            # Check if we should disable sync
            if self.consecutive_failures >= self.max_consecutive_failures:
                await self._handle_critical_failure()

        finally:
            if self.current_status == SyncStatus.RUNNING:
                self.current_status = SyncStatus.IDLE

    async def _run_full_sync(self):
        """
        Run full synchronization.
        """
        if self.current_status == SyncStatus.RUNNING:
            logger.warning("Sync already in progress, skipping full sync")
            return

        logger.info("Starting full sync")
        self.current_status = SyncStatus.RUNNING
        start_time = datetime.utcnow()

        try:
            # Run full sync
            result = await self.sync_service.full_sync()

            # Process results
            sync_result = {
                "type": "full",
                "start_time": start_time,
                "end_time": datetime.utcnow(),
                "duration_seconds": (datetime.utcnow() - start_time).total_seconds(),
                "records_synced": result.get("records_synced", 0),
                "conflicts_detected": result.get("conflicts_detected", 0),
                "errors": result.get("errors", []),
                "status": (
                    SyncStatus.SUCCESS
                    if not result.get("errors")
                    else SyncStatus.PARTIAL
                ),
            }

            # Update status
            self.current_status = sync_result["status"]
            self.last_sync_time = datetime.utcnow()
            self.last_sync_result = sync_result
            self._add_to_history(sync_result)

            # Reset failure counter on success
            if sync_result["status"] == SyncStatus.SUCCESS:
                self.consecutive_failures = 0

            logger.info(
                f"Full sync completed: {sync_result['records_synced']} records, {sync_result['conflicts_detected']} conflicts"
            )

            # Handle conflicts if any
            if sync_result["conflicts_detected"] > 0:
                await self._handle_conflicts(result.get("conflicts", []))

        except Exception as e:
            logger.error(f"Full sync failed: {e}")

            sync_result = {
                "type": "full",
                "start_time": start_time,
                "end_time": datetime.utcnow(),
                "duration_seconds": (datetime.utcnow() - start_time).total_seconds(),
                "error": str(e),
                "status": SyncStatus.FAILED,
            }

            self.current_status = SyncStatus.FAILED
            self.last_sync_result = sync_result
            self._add_to_history(sync_result)

            # Increment failure counter
            self.consecutive_failures += 1

            # Check if we should disable sync
            if self.consecutive_failures >= self.max_consecutive_failures:
                await self._handle_critical_failure()

        finally:
            if self.current_status == SyncStatus.RUNNING:
                self.current_status = SyncStatus.IDLE

    async def _run_initial_sync(self):
        """
        Run initial sync on scheduler startup.
        """
        logger.info("Running initial sync on startup")

        # Check if we need a full sync
        stats = await self.knowledge_manager.get_statistics()

        if stats.get("total_entries", 0) == 0:
            # Empty database, run full sync
            logger.info("Empty database detected, running full sync")
            await self._run_full_sync()
        else:
            # Run incremental sync
            logger.info("Existing data found, running incremental sync")
            await self._run_incremental_sync()

    async def _handle_conflicts(self, conflicts: list[dict[str, Any]]):
        """
        Handle sync conflicts.

        Args:
            conflicts: List of conflict records
        """
        logger.warning(f"Handling {len(conflicts)} sync conflicts")

        # For now, log conflicts for manual resolution
        # In production, this could send alerts or attempt auto-resolution
        for conflict in conflicts:
            logger.warning(f"Conflict detected: {conflict}")

        # TODO: Implement conflict resolution strategies
        # - Newest wins
        # - Local wins
        # - Remote wins
        # - Manual review queue

    async def _handle_critical_failure(self):
        """
        Handle critical sync failure (multiple consecutive failures).
        """
        logger.critical(
            f"Critical sync failure: {self.consecutive_failures} consecutive failures"
        )

        # Pause scheduled jobs
        self.scheduler.pause_job("incremental_sync")
        self.scheduler.pause_job("full_sync")

        # TODO: Send alert to administrators
        # - Email notification
        # - Slack/Discord webhook
        # - PagerDuty incident

        logger.critical(
            "Sync scheduler paused due to critical failures. Manual intervention required."
        )

    def _add_to_history(self, sync_result: dict[str, Any]):
        """
        Add sync result to history.

        Args:
            sync_result: Sync operation result
        """
        self.sync_history.append(sync_result)

        # Trim history if needed
        if len(self.sync_history) > self.max_history_entries:
            self.sync_history = self.sync_history[-self.max_history_entries :]

    async def _cleanup_history(self):
        """
        Clean up old sync history entries.
        """
        cutoff_time = datetime.utcnow() - timedelta(days=7)

        self.sync_history = [
            entry
            for entry in self.sync_history
            if entry.get("start_time", datetime.min) > cutoff_time
        ]

        logger.debug(
            f"Cleaned up sync history, {len(self.sync_history)} entries remaining"
        )

    async def trigger_manual_sync(
        self, sync_type: str = "incremental"
    ) -> dict[str, Any]:
        """
        Manually trigger a synchronization.

        Args:
            sync_type: Type of sync ('incremental' or 'full')

        Returns:
            Sync result dictionary
        """
        if self.current_status == SyncStatus.RUNNING:
            return {
                "error": "Sync already in progress",
                "current_status": self.current_status.value,
            }

        if sync_type == "full":
            await self._run_full_sync()
        else:
            await self._run_incremental_sync()

        return self.last_sync_result

    def get_status(self) -> dict[str, Any]:
        """
        Get current sync status and statistics.

        Returns:
            Status dictionary
        """
        # Calculate sync health
        sync_health = "healthy"
        if self.consecutive_failures > 0:
            sync_health = "degraded"
        if self.consecutive_failures >= self.max_consecutive_failures:
            sync_health = "critical"

        # Get next scheduled runs
        next_runs = {}
        for job in self.scheduler.get_jobs():
            if job.next_run_time:
                next_runs[job.id] = job.next_run_time.isoformat()

        return {
            "current_status": self.current_status.value,
            "sync_health": sync_health,
            "consecutive_failures": self.consecutive_failures,
            "last_sync_time": (
                self.last_sync_time.isoformat() if self.last_sync_time else None
            ),
            "last_sync_result": self.last_sync_result,
            "next_scheduled_runs": next_runs,
            "scheduler_running": self.scheduler.running,
            "auto_sync_enabled": self.enable_auto_sync,
            "incremental_interval_minutes": self.incremental_interval_minutes,
            "full_sync_schedule": self.full_sync_cron,
            "history_count": len(self.sync_history),
        }

    def get_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get sync history.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of sync history entries
        """
        return self.sync_history[-limit:] if self.sync_history else []

    async def resume_scheduler(self):
        """
        Resume paused scheduler after critical failure.
        """
        if not self.scheduler.running:
            logger.info("Scheduler is not running")
            return

        # Resume jobs
        self.scheduler.resume_job("incremental_sync")
        self.scheduler.resume_job("full_sync")

        # Reset failure counter
        self.consecutive_failures = 0

        logger.info("Sync scheduler resumed")


# Global scheduler instance
_global_scheduler: Optional[SyncScheduler] = None


def get_sync_scheduler() -> SyncScheduler:
    """Get or create global sync scheduler instance."""
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = SyncScheduler()
    return _global_scheduler


async def initialize_sync_scheduler():
    """Initialize the global sync scheduler."""
    scheduler = get_sync_scheduler()
    await scheduler.initialize()
    return scheduler
