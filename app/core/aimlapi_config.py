"""
AIMLAPI Configuration and Management
Provides access to 300+ models including GPT-5, Grok-4, and more
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)


class AIMLModelFamily(Enum):
    """AIMLAPI model families"""

    # OpenAI Models
    GPT5 = "gpt5"
    GPT4 = "gpt4"
    GPT3 = "gpt3"
    O_SERIES = "o_series"

    # xAI Models
    GROK = "grok"

    # Anthropic Models
    CLAUDE = "claude"
    CLAUDE4 = "claude4"

    # Google Models
    GEMINI = "gemini"
    GEMINI25 = "gemini25"

    # Meta Models
    LLAMA = "llama"

    # Other Providers
    MISTRAL = "mistral"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    ZHIPU = "zhipu"

    # Specialized
    COHERE = "cohere"
    PERPLEXITY = "perplexity"
    MINIMAX = "minimax"
    MOONSHOT = "moonshot"
    NVIDIA = "nvidia"
    NOUS = "nous"
    ANTHRACITE = "anthracite"


@dataclass
class AIMLModelConfig:
    """Configuration for AIMLAPI models"""

    model_id: str
    family: AIMLModelFamily
    capabilities: List[str]
    context_window: int
    max_tokens: int
    supports_vision: bool = False
    supports_tools: bool = False
    supports_reasoning: bool = False
    supports_streaming: bool = True


class AIMLAPIManager:
    """Manager for AIMLAPI service with 300+ models"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.api_key = os.getenv("AIMLAPI_API_KEY", "562d964ac0b54357874b01de33cb91e9")
            self.base_url = os.getenv("AIMLAPI_BASE_URL", "https://api.aimlapi.com/v1")

            # Initialize OpenAI-compatible client
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

            # Define available models
            self.models = self._initialize_models()
            self._initialized = True
            logger.info(f"AIMLAPI Manager initialized with {len(self.models)} models")

    def _initialize_models(self) -> Dict[str, AIMLModelConfig]:
        """Initialize available AIMLAPI models - Updated with latest prioritized models"""
        return {
            # GPT-5 Series (Latest)
            "gpt-5": AIMLModelConfig(
                model_id="openai/gpt-5-2025-08-07",
                family=AIMLModelFamily.GPT5,
                capabilities=["chat", "reasoning", "vision", "tools"],
                context_window=256000,
                max_tokens=65536,
                supports_vision=True,
                supports_tools=True,
                supports_reasoning=True,
            ),
            "gpt-5-mini": AIMLModelConfig(
                model_id="openai/gpt-5-mini-2025-08-07",
                family=AIMLModelFamily.GPT5,
                capabilities=["chat", "reasoning", "tools"],
                context_window=128000,
                max_tokens=32768,
                supports_tools=True,
                supports_reasoning=True,
            ),
            "gpt-5-nano": AIMLModelConfig(
                model_id="openai/gpt-5-nano-2025-08-07",
                family=AIMLModelFamily.GPT5,
                capabilities=["chat", "tools"],
                context_window=64000,
                max_tokens=16384,
                supports_tools=True,
            ),
            "gpt-5-chat": AIMLModelConfig(
                model_id="openai/gpt-5-chat-latest",
                family=AIMLModelFamily.GPT5,
                capabilities=["chat", "vision", "tools"],
                context_window=256000,
                max_tokens=65536,
                supports_vision=True,
                supports_tools=True,
            ),
            # GPT-4.1 Series (Enhanced)
            "gpt-4.1": AIMLModelConfig(
                model_id="openai/gpt-4.1-2025-04-14",
                family=AIMLModelFamily.GPT4,
                capabilities=["chat", "vision", "tools"],
                context_window=128000,
                max_tokens=32768,
                supports_vision=True,
                supports_tools=True,
            ),
            "gpt-4.1-mini": AIMLModelConfig(
                model_id="openai/gpt-4.1-mini-2025-04-14",
                family=AIMLModelFamily.GPT4,
                capabilities=["chat", "tools"],
                context_window=64000,
                max_tokens=16384,
                supports_tools=True,
            ),
            # O-Series (Reasoning Models)
            "o4-mini": AIMLModelConfig(
                model_id="openai/o4-mini-2025-04-16",
                family=AIMLModelFamily.O_SERIES,
                capabilities=["chat", "reasoning", "tools"],
                context_window=128000,
                max_tokens=65536,
                supports_tools=True,
                supports_reasoning=True,
            ),
            "o3": AIMLModelConfig(
                model_id="openai/o3-2025-04-16",
                family=AIMLModelFamily.O_SERIES,
                capabilities=["chat", "reasoning", "tools"],
                context_window=256000,
                max_tokens=100000,
                supports_tools=True,
                supports_reasoning=True,
            ),
            "o3-pro": AIMLModelConfig(
                model_id="openai/o3-pro",
                family=AIMLModelFamily.O_SERIES,
                capabilities=["chat", "reasoning", "tools"],
                context_window=256000,
                max_tokens=100000,
                supports_tools=True,
                supports_reasoning=True,
            ),
            # Grok Series (xAI) - UPDATED WITH LATEST MODELS
            "grok-4-heavy": AIMLModelConfig(
                model_id="x-ai/grok-4-heavy",
                family=AIMLModelFamily.GROK,
                capabilities=["multi_agent_reasoning", "complex_problems", "vision", "tools"],
                context_window=256000,
                max_tokens=100000,
                supports_vision=True,
                supports_tools=True,
                supports_reasoning=True,
            ),
            "grok-4": AIMLModelConfig(
                model_id="x-ai/grok-4-0709",
                family=AIMLModelFamily.GROK,
                capabilities=["chat", "reasoning", "vision", "tools", "real_time_search"],
                context_window=256000,
                max_tokens=32768,
                supports_vision=True,
                supports_tools=True,
                supports_reasoning=True,
            ),
            "grok-code-fast-1": AIMLModelConfig(
                model_id="x-ai/grok-code-fast-1",
                family=AIMLModelFamily.GROK,
                capabilities=["coding", "agentic_workflows", "fast_generation"],
                context_window=131072,
                max_tokens=32768,
                supports_tools=True,
                supports_reasoning=True,
            ),
            "grok-3": AIMLModelConfig(
                model_id="x-ai/grok-3",
                family=AIMLModelFamily.GROK,
                capabilities=["chat", "tools", "enterprise"],
                context_window=131072,
                max_tokens=16384,
                supports_tools=True,
            ),
            "grok-3-mini": AIMLModelConfig(
                model_id="x-ai/grok-3-mini",
                family=AIMLModelFamily.GROK,
                capabilities=["chat", "cost_effective"],
                context_window=65536,
                max_tokens=8192,
            ),
            # Zhipu GLM Series
            "glm-4.5": AIMLModelConfig(
                model_id="zhipu/glm-4.5",
                family=AIMLModelFamily.ZHIPU,
                capabilities=["chat", "reasoning", "tools", "web_search"],
                context_window=131072,
                max_tokens=65536,
                supports_tools=True,
                supports_reasoning=True,
            ),
            "glm-4.5-air": AIMLModelConfig(
                model_id="zhipu/glm-4.5-air",
                family=AIMLModelFamily.ZHIPU,
                capabilities=["chat", "reasoning", "tools"],
                context_window=65536,
                max_tokens=32768,
                supports_tools=True,
                supports_reasoning=True,
            ),
            # GPT-OSS Series
            "gpt-oss-120b": AIMLModelConfig(
                model_id="gpt-oss-120b",
                family=AIMLModelFamily.GPT3,
                capabilities=["chat"],
                context_window=32768,
                max_tokens=8192,
            ),
            "gpt-oss-20b": AIMLModelConfig(
                model_id="gpt-oss-20b",
                family=AIMLModelFamily.GPT3,
                capabilities=["chat"],
                context_window=32768,
                max_tokens=4096,
            ),
            # Standard GPT-4 Models
            "gpt-4o": AIMLModelConfig(
                model_id="gpt-4o",
                family=AIMLModelFamily.GPT4,
                capabilities=["chat", "vision", "tools"],
                context_window=128000,
                max_tokens=16384,
                supports_vision=True,
                supports_tools=True,
            ),
            "gpt-4o-mini": AIMLModelConfig(
                model_id="gpt-4o-mini",
                family=AIMLModelFamily.GPT4,
                capabilities=["chat", "tools"],
                context_window=128000,
                max_tokens=16384,
                supports_tools=True,
            ),
            "gpt-4-turbo": AIMLModelConfig(
                model_id="gpt-4-turbo",
                family=AIMLModelFamily.GPT4,
                capabilities=["chat", "vision", "tools"],
                context_window=128000,
                max_tokens=4096,
                supports_vision=True,
                supports_tools=True,
            ),
            # Llama-4 Series (Latest Meta Models)
            "llama-4-maverick": AIMLModelConfig(
                model_id="meta-llama/llama-4-maverick",
                family=AIMLModelFamily.LLAMA,
                capabilities=[
                    "chat",
                    "reasoning",
                    "coding",
                    "tools",
                    "vision",
                    "repository_analysis",
                ],
                context_window=131072,
                max_tokens=32768,
                supports_vision=True,
                supports_tools=True,
                supports_reasoning=True,
            ),
            "llama-4-scout": AIMLModelConfig(
                model_id="meta-llama/llama-4-scout",
                family=AIMLModelFamily.LLAMA,
                capabilities=["reconnaissance", "pattern_finding", "repository_scouting", "tools"],
                context_window=131072,
                max_tokens=16384,
                supports_tools=True,
                supports_reasoning=True,
            ),
            "llama-3.3-70b": AIMLModelConfig(
                model_id="meta-llama/Llama-3.3-70B-Instruct-Turbo",
                family=AIMLModelFamily.LLAMA,
                capabilities=["chat", "reasoning", "tools"],
                context_window=128000,
                max_tokens=16384,
                supports_tools=True,
            ),
            # Qwen3 Coder Series (Alibaba)
            "qwen3-coder-480b": AIMLModelConfig(
                model_id="alibaba/qwen3-coder-480b-a35b-instruct",
                family=AIMLModelFamily.QWEN,
                capabilities=["coding", "agentic", "tools", "reasoning", "long_context"],
                context_window=256000,  # Can handle up to 1M with extrapolation
                max_tokens=65536,
                supports_tools=True,
                supports_reasoning=True,
            ),
            # Claude 4 Series (Anthropic)
            "claude-opus-4.1": AIMLModelConfig(
                model_id="anthropic/claude-opus-4.1",
                family=AIMLModelFamily.CLAUDE4,
                capabilities=[
                    "reasoning",
                    "analysis",
                    "strategic_thinking",
                    "nuanced_understanding",
                ],
                context_window=200000,
                max_tokens=65536,
                supports_tools=True,
                supports_reasoning=True,
            ),
            "claude-sonnet-4": AIMLModelConfig(
                model_id="anthropic/claude-sonnet-4",
                family=AIMLModelFamily.CLAUDE4,
                capabilities=["chat", "analysis", "balanced_performance"],
                context_window=200000,
                max_tokens=32768,
                supports_tools=True,
            ),
            # Gemini 2.5 Series (Google)
            "gemini-2.5-pro": AIMLModelConfig(
                model_id="google/gemini-2.5-pro",
                family=AIMLModelFamily.GEMINI25,
                capabilities=["reasoning", "multimodal", "analysis", "tools"],
                context_window=200000,
                max_tokens=32768,
                supports_vision=True,
                supports_tools=True,
                supports_reasoning=True,
            ),
            "gemini-2.5-flash": AIMLModelConfig(
                model_id="google/gemini-2.5-flash",
                family=AIMLModelFamily.GEMINI25,
                capabilities=["fast_processing", "repository_scanning", "quick_analysis"],
                context_window=100000,
                max_tokens=16384,
                supports_vision=True,
                supports_tools=True,
            ),
            # DeepSeek V3.1 and R1 Series
            "deepseek-reasoner-v3.1": AIMLModelConfig(
                model_id="deepseek/deepseek-reasoner-v3.1",
                family=AIMLModelFamily.DEEPSEEK,
                capabilities=["reasoning", "complex_analysis", "step_by_step_thinking"],
                context_window=128000,
                max_tokens=32768,
                supports_reasoning=True,
                supports_tools=True,
            ),
            "deepseek-chat-v3.1": AIMLModelConfig(
                model_id="deepseek/deepseek-chat-v3.1",
                family=AIMLModelFamily.DEEPSEEK,
                capabilities=["chat", "general_purpose", "tools"],
                context_window=128000,
                max_tokens=16384,
                supports_tools=True,
            ),
            "deepseek-r1": AIMLModelConfig(
                model_id="deepseek/deepseek-r1",
                family=AIMLModelFamily.DEEPSEEK,
                capabilities=["reasoning", "research", "deep_analysis"],
                context_window=128000,
                max_tokens=32768,
                supports_reasoning=True,
                supports_tools=True,
            ),
            # Perplexity Sonar Pro
            "sonar-pro": AIMLModelConfig(
                model_id="perplexity/sonar-pro",
                family=AIMLModelFamily.PERPLEXITY,
                capabilities=["web_search", "real_time_info", "citation_heavy", "research"],
                context_window=128000,
                max_tokens=16384,
                supports_tools=True,
            ),
        }

    def get_client(self) -> OpenAI:
        """Get the OpenAI-compatible client"""
        return self.client

    def get_model_config(self, model_name: str) -> Optional[AIMLModelConfig]:
        """Get configuration for a specific model"""
        return self.models.get(model_name)

    def list_models(self, family: Optional[AIMLModelFamily] = None) -> List[str]:
        """List available models, optionally filtered by family"""
        if family:
            return [name for name, config in self.models.items() if config.family == family]
        return list(self.models.keys())

    def get_best_model_for_task(
        self,
        task_type: str,
        require_vision: bool = False,
        require_tools: bool = False,
        require_reasoning: bool = False,
        max_context: Optional[int] = None,
    ) -> Optional[str]:
        """Get the best model for a specific task"""
        candidates = []

        for name, config in self.models.items():
            # Check requirements
            if require_vision and not config.supports_vision:
                continue
            if require_tools and not config.supports_tools:
                continue
            if require_reasoning and not config.supports_reasoning:
                continue
            if max_context and config.context_window < max_context:
                continue

            # Check if model supports the task
            if task_type in config.capabilities:
                candidates.append((name, config))

        if not candidates:
            return None

        # Sort by capability and return the best
        # Prefer GPT-5 > Grok-4 > GPT-4.1 > Others
        priority_order = [
            AIMLModelFamily.GPT5,
            AIMLModelFamily.GROK,
            AIMLModelFamily.GPT4,
            AIMLModelFamily.O_SERIES,
            AIMLModelFamily.ZHIPU,
        ]

        for family in priority_order:
            family_models = [name for name, config in candidates if config.family == family]
            if family_models:
                return family_models[0]

        # Return first available if no priority match
        return candidates[0][0] if candidates else None

    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict]] = None,
        **kwargs,
    ) -> Any:
        """Create a chat completion using AIMLAPI"""
        try:
            model_config = self.get_model_config(model)
            if not model_config:
                logger.warning(f"Model {model} not found in config, using raw model ID")
                model_id = model
            else:
                model_id = model_config.model_id

                # Use model's default max_tokens if not specified
                if max_tokens is None:
                    max_tokens = min(4096, model_config.max_tokens)

            # Build request parameters
            params = {
                "model": model_id,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens or 4096,
                "stream": stream,
                **kwargs,
            }

            # Add tools if supported and provided
            if tools and model_config and model_config.supports_tools:
                params["tools"] = tools

            # Make the API call
            response = self.client.chat.completions.create(**params)

            logger.info(f"AIMLAPI request successful for model {model}")
            return response

        except Exception as e:
            logger.error(f"AIMLAPI request failed: {str(e)}")
            raise

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to AIMLAPI service"""
        results = {}

        # Test a few key models
        test_models = [
            ("gpt-5-nano", "Testing GPT-5 Nano"),
            ("grok-3-mini", "Testing Grok-3 Mini"),
            ("glm-4.5-air", "Testing GLM-4.5 Air"),
            ("gpt-4o-mini", "Testing GPT-4o Mini"),
        ]

        for model_name, test_msg in test_models:
            try:
                response = self.chat_completion(
                    model=model_name,
                    messages=[{"role": "user", "content": "Say 'OK'"}],
                    max_tokens=10,
                )
                results[model_name] = {
                    "status": "success",
                    "response": response.choices[0].message.content,
                }
                logger.info(f"✅ {test_msg}: Success")
            except Exception as e:
                results[model_name] = {"status": "error", "error": str(e)[:100]}
                logger.error(f"❌ {test_msg}: {str(e)[:100]}")

        return results


# Singleton instance
aimlapi_manager = AIMLAPIManager()
