"""
Portkey Gateway Load Balance Configuration
Full multi-model swarm with intelligent routing and fallbacks
NO MOCKS - REAL API CALLS ONLY
"""

import logging
import os
import uuid
from typing import Any

from portkey_ai import Portkey

logger = logging.getLogger(__name__)

# ============================================
# PORTKEY MULTI-MODEL SWARM CONFIGURATION
# ============================================

PORTKEY_CONFIG = {
    "config_id": "pc-multi-model-swarm",
    "description": "Load balance across all requested models with intelligent routing",
    "strategy": {
        "mode": "loadbalance",
        "on_status_codes": [429, 500, 502, 503],
        "targets": [
            {
                "provider": "openrouter",
                "model": "openai/gpt-5",  # Primary for most important things
                "weight": 0.3,
                "override_params": {"temperature": 0.7, "max_tokens": 4096},
            },
            {
                "provider": "openrouter",
                "model": "x-ai/grok-4",  # Counter-reasoning
                "weight": 0.15,
                "override_params": {"temperature": 0.5, "max_tokens": 8192},
            },
            {
                "provider": "openrouter",
                "model": "x-ai/grok-code-fast-1",  # Fast coding
                "weight": 0.1,
                "override_params": {"temperature": 0.6, "max_tokens": 16384},
            },
            {
                "provider": "openrouter",
                "model": "deepseek/deepseek-chat-v3-0324",  # From your list
                "weight": 0.1,
                "override_params": {"temperature": 0.4, "max_tokens": 8192},
            },
            {
                "provider": "openrouter",
                "model": "nousresearch/hermes-4-405b",  # From your list
                "weight": 0.05,
                "override_params": {"temperature": 0.4, "max_tokens": 8192},
            },
            {
                "provider": "openrouter",
                "model": "qwen/qwen3-30b-a3b-thinking-2507",  # Thinking model
                "weight": 0.2,
                "override_params": {"temperature": 0.5, "max_tokens": 4096},
            },
            {
                "provider": "openrouter",
                "model": "qwen/qwen-2.5-coder-32b-instruct",  # Updated coder model
                "weight": 0.05,
                "override_params": {"temperature": 0.2, "max_tokens": 8192},
            },
            {
                "provider": "openrouter",
                "model": "openai/gpt-5",  # GPT-5 when available (will fallback)
                "weight": 0.05,
                "override_params": {"temperature": 0.7, "max_tokens": 8192},
            },
            {
                "provider": "openrouter",
                "model": "google/gemini-2.0-flash-exp:free",  # Free tier
                "weight": 0.03,
                "override_params": {"temperature": 0.5, "max_tokens": 4096},
            },
            {
                "provider": "openrouter",
                "model": "gpt-4o-mini",  # Fallback mini model
                "weight": 0.02,
                "override_params": {"temperature": 0.7, "max_tokens": 4096},
            },
        ],
    },
    "retry": {"attempts": 3, "on_status_codes": [429, 500, 502, 503], "exponential_backoff": True},
    "cache": {"enabled": True, "ttl": 3600, "mode": "semantic"},
    "timeout": {"request_timeout": 120, "stream_timeout": 300},
}

# Task-specific routing configurations
TASK_ROUTING = {
    "code_generation": {
        "primary": [
            "deepseek/deepseek-chat",
            "qwen/qwen-2.5-coder-32b-instruct",
            "x-ai/grok-code-fast-1",
        ],
        "fallback": ["openai/gpt-5-mini"],
    },
    "research_analysis": {
        "primary": [
            "x-ai/grok-5",  # Your favorite
            "qwen/qwen3-30b-a3b-thinking-2507",  # Your favorite
        ],
        "fallback": ["google/gemini-2.5-flash", "gpt-4o-mini"],
    },
    "creative_tasks": {
        "primary": ["x-ai/grok-code-fast-1", "google/gemini-2.5-flash"],
        "fallback": ["deepseek/deepseek-chat"],
    },
    "quick_responses": {
        "primary": ["google/gemini-2.5-flash", "google/gemini-2.0-flash-exp:free"],
        "fallback": ["openai/gpt-5-mini"],
    },
}


class PortkeyLoadBalancer:
    """
    Real Portkey Gateway with load balancing across multiple models.
    NO MOCKS - REAL API CALLS ONLY.
    """

    def __init__(self):
        """Initialize Portkey with real API keys and configuration."""

        self.portkey_api_key = os.getenv("PORTKEY_API_KEY")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

        if not self.portkey_api_key or not self.openrouter_api_key:
            raise ValueError("PORTKEY_API_KEY and OPENROUTER_API_KEY must be set")

        # Initialize Portkey client with virtual key
        self.client = Portkey(
            api_key=self.portkey_api_key,
            provider="openrouter",
            virtual_key="vkj-openrouter-cc4151",  # Portkey virtual key for OpenRouter
            config=PORTKEY_CONFIG,
        )

        logger.info("✅ Portkey Load Balancer initialized with REAL multi-model configuration")

    async def execute_with_routing(
        self,
        messages: list[dict[str, str]],
        task_type: str = "general",
        stream: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Execute request with intelligent task-based routing.

        Args:
            messages: Chat messages
            task_type: Type of task for routing
            stream: Whether to stream response
            **kwargs: Additional parameters

        Returns:
            Real API response from load-balanced models
        """

        # Get routing configuration for task type
        routing = TASK_ROUTING.get(task_type, {})
        primary_models = routing.get("primary", [])

        # Add metadata for tracking
        metadata = {
            "request_id": str(uuid.uuid4()),
            "task_type": task_type,
            "routing": "load_balanced",
            "primary_models": primary_models,
        }

        try:
            # Make REAL API call through Portkey
            logger.info(f"🚀 Executing load-balanced request for {task_type}")

            response = await self.client.chat.completions.create(
                messages=messages,
                model="auto",  # Let Portkey handle routing
                stream=stream,
                metadata=metadata,
                **kwargs,
            )

            logger.info("✅ Received REAL response from load-balanced models")

            if stream:
                return self._handle_stream(response)
            else:
                return {
                    "success": True,
                    "content": response.choices[0].message.content,
                    "model": response.model,
                    "usage": response.usage,
                    "metadata": metadata,
                    "real_api_call": True,
                    "load_balanced": True,
                }

        except Exception as e:
            logger.error(f"Load balancer error: {str(e)}")
            raise

    async def _handle_stream(self, stream):
        """Handle streaming responses from load balancer."""
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield {
                    "token": chunk.choices[0].delta.content,
                    "model": chunk.model if hasattr(chunk, "model") else "unknown",
                    "real_stream": True,
                }

    def get_model_for_task(self, task_type: str) -> str:
        """Get the best model for a specific task type."""
        routing = TASK_ROUTING.get(task_type, {})
        primary = routing.get("primary", [])

        if primary:
            return primary[0]
        else:
            # Default to Gemini Flash for general tasks
            return "google/gemini-2.5-flash"

    async def execute_on_specific_model(
        self, messages: list[dict[str, str]], model: str, **kwargs
    ) -> dict[str, Any]:
        """
        Execute on a specific model (bypassing load balancer).

        Args:
            messages: Chat messages
            model: Specific model to use
            **kwargs: Additional parameters

        Returns:
            Real API response from specified model
        """

        try:
            logger.info(f"🎯 Direct execution on {model}")

            response = await self.client.chat.completions.create(
                messages=messages,
                model=model,
                metadata={
                    "request_id": str(uuid.uuid4()),
                    "direct_model": model,
                    "routing": "direct",
                },
                **kwargs,
            )

            return {
                "success": True,
                "content": response.choices[0].message.content,
                "model": model,
                "usage": response.usage,
                "real_api_call": True,
                "direct_execution": True,
            }

        except Exception as e:
            logger.error(f"Direct execution error on {model}: {str(e)}")
            raise


# Global instance for immediate use
portkey_balancer = None


def initialize_portkey_balancer():
    """Initialize the global Portkey load balancer."""
    global portkey_balancer
    if not portkey_balancer:
        portkey_balancer = PortkeyLoadBalancer()
    return portkey_balancer


# Auto-initialize if environment variables are set
if os.getenv("PORTKEY_API_KEY") and os.getenv("OPENROUTER_API_KEY"):
    try:
        portkey_balancer = PortkeyLoadBalancer()
        logger.info("✅ Global Portkey Load Balancer initialized")
    except Exception as e:
        logger.warning(f"Could not auto-initialize Portkey: {e}")
