"""
Model Registry API endpoints for Visual Model Registry interface.
Provides provider health monitoring, cost analytics, and virtual key management.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app.api.portkey_unified_router import RoutingStrategy, unified_router
from app.core.portkey_config import AgentRole, ModelProvider, PortkeyManager

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/model-registry", tags=["model-registry"])


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass


manager = ConnectionManager()


# Pydantic models
class ProviderHealthStatus(BaseModel):
    provider: str = Field(..., description="Provider name")
    status: str = Field(..., description="Health status: active, degraded, offline")
    last_success: datetime = Field(..., description="Last successful request timestamp")
    success_rate: float = Field(..., description="Success rate percentage (0-100)")
    avg_latency_ms: float = Field(..., description="Average response latency in milliseconds")
    error_count: int = Field(..., description="Recent error count")
    cost_per_1k_tokens: float = Field(..., description="Cost per 1000 tokens in USD")


class VirtualKeyConfig(BaseModel):
    provider: str = Field(..., description="Provider name")
    virtual_key: str = Field(..., description="Virtual key identifier")
    models: List[str] = Field(..., description="Available models for this provider")
    fallback_providers: List[str] = Field(..., description="Fallback provider chain")
    max_tokens: int = Field(default=4096, description="Maximum tokens per request")
    temperature: float = Field(default=0.7, description="Default temperature setting")
    retry_count: int = Field(default=3, description="Retry attempts on failure")


class CostAnalytics(BaseModel):
    daily_cost: float = Field(..., description="Total cost today in USD")
    weekly_cost: float = Field(..., description="Total cost this week in USD")
    monthly_cost: float = Field(..., description="Total cost this month in USD")
    cost_by_provider: Dict[str, float] = Field(..., description="Cost breakdown by provider")
    token_usage: Dict[str, int] = Field(..., description="Token usage by provider")
    request_count: int = Field(..., description="Total requests today")


class FallbackChainConfig(BaseModel):
    primary_provider: str = Field(..., description="Primary provider")
    fallback_chain: List[str] = Field(..., description="Ordered fallback provider list")
    load_balance_weights: Dict[str, float] = Field(
        default_factory=dict, description="Load balancing weights"
    )
    routing_strategy: str = Field(default="balanced", description="Routing strategy")


class ModelTestRequest(BaseModel):
    provider: str = Field(..., description="Provider to test")
    model: Optional[str] = Field(None, description="Specific model to test")
    test_message: str = Field(default="Test connection", description="Test message")


class PerformanceMetrics(BaseModel):
    provider: str = Field(..., description="Provider name")
    latency_p50: float = Field(..., description="50th percentile latency in ms")
    latency_p95: float = Field(..., description="95th percentile latency in ms")
    latency_p99: float = Field(..., description="99th percentile latency in ms")
    throughput_rpm: int = Field(..., description="Requests per minute")
    error_rate: float = Field(..., description="Error rate percentage")
    uptime_percentage: float = Field(..., description="Uptime percentage last 24h")


# Initialize portkey manager
portkey_manager = PortkeyManager()


@router.get("/providers", response_model=List[ProviderHealthStatus])
async def get_provider_health():
    """Get health status for all configured providers."""
    try:
        provider_statuses = []

        for provider in ModelProvider:
            try:
                # Test connection
                is_healthy = portkey_manager.test_connection(provider)
                config = portkey_manager.providers[provider]

                # Get metrics from router if available
                metrics = None
                if hasattr(unified_router, "model_registry"):
                    models = config.models
                    if models:
                        model_key = models[0]  # Use first model for metrics
                        metrics = unified_router.model_registry.get(model_key)

                # Calculate status
                status = "active" if is_healthy else "offline"
                if metrics and metrics.success_rate < 0.8:
                    status = "degraded"

                # Estimate cost per 1k tokens based on provider
                cost_estimates = {
                    ModelProvider.OPENAI: 0.03,
                    ModelProvider.ANTHROPIC: 0.015,
                    ModelProvider.DEEPSEEK: 0.0014,
                    ModelProvider.PERPLEXITY: 0.001,
                    ModelProvider.GROQ: 0.0002,
                    ModelProvider.MISTRAL: 0.0025,
                    ModelProvider.GEMINI: 0.00125,
                    ModelProvider.XAI: 0.005,
                    ModelProvider.TOGETHER: 0.0002,
                    ModelProvider.COHERE: 0.015,
                    ModelProvider.HUGGINGFACE: 0.0005,
                    ModelProvider.OPENROUTER: 0.002,
                }

                provider_status = ProviderHealthStatus(
                    provider=provider.value,
                    status=status,
                    last_success=metrics.last_success if metrics else datetime.now(),
                    success_rate=(
                        (metrics.success_rate * 100) if metrics else (95.0 if is_healthy else 0.0)
                    ),
                    avg_latency_ms=(
                        metrics.avg_latency_ms if metrics else (1000.0 if is_healthy else 0.0)
                    ),
                    error_count=metrics.error_count if metrics else (0 if is_healthy else 10),
                    cost_per_1k_tokens=cost_estimates.get(provider, 0.002),
                )
                provider_statuses.append(provider_status)

            except Exception as e:
                logger.error(f"Error checking provider {provider.value}: {e}")
                # Add offline status for failed providers
                provider_statuses.append(
                    ProviderHealthStatus(
                        provider=provider.value,
                        status="offline",
                        last_success=datetime.now() - timedelta(hours=1),
                        success_rate=0.0,
                        avg_latency_ms=0.0,
                        error_count=999,
                        cost_per_1k_tokens=0.002,
                    )
                )

        return provider_statuses

    except Exception as e:
        logger.error(f"Error getting provider health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get provider health: {str(e)}")


@router.get("/virtual-keys", response_model=List[VirtualKeyConfig])
async def get_virtual_keys():
    """Get all virtual key configurations."""
    try:
        virtual_keys = []

        for provider, config in portkey_manager.providers.items():
            virtual_key = VirtualKeyConfig(
                provider=provider.value,
                virtual_key=config.virtual_key,
                models=config.models,
                fallback_providers=[p.value for p in config.fallback_providers],
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                retry_count=config.retry_count,
            )
            virtual_keys.append(virtual_key)

        return virtual_keys

    except Exception as e:
        logger.error(f"Error getting virtual keys: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get virtual keys: {str(e)}")


@router.post("/virtual-keys/{provider}")
async def update_virtual_key(provider: str, config: VirtualKeyConfig):
    """Update virtual key configuration for a provider."""
    try:
        provider_enum = ModelProvider(provider.lower())

        # Update the provider configuration
        portkey_manager.providers[provider_enum].virtual_key = config.virtual_key
        portkey_manager.providers[provider_enum].models = config.models
        portkey_manager.providers[provider_enum].max_tokens = config.max_tokens
        portkey_manager.providers[provider_enum].temperature = config.temperature
        portkey_manager.providers[provider_enum].retry_count = config.retry_count

        # Update fallback providers
        fallback_providers = []
        for fallback in config.fallback_providers:
            try:
                fallback_enum = ModelProvider(fallback.lower())
                fallback_providers.append(fallback_enum)
            except ValueError:
                logger.warning(f"Invalid fallback provider: {fallback}")

        portkey_manager.providers[provider_enum].fallback_providers = fallback_providers

        return {"message": f"Virtual key updated for {provider}", "success": True}

    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
    except Exception as e:
        logger.error(f"Error updating virtual key: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update virtual key: {str(e)}")


@router.get("/cost-analytics", response_model=CostAnalytics)
async def get_cost_analytics():
    """Get cost analytics and usage statistics."""
    try:
        # Get analytics from unified router
        analytics = await unified_router.get_routing_analytics()

        # Calculate weekly and monthly costs (mock data for now)
        daily_cost = analytics.get("daily_cost", 0.0)
        weekly_cost = daily_cost * 7  # Simplified calculation
        monthly_cost = daily_cost * 30  # Simplified calculation

        # Cost breakdown by provider
        cost_by_provider = {}
        token_usage = {}

        model_stats = analytics.get("model_statistics", {})
        for model, stats in model_stats.items():
            # Extract provider from model name
            provider = model.split("/")[0] if "/" in model else "unknown"
            requests = stats.get("requests", 0)
            cost_per_token = stats.get("cost_per_token", 0.002)

            # Estimate tokens (rough calculation)
            estimated_tokens = requests * 1000  # Assume 1k tokens per request
            cost = estimated_tokens * cost_per_token

            cost_by_provider[provider] = cost_by_provider.get(provider, 0.0) + cost
            token_usage[provider] = token_usage.get(provider, 0) + estimated_tokens

        return CostAnalytics(
            daily_cost=daily_cost,
            weekly_cost=weekly_cost,
            monthly_cost=monthly_cost,
            cost_by_provider=cost_by_provider,
            token_usage=token_usage,
            request_count=analytics.get("total_requests", 0),
        )

    except Exception as e:
        logger.error(f"Error getting cost analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cost analytics: {str(e)}")


@router.get("/fallback-chains", response_model=Dict[str, FallbackChainConfig])
async def get_fallback_chains():
    """Get current fallback chain configurations."""
    try:
        fallback_chains = {}

        for provider, config in portkey_manager.providers.items():
            chain_config = FallbackChainConfig(
                primary_provider=provider.value,
                fallback_chain=[p.value for p in config.fallback_providers],
                routing_strategy="balanced",
            )
            fallback_chains[provider.value] = chain_config

        return fallback_chains

    except Exception as e:
        logger.error(f"Error getting fallback chains: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get fallback chains: {str(e)}")


@router.post("/fallback-chains/{provider}")
async def update_fallback_chain(provider: str, config: FallbackChainConfig):
    """Update fallback chain configuration for a provider."""
    try:
        provider_enum = ModelProvider(provider.lower())

        # Update fallback providers
        fallback_providers = []
        for fallback in config.fallback_chain:
            try:
                fallback_enum = ModelProvider(fallback.lower())
                fallback_providers.append(fallback_enum)
            except ValueError:
                logger.warning(f"Invalid fallback provider: {fallback}")

        portkey_manager.providers[provider_enum].fallback_providers = fallback_providers

        return {"message": f"Fallback chain updated for {provider}", "success": True}

    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
    except Exception as e:
        logger.error(f"Error updating fallback chain: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update fallback chain: {str(e)}")


@router.post("/test-model", response_model=Dict[str, Any])
async def test_model(request: ModelTestRequest):
    """Test a specific model/provider connection."""
    try:
        provider_enum = ModelProvider(request.provider.lower())

        # Test the connection
        is_healthy = portkey_manager.test_connection(provider_enum)

        result = {
            "provider": request.provider,
            "model": request.model,
            "healthy": is_healthy,
            "timestamp": datetime.now().isoformat(),
            "test_message": request.test_message,
        }

        if is_healthy:
            result["status"] = "Connection successful"
            result["latency_ms"] = 1200  # Mock latency
        else:
            result["status"] = "Connection failed"
            result["error"] = "Unable to connect to provider"

        return result

    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {request.provider}")
    except Exception as e:
        logger.error(f"Error testing model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test model: {str(e)}")


@router.get("/performance-metrics", response_model=List[PerformanceMetrics])
async def get_performance_metrics():
    """Get performance metrics for all providers."""
    try:
        metrics = []

        for provider in ModelProvider:
            # Mock performance metrics (in real implementation, get from monitoring system)
            provider_metrics = PerformanceMetrics(
                provider=provider.value,
                latency_p50=800.0,
                latency_p95=2000.0,
                latency_p99=5000.0,
                throughput_rpm=120,
                error_rate=2.5,
                uptime_percentage=99.5,
            )
            metrics.append(provider_metrics)

        return metrics

    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")


@router.get("/routing-strategies")
async def get_routing_strategies():
    """Get available routing strategies."""
    return {
        "strategies": [
            {
                "name": "cost_optimized",
                "display_name": "Cost Optimized",
                "description": "Prioritize lowest cost providers",
            },
            {
                "name": "performance_first",
                "display_name": "Performance First",
                "description": "Prioritize fastest, most reliable providers",
            },
            {
                "name": "balanced",
                "display_name": "Balanced",
                "description": "Balance cost, performance, and reliability",
            },
            {
                "name": "fastest_available",
                "display_name": "Fastest Available",
                "description": "Route to fastest responding provider",
            },
            {
                "name": "highest_quality",
                "display_name": "Highest Quality",
                "description": "Route to highest quality models",
            },
        ]
    }


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates every 30 seconds
            await asyncio.sleep(30)

            # Get current provider health
            provider_health = await get_provider_health()

            # Send update to client
            await manager.send_personal_message(
                json.dumps(
                    {
                        "type": "provider_health_update",
                        "data": [status.dict() for status in provider_health],
                        "timestamp": datetime.now().isoformat(),
                    }
                ),
                websocket,
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# Background task to broadcast updates
async def broadcast_updates():
    """Background task to broadcast periodic updates to all connected clients."""
    while True:
        try:
            await asyncio.sleep(60)  # Update every minute

            # Get current analytics
            analytics = await get_cost_analytics()

            # Broadcast to all connected clients
            await manager.broadcast(
                {
                    "type": "cost_analytics_update",
                    "data": analytics.dict(),
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            logger.error(f"Error in broadcast updates: {e}")


# Start background task when router is loaded
@router.on_event("startup")
async def startup_event():
    """Initialize router on startup."""
    try:
        # Initialize unified router if not already done
        if not unified_router.session:
            await unified_router.initialize()

        logger.info("Model Registry API router initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize Model Registry router: {e}")
