"""
OpenRouter Latest Model Integration (August 2025).
Dynamic model management with automatic updates and fallbacks.
"""

import os
import asyncio
import httpx
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ModelTier(Enum):
    """Model pricing tiers."""
    PREMIUM = "premium"  # High-cost, highest capability
    BALANCED = "balanced"  # Medium cost-performance ratio
    FREE = "free"  # Free tier models


class TaskType(Enum):
    """Task categories for model selection."""
    REASONING = "reasoning"
    CODING = "coding"
    CREATIVE = "creative"
    GENERAL = "general"
    VISION = "vision"
    AUDIO = "audio"


@dataclass
class ModelInfo:
    """Model information from OpenRouter."""
    id: str
    name: str
    context_length: int
    pricing_prompt: float  # Per 1M tokens
    pricing_completion: float  # Per 1M tokens
    supports_functions: bool = False
    supports_vision: bool = False
    supports_audio: bool = False
    is_free: bool = False
    provider: str = ""
    
    @property
    def is_premium(self) -> bool:
        """Check if model is premium tier."""
        return self.pricing_prompt > 5.0 or self.pricing_completion > 10.0


class OpenRouterLatest:
    """
    OpenRouter integration with latest models (August 2025).
    Includes GPT-5, Claude-4, Gemini 2.5, DeepSeek V3.1, etc.
    """
    
    # Latest flagship models as of August 2025
    LATEST_MODELS = {
        # OpenAI GPT-5 Series
        "openai/gpt-5": {"tier": ModelTier.PREMIUM, "context": 400000},
        "openai/gpt-5-chat": {"tier": ModelTier.PREMIUM, "context": 128000},
        "openai/gpt-5-mini": {"tier": ModelTier.BALANCED, "context": 400000},
        "openai/gpt-5-nano": {"tier": ModelTier.BALANCED, "context": 400000},
        "openai/o3-pro": {"tier": ModelTier.PREMIUM, "context": 128000},
        "openai/o3": {"tier": ModelTier.PREMIUM, "context": 128000},
        
        # Anthropic Claude 4 Series
        "anthropic/claude-opus-4": {"tier": ModelTier.PREMIUM, "context": 200000},
        "anthropic/claude-sonnet-4": {"tier": ModelTier.PREMIUM, "context": 1000000},
        "anthropic/claude-3.7-sonnet": {"tier": ModelTier.BALANCED, "context": 200000},
        "anthropic/claude-3.7-sonnet:thinking": {"tier": ModelTier.BALANCED, "context": 200000},
        
        # Google Gemini 2.5 Series
        "google/gemini-2.5-pro": {"tier": ModelTier.BALANCED, "context": 1000000},
        "google/gemini-2.5-flash": {"tier": ModelTier.BALANCED, "context": 1000000},
        "google/gemini-2.5-flash-image-preview": {"tier": ModelTier.BALANCED, "context": 1000000},
        "google/gemini-2.0-flash-001": {"tier": ModelTier.BALANCED, "context": 1000000},
        
        # DeepSeek V3.1 Series
        "deepseek/deepseek-chat-v3.1": {"tier": ModelTier.BALANCED, "context": 164000},
        "deepseek/deepseek-chat-v3.1:free": {"tier": ModelTier.FREE, "context": 164000},
        "deepseek/deepseek-r1": {"tier": ModelTier.BALANCED, "context": 128000},
        "deepseek/deepseek-r1:free": {"tier": ModelTier.FREE, "context": 128000},
        
        # X.AI Grok Series
        "x-ai/grok-code-fast-1": {"tier": ModelTier.BALANCED, "context": 128000},
        "x-ai/grok-3": {"tier": ModelTier.PREMIUM, "context": 128000},
        "x-ai/grok-3-mini": {"tier": ModelTier.BALANCED, "context": 128000},
        
        # Meta Llama Latest
        "meta-llama/llama-4-maverick": {"tier": ModelTier.BALANCED, "context": 128000},
        "meta-llama/llama-4-maverick:free": {"tier": ModelTier.FREE, "context": 128000},
        "meta-llama/llama-3.3-70b-instruct": {"tier": ModelTier.BALANCED, "context": 128000},
        "meta-llama/llama-3.3-70b-instruct:free": {"tier": ModelTier.FREE, "context": 128000},
        
        # Qwen Latest
        "qwen/qwen3-coder": {"tier": ModelTier.BALANCED, "context": 32768},
        "qwen/qwen3-235b-a22b": {"tier": ModelTier.PREMIUM, "context": 32768},
        "qwen/qwen3-235b-a22b:free": {"tier": ModelTier.FREE, "context": 32768},
        
        # Mistral Latest
        "mistralai/mistral-medium-3.1": {"tier": ModelTier.BALANCED, "context": 128000},
        "mistralai/codestral-2501": {"tier": ModelTier.BALANCED, "context": 128000},
        "mistralai/mistral-small-3.2-24b-instruct:free": {"tier": ModelTier.FREE, "context": 128000},
    }
    
    # Task-optimized model recommendations
    MODEL_RECOMMENDATIONS = {
        TaskType.REASONING: {
            ModelTier.PREMIUM: ["openai/gpt-5", "deepseek/deepseek-r1", "openai/o3-pro"],
            ModelTier.BALANCED: ["deepseek/deepseek-r1", "anthropic/claude-3.7-sonnet:thinking"],
            ModelTier.FREE: ["deepseek/deepseek-r1:free", "deepseek/deepseek-chat-v3.1:free"]
        },
        TaskType.CODING: {
            ModelTier.PREMIUM: ["openai/gpt-5", "x-ai/grok-code-fast-1", "anthropic/claude-opus-4"],
            ModelTier.BALANCED: ["x-ai/grok-code-fast-1", "qwen/qwen3-coder", "mistralai/codestral-2501"],
            ModelTier.FREE: ["deepseek/deepseek-chat-v3.1:free", "qwen/qwen3-235b-a22b:free"]
        },
        TaskType.CREATIVE: {
            ModelTier.PREMIUM: ["anthropic/claude-opus-4", "openai/gpt-5"],
            ModelTier.BALANCED: ["anthropic/claude-3.7-sonnet", "google/gemini-2.5-pro"],
            ModelTier.FREE: ["meta-llama/llama-4-maverick:free", "google/gemini-2.5-flash:free"]
        },
        TaskType.GENERAL: {
            ModelTier.PREMIUM: ["openai/gpt-5", "anthropic/claude-sonnet-4"],
            ModelTier.BALANCED: ["google/gemini-2.5-pro", "deepseek/deepseek-chat-v3.1"],
            ModelTier.FREE: ["meta-llama/llama-4-maverick:free", "mistralai/mistral-small-3.2-24b-instruct:free"]
        },
        TaskType.VISION: {
            ModelTier.PREMIUM: ["openai/gpt-5", "anthropic/claude-opus-4"],
            ModelTier.BALANCED: ["google/gemini-2.5-flash-image-preview", "google/gemini-2.5-pro"],
            ModelTier.FREE: ["google/gemini-2.5-flash-image-preview:free"]
        }
    }
    
    def __init__(self, api_key: str, referer: str = "http://localhost:3000", app_name: str = "Sophia-Intel-AI"):
        """Initialize OpenRouter client with latest configuration."""
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": referer,
            "X-Title": app_name,
            "Content-Type": "application/json"
        }
        
        # Model cache
        self.model_cache: Dict[str, ModelInfo] = {}
        self.cache_timestamp: Optional[datetime] = None
        self.cache_ttl = timedelta(hours=6)
        
        # Health monitoring
        self.model_health: Dict[str, Dict[str, Any]] = {}
        self.fallback_chains: Dict[str, List[str]] = self._build_fallback_chains()
        
    def _build_fallback_chains(self) -> Dict[str, List[str]]:
        """Build fallback chains for each primary model."""
        return {
            # GPT-5 fallbacks
            "openai/gpt-5": ["openai/gpt-5-mini", "openai/gpt-4o", "openai/gpt-4o-mini"],
            "openai/gpt-5-mini": ["openai/gpt-5-nano", "openai/gpt-4o-mini"],
            
            # Claude-4 fallbacks
            "anthropic/claude-opus-4": ["anthropic/claude-sonnet-4", "anthropic/claude-3.7-sonnet", "anthropic/claude-3.5-sonnet"],
            "anthropic/claude-3.7-sonnet:thinking": ["anthropic/claude-3.7-sonnet", "anthropic/claude-3.5-sonnet"],
            
            # DeepSeek fallbacks
            "deepseek/deepseek-r1": ["deepseek/deepseek-chat-v3.1", "deepseek/deepseek-r1:free"],
            "deepseek/deepseek-chat-v3.1": ["deepseek/deepseek-chat-v3.1:free", "qwen/qwen3-coder"],
            
            # Gemini fallbacks
            "google/gemini-2.5-pro": ["google/gemini-2.5-flash", "google/gemini-2.0-flash-001"],
            
            # X.AI fallbacks
            "x-ai/grok-code-fast-1": ["qwen/qwen3-coder", "mistralai/codestral-2501", "deepseek/deepseek-chat-v3.1"],
            
            # Generic fallback for unknown models
            "default": ["openai/gpt-4o-mini", "deepseek/deepseek-chat-v3.1:free", "meta-llama/llama-3.3-70b-instruct:free"]
        }
        
    async def refresh_model_cache(self) -> Dict[str, ModelInfo]:
        """Fetch and cache the latest model list from OpenRouter."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.model_cache.clear()
                    
                    for model_data in data.get("data", []):
                        model_id = model_data.get("id")
                        if model_id:
                            pricing = model_data.get("pricing", {})
                            self.model_cache[model_id] = ModelInfo(
                                id=model_id,
                                name=model_data.get("name", model_id),
                                context_length=model_data.get("context_length", 4096),
                                pricing_prompt=float(pricing.get("prompt", 0)) if pricing.get("prompt") else 0,
                                pricing_completion=float(pricing.get("completion", 0)) if pricing.get("completion") else 0,
                                supports_functions=model_data.get("supports_functions", False),
                                supports_vision="vision" in model_data.get("description", "").lower(),
                                supports_audio="audio" in model_id.lower(),
                                is_free=":free" in model_id,
                                provider=model_id.split("/")[0] if "/" in model_id else ""
                            )
                    
                    self.cache_timestamp = datetime.now()
                    logger.info(f"Refreshed model cache: {len(self.model_cache)} models available")
                    
        except Exception as e:
            logger.error(f"Failed to refresh model cache: {e}")
            
        return self.model_cache
        
    def should_refresh_cache(self) -> bool:
        """Check if cache needs refreshing."""
        if not self.cache_timestamp:
            return True
        return datetime.now() - self.cache_timestamp > self.cache_ttl
        
    async def get_best_model(self, 
                            task: TaskType = TaskType.GENERAL,
                            tier: ModelTier = ModelTier.BALANCED,
                            require_vision: bool = False,
                            require_functions: bool = False,
                            max_cost_per_1m: Optional[float] = None) -> str:
        """
        Get the best available model for the task and requirements.
        
        Args:
            task: Type of task (reasoning, coding, creative, etc.)
            tier: Pricing tier preference
            require_vision: If True, only return vision-capable models
            require_functions: If True, only return function-calling capable models
            max_cost_per_1m: Maximum cost per 1M tokens (prompt + completion)
            
        Returns:
            Model ID string (e.g., "openai/gpt-5")
        """
        # Refresh cache if needed
        if self.should_refresh_cache():
            await self.refresh_model_cache()
            
        # Get recommended models for task and tier
        recommendations = self.MODEL_RECOMMENDATIONS.get(task, {}).get(tier, [])
        
        # Filter by requirements
        for model_id in recommendations:
            if model_id in self.model_cache:
                model = self.model_cache[model_id]
                
                # Check requirements
                if require_vision and not model.supports_vision:
                    continue
                if require_functions and not model.supports_functions:
                    continue
                if max_cost_per_1m:
                    total_cost = model.pricing_prompt + model.pricing_completion
                    if total_cost > max_cost_per_1m:
                        continue
                        
                # Check health
                if await self.check_model_health(model_id):
                    return model_id
                    
        # Fallback to any available model
        fallback_order = [
            "openai/gpt-4o-mini",
            "deepseek/deepseek-chat-v3.1:free",
            "meta-llama/llama-3.3-70b-instruct:free"
        ]
        
        for model_id in fallback_order:
            if await self.check_model_health(model_id):
                logger.warning(f"Using fallback model: {model_id}")
                return model_id
                
        # Last resort
        return "openai/gpt-4o-mini"
        
    async def check_model_health(self, model_id: str) -> bool:
        """Check if a model is healthy and available."""
        # Check cache first
        if model_id in self.model_health:
            health = self.model_health[model_id]
            if health.get("checked_at"):
                age = datetime.now() - health["checked_at"]
                if age < timedelta(minutes=15):
                    return health.get("available", False)
                    
        # Perform health check
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": model_id,
                        "messages": [{"role": "user", "content": "test"}],
                        "max_tokens": 1,
                        "temperature": 0
                    }
                )
                
                available = response.status_code == 200
                self.model_health[model_id] = {
                    "available": available,
                    "checked_at": datetime.now(),
                    "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else None
                }
                
                return available
                
        except Exception as e:
            logger.debug(f"Model {model_id} health check failed: {e}")
            self.model_health[model_id] = {
                "available": False,
                "checked_at": datetime.now(),
                "error": str(e)
            }
            return False
            
    async def create_completion_with_fallback(self,
                                             messages: List[Dict[str, str]],
                                             model: Optional[str] = None,
                                             task: TaskType = TaskType.GENERAL,
                                             tier: ModelTier = ModelTier.BALANCED,
                                             **kwargs) -> Dict[str, Any]:
        """
        Create completion with automatic fallback on failure.
        
        Args:
            messages: Chat messages
            model: Specific model to use (optional)
            task: Task type if model not specified
            tier: Tier preference if model not specified
            **kwargs: Additional OpenAI API parameters
            
        Returns:
            API response dict
        """
        # Determine primary model
        if not model:
            model = await self.get_best_model(task, tier)
            
        # Get fallback chain
        fallback_models = [model] + self.fallback_chains.get(model, self.fallback_chains["default"])
        
        last_error = None
        for attempt_model in fallback_models:
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=self.headers,
                        json={
                            "model": attempt_model,
                            "messages": messages,
                            **kwargs
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        result["_model_used"] = attempt_model
                        result["_fallback_attempted"] = attempt_model != model
                        return result
                    else:
                        last_error = f"HTTP {response.status_code}: {response.text}"
                        
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Model {attempt_model} failed: {e}")
                continue
                
        # All models failed
        raise Exception(f"All models failed. Last error: {last_error}")
        
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get cached information about a specific model."""
        return self.model_cache.get(model_id)
        
    def get_available_models(self, 
                           tier: Optional[ModelTier] = None,
                           max_cost: Optional[float] = None,
                           require_vision: bool = False) -> List[str]:
        """Get list of available models matching criteria."""
        models = []
        
        for model_id, info in self.model_cache.items():
            # Filter by tier
            if tier:
                model_tier = self.LATEST_MODELS.get(model_id, {}).get("tier")
                if model_tier != tier:
                    continue
                    
            # Filter by cost
            if max_cost:
                total_cost = info.pricing_prompt + info.pricing_completion
                if total_cost > max_cost:
                    continue
                    
            # Filter by capabilities
            if require_vision and not info.supports_vision:
                continue
                
            models.append(model_id)
            
        return sorted(models)
        
    def estimate_cost(self, model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost for a completion."""
        info = self.model_cache.get(model_id)
        if not info:
            return 0.0
            
        prompt_cost = (prompt_tokens / 1_000_000) * info.pricing_prompt
        completion_cost = (completion_tokens / 1_000_000) * info.pricing_completion
        
        return prompt_cost + completion_cost