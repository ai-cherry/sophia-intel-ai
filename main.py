from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from typing import List, Optional

app = FastAPI(
    title="SOPHIA Intel API",
    description="Clean minimal backend with correct API endpoints",
    version="1.0.0"
)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = "gpt-4"
    stream: Optional[bool] = False

class ChatResponse(BaseModel):
    message: str
    model: str
    status: str

@app.get("/")
async def root():
    return {"message": "SOPHIA Intel API - Clean Backend", "version": "1.0.0"}

@app.get("/health")
async def health():
    """Health check endpoint for Railway"""
    try:
        print("Health check endpoint called")  # Simple logging for Railway
        return {
            "status": "healthy", 
            "service": "sophia-intel-clean",
            "timestamp": "2025-08-18T01:50:00Z",
            "port": os.getenv("PORT", "8000")
        }
    except Exception as e:
        print(f"Health check error: {e}")
        return {"status": "error", "error": str(e)}

@app.get("/api/v1/system/status")
async def system_status():
    return {
        "status": "operational",
        "service": "sophia-intel-clean",
        "endpoints": {
            "chat": "/api/v1/chat/enhanced",
            "stream": "/api/v1/chat/stream",
            "status": "/api/v1/system/status"
        },
        "version": "1.0.0"
    }

@app.post("/api/v1/chat/enhanced")
async def chat_enhanced(request: ChatRequest):
    """Enhanced chat endpoint with correct API path"""
    return ChatResponse(
        message="Enhanced chat response from clean backend",
        model=request.model,
        status="success"
    )

@app.post("/api/v1/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint with correct API path"""
    return ChatResponse(
        message="Streaming chat response from clean backend",
        model=request.model,
        status="success"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

