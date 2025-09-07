"""
Portkey Virtual Keys Management System
Centralized provider abstraction with intelligent routing
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import yaml
from portkey_ai import Portkey

from app.core.secrets_manager import get_secret

logger = logging.getLogger(__name__)


class ModelTier(Enum):
    """Model quality/cost tiers"""

    QUALITY = "quality"  # GPT-5, Opus, etc. - Best quality
    BALANCED = "balanced"  # GPT-4o, Sonnet, etc. - Good balance
    FAST = "fast"  # Groq, Haiku, etc. - Speed focused
    SEARCH = "search"  # Perplexity, etc. - Web search


class TaskType(Enum):
    """Types of tasks for routing"""

    ORCHESTRATION = "orchestration"
    LONG_PLANNING = "long_planning"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    WEB_RESEARCH = "web_research"
    EMBEDDING = "embedding"
    RERANKING = "reranking"
    DRAFT = "draft"
    GENERAL = "general"


@dataclass
class ModelConfig:
    """Configuration for a specific model"""

    provider: str
    model: str
    virtual_key: str
    max_tokens: int = 6000
    temperature: float = 0.2
    cost_per_1k_tokens: float = 0.01
    supports_streaming: bool = True
    context_window: int = 128000


@dataclass
class RoutingDecision:
    """Result of routing decision"""

    provider: str
    model: str
    virtual_key: str
    reason: str
    estimated_cost: float
    fallbacks: list[ModelConfig]


class PortkeyManager:
    """
    Manages all provider access through Portkey virtual keys.
    Provides intelligent routing, cost optimization, and fallback handling.
    """

    # Virtual keys mapping (from portkey_config.yaml)
    VIRTUAL_KEYS = {
        "deepseek": "deepseek-vk-24102f",
        "openai": "openai-vk-190a60",
        "anthropic": "anthropic-vk-b42804",
        "openrouter": "vkj-openrouter-cc4151",
        "perplexity": "perplexity-vk-56c172",
        "groq": "groq-vk-6b9b52",
        "mistral": "mistral-vk-f92861",
        "xai": "xai-vk-e65d0f",
        "together": "together-ai-670469",
        "cohere": "cohere-vk-496fa9",
        "gemini": "gemini-vk-3d6108",
        "huggingface": "huggingface-vk-28240e",
        "milvus": "milvus-vk-34fa02",
        "qdrant": "qdrant-vk-d2b62a",
    }

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize Portkey Manager

        Args:
            config_path: Path to portkey_config.yaml
        """
        self.config_path = config_path or Path("app/core/portkey_config.yaml")
        self.portkey_api_key = get_secret("PORTKEY_API_KEY")

        if not self.portkey_api_key:
            raise ValueError("PORTKEY_API_KEY not found in environment or secrets")

        self.config = self._load_config()
        self._clients = {}
        self._usage_stats = {}

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from YAML file"""
        if self.config_path.exists():
            with open(self.config_path) as f:
                return yaml.safe_load(f)
        else:
            # Return default configuration if file doesn't exist
            return self._get_default_config()

    def _get_default_config(self) -> dict[str, Any]:
        """Get default configuration"""
        return {
            "virtual_keys": self.VIRTUAL_KEYS,
            "model_policy": {
                "defaults": {
                    "max_tokens": 6000,
                    "temperature": 0.2,
                    "cost_ceiling_usd": 0.50,
                    "timeout_s": 120,
                },
                "routes": {
                    "orchestration.long_planning": {
                        "primary": {"vk": "openai-vk-190a60", "model": "gpt-5"},
                        "fallbacks": [
                            {"vk": "anthropic-vk-b42804", "model": "claude-3-opus"},
                            {"vk": "deepseek-vk-24102f", "model": "deepseek-r1"},
                        ],
                    },
                    "code.generation": {
                        "primary": {"vk": "deepseek-vk-24102f", "model": "deepseek-coder"},
                        "fallbacks": [
                            {"vk": "vkj-openrouter-cc4151", "model": "qwen-3-coder-plus"},
                            {"vk": "openai-vk-190a60", "model": "gpt-4o"},
                        ],
                    },
                    "research.web": {
                        "primary": {"vk": "perplexity-vk-56c172", "model": "sonar-large"},
                        "fallbacks": [
                            {"vk": "gemini-vk-3d6108", "model": "gemini-2.0-pro"},
                            {"vk": "xai-vk-e65d0f", "model": "grok-5"},
                        ],
                    },
                },
            },
        }

    def get_client(self, provider: str) -> Portkey:
        """
        Get Portkey client for a specific provider

        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')

        Returns:
            Configured Portkey client
        """
        if provider not in self._clients:
            vk = self.VIRTUAL_KEYS.get(provider)
            if not vk:
                raise ValueError(f"Unknown provider: {provider}")

            self._clients[provider] = Portkey(
                api_key=self.portkey_api_key,
                virtual_key=vk,
                cache=True,
                retry={"attempts": 3, "on_status_codes": [429, 500, 502, 503, 504]},
                metadata={"app": "sophia-intel-ai", "provider": provider},
            )

        return self._clients[provider]

    def route_request(
        self,
        task_type: TaskType,
        estimated_tokens: int = 0,
        require_streaming: bool = False,
        max_cost_usd: float = 1.0,
        prefer_provider: Optional[str] = None,
    ) -> RoutingDecision:
        """
        Intelligently route a request to the best provider

        Args:
            task_type: Type of task to perform
            estimated_tokens: Estimated tokens for the request
            require_streaming: Whether streaming is required
            max_cost_usd: Maximum allowed cost
            prefer_provider: Preferred provider if any

        Returns:
            Routing decision with primary and fallback options
        """
        # Map task type to configuration key
        route_key = self._get_route_key(task_type)

        # Get route configuration
        route_config = self.config["model_policy"]["routes"].get(
            route_key, self._get_default_route(task_type)
        )

        # Extract primary and fallbacks
        primary = route_config["primary"]
        fallbacks = route_config.get("fallbacks", [])

        # Apply preferences
        if prefer_provider and prefer_provider in self.VIRTUAL_KEYS:
            # Move preferred provider to front if it's in the list
            primary = {
                "vk": self.VIRTUAL_KEYS[prefer_provider],
                "model": self._get_default_model(prefer_provider),
            }

        # Estimate cost
        estimated_cost = self._estimate_cost(primary["model"], estimated_tokens)

        # Check cost constraint
        if estimated_cost > max_cost_usd:
            logger.warning(
                f"Estimated cost ${estimated_cost:.2f} exceeds limit ${max_cost_usd:.2f}"
            )
            # Switch to cheaper option
            primary = self._find_cheaper_alternative(task_type, max_cost_usd)

        # Build fallback configs
        fallback_configs = [self._build_model_config(fb["vk"], fb["model"]) for fb in fallbacks]

        return RoutingDecision(
            provider=self._vk_to_provider(primary["vk"]),
            model=primary["model"],
            virtual_key=primary["vk"],
            reason=f"Selected for {task_type.value} task",
            estimated_cost=estimated_cost,
            fallbacks=fallback_configs,
        )

    def _get_route_key(self, task_type: TaskType) -> str:
        """Map task type to route configuration key"""
        mapping = {
            TaskType.ORCHESTRATION: "orchestration.long_planning",
            TaskType.LONG_PLANNING: "orchestration.long_planning",
            TaskType.CODE_GENERATION: "code.generation",
            TaskType.CODE_REVIEW: "code.review",
            TaskType.WEB_RESEARCH: "research.web",
            TaskType.EMBEDDING: "embeddings.default",
            TaskType.RERANKING: "rerank.default",
            TaskType.DRAFT: "fast.draft",
            TaskType.GENERAL: "fast.draft",
        }
        return mapping.get(task_type, "fast.draft")

    def _get_default_route(self, task_type: TaskType) -> dict[str, Any]:
        """Get default route for a task type"""
        # Default to GPT-4o for most tasks
        return {
            "primary": {"vk": "openai-vk-190a60", "model": "gpt-4o"},
            "fallbacks": [
                {"vk": "anthropic-vk-b42804", "model": "claude-3-sonnet"},
                {"vk": "gemini-vk-3d6108", "model": "gemini-2.0-flash"},
            ],
        }

    def _vk_to_provider(self, virtual_key: str) -> str:
        """Convert virtual key back to provider name"""
        for provider, vk in self.VIRTUAL_KEYS.items():
            if vk == virtual_key:
                return provider
        return "unknown"

    def _get_default_model(self, provider: str) -> str:
        """Get default model for a provider"""
        defaults = {
            "openai": "gpt-4o",
            "anthropic": "claude-3-sonnet",
            "deepseek": "deepseek-coder",
            "groq": "llama3-70b",
            "gemini": "gemini-2.0-flash",
            "perplexity": "sonar-large",
        }
        return defaults.get(provider, "default")

    def _estimate_cost(self, model: str, tokens: int) -> float:
        """Estimate cost for a model and token count"""
        # Cost per 1K tokens (rough estimates)
        costs = {
            "gpt-5": 0.10,
            "gpt-4o": 0.03,
            "gpt-4o-mini": 0.002,
            "claude-3-opus": 0.075,
            "claude-3-sonnet": 0.018,
            "claude-3-haiku": 0.0008,
            "deepseek-coder": 0.001,
            "gemini-2.0-pro": 0.02,
            "gemini-2.0-flash": 0.001,
            "llama3-70b": 0.0008,
            "sonar-large": 0.005,
        }

        cost_per_1k = costs.get(model, 0.01)
        return (tokens / 1000) * cost_per_1k

    def _find_cheaper_alternative(self, task_type: TaskType, max_cost: float) -> dict[str, str]:
        """Find a cheaper alternative model"""
        # Fast tier models for cost optimization
        return {"vk": "groq-vk-6b9b52", "model": "llama3-70b"}

    def _build_model_config(self, virtual_key: str, model: str) -> ModelConfig:
        """Build a ModelConfig object"""
        provider = self._vk_to_provider(virtual_key)
        return ModelConfig(
            provider=provider,
            model=model,
            virtual_key=virtual_key,
            cost_per_1k_tokens=self._estimate_cost(model, 1000),
        )

    async def execute_with_fallback(
        self, task_type: TaskType, messages: list[dict[str, str]], **kwargs
    ) -> dict[str, Any]:
        """
        Execute a request with automatic fallback on failure

        Args:
            task_type: Type of task
            messages: Chat messages
            **kwargs: Additional parameters

        Returns:
            Response from successful provider
        """
        routing = self.route_request(
            task_type=task_type, estimated_tokens=kwargs.get("max_tokens", 1000)
        )

        # Try primary
        try:
            client = self.get_client(routing.provider)
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=routing.model,
                messages=messages,
                **kwargs,
            )
            self._record_usage(routing.provider, routing.model, response.usage)
            return response
        except Exception as e:
            logger.warning(f"Primary provider {routing.provider} failed: {e}")

        # Try fallbacks
        for fallback in routing.fallbacks:
            try:
                client = self.get_client(fallback.provider)
                response = await asyncio.to_thread(
                    client.chat.completions.create,
                    model=fallback.model,
                    messages=messages,
                    **kwargs,
                )
                self._record_usage(fallback.provider, fallback.model, response.usage)
                logger.info(f"Succeeded with fallback: {fallback.provider}/{fallback.model}")
                return response
            except Exception as e:
                logger.warning(f"Fallback {fallback.provider} failed: {e}")
                continue

        raise Exception("All providers failed")

    async def embed_texts(
        self,
        texts: list[str],
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> list[list[float]]:
        """Generate embeddings with provider, fallback to local if needed.

        Provider/model resolution order:
        - Explicit args
        - EMBEDDING_PROVIDER / EMBEDDING_MODEL
        - LLM_EMBEDDING_PROVIDER / LLM_EMBEDDING_MODEL
        - Defaults: openai + text-embedding-3-small
        """
        prov = (
            provider
            or os.getenv("EMBEDDING_PROVIDER")
            or os.getenv("LLM_EMBEDDING_PROVIDER")
            or "openai"
        )
        mdl = (
            model
            or os.getenv("EMBEDDING_MODEL")
            or os.getenv("LLM_EMBEDDING_MODEL")
            or "text-embedding-3-small"
        )

        try:
            client = self.get_client(prov)
            # Portkey proxies provider SDKs; use embeddings API
            resp = await asyncio.to_thread(
                client.embeddings.create,
                model=mdl,
                input=texts,
            )
            # OpenAI-compatible structure: resp may be object or dict
            data = (
                getattr(resp, "data", None)
                if hasattr(resp, "data")
                else (resp.get("data") if isinstance(resp, dict) else None)
            ) or []
            vectors = [
                (
                    getattr(item, "embedding", None)
                    if hasattr(item, "embedding")
                    else item.get("embedding")
                )
                for item in data
            ]
            # Validate shape; trigger fallback if invalid
            if not vectors or not isinstance(vectors[0], list):
                raise ValueError("Embedding response in unexpected format")
            # Ensure all produced
            if len(vectors) == len(texts) and all(v is not None for v in vectors):
                return vectors  # type: ignore[return-value]
            raise ValueError("Embedding provider returned incomplete vectors")
        except Exception as e:
            logger.warning(f"Embedding provider '{prov}' failed; using local fallback: {e}")
            return self._local_embed(texts)

    def _local_embed(self, texts: list[str], dim: int = 256) -> list[list[float]]:
        """Very simple local hash-based embedding as a safety fallback.
        Not semantically meaningful, but stable and deterministic for indexing.
        """
        import hashlib
        import math

        vectors: list[list[float]] = []
        for t in texts:
            v = [0.0] * dim
            # Hash tokens into buckets
            for tok in t.split():
                h = int(hashlib.sha256(tok.encode()).hexdigest()[:8], 16)
                idx = h % dim
                v[idx] += 1.0
            # L2 normalize
            norm = math.sqrt(sum(x * x for x in v)) or 1.0
            v = [x / norm for x in v]
            vectors.append(v)
        return vectors

    async def execute_manual(
        self, provider: str, model: str, messages: list[dict[str, str]], **kwargs
    ) -> dict[str, Any]:
        """
        Execute a request against an explicit provider/model without any routing or fallback.

        Args:
            provider: Provider key (e.g., 'openai','anthropic','groq','openrouter', etc.)
            model: Exact model ID for that provider
            messages: Chat messages
            **kwargs: Additional parameters passed to chat.completions.create

        Returns:
            Response from provider
        """
        client = self.get_client(provider)
        response = await asyncio.to_thread(
            client.chat.completions.create, model=model, messages=messages, **kwargs
        )
        self._record_usage(provider, model, getattr(response, "usage", None))
        return response

    def _record_usage(self, provider: str, model: str, usage: Any) -> None:
        """Record usage statistics"""
        key = f"{provider}/{model}"
        if key not in self._usage_stats:
            self._usage_stats[key] = {"requests": 0, "total_tokens": 0, "total_cost": 0.0}

        stats = self._usage_stats[key]
        stats["requests"] += 1
        if usage:
            tokens = getattr(usage, "total_tokens", 0)
            stats["total_tokens"] += tokens
            stats["total_cost"] += self._estimate_cost(model, tokens)

    def get_usage_report(self) -> dict[str, Any]:
        """Get usage statistics report"""
        total_cost = sum(s["total_cost"] for s in self._usage_stats.values())
        total_requests = sum(s["requests"] for s in self._usage_stats.values())

        return {
            "total_cost_usd": total_cost,
            "total_requests": total_requests,
            "by_provider": self._usage_stats,
            "top_models": sorted(
                self._usage_stats.items(), key=lambda x: x[1]["requests"], reverse=True
            )[:5],
        }

    def validate_virtual_keys(self) -> dict[str, bool]:
        """
        Validate that all virtual keys are accessible

        Returns:
            Dictionary of provider to validation status
        """
        results = {}
        for provider, vk in self.VIRTUAL_KEYS.items():
            try:
                client = self.get_client(provider)
                # Test with a minimal request
                # Note: This is just checking client creation, not actual API call
                results[provider] = True
            except Exception as e:
                logger.error(f"Virtual key validation failed for {provider}: {e}")
                results[provider] = False

        return results


# Global instance for convenience
_portkey_manager = None


def get_portkey_manager() -> PortkeyManager:
    """Get global PortkeyManager instance"""
    global _portkey_manager
    if _portkey_manager is None:
        _portkey_manager = PortkeyManager()
    return _portkey_manager
