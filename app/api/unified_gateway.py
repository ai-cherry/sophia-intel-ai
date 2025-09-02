from bleach import clean
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.api.openrouter_gateway import OpenRouterGateway
from app.models.requests import (
    ChatRequest,
    EmbeddingRequest,
    MemoryDeleteRequest,
    MemorySearchRequest,
    MemoryStoreRequest,
    MemoryUpdateRequest,
)
from app.observability.prometheus_metrics import record_cost
from app.swarms.communication.message_bus import MessageBus, MessageType

router = APIRouter()
openrouter_gateway = OpenRouterGateway()

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Unified chat endpoint with OpenRouter model routing"""
    if "openrouter" in request.model or any(m in request.model for m in ["openai/gpt-5", "x-ai/", "anthropic/"]):
        response = await openrouter_gateway.chat_completion(
            model=request.model,
            messages=request.messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            presence_penalty=request.presence_penalty,
            frequency_penalty=request.frequency_penalty,
            stop=request.stop
        )
        return {"choices": [{"message": {"content": response.choices[0].message.content}}]}

    # Fallback to default OpenAI client (for non-OpenRouter models)
    # [Add default OpenAI client handling here]
    raise HTTPException(status_code=404, detail="OpenRouter model not found")

@router.post("/embeddings")
async def embeddings(request: EmbeddingRequest):
    sanitized_text = clean(request.text)
    record_cost("embedding", sanitized_text)
    return {"embedding": [0.1, 0.2, 0.3]}

@router.post("/mcp/memory/store")
async def store_memory_endpoint(request: MemoryStoreRequest):
    sanitized_content = clean(request.content)
    store_memory(sanitized_content, request.metadata)
    return {"status": "success"}

@router.post("/mcp/memory/search")
async def search_memory_endpoint(request: MemorySearchRequest):
    sanitized_query = clean(request.query)
    results = search_memory(sanitized_query, request.filters, request.top_k)
    return {"results": results}

@router.post("/mcp/memory/update")
async def update_memory_endpoint(request: MemoryUpdateRequest):
    sanitized_content = clean(request.content)
    update_memory(request.memory_id, sanitized_content, request.metadata)
    return {"status": "success"}

@router.post("/mcp/memory/delete")
async def delete_memory_endpoint(request: MemoryDeleteRequest):
    delete_memory(request.memory_id)
    return {"status": "success"}

@router.get("/health")
async def health_check():
    return {"status": "ok"}

# WebSocket endpoint for real-time message streaming
@router.websocket("/ws/swarm")
async def websocket_swarm_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Parse query parameters
    query_params = websocket.query_params
    thread_id = query_params.get("thread_id", None)
    agent_id = query_params.get("agent_id", None)
    pattern = query_params.get("pattern", None)
    message_type = query_params.get("type", None)

    # Convert types if needed
    if message_type:
        try:
            message_type = MessageType(message_type.upper())
        except:
            message_type = None

    # Initialize message bus (using global instance)
    if "bus" not in websocket.app.state:
        bus = MessageBus()
        await bus.initialize()
        websocket.app.state.bus = bus

    bus = websocket.app.state.bus

    try:
        # Start subscription to the message bus
        async for message in bus.subscribe(
            agent_id or "all",
            [message_type] if message_type else None
        ):
            # Filter messages based on parameters
            if thread_id and message.thread_id != thread_id:
                continue

            # Format message for UI
            msg_data = {
                "id": message.id,
                "sender": message.sender_agent_id,
                "receiver": message.receiver_agent_id,
                "type": message.message_type.value,
                "content": message.content,
                "thread_id": message.thread_id,
                "timestamp": message.timestampisoformat(),
                "priority": message.priority,
                "trace_id": message.trace_id,
                "span_id": message.span_id
            }

            # Send formatted message to UI
            await websocket.send_json(msg_data)

    except WebSocketDisconnect:
        logger.info("Client disconnected from swarm WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        # Send error message before disconnecting
        await websocket.send_json({"error": str(e)})
        await websocket.close()
    finally:
        # Disable the WebSocket subscription
        pass

# Initialize bus for websockets (to be run on startup)
# Note: These handlers should be registered at the app level, not router level
# The app object is not available here, so we'll comment these out
# and handle initialization in the main app file if needed

# @router.on_event("startup")
# async def startup_event():
#     bus = MessageBus()
#     await bus.initialize()
#     app.state.bus = bus

# @router.on_event("shutdown")
# async def shutdown_event():
#     if hasattr(app.state, "bus") and app.state.bus:
#         await app.state.bus.close()
