"""
Dynamic Portkey Client with Latest OpenRouter Models (August 2025).
Automatically adapts to model availability and manages fallbacks.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Union

from openai import AsyncOpenAI
from portkey_ai import PORTKEY_GATEWAY_URL, Portkey

from app.core.circuit_breaker import with_circuit_breaker

from .openrouter_latest import ModelTier, OpenRouterLatest, TaskType

logger = logging.getLogger(__name__)


class DynamicPortkeyClient:
    """
    Dynamic Portkey client that automatically manages latest OpenRouter models.
    Features:
    - Automatic model updates from OpenRouter
    - Intelligent fallback chains
    - Cost optimization
    - Health monitoring
    - Deprecated model handling
    """

    @with_circuit_breaker("external_api")
    def __init__(
        self, portkey_api_key: str, openrouter_api_key: str, config_path: Optional[str] = None
    ):
        """
        Initialize dynamic Portkey client.

        Args:
            portkey_api_key: Portkey API key
            openrouter_api_key: OpenRouter API key
            config_path: Path to dynamic config JSON (optional)
        """
        self.portkey_key = portkey_api_key
        self.openrouter_key = openrouter_api_key

        # Load dynamic configuration
        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                self.config = json.load(f)
        else:
            # Load default config
            default_config_path = Path(__file__).parent.parent / "config" / "portkey_dynamic.json"
            with open(default_config_path) as f:
                self.config = json.load(f)

        # Initialize OpenRouter client for model management
        self.openrouter = OpenRouterLatest(api_key=openrouter_api_key, app_name="Sophia-Intel-AI")

        # Initialize Portkey client
        self.client = Portkey(api_key=portkey_api_key, config=self._generate_portkey_config())

        # Alternative: Use OpenAI client with Portkey headers
        self.openai_client = AsyncOpenAI(
            api_key=portkey_api_key,
            base_url=PORTKEY_GATEWAY_URL,
            default_headers={"x-portkey-config": json.dumps(self._generate_portkey_config())},
        )

        # Model cache and health tracking
        self.model_cache = {}
        self.last_refresh = None
        self.health_status = {}

    @with_circuit_breaker("external_api")
    def _generate_portkey_config(self) -> dict[str, Any]:
        """Generate Portkey configuration with OpenRouter virtual key."""
        return {
            "provider": "openrouter",
            "api_key": self.openrouter_key,
            "override_params": {
                "headers": {"HTTP-Referer": "http://localhost:3000", "X-Title": "Sophia-Intel-AI"}
            },
            "retry": {"attempts": 3, "on_status_codes": [429, 502, 503]},
        }

    @with_circuit_breaker("external_api")
    async def refresh_models(self) -> None:
        """Refresh available models from OpenRouter."""
        self.model_cache = await self.openrouter.refresh_model_cache()
        self.last_refresh = datetime.now()
        logger.info(f"Refreshed model cache: {len(self.model_cache)} models available")

    @with_circuit_breaker("external_api")
    async def get_model_for_task(
        self,
        task: Union[str, TaskType] = TaskType.GENERAL,
        budget: Union[str, ModelTier] = ModelTier.BALANCED,
    ) -> str:
        """
        Get the best available model for a specific task.

        Args:
            task: Task type (reasoning, coding, creative, etc.)
            budget: Budget tier (premium, balanced, free)

        Returns:
            Model ID string
        """
        # Convert strings to enums if needed
        if isinstance(task, str):
            task = TaskType[task.upper()]
        if isinstance(budget, str):
            budget = ModelTier[budget.upper()]

        # Refresh cache if needed
        if not self.model_cache or self._should_refresh():
            await self.refresh_models()

        # Get best model from OpenRouter client
        return await self.openrouter.get_best_model(task, budget)

    def _should_refresh(self) -> bool:
        """Check if model cache needs refreshing."""
        if not self.last_refresh:
            return True
        return datetime.now() - self.last_refresh > timedelta(hours=6)

    @with_circuit_breaker("external_api")
    async def create_completion(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        task: Union[str, TaskType] = TaskType.GENERAL,
        budget: Union[str, ModelTier] = ModelTier.BALANCED,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Create chat completion with dynamic model selection.

        Args:
            messages: Chat messages
            model: Specific model or semantic name (e.g., "latest-gpt", "best-coding")
            task: Task type if model not specified
            budget: Budget tier if model not specified
            **kwargs: Additional OpenAI API parameters

        Returns:
            API response dict
        """
        # Handle semantic model names
        if model and model in self.config.get("model_aliases", {}):
            model = self.config["model_aliases"][model]

        # Handle deprecated models
        if model and model in self.config.get("deprecated_mappings", {}):
            old_model = model
            model = self.config["deprecated_mappings"][model]
            logger.warning(f"Model {old_model} is deprecated, using {model} instead")

        # Auto-select model if not specified
        if not model:
            model = await self.get_model_for_task(task, budget)

        # Create completion with fallback
        return await self.openrouter.create_completion_with_fallback(
            messages=messages,
            model=model,
            task=TaskType[task.upper()] if isinstance(task, str) else task,
            tier=ModelTier[budget.upper()] if isinstance(budget, str) else budget,
            **kwargs,
        )

    async def create_completion_with_metadata(
        self, messages: list[dict[str, str]], metadata: dict[str, Any], **kwargs
    ) -> dict[str, Any]:
        """
        Create completion with metadata-driven routing.

        Args:
            messages: Chat messages
            metadata: Routing metadata (priority, budget, environment, etc.)
            **kwargs: Additional API parameters

        Returns:
            API response dict
        """
        # Determine model based on metadata
        if metadata.get("priority") == "critical" and metadata.get("budget", 0) >= 100:
            model = "openai/gpt-5"
        elif metadata.get("cost_sensitive"):
            model = "deepseek/deepseek-chat-v3.1:free"
        elif metadata.get("require_vision"):
            model = "google/gemini-2.5-flash-image-preview"
        elif metadata.get("require_reasoning"):
            model = "deepseek/deepseek-r1"
        else:
            # Use task-based selection
            task = TaskType[metadata.get("task", "general").upper()]
            budget = ModelTier[metadata.get("tier", "balanced").upper()]
            model = await self.get_model_for_task(task, budget)

        # Add metadata to request
        kwargs["metadata"] = metadata

        return await self.create_completion(messages=messages, model=model, **kwargs)

    async def stream_completion(
        self, messages: list[dict[str, str]], model: Optional[str] = None, **kwargs
    ):
        """
        Stream chat completion with dynamic model selection.

        Args:
            messages: Chat messages
            model: Model ID or semantic name
            **kwargs: Additional API parameters

        Yields:
            Streaming response chunks
        """
        # Handle model selection
        if not model:
            model = await self.get_model_for_task()

        # Handle semantic names
        if model in self.config.get("model_aliases", {}):
            model = self.config["model_aliases"][model]

        # Create streaming request
        kwargs["stream"] = True

        response = await self.openai_client.chat.completions.create(
            model=model, messages=messages, **kwargs
        )

        async for chunk in response:
            yield chunk

    @with_circuit_breaker("external_api")
    async def check_model_health(self, model_id: str) -> dict[str, Any]:
        """
        Check health status of a specific model.

        Args:
            model_id: Model identifier

        Returns:
            Health status dict
        """
        health = await self.openrouter.check_model_health(model_id)

        self.health_status[model_id] = {
            "available": health,
            "checked_at": datetime.now().isoformat(),
            "model_info": self.openrouter.get_model_info(model_id),
        }

        return self.health_status[model_id]

    async def monitor_all_models(self) -> dict[str, Any]:
        """
        Monitor health of all configured models.

        Returns:
            Health report for all models
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "models": {},
            "summary": {"total": 0, "available": 0, "unavailable": 0},
        }

        # Check all models in config
        all_models = set()

        # Add role models
        for model in self.config.get("role_models", {}).values():
            all_models.add(model)

        # Add pool models
        for pool in self.config.get("model_pools", {}).values():
            all_models.update(pool)

        # Check each model
        for model_id in all_models:
            health = await self.check_model_health(model_id)
            report["models"][model_id] = health
            report["summary"]["total"] += 1

            if health["available"]:
                report["summary"]["available"] += 1
            else:
                report["summary"]["unavailable"] += 1

        return report

    @with_circuit_breaker("external_api")
    def estimate_cost(self, model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate cost for a completion.

        Args:
            model_id: Model identifier
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            Estimated cost in USD
        """
        return self.openrouter.estimate_cost(model_id, prompt_tokens, completion_tokens)

    @with_circuit_breaker("external_api")
    async def get_available_models(
        self, tier: Optional[Union[str, ModelTier]] = None, max_cost: Optional[float] = None
    ) -> list[str]:
        """
        Get list of available models matching criteria.

        Args:
            tier: Model tier filter
            max_cost: Maximum cost per 1M tokens

        Returns:
            List of model IDs
        """
        if isinstance(tier, str):
            tier = ModelTier[tier.upper()]

        # Refresh if needed
        if self._should_refresh():
            await self.refresh_models()

        return self.openrouter.get_available_models(tier, max_cost)

    async def benchmark_models(
        self, prompt: str, models: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """
        Benchmark response time and quality across models.

        Args:
            prompt: Test prompt
            models: List of models to test (or use defaults)

        Returns:
            Benchmark results
        """
        if not models:
            # Use a representative sample
            models = [
                "openai/gpt-5-mini",
                "anthropic/claude-3.7-sonnet",
                "deepseek/deepseek-chat-v3.1",
                "google/gemini-2.5-flash",
                "deepseek/deepseek-chat-v3.1:free",
            ]

        results = {}

        for model_id in models:
            try:
                start_time = datetime.now()

                response = await self.create_completion(
                    messages=[{"role": "user", "content": prompt}],
                    model=model_id,
                    max_tokens=100,
                    temperature=0.7,
                )

                elapsed = (datetime.now() - start_time).total_seconds()

                results[model_id] = {
                    "success": True,
                    "response_time": elapsed,
                    "tokens_used": response.get("usage", {}),
                    "cost": self.estimate_cost(
                        model_id,
                        response.get("usage", {}).get("prompt_tokens", 0),
                        response.get("usage", {}).get("completion_tokens", 0),
                    ),
                }

            except Exception as e:
                results[model_id] = {"success": False, "error": str(e)}

        return results


# Convenience functions
@with_circuit_breaker("external_api")
async def create_dynamic_client() -> DynamicPortkeyClient:
    """Create a dynamic Portkey client with environment configuration."""
    from dotenv import load_dotenv

    load_dotenv(".env.local")

    return DynamicPortkeyClient(
        portkey_api_key=os.getenv("PORTKEY_API_KEY"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
    )


async def quick_completion(prompt: str, task: str = "general", budget: str = "balanced") -> str:
    """Quick helper for single completions."""
    client = await create_dynamic_client()

    response = await client.create_completion(
        messages=[{"role": "user", "content": prompt}], task=task, budget=budget
    )

    return response["choices"][0]["message"]["content"]
