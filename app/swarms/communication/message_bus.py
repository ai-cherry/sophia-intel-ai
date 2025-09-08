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
from opentelemetry import trace
from opentelemetry.trace import SpanKind
from pydantic import BaseModel, Field

from app.core.ai_logger import logger
from app.core.redis_manager import RedisManager

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
    Enhanced with connection pooling, bounded streams, and performance optimizations.
    """

    def __init__(self, redis_manager: Optional[RedisManager] = None):
        self.redis_manager = redis_manager or RedisManager()
        self._initialized = False
        self._setup_metrics()

        # Stream configuration with bounds
        self.streams = {
            "global": "swarm:global",
            "threads": "swarm:threads",
            "inbox": "swarm:inbox",
        }

    async def initialize(self):
        """Initialize Redis connection with enhanced manager"""
        if self._initialized:
            return

        # Initialize the Redis manager
        await self.redis_manager.initialize()

        # Ensure streams exist with bounded configuration
        for _stream_name, stream_key in self.streams.items():
            try:
                # Try to get stream info
                async with self.redis_manager.get_connection() as redis:
                    await redis.xinfo_stream(stream_key)
            except Exception:
                logger.info(f"Creating bounded stream {stream_key}")
                # Create stream with initial dummy entry and bounds
                await self.redis_manager.stream_add(
                    stream_key, {"init": "true", "timestamp": str(time.time())}
                )

        self._initialized = True
        logger.info(
            "📊 Message bus initialized with bounded streams and connection pooling"
        )

    async def _get_redis_manager(self) -> RedisManager:
        """Get Redis manager, ensuring initialization"""
        if not self._initialized:
            await self.initialize()
        return self.redis_manager

    async def publish(self, message: SwarmMessage):
        """Publish a message to the bus with bounded streams and observability"""
        redis_manager = await self._get_redis_manager()
        start_time = time.time()
        await self.record_publish_span(message)

        # Use msgpack for efficient serialization
        try:
            # Build payload for Redis stream
            payload = {
                "message": msgpack.dumps(message.dict()),
                "priority": str(message.priority),
                "type": message.message_type.value,
                "timestamp": str(time.time()),
            }

            # Add to global stream with bounds
            global_id = await redis_manager.stream_add(self.streams["global"], payload)

            # Add to thread stream with bounds
            thread_id = message.thread_id
            thread_stream = f"{self.streams['threads']}:{thread_id}"
            await redis_manager.stream_add(thread_stream, payload)

            # Add to receiver inbox if specified
            if message.receiver_agent_id:
                inbox_stream = f"{self.streams['inbox']}:{message.receiver_agent_id}"
                await redis_manager.stream_add(inbox_stream, payload)

            # Record metrics
            metrics = {
                "message_type": message.message_type.value,
                "priority": message.priority,
                "thread_id": message.thread_id,
                "sender": message.sender_agent_id,
                "receiver": message.receiver_agent_id,
            }
            self._record_metrics("bus_messages_total", metrics, 1)
            self._record_metrics(
                "bus_publish_latency_ms", metrics, time.time() - start_time
            )

            logger.debug(
                f"📨 Published bounded message {message.id} to {message.receiver_agent_id or 'broadcast'}"
            )
            return str(global_id)

        except Exception as e:
            logger.error(f"Message publish failed: {str(e)}")
            self._record_metrics("bus_errors_total", {"error": str(e)}, 1)
            raise

    async def subscribe(
        self, agent_id: str, message_types: Optional[list[MessageType]] = None
    ) -> AsyncIterator[SwarmMessage]:
        """Subscribes to messages for an agent with circuit breaker protection"""
        redis_manager = await self._get_redis_manager()
        stream = f"{self.streams['inbox']}:{agent_id}"
        group = f"agent_{agent_id}"

        # Create consumer group with circuit breaker protection
        await redis_manager.stream_create_group(stream, group)

        # Start consuming with bounded reads
        last_id = ">"
        consumer_name = f"{agent_id}_{int(time.time())}"

        while True:
            try:
                # Use consumer group for reliable delivery
                messages = await redis_manager.stream_read_group(
                    group, consumer_name, {stream: last_id}
                )

                if not messages:
                    await asyncio.sleep(0.1)  # Brief pause if no messages
                    continue

                stream_name, message_list = messages[0]
                message_ids_to_ack = []

                for message_id, message_data in message_list:
                    try:
                        # Parse the message
                        msg_data = msgpack.loads(message_data[b"message"])
                        message = SwarmMessage(**msg_data)

                        # Check filters
                        if message_types and message.message_type not in message_types:
                            message_ids_to_ack.append(message_id)
                            continue

                        # Yield message
                        yield message
                        message_ids_to_ack.append(message_id)

                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Invalid message format: {e}")
                        message_ids_to_ack.append(message_id)  # Ack invalid messages
                    except Exception as e:
                        logger.error(f"Message processing error: {e}")
                        message_ids_to_ack.append(
                            message_id
                        )  # Ack to prevent redelivery

                # Acknowledge processed messages
                if message_ids_to_ack:
                    await redis_manager.stream_ack(stream, group, message_ids_to_ack)

            except Exception as e:
                logger.error(f"Subscription error for agent {agent_id}: {e}")
                await asyncio.sleep(1)  # Back off on error

    async def get_thread_history(
        self, thread_id: str, limit: int = 100
    ) -> list[SwarmMessage]:
        """Get message history for a specific thread with circuit breaker protection"""
        redis_manager = await self._get_redis_manager()
        stream = f"{self.streams['threads']}:{thread_id}"

        try:
            # Use Redis manager for protected access
            async with redis_manager.get_connection() as redis:
                messages = await redis_manager.circuit_breaker.call(
                    redis.xrevrange, stream, count=limit
                )
        except Exception as e:
            logger.warning(f"Failed to get thread history for {thread_id}: {e}")
            return []

        if not messages:
            return []

        # Sort messages chronologically
        sorted_messages = sorted(messages, key=lambda x: int(x[0].split("-")[0]))

        parsed_messages = []
        for _, msg_data in sorted_messages:
            try:
                parsed_messages.append(
                    SwarmMessage(**msgpack.loads(msg_data[b"message"]))
                )
            except Exception as e:
                logger.warning(f"Failed to parse message in thread {thread_id}: {e}")
                continue

        return parsed_messages

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
        """Clean up Redis manager connection"""
        try:
            await self.redis_manager.close()
            self._initialized = False
            logger.info("🔌 Message bus connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")

    async def get_health_status(self) -> dict[str, Any]:
        """Get message bus health status"""
        redis_manager = await self._get_redis_manager()
        health = await redis_manager.health_check()

        # Add message bus specific metrics
        health["message_bus_metrics"] = self.metrics
        health["streams_info"] = {}

        try:
            async with redis_manager.get_connection() as redis:
                for stream_name, stream_key in self.streams.items():
                    try:
                        info = await redis.xinfo_stream(stream_key)
                        health["streams_info"][stream_name] = {
                            "length": info.get("length", 0),
                            "last_generated_id": info.get("last-generated-id", "0-0"),
                        }
                    except Exception:
                        health["streams_info"][stream_name] = {
                            "error": "Stream not found"
                        }
        except Exception as e:
            logger.warning(f"Could not get stream info: {e}")

        return health


# Example usage for testing
if __name__ == "__main__":

    async def demo():
        bus = MessageBus()
        await bus.initialize()

        # Check health status
        health = await bus.get_health_status()
        logger.info(f"Message bus health: {health['healthy']}")

        # Publish a message
        message = SwarmMessage(
            sender_agent_id="agent_1",
            receiver_agent_id="agent_2",
            message_type=MessageType.QUERY,
            content={"question": "What is 2+2?"},
            priority=7,
        )
        await bus.publish(message)

        # Subscribe and get messages (with timeout for demo)
        count = 0
        async for msg in bus.subscribe("agent_2", [MessageType.QUERY]):
            logger.info(f"Received: {msg.content}")
            count += 1
            if count >= 1:  # Exit after first message for demo
                break

        await bus.close()

    asyncio.run(demo())
