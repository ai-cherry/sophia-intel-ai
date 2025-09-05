"""
Task-Specific Intelligent Routing System
Routes tasks to optimal providers based on task type and provider strengths
"""

import logging
import random
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from app.swarms.core.rate_limit_monitor import get_rate_monitor

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of tasks with different requirements"""

    # Coding tasks
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    CODE_DEBUGGING = "code_debugging"
    CODE_REFACTORING = "code_refactoring"

    # Analysis tasks
    DEEP_ANALYSIS = "deep_analysis"
    DATA_ANALYSIS = "data_analysis"
    SECURITY_ANALYSIS = "security_analysis"

    # Research tasks
    WEB_RESEARCH = "web_research"
    ACADEMIC_RESEARCH = "academic_research"
    TECHNICAL_RESEARCH = "technical_research"

    # Creative tasks
    CREATIVE_WRITING = "creative_writing"
    BRAINSTORMING = "brainstorming"
    DESIGN_THINKING = "design_thinking"

    # Fast tasks
    QUICK_ANSWER = "quick_answer"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"

    # Reasoning tasks
    COMPLEX_REASONING = "complex_reasoning"
    MATHEMATICAL = "mathematical"
    LOGICAL_ANALYSIS = "logical_analysis"

    # Planning tasks
    PROJECT_PLANNING = "project_planning"
    ARCHITECTURE_DESIGN = "architecture_design"
    STRATEGY_PLANNING = "strategy_planning"


@dataclass
class TaskRequirements:
    """Requirements for a specific task"""

    task_type: TaskType
    estimated_tokens: int = 1000
    max_latency_seconds: Optional[float] = None
    required_capabilities: list[str] = None
    preferred_providers: list[str] = None
    avoid_providers: list[str] = None
    min_quality_score: float = 0.7


class TaskRouter:
    """Route tasks to optimal providers based on task requirements and provider capabilities"""

    # Provider strengths matrix (0-1 scoring)
    PROVIDER_STRENGTHS = {
        "deepseek": {
            TaskType.CODE_GENERATION: 0.95,
            TaskType.CODE_DEBUGGING: 0.95,
            TaskType.CODE_REFACTORING: 0.90,
            TaskType.CODE_REVIEW: 0.85,
            TaskType.MATHEMATICAL: 0.80,
            TaskType.LOGICAL_ANALYSIS: 0.85,
            "special_features": ["specialized_coding", "cost_effective"],
        },
        "openai": {
            TaskType.CODE_GENERATION: 0.90,
            TaskType.DEEP_ANALYSIS: 0.95,
            TaskType.CREATIVE_WRITING: 0.90,
            TaskType.COMPLEX_REASONING: 0.95,
            TaskType.PROJECT_PLANNING: 0.90,
            TaskType.ARCHITECTURE_DESIGN: 0.90,
            "special_features": ["general_excellence", "reliable"],
        },
        "anthropic": {
            TaskType.CODE_REVIEW: 0.95,
            TaskType.DEEP_ANALYSIS: 0.95,
            TaskType.SECURITY_ANALYSIS: 0.95,
            TaskType.CREATIVE_WRITING: 0.95,
            TaskType.COMPLEX_REASONING: 0.90,
            TaskType.ACADEMIC_RESEARCH: 0.90,
            "special_features": ["safety_focused", "thorough_analysis", "ethical"],
        },
        "perplexity": {
            TaskType.WEB_RESEARCH: 1.0,
            TaskType.ACADEMIC_RESEARCH: 0.95,
            TaskType.TECHNICAL_RESEARCH: 0.90,
            TaskType.DATA_ANALYSIS: 0.80,
            "special_features": ["real_time_search", "citations", "current_data"],
        },
        "groq": {
            TaskType.QUICK_ANSWER: 1.0,
            TaskType.CLASSIFICATION: 0.95,
            TaskType.EXTRACTION: 0.95,
            TaskType.CODE_GENERATION: 0.75,
            TaskType.DATA_ANALYSIS: 0.80,
            "special_features": ["ultra_fast", "high_throughput", "low_latency"],
        },
        "xai": {
            TaskType.COMPLEX_REASONING: 0.90,
            TaskType.CODE_GENERATION: 0.85,
            TaskType.CREATIVE_WRITING: 0.85,
            TaskType.BRAINSTORMING: 0.85,
            TaskType.DEEP_ANALYSIS: 0.85,
            "special_features": ["reasoning", "creative", "unconventional"],
        },
        "together": {
            TaskType.CODE_GENERATION: 0.80,
            TaskType.DATA_ANALYSIS: 0.85,
            TaskType.QUICK_ANSWER: 0.85,
            TaskType.CLASSIFICATION: 0.85,
            "special_features": ["open_source", "scalable", "cost_effective"],
        },
        "mistral": {
            TaskType.CODE_GENERATION: 0.80,
            TaskType.QUICK_ANSWER: 0.85,
            TaskType.CLASSIFICATION: 0.85,
            TaskType.EXTRACTION: 0.80,
            "special_features": ["european", "efficient", "multilingual"],
        },
        "cohere": {
            TaskType.CLASSIFICATION: 0.90,
            TaskType.EXTRACTION: 0.90,
            TaskType.DATA_ANALYSIS: 0.85,
            TaskType.WEB_RESEARCH: 0.80,
            "special_features": ["rag_optimized", "embeddings", "reranking"],
        },
        "openrouter": {
            # OpenRouter is a gateway - can access many models
            TaskType.CODE_GENERATION: 0.85,
            TaskType.DEEP_ANALYSIS: 0.85,
            TaskType.CREATIVE_WRITING: 0.85,
            "special_features": ["model_variety", "fallback_option", "flexible"],
        },
    }

    # Virtual key to provider mapping
    VIRTUAL_KEY_PROVIDERS = {
        "deepseek-vk-24102f": "deepseek",
        "openai-vk-190a60": "openai",
        "anthropic-vk-b42804": "anthropic",
        "vkj-openrouter-cc4151": "openrouter",
        "perplexity-vk-56c172": "perplexity",
        "groq-vk-6b9b52": "groq",
        "mistral-vk-f92861": "mistral",
        "xai-vk-e65d0f": "xai",
        "together-ai-670469": "together",
        "cohere-vk-496fa9": "cohere",
    }

    def __init__(self):
        self.rate_monitor = get_rate_monitor()
        self.routing_history = []

    def route_task(self, requirements: TaskRequirements) -> tuple[str, dict[str, Any]]:
        """
        Route a task to the optimal provider.

        Returns:
            Tuple of (virtual_key, routing_metadata)
        """

        # Get candidate providers
        candidates = self._get_candidate_providers(requirements)

        if not candidates:
            # Fallback to any available provider
            logger.warning(f"No optimal provider for {requirements.task_type}, using fallback")
            return self._get_fallback_provider(requirements)

        # Score and rank candidates
        scored_candidates = []
        for virtual_key, provider in candidates:
            score = self._score_provider(provider, requirements)
            scored_candidates.append((virtual_key, provider, score))

        # Sort by score
        scored_candidates.sort(key=lambda x: x[2], reverse=True)

        # Select best available
        for virtual_key, provider, score in scored_candidates:
            if self.rate_monitor.rate_limits[virtual_key].can_handle_request(
                requirements.estimated_tokens
            ):
                metadata = {
                    "task_type": requirements.task_type.value,
                    "provider": provider,
                    "score": round(score, 3),
                    "reason": self._get_selection_reason(provider, requirements),
                    "estimated_tokens": requirements.estimated_tokens,
                }

                # Record routing decision
                self.routing_history.append(
                    {
                        "virtual_key": virtual_key,
                        "provider": provider,
                        "task_type": requirements.task_type.value,
                        "score": score,
                    }
                )

                logger.info(
                    f"Routed {requirements.task_type.value} to {provider} (score: {score:.2f})"
                )

                return virtual_key, metadata

        # If no provider has capacity, return the best one anyway
        best_key, best_provider, best_score = scored_candidates[0]
        logger.warning(f"All providers at capacity, using best match: {best_provider}")

        return best_key, {
            "task_type": requirements.task_type.value,
            "provider": best_provider,
            "score": round(best_score, 3),
            "warning": "Provider at capacity",
        }

    def _get_candidate_providers(self, requirements: TaskRequirements) -> list[tuple[str, str]]:
        """Get list of candidate providers for a task"""

        candidates = []

        for virtual_key, provider in self.VIRTUAL_KEY_PROVIDERS.items():
            # Check if provider is avoided
            if requirements.avoid_providers and provider in requirements.avoid_providers:
                continue

            # Check if provider is in preferred list
            if requirements.preferred_providers:
                if provider not in requirements.preferred_providers:
                    continue

            # Check if provider has capability for this task
            provider_config = self.PROVIDER_STRENGTHS.get(provider, {})
            if requirements.task_type in provider_config:
                score = provider_config[requirements.task_type]
                if score >= requirements.min_quality_score:
                    candidates.append((virtual_key, provider))

        return candidates

    def _score_provider(self, provider: str, requirements: TaskRequirements) -> float:
        """Score a provider for a specific task"""

        provider_config = self.PROVIDER_STRENGTHS.get(provider, {})

        # Base score from task capability
        base_score = provider_config.get(requirements.task_type, 0.5)

        # Adjust for latency requirements
        latency_multiplier = 1.0
        if requirements.max_latency_seconds:
            if "ultra_fast" in provider_config.get("special_features", []):
                latency_multiplier = 1.2
            elif requirements.max_latency_seconds < 2.0 and "ultra_fast" not in provider_config.get(
                "special_features", []
            ):
                latency_multiplier = 0.5

        # Adjust for special requirements
        feature_bonus = 0.0
        if requirements.required_capabilities:
            for capability in requirements.required_capabilities:
                if capability in provider_config.get("special_features", []):
                    feature_bonus += 0.1

        # Get current availability
        virtual_key = None
        for vk, p in self.VIRTUAL_KEY_PROVIDERS.items():
            if p == provider:
                virtual_key = vk
                break

        availability_multiplier = 1.0
        if virtual_key and virtual_key in self.rate_monitor.rate_limits:
            availability = self.rate_monitor.rate_limits[virtual_key].get_availability()
            availability_multiplier = 0.5 + (availability * 0.5)  # 0.5 to 1.0 based on availability

        # Calculate final score
        final_score = (base_score * latency_multiplier + feature_bonus) * availability_multiplier

        return min(1.0, final_score)

    def _get_selection_reason(self, provider: str, requirements: TaskRequirements) -> str:
        """Get human-readable reason for provider selection"""

        provider_config = self.PROVIDER_STRENGTHS.get(provider, {})
        task_score = provider_config.get(requirements.task_type, 0)
        features = provider_config.get("special_features", [])

        reasons = []

        if task_score >= 0.9:
            reasons.append(f"excellent at {requirements.task_type.value}")
        elif task_score >= 0.8:
            reasons.append(f"good at {requirements.task_type.value}")

        if requirements.max_latency_seconds and "ultra_fast" in features:
            reasons.append("ultra-fast response")

        if requirements.required_capabilities:
            matching = [cap for cap in requirements.required_capabilities if cap in features]
            if matching:
                reasons.append(f"has {', '.join(matching)}")

        return "; ".join(reasons) if reasons else "best available option"

    def _get_fallback_provider(self, requirements: TaskRequirements) -> tuple[str, dict[str, Any]]:
        """Get a fallback provider when no optimal match exists"""

        # Try OpenRouter as it has access to many models
        if "vkj-openrouter-cc4151" in self.rate_monitor.rate_limits:
            if self.rate_monitor.rate_limits["vkj-openrouter-cc4151"].can_handle_request(
                requirements.estimated_tokens
            ):
                return "vkj-openrouter-cc4151", {
                    "provider": "openrouter",
                    "reason": "fallback - model variety",
                    "task_type": requirements.task_type.value,
                }

        # Get any available provider
        best_key = self.rate_monitor.get_best_key_for_task(requirements.estimated_tokens)
        if best_key:
            return best_key, {
                "provider": self.VIRTUAL_KEY_PROVIDERS.get(best_key, "unknown"),
                "reason": "fallback - best available",
                "task_type": requirements.task_type.value,
            }

        # Last resort - pick a random key
        all_keys = list(self.VIRTUAL_KEY_PROVIDERS.keys())
        return random.choice(all_keys), {
            "provider": "random",
            "reason": "emergency fallback",
            "warning": "all providers at capacity",
        }

    def get_routing_recommendations(self) -> dict[str, list[str]]:
        """Get recommendations for task routing"""

        recommendations = {}

        for task_type in TaskType:
            best_providers = []

            for provider, config in self.PROVIDER_STRENGTHS.items():
                score = config.get(task_type, 0)
                if score >= 0.8:
                    best_providers.append(f"{provider} ({score:.0%})")

            if best_providers:
                recommendations[task_type.value] = best_providers
            else:
                recommendations[task_type.value] = ["openrouter (fallback)"]

        return recommendations


# Convenience functions for common routing patterns


def route_coding_task(code: str, task: str = "generate") -> tuple[str, dict[str, Any]]:
    """Route a coding task to the best provider"""

    router = TaskRouter()

    # Determine task type
    if "debug" in task.lower():
        task_type = TaskType.CODE_DEBUGGING
    elif "review" in task.lower():
        task_type = TaskType.CODE_REVIEW
    elif "refactor" in task.lower():
        task_type = TaskType.CODE_REFACTORING
    else:
        task_type = TaskType.CODE_GENERATION

    requirements = TaskRequirements(
        task_type=task_type,
        estimated_tokens=len(code) // 4 + 500,  # Rough estimate
        preferred_providers=["deepseek", "openai", "anthropic"],
        required_capabilities=["specialized_coding"]
        if task_type == TaskType.CODE_GENERATION
        else None,
    )

    return router.route_task(requirements)


def route_research_task(query: str, need_realtime: bool = False) -> tuple[str, dict[str, Any]]:
    """Route a research task to the best provider"""

    router = TaskRouter()

    requirements = TaskRequirements(
        task_type=TaskType.WEB_RESEARCH if need_realtime else TaskType.TECHNICAL_RESEARCH,
        estimated_tokens=500,
        preferred_providers=["perplexity"] if need_realtime else ["anthropic", "openai"],
        required_capabilities=["real_time_search", "citations"]
        if need_realtime
        else ["thorough_analysis"],
    )

    return router.route_task(requirements)


def route_fast_task(prompt: str) -> tuple[str, dict[str, Any]]:
    """Route a fast task to the speediest provider"""

    router = TaskRouter()

    requirements = TaskRequirements(
        task_type=TaskType.QUICK_ANSWER,
        estimated_tokens=200,
        max_latency_seconds=1.0,
        preferred_providers=["groq", "together", "mistral"],
        required_capabilities=["ultra_fast"],
    )

    return router.route_task(requirements)


def route_analysis_task(content: str, analysis_type: str = "general") -> tuple[str, dict[str, Any]]:
    """Route an analysis task to the best provider"""

    router = TaskRouter()

    # Determine specific analysis type
    if "security" in analysis_type.lower():
        task_type = TaskType.SECURITY_ANALYSIS
        preferred = ["anthropic", "openai"]
    elif "data" in analysis_type.lower():
        task_type = TaskType.DATA_ANALYSIS
        preferred = ["openai", "together", "cohere"]
    else:
        task_type = TaskType.DEEP_ANALYSIS
        preferred = ["anthropic", "openai", "xai"]

    requirements = TaskRequirements(
        task_type=task_type,
        estimated_tokens=len(content) // 4 + 1000,
        preferred_providers=preferred,
        min_quality_score=0.8,
    )

    return router.route_task(requirements)


# Example usage
if __name__ == "__main__":
    # Create router
    router = TaskRouter()

    # Test different task types
    test_tasks = [
        TaskRequirements(TaskType.CODE_GENERATION, estimated_tokens=2000),
        TaskRequirements(
            TaskType.WEB_RESEARCH, estimated_tokens=500, required_capabilities=["real_time_search"]
        ),
        TaskRequirements(TaskType.QUICK_ANSWER, estimated_tokens=100, max_latency_seconds=0.5),
        TaskRequirements(TaskType.DEEP_ANALYSIS, estimated_tokens=3000),
        TaskRequirements(TaskType.CREATIVE_WRITING, estimated_tokens=1500),
    ]

    print("Task Routing Examples:")
    print("=" * 70)

    for req in test_tasks:
        virtual_key, metadata = router.route_task(req)
        print(f"\nTask: {req.task_type.value}")
        print(f"  → Provider: {metadata.get('provider')}")
        print(f"  → Score: {metadata.get('score')}")
        print(f"  → Reason: {metadata.get('reason')}")

    # Show recommendations
    print("\n" + "=" * 70)
    print("Routing Recommendations by Task Type:")
    print("=" * 70)

    recommendations = router.get_routing_recommendations()
    for task_type, providers in recommendations.items():
        print(f"\n{task_type}:")
        for provider in providers:
            print(f"  • {provider}")
