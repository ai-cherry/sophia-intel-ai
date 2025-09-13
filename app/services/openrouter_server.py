#!/usr/bin/env python3
"""
OpenRouter Squad Server
Provides HTTP API for OpenRouter-based squad orchestration
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
import yaml

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.services.openrouter_squad_service import (
    OpenRouterSquadService,
    OpenRouterSquadOrchestrator,
    OpenRouterModels
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "openrouter_squad_config.yaml"
if CONFIG_PATH.exists():
    with open(CONFIG_PATH) as f:
        CONFIG = yaml.safe_load(f)
else:
    CONFIG = {}

# FastAPI app
app = FastAPI(
    title="OpenRouter Squad Server",
    description="Multi-model orchestration with 200+ models via OpenRouter",
    version="1.0.0"
)

# Global orchestrator instance
orchestrator: Optional[OpenRouterSquadOrchestrator] = None


class ProcessRequest(BaseModel):
    """Request for processing a task"""
    task: str = Field(..., description="Task description")
    task_type: Optional[str] = Field(None, description="Task type (architecture, coding, research, etc)")
    context: Optional[Dict] = Field(None, description="Additional context")
    model: Optional[str] = Field(None, description="Specific model to use")
    max_cost: Optional[float] = Field(None, description="Maximum cost per request")
    stream: bool = Field(False, description="Stream the response")


class ModelInfoResponse(BaseModel):
    """Response with model information"""
    total_models: int
    categories: Dict[str, int]
    models: List[Dict]


@app.on_event("startup")
async def startup_event():
    """Initialize the orchestrator on startup"""
    global orchestrator
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        logger.warning("OPENROUTER_API_KEY not set, some features may not work")
    orchestrator = OpenRouterSquadOrchestrator(api_key)
    logger.info("OpenRouter Squad Server started on port 8092")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global orchestrator
    if orchestrator:
        await orchestrator.close()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "openrouter_squad",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/models", response_model=ModelInfoResponse)
async def get_models():
    """Get available models and their information"""
    all_models = {}
    
    # Aggregate models by category
    categories = {
        'premium': OpenRouterModels.PREMIUM,
        'standard': OpenRouterModels.STANDARD,
        'economy': OpenRouterModels.ECONOMY,
        'specialized': OpenRouterModels.SPECIALIZED,
        'free': OpenRouterModels.FREE
    }
    
    model_list = []
    for category, models in categories.items():
        for model_id, info in models.items():
            model_info = {
                'id': model_id,
                'category': category,
                **info
            }
            model_list.append(model_info)
    
    return ModelInfoResponse(
        total_models=len(model_list),
        categories={cat: len(models) for cat, models in categories.items()},
        models=model_list
    )


@app.get("/costs")
async def get_cost_analysis():
    """Get cost analysis for different task types"""
    return {
        "cost_per_task_type": {
            "architecture": {
                "recommended_model": "anthropic/claude-3-opus",
                "cost_per_1k_tokens": "$0.015",
                "average_task_cost": "$0.30"
            },
            "coding": {
                "recommended_model": "anthropic/claude-3-sonnet",
                "cost_per_1k_tokens": "$0.003",
                "average_task_cost": "$0.06"
            },
            "research": {
                "recommended_model": "perplexity/llama-3-sonar-large-32k-online",
                "cost_per_1k_tokens": "$0.001",
                "average_task_cost": "$0.02"
            },
            "quick_task": {
                "recommended_model": "google/gemini-flash",
                "cost_per_1k_tokens": "$0.000075",
                "average_task_cost": "$0.001"
            },
            "reasoning": {
                "recommended_model": "openai/o1-preview",
                "cost_per_1k_tokens": "$0.015",
                "average_task_cost": "$0.50"
            }
        },
        "daily_estimate": {
            "light_usage": "$5-10",
            "moderate_usage": "$20-30",
            "heavy_usage": "$50-100"
        },
        "savings_vs_direct": "30-50% compared to direct API access"
    }


@app.post("/process")
async def process_task(request: ProcessRequest):
    """Process a task using the OpenRouter squad"""
    try:
        # Select task type if not provided
        task_type = request.task_type
        if not task_type:
            # Auto-detect task type
            task_lower = request.task.lower()
            if any(word in task_lower for word in ['design', 'architecture', 'system']):
                task_type = 'architecture'
            elif any(word in task_lower for word in ['research', 'find', 'search', 'latest']):
                task_type = 'research'
            elif any(word in task_lower for word in ['reason', 'prove', 'solve', 'algorithm']):
                task_type = 'reasoning'
            elif any(word in task_lower for word in ['implement', 'code', 'fix', 'refactor']):
                task_type = 'coding'
            elif any(word in task_lower for word in ['quick', 'simple', 'format']):
                task_type = 'quick'
            else:
                task_type = 'general'
        
        # Process with orchestrator
        result = await orchestrator.assign_task(
            task=request.task,
            task_type=task_type,
            context=request.context
        )
        
        return {
            "success": True,
            "task_type": task_type,
            "agent": result['agent'],
            "model": result['model'],
            "response": result['response'],
            "usage": {
                "tokens": result['tokens'],
                "estimated_cost": f"${result['cost']:.4f}"
            }
        }
        
    except Exception as e:
        logger.error(f"Task processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/completions")
async def chat_completion(request: Request):
    """OpenAI-compatible chat completion endpoint"""
    try:
        data = await request.json()
        
        # Extract parameters
        model = data.get('model', 'anthropic/claude-3-haiku')
        messages = data.get('messages', [])
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens')
        stream = data.get('stream', False)
        
        # Use the service directly
        result = await orchestrator.service.completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        
        if stream:
            # Return streaming response
            async def generate():
                async for chunk in result:
                    yield f"data: {json.dumps({'choices': [{'delta': {'content': chunk}}]})}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )
        else:
            return result
            
    except Exception as e:
        logger.error(f"Chat completion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents")
async def get_agents():
    """Get information about available squad agents"""
    agents = []
    for role, info in orchestrator.agents.items():
        agents.append({
            "role": role,
            "name": info['name'],
            "models": info['models'],
            "capabilities": info['capabilities'],
            "max_cost": f"${info['max_cost']:.2f}"
        })
    return {"agents": agents}


@app.get("/pricing")
async def get_current_pricing():
    """Get current model pricing from OpenRouter"""
    try:
        pricing = await orchestrator.service.get_model_pricing()
        
        # Format pricing by tier
        formatted = {
            "premium": [],
            "standard": [],
            "economy": [],
            "free": []
        }
        
        for model_id, price in pricing.items():
            entry = {
                "model": model_id,
                "price_per_million": f"${price:.2f}"
            }
            
            if price > 10:
                formatted["premium"].append(entry)
            elif price > 1:
                formatted["standard"].append(entry)
            elif price > 0:
                formatted["economy"].append(entry)
            else:
                formatted["free"].append(entry)
        
        return formatted
        
    except Exception as e:
        logger.error(f"Failed to get pricing: {e}")
        return {"error": "Failed to fetch current pricing"}


@app.get("/features")
async def get_features():
    """Get unique OpenRouter features"""
    return {
        "unique_features": {
            "automatic_fallback": {
                "description": "Automatically falls back to alternative models if primary fails",
                "enabled": True
            },
            "web_search": {
                "description": "Integrated web search via Perplexity models",
                "models": ["perplexity/llama-3-sonar-large-32k-online"],
                "enabled": True
            },
            "long_context": {
                "description": "Support for up to 1M token context",
                "models": {
                    "google/gemini-pro-1.5": "1,000,000 tokens",
                    "anthropic/claude-3-opus": "200,000 tokens",
                    "cohere/command-r-plus": "128,000 tokens"
                },
                "enabled": True
            },
            "free_tier": {
                "description": "Access to free models with rate limits",
                "models": ["google/gemma-7b-it:free", "meta-llama/llama-3-8b-instruct:free"],
                "rate_limit": "10 requests/minute",
                "enabled": True
            },
            "provider_redundancy": {
                "description": "Multiple providers for each model class",
                "providers": ["Anthropic", "OpenAI", "Google", "Meta", "Mistral", "Together", "Replicate"],
                "enabled": True
            },
            "compression": {
                "description": "Context compression for cost optimization",
                "method": "middle-out",
                "enabled": True
            }
        }
    }


def main():
    """Run the server"""
    port = int(os.getenv('OPENROUTER_PORT', '8092'))
    uvicorn.run(
        "app.services.openrouter_server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()