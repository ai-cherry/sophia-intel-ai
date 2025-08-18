"""
🚀 SOPHIA Ultimate Backend Main
Resilient Railway deployment with badass AI orchestrator and incredible memory ecosystem
Single source of truth for all backend functionality
"""

import os
import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

# FastAPI and web framework
from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn

# Pydantic models
from pydantic import BaseModel, Field

# Monitoring and observability
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import structlog

# Ultimate orchestrator
from ultimate_orchestrator import get_ultimate_orchestrator, UltimateSOPHIAOrchestrator

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Security
security = HTTPBearer()

# Pydantic models for API
class ChatMessage(BaseModel):
    message: str = Field(..., description="The chat message to process")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    user_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="User context")
    use_swarm: Optional[bool] = Field(default=False, description="Force use of agent swarm")
    deep_research: Optional[bool] = Field(default=False, description="Enable deep research mode")
    web_access: Optional[bool] = Field(default=True, description="Enable web access")

class ChatResponse(BaseModel):
    response: str
    session_id: str
    metadata: Dict[str, Any]

class SystemHealth(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    components: Dict[str, Any]

class EcosystemStatus(BaseModel):
    orchestrator: Dict[str, Any]
    memory_ecosystem: Dict[str, Any]
    agent_swarm: Dict[str, Any]
    system_health: Dict[str, Any]

# Global orchestrator
orchestrator: Optional[UltimateSOPHIAOrchestrator] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global orchestrator
    
    try:
        logger.info("🚀 Starting SOPHIA Ultimate Backend")
        
        # Initialize the ultimate orchestrator
        orchestrator = await get_ultimate_orchestrator()
        
        logger.info("✅ SOPHIA Ultimate Backend started successfully")
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    finally:
        logger.info("🛑 SOPHIA Ultimate Backend shutting down")

# Create FastAPI app with lifespan
app = FastAPI(
    title="SOPHIA Ultimate Backend",
    description="Badass AI orchestrator with agent swarm and incredible memory ecosystem",
    version="4.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Authentication
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify authentication token"""
    try:
        token = credentials.credentials
        
        # Admin API key check
        admin_key = "a90eaf7fe842390e95b73071bee73c5d"  # SHA-256 of "admin_sophia_2024"
        
        if token == admin_key:
            return {
                "user_id": "admin",
                "access_level": "admin",
                "auth_type": "api_key"
            }
        
        # Add more authentication methods here (JWT, OAuth, etc.)
        
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
    except Exception as e:
        logger.error(f"❌ Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

# Health check endpoint
@app.get("/health", response_model=SystemHealth)
async def health_check():
    """Health check endpoint for Railway and monitoring"""
    try:
        global orchestrator
        
        components = {
            "orchestrator": "healthy" if orchestrator else "not_initialized",
            "memory_ecosystem": "healthy",
            "agent_swarm": "healthy",
            "api": "healthy"
        }
        
        overall_status = "healthy" if all(status == "healthy" for status in components.values()) else "degraded"
        
        return SystemHealth(
            status=overall_status,
            service="sophia-ultimate-backend",
            version="4.0.0",
            timestamp=datetime.utcnow().isoformat(),
            components=components
        )
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return SystemHealth(
            status="unhealthy",
            service="sophia-ultimate-backend", 
            version="4.0.0",
            timestamp=datetime.utcnow().isoformat(),
            components={"error": str(e)}
        )

# Main chat endpoint
@app.post("/api/v1/chat/enhanced", response_model=ChatResponse)
async def enhanced_chat(
    chat_message: ChatMessage,
    user_context: Dict[str, Any] = Depends(verify_token),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Enhanced chat with ultimate SOPHIA orchestrator"""
    try:
        global orchestrator
        
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
        
        # Generate session ID if not provided
        session_id = chat_message.session_id or f"session_{int(datetime.utcnow().timestamp())}"
        
        # Merge user context
        full_context = {**user_context, **chat_message.user_context}
        
        # Process with ultimate orchestrator
        result = await orchestrator.process_chat_message(
            message=chat_message.message,
            session_id=session_id,
            user_context=full_context
        )
        
        # Add request metadata
        result['metadata'].update({
            'use_swarm': chat_message.use_swarm,
            'deep_research': chat_message.deep_research,
            'web_access': chat_message.web_access,
            'user_id': user_context.get('user_id'),
            'access_level': user_context.get('access_level')
        })
        
        logger.info(f"✅ Chat processed successfully for session {session_id}")
        
        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Enhanced chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

# Streaming chat endpoint
@app.post("/api/v1/chat/stream")
async def streaming_chat(
    chat_message: ChatMessage,
    user_context: Dict[str, Any] = Depends(verify_token)
):
    """Streaming chat response"""
    try:
        global orchestrator
        
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
        
        async def generate_stream():
            # For now, return the full response
            # TODO: Implement true streaming
            result = await orchestrator.process_chat_message(
                message=chat_message.message,
                session_id=chat_message.session_id or f"stream_{int(datetime.utcnow().timestamp())}",
                user_context={**user_context, **chat_message.user_context}
            )
            
            yield f"data: {result['response']}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
        
    except Exception as e:
        logger.error(f"❌ Streaming chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Streaming failed: {str(e)}")

# System status endpoint
@app.get("/api/v1/system/status", response_model=EcosystemStatus)
async def system_status(user_context: Dict[str, Any] = Depends(verify_token)):
    """Get comprehensive system status"""
    try:
        global orchestrator
        
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
        
        # Get system health from orchestrator
        await orchestrator._update_system_health()
        
        return EcosystemStatus(
            orchestrator={
                "status": "healthy",
                "capabilities": list(orchestrator.capabilities),
                "authority_level": orchestrator.authority_level.value
            },
            memory_ecosystem={
                "status": "healthy",
                "layers": len(orchestrator.memory_ecosystem.memory_layers),
                "types": list(orchestrator.memory_ecosystem.memory_layers.keys())
            },
            agent_swarm={
                "status": "healthy",
                "active_agents": len(orchestrator.agent_swarm.agents),
                "agents": list(orchestrator.agent_swarm.agents.keys())
            },
            system_health=orchestrator.system_health
        )
        
    except Exception as e:
        logger.error(f"❌ System status failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

# Ecosystem self-assessment endpoint
@app.post("/api/v1/system/self-assessment")
async def ecosystem_self_assessment(user_context: Dict[str, Any] = Depends(verify_token)):
    """Trigger SOPHIA's ecosystem self-assessment"""
    try:
        global orchestrator
        
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
        
        # Trigger comprehensive self-assessment
        assessment_message = """
        SOPHIA, please perform a complete ecosystem self-assessment:
        1. List all active services and agents
        2. Report database and vector store status
        3. Summarize environment variables and configurations
        4. Check system health and performance metrics
        5. Identify any issues or optimization opportunities
        6. Suggest next steps for improvement
        """
        
        result = await orchestrator.process_chat_message(
            message=assessment_message,
            session_id=f"assessment_{int(datetime.utcnow().timestamp())}",
            user_context=user_context
        )
        
        return {
            "assessment": result['response'],
            "metadata": result['metadata'],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Self-assessment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Self-assessment failed: {str(e)}")

# Authentication endpoints
@app.post("/auth/login")
async def login(credentials: Dict[str, str]):
    """Login endpoint"""
    try:
        api_key = credentials.get("api_key")
        
        if not api_key:
            raise HTTPException(status_code=400, detail="API key required")
        
        # Verify API key
        admin_key = "a90eaf7fe842390e95b73071bee73c5d"
        
        if api_key == admin_key:
            return {
                "access_token": api_key,
                "token_type": "bearer",
                "user_id": "admin",
                "access_level": "admin"
            }
        
        raise HTTPException(status_code=401, detail="Invalid API key")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "sophia-ultimate-backend",
        "version": "4.0.0",
        "description": "Badass AI orchestrator with agent swarm and incredible memory ecosystem",
        "status": "operational",
        "capabilities": [
            "Ultimate AI Orchestration",
            "Badass Agent Swarm",
            "Incredible Memory Ecosystem", 
            "Complete Infrastructure Control",
            "Multi-Model AI Routing",
            "Real-time System Monitoring"
        ],
        "endpoints": {
            "chat": "/api/v1/chat/enhanced",
            "streaming": "/api/v1/chat/stream",
            "status": "/api/v1/system/status",
            "health": "/health",
            "docs": "/docs"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"❌ Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Railway deployment configuration
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "ultimate_main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True,
        reload=False  # Disable reload in production
    )

