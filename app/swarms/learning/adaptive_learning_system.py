#!/usr/bin/env python3
"""
Adaptive Learning System for Sophia Intel AI Swarms
Comprehensive learning framework that integrates with existing swarm execution patterns

Features:
- Real-time learning during swarm execution
- Cross-modal knowledge transfer between execution modes
- Memory-integrated learning with vector embeddings
- Sub-second learning updates with minimal overhead
- Domain-specific learning specialization
"""

import asyncio
import contextlib
import logging
import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

import numpy as np
from opentelemetry import trace
from opentelemetry.trace import SpanKind

from app.core.ai_logger import logger
from app.memory.unified_memory import UnifiedMemoryStore
from app.swarms.communication.message_bus import MessageBus
from app.swarms.core.swarm_base import SwarmExecutionMode, SwarmMetrics

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


# =============================================================================
# LEARNING ENUMS AND TYPES
# =============================================================================


class LearningType(Enum):
    """Types of learning supported by the system"""

    REINFORCEMENT = "reinforcement"
    IMITATION = "imitation"
    EVOLUTIONARY = "evolutionary"
    TRANSFER = "transfer"
    META = "meta"
    ADVERSARIAL = "adversarial"
    COLLECTIVE = "collective"


class KnowledgeType(Enum):
    """Types of knowledge that can be learned"""

    EXECUTION_PATTERN = "execution_pattern"
    PROBLEM_SOLUTION_MAPPING = "problem_solution_mapping"
    AGENT_COLLABORATION = "agent_collaboration"
    QUALITY_CRITERIA = "quality_criteria"
    FAILURE_PATTERN = "failure_pattern"
    OPTIMIZATION_STRATEGY = "optimization_strategy"
    CONSENSUS_MECHANISM = "consensus_mechanism"


class LearningScope(Enum):
    """Scope of learning application"""

    AGENT_LOCAL = "agent_local"
    SWARM_LOCAL = "swarm_local"
    CROSS_SWARM = "cross_swarm"
    GLOBAL = "global"


# =============================================================================
# LEARNING DATA STRUCTURES
# =============================================================================


@dataclass
class LearningExperience:
    """A single learning experience captured during execution"""

    id: str = field(default_factory=lambda: f"exp_{uuid4().hex[:8]}")
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    swarm_id: str = ""
    execution_mode: SwarmExecutionMode = SwarmExecutionMode.PARALLEL
    problem_type: str = ""

    # Context data
    problem_context: dict[str, Any] = field(default_factory=dict)
    execution_context: dict[str, Any] = field(default_factory=dict)
    agent_states: dict[str, Any] = field(default_factory=dict)

    # Outcome data
    solution: dict[str, Any] = field(default_factory=dict)
    success: bool = False
    performance_metrics: dict[str, float] = field(default_factory=dict)
    quality_score: float = 0.0

    # Learning metadata
    knowledge_type: KnowledgeType = KnowledgeType.EXECUTION_PATTERN
    learning_scope: LearningScope = LearningScope.SWARM_LOCAL
    confidence: float = 0.0

    def to_vector(self) -> np.ndarray:
        """Convert experience to vector representation for similarity search"""
        # Simple vectorization - in production would use more sophisticated embeddings
        features = []

        # Execution context features
        features.extend(
            [
                len(self.agent_states),
                self.quality_score,
                self.confidence,
                1.0 if self.success else 0.0,
            ]
        )

        # Performance metrics
        features.extend(
            [
                self.performance_metrics.get("response_time", 0.0),
                self.performance_metrics.get("agent_utilization", 0.0),
                self.performance_metrics.get("consensus_score", 0.0),
            ]
        )

        # Execution mode encoding
        mode_encoding = [0.0] * len(SwarmExecutionMode)
        for i, mode in enumerate(SwarmExecutionMode):
            if mode == self.execution_mode:
                mode_encoding[i] = 1.0
        features.extend(mode_encoding)

        return np.array(features, dtype=np.float32)


@dataclass
class LearnedKnowledge:
    """A piece of learned knowledge that can be applied"""

    id: str = field(default_factory=lambda: f"knowledge_{uuid4().hex[:8]}")
    knowledge_type: KnowledgeType = KnowledgeType.EXECUTION_PATTERN

    # Knowledge content
    pattern: dict[str, Any] = field(default_factory=dict)
    conditions: dict[str, Any] = field(default_factory=dict)
    expected_outcome: dict[str, Any] = field(default_factory=dict)

    # Learning metadata
    source_experiences: list[str] = field(default_factory=list)
    confidence: float = 0.0
    success_rate: float = 0.0
    usage_count: int = 0
    last_used: Optional[datetime] = None

    # Applicability
    applicable_modes: list[SwarmExecutionMode] = field(default_factory=list)
    problem_types: list[str] = field(default_factory=list)

    # Performance tracking
    effectiveness_history: list[float] = field(default_factory=list)

    def is_applicable(self, context: dict[str, Any]) -> tuple[bool, float]:
        """Check if this knowledge is applicable to given context"""
        score = 0.0
        total_checks = 0

        # Check execution mode
        if "execution_mode" in context:
            total_checks += 1
            if context["execution_mode"] in self.applicable_modes:
                score += 1.0

        # Check problem type
        if "problem_type" in context:
            total_checks += 1
            if any(pt in context.get("problem_type", "") for pt in self.problem_types):
                score += 1.0

        # Check conditions
        for condition, expected_value in self.conditions.items():
            if condition in context:
                total_checks += 1
                if context[condition] == expected_value:
                    score += 1.0

        if total_checks == 0:
            return False, 0.0

        applicability_score = score / total_checks
        is_applicable = applicability_score >= 0.6  # Threshold for applicability

        return is_applicable, applicability_score * self.confidence


@dataclass
class ExperienceReplayBuffer:
    """Buffer for storing and replaying learning experiences"""

    max_size: int = 10000
    experiences: deque = field(default_factory=lambda: deque(maxlen=10000))

    # Indexing for fast retrieval
    by_mode: dict[SwarmExecutionMode, list[str]] = field(default_factory=lambda: defaultdict(list))
    by_success: dict[bool, list[str]] = field(default_factory=lambda: defaultdict(list))
    by_knowledge_type: dict[KnowledgeType, list[str]] = field(
        default_factory=lambda: defaultdict(list)
    )

    def add_experience(self, experience: LearningExperience):
        """Add experience to buffer with indexing"""
        # Remove oldest if at capacity
        if len(self.experiences) >= self.max_size:
            old_exp = self.experiences[0]
            self._remove_from_indices(old_exp)

        # Add new experience
        self.experiences.append(experience)
        self._add_to_indices(experience)

    def _add_to_indices(self, experience: LearningExperience):
        """Add experience to search indices"""
        self.by_mode[experience.execution_mode].append(experience.id)
        self.by_success[experience.success].append(experience.id)
        self.by_knowledge_type[experience.knowledge_type].append(experience.id)

    def _remove_from_indices(self, experience: LearningExperience):
        """Remove experience from search indices"""
        self.by_mode[experience.execution_mode].remove(experience.id)
        self.by_success[experience.success].remove(experience.id)
        self.by_knowledge_type[experience.knowledge_type].remove(experience.id)

    def get_similar_experiences(
        self, query_experience: LearningExperience, limit: int = 10
    ) -> list[LearningExperience]:
        """Get experiences similar to the query"""
        query_vector = query_experience.to_vector()
        similarities = []

        for experience in self.experiences:
            exp_vector = experience.to_vector()
            # Cosine similarity
            similarity = np.dot(query_vector, exp_vector) / (
                np.linalg.norm(query_vector) * np.linalg.norm(exp_vector)
            )
            similarities.append((experience, similarity))

        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [exp for exp, _ in similarities[:limit]]


# =============================================================================
# LEARNING ALGORITHMS
# =============================================================================


class LearningAlgorithm(ABC):
    """Abstract base class for learning algorithms"""

    @abstractmethod
    async def learn_from_experience(
        self, experience: LearningExperience, context: dict[str, Any]
    ) -> Optional[LearnedKnowledge]:
        """Learn knowledge from a single experience"""
        pass

    @abstractmethod
    async def learn_from_batch(
        self, experiences: list[LearningExperience], context: dict[str, Any]
    ) -> list[LearnedKnowledge]:
        """Learn knowledge from a batch of experiences"""
        pass


class ReinforcementLearningAlgorithm(LearningAlgorithm):
    """Reinforcement learning for swarm optimization"""

    def __init__(self, learning_rate: float = 0.1, discount_factor: float = 0.9):
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.q_table: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    async def learn_from_experience(
        self, experience: LearningExperience, context: dict[str, Any]
    ) -> Optional[LearnedKnowledge]:
        """Update Q-values based on experience"""
        state_key = self._encode_state(experience.problem_context, experience.execution_context)
        action_key = self._encode_action(experience.execution_mode, experience.agent_states)

        # Calculate reward based on success and quality
        reward = self._calculate_reward(experience)

        # Q-learning update
        current_q = self.q_table[state_key][action_key]
        max_next_q = max(self.q_table[state_key].values()) if self.q_table[state_key] else 0.0

        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        self.q_table[state_key][action_key] = new_q

        # Create learned knowledge if significant improvement
        if abs(new_q - current_q) > 0.1:
            return LearnedKnowledge(
                knowledge_type=KnowledgeType.EXECUTION_PATTERN,
                pattern={"state": state_key, "action": action_key, "q_value": new_q},
                conditions=experience.problem_context,
                expected_outcome={"quality_score": experience.quality_score},
                confidence=min(abs(new_q) / 10.0, 1.0),
                applicable_modes=[experience.execution_mode],
                problem_types=[experience.problem_type],
            )

        return None

    async def learn_from_batch(
        self, experiences: list[LearningExperience], context: dict[str, Any]
    ) -> list[LearnedKnowledge]:
        """Learn from batch of experiences"""
        learned_knowledge = []

        for experience in experiences:
            knowledge = await self.learn_from_experience(experience, context)
            if knowledge:
                learned_knowledge.append(knowledge)

        return learned_knowledge

    def _encode_state(
        self, problem_context: dict[str, Any], execution_context: dict[str, Any]
    ) -> str:
        """Encode state for Q-table lookup"""
        # Simple encoding - in production would use more sophisticated state representation
        key_features = []
        key_features.append(f"agents_{execution_context.get('agent_count', 0)}")
        key_features.append(f"complexity_{problem_context.get('complexity', 'medium')}")
        key_features.append(f"type_{problem_context.get('type', 'general')}")
        return "|".join(key_features)

    def _encode_action(
        self, execution_mode: SwarmExecutionMode, agent_states: dict[str, Any]
    ) -> str:
        """Encode action for Q-table lookup"""
        return f"{execution_mode.value}_{len(agent_states)}"

    def _calculate_reward(self, experience: LearningExperience) -> float:
        """Calculate reward for reinforcement learning"""
        base_reward = 1.0 if experience.success else -0.5
        quality_bonus = experience.quality_score * 0.5
        efficiency_bonus = 1.0 / max(experience.performance_metrics.get("response_time", 1.0), 0.1)

        return base_reward + quality_bonus + min(efficiency_bonus, 1.0)


class TransferLearningAlgorithm(LearningAlgorithm):
    """Transfer learning between execution modes"""

    def __init__(self):
        self.mode_similarities: dict[tuple[SwarmExecutionMode, SwarmExecutionMode], float] = {}
        self._initialize_mode_similarities()

    def _initialize_mode_similarities(self):
        """Initialize similarity matrix between execution modes"""
        modes = list(SwarmExecutionMode)

        # Define similarity relationships
        similarities = {
            (SwarmExecutionMode.PARALLEL, SwarmExecutionMode.HIERARCHICAL): 0.7,
            (SwarmExecutionMode.CONSENSUS, SwarmExecutionMode.DEBATE): 0.8,
            (SwarmExecutionMode.LINEAR, SwarmExecutionMode.HIERARCHICAL): 0.6,
            (SwarmExecutionMode.EVOLUTIONARY, SwarmExecutionMode.CONSENSUS): 0.5,
        }

        # Populate similarity matrix (symmetric)
        for mode1 in modes:
            for mode2 in modes:
                if mode1 == mode2:
                    self.mode_similarities[(mode1, mode2)] = 1.0
                elif (mode1, mode2) in similarities:
                    self.mode_similarities[(mode1, mode2)] = similarities[(mode1, mode2)]
                elif (mode2, mode1) in similarities:
                    self.mode_similarities[(mode1, mode2)] = similarities[(mode2, mode1)]
                else:
                    self.mode_similarities[(mode1, mode2)] = 0.1

    async def learn_from_experience(
        self, experience: LearningExperience, context: dict[str, Any]
    ) -> Optional[LearnedKnowledge]:
        """Transfer knowledge from one mode to others"""
        if not experience.success:
            return None

        # Find similar execution modes for transfer
        similar_modes = []
        for mode in SwarmExecutionMode:
            similarity = self.mode_similarities.get((experience.execution_mode, mode), 0.0)
            if similarity > 0.5 and mode != experience.execution_mode:
                similar_modes.append((mode, similarity))

        if not similar_modes:
            return None

        # Create transferable knowledge
        return LearnedKnowledge(
            knowledge_type=KnowledgeType.EXECUTION_PATTERN,
            pattern={
                "source_mode": experience.execution_mode.value,
                "solution_pattern": experience.solution,
                "agent_collaboration": experience.agent_states,
            },
            conditions=experience.problem_context,
            expected_outcome={
                "quality_score": experience.quality_score * 0.8,  # Reduced confidence for transfer
                "success_probability": 0.7,
            },
            confidence=experience.confidence * 0.8,
            applicable_modes=[mode for mode, _ in similar_modes],
            problem_types=[experience.problem_type],
        )

    async def learn_from_batch(
        self, experiences: list[LearningExperience], context: dict[str, Any]
    ) -> list[LearnedKnowledge]:
        """Learn transferable patterns from batch"""
        # Group experiences by execution mode
        mode_groups = defaultdict(list)
        for exp in experiences:
            mode_groups[exp.execution_mode].append(exp)

        learned_knowledge = []

        # For each mode, create transferable knowledge to similar modes
        for source_mode, mode_experiences in mode_groups.items():
            successful_experiences = [exp for exp in mode_experiences if exp.success]

            if len(successful_experiences) >= 3:  # Need minimum examples for transfer
                # Find common patterns
                common_patterns = self._extract_common_patterns(successful_experiences)

                if common_patterns:
                    # Find target modes for transfer
                    target_modes = []
                    for mode in SwarmExecutionMode:
                        similarity = self.mode_similarities.get((source_mode, mode), 0.0)
                        if similarity > 0.5 and mode != source_mode:
                            target_modes.append(mode)

                    if target_modes:
                        knowledge = LearnedKnowledge(
                            knowledge_type=KnowledgeType.EXECUTION_PATTERN,
                            pattern={
                                "source_mode": source_mode.value,
                                "common_patterns": common_patterns,
                                "transfer_confidence": min(
                                    [exp.confidence for exp in successful_experiences]
                                ),
                            },
                            conditions=self._merge_conditions(
                                [exp.problem_context for exp in successful_experiences]
                            ),
                            expected_outcome={
                                "avg_quality": np.mean(
                                    [exp.quality_score for exp in successful_experiences]
                                )
                            },
                            confidence=0.7,
                            applicable_modes=target_modes,
                            problem_types=list(
                                {exp.problem_type for exp in successful_experiences}
                            ),
                        )
                        learned_knowledge.append(knowledge)

        return learned_knowledge

    def _extract_common_patterns(self, experiences: list[LearningExperience]) -> dict[str, Any]:
        """Extract common patterns from successful experiences"""
        patterns = {}

        # Find common agent count
        agent_counts = [len(exp.agent_states) for exp in experiences]
        if len(set(agent_counts)) == 1:
            patterns["optimal_agent_count"] = agent_counts[0]

        # Find common quality thresholds
        quality_scores = [exp.quality_score for exp in experiences]
        patterns["min_quality_threshold"] = min(quality_scores)
        patterns["avg_quality"] = np.mean(quality_scores)

        return patterns

    def _merge_conditions(self, conditions_list: list[dict[str, Any]]) -> dict[str, Any]:
        """Merge conditions from multiple experiences"""
        merged = {}

        # Find common conditions
        if conditions_list:
            common_keys = set(conditions_list[0].keys())
            for conditions in conditions_list[1:]:
                common_keys &= set(conditions.keys())

            for key in common_keys:
                values = [conditions[key] for conditions in conditions_list]
                if len(set(values)) == 1:
                    merged[key] = values[0]

        return merged


# =============================================================================
# CROSS-AGENT KNOWLEDGE DISTILLATION
# =============================================================================


class CrossAgentKnowledgeDistiller:
    """Distill knowledge between agents within a swarm"""

    def __init__(self):
        self.agent_knowledge_maps: dict[str, dict[str, Any]] = defaultdict(dict)
        self.distillation_history: list[dict[str, Any]] = []

    async def distill_knowledge(
        self,
        teacher_agents: list[str],
        student_agents: list[str],
        experiences: list[LearningExperience],
    ) -> dict[str, LearnedKnowledge]:
        """Distill knowledge from teacher agents to student agents"""
        with tracer.start_span("knowledge_distillation", kind=SpanKind.INTERNAL) as span:
            span.set_attribute("teacher_count", len(teacher_agents))
            span.set_attribute("student_count", len(student_agents))

            distilled_knowledge = {}

            # Extract knowledge from teacher experiences
            teacher_patterns = self._extract_teacher_patterns(experiences, teacher_agents)

            # Create distilled knowledge for each student
            for student_agent in student_agents:
                student_knowledge = self._create_student_knowledge(
                    student_agent, teacher_patterns, experiences
                )

                if student_knowledge:
                    distilled_knowledge[student_agent] = student_knowledge

            # Record distillation event
            self.distillation_history.append(
                {
                    "timestamp": datetime.now(timezone.utc),
                    "teachers": teacher_agents,
                    "students": student_agents,
                    "knowledge_transferred": len(distilled_knowledge),
                }
            )

            logger.info(
                f"🧠 Distilled knowledge from {len(teacher_agents)} teachers to {len(student_agents)} students"
            )

            return distilled_knowledge

    def _extract_teacher_patterns(
        self, experiences: list[LearningExperience], teacher_agents: list[str]
    ) -> dict[str, Any]:
        """Extract successful patterns from teacher agents"""
        patterns = {
            "successful_strategies": [],
            "optimal_configurations": {},
            "performance_benchmarks": {},
        }

        # Filter experiences involving teacher agents
        teacher_experiences = [
            exp
            for exp in experiences
            if any(agent in exp.agent_states for agent in teacher_agents) and exp.success
        ]

        if teacher_experiences:
            # Extract successful strategies
            for exp in teacher_experiences:
                strategy = {
                    "execution_mode": exp.execution_mode.value,
                    "agent_configuration": exp.agent_states,
                    "problem_approach": exp.solution,
                    "quality_achieved": exp.quality_score,
                }
                patterns["successful_strategies"].append(strategy)

            # Find optimal configurations
            mode_performances = defaultdict(list)
            for exp in teacher_experiences:
                mode_performances[exp.execution_mode].append(exp.quality_score)

            patterns["optimal_configurations"] = {
                mode.value: np.mean(scores) for mode, scores in mode_performances.items()
            }

        return patterns

    def _create_student_knowledge(
        self,
        student_agent: str,
        teacher_patterns: dict[str, Any],
        experiences: list[LearningExperience],
    ) -> Optional[LearnedKnowledge]:
        """Create knowledge appropriate for student agent"""
        if not teacher_patterns["successful_strategies"]:
            return None

        # Find most applicable strategy for this student
        best_strategy = max(
            teacher_patterns["successful_strategies"], key=lambda s: s["quality_achieved"]
        )

        return LearnedKnowledge(
            knowledge_type=KnowledgeType.AGENT_COLLABORATION,
            pattern={
                "distilled_strategy": best_strategy,
                "teacher_benchmarks": teacher_patterns["performance_benchmarks"],
                "distillation_confidence": 0.8,
            },
            conditions={"min_quality_required": best_strategy["quality_achieved"] * 0.9},
            expected_outcome={"quality_improvement": 0.2, "success_probability": 0.8},
            confidence=0.8,
            applicable_modes=[SwarmExecutionMode(best_strategy["execution_mode"])],
            problem_types=[],  # Will be filled based on context
            source_experiences=[exp.id for exp in experiences[:5]],
        )


# =============================================================================
# MAIN ADAPTIVE LEARNING SYSTEM
# =============================================================================


class AdaptiveLearningSystem:
    """
    Main adaptive learning system that integrates with existing swarm infrastructure
    """

    def __init__(
        self,
        memory_store: UnifiedMemoryStore,
        message_bus: MessageBus,
        learning_rate: float = 0.1,
        experience_buffer_size: int = 10000,
    ):
        self.memory_store = memory_store
        self.message_bus = message_bus
        self.learning_rate = learning_rate

        # Core components
        self.experience_buffer = ExperienceReplayBuffer(max_size=experience_buffer_size)
        self.knowledge_base: dict[str, LearnedKnowledge] = {}
        self.learning_algorithms: dict[LearningType, LearningAlgorithm] = {}
        self.knowledge_distiller = CrossAgentKnowledgeDistiller()

        # Performance tracking
        self.learning_metrics = {
            "experiences_collected": 0,
            "knowledge_created": 0,
            "knowledge_applied": 0,
            "learning_effectiveness": 0.0,
            "last_learning_time": None,
        }

        # Real-time learning queue
        self.learning_queue: asyncio.Queue = asyncio.Queue()
        self.learning_task: Optional[asyncio.Task] = None

        self._initialize_algorithms()
        logger.info("🧠 AdaptiveLearningSystem initialized")

    def _initialize_algorithms(self):
        """Initialize learning algorithms"""
        self.learning_algorithms[LearningType.REINFORCEMENT] = ReinforcementLearningAlgorithm(
            learning_rate=self.learning_rate
        )
        self.learning_algorithms[LearningType.TRANSFER] = TransferLearningAlgorithm()

    async def start_learning_loop(self):
        """Start the asynchronous learning loop"""
        if self.learning_task is None or self.learning_task.done():
            self.learning_task = asyncio.create_task(self._learning_loop())
            logger.info("🔄 Learning loop started")

    async def stop_learning_loop(self):
        """Stop the learning loop"""
        if self.learning_task and not self.learning_task.done():
            self.learning_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.learning_task
            logger.info("⏹️ Learning loop stopped")

    async def _learning_loop(self):
        """Main learning loop that processes experiences"""
        while True:
            try:
                # Get experience from queue (with timeout to prevent blocking)
                experience = await asyncio.wait_for(self.learning_queue.get(), timeout=1.0)

                # Process learning from experience
                await self._process_learning_experience(experience)

                # Mark task done
                self.learning_queue.task_done()

            except asyncio.TimeoutError:
                # No experience to process, continue loop
                continue
            except Exception as e:
                logger.error(f"Error in learning loop: {e}")
                await asyncio.sleep(0.1)

    async def capture_experience(
        self,
        swarm_id: str,
        execution_mode: SwarmExecutionMode,
        problem_context: dict[str, Any],
        execution_context: dict[str, Any],
        agent_states: dict[str, Any],
        solution: dict[str, Any],
        metrics: SwarmMetrics,
    ) -> str:
        """Capture a learning experience during swarm execution"""
        with tracer.start_span("capture_experience", kind=SpanKind.INTERNAL) as span:
            experience = LearningExperience(
                swarm_id=swarm_id,
                execution_mode=execution_mode,
                problem_type=problem_context.get("type", "general"),
                problem_context=problem_context,
                execution_context=execution_context,
                agent_states=agent_states,
                solution=solution,
                success=solution.get("success", False),
                performance_metrics={
                    "response_time": metrics.avg_response_time,
                    "agent_utilization": sum(metrics.agent_utilization.values())
                    / max(len(metrics.agent_utilization), 1),
                    "quality_score": solution.get("quality_score", 0.0),
                },
                quality_score=solution.get("quality_score", 0.0),
                confidence=solution.get("confidence", 0.0),
            )

            # Add to experience buffer
            self.experience_buffer.add_experience(experience)
            self.learning_metrics["experiences_collected"] += 1

            # Store in memory for persistence
            await self.memory_store.store_memory(
                content=f"Learning experience: {experience.problem_type}",
                metadata={
                    "type": "learning_experience",
                    "experience_id": experience.id,
                    "swarm_id": swarm_id,
                    "execution_mode": execution_mode.value,
                    "success": experience.success,
                    "quality_score": experience.quality_score,
                },
            )

            # Queue for asynchronous learning
            await self.learning_queue.put(experience)

            span.set_attribute("experience.id", experience.id)
            span.set_attribute("experience.success", experience.success)
            span.set_attribute("experience.quality_score", experience.quality_score)

            logger.debug(f"📊 Captured experience: {experience.id} (success: {experience.success})")

            return experience.id

    async def _process_learning_experience(self, experience: LearningExperience):
        """Process a single learning experience"""
        learning_start = time.time()

        try:
            # Apply different learning algorithms
            learned_knowledge = []

            # Reinforcement learning
            if LearningType.REINFORCEMENT in self.learning_algorithms:
                rl_knowledge = await self.learning_algorithms[
                    LearningType.REINFORCEMENT
                ].learn_from_experience(experience, {"learning_type": "reinforcement"})
                if rl_knowledge:
                    learned_knowledge.append(rl_knowledge)

            # Transfer learning (if we have similar experiences)
            similar_experiences = self.experience_buffer.get_similar_experiences(
                experience, limit=5
            )
            if len(similar_experiences) >= 2:
                if LearningType.TRANSFER in self.learning_algorithms:
                    transfer_knowledge = await self.learning_algorithms[
                        LearningType.TRANSFER
                    ].learn_from_experience(
                        experience, {"similar_experiences": similar_experiences}
                    )
                    if transfer_knowledge:
                        learned_knowledge.append(transfer_knowledge)

            # Store learned knowledge
            for knowledge in learned_knowledge:
                self.knowledge_base[knowledge.id] = knowledge
                self.learning_metrics["knowledge_created"] += 1

                # Persist to memory
                await self.memory_store.store_memory(
                    content=f"Learned knowledge: {knowledge.knowledge_type.value}",
                    metadata={
                        "type": "learned_knowledge",
                        "knowledge_id": knowledge.id,
                        "knowledge_type": knowledge.knowledge_type.value,
                        "confidence": knowledge.confidence,
                        "applicable_modes": [mode.value for mode in knowledge.applicable_modes],
                    },
                )

            # Update metrics
            learning_time = time.time() - learning_start
            self.learning_metrics["last_learning_time"] = learning_time

            if learned_knowledge:
                logger.debug(
                    f"🎓 Learned {len(learned_knowledge)} new knowledge items in {learning_time:.3f}s"
                )

        except Exception as e:
            logger.error(f"Error processing learning experience: {e}")

    async def get_applicable_knowledge(
        self, context: dict[str, Any], limit: int = 5
    ) -> list[LearnedKnowledge]:
        """Get knowledge applicable to current execution context"""
        applicable_knowledge = []

        for knowledge in self.knowledge_base.values():
            is_applicable, score = knowledge.is_applicable(context)
            if is_applicable:
                applicable_knowledge.append((knowledge, score))

        # Sort by applicability score
        applicable_knowledge.sort(key=lambda x: x[1], reverse=True)

        # Return top knowledge items
        return [knowledge for knowledge, _ in applicable_knowledge[:limit]]

    async def apply_knowledge(
        self, knowledge: LearnedKnowledge, execution_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply learned knowledge to current execution"""
        with tracer.start_span("apply_knowledge", kind=SpanKind.INTERNAL) as span:
            span.set_attribute("knowledge.id", knowledge.id)
            span.set_attribute("knowledge.type", knowledge.knowledge_type.value)

            # Update usage statistics
            knowledge.usage_count += 1
            knowledge.last_used = datetime.now(timezone.utc)

            # Apply knowledge-specific logic
            application_result = {
                "knowledge_applied": knowledge.id,
                "confidence": knowledge.confidence,
                "expected_improvement": 0.0,
                "modifications": {},
            }

            if knowledge.knowledge_type == KnowledgeType.EXECUTION_PATTERN:
                # Apply execution pattern knowledge
                pattern = knowledge.pattern
                if "optimal_agent_count" in pattern:
                    application_result["modifications"]["agent_count"] = pattern[
                        "optimal_agent_count"
                    ]
                if "q_value" in pattern:
                    application_result["expected_improvement"] = abs(pattern["q_value"]) / 10.0

            elif knowledge.knowledge_type == KnowledgeType.AGENT_COLLABORATION:
                # Apply collaboration knowledge
                if "distilled_strategy" in knowledge.pattern:
                    strategy = knowledge.pattern["distilled_strategy"]
                    application_result["modifications"].update(strategy)

            # Track application
            self.learning_metrics["knowledge_applied"] += 1

            logger.debug(
                f"🎯 Applied knowledge {knowledge.id} with confidence {knowledge.confidence}"
            )

            return application_result

    async def distill_cross_agent_knowledge(
        self,
        swarm_id: str,
        agent_performance: dict[str, float],
        experiences: list[LearningExperience],
    ) -> dict[str, LearnedKnowledge]:
        """Distill knowledge between high and low performing agents"""
        # Identify teacher and student agents
        performance_threshold = np.median(list(agent_performance.values()))

        teacher_agents = [
            agent for agent, perf in agent_performance.items() if perf > performance_threshold
        ]

        student_agents = [
            agent for agent, perf in agent_performance.items() if perf <= performance_threshold
        ]

        if not teacher_agents or not student_agents:
            return {}

        # Distill knowledge
        distilled_knowledge = await self.knowledge_distiller.distill_knowledge(
            teacher_agents, student_agents, experiences
        )

        # Store distilled knowledge
        for agent, knowledge in distilled_knowledge.items():
            self.knowledge_base[knowledge.id] = knowledge

            # Persist to memory
            await self.memory_store.store_memory(
                content=f"Distilled knowledge for agent {agent}",
                metadata={
                    "type": "distilled_knowledge",
                    "target_agent": agent,
                    "knowledge_id": knowledge.id,
                    "source_swarm": swarm_id,
                },
            )

        logger.info(
            f"🔄 Distilled knowledge from {len(teacher_agents)} teachers to {len(student_agents)} students"
        )

        return distilled_knowledge

    async def get_learning_insights(self) -> dict[str, Any]:
        """Get insights about the learning system's performance"""
        # Calculate effectiveness
        if self.learning_metrics["knowledge_created"] > 0:
            effectiveness = (
                self.learning_metrics["knowledge_applied"]
                / self.learning_metrics["knowledge_created"]
            )
            self.learning_metrics["learning_effectiveness"] = effectiveness

        # Knowledge distribution by type
        knowledge_by_type = defaultdict(int)
        for knowledge in self.knowledge_base.values():
            knowledge_by_type[knowledge.knowledge_type.value] += 1

        # Recent learning activity
        recent_experiences = [
            exp
            for exp in self.experience_buffer.experiences
            if (datetime.now(timezone.utc) - exp.timestamp).total_seconds() < 3600  # Last hour
        ]

        return {
            "metrics": self.learning_metrics,
            "knowledge_base_size": len(self.knowledge_base),
            "experience_buffer_size": len(self.experience_buffer.experiences),
            "knowledge_distribution": dict(knowledge_by_type),
            "recent_activity": {
                "experiences_last_hour": len(recent_experiences),
                "success_rate_last_hour": sum(1 for exp in recent_experiences if exp.success)
                / max(len(recent_experiences), 1),
            },
            "learning_queue_size": self.learning_queue.qsize(),
        }

    async def cleanup(self):
        """Cleanup learning system resources"""
        await self.stop_learning_loop()

        # Save final state to memory
        insights = await self.get_learning_insights()
        await self.memory_store.store_memory(
            content="Learning system final state",
            metadata={"type": "learning_system_state", "final_insights": insights},
        )

        logger.info("🧹 Learning system cleaned up")


# =============================================================================
# LEARNING-ENHANCED SWARM BASE
# =============================================================================


class LearningEnhancedSwarmMixin:
    """
    Mixin class that adds learning capabilities to existing swarm implementations
    Can be mixed with any SwarmBase subclass
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.learning_system: Optional[AdaptiveLearningSystem] = None
        self.learning_enabled = True

    async def initialize_learning(
        self,
        memory_store: UnifiedMemoryStore,
        message_bus: MessageBus,
        learning_config: Optional[dict[str, Any]] = None,
    ):
        """Initialize the learning system"""
        if not self.learning_enabled:
            return

        config = learning_config or {}

        self.learning_system = AdaptiveLearningSystem(
            memory_store=memory_store,
            message_bus=message_bus,
            learning_rate=config.get("learning_rate", 0.1),
            experience_buffer_size=config.get("experience_buffer_size", 10000),
        )

        await self.learning_system.start_learning_loop()
        logger.info(f"🎓 Learning system initialized for swarm {self.config.swarm_id}")

    async def enhanced_solve_problem(self, problem: dict[str, Any]) -> Any:
        """Enhanced problem solving with learning integration"""
        # Get applicable knowledge before execution
        applicable_knowledge = []
        if self.learning_system:
            context = {
                "execution_mode": self.config.execution_mode,
                "problem_type": problem.get("type", "general"),
                "agent_count": len(self.agents),
            }
            applicable_knowledge = await self.learning_system.get_applicable_knowledge(context)

        # Apply pre-execution learning
        execution_modifications = {}
        for knowledge in applicable_knowledge:
            application = await self.learning_system.apply_knowledge(knowledge, context)
            execution_modifications.update(application.get("modifications", {}))

        # Apply modifications to execution
        original_config = self._preserve_config()
        self._apply_execution_modifications(execution_modifications)

        # Execute with original method
        start_time = time.time()
        try:
            result = await super().solve_problem(problem)

            # Capture learning experience
            if self.learning_system:
                execution_time = time.time() - start_time

                await self.learning_system.capture_experience(
                    swarm_id=self.config.swarm_id,
                    execution_mode=self.config.execution_mode,
                    problem_context=problem,
                    execution_context={
                        "agent_count": len(self.agents),
                        "execution_time": execution_time,
                        "applied_knowledge": [k.id for k in applicable_knowledge],
                    },
                    agent_states={agent.__class__.__name__: {} for agent in self.agents},
                    solution=(
                        result.__dict__ if hasattr(result, "__dict__") else {"result": str(result)}
                    ),
                    metrics=self.metrics,
                )

            return result

        finally:
            # Restore original configuration
            self._restore_config(original_config)

    def _preserve_config(self) -> dict[str, Any]:
        """Preserve current configuration"""
        return {
            "agent_count": self.config.agent_count,
            "timeout_per_agent": self.config.timeout_per_agent,
            "quality_threshold": self.config.quality_threshold,
        }

    def _restore_config(self, original_config: dict[str, Any]):
        """Restore original configuration"""
        for key, value in original_config.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def _apply_execution_modifications(self, modifications: dict[str, Any]):
        """Apply learning-suggested modifications to execution"""
        if "agent_count" in modifications:
            # Don't modify actual agent count, but use for planning
            pass

        if "quality_threshold" in modifications:
            self.config.quality_threshold = modifications["quality_threshold"]

        if "timeout_per_agent" in modifications:
            self.config.timeout_per_agent = modifications["timeout_per_agent"]

    async def cleanup_learning(self):
        """Cleanup learning resources"""
        if self.learning_system:
            await self.learning_system.cleanup()


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================


async def create_learning_system(
    memory_store: UnifiedMemoryStore,
    message_bus: MessageBus,
    config: Optional[dict[str, Any]] = None,
) -> AdaptiveLearningSystem:
    """Factory function to create a configured learning system"""
    learning_system = AdaptiveLearningSystem(
        memory_store=memory_store,
        message_bus=message_bus,
        learning_rate=config.get("learning_rate", 0.1) if config else 0.1,
        experience_buffer_size=config.get("experience_buffer_size", 10000) if config else 10000,
    )

    await learning_system.start_learning_loop()

    # Store creation event in memory
    await memory_store.store_memory(
        content="Adaptive Learning System created",
        metadata={
            "type": "learning_system_creation",
            "component": "adaptive_learning",
            "config": config or {},
        },
    )

    return learning_system


# =============================================================================
# LEARNING MIDDLEWARE
# =============================================================================


class LearningMiddleware:
    """Middleware that can be injected into any execution mode"""

    def __init__(self, learning_system: AdaptiveLearningSystem):
        self.learning_system = learning_system

    async def pre_execution(self, context: dict[str, Any]) -> dict[str, Any]:
        """Pre-execution learning enhancement"""
        applicable_knowledge = await self.learning_system.get_applicable_knowledge(context)

        enhancements = {"applicable_knowledge": applicable_knowledge, "learning_suggestions": []}

        for knowledge in applicable_knowledge:
            application = await self.learning_system.apply_knowledge(knowledge, context)
            enhancements["learning_suggestions"].append(application)

        return enhancements

    async def post_execution(
        self, context: dict[str, Any], result: Any, execution_time: float
    ) -> dict[str, Any]:
        """Post-execution learning capture"""
        # This would be called by the swarm after execution
        # to capture the learning experience

        return {"learning_captured": True, "execution_time": execution_time}


if __name__ == "__main__":
    # Example usage
    async def demo():
        from app.memory.unified_memory import get_memory_store
        from app.swarms.communication.message_bus import MessageBus

        # Initialize components
        memory_store = get_memory_store()
        message_bus = MessageBus()

        await message_bus.initialize()

        # Create learning system
        learning_system = await create_learning_system(
            memory_store=memory_store, message_bus=message_bus, config={"learning_rate": 0.15}
        )

        print("🧠 Learning system demo initialized")

        # Simulate learning experience
        await learning_system.capture_experience(
            swarm_id="demo-swarm",
            execution_mode=SwarmExecutionMode.PARALLEL,
            problem_context={"type": "coding", "complexity": "medium"},
            execution_context={"agent_count": 5},
            agent_states={"agent1": {}, "agent2": {}, "agent3": {}, "agent4": {}, "agent5": {}},
            solution={"success": True, "quality_score": 0.85, "confidence": 0.9},
            metrics=SwarmMetrics(),
        )

        print("📊 Captured demo experience")

        # Get insights
        insights = await learning_system.get_learning_insights()
        print(f"🎯 Learning insights: {insights}")

        # Cleanup
        await learning_system.cleanup()
        await message_bus.close()

        print("✅ Demo completed")

    asyncio.run(demo())
