#!/usr/bin/env python3
"""
SOPHIA Intel MCP Server - Main FastAPI Application
Handles all API endpoints for SOPHIA autonomy testing
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis.asyncio as redis
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SOPHIA Intel API",
    description="SOPHIA Intel autonomy testing API",
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

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# API key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    """Verify API key (optional for testing)"""
    if api_key:
        expected_key = os.getenv("MCP_API_KEY", "sophia-mcp-secret")
        if api_key != expected_key:
            raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

# Redis client for caching
redis_client = None

@app.on_event("startup")
async def startup_event():
    """Initialize Redis connection"""
    global redis_client
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_client = redis.from_url(redis_url, decode_responses=True)
        logger.info("Redis connection initialized")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        redis_client = None

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SOPHIA Intel API",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "endpoints": [
            "/api/v1/health",
            "/api/v1/dashboard/status", 
            "/api/v1/chat/persona",
            "/api/v1/research/scrape",
            "/api/v1/code/modify",
            "/api/v1/monitor/log"
        ]
    }

# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "secrets_configured": len([k for k in os.environ.keys() if k.endswith("_API_KEY") or k.endswith("_TOKEN")]),
        "redis_connected": redis_client is not None
    }

# Dashboard status endpoint
@app.get("/api/v1/dashboard/status")
async def dashboard_status():
    """Dashboard status endpoint"""
    return {
        "status": "operational",
        "services": {
            "api": "running",
            "database": "connected" if os.getenv("NEON_DATABASE_URL") else "not configured",
            "redis": "connected" if redis_client else "not configured",
            "qdrant": "connected" if os.getenv("QDRANT_URL") else "not configured"
        },
        "timestamp": datetime.now().isoformat(),
        "uptime": "running",
        "version": "1.0.0"
    }

# Chat with persona endpoint
@app.post("/api/v1/chat/persona")
@limiter.limit("50/minute")
async def chat_persona(request: Request, data: dict, api_key: str = Depends(verify_api_key)):
    """Chat with persona endpoint"""
    query = data.get("query", "")
    persona = data.get("persona", "developer")
    
    logger.info(f"Chat request: {query} (persona: {persona})")
    
    # Simple response for autonomy testing
    response_map = {
        "developer": f"SOPHIA Intel Developer: I understand '{query}'. Ready to implement code changes.",
        "analyst": f"SOPHIA Intel Analyst: Analyzing '{query}'. Generating insights and metrics.",
        "researcher": f"SOPHIA Intel Researcher: Researching '{query}'. Gathering data and sources.",
        "tester": f"SOPHIA Intel Tester: Testing '{query}'. Running validation and quality checks."
    }
    
    response = response_map.get(persona, f"SOPHIA Intel ({persona}): Processing '{query}'")
    
    return {
        "response": response,
        "persona": persona,
        "timestamp": datetime.now().isoformat(),
        "status": "autonomy_test_ready",
        "query": query
    }

# Research scraping endpoint
@app.post("/api/v1/research/scrape")
@limiter.limit("30/minute")
async def research_scrape(request: Request, data: dict, api_key: str = Depends(verify_api_key)):
    """Research scraping endpoint"""
    url = data.get("url", "")
    
    logger.info(f"Research scrape request: {url}")
    
    # Mock research data for autonomy testing
    mock_data = {
        "todo+app+bug": "Users report tasks not saving after completion. localStorage implementation needed.",
        "dark+mode+feature": "Users requesting dark mode toggle. Popular feature for modern web apps.",
        "slow+api+response": "API response times over 2 seconds. Caching and optimization needed."
    }
    
    # Extract search terms from URL
    search_terms = ""
    for term in mock_data.keys():
        if term.replace("+", " ") in url:
            search_terms = term
            break
    
    research_result = mock_data.get(search_terms, f"Research data for {url}")
    
    return {
        "url": url,
        "status": "scraped",
        "data": research_result,
        "timestamp": datetime.now().isoformat(),
        "source": "mock_research_engine",
        "confidence": 0.85
    }

# Code modification endpoint
@app.post("/api/v1/code/modify")
@limiter.limit("20/minute")
async def code_modify(request: Request, data: dict, api_key: str = Depends(verify_api_key)):
    """Code modification endpoint"""
    query = data.get("query", "")
    repo = data.get("repo", "")
    
    logger.info(f"Code modification request: {query} for {repo}")
    
    return {
        "query": query,
        "repo": repo,
        "status": "modification_planned",
        "timestamp": datetime.now().isoformat(),
        "changes": f"Planning to implement: {query}",
        "branch": f"auto/{query.lower().replace(' ', '-')[:20]}",
        "estimated_time": "5-10 minutes"
    }

# Monitor logging endpoint
@app.post("/api/v1/monitor/log")
@limiter.limit("100/minute")
async def monitor_log(request: Request, data: dict, api_key: str = Depends(verify_api_key)):
    """Monitor logging endpoint"""
    action = data.get("action", "")
    details = data.get("details", "")
    
    logger.info(f"Monitor log: {action} - {details}")
    
    # Store in Redis if available
    if redis_client:
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "details": details
            }
            await redis_client.lpush("sophia_logs", json.dumps(log_entry))
            await redis_client.ltrim("sophia_logs", 0, 999)  # Keep last 1000 logs
        except Exception as e:
            logger.warning(f"Failed to store log in Redis: {e}")
    
    return {
        "status": "logged",
        "action": action,
        "details": details,
        "timestamp": datetime.now().isoformat(),
        "stored": redis_client is not None
    }

# MCP proxy endpoint for business integrations
@app.post("/mcp/{tool}")
@limiter.limit("100/minute")
async def mcp_proxy(request: Request, tool: str, data: dict, api_key: str = Depends(verify_api_key)):
    """MCP proxy for business tool integrations"""
    logger.info(f"MCP proxy request for {tool}: {data}")
    
    # Mock responses for autonomy testing
    mock_responses = {
        "notion": {"status": "success", "data": f"Notion integration: {data}"},
        "salesforce": {"status": "success", "data": f"Salesforce integration: {data}"},
        "slack": {"status": "success", "data": f"Slack integration: {data}"},
        "github": {"status": "success", "data": f"GitHub integration: {data}"}
    }
    
    response = mock_responses.get(tool, {"status": "error", "message": f"Unknown tool: {tool}"})
    response["timestamp"] = datetime.now().isoformat()
    
    return response

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting SOPHIA Intel API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

