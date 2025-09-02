"""
FastAPI endpoints for Portkey Unified Router
Provides HTTP API for routing and analytics
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.portkey_unified_router import ModelTier, RouteConfig, RoutingStrategy, unified_router
from app.swarms.agno_teams import ExecutionStrategy

router = APIRouter(prefix="/portkey-routing", tags=["portkey", "routing"])


# Request/Response Models
class RouteSelectionRequest(BaseModel):
    agent_role: str
    task_complexity: float = 0.5
    execution_strategy: str = "balanced"
    routing_strategy: str | None = "balanced"
    max_cost_per_request: float | None = 0.05
    fallback_enabled: bool = True
    cache_enabled: bool = True


class CompletionRequest(BaseModel):
    messages: list[dict[str, str]]
    agent_role: str
    task_complexity: float = 0.5
    execution_strategy: str = "balanced"
    routing_config: dict[str, Any] | None = None
    temperature: float | None = None
    max_tokens: int | None = None


class RouteSelectionResponse(BaseModel):
    selected_model: str
    primary_model: str
    agent_role: str
    execution_strategy: str
    routing_strategy: str
    task_complexity: float
    model_tier: str
    fallback_models: list[str]
    routing_metadata: dict[str, Any]


class CompletionResponse(BaseModel):
    content: str
    model_used: str
    completion_time_ms: float
    attempt: int
    routing_decision: dict[str, Any]
    success: bool


class AnalyticsResponse(BaseModel):
    daily_cost: float
    total_requests: int
    cache_hit_rate: float
    model_statistics: dict[str, Any]
    routing_cache_size: int
    timestamp: str


async def get_router():
    """Dependency to get initialized router"""
    if not unified_router.session:
        await unified_router.initialize()
    return unified_router


@router.post("/select-model", response_model=RouteSelectionResponse)
async def select_optimal_model(
    request: RouteSelectionRequest,
    router_instance = Depends(get_router)
):
    """
    Select optimal model for given role and parameters
    """
    try:
        # Parse execution strategy
        try:
            execution_strategy = ExecutionStrategy(request.execution_strategy.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid execution strategy: {request.execution_strategy}"
            )

        # Parse routing strategy
        routing_strategy = RoutingStrategy.BALANCED
        if request.routing_strategy:
            try:
                routing_strategy = RoutingStrategy(request.routing_strategy.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid routing strategy: {request.routing_strategy}"
                )

        # Build route config
        route_config = RouteConfig(
            strategy=routing_strategy,
            max_cost_per_request=request.max_cost_per_request,
            fallback_enabled=request.fallback_enabled,
            cache_enabled=request.cache_enabled
        )

        # Get routing decision
        result = await router_instance.select_optimal_model(
            agent_role=request.agent_role,
            task_complexity=request.task_complexity,
            execution_strategy=execution_strategy,
            route_config=route_config
        )

        return RouteSelectionResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model selection failed: {str(e)}")


@router.post("/completion", response_model=CompletionResponse)
async def route_completion(
    request: CompletionRequest,
    router_instance = Depends(get_router)
):
    """
    Route completion request through optimal model
    """
    try:
        # Parse execution strategy
        try:
            execution_strategy = ExecutionStrategy(request.execution_strategy.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid execution strategy: {request.execution_strategy}"
            )

        # Build route config from request
        route_config = None
        if request.routing_config:
            route_config = RouteConfig(**request.routing_config)

        # Route completion
        result = await router_instance.route_completion(
            messages=request.messages,
            agent_role=request.agent_role,
            task_complexity=request.task_complexity,
            execution_strategy=execution_strategy,
            route_config=route_config,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        return CompletionResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Completion routing failed: {str(e)}")


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_routing_analytics(router_instance = Depends(get_router)):
    """
    Get routing and usage analytics
    """
    try:
        analytics = await router_instance.get_routing_analytics()
        return AnalyticsResponse(**analytics)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics retrieval failed: {str(e)}")


@router.get("/models")
async def list_approved_models():
    """
    List all approved models with their configurations
    """
    from app.elite_portkey_config import EliteAgentConfig
    from app.swarms.agno_teams import SophiaAGNOTeam

    config = EliteAgentConfig()

    models_info = {}
    for role, model in SophiaAGNOTeam.APPROVED_MODELS.items():
        models_info[role] = {
            "model": model,
            "temperature": config.TEMPERATURES.get(role, 0.5),
            "max_tokens": config.MAX_TOKENS.get(role, 4000),
            "purpose": role.replace("_", " ").title()
        }

    return {
        "approved_models": models_info,
        "total_models": len(models_info),
        "strategies": [strategy.value for strategy in ExecutionStrategy],
        "routing_strategies": [strategy.value for strategy in RoutingStrategy],
        "model_tiers": [tier.value for tier in ModelTier]
    }


@router.get("/health")
async def health_check():
    """
    Check Portkey routing system health
    """
    try:
        if not unified_router.session:
            await unified_router.initialize()

        # Check if we have models registered
        model_count = len(unified_router.model_registry)
        cache_size = len(unified_router.routing_cache)

        return {
            "status": "healthy",
            "models_registered": model_count,
            "cache_size": cache_size,
            "virtual_keys_configured": len(unified_router.VIRTUAL_KEYS),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.post("/cache/clear")
async def clear_routing_cache(router_instance = Depends(get_router)):
    """
    Clear the routing cache
    """
    try:
        cache_size_before = len(router_instance.routing_cache)
        router_instance.routing_cache.clear()

        return {
            "success": True,
            "cleared_entries": cache_size_before,
            "message": f"Cleared {cache_size_before} cache entries"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")


@router.get("/usage/{model}")
async def get_model_usage(model: str, router_instance = Depends(get_router)):
    """
    Get usage statistics for a specific model
    """
    if model not in router_instance.model_registry:
        raise HTTPException(status_code=404, detail=f"Model {model} not found")

    metrics = router_instance.model_registry[model]

    return {
        "model": model,
        "avg_latency_ms": metrics.avg_latency_ms,
        "success_rate": metrics.success_rate,
        "cost_per_token": metrics.cost_per_token,
        "requests_per_minute": metrics.requests_per_minute,
        "error_count": metrics.error_count,
        "last_success": metrics.last_success.isoformat(),
        "total_requests": router_instance.request_counts.get(model, 0)
    }


# Add routing info endpoint
@router.get("/routing-strategies")
async def get_routing_strategies():
    """
    Get available routing strategies and their descriptions
    """
    strategies = {
        RoutingStrategy.COST_OPTIMIZED.value: {
            "name": "Cost Optimized",
            "description": "Prioritizes cheapest models while maintaining quality",
            "weight_factors": "70% cost, 20% performance, 10% availability"
        },
        RoutingStrategy.PERFORMANCE_FIRST.value: {
            "name": "Performance First",
            "description": "Prioritizes fastest and most reliable models",
            "weight_factors": "80% performance, 10% cost, 10% availability"
        },
        RoutingStrategy.BALANCED.value: {
            "name": "Balanced",
            "description": "Balanced approach considering all factors",
            "weight_factors": "40% performance, 30% cost, 30% availability"
        },
        RoutingStrategy.FASTEST_AVAILABLE.value: {
            "name": "Fastest Available",
            "description": "Prioritizes lowest latency models",
            "weight_factors": "60% latency, 30% availability, 10% cost"
        },
        RoutingStrategy.HIGHEST_QUALITY.value: {
            "name": "Highest Quality",
            "description": "Prioritizes premium models for complex tasks",
            "weight_factors": "50% performance, 30% availability, 20% cost + tier bonus"
        }
    }

    return {
        "strategies": strategies,
        "default": RoutingStrategy.BALANCED.value,
        "total_strategies": len(strategies)
    }
