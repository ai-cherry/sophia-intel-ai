from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from app.models.requests import EmbeddingRequest, MemoryStoreRequest, MemorySearchRequest, MemoryUpdateRequest, MemoryDeleteRequest
from app.observability.prometheus_metrics import record_cost
from app.memory.unified_memory import UnifiedMemoryStore
from bleach import clean
from app.swarms.communication.message_bus import MessageBus, MessageType, SwarmMessage

router = APIRouter()

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
@router.on_event("startup")
async def startup_event():
    bus = MessageBus()
    await bus.initialize()
    app.state.bus = bus

# Cleanup bus on shutdown
@router.on_event("shutdown")
async def shutdown_event():
    if hasattr(app.state, "bus") and app.state.bus:
        await app.state.bus.close()  # Make sure this exists in your app
