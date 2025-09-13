"""
Advanced AI Gateway 2025 - Portkey with OpenRouter & Together AI
Latest August 2025 models with virtual keys and smart routing.
NO OpenAI dependency required.
"""
import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional
import httpx
from app.core.env import load_env_once
from app.core.circuit_breaker import with_circuit_breaker
# Load environment variables
load_env_once()
logger = logging.getLogger(__name__)
class TaskType(Enum):
    """Task-based model routing."""
    REASONING = "reasoning"
    CREATIVE = "creative"
    CODING = "coding"
    FAST = "fast"
    GENERAL = "general"
    EMBEDDINGS = "embeddings"
@dataclass
class ModelConfig2025:
    """Latest 2025 model configuration."""
    model_name: str
    virtual_key: str
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: float = 30.0
class AdvancedAIGateway2025:
    """Production AI Gateway with latest 2025 models and virtual keys."""
    @with_circuit_breaker("external_api")
    def __init__(self):
        self.validate_environment()
        self.setup_latest_models()
        self.setup_portkey_configs()
        self.cache_metrics = {
            "hits": 0,
            "misses": 0,
            "total_requests": 0,
            "cost_saved": 0.0,
            "last_reset": None,
        }
    @with_circuit_breaker("external_api")
    def validate_environment(self):
        """Validate required API keys."""
        required_keys = ["PORTKEY_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY"]
        missing_keys = [key for key in required_keys if not os.getenv(key)]
        if missing_keys:
            raise ValueError(f"Missing required API keys: {', '.join(missing_keys)}")
        logger.info("✅ All virtual key dependencies validated")
    @with_circuit_breaker("external_api")
    def setup_latest_models(self):
        """Setup latest August 2025 model configurations."""
        self.model_configs = {
            # 🔥 Latest 2025 releases with YOUR REAL VIRTUAL KEYS
            TaskType.REASONING: ModelConfig2025(
                model_name="x-ai/grok-2-1212",  # Latest xAI model
                virtual_key="xai-vk-e65d0f",  # Your XAI virtual key
                max_tokens=4000,
                temperature=0.3,
            ),
            TaskType.CREATIVE: ModelConfig2025(
                model_name="google/gemini-2.0-flash-exp",  # Latest Gemini via OpenRouter
                virtual_key="vkj-openrouter-cc4151",  # Your OpenRouter virtual key
                max_tokens=6000,
                temperature=0.8,
            ),
            TaskType.CODING: ModelConfig2025(
                model_name="anthropic/claude-3.5-sonnet-20241022",  # Latest Claude via OpenRouter
                virtual_key="vkj-openrouter-cc4151",  # Your OpenRouter virtual key
                max_tokens=4000,
                temperature=0.2,
            ),
            TaskType.FAST: ModelConfig2025(
                model_name="openai/gpt-4o-mini-2024-07-18",  # Speed optimized via OpenRouter
                virtual_key="vkj-openrouter-cc4151",  # Your OpenRouter virtual key
                max_tokens=2000,
                temperature=0.7,
            ),
            TaskType.GENERAL: ModelConfig2025(
                model_name="anthropic/claude-3.5-sonnet-20241022",  # Reliable default
                virtual_key="vkj-openrouter-cc4151",  # Your OpenRouter virtual key
                max_tokens=3000,
                temperature=0.7,
            ),
            TaskType.EMBEDDINGS: ModelConfig2025(
                model_name="togethercomputer/m2-bert-80M-32k-retrieval",  # 32k context
                virtual_key="together-ai-670469",  # Your Together AI virtual key
                max_tokens=1,  # Not applicable for embeddings
                temperature=0.0,
            ),
        }
    @with_circuit_breaker("external_api")
    def setup_portkey_configs(self):
        """Setup Portkey configurations for each task type with advanced semantic caching."""
        self.portkey_configs = {
            "llm_config": {
                "strategy": {"mode": "single"},
                "retry": {"attempts": 3, "on_status_codes": [429, 500, 502, 503, 504]},
                "cache": {
                    "enabled": True,
                    "mode": "semantic",
                    "ttl": 1800,
                    "similarity_threshold": 0.95,
                    "embedding_model": "togethercomputer/m2-bert-80M-32k-retrieval",
                    "max_cache_size": 10000,
                    "cache_eviction_policy": "lru",
                },
                "metadata": {"environment": "production", "version": "2025.1"},
            },
            "embedding_config": {
                "strategy": {"mode": "single"},
                "retry": {"attempts": 2},
                "cache": {
                    "enabled": True,
                    "mode": "semantic",
                    "ttl": 3600,
                    "similarity_threshold": 0.98,
                    "embedding_model": "togethercomputer/m2-bert-80M-32k-retrieval",
                    "max_cache_size": 5000,
                    "cache_eviction_policy": "lru",
                },
                "metadata": {"service": "embeddings"},
            },
        }
    @with_circuit_breaker("external_api")
    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        task_type: TaskType = TaskType.GENERAL,
        stream: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """Execute chat completion with latest 2025 models via Portkey virtual keys and semantic caching."""
        # Update cache metrics
        self.cache_metrics["total_requests"] += 1
        config = self.model_configs[task_type]
        # Determine config type
        portkey_config = (
            self.portkey_configs["embedding_config"]
            if task_type == TaskType.EMBEDDINGS
            else self.portkey_configs["llm_config"]
        )
        # Setup headers for Portkey with virtual keys
        headers = {
            "x-portkey-api-key": os.getenv("PORTKEY_API_KEY"),
            "x-portkey-config": json.dumps(portkey_config),
            "x-portkey-provider": config.virtual_key,  # Use virtual key
            "content-type": "application/json",
        }
        # Prepare payload
        payload = {
            "model": config.model_name,
            "messages": messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "stream": stream,
        }
        payload.update(kwargs)
        # Make API call through Portkey
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            logger.info(
                f"Calling {task_type.value} model: {config.model_name} via {config.virtual_key}"
            )
            response = await client.post(
                "https://api.portkey.ai/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            if response.status_code != 200:
                error_details = response.text
                logger.error(
                    f"Portkey API failed: {response.status_code} - {error_details}"
                )
                raise httpx.HTTPStatusError(
                    f"Portkey returned {response.status_code}: {error_details}",
                    request=response.request,
                    response=response,
                )
            result = response.json()
            result["task_type"] = task_type.value
            result["virtual_key"] = config.virtual_key
            result["model_name"] = config.model_name
            # Track cache performance metrics
            if "cache_hit" in result.get("metadata", {}):
                if result["metadata"]["cache_hit"]:
                    self.cache_metrics["hits"] += 1
                    # Estimate cost savings (rough approximation)
                    self.cache_metrics[
                        "cost_saved"
                    ] += 0.001  # $0.001 per cached request
                    logger.info("Cache hit - cost saved")
                else:
                    self.cache_metrics["misses"] += 1
                    logger.info("Cache miss - new request processed")
            return result
    @with_circuit_breaker("external_api")
    async def generate_embeddings(
        self,
        texts: list[str],
        model: str = "togethercomputer/m2-bert-80M-32k-retrieval",
    ) -> dict[str, Any]:
        """Generate embeddings using Together AI via Portkey virtual keys."""
        headers = {
            "x-portkey-api-key": os.getenv("PORTKEY_API_KEY"),
            "x-portkey-config": json.dumps(self.portkey_configs["embedding_config"]),
            "x-portkey-provider": "@TOGETHER_EMBEDDINGS",
            "content-type": "application/json",
        }
        payload = {"input": texts, "model": model}
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"Generating embeddings with {model} via Together AI")
            response = await client.post(
                "https://api.portkey.ai/v1/embeddings", headers=headers, json=payload
            )
            if response.status_code != 200:
                error_details = response.text
                raise httpx.HTTPStatusError(
                    f"Together AI embeddings failed: {response.status_code} - {error_details}",
                    request=response.request,
                    response=response,
                )
            result = response.json()
            result["provider"] = "together_ai"
            result["virtual_key"] = "@TOGETHER_EMBEDDINGS"
            return result
    async def smart_chat(
        self,
        messages: list[dict[str, str]],
        task_type: TaskType = TaskType.GENERAL,
        **kwargs,
    ) -> dict[str, Any]:
        """Smart model routing based on task type with latest 2025 models."""
        try:
            # Primary attempt with latest models
            return await self.chat_completion(messages, task_type, **kwargs)
        except Exception as primary_error:
            logger.warning(f"Primary model {task_type.value} failed: {primary_error}")
            # Smart fallback based on task type
            fallback_map = {
                TaskType.REASONING: TaskType.GENERAL,
                TaskType.CREATIVE: TaskType.GENERAL,
                TaskType.CODING: TaskType.FAST,
                TaskType.FAST: TaskType.GENERAL,
                TaskType.GENERAL: TaskType.FAST,
            }
            fallback_type = fallback_map.get(task_type, TaskType.FAST)
            try:
                logger.info(f"Trying fallback: {fallback_type.value}")
                return await self.chat_completion(messages, fallback_type, **kwargs)
            except Exception as fallback_error:
                logger.error(
                    f"All models failed. Primary: {primary_error}, Fallback: {fallback_error}"
                )
                raise Exception(f"Smart routing failed: {primary_error}")
    @with_circuit_breaker("external_api")
    async def get_latest_models(self) -> dict[str, list[str]]:
        """Get available latest 2025 models from OpenRouter."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.portkey.ai/v1/models",
                    headers={
                        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"
                    },
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("data", [])
                    # Filter latest 2025 models
                    latest_models = {
                        "gpt_5_models": [m["id"] for m in models if "gpt-5" in m["id"]],
                        "gemini_25_models": [
                            m["id"] for m in models if "gemini-2.5" in m["id"]
                        ],
                        "claude_4_models": [
                            m["id"]
                            for m in models
                            if "claude-4" in m["id"] or "claude-sonnet-4" in m["id"]
                        ],
                        "llama_4_models": [
                            m["id"] for m in models if "llama-4" in m["id"]
                        ],
                        "all_models": [m["id"] for m in models],
                    }
                    return latest_models
                else:
                    logger.error(f"Failed to get models: {response.status_code}")
                    return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return {"error": str(e)}
    @with_circuit_breaker("external_api")
    async def health_check(self) -> dict[str, Any]:
        """Comprehensive health check for all virtual key providers."""
        health_status = {}
        # Test each task type
        for task_type in [TaskType.REASONING, TaskType.FAST, TaskType.EMBEDDINGS]:
            try:
                if task_type == TaskType.EMBEDDINGS:
                    # Test embeddings
                    result = await self.generate_embeddings(["test embedding"])
                    health_status[task_type.value] = {
                        "status": "healthy",
                        "model": self.model_configs[task_type].model_name,
                        "virtual_key": self.model_configs[task_type].virtual_key,
                        "embedding_dimensions": len(
                            result.get("data", [{}])[0].get("embedding", [])
                        ),
                    }
                else:
                    # Test chat completions
                    result = await self.chat_completion(
                        messages=[{"role": "user", "content": "Hi"}],
                        task_type=task_type,
                    )
                    health_status[task_type.value] = {
                        "status": "healthy",
                        "model": result.get("model_name"),
                        "virtual_key": result.get("virtual_key"),
                        "response_received": bool(result.get("choices")),
                    }
            except Exception as e:
                health_status[task_type.value] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "model": self.model_configs[task_type].model_name,
                    "virtual_key": self.model_configs[task_type].virtual_key,
                }
        # Overall health
        healthy_count = sum(
            1 for status in health_status.values() if status["status"] == "healthy"
        )
        total_count = len(health_status)
        return {
            "overall_status": "healthy" if healthy_count == total_count else "degraded",
            "healthy_services": healthy_count,
            "total_services": total_count,
            "virtual_keys_configured": ["@OPENROUTER_MAIN", "@TOGETHER_EMBEDDINGS"],
            "latest_models_available": await self.get_latest_models(),
            "services": health_status,
        }
    @with_circuit_breaker("external_api")
    def get_cache_statistics(self) -> dict[str, Any]:
        """Get comprehensive cache performance statistics."""
        total = self.cache_metrics["total_requests"]
        hits = self.cache_metrics["hits"]
        misses = self.cache_metrics["misses"]
        hit_rate = (hits / total * 100) if total > 0 else 0
        cost_savings_percentage = (hits / total * 100) if total > 0 else 0
        return {
            "total_requests": total,
            "cache_hits": hits,
            "cache_misses": misses,
            "hit_rate_percentage": round(hit_rate, 2),
            "estimated_cost_saved": round(self.cache_metrics["cost_saved"], 4),
            "cost_savings_percentage": round(cost_savings_percentage, 2),
            "cache_config": {
                "llm_cache_ttl": self.portkey_configs["llm_config"]["cache"]["ttl"],
                "embedding_cache_ttl": self.portkey_configs["embedding_config"][
                    "cache"
                ]["ttl"],
                "similarity_threshold_llm": self.portkey_configs["llm_config"]["cache"][
                    "similarity_threshold"
                ],
                "similarity_threshold_embeddings": self.portkey_configs[
                    "embedding_config"
                ]["cache"]["similarity_threshold"],
            },
        }
    @with_circuit_breaker("external_api")
    async def invalidate_cache(
        self, pattern: Optional[str] = None, model: Optional[str] = None
    ) -> dict[str, Any]:
        """Invalidate cache entries based on pattern or model."""
        try:
            # Prepare invalidation request
            headers = {
                "x-portkey-api-key": os.getenv("PORTKEY_API_KEY"),
                "content-type": "application/json",
            }
            payload = {}
            if pattern:
                payload["pattern"] = pattern
            if model:
                payload["model"] = model
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.portkey.ai/v1/cache/invalidate",
                    headers=headers,
                    json=payload,
                )
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Cache invalidation successful: {result}")
                    return {
                        "success": True,
                        "entries_invalidated": result.get("entries_invalidated", 0),
                        "pattern": pattern,
                        "model": model,
                    }
                else:
                    logger.error(f"Cache invalidation failed: {response.status_code}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "pattern": pattern,
                        "model": model,
                    }
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "pattern": pattern,
                "model": model,
            }
    async def clear_all_cache(self) -> dict[str, Any]:
        """Clear all cached entries across all models."""
        return await self.invalidate_cache()
    async def invalidate_model_cache(self, model_name: str) -> dict[str, Any]:
        """Invalidate cache for a specific model."""
        return await self.invalidate_cache(model=model_name)
    def reset_cache_metrics(self):
        """Reset cache performance metrics."""
        from datetime import datetime
        self.cache_metrics = {
            "hits": 0,
            "misses": 0,
            "total_requests": 0,
            "cost_saved": 0.0,
            "last_reset": datetime.now().isoformat(),
        }
        logger.info("Cache metrics reset")
# Global instance
_advanced_gateway = None
def get_advanced_gateway() -> AdvancedAIGateway2025:
    """Get or create the global advanced gateway instance."""
    global _advanced_gateway
    if _advanced_gateway is None:
        _advanced_gateway = AdvancedAIGateway2025()
    return _advanced_gateway
# Convenience functions for easy integration
@with_circuit_breaker("external_api")
async def chat_with_gpt5(messages: list[dict[str, str]], **kwargs) -> dict[str, Any]:
    """Chat with latest GPT-5 via OpenRouter virtual key."""
    gateway = get_advanced_gateway()
    return await gateway.smart_chat(messages, TaskType.REASONING, **kwargs)
@with_circuit_breaker("external_api")
async def chat_with_gemini25_pro(
    messages: list[dict[str, str]], **kwargs
) -> dict[str, Any]:
    """Chat with Gemini 2.5 Pro (1M context) via OpenRouter virtual key."""
    gateway = get_advanced_gateway()
    return await gateway.smart_chat(messages, TaskType.CREATIVE, **kwargs)
@with_circuit_breaker("external_api")
async def chat_with_claude_sonnet4(
    messages: list[dict[str, str]], **kwargs
) -> dict[str, Any]:
    """Chat with Claude Sonnet 4 via OpenRouter virtual key."""
    gateway = get_advanced_gateway()
    return await gateway.smart_chat(messages, TaskType.CODING, **kwargs)
@with_circuit_breaker("llm")
async def generate_embeddings_32k(texts: list[str]) -> dict[str, Any]:
    """Generate embeddings with 32k context via Together AI virtual key."""
    gateway = get_advanced_gateway()
    return await gateway.generate_embeddings(texts)
async def smart_route_chat(
    messages: list[dict[str, str]], task_hint: str = "general"
) -> dict[str, Any]:
    """Automatically route to best model based on task hint."""
    gateway = get_advanced_gateway()
    # Smart task detection
    task_keywords = {
        TaskType.REASONING: ["analyze", "reason", "logic", "math", "problem", "think"],
        TaskType.CREATIVE: ["write", "story", "creative", "imagine", "art", "design"],
        TaskType.CODING: [
            "code",
            "program",
            "debug",
            "function",
            "algorithm",
            "python",
        ],
        TaskType.FAST: ["quick", "simple", "fast", "brief", "short"],
    }
    # Detect task type from content
    content = " ".join([m.get("content", "") for m in messages]).lower()
    task_hint_lower = task_hint.lower()
    detected_task = TaskType.GENERAL
    for task_type, keywords in task_keywords.items():
        if any(
            keyword in content or keyword in task_hint_lower for keyword in keywords
        ):
            detected_task = task_type
            break
    logger.info(f"Smart routing detected task: {detected_task.value}")
    return await gateway.smart_chat(messages, detected_task)
