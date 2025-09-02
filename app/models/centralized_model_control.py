"""
CENTRALIZED MODEL CONTROL
Only use these specific models - NO OTHERS!
"""

from enum import Enum


class ModelPurpose(Enum):
    """Model usage purposes"""
    CRITICAL = "critical"  # Most important tasks - GPT-5
    COUNTER_REASONING = "counter_reasoning"  # Counter arguments - Grok-4
    FAST_CODING = "fast_coding"  # Quick code generation
    DEEP_THINKING = "deep_thinking"  # Complex reasoning
    RESEARCH = "research"  # Information gathering
    VISION = "vision"  # Image tasks
    CREATIVE = "creative"  # Creative tasks
    QUICK = "quick"  # Fast simple tasks

class CentralizedModelControl:
    """
    CENTRALIZED MODEL CONTROL - ONLY USE THESE MODELS!
    Dashboard integration for model selection and monitoring
    """

    # ONLY THESE MODELS - NO OTHERS!
    APPROVED_MODELS = {
        # PRIMARY MODELS
        "openai/gpt-5": {
            "purpose": ModelPurpose.CRITICAL,
            "description": "Most important tasks - PRIMARY MODEL",
            "priority": 1,
            "cost_tier": "premium"
        },
        "x-ai/grok-4": {
            "purpose": ModelPurpose.COUNTER_REASONING,
            "description": "Counter-reasoning and critical review",
            "priority": 2,
            "cost_tier": "premium"
        },

        # SPECIALIZED MODELS (FROM YOUR LIST)
        "x-ai/grok-code-fast-1": {
            "purpose": ModelPurpose.FAST_CODING,
            "description": "Fast code generation",
            "priority": 3,
            "cost_tier": "standard"
        },
        "qwen/qwen3-30b-a3b-thinking-2507": {
            "purpose": ModelPurpose.DEEP_THINKING,
            "description": "Deep thinking and complex reasoning",
            "priority": 3,
            "cost_tier": "standard"
        },
        "nousresearch/hermes-4-405b": {
            "purpose": ModelPurpose.RESEARCH,
            "description": "Research and information gathering",
            "priority": 4,
            "cost_tier": "standard"
        },
        "google/gemini-2.5-flash-image-preview:free": {
            "purpose": ModelPurpose.VISION,
            "description": "Vision and image tasks (FREE)",
            "priority": 5,
            "cost_tier": "free"
        },
        "openai/gpt-5-mini": {
            "purpose": ModelPurpose.QUICK,
            "description": "Quick simple tasks",
            "priority": 5,
            "cost_tier": "economy"
        },
        "anthropic/claude-sonnet-4": {
            "purpose": ModelPurpose.CREATIVE,
            "description": "Creative and balanced tasks",
            "priority": 4,
            "cost_tier": "standard"
        },
        "deepseek/deepseek-chat-v3-0324": {
            "purpose": ModelPurpose.CREATIVE,
            "description": "Creative exploration",
            "priority": 4,
            "cost_tier": "economy"
        },
        "z-ai/glm-4.5v": {
            "purpose": ModelPurpose.VISION,
            "description": "Advanced vision tasks",
            "priority": 4,
            "cost_tier": "standard"
        }
    }

    # TASK-TO-MODEL MAPPING
    TASK_ROUTING = {
        "critical_decision": ["openai/gpt-5", "x-ai/grok-4"],  # GPT-5 decides, Grok-4 counters
        "code_generation": ["x-ai/grok-code-fast-1", "qwen/qwen3-30b-a3b-thinking-2507"],
        "research_analysis": ["openai/gpt-5", "nousresearch/hermes-4-405b"],
        "creative_tasks": ["anthropic/claude-sonnet-4", "deepseek/deepseek-chat-v3-0324"],
        "vision_tasks": ["google/gemini-2.5-flash-image-preview:free", "z-ai/glm-4.5v"],
        "quick_tasks": ["openai/gpt-5-mini", "x-ai/grok-code-fast-1"],
        "deep_reasoning": ["qwen/qwen3-30b-a3b-thinking-2507", "openai/gpt-5"]
    }

    def __init__(self):
        self.active_model = "openai/gpt-5"  # Default to most important
        self.fallback_chain = [
            "openai/gpt-5",
            "x-ai/grok-4",
            "qwen/qwen3-30b-a3b-thinking-2507"
        ]
        self.usage_stats = dict.fromkeys(self.APPROVED_MODELS, 0)
        self.model_health = dict.fromkeys(self.APPROVED_MODELS, "healthy")

    def select_model(self, task_type: str, importance: str = "normal") -> str:
        """
        Select appropriate model based on task and importance
        ONLY returns approved models
        """
        if importance == "critical":
            # Always use GPT-5 for critical tasks
            return "openai/gpt-5"
        elif importance == "counter":
            # Use Grok-4 for counter-reasoning
            return "x-ai/grok-4"

        # Get models for task type
        models = self.TASK_ROUTING.get(task_type, ["openai/gpt-5"])

        # Return first healthy model
        for model in models:
            if self.model_health.get(model) == "healthy":
                return model

        # Fallback to GPT-5
        return "openai/gpt-5"

    def validate_model(self, model: str) -> bool:
        """Check if model is in approved list"""
        return model in self.APPROVED_MODELS

    def get_model_info(self, model: str) -> dict | None:
        """Get information about a model"""
        if not self.validate_model(model):
            raise ValueError(f"Model {model} is NOT APPROVED! Use only: {list(self.APPROVED_MODELS.keys())}")
        return self.APPROVED_MODELS.get(model)

    def get_dashboard_data(self) -> dict:
        """Get data for dashboard display"""
        return {
            "approved_models": list(self.APPROVED_MODELS.keys()),
            "active_model": self.active_model,
            "model_health": self.model_health,
            "usage_stats": self.usage_stats,
            "task_routing": self.TASK_ROUTING,
            "primary_models": {
                "critical": "openai/gpt-5",
                "counter_reasoning": "x-ai/grok-4"
            }
        }

    def update_model_health(self, model: str, status: str):
        """Update model health status"""
        if self.validate_model(model):
            self.model_health[model] = status

            # If primary model fails, switch to fallback
            if model == self.active_model and status != "healthy":
                for fallback in self.fallback_chain:
                    if self.model_health.get(fallback) == "healthy":
                        self.active_model = fallback
                        break

    def record_usage(self, model: str):
        """Record model usage for monitoring"""
        if self.validate_model(model):
            self.usage_stats[model] += 1

# Global instance for centralized control
model_controller = CentralizedModelControl()

def get_model_for_task(task: str, importance: str = "normal") -> str:
    """
    Public API to get the right model for a task
    GUARANTEES only approved models are returned
    """
    return model_controller.select_model(task, importance)

def validate_model_choice(model: str) -> bool:
    """Validate if a model is approved for use"""
    return model_controller.validate_model(model)
