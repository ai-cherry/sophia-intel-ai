"""
Portkey Unified Router for AGNO Teams
Implements intelligent routing, load balancing, and cost optimization
"""

import asyncio
import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

import aiohttp
from fastapi import HTTPException

from app.core.circuit_breaker import with_circuit_breaker
from app.elite_portkey_config import EliteAgentConfig, EliteOptimizations, ElitePortkeyGateway


# Import ExecutionStrategy locally to avoid circular import
class ExecutionStrategy(Enum):
    """Swarm execution strategies"""

    LITE = "lite"
    BALANCED = "balanced"
    QUALITY = "quality"
    DEBATE = "debate"
    CONSENSUS = "consensus"


logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Routing strategies for model selection"""

    COST_OPTIMIZED = "cost_optimized"
    PERFORMANCE_FIRST = "performance_first"
    BALANCED = "balanced"
    FASTEST_AVAILABLE = "fastest_available"
    HIGHEST_QUALITY = "highest_quality"


class ModelTier(Enum):
    """Model cost tiers"""

    PREMIUM = "premium"  # GPT-5, Claude Sonnet 4
    STANDARD = "standard"  # Grok-4, Gemini Pro
    ECONOMY = "economy"  # Flash models, Mini variants
    FREE = "free"  # Free tier models


@dataclass
class RouteConfig:
    """Configuration for routing decisions"""

    strategy: RoutingStrategy = RoutingStrategy.BALANCED
    max_cost_per_request: float = 0.05
    max_latency_ms: int = 10000
    fallback_enabled: bool = True
    cache_enabled: bool = True
    retry_attempts: int = 3


@dataclass
class ModelMetrics:
    """Real-time model performance metrics"""

    model: str
    avg_latency_ms: float
    success_rate: float
    cost_per_token: float
    requests_per_minute: int
    error_count: int
    last_success: datetime


class PortkeyUnifiedRouter:
    """
    Unified routing system for Portkey-managed models
    Integrates with AGNO Teams for intelligent model selection
    """

    # Portkey Virtual Keys (Updated 2025-09-02)
    VIRTUAL_KEYS = {
        "OPENAI": "openai-vk-190a60",
        "XAI": "xai-vk-e65d0f",
        "OPENROUTER": "vkj-openrouter-cc4151",
        "TOGETHER": "together-ai-670469",
    }

    def __init__(self):
        self.gateway = ElitePortkeyGateway()
        self.agent_config = EliteAgentConfig()
        self.optimizations = EliteOptimizations()

        # Model registry with real-time metrics
        self.model_registry: dict[str, ModelMetrics] = {}
        self.routing_cache: dict[str, Any] = {}

        # Cost tracking
        self.daily_costs: dict[str, float] = {}
        self.request_counts: dict[str, int] = {}

        # Initialize Portkey clients with virtual keys
        self.portkey_clients: dict[str, Any] = {}

        # Initialize session
        self.session: aiohttp.Optional[ClientSession] = None

    async def initialize(self):
        """Initialize routing system"""
        self.session = aiohttp.ClientSession()
        await self._initialize_portkey_clients()
        await self._initialize_model_metrics()
        await self._load_routing_cache()

    async def _initialize_portkey_clients(self):
        """Initialize Portkey clients with virtual keys"""
        from openai import AsyncOpenAI

        portkey_api_key = os.getenv("PORTKEY_API_KEY")
        if not portkey_api_key:
            logger.warning("PORTKEY_API_KEY not found in environment")
            return

        # OpenRouter client
        self.portkey_clients["OPENROUTER"] = AsyncOpenAI(
            base_url="https://api.portkey.ai/v1",
            api_key=f"pk_{portkey_api_key}",
            default_headers={
                "x-portkey-virtual-key": self.VIRTUAL_KEYS["OPENROUTER"],
                "x-portkey-mode": "proxy",
                "x-portkey-provider": "openrouter",
            },
        )

        # Together AI client
        self.portkey_clients["TOGETHER"] = AsyncOpenAI(
            base_url="https://api.portkey.ai/v1",
            api_key=f"pk_{portkey_api_key}",
            default_headers={
                "x-portkey-virtual-key": self.VIRTUAL_KEYS["TOGETHER"],
                "x-portkey-mode": "proxy",
                "x-portkey-provider": "together",
            },
        )

        logger.info(f"Initialized {len(self.portkey_clients)} Portkey clients")

    async def _initialize_model_metrics(self):
        """Initialize metrics for all approved models"""
        for _role, model in self.agent_config.MODELS.items():
            self.model_registry[model] = ModelMetrics(
                model=model,
                avg_latency_ms=1000.0,
                success_rate=0.95,
                cost_per_token=0.002,
                requests_per_minute=0,
                error_count=0,
                last_success=datetime.now(),
            )

    async def _load_routing_cache(self):
        """Load routing decisions from cache"""
        try:
            cache_file = "/tmp/portkey_routing_cache.json"
            if os.path.exists(cache_file):
                with open(cache_file) as f:
                    self.routing_cache = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load routing cache: {e}")

    async def _save_routing_cache(self):
        """Save routing decisions to cache"""
        try:
            cache_file = "/tmp/portkey_routing_cache.json"
            with open(cache_file, "w") as f:
                json.dump(self.routing_cache, f, default=str)
        except Exception as e:
            logger.warning(f"Failed to save routing cache: {e}")

    def _get_model_tier(self, model: str) -> ModelTier:
        """Determine cost tier for model"""
        tier_mapping = {
            "openai/gpt-5": ModelTier.PREMIUM,
            "anthropic/claude-sonnet-4": ModelTier.PREMIUM,
            "x-ai/grok-4": ModelTier.STANDARD,
            "google/gemini-2.5-pro": ModelTier.STANDARD,
            "google/gemini-2.5-flash": ModelTier.ECONOMY,
            "openai/gpt-5-mini": ModelTier.ECONOMY,
            "google/gemini-2.5-flash-image-preview:free": ModelTier.FREE,
        }
        return tier_mapping.get(model, ModelTier.STANDARD)

    def _calculate_routing_score(
        self, model: str, strategy: RoutingStrategy, task_complexity: float, max_cost: float
    ) -> float:
        """Calculate routing score for model selection"""

        metrics = self.model_registry.get(model)
        if not metrics:
            return 0.0

        tier = self._get_model_tier(model)

        # Base score factors
        performance_score = metrics.success_rate * (1.0 - metrics.avg_latency_ms / 10000.0)
        cost_score = max(0.0, 1.0 - metrics.cost_per_token / max_cost) if max_cost > 0 else 0.5
        availability_score = 1.0 - min(1.0, metrics.error_count / 10.0)

        # Strategy-specific weighting
        if strategy == RoutingStrategy.COST_OPTIMIZED:
            return 0.7 * cost_score + 0.2 * performance_score + 0.1 * availability_score

        elif strategy == RoutingStrategy.PERFORMANCE_FIRST:
            return 0.8 * performance_score + 0.1 * cost_score + 0.1 * availability_score

        elif strategy == RoutingStrategy.FASTEST_AVAILABLE:
            latency_score = 1.0 - metrics.avg_latency_ms / 5000.0
            return 0.6 * latency_score + 0.3 * availability_score + 0.1 * cost_score

        elif strategy == RoutingStrategy.HIGHEST_QUALITY:
            # Prefer premium models for high complexity
            tier_bonus = 0.3 if tier == ModelTier.PREMIUM and task_complexity > 0.7 else 0.0
            return (
                0.5 * performance_score + 0.3 * availability_score + 0.2 * cost_score + tier_bonus
            )

        else:  # BALANCED
            return 0.4 * performance_score + 0.3 * cost_score + 0.3 * availability_score

    @with_circuit_breaker("portkey_routing")
    async def select_optimal_model(
        self,
        agent_role: str,
        task_complexity: float,
        execution_strategy: ExecutionStrategy,
        route_config: Optional[RouteConfig] = None,
    ) -> dict[str, Any]:
        """
        Select optimal model based on role, complexity, and strategy

        Args:
            agent_role: AGNO agent role (planner, generator, critic, etc.)
            task_complexity: Task complexity score (0.0 - 1.0)
            execution_strategy: AGNO execution strategy
            route_config: Routing configuration

        Returns:
            Dictionary with selected model and routing metadata
        """

        config = route_config or RouteConfig()

        # Generate cache key
        cache_key = hashlib.md5(
            f"{agent_role}_{task_complexity}_{execution_strategy.value}_{config.strategy.value}".encode()
        ).hexdigest()

        # Check cache first
        if config.cache_enabled and cache_key in self.routing_cache:
            cached = self.routing_cache[cache_key]
            if datetime.fromisoformat(cached["timestamp"]) > datetime.now() - timedelta(minutes=10):
                logger.info(f"Using cached routing decision for {agent_role}")
                return cached["result"]

        # Get candidate models for role
        primary_model = self.agent_config.MODELS.get(agent_role)
        if not primary_model:
            raise HTTPException(status_code=400, detail=f"Unknown agent role: {agent_role}")

        # Get fallback models based on execution strategy
        candidate_models = self._get_candidate_models(agent_role, execution_strategy)

        # Score all candidates
        model_scores = {}
        for model in candidate_models:
            score = self._calculate_routing_score(
                model, config.strategy, task_complexity, config.max_cost_per_request
            )
            model_scores[model] = score

        # Select best model
        if not model_scores:
            selected_model = primary_model
        else:
            selected_model = max(model_scores.items(), key=lambda x: x[1])[0]

        # Build result
        result = {
            "selected_model": selected_model,
            "primary_model": primary_model,
            "agent_role": agent_role,
            "execution_strategy": execution_strategy.value,
            "routing_strategy": config.strategy.value,
            "task_complexity": task_complexity,
            "model_tier": self._get_model_tier(selected_model).value,
            "fallback_models": [m for m in candidate_models if m != selected_model][:3],
            "routing_metadata": {
                "selection_score": model_scores.get(selected_model, 0.0),
                "candidate_count": len(candidate_models),
                "cache_used": False,
                "timestamp": datetime.now().isoformat(),
            },
        }

        # Cache result
        if config.cache_enabled:
            self.routing_cache[cache_key] = {
                "result": result,
                "timestamp": datetime.now().isoformat(),
            }
            asyncio.create_task(self._save_routing_cache())

        logger.info(
            f"Selected {selected_model} for {agent_role} (score: {model_scores.get(selected_model, 0.0):.3f})"
        )
        return result

    def _get_candidate_models(
        self, agent_role: str, execution_strategy: ExecutionStrategy
    ) -> list[str]:
        """Get candidate models based on role and strategy"""

        primary = self.agent_config.MODELS.get(agent_role)
        candidates = [primary] if primary else []

        # Add strategy-specific models
        if execution_strategy == ExecutionStrategy.LITE:
            # Prefer fast, cheap models
            candidates.extend(
                ["google/gemini-2.5-flash", "openai/gpt-5-mini", "x-ai/grok-code-fast-1"]
            )

        elif execution_strategy == ExecutionStrategy.QUALITY:
            # Prefer premium models
            candidates.extend(["openai/gpt-5", "anthropic/claude-sonnet-4", "x-ai/grok-4"])

        elif execution_strategy == ExecutionStrategy.DEBATE:
            # Need diverse perspectives
            candidates.extend(["x-ai/grok-4", "anthropic/claude-sonnet-4", "openai/gpt-5"])

        else:  # BALANCED, CONSENSUS
            # Use balanced selection
            candidates.extend(["x-ai/grok-4", "google/gemini-2.5-pro", "qwen/qwen3-30b-a3b"])

        # Remove duplicates while preserving order
        seen = set()
        unique_candidates = []
        for model in candidates:
            if model and model not in seen:
                seen.add(model)
                unique_candidates.append(model)

        return unique_candidates

    @with_circuit_breaker("portkey_completion")
    async def route_completion(
        self,
        messages: list[dict[str, str]],
        agent_role: str,
        task_complexity: float = 0.5,
        execution_strategy: ExecutionStrategy = ExecutionStrategy.BALANCED,
        route_config: Optional[RouteConfig] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Route completion request through optimal model

        Args:
            messages: Chat messages
            agent_role: AGNO agent role
            task_complexity: Task complexity score
            execution_strategy: AGNO execution strategy
            route_config: Routing configuration
            **kwargs: Additional completion parameters

        Returns:
            Completion response with routing metadata
        """

        # Select optimal model
        routing_decision = await self.select_optimal_model(
            agent_role, task_complexity, execution_strategy, route_config
        )

        selected_model = routing_decision["selected_model"]
        fallback_models = routing_decision["fallback_models"]

        # Build completion request
        completion_params = {
            "model": selected_model,
            "messages": messages,
            "temperature": self.agent_config.TEMPERATURES.get(agent_role, 0.7),
            "max_tokens": self.agent_config.MAX_TOKENS.get(agent_role, 4000),
            **kwargs,
        }

        # Attempt completion with retries and fallbacks
        last_error = None
        for attempt in range(route_config.retry_attempts if route_config else 3):
            current_model = (
                selected_model
                if attempt == 0
                else fallback_models[min(attempt - 1, len(fallback_models) - 1)]
                if fallback_models
                else selected_model
            )

            completion_params["model"] = current_model

            try:
                start_time = datetime.now()

                # Make completion request through gateway
                response_content = await self.gateway.elite_completion(
                    role=agent_role,
                    messages=messages,
                    task_complexity=task_complexity,
                    **completion_params,
                )

                completion_time = (datetime.now() - start_time).total_seconds() * 1000

                # Update metrics
                await self._update_model_metrics(current_model, completion_time, True)

                # Track costs
                await self._track_request_cost(
                    current_model, len(str(messages)) + len(response_content)
                )

                return {
                    "content": response_content,
                    "model_used": current_model,
                    "completion_time_ms": completion_time,
                    "attempt": attempt + 1,
                    "routing_decision": routing_decision,
                    "success": True,
                }

            except Exception as e:
                last_error = e
                logger.warning(f"Completion attempt {attempt+1} failed with {current_model}: {e}")

                # Update error metrics
                await self._update_model_metrics(current_model, 0, False)

                # Continue to next attempt/fallback
                if attempt >= (route_config.retry_attempts if route_config else 3) - 1:
                    break

        # All attempts failed
        logger.error(f"All completion attempts failed for {agent_role}: {last_error}")
        raise HTTPException(
            status_code=503, detail=f"Model completion failed after retries: {str(last_error)}"
        )

    async def _update_model_metrics(self, model: str, latency_ms: float, success: bool):
        """Update real-time model metrics"""
        if model not in self.model_registry:
            return

        metrics = self.model_registry[model]

        # Update latency (exponential moving average)
        if latency_ms > 0:
            metrics.avg_latency_ms = 0.8 * metrics.avg_latency_ms + 0.2 * latency_ms

        # Update success rate
        metrics.success_rate = 0.9 * metrics.success_rate + 0.1 * (1.0 if success else 0.0)

        # Update error count
        if not success:
            metrics.error_count += 1
        else:
            metrics.error_count = max(0, metrics.error_count - 1)  # Decay errors
            metrics.last_success = datetime.now()

        # Update request rate
        metrics.requests_per_minute += 1

    async def _track_request_cost(self, model: str, token_count: int):
        """Track request costs for budgeting"""
        metrics = self.model_registry.get(model)
        if not metrics:
            return

        cost = token_count * metrics.cost_per_token
        today = datetime.now().strftime("%Y-%m-%d")

        if today not in self.daily_costs:
            self.daily_costs[today] = 0.0

        self.daily_costs[today] += cost
        self.request_counts[model] = self.request_counts.get(model, 0) + 1

    async def get_routing_analytics(self) -> dict[str, Any]:
        """Get routing and usage analytics"""

        # Calculate daily costs
        today = datetime.now().strftime("%Y-%m-%d")
        daily_cost = self.daily_costs.get(today, 0.0)

        # Model usage statistics
        model_stats = {}
        for model, metrics in self.model_registry.items():
            model_stats[model] = {
                "requests": self.request_counts.get(model, 0),
                "avg_latency_ms": metrics.avg_latency_ms,
                "success_rate": metrics.success_rate,
                "error_count": metrics.error_count,
                "cost_per_token": metrics.cost_per_token,
                "tier": self._get_model_tier(model).value,
            }

        return {
            "daily_cost": daily_cost,
            "total_requests": sum(self.request_counts.values()),
            "cache_hit_rate": len(self.routing_cache) / max(1, sum(self.request_counts.values())),
            "model_statistics": model_stats,
            "routing_cache_size": len(self.routing_cache),
            "timestamp": datetime.now().isoformat(),
        }

    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()


# Global router instance
unified_router = PortkeyUnifiedRouter()


# Helper functions for AGNO integration
async def route_agno_completion(
    agent_role: str,
    messages: list[dict[str, str]],
    execution_strategy: ExecutionStrategy = ExecutionStrategy.BALANCED,
    task_complexity: float = 0.5,
    **kwargs,
) -> dict[str, Any]:
    """Route AGNO agent completion through unified router"""

    if not unified_router.session:
        await unified_router.initialize()

    return await unified_router.route_completion(
        messages=messages,
        agent_role=agent_role,
        task_complexity=task_complexity,
        execution_strategy=execution_strategy,
        **kwargs,
    )


async def get_optimal_model_for_role(
    agent_role: str,
    execution_strategy: ExecutionStrategy = ExecutionStrategy.BALANCED,
    task_complexity: float = 0.5,
) -> str:
    """Get optimal model for AGNO agent role"""

    if not unified_router.session:
        await unified_router.initialize()

    routing_decision = await unified_router.select_optimal_model(
        agent_role=agent_role,
        task_complexity=task_complexity,
        execution_strategy=execution_strategy,
    )

    return routing_decision["selected_model"]
