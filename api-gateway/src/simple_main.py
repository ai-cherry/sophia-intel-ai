"""
Simple SOPHIA Backend with Lambda Inference API Integration
Production-ready FastAPI application for www.sophia-intel.ai
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn

from backend.lambda_inference_client import LambdaInferenceClient, create_lambda_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    user_id: str
    session_id: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7
    # Feature toggle flags
    web_access: bool = False
    deep_research: bool = False
    training: bool = False


class ChatResponse(BaseModel):
    success: bool
    session_id: str
    response: str
    model_used: str
    timestamp: str
    usage: Dict[str, Any]
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    components: Dict[str, str]
    lambda_api: str
    available_models: int
    timestamp: str


# FastAPI app
app = FastAPI(
    title="SOPHIA Intel API",
    description="AI-powered platform with Lambda Inference API integration",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.sophia-intel.ai", 
        "https://sophia-intel.ai", 
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "*"  # Allow all for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Lambda client
lambda_client = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global lambda_client
    
    try:
        # Initialize Lambda Inference API client
        lambda_client = create_lambda_client()
        logger.info("Lambda Inference API client initialized successfully")
        
        # Test connection
        models = lambda_client.list_models()
        logger.info(f"Connected to Lambda API with {len(models)} available models")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        # Don't raise - allow app to start even if Lambda API is temporarily unavailable


def get_lambda_client() -> LambdaInferenceClient:
    """Get Lambda client instance"""
    global lambda_client
    if lambda_client is None:
        lambda_client = create_lambda_client()
    return lambda_client


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with component status"""
    try:
        client = get_lambda_client()
        models = client.list_models()
        
        return HealthResponse(
            status="healthy",
            components={
                "lambda_api": "connected",
                "backend": "operational",
                "models": "available"
            },
            lambda_api="connected",
            available_models=len(models),
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        return HealthResponse(
            status="degraded",
            components={
                "lambda_api": "disconnected",
                "backend": "operational", 
                "models": "unavailable"
            },
            lambda_api="disconnected",
            available_models=0,
            timestamp=datetime.now().isoformat()
        )


# Main chat endpoint
@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_sophia(message: ChatMessage):
    """Chat with SOPHIA using Lambda Inference API"""
    try:
        client = get_lambda_client()
        
        # Build context-aware messages with feature flags
        system_content = f"You are SOPHIA, an advanced AI assistant created by the SOPHIA Intel team. You are helpful, accurate, and engaging. You have access to state-of-the-art AI models through Lambda Inference API. You are currently helping user {message.user_id}."
        
        # Add feature flag context
        enabled_features = []
        if message.web_access:
            enabled_features.append("web search and real-time information access")
        if message.deep_research:
            enabled_features.append("multi-step research and analysis capabilities")
        if message.training:
            enabled_features.append("training mode for knowledge capture and learning")
            
        if enabled_features:
            system_content += f" Currently enabled features: {', '.join(enabled_features)}."
        
        messages = [
            {
                "role": "system",
                "content": system_content
            },
            {
                "role": "user",
                "content": message.message
            }
        ]
        
        # Use specified model or default to Llama 4 Maverick
        model = message.model or "llama-4-maverick-17b-128e-instruct-fp8"
        
        response = client.chat_completion(
            messages=messages,
            model=model,
            temperature=message.temperature
        )
        
        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])
        
        return ChatResponse(
            success=True,
            session_id=message.session_id or f"session_{datetime.now().timestamp()}",
            response=response.get("content", ""),
            model_used=response.get("model", model),
            timestamp=datetime.now().isoformat(),
            usage=response.get("usage", {}),
            error=None
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return ChatResponse(
            success=False,
            session_id=message.session_id or "error_session",
            response="I apologize, but I'm experiencing technical difficulties. Please try again.",
            model_used="error",
            timestamp=datetime.now().isoformat(),
            usage={},
            error=str(e)
        )


# Quick chat endpoint
@app.get("/api/quick-chat")
async def quick_chat(
    prompt: str = Query(..., description="Chat prompt"),
    model: Optional[str] = Query(None, description="Model to use"),
    temperature: float = Query(0.7, description="Temperature (0-2)"),
    user_id: str = Query("anonymous", description="User ID")
):
    """Quick chat endpoint for simple interactions"""
    try:
        message = ChatMessage(
            message=prompt,
            user_id=user_id,
            model=model,
            temperature=temperature
        )
        response = await chat_with_sophia(message)
        return {"response": response.response, "model": response.model_used}
    except Exception as e:
        return {"error": str(e)}


# Model management endpoints
@app.get("/api/models")
async def list_available_models():
    """List all available Lambda Inference API models"""
    try:
        client = get_lambda_client()
        models = client.list_models()
        
        # Add model information
        enhanced_models = []
        for model in models:
            model_info = client.get_model_info(model["id"])
            enhanced_models.append({
                **model,
                **model_info
            })
        
        return {
            "total": len(enhanced_models),
            "models": enhanced_models,
            "recommendations": client.model_recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@app.get("/api/models/{model_id}")
async def get_model_details(model_id: str):
    """Get detailed information about a specific model"""
    try:
        client = get_lambda_client()
        info = client.get_model_info(model_id)
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")


# Specialized endpoints
@app.post("/api/reasoning")
async def reasoning_endpoint(
    prompt: str,
    model: Optional[str] = None,
    user_id: str = "anonymous"
):
    """Use DeepSeek R1 for complex reasoning tasks"""
    try:
        client = get_lambda_client()
        response = client.reasoning_completion(prompt, model=model)
        
        return {
            "success": True,
            "user_id": user_id,
            "reasoning": response.get("content", ""),
            "model_used": response.get("model", "deepseek-r1-671b"),
            "usage": response.get("usage", {}),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/code")
async def code_generation_endpoint(
    prompt: str,
    language: Optional[str] = None,
    model: Optional[str] = None,
    user_id: str = "anonymous"
):
    """Use Qwen 2.5 Coder for code generation tasks"""
    try:
        client = get_lambda_client()
        response = client.code_completion(prompt, language=language, model=model)
        
        return {
            "success": True,
            "user_id": user_id,
            "code": response.get("content", ""),
            "language": language,
            "model_used": response.get("model", "qwen25-coder-32b-instruct"),
            "usage": response.get("usage", {}),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/analyze")
async def content_analysis_endpoint(
    content: str,
    analysis_type: str = "general",
    model: Optional[str] = None,
    user_id: str = "anonymous"
):
    """Analyze content using appropriate Lambda models"""
    try:
        client = get_lambda_client()
        
        # Choose model based on analysis type
        if analysis_type == "reasoning" and not model:
            model = "deepseek-r1-671b"
        elif analysis_type == "code" and not model:
            model = "qwen25-coder-32b-instruct"
        elif not model:
            model = "llama-4-maverick-17b-128e-instruct-fp8"
        
        # Build analysis prompt
        prompts = {
            "reasoning": f"Analyze this content step by step with detailed reasoning:\n\n{content}",
            "code": f"Analyze this code and provide insights, improvements, and explanations:\n\n{content}",
            "general": f"Provide a comprehensive analysis of this content:\n\n{content}",
            "summary": f"Provide a concise summary of this content:\n\n{content}"
        }
        
        prompt = prompts.get(analysis_type, prompts["general"])
        
        if analysis_type == "reasoning":
            response = client.reasoning_completion(prompt, model=model)
        elif analysis_type == "code":
            response = client.code_completion(prompt, model=model)
        else:
            messages = [{"role": "user", "content": prompt}]
            response = client.chat_completion(messages, model=model)
        
        return {
            "success": True,
            "user_id": user_id,
            "analysis_type": analysis_type,
            "analysis": response.get("content", ""),
            "model_used": model,
            "usage": response.get("usage", {}),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# Streaming chat endpoint
@app.post("/api/chat/stream")
async def stream_chat(message: ChatMessage):
    """Stream chat responses for real-time interaction"""
    try:
        client = get_lambda_client()
        
        messages = [
            {
                "role": "system",
                "content": f"You are SOPHIA, an advanced AI assistant. You are helping user {message.user_id}."
            },
            {
                "role": "user",
                "content": message.message
            }
        ]
        
        model = message.model or "llama-4-maverick-17b-128e-instruct-fp8"
        
        def generate():
            try:
                for chunk in client.stream_chat_completion(
                    messages=messages,
                    model=model,
                    temperature=message.temperature
                ):
                    if chunk.get("content"):
                        yield f"data: {json.dumps(chunk)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Legacy endpoints for backward compatibility
@app.post("/chat")
async def legacy_chat(message: ChatMessage):
    """Legacy chat endpoint"""
    return await chat_with_sophia(message)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "SOPHIA Intel API",
        "version": "2.1.0",
        "status": "operational",
        "lambda_integration": "active",
        "endpoints": {
            "health": "/health",
            "chat": "/api/chat",
            "quick_chat": "/api/quick-chat",
            "stream_chat": "/api/chat/stream",
            "models": "/api/models",
            "reasoning": "/api/reasoning",
            "code": "/api/code",
            "analyze": "/api/analyze",
            "docs": "/docs"
        },
        "features": [
            "Lambda Inference API integration",
            "19 state-of-the-art AI models",
            "Real-time streaming responses",
            "Specialized reasoning and coding",
            "Content analysis capabilities"
        ]
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "path": str(request.url),
            "available_endpoints": [
                "/health", "/api/chat", "/api/models", "/docs"
            ]
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "SOPHIA is experiencing technical difficulties",
            "support": "Please try again or contact support"
        }
    )


if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5002)),
        reload=False,
        access_log=True,
        log_level="info"
    )

