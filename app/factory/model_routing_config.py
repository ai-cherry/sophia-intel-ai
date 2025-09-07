"""
Advanced Model Routing Configuration for Swarm Factory
Integrates with Portkey for intelligent model selection based on agent roles,
task types, cost constraints, and performance requirements.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.core.portkey_manager import TaskType, get_portkey_manager
from app.swarms.core.micro_swarm_base import AgentRole

logger = logging.getLogger(__name__)


class ModelPerformanceTier(Enum):
    """Model performance tiers for different requirements"""

    PREMIUM = "premium"  # Best models regardless of cost
    BALANCED = "balanced"  # Good performance with reasonable cost
    EFFICIENT = "efficient"  # Cost-effective models for routine tasks
    SPEED = "speed"  # Fastest models for real-time responses


class SwarmModelProfile(Enum):
    """Model profiles for different swarm types"""

    MYTHOLOGY_STRATEGIC = "mythology_strategic"  # High-quality models for strategic thinking
    MYTHOLOGY_ANALYTICAL = "mythology_analytical"  # Analysis-optimized models
    MILITARY_TACTICAL = "military_tactical"  # Fast, precise models for tactical operations
    MILITARY_RECON = "military_recon"  # Efficient scanning and pattern recognition
    HYBRID_BALANCED = "hybrid_balanced"  # Balanced mix for hybrid swarms
    CUSTOM_CONFIGURABLE = "custom_configurable"  # User-configurable routing


@dataclass
class ModelRoutingRule:
    """Rule for routing model requests"""

    rule_id: str
    name: str
    description: str

    # Matching criteria
    agent_roles: list[AgentRole] = field(default_factory=list)
    task_types: list[TaskType] = field(default_factory=list)
    swarm_profiles: list[SwarmModelProfile] = field(default_factory=list)

    # Model preferences
    primary_models: list[str] = field(default_factory=list)
    fallback_models: list[str] = field(default_factory=list)
    excluded_models: list[str] = field(default_factory=list)

    # Performance constraints
    max_cost_per_1k_tokens: float = 0.05
    min_context_window: int = 4000
    required_capabilities: list[str] = field(default_factory=list)

    # Quality requirements
    min_performance_tier: ModelPerformanceTier = ModelPerformanceTier.EFFICIENT
    prefer_streaming: bool = False
    require_function_calling: bool = False

    # Routing behavior
    enable_fallback: bool = True
    retry_on_failure: bool = True
    cache_responses: bool = True
    priority: int = 1  # 1=highest, 10=lowest

    # Metadata
    enabled: bool = True
    created_by: str = "system"
    tags: list[str] = field(default_factory=list)


class ModelRoutingEngine:
    """Advanced model routing engine for swarm factory"""

    def __init__(self):
        self.portkey = get_portkey_manager()
        self.routing_rules: dict[str, ModelRoutingRule] = {}
        self.model_performance_cache: dict[str, dict[str, float]] = {}
        self.routing_statistics = {
            "total_requests": 0,
            "successful_routes": 0,
            "fallback_usage": 0,
            "model_usage_counts": {},
            "cost_savings": 0.0,
        }

        # Initialize default routing rules
        self._initialize_default_rules()

        logger.info("Model routing engine initialized")

    def _initialize_default_rules(self):
        """Initialize default routing rules for different swarm types"""

        # Mythology Strategic - Premium models for strategic thinking
        self.routing_rules["mythology_strategic"] = ModelRoutingRule(
            rule_id="mythology_strategic",
            name="Mythology Strategic Routing",
            description="Premium models for mythology agents doing strategic analysis",
            agent_roles=[AgentRole.STRATEGIST],
            task_types=[TaskType.LONG_PLANNING, TaskType.ORCHESTRATION],
            swarm_profiles=[SwarmModelProfile.MYTHOLOGY_STRATEGIC],
            primary_models=["openai/gpt-5-chat", "anthropic/claude-3-5-sonnet", "x-ai/grok-5"],
            fallback_models=["openai/gpt-4o", "anthropic/claude-3-sonnet", "google/gemini-2.0-pro"],
            max_cost_per_1k_tokens=0.10,
            min_context_window=8000,
            min_performance_tier=ModelPerformanceTier.PREMIUM,
            required_capabilities=["reasoning", "planning", "strategic_analysis"],
            tags=["mythology", "strategic", "premium"],
        )

        # Mythology Analytical - Balanced models for deep analysis
        self.routing_rules["mythology_analytical"] = ModelRoutingRule(
            rule_id="mythology_analytical",
            name="Mythology Analytical Routing",
            description="Analysis-optimized models for mythology agents",
            agent_roles=[AgentRole.ANALYST, AgentRole.VALIDATOR],
            task_types=[TaskType.WEB_RESEARCH, TaskType.CODE_REVIEW],
            swarm_profiles=[SwarmModelProfile.MYTHOLOGY_ANALYTICAL],
            primary_models=["anthropic/claude-3-opus", "openai/gpt-4o", "deepseek/deepseek-chat"],
            fallback_models=[
                "anthropic/claude-3-sonnet",
                "google/gemini-2.0-pro",
                "qwen/qwen-3-70b",
            ],
            max_cost_per_1k_tokens=0.075,
            min_context_window=6000,
            min_performance_tier=ModelPerformanceTier.BALANCED,
            required_capabilities=["analysis", "reasoning", "validation"],
            tags=["mythology", "analytical", "balanced"],
        )

        # Military Tactical - Fast, precise models for tactical operations
        self.routing_rules["military_tactical"] = ModelRoutingRule(
            rule_id="military_tactical",
            name="Military Tactical Routing",
            description="Fast, precise models for military-themed swarms",
            agent_roles=[AgentRole.STRATEGIST, AgentRole.ANALYST],
            task_types=[TaskType.CODE_GENERATION, TaskType.CODE_REVIEW],
            swarm_profiles=[SwarmModelProfile.MILITARY_TACTICAL],
            primary_models=[
                "deepseek/deepseek-coder-v3",
                "qwen/qwen-3-coder-plus",
                "openai/gpt-4o",
            ],
            fallback_models=[
                "deepseek/deepseek-chat",
                "anthropic/claude-3-sonnet",
                "google/gemini-2.0-flash",
            ],
            max_cost_per_1k_tokens=0.03,
            min_context_window=8000,
            min_performance_tier=ModelPerformanceTier.BALANCED,
            required_capabilities=["coding", "precision", "speed"],
            prefer_streaming=True,
            tags=["military", "tactical", "coding"],
        )

        # Military Recon - Efficient models for scanning and pattern recognition
        self.routing_rules["military_recon"] = ModelRoutingRule(
            rule_id="military_recon",
            name="Military Reconnaissance Routing",
            description="Efficient models for reconnaissance and scanning tasks",
            agent_roles=[AgentRole.ANALYST],
            task_types=[TaskType.WEB_RESEARCH, TaskType.GENERAL],
            swarm_profiles=[SwarmModelProfile.MILITARY_RECON],
            primary_models=[
                "google/gemini-2.0-flash-exp",
                "groq/llama-3.1-70b-versatile",
                "deepseek/deepseek-chat",
            ],
            fallback_models=[
                "openai/gpt-4o-mini",
                "anthropic/claude-3-haiku",
                "google/gemini-1.5-flash",
            ],
            max_cost_per_1k_tokens=0.015,
            min_context_window=4000,
            min_performance_tier=ModelPerformanceTier.EFFICIENT,
            required_capabilities=["pattern_recognition", "scanning", "efficiency"],
            prefer_streaming=True,
            tags=["military", "recon", "efficient"],
        )

        # Hybrid Balanced - Mixed approach for hybrid swarms
        self.routing_rules["hybrid_balanced"] = ModelRoutingRule(
            rule_id="hybrid_balanced",
            name="Hybrid Balanced Routing",
            description="Balanced model selection for hybrid mythology-military swarms",
            agent_roles=[AgentRole.ANALYST, AgentRole.STRATEGIST, AgentRole.VALIDATOR],
            task_types=[TaskType.GENERAL, TaskType.LONG_PLANNING, TaskType.CODE_REVIEW],
            swarm_profiles=[SwarmModelProfile.HYBRID_BALANCED],
            primary_models=["openai/gpt-4o", "anthropic/claude-3-sonnet", "google/gemini-2.0-pro"],
            fallback_models=["deepseek/deepseek-chat", "qwen/qwen-3-70b", "x-ai/grok-4"],
            max_cost_per_1k_tokens=0.04,
            min_context_window=6000,
            min_performance_tier=ModelPerformanceTier.BALANCED,
            required_capabilities=["versatility", "reasoning", "analysis"],
            tags=["hybrid", "balanced", "versatile"],
        )

        # Cost-Conscious - For budget-constrained operations
        self.routing_rules["cost_conscious"] = ModelRoutingRule(
            rule_id="cost_conscious",
            name="Cost-Conscious Routing",
            description="Cost-optimized model selection for routine operations",
            agent_roles=[AgentRole.ANALYST, AgentRole.VALIDATOR],
            task_types=[TaskType.GENERAL, TaskType.DRAFT],
            primary_models=[
                "openai/gpt-4o-mini",
                "anthropic/claude-3-haiku",
                "groq/llama-3.1-8b-instant",
            ],
            fallback_models=[
                "google/gemini-1.5-flash",
                "deepseek/deepseek-chat",
                "qwen/qwen-2.5-7b",
            ],
            max_cost_per_1k_tokens=0.005,
            min_context_window=4000,
            min_performance_tier=ModelPerformanceTier.EFFICIENT,
            required_capabilities=["cost_efficiency"],
            prefer_streaming=True,
            tags=["cost_conscious", "efficient", "budget"],
        )

        logger.info(f"Initialized {len(self.routing_rules)} default routing rules")

    def route_request(
        self,
        agent_role: AgentRole,
        task_type: TaskType,
        swarm_profile: SwarmModelProfile,
        estimated_tokens: int = 1000,
        cost_limit: float = None,
        context: dict[str, Any] = None,
    ) -> dict[str, Any]:
        """
        Route model request based on agent role, task type, and constraints

        Args:
            agent_role: Role of the requesting agent
            task_type: Type of task being performed
            swarm_profile: Profile of the swarm making the request
            estimated_tokens: Estimated token count
            cost_limit: Maximum cost constraint
            context: Additional routing context

        Returns:
            Routing decision with model, rationale, and fallbacks
        """
        context = context or {}

        # Find matching routing rules
        matching_rules = self._find_matching_rules(agent_role, task_type, swarm_profile)

        if not matching_rules:
            # Fallback to default routing
            return self._get_default_routing(agent_role, task_type, estimated_tokens, cost_limit)

        # Select best rule (highest priority)
        best_rule = max(matching_rules, key=lambda r: r.priority)

        # Apply cost constraints
        if cost_limit:
            best_rule = self._apply_cost_constraints(best_rule, cost_limit, estimated_tokens)

        # Select primary model
        primary_model = self._select_primary_model(best_rule, context)

        # Prepare fallback options
        fallback_models = self._prepare_fallbacks(best_rule, context)

        # Get routing from Portkey
        portkey_routing = self.portkey.route_request(
            task_type=task_type,
            estimated_tokens=estimated_tokens,
            max_cost_usd=cost_limit or best_rule.max_cost_per_1k_tokens * (estimated_tokens / 1000),
            prefer_provider=primary_model.split("/")[0] if "/" in primary_model else None,
        )

        routing_decision = {
            "rule_used": best_rule.rule_id,
            "primary_model": primary_model,
            "fallback_models": fallback_models,
            "portkey_routing": {
                "provider": portkey_routing.provider,
                "model": portkey_routing.model,
                "virtual_key": portkey_routing.virtual_key,
                "estimated_cost": portkey_routing.estimated_cost,
            },
            "routing_rationale": self._generate_routing_rationale(best_rule, agent_role, task_type),
            "constraints_applied": {
                "cost_limit": cost_limit,
                "max_cost_per_1k": best_rule.max_cost_per_1k_tokens,
                "min_context_window": best_rule.min_context_window,
                "performance_tier": best_rule.min_performance_tier.value,
            },
            "metadata": {
                "rule_priority": best_rule.priority,
                "estimated_tokens": estimated_tokens,
                "swarm_profile": swarm_profile.value,
                "caching_enabled": best_rule.cache_responses,
            },
        }

        # Update statistics
        self._update_routing_stats(routing_decision)

        return routing_decision

    def _find_matching_rules(
        self, agent_role: AgentRole, task_type: TaskType, swarm_profile: SwarmModelProfile
    ) -> list[ModelRoutingRule]:
        """Find routing rules that match the request criteria"""

        matching_rules = []

        for rule in self.routing_rules.values():
            if not rule.enabled:
                continue

            # Check agent role match
            if rule.agent_roles and agent_role not in rule.agent_roles:
                continue

            # Check task type match
            if rule.task_types and task_type not in rule.task_types:
                continue

            # Check swarm profile match
            if rule.swarm_profiles and swarm_profile not in rule.swarm_profiles:
                continue

            matching_rules.append(rule)

        return matching_rules

    def _apply_cost_constraints(
        self, rule: ModelRoutingRule, cost_limit: float, estimated_tokens: int
    ) -> ModelRoutingRule:
        """Apply cost constraints to routing rule"""

        estimated_cost = (estimated_tokens / 1000) * rule.max_cost_per_1k_tokens

        if estimated_cost > cost_limit:
            # Create modified rule with tighter cost constraints
            import copy

            modified_rule = copy.deepcopy(rule)
            modified_rule.max_cost_per_1k_tokens = min(
                rule.max_cost_per_1k_tokens, cost_limit / (estimated_tokens / 1000)
            )

            # Filter models that are too expensive
            affordable_models = []
            for model in rule.primary_models:
                model_cost = self._estimate_model_cost(model)
                if (estimated_tokens / 1000) * model_cost <= cost_limit:
                    affordable_models.append(model)

            if affordable_models:
                modified_rule.primary_models = affordable_models
            else:
                # Use fallback models if primary models are too expensive
                modified_rule.primary_models = rule.fallback_models

            return modified_rule

        return rule

    def _select_primary_model(self, rule: ModelRoutingRule, context: dict[str, Any]) -> str:
        """Select the best primary model from the rule"""

        if not rule.primary_models:
            return "openai/gpt-4o-mini"  # Safe default

        # Consider performance cache if available
        if self.model_performance_cache:
            performance_scores = {}
            for model in rule.primary_models:
                if model in self.model_performance_cache:
                    cache_entry = self.model_performance_cache[model]
                    performance_scores[model] = cache_entry.get("avg_performance", 0.7)
                else:
                    performance_scores[model] = 0.7  # Default score

            # Select model with highest performance score
            best_model = max(performance_scores.items(), key=lambda x: x[1])[0]
            return best_model

        # Default to first model in list
        return rule.primary_models[0]

    def _prepare_fallbacks(self, rule: ModelRoutingRule, context: dict[str, Any]) -> list[str]:
        """Prepare fallback model list"""

        fallbacks = []

        # Add rule-specific fallbacks
        fallbacks.extend(rule.fallback_models)

        # Add general fallbacks if needed
        general_fallbacks = [
            "openai/gpt-4o-mini",
            "anthropic/claude-3-haiku",
            "google/gemini-1.5-flash",
        ]

        for model in general_fallbacks:
            if model not in fallbacks and model not in rule.excluded_models:
                fallbacks.append(model)

        return fallbacks[:3]  # Limit to top 3 fallbacks

    def _get_default_routing(
        self, agent_role: AgentRole, task_type: TaskType, estimated_tokens: int, cost_limit: float
    ) -> dict[str, Any]:
        """Get default routing when no rules match"""

        # Use Portkey's built-in routing
        portkey_routing = self.portkey.route_request(
            task_type=task_type, estimated_tokens=estimated_tokens, max_cost_usd=cost_limit or 1.0
        )

        return {
            "rule_used": "default",
            "primary_model": f"{portkey_routing.provider}/{portkey_routing.model}",
            "fallback_models": [
                config.provider + "/" + config.model for config in portkey_routing.fallbacks
            ],
            "portkey_routing": {
                "provider": portkey_routing.provider,
                "model": portkey_routing.model,
                "virtual_key": portkey_routing.virtual_key,
                "estimated_cost": portkey_routing.estimated_cost,
            },
            "routing_rationale": "No specific routing rules matched, using Portkey default routing",
            "constraints_applied": {"cost_limit": cost_limit, "estimated_tokens": estimated_tokens},
            "metadata": {"rule_priority": 0, "fallback_routing": True},
        }

    def _estimate_model_cost(self, model: str) -> float:
        """Estimate cost per 1K tokens for a model"""

        # Model cost estimates (rough approximations)
        cost_map = {
            "openai/gpt-5-chat": 0.10,
            "openai/gpt-4o": 0.03,
            "openai/gpt-4o-mini": 0.002,
            "anthropic/claude-3-opus": 0.075,
            "anthropic/claude-3-sonnet": 0.018,
            "anthropic/claude-3-haiku": 0.001,
            "google/gemini-2.0-pro": 0.02,
            "google/gemini-2.0-flash": 0.001,
            "deepseek/deepseek-coder-v3": 0.001,
            "deepseek/deepseek-chat": 0.0005,
            "x-ai/grok-5": 0.05,
            "x-ai/grok-4": 0.03,
            "groq/llama-3.1-70b-versatile": 0.0008,
        }

        return cost_map.get(model, 0.01)  # Default estimate

    def _generate_routing_rationale(
        self, rule: ModelRoutingRule, agent_role: AgentRole, task_type: TaskType
    ) -> str:
        """Generate human-readable routing rationale"""

        rationale_parts = [
            f"Selected rule '{rule.name}' for {agent_role.value} agent performing {task_type.value} task"
        ]

        if rule.min_performance_tier != ModelPerformanceTier.EFFICIENT:
            rationale_parts.append(
                f"Using {rule.min_performance_tier.value} tier models for quality"
            )

        if rule.max_cost_per_1k_tokens < 0.01:
            rationale_parts.append("Cost-optimized routing applied")

        if rule.prefer_streaming:
            rationale_parts.append("Streaming-capable models preferred")

        return ". ".join(rationale_parts) + "."

    def _update_routing_stats(self, routing_decision: dict[str, Any]):
        """Update routing statistics"""

        self.routing_statistics["total_requests"] += 1

        if routing_decision.get("portkey_routing"):
            self.routing_statistics["successful_routes"] += 1

        if routing_decision["rule_used"] == "default":
            self.routing_statistics["fallback_usage"] += 1

        model = routing_decision["primary_model"]
        self.routing_statistics["model_usage_counts"][model] = (
            self.routing_statistics["model_usage_counts"].get(model, 0) + 1
        )

    def add_routing_rule(self, rule: ModelRoutingRule):
        """Add a custom routing rule"""
        self.routing_rules[rule.rule_id] = rule
        logger.info(f"Added routing rule: {rule.name}")

    def remove_routing_rule(self, rule_id: str) -> bool:
        """Remove a routing rule"""
        if rule_id in self.routing_rules:
            del self.routing_rules[rule_id]
            logger.info(f"Removed routing rule: {rule_id}")
            return True
        return False

    def update_model_performance(self, model: str, performance_metrics: dict[str, float]):
        """Update model performance cache"""
        self.model_performance_cache[model] = performance_metrics

    def get_routing_statistics(self) -> dict[str, Any]:
        """Get routing statistics"""

        success_rate = 0.0
        if self.routing_statistics["total_requests"] > 0:
            success_rate = (
                self.routing_statistics["successful_routes"]
                / self.routing_statistics["total_requests"]
            )

        fallback_rate = 0.0
        if self.routing_statistics["total_requests"] > 0:
            fallback_rate = (
                self.routing_statistics["fallback_usage"]
                / self.routing_statistics["total_requests"]
            )

        return {
            "total_requests": self.routing_statistics["total_requests"],
            "success_rate": success_rate,
            "fallback_rate": fallback_rate,
            "most_used_models": sorted(
                self.routing_statistics["model_usage_counts"].items(),
                key=lambda x: x[1],
                reverse=True,
            )[:5],
            "active_rules": len([r for r in self.routing_rules.values() if r.enabled]),
            "total_rules": len(self.routing_rules),
        }


# Global routing engine instance
_routing_engine = None


def get_routing_engine() -> ModelRoutingEngine:
    """Get global model routing engine instance"""
    global _routing_engine
    if _routing_engine is None:
        _routing_engine = ModelRoutingEngine()
    return _routing_engine


# Convenience functions for creating common routing rules
def create_cost_optimized_rule(rule_id: str, max_cost_per_1k: float = 0.005) -> ModelRoutingRule:
    """Create a cost-optimized routing rule"""
    return ModelRoutingRule(
        rule_id=rule_id,
        name=f"Cost Optimized ({max_cost_per_1k} per 1K tokens)",
        description="Cost-optimized routing for budget-conscious operations",
        primary_models=[
            "openai/gpt-4o-mini",
            "anthropic/claude-3-haiku",
            "groq/llama-3.1-8b-instant",
        ],
        fallback_models=["google/gemini-1.5-flash", "deepseek/deepseek-chat"],
        max_cost_per_1k_tokens=max_cost_per_1k,
        min_performance_tier=ModelPerformanceTier.EFFICIENT,
        tags=["cost_optimized", "budget"],
    )


def create_quality_focused_rule(rule_id: str, agent_roles: list[AgentRole]) -> ModelRoutingRule:
    """Create a quality-focused routing rule"""
    return ModelRoutingRule(
        rule_id=rule_id,
        name="Quality Focused Routing",
        description="High-quality models for critical tasks",
        agent_roles=agent_roles,
        primary_models=["openai/gpt-5-chat", "anthropic/claude-3-opus", "x-ai/grok-5"],
        fallback_models=["openai/gpt-4o", "anthropic/claude-3-sonnet"],
        max_cost_per_1k_tokens=0.10,
        min_performance_tier=ModelPerformanceTier.PREMIUM,
        tags=["quality_focused", "premium"],
    )


def create_speed_optimized_rule(rule_id: str, task_types: list[TaskType]) -> ModelRoutingRule:
    """Create a speed-optimized routing rule"""
    return ModelRoutingRule(
        rule_id=rule_id,
        name="Speed Optimized Routing",
        description="Fast models for time-sensitive tasks",
        task_types=task_types,
        primary_models=[
            "groq/llama-3.1-70b-versatile",
            "google/gemini-2.0-flash-exp",
            "deepseek/deepseek-chat",
        ],
        fallback_models=["openai/gpt-4o-mini", "anthropic/claude-3-haiku"],
        max_cost_per_1k_tokens=0.02,
        min_performance_tier=ModelPerformanceTier.SPEED,
        prefer_streaming=True,
        tags=["speed_optimized", "fast"],
    )
