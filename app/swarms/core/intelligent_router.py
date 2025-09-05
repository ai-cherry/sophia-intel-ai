"""
Intelligent LLM Router for Micro-Swarms
Advanced routing with agent-specific optimization, cost management, and performance tracking
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from app.core.portkey_manager import RoutingDecision, TaskType, get_portkey_manager
from app.memory.unified_memory_router import get_memory_router
from app.swarms.core.micro_swarm_base import AgentRole, SwarmMessage

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Routing strategies for different scenarios"""

    COST_OPTIMIZED = "cost_optimized"  # Minimize cost
    PERFORMANCE_OPTIMIZED = "performance_optimized"  # Maximize quality
    BALANCED = "balanced"  # Balance cost and performance
    AGENT_SPECIALIZED = "agent_specialized"  # Route based on agent specialization
    ADAPTIVE = "adaptive"  # Learn and adapt over time


class ModelTier(Enum):
    """Model capability tiers"""

    PREMIUM = "premium"  # GPT-4, Claude-3-Opus (highest capability, highest cost)
    STANDARD = "standard"  # GPT-4o, Claude-3-Sonnet (balanced)
    FAST = "fast"  # GPT-4o-mini, Claude-3-Haiku (fast, cost-effective)
    SPECIALIZED = "specialized"  # DeepSeek-Coder, Perplexity (task-specific)


@dataclass
class ModelPerformanceMetrics:
    """Performance metrics for a model"""

    model_name: str
    provider: str
    success_rate: float = 0.0
    avg_response_time_ms: float = 0.0
    avg_cost_per_request: float = 0.0
    avg_confidence_score: float = 0.0
    total_requests: int = 0
    last_updated: datetime = field(default_factory=datetime.now)

    # Agent-specific performance
    agent_performance: Dict[AgentRole, float] = field(default_factory=dict)
    task_performance: Dict[TaskType, float] = field(default_factory=dict)


@dataclass
class RoutingContext:
    """Context for routing decisions"""

    agent_role: AgentRole
    task_type: TaskType
    message_type: str
    swarm_budget: float
    time_constraint_ms: Optional[int] = None
    quality_requirement: float = 0.8  # 0.0 to 1.0
    previous_models_tried: List[str] = field(default_factory=list)
    retry_count: int = 0

    # Historical context
    recent_performance: Dict[str, float] = field(default_factory=dict)
    workload_characteristics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnhancedRoutingDecision:
    """Enhanced routing decision with additional metadata"""

    primary_choice: RoutingDecision
    fallback_choices: List[RoutingDecision]
    reasoning: str
    confidence: float
    expected_performance: ModelPerformanceMetrics
    cost_estimation: Dict[str, float]
    risk_assessment: Dict[str, float]
    routing_strategy_used: RoutingStrategy


class IntelligentRouter:
    """
    Advanced LLM router for micro-swarms with learning capabilities
    """

    def __init__(self):
        self.portkey = get_portkey_manager()
        self.memory = get_memory_router()

        # Performance tracking
        self.model_metrics: Dict[str, ModelPerformanceMetrics] = {}
        self.routing_history: List[Dict[str, Any]] = []

        # Model configuration
        self.model_tiers = self._initialize_model_tiers()
        self.agent_model_preferences = self._initialize_agent_preferences()

        # Adaptive parameters
        self.learning_rate = 0.1
        self.performance_window = timedelta(hours=24)

        logger.info("Intelligent Router initialized with adaptive capabilities")

    def _initialize_model_tiers(self) -> Dict[ModelTier, List[Dict[str, Any]]]:
        """Initialize model tier configurations"""
        return {
            ModelTier.PREMIUM: [
                {
                    "model": "gpt-4",
                    "provider": "openai",
                    "cost_multiplier": 10.0,
                    "quality_score": 0.95,
                },
                {
                    "model": "claude-3-opus",
                    "provider": "anthropic",
                    "cost_multiplier": 8.0,
                    "quality_score": 0.93,
                },
                {
                    "model": "gemini-2.0-pro",
                    "provider": "google",
                    "cost_multiplier": 6.0,
                    "quality_score": 0.90,
                },
            ],
            ModelTier.STANDARD: [
                {
                    "model": "gpt-4o",
                    "provider": "openai",
                    "cost_multiplier": 3.0,
                    "quality_score": 0.88,
                },
                {
                    "model": "claude-3-sonnet",
                    "provider": "anthropic",
                    "cost_multiplier": 3.5,
                    "quality_score": 0.86,
                },
                {
                    "model": "gemini-2.0-flash",
                    "provider": "google",
                    "cost_multiplier": 2.0,
                    "quality_score": 0.84,
                },
            ],
            ModelTier.FAST: [
                {
                    "model": "gpt-4o-mini",
                    "provider": "openai",
                    "cost_multiplier": 1.0,
                    "quality_score": 0.78,
                },
                {
                    "model": "claude-3-haiku",
                    "provider": "anthropic",
                    "cost_multiplier": 1.2,
                    "quality_score": 0.76,
                },
                {
                    "model": "llama3-70b",
                    "provider": "groq",
                    "cost_multiplier": 0.8,
                    "quality_score": 0.74,
                },
            ],
            ModelTier.SPECIALIZED: [
                {
                    "model": "deepseek-coder",
                    "provider": "deepseek",
                    "cost_multiplier": 1.5,
                    "quality_score": 0.92,
                    "specialization": "coding",
                },
                {
                    "model": "sonar-large",
                    "provider": "perplexity",
                    "cost_multiplier": 2.0,
                    "quality_score": 0.89,
                    "specialization": "research",
                },
                {
                    "model": "grok-beta",
                    "provider": "xai",
                    "cost_multiplier": 4.0,
                    "quality_score": 0.85,
                    "specialization": "analysis",
                },
            ],
        }

    def _initialize_agent_preferences(self) -> Dict[AgentRole, Dict[str, Any]]:
        """Initialize agent-specific model preferences"""
        return {
            AgentRole.ANALYST: {
                "preferred_tiers": [ModelTier.SPECIALIZED, ModelTier.STANDARD, ModelTier.PREMIUM],
                "quality_threshold": 0.85,
                "cost_sensitivity": 0.6,
                "specializations": ["research", "analysis"],
                "optimal_models": ["deepseek-coder", "sonar-large", "gpt-4o"],
            },
            AgentRole.STRATEGIST: {
                "preferred_tiers": [ModelTier.PREMIUM, ModelTier.STANDARD],
                "quality_threshold": 0.90,
                "cost_sensitivity": 0.3,
                "specializations": ["planning", "synthesis"],
                "optimal_models": ["gpt-4", "claude-3-opus", "gemini-2.0-pro"],
            },
            AgentRole.VALIDATOR: {
                "preferred_tiers": [ModelTier.PREMIUM, ModelTier.SPECIALIZED],
                "quality_threshold": 0.92,
                "cost_sensitivity": 0.2,
                "specializations": ["validation", "quality_check"],
                "optimal_models": ["claude-3-opus", "gpt-4", "deepseek-coder"],
            },
        }

    async def route_request(
        self, context: RoutingContext, strategy: RoutingStrategy = RoutingStrategy.BALANCED
    ) -> EnhancedRoutingDecision:
        """
        Route LLM request with intelligent decision making

        Args:
            context: Routing context with requirements and constraints
            strategy: Routing strategy to apply

        Returns:
            Enhanced routing decision with fallbacks and reasoning
        """
        start_time = datetime.now()

        try:
            # Apply routing strategy
            if strategy == RoutingStrategy.COST_OPTIMIZED:
                decision = await self._route_cost_optimized(context)
            elif strategy == RoutingStrategy.PERFORMANCE_OPTIMIZED:
                decision = await self._route_performance_optimized(context)
            elif strategy == RoutingStrategy.AGENT_SPECIALIZED:
                decision = await self._route_agent_specialized(context)
            elif strategy == RoutingStrategy.ADAPTIVE:
                decision = await self._route_adaptive(context)
            else:  # BALANCED
                decision = await self._route_balanced(context)

            # Record routing decision
            await self._record_routing_decision(context, decision, start_time)

            return decision

        except Exception as e:
            logger.error(f"Routing failed: {e}")
            # Fallback to basic routing
            basic_routing = self.portkey.route_request(
                task_type=context.task_type,
                estimated_tokens=context.workload_characteristics.get("estimated_tokens", 1000),
                max_cost_usd=context.swarm_budget,
            )

            return EnhancedRoutingDecision(
                primary_choice=basic_routing,
                fallback_choices=[],
                reasoning="Fallback to basic routing due to error",
                confidence=0.5,
                expected_performance=ModelPerformanceMetrics("unknown", "unknown"),
                cost_estimation={"primary": basic_routing.estimated_cost},
                risk_assessment={"failure_risk": 0.3},
                routing_strategy_used=RoutingStrategy.BALANCED,
            )

    async def _route_cost_optimized(self, context: RoutingContext) -> EnhancedRoutingDecision:
        """Route with cost optimization priority"""

        # Get cheapest models that meet minimum quality threshold
        candidate_models = []
        min_quality = max(0.7, context.quality_requirement - 0.1)  # Allow slightly lower quality

        for tier in [ModelTier.FAST, ModelTier.STANDARD, ModelTier.SPECIALIZED]:
            for model_config in self.model_tiers[tier]:
                if model_config["quality_score"] >= min_quality:
                    candidate_models.append((model_config, tier))

        # Sort by cost (ascending)
        candidate_models.sort(key=lambda x: x[0]["cost_multiplier"])

        if not candidate_models:
            # Fallback to any available model
            candidate_models = [(self.model_tiers[ModelTier.FAST][0], ModelTier.FAST)]

        # Select primary and fallbacks
        primary_model, primary_tier = candidate_models[0]
        primary_routing = await self._create_routing_decision(primary_model, context)

        fallbacks = []
        for model_config, tier in candidate_models[1:3]:  # Up to 2 fallbacks
            fallback_routing = await self._create_routing_decision(model_config, context)
            fallbacks.append(fallback_routing)

        return EnhancedRoutingDecision(
            primary_choice=primary_routing,
            fallback_choices=fallbacks,
            reasoning=f"Cost-optimized routing selected {primary_model['model']} for lowest cost while meeting quality threshold {min_quality}",
            confidence=0.8,
            expected_performance=await self._get_model_performance(primary_model["model"]),
            cost_estimation={
                "primary": primary_routing.estimated_cost,
                "fallbacks": [fb.estimated_cost for fb in fallbacks],
            },
            risk_assessment={"cost_overrun_risk": 0.1, "quality_risk": 0.3},
            routing_strategy_used=RoutingStrategy.COST_OPTIMIZED,
        )

    async def _route_performance_optimized(
        self, context: RoutingContext
    ) -> EnhancedRoutingDecision:
        """Route with performance/quality optimization priority"""

        # Get highest quality models within budget
        candidate_models = []
        budget_per_request = context.swarm_budget / 3  # Conservative estimate

        for tier in [ModelTier.PREMIUM, ModelTier.STANDARD, ModelTier.SPECIALIZED]:
            for model_config in self.model_tiers[tier]:
                estimated_cost = model_config["cost_multiplier"] * 0.01  # Base cost estimate
                if estimated_cost <= budget_per_request:
                    candidate_models.append((model_config, tier))

        # Sort by quality score (descending)
        candidate_models.sort(key=lambda x: x[0]["quality_score"], reverse=True)

        if not candidate_models:
            # Use premium models anyway, but flag budget risk
            candidate_models = [(self.model_tiers[ModelTier.PREMIUM][0], ModelTier.PREMIUM)]

        primary_model, primary_tier = candidate_models[0]
        primary_routing = await self._create_routing_decision(primary_model, context)

        fallbacks = []
        for model_config, tier in candidate_models[1:3]:
            fallback_routing = await self._create_routing_decision(model_config, context)
            fallbacks.append(fallback_routing)

        return EnhancedRoutingDecision(
            primary_choice=primary_routing,
            fallback_choices=fallbacks,
            reasoning=f"Performance-optimized routing selected {primary_model['model']} for highest quality score {primary_model['quality_score']}",
            confidence=0.9,
            expected_performance=await self._get_model_performance(primary_model["model"]),
            cost_estimation={
                "primary": primary_routing.estimated_cost,
                "total_budget_usage": primary_routing.estimated_cost / context.swarm_budget,
            },
            risk_assessment={"cost_overrun_risk": 0.4, "quality_risk": 0.1},
            routing_strategy_used=RoutingStrategy.PERFORMANCE_OPTIMIZED,
        )

    async def _route_agent_specialized(self, context: RoutingContext) -> EnhancedRoutingDecision:
        """Route based on agent role specialization"""

        agent_prefs = self.agent_model_preferences.get(context.agent_role, {})
        preferred_tiers = agent_prefs.get("preferred_tiers", [ModelTier.STANDARD])
        quality_threshold = agent_prefs.get("quality_threshold", 0.8)
        optimal_models = agent_prefs.get("optimal_models", [])

        # First, try optimal models for this agent
        candidate_models = []
        for tier in preferred_tiers:
            for model_config in self.model_tiers[tier]:
                if (
                    model_config["model"] in optimal_models
                    or model_config["quality_score"] >= quality_threshold
                ):
                    candidate_models.append((model_config, tier))

        # Sort by agent-specific performance if available
        def agent_score(model_tuple):
            model_config, tier = model_tuple
            model_name = model_config["model"]

            # Get agent-specific performance
            if model_name in self.model_metrics:
                metrics = self.model_metrics[model_name]
                agent_perf = metrics.agent_performance.get(context.agent_role, 0.5)
                return agent_perf * model_config["quality_score"]
            else:
                return model_config["quality_score"]

        candidate_models.sort(key=agent_score, reverse=True)

        if not candidate_models:
            # Fallback to any model meeting quality threshold
            for tier in ModelTier:
                for model_config in self.model_tiers[tier]:
                    if model_config["quality_score"] >= quality_threshold:
                        candidate_models.append((model_config, tier))
                        break

        primary_model, primary_tier = candidate_models[0]
        primary_routing = await self._create_routing_decision(primary_model, context)

        fallbacks = []
        for model_config, tier in candidate_models[1:2]:  # 1 fallback
            fallback_routing = await self._create_routing_decision(model_config, context)
            fallbacks.append(fallback_routing)

        return EnhancedRoutingDecision(
            primary_choice=primary_routing,
            fallback_choices=fallbacks,
            reasoning=f"Agent-specialized routing for {context.agent_role.value} selected {primary_model['model']} based on role preferences and historical performance",
            confidence=0.85,
            expected_performance=await self._get_model_performance(primary_model["model"]),
            cost_estimation={"primary": primary_routing.estimated_cost},
            risk_assessment={"specialization_mismatch_risk": 0.2},
            routing_strategy_used=RoutingStrategy.AGENT_SPECIALIZED,
        )

    async def _route_adaptive(self, context: RoutingContext) -> EnhancedRoutingDecision:
        """Route with adaptive learning from historical performance"""

        # Get models with recent good performance for this agent/task combination
        recent_performance = await self._get_recent_performance(context)

        # Combine historical performance with base model capabilities
        scored_models = []
        for tier in ModelTier:
            for model_config in self.model_tiers[tier]:
                model_name = model_config["model"]

                # Base score from model quality
                base_score = model_config["quality_score"]

                # Adaptive score from recent performance
                adaptive_score = recent_performance.get(model_name, 0.5)

                # Cost penalty
                cost_penalty = model_config["cost_multiplier"] / 10.0

                # Combined score (weighted)
                combined_score = 0.4 * base_score + 0.5 * adaptive_score - 0.1 * cost_penalty

                scored_models.append((model_config, tier, combined_score))

        # Sort by combined score
        scored_models.sort(key=lambda x: x[2], reverse=True)

        primary_model, primary_tier, primary_score = scored_models[0]
        primary_routing = await self._create_routing_decision(primary_model, context)

        fallbacks = []
        for model_config, tier, score in scored_models[1:3]:
            fallback_routing = await self._create_routing_decision(model_config, context)
            fallbacks.append(fallback_routing)

        return EnhancedRoutingDecision(
            primary_choice=primary_routing,
            fallback_choices=fallbacks,
            reasoning=f"Adaptive routing selected {primary_model['model']} with combined score {primary_score:.2f} based on historical performance and current context",
            confidence=0.88,
            expected_performance=await self._get_model_performance(primary_model["model"]),
            cost_estimation={"primary": primary_routing.estimated_cost},
            risk_assessment={"adaptation_uncertainty": 0.15},
            routing_strategy_used=RoutingStrategy.ADAPTIVE,
        )

    async def _route_balanced(self, context: RoutingContext) -> EnhancedRoutingDecision:
        """Route with balanced cost/performance optimization"""

        # Score models based on balanced criteria
        scored_models = []
        target_budget_per_request = context.swarm_budget / 5  # Conservative estimate

        for tier in ModelTier:
            for model_config in self.model_tiers[tier]:
                quality_score = model_config["quality_score"]
                cost_score = 1.0 / model_config["cost_multiplier"]  # Inverse of cost
                estimated_cost = model_config["cost_multiplier"] * 0.01

                # Budget penalty if over target
                budget_penalty = max(
                    0, (estimated_cost - target_budget_per_request) / target_budget_per_request
                )

                # Balanced score (equal weight to quality and cost efficiency)
                balanced_score = 0.6 * quality_score + 0.4 * cost_score - 0.2 * budget_penalty

                scored_models.append((model_config, tier, balanced_score))

        # Sort by balanced score
        scored_models.sort(key=lambda x: x[2], reverse=True)

        primary_model, primary_tier, primary_score = scored_models[0]
        primary_routing = await self._create_routing_decision(primary_model, context)

        fallbacks = []
        for model_config, tier, score in scored_models[1:3]:
            fallback_routing = await self._create_routing_decision(model_config, context)
            fallbacks.append(fallback_routing)

        return EnhancedRoutingDecision(
            primary_choice=primary_routing,
            fallback_choices=fallbacks,
            reasoning=f"Balanced routing selected {primary_model['model']} with score {primary_score:.2f} optimizing for both cost and performance",
            confidence=0.82,
            expected_performance=await self._get_model_performance(primary_model["model"]),
            cost_estimation={
                "primary": primary_routing.estimated_cost,
                "budget_utilization": primary_routing.estimated_cost / context.swarm_budget,
            },
            risk_assessment={"balanced_tradeoff_risk": 0.25},
            routing_strategy_used=RoutingStrategy.BALANCED,
        )

    async def _create_routing_decision(
        self, model_config: Dict[str, Any], context: RoutingContext
    ) -> RoutingDecision:
        """Create routing decision for a specific model"""

        # Use portkey manager to get actual routing decision
        basic_routing = self.portkey.route_request(
            task_type=context.task_type,
            estimated_tokens=context.workload_characteristics.get("estimated_tokens", 1000),
            max_cost_usd=context.swarm_budget,
            prefer_provider=model_config.get("provider"),
        )

        return basic_routing

    async def _get_model_performance(self, model_name: str) -> ModelPerformanceMetrics:
        """Get performance metrics for a model"""
        if model_name in self.model_metrics:
            return self.model_metrics[model_name]
        else:
            # Create default metrics for new model
            return ModelPerformanceMetrics(
                model_name=model_name,
                provider="unknown",
                success_rate=0.8,
                avg_response_time_ms=2000.0,
                avg_cost_per_request=0.01,
                avg_confidence_score=0.75,
            )

    async def _get_recent_performance(self, context: RoutingContext) -> Dict[str, float]:
        """Get recent performance data for models with this agent/task combination"""

        # Filter routing history for relevant entries
        recent_cutoff = datetime.now() - self.performance_window
        relevant_history = [
            entry
            for entry in self.routing_history
            if (
                entry["timestamp"] > recent_cutoff
                and entry["agent_role"] == context.agent_role
                and entry["task_type"] == context.task_type
            )
        ]

        # Calculate performance scores
        performance = {}
        for entry in relevant_history:
            model_name = entry["model_used"]
            success = entry.get("success", True)
            response_time = entry.get("response_time_ms", 2000)
            confidence = entry.get("confidence", 0.7)

            # Calculate performance score (higher is better)
            time_score = max(0, 1.0 - (response_time - 1000) / 5000)  # Normalize response time
            perf_score = 0.5 * (1.0 if success else 0.0) + 0.3 * confidence + 0.2 * time_score

            if model_name not in performance:
                performance[model_name] = []
            performance[model_name].append(perf_score)

        # Average performance scores
        avg_performance = {}
        for model_name, scores in performance.items():
            avg_performance[model_name] = sum(scores) / len(scores)

        return avg_performance

    async def _record_routing_decision(
        self, context: RoutingContext, decision: EnhancedRoutingDecision, start_time: datetime
    ) -> None:
        """Record routing decision for learning"""

        routing_time = (datetime.now() - start_time).total_seconds() * 1000

        record = {
            "timestamp": datetime.now(),
            "agent_role": context.agent_role,
            "task_type": context.task_type,
            "message_type": context.message_type,
            "routing_strategy": decision.routing_strategy_used,
            "model_selected": decision.primary_choice.model,
            "provider_selected": decision.primary_choice.provider,
            "estimated_cost": decision.primary_choice.estimated_cost,
            "reasoning": decision.reasoning,
            "confidence": decision.confidence,
            "routing_time_ms": routing_time,
            "budget_available": context.swarm_budget,
            "quality_requirement": context.quality_requirement,
            "retry_count": context.retry_count,
        }

        self.routing_history.append(record)

        # Keep only recent history (last 1000 entries)
        if len(self.routing_history) > 1000:
            self.routing_history = self.routing_history[-1000:]

    async def record_execution_result(
        self,
        routing_id: str,
        success: bool,
        response_time_ms: float,
        confidence: float,
        actual_cost: float,
        error_message: Optional[str] = None,
    ) -> None:
        """Record the result of an execution for learning"""

        # Find the corresponding routing record
        for record in reversed(self.routing_history):
            if record.get("routing_id") == routing_id:
                record.update(
                    {
                        "success": success,
                        "actual_response_time_ms": response_time_ms,
                        "actual_confidence": confidence,
                        "actual_cost": actual_cost,
                        "error_message": error_message,
                        "completed_at": datetime.now(),
                    }
                )
                break

        # Update model performance metrics
        await self._update_model_metrics(
            routing_id, success, response_time_ms, confidence, actual_cost
        )

    async def _update_model_metrics(
        self,
        routing_id: str,
        success: bool,
        response_time_ms: float,
        confidence: float,
        actual_cost: float,
    ) -> None:
        """Update model performance metrics for learning"""

        # Find the routing record
        routing_record = None
        for record in reversed(self.routing_history):
            if record.get("routing_id") == routing_id:
                routing_record = record
                break

        if not routing_record:
            return

        model_name = routing_record["model_selected"]
        agent_role = routing_record["agent_role"]
        task_type = routing_record["task_type"]

        # Get or create metrics
        if model_name not in self.model_metrics:
            self.model_metrics[model_name] = ModelPerformanceMetrics(
                model_name=model_name, provider=routing_record["provider_selected"]
            )

        metrics = self.model_metrics[model_name]

        # Update metrics with exponential moving average
        alpha = self.learning_rate

        metrics.success_rate = (
            alpha * (1.0 if success else 0.0) + (1 - alpha) * metrics.success_rate
        )
        metrics.avg_response_time_ms = (
            alpha * response_time_ms + (1 - alpha) * metrics.avg_response_time_ms
        )
        metrics.avg_cost_per_request = (
            alpha * actual_cost + (1 - alpha) * metrics.avg_cost_per_request
        )
        metrics.avg_confidence_score = (
            alpha * confidence + (1 - alpha) * metrics.avg_confidence_score
        )
        metrics.total_requests += 1
        metrics.last_updated = datetime.now()

        # Update agent-specific performance
        if agent_role not in metrics.agent_performance:
            metrics.agent_performance[agent_role] = 0.7

        agent_perf_score = 0.5 * (1.0 if success else 0.0) + 0.5 * confidence
        metrics.agent_performance[agent_role] = (
            alpha * agent_perf_score + (1 - alpha) * metrics.agent_performance[agent_role]
        )

        # Update task-specific performance
        if task_type not in metrics.task_performance:
            metrics.task_performance[task_type] = 0.7

        task_perf_score = 0.5 * (1.0 if success else 0.0) + 0.5 * confidence
        metrics.task_performance[task_type] = (
            alpha * task_perf_score + (1 - alpha) * metrics.task_performance[task_type]
        )

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""

        report = {
            "total_models_tracked": len(self.model_metrics),
            "total_routing_decisions": len(self.routing_history),
            "model_performance": {},
            "routing_strategy_performance": {},
            "agent_model_preferences": {},
            "cost_analysis": {},
            "recent_trends": {},
        }

        # Model performance summary
        for model_name, metrics in self.model_metrics.items():
            report["model_performance"][model_name] = {
                "success_rate": metrics.success_rate,
                "avg_response_time_ms": metrics.avg_response_time_ms,
                "avg_cost": metrics.avg_cost_per_request,
                "avg_confidence": metrics.avg_confidence_score,
                "total_requests": metrics.total_requests,
                "agent_performance": dict(metrics.agent_performance),
                "task_performance": dict(metrics.task_performance),
            }

        # Routing strategy performance
        recent_history = [r for r in self.routing_history if r.get("completed_at")]
        strategy_performance = {}
        for record in recent_history:
            strategy = record["routing_strategy"].value
            if strategy not in strategy_performance:
                strategy_performance[strategy] = {"count": 0, "success_rate": 0.0, "avg_cost": 0.0}

            strategy_performance[strategy]["count"] += 1
            success = record.get("success", False)
            cost = record.get("actual_cost", 0)

            # Update running averages
            count = strategy_performance[strategy]["count"]
            strategy_performance[strategy]["success_rate"] = (
                strategy_performance[strategy]["success_rate"] * (count - 1)
                + (1.0 if success else 0.0)
            ) / count
            strategy_performance[strategy]["avg_cost"] = (
                strategy_performance[strategy]["avg_cost"] * (count - 1) + cost
            ) / count

        report["routing_strategy_performance"] = strategy_performance

        return report


# Global intelligent router instance
_intelligent_router = None


def get_intelligent_router() -> IntelligentRouter:
    """Get global intelligent router instance"""
    global _intelligent_router
    if _intelligent_router is None:
        _intelligent_router = IntelligentRouter()
    return _intelligent_router
