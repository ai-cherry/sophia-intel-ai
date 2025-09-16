"""
Sophia AI Fusion Systems - OpenRouter Integration
Week 3: Essential Integrations Implementation
Multi-model AI routing with cost optimization, intelligent model selection,
and comprehensive usage tracking. Integrates with existing performance monitoring.
"""
import asyncio
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import aiohttp
try:
    from app.api.services.intelligent_cache import cached  # lightweight shim
except Exception:  # pragma: no cover
    def cached(func):  # type: ignore
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
try:
    from app.api.services.performance_monitor import monitor_performance
except Exception:
    def monitor_performance(*args, **kwargs):  # type: ignore
        def deco(func):
            return func
        return deco
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class ModelTier(Enum):
    """Model performance and cost tiers"""
    FAST = "fast"  # Low cost, fast response
    BALANCED = "balanced"  # Medium cost, good quality
    PREMIUM = "premium"  # High cost, best quality
@dataclass
class ModelConfig:
    """Configuration for an OpenRouter model"""
    model_id: str
    name: str
    tier: ModelTier
    cost_per_1k_tokens: float
    max_tokens: int
    context_window: int
    supports_streaming: bool = True
    supports_function_calling: bool = False
    recommended_use_cases: List[str] = None
@dataclass
class UsageStats:
    """Usage statistics for OpenRouter integration"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    avg_response_time_ms: float = 0.0
    models_used: Dict[str, int] = None
    last_request_time: str = ""
class OpenRouterIntegration:
    """
    Advanced OpenRouter integration with intelligent model routing and cost optimization
    """
    def __init__(self, api_key: str, base_url: str = "https://api.portkey.ai/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        # Usage tracking
        self.usage_stats = UsageStats(models_used={})
        # Model configurations
        self.models = {
            # Fast tier - optimized for speed and cost
            "anthropic/claude-3-haiku": ModelConfig(
                model_id="anthropic/claude-3-haiku",
                name="Claude 3 Haiku",
                tier=ModelTier.FAST,
                cost_per_1k_tokens=0.25,
                max_tokens=4096,
                context_window=200000,
                recommended_use_cases=[
                    "quick_responses",
                    "simple_queries",
                    "classification",
                ],
            ),
            "meta-llama/llama-3.1-8b-instruct": ModelConfig(
                model_id="meta-llama/llama-3.1-8b-instruct",
                name="Llama 3.1 8B",
                tier=ModelTier.FAST,
                cost_per_1k_tokens=0.18,
                max_tokens=2048,
                context_window=131072,
                recommended_use_cases=["general_purpose", "coding", "analysis"],
            ),
            # Balanced tier - good quality/cost ratio
            "anthropic/claude-3-sonnet": ModelConfig(
                model_id="anthropic/claude-3-sonnet",
                name="Claude 3 Sonnet",
                tier=ModelTier.BALANCED,
                cost_per_1k_tokens=3.0,
                max_tokens=4096,
                context_window=200000,
                recommended_use_cases=["complex_reasoning", "writing", "research"],
            ),
            "openai/gpt-4o-mini": ModelConfig(
                model_id="openai/gpt-4o-mini",
                name="GPT-4o Mini",
                tier=ModelTier.BALANCED,
                cost_per_1k_tokens=0.15,
                max_tokens=16384,
                context_window=128000,
                supports_function_calling=True,
                recommended_use_cases=[
                    "function_calling",
                    "structured_output",
                    "reasoning",
                ],
            ),
            # Premium tier - highest quality
            "anthropic/claude-3-opus": ModelConfig(
                model_id="anthropic/claude-3-opus",
                name="Claude 3 Opus",
                tier=ModelTier.PREMIUM,
                cost_per_1k_tokens=15.0,
                max_tokens=4096,
                context_window=200000,
                recommended_use_cases=[
                    "complex_analysis",
                    "creative_writing",
                    "expert_reasoning",
                ],
            ),
            "openai/gpt-4": ModelConfig(
                model_id="openai/gpt-4",
                name="GPT-4",
                tier=ModelTier.PREMIUM,
                cost_per_1k_tokens=30.0,
                max_tokens=8192,
                context_window=8192,
                supports_function_calling=True,
                recommended_use_cases=[
                    "complex_reasoning",
                    "code_generation",
                    "expert_analysis",
                ],
            ),
        }
        # Routing rules
        self.routing_rules = {
            "default": "anthropic/claude-3-haiku",
            "fast": "meta-llama/llama-3.1-8b-instruct",
            "balanced": "anthropic/claude-3-sonnet",
            "premium": "anthropic/claude-3-opus",
            "function_calling": "openai/gpt-4o-mini",
            "coding": "meta-llama/llama-3.1-8b-instruct",
            "analysis": "anthropic/claude-3-sonnet",
            "creative": "anthropic/claude-3-opus",
        }
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
    async def connect(self):
        """Initialize HTTP session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=60, connect=10)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "x-portkey-api-key": self.api_key,
                    "x-portkey-provider": "openrouter",
                    "Content-Type": "application/json",
                },
            )
            logger.info("✅ OpenRouter via Portkey session initialized")
    async def disconnect(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("🔌 OpenRouter session closed")
    def select_model(
        self,
        use_case: str = "default",
        max_cost_per_1k: Optional[float] = None,
        require_function_calling: bool = False,
        prefer_speed: bool = False,
    ) -> str:
        """
        Intelligently select the best model based on requirements
        """
        # Start with use case routing
        if use_case in self.routing_rules:
            candidate = self.routing_rules[use_case]
        else:
            candidate = self.routing_rules["default"]
        # Apply constraints
        available_models = list(self.models.keys())
        # Filter by cost constraint
        if max_cost_per_1k:
            available_models = [
                m
                for m in available_models
                if self.models[m].cost_per_1k_tokens <= max_cost_per_1k
            ]
        # Filter by function calling requirement
        if require_function_calling:
            available_models = [
                m for m in available_models if self.models[m].supports_function_calling
            ]
        # If candidate doesn't meet constraints, find alternative
        if candidate not in available_models:
            if not available_models:
                logger.warning("⚠️ No models meet constraints, using default")
                return self.routing_rules["default"]
            # Sort by preference
            if prefer_speed:
                # Prefer fast tier, then by cost
                available_models.sort(
                    key=lambda m: (
                        self.models[m].tier != ModelTier.FAST,
                        self.models[m].cost_per_1k_tokens,
                    )
                )
            else:
                # Prefer balanced tier, then by cost
                available_models.sort(
                    key=lambda m: (
                        self.models[m].tier != ModelTier.BALANCED,
                        self.models[m].cost_per_1k_tokens,
                    )
                )
            candidate = available_models[0]
        logger.info(
            f"🎯 Selected model: {self.models[candidate].name} for use case: {use_case}"
        )
        return candidate
    @cached(ttl=300, prefix="openrouter_models")
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from OpenRouter"""
        try:
            async with self.session.get(f"{self.base_url}/models") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
                else:
                    logger.error(f"❌ Failed to fetch models: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"❌ Error fetching models: {e}")
            return []
    @monitor_performance("/openrouter/chat", "POST")
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        use_case: str = "default",
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        stream: bool = False,
        functions: Optional[List[Dict]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a chat completion with intelligent model routing
        """
        start_time = time.time()
        try:
            # Select model if not specified
            if not model:
                model = self.select_model(
                    use_case=use_case,
                    require_function_calling=bool(functions),
                    prefer_speed=stream,
                )
            # Get model config
            model_config = self.models.get(model)
            if not model_config:
                raise ValueError(f"Unknown model: {model}")
            # Prepare request
            request_data = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": stream,
                **kwargs,
            }
            # Set max_tokens if not specified
            if max_tokens:
                request_data["max_tokens"] = min(max_tokens, model_config.max_tokens)
            else:
                request_data["max_tokens"] = model_config.max_tokens
            # Add functions if supported
            if functions and model_config.supports_function_calling:
                request_data["functions"] = functions
            elif functions:
                logger.warning(f"⚠️ Model {model} doesn't support function calling")
            # Make request
            async with self.session.post(
                f"{self.base_url}/chat/completions", json=request_data
            ) as response:
                response_time = (time.time() - start_time) * 1000
                if response.status == 200:
                    result = await response.json()
                    # Track usage
                    await self._track_usage(model, result, response_time, success=True)
                    logger.info(f"✅ Chat completion: {model} ({response_time:.1f}ms)")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"❌ OpenRouter error {response.status}: {error_text}")
                    # Track failed usage
                    await self._track_usage(model, None, response_time, success=False)
                    return {
                        "error": {
                            "status": response.status,
                            "message": error_text,
                            "model": model,
                        }
                    }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"❌ Chat completion error: {e}")
            # Track failed usage
            await self._track_usage(
                model or "unknown", None, response_time, success=False
            )
            return {"error": {"message": str(e), "model": model}}
    async def _track_usage(
        self, model: str, result: Optional[Dict], response_time: float, success: bool
    ):
        """Track usage statistics"""
        self.usage_stats.total_requests += 1
        if success:
            self.usage_stats.successful_requests += 1
            if result and "usage" in result:
                usage = result["usage"]
                tokens_used = usage.get("total_tokens", 0)
                self.usage_stats.total_tokens_used += tokens_used
                # Calculate cost
                model_config = self.models.get(model)
                if model_config:
                    cost = (tokens_used / 1000) * model_config.cost_per_1k_tokens
                    self.usage_stats.total_cost_usd += cost
            # Track model usage
            if model not in self.usage_stats.models_used:
                self.usage_stats.models_used[model] = 0
            self.usage_stats.models_used[model] += 1
        else:
            self.usage_stats.failed_requests += 1
        # Update average response time
        alpha = 0.1  # Smoothing factor
        if self.usage_stats.avg_response_time_ms == 0:
            self.usage_stats.avg_response_time_ms = response_time
        else:
            self.usage_stats.avg_response_time_ms = (
                alpha * response_time
                + (1 - alpha) * self.usage_stats.avg_response_time_ms
            )
        self.usage_stats.last_request_time = datetime.now().isoformat()
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        stats = asdict(self.usage_stats)
        # Add derived metrics
        if self.usage_stats.total_requests > 0:
            stats["success_rate"] = (
                self.usage_stats.successful_requests / self.usage_stats.total_requests
            ) * 100
        else:
            stats["success_rate"] = 0.0
        # Add cost efficiency metrics
        if self.usage_stats.total_tokens_used > 0:
            stats["cost_per_token"] = (
                self.usage_stats.total_cost_usd / self.usage_stats.total_tokens_used
            )
            stats["tokens_per_request"] = self.usage_stats.total_tokens_used / max(
                self.usage_stats.successful_requests, 1
            )
        else:
            stats["cost_per_token"] = 0.0
            stats["tokens_per_request"] = 0.0
        return stats
    async def get_model_recommendations(self, use_case: str) -> List[Dict[str, Any]]:
        """Get model recommendations for a specific use case"""
        recommendations = []
        for model_id, config in self.models.items():
            if (
                not config.recommended_use_cases
                or use_case in config.recommended_use_cases
            ):
                score = 100  # Base score
                # Adjust score based on tier and use case
                if use_case in ["quick_responses", "simple_queries"]:
                    if config.tier == ModelTier.FAST:
                        score += 20
                elif use_case in ["complex_reasoning", "expert_analysis"]:
                    if config.tier == ModelTier.PREMIUM:
                        score += 20
                else:
                    if config.tier == ModelTier.BALANCED:
                        score += 20
                # Adjust for cost efficiency
                score -= config.cost_per_1k_tokens * 2
                recommendations.append(
                    {
                        "model_id": model_id,
                        "name": config.name,
                        "tier": config.tier.value,
                        "cost_per_1k_tokens": config.cost_per_1k_tokens,
                        "score": max(0, score),
                        "recommended_for": config.recommended_use_cases or [],
                    }
                )
        # Sort by score
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:5]  # Top 5 recommendations
    async def health_check(self) -> Dict[str, Any]:
        """Perform OpenRouter integration health check"""
        health_status = {
            "status": "healthy",
            "session_active": self.session is not None,
            "models_configured": len(self.models),
            "total_requests": self.usage_stats.total_requests,
            "success_rate": 0.0,
            "avg_response_time_ms": self.usage_stats.avg_response_time_ms,
            "total_cost_usd": self.usage_stats.total_cost_usd,
            "last_updated": datetime.now().isoformat(),
        }
        # Calculate success rate
        if self.usage_stats.total_requests > 0:
            health_status["success_rate"] = (
                self.usage_stats.successful_requests / self.usage_stats.total_requests
            ) * 100
        # Test API connectivity
        try:
            if self.session:
                async with self.session.get(
                    f"{self.base_url}/models", timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        health_status["api_connectivity"] = "success"
                    else:
                        health_status["api_connectivity"] = f"error_{response.status}"
                        health_status["status"] = "degraded"
            else:
                health_status["api_connectivity"] = "no_session"
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["api_connectivity"] = f"failed: {e}"
            health_status["status"] = "unhealthy"
        return health_status
# Global OpenRouter instance
_openrouter_instance: Optional[OpenRouterIntegration] = None
async def get_openrouter(api_key: str) -> OpenRouterIntegration:
    """Get or create global OpenRouter instance"""
    global _openrouter_instance
    if _openrouter_instance is None:
        _openrouter_instance = OpenRouterIntegration(api_key)
        await _openrouter_instance.connect()
    return _openrouter_instance
# Example usage and testing
async def sophia_openrouter_integration():
    """Test the OpenRouter integration"""
    print("🧪 Testing OpenRouter Integration...")
    # Note: This requires a valid API key
    api_key = "your-openrouter-api-key"  # Replace with actual key
    async with OpenRouterIntegration(api_key) as openrouter:
        # Test model selection
        model = openrouter.select_model(use_case="coding", prefer_speed=True)
        print(f"✅ Selected model for coding: {openrouter.models[model].name}")
        # Test model recommendations
        recommendations = await openrouter.get_model_recommendations("analysis")
        print(f"✅ Got {len(recommendations)} recommendations for analysis")
        # Test health check
        health = await openrouter.health_check()
        print(f"🏥 Health check: {health['status']}")
        # Test usage stats
        stats = await openrouter.get_usage_stats()
        print(f"📊 Usage stats: {stats['total_requests']} requests")
    return True
if __name__ == "__main__":
    asyncio.run(sophia_openrouter_integration())
