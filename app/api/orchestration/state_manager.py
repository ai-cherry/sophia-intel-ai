"""
State Manager for Sophia AI Orchestration
Handles workflow state persistence with Redis and PostgreSQL
"""

import json
import logging
import os
from datetime import datetime
from typing import Any

import asyncpg
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class StateManager:
    """Manages workflow state with Redis caching and PostgreSQL persistence"""

    def __init__(
        self, redis_url: str | None = None, pg_config: dict[str, Any] | None = None
    ):
        # Redis configuration
        self.redis_url = redis_url or os.getenv(
            "REDIS_URL", "redis://${REDIS_HOST}:${REDIS_PORT}/3"
        )
        self.redis: redis.Redis | None = None

        # PostgreSQL configuration
        self.pg_config = pg_config or {
            "host": os.getenv("POSTGRES_HOST", "postgres"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DB", "sophia_ai"),
            "user": os.getenv("POSTGRES_USER", "sophia"),
            "password": os.getenv("POSTGRES_PASSWORD", "sophia"),
        }
        self.pg_pool: asyncpg.Pool | None = None

    async def initialize(self):
        """Initialize connections"""
        # Initialize Redis
        try:
            self.redis = await redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # Continue without Redis - PostgreSQL only mode
            self.redis = None

        # Initialize PostgreSQL pool
        try:
            self.pg_pool = await asyncpg.create_pool(**self.pg_config)
            logger.info("PostgreSQL connection pool created")
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL pool: {e}")
            raise  # PostgreSQL is required

    async def close(self):
        """Close connections"""
        if self.redis:
            await self.redis.close()
        if self.pg_pool:
            await self.pg_pool.close()

    async def save_state(self, task_id: str, state: dict[str, Any]):
        """Save workflow state to Redis and PostgreSQL"""
        state_json = json.dumps(state)

        # Save to Redis for quick access
        if self.redis:
            try:
                await self.redis.set(
                    f"workflow:state:{task_id}", state_json, ex=86400  # 24 hour expiry
                )
                logger.debug(f"State saved to Redis for task {task_id}")
            except Exception as e:
                logger.warning(f"Failed to save to Redis: {e}")

        # Save to PostgreSQL for persistence
        if self.pg_pool:
            async with self.pg_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO workflow_states (task_id, state, updated_at)
                    VALUES ($1, $2::jsonb, NOW())
                    ON CONFLICT (task_id)
                    DO UPDATE SET state = $2::jsonb, updated_at = NOW()
                """,
                    task_id,
                    state_json,
                )

            # Also save to history
            await self._save_history(
                task_id, state.get("current_step", "unknown"), state
            )

        logger.info(f"State saved for task {task_id}")

    async def get_state(self, task_id: str) -> dict[str, Any] | None:
        """Retrieve workflow state"""
        # Try Redis first
        if self.redis:
            try:
                state_json = await self.redis.get(f"workflow:state:{task_id}")
                if state_json:
                    logger.debug(f"State retrieved from Redis for task {task_id}")
                    return json.loads(state_json)
            except Exception as e:
                logger.warning(f"Failed to get from Redis: {e}")

        # Fall back to PostgreSQL
        if self.pg_pool:
            async with self.pg_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT state FROM workflow_states WHERE task_id = $1", task_id
                )
                if row:
                    logger.debug(f"State retrieved from PostgreSQL for task {task_id}")
                    return json.loads(row["state"])

        return None

    async def update_context(self, task_id: str, context_update: dict[str, Any]):
        """Update workflow context"""
        state = await self.get_state(task_id)
        if state:
            if "context" not in state:
                state["context"] = {}
            state["context"].update(context_update)
            state["metadata"]["updated_at"] = datetime.now().isoformat()
            await self.save_state(task_id, state)

    async def list_tasks(
        self, status: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """List tasks with optional status filter"""
        if not self.pg_pool:
            return []

        async with self.pg_pool.acquire() as conn:
            if status:
                rows = await conn.fetch(
                    """
                    SELECT task_id, state
                    FROM workflow_states
                    WHERE state->>'status' = $1
                    ORDER BY updated_at DESC
                    LIMIT $2
                """,
                    status,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT task_id, state
                    FROM workflow_states
                    ORDER BY updated_at DESC
                    LIMIT $1
                """,
                    limit,
                )

            return [
                {"task_id": row["task_id"], **json.loads(row["state"])} for row in rows
            ]

    async def _save_history(
        self, task_id: str, event_type: str, event_data: dict[str, Any]
    ):
        """Save workflow history event"""
        if self.pg_pool:
            async with self.pg_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO workflow_history (task_id, event_type, event_data)
                    VALUES ($1, $2, $3::jsonb)
                """,
                    task_id,
                    event_type,
                    json.dumps(event_data),
                )

    async def get_task_history(self, task_id: str) -> list[dict[str, Any]]:
        """Get task execution history"""
        if not self.pg_pool:
            return []

        async with self.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT event_type, event_data, created_at
                FROM workflow_history
                WHERE task_id = $1
                ORDER BY created_at ASC
            """,
                task_id,
            )

            return [
                {
                    "event_type": row["event_type"],
                    "event_data": json.loads(row["event_data"]),
                    "created_at": row["created_at"].isoformat(),
                }
                for row in rows
            ]

    async def save_analytics(
        self,
        task_type: str,
        complexity: str,
        duration: int,
        success: bool,
        tools_used: list[str],
    ):
        """Save task analytics for reporting"""
        if self.pg_pool:
            async with self.pg_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO task_analytics
                    (task_type, complexity, duration_seconds, success, tools_used)
                    VALUES ($1, $2, $3, $4, $5)
                """,
                    task_type,
                    complexity,
                    duration,
                    success,
                    tools_used,
                )

    async def get_analytics_summary(self) -> dict[str, Any]:
        """Get analytics summary"""
        if not self.pg_pool:
            return {}

        async with self.pg_pool.acquire() as conn:
            # Task type distribution
            type_rows = await conn.fetch(
                """
                SELECT task_type, COUNT(*) as count,
                       AVG(duration_seconds) as avg_duration,
                       SUM(CASE WHEN success THEN 1 ELSE 0 END)::float / COUNT(*) as success_rate
                FROM task_analytics
                GROUP BY task_type
            """
            )

            # Complexity distribution
            complexity_rows = await conn.fetch(
                """
                SELECT complexity, COUNT(*) as count,
                       AVG(duration_seconds) as avg_duration
                FROM task_analytics
                GROUP BY complexity
            """
            )

            # Tool usage
            tool_rows = await conn.fetch(
                """
                SELECT unnest(tools_used) as tool, COUNT(*) as usage_count
                FROM task_analytics
                GROUP BY tool
                ORDER BY usage_count DESC
            """
            )

            return {
                "by_type": [dict(row) for row in type_rows],
                "by_complexity": [dict(row) for row in complexity_rows],
                "tool_usage": [dict(row) for row in tool_rows],
            }
