"""Micro-Swarm Configurations: Lightweight, specialized swarm configurations for testing and optimization.

This module defines small, focused swarm configurations that can be used for
A/B testing, quick analysis, and cost-effective processing.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SwarmPurpose(Enum):
    """Purpose categories for micro-swarms."""

    QUICK_ANALYSIS = "quick_analysis"
    DEEP_ANALYSIS = "deep_analysis"
    CODE_REVIEW = "code_review"
    SECURITY_AUDIT = "security_audit"
    PERFORMANCE_TEST = "performance_test"
    COST_OPTIMIZATION = "cost_optimization"
    COMPREHENSIVE_AUDIT = "comprehensive_audit"


@dataclass
class MicroSwarmConfig:
    """Configuration for a micro-swarm."""

    name: str
    purpose: SwarmPurpose
    agents: list[str]  # Model IDs
    pattern: str  # Execution pattern
    max_time: float  # Maximum execution time in seconds
    cost_limit: float  # Maximum cost in dollars
    use_case: str  # Description of when to use

    # Optional parameters
    consensus_required: bool = False
    min_consensus: float = 0.8
    parallel: bool = True
    gates: list[str] = None
    escalation_enabled: bool = True
    cache_results: bool = True

    def __post_init__(self):
        if self.gates is None:
            self.gates = []

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "purpose": self.purpose.value,
            "agents": self.agents,
            "pattern": self.pattern,
            "max_time": self.max_time,
            "cost_limit": self.cost_limit,
            "use_case": self.use_case,
            "consensus_required": self.consensus_required,
            "min_consensus": self.min_consensus,
            "parallel": self.parallel,
            "gates": self.gates,
            "escalation_enabled": self.escalation_enabled,
            "cache_results": self.cache_results,
        }


class MicroSwarmLibrary:
    """Library of pre-configured micro-swarms."""

    # Confidence-based escalation tiers
    ESCALATION_TIERS = {
        "tier1": ["gpt-4o-mini", "claude-3-haiku-20240307"],  # ~$0.0002/1K tokens
        "tier2": ["gpt-4o", "claude-3-5-sonnet-20241022"],  # ~$0.003/1K tokens
        "tier3": ["gpt-4", "claude-3-opus-20240229"],  # ~$0.01/1K tokens
    }

    @staticmethod
    def get_all_configs() -> dict[str, MicroSwarmConfig]:
        """Get all micro-swarm configurations."""
        return {
            "quick_analysis": MicroSwarmConfig(
                name="Quick Analysis Swarm",
                purpose=SwarmPurpose.QUICK_ANALYSIS,
                agents=["gpt-4o-mini", "claude-3-haiku-20240307"],
                pattern="parallel_then_merge",
                max_time=5.0,
                cost_limit=0.01,
                use_case="Simple queries and quick analyses",
                consensus_required=False,
                parallel=True,
            ),
            "deep_analysis": MicroSwarmConfig(
                name="Deep Analysis Swarm",
                purpose=SwarmPurpose.DEEP_ANALYSIS,
                agents=["gpt-4", "claude-3-opus-20240229", "deepseek/deepseek-chat"],
                pattern="debate",
                max_time=60.0,
                cost_limit=0.50,
                use_case="Complex problems requiring deep reasoning",
                consensus_required=True,
                min_consensus=0.8,
                parallel=False,
            ),
            "code_review_express": MicroSwarmConfig(
                name="Code Review Express",
                purpose=SwarmPurpose.CODE_REVIEW,
                agents=["deepseek/deepseek-coder", "meta-llama/llama-3.1-70b-instruct"],
                pattern="parallel_review",
                max_time=15.0,
                cost_limit=0.05,
                use_case="Quick code review and suggestions",
                parallel=True,
                gates=["syntax", "style"],
            ),
            "security_scan": MicroSwarmConfig(
                name="Security Scanner",
                purpose=SwarmPurpose.SECURITY_AUDIT,
                agents=["gpt-4", "anthropic/claude-3-opus-20240229"],
                pattern="sequential_audit",
                max_time=30.0,
                cost_limit=0.20,
                use_case="Security vulnerability scanning",
                consensus_required=True,
                min_consensus=0.9,
                gates=["security", "vulnerabilities", "compliance"],
            ),
            "performance_optimizer": MicroSwarmConfig(
                name="Performance Optimizer",
                purpose=SwarmPurpose.PERFORMANCE_TEST,
                agents=["deepseek/deepseek-chat", "gpt-4o"],
                pattern="analyze_and_optimize",
                max_time=20.0,
                cost_limit=0.10,
                use_case="Performance analysis and optimization",
                parallel=False,
                gates=["performance", "scalability"],
            ),
            "cost_saver": MicroSwarmConfig(
                name="Cost Optimization Swarm",
                purpose=SwarmPurpose.COST_OPTIMIZATION,
                agents=["gpt-4o-mini"],
                pattern="single_pass",
                max_time=3.0,
                cost_limit=0.005,
                use_case="Ultra low-cost processing for simple tasks",
                escalation_enabled=True,
                cache_results=True,
            ),
            "comprehensive_audit": MicroSwarmConfig(
                name="Comprehensive Audit Swarm",
                purpose=SwarmPurpose.COMPREHENSIVE_AUDIT,
                agents=[
                    "gpt-4",
                    "claude-3-opus-20240229",
                    "deepseek/deepseek-coder",
                    "meta-llama/llama-3.1-70b-instruct",
                ],
                pattern="hierarchical",
                max_time=120.0,
                cost_limit=1.00,
                use_case="Production deployments and critical reviews",
                consensus_required=True,
                min_consensus=0.85,
                gates=["security", "performance", "quality", "compliance"],
                parallel=False,
            ),
        }

    @staticmethod
    def get_config(name: str) -> Optional[MicroSwarmConfig]:
        """Get a specific micro-swarm configuration."""
        configs = MicroSwarmLibrary.get_all_configs()
        return configs.get(name)

    @staticmethod
    def get_configs_by_purpose(purpose: SwarmPurpose) -> list[MicroSwarmConfig]:
        """Get all configs for a specific purpose."""
        configs = MicroSwarmLibrary.get_all_configs()
        return [cfg for cfg in configs.values() if cfg.purpose == purpose]

    @staticmethod
    def get_configs_under_cost(max_cost: float) -> list[MicroSwarmConfig]:
        """Get all configs under a certain cost limit."""
        configs = MicroSwarmLibrary.get_all_configs()
        return [cfg for cfg in configs.values() if cfg.cost_limit <= max_cost]


class ConfidenceBasedRouter:
    """Routes requests to appropriate micro-swarms based on confidence thresholds."""

    def __init__(self):
        self.tier1_threshold = 0.7
        self.tier2_threshold = 0.8
        self.cost_tracker = {}

        logger.info("ConfidenceBasedRouter initialized")

    async def route_request(
        self, request: str, initial_tier: str = "tier1"
    ) -> dict[str, Any]:
        """Route request through escalation tiers based on confidence."""
        tiers = MicroSwarmLibrary.ESCALATION_TIERS
        current_tier = initial_tier
        total_cost = 0.0
        attempts = []

        # Start with lowest tier
        result = await self._execute_tier(request, tiers[current_tier])
        attempts.append(
            {
                "tier": current_tier,
                "confidence": result.get("confidence", 0),
                "cost": result.get("cost", 0),
            }
        )
        total_cost += result.get("cost", 0)

        # Escalate if confidence is low
        if (
            result.get("confidence", 0) < self.tier1_threshold
            and current_tier == "tier1"
        ):
            logger.info(
                f"Escalating to tier2 (confidence: {result.get('confidence', 0)})"
            )
            current_tier = "tier2"
            result = await self._execute_tier(request, tiers[current_tier])
            attempts.append(
                {
                    "tier": current_tier,
                    "confidence": result.get("confidence", 0),
                    "cost": result.get("cost", 0),
                }
            )
            total_cost += result.get("cost", 0)

        if (
            result.get("confidence", 0) < self.tier2_threshold
            and current_tier == "tier2"
        ):
            logger.info(
                f"Escalating to tier3 (confidence: {result.get('confidence', 0)})"
            )
            current_tier = "tier3"
            result = await self._execute_tier(request, tiers[current_tier])
            attempts.append(
                {
                    "tier": current_tier,
                    "confidence": result.get("confidence", 0),
                    "cost": result.get("cost", 0),
                }
            )
            total_cost += result.get("cost", 0)

        return {
            "final_result": result,
            "final_tier": current_tier,
            "total_cost": total_cost,
            "attempts": attempts,
            "escalated": len(attempts) > 1,
        }

    async def _execute_tier(self, request: str, models: list[str]) -> dict[str, Any]:
        """Execute request with specified model tier."""
        # In production, this would actually execute with the models
        # For now, return mock result
        import random

        # Simulate varying confidence based on tier
        if "gpt-4" in models[0] or "opus" in models[0]:
            confidence = 0.85 + random.random() * 0.15  # 0.85-1.0
            cost = 0.05
        elif "gpt-4o" in models[0] or "sonnet" in models[0]:
            confidence = 0.70 + random.random() * 0.20  # 0.70-0.90
            cost = 0.02
        else:
            confidence = 0.50 + random.random() * 0.30  # 0.50-0.80
            cost = 0.005

        return {
            "response": f"Response from {models[0]}",
            "confidence": confidence,
            "cost": cost,
            "models_used": models,
        }


class MicroSwarmExecutor:
    """Executes micro-swarm configurations."""

    def __init__(self):
        self.library = MicroSwarmLibrary()
        self.router = ConfidenceBasedRouter()
        self.execution_history = []

        logger.info("MicroSwarmExecutor initialized")

    async def execute(self, config_name: str, request: str) -> dict[str, Any]:
        """Execute a micro-swarm configuration."""
        config = self.library.get_config(config_name)

        if not config:
            raise ValueError(f"Unknown micro-swarm configuration: {config_name}")

        logger.info(f"Executing micro-swarm: {config.name}")

        # Check if escalation is enabled
        if config.escalation_enabled:
            result = await self.router.route_request(request)
        else:
            # Execute with fixed configuration
            result = await self._execute_fixed(config, request)

        # Store execution history
        self.execution_history.append(
            {
                "config": config_name,
                "request": request[:100],  # Truncated
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        return result

    async def _execute_fixed(
        self, config: MicroSwarmConfig, request: str
    ) -> dict[str, Any]:
        """Execute with fixed swarm configuration."""
        # In production, this would execute with actual agents
        # For now, return mock result
        import asyncio
        import random

        # Simulate execution time
        execution_time = random.uniform(1, config.max_time)
        await asyncio.sleep(min(execution_time, 2))  # Cap at 2s for demo

        # Simulate cost
        cost = random.uniform(config.cost_limit * 0.3, config.cost_limit * 0.8)

        return {
            "config": config.name,
            "response": f"Executed with {len(config.agents)} agents",
            "agents_used": config.agents,
            "execution_time": execution_time,
            "cost": cost,
            "consensus_achieved": config.consensus_required and random.random() > 0.3,
            "gates_passed": config.gates,
        }

    async def compare_configs(
        self, config_names: list[str], request: str
    ) -> dict[str, Any]:
        """Compare multiple micro-swarm configurations (A/B testing)."""
        results = {}

        for config_name in config_names:
            try:
                result = await self.execute(config_name, request)
                results[config_name] = result
            except Exception as e:
                logger.error(f"Error executing {config_name}: {e}")
                results[config_name] = {"error": str(e)}

        # Determine winner based on cost-efficiency
        winner = None
        best_score = float("inf")

        for name, result in results.items():
            if "error" not in result:
                # Score = cost * execution_time (lower is better)
                score = result.get("cost", float("inf")) * result.get(
                    "execution_time", float("inf")
                )
                if score < best_score:
                    best_score = score
                    winner = name

        return {
            "results": results,
            "winner": winner,
            "comparison_metric": "cost_efficiency",
            "scores": {
                name: result.get("cost", 0) * result.get("execution_time", 0)
                for name, result in results.items()
                if "error" not in result
            },
        }


# Import for timestamp
from datetime import datetime

# Global executor instance
_micro_swarm_executor = None


def get_micro_swarm_executor() -> MicroSwarmExecutor:
    """Get or create the global micro-swarm executor."""
    global _micro_swarm_executor
    if _micro_swarm_executor is None:
        _micro_swarm_executor = MicroSwarmExecutor()
    return _micro_swarm_executor
