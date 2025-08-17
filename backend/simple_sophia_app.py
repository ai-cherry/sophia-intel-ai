"""
Simple SOPHIA Intel Application - Production Ready
Minimal working version for Railway deployment
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple config
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# Create app
app = FastAPI(
    title="SOPHIA Intel",
    description="Advanced AI Orchestrator for Pay Ready",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthResponse(BaseModel):
    status: str
    environment: str
    message: str

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check for Railway"""
    return HealthResponse(
        status="healthy",
        environment=ENVIRONMENT,
        message="SOPHIA Intel is operational"
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SOPHIA Intel - AI Orchestrator",
        "status": "operational",
        "version": "1.0.0"
    }

@app.get("/api/v1/status")
async def status():
    """System status"""
    return {
        "sophia_intel": {
            "status": "operational",
            "capabilities": ["business_intelligence", "rag_systems", "micro_agents"],
            "environment": ENVIRONMENT
        }
    }

if __name__ == "__main__":
    logger.info(f"🚀 Starting SOPHIA Intel on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
