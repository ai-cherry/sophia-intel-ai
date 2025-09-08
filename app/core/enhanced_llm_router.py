"""
Enhanced LLM Router with AIMLAPI Integration
Provides intelligent routing between Portkey, AIMLAPI, and direct providers
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from openai import OpenAI

from app.core.aimlapi_config import aimlapi_manager

# Import existing managers
from app.core.portkey_config import ModelProvider, portkey_manager
from app.core.unified_keys import unified_keys

logger = logging.getLogger(__name__)


class LLMProviderType(Enum):
    """Types of LLM providers"""

    PORTKEY = "portkey"  # Via Portkey gateway
    AIMLAPI = "aimlapi"  # Via AIMLAPI (300+ models)
    DIRECT = "direct"  # Direct API access
    FALLBACK = "fallback"  # Automatic fallback chain


@dataclass
class ModelCapability:
    """Model capabilities for intelligent routing"""

    supports_vision: bool = False
    supports_tools: bool = False
    supports_reasoning: bool = False
    supports_streaming: bool = True
    supports_long_context: bool = False
    max_tokens: int = 4096
    context_window: int = 32768
    cost_tier: str = "standard"  # low, standard, premium


class EnhancedLLMRouter:
    """Enhanced router with AIMLAPI, Portkey, and direct access"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True

            # Initialize all providers
            self.portkey = portkey_manager
            self.aimlapi = aimlapi_manager
            self.keys = unified_keys

            # Direct clients cache
            self._direct_clients = {}

            # Priority ordering for provider selection
            self.provider_priority = {
                "premium": [
                    LLMProviderType.AIMLAPI,
                    LLMProviderType.PORTKEY,
                    LLMProviderType.DIRECT,
                ],
                "standard": [
                    LLMProviderType.PORTKEY,
                    LLMProviderType.AIMLAPI,
                    LLMProviderType.DIRECT,
                ],
                "budget": [
                    LLMProviderType.DIRECT,
                    LLMProviderType.PORTKEY,
                    LLMProviderType.AIMLAPI,
                ],
            }

            logger.info(
                "Enhanced LLM Router initialized with AIMLAPI, Portkey, and Direct access"
            )

    def get_best_model_for_task(
        self,
        task_type: str,
        require_vision: bool = False,
        require_tools: bool = False,
        require_reasoning: bool = False,
        require_long_context: bool = False,
        budget_mode: bool = False,
    ) -> dict[str, Any]:
        """Get the best model and provider for a specific task"""

        candidates = []

        # Check AIMLAPI models (premium options)
        if not budget_mode:
            # GPT-5 for most advanced tasks
            if require_reasoning or require_long_context:
                candidates.append(
                    {
                        "provider": LLMProviderType.AIMLAPI,
                        "model": "gpt-5",
                        "model_id": "openai/gpt-5-2025-08-07",
                        "priority": 1,
                        "capabilities": ModelCapability(
                            supports_vision=True,
                            supports_tools=True,
                            supports_reasoning=True,
                            supports_long_context=True,
                            max_tokens=65536,
                            context_window=256000,
                            cost_tier="premium",
                        ),
                    }
                )

            # Grok-4 for alternative advanced tasks
            if require_vision or require_reasoning:
                candidates.append(
                    {
                        "provider": LLMProviderType.AIMLAPI,
                        "model": "grok-4",
                        "model_id": "x-ai/grok-4-07-09",
                        "priority": 2,
                        "capabilities": ModelCapability(
                            supports_vision=True,
                            supports_tools=True,
                            supports_reasoning=True,
                            max_tokens=32768,
                            context_window=131072,
                            cost_tier="premium",
                        ),
                    }
                )

            # O-series for pure reasoning
            if require_reasoning and not require_vision:
                candidates.append(
                    {
                        "provider": LLMProviderType.AIMLAPI,
                        "model": "o3",
                        "model_id": "openai/o3-2025-04-16",
                        "priority": 1,
                        "capabilities": ModelCapability(
                            supports_reasoning=True,
                            supports_tools=True,
                            max_tokens=100000,
                            context_window=256000,
                            cost_tier="premium",
                        ),
                    }
                )

        # Check Portkey models (standard options)
        if task_type == "coding":
            candidates.append(
                {
                    "provider": LLMProviderType.PORTKEY,
                    "model": "deepseek-coder",
                    "model_id": "deepseek-coder",
                    "priority": 3,
                    "capabilities": ModelCapability(
                        supports_tools=True,
                        max_tokens=16384,
                        context_window=128000,
                        cost_tier="standard",
                    ),
                }
            )

        # Standard models for general tasks
        candidates.append(
            {
                "provider": LLMProviderType.PORTKEY,
                "model": "gpt-4o",
                "model_id": "gpt-4o",
                "priority": 4,
                "capabilities": ModelCapability(
                    supports_vision=True,
                    supports_tools=True,
                    max_tokens=16384,
                    context_window=128000,
                    cost_tier="standard",
                ),
            }
        )

        # Budget options
        if budget_mode:
            candidates.append(
                {
                    "provider": LLMProviderType.AIMLAPI,
                    "model": "gpt-4o-mini",
                    "model_id": "gpt-4o-mini",
                    "priority": 5,
                    "capabilities": ModelCapability(
                        supports_tools=True,
                        max_tokens=16384,
                        context_window=128000,
                        cost_tier="low",
                    ),
                }
            )

        # Filter by requirements
        filtered = []
        for candidate in candidates:
            caps = candidate["capabilities"]
            if require_vision and not caps.supports_vision:
                continue
            if require_tools and not caps.supports_tools:
                continue
            if require_reasoning and not caps.supports_reasoning:
                continue
            if require_long_context and caps.context_window < 100000:
                continue
            filtered.append(candidate)

        # Sort by priority and return best
        if filtered:
            filtered.sort(key=lambda x: x["priority"])
            return filtered[0]

        # Default fallback
        return {
            "provider": LLMProviderType.PORTKEY,
            "model": "gpt-3.5-turbo",
            "model_id": "gpt-3.5-turbo",
            "priority": 10,
            "capabilities": ModelCapability(cost_tier="low"),
        }

    def create_completion(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        provider_type: Optional[LLMProviderType] = None,
        task_type: str = "chat",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> Any:
        """Create a completion using the best available provider"""

        # Auto-select model if not specified
        if not model:
            model_info = self.get_best_model_for_task(
                task_type=task_type,
                require_tools=bool(tools),
                budget_mode=kwargs.get("budget_mode", False),
            )
            provider_type = model_info["provider"]
            model = model_info["model_id"]

        # Default to PORTKEY if provider not specified
        if not provider_type:
            provider_type = LLMProviderType.PORTKEY

        try:
            # Route to appropriate provider
            if provider_type == LLMProviderType.AIMLAPI:
                return self._call_aimlapi(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream,
                    tools=tools,
                    **kwargs,
                )

            elif provider_type == LLMProviderType.PORTKEY:
                return self._call_portkey(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream,
                    tools=tools,
                    **kwargs,
                )

            elif provider_type == LLMProviderType.DIRECT:
                return self._call_direct(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream,
                    **kwargs,
                )

            else:
                # Fallback chain
                return self._call_with_fallback(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream,
                    tools=tools,
                    **kwargs,
                )

        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            # Try fallback
            if provider_type != LLMProviderType.FALLBACK:
                logger.info("Attempting fallback chain...")
                return self._call_with_fallback(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream,
                    tools=tools,
                    **kwargs,
                )
            raise

    def _call_aimlapi(self, model: str, messages: list[dict], **kwargs) -> Any:
        """Call AIMLAPI for GPT-5, Grok-4, and 300+ models"""
        # Map short names to full model IDs if needed
        model_mapping = {
            "gpt-5": "openai/gpt-5-2025-08-07",
            "gpt-5-mini": "openai/gpt-5-mini-2025-08-07",
            "grok-4": "x-ai/grok-4-07-09",
            "o3": "openai/o3-2025-04-16",
        }

        if model in model_mapping:
            model = model_mapping[model]

        return self.aimlapi.chat_completion(model=model, messages=messages, **kwargs)

    def _call_portkey(self, model: str, messages: list[dict], **kwargs) -> Any:
        """Call via Portkey gateway"""
        # Get appropriate provider for the model
        provider = None
        for p in ModelProvider:
            config = self.portkey.providers.get(p)
            if config and model in config.models:
                provider = p
                break

        if not provider:
            provider = ModelProvider.OPENAI  # Default

        client = self.portkey.get_client_for_provider(provider)
        return client.chat.completions.create(model=model, messages=messages, **kwargs)

    def _call_direct(self, model: str, messages: list[dict], **kwargs) -> Any:
        """Call provider directly without gateway"""
        # Determine provider from model name
        if "gpt" in model.lower():
            provider = "openai"
        elif "claude" in model.lower():
            provider = "anthropic"
        elif "llama" in model.lower():
            provider = "together"
        else:
            provider = "openrouter"  # Universal fallback

        # Get or create direct client
        if provider not in self._direct_clients:
            key_config = self.keys.get_key_for_provider(provider)
            if key_config:
                self._direct_clients[provider] = OpenAI(
                    api_key=key_config.key, base_url=key_config.base_url
                )

        if provider in self._direct_clients:
            return self._direct_clients[provider].chat.completions.create(
                model=model, messages=messages, **kwargs
            )

        raise ValueError(f"No direct client available for {provider}")

    def _call_with_fallback(self, **kwargs) -> Any:
        """Try multiple providers in sequence"""
        providers = [
            (LLMProviderType.PORTKEY, "gpt-4o-mini"),
            (LLMProviderType.AIMLAPI, "gpt-4o-mini"),
            (LLMProviderType.DIRECT, "gpt-3.5-turbo"),
        ]

        last_error = None
        for provider_type, fallback_model in providers:
            try:
                kwargs["model"] = kwargs.get("model", fallback_model)
                kwargs["provider_type"] = provider_type

                return self.create_completion(**kwargs)
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Fallback attempt with {provider_type} failed: {str(e)}"
                )
                continue

        raise last_error or Exception("All fallback attempts failed")

    def list_available_models(self) -> dict[str, list[str]]:
        """List all available models by provider"""
        return {
            "aimlapi": self.aimlapi.list_models(),
            "portkey": [
                model
                for provider in ModelProvider
                for model in self.portkey.providers.get(provider, {}).models
            ],
            "direct": list(self.keys.direct_api_keys.keys()),
        }

    def get_provider_status(self) -> dict[str, Any]:
        """Get status of all providers"""
        status = {
            "aimlapi": {
                "available": True,
                "models_count": len(self.aimlapi.list_models()),
                "flagship_models": ["gpt-5", "grok-4", "o3"],
                "api_key_set": bool(os.getenv("AIMLAPI_API_KEY")),
            },
            "portkey": {
                "available": True,
                "providers_count": len(self.portkey.providers),
                "api_key_set": bool(os.getenv("PORTKEY_API_KEY")),
            },
            "direct": {
                "available": True,
                "providers_count": len(self.keys.direct_api_keys),
            },
        }
        return status


# Singleton instance
enhanced_router = EnhancedLLMRouter()
