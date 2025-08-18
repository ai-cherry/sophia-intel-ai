#!/usr/bin/env python3
"""
Simple test application for SOPHIA Intel autonomy testing
"""
import os
import json
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SOPHIA Intel Test API",
    description="Test API for SOPHIA autonomy verification",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SOPHIA Intel Test API",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "secrets_configured": len([k for k in os.environ.keys() if k.endswith("_API_KEY") or k.endswith("_TOKEN")])
    }

@app.get("/api/v1/dashboard/status")
async def dashboard_status():
    """Dashboard status endpoint"""
    return {
        "status": "operational",
        "services": {
            "api": "running",
            "database": "connected" if os.getenv("NEON_DATABASE_URL") else "not configured",
            "redis": "connected" if os.getenv("REDIS_URL") else "not configured",
            "qdrant": "connected" if os.getenv("QDRANT_URL") else "not configured"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/chat/persona")
async def chat_persona(data: dict):
    """Chat with persona endpoint"""
    query = data.get("query", "")
    persona = data.get("persona", "developer")
    
    logger.info(f"Chat request: {query} (persona: {persona})")
    
    return {
        "response": f"SOPHIA Intel ({persona} persona) received: {query}",
        "persona": persona,
        "timestamp": datetime.now().isoformat(),
        "status": "autonomy_test_ready"
    }

@app.post("/api/v1/research/scrape")
async def research_scrape(data: dict):
    """Research scraping endpoint"""
    url = data.get("url", "")
    
    logger.info(f"Research scrape request: {url}")
    
    return {
        "url": url,
        "status": "scraped",
        "data": f"Mock research data from {url}",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/code/modify")
async def code_modify(data: dict):
    """Code modification endpoint"""
    query = data.get("query", "")
    repo = data.get("repo", "")
    
    logger.info(f"Code modification request: {query} for {repo}")
    
    return {
        "query": query,
        "repo": repo,
        "status": "modification_planned",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/monitor/log")
async def monitor_log(data: dict):
    """Monitor logging endpoint"""
    action = data.get("action", "")
    details = data.get("details", "")
    
    logger.info(f"Monitor log: {action} - {details}")
    
    return {
        "status": "logged",
        "action": action,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    logger.info(f"Starting SOPHIA Intel Test API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

