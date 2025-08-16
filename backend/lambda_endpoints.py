"""
Lambda Inference API Endpoints for SOPHIA Intel
Provides direct access to Lambda's state-of-the-art models
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union
import json
import asyncio
from lambda_inference_client import LambdaInferenceClient, create_lambda_client

# Create router
router = APIRouter(prefix="/api/lambda", tags=["Lambda Inference"])

# Pydantic models
class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False


class TextRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None


class VisionRequest(BaseModel):
    text: str
    image_data: str
    model: Optional[str] = None
    is_url: bool = False


class ReasoningRequest(BaseModel):
    prompt: str
    model: Optional[str] = None


class CodeRequest(BaseModel):
    prompt: str
    language: Optional[str] = None
    model: Optional[str] = None


class ModelResponse(BaseModel):
    id: str
    name: str
    size: str
    context: str
    strengths: List[str]
    best_for: str


# Global client instance
lambda_client = None


def get_lambda_client() -> LambdaInferenceClient:
    """Get or create Lambda client"""
    global lambda_client
    if lambda_client is None:
        lambda_client = create_lambda_client()
    return lambda_client


@router.get("/models", response_model=List[Dict[str, Any]])
async def list_models():
    """List all available Lambda Inference API models"""
    try:
        client = get_lambda_client()
        models = client.list_models()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@router.get("/models/{model_id}", response_model=ModelResponse)
async def get_model_info(model_id: str):
    """Get detailed information about a specific model"""
    try:
        client = get_lambda_client()
        info = client.get_model_info(model_id)
        return ModelResponse(**info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")


@router.get("/models/recommended/{task_type}")
async def get_recommended_model(task_type: str):
    """Get recommended model for specific task type"""
    try:
        client = get_lambda_client()
        model = client.get_recommended_model(task_type)
        info = client.get_model_info(model)
        return {
            "task_type": task_type,
            "recommended_model": model,
            "model_info": info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendation: {str(e)}")


@router.post("/chat/completions")
async def chat_completions(request: ChatRequest):
    """Create chat completion using Lambda Inference API"""
    try:
        client = get_lambda_client()
        
        if request.stream:
            # Return streaming response
            def generate():
                for chunk in client.stream_chat_completion(
                    messages=request.messages,
                    model=request.model,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                ):
                    yield f"data: {json.dumps(chunk)}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
        else:
            # Return regular response
            response = client.chat_completion(
                messages=request.messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            return response
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")


@router.post("/completions")
async def text_completions(request: TextRequest):
    """Create text completion using Lambda Inference API"""
    try:
        client = get_lambda_client()
        response = client.text_completion(
            prompt=request.prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text completion failed: {str(e)}")


@router.post("/vision/completions")
async def vision_completions(request: VisionRequest):
    """Create vision completion with image input"""
    try:
        client = get_lambda_client()
        response = client.vision_completion(
            text=request.text,
            image_data=request.image_data,
            model=request.model,
            is_url=request.is_url
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vision completion failed: {str(e)}")


@router.post("/reasoning/completions")
async def reasoning_completions(request: ReasoningRequest):
    """Use DeepSeek R1 for complex reasoning tasks"""
    try:
        client = get_lambda_client()
        response = client.reasoning_completion(
            prompt=request.prompt,
            model=request.model
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reasoning completion failed: {str(e)}")


@router.post("/code/completions")
async def code_completions(request: CodeRequest):
    """Use Qwen 2.5 Coder for code generation tasks"""
    try:
        client = get_lambda_client()
        response = client.code_completion(
            prompt=request.prompt,
            language=request.language,
            model=request.model
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code completion failed: {str(e)}")


@router.get("/quick/chat")
async def quick_chat_endpoint(
    prompt: str = Query(..., description="Chat prompt"),
    model: Optional[str] = Query(None, description="Model to use"),
    temperature: float = Query(0.7, description="Temperature (0-2)")
):
    """Quick chat completion endpoint"""
    try:
        client = get_lambda_client()
        messages = [{"role": "user", "content": prompt}]
        response = client.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature
        )
        return {"response": response.get("content", "Error occurred")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick chat failed: {str(e)}")


@router.get("/quick/reasoning")
async def quick_reasoning_endpoint(
    prompt: str = Query(..., description="Reasoning prompt")
):
    """Quick reasoning with DeepSeek R1"""
    try:
        client = get_lambda_client()
        response = client.reasoning_completion(prompt)
        return {"response": response.get("content", "Error occurred")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick reasoning failed: {str(e)}")


@router.get("/quick/code")
async def quick_code_endpoint(
    prompt: str = Query(..., description="Code generation prompt"),
    language: Optional[str] = Query(None, description="Programming language")
):
    """Quick code generation with Qwen 2.5 Coder"""
    try:
        client = get_lambda_client()
        response = client.code_completion(prompt, language=language)
        return {"response": response.get("content", "Error occurred")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick code generation failed: {str(e)}")


@router.get("/health")
async def lambda_health_check():
    """Health check for Lambda Inference API"""
    try:
        client = get_lambda_client()
        # Test with a simple request
        response = client.chat_completion([
            {"role": "user", "content": "Hello"}
        ], model="hermes3-8b")  # Use fastest model for health check
        
        return {
            "status": "healthy",
            "lambda_api": "connected",
            "test_response": "success" if response.get("content") else "failed",
            "available_models": len(client.available_models)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "lambda_api": "disconnected",
            "error": str(e),
            "available_models": 0
        }


@router.get("/stats")
async def lambda_stats():
    """Get Lambda Inference API statistics"""
    try:
        client = get_lambda_client()
        models = client.list_models()
        
        # Group models by type
        model_types = {}
        for model in models:
            model_id = model["id"]
            if "llama" in model_id:
                model_types.setdefault("llama", []).append(model_id)
            elif "deepseek" in model_id:
                model_types.setdefault("deepseek", []).append(model_id)
            elif "hermes" in model_id:
                model_types.setdefault("hermes", []).append(model_id)
            elif "qwen" in model_id:
                model_types.setdefault("qwen", []).append(model_id)
            else:
                model_types.setdefault("other", []).append(model_id)
        
        return {
            "total_models": len(models),
            "model_types": model_types,
            "recommendations": client.model_recommendations,
            "api_base": "https://api.lambda.ai/v1"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


# Convenience endpoints for SOPHIA integration
@router.post("/sophia/chat")
async def sophia_chat(
    message: str,
    user_id: str,
    session_id: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7
):
    """SOPHIA-specific chat endpoint with user context"""
    try:
        client = get_lambda_client()
        
        # Build context-aware messages
        messages = [
            {
                "role": "system",
                "content": f"You are SOPHIA, an advanced AI assistant. You are helping user {user_id}. Be helpful, accurate, and engaging."
            },
            {
                "role": "user",
                "content": message
            }
        ]
        
        response = client.chat_completion(
            messages=messages,
            model=model or "llama-4-maverick-17b-128e-instruct-fp8",
            temperature=temperature
        )
        
        return {
            "success": True,
            "user_id": user_id,
            "session_id": session_id,
            "response": response.get("content", ""),
            "model_used": response.get("model", "unknown"),
            "usage": response.get("usage", {}),
            "timestamp": response.get("timestamp", "")
        }
        
    except Exception as e:
        return {
            "success": False,
            "user_id": user_id,
            "session_id": session_id,
            "error": str(e),
            "timestamp": ""
        }


@router.post("/sophia/analyze")
async def sophia_analyze(
    content: str,
    analysis_type: str = "general",
    model: Optional[str] = None
):
    """SOPHIA analysis endpoint for different content types"""
    try:
        client = get_lambda_client()
        
        # Choose appropriate model based on analysis type
        if analysis_type == "reasoning":
            model = model or "deepseek-r1-671b"
        elif analysis_type == "code":
            model = model or "qwen25-coder-32b-instruct"
        else:
            model = model or "llama-4-maverick-17b-128e-instruct-fp8"
        
        # Build analysis prompt
        prompts = {
            "reasoning": f"Analyze this content step by step and provide detailed reasoning:\n\n{content}",
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
            "analysis_type": analysis_type,
            "model_used": model,
            "analysis": response.get("content", ""),
            "usage": response.get("usage", {})
        }
        
    except Exception as e:
        return {
            "success": False,
            "analysis_type": analysis_type,
            "error": str(e)
        }

