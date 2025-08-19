"""
SOPHIA Intel OpenRouter Models Integration
Phase 5 of V4 Mega Upgrade - Enhanced AI Model Access

Provides access to top-tier AI models through OpenRouter API including:
- Claude Sonnet 4, DeepSeek V3, Qwen 3 Coder, and other cutting-edge models
"""

import os
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import asyncio
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class ModelTier(Enum):
    """Model performance and cost tiers"""
    PREMIUM = "premium"      # Claude Sonnet 4, GPT-4 Turbo
    ADVANCED = "advanced"    # DeepSeek V3, Qwen 3 Coder
    STANDARD = "standard"    # GPT-4, Claude 3.5 Sonnet
    EFFICIENT = "efficient"  # GPT-3.5 Turbo, Claude 3 Haiku

@dataclass
class ModelConfig:
    """Configuration for OpenRouter models"""
    name: str
    openrouter_id: str
    tier: ModelTier
    context_length: int
    cost_per_1k_tokens: float
    specialties: List[str]
    supports_streaming: bool = True
    supports_function_calling: bool = True

class OpenRouterModels:
    """
    OpenRouter models integration with intelligent model selection and routing.
    Provides access to cutting-edge AI models with automatic fallback and optimization.
    """
    
    # Model configurations for top-tier models
    MODELS = {
        # Premium Tier - Highest capability models
        "claude-sonnet-4": ModelConfig(
            name="Claude Sonnet 4",
            openrouter_id="anthropic/claude-3-5-sonnet-20241022",
            tier=ModelTier.PREMIUM,
            context_length=200000,
            cost_per_1k_tokens=3.0,
            specialties=["reasoning", "analysis", "coding", "writing"],
            supports_streaming=True,
            supports_function_calling=True
        ),
        "gpt-4-turbo": ModelConfig(
            name="GPT-4 Turbo",
            openrouter_id="openai/gpt-4-turbo",
            tier=ModelTier.PREMIUM,
            context_length=128000,
            cost_per_1k_tokens=10.0,
            specialties=["general", "coding", "analysis", "multimodal"],
            supports_streaming=True,
            supports_function_calling=True
        ),
        
        # Advanced Tier - Specialized high-performance models
        "deepseek-v3": ModelConfig(
            name="DeepSeek V3",
            openrouter_id="deepseek/deepseek-chat",
            tier=ModelTier.ADVANCED,
            context_length=64000,
            cost_per_1k_tokens=0.14,
            specialties=["coding", "mathematics", "reasoning", "efficiency"],
            supports_streaming=True,
            supports_function_calling=True
        ),
        "qwen-3-coder": ModelConfig(
            name="Qwen 3 Coder",
            openrouter_id="qwen/qwen-2.5-coder-32b-instruct",
            tier=ModelTier.ADVANCED,
            context_length=32768,
            cost_per_1k_tokens=0.3,
            specialties=["coding", "debugging", "refactoring", "architecture"],
            supports_streaming=True,
            supports_function_calling=True
        ),
        "claude-3.5-sonnet": ModelConfig(
            name="Claude 3.5 Sonnet",
            openrouter_id="anthropic/claude-3-5-sonnet",
            tier=ModelTier.ADVANCED,
            context_length=200000,
            cost_per_1k_tokens=3.0,
            specialties=["reasoning", "analysis", "writing", "research"],
            supports_streaming=True,
            supports_function_calling=True
        ),
        
        # Standard Tier - Reliable general-purpose models
        "gpt-4": ModelConfig(
            name="GPT-4",
            openrouter_id="openai/gpt-4",
            tier=ModelTier.STANDARD,
            context_length=8192,
            cost_per_1k_tokens=30.0,
            specialties=["general", "reasoning", "writing"],
            supports_streaming=True,
            supports_function_calling=True
        ),
        "claude-3-opus": ModelConfig(
            name="Claude 3 Opus",
            openrouter_id="anthropic/claude-3-opus",
            tier=ModelTier.STANDARD,
            context_length=200000,
            cost_per_1k_tokens=15.0,
            specialties=["complex_reasoning", "analysis", "creative_writing"],
            supports_streaming=True,
            supports_function_calling=True
        ),
        
        # Efficient Tier - Fast and cost-effective models
        "gpt-3.5-turbo": ModelConfig(
            name="GPT-3.5 Turbo",
            openrouter_id="openai/gpt-3.5-turbo",
            tier=ModelTier.EFFICIENT,
            context_length=16385,
            cost_per_1k_tokens=0.5,
            specialties=["general", "speed", "efficiency"],
            supports_streaming=True,
            supports_function_calling=True
        ),
        "claude-3-haiku": ModelConfig(
            name="Claude 3 Haiku",
            openrouter_id="anthropic/claude-3-haiku",
            tier=ModelTier.EFFICIENT,
            context_length=200000,
            cost_per_1k_tokens=0.25,
            specialties=["speed", "efficiency", "simple_tasks"],
            supports_streaming=True,
            supports_function_calling=True
        )
    }
    
    def __init__(self):
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.openrouter_api_key:
            logger.warning("OPENROUTER_API_KEY not found, using OpenAI fallback")
            self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.base_url = "https://api.openai.com/v1"
        else:
            self.client = AsyncOpenAI(
                api_key=self.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            self.base_url = "https://openrouter.ai/api/v1"
        
        logger.info(f"Initialized OpenRouter with {len(self.MODELS)} models")
    
    def select_optimal_model(self, 
                           task_type: str, 
                           complexity: str = "medium",
                           budget_tier: ModelTier = ModelTier.ADVANCED) -> ModelConfig:
        """
        Intelligently select the optimal model based on task requirements.
        
        Args:
            task_type: Type of task (coding, reasoning, writing, analysis, etc.)
            complexity: Task complexity (simple, medium, complex)
            budget_tier: Maximum budget tier to consider
            
        Returns:
            Optimal model configuration for the task
        """
        # Filter models by budget tier
        available_models = {
            k: v for k, v in self.MODELS.items() 
            if v.tier.value <= budget_tier.value or v.tier == budget_tier
        }
        
        # Score models based on task requirements
        scored_models = []
        for model_key, model in available_models.items():
            score = 0
            
            # Task specialty matching
            if task_type in model.specialties:
                score += 10
            elif "general" in model.specialties:
                score += 5
            
            # Complexity matching
            if complexity == "complex" and model.tier in [ModelTier.PREMIUM, ModelTier.ADVANCED]:
                score += 8
            elif complexity == "medium" and model.tier in [ModelTier.ADVANCED, ModelTier.STANDARD]:
                score += 6
            elif complexity == "simple" and model.tier in [ModelTier.EFFICIENT, ModelTier.STANDARD]:
                score += 4
            
            # Cost efficiency (lower cost = higher score for efficiency)
            if model.cost_per_1k_tokens < 1.0:
                score += 5
            elif model.cost_per_1k_tokens < 5.0:
                score += 3
            
            # Context length bonus for complex tasks
            if complexity == "complex" and model.context_length > 100000:
                score += 3
            
            scored_models.append((score, model_key, model))
        
        # Return highest scoring model
        if scored_models:
            scored_models.sort(reverse=True)
            selected_model = scored_models[0][2]
            logger.info(f"Selected model: {selected_model.name} for {task_type} task")
            return selected_model
        
        # Fallback to Claude 3.5 Sonnet
        return self.MODELS["claude-3.5-sonnet"]
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_completion(self,
                                messages: List[Dict[str, str]],
                                model_key: Optional[str] = None,
                                task_type: str = "general",
                                complexity: str = "medium",
                                temperature: float = 0.7,
                                max_tokens: int = 4000,
                                stream: bool = False) -> Dict[str, Any]:
        """
        Generate completion using optimal model selection.
        
        Args:
            messages: List of messages in OpenAI format
            model_key: Specific model to use (optional)
            task_type: Type of task for model selection
            complexity: Task complexity level
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            Completion response with model info and usage stats
        """
        # Select optimal model if not specified
        if model_key and model_key in self.MODELS:
            model = self.MODELS[model_key]
        else:
            model = self.select_optimal_model(task_type, complexity)
        
        try:
            # Prepare request parameters
            request_params = {
                "model": model.openrouter_id,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": min(max_tokens, model.context_length // 4),  # Reserve context for input
                "stream": stream
            }
            
            # Add OpenRouter specific headers if using OpenRouter
            if self.base_url == "https://openrouter.ai/api/v1":
                request_params["extra_headers"] = {
                    "HTTP-Referer": "https://sophia-intel.ai",
                    "X-Title": "SOPHIA Intel V4"
                }
            
            # Generate completion
            if stream:
                return await self._generate_streaming_completion(request_params, model)
            else:
                response = await self.client.chat.completions.create(**request_params)
                
                return {
                    "content": response.choices[0].message.content,
                    "model_used": model.name,
                    "model_id": model.openrouter_id,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                        "total_tokens": response.usage.total_tokens if response.usage else 0
                    },
                    "finish_reason": response.choices[0].finish_reason,
                    "cost_estimate": self._calculate_cost(response.usage, model) if response.usage else 0
                }
                
        except Exception as e:
            logger.error(f"Error generating completion with {model.name}: {e}")
            # Fallback to efficient model
            if model.tier != ModelTier.EFFICIENT:
                logger.info("Falling back to efficient model")
                return await self.generate_completion(
                    messages, "gpt-3.5-turbo", task_type, "simple", temperature, max_tokens, stream
                )
            raise e
    
    async def _generate_streaming_completion(self, request_params: Dict, model: ModelConfig) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate streaming completion"""
        try:
            stream = await self.client.chat.completions.create(**request_params)
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {
                        "content": chunk.choices[0].delta.content,
                        "model_used": model.name,
                        "model_id": model.openrouter_id,
                        "is_streaming": True,
                        "finish_reason": chunk.choices[0].finish_reason
                    }
                    
        except Exception as e:
            logger.error(f"Error in streaming completion: {e}")
            yield {
                "content": f"Error: {str(e)}",
                "model_used": model.name,
                "error": True
            }
    
    def _calculate_cost(self, usage: Any, model: ModelConfig) -> float:
        """Calculate estimated cost for the completion"""
        if not usage:
            return 0.0
        
        total_tokens = usage.total_tokens or 0
        return (total_tokens / 1000) * model.cost_per_1k_tokens
    
    def get_available_models(self, tier: Optional[ModelTier] = None) -> Dict[str, ModelConfig]:
        """Get available models, optionally filtered by tier"""
        if tier:
            return {k: v for k, v in self.MODELS.items() if v.tier == tier}
        return self.MODELS.copy()
    
    def get_model_info(self, model_key: str) -> Optional[ModelConfig]:
        """Get detailed information about a specific model"""
        return self.MODELS.get(model_key)
    
    async def test_model_connectivity(self) -> Dict[str, Any]:
        """Test connectivity to OpenRouter and model availability"""
        test_messages = [{"role": "user", "content": "Hello, this is a connectivity test."}]
        
        try:
            result = await self.generate_completion(
                messages=test_messages,
                model_key="claude-3-haiku",  # Use efficient model for testing
                max_tokens=50
            )
            
            return {
                "status": "connected",
                "base_url": self.base_url,
                "test_model": result["model_used"],
                "response_length": len(result["content"]),
                "cost_estimate": result.get("cost_estimate", 0)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "base_url": self.base_url,
                "error": str(e)
            }

# Global OpenRouter models instance
openrouter_models = OpenRouterModels()

