"""
Sophia MCP Server - Main FastAPI Application
Cloud-native MCP server for code, context, memory, research, and business operations.
Supports service routing via --service argument or MCP_ROLE environment variable.
"""

import os
import sys
import logging
import argparse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import routers
from .code_server import app as code_app
from .context_server import router as context_router
from .memory_server import router as memory_router
from .research_router import router as research_router
from .business_server import router as business_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    service_name = getattr(app.state, 'service_name', 'unknown')
    logger.info(f"Starting Sophia MCP Server ({service_name})...")
    
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
    
    logger.info(f"Shutting down Sophia MCP Server ({service_name})...")

def create_app(service: str = None) -> FastAPI:
    """Create FastAPI application for specific service."""
    
    # Determine service from argument, environment, or default to all
    if not service:
        service = os.getenv("MCP_ROLE", "all")
    
    # Create FastAPI application
    app = FastAPI(
        title=f"Sophia MCP Server ({service})",
        description=f"Cloud-native Model Context Protocol server - {service} service",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Store service name in app state
    app.state.service_name = service

    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers based on service
    if service == "all":
        # Include all routers for development/testing
        app.mount("/code", code_app)
        app.include_router(context_router, prefix="/context", tags=["Context Management"])
        app.include_router(memory_router, prefix="/memory", tags=["Memory Operations"])
        app.include_router(research_router, prefix="/research", tags=["Research Operations"])
        app.include_router(business_router, prefix="/business", tags=["Business Intelligence"])
        
        # Include feedback router
        from .feedback_server import router as feedback_router
        app.include_router(feedback_router, prefix="/feedback", tags=["Feedback Management"])
        
    elif service == "code":
        # Mount the code app directly since it's a FastAPI app, not a router
        return code_app
    elif service == "context":
        app.include_router(context_router, prefix="", tags=["Context Management"])
    elif service == "memory":
        app.include_router(memory_router, prefix="", tags=["Memory Operations"])
    elif service == "research":
        app.include_router(research_router, prefix="", tags=["Research Operations"])
    elif service == "business":
        app.include_router(business_router, prefix="", tags=["Business Intelligence"])
    elif service == "feedback":
        from .feedback_server import router as feedback_router
        app.include_router(feedback_router, prefix="", tags=["Feedback Management"])
    else:
        logger.error(f"Unknown service: {service}")
        raise ValueError(f"Unknown service: {service}")

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "service": f"Sophia MCP Server ({service})",
            "version": "1.0.0",
            "status": "operational",
            "service_type": service
        }

    @app.get("/healthz")
    async def health_check():
        """Health check endpoint for load balancers."""
        try:
            # Basic health checks
            health_status = {
                "status": "healthy",
                "service": f"sophia-mcp-{service}",
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

    @app.get("/readyz")
    async def readiness_check():
        """Readiness check endpoint."""
        return {"status": "ready", "service": f"sophia-mcp-{service}"}

    @app.get("/metrics")
    async def metrics():
        """Basic metrics endpoint."""
        return {
            "service": f"sophia-mcp-{service}",
            "uptime": "operational",
            "version": "1.0.0"
        }
    
    return app

# Create default app (for backwards compatibility)
app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Sophia MCP Server")
    parser.add_argument("--service", choices=["code", "context", "memory", "research", "business", "feedback", "all"], 
                       default="all", help="Service to run")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    
    args = parser.parse_args()
    
    # Create app for specific service
    service_app = create_app(args.service)
    
    # Run the server
    uvicorn.run(service_app, host=args.host, port=args.port)

