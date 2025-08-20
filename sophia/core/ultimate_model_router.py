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
        """Initialize with the approved model list only."""
        self.model_registry: Dict[str, List[ModelConfig]] = {
            TaskType.CODE_GENERATION.value: [
                ModelConfig("openai", "gpt-5", 1, 128_000, 0.00008, "OPENAI_API_KEY"),
                ModelConfig("anthropic", "claude-sonnet-4", 2, 200_000, 0.00006, "ANTHROPIC_API_KEY"),
                ModelConfig("google", "gemini-2.5-pro", 3, 128_000, 0.00005, "GEMINI_API_KEY"),
                ModelConfig("qwen", "qwen3-coder", 4, 32_000, 0.00003, "QWEN_API_KEY"),
                ModelConfig("openai", "gpt-4o-mini", 5, 8_192, 0.00002, "OPENAI_API_KEY"),
                ModelConfig("qwen", "qwen3-coder-free", 6, 32_000, 0.00001, "QWEN_API_KEY"),
            ],
            TaskType.RESEARCH.value: [
                ModelConfig("deepseek", "deepseek-v3-0324", 1, 16_384, 0.00002, "DEEPSEEK_API_KEY"),
                ModelConfig("anthropic", "claude-3.7-sonnet", 2, 200_000, 0.00006, "ANTHROPIC_API_KEY"),
                ModelConfig("google", "gemini-2.5-flash", 3, 128_000, 0.00004, "GEMINI_API_KEY"),
                ModelConfig("openai", "gpt-5-mini", 4, 16_384, 0.00003, "OPENAI_API_KEY"),
                ModelConfig("moonshot", "kimi-k2", 5, 32_000, 0.00003, "MOONSHOT_API_KEY"),
                ModelConfig("deepseek", "deepseek-v3-0324-free", 6, 16_384, 0.00001, "DEEPSEEK_API_KEY"),
            ],
            TaskType.DEPLOYMENT.value: [
                ModelConfig("openai", "gpt-5", 1, 128_000, 0.00008, "OPENAI_API_KEY"),
                ModelConfig("google", "gemini-2.5-pro", 2, 128_000, 0.00005, "GEMINI_API_KEY"),
                ModelConfig("anthropic", "claude-sonnet-4", 3, 200_000, 0.00006, "ANTHROPIC_API_KEY"),
                ModelConfig("google", "gemini-2.0-flash", 4, 64_000, 0.00003, "GEMINI_API_KEY"),
            ],
            TaskType.CREATIVE.value: [
                ModelConfig("anthropic", "claude-3.7-sonnet", 1, 200_000, 0.00006, "ANTHROPIC_API_KEY", 0.7),
                ModelConfig("openai", "gpt-5", 2, 128_000, 0.00008, "OPENAI_API_KEY", 0.7),
                ModelConfig("mistral", "mistral-nemo", 3, 32_000, 0.00004, "MISTRAL_API_KEY", 0.8),
                ModelConfig("zhipu", "glm-4.5", 4, 16_384, 0.00003, "ZHIPU_API_KEY", 0.7),
            ],
            TaskType.REASONING.value: [
                ModelConfig("openai", "gpt-5", 1, 128_000, 0.00008, "OPENAI_API_KEY", 0.1),
                ModelConfig("deepseek", "r1-0528-free", 2, 16_384, 0.00001, "DEEPSEEK_API_KEY", 0.1),
                ModelConfig("anthropic", "claude-sonnet-4", 3, 200_000, 0.00006, "ANTHROPIC_API_KEY", 0.1),
                ModelConfig("google", "gemini-2.5-flash", 4, 128_000, 0.00004, "GEMINI_API_KEY", 0.1),
                ModelConfig("moonshot", "kimi-k2", 5, 32_000, 0.00003, "MOONSHOT_API_KEY", 0.1),
            ],
            TaskType.ANALYSIS.value: [
                ModelConfig("openai", "gpt-5", 1, 128_000, 0.00008, "OPENAI_API_KEY"),
                ModelConfig("deepseek", "deepseek-v3-0324", 2, 16_384, 0.00002, "DEEPSEEK_API_KEY"),
                ModelConfig("google", "gemini-2.5-pro", 3, 128_000, 0.00005, "GEMINI_API_KEY"),
                ModelConfig("anthropic", "claude-sonnet-4", 4, 200_000, 0.00006, "ANTHROPIC_API_KEY"),
                ModelConfig("openai", "gpt-oss-120b", 5, 32_000, 0.00004, "OPENAI_API_KEY"),
                ModelConfig("google", "gemini-2.5-flash-lite", 6, 64_000, 0.00002, "GEMINI_API_KEY"),
            ],
        }
        
        # Additional approved models for specialized tasks
        self.approved_models = {
            "gpt-5", "claude-sonnet-4", "gemini-2.5-flash", "gemini-2.0-flash", 
            "deepseek-v3-0324", "gemini-2.5-pro", "qwen3-coder", "claude-3.7-sonnet",
            "deepseek-v3-0324-free", "r1-0528-free", "kimi-k2", "gpt-oss-120b",
            "qwen3-coder-free", "gemini-2.5-flash-lite", "glm-4.5", "mistral-nemo",
            "gpt-4o-mini", "r1-free", "gpt-5-mini", "gpt-4.1"
        }
        
        logger.info(f"Initialized UltimateModelRouter with {len(self.approved_models)} approved models")

    def select_model(self, task_type: str, fallback: bool = True) -> ModelConfig:
        """
        Return the highest-ranked model for the given task_type from the approved list.
        
        Args:
            task_type: The type of task to select a model for
            fallback: Whether to try fallback models if primary is unavailable
            
        Returns:
            ModelConfig for the best available model
            
        Raises:
            ValueError: If no models are configured for the task type
            RuntimeError: If no API keys are available for any approved model
        """
        models = self.model_registry.get(task_type, [])
        if not models:
            raise ValueError(f"No approved models configured for task_type: {task_type}")
        
        # Try models in quality order (1 = highest quality)
        for model in models:
            # Verify model is in approved list
            if model.model_name not in self.approved_models:
                logger.warning(f"Model {model.model_name} not in approved list, skipping")
                continue
                
            api_key = os.getenv(model.api_key_env_var)
            if api_key:
                logger.info(f"Selected approved model {model.provider}:{model.model_name} for {task_type}")
                return model
            elif not fallback:
                break
        
        # If we get here, no models had valid API keys
        available_models = [m.model_name for m in models if m.model_name in self.approved_models]
        required_keys = [m.api_key_env_var for m in models if m.model_name in self.approved_models]
        raise RuntimeError(
            f"No available approved models for task_type {task_type}. "
            f"Available models: {available_models}. "
            f"Required API keys: {required_keys}"
        )

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
            elif model_config.provider == "deepseek":
                return await self._call_deepseek(model_config, prompt, system_prompt, temperature, max_tokens)
            elif model_config.provider == "qwen":
                return await self._call_qwen(model_config, prompt, system_prompt, temperature, max_tokens)
            elif model_config.provider == "moonshot":
                return await self._call_moonshot(model_config, prompt, system_prompt, temperature, max_tokens)
            elif model_config.provider == "mistral":
                return await self._call_mistral(model_config, prompt, system_prompt, temperature, max_tokens)
            elif model_config.provider == "zhipu":
                return await self._call_zhipu(model_config, prompt, system_prompt, temperature, max_tokens)
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


    async def _call_qwen(self, config: ModelConfig, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
        """Call Qwen API."""
        # TODO: Implement Qwen API call
        # For now, use OpenAI-compatible endpoint if available
        raise NotImplementedError("Qwen API integration not yet implemented")

    async def _call_moonshot(self, config: ModelConfig, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
        """Call Moonshot (Kimi) API."""
        # TODO: Implement Moonshot API call
        raise NotImplementedError("Moonshot API integration not yet implemented")

    async def _call_mistral(self, config: ModelConfig, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
        """Call Mistral API."""
        # TODO: Implement Mistral API call
        raise NotImplementedError("Mistral API integration not yet implemented")

    async def _call_zhipu(self, config: ModelConfig, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
        """Call Zhipu (GLM) API."""
        # TODO: Implement Zhipu API call
        raise NotImplementedError("Zhipu API integration not yet implemented")

    def validate_approved_models(self) -> Dict[str, Any]:
        """
        Validate that all models in the registry are in the approved list.
        
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            "valid": True,
            "total_models": 0,
            "approved_models": 0,
            "unapproved_models": [],
            "missing_providers": []
        }
        
        all_models = set()
        for task_type, models in self.model_registry.items():
            for model in models:
                all_models.add(model.model_name)
                validation_results["total_models"] += 1
                
                if model.model_name in self.approved_models:
                    validation_results["approved_models"] += 1
                else:
                    validation_results["unapproved_models"].append({
                        "task_type": task_type,
                        "provider": model.provider,
                        "model_name": model.model_name
                    })
                    validation_results["valid"] = False
        
        # Check for missing provider implementations
        providers_in_use = set()
        for models in self.model_registry.values():
            for model in models:
                providers_in_use.add(model.provider)
        
        implemented_providers = {"openai", "anthropic", "google", "deepseek", "qwen", "moonshot", "mistral", "zhipu"}
        missing_providers = providers_in_use - implemented_providers
        
        if missing_providers:
            validation_results["missing_providers"] = list(missing_providers)
            validation_results["valid"] = False
        
        return validation_results

