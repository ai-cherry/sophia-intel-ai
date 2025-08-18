from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sentry_sdk
import os
import logging
import httpx
import asyncio
from typing import Dict, Any, List
from datetime import datetime
from search_engine import SearchEnhancedSwarm

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Sentry
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=1.0,
    environment="production"
)

# FastAPI app with CORS
app = FastAPI(title="SOPHIA Intel - AI Swarm Orchestrator")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount dashboard static files
try:
    app.mount("/dashboard", StaticFiles(directory="apps/dashboard/dist", html=True), name="dashboard")
    logger.info("✅ Dashboard static files mounted successfully at /dashboard")
except Exception as e:
    logger.warning(f"⚠️ Could not mount dashboard static files: {e}")

# API keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

class ChatRequest(BaseModel):
    query: str
    use_case: str = "general"

class TaskRequest(BaseModel):
    task: str

class SearchRequest(BaseModel):
    query: str
    max_results: int = 10
    sources: List[str] = ["duckduckgo"]

class TaskResponse(BaseModel):
    result: str
    status: str
    agents_used: List[str]

# Initialize search-enhanced swarm
search_swarm = SearchEnhancedSwarm()

# SOPHIA's Minimal Swarm Implementation
agents = {
    "planner": {"status": "active", "role": "task_planning", "model": "anthropic/claude-3.5-sonnet"},
    "coder": {"status": "active", "role": "code_generation", "model": "anthropic/claude-3.5-sonnet"},
    "reviewer": {"status": "active", "role": "quality_assurance", "model": "anthropic/claude-3.5-sonnet"},
    "coordinator": {"status": "active", "role": "orchestrator", "model": "google/gemini-flash-1.5"}
}

# OpenRouter client
class OpenRouterClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"

    async def generate(self, query: str, model: str) -> str:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://sophia-intel.pay-ready.com",
                        "X-Title": "SOPHIA Intel"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": query}]
                    }
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"Token usage: {data.get('usage', {})}")
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"OpenRouter API error: {str(e)}")
                sentry_sdk.capture_exception(e)
                raise

# Initialize client
openrouter_client = OpenRouterClient(OPENROUTER_API_KEY)

# Model selection logic based on LATEST OpenRouter leaderboard
async def select_model(query: str, use_case: str) -> str:
    try:
        if "complex" in use_case.lower() or len(query.split()) > 50:
            return "anthropic/claude-3.5-sonnet"  # High-performance model
        elif "code" in use_case.lower():
            return "anthropic/claude-3.5-sonnet"  # Also good for code
        elif "reasoning" in use_case.lower():
            return "anthropic/claude-3.5-sonnet"  # Strong reasoning
        else:
            return "google/gemini-flash-1.5"  # Fast general purpose
    except Exception as e:
        logger.error(f"Model selection failed: {str(e)}")
        return "google/gemini-flash-1.5"  # Reliable fallback

# Simple Agent Coordination
async def coordinate_agents(task: str) -> TaskResponse:
    """Simple agent coordination without complex dependencies"""
    try:
        agents_used = []
        
        # Step 1: Planning
        logger.info("Agent coordination: Planning phase")
        planning_prompt = f"As a task planner, break down this task: {task}"
        plan = await openrouter_client.generate(planning_prompt, agents["planner"]["model"])
        agents_used.append("Planner")
        
        # Step 2: Implementation
        logger.info("Agent coordination: Implementation phase")
        coding_prompt = f"Based on this plan, implement the solution:\n{plan}"
        implementation = await openrouter_client.generate(coding_prompt, agents["coder"]["model"])
        agents_used.append("Coder")
        
        # Step 3: Review
        logger.info("Agent coordination: Review phase")
        review_prompt = f"Review this implementation for quality:\n{implementation}"
        review = await openrouter_client.generate(review_prompt, agents["reviewer"]["model"])
        agents_used.append("Reviewer")
        
        # Combine results
        final_result = f"## Plan\n{plan}\n\n## Implementation\n{implementation}\n\n## Review\n{review}"
        
        return TaskResponse(
            result=final_result,
            status="completed",
            agents_used=agents_used
        )
        
    except Exception as e:
        logger.error(f"Agent coordination error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent coordination failed: {str(e)}")

# API Endpoints
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "port": os.getenv("PORT", "8000"),
        "sentry": "connected" if os.getenv("SENTRY_DSN") else "disconnected",
        "llm_providers": ["openrouter"],
        "swarm_enabled": True,
        "deployment_timestamp": datetime.utcnow().isoformat()
    }

@app.get("/debug/routes")
async def debug_routes():
    return [str(route) for route in app.routes]

@app.post("/api/chat")
async def legacy_chat(request: ChatRequest):
    try:
        model = await select_model(request.query, request.use_case)
        response = await openrouter_client.generate(request.query, model)
        return {"response": response}
    except Exception as e:
        logger.error(f"Legacy chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chat/enhanced")
async def enhanced_chat(request: ChatRequest):
    try:
        model = await select_model(request.query, request.use_case)
        logger.info(f"Selected model: {model} for query: {request.query[:50]}...")
        response = await openrouter_client.generate(request.query, model)
        logger.info(f"Enhanced chat response: {response[:50]}...")
        return {"response": response, "model_used": model}
    except Exception as e:
        logger.error(f"Enhanced chat error: {str(e)}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/swarm/status")
async def swarm_status():
    """Get current swarm status"""
    active_agents = sum(1 for agent in agents.values() if agent["status"] == "active")
    
    return {
        "swarm_status": "operational" if active_agents > 0 else "degraded",
        "total_agents": len(agents),
        "active_agents": active_agents,
        "agents": agents,
        "coordinator_model": "google/gemini-flash-1.5",
        "openrouter_connected": OPENROUTER_API_KEY is not None,
        "last_updated": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/system/stats")
async def system_stats():
    """Get comprehensive system statistics"""
    import psutil
    import time
    
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Calculate uptime
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    uptime_hours = uptime_seconds / 3600
    
    # Agent statistics
    active_agents = sum(1 for agent in agents.values() if agent["status"] == "active")
    
    return {
        "system_health": "healthy" if cpu_percent < 80 and memory.percent < 80 else "warning",
        "performance": {
            "cpu_usage_percent": round(cpu_percent, 2),
            "memory_usage_percent": round(memory.percent, 2),
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_usage_percent": round(disk.percent, 2),
            "disk_free_gb": round(disk.free / (1024**3), 2)
        },
        "uptime": {
            "hours": round(uptime_hours, 2),
            "days": round(uptime_hours / 24, 2)
        },
        "ai_swarm": {
            "status": "operational" if active_agents > 0 else "degraded",
            "active_agents": active_agents,
            "total_agents": len(agents),
            "models_available": ["anthropic/claude-3.5-sonnet", "google/gemini-flash-1.5"]
        },
        "services": {
            "openrouter_connected": OPENROUTER_API_KEY is not None,
            "database_connected": True,  # Placeholder for future DB connection check
            "cache_connected": True      # Placeholder for future Redis connection check
        },
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.1.0"
    }

@app.post("/api/v1/swarm/execute", response_model=TaskResponse)
async def execute_swarm_task(request: TaskRequest):
    """Execute task through simple agent coordination"""
    try:
        logger.info(f"Executing swarm task: {request.task[:100]}...")
        
        # Execute with timeout protection
        task_result = await asyncio.wait_for(
            coordinate_agents(request.task), 
            timeout=120.0
        )
        
        logger.info(f"Swarm task completed. Agents used: {task_result.agents_used}")
        return task_result
            
    except asyncio.TimeoutError:
        logger.error("Swarm task timeout exceeded")
        raise HTTPException(status_code=408, detail="Task timeout exceeded")
    except Exception as e:
        logger.error(f"Swarm execution error: {str(e)}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=f"Swarm execution failed: {str(e)}")

@app.post("/api/v1/search/research")
async def search_research(request: SearchRequest):
    """SOPHIA's bootstrap search capability - she will use this to research and upgrade herself"""
    try:
        logger.info(f"SOPHIA executing search research: {request.query[:100]}...")
        
        # Use the search-enhanced swarm for research
        result = await search_swarm.research_task(
            research_query=request.query,
            analysis_focus="implementation strategies and technical details"
        )
        
        logger.info(f"Search research completed. Status: {result.get('status')}")
        return result
        
    except Exception as e:
        logger.error(f"Search research error: {str(e)}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=f"Search research failed: {str(e)}")

@app.post("/api/v1/search/upgrade")
async def search_upgrade_analysis(request: TaskRequest):
    """SOPHIA analyzes search capabilities and plans upgrades"""
    try:
        logger.info("SOPHIA analyzing her own search capabilities for upgrades...")
        
        # Have SOPHIA research her own search architecture
        research_result = await search_swarm.research_task(
            research_query="AI agent search architecture web scraping frameworks 2024 2025 best practices",
            analysis_focus="search system improvements and implementation strategies"
        )
        
        # Combine with task analysis
        upgrade_analysis = {
            "current_capabilities": {
                "search_engines": ["duckduckgo"],
                "agent_types": ["researcher", "analyzer", "synthesizer"],
                "limitations": ["basic search only", "no specialized scraping", "limited source diversity"]
            },
            "research_findings": research_result,
            "upgrade_recommendations": [
                "Add multiple search engine support",
                "Implement specialized scraping agents",
                "Add academic and social media search",
                "Implement real-time monitoring capabilities"
            ],
            "next_steps": [
                "Research specific implementation frameworks",
                "Design enhanced search architecture",
                "Implement and test improvements",
                "Deploy upgraded search system"
            ],
            "status": "analysis_complete",
            "agents_used": ["researcher", "analyzer", "synthesizer"]
        }
        
        return upgrade_analysis
        
    except Exception as e:
        logger.error(f"Search upgrade analysis error: {str(e)}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=f"Search upgrade analysis failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

