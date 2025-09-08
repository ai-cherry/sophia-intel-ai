#!/usr/bin/env python3
"""
Learning-Enhanced Execution Modes for Sophia Intel AI Swarms
Specialized learning versions of each execution mode with knowledge transfer

Features:
- Learning-enhanced versions of all SwarmExecutionMode types
- Cross-modal learning transfer mechanisms
- Real-time knowledge optimization during execution
- Memory-integrated learning persistence
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

import numpy as np
from opentelemetry import trace
from opentelemetry.trace import SpanKind

from app.core.ai_logger import logger
from app.swarms.core.swarm_base import SwarmBase, SwarmExecutionMode
from app.swarms.learning.adaptive_learning_system import (
    AdaptiveLearningSystem,
    KnowledgeType,
    LearnedKnowledge,
)

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


# =============================================================================
# LEARNING-ENHANCED EXECUTION STRATEGIES
# =============================================================================


class LearningEnhancedExecutionStrategy(ABC):
    """Abstract base class for learning-enhanced execution strategies"""

    def __init__(self, learning_system: AdaptiveLearningSystem):
        self.learning_system = learning_system
        self.execution_history: list[dict[str, Any]] = []
        self.mode_specific_knowledge: dict[str, LearnedKnowledge] = {}

    @abstractmethod
    async def execute_with_learning(
        self, swarm: SwarmBase, problem: dict[str, Any], context: dict[str, Any]
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Execute swarm with learning enhancement"""
        pass

    async def capture_execution_experience(
        self,
        swarm: SwarmBase,
        problem: dict[str, Any],
        result: list[dict[str, Any]],
        execution_metadata: dict[str, Any],
    ) -> str:
        """Capture learning experience for this execution mode"""
        return await self.learning_system.capture_experience(
            swarm_id=swarm.config.swarm_id,
            execution_mode=swarm.config.execution_mode,
            problem_context=problem,
            execution_context=execution_metadata,
            agent_states={f"agent_{i}": {} for i in range(len(swarm.agents))},
            solution={
                "success": len([r for r in result if r.get("success", False)]) > 0,
                "quality_score": (
                    np.mean([r.get("quality_score", 0.0) for r in result])
                    if result
                    else 0.0
                ),
                "agent_results": result,
            },
            metrics=swarm.metrics,
        )

    async def apply_pre_execution_learning(
        self, swarm: SwarmBase, problem: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply learned knowledge before execution"""
        context = {
            "execution_mode": swarm.config.execution_mode,
            "problem_type": problem.get("type", "general"),
            "agent_count": len(swarm.agents),
        }

        applicable_knowledge = await self.learning_system.get_applicable_knowledge(
            context, limit=3
        )
        modifications = {}

        for knowledge in applicable_knowledge:
            application = await self.learning_system.apply_knowledge(knowledge, context)
            modifications.update(application.get("modifications", {}))

        return {
            "applied_knowledge": [k.id for k in applicable_knowledge],
            "modifications": modifications,
            "expected_improvements": [k.expected_outcome for k in applicable_knowledge],
        }


class LearningEnhancedParallelExecution(LearningEnhancedExecutionStrategy):
    """Learning-enhanced parallel execution with coordination learning"""

    async def execute_with_learning(
        self, swarm: SwarmBase, problem: dict[str, Any], context: dict[str, Any]
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Execute parallel swarm with learning coordination"""
        with tracer.start_span(
            "learning_parallel_execution", kind=SpanKind.INTERNAL
        ) as span:
            span.set_attribute("swarm.id", swarm.config.swarm_id)
            span.set_attribute("agent.count", len(swarm.agents))

            # Apply pre-execution learning
            learning_enhancements = await self.apply_pre_execution_learning(
                swarm, problem
            )

            # Enhanced parallel execution with knowledge sharing
            start_time = time.time()

            # Create shared knowledge context for agents
            shared_context = {
                **context,
                "learning_enhancements": learning_enhancements,
                "parallel_coordination": await self._get_coordination_knowledge(
                    swarm, problem
                ),
            }

            # Execute agents with learning-enhanced coordination
            async def execute_learning_agent(agent, agent_id: str):
                agent_context = {
                    **shared_context,
                    "agent_id": agent_id,
                    "peer_agents": [
                        f"agent_{i}"
                        for i in range(len(swarm.agents))
                        if f"agent_{i}" != agent_id
                    ],
                }

                # Apply agent-specific learned knowledge
                agent_knowledge = await self._get_agent_knowledge(agent_id, problem)
                if agent_knowledge:
                    agent_context["agent_knowledge"] = agent_knowledge

                try:
                    result = await swarm._execute_single_agent(
                        agent, problem, agent_context
                    )

                    # Enhance result with learning metadata
                    result["learning_metadata"] = {
                        "knowledge_applied": (
                            len(agent_knowledge) if agent_knowledge else 0
                        ),
                        "execution_mode": "learning_parallel",
                    }

                    return result
                except Exception as e:
                    logger.error(f"Learning-enhanced agent execution failed: {e}")
                    return {"success": False, "error": str(e), "agent_id": agent_id}

            # Execute all agents with learning coordination
            tasks = [
                execute_learning_agent(agent, f"agent_{i}")
                for i, agent in enumerate(swarm.agents)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions
            valid_results = [r for r in results if isinstance(r, dict)]

            # Post-execution learning analysis
            execution_time = time.time() - start_time

            # Analyze parallel coordination effectiveness
            coordination_analysis = await self._analyze_parallel_coordination(
                valid_results, execution_time
            )

            # Capture execution experience
            execution_metadata = {
                "execution_time": execution_time,
                "coordination_effectiveness": coordination_analysis["effectiveness"],
                "knowledge_sharing_success": coordination_analysis[
                    "knowledge_sharing_success"
                ],
                "agent_synchronization": coordination_analysis.get(
                    "synchronization_score", 0.0
                ),
            }

            await self.capture_execution_experience(
                swarm, problem, valid_results, execution_metadata
            )

            span.set_attribute("execution.time", execution_time)
            span.set_attribute("results.count", len(valid_results))

            return valid_results, execution_metadata

    async def _get_coordination_knowledge(
        self, swarm: SwarmBase, problem: dict[str, Any]
    ) -> dict[str, Any]:
        """Get learned knowledge about parallel coordination"""
        context = {
            "execution_mode": SwarmExecutionMode.PARALLEL,
            "problem_type": problem.get("type", "general"),
            "knowledge_type": KnowledgeType.AGENT_COLLABORATION,
        }

        coordination_knowledge = await self.learning_system.get_applicable_knowledge(
            context, limit=2
        )

        coordination_strategies = {}
        for knowledge in coordination_knowledge:
            if knowledge.knowledge_type == KnowledgeType.AGENT_COLLABORATION:
                strategies = knowledge.pattern.get("coordination_strategies", {})
                coordination_strategies.update(strategies)

        return {
            "strategies": coordination_strategies,
            "optimal_agent_count": coordination_strategies.get(
                "optimal_agent_count", len(swarm.agents)
            ),
            "synchronization_points": coordination_strategies.get("sync_points", []),
        }

    async def _get_agent_knowledge(
        self, agent_id: str, problem: dict[str, Any]
    ) -> Optional[list[LearnedKnowledge]]:
        """Get agent-specific learned knowledge"""
        # This would integrate with agent-specific learning in a full implementation
        return []

    async def _analyze_parallel_coordination(
        self, results: list[dict[str, Any]], execution_time: float
    ) -> dict[str, Any]:
        """Analyze how well agents coordinated in parallel execution"""
        if not results:
            return {"effectiveness": 0.0, "knowledge_sharing_success": 0.0}

        # Calculate coordination metrics
        success_count = sum(1 for r in results if r.get("success", False))
        success_rate = success_count / len(results)

        # Analyze result consistency (indicator of good coordination)
        quality_scores = [
            r.get("quality_score", 0.0) for r in results if "quality_score" in r
        ]
        quality_variance = np.var(quality_scores) if quality_scores else 1.0
        consistency_score = max(
            0.0, 1.0 - quality_variance
        )  # Lower variance = better coordination

        # Knowledge sharing effectiveness (based on metadata)
        knowledge_applications = [
            r.get("learning_metadata", {}).get("knowledge_applied", 0) for r in results
        ]
        knowledge_sharing_success = (
            np.mean(knowledge_applications) if knowledge_applications else 0.0
        )

        effectiveness = (
            success_rate * 0.4
            + consistency_score * 0.4
            + min(knowledge_sharing_success / 5.0, 1.0) * 0.2
        )

        return {
            "effectiveness": effectiveness,
            "knowledge_sharing_success": min(knowledge_sharing_success / 5.0, 1.0),
            "synchronization_score": consistency_score,
            "success_rate": success_rate,
        }


class LearningEnhancedSequentialExecution(LearningEnhancedExecutionStrategy):
    """Learning-enhanced sequential execution with progressive knowledge building"""

    async def execute_with_learning(
        self, swarm: SwarmBase, problem: dict[str, Any], context: dict[str, Any]
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Execute sequential swarm with progressive learning"""
        with tracer.start_span(
            "learning_sequential_execution", kind=SpanKind.INTERNAL
        ) as span:
            span.set_attribute("swarm.id", swarm.config.swarm_id)
            span.set_attribute("agent.count", len(swarm.agents))

            # Apply pre-execution learning
            learning_enhancements = await self.apply_pre_execution_learning(
                swarm, problem
            )

            results = []
            progressive_knowledge = {}
            start_time = time.time()

            # Execute agents sequentially with learning accumulation
            for i, agent in enumerate(swarm.agents):
                agent_start_time = time.time()

                # Build context with accumulated knowledge
                agent_context = {
                    **context,
                    "agent_position": i,
                    "previous_results": results.copy(),
                    "progressive_knowledge": progressive_knowledge.copy(),
                    "learning_enhancements": learning_enhancements,
                }

                # Apply sequential learning patterns
                sequential_knowledge = await self._get_sequential_knowledge(
                    i, results, problem
                )
                if sequential_knowledge:
                    agent_context["sequential_patterns"] = sequential_knowledge

                try:
                    # Execute agent with enhanced context
                    result = await swarm._execute_single_agent(
                        agent, problem, agent_context
                    )

                    # Enhance result with sequential learning metadata
                    agent_execution_time = time.time() - agent_start_time
                    result["learning_metadata"] = {
                        "agent_position": i,
                        "execution_time": agent_execution_time,
                        "knowledge_inherited": len(results),
                        "sequential_improvements": await self._calculate_sequential_improvement(
                            results, result
                        ),
                    }

                    results.append(result)

                    # Update progressive knowledge
                    progressive_knowledge = await self._update_progressive_knowledge(
                        progressive_knowledge, result, i
                    )

                except Exception as e:
                    logger.error(f"Sequential agent {i} execution failed: {e}")
                    error_result = {
                        "success": False,
                        "error": str(e),
                        "agent_position": i,
                        "learning_metadata": {"knowledge_inherited": len(results)},
                    }
                    results.append(error_result)

            # Analyze sequential learning effectiveness
            execution_time = time.time() - start_time
            sequential_analysis = await self._analyze_sequential_learning(
                results, execution_time
            )

            # Capture execution experience
            execution_metadata = {
                "execution_time": execution_time,
                "sequential_effectiveness": sequential_analysis["effectiveness"],
                "knowledge_progression": sequential_analysis["knowledge_progression"],
                "improvement_trend": sequential_analysis.get("improvement_trend", 0.0),
            }

            await self.capture_execution_experience(
                swarm, problem, results, execution_metadata
            )

            span.set_attribute("execution.time", execution_time)
            span.set_attribute("results.count", len(results))

            return results, execution_metadata

    async def _get_sequential_knowledge(
        self,
        agent_position: int,
        previous_results: list[dict[str, Any]],
        problem: dict[str, Any],
    ) -> dict[str, Any]:
        """Get knowledge patterns for sequential execution"""
        context = {
            "execution_mode": SwarmExecutionMode.LINEAR,
            "agent_position": agent_position,
            "problem_type": problem.get("type", "general"),
        }

        sequential_knowledge = await self.learning_system.get_applicable_knowledge(
            context, limit=2
        )

        patterns = {}
        for knowledge in sequential_knowledge:
            if "sequential_patterns" in knowledge.pattern:
                patterns.update(knowledge.pattern["sequential_patterns"])

        # Add dynamic patterns based on previous results
        if previous_results:
            success_trend = [r.get("success", False) for r in previous_results]
            quality_trend = [r.get("quality_score", 0.0) for r in previous_results]

            patterns.update(
                {
                    "success_trend": success_trend,
                    "quality_trend": quality_trend,
                    "recommended_approach": (
                        "build_on_success" if success_trend[-1] else "course_correct"
                    ),
                }
            )

        return patterns

    async def _calculate_sequential_improvement(
        self, previous_results: list[dict[str, Any]], current_result: dict[str, Any]
    ) -> dict[str, Any]:
        """Calculate how much the current agent improved on previous work"""
        if not previous_results:
            return {"improvement_score": 0.0, "baseline": True}

        # Compare with previous result
        prev_quality = previous_results[-1].get("quality_score", 0.0)
        current_quality = current_result.get("quality_score", 0.0)

        improvement = current_quality - prev_quality
        improvement_percentage = (improvement / max(prev_quality, 0.1)) * 100

        return {
            "improvement_score": improvement,
            "improvement_percentage": improvement_percentage,
            "quality_progression": current_quality,
            "baseline": False,
        }

    async def _update_progressive_knowledge(
        self,
        current_knowledge: dict[str, Any],
        new_result: dict[str, Any],
        agent_position: int,
    ) -> dict[str, Any]:
        """Update progressive knowledge with new result"""
        updated_knowledge = current_knowledge.copy()

        # Add insights from current result
        if new_result.get("success", False):
            successful_patterns = updated_knowledge.get("successful_patterns", [])
            successful_patterns.append(
                {
                    "position": agent_position,
                    "approach": new_result.get("approach", "unknown"),
                    "quality_score": new_result.get("quality_score", 0.0),
                }
            )
            updated_knowledge["successful_patterns"] = successful_patterns

        # Track quality progression
        quality_history = updated_knowledge.get("quality_history", [])
        quality_history.append(new_result.get("quality_score", 0.0))
        updated_knowledge["quality_history"] = quality_history

        # Update recommendations for next agent
        if agent_position > 0:
            updated_knowledge["next_agent_recommendations"] = (
                await self._generate_next_agent_recommendations(
                    updated_knowledge, new_result
                )
            )

        return updated_knowledge

    async def _generate_next_agent_recommendations(
        self, knowledge: dict[str, Any], latest_result: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate recommendations for the next agent in sequence"""
        recommendations = {}

        # Analyze quality trend
        quality_history = knowledge.get("quality_history", [])
        if len(quality_history) >= 2:
            trend = quality_history[-1] - quality_history[-2]
            if trend > 0:
                recommendations["strategy"] = "continue_current_approach"
                recommendations["confidence_boost"] = 0.1
            else:
                recommendations["strategy"] = "try_different_approach"
                recommendations["confidence_penalty"] = 0.1

        # Successful pattern recommendations
        successful_patterns = knowledge.get("successful_patterns", [])
        if successful_patterns:
            best_pattern = max(successful_patterns, key=lambda p: p["quality_score"])
            recommendations["emulate_pattern"] = best_pattern

        return recommendations

    async def _analyze_sequential_learning(
        self, results: list[dict[str, Any]], execution_time: float
    ) -> dict[str, Any]:
        """Analyze effectiveness of sequential learning"""
        if not results:
            return {"effectiveness": 0.0, "knowledge_progression": 0.0}

        # Calculate quality progression
        quality_scores = [r.get("quality_score", 0.0) for r in results]
        if len(quality_scores) > 1:
            # Linear regression to find improvement trend
            x = np.arange(len(quality_scores))
            slope = np.polyfit(x, quality_scores, 1)[0]
            improvement_trend = max(0.0, slope)  # Positive trend indicates learning
        else:
            improvement_trend = 0.0

        # Calculate knowledge inheritance effectiveness
        knowledge_inheritance = [
            r.get("learning_metadata", {}).get("knowledge_inherited", 0)
            for r in results
        ]
        avg_inheritance = (
            np.mean(knowledge_inheritance) if knowledge_inheritance else 0.0
        )

        # Overall effectiveness
        success_rate = sum(1 for r in results if r.get("success", False)) / len(results)
        effectiveness = (
            success_rate * 0.4
            + improvement_trend * 0.4
            + min(avg_inheritance / 10.0, 1.0) * 0.2
        )

        return {
            "effectiveness": effectiveness,
            "knowledge_progression": improvement_trend,
            "improvement_trend": improvement_trend,
            "average_inheritance": avg_inheritance,
            "success_rate": success_rate,
        }


class LearningEnhancedDebateExecution(LearningEnhancedExecutionStrategy):
    """Learning-enhanced debate execution with adversarial learning"""

    async def execute_with_learning(
        self, swarm: SwarmBase, problem: dict[str, Any], context: dict[str, Any]
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Execute debate swarm with adversarial learning"""
        with tracer.start_span(
            "learning_debate_execution", kind=SpanKind.INTERNAL
        ) as span:
            span.set_attribute("swarm.id", swarm.config.swarm_id)
            span.set_attribute("agent.count", len(swarm.agents))

            # Apply pre-execution learning for debate strategies
            learning_enhancements = await self.apply_pre_execution_learning(
                swarm, problem
            )

            start_time = time.time()

            # Get debate-specific learned knowledge
            debate_knowledge = await self._get_debate_knowledge(swarm, problem)

            # Enhanced debate execution with learning
            debate_context = {
                **context,
                "learning_enhancements": learning_enhancements,
                "debate_strategies": debate_knowledge,
                "adversarial_learning_enabled": True,
            }

            # Execute debate pattern with learning enhancement
            if "debate" in swarm.patterns:
                try:
                    debate_result = await swarm.patterns["debate"].apply(
                        problem, debate_context
                    )
                    results = [debate_result] if debate_result else []
                except Exception as e:
                    logger.error(f"Learning-enhanced debate execution failed: {e}")
                    results = [{"success": False, "error": str(e)}]
            else:
                # Fallback to parallel with debate-like learning
                results = await self._simulate_learning_debate(
                    swarm, problem, debate_context
                )

            execution_time = time.time() - start_time

            # Analyze debate learning effectiveness
            debate_analysis = await self._analyze_debate_learning(
                results, execution_time, debate_knowledge
            )

            # Capture execution experience
            execution_metadata = {
                "execution_time": execution_time,
                "debate_effectiveness": debate_analysis["effectiveness"],
                "consensus_quality": debate_analysis["consensus_quality"],
                "adversarial_learning_score": debate_analysis.get(
                    "adversarial_score", 0.0
                ),
            }

            await self.capture_execution_experience(
                swarm, problem, results, execution_metadata
            )

            span.set_attribute("execution.time", execution_time)
            span.set_attribute("results.count", len(results))

            return results, execution_metadata

    async def _get_debate_knowledge(
        self, swarm: SwarmBase, problem: dict[str, Any]
    ) -> dict[str, Any]:
        """Get learned knowledge about debate strategies"""
        context = {
            "execution_mode": SwarmExecutionMode.DEBATE,
            "problem_type": problem.get("type", "general"),
            "knowledge_type": KnowledgeType.CONSENSUS_MECHANISM,
        }

        debate_knowledge = await self.learning_system.get_applicable_knowledge(
            context, limit=3
        )

        strategies = {
            "argument_strategies": [],
            "consensus_mechanisms": [],
            "quality_criteria": {},
        }

        for knowledge in debate_knowledge:
            pattern = knowledge.pattern

            if "argument_strategies" in pattern:
                strategies["argument_strategies"].extend(pattern["argument_strategies"])

            if "consensus_mechanisms" in pattern:
                strategies["consensus_mechanisms"].extend(
                    pattern["consensus_mechanisms"]
                )

            if "quality_criteria" in pattern:
                strategies["quality_criteria"].update(pattern["quality_criteria"])

        return strategies

    async def _simulate_learning_debate(
        self, swarm: SwarmBase, problem: dict[str, Any], context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Simulate debate execution with learning when pattern not available"""
        # Split agents into debate roles
        total_agents = len(swarm.agents)
        debaters = (
            swarm.agents[: total_agents // 2] if total_agents > 1 else swarm.agents
        )
        moderators = swarm.agents[total_agents // 2 :] if total_agents > 2 else []

        debate_results = []

        # Simulated debate rounds with learning
        for round_num in range(min(3, len(debaters))):  # Up to 3 rounds
            round_context = {
                **context,
                "round_number": round_num,
                "debate_role": "debater" if round_num < len(debaters) else "moderator",
            }

            agent = debaters[round_num] if round_num < len(debaters) else moderators[0]

            try:
                result = await swarm._execute_single_agent(
                    agent, problem, round_context
                )
                result["debate_metadata"] = {
                    "round": round_num,
                    "role": round_context["debate_role"],
                    "adversarial_score": 0.7 + round_num * 0.1,  # Simulated improvement
                }
                debate_results.append(result)
            except Exception as e:
                debate_results.append(
                    {"success": False, "error": str(e), "round": round_num}
                )

        return debate_results

    async def _analyze_debate_learning(
        self,
        results: list[dict[str, Any]],
        execution_time: float,
        debate_knowledge: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyze effectiveness of debate learning"""
        if not results:
            return {"effectiveness": 0.0, "consensus_quality": 0.0}

        # Calculate consensus quality
        quality_scores = [
            r.get("quality_score", 0.0) for r in results if "quality_score" in r
        ]
        consensus_quality = np.mean(quality_scores) if quality_scores else 0.0

        # Calculate adversarial learning score
        adversarial_scores = [
            r.get("debate_metadata", {}).get("adversarial_score", 0.0) for r in results
        ]
        adversarial_score = np.mean(adversarial_scores) if adversarial_scores else 0.0

        # Knowledge application effectiveness
        knowledge_applied = len(debate_knowledge.get("argument_strategies", [])) > 0

        # Overall effectiveness
        success_rate = sum(1 for r in results if r.get("success", False)) / len(results)
        effectiveness = (
            success_rate * 0.3
            + consensus_quality * 0.3
            + adversarial_score * 0.2
            + (0.2 if knowledge_applied else 0.0)
        )

        return {
            "effectiveness": effectiveness,
            "consensus_quality": consensus_quality,
            "adversarial_score": adversarial_score,
            "success_rate": success_rate,
            "knowledge_applied": knowledge_applied,
        }


class LearningEnhancedHierarchicalExecution(LearningEnhancedExecutionStrategy):
    """Learning-enhanced hierarchical execution with knowledge distillation"""

    async def execute_with_learning(
        self, swarm: SwarmBase, problem: dict[str, Any], context: dict[str, Any]
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Execute hierarchical swarm with knowledge distillation"""
        with tracer.start_span(
            "learning_hierarchical_execution", kind=SpanKind.INTERNAL
        ) as span:
            span.set_attribute("swarm.id", swarm.config.swarm_id)
            span.set_attribute("agent.count", len(swarm.agents))

            if not swarm.agents:
                return [], {"execution_time": 0.0, "hierarchical_effectiveness": 0.0}

            # Apply pre-execution learning
            learning_enhancements = await self.apply_pre_execution_learning(
                swarm, problem
            )

            start_time = time.time()

            # Get hierarchical learning knowledge
            hierarchy_knowledge = await self._get_hierarchical_knowledge(swarm, problem)

            # Enhanced hierarchical execution
            coordinator = swarm.agents[0]
            workers = swarm.agents[1:] if len(swarm.agents) > 1 else []

            # Coordinator planning with learning
            coordinator_context = {
                **context,
                "role": "coordinator",
                "worker_count": len(workers),
                "learning_enhancements": learning_enhancements,
                "hierarchy_knowledge": hierarchy_knowledge,
            }

            try:
                # Execute coordinator with enhanced context
                coordinator_result = await swarm._execute_single_agent(
                    coordinator, problem, coordinator_context
                )

                # Extract task assignments from coordinator
                task_assignments = coordinator_result.get(
                    "task_assignments",
                    [
                        {"task": f"subtask_{i}", "context": problem}
                        for i in range(len(workers))
                    ],
                )

                # Execute workers with knowledge distillation
                worker_results = []
                if workers and coordinator_result.get("success", False):
                    worker_results = await self._execute_workers_with_distillation(
                        swarm, workers, task_assignments, coordinator_result, context
                    )

                results = [coordinator_result] + worker_results

            except Exception as e:
                logger.error(f"Hierarchical coordinator execution failed: {e}")
                results = [{"success": False, "error": str(e), "role": "coordinator"}]

            execution_time = time.time() - start_time

            # Analyze hierarchical learning effectiveness
            hierarchical_analysis = await self._analyze_hierarchical_learning(
                results, execution_time, hierarchy_knowledge
            )

            # Capture execution experience
            execution_metadata = {
                "execution_time": execution_time,
                "hierarchical_effectiveness": hierarchical_analysis["effectiveness"],
                "knowledge_distillation_score": hierarchical_analysis[
                    "distillation_score"
                ],
                "coordination_quality": hierarchical_analysis.get(
                    "coordination_quality", 0.0
                ),
            }

            await self.capture_execution_experience(
                swarm, problem, results, execution_metadata
            )

            span.set_attribute("execution.time", execution_time)
            span.set_attribute("results.count", len(results))

            return results, execution_metadata

    async def _get_hierarchical_knowledge(
        self, swarm: SwarmBase, problem: dict[str, Any]
    ) -> dict[str, Any]:
        """Get learned knowledge about hierarchical coordination"""
        context = {
            "execution_mode": SwarmExecutionMode.HIERARCHICAL,
            "problem_type": problem.get("type", "general"),
            "knowledge_type": KnowledgeType.AGENT_COLLABORATION,
        }

        hierarchical_knowledge = await self.learning_system.get_applicable_knowledge(
            context, limit=3
        )

        knowledge = {
            "coordination_patterns": [],
            "delegation_strategies": {},
            "knowledge_flow": {},
        }

        for learned_knowledge in hierarchical_knowledge:
            pattern = learned_knowledge.pattern

            if "coordination_patterns" in pattern:
                knowledge["coordination_patterns"].extend(
                    pattern["coordination_patterns"]
                )

            if "delegation_strategies" in pattern:
                knowledge["delegation_strategies"].update(
                    pattern["delegation_strategies"]
                )

            if "knowledge_flow" in pattern:
                knowledge["knowledge_flow"].update(pattern["knowledge_flow"])

        return knowledge

    async def _execute_workers_with_distillation(
        self,
        swarm: SwarmBase,
        workers: list[Any],
        task_assignments: list[dict[str, Any]],
        coordinator_result: dict[str, Any],
        base_context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute worker agents with knowledge distillation from coordinator"""

        # Distill knowledge from coordinator to workers
        coordinator_knowledge = {
            "successful_approach": coordinator_result.get("approach", "standard"),
            "quality_insights": coordinator_result.get("quality_insights", {}),
            "coordination_strategy": coordinator_result.get("strategy", "parallel"),
        }

        async def execute_worker_with_distillation(
            worker, worker_id: int, task_assignment: dict[str, Any]
        ):
            worker_context = {
                **base_context,
                "role": "worker",
                "worker_id": worker_id,
                "task_assignment": task_assignment,
                "coordinator_knowledge": coordinator_knowledge,
                "distillation_enabled": True,
            }

            try:
                result = await swarm._execute_single_agent(
                    worker, task_assignment, worker_context
                )

                # Add distillation metadata
                result["distillation_metadata"] = {
                    "coordinator_knowledge_applied": True,
                    "task_assignment_id": task_assignment.get(
                        "id", f"task_{worker_id}"
                    ),
                    "distillation_effectiveness": await self._calculate_distillation_effectiveness(
                        result, coordinator_result
                    ),
                }

                return result
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "worker_id": worker_id,
                    "distillation_metadata": {"coordinator_knowledge_applied": False},
                }

        # Execute workers in parallel with knowledge distillation
        worker_tasks = [
            execute_worker_with_distillation(
                worker, i, task_assignments[i % len(task_assignments)]
            )
            for i, worker in enumerate(workers)
        ]

        return await asyncio.gather(*worker_tasks, return_exceptions=False)

    async def _calculate_distillation_effectiveness(
        self, worker_result: dict[str, Any], coordinator_result: dict[str, Any]
    ) -> float:
        """Calculate how effectively knowledge was distilled from coordinator to worker"""
        # Compare quality scores
        worker_quality = worker_result.get("quality_score", 0.0)
        coordinator_quality = coordinator_result.get("quality_score", 0.0)

        if coordinator_quality > 0:
            quality_retention = min(worker_quality / coordinator_quality, 1.0)
        else:
            quality_retention = 0.5  # Default if no quality score

        # Check approach similarity
        worker_approach = worker_result.get("approach", "unknown")
        coordinator_approach = coordinator_result.get("approach", "unknown")
        approach_similarity = 1.0 if worker_approach == coordinator_approach else 0.5

        # Overall distillation effectiveness
        return quality_retention * 0.7 + approach_similarity * 0.3

    async def _analyze_hierarchical_learning(
        self,
        results: list[dict[str, Any]],
        execution_time: float,
        hierarchy_knowledge: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyze effectiveness of hierarchical learning"""
        if not results:
            return {"effectiveness": 0.0, "distillation_score": 0.0}

        # Separate coordinator and worker results
        coordinator_results = [r for r in results if r.get("role") == "coordinator"]
        worker_results = [
            r
            for r in results
            if r.get("role") == "worker" or "distillation_metadata" in r
        ]

        # Calculate coordination quality
        coordinator_success = (
            len([r for r in coordinator_results if r.get("success", False)]) > 0
        )
        worker_success_rate = sum(
            1 for r in worker_results if r.get("success", False)
        ) / max(len(worker_results), 1)

        coordination_quality = (0.6 if coordinator_success else 0.0) + (
            worker_success_rate * 0.4
        )

        # Calculate knowledge distillation score
        distillation_scores = [
            r.get("distillation_metadata", {}).get("distillation_effectiveness", 0.0)
            for r in worker_results
        ]
        distillation_score = (
            np.mean(distillation_scores) if distillation_scores else 0.0
        )

        # Knowledge application effectiveness
        knowledge_applied = (
            len(hierarchy_knowledge.get("coordination_patterns", [])) > 0
        )

        # Overall effectiveness
        overall_success_rate = sum(1 for r in results if r.get("success", False)) / len(
            results
        )
        effectiveness = (
            overall_success_rate * 0.3
            + coordination_quality * 0.3
            + distillation_score * 0.3
            + (0.1 if knowledge_applied else 0.0)
        )

        return {
            "effectiveness": effectiveness,
            "distillation_score": distillation_score,
            "coordination_quality": coordination_quality,
            "coordinator_success": coordinator_success,
            "worker_success_rate": worker_success_rate,
            "knowledge_applied": knowledge_applied,
        }


# =============================================================================
# EXECUTION MODE FACTORY
# =============================================================================


class LearningEnhancedExecutionFactory:
    """Factory for creating learning-enhanced execution strategies"""

    def __init__(self, learning_system: AdaptiveLearningSystem):
        self.learning_system = learning_system
        self._strategies = {}
        self._initialize_strategies()

    def _initialize_strategies(self):
        """Initialize all learning-enhanced execution strategies"""
        self._strategies = {
            SwarmExecutionMode.PARALLEL: LearningEnhancedParallelExecution(
                self.learning_system
            ),
            SwarmExecutionMode.LINEAR: LearningEnhancedSequentialExecution(
                self.learning_system
            ),
            SwarmExecutionMode.DEBATE: LearningEnhancedDebateExecution(
                self.learning_system
            ),
            SwarmExecutionMode.HIERARCHICAL: LearningEnhancedHierarchicalExecution(
                self.learning_system
            ),
            # Note: CONSENSUS and EVOLUTIONARY would be implemented similarly
        }

    def get_strategy(
        self, execution_mode: SwarmExecutionMode
    ) -> Optional[LearningEnhancedExecutionStrategy]:
        """Get learning-enhanced strategy for execution mode"""
        return self._strategies.get(execution_mode)

    async def execute_with_learning(
        self, swarm: SwarmBase, problem: dict[str, Any], context: dict[str, Any]
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Execute swarm with appropriate learning-enhanced strategy"""
        strategy = self.get_strategy(swarm.config.execution_mode)

        if strategy:
            return await strategy.execute_with_learning(swarm, problem, context)
        else:
            # Fallback to original execution without learning
            logger.warning(
                f"No learning strategy for {swarm.config.execution_mode}, using original execution"
            )
            results = await swarm.execute_agents(problem, context)
            return results, {"execution_time": 0.0, "learning_enhanced": False}


# =============================================================================
# LEARNING-ENHANCED SWARM INTEGRATION
# =============================================================================


async def integrate_learning_with_swarm(
    swarm: SwarmBase, learning_system: AdaptiveLearningSystem
) -> SwarmBase:
    """Integrate learning system with existing swarm"""

    # Create execution factory
    execution_factory = LearningEnhancedExecutionFactory(learning_system)

    # Override execute_agents method with learning-enhanced version
    original_execute_agents = swarm.execute_agents

    async def learning_enhanced_execute_agents(
        problem: dict[str, Any], context: dict[str, Any]
    ):
        """Learning-enhanced version of execute_agents"""
        try:
            # Use learning-enhanced execution
            results, execution_metadata = await execution_factory.execute_with_learning(
                swarm, problem, context
            )

            # Update swarm metrics with learning metadata
            if hasattr(swarm, "metrics") and execution_metadata:
                # Add learning-specific metrics to swarm metrics
                if "execution_time" in execution_metadata:
                    # This would integrate with existing metrics system
                    pass

            return results

        except Exception as e:
            logger.error(
                f"Learning-enhanced execution failed, falling back to original: {e}"
            )
            return await original_execute_agents(problem, context)

    # Replace method
    swarm.execute_agents = learning_enhanced_execute_agents

    logger.info(f"🧠 Integrated learning system with swarm {swarm.config.swarm_id}")
    return swarm


if __name__ == "__main__":
    # Example usage demonstration
    async def demo():
        from app.memory.unified_memory import get_memory_store
        from app.swarms.communication.message_bus import MessageBus
        from app.swarms.learning.adaptive_learning_system import create_learning_system

        # Initialize components
        memory_store = get_memory_store()
        message_bus = MessageBus()
        await message_bus.initialize()

        # Create learning system
        learning_system = await create_learning_system(memory_store, message_bus)

        # Create execution factory
        factory = LearningEnhancedExecutionFactory(learning_system)

        print("🧠 Learning-enhanced execution modes initialized")
        print(f"Available strategies: {list(factory._strategies.keys())}")

        # Cleanup
        await learning_system.cleanup()
        await message_bus.close()

        print("✅ Demo completed")

    asyncio.run(demo())
