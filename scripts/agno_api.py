"""
FastAPI server for Agno agents.
Provides HTTP API endpoints for agent execution.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from loguru import logger
import asyncio
import uvicorn
from datetime import datetime

from agents.coding_agent import CodingAgent
from config.config import settings
from scripts.agents_hygiene import router as hygiene_router
from scripts.agents_deps import router as deps_router
from scripts.agents_config import router as config_router
from scripts.agents_docs import router as docs_router

# Initialize FastAPI app
app = FastAPI(
    title="Sophia Agno API",
    version="0.1.0",
    description="HTTP API for Sophia AI agents powered by Agno framework"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
coding_agent = CodingAgent()

# Include hygiene agent routers
app.include_router(hygiene_router)
app.include_router(deps_router)
app.include_router(config_router)
app.include_router(docs_router)

# Request/Response Models
class CodingTaskRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    code: str = Field(..., description="Code to analyze/modify")
    query: str = Field(..., description="Task description")
    file_path: Optional[str] = Field(default="", description="Optional file path")
    language: Optional[str] = Field(default="", description="Programming language")

class AgentResponse(BaseModel):
    success: bool
    task_id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    duration: float
    agent: str
    timestamp: str

class AgentStats(BaseModel):
    name: str
    status: str
    concurrency: int
    timeout_seconds: int
    active_tasks: int
    tasks_completed: int
    tasks_failed: int
    tasks_timeout: int
    total_tasks: int
    success_rate: float
    average_duration: float
    total_duration: float

# Health endpoint
@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        coding_health = await coding_agent.health_check()
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "agents": {
                "coding": coding_health
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

# Coding agent endpoint
@app.post("/agent/coding", response_model=AgentResponse)
async def execute_coding_task(request: CodingTaskRequest):
    """Execute a coding task using the coding agent."""
    task_id = f"coding_{int(asyncio.get_event_loop().time() * 1000000)}"
    
    try:
        logger.info(f"Received coding task {task_id} for session {request.session_id}")
        
        result = await coding_agent.execute(task_id, {
            "session_id": request.session_id,
            "code": request.code,
            "query": request.query,
            "file_path": request.file_path,
            "language": request.language
        })
        
        return AgentResponse(
            success=result["success"],
            task_id=task_id,
            result=result.get("result"),
            error=result.get("error"),
            error_type=result.get("error_type"),
            duration=result["duration"],
            agent=result["agent"],
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to execute coding task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Agent statistics endpoint
@app.get("/agent/coding/stats", response_model=AgentStats)
async def get_coding_agent_stats():
    """Get coding agent performance statistics."""
    try:
        stats = coding_agent.get_stats()
        return AgentStats(**stats)
    except Exception as e:
        logger.error(f"Failed to get agent stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# List all agents endpoint
@app.get("/agents")
async def list_agents():
    """List all available agents and their status."""
    try:
        agents = {
            "coding": await coding_agent.health_check()
        }
        return {
            "agents": agents,
            "total_agents": len(agents),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Agent health check endpoint
@app.get("/agent/{agent_name}/health")
async def get_agent_health(agent_name: str):
    """Get health status for a specific agent."""
    try:
        if agent_name == "coding":
            return await coding_agent.health_check()
        else:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task for agent maintenance
async def agent_maintenance():
    """Periodic maintenance tasks for agents."""
    while True:
        try:
            # Log agent statistics
            coding_stats = coding_agent.get_stats()
            logger.info(f"Coding agent stats: {coding_stats}")
            
            # Wait 5 minutes
            await asyncio.sleep(300)
        except Exception as e:
            logger.error(f"Agent maintenance error: {e}")
            await asyncio.sleep(60)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Agno API server")
    
    # Start background maintenance task
    asyncio.create_task(agent_maintenance())
    
    logger.info("Agno API server started successfully")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Agno API server")

# Exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception in {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    logger.info(f"Starting Agno API server on port 7777")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=7777,
        log_level="info",
        reload=settings.ENVIRONMENT == "development"
    )