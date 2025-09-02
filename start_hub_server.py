"""
Minimal server to run the hub interface
"""
import os
import sys
sys.path.insert(0, '/Users/lynnmusil/sophia-intel-ai')

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import PlainTextResponse
from app.api.hub.hub_controller import router as hub_router
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time

app = FastAPI(
    title="Sophia Intel AI Hub",
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

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include hub router
app.include_router(hub_router)

# Request/Response models
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    max_tokens: Optional[int] = 100
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

# Basic health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Hub Server"}

# Add chat completions endpoint
@app.post("/chat/completions", response_model=ChatResponse)
async def chat_completions(request: ChatRequest):
    """Mock chat completions endpoint for testing"""
    return ChatResponse(
        id=f"chatcmpl-{int(time.time())}",
        created=int(time.time()),
        model=request.model,
        choices=[{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! This is a test response from the hub server."
            },
            "finish_reason": "stop"
        }],
        usage={
            "prompt_tokens": 10,
            "completion_tokens": 15,
            "total_tokens": 25
        }
    )

# Add models endpoint
@app.get("/models")
async def list_models():
    """List available models"""
    return {
        "object": "list",
        "data": [
            {"id": "google/gemini-2.5-flash", "object": "model", "created": 1677649963},
            {"id": "openai/gpt-4", "object": "model", "created": 1677649963},
            {"id": "anthropic/claude-3-opus", "object": "model", "created": 1677649963}
        ]
    }

# Add metrics endpoint (Prometheus format)
@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Return Prometheus-style metrics"""
    metrics_text = """# HELP api_requests_total Total number of API requests
# TYPE api_requests_total counter
api_requests_total{method="GET",endpoint="/health"} 100
api_requests_total{method="POST",endpoint="/chat/completions"} 50

# HELP api_request_duration_seconds API request duration in seconds
# TYPE api_request_duration_seconds histogram
api_request_duration_seconds_bucket{le="0.1"} 120
api_request_duration_seconds_bucket{le="0.5"} 145
api_request_duration_seconds_bucket{le="1.0"} 150
api_request_duration_seconds_sum 45.5
api_request_duration_seconds_count 150

# HELP active_connections Number of active connections
# TYPE active_connections gauge
active_connections 5

# HELP model_usage_total Total model usage by model
# TYPE model_usage_total counter
model_usage_total{model="google/gemini-2.5-flash"} 25
model_usage_total{model="openai/gpt-4"} 15
model_usage_total{model="anthropic/claude-3-opus"} 10
"""
    return metrics_text

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)