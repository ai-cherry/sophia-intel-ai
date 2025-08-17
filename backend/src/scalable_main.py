"""
Scalable SOPHIA Backend with CQRS, WebSockets, and Monitoring
Production-ready FastAPI application for www.sophia-intel.ai
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import redis.asyncio as redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import uvicorn

from orchestrator.scalable_orchestrator import orchestrator
from config.config import settings
from lambda_inference_client import LambdaInferenceClient, create_lambda_client
from lambda_endpoints import router as lambda_router


# Pydantic models
class ChatMessage(BaseModel):
    message: str
    user_id: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    success: bool
    session_id: str
    response: str
    timestamp: str
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    components: Dict[str, str]
    active_sessions: int
    timestamp: str


# FastAPI app
app = FastAPI(
    title="SOPHIA Intel API",
    description="Scalable AI orchestration platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.sophia-intel.ai", "https://sophia-intel.ai", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Lambda Inference API router
app.include_router(lambda_router)

# Global state
redis_client = None
lambda_client = None
active_connections: Dict[str, WebSocket] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global redis_client, lambda_client
    
    try:
        # Initialize Lambda Inference API client
        lambda_client = create_lambda_client()
        logging.info("Lambda Inference API client initialized")
        
        # Initialize Redis for queuing
        redis_client = redis.Redis(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            decode_responses=True
        )
        
        # Test Redis connection
        await redis_client.ping()
        
        logging.info("SOPHIA backend started successfully")
        
    except Exception as e:
        logging.error(f"Startup error: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global redis_client
    
    if redis_client:
        await redis_client.close()
    
    logging.info("SOPHIA backend shutdown complete")


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with component status"""
    try:
        health_data = await orchestrator.health_check()
        return HealthResponse(**health_data)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# CQRS Write Operations (Commands)
@app.post("/api/v2/chat", response_model=ChatResponse)
async def process_chat_message(message: ChatMessage, background_tasks: BackgroundTasks):
    """Process chat message (Write operation)"""
    try:
        # Queue the message for async processing
        task_id = f"chat_{message.user_id}_{datetime.now().timestamp()}"
        
        await redis_client.lpush("chat_queue", json.dumps({
            "task_id": task_id,
            "user_id": message.user_id,
            "message": message.message,
            "session_id": message.session_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        # Process immediately for synchronous response
        result = await orchestrator.process_message(
            user_id=message.user_id,
            message=message.message,
            session_id=message.session_id
        )
        
        # Notify WebSocket clients if connected
        if message.session_id in active_connections:
            await active_connections[message.session_id].send_json({
                "type": "response",
                "data": result
            })
        
        return ChatResponse(
            success=result["success"],
            session_id=result["session_id"],
            response=result.get("response", ""),
            timestamp=result["timestamp"],
            error=result.get("error")
        )
        
    except Exception as e:
        logging.error(f"Chat processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# CQRS Read Operations (Queries)
@app.get("/api/v2/sessions/{session_id}/history")
async def get_session_history(session_id: str, limit: int = 50):
    """Get chat history for session (Read operation)"""
    try:
        # Retrieve from Redis cache or database
        history_key = f"session_history:{session_id}"
        history = await redis_client.lrange(history_key, 0, limit - 1)
        
        return {
            "session_id": session_id,
            "messages": [json.loads(msg) for msg in history],
            "count": len(history)
        }
        
    except Exception as e:
        logging.error(f"History retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v2/users/{user_id}/preferences")
async def get_user_preferences(user_id: str):
    """Get user preferences (Read operation)"""
    try:
        prefs = await redis_client.hgetall(f"user_prefs:{user_id}")
        return prefs if prefs else {"temperature": 0.7, "max_tokens": 2000}
        
    except Exception as e:
        logging.error(f"Preferences retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v2/users/{user_id}/preferences")
async def update_user_preferences(user_id: str, preferences: Dict[str, any]):
    """Update user preferences (Write operation)"""
    try:
        await redis_client.hset(f"user_prefs:{user_id}", mapping=preferences)
        return {"success": True, "message": "Preferences updated"}
        
    except Exception as e:
        logging.error(f"Preferences update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time communication
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    active_connections[session_id] = websocket
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            if data.get("type") == "chat":
                # Process chat message
                result = await orchestrator.process_message(
                    user_id=data.get("user_id"),
                    message=data.get("message"),
                    session_id=session_id
                )
                
                # Send response back
                await websocket.send_json({
                    "type": "response",
                    "data": result
                })
                
                # Store in session history
                history_key = f"session_history:{session_id}"
                await redis_client.lpush(history_key, json.dumps({
                    "role": "user",
                    "content": data.get("message"),
                    "timestamp": datetime.now().isoformat()
                }))
                await redis_client.lpush(history_key, json.dumps({
                    "role": "assistant", 
                    "content": result.get("response", ""),
                    "timestamp": result["timestamp"]
                }))
                
                # Expire history after 24 hours
                await redis_client.expire(history_key, 86400)
            
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        if session_id in active_connections:
            del active_connections[session_id]
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        if session_id in active_connections:
            del active_connections[session_id]


# Background task processor
async def process_chat_queue():
    """Background task to process queued chat messages"""
    while True:
        try:
            # Get message from queue
            message_data = await redis_client.brpop("chat_queue", timeout=1)
            
            if message_data:
                _, message_json = message_data
                message = json.loads(message_json)
                
                # Process with orchestrator
                result = await orchestrator.process_message(
                    user_id=message["user_id"],
                    message=message["message"],
                    session_id=message.get("session_id")
                )
                
                # Store result for later retrieval
                result_key = f"task_result:{message['task_id']}"
                await redis_client.setex(result_key, 3600, json.dumps(result))
                
        except Exception as e:
            logging.error(f"Queue processing error: {e}")
            await asyncio.sleep(1)


# Legacy endpoints for backward compatibility
@app.post("/chat")
async def legacy_chat(message: ChatMessage):
    """Legacy chat endpoint for backward compatibility"""
    return await process_chat_message(message, BackgroundTasks())


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SOPHIA Intel API",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "chat": "/api/v2/chat",
            "websocket": "/ws/{session_id}",
            "docs": "/docs"
        }
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "path": str(request.url)}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": str(exc)}
    )


if __name__ == "__main__":
    # Start background queue processor
    asyncio.create_task(process_chat_queue())
    
    # Run the server
    uvicorn.run(
        "scalable_main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        reload=False,
        access_log=True
    )

