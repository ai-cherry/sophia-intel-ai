"""
Research Router for Sophia MCP Server
Exports a FastAPI router for integration with the main app
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResearchRequest(BaseModel):
    query: str
    max_sources: int = 10
    include_summary: bool = True

class ResearchResponse(BaseModel):
    query: str
    sources: List[Dict] = []
    summary: Optional[Dict] = None
    total_sources: int = 0
    created_at: str

# Create router
router = APIRouter()

@router.get("/healthz")
async def healthz():
    """Health check endpoint for research service - dependency-free"""
    return {
        "status": "ok",
        "service": "sophia-research-mcp",
        "version": "4.2.0"
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "research-server",
        "version": "4.2.0",
        "apis_configured": {
            "serper": bool(os.getenv("SERPER_API_KEY")),
            "tavily": bool(os.getenv("TAVILY_API_KEY")),
            "zenrows": bool(os.getenv("ZENROWS_API_KEY")),
            "apify": bool(os.getenv("APIFY_API_TOKEN")),
            "openai": bool(os.getenv("OPENAI_API_KEY"))
        }
    }

@router.post("/search", response_model=ResearchResponse)
async def comprehensive_search(request: ResearchRequest):
    """Comprehensive multi-source research with robust error handling"""
    try:
        logger.info(f"Research request: {request.query}")
        
        # Return a normalized error response for now since providers aren't configured
        return ResearchResponse(
            query=request.query,
            sources=[],
            summary={
                "text": "Research service is operational but providers need configuration",
                "confidence": 0.5,
                "model": "fallback",
                "method": "placeholder",
                "sources_used": 0
            },
            total_sources=0,
            created_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Research failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

