"""
Enhanced Model & Cost Management Endpoints for Bridge API
Super-current OpenRouter integration with Redis caching and usage tracking
"""
import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field
import structlog

from app.services.model_catalog_manager import get_model_catalog_manager, ModelMetadata
from app.services.usage_aggregator import get_usage_aggregator, UsageEvent, TimeWindow, UsageMetrics, CostAlert
from app.api.openrouter_gateway import OpenRouterGateway

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["models", "costs"])


# Request/Response Models
class ModelSearchRequest(BaseModel):
    query: Optional[str] = None
    provider: Optional[str] = None
    capabilities: Optional[List[str]] = None
    max_cost_per_1m: Optional[float] = None
    min_context_window: Optional[int] = None
    performance_tier: Optional[str] = Field(None, pattern="^(economy|balanced|premium)$")


class ModelRecommendationRequest(BaseModel):
    task_description: str
    max_cost_per_request: Optional[float] = 0.10
    priority: str = Field("balanced", pattern="^(speed|cost|quality|balanced)$")
    context_length_needed: Optional[int] = None
    capabilities_required: Optional[List[str]] = None


class CostBudgetRequest(BaseModel):
    hourly_limit: Optional[float] = None
    daily_limit: Optional[float] = None
    monthly_limit: Optional[float] = None


class UsageTrackingRequest(BaseModel):
    model_id: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    latency_ms: Optional[float] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    endpoint: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False
    track_usage: Optional[bool] = True


# Dependency for OpenRouter Gateway
async def get_openrouter_gateway() -> OpenRouterGateway:
    return OpenRouterGateway()


@router.get("/models/catalog", response_model=Dict[str, Any])
async def get_model_catalog(
    force_refresh: bool = Query(False, description="Force refresh from OpenRouter"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    tier: Optional[str] = Query(None, description="Filter by performance tier")
):
    """
    Get comprehensive model catalog with Redis caching
    Returns 400+ models from OpenRouter with pricing, capabilities, and metadata
    """
    try:
        catalog_manager = await get_model_catalog_manager()
        
        if provider:
            models = await catalog_manager.get_models_by_provider(provider)
            return {
                "models": [model.__dict__ for model in models],
                "total_models": len(models),
                "filtered_by": {"provider": provider},
                "cache_info": await catalog_manager.get_cache_stats()
            }
        elif tier:
            models = await catalog_manager.get_models_by_tier(tier)
            return {
                "models": [model.__dict__ for model in models],
                "total_models": len(models),
                "filtered_by": {"tier": tier},
                "cache_info": await catalog_manager.get_cache_stats()
            }
        else:
            catalog = await catalog_manager.get_models(force_refresh=force_refresh)
            return {
                "models": [model.__dict__ for model in catalog.models],
                "total_models": catalog.total_models,
                "last_updated": catalog.last_updated,
                "provider_stats": catalog.provider_stats,
                "cache_info": await catalog_manager.get_cache_stats()
            }
    except Exception as e:
        logger.error("Failed to get model catalog", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve model catalog: {e}")


@router.post("/models/search", response_model=Dict[str, Any])
async def search_models(request: ModelSearchRequest):
    """
    Advanced model search with multiple filters
    Search by name, provider, capabilities, cost, and performance tier
    """
    try:
        catalog_manager = await get_model_catalog_manager()
        
        # Start with all models
        catalog = await catalog_manager.get_models()
        filtered_models = catalog.models
        
        # Apply filters
        if request.query:
            filtered_models = await catalog_manager.search_models(
                request.query, request.capabilities
            )
        elif request.capabilities:
            filtered_models = [
                m for m in filtered_models 
                if any(cap in m.capabilities for cap in request.capabilities)
            ]
        
        if request.provider:
            filtered_models = [m for m in filtered_models if m.provider == request.provider]
        
        if request.performance_tier:
            filtered_models = [m for m in filtered_models if m.performance_tier == request.performance_tier]
        
        if request.max_cost_per_1m:
            filtered_models = [
                m for m in filtered_models 
                if m.pricing.input_cost_per_1m <= request.max_cost_per_1m
            ]
        
        if request.min_context_window:
            filtered_models = [
                m for m in filtered_models 
                if m.pricing.context_window >= request.min_context_window
            ]
        
        # Sort by cost (ascending)
        filtered_models.sort(key=lambda m: m.pricing.input_cost_per_1m)
        
        return {
            "models": [model.__dict__ for model in filtered_models[:50]],  # Limit to 50 results
            "total_matches": len(filtered_models),
            "filters_applied": request.__dict__,
            "suggestions": {
                "cheapest": filtered_models[0].__dict__ if filtered_models else None,
                "most_capable": max(filtered_models, key=lambda m: len(m.capabilities)).__dict__ if filtered_models else None
            }
        }
    except Exception as e:
        logger.error("Failed to search models", error=str(e))
        raise HTTPException(status_code=500, detail=f"Model search failed: {e}")


@router.post("/models/recommend", response_model=Dict[str, Any])
async def recommend_model(request: ModelRecommendationRequest):
    """
    AI-powered model recommendation based on task and constraints
    Analyzes task requirements and suggests optimal model
    """
    try:
        catalog_manager = await get_model_catalog_manager()
        catalog = await catalog_manager.get_models()
        
        # Score models based on request criteria
        scored_models = []
        
        for model in catalog.models:
            score = 0.0
            
            # Cost scoring (higher score for lower cost if priority is cost)
            if request.priority in ["cost", "balanced"]:
                # Estimate cost per request (assuming 1000 tokens average)
                est_cost = (model.pricing.input_cost_per_1m / 1_000_000) * 750 + \
                          (model.pricing.output_cost_per_1m / 1_000_000) * 250
                
                if est_cost <= request.max_cost_per_request:
                    score += 30 if request.priority == "cost" else 15
                    # Bonus for being well under budget
                    if est_cost <= request.max_cost_per_request * 0.5:
                        score += 10
            
            # Context window scoring
            if request.context_length_needed:
                if model.pricing.context_window >= request.context_length_needed:
                    score += 20
                elif model.pricing.context_window >= request.context_length_needed * 0.8:
                    score += 10
            else:
                # Default bonus for large context
                if model.pricing.context_window >= 100000:
                    score += 10
            
            # Capability matching
            if request.capabilities_required:
                matches = sum(1 for cap in request.capabilities_required if cap in model.capabilities)
                score += matches * 15
            
            # Performance tier scoring
            tier_scores = {"premium": 25, "balanced": 15, "economy": 10}
            if request.priority == "quality":
                score += tier_scores.get(model.performance_tier, 0)
            elif request.priority == "speed":
                # Prefer economy models for speed
                if model.performance_tier == "economy":
                    score += 20
            
            # Provider reliability bonus (based on common providers)
            reliable_providers = ["openai", "anthropic", "google", "meta-llama"]
            if model.provider in reliable_providers:
                score += 5
            
            # Task-specific bonuses
            task_lower = request.task_description.lower()
            if "code" in task_lower or "programming" in task_lower:
                if "coding" in model.capabilities:
                    score += 15
            if "analysis" in task_lower or "research" in task_lower:
                if model.pricing.context_window >= 50000:
                    score += 10
            if "chat" in task_lower or "conversation" in task_lower:
                if "chat" in model.capabilities:
                    score += 10
            
            scored_models.append({
                "model": model.__dict__,
                "score": score,
                "estimated_cost_per_request": (model.pricing.input_cost_per_1m / 1_000_000) * 750 + \
                                            (model.pricing.output_cost_per_1m / 1_000_000) * 250,
                "reasoning": f"Score: {score:.1f} - {model.performance_tier} tier, {model.provider} provider"
            })
        
        # Sort by score and return top recommendations
        scored_models.sort(key=lambda x: x["score"], reverse=True)
        top_recommendations = scored_models[:5]
        
        return {
            "task": request.task_description,
            "priority": request.priority,
            "budget": request.max_cost_per_request,
            "recommended_model": top_recommendations[0] if top_recommendations else None,
            "alternatives": top_recommendations[1:3],
            "total_models_evaluated": len(scored_models),
            "selection_criteria": {
                "cost_weight": 30 if request.priority == "cost" else 15,
                "capability_weight": 15,
                "context_weight": 20,
                "tier_weight": 25 if request.priority == "quality" else 10
            }
        }
    except Exception as e:
        logger.error("Failed to recommend model", error=str(e))
        raise HTTPException(status_code=500, detail=f"Model recommendation failed: {e}")


@router.post("/models/chat", response_model=Dict[str, Any])
async def chat_completion(
    request: ChatCompletionRequest,
    gateway: OpenRouterGateway = Depends(get_openrouter_gateway)
):
    """
    Enhanced chat completion with automatic usage tracking
    Supports all OpenRouter models with cost monitoring
    """
    try:
        start_time = datetime.utcnow()
        
        # Validate model exists
        catalog_manager = await get_model_catalog_manager()
        catalog = await catalog_manager.get_models()
        
        model_exists = any(m.id == request.model for m in catalog.models)
        if not model_exists:
            raise HTTPException(status_code=400, detail=f"Model {request.model} not found in catalog")
        
        # Make the chat completion
        completion = await gateway.chat_completion(
            model=request.model,
            messages=request.messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stream=request.stream
        )
        
        # Track usage if enabled
        if request.track_usage and completion.usage:
            usage_aggregator = await get_usage_aggregator()
            
            # Calculate actual cost based on usage
            model_data = next((m for m in catalog.models if m.id == request.model), None)
            if model_data:
                input_cost = (completion.usage.prompt_tokens / 1_000_000) * model_data.pricing.input_cost_per_1m
                output_cost = (completion.usage.completion_tokens / 1_000_000) * model_data.pricing.output_cost_per_1m
                total_cost = input_cost + output_cost
            else:
                total_cost = 0.0
            
            # Create usage event
            usage_event = UsageEvent(
                timestamp=start_time.timestamp(),
                model_id=request.model,
                provider=request.model.split('/')[0],
                prompt_tokens=completion.usage.prompt_tokens,
                completion_tokens=completion.usage.completion_tokens,
                total_tokens=completion.usage.total_tokens,
                cost_usd=total_cost,
                request_id=getattr(completion, 'id', 'unknown'),
                user_id=request.user_id,
                session_id=request.session_id,
                endpoint="chat_completion",
                latency_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
            )
            
            await usage_aggregator.track_usage(usage_event)
        
        return {
            "model": request.model,
            "content": completion.choices[0].message.content,
            "usage": {
                "prompt_tokens": completion.usage.prompt_tokens if completion.usage else 0,
                "completion_tokens": completion.usage.completion_tokens if completion.usage else 0,
                "total_tokens": completion.usage.total_tokens if completion.usage else 0,
                "estimated_cost_usd": total_cost if request.track_usage else None
            },
            "response_time_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
            "tracked": request.track_usage
        }
    except Exception as e:
        logger.error("Chat completion failed", model=request.model, error=str(e))
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {e}")


@router.post("/usage/track", response_model=Dict[str, str])
async def track_usage_manually(request: UsageTrackingRequest):
    """
    Manually track usage for external model calls
    Useful for tracking usage from other OpenRouter integrations
    """
    try:
        usage_aggregator = await get_usage_aggregator()
        
        usage_event = UsageEvent(
            timestamp=datetime.utcnow().timestamp(),
            model_id=request.model_id,
            provider=request.model_id.split('/')[0],
            prompt_tokens=request.prompt_tokens,
            completion_tokens=request.completion_tokens,
            total_tokens=request.prompt_tokens + request.completion_tokens,
            cost_usd=request.cost_usd,
            request_id=f"manual_{int(datetime.utcnow().timestamp())}",
            user_id=request.user_id,
            session_id=request.session_id,
            endpoint=request.endpoint or "manual",
            latency_ms=request.latency_ms
        )
        
        await usage_aggregator.track_usage(usage_event)
        
        return {
            "status": "success",
            "message": f"Tracked usage for {request.model_id}: ${request.cost_usd:.4f}"
        }
    except Exception as e:
        logger.error("Failed to track usage", error=str(e))
        raise HTTPException(status_code=500, detail=f"Usage tracking failed: {e}")


@router.get("/usage/metrics", response_model=Dict[str, Any])
async def get_usage_metrics(
    window: str = Query("day", pattern="^(hour|day|week|month)$"),
    start_date: Optional[str] = Query(None, description="ISO format date (YYYY-MM-DD)")
):
    """
    Get comprehensive usage metrics and cost analytics
    Provides real-time insights into model usage and spending
    """
    try:
        usage_aggregator = await get_usage_aggregator()
        
        # Parse time window
        time_window = TimeWindow(window)
        
        # Parse start date if provided
        start_time = None
        if start_date:
            start_time = datetime.fromisoformat(start_date)
        
        metrics = await usage_aggregator.get_usage_metrics(time_window, start_time)
        
        return {
            "window": window,
            "start_date": start_date,
            "metrics": {
                "total_requests": metrics.total_requests,
                "total_tokens": metrics.total_tokens,
                "total_cost_usd": round(metrics.total_cost_usd, 4),
                "average_tokens_per_request": round(metrics.average_tokens_per_request, 1),
                "average_cost_per_request": round(metrics.average_cost_per_request, 4),
                "average_latency_ms": round(metrics.average_latency_ms, 1),
                "unique_models": metrics.unique_models,
                "top_models": metrics.top_models[:10],
                "cost_by_model": {k: round(v, 4) for k, v in metrics.cost_by_model.items()},
                "cost_by_provider": {k: round(v, 4) for k, v in metrics.cost_by_provider.items()},
                "hourly_distribution": {k: round(v, 4) for k, v in metrics.hourly_distribution.items()}
            },
            "efficiency_insights": {
                "cost_per_token": round(metrics.total_cost_usd / metrics.total_tokens, 6) if metrics.total_tokens > 0 else 0,
                "most_efficient_model": min(metrics.cost_by_model.items(), key=lambda x: x[1])[0] if metrics.cost_by_model else None,
                "spending_trend": "increasing" if metrics.total_cost_usd > 1.0 else "stable"
            }
        }
    except Exception as e:
        logger.error("Failed to get usage metrics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve usage metrics: {e}")


@router.get("/usage/alerts", response_model=List[Dict[str, Any]])
async def get_cost_alerts(
    severity: Optional[str] = Query(None, pattern="^(info|warning|critical)$"),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get recent cost alerts and threshold violations
    Monitor spending patterns and budget overruns
    """
    try:
        usage_aggregator = await get_usage_aggregator()
        alerts = await usage_aggregator.get_alerts(severity=severity, limit=limit)
        
        return [
            {
                "id": alert.id,
                "type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "current_value": round(alert.current_value, 4),
                "threshold": round(alert.threshold, 4),
                "timestamp": alert.timestamp,
                "model_id": alert.model_id,
                "provider": alert.provider
            }
            for alert in alerts
        ]
    except Exception as e:
        logger.error("Failed to get cost alerts", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve cost alerts: {e}")


@router.post("/usage/budgets", response_model=Dict[str, str])
async def set_cost_budgets(request: CostBudgetRequest):
    """
    Set cost budget thresholds for monitoring
    Configure hourly, daily, and monthly spending limits
    """
    try:
        usage_aggregator = await get_usage_aggregator()
        
        await usage_aggregator.set_budgets(
            hourly=request.hourly_limit,
            daily=request.daily_limit,
            monthly=request.monthly_limit
        )
        
        return {
            "status": "success",
            "message": "Budget thresholds updated successfully"
        }
    except Exception as e:
        logger.error("Failed to set budgets", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to set budgets: {e}")


@router.get("/models/providers", response_model=Dict[str, Any])
async def get_model_providers():
    """
    Get summary of model providers and their offerings
    Quick overview of available AI providers
    """
    try:
        catalog_manager = await get_model_catalog_manager()
        provider_stats = await catalog_manager.get_provider_stats()
        
        # Get sample models for each provider
        provider_details = {}
        for provider, count in provider_stats.items():
            models = await catalog_manager.get_models_by_provider(provider)
            if models:
                cheapest = min(models, key=lambda m: m.pricing.input_cost_per_1m)
                most_expensive = max(models, key=lambda m: m.pricing.input_cost_per_1m)
                
                provider_details[provider] = {
                    "total_models": count,
                    "cheapest_model": {
                        "id": cheapest.id,
                        "cost_per_1m": cheapest.pricing.input_cost_per_1m
                    },
                    "premium_model": {
                        "id": most_expensive.id,
                        "cost_per_1m": most_expensive.pricing.input_cost_per_1m
                    },
                    "capabilities": list(set().union(*[m.capabilities for m in models[:5]]))
                }
        
        return {
            "total_providers": len(provider_stats),
            "provider_stats": provider_stats,
            "provider_details": provider_details,
            "recommendations": {
                "cost_conscious": "anthropic",  # Often has good Haiku models
                "premium_quality": "openai",    # GPT-4 variants
                "open_source": "meta-llama",   # Llama models
                "balanced": "google"           # Gemini models
            }
        }
    except Exception as e:
        logger.error("Failed to get provider info", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve provider information: {e}")


@router.post("/models/cache/invalidate", response_model=Dict[str, str])
async def invalidate_model_cache():
    """
    Manually invalidate model catalog cache
    Force refresh of model data from OpenRouter
    """
    try:
        catalog_manager = await get_model_catalog_manager()
        await catalog_manager.invalidate_cache()
        
        return {
            "status": "success", 
            "message": "Model catalog cache invalidated"
        }
    except Exception as e:
        logger.error("Failed to invalidate cache", error=str(e))
        raise HTTPException(status_code=500, detail=f"Cache invalidation failed: {e}")


@router.get("/usage/cost/current", response_model=Dict[str, float])
async def get_current_costs():
    """
    Get current spending across different time windows
    Real-time cost monitoring dashboard data
    """
    try:
        usage_aggregator = await get_usage_aggregator()
        
        hourly_cost = await usage_aggregator.get_cost_for_period(TimeWindow.HOUR)
        daily_cost = await usage_aggregator.get_cost_for_period(TimeWindow.DAY)
        weekly_cost = await usage_aggregator.get_cost_for_period(TimeWindow.WEEK)
        monthly_cost = await usage_aggregator.get_cost_for_period(TimeWindow.MONTH)
        
        return {
            "hourly_cost_usd": round(hourly_cost, 4),
            "daily_cost_usd": round(daily_cost, 4),
            "weekly_cost_usd": round(weekly_cost, 4),
            "monthly_cost_usd": round(monthly_cost, 4),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error("Failed to get current costs", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve current costs: {e}")