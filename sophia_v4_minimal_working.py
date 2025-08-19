#!/usr/bin/env python3
"""
SOPHIA V4 Minimal Working - Basic Autonomous AI Server
Repository: https://github.com/ai-cherry/sophia-intel
Live URL: https://sophia-intel.fly.dev/v4/
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import logging
import uuid
from datetime import datetime
from typing import List, Dict
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sophia_v4_minimal")

# Initialize FastAPI app
app = FastAPI(title="SOPHIA V4 Minimal", version="4.0.0-MINIMAL")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatRequest(BaseModel):
    query: str
    user_id: str
    sources_limit: int = 3
    action: str = "search"

class PersonaRequest(BaseModel):
    query: str
    user_id: str

# SOPHIA's personality variants
SOPHIA_GREETINGS = [
    "🤠 Howdy partner! SOPHIA here with the real deal.",
    "⚡ Hey there! SOPHIA's got the scoop for you.",
    "🎯 SOPHIA in the house with genuine results!",
    "🔥 What's up! SOPHIA's locked and loaded.",
    "🚀 Yo, partner! Ready to conquer together?"
]

# Simple web search function
async def simple_web_search(query: str, sources_limit: int = 3) -> List[Dict]:
    """Simple web search with Serper API"""
    results = []
    
    try:
        # Try Serper API first
        if os.getenv("SERPER_API_KEY"):
            logger.info("🔍 Trying Serper API")
            response = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": os.getenv("SERPER_API_KEY")},
                json={"q": query, "num": sources_limit},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                for item in data.get("organic", [])[:sources_limit]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "summary": item.get("snippet", ""),
                        "source": "Google (Serper)",
                        "relevance_score": 0.9
                    })
                if results:
                    logger.info(f"✅ Serper returned {len(results)} results")
                    return results
    except Exception as e:
        logger.warning(f"⚠️ Serper failed: {e}")

    # Fallback to basic search
    logger.info("🌐 Using basic search fallback")
    results.append({
        "title": f"Search results for: {query}",
        "url": f"https://www.google.com/search?q={query.replace(' ', '+')}",
        "summary": f"Basic search results for {query}",
        "source": "Basic Search",
        "relevance_score": 0.7
    })
    
    return results

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "🤠 SOPHIA V4 Minimal is live! Visit /v4/ for the interface.",
        "version": "4.0.0-MINIMAL",
        "status": "operational"
    }

@app.get("/api/v1/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "version": "4.0.0-MINIMAL",
        "timestamp": datetime.now().isoformat(),
        "mode": "MINIMAL_WORKING",
        "apis": {
            "serper": "active" if os.getenv("SERPER_API_KEY") else "inactive",
            "basic_search": "active"
        }
    }

@app.post("/api/v1/chat")
async def minimal_chat(request: ChatRequest):
    """Minimal chat with basic web search"""
    start_time = datetime.now()
    
    try:
        # Simple web search
        results = await simple_web_search(request.query, request.sources_limit)
        
        # Basic response
        if results:
            summary = results[0]["summary"]
            message = f"🤠 Got the scoop on '{request.query}': {summary}. That's from {results[0]['source']}! 🎯"
        else:
            message = f"🤠 Couldn't find specific data for '{request.query}', but I'm ready for your next query! 🚀"
        
        response_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "results": results,
            "message": message,
            "sophia_mode": "MINIMAL_WORKING",
            "user_id": request.user_id,
            "response_time": f"{response_time:.2f}s",
            "sources_count": len(results),
            "greeting": SOPHIA_GREETINGS[hash(request.user_id) % len(SOPHIA_GREETINGS)]
        }
    
    except Exception as e:
        logger.error(f"❌ Chat error: {e}")
        return {
            "error": str(e),
            "message": f"🤠 Oops! Something went wrong: {str(e)}. But I'm still here! 🚀",
            "sophia_mode": "MINIMAL_WORKING",
            "user_id": request.user_id
        }

@app.post("/api/v1/persona")
async def persona_chat(request: PersonaRequest):
    """SOPHIA's personality endpoint"""
    greeting = SOPHIA_GREETINGS[hash(request.user_id) % len(SOPHIA_GREETINGS)]
    
    return {
        "message": f"{greeting}\n\nGot your query: {request.query}! I'm your AI sidekick! 🤠",
        "sophia_mode": "MINIMAL_WORKING",
        "user_id": request.user_id,
        "personality": "neon_cowboy_active"
    }

@app.get("/api/v1/status")
async def system_status():
    """Basic system status"""
    return {
        "sophia_version": "4.0.0-MINIMAL",
        "status": "operational",
        "personality": "neon_cowboy_active",
        "capabilities": {
            "basic_search": True,
            "personality": True,
            "chat": True
        },
        "greeting": "🤠 SOPHIA V4 Minimal is ready to help!"
    }

# Serve frontend (if directory exists)
try:
    app.mount("/v4", StaticFiles(directory="/app/apps/frontend/v4", html=True), name="frontend")
    logger.info("✅ Frontend mounted at /v4")
except Exception as e:
    logger.warning(f"⚠️ Frontend not mounted: {e}")

if __name__ == "__main__":
    logger.info("🚀 Starting SOPHIA V4 Minimal Working Server")
    logger.info("🤠 Basic neon cowboy mode: ACTIVATED")
    
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("sophia_v4_minimal_working:app", host="0.0.0.0", port=port, log_level="info")

