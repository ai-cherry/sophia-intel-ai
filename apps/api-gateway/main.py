"""SOPHIA Intel API Gateway - Single Front Door"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.env_schema import validate_environment

# Validate environment on startup
config = validate_environment()

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

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "service": "sophia-api-gateway",
        "status": "healthy",
        "version": "1.0.0",
        "environment": config.env
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.debug
    )
