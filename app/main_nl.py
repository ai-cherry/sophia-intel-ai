"""
Main FastAPI application with Natural Language Interface
Phase 2 Week 3-4 Implementation
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import our NL endpoints
from app.api.nl_endpoints import router as nl_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting Sophia Intel AI - Natural Language Interface")
    logger.info("Phase 2 Week 3-4 Implementation")
    
    # Initialize services
    logger.info("Initializing services...")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Natural Language Interface")


# Create FastAPI app
app = FastAPI(
    title="Sophia Intel AI - Natural Language Interface",
    description="Natural Language Processing and Agent Orchestration API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(nl_router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Sophia Intel AI",
        "component": "Natural Language Interface",
        "version": "1.0.0",
        "phase": "Phase 2 Week 3-4",
        "endpoints": {
            "docs": "/docs",
            "openapi": "/openapi.json",
            "nl_process": "/api/nl/process",
            "nl_intents": "/api/nl/intents",
            "system_status": "/api/nl/system/status",
            "agents_list": "/api/nl/agents/list",
            "workflows_trigger": "/api/nl/workflows/trigger"
        }
    }

# Health check
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "natural-language-interface"
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The path {request.url.path} was not found",
            "suggestion": "Check /docs for available endpoints"
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "app.main_nl:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )