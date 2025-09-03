import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket
from opentelemetry import trace

from app.swarms.communication.message_bus import MessageBus, MessageType

logger = logging.getLogger(__name__)

router = APIRouter()

# Message bus will be injected by the main app
message_bus = None

async def get_message_bus() -> MessageBus:
    """Get the global message bus instance"""
    if not message_bus:
        raise HTTPException(status_code=500, detail="Message bus not initialized")
    return message_bus

@router.websocket("/bus")
async def websocket_bus_endpoint(
    websocket: WebSocket,
    agent_id: str,
    thread_id: Optional[str] = None
):
    """
    WebSocket endpoint streaming messages from message bus.
    Query parameters:
    - agent_id: target agent for inbox messages
    - thread_id: optional filter for thread-specific messages
    """
    await websocket.accept()

    # Get message bus instance
    bus = await get_message_bus()

    # Create a list of message types to filter
    message_types = [MessageType.QUERY, MessageType.PROPOSAL, MessageType.RESULT, MessageType.VOTE]

    # Create a span for this WebSocket connection
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("websocket_bus_connection") as span:
        span.set_attribute("agent_id", agent_id)
        span.set_attribute("thread_id", thread_id)

        try:
            logger.info(f"Agent {agent_id} connected to bus. Thread: {thread_id}")

            # Subscribe to agent's inbox and specific thread (if provided)
            async for message in bus.subscribe(agent_id, message_types):
                if thread_id and message.thread_id != thread_id:
                    continue

                # Format message as JSON for WebSocket transmission
                msg_data = {
                    "id": message.id,
                    "type": message.message_type.value,
                    "content": message.content,
                    "thread_id": message.thread_id,
                    "timestamp": message.timestamp.isoformat(),
                    "sender": message.sender_agent_id
                }

                # Send message over WebSocket
                await websocket.send_text(json.dumps(msg_data))

        except Exception as e:
            logger.error(f"WebSocket error for agent {agent_id}: {str(e)}")
            await websocket.close(code=1001)
        finally:
            logger.info(f"Agent {agent_id} disconnected from bus")
