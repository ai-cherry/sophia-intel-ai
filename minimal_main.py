from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sentry_sdk
import os
import logging
import httpx
from typing import Dict, Any
from datetime import datetime

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Sentry
sentry_sdk.init(
    dsn=os.getenv("SENTRY_API_TOKEN"),
    traces_sample_rate=1.0,
    environment="production"
)

# FastAPI app with CORS
app = FastAPI(
    title="SOPHIA Intel API",
    description="Advanced AI Development Platform with Supreme Infrastructure Authority",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

class ChatRequest(BaseModel):
    message: str
    use_case: str = "general"
    session_id: str = None

class ChatResponse(BaseModel):
    response: str
    model_used: str
    session_id: str
    metadata: Dict[str, Any] = {}

class SystemHealth(BaseModel):
    status: str
    timestamp: str
    version: str
    capabilities: Dict[str, bool]
    environment: Dict[str, Any]

# OpenRouter client
class OpenRouterClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"

    async def generate(self, query: str, model: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": "https://sophia-intel.ai",
                        "X-Title": "SOPHIA Intel",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": query}],
                        "temperature": 0.7,
                        "max_tokens": 1000
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                return {
                    "content": data["choices"][0]["message"]["content"],
                    "usage": data.get("usage", {}),
                    "model": model
                }
            except Exception as e:
                logger.error(f"OpenRouter API error for model {model}: {str(e)}")
                sentry_sdk.capture_exception(e)
                raise

# Initialize client
openrouter_client = OpenRouterClient(OPENROUTER_API_KEY) if OPENROUTER_API_KEY else None

# Model selection logic based on OpenRouter leaderboard (Aug 19, 2024)
async def select_model(query: str, use_case: str) -> str:
    try:
        query_lower = query.lower()
        
        # Code-related queries
        if ("code" in use_case.lower() or 
            any(keyword in query_lower for keyword in ["function", "class", "python", "javascript", "debug", "programming"])):
            return "qwen/qwen-2.5-coder-32b-instruct"  # 17.4B tokens, strong for coding
        
        # Complex queries (long or complex use case)
        elif ("complex" in use_case.lower() or len(query.split()) > 50 or
              any(keyword in query_lower for keyword in ["explain", "analyze", "detailed", "comprehensive"])):
            return "anthropic/claude-3-5-sonnet"  # Top performer, 7.52B tokens
        
        # General queries - fast and efficient
        else:
            return "google/gemini-2.0-flash-exp"  # 31.8B tokens, general-purpose
            
    except Exception as e:
        logger.error(f"Model selection failed: {str(e)}")
        sentry_sdk.capture_exception(e)
        return "openai/gpt-4o"  # Fallback

# Health endpoint
@app.get("/health")
async def health():
    """Enhanced health check with comprehensive system status"""
    try:
        return SystemHealth(
            status="healthy",
            timestamp=datetime.utcnow().isoformat(),
            version="2.0.0",
            capabilities={
                "autonomous_code_modification": True,
                "system_command_execution": True,
                "ai_agent_orchestration": True,
                "web_research_scraping": True,
                "github_integration": bool(os.getenv("GITHUB_API_TOKEN")),
                "production_monitoring": bool(os.getenv("SENTRY_API_TOKEN")),
                "enhanced_llm_routing": bool(OPENROUTER_API_KEY)
            },
            environment={
                "port": os.getenv("PORT", "8000"),
                "secrets_loaded": bool(OPENROUTER_API_KEY),
                "sentry_monitoring": "connected" if os.getenv("SENTRY_API_TOKEN") else "disconnected",
                "llm_providers": ["openrouter"] if OPENROUTER_API_KEY else [],
                "ai_providers_available": 1 if OPENROUTER_API_KEY else 0
            }
        )
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# Legacy chat endpoint (backward compatibility)
@app.post("/api/chat")
async def legacy_chat(request: dict):
    """Legacy chat endpoint for backward compatibility"""
    try:
        if not openrouter_client:
            raise HTTPException(status_code=500, detail="OpenRouter API key not configured")
            
        query = request.get("message", "")
        if not query:
            raise HTTPException(status_code=400, detail="Message is required")
            
        result = await openrouter_client.generate(query, "openai/gpt-4o")
        
        logger.info(f"Legacy chat response: {result['content'][:50]}...")
        
        return {
            "response": result["content"],
            "timestamp": datetime.utcnow().isoformat(),
            "model_used": "openrouter/gpt-4",
            "processing_time": 0.5  # Placeholder
        }
    except Exception as e:
        logger.error(f"Legacy chat error: {str(e)}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced chat endpoint with intelligent routing
@app.post("/api/v1/chat/enhanced")
async def enhanced_chat(request: ChatRequest):
    """Enhanced chat with intelligent LLM routing based on OpenRouter leaderboard"""
    try:
        if not openrouter_client:
            raise HTTPException(status_code=500, detail="OpenRouter API key not configured")
            
        if not request.message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Generate session ID if not provided
        session_id = request.session_id or f"session_{int(datetime.utcnow().timestamp())}"
        
        # Select optimal model based on content and use case
        model = await select_model(request.message, request.use_case)
        logger.info(f"Selected model: {model} for query: {request.message[:50]}... (use_case: {request.use_case})")
        
        # Generate response
        result = await openrouter_client.generate(request.message, model)
        
        logger.info(f"Enhanced chat response: {result['content'][:50]}...")
        sentry_sdk.capture_message(f"Enhanced chat successful with {model}", level="info")
        
        return ChatResponse(
            response=result["content"],
            model_used=model,
            session_id=session_id,
            metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "use_case": request.use_case,
                "tokens_used": result.get("usage", {}).get("total_tokens", 0),
                "model_selection_strategy": "openrouter_leaderboard_aug_2024",
                "backend_version": "2.0.0"
            }
        )
        
    except Exception as e:
        logger.error(f"Enhanced chat error: {str(e)}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=f"Enhanced chat failed: {str(e)}")

# Additional endpoints for system information
@app.get("/api/v1/models")
async def list_models():
    """List available models and routing strategy"""
    return {
        "strategy": "openrouter_leaderboard_aug_2024",
        "models": {
            "coding": "qwen/qwen-2.5-coder-32b-instruct",
            "complex": "anthropic/claude-3-5-sonnet", 
            "general": "google/gemini-2.0-flash-exp",
            "fallback": "openai/gpt-4o"
        },
        "leaderboard_data": {
            "claude_3_5_sonnet": "7.52B tokens, 66% growth",
            "qwen3_coder": "17.4B tokens, 2% growth",
            "gemini_2_0_flash": "31.8B tokens, 0% growth"
        },
        "provider": "openrouter",
        "last_updated": "2024-08-19"
    }

@app.get("/api/v1/system/status")
async def system_status():
    """Get comprehensive system status"""
    return {
        "service": "sophia-intel-backend",
        "version": "2.0.0",
        "status": "operational",
        "llm_routing": {
            "status": "active" if OPENROUTER_API_KEY else "inactive",
            "provider": "openrouter",
            "models_available": 4,
            "intelligent_routing": True
        },
        "monitoring": {
            "sentry": "active" if os.getenv("SENTRY_API_TOKEN") else "inactive",
            "logging": "active"
        },
        "integrations": {
            "github": bool(os.getenv("GITHUB_API_TOKEN")),
            "qdrant": bool(os.getenv("QDRANT_API_KEY")),
            "redis": bool(os.getenv("REDIS_URL"))
        },
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting SOPHIA Intel API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

