"""
Memory-Enhanced Swarm System
Extends ImprovedAgentSwarm with full memory integration following ADR-005.
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional

from app.core.circuit_breaker import with_circuit_breaker
from app.memory.supermemory_mcp import MemoryType

from .consciousness_tracking import ConsciousnessTracker
from .improved_swarm import ImprovedAgentSwarm
from .memory_integration import SwarmMemoryEventType, SwarmMemoryMixin
from .patterns.memory_integration import (
    MemoryEnhancedStrategyArchive,
    MemoryIntegrationPattern,
)

logger = logging.getLogger(__name__)


class MemoryEnhancedImprovedSwarm(ImprovedAgentSwarm, SwarmMemoryMixin):
    """
    Memory-enhanced version of ImprovedAgentSwarm with full memory integration.
    Combines all 8 enhancement patterns with persistent memory capabilities.
    """

    def __init__(
        self,
        agents: list,
        config_file: str = "swarm_config.json",
        swarm_type: str = "enhanced_swarm",
    ):
        """
        Initialize memory-enhanced swarm.

        Args:
            agents: List of agents
            config_file: Configuration file path
            swarm_type: Type identifier for this swarm
        """
        # Initialize parent classes
        ImprovedAgentSwarm.__init__(self, agents, config_file)
        SwarmMemoryMixin.__init__(self)

        self.swarm_type = swarm_type
        self.swarm_id = f"{swarm_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Memory integration components
        self.memory_pattern = MemoryIntegrationPattern()
        self.memory_enhanced_archive: Optional[MemoryEnhancedStrategyArchive] = None

        # Consciousness tracking integration
        self.consciousness_tracker: Optional[ConsciousnessTracker] = None

        # Memory-enhanced execution tracking
        self.memory_execution_log = []
        self.context_cache = {}

        logger.info(
            f"Memory-enhanced swarm initialized: {self.swarm_type}:{self.swarm_id}"
        )

    async def initialize_full_system(self):
        """Initialize all swarm systems including memory integration."""
        try:
            # Initialize memory integration
            await self.initialize_memory(self.swarm_type, self.swarm_id)
            await self.memory_pattern.initialize()

            # Replace file-based strategy archive with memory-enhanced version
            if self.memory_client:
                self.memory_enhanced_archive = MemoryEnhancedStrategyArchive(
                    self.swarm_type, self.memory_client
                )

            # Initialize consciousness tracking
            await self.initialize_consciousness_tracking()

            # Load initial context from memory
            await self._load_initial_context()

            logger.info(f"Full system initialization complete for {self.swarm_type}")

        except Exception as e:
            logger.error(f"Failed to initialize full system: {e}")
            # Continue without memory integration if it fails

    async def initialize_consciousness_tracking(self):
        """Initialize consciousness tracking for the swarm."""
        if not self.memory_client:
            logger.warning("Memory client not available for consciousness tracking")
            return

        try:
            self.consciousness_tracker = ConsciousnessTracker(
                self.swarm_type, self.swarm_id, self.memory_client
            )

            logger.info(
                f"🧠 Consciousness tracking initialized for {self.swarm_type}:{self.swarm_id}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize consciousness tracking: {e}")

    async def _load_initial_context(self):
        """Load initial context from memory system."""
        if not self.memory_client:
            return

        try:
            # Load swarm context
            context = await self.memory_client.load_swarm_context()
            self.context_cache = context

            # Apply context to existing systems
            await self._apply_memory_context_to_systems(context)

        except Exception as e:
            logger.error(f"Failed to load initial context: {e}")

    async def _apply_memory_context_to_systems(self, context: dict[str, Any]):
        """Apply memory context to enhance existing swarm systems."""

        # Enhance adaptive parameters with historical data
        if "learnings" in context and hasattr(self, "param_manager"):
            performance_learnings = [
                l
                for l in context["learnings"]
                if l.get("learning_type") == "performance_optimization"
            ]

            for learning in performance_learnings[:5]:
                # Apply performance insights to parameter manager
                confidence = learning.get("confidence", 0)
                if confidence > 0.8:
                    # Simulate parameter adjustment based on learning
                    self.param_manager.performance_history.append(confidence)

        # Enhance safety system with historical risk patterns
        if "patterns" in context and hasattr(self, "safety_system"):
            risk_patterns = [
                p
                for p in context["patterns"]
                if "risk" in p.get("pattern_name", "").lower()
            ]

            # Update safety thresholds based on historical data
            if risk_patterns:
                avg_risk_score = sum(
                    p.get("success_score", 0.5) for p in risk_patterns
                ) / len(risk_patterns)
                if avg_risk_score < 0.6:
                    # Increase safety threshold if historical patterns show risks
                    self.safety_system.max_risk *= 0.9
                    logger.info(
                        "Adjusted safety threshold based on historical risk patterns"
                    )

    async def solve_with_memory_integration(self, problem: dict) -> dict:
        """
        Solve problem with full memory integration and enhancement patterns.

        Args:
            problem: Problem to solve

        Returns:
            Enhanced solution with memory integration data
        """
        start_time = datetime.now()

        # Prepare memory-enhanced context
        memory_context = {
            "task": problem,
            "swarm_info": {
                "type": self.swarm_type,
                "id": self.swarm_id,
                "agent_count": len(self.agents),
            },
        }

        # Execute memory integration pattern
        memory_result = await self.memory_pattern.execute(memory_context, self.agents)

        # Load relevant memory context
        relevant_context = await self._load_relevant_context(problem)

        # Enhanced execution with memory insights
        enhanced_problem = self._enhance_problem_with_memory(problem, relevant_context)

        # Execute original solve_with_improvements with enhancements
        base_result = await self._execute_enhanced_solve(enhanced_problem)

        # Measure consciousness after execution
        consciousness_result = await self._measure_post_execution_consciousness(
            problem, base_result
        )
        if consciousness_result:
            base_result["consciousness_measurement"] = consciousness_result

        # Post-execution memory operations
        await self._post_execution_memory_operations(
            problem, base_result, relevant_context
        )

        # Combine results
        execution_time = (datetime.now() - start_time).total_seconds()

        enhanced_result = {
            **base_result,
            "memory_integration": {
                "active": memory_result.success,
                "context_loaded": bool(relevant_context),
                "patterns_applied": len(relevant_context.get("relevant_patterns", [])),
                "learnings_applied": len(
                    relevant_context.get("relevant_learnings", [])
                ),
                "memory_operations": (
                    memory_result.data if memory_result.success else {}
                ),
            },
            "total_execution_time": execution_time,
            "memory_enhanced": True,
        }

        # Log execution
        self.memory_execution_log.append(
            {
                "problem": problem,
                "result": enhanced_result,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Include consciousness data in result
        if consciousness_result:
            enhanced_result["consciousness_data"] = consciousness_result

        return enhanced_result

    async def _load_relevant_context(self, problem: dict[str, Any]) -> dict[str, Any]:
        """Load relevant context from memory for problem solving."""
        if not self.memory_client:
            return {}

        return await super()._load_relevant_context(problem)

    def _enhance_problem_with_memory(self, problem: dict, context: dict) -> dict:
        """Enhance problem with memory insights."""
        enhanced_problem = problem.copy()

        # Add memory insights to problem context
        if context.get("relevant_patterns"):
            enhanced_problem["memory_insights"] = {
                "successful_patterns": context["relevant_patterns"][:3],
                "pattern_count": len(context["relevant_patterns"]),
            }

        if context.get("relevant_learnings"):
            enhanced_problem["historical_learnings"] = {
                "learnings": context["relevant_learnings"][:5],
                "learning_count": len(context["relevant_learnings"]),
            }

        if context.get("similar_tasks"):
            enhanced_problem["similar_executions"] = {
                "similar_tasks": context["similar_tasks"][:3],
                "task_count": len(context["similar_tasks"]),
            }

        return enhanced_problem

    async def _execute_enhanced_solve(self, enhanced_problem: dict) -> dict:
        """Execute enhanced solve with memory integration."""

        # Memory-enhanced safety check
        is_safe, safety_result = await self._memory_enhanced_safety_check(
            enhanced_problem
        )
        if not is_safe:
            return safety_result

        # Memory-enhanced role assignment
        problem_type = enhanced_problem.get("type", "general")
        agent_roles = await self._memory_enhanced_role_assignment(enhanced_problem)

        # Check memory-enhanced strategy archive
        archived_pattern = None
        if self.memory_enhanced_archive:
            archived_pattern = await self.memory_enhanced_archive.retrieve_best_pattern(
                problem_type
            )

        if archived_pattern:
            logger.info(f"Using memory-enhanced archived pattern for {problem_type}")
            agent_roles = archived_pattern.get("roles", agent_roles)

        # Execute with quality gates (enhanced with memory context)
        initial_result = await self._memory_enhanced_quality_execution(
            enhanced_problem, agent_roles
        )

        # Memory-enhanced adversarial debate if needed
        if 0.6 <= initial_result.get("quality_score", 0) < 0.8:
            initial_result = await self._memory_enhanced_debate(
                enhanced_problem, initial_result
            )

        # Memory-enhanced consensus if needed
        if initial_result.get("multiple_solutions"):
            consensus_result = await self._memory_enhanced_consensus(
                enhanced_problem, initial_result["multiple_solutions"]
            )
            initial_result["consensus"] = consensus_result

        # Archive successful pattern in memory
        if (
            initial_result.get("quality_score", 0) > 0.8
            and self.memory_enhanced_archive
        ):
            await self.memory_enhanced_archive.archive_success(
                problem_type,
                agent_roles,
                "memory_enhanced_flow",
                initial_result["quality_score"],
                additional_context={
                    "memory_patterns_used": len(
                        enhanced_problem.get("memory_insights", {}).get(
                            "successful_patterns", []
                        )
                    ),
                    "learnings_applied": len(
                        enhanced_problem.get("historical_learnings", {}).get(
                            "learnings", []
                        )
                    ),
                },
            )

        # Update adaptive parameters with memory context
        if self.param_manager:
            self.param_manager.update_parameters(initial_result)

        # Attempt knowledge transfer with memory enhancement
        if initial_result.get("quality_score", 0) > 0.85:
            await self._memory_enhanced_knowledge_transfer(
                problem_type, agent_roles, initial_result
            )

        return {
            **initial_result,
            "agent_roles": agent_roles,
            "safety_check": safety_result,
            "memory_enhanced": True,
            "memory_patterns_applied": len(
                enhanced_problem.get("memory_insights", {}).get(
                    "successful_patterns", []
                )
            ),
            "historical_learnings_applied": len(
                enhanced_problem.get("historical_learnings", {}).get("learnings", [])
            ),
        }

    @with_circuit_breaker("database")
    async def _memory_enhanced_safety_check(self, problem: dict) -> tuple[bool, dict]:
        """Enhanced safety check using memory-based risk patterns."""

        # Standard safety check
        is_safe, safety_result = await self.safety_system.check_safety(problem)

        # Enhance with memory-based risk analysis
        if self.memory_client and is_safe:
            try:
                # Search for similar past safety incidents
                risk_memories = await self.memory_client.search_memory(
                    query=f"safety risk {problem.get('type', '')}",
                    limit=5,
                    memory_type=MemoryType.EPISODIC,
                    tags=["safety", "risk"],
                )

                if risk_memories:
                    # Analyze risk patterns
                    risk_count = len(risk_memories)
                    safety_result["memory_risk_analysis"] = {
                        "historical_risks_found": risk_count,
                        "risk_level": "elevated" if risk_count > 2 else "normal",
                    }

                    # Adjust risk score based on historical data
                    if risk_count > 2:
                        safety_result["risk_score"] = min(
                            safety_result.get("risk_score", 0) + 0.1, 1.0
                        )

            except Exception as e:
                logger.warning(f"Memory-enhanced safety check failed: {e}")

        return is_safe, safety_result

    async def _memory_enhanced_role_assignment(self, problem: dict) -> list[str]:
        """Enhanced role assignment using memory-based successful patterns."""

        # Standard role assignment
        standard_roles = await self.role_assigner.assign_roles(problem)

        # Enhance with memory patterns
        if self.memory_client:
            try:
                # Search for successful role patterns
                role_patterns = await self.memory_client.retrieve_patterns(
                    pattern_name=f"execution_strategy_{problem.get('type', 'general')}",
                    limit=3,
                )

                if role_patterns:
                    # Extract successful role combinations
                    memory_roles = []
                    for pattern in role_patterns:
                        pattern_data = pattern.get("pattern_data", {})
                        execution_strategy = pattern_data.get("execution_strategy", {})
                        agent_roles = execution_strategy.get("agent_roles", [])

                        if agent_roles and pattern.get("success_score", 0) > 0.85:
                            memory_roles.extend(agent_roles)

                    # Merge memory-based roles with standard roles
                    if memory_roles:
                        enhanced_roles = self._merge_roles(standard_roles, memory_roles)
                        logger.info(
                            f"Enhanced roles with memory patterns: {len(enhanced_roles)} roles"
                        )
                        return enhanced_roles

            except Exception as e:
                logger.warning(f"Memory-enhanced role assignment failed: {e}")

        return standard_roles

    def _merge_roles(
        self, standard_roles: list[str], memory_roles: list[str]
    ) -> list[str]:
        """Merge standard and memory-based roles."""
        # Combine and deduplicate while preserving order
        seen = set()
        merged = []

        # Add standard roles first
        for role in standard_roles:
            if role not in seen:
                seen.add(role)
                merged.append(role)

        # Add memory roles that aren't already present
        for role in memory_roles:
            if role not in seen and len(merged) < 10:  # Limit total roles
                seen.add(role)
                merged.append(role)

        return merged

    async def _memory_enhanced_quality_execution(
        self, problem: dict, agent_roles: list[str]
    ) -> dict:
        """Enhanced quality execution with memory-based optimization."""

        # Load quality optimization learnings
        quality_learnings = []
        if self.memory_client:
            try:
                quality_learnings = await self.memory_client.retrieve_learnings(
                    learning_type="quality_optimization", limit=5
                )
            except Exception as e:
                logger.warning(f"Failed to load quality learnings: {e}")

        # Adjust quality gates based on memory insights
        if quality_learnings:
            avg_confidence = sum(
                l.get("confidence", 0) for l in quality_learnings
            ) / len(quality_learnings)
            if avg_confidence > 0.8:
                # Historical learnings suggest adjusting quality threshold
                original_threshold = self.quality_gates.min_quality
                self.quality_gates.min_quality = min(original_threshold + 0.05, 0.95)
                logger.info(
                    f"Adjusted quality threshold based on memory: {original_threshold:.2f} -> {self.quality_gates.min_quality:.2f}"
                )

        # Execute with quality gates
        result = await self.quality_gates.execute_with_quality_gates(
            problem, self.agents[: len(agent_roles)]
        )

        # Log quality gate execution
        if self.memory_client:
            await self.memory_client.log_swarm_event(
                SwarmMemoryEventType.PATTERN_EXECUTED,
                {
                    "pattern": "quality_gates",
                    "rounds_required": result.get("rounds_required", 1),
                    "final_quality": result.get("quality_score", 0),
                    "status": result.get("status", "unknown"),
                },
            )

        return result

    async def _memory_enhanced_debate(
        self, problem: dict, initial_result: dict
    ) -> dict:
        """Enhanced adversarial debate with memory-based argument quality."""

        logger.info("Running memory-enhanced adversarial debate")

        # Load debate strategies from memory
        debate_strategies = []
        if self.memory_client:
            try:
                debate_strategies = await self.memory_client.retrieve_patterns(
                    pattern_name="adversarial_debate", limit=3
                )
            except Exception as e:
                logger.warning(f"Failed to load debate strategies: {e}")

        # Generate alternatives with memory enhancement
        alternatives = [initial_result["result"]]

        # Add memory-informed alternatives
        if debate_strategies:
            for strategy in debate_strategies:
                strategy_data = strategy.get("pattern_data", {})
                if strategy_data.get("outcome", {}).get("quality_score", 0) > 0.8:
                    alternatives.append(
                        {
                            "solution": f"Memory-enhanced alternative based on {strategy.get('pattern_name', 'unknown')}",
                            "confidence": strategy.get("success_score", 0.7),
                            "memory_source": strategy.get("pattern_name", ""),
                        }
                    )

        # Add standard alternatives
        alternatives.extend(
            [
                {"solution": f"Alternative {i}", "confidence": 0.6 + (i * 0.1)}
                for i in range(1, 3)
            ]
        )

        # Conduct debate
        debate_result = await self.debate_system.conduct_debate(
            str(problem), alternatives
        )

        # Log debate execution
        if self.memory_client:
            await self.memory_client.log_swarm_event(
                SwarmMemoryEventType.PATTERN_EXECUTED,
                {
                    "pattern": "adversarial_debate",
                    "alternatives_count": len(alternatives),
                    "winner_score": debate_result.get("score", 0),
                    "memory_alternatives_used": len(debate_strategies),
                },
            )

        # Update result
        initial_result["result"] = debate_result["solution"]
        initial_result["quality_score"] = debate_result["score"]
        initial_result["debate_enhanced"] = True

        return initial_result

    async def _memory_enhanced_consensus(
        self, problem: dict, multiple_solutions: list
    ) -> dict:
        """Enhanced consensus with memory-based voting patterns."""

        # Load consensus strategies from memory
        consensus_strategies = []
        if self.memory_client:
            try:
                consensus_strategies = await self.memory_client.retrieve_patterns(
                    pattern_name="consensus", limit=3
                )
            except Exception as e:
                logger.warning(f"Failed to load consensus strategies: {e}")

        # Adjust consensus parameters based on memory
        if consensus_strategies:
            avg_success = sum(
                s.get("success_score", 0) for s in consensus_strategies
            ) / len(consensus_strategies)
            if avg_success > 0.85:
                # Historical consensus patterns are very successful, use those parameters
                best_strategy = max(
                    consensus_strategies, key=lambda s: s.get("success_score", 0)
                )
                strategy_data = best_strategy.get("pattern_data", {})

                # Apply memory-based consensus configuration
                if "consensus_method" in strategy_data:
                    self.consensus_system.config["consensus_method"] = strategy_data[
                        "consensus_method"
                    ]

        # Execute consensus
        consensus_result = await self.consensus_system.reach_consensus(
            self.agents, multiple_solutions
        )

        # Log consensus execution
        if self.memory_client:
            await self.memory_client.log_swarm_event(
                SwarmMemoryEventType.CONSENSUS_REACHED,
                {
                    "solutions_count": len(multiple_solutions),
                    "consensus_achieved": consensus_result.get("consensus", False),
                    "winner": str(consensus_result.get("winner", "")),
                    "agreement_level": consensus_result.get("agreement_level", 0),
                },
            )

        return consensus_result

    async def _memory_enhanced_knowledge_transfer(
        self, problem_type: str, agent_roles: list[str], result: dict
    ):
        """Enhanced knowledge transfer using memory system."""

        if not self.memory_client:
            return

        # Create knowledge package
        knowledge_package = {
            "problem_type": problem_type,
            "agent_roles": agent_roles,
            "success_score": result.get("quality_score", 0),
            "execution_strategies": result.get("patterns_used", []),
            "performance_metrics": {
                "execution_time": result.get("execution_time", 0),
                "rounds_required": result.get("rounds_required", 1),
            },
            "context": {
                "memory_enhanced": True,
                "patterns_applied": result.get("memory_patterns_applied", 0),
                "learnings_applied": result.get("historical_learnings_applied", 0),
            },
        }

        # Transfer to related swarm types
        related_swarms = self._get_related_swarm_types(problem_type)

        for target_swarm in related_swarms:
            try:
                # Send knowledge through memory system
                await self.memory_client.send_message_to_swarm(
                    target_swarm_type=target_swarm,
                    message={
                        "type": "knowledge_transfer",
                        "knowledge_package": knowledge_package,
                    },
                    priority="normal",
                )

                # Store knowledge transfer event
                await self.memory_client.log_swarm_event(
                    SwarmMemoryEventType.KNOWLEDGE_TRANSFERRED,
                    {
                        "target_swarm": target_swarm,
                        "problem_type": problem_type,
                        "success_score": result.get("quality_score", 0),
                    },
                )

            except Exception as e:
                logger.error(f"Knowledge transfer to {target_swarm} failed: {e}")

        if related_swarms:
            logger.info(
                f"Knowledge transferred to {len(related_swarms)} related swarms"
            )

    def _get_related_swarm_types(self, problem_type: str) -> list[str]:
        """Get related swarm types for knowledge transfer."""
        # Define relationships between swarm types
        swarm_relationships = {
            "coding_team": ["coding_swarm", "coding_swarm_fast"],
            "coding_swarm": ["coding_team", "genesis_swarm"],
            "coding_swarm_fast": ["coding_team"],
            "genesis_swarm": ["coding_swarm"],
        }

        return swarm_relationships.get(self.swarm_type, [])

    async def _post_execution_memory_operations(
        self, problem: dict, result: dict, context: dict
    ):
        """Perform post-execution memory operations."""
        if not self.memory_client:
            return

        try:
            # Store execution metrics
            if self.memory_pattern.config.auto_store_metrics:
                metrics = {
                    "quality_score": result.get("quality_score", 0),
                    "execution_time": result.get("execution_time", 0),
                    "patterns_used": result.get("patterns_used", []),
                    "memory_enhancement_impact": {
                        "patterns_applied": result.get("memory_patterns_applied", 0),
                        "learnings_applied": result.get(
                            "historical_learnings_applied", 0
                        ),
                        "context_loaded": bool(context),
                    },
                }

                await self.memory_client.store_performance_metrics(
                    metrics, execution_context={"problem": problem}
                )

            # Capture new learnings from this execution
            await self._capture_execution_learnings(problem, result, context)

            # Store execution completion
            await self._store_task_execution(problem, result)

        except Exception as e:
            logger.error(f"Post-execution memory operations failed: {e}")

    async def _capture_execution_learnings(
        self, problem: dict, result: dict, context: dict
    ):
        """Capture learnings from this execution."""
        if not self.memory_client:
            return

        learnings = []

        # Learning from quality outcome
        quality_score = result.get("quality_score", 0)
        if quality_score > 0.9:
            learnings.append(
                {
                    "type": "quality_optimization",
                    "content": f"Achieved high quality ({quality_score:.2f}) for {problem.get('type', 'unknown')} using memory-enhanced approach",
                    "confidence": 0.9,
                    "context": {
                        "patterns_applied": result.get("memory_patterns_applied", 0),
                        "learnings_applied": result.get(
                            "historical_learnings_applied", 0
                        ),
                    },
                }
            )

        # Learning from execution efficiency
        execution_time = result.get("execution_time", 0)
        if execution_time > 0 and execution_time < 10.0:
            learnings.append(
                {
                    "type": "performance_optimization",
                    "content": f"Efficient execution in {execution_time:.1f}s with memory enhancement",
                    "confidence": 0.8,
                    "context": {"execution_time": execution_time},
                }
            )

        # Learning from memory enhancement impact
        patterns_applied = result.get("memory_patterns_applied", 0)
        if patterns_applied > 0:
            learnings.append(
                {
                    "type": "memory_enhancement_effectiveness",
                    "content": f"Memory enhancement with {patterns_applied} patterns improved execution quality",
                    "confidence": 0.75,
                    "context": {"patterns_count": patterns_applied},
                }
            )

        # Store learnings
        for learning in learnings:
            await self.memory_client.store_learning(
                learning_type=learning["type"],
                content=learning["content"],
                confidence=learning["confidence"],
                context=learning["context"],
            )

        if learnings:
            logger.info(f"Captured {len(learnings)} new learnings from execution")

    # ============================================
    # Inter-Swarm Communication
    # ============================================

    async def process_inter_swarm_messages(self) -> list[dict[str, Any]]:
        """Process messages from other swarms."""
        if not self.memory_client:
            return []

        try:
            # Get messages for this swarm
            messages = await self.memory_client.get_messages_for_swarm(limit=10)

            processed_messages = []
            for message in messages:
                message_data = message.get("message", {})

                if message_data.get("type") == "knowledge_transfer":
                    # Process knowledge transfer
                    knowledge = message_data.get("knowledge_package", {})
                    await self._process_knowledge_transfer(
                        knowledge, message.get("from_swarm", "")
                    )
                    processed_messages.append(message)

            if processed_messages:
                logger.info(f"Processed {len(processed_messages)} inter-swarm messages")

            return processed_messages

        except Exception as e:
            logger.error(f"Failed to process inter-swarm messages: {e}")
            return []

    async def _process_knowledge_transfer(
        self, knowledge: dict[str, Any], from_swarm: str
    ):
        """Process incoming knowledge transfer from another swarm."""
        if not self.memory_client:
            return

        try:
            # Store transferred knowledge as learning
            await self.memory_client.store_learning(
                learning_type="knowledge_transfer",
                content=f"Knowledge transfer from {from_swarm}: {json.dumps(knowledge, default=str)[:500]}",
                confidence=0.8,
                context={
                    "from_swarm": from_swarm,
                    "transfer_type": knowledge.get("problem_type", "general"),
                    "success_score": knowledge.get("success_score", 0),
                },
            )

            # If knowledge has high success score, adapt our parameters
            if knowledge.get("success_score", 0) > 0.85:
                # Try to adapt successful strategies
                await self._adapt_transferred_knowledge(knowledge)

            logger.info(f"Processed knowledge transfer from {from_swarm}")

        except Exception as e:
            logger.error(f"Failed to process knowledge transfer: {e}")

    async def _adapt_transferred_knowledge(self, knowledge: dict[str, Any]):
        """Adapt transferred knowledge to this swarm's context."""

        # Extract performance insights
        performance_metrics = knowledge.get("performance_metrics", {})
        execution_time = performance_metrics.get("execution_time", 0)

        # If the transferred knowledge shows good performance, learn from it
        if execution_time > 0 and execution_time < 15.0:
            # Update our adaptive parameters
            self.param_manager.performance_history.append(
                knowledge.get("success_score", 0.8)
            )

        # Extract successful execution strategies
        execution_strategies = knowledge.get("execution_strategies", [])
        if execution_strategies:
            # Store as potential patterns for future use
            await self.memory_client.store_pattern(
                pattern_name=f"transferred_strategy_{knowledge.get('problem_type', 'general')}",
                pattern_data={
                    "transferred_from": knowledge.get("context", {}).get(
                        "from_swarm", "unknown"
                    ),
                    "strategies": execution_strategies,
                    "original_success": knowledge.get("success_score", 0),
                },
                success_score=knowledge.get("success_score", 0.8)
                * 0.9,  # Slight discount for transferred knowledge
                context={"transfer_source": True},
            )

    # ============================================
    # Memory System Management
    # ============================================

    async def get_memory_enhanced_metrics(self) -> dict[str, Any]:
        """Get comprehensive metrics including memory integration data."""

        # Get base metrics
        base_metrics = self.get_performance_metrics()

        # Add memory integration metrics
        memory_metrics = {}
        if self.memory_pattern:
            memory_metrics = self.memory_pattern.get_memory_integration_metrics()

        # Get memory system statistics
        memory_stats = {}
        if self.memory_client:
            try:
                memory_stats = await self.memory_client.get_memory_stats()
            except Exception as e:
                memory_stats = {"error": str(e)}

        # Performance trends from memory
        performance_trends = []
        if self.memory_client:
            try:
                performance_trends = await self.memory_client.get_performance_trends(
                    metric_name="quality_score", days=7
                )
            except Exception as e:
                logger.warning(f"Failed to get performance trends: {e}")

        return {
            **base_metrics,
            "memory_integration": memory_metrics,
            "memory_system_stats": memory_stats,
            "performance_trends": performance_trends,
            "memory_execution_log": self.memory_execution_log[
                -10:
            ],  # Last 10 executions
            "context_cache_size": len(self.context_cache),
        }

    async def validate_memory_integration(self) -> dict[str, Any]:
        """Validate memory integration is working correctly."""
        validation = {
            "swarm_memory_client": self.memory_client is not None,
            "memory_pattern_active": self.memory_pattern is not None,
            "memory_archive_active": self.memory_enhanced_archive is not None,
        }

        # Test memory pattern if available
        if self.memory_pattern:
            pattern_validation = await self.memory_pattern.validate_memory_integration()
            validation["memory_pattern_validation"] = pattern_validation

        # Test memory client connectivity
        if self.memory_client:
            try:
                stats = await self.memory_client.get_memory_stats()
                validation["memory_server_accessible"] = "error" not in stats
            except Exception as e:
                validation["memory_server_accessible"] = False
                validation["memory_server_error"] = str(e)

        return validation

    async def cleanup_full_system(self):
        """Cleanup all systems including memory integration."""
        try:
            # Cleanup memory integration
            if self.memory_pattern:
                await self.memory_pattern.cleanup()

            # Close memory client
            await self.close_memory()

            logger.info(f"Full system cleanup complete for {self.swarm_type}")

        except Exception as e:
            logger.error(f"Failed to cleanup full system: {e}")

    async def _measure_post_execution_consciousness(
        self, problem: dict, result: dict
    ) -> Optional[dict[str, Any]]:
        """Measure consciousness after task execution."""
        if not self.consciousness_tracker:
            return None

        try:
            # Prepare context for consciousness measurement
            context = {
                "task": problem,
                "agent_count": len(self.agents),
                "execution_data": {
                    "quality_score": result.get("quality_score", 0.5),
                    "execution_time": result.get("execution_time", 0),
                    "success": result.get("success", True),
                    "agent_roles": result.get("agent_roles", []),
                    "patterns_used": result.get("patterns_used", []),
                    "memory_enhanced": result.get("memory_enhanced", False),
                    "memory_patterns_applied": result.get("memory_patterns_applied", 0),
                    "agent_response_times": [0.5] * len(self.agents),  # Simulated
                    "task_assignments": {
                        f"agent_{i}": 2 for i in range(len(self.agents))
                    },  # Simulated
                    "communication": {
                        "clarity_score": 0.7,
                        "relevance_score": 0.8,
                        "info_sharing_score": 0.6,
                        "feedback_score": 0.7,
                    },
                },
                "performance_data": {
                    "quality_scores": [result.get("quality_score", 0.5)],
                    "speed_score": min(
                        1.0, 10.0 / max(result.get("execution_time", 1), 0.1)
                    ),
                    "efficiency_score": result.get("quality_score", 0.5) * 0.8,
                    "reliability_score": 0.8 if result.get("success", True) else 0.3,
                },
                "memory_data": result.get("memory_integration", {}),
                "learning_data": {
                    "learnings_count": len(result.get("patterns_used", [])),
                    "avg_confidence": 0.7,
                },
            }

            # Perform consciousness measurement
            measurements = await self.consciousness_tracker.measure_consciousness(
                context
            )

            if measurements:
                # Get comprehensive consciousness metrics
                consciousness_metrics = (
                    self.consciousness_tracker.get_consciousness_metrics()
                )

                # Correlate with performance
                performance_correlation = await self.consciousness_tracker.correlate_consciousness_with_performance(
                    context["performance_data"]
                )

                return {
                    "consciousness_level": self.consciousness_tracker.consciousness_profile.current_level,
                    "development_stage": self.consciousness_tracker.consciousness_profile.development_stage,
                    "maturity_score": self.consciousness_tracker.consciousness_profile.maturity_score,
                    "measurements": {k.value: v.value for k, v in measurements.items()},
                    "emergence_events": len(
                        self.consciousness_tracker.emergence_events
                    ),
                    "breakthrough_patterns": len(
                        self.consciousness_tracker.breakthrough_patterns
                    ),
                    "performance_correlation": performance_correlation,
                    "consciousness_metrics": consciousness_metrics,
                }

        except Exception as e:
            logger.error(f"Failed to measure consciousness: {e}")
            return None


# ============================================
# Swarm Type Specializations
# ============================================


class MemoryEnhancedCodingTeam(MemoryEnhancedImprovedSwarm):
    """Memory-enhanced coding team optimized for general coding tasks."""

    def __init__(self, agents: list):
        super().__init__(agents, "swarm_config.json", "coding_team")

        # Coding team specific memory configuration
        self.memory_pattern.config.max_context_patterns = 3
        self.memory_pattern.config.max_context_learnings = 5
        self.memory_pattern.config.min_quality_for_pattern_storage = 0.75

    @with_circuit_breaker("database")
    async def _get_coding_specific_context(self, problem: dict) -> dict[str, Any]:
        """Load coding-specific context from memory."""
        if not self.memory_client:
            return {}

        # Search for coding patterns
        coding_patterns = await self.memory_client.search_memory(
            query=f"coding {problem.get('type', 'general')}",
            limit=5,
            memory_type=MemoryType.PROCEDURAL,
            tags=["coding", "pattern"],
        )

        # Search for code quality learnings
        quality_learnings = await self.memory_client.retrieve_learnings(
            learning_type="code_quality", limit=3
        )

        return {
            "coding_patterns": coding_patterns,
            "quality_learnings": quality_learnings,
        }


class MemoryEnhancedCodingSwarm(MemoryEnhancedImprovedSwarm):
    """Memory-enhanced coding swarm for complex projects."""

    def __init__(self, agents: list):
        super().__init__(agents, "swarm_config.json", "coding_swarm")

        # Advanced coding swarm memory configuration
        self.memory_pattern.config.max_context_patterns = 7
        self.memory_pattern.config.max_context_learnings = 15
        self.memory_pattern.config.min_quality_for_pattern_storage = 0.8
        self.memory_pattern.config.enable_inter_swarm_comm = True


class MemoryEnhancedFastSwarm(MemoryEnhancedImprovedSwarm):
    """Memory-enhanced fast swarm optimized for speed."""

    def __init__(self, agents: list):
        super().__init__(agents, "swarm_config.json", "coding_swarm_fast")

        # Fast swarm memory configuration (lighter memory usage)
        self.memory_pattern.config.max_context_patterns = 2
        self.memory_pattern.config.max_context_learnings = 3
        self.memory_pattern.config.load_context_on_init = False  # Skip for speed
        self.memory_pattern.config.auto_store_learnings = False  # Skip for speed
        self.memory_pattern.config.memory_operation_timeout = 2.0  # Shorter timeout


class MemoryEnhancedGenesisSwarm(MemoryEnhancedImprovedSwarm):
    """Memory-enhanced GENESIS swarm with advanced memory capabilities."""

    def __init__(self, agents: list):
        super().__init__(agents, "swarm_config.json", "genesis_swarm")

        # GENESIS swarm memory configuration (maximum capabilities)
        self.memory_pattern.config.max_context_patterns = 10
        self.memory_pattern.config.max_context_learnings = 20
        self.memory_pattern.config.max_context_history = 50
        self.memory_pattern.config.enable_inter_swarm_comm = True
        self.memory_pattern.config.auto_store_patterns = True
        self.memory_pattern.config.auto_store_learnings = True
        self.memory_pattern.config.auto_store_metrics = True

    @with_circuit_breaker("database")
    async def evolution_with_memory(self, performance_data: dict):
        """Evolution enhanced with memory-based insights."""
        if hasattr(self, "evolution_engine") and self.memory_client:
            # Store evolution event
            await self.memory_client.log_swarm_event(
                SwarmMemoryEventType.EVOLUTION_EVENT,
                {
                    "generation": getattr(self.evolution_engine, "generation", 1),
                    "avg_fitness": performance_data.get("avg_fitness", 0),
                    "evolution_type": "memory_enhanced",
                },
            )

            # Get historical evolution data for enhancement
            evolution_history = await self.memory_client.search_memory(
                query="evolution generation fitness",
                limit=10,
                memory_type=MemoryType.EPISODIC,
                tags=["evolution", "genesis"],
            )

            # Apply memory insights to evolution
            if evolution_history:
                logger.info(
                    f"Enhancing evolution with {len(evolution_history)} historical data points"
                )

            # Execute standard evolution
            evolution_result = await self.evolution_engine.evolve_agents(
                performance_data
            )

            # Store evolution learnings
            await self.memory_client.store_learning(
                learning_type="evolution_optimization",
                content=f"Evolution generation {evolution_result.get('generation', 0)} achieved avg fitness {evolution_result.get('avg_fitness', 0):.3f}",
                confidence=0.85,
                context=evolution_result,
            )

            return evolution_result

    @with_circuit_breaker("database")
    async def consciousness_with_memory(self):
        """Consciousness measurement enhanced with memory correlation."""
        if hasattr(self, "consciousness_tracker") and self.memory_client:
            # Standard consciousness measurement
            consciousness_level = (
                await self.consciousness_tracker.measure_consciousness()
            )

            # Store consciousness measurement
            await self.memory_client.log_swarm_event(
                SwarmMemoryEventType.CONSCIOUSNESS_MEASURED,
                {
                    "consciousness_level": consciousness_level,
                    "generation": (
                        getattr(self.evolution_engine, "generation", 1)
                        if hasattr(self, "evolution_engine")
                        else 1
                    ),
                    "emergence_events": len(
                        getattr(self.consciousness_tracker, "emergence_events", [])
                    ),
                },
            )

            # Correlate consciousness with memory patterns
            consciousness_history = await self.memory_client.search_memory(
                query="consciousness_level emergence",
                limit=20,
                memory_type=MemoryType.EPISODIC,
                tags=["consciousness", "genesis"],
            )

            if consciousness_history:
                logger.info(
                    f"Correlating consciousness with {len(consciousness_history)} historical measurements"
                )

            return consciousness_level
