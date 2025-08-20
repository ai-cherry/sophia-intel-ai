"""
SOPHIA V4 Ultimate Model Router
Central router that selects the best available language model for a given task.
"""

import os
import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    """Metadata and configuration for each LLM provider/model."""
    provider: str
    model_name: str
    quality_rank: int  # 1=highest
    max_tokens: int
    cost_per_1k: float
    api_key_env_var: str
    temperature_default: float = 0.3

class TaskType(Enum):
    """Supported task types for model routing."""
    CODE_GENERATION = "code_generation"
    RESEARCH = "research"
    DEPLOYMENT = "deployment"
    CREATIVE = "creative"
    REASONING = "reasoning"
    ANALYSIS = "analysis"

class UltimateModelRouter:
    """
    Central router that selects the best available language model for a given task.
    Only includes the highest-quality models for each task type.
    """

    def __init__(self):
        self.model_registry: Dict[str, List[ModelConfig]] = {
            TaskType.CODE_GENERATION.value: [
                ModelConfig("openai", "gpt-4o", 1, 128_000, 0.00003, "OPENAI_API_KEY"),
                ModelConfig("anthropic", "claude-3-opus-20240229", 2, 200_000, 0.00005, "ANTHROPIC_API_KEY"),
                ModelConfig("google", "gemini-1.5-pro", 3, 128_000, 0.00004, "GEMINI_API_KEY"),
                ModelConfig("groq", "llama-3-70b-8192", 4, 8_192, 0.00002, "GROQ_API_KEY"),
                ModelConfig("deepseek", "deepseek-coder", 5, 16_384, 0.00002, "DEEPSEEK_API_KEY"),
            ],
            TaskType.RESEARCH.value: [
                ModelConfig("openai", "gpt-4o", 1, 128_000, 0.00003, "OPENAI_API_KEY"),
                ModelConfig("anthropic", "claude-3-opus-20240229", 2, 200_000, 0.00005, "ANTHROPIC_API_KEY"),
                ModelConfig("google", "gemini-1.5-pro", 3, 128_000, 0.00004, "GEMINI_API_KEY"),
            ],
            TaskType.DEPLOYMENT.value: [
                ModelConfig("openai", "gpt-4o", 1, 128_000, 0.00003, "OPENAI_API_KEY"),
                ModelConfig("anthropic", "claude-3-opus-20240229", 2, 200_000, 0.00005, "ANTHROPIC_API_KEY"),
            ],
            TaskType.CREATIVE.value: [
                ModelConfig("anthropic", "claude-3-opus-20240229", 1, 200_000, 0.00005, "ANTHROPIC_API_KEY", 0.7),
                ModelConfig("openai", "gpt-4o", 2, 128_000, 0.00003, "OPENAI_API_KEY", 0.7),
            ],
            TaskType.REASONING.value: [
                ModelConfig("openai", "o1-preview", 1, 32_768, 0.00015, "OPENAI_API_KEY", 0.1),
                ModelConfig("anthropic", "claude-3-opus-20240229", 2, 200_000, 0.00005, "ANTHROPIC_API_KEY", 0.1),
            ],
            TaskType.ANALYSIS.value: [
                ModelConfig("openai", "gpt-4o", 1, 128_000, 0.00003, "OPENAI_API_KEY"),
                ModelConfig("anthropic", "claude-3-opus-20240229", 2, 200_000, 0.00005, "ANTHROPIC_API_KEY"),
                ModelConfig("google", "gemini-1.5-pro", 3, 128_000, 0.00004, "GEMINI_API_KEY"),
            ],
        }

    def select_model(self, task_type: str, fallback: bool = True) -> ModelConfig:
        """
        Return the highest-quality available model for the given task.
        
        Args:
            task_type: The type of task to select a model for
            fallback: Whether to try fallback models if primary is unavailable
            
        Returns:
            ModelConfig for the best available model
            
        Raises:
            ValueError: If no models are configured for the task type
            EnvironmentError: If no API keys are available for any model
        """
        models = self.model_registry.get(task_type, [])
        if not models:
            raise ValueError(f"No models configured for task_type: {task_type}")
        
        # Try models in quality order
        for model in models:
            api_key = os.getenv(model.api_key_env_var)
            if api_key:
                logger.info(f"Selected {model.provider}:{model.model_name} for {task_type}")
                return model
            elif not fallback:
                break
        
        # If we get here, no API keys were found
        available_vars = [model.api_key_env_var for model in models]
        raise EnvironmentError(f"No API keys found for {task_type}. Required: {available_vars}")

    async def call_model(self, model_config: ModelConfig, prompt: str, **kwargs) -> str:
        """
        Call the selected model with the given prompt.
        
        Args:
            model_config: Configuration for the model to call
            prompt: The prompt to send to the model
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            The model's response as a string
            
        Raises:
            EnvironmentError: If API key is missing
            RuntimeError: If the API call fails
        """
        api_key = os.getenv(model_config.api_key_env_var)
        if not api_key:
            raise EnvironmentError(f"Missing API key for {model_config.provider} in env var {model_config.api_key_env_var}")

        # Extract parameters with defaults
        temperature = kwargs.get("temperature", model_config.temperature_default)
        max_tokens = min(model_config.max_tokens, kwargs.get("max_tokens", 4096))
        system_prompt = kwargs.get("system_prompt", "")

        try:
            if model_config.provider == "openai":
                return await self._call_openai(model_config, prompt, system_prompt, temperature, max_tokens)
            elif model_config.provider == "anthropic":
                return await self._call_anthropic(model_config, prompt, system_prompt, temperature, max_tokens)
            elif model_config.provider == "google":
                return await self._call_google(model_config, prompt, system_prompt, temperature, max_tokens)
            elif model_config.provider == "groq":
                return await self._call_groq(model_config, prompt, system_prompt, temperature, max_tokens)
            elif model_config.provider == "deepseek":
                return await self._call_deepseek(model_config, prompt, system_prompt, temperature, max_tokens)
            else:
                raise NotImplementedError(f"Provider {model_config.provider} not yet implemented")
        except Exception as e:
            logger.error(f"Failed to call {model_config.provider}:{model_config.model_name}: {e}")
            raise RuntimeError(f"Failed to call {model_config.provider}:{model_config.model_name}: {e}")

    async def _call_openai(self, config: ModelConfig, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
        """Call OpenAI API."""
        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=os.getenv(config.api_key_env_var))
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await client.chat.completions.create(
                model=config.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
        except ImportError:
            raise RuntimeError("OpenAI library not installed. Run: pip install openai")

    async def _call_anthropic(self, config: ModelConfig, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
        """Call Anthropic API."""
        try:
            import anthropic
            
            client = anthropic.AsyncAnthropic(api_key=os.getenv(config.api_key_env_var))
            
            response = await client.messages.create(
                model=config.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
        except ImportError:
            raise RuntimeError("Anthropic library not installed. Run: pip install anthropic")

    async def _call_google(self, config: ModelConfig, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
        """Call Google Gemini API."""
        # TODO: Implement Google Gemini API call
        raise NotImplementedError("Google Gemini API integration not yet implemented")

    async def _call_groq(self, config: ModelConfig, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
        """Call Groq API."""
        # TODO: Implement Groq API call
        raise NotImplementedError("Groq API integration not yet implemented")

    async def _call_deepseek(self, config: ModelConfig, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
        """Call DeepSeek API."""
        # TODO: Implement DeepSeek API call
        raise NotImplementedError("DeepSeek API integration not yet implemented")

    def get_available_models(self, task_type: str) -> List[ModelConfig]:
        """Get all available models for a task type (those with API keys)."""
        models = self.model_registry.get(task_type, [])
        return [model for model in models if os.getenv(model.api_key_env_var)]

    def get_model_info(self, task_type: str) -> Dict[str, Any]:
        """Get information about models for a task type."""
        models = self.model_registry.get(task_type, [])
        available = self.get_available_models(task_type)
        
        return {
            "task_type": task_type,
            "total_models": len(models),
            "available_models": len(available),
            "models": [
                {
                    "provider": model.provider,
                    "model_name": model.model_name,
                    "quality_rank": model.quality_rank,
                    "available": model in available
                }
                for model in models
            ]
        }

