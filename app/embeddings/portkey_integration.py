"""
Portkey Integration for Sophia Intel AI
Unified gateway for all LLM and embedding providers
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, Optional, Union

from pydantic import BaseModel, Field

from app.core.ai_logger import logger

logger = logging.getLogger(__name__)

# ============================================
# Virtual Key Management
# ============================================

@dataclass
class VirtualKeyConfig:
    """Virtual key configuration for secure API management"""
    provider: str
    key_alias: str
    is_active: bool = True
    rate_limit: Optional[int] = None
    monthly_quota: Optional[float] = None
    metadata: dict[str, Any] = None

class PortkeyVirtualKeyManager:
    """
    Manages virtual keys for secure API access
    Virtual keys mask actual API keys for security
    """

    def __init__(self):
        self.virtual_keys = self._load_virtual_keys()

    def _load_virtual_keys(self) -> dict[str, VirtualKeyConfig]:
        """Load virtual key configurations from environment"""
        keys = {}

        # Together AI virtual key
        if together_key := os.getenv("TOGETHER_VK"):
            keys["together"] = VirtualKeyConfig(
                provider="together",
                key_alias=together_key,
                rate_limit=1000,  # requests per minute
                monthly_quota=100.0,  # dollars
                metadata={"models": ["BAAI/*", "togethercomputer/*", "intfloat/*"]}
            )

        # OpenAI virtual key
        if openai_key := os.getenv("OPENAI_VK"):
            keys["openai"] = VirtualKeyConfig(
                provider="openai",
                key_alias=openai_key,
                rate_limit=500,
                monthly_quota=500.0,
                metadata={"models": ["text-embedding-*", "gpt-*"]}
            )

        # XAI (Grok) virtual key
        if xai_key := os.getenv("XAI_VK"):
            keys["xai"] = VirtualKeyConfig(
                provider="xai",
                key_alias=xai_key,
                rate_limit=1000,
                monthly_quota=50.0,
                metadata={"models": ["grok-*"]}
            )

        # OpenRouter virtual key
        if openrouter_key := os.getenv("OPENROUTER_VK"):
            keys["openrouter"] = VirtualKeyConfig(
                provider="openrouter",
                key_alias=openrouter_key,
                rate_limit=100,
                monthly_quota=200.0,
                metadata={"models": ["*"]}
            )

        return keys

    def get_virtual_key(self, provider: str) -> Optional[str]:
        """Get virtual key for provider"""
        if config := self.virtual_keys.get(provider):
            if config.is_active:
                return config.key_alias
        return None

    def get_active_providers(self) -> list[str]:
        """Get list of active providers"""
        return [
            provider for provider, config in self.virtual_keys.items()
            if config.is_active
        ]

# ============================================
# Portkey Configuration Builder
# ============================================

class PortkeyConfigBuilder:
    """
    Builds Portkey configurations for different use cases
    Following best practices from Agno documentation
    """

    @staticmethod
    def build_embedding_config(
        provider: str,
        virtual_key: str,
        cache_enabled: bool = True,
        retry_enabled: bool = True
    ) -> dict[str, Any]:
        """
        Build Portkey configuration for embeddings
        
        Args:
            provider: Provider name (together, openai, etc.)
            virtual_key: Virtual key for the provider
            cache_enabled: Enable caching
            retry_enabled: Enable retries
            
        Returns:
            Portkey configuration dictionary
        """
        config = {
            "provider": provider,
            "virtual_key": virtual_key,
        }

        if cache_enabled:
            config["cache"] = {
                "mode": "semantic",
                "max_age": 3600,
            }

        if retry_enabled:
            config["retry"] = {
                "attempts": 3,
                "on_status_codes": [429, 500, 502, 503],
            }

        # Provider-specific optimizations
        if provider == "together":
            config["metadata"] = {
                "user": "sophia-intel-ai",
                "purpose": "embeddings",
            }
        elif provider == "openai":
            config["forward_headers"] = ["x-request-id"]

        return config

    @staticmethod
    def build_llm_config(
        provider: str,
        virtual_key: str,
        mode: str = "single",
        fallback_providers: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """
        Build Portkey configuration for LLM calls
        
        Args:
            provider: Primary provider
            virtual_key: Virtual key
            mode: Mode (single, loadbalance, fallback)
            fallback_providers: List of fallback providers
            
        Returns:
            Portkey configuration dictionary
        """
        config = {
            "mode": mode,
            "provider": provider,
            "virtual_key": virtual_key,
            "retry": {
                "attempts": 3,
                "on_status_codes": [429, 500, 502, 503],
            },
            "cache": {
                "mode": "simple",
                "max_age": 300,
            }
        }

        if mode == "fallback" and fallback_providers:
            config["fallbacks"] = [
                {"provider": p, "virtual_key": f"vk-{p}"}
                for p in fallback_providers
            ]
        elif mode == "loadbalance":
            config["loadbalance"] = {
                "strategy": "round_robin",
                "providers": [provider] + (fallback_providers or [])
            }

        return config

# ============================================
# Portkey Request Wrapper
# ============================================

class PortkeyRequest(BaseModel):
    """Standardized Portkey request format"""
    model: str
    input: Union[list[str], str]
    portkey_config: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)
    options: dict[str, Any] = Field(default_factory=dict)

class PortkeyResponse(BaseModel):
    """Standardized Portkey response format"""
    data: list[dict[str, Any]]
    model: str
    usage: dict[str, int]
    latency_ms: float
    cached: bool = False
    provider_used: str
    metadata: dict[str, Any] = Field(default_factory=dict)

# ============================================
# Portkey Gateway Client
# ============================================

class PortkeyGateway:
    """
    Unified gateway client for all AI providers
    Implements Agno best practices for production use
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PORTKEY_API_KEY")
        self.base_url = "https://api.portkey.ai/v1"
        self.key_manager = PortkeyVirtualKeyManager()
        self.config_builder = PortkeyConfigBuilder()
        self._client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize OpenAI-compatible client for Portkey"""
        try:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                default_headers={
                    "x-portkey-api-key": self.api_key,
                }
            )
            logger.info("Initialized Portkey gateway client")
        except ImportError:
            logger.warning("OpenAI client not available")
            self._client = None

    async def create_embeddings(
        self,
        texts: list[str],
        model: str,
        provider: str = "together",
        use_cache: bool = True
    ) -> PortkeyResponse:
        """
        Create embeddings through Portkey gateway
        
        Args:
            texts: Texts to embed
            model: Model ID
            provider: Provider to use
            use_cache: Enable caching
            
        Returns:
            PortkeyResponse with embeddings
        """
        # Get virtual key
        virtual_key = self.key_manager.get_virtual_key(provider)
        if not virtual_key:
            raise ValueError(f"No virtual key for provider: {provider}")

        # Build configuration
        portkey_config = self.config_builder.build_embedding_config(
            provider=provider,
            virtual_key=virtual_key,
            cache_enabled=use_cache
        )

        # Create request
        request = PortkeyRequest(
            model=model,
            input=texts,
            portkey_config=portkey_config,
            metadata={
                "source": "sophia-intel-ai",
                "type": "embedding",
                "batch_size": len(texts)
            }
        )

        # Execute request
        if self._client:
            try:
                import time
                start_time = time.perf_counter()

                response = await self._client.embeddings.create(
                    model=request.model,
                    input=request.input,
                    extra_body={"portkey_config": request.portkey_config}
                )

                latency_ms = (time.perf_counter() - start_time) * 1000

                return PortkeyResponse(
                    data=[{"embedding": item.embedding} for item in response.data],
                    model=request.model,
                    usage={"total_tokens": response.usage.total_tokens},
                    latency_ms=latency_ms,
                    provider_used=provider,
                    metadata=request.metadata
                )

            except Exception as e:
                logger.error(f"Embedding request failed: {e}")
                raise
        else:
            # Mock response for testing
            import numpy as np
            mock_embeddings = []
            for text in texts:
                np.random.seed(hash(text) % 2**32)
                embedding = np.random.randn(768).tolist()
                mock_embeddings.append({"embedding": embedding})

            return PortkeyResponse(
                data=mock_embeddings,
                model=model,
                usage={"total_tokens": sum(len(t.split()) for t in texts)},
                latency_ms=10.0,
                provider_used=provider,
                metadata=request.metadata
            )

    async def create_completion(
        self,
        prompt: str,
        model: str,
        provider: str = "openrouter",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        fallback_providers: Optional[list[str]] = None
    ) -> PortkeyResponse:
        """
        Create LLM completion through Portkey gateway
        
        Args:
            prompt: Input prompt
            model: Model ID
            provider: Primary provider
            max_tokens: Maximum tokens
            temperature: Temperature
            fallback_providers: Fallback providers
            
        Returns:
            PortkeyResponse with completion
        """
        # Get virtual key
        virtual_key = self.key_manager.get_virtual_key(provider)
        if not virtual_key:
            raise ValueError(f"No virtual key for provider: {provider}")

        # Build configuration
        mode = "fallback" if fallback_providers else "single"
        portkey_config = self.config_builder.build_llm_config(
            provider=provider,
            virtual_key=virtual_key,
            mode=mode,
            fallback_providers=fallback_providers
        )

        # Create request
        request = PortkeyRequest(
            model=model,
            input=prompt,
            portkey_config=portkey_config,
            options={
                "max_tokens": max_tokens,
                "temperature": temperature
            },
            metadata={
                "source": "sophia-intel-ai",
                "type": "completion"
            }
        )

        # Execute request
        if self._client:
            try:
                import time
                start_time = time.perf_counter()

                response = await self._client.chat.completions.create(
                    model=request.model,
                    messages=[{"role": "user", "content": request.input}],
                    max_tokens=request.options["max_tokens"],
                    temperature=request.options["temperature"],
                    extra_body={"portkey_config": request.portkey_config}
                )

                latency_ms = (time.perf_counter() - start_time) * 1000

                return PortkeyResponse(
                    data=[{"text": response.choices[0].message.content}],
                    model=request.model,
                    usage={
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    },
                    latency_ms=latency_ms,
                    provider_used=provider,
                    metadata=request.metadata
                )

            except Exception as e:
                logger.error(f"Completion request failed: {e}")
                raise
        else:
            # Mock response for testing
            return PortkeyResponse(
                data=[{"text": f"Mock response for: {prompt[:50]}..."}],
                model=model,
                usage={"total_tokens": 100},
                latency_ms=50.0,
                provider_used=provider,
                metadata=request.metadata
            )

    def get_provider_status(self) -> dict[str, Any]:
        """Get status of all configured providers"""
        status = {}

        for provider in self.key_manager.get_active_providers():
            config = self.key_manager.virtual_keys[provider]
            status[provider] = {
                "active": config.is_active,
                "rate_limit": config.rate_limit,
                "monthly_quota": config.monthly_quota,
                "supported_models": config.metadata.get("models", [])
            }

        return status

# ============================================
# Example Usage
# ============================================

async def example_usage():
    """Example of using Portkey gateway"""

    # Initialize gateway
    gateway = PortkeyGateway()

    # Create embeddings via Together AI
    embedding_response = await gateway.create_embeddings(
        texts=["Hello world", "Test embedding"],
        model="BAAI/bge-large-en-v1.5",
        provider="together"
    )

    logger.info(f"Embeddings created: {len(embedding_response.data)} vectors")
    logger.info(f"Latency: {embedding_response.latency_ms:.2f}ms")

    # Create completion with fallback
    completion_response = await gateway.create_completion(
        prompt="Explain what AI agents are",
        model="gpt-4",
        provider="openai",
        fallback_providers=["anthropic", "openrouter"]
    )

    logger.info(f"Completion: {completion_response.data[0]['text'][:100]}...")

    # Check provider status
    status = gateway.get_provider_status()
    logger.info(f"Active providers: {list(status.keys())}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
