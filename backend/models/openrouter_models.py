"""
OpenRouter Model Configuration for SOPHIA Intel
Latest models with intelligent selection based on task requirements
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass

class ModelTier(Enum):
    """Model performance tiers"""
    FLAGSHIP = "flagship"      # Best performance, highest cost
    PREMIUM = "premium"        # High performance, moderate cost
    STANDARD = "standard"      # Good performance, low cost
    EFFICIENT = "efficient"    # Fast, very low cost

@dataclass
class ModelConfig:
    """Configuration for an OpenRouter model"""
    name: str
    provider: str
    tier: ModelTier
    context_length: int
    cost_per_1k_tokens: float
    strengths: List[str]
    best_for: List[str]
    temperature_range: tuple = (0.0, 1.0)
    max_tokens_default: int = 4000

class OpenRouterModels:
    """
    Latest OpenRouter models with intelligent selection
    """
    
    # Flagship Models - Best Performance
    CLAUDE_SONNET_4 = ModelConfig(
        name="anthropic/claude-4-sonnet",
        provider="anthropic",
        tier=ModelTier.FLAGSHIP,
        context_length=200000,
        cost_per_1k_tokens=3.0,
        strengths=["reasoning", "code", "analysis", "writing"],
        best_for=["complex_coding", "research", "analysis", "creative_writing"],
        temperature_range=(0.0, 1.0),
        max_tokens_default=8000
    )
    
    GPT_5 = ModelConfig(
        name="openai/gpt-5",
        provider="openai", 
        tier=ModelTier.FLAGSHIP,
        context_length=128000,
        cost_per_1k_tokens=2.5,
        strengths=["reasoning", "code", "multimodal", "planning"],
        best_for=["complex_reasoning", "code_generation", "planning"],
        temperature_range=(0.0, 2.0),
        max_tokens_default=8000
    )
    
    GEMINI_2_5_PRO = ModelConfig(
        name="google/gemini-2.5-pro",
        provider="google",
        tier=ModelTier.FLAGSHIP,
        context_length=1000000,
        cost_per_1k_tokens=2.0,
        strengths=["long_context", "multimodal", "reasoning"],
        best_for=["document_analysis", "long_context_tasks", "research"],
        temperature_range=(0.0, 2.0),
        max_tokens_default=8000
    )
    
    # Premium Models - High Performance
    DEEPSEEK_V3 = ModelConfig(
        name="deepseek/deepseek-v3-0324",
        provider="deepseek",
        tier=ModelTier.PREMIUM,
        context_length=64000,
        cost_per_1k_tokens=1.5,
        strengths=["code", "reasoning", "math"],
        best_for=["coding", "technical_analysis", "problem_solving"],
        temperature_range=(0.0, 1.0),
        max_tokens_default=6000
    )
    
    GPT_4_1 = ModelConfig(
        name="openai/gpt-4.1",
        provider="openai",
        tier=ModelTier.PREMIUM,
        context_length=128000,
        cost_per_1k_tokens=1.8,
        strengths=["reasoning", "code", "analysis"],
        best_for=["general_tasks", "coding", "analysis"],
        temperature_range=(0.0, 2.0),
        max_tokens_default=6000
    )
    
    QWEN3_CODER = ModelConfig(
        name="qwen/qwen3-coder",
        provider="qwen",
        tier=ModelTier.PREMIUM,
        context_length=32000,
        cost_per_1k_tokens=1.2,
        strengths=["code", "programming", "debugging"],
        best_for=["code_generation", "debugging", "code_review"],
        temperature_range=(0.0, 1.0),
        max_tokens_default=6000
    )
    
    # Standard Models - Good Performance
    GEMINI_2_5_FLASH = ModelConfig(
        name="google/gemini-2.5-flash",
        provider="google",
        tier=ModelTier.STANDARD,
        context_length=1000000,
        cost_per_1k_tokens=0.8,
        strengths=["speed", "long_context", "general"],
        best_for=["general_tasks", "quick_responses", "document_processing"],
        temperature_range=(0.0, 2.0),
        max_tokens_default=4000
    )
    
    KIMI_K2 = ModelConfig(
        name="moonshotai/kimi-k2",
        provider="moonshotai",
        tier=ModelTier.STANDARD,
        context_length=200000,
        cost_per_1k_tokens=1.0,
        strengths=["long_context", "chinese", "reasoning"],
        best_for=["long_documents", "multilingual", "analysis"],
        temperature_range=(0.0, 1.0),
        max_tokens_default=4000
    )
    
    GLM_4_5 = ModelConfig(
        name="z-ai/glm-4.5",
        provider="z-ai",
        tier=ModelTier.STANDARD,
        context_length=128000,
        cost_per_1k_tokens=0.9,
        strengths=["reasoning", "chinese", "general"],
        best_for=["general_tasks", "reasoning", "multilingual"],
        temperature_range=(0.0, 1.0),
        max_tokens_default=4000
    )
    
    # Efficient Models - Fast & Low Cost
    GPT_5_MINI = ModelConfig(
        name="openai/gpt-5-mini",
        provider="openai",
        tier=ModelTier.EFFICIENT,
        context_length=128000,
        cost_per_1k_tokens=0.3,
        strengths=["speed", "efficiency", "general"],
        best_for=["quick_tasks", "simple_queries", "high_volume"],
        temperature_range=(0.0, 2.0),
        max_tokens_default=2000
    )
    
    GPT_4_1_MINI = ModelConfig(
        name="openai/gpt-4.1-mini",
        provider="openai",
        tier=ModelTier.EFFICIENT,
        context_length=128000,
        cost_per_1k_tokens=0.25,
        strengths=["speed", "efficiency", "code"],
        best_for=["quick_coding", "simple_tasks", "high_volume"],
        temperature_range=(0.0, 2.0),
        max_tokens_default=2000
    )
    
    DEEPSEEK_R1_FREE = ModelConfig(
        name="deepseek/r1-free",
        provider="deepseek",
        tier=ModelTier.EFFICIENT,
        context_length=32000,
        cost_per_1k_tokens=0.0,
        strengths=["free", "reasoning", "code"],
        best_for=["development", "testing", "free_tier"],
        temperature_range=(0.0, 1.0),
        max_tokens_default=2000
    )
    
    GEMINI_2_5_FLASH_LITE = ModelConfig(
        name="google/gemini-2.5-flash-lite",
        provider="google",
        tier=ModelTier.EFFICIENT,
        context_length=1000000,
        cost_per_1k_tokens=0.2,
        strengths=["speed", "long_context", "efficiency"],
        best_for=["quick_tasks", "document_scanning", "high_volume"],
        temperature_range=(0.0, 2.0),
        max_tokens_default=2000
    )

class ModelSelector:
    """
    Intelligent model selection based on task requirements
    """
    
    def __init__(self):
        self.models = {
            # Flagship
            "claude-4-sonnet": OpenRouterModels.CLAUDE_SONNET_4,
            "gpt-5": OpenRouterModels.GPT_5,
            "gemini-2.5-pro": OpenRouterModels.GEMINI_2_5_PRO,
            
            # Premium
            "deepseek-v3": OpenRouterModels.DEEPSEEK_V3,
            "gpt-4.1": OpenRouterModels.GPT_4_1,
            "qwen3-coder": OpenRouterModels.QWEN3_CODER,
            
            # Standard
            "gemini-2.5-flash": OpenRouterModels.GEMINI_2_5_FLASH,
            "kimi-k2": OpenRouterModels.KIMI_K2,
            "glm-4.5": OpenRouterModels.GLM_4_5,
            
            # Efficient
            "gpt-5-mini": OpenRouterModels.GPT_5_MINI,
            "gpt-4.1-mini": OpenRouterModels.GPT_4_1_MINI,
            "deepseek-r1-free": OpenRouterModels.DEEPSEEK_R1_FREE,
            "gemini-2.5-flash-lite": OpenRouterModels.GEMINI_2_5_FLASH_LITE,
        }
    
    def select_model_for_task(self, task_type: str, complexity: str = "medium", budget: str = "standard") -> ModelConfig:
        """
        Select the best model for a specific task
        
        Args:
            task_type: Type of task (coding, research, general, creative, analysis)
            complexity: Task complexity (simple, medium, complex)
            budget: Budget constraint (free, efficient, standard, premium, flagship)
        """
        
        # Budget-based filtering
        if budget == "free":
            candidates = [m for m in self.models.values() if m.cost_per_1k_tokens == 0.0]
        elif budget == "efficient":
            candidates = [m for m in self.models.values() if m.tier == ModelTier.EFFICIENT]
        elif budget == "standard":
            candidates = [m for m in self.models.values() if m.tier in [ModelTier.STANDARD, ModelTier.EFFICIENT]]
        elif budget == "premium":
            candidates = [m for m in self.models.values() if m.tier in [ModelTier.PREMIUM, ModelTier.STANDARD]]
        else:  # flagship
            candidates = list(self.models.values())
        
        # Task-based selection
        if task_type == "coding":
            # Prefer models good at code
            if complexity == "complex":
                preferred = ["claude-4-sonnet", "gpt-5", "deepseek-v3", "qwen3-coder"]
            elif complexity == "medium":
                preferred = ["deepseek-v3", "qwen3-coder", "gpt-4.1", "claude-4-sonnet"]
            else:  # simple
                preferred = ["qwen3-coder", "gpt-4.1-mini", "deepseek-r1-free", "gpt-5-mini"]
                
        elif task_type == "research":
            # Prefer models with long context and reasoning
            if complexity == "complex":
                preferred = ["gemini-2.5-pro", "claude-4-sonnet", "gpt-5", "kimi-k2"]
            elif complexity == "medium":
                preferred = ["claude-4-sonnet", "gemini-2.5-flash", "gpt-4.1", "kimi-k2"]
            else:  # simple
                preferred = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gpt-5-mini"]
                
        elif task_type == "analysis":
            # Prefer reasoning-focused models
            if complexity == "complex":
                preferred = ["claude-4-sonnet", "gpt-5", "gemini-2.5-pro", "deepseek-v3"]
            elif complexity == "medium":
                preferred = ["claude-4-sonnet", "gpt-4.1", "deepseek-v3", "glm-4.5"]
            else:  # simple
                preferred = ["gpt-4.1-mini", "gemini-2.5-flash", "gpt-5-mini"]
                
        elif task_type == "creative":
            # Prefer models good at creative writing
            if complexity == "complex":
                preferred = ["claude-4-sonnet", "gpt-5", "gemini-2.5-pro"]
            elif complexity == "medium":
                preferred = ["claude-4-sonnet", "gpt-4.1", "gemini-2.5-flash"]
            else:  # simple
                preferred = ["gpt-5-mini", "gpt-4.1-mini", "gemini-2.5-flash-lite"]
                
        else:  # general
            # Balanced selection
            if complexity == "complex":
                preferred = ["claude-4-sonnet", "gpt-5", "gpt-4.1", "gemini-2.5-pro"]
            elif complexity == "medium":
                preferred = ["gpt-4.1", "claude-4-sonnet", "gemini-2.5-flash", "glm-4.5"]
            else:  # simple
                preferred = ["gpt-5-mini", "gpt-4.1-mini", "gemini-2.5-flash-lite", "deepseek-r1-free"]
        
        # Find the best available model from preferences
        for model_key in preferred:
            if model_key in self.models:
                model = self.models[model_key]
                if model in candidates:
                    return model
        
        # Fallback to first available candidate
        return candidates[0] if candidates else self.models["gpt-5-mini"]
    
    def get_model_by_name(self, name: str) -> Optional[ModelConfig]:
        """Get model configuration by name"""
        return self.models.get(name)
    
    def list_models_by_tier(self, tier: ModelTier) -> List[ModelConfig]:
        """List all models in a specific tier"""
        return [m for m in self.models.values() if m.tier == tier]
    
    def get_flagship_models(self) -> List[ModelConfig]:
        """Get all flagship models"""
        return self.list_models_by_tier(ModelTier.FLAGSHIP)
    
    def get_free_models(self) -> List[ModelConfig]:
        """Get all free models"""
        return [m for m in self.models.values() if m.cost_per_1k_tokens == 0.0]

# Global model selector instance
model_selector = ModelSelector()

