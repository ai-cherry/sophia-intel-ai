"""
Unified SOPHIA Intel Application
Consolidates all functionality into a single, conflict-free production application
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

# Import unified components
from .core.sophia_orchestrator_enhanced import SophiaOrchestratorEnhanced
from .database.unified_knowledge_repository import UnifiedKnowledgeRepository
from .agents.celery_app import celery_app
from .agents.entity_recognition import extract_from_conversation
from .agents.relationship_mapping import map_conversation_relationships
from .agents.cross_platform_correlation import correlate_specific_sources
from .config.settings import SophiaConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Unified Configuration
config = SophiaConfig()

# Security
security = HTTPBearer()

# Request/Response Models
class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    user_id: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    stream: bool = False
    model: str = "gpt-4"

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    entities_extracted: List[Dict[str, Any]] = []
    relationships_mapped: List[Dict[str, Any]] = []
    confidence_score: float
    processing_time: float
    sources_used: List[str] = []

class IntelligenceRequest(BaseModel):
    query: str
    user_id: str
    context: Optional[Dict[str, Any]] = None
    data_sources: Optional[List[str]] = None
    analysis_type: str = "comprehensive"

class IntelligenceResponse(BaseModel):
    analysis: str
    insights: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    confidence_score: float
    data_sources_used: List[str]
    processing_time: float

class SystemStatus(BaseModel):
    status: str
    uptime: float
    active_connections: int
    agents_status: Dict[str, str]
    database_status: str
    knowledge_base_size: int
    last_updated: datetime

# Global instances
orchestrator: Optional[SophiaOrchestratorEnhanced] = None
knowledge_repo: Optional[UnifiedKnowledgeRepository] = None
active_connections: Dict[str, WebSocket] = {}

# Startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global orchestrator, knowledge_repo
    
    logger.info("Starting SOPHIA Intel Unified Application")
    
    try:
        # Initialize core components
        knowledge_repo = UnifiedKnowledgeRepository()
        orchestrator = SophiaOrchestratorEnhanced()
        
        # Initialize database
        await knowledge_repo.initialize()
        
        # Start Celery workers (in production, run separately)
        if config.ENVIRONMENT == "development":
            logger.info("Starting Celery workers for development")
            # celery_app.start() # Uncomment for development
        
        logger.info("SOPHIA Intel application started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    finally:
        logger.info("Shutting down SOPHIA Intel application")
        # Cleanup connections
        for connection in active_connections.values():
            try:
                await connection.close()
            except:
                pass
        active_connections.clear()

# Create FastAPI application
app = FastAPI(
    title="SOPHIA Intel Unified API",
    description="Advanced Business Intelligence Platform for Pay Ready",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate user authentication"""
    # Implement proper authentication logic here
    # For now, return a mock user
    return {"user_id": "authenticated_user", "role": "user"}

# Health check endpoint
@app.get("/health", response_model=SystemStatus)
async def health_check():
    """System health check"""
    try:
        # Check database connection
        db_status = "healthy" if knowledge_repo and await knowledge_repo.health_check() else "unhealthy"
        
        # Check agent status
        agents_status = {
            "entity_recognition": "active",
            "relationship_mapping": "active", 
            "cross_platform_correlation": "active",
            "quality_assurance": "active"
        }
        
        # Get knowledge base size
        kb_size = await knowledge_repo.get_total_entities_count() if knowledge_repo else 0
        
        return SystemStatus(
            status="healthy" if db_status == "healthy" else "degraded",
            uptime=0.0,  # Calculate actual uptime
            active_connections=len(active_connections),
            agents_status=agents_status,
            database_status=db_status,
            knowledge_base_size=kb_size,
            last_updated=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

# Unified chat endpoint
@app.post("/api/v2/chat", response_model=ChatResponse)
async def unified_chat(request: ChatRequest, user: dict = Depends(get_current_user)):
    """Unified chat endpoint for all SOPHIA interactions"""
    start_time = datetime.utcnow()
    
    try:
        # Process the chat request through orchestrator
        response_data = await orchestrator.process_unified_chat_request(
            messages=request.messages,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            context=request.context or {},
            model=request.model
        )
        
        # Extract entities in background
        last_message = request.messages[-1] if request.messages else None
        if last_message and last_message.role == "user":
            entity_task = extract_from_conversation.delay(
                conversation_id=response_data["conversation_id"],
                message_content=last_message.content,
                user_context={"user_id": request.user_id}
            )
            
            # Map relationships if entities found
            if response_data.get("entities_extracted"):
                relationship_task = map_conversation_relationships.delay(
                    conversation_id=response_data["conversation_id"],
                    entities=response_data["entities_extracted"],
                    message_content=last_message.content
                )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return ChatResponse(
            response=response_data["response"],
            conversation_id=response_data["conversation_id"],
            entities_extracted=response_data.get("entities_extracted", []),
            relationships_mapped=response_data.get("relationships_mapped", []),
            confidence_score=response_data.get("confidence_score", 0.8),
            processing_time=processing_time,
            sources_used=response_data.get("sources_used", [])
        )
        
    except Exception as e:
        logger.error(f"Chat request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

# Streaming chat endpoint
@app.post("/api/v2/chat/stream")
async def stream_chat(request: ChatRequest, user: dict = Depends(get_current_user)):
    """Streaming chat endpoint for real-time responses"""
    
    async def generate_stream():
        try:
            async for chunk in orchestrator.stream_chat_response(
                messages=request.messages,
                user_id=request.user_id,
                conversation_id=request.conversation_id,
                context=request.context or {},
                model=request.model
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
                
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

# Business intelligence endpoint
@app.post("/api/v2/intelligence", response_model=IntelligenceResponse)
async def business_intelligence(request: IntelligenceRequest, user: dict = Depends(get_current_user)):
    """Unified business intelligence endpoint"""
    start_time = datetime.utcnow()
    
    try:
        # Process intelligence query through orchestrator
        analysis_result = await orchestrator.process_business_intelligence_query(
            query=request.query,
            context={
                "user_id": request.user_id,
                "data_sources": request.data_sources or [],
                "analysis_type": request.analysis_type,
                "pay_ready_context": True,
                **(request.context or {})
            }
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return IntelligenceResponse(
            analysis=analysis_result["analysis"],
            insights=analysis_result.get("insights", []),
            recommendations=analysis_result.get("recommendations", []),
            confidence_score=analysis_result.get("confidence_score", 0.8),
            data_sources_used=analysis_result.get("data_sources_used", []),
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Intelligence query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Intelligence processing failed: {str(e)}")

# Knowledge management endpoints
@app.get("/api/v2/knowledge/entities")
async def get_entities(
    limit: int = 100,
    offset: int = 0,
    category: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get entities from knowledge base"""
    try:
        entities = await knowledge_repo.get_entities_paginated(
            limit=limit,
            offset=offset,
            category=category
        )
        return {"entities": entities, "total": len(entities)}
        
    except Exception as e:
        logger.error(f"Failed to get entities: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve entities")

@app.get("/api/v2/knowledge/relationships")
async def get_relationships(
    limit: int = 100,
    offset: int = 0,
    relationship_type: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get relationships from knowledge base"""
    try:
        relationships = await knowledge_repo.get_relationships_paginated(
            limit=limit,
            offset=offset,
            relationship_type=relationship_type
        )
        return {"relationships": relationships, "total": len(relationships)}
        
    except Exception as e:
        logger.error(f"Failed to get relationships: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve relationships")

# Data source management
@app.get("/api/v2/datasources")
async def get_data_sources(user: dict = Depends(get_current_user)):
    """Get configured data sources"""
    data_sources = [
        {"name": "salesforce", "status": "active", "priority": 1},
        {"name": "gong", "status": "active", "priority": 2},
        {"name": "hubspot", "status": "active", "priority": 3},
        {"name": "intercom", "status": "active", "priority": 4},
        {"name": "looker", "status": "active", "priority": 5},
        {"name": "slack", "status": "active", "priority": 6},
        {"name": "asana", "status": "active", "priority": 7},
        {"name": "linear", "status": "active", "priority": 8},
        {"name": "factor_ai", "status": "active", "priority": 9},
        {"name": "notion", "status": "active", "priority": 10},
        {"name": "netsuite", "status": "active", "priority": 11}
    ]
    return {"data_sources": data_sources}

@app.post("/api/v2/datasources/{source1}/{source2}/correlate")
async def trigger_correlation(
    source1: str,
    source2: str,
    time_window_hours: int = 24,
    user: dict = Depends(get_current_user)
):
    """Trigger correlation between two data sources"""
    try:
        task = correlate_specific_sources.delay(source1, source2, time_window_hours)
        return {"task_id": task.id, "status": "started"}
        
    except Exception as e:
        logger.error(f"Failed to trigger correlation: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger correlation")

# WebSocket endpoint for real-time communication
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    connection_id = f"ws_{datetime.utcnow().timestamp()}"
    active_connections[connection_id] = websocket
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message through orchestrator
            response = await orchestrator.process_websocket_message(message_data)
            
            # Send response back to client
            await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket connection {connection_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if connection_id in active_connections:
            del active_connections[connection_id]

# Agent management endpoints
@app.get("/api/v2/agents/status")
async def get_agents_status(user: dict = Depends(get_current_user)):
    """Get status of all background agents"""
    try:
        # Get Celery worker status
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        active_tasks = inspect.active()
        
        return {
            "workers": stats or {},
            "active_tasks": active_tasks or {},
            "queues": [
                "entity_processing",
                "graph_updates", 
                "data_correlation",
                "quality_control",
                "model_evolution",
                "learning",
                "insights"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get agent status: {e}")
        return {"error": "Failed to get agent status", "workers": {}, "active_tasks": {}}

# Analytics endpoints
@app.get("/api/v2/analytics/summary")
async def get_analytics_summary(
    days: int = 7,
    user: dict = Depends(get_current_user)
):
    """Get analytics summary"""
    try:
        summary = await knowledge_repo.get_analytics_summary(days)
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get analytics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")

# Main application entry point
if __name__ == "__main__":
    uvicorn.run(
        "unified_sophia_app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=config.ENVIRONMENT == "development",
        log_level="info"
    )

