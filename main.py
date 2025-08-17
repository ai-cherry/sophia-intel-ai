"""
SOPHIA Intel Production Entry Point
Railway deployment main file
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.application import get_application
from backend.api.enhanced_endpoints import create_enhanced_api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    try:
        # Initialize SOPHIA Intel application
        sophia_app = await get_application()
        app.state.sophia_app = sophia_app
        logger.info("SOPHIA Intel application initialized successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize SOPHIA Intel: {e}")
        raise
    finally:
        # Cleanup
        if hasattr(app.state, 'sophia_app'):
            await app.state.sophia_app.shutdown()
            logger.info("SOPHIA Intel application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="SOPHIA Intel API",
    description="Advanced AI Development Platform with Supreme Infrastructure Authority",
    version="1.0.0",
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


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SOPHIA Intel API - Advanced AI Development Platform",
        "version": "1.0.0",
        "status": "operational",
        "capabilities": [
            "Intelligent Chat Routing",
            "Lambda Labs GH200 Integration",
            "Infrastructure Automation",
            "Multi-Modal Interface",
            "Enterprise Observability"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        if hasattr(app.state, 'sophia_app'):
            health = await app.state.sophia_app.health_check()
            return health
        else:
            return {"status": "initializing", "message": "Application starting up"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


# Include enhanced API router
app.include_router(create_enhanced_api_router(), prefix="/api/v1")


if __name__ == "__main__":
    # Production server configuration
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    logger.info(f"Starting SOPHIA Intel API server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level="info",
        access_log=True,
        reload=False  # Disable reload in production
    )
