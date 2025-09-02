from typing import Dict, List, Optional, AsyncIterator, Tuple
import aioredis
import asyncio
import json
import logging
import time
from pydantic import BaseModel
from opentelemetry import trace
from opentelemetry.trace import SpanKind
from uuid import uuid4
from datetime import datetime, timezone

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
    id: str = field(default_factory=lambda: f"msg:{uuid4().hex}")
    sender_agent_id: str
    receiver_agent_id: Optional[str] = None
    message_type: MessageType
    content: Dict[str, Any]
    thread_id: str = field(default_factory=lambda: f"thd:{uuid4().hex}")
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    priority: int = 5  # 1-10, default medium priority
    trace_id: str = field(default_factory=lambda: f"trc:{uuid4().hex}")
    span_id: str = field(default_factory=lambda: f"span:{uuid4().hex}")
    headers: Dict[str, str] = field(default_factory=dict)

class MessageBus:
    """
    Redis-backed, observable message bus for agent communication.
    Implements persistence, replay, and observability as required.
    """
    
    def __init__(self, redis_url: str = None, redis_pool: aioredis.Redis = None):
        self.redis_url = redis_url or "redis://localhost:6379"
        self.redis = None
        self.redis_pool = redis_pool
        self._initialized = False
        self._setup_metrics()
        
    async def initialize(self):
        """Initialize Redis connection"""
        if self._initialized:
            return
        
        if self.redis_pool:
            self.redis = self.redis_pool
        else:
            self.redis = await aioredis.create_redis_pool(
                self.redis_url,
                minsize=5,
                maxsize=20
            )
        
        # Create global namespace
        await self.redis.execute(b'STRUCT', b'CREATE', b'bus', b'type', b'string', b'data')
        
        # Setup Redis streams
        self.streams = {
            'global': b'swarm:global',
            'threads': b'swarm:threads',
            'inbox': b'swarm:inbox'
        }
        
        # Ensure initial stream existence
        await self.redis.xinfo_stream(self.streams['global'])
        await self.redis.xinfo_stream(self.streams['threads'])
        
        self._initialized = True
        logger.info("✅ Message bus initialized successfully with Redis")
    
    async def _get_redis(self):
        if not self._initialized:
            await self.initialize()
        return self.redis
    
    async def publish(self, message: SwarmMessage):
        """Publish a message to the bus with persistence and observability"""
        redis = await self._get_redis()
        spans = await self.record_publish_span(message)
        
        try:
            # Add to global stream
            global_id = await redis.xadd(
                self.streams['global'],
                {
                    'message': json.dumps(message.dict()),
                    'priority': str(message.priority),
                    'type': message.message_type.value
                }
            )
            
            # Add to thread stream
            thread_id = message.thread_id
            await redis.xadd(
                f"{self.streams['threads']}:{thread_id}",
                {
                    'message': json.dumps(message.dict()),
                    'priority': str(message.priority),
                    'type': message.message_type.value
                }
            )
            
            # Add to receiver inbox if specified
            if message.receiver_agent_id:
                await redis.xadd(
                    f"{self.streams['inbox']}:{message.receiver_agent_id}",
                    {
                        'message': json.dumps(message.dict()),
                        'priority': str(message.priority),
                        'type': message.message_type.value
                    }
                )
            
            # Record metrics
            metrics = {
                'message_type': message.message_type.value,
                'priority': message.priority,
                'thread_id': message.thread_id,
                'sender': message.sender_agent_id
            }
            self._record_metrics('bus_messages_total', metrics, 1)
            self._record_metrics('bus_publish_latency_ms', metrics, time.time() - spans['start'])
            
            logger.debug(f"📨 Published message {message.id} to {message.receiver_agent_id if message.receiver_agent_id else 'broadcast'}")
            return global_id
            
        except Exception as e:
            logger.error(f"Message publish failed: {str(e)}")
            self._record_metrics('bus_errors_total', {'error': str(e)}, 1)
            raise
    
    async def subscribe(
        self,
        agent_id: str,
        message_types: Optional[List[MessageType]] = None
    ) -> AsyncIterator[SwarmMessage]:
        """Subscribes to messages for an agent with optional filters"""
        redis = await self._get_redis()
        stream = f"{self.streams['inbox']}:{agent_id}"
        
        # Set up consumer group if not exists
        try:
            await redis.xgroup_create(  # Ensure group exists
                stream,
                f"agent_{agent_id}",
                id='0-0',
                mkstream=True
            )
        except:
            pass  # Group likely already exists
        
        # Start consuming
        last_id = "0-0"
        while True:
            messages = await redis.xread(
                streams={stream: last_id},
                count=1,
                block=5000  # 5 seconds timeout
            )
            
            if not messages:
                continue
                
            stream_name, message_list = messages[0]
            for message_id, message_data in message_list:
                try:
                    # Parse the message
                    msg_data = json.loads(message_data[b'message'].decode())
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
    
    async def get_thread_history(
        self,
        thread_id: str,
        limit: int = 100
    ) -> List[SwarmMessage]:
        """Get message history for a specific thread with ordering"""
        redis = await self._get_redis()
        stream = f"{self.streams['threads']}:{thread_id}"
        
        try:
            messages = await redis.xrevrange(stream, count=limit)
        except:
            return []
        
        messages = [msg for msg in reversed(messages) if msg[1]]
        messages_sorted = sorted(messages, key=lambda x: x[0])
        
        return [
            SwarmMessage(**json.loads(msg[1][b'message'].decode()))
            for msg in messages_sorted
        ]
    
    def _setup_metrics(self):
        """Initialize Prometheus metrics tracking"""
        # In a real implementation, this would connect to Prometheus
        self.metrics = {'bus_messages_total': {}, 'bus_publish_latency_ms': {}}
        
    def _record_metrics(self, metric_name: str, labels: Dict[str, str], value: float):
        """Record metrics for observability"""
        # In a real implementation, this would call a metrics library
        # For now, we log as a placeholder
        logger.debug(f"METRIC: {metric_name} | {labels} | {value}")
    
    async def record_publish_span(self, message: SwarmMessage) -> Dict:
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
                "priority": message.priority
            }
        )
        
        # Add context for distributed tracing
        message.trace_id = span.get_span_context().trace_id
        message.span_id = span.get_span_context().span_id
        
        return {"start": start, "span": span}
    
    async def close(self):
        """Clean up Redis connection"""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()
            self._initialized = False
            logger.info("🔌 Message bus connection closed")

# Example usage
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
            priority=7
        )
        await bus.publish(message)
        
        # Subscribe and get messages
        async for msg in bus.subscribe("agent_2", [MessageType.QUERY]):
            print(f"Received: {msg.content}")
            break
            await bus.close()
    
    asyncio.run(demo())
