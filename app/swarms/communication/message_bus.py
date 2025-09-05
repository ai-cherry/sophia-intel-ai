import asyncio
import enum
import json
import logging
import time
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

import msgpack
import redis.asyncio as aioredis
from opentelemetry import trace
from opentelemetry.trace import SpanKind
from pydantic import BaseModel, Field

from app.core.ai_logger import logger

logger = logging.getLogger(__name__)


class MessageType(str, enum.Enum):
    """Standardized message types for swarm communication"""

    QUERY = "query"
    RESPONSE = "response"
    PROPOSAL = "proposal"
    VOTE = "vote"
    RESULT = "result"
    EVENT = "event"
    ERROR = "error"


class SwarmMessage(BaseModel):
    """Structured message for agent communication"""

    id: str = Field(default_factory=lambda: f"msg:{uuid4().hex}")
    sender_agent_id: str
    receiver_agent_id: Optional[str] = None
    message_type: MessageType
    content: dict[str, Any]
    thread_id: str = Field(default_factory=lambda: f"thd:{uuid4().hex}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    priority: int = 5  # 1-10, default medium priority
    trace_id: str = Field(default_factory=lambda: f"trc:{uuid4().hex}")
    span_id: str = Field(default_factory=lambda: f"span:{uuid4().hex}")
    headers: dict[str, str] = Field(default_factory=dict)


class MessageBus:
    """
    Redis-backed, observable message bus for agent communication.
    Implements persistence, replay, and observability as required.
    Enhanced with connection pooling and performance optimizations.
    """

    def __init__(self, redis_pool: aioredis.Redis = None, redis_url: str = None):
        self.redis = redis_pool
        self.redis_url = redis_url or "redis://localhost:6379"
        self._initialized = False
        self._setup_metrics()
        self.connection_closed = False

    async def initialize(self):
        """Initialize Redis connection pool"""
        if self._initialized:
            return

        if not self.redis:
            try:
                # Use the current redis-py async API
                self.redis = await aioredis.from_url(
                    self.redis_url, max_connections=20, decode_responses=False
                )
                logger.info("✅ Successfully connected to Redis with connection pool")
            except Exception as e:
                logger.error(f"Failed to initialize Redis connection pool: {str(e)}")
                raise

        # Create global namespace (skip custom STRUCT command as it's not standard Redis)
        # This was likely for a Redis module that may not be installed

        # Setup Redis streams
        self.streams = {
            "global": b"swarm:global",
            "threads": b"swarm:threads",
            "inbox": b"swarm:inbox",
        }

        # Ensure initial stream existence
        for stream in self.streams.values():
            try:
                await self.redis.xinfo_stream(stream)
            except Exception as e:
                logger.warning(f"Stream {stream} may not exist: {e}")
                # Create stream by adding a dummy entry
                try:
                    await self.redis.xadd(stream, {"init": "true"})
                except Exception as create_error:
                    logger.warning(f"Could not create stream {stream}: {create_error}")

        self._initialized = True
        logger.info("📊 Message bus fully initialized with connection pooling")

    async def _get_redis(self) -> aioredis.Redis:
        """Get Redis connection, ensuring initialization"""
        if not self._initialized:
            await self.initialize()
        if self.connection_closed:
            logger.error("Redis connection closed during operation.")
            raise RuntimeError("Redis connection closed")
        return self.redis

    async def publish(self, message: SwarmMessage):
        """Publish a message to the bus with persistence and observability"""
        redis = await self._get_redis()
        start_time = time.time()
        await self.record_publish_span(message)

        # Use msgpack for efficient serialization
        try:
            # Build payload for Redis stream
            payload = {
                "message": msgpack.dumps(message.dict()),
                "priority": str(message.priority),
                "type": message.message_type.value,
            }

            # Add to global stream
            global_id = await redis.xadd(self.streams["global"], payload, id="*")

            # Add to thread stream
            thread_id = message.thread_id
            await redis.xadd(f"{self.streams['threads']}:{thread_id}", payload, id="*")

            # Add to receiver inbox if specified
            if message.receiver_agent_id:
                await redis.xadd(
                    f"{self.streams['inbox']}:{message.receiver_agent_id}", payload, id="*"
                )

            # Record metrics
            metrics = {
                "message_type": message.message_type.value,
                "priority": message.priority,
                "thread_id": message.thread_id,
                "sender": message.sender_agent_id,
                "receiver": message.receiver_agent_id,
            }
            self._record_metrics("bus_messages_total", metrics, 1)
            self._record_metrics("bus_publish_latency_ms", metrics, time.time() - start_time)

            logger.debug(
                f"📨 Published message {message.id} to {message.receiver_agent_id or 'broadcast'}"
            )
            return str(global_id)

        except Exception as e:
            logger.error(f"Message publish failed: {str(e)}")
            self._record_metrics("bus_errors_total", {"error": str(e)}, 1)
            raise

    async def subscribe(
        self, agent_id: str, message_types: Optional[list[MessageType]] = None
    ) -> AsyncIterator[SwarmMessage]:
        """Subscribes to messages for an agent with optional filters"""
        redis = await self._get_redis()
        stream = f"{self.streams['inbox']}:{agent_id}"

        # Ensure consumer group exists
        try:
            await redis.xgroup_create(stream, f"agent_{agent_id}", id="0-0", mkstream=True)
        except aioredis.error.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                logger.warning(f"Failed to create group {stream}: {e}")

        # Start consuming
        last_id = "0-0"
        while True:
            # Provide 5s blocking timeout to prevent starvation
            messages = await redis.xread(streams={stream: last_id}, count=1, block=5000)

            if not messages:
                continue

            stream_name, message_list = messages[0]
            for message_id, message_data in message_list:
                try:
                    # Parse the message
                    msg_data = msgpack.loads(message_data[b"message"])
                    message = SwarmMessage(**msg_data)

                    # Check filters
                    if message_types and message.message_type not in message_types:
                        last_id = message_id
                        continue

                    # Process message
                    yield message
                    last_id = message_id

                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Invalid message format: {e}")
                except Exception as e:
                    logger.error(f"Message processing error: {e}")

    async def get_thread_history(self, thread_id: str, limit: int = 100) -> list[SwarmMessage]:
        """Get message history for a specific thread with ordering"""
        redis = await self._get_redis()
        stream = f"{self.streams['threads']}:{thread_id}"

        try:
            # Get messages in reverse order (newest first), then reverse for chronological
            messages = await redis.xrevrange(stream, count=limit)
        except:
            return []

        # Sort messages chronologically
        sorted_messages = sorted(messages, key=lambda x: int(x[0].split("-")[0]))

        return [SwarmMessage(**msgpack.loads(msg[1][b"message"])) for _, msg in sorted_messages]

    def _setup_metrics(self):
        """Initialize Prometheus metrics tracking"""
        self.metrics = {
            "bus_messages_total": {},
            "bus_publish_latency_ms": {},
            "bus_errors_total": {},
        }

    def _record_metrics(self, metric_name: str, labels: dict[str, str], value: float):
        """Record metrics for observability"""
        # In production, this would interface with a metrics library
        logger.debug(f"METRIC: {metric_name} | {labels} | {value}")

    async def record_publish_span(self, message: SwarmMessage) -> dict:
        """Record OpenTelemetry span for message publishing"""
        tracer = trace.get_tracer(__name__)
        start = time.time()
        span = tracer.start_span(
            "message.publish",
            kind=SpanKind.PRODUCER,
            attributes={
                "message.id": message.id,
                "message.type": message.message_type.value,
                "sender": message.sender_agent_id,
                "receiver": message.receiver_agent_id,
                "priority": message.priority,
            },
        )

        # Add context for distributed tracing
        message.trace_id = span.get_span_context().trace_id
        message.span_id = span.get_span_context().span_id

        return {"start": start, "span": span}

    async def close(self):
        """Clean up Redis connection"""
        if self.redis and not self.connection_closed:
            try:
                self.redis.close()
                await self.redis.wait_closed()
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
            finally:
                self.connection_closed = True
                self._initialized = False
                logger.info("🔌 Message bus connection closed successfully")


# Example usage for testing
if __name__ == "__main__":

    async def demo():
        bus = MessageBus()
        await bus.initialize()

        # Publish a message
        message = SwarmMessage(
            sender_agent_id="agent_1",
            receiver_agent_id="agent_2",
            message_type=MessageType.QUERY,
            content={"question": "What is 2+2?"},
            priority=7,
        )
        await bus.publish(message)

        # Subscribe and get messages
        async for msg in bus.subscribe("agent_2", [MessageType.QUERY]):
            logger.info(f"Received: {msg.content}")
            await bus.close()
            break

    asyncio.run(demo())
