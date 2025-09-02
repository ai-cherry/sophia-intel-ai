from app.config.env_loader import get_env_config

class IntelligentModelSelector:
    def __init__(self):
        """Initialize with environment configuration for GPT-5 availability."""
        self.env_config = get_env_config()
        self.gpt5_enabled = self._is_gpt5_enabled()

    def _is_gpt5_enabled(self) -> bool:
        """Check if GPT-5 should be enabled based on environment."""
        return self.env_config.environment_name == "production" and os.getenv("GPT5_ENABLED", "true").lower() == "true"

    def select_model(self, task_context: dict) -> str:
        """
        Select optimal model based on task characteristics.
        
        Args:
            task_context: Dictionary containing task attributes including:
                - complexity: "low", "medium", "high", "extreme"
                - budget: "minimal", "standard", "premium"
                - speed: "slow", "normal", "fast"
                - accuracy: "low", "medium", "high", "critical"
                - type: "chat", "code", "analysis", "multimodal"
                - is_multimodal: bool
        Returns:
            Model name from AVAILABLE_MODELS
        """
        complexity = task_context.get("complexity", "medium")
        budget = task_context.get("budget", "standard")
        speed_required = task_context.get("speed", "normal")
        accuracy_required = task_context.get("accuracy", "high")
        task_type = task_context.get("type")
        is_multimodal = task_context.get("is_multimodal", False)

        # Prioritize GPT-5 for high-severity tasks
        if (complexity == "extreme" or 
            accuracy_required == "critical" or 
            is_multimodal) and self.gpt5_enabled:
            return "openai/gpt-5"

        # Code-specific optimizations
        if task_type == "code":
            if speed_required == "fast":
                return "x-ai/grok-code-fast-1"
            return "openai/gpt-5"

        # Budget-driven selection
        if budget == "minimal":
            return "z-ai/glm-4.5-air"

        # Default to balanced standard model
        return "google/gemini-2.5-pro"
