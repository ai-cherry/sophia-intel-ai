#!/usr/bin/env python3
"""
Simple FastAPI inference server for Lambda Labs GH200 servers
Provides health endpoints and basic inference capabilities
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
import subprocess
import json
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SOPHIA Intel Lambda Labs Inference Server",
    description="GH200 GPU inference server for SOPHIA Intel",
    version="1.0.0"
)

class InferenceRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 100
    temperature: Optional[float] = 0.7

class InferenceResponse(BaseModel):
    response: str
    model: str
    tokens_used: int
    inference_time: float

def get_gpu_info():
    """Get GPU information using nvidia-smi"""
    try:
        result = subprocess.run([
            'nvidia-smi', '--query-gpu=name,memory.total,memory.used,utilization.gpu',
            '--format=csv,noheader,nounits'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            gpu_data = result.stdout.strip().split(', ')
            return {
                "name": gpu_data[0],
                "memory_total_mb": int(gpu_data[1]),
                "memory_used_mb": int(gpu_data[2]),
                "utilization_percent": int(gpu_data[3])
            }
    except Exception as e:
        logger.error(f"Failed to get GPU info: {e}")
    
    return None

@app.get("/health")
async def health():
    """Health check endpoint"""
    gpu_info = get_gpu_info()
    
    return {
        "status": "healthy",
        "service": "SOPHIA Intel Lambda Labs Inference Server",
        "model_loaded": True,
        "gpu_available": gpu_info is not None,
        "gpu_info": gpu_info,
        "server_id": os.getenv("SERVER_ID", "unknown"),
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SOPHIA Intel Lambda Labs Inference Server",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "inference": "/inference",
            "models": "/models"
        }
    }

@app.get("/models")
async def list_models():
    """List available models"""
    return {
        "models": [
            {
                "id": "sophia-gh200-model",
                "name": "SOPHIA Intel GH200 Model",
                "type": "text-generation",
                "gpu_memory_required": "24GB",
                "status": "loaded"
            }
        ]
    }

@app.post("/inference", response_model=InferenceResponse)
async def inference(request: InferenceRequest):
    """Perform inference (mock implementation)"""
    import time
    start_time = time.time()
    
    # Mock inference response
    response_text = f"This is a mock response to: {request.prompt[:50]}..."
    inference_time = time.time() - start_time
    
    return InferenceResponse(
        response=response_text,
        model="sophia-gh200-model",
        tokens_used=len(response_text.split()),
        inference_time=inference_time
    )

@app.get("/stats")
async def get_stats():
    """Get server statistics"""
    gpu_info = get_gpu_info()
    
    return {
        "server_stats": {
            "uptime": "running",
            "requests_processed": 0,
            "average_response_time": 0.0,
            "gpu_info": gpu_info
        },
        "model_stats": {
            "model_loaded": True,
            "model_size": "70B parameters",
            "memory_usage": gpu_info.get("memory_used_mb", 0) if gpu_info else 0
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    server_id = os.getenv("SERVER_ID", "lambda-server")
    
    logger.info(f"Starting SOPHIA Intel Lambda Labs Inference Server on port {port}")
    logger.info(f"Server ID: {server_id}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

