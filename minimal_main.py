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
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=1.0,
    environment="production"
)

# FastAPI app with CORS
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Log registered routes on startup
logger.info("Registered routes: %s", [str(route) for route in app.routes])

# API keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

class ChatRequest(BaseModel):
    query: str
    use_case: str = "general"

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

    async def get_model_rankings(self) -> list:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                return [{"model_id": m["id"]} for m in response.json()["data"]]
            except Exception as e:
                logger.error(f"OpenRouter rankings error: {str(e)}")
                sentry_sdk.capture_exception(e)
                return [{"model_id": "openai/gpt-4o"}]

# Initialize client
openrouter_client = OpenRouterClient(OPENROUTER_API_KEY)

# Model selection logic based on LATEST OpenRouter leaderboard (Aug 18, 2025)
async def select_model(query: str, use_case: str) -> str:
    try:
        # TOP MODELS from current leaderboard - NO OLD MODELS!
        if "complex" in use_case.lower() or len(query.split()) > 50:
            return "anthropic/claude-sonnet-4"  # #1 on leaderboard - 60.3B tokens
        elif "code" in use_case.lower():
            return "qwen/qwen3-coder"  # #6 on leaderboard - 17.4B tokens
        elif "reasoning" in use_case.lower():
            return "deepseek/deepseek-v3-0324"  # #5 on leaderboard - 20.8B tokens
        else:
            return "google/gemini-2.0-flash"  # #2 on leaderboard - 38.8B tokens
    except Exception as e:
        logger.error(f"Model selection failed: {str(e)}")
        sentry_sdk.capture_exception(e)
        return "google/gemini-2.5-flash"  # #3 fallback - 31.8B tokens

# Debug route to verify FastAPI registration
@app.get("/debug/routes")
async def debug_routes():
    return [str(route) for route in app.routes]

# Health endpoint with deployment timestamp
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "port": os.getenv("PORT", "8000"),
        "sentry": "connected" if os.getenv("SENTRY_DSN") else "disconnected",
        "llm_providers": ["openrouter"],
        "deployment_timestamp": datetime.utcnow().isoformat()
    }

# Legacy chat endpoint
@app.post("/api/chat")
async def legacy_chat(request: dict):
    try:
        query = request.get("message", "")
        response = await openrouter_client.generate(query, "openai/gpt-4o")
        logger.info(f"Legacy chat response: {response[:50]}...")
        return {"response": response}
    except Exception as e:
        logger.error(f"Legacy chat error: {str(e)}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced chat endpoint
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

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

