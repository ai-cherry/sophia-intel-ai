"""
Main application entry point for the Sophia Intelligence AI Platform.

This module initializes the FastAPI application with dual orchestrators:
- Artemis: Handles coding workflows and technical operations
- Sophia: Manages business logic and intelligence operations

The application provides unified API gateways and enhanced security middleware
for enterprise-grade AI orchestration.
"""

import logging
from typing import Any

from fastapi import FastAPI

from app.api import unified_gateway
from app.security.enhanced_middleware import setup_error_handling
from app.swarms.communication.message_bus import MessageBus

logger = logging.getLogger(__name__)
app = FastAPI(
    title="Sophia Intelligence AI Platform",
    description="Dual orchestrator system for AI-powered business intelligence and coding workflows",
    version="1.0.0"
)

# Setup error handling middleware
setup_error_handling(app)

# Register API routers
app.include_router(unified_gateway.router)

# Initialize services on startup
@app.on_event("startup")
async def startup_event() -> None:
    """
    Initialize core services during application startup.
    
    Sets up the message bus with Redis connection pool for inter-service communication.
    """
    logger.info("🚀 Starting up AI Orchestrator services")

    # Initialize message bus for inter-service communication
    app.state.message_bus = MessageBus()
    try:
        await app.state.message_bus.initialize()
        logger.info("✅ Message bus initialized with Redis connection pool")
    except Exception as e:
        logger.error(f"Failed to initialize message bus: {str(e)}")
        raise

    logger.info("✅ Core services initialized")

# Register shutdown event
@app.on_event("shutdown")
async def shutdown_event() -> None:
    """
    Clean up resources during application shutdown.
    
    Closes the message bus connection and performs graceful cleanup.
    """
    if hasattr(app.state, 'message_bus'):
        await app.state.message_bus.close()
        logger.info("🔌 Message bus connection closed on shutdown")

# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
