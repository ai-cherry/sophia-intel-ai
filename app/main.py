import logging

from fastapi import FastAPI

from app.api import advanced_gateway_2025, unified_gateway
from app.deployment import orchestrator
from app.deployments import service_discovery
from app.security.enhanced_middleware import setup_middleware
from app.swarms.communication.message_bus import MessageBus

logger = logging.getLogger(__name__)
app = FastAPI()

# Setup security middleware
setup_middleware(app)

# Register API routers
app.include_router(advanced_gateway_2025.router)
app.include_router(unified_gateway.router)

# Initialize services on startup
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting up AI Orchestrator services")

    # Initialize message bus
    app.state.message_bus = MessageBus()
    try:
        await app.state.message_bus.initialize()
        logger.info("✅ Message bus initialized with Redis connection pool")
    except Exception as e:
        logger.error(f"Failed to initialize message bus: {str(e)}")
        raise

    # Initialize deployment services
    orchestrator.initialize_services()
    service_discovery.init_service_discovery()
    logger.info("✅ Core services initialized")

# Register shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    if hasattr(app.state, 'message_bus'):
        await app.state.message_bus.close()
        logger.info("🔌 Message bus connection closed on shutdown")

# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
