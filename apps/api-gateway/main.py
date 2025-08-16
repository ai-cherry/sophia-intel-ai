"""SOPHIA Intel API Gateway - Single Front Door"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import health, orchestration, speech
from core.env_schema import validate_environment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Validate environment on startup
config = validate_environment()
logger.info(f"Starting SOPHIA Intel API Gateway in {config.env} mode")

app = FastAPI(
    title="SOPHIA Intel API Gateway",
    description="Single front door for orchestration, voice, and health",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(orchestration.router)
app.include_router(speech.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.debug
    )
