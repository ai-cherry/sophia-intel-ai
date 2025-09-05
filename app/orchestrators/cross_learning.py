"""
Cross-Learning Orchestrator
Facilitates knowledge sharing and collaborative execution between Sophia and Artemis
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from app.core.portkey_manager import TaskType
from app.memory.unified_memory_router import DocChunk, MemoryDomain
from app.orchestrators.unified_base import (
    ExecutionPriority,
    OrchestratorConfig,
    UnifiedBaseOrchestrator,
    UnifiedResult,
    UnifiedTask,
)

logger = logging.getLogger(__name__)


class CollaborationType(Enum):
    """Types of cross-orchestrator collaboration"""

    KNOWLEDGE_SHARING = "knowledge_sharing"
    TASK_HANDOFF = "task_handoff"
    JOINT_EXECUTION = "joint_execution"
    PATTERN_LEARNING = "pattern_learning"
    QUALITY_VALIDATION = "quality_validation"
    CONTEXT_ENRICHMENT = "context_enrichment"


class LearnedPatternType(Enum):
    """Types of learned patterns"""

    SUCCESS_PATTERN = "success_pattern"
    FAILURE_PATTERN = "failure_pattern"
    OPTIMIZATION_PATTERN = "optimization_pattern"
    INTEGRATION_PATTERN = "integration_pattern"
    WORKFLOW_PATTERN = "workflow_pattern"


@dataclass
class CrossDomainKnowledge:
    """Represents knowledge that can be shared across domains"""

    id: str
    source_domain: MemoryDomain
    target_domains: List[MemoryDomain]
    knowledge_type: str
    content: Dict[str, Any]
    confidence: float
    applicability_score: float
    created_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    success_rate: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CollaborationRequest:
    """Request for cross-orchestrator collaboration"""

    id: str
    requesting_domain: MemoryDomain
    target_domain: MemoryDomain
    collaboration_type: CollaborationType
    task_context: Dict[str, Any]
    expected_outcome: str
    priority: ExecutionPriority
    timeout_s: int = 300
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class CollaborationResult:
    """Result of cross-orchestrator collaboration"""

    collaboration_id: str
    success: bool
    shared_knowledge: List[CrossDomainKnowledge]
    enhanced_context: Dict[str, Any]
    recommendations: List[str]
    lessons_learned: List[str]
    performance_metrics: Dict[str, float]
    execution_time_ms: float
    errors: List[str] = field(default_factory=list)


@dataclass
class LearnedPattern:
    """Represents a learned pattern from cross-domain collaboration"""

    id: str
    pattern_type: LearnedPatternType
    domains_involved: List[MemoryDomain]
    trigger_conditions: Dict[str, Any]
    success_indicators: Dict[str, Any]
    actions: List[Dict[str, Any]]
    confidence: float
    usage_count: int = 0
    success_rate: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None


class KnowledgeGraph:
    """
    Represents the knowledge graph connecting insights across domains
    """

    def __init__(self):
        self.nodes = {}  # domain knowledge nodes
        self.edges = {}  # relationships between knowledge
        self.patterns = {}  # learned patterns
        self.similarity_cache = {}  # cached similarity calculations

    def add_knowledge_node(self, knowledge: CrossDomainKnowledge) -> None:
        """Add a knowledge node to the graph"""
        self.nodes[knowledge.id] = knowledge

        # Update relationships with existing nodes
        self._update_relationships(knowledge)

    def _update_relationships(self, new_knowledge: CrossDomainKnowledge) -> None:
        """Update relationships when adding new knowledge"""
        for existing_id, existing_knowledge in self.nodes.items():
            if existing_id != new_knowledge.id:
                similarity = self._calculate_knowledge_similarity(new_knowledge, existing_knowledge)

                if similarity > 0.6:  # Threshold for creating relationship
                    edge_id = f"{new_knowledge.id}:{existing_id}"
                    self.edges[edge_id] = {
                        "similarity": similarity,
                        "relationship_type": self._determine_relationship_type(
                            new_knowledge, existing_knowledge
                        ),
                        "created_at": datetime.now(),
                    }

    def _calculate_knowledge_similarity(
        self, knowledge1: CrossDomainKnowledge, knowledge2: CrossDomainKnowledge
    ) -> float:
        """Calculate similarity between two knowledge pieces"""
        # Simple similarity based on content overlap and metadata

        # Check if already cached
        cache_key = f"{knowledge1.id}:{knowledge2.id}"
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]

        factors = []

        # Content similarity (simplified)
        content1_str = json.dumps(knowledge1.content, sort_keys=True)
        content2_str = json.dumps(knowledge2.content, sort_keys=True)

        # Simple word overlap
        words1 = set(content1_str.lower().split())
        words2 = set(content2_str.lower().split())

        if words1 and words2:
            overlap = len(words1.intersection(words2)) / len(words1.union(words2))
            factors.append(overlap)

        # Knowledge type similarity
        if knowledge1.knowledge_type == knowledge2.knowledge_type:
            factors.append(1.0)
        else:
            factors.append(0.0)

        # Domain compatibility
        if knowledge1.source_domain != knowledge2.source_domain:
            factors.append(0.8)  # Cross-domain knowledge is valuable
        else:
            factors.append(0.5)

        similarity = sum(factors) / len(factors) if factors else 0.0

        # Cache the result
        self.similarity_cache[cache_key] = similarity

        return similarity

    def _determine_relationship_type(
        self, knowledge1: CrossDomainKnowledge, knowledge2: CrossDomainKnowledge
    ) -> str:
        """Determine the type of relationship between knowledge pieces"""
        if knowledge1.source_domain != knowledge2.source_domain:
            return "cross_domain_similarity"
        elif knowledge1.knowledge_type == knowledge2.knowledge_type:
            return "same_type_similarity"
        else:
            return "general_similarity"

    def find_related_knowledge(
        self, knowledge_id: str, max_results: int = 5
    ) -> List[Tuple[CrossDomainKnowledge, float]]:
        """Find knowledge related to a given piece"""
        related = []

        for edge_id, edge_data in self.edges.items():
            if knowledge_id in edge_id:
                other_id = edge_id.replace(f"{knowledge_id}:", "").replace(f":{knowledge_id}", "")

                if other_id in self.nodes:
                    related.append((self.nodes[other_id], edge_data["similarity"]))

        # Sort by similarity and return top results
        related.sort(key=lambda x: x[1], reverse=True)
        return related[:max_results]

    def get_domain_knowledge(self, domain: MemoryDomain) -> List[CrossDomainKnowledge]:
        """Get all knowledge from a specific domain"""
        return [knowledge for knowledge in self.nodes.values() if knowledge.source_domain == domain]

    def get_applicable_knowledge(
        self, target_domain: MemoryDomain, task_context: Dict[str, Any]
    ) -> List[CrossDomainKnowledge]:
        """Get knowledge applicable to a specific domain and context"""
        applicable = []

        for knowledge in self.nodes.values():
            if target_domain in knowledge.target_domains:
                # Calculate applicability score based on context
                applicability = self._calculate_context_applicability(knowledge, task_context)

                if applicability > 0.5:
                    knowledge.applicability_score = applicability
                    applicable.append(knowledge)

        # Sort by applicability score
        applicable.sort(key=lambda x: x.applicability_score, reverse=True)
        return applicable

    def _calculate_context_applicability(
        self, knowledge: CrossDomainKnowledge, task_context: Dict[str, Any]
    ) -> float:
        """Calculate how applicable knowledge is to a specific context"""
        factors = []

        # Check metadata alignment
        knowledge_metadata = knowledge.metadata
        context_keys = set(task_context.keys())
        metadata_keys = set(knowledge_metadata.keys())

        if context_keys and metadata_keys:
            key_overlap = len(context_keys.intersection(metadata_keys)) / len(
                context_keys.union(metadata_keys)
            )
            factors.append(key_overlap)

        # Check success rate
        factors.append(knowledge.success_rate)

        # Check usage frequency (popular knowledge is often good)
        usage_factor = min(1.0, knowledge.usage_count / 10)  # Normalize to 0-1
        factors.append(usage_factor)

        return sum(factors) / len(factors) if factors else 0.0


class PatternLearningEngine:
    """
    Engine for learning patterns from cross-domain collaboration
    """

    def __init__(self):
        self.patterns = {}  # id -> LearnedPattern
        self.pattern_matcher = PatternMatcher()
        self.success_threshold = 0.7

    async def learn_from_collaboration(
        self, collaboration_result: CollaborationResult, task_context: Dict[str, Any]
    ) -> List[LearnedPattern]:
        """Learn patterns from collaboration results"""
        learned_patterns = []

        if collaboration_result.success:
            # Learn success patterns
            success_pattern = await self._extract_success_pattern(
                collaboration_result, task_context
            )
            if success_pattern:
                learned_patterns.append(success_pattern)

            # Learn optimization patterns
            optimization_pattern = await self._extract_optimization_pattern(
                collaboration_result, task_context
            )
            if optimization_pattern:
                learned_patterns.append(optimization_pattern)
        else:
            # Learn failure patterns to avoid
            failure_pattern = await self._extract_failure_pattern(
                collaboration_result, task_context
            )
            if failure_pattern:
                learned_patterns.append(failure_pattern)

        # Store patterns
        for pattern in learned_patterns:
            self.patterns[pattern.id] = pattern

        return learned_patterns

    async def _extract_success_pattern(
        self, result: CollaborationResult, context: Dict[str, Any]
    ) -> Optional[LearnedPattern]:
        """Extract successful collaboration pattern"""
        if not result.success:
            return None

        pattern_id = f"success_{datetime.now().timestamp()}"

        # Extract trigger conditions from context
        trigger_conditions = {
            "task_type": context.get("task_type"),
            "domains_involved": context.get("domains_involved", []),
            "collaboration_type": context.get("collaboration_type"),
            "complexity_level": context.get("complexity_level", "medium"),
        }

        # Extract success indicators from result
        success_indicators = {
            "execution_time_threshold": result.execution_time_ms,
            "knowledge_sharing_count": len(result.shared_knowledge),
            "recommendations_generated": len(result.recommendations),
        }

        # Extract actions that led to success
        actions = [
            {"type": "knowledge_sharing", "count": len(result.shared_knowledge)},
            {"type": "context_enhancement", "applied": bool(result.enhanced_context)},
            {"type": "cross_validation", "performed": True},
        ]

        return LearnedPattern(
            id=pattern_id,
            pattern_type=LearnedPatternType.SUCCESS_PATTERN,
            domains_involved=context.get("domains_involved", []),
            trigger_conditions=trigger_conditions,
            success_indicators=success_indicators,
            actions=actions,
            confidence=0.8,  # Initial confidence
        )

    async def _extract_optimization_pattern(
        self, result: CollaborationResult, context: Dict[str, Any]
    ) -> Optional[LearnedPattern]:
        """Extract optimization patterns from successful collaboration"""
        if not result.success or result.execution_time_ms > 5000:  # Skip slow executions
            return None

        pattern_id = f"optimization_{datetime.now().timestamp()}"

        # Look for optimization indicators
        performance_metrics = result.performance_metrics

        if performance_metrics.get("efficiency_score", 0) > 0.8:
            return LearnedPattern(
                id=pattern_id,
                pattern_type=LearnedPatternType.OPTIMIZATION_PATTERN,
                domains_involved=context.get("domains_involved", []),
                trigger_conditions={
                    "performance_requirements": "high",
                    "resource_constraints": "limited",
                },
                success_indicators={
                    "efficiency_threshold": 0.8,
                    "execution_time_max": 5000,
                },
                actions=[
                    {"type": "parallel_execution", "enabled": True},
                    {"type": "caching_strategy", "aggressive": True},
                    {"type": "knowledge_pruning", "applied": True},
                ],
                confidence=0.7,
            )

        return None

    async def _extract_failure_pattern(
        self, result: CollaborationResult, context: Dict[str, Any]
    ) -> Optional[LearnedPattern]:
        """Extract failure patterns to avoid"""
        if result.success:
            return None

        pattern_id = f"failure_{datetime.now().timestamp()}"

        return LearnedPattern(
            id=pattern_id,
            pattern_type=LearnedPatternType.FAILURE_PATTERN,
            domains_involved=context.get("domains_involved", []),
            trigger_conditions={
                "error_indicators": result.errors[:3],  # Top errors
                "context_similarity": context,
            },
            success_indicators={
                "avoid_conditions": True,
            },
            actions=[
                {"type": "error_prevention", "conditions": result.errors},
                {"type": "alternative_approach", "required": True},
            ],
            confidence=0.9,  # High confidence in failure patterns
        )

    def find_applicable_patterns(
        self, context: Dict[str, Any], domains_involved: List[MemoryDomain]
    ) -> List[LearnedPattern]:
        """Find patterns applicable to current context"""
        applicable = []

        for pattern in self.patterns.values():
            if self._is_pattern_applicable(pattern, context, domains_involved):
                applicable.append(pattern)

        # Sort by confidence and success rate
        applicable.sort(key=lambda p: (p.confidence * p.success_rate), reverse=True)
        return applicable

    def _is_pattern_applicable(
        self, pattern: LearnedPattern, context: Dict[str, Any], domains: List[MemoryDomain]
    ) -> bool:
        """Check if a pattern is applicable to the current context"""
        # Check domain compatibility
        if not any(domain in pattern.domains_involved for domain in domains):
            return False

        # Check trigger conditions
        trigger_match_score = self.pattern_matcher.calculate_trigger_match(
            pattern.trigger_conditions, context
        )

        return trigger_match_score > 0.6

    def update_pattern_success(self, pattern_id: str, success: bool) -> None:
        """Update pattern success rate based on usage outcome"""
        if pattern_id in self.patterns:
            pattern = self.patterns[pattern_id]
            pattern.usage_count += 1
            pattern.last_used = datetime.now()

            # Update success rate using weighted average
            if pattern.usage_count == 1:
                pattern.success_rate = 1.0 if success else 0.0
            else:
                current_successes = pattern.success_rate * (pattern.usage_count - 1)
                new_successes = current_successes + (1 if success else 0)
                pattern.success_rate = new_successes / pattern.usage_count


class PatternMatcher:
    """Utility class for pattern matching"""

    def calculate_trigger_match(
        self, trigger_conditions: Dict[str, Any], context: Dict[str, Any]
    ) -> float:
        """Calculate how well trigger conditions match the context"""
        if not trigger_conditions or not context:
            return 0.0

        matches = 0
        total_conditions = len(trigger_conditions)

        for key, expected_value in trigger_conditions.items():
            if key in context:
                actual_value = context[key]

                if isinstance(expected_value, str) and isinstance(actual_value, str):
                    if expected_value.lower() == actual_value.lower():
                        matches += 1
                elif expected_value == actual_value:
                    matches += 1
                elif isinstance(expected_value, list) and isinstance(actual_value, list):
                    # Check list overlap
                    overlap = len(set(expected_value).intersection(set(actual_value)))
                    if overlap > 0:
                        matches += overlap / len(set(expected_value).union(set(actual_value)))

        return matches / total_conditions if total_conditions > 0 else 0.0


class CrossLearningOrchestrator(UnifiedBaseOrchestrator):
    """
    Cross-learning orchestrator that facilitates knowledge sharing and collaboration
    between Sophia (business intelligence) and Artemis (code excellence) domains.
    """

    def __init__(self):
        """Initialize cross-learning orchestrator"""
        config = OrchestratorConfig(
            domain=MemoryDomain.SHARED,
            name="Cross-Learning Collaboration Engine",
            description="Facilitates knowledge sharing and collaboration between orchestrators",
            max_concurrent_tasks=15,
            default_timeout_s=300,
            enable_caching=True,
            enable_monitoring=True,
            enable_memory=True,
            enable_persona=False,
            enable_cross_learning=True,
            budget_limits={
                "hourly_cost_usd": 25.0,
                "daily_cost_usd": 200.0,
                "monthly_cost_usd": 5000.0,
            },
            data_sources=["sophia_knowledge", "artemis_knowledge", "shared_patterns"],
            quality_thresholds={"confidence_min": 0.6, "citation_min": 1, "source_diversity": 0.5},
        )

        super().__init__(config)

        # Cross-learning components
        self.knowledge_graph = KnowledgeGraph()
        self.pattern_engine = PatternLearningEngine()

        # Collaboration tracking
        self.active_collaborations = {}  # id -> CollaborationRequest
        self.collaboration_history = []

        # Knowledge sharing metrics
        self.sharing_metrics = {
            "total_knowledge_shared": 0,
            "successful_collaborations": 0,
            "failed_collaborations": 0,
            "patterns_learned": 0,
            "cross_domain_successes": 0,
        }

        # Connected orchestrators (would be set by the system)
        self.connected_orchestrators = {}  # domain -> orchestrator_instance

        logger.info("Cross-Learning Orchestrator initialized")

    def register_orchestrator(
        self, domain: MemoryDomain, orchestrator: UnifiedBaseOrchestrator
    ) -> None:
        """Register an orchestrator for collaboration"""
        self.connected_orchestrators[domain] = orchestrator
        logger.info(f"Registered {domain.value} orchestrator for cross-learning")

    async def _execute_core(self, task: UnifiedTask, routing: Any) -> UnifiedResult:
        """
        Execute cross-learning task

        Args:
            task: Task to execute
            routing: Model routing decision

        Returns:
            Execution result
        """
        result = UnifiedResult(success=False, content=None)

        try:
            # Determine collaboration type from task
            collaboration_type = self._determine_collaboration_type(task)

            # Execute based on collaboration type
            if collaboration_type == CollaborationType.KNOWLEDGE_SHARING:
                result = await self._facilitate_knowledge_sharing(task, routing)
            elif collaboration_type == CollaborationType.TASK_HANDOFF:
                result = await self._facilitate_task_handoff(task, routing)
            elif collaboration_type == CollaborationType.JOINT_EXECUTION:
                result = await self._facilitate_joint_execution(task, routing)
            elif collaboration_type == CollaborationType.PATTERN_LEARNING:
                result = await self._facilitate_pattern_learning(task, routing)
            else:
                result = await self._facilitate_general_collaboration(task, routing)

            # Learn from the collaboration
            await self._learn_from_collaboration(task, result)

        except Exception as e:
            logger.error(f"Cross-learning execution failed: {e}")
            result.errors.append(str(e))

        return result

    def _determine_collaboration_type(self, task: UnifiedTask) -> CollaborationType:
        """Determine the type of collaboration needed"""
        content_lower = task.content.lower()

        if any(keyword in content_lower for keyword in ["share", "knowledge", "learn", "pattern"]):
            return CollaborationType.KNOWLEDGE_SHARING
        elif any(keyword in content_lower for keyword in ["handoff", "transfer", "delegate"]):
            return CollaborationType.TASK_HANDOFF
        elif any(
            keyword in content_lower for keyword in ["together", "collaborate", "joint", "combine"]
        ):
            return CollaborationType.JOINT_EXECUTION
        elif any(keyword in content_lower for keyword in ["pattern", "learn", "optimize"]):
            return CollaborationType.PATTERN_LEARNING
        else:
            return CollaborationType.CONTEXT_ENRICHMENT

    async def _facilitate_knowledge_sharing(self, task: UnifiedTask, routing: Any) -> UnifiedResult:
        """Facilitate knowledge sharing between domains"""
        result = UnifiedResult(success=False, content={})

        try:
            # Extract source and target domains from task
            source_domain, target_domain = self._extract_domains_from_task(task)

            # Find applicable knowledge from source domain
            applicable_knowledge = self.knowledge_graph.get_applicable_knowledge(
                target_domain, task.metadata
            )

            # Share knowledge with target domain
            shared_knowledge = []
            for knowledge in applicable_knowledge[:5]:  # Limit to top 5
                # Update usage statistics
                knowledge.usage_count += 1
                shared_knowledge.append(knowledge)

            # Create enhanced context for target domain
            enhanced_context = await self._create_enhanced_context(shared_knowledge, task.metadata)

            # Update sharing metrics
            self.sharing_metrics["total_knowledge_shared"] += len(shared_knowledge)

            result.success = True
            result.content = {
                "shared_knowledge": shared_knowledge,
                "enhanced_context": enhanced_context,
                "knowledge_count": len(shared_knowledge),
                "applicability_scores": [k.applicability_score for k in shared_knowledge],
            }
            result.confidence = 0.8

        except Exception as e:
            result.errors.append(f"Knowledge sharing failed: {e}")

        return result

    async def _facilitate_task_handoff(self, task: UnifiedTask, routing: Any) -> UnifiedResult:
        """Facilitate task handoff between orchestrators"""
        result = UnifiedResult(success=False, content={})

        try:
            # Determine target orchestrator
            target_domain = self._determine_handoff_target(task)

            if target_domain not in self.connected_orchestrators:
                raise ValueError(f"Target orchestrator {target_domain.value} not available")

            target_orchestrator = self.connected_orchestrators[target_domain]

            # Prepare task for handoff with enhanced context
            enhanced_task = await self._prepare_task_for_handoff(task, target_domain)

            # Execute task in target orchestrator
            handoff_result = await target_orchestrator.execute(enhanced_task)

            # Process handoff result
            processed_result = await self._process_handoff_result(handoff_result, task)

            result.success = handoff_result.success
            result.content = {
                "handoff_target": target_domain.value,
                "original_task": task.id,
                "enhanced_task": enhanced_task.id,
                "result": processed_result,
            }
            result.confidence = handoff_result.confidence

        except Exception as e:
            result.errors.append(f"Task handoff failed: {e}")

        return result

    async def _facilitate_joint_execution(self, task: UnifiedTask, routing: Any) -> UnifiedResult:
        """Facilitate joint execution across multiple orchestrators"""
        result = UnifiedResult(success=False, content={})

        try:
            # Determine participating orchestrators
            participating_domains = self._determine_joint_execution_domains(task)

            # Create sub-tasks for each domain
            sub_tasks = await self._create_joint_sub_tasks(task, participating_domains)

            # Execute sub-tasks in parallel
            sub_results = await asyncio.gather(
                *[
                    self.connected_orchestrators[domain].execute(sub_task)
                    for domain, sub_task in sub_tasks.items()
                    if domain in self.connected_orchestrators
                ],
                return_exceptions=True,
            )

            # Synthesize results
            synthesized_result = await self._synthesize_joint_results(
                dict(zip(participating_domains, sub_results)), task
            )

            result.success = all(r.success for r in sub_results if isinstance(r, UnifiedResult))
            result.content = {
                "participating_domains": [d.value for d in participating_domains],
                "sub_results": {
                    domain.value: r
                    for domain, r in zip(participating_domains, sub_results)
                    if isinstance(r, UnifiedResult)
                },
                "synthesized_result": synthesized_result,
            }

        except Exception as e:
            result.errors.append(f"Joint execution failed: {e}")

        return result

    async def _facilitate_pattern_learning(self, task: UnifiedTask, routing: Any) -> UnifiedResult:
        """Facilitate pattern learning from cross-domain interactions"""
        result = UnifiedResult(success=False, content={})

        try:
            # Analyze recent collaboration history
            recent_collaborations = self._get_recent_collaborations()

            # Extract patterns from successful collaborations
            learned_patterns = []
            for collaboration in recent_collaborations:
                if collaboration.success:
                    patterns = await self.pattern_engine.learn_from_collaboration(
                        collaboration, task.metadata
                    )
                    learned_patterns.extend(patterns)

            # Update pattern library
            for pattern in learned_patterns:
                self.pattern_engine.patterns[pattern.id] = pattern

            # Generate insights about learned patterns
            pattern_insights = await self._generate_pattern_insights(learned_patterns)

            # Update metrics
            self.sharing_metrics["patterns_learned"] += len(learned_patterns)

            result.success = True
            result.content = {
                "patterns_learned": len(learned_patterns),
                "pattern_types": [p.pattern_type.value for p in learned_patterns],
                "pattern_insights": pattern_insights,
                "total_patterns": len(self.pattern_engine.patterns),
            }

        except Exception as e:
            result.errors.append(f"Pattern learning failed: {e}")

        return result

    async def _facilitate_general_collaboration(
        self, task: UnifiedTask, routing: Any
    ) -> UnifiedResult:
        """Facilitate general cross-domain collaboration"""
        result = UnifiedResult(success=False, content={})

        try:
            # Use LLM to understand collaboration requirements
            messages = self._prepare_collaboration_messages(task)

            response = await self.portkey.execute_with_fallback(
                task_type=TaskType.ORCHESTRATION,
                messages=messages,
                max_tokens=task.budget.get("tokens", 3000),
                temperature=0.3,
            )

            # Process LLM response to determine collaboration strategy
            collaboration_strategy = await self._process_collaboration_response(response, task)

            # Execute collaboration strategy
            strategy_result = await self._execute_collaboration_strategy(
                collaboration_strategy, task
            )

            result.success = strategy_result.get("success", False)
            result.content = {
                "collaboration_strategy": collaboration_strategy,
                "strategy_result": strategy_result,
            }

        except Exception as e:
            result.errors.append(f"General collaboration failed: {e}")

        return result

    # Helper methods for collaboration facilitation

    def _extract_domains_from_task(self, task: UnifiedTask) -> Tuple[MemoryDomain, MemoryDomain]:
        """Extract source and target domains from task metadata"""
        source_domain = task.metadata.get("source_domain", MemoryDomain.SHARED)
        target_domain = task.metadata.get("target_domain", MemoryDomain.SHARED)

        # Convert strings to MemoryDomain if needed
        if isinstance(source_domain, str):
            source_domain = MemoryDomain(source_domain)
        if isinstance(target_domain, str):
            target_domain = MemoryDomain(target_domain)

        return source_domain, target_domain

    async def _create_enhanced_context(
        self, shared_knowledge: List[CrossDomainKnowledge], task_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create enhanced context from shared knowledge"""
        enhanced_context = {
            "shared_insights": [],
            "cross_domain_patterns": [],
            "recommended_approaches": [],
            "potential_pitfalls": [],
        }

        for knowledge in shared_knowledge:
            enhanced_context["shared_insights"].append(
                {
                    "domain": knowledge.source_domain.value,
                    "type": knowledge.knowledge_type,
                    "content": knowledge.content,
                    "confidence": knowledge.confidence,
                }
            )

            # Extract patterns if available
            if knowledge.knowledge_type == "pattern":
                enhanced_context["cross_domain_patterns"].append(knowledge.content)
            elif knowledge.knowledge_type == "recommendation":
                enhanced_context["recommended_approaches"].append(knowledge.content)
            elif knowledge.knowledge_type == "warning" or knowledge.knowledge_type == "failure":
                enhanced_context["potential_pitfalls"].append(knowledge.content)

        return enhanced_context

    def _determine_handoff_target(self, task: UnifiedTask) -> MemoryDomain:
        """Determine target domain for task handoff"""
        content_lower = task.content.lower()

        # Business intelligence indicators
        if any(
            keyword in content_lower
            for keyword in [
                "business",
                "revenue",
                "sales",
                "customer",
                "market",
                "analytics",
                "dashboard",
            ]
        ):
            return MemoryDomain.SOPHIA

        # Code excellence indicators
        elif any(
            keyword in content_lower
            for keyword in ["code", "function", "class", "test", "refactor", "debug", "optimize"]
        ):
            return MemoryDomain.ARTEMIS

        # Default based on task metadata
        else:
            return task.metadata.get("preferred_domain", MemoryDomain.SHARED)

    async def _prepare_task_for_handoff(
        self, original_task: UnifiedTask, target_domain: MemoryDomain
    ) -> UnifiedTask:
        """Prepare task for handoff with enhanced context"""
        # Get relevant knowledge for target domain
        relevant_knowledge = self.knowledge_graph.get_applicable_knowledge(
            target_domain, original_task.metadata
        )

        # Create enhanced task
        enhanced_task = UnifiedTask(
            id=f"handoff_{original_task.id}_{datetime.now().timestamp()}",
            type=original_task.type,
            content=original_task.content,
            priority=original_task.priority,
            metadata={
                **original_task.metadata,
                "original_task_id": original_task.id,
                "handoff_source": "cross_learning",
                "relevant_knowledge": [k.__dict__ for k in relevant_knowledge[:3]],
                "cross_domain_context": True,
            },
            tags=original_task.tags + ["cross_learning", "handoff"],
            budget=original_task.budget,
        )

        return enhanced_task

    async def _process_handoff_result(
        self, handoff_result: UnifiedResult, original_task: UnifiedTask
    ) -> Dict[str, Any]:
        """Process result from handoff execution"""
        # Create knowledge from successful handoff
        if handoff_result.success:
            knowledge = CrossDomainKnowledge(
                id=f"handoff_knowledge_{datetime.now().timestamp()}",
                source_domain=MemoryDomain.SHARED,
                target_domains=[MemoryDomain.SOPHIA, MemoryDomain.ARTEMIS],
                knowledge_type="handoff_success",
                content={
                    "original_task": original_task.content,
                    "handoff_approach": "cross_learning_facilitated",
                    "success_factors": handoff_result.metadata,
                },
                confidence=handoff_result.confidence,
                applicability_score=0.8,
                metadata={
                    "task_type": original_task.type.value,
                    "execution_time": handoff_result.execution_time_ms,
                },
            )

            # Add to knowledge graph
            self.knowledge_graph.add_knowledge_node(knowledge)

        return {
            "success": handoff_result.success,
            "confidence": handoff_result.confidence,
            "insights": handoff_result.insights,
            "recommendations": handoff_result.recommendations,
        }

    def _determine_joint_execution_domains(self, task: UnifiedTask) -> List[MemoryDomain]:
        """Determine which domains should participate in joint execution"""
        content_lower = task.content.lower()
        participating_domains = []

        # Check for business intelligence needs
        if any(
            keyword in content_lower
            for keyword in ["business", "analytics", "customer", "revenue", "market"]
        ):
            participating_domains.append(MemoryDomain.SOPHIA)

        # Check for code excellence needs
        if any(
            keyword in content_lower
            for keyword in ["code", "development", "technical", "implementation", "architecture"]
        ):
            participating_domains.append(MemoryDomain.ARTEMIS)

        # Always include shared domain for coordination
        if MemoryDomain.SHARED not in participating_domains:
            participating_domains.append(MemoryDomain.SHARED)

        return participating_domains

    async def _create_joint_sub_tasks(
        self, main_task: UnifiedTask, domains: List[MemoryDomain]
    ) -> Dict[MemoryDomain, UnifiedTask]:
        """Create sub-tasks for joint execution"""
        sub_tasks = {}

        for domain in domains:
            if domain == MemoryDomain.SHARED:
                continue  # Skip shared domain for sub-task creation

            # Create domain-specific sub-task
            sub_task = UnifiedTask(
                id=f"joint_{domain.value}_{main_task.id}_{datetime.now().timestamp()}",
                type=main_task.type,
                content=self._adapt_task_content_for_domain(main_task.content, domain),
                priority=main_task.priority,
                metadata={
                    **main_task.metadata,
                    "main_task_id": main_task.id,
                    "execution_mode": "joint",
                    "coordinating_domain": MemoryDomain.SHARED.value,
                },
                tags=main_task.tags + ["joint_execution", domain.value],
                budget={
                    "cost_usd": main_task.budget["cost_usd"] / len(domains),
                    "tokens": main_task.budget["tokens"] // len(domains),
                },
            )

            sub_tasks[domain] = sub_task

        return sub_tasks

    def _adapt_task_content_for_domain(self, content: str, domain: MemoryDomain) -> str:
        """Adapt task content for specific domain"""
        if domain == MemoryDomain.SOPHIA:
            return f"From a business intelligence perspective: {content}"
        elif domain == MemoryDomain.ARTEMIS:
            return f"From a code excellence perspective: {content}"
        else:
            return content

    async def _synthesize_joint_results(
        self, sub_results: Dict[MemoryDomain, UnifiedResult], main_task: UnifiedTask
    ) -> Dict[str, Any]:
        """Synthesize results from joint execution"""
        synthesis = {
            "combined_insights": [],
            "cross_domain_recommendations": [],
            "integrated_approach": "",
            "confidence_aggregate": 0.0,
        }

        successful_results = {
            domain: result
            for domain, result in sub_results.items()
            if isinstance(result, UnifiedResult) and result.success
        }

        # Combine insights
        for domain, result in successful_results.items():
            synthesis["combined_insights"].extend(
                [{"domain": domain.value, "insight": insight} for insight in result.insights]
            )

        # Generate cross-domain recommendations
        if len(successful_results) >= 2:
            synthesis["cross_domain_recommendations"] = (
                await self._generate_cross_domain_recommendations(successful_results)
            )

        # Calculate aggregate confidence
        if successful_results:
            synthesis["confidence_aggregate"] = sum(
                result.confidence for result in successful_results.values()
            ) / len(successful_results)

        return synthesis

    async def _generate_cross_domain_recommendations(
        self, results: Dict[MemoryDomain, UnifiedResult]
    ) -> List[str]:
        """Generate recommendations that leverage insights from multiple domains"""
        recommendations = []

        sophia_insights = []
        artemis_insights = []

        for domain, result in results.items():
            if domain == MemoryDomain.SOPHIA:
                sophia_insights.extend(result.insights)
            elif domain == MemoryDomain.ARTEMIS:
                artemis_insights.extend(result.insights)

        # Generate cross-domain recommendations
        if sophia_insights and artemis_insights:
            recommendations.append(
                "Integrate business intelligence insights with technical implementation for optimal outcomes"
            )
            recommendations.append(
                "Leverage data-driven decision making throughout the development lifecycle"
            )
            recommendations.append(
                "Establish feedback loops between business metrics and code quality indicators"
            )

        return recommendations

    def _get_recent_collaborations(self, hours: int = 24) -> List[CollaborationResult]:
        """Get recent collaboration results for pattern learning"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        return [
            collab
            for collab in self.collaboration_history
            if collab.get("timestamp", datetime.min) > cutoff_time
        ]

    async def _generate_pattern_insights(self, patterns: List[LearnedPattern]) -> Dict[str, Any]:
        """Generate insights about learned patterns"""
        insights = {
            "pattern_distribution": {},
            "success_patterns": [],
            "optimization_opportunities": [],
            "common_failure_modes": [],
        }

        # Analyze pattern distribution
        for pattern in patterns:
            pattern_type = pattern.pattern_type.value
            insights["pattern_distribution"][pattern_type] = (
                insights["pattern_distribution"].get(pattern_type, 0) + 1
            )

        # Identify high-success patterns
        success_patterns = [p for p in patterns if p.success_rate > 0.8 and p.usage_count > 2]
        insights["success_patterns"] = [
            {"id": p.id, "type": p.pattern_type.value, "success_rate": p.success_rate}
            for p in success_patterns
        ]

        # Identify failure patterns to avoid
        failure_patterns = [
            p for p in patterns if p.pattern_type == LearnedPatternType.FAILURE_PATTERN
        ]
        insights["common_failure_modes"] = [
            {"id": p.id, "conditions": p.trigger_conditions} for p in failure_patterns
        ]

        return insights

    def _prepare_collaboration_messages(self, task: UnifiedTask) -> List[Dict[str, str]]:
        """Prepare messages for LLM-guided collaboration"""
        system_prompt = """You are a Cross-Learning Coordination AI that facilitates collaboration between different AI orchestrators.

Your role is to:
1. Understand collaboration requirements from task descriptions
2. Identify the best collaboration strategy
3. Determine which orchestrators should be involved
4. Plan the coordination approach

Available orchestrators:
- Sophia: Business Intelligence and Analytics
- Artemis: Code Excellence and Development
- Shared: Cross-domain coordination

Collaboration types:
- Knowledge Sharing: Share relevant knowledge between domains
- Task Handoff: Transfer task execution to appropriate orchestrator
- Joint Execution: Coordinate parallel execution across orchestrators
- Pattern Learning: Extract and apply learned collaboration patterns"""

        user_prompt = f"""Collaboration Task: {task.content}

Current Context:
- Available orchestrators: {list(self.connected_orchestrators.keys())}
- Task type: {task.type.value}
- Priority: {task.priority.value}
- Metadata: {json.dumps(task.metadata, indent=2)}

Please recommend:
1. The best collaboration strategy for this task
2. Which orchestrators should be involved and their roles
3. How to coordinate the collaboration
4. What knowledge should be shared between domains
5. Success criteria for the collaboration

Provide a structured response with clear action items."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    async def _process_collaboration_response(
        self, response: Any, task: UnifiedTask
    ) -> Dict[str, Any]:
        """Process LLM response to extract collaboration strategy"""
        content = (
            response.choices[0].message.content if hasattr(response, "choices") else str(response)
        )

        # Simple extraction - would be more sophisticated in production
        strategy = {
            "approach": "general_collaboration",
            "participating_domains": [MemoryDomain.SHARED],
            "coordination_plan": content,
            "success_criteria": ["task_completion", "knowledge_sharing"],
        }

        # Extract participating domains from response
        if "sophia" in content.lower():
            strategy["participating_domains"].append(MemoryDomain.SOPHIA)
        if "artemis" in content.lower():
            strategy["participating_domains"].append(MemoryDomain.ARTEMIS)

        return strategy

    async def _execute_collaboration_strategy(
        self, strategy: Dict[str, Any], task: UnifiedTask
    ) -> Dict[str, Any]:
        """Execute the determined collaboration strategy"""
        strategy_result = {"success": False, "details": {}}

        try:
            participating_domains = strategy.get("participating_domains", [])

            if len(participating_domains) == 1:
                # Simple execution in single domain
                if participating_domains[0] in self.connected_orchestrators:
                    orchestrator = self.connected_orchestrators[participating_domains[0]]
                    result = await orchestrator.execute(task)
                    strategy_result = {
                        "success": result.success,
                        "details": {"single_domain_execution": result.__dict__},
                    }
            else:
                # Multi-domain collaboration
                strategy_result = await self._execute_multi_domain_strategy(
                    participating_domains, task, strategy
                )

        except Exception as e:
            strategy_result["details"]["error"] = str(e)

        return strategy_result

    async def _execute_multi_domain_strategy(
        self, domains: List[MemoryDomain], task: UnifiedTask, strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute multi-domain collaboration strategy"""
        results = {}

        for domain in domains:
            if domain in self.connected_orchestrators and domain != MemoryDomain.SHARED:
                orchestrator = self.connected_orchestrators[domain]

                # Adapt task for domain
                adapted_task = UnifiedTask(
                    id=f"multi_domain_{domain.value}_{task.id}",
                    type=task.type,
                    content=self._adapt_task_content_for_domain(task.content, domain),
                    priority=task.priority,
                    metadata={**task.metadata, "collaboration_mode": "multi_domain"},
                    tags=task.tags + ["multi_domain", domain.value],
                    budget=task.budget,
                )

                try:
                    result = await orchestrator.execute(adapted_task)
                    results[domain.value] = result.__dict__
                except Exception as e:
                    results[domain.value] = {"error": str(e), "success": False}

        return {
            "success": any(r.get("success", False) for r in results.values()),
            "details": {"multi_domain_results": results},
        }

    async def _learn_from_collaboration(self, task: UnifiedTask, result: UnifiedResult) -> None:
        """Learn from collaboration execution"""
        # Create collaboration result for learning
        collaboration_result = CollaborationResult(
            collaboration_id=task.id,
            success=result.success,
            shared_knowledge=[],  # Would be populated from actual execution
            enhanced_context=result.metadata,
            recommendations=result.recommendations,
            lessons_learned=[],
            performance_metrics={
                "execution_time": result.execution_time_ms,
                "confidence": result.confidence,
            },
            execution_time_ms=result.execution_time_ms,
            errors=result.errors,
        )

        # Store in collaboration history
        self.collaboration_history.append(collaboration_result)

        # Learn patterns from the collaboration
        patterns = await self.pattern_engine.learn_from_collaboration(
            collaboration_result, task.metadata
        )

        # Update metrics
        if result.success:
            self.sharing_metrics["successful_collaborations"] += 1
        else:
            self.sharing_metrics["failed_collaborations"] += 1

        self.sharing_metrics["patterns_learned"] += len(patterns)

    # Public API methods

    async def request_collaboration(
        self,
        requesting_domain: MemoryDomain,
        target_domain: MemoryDomain,
        collaboration_type: CollaborationType,
        task_context: Dict[str, Any],
        expected_outcome: str = "Enhanced task execution",
    ) -> CollaborationResult:
        """Request cross-domain collaboration"""

        request = CollaborationRequest(
            id=f"collab_request_{datetime.now().timestamp()}",
            requesting_domain=requesting_domain,
            target_domain=target_domain,
            collaboration_type=collaboration_type,
            task_context=task_context,
            expected_outcome=expected_outcome,
            priority=ExecutionPriority.NORMAL,
        )

        # Store active collaboration
        self.active_collaborations[request.id] = request

        # Create task for collaboration
        task = UnifiedTask(
            id=f"collaboration_{request.id}",
            type=TaskType.ORCHESTRATION,
            content=f"Facilitate {collaboration_type.value} between {requesting_domain.value} and {target_domain.value}",
            metadata={
                "source_domain": requesting_domain.value,
                "target_domain": target_domain.value,
                "collaboration_type": collaboration_type.value,
                **task_context,
            },
            tags=[
                "collaboration",
                collaboration_type.value,
                requesting_domain.value,
                target_domain.value,
            ],
        )

        # Execute collaboration
        result = await self.execute(task)

        # Create collaboration result
        collaboration_result = CollaborationResult(
            collaboration_id=request.id,
            success=result.success,
            shared_knowledge=[],  # Extract from result
            enhanced_context=result.metadata,
            recommendations=result.recommendations,
            lessons_learned=[],
            performance_metrics={"execution_time": result.execution_time_ms},
            execution_time_ms=result.execution_time_ms,
            errors=result.errors,
        )

        # Clean up active collaboration
        if request.id in self.active_collaborations:
            del self.active_collaborations[request.id]

        return collaboration_result

    async def share_knowledge(
        self, source_domain: MemoryDomain, knowledge: CrossDomainKnowledge
    ) -> bool:
        """Share knowledge from one domain to others"""
        try:
            # Add knowledge to the graph
            self.knowledge_graph.add_knowledge_node(knowledge)

            # Store in memory for persistence
            if self.memory:
                chunk = DocChunk(
                    content=json.dumps(knowledge.__dict__, indent=2),
                    source_uri=f"cross_learning://knowledge/{knowledge.id}",
                    domain=MemoryDomain.SHARED,
                    metadata={
                        "type": "shared_knowledge",
                        "source_domain": source_domain.value,
                        "knowledge_type": knowledge.knowledge_type,
                        "confidence": knowledge.confidence,
                    },
                    confidence=knowledge.confidence,
                )

                await self.memory.upsert_chunks([chunk], MemoryDomain.SHARED)

            # Update metrics
            self.sharing_metrics["total_knowledge_shared"] += 1

            return True

        except Exception as e:
            logger.error(f"Failed to share knowledge: {e}")
            return False

    def get_collaboration_metrics(self) -> Dict[str, Any]:
        """Get collaboration and knowledge sharing metrics"""
        return {
            **self.sharing_metrics,
            "active_collaborations": len(self.active_collaborations),
            "total_knowledge_nodes": len(self.knowledge_graph.nodes),
            "total_patterns": len(self.pattern_engine.patterns),
            "collaboration_history_size": len(self.collaboration_history),
            "connected_orchestrators": list(self.connected_orchestrators.keys()),
        }

    async def get_applicable_patterns(
        self, context: Dict[str, Any], domains: List[MemoryDomain]
    ) -> List[LearnedPattern]:
        """Get patterns applicable to current context"""
        return self.pattern_engine.find_applicable_patterns(context, domains)

    async def get_cross_domain_knowledge(
        self, target_domain: MemoryDomain, context: Dict[str, Any], limit: int = 10
    ) -> List[CrossDomainKnowledge]:
        """Get knowledge applicable to target domain"""
        return self.knowledge_graph.get_applicable_knowledge(target_domain, context)[:limit]
