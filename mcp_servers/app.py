"""
Sophia MCP Server - Main FastAPI Application
Cloud-native MCP server for code, context, memory, research, and business operations.
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import routers
from .code_server import router as code_router
from .context_server import router as context_router
from .memory_server import router as memory_router
from .research_server import router as research_router
from .business_server import router as business_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Sophia MCP Server...")
    
    # Verify required environment variables
    required_env_vars = [
        "NEON_POSTGRES_DSN",
        "QDRANT_URL", 
        "REDIS_URL",
        "MEM0_URL"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
    
    yield
    
    logger.info("Shutting down Sophia MCP Server...")

# Create FastAPI application
app = FastAPI(
    title="Sophia MCP Server",
    description="Cloud-native Model Context Protocol server for Sophia AI orchestrator",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(code_router, prefix="/code", tags=["Code Operations"])
app.include_router(context_router, prefix="/context", tags=["Context Management"])
app.include_router(memory_router, prefix="/memory", tags=["Memory Operations"])
app.include_router(research_router, prefix="/research", tags=["Research Operations"])
app.include_router(business_router, prefix="/business", tags=["Business Intelligence"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Sophia MCP Server",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "code": "/code",
            "context": "/context", 
            "memory": "/memory",
            "research": "/research",
            "business": "/business"
        }
    }

@app.get("/healthz")
async def health_check():
    """Health check endpoint for load balancers."""
    try:
        # Basic health checks
        health_status = {
            "status": "healthy",
            "service": "sophia-mcp-server",
            "version": "1.0.0"
        }
        
        # Check environment variables
        env_checks = {}
        for var in ["NEON_POSTGRES_DSN", "QDRANT_URL", "REDIS_URL", "MEM0_URL"]:
            env_checks[var] = "configured" if os.getenv(var) else "missing"
        
        health_status["environment"] = env_checks
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint."""
    return {
        "service": "sophia-mcp-server",
        "uptime": "operational",
        "endpoints_active": 5,
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=False,  # Set to False for production
        log_level="info"
    )

