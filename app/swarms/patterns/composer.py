"""
Swarm Composer for combining multiple patterns into complex behaviors.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from .base import SwarmPattern
from .adaptive_parameters import AdaptiveParametersPattern
from .adversarial_debate import AdversarialDebatePattern
from .consensus import ConsensusPattern
from .dynamic_roles import DynamicRolesPattern
from .knowledge_transfer import KnowledgeTransferPattern
from .quality_gates import QualityGatesPattern
from .safety_boundaries import SafetyBoundariesPattern
from .strategy_archive import StrategyArchivePattern

logger = logging.getLogger(__name__)


@dataclass
class ComposerConfig:
    """Configuration for pattern composition."""
    patterns: list[str]
    execution_mode: str = "sequential"  # sequential, parallel, conditional
    fail_fast: bool = False
    merge_results: bool = True


class SwarmComposer:
    """
    Composes multiple swarm patterns into complex coordination strategies.
    """

    def __init__(self, config: ComposerConfig):
        self.config = config
        self.patterns: dict[str, SwarmPattern] = {}
        self._initialize_patterns()

    def _initialize_patterns(self):
        """Initialize requested patterns."""
        pattern_classes = {
            "adversarial_debate": AdversarialDebatePattern,
            "quality_gates": QualityGatesPattern,
            "strategy_archive": StrategyArchivePattern,
            "safety_boundaries": SafetyBoundariesPattern,
            "dynamic_roles": DynamicRolesPattern,
            "consensus": ConsensusPattern,
            "adaptive_parameters": AdaptiveParametersPattern,
            "knowledge_transfer": KnowledgeTransferPattern
        }

        for pattern_name in self.config.patterns:
            if pattern_name in pattern_classes:
                self.patterns[pattern_name] = pattern_classes[pattern_name]()
                logger.info(f"Initialized pattern: {pattern_name}")

    async def execute(self, context: dict[str, Any], agents: list[Any]) -> dict[str, Any]:
        """
        Execute composed patterns.
        
        Args:
            context: Execution context
            agents: Available agents
            
        Returns:
            Combined results from all patterns
        """
        if self.config.execution_mode == "parallel":
            return await self._execute_parallel(context, agents)
        elif self.config.execution_mode == "conditional":
            return await self._execute_conditional(context, agents)
        else:  # sequential
            return await self._execute_sequential(context, agents)

    async def _execute_sequential(self, context: dict[str, Any], agents: list[Any]) -> dict[str, Any]:
        """Execute patterns sequentially."""
        results = {}
        current_context = context.copy()

        for pattern_name, pattern in self.patterns.items():
            try:
                result = await pattern.execute(current_context, agents)
                results[pattern_name] = result

                if result.success and self.config.merge_results:
                    # Merge successful results into context for next pattern
                    if result.data:
                        current_context["prior_results"] = current_context.get("prior_results", {})
                        current_context["prior_results"][pattern_name] = result.data

                elif not result.success and self.config.fail_fast:
                    logger.warning(f"Pattern {pattern_name} failed, stopping execution")
                    break

            except Exception as e:
                logger.error(f"Pattern {pattern_name} raised exception: {e}")
                if self.config.fail_fast:
                    raise

        return results

    async def _execute_parallel(self, context: dict[str, Any], agents: list[Any]) -> dict[str, Any]:
        """Execute patterns in parallel."""
        tasks = []

        for pattern_name, pattern in self.patterns.items():
            task = asyncio.create_task(pattern.execute(context.copy(), agents))
            tasks.append((pattern_name, task))

        results = {}
        for pattern_name, task in tasks:
            try:
                result = await task
                results[pattern_name] = result
            except Exception as e:
                logger.error(f"Pattern {pattern_name} failed: {e}")
                if self.config.fail_fast:
                    # Cancel remaining tasks
                    for _, t in tasks:
                        if not t.done():
                            t.cancel()
                    raise

        return results

    async def _execute_conditional(self, context: dict[str, Any], agents: list[Any]) -> dict[str, Any]:
        """Execute patterns based on conditions."""
        results = {}

        # Example conditional logic
        if "high_risk" in context:
            if "safety_boundaries" in self.patterns:
                result = await self.patterns["safety_boundaries"].execute(context, agents)
                results["safety_boundaries"] = result

        if "multiple_solutions" in context:
            if "adversarial_debate" in self.patterns:
                result = await self.patterns["adversarial_debate"].execute(context, agents)
                results["adversarial_debate"] = result

        # Always run quality gates if available
        if "quality_gates" in self.patterns:
            result = await self.patterns["quality_gates"].execute(context, agents)
            results["quality_gates"] = result

        return results

    async def cleanup(self):
        """Cleanup all patterns."""
        for pattern in self.patterns.values():
            await pattern.cleanup()
