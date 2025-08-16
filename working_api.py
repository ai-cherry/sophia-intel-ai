from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
import logging

app = FastAPI(title="SOPHIA Intel API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OrchestrationRequest(BaseModel):
    request_type: str
    payload: Dict[str, Any]
    timeout: Optional[int] = 300

@app.get("/health")
def health():
    return {
        "service": "sophia-intel-api",
        "status": "healthy",
        "version": "1.0.0",
        "features": ["orchestration", "voice"]
    }

@app.post("/api/orchestration")
def orchestration(request: OrchestrationRequest):
    if request.request_type == "health":
        return {"status": "ok", "message": "Orchestration working"}
    elif request.request_type == "chat":
        return {"response": f"Echo: {request.payload.get('message', 'No message')}", "status": "success"}
    else:
        return {"response": f"Received {request.request_type} request", "status": "success"}

@app.get("/api/speech/health")
def speech_health():
    return {"status": "ok", "provider": "mock", "features": ["stt", "tts"]}

@app.get("/api/speech/voices")
def speech_voices():
    return {
        "provider": "mock",
        "voices": [
            {"id": "test", "name": "Test Voice", "gender": "neutral"}
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
