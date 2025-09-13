"""
Durable Outbox Pattern Implementation
Ensures reliable message delivery with transactional guarantees
"""
import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import asyncpg
import redis.asyncio as redis
from pydantic import BaseModel
logger = logging.getLogger(__name__)
class EventStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
class EventType(Enum):
    GITHUB_PR_CREATE = "github.pr.create"
    GITHUB_COMMIT = "github.commit"
    SEARCH_INDEX = "search.index"
    NOTIFICATION_SEND = "notification.send"
    WEBHOOK_CALL = "webhook.call"
@dataclass
class OutboxEvent:
    id: str
    event_type: EventType
    payload: Dict[str, Any]
    status: EventStatus
    created_at: datetime
    scheduled_at: datetime
    attempts: int = 0
    max_attempts: int = 5
    last_error: Optional[str] = None
    idempotency_key: Optional[str] = None
    correlation_id: Optional[str] = None
class OutboxEventModel(BaseModel):
    event_type: str
    payload: Dict[str, Any]
    scheduled_at: Optional[datetime] = None
    max_attempts: int = 5
    idempotency_key: Optional[str] = None
    correlation_id: Optional[str] = None
class DurableOutbox:
    """
    Implements durable outbox pattern for reliable event processing
    """
    def __init__(self, db_pool: asyncpg.Pool, redis_pool: redis.ConnectionPool):
        self.db_pool = db_pool
        self.redis_pool = redis_pool
        self.worker_running = False
        self.worker_task = None
        # Configuration
        self.batch_size = 10
        self.poll_interval = 1.0  # seconds
        self.retry_delays = [1, 5, 15, 60, 300]  # seconds
        self.dead_letter_threshold = 5
    async def initialize(self):
        """Initialize outbox tables and indexes"""
        async with self.db_pool.acquire() as conn:
            # Create outbox events table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS outbox_events (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    event_type VARCHAR(100) NOT NULL,
                    payload JSONB NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    attempts INTEGER DEFAULT 0,
                    max_attempts INTEGER DEFAULT 5,
                    last_error TEXT,
                    idempotency_key VARCHAR(255),
                    correlation_id VARCHAR(255),
                    processed_at TIMESTAMP WITH TIME ZONE
                );
            """)
            # Create indexes for performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_outbox_status_scheduled 
                ON outbox_events (status, scheduled_at) 
                WHERE status IN ('pending', 'failed');
            """)
            await conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_outbox_idempotency 
                ON outbox_events (idempotency_key) 
                WHERE idempotency_key IS NOT NULL;
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_outbox_correlation 
                ON outbox_events (correlation_id) 
                WHERE correlation_id IS NOT NULL;
            """)
            logger.info("Outbox tables and indexes initialized")
    async def publish_event(
        self,
        event_type: EventType,
        payload: Dict[str, Any],
        scheduled_at: Optional[datetime] = None,
        idempotency_key: Optional[str] = None,
        correlation_id: Optional[str] = None,
        max_attempts: int = 5,
        conn: Optional[asyncpg.Connection] = None
    ) -> str:
        """
        Publish event to outbox within a transaction
        """
        event_id = str(uuid.uuid4())
        if scheduled_at is None:
            scheduled_at = datetime.utcnow()
        # Use provided connection or acquire new one
        if conn:
            return await self._insert_event(
                conn, event_id, event_type, payload, scheduled_at,
                idempotency_key, correlation_id, max_attempts
            )
        else:
            async with self.db_pool.acquire() as connection:
                return await self._insert_event(
                    connection, event_id, event_type, payload, scheduled_at,
                    idempotency_key, correlation_id, max_attempts
                )
    async def _insert_event(
        self,
        conn: asyncpg.Connection,
        event_id: str,
        event_type: EventType,
        payload: Dict[str, Any],
        scheduled_at: datetime,
        idempotency_key: Optional[str],
        correlation_id: Optional[str],
        max_attempts: int
    ) -> str:
        """Insert event into outbox table"""
        try:
            await conn.execute("""
                INSERT INTO outbox_events (
                    id, event_type, payload, scheduled_at, 
                    idempotency_key, correlation_id, max_attempts
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, event_id, event_type.value, json.dumps(payload), 
                scheduled_at, idempotency_key, correlation_id, max_attempts)
            logger.debug(f"Published event {event_id} of type {event_type.value}")
            return event_id
        except asyncpg.UniqueViolationError:
            if idempotency_key:
                # Event already exists with this idempotency key
                logger.info(f"Event with idempotency key {idempotency_key} already exists")
                # Return existing event ID
                row = await conn.fetchrow(
                    "SELECT id FROM outbox_events WHERE idempotency_key = $1",
                    idempotency_key
                )
                return str(row['id']) if row else event_id
            else:
                raise
    async def start_worker(self):
        """Start the outbox worker for processing events"""
        if self.worker_running:
            logger.warning("Outbox worker is already running")
            return
        self.worker_running = True
        self.worker_task = asyncio.create_task(self._worker_loop())
        logger.info("Outbox worker started")
    async def stop_worker(self):
        """Stop the outbox worker"""
        if not self.worker_running:
            return
        self.worker_running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Outbox worker stopped")
    async def _worker_loop(self):
        """Main worker loop for processing outbox events"""
        while self.worker_running:
            try:
                # Get pending events
                events = await self._get_pending_events()
                if events:
                    # Process events in parallel
                    tasks = [self._process_event(event) for event in events]
                    await asyncio.gather(*tasks, return_exceptions=True)
                else:
                    # No events to process, wait before next poll
                    await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Error in outbox worker loop: {e}")
                await asyncio.sleep(self.poll_interval)
    async def _get_pending_events(self) -> List[OutboxEvent]:
        """Get pending events ready for processing"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, event_type, payload, status, created_at, scheduled_at,
                       attempts, max_attempts, last_error, idempotency_key, correlation_id
                FROM outbox_events
                WHERE status IN ('pending', 'failed')
                  AND scheduled_at <= NOW()
                ORDER BY created_at
                LIMIT $1
                FOR UPDATE SKIP LOCKED
            """, self.batch_size)
            events = []
            for row in rows:
                events.append(OutboxEvent(
                    id=str(row['id']),
                    event_type=EventType(row['event_type']),
                    payload=json.loads(row['payload']),
                    status=EventStatus(row['status']),
                    created_at=row['created_at'],
                    scheduled_at=row['scheduled_at'],
                    attempts=row['attempts'],
                    max_attempts=row['max_attempts'],
                    last_error=row['last_error'],
                    idempotency_key=row['idempotency_key'],
                    correlation_id=row['correlation_id']
                ))
            return events
    async def _process_event(self, event: OutboxEvent):
        """Process a single outbox event"""
        # Mark event as processing
        await self._update_event_status(event.id, EventStatus.PROCESSING)
        try:
            # Route event to appropriate handler
            success = await self._route_event(event)
            if success:
                # Mark as completed
                await self._update_event_status(
                    event.id, 
                    EventStatus.COMPLETED,
                    processed_at=datetime.utcnow()
                )
                logger.debug(f"Event {event.id} processed successfully")
            else:
                # Handle failure
                await self._handle_event_failure(event, "Handler returned False")
        except Exception as e:
            # Handle exception
            await self._handle_event_failure(event, str(e))
            logger.error(f"Error processing event {event.id}: {e}")
    async def _route_event(self, event: OutboxEvent) -> bool:
        """Route event to appropriate handler"""
        if event.event_type == EventType.GITHUB_PR_CREATE:
            return await self._handle_github_pr_create(event)
        elif event.event_type == EventType.GITHUB_COMMIT:
            return await self._handle_github_commit(event)
        elif event.event_type == EventType.SEARCH_INDEX:
            return await self._handle_search_index(event)
        elif event.event_type == EventType.NOTIFICATION_SEND:
            return await self._handle_notification_send(event)
        elif event.event_type == EventType.WEBHOOK_CALL:
            return await self._handle_webhook_call(event)
        else:
            logger.error(f"Unknown event type: {event.event_type}")
            return False
    async def _handle_github_pr_create(self, event: OutboxEvent) -> bool:
        """Handle GitHub PR creation event"""
        try:
            # Call GitHub service to create PR
            async with redis.Redis(connection_pool=self.redis_pool) as r:
                # Publish to Redis stream for GitHub service
                await r.xadd(
                    "github:pr:create",
                    {
                        "event_id": event.id,
                        "payload": json.dumps(event.payload),
                        "correlation_id": event.correlation_id or ""
                    }
                )
            return True
        except Exception as e:
            logger.error(f"Failed to handle GitHub PR create event {event.id}: {e}")
            return False
    async def _handle_github_commit(self, event: OutboxEvent) -> bool:
        """Handle GitHub commit event"""
        try:
            async with redis.Redis(connection_pool=self.redis_pool) as r:
                await r.xadd(
                    "github:commit",
                    {
                        "event_id": event.id,
                        "payload": json.dumps(event.payload),
                        "correlation_id": event.correlation_id or ""
                    }
                )
            return True
        except Exception as e:
            logger.error(f"Failed to handle GitHub commit event {event.id}: {e}")
            return False
    async def _handle_search_index(self, event: OutboxEvent) -> bool:
        """Handle search indexing event"""
        try:
            async with redis.Redis(connection_pool=self.redis_pool) as r:
                await r.xadd(
                    "search:index",
                    {
                        "event_id": event.id,
                        "payload": json.dumps(event.payload),
                        "correlation_id": event.correlation_id or ""
                    }
                )
            return True
        except Exception as e:
            logger.error(f"Failed to handle search index event {event.id}: {e}")
            return False
    async def _handle_notification_send(self, event: OutboxEvent) -> bool:
        """Handle notification sending event"""
        try:
            async with redis.Redis(connection_pool=self.redis_pool) as r:
                await r.xadd(
                    "notifications:send",
                    {
                        "event_id": event.id,
                        "payload": json.dumps(event.payload),
                        "correlation_id": event.correlation_id or ""
                    }
                )
            return True
        except Exception as e:
            logger.error(f"Failed to handle notification send event {event.id}: {e}")
            return False
    async def _handle_webhook_call(self, event: OutboxEvent) -> bool:
        """Handle webhook call event"""
        try:
            async with redis.Redis(connection_pool=self.redis_pool) as r:
                await r.xadd(
                    "webhooks:call",
                    {
                        "event_id": event.id,
                        "payload": json.dumps(event.payload),
                        "correlation_id": event.correlation_id or ""
                    }
                )
            return True
        except Exception as e:
            logger.error(f"Failed to handle webhook call event {event.id}: {e}")
            return False
    async def _handle_event_failure(self, event: OutboxEvent, error_message: str):
        """Handle event processing failure with retry logic"""
        attempts = event.attempts + 1
        if attempts >= event.max_attempts:
            # Move to dead letter queue
            await self._update_event_status(
                event.id,
                EventStatus.DEAD_LETTER,
                attempts=attempts,
                last_error=error_message
            )
            logger.warning(f"Event {event.id} moved to dead letter queue after {attempts} attempts")
        else:
            # Schedule retry with exponential backoff
            retry_delay = self.retry_delays[min(attempts - 1, len(self.retry_delays) - 1)]
            scheduled_at = datetime.utcnow() + timedelta(seconds=retry_delay)
            await self._update_event_status(
                event.id,
                EventStatus.FAILED,
                attempts=attempts,
                last_error=error_message,
                scheduled_at=scheduled_at
            )
            logger.info(f"Event {event.id} scheduled for retry in {retry_delay}s (attempt {attempts})")
    async def _update_event_status(
        self,
        event_id: str,
        status: EventStatus,
        attempts: Optional[int] = None,
        last_error: Optional[str] = None,
        scheduled_at: Optional[datetime] = None,
        processed_at: Optional[datetime] = None
    ):
        """Update event status in database"""
        async with self.db_pool.acquire() as conn:
            query_parts = ["UPDATE outbox_events SET status = $2"]
            params = [event_id, status.value]
            param_count = 2
            if attempts is not None:
                param_count += 1
                query_parts.append(f"attempts = ${param_count}")
                params.append(attempts)
            if last_error is not None:
                param_count += 1
                query_parts.append(f"last_error = ${param_count}")
                params.append(last_error)
            if scheduled_at is not None:
                param_count += 1
                query_parts.append(f"scheduled_at = ${param_count}")
                params.append(scheduled_at)
            if processed_at is not None:
                param_count += 1
                query_parts.append(f"processed_at = ${param_count}")
                params.append(processed_at)
            query = " ".join(query_parts) + " WHERE id = $1"
            await conn.execute(query, *params)
    async def get_event_status(self, event_id: str) -> Optional[OutboxEvent]:
        """Get status of a specific event"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, event_type, payload, status, created_at, scheduled_at,
                       attempts, max_attempts, last_error, idempotency_key, correlation_id
                FROM outbox_events
                WHERE id = $1
            """, event_id)
            if row:
                return OutboxEvent(
                    id=str(row['id']),
                    event_type=EventType(row['event_type']),
                    payload=json.loads(row['payload']),
                    status=EventStatus(row['status']),
                    created_at=row['created_at'],
                    scheduled_at=row['scheduled_at'],
                    attempts=row['attempts'],
                    max_attempts=row['max_attempts'],
                    last_error=row['last_error'],
                    idempotency_key=row['idempotency_key'],
                    correlation_id=row['correlation_id']
                )
            return None
    async def get_metrics(self) -> Dict[str, Any]:
        """Get outbox processing metrics"""
        async with self.db_pool.acquire() as conn:
            # Get status counts
            status_counts = await conn.fetch("""
                SELECT status, COUNT(*) as count
                FROM outbox_events
                WHERE created_at > NOW() - INTERVAL '24 hours'
                GROUP BY status
            """)
            # Get processing rates
            processing_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_events,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed_events,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed_events,
                    COUNT(*) FILTER (WHERE status = 'dead_letter') as dead_letter_events,
                    AVG(EXTRACT(EPOCH FROM (processed_at - created_at))) as avg_processing_time
                FROM outbox_events
                WHERE created_at > NOW() - INTERVAL '24 hours'
            """)
            return {
                "status_counts": {row['status']: row['count'] for row in status_counts},
                "total_events_24h": processing_stats['total_events'] or 0,
                "completed_events_24h": processing_stats['completed_events'] or 0,
                "failed_events_24h": processing_stats['failed_events'] or 0,
                "dead_letter_events_24h": processing_stats['dead_letter_events'] or 0,
                "avg_processing_time_seconds": processing_stats['avg_processing_time'] or 0,
                "worker_running": self.worker_running
            }
