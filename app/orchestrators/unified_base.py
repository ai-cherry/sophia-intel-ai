"""
Unified Base Orchestrator
Foundation for consolidated Sophia and Artemis orchestrators
"""

import asyncio
import json
import logging
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from app.core.portkey_manager import TaskType, get_portkey_manager
from app.core.secrets_manager import get_secrets_manager
from app.memory.unified_memory_router import DocChunk, MemoryDomain, get_memory_router
from app.observability.metrics_collector import MetricsCollector
from app.orchestrators.persona_system import PersonaContext, SophiaPersonaSystem

logger = logging.getLogger(__name__)


class ExecutionPriority(Enum):
    """Task execution priority"""

    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


class TaskStatus(Enum):
    """Task execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class UnifiedTask:
    """Enhanced task with persona and meta-tagging support"""

    id: str
    type: TaskType
    content: str
    priority: ExecutionPriority = ExecutionPriority.NORMAL
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    retries: int = 0
    max_retries: int = 3
    budget: Dict[str, float] = field(default_factory=lambda: {"cost_usd": 1.0, "tokens": 10000})

    # Enhanced fields
    persona_context: Optional[PersonaContext] = None
    tags: List[str] = field(default_factory=list)
    source_integration: Optional[str] = None
    confidence_threshold: float = 0.7


@dataclass
class UnifiedResult:
    """Enhanced result with citations and confidence scoring"""

    success: bool
    content: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    citations: List[Dict[str, str]] = field(default_factory=list)
    confidence: float = 1.0
    cost: float = 0.0
    tokens_used: int = 0
    execution_time_ms: float = 0.0
    errors: List[str] = field(default_factory=list)

    # Enhanced fields
    persona_used: Optional[str] = None
    insights: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    data_quality_score: float = 1.0
    source_attribution: List[str] = field(default_factory=list)


@dataclass
class OrchestratorConfig:
    """Enhanced configuration for unified orchestrators"""

    domain: MemoryDomain
    name: str
    description: str
    max_concurrent_tasks: int = 10
    default_timeout_s: int = 120
    enable_caching: bool = True
    enable_monitoring: bool = True
    enable_memory: bool = True
    enable_persona: bool = True
    enable_cross_learning: bool = True

    budget_limits: Dict[str, float] = field(
        default_factory=lambda: {
            "hourly_cost_usd": 100.0,
            "daily_cost_usd": 1000.0,
            "monthly_cost_usd": 20000.0,
        }
    )

    # Integration configurations
    integration_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    data_sources: List[str] = field(default_factory=list)
    quality_thresholds: Dict[str, float] = field(
        default_factory=lambda: {"confidence_min": 0.6, "citation_min": 2, "source_diversity": 0.8}
    )


class UnifiedBaseOrchestrator(ABC):
    """
    Unified base orchestrator consolidating all shared functionality.

    Features:
    - Integrated persona management
    - Memory management with embeddings and meta-tagging
    - Circuit breakers and monitoring
    - Cross-orchestrator knowledge sharing
    - Quality assurance pipeline
    - Multi-source data integration
    """

    def __init__(self, config: OrchestratorConfig):
        """
        Initialize unified base orchestrator

        Args:
            config: Orchestrator configuration
        """
        self.config = config
        self.domain = config.domain

        # Core services
        self.memory = get_memory_router() if config.enable_memory else None
        self.portkey = get_portkey_manager()
        self.secrets = get_secrets_manager()
        self.metrics = MetricsCollector() if config.enable_monitoring else None

        # Persona system
        self.persona_system = SophiaPersonaSystem() if config.enable_persona else None

        # Circuit breaker for fault tolerance
        self.circuit_breaker = CircuitBreaker(
            name=f"{self.config.name}.orchestrator",
            config=CircuitBreakerConfig(
                failure_threshold=5,
                success_threshold=2,
                timeout=60.0,
                expected_exception=Exception,
            ),
        )

        # Task management
        self._task_queue = asyncio.Queue()
        self._active_tasks: Dict[str, UnifiedTask] = {}
        self._task_history: List[Dict[str, Any]] = []
        self._semaphore = asyncio.Semaphore(config.max_concurrent_tasks)

        # Cost tracking
        self._cost_tracker = {"hourly": 0.0, "daily": 0.0, "monthly": 0.0, "total": 0.0}

        # Cross-orchestrator knowledge sharing
        self._shared_context = {}
        self._learning_patterns = []

        # Integration connectors (to be initialized by subclasses)
        self.connectors = {}

        logger.info(f"Initialized {self.config.name} orchestrator for {self.domain.value} domain")

    async def execute(self, task: UnifiedTask) -> UnifiedResult:
        """
        Unified execution pattern with enhanced capabilities

        Args:
            task: Task to execute

        Returns:
            Execution result
        """
        # Start timing
        start_time = datetime.now()
        task.started_at = start_time
        task.status = TaskStatus.RUNNING

        # Store in active tasks
        self._active_tasks[task.id] = task

        result = UnifiedResult(success=False, content=None)

        try:
            # Pre-execution hooks with enhanced context loading
            await self._pre_execute(task)

            # Budget and quality checks
            if not self._check_budget(task):
                result.errors.append("Budget limit exceeded")
                task.status = TaskStatus.FAILED
                return result

            # Route to appropriate model with enhanced routing
            routing = self.portkey.route_request(
                task_type=task.type,
                estimated_tokens=task.budget.get("tokens", 1000),
                max_cost_usd=task.budget.get("cost_usd", 1.0),
            )

            # Execute with monitoring and circuit breaker
            async with self._semaphore:
                if self.metrics:
                    with self.metrics.timer(f"{self.domain.value}.execution"):
                        result = await self._execute_with_circuit_breaker(task, routing)
                else:
                    result = await self._execute_with_circuit_breaker(task, routing)

            # Post-execution hooks with enhanced storage
            await self._post_execute(task, result)

            # Quality assurance
            await self._apply_quality_assurance(task, result)

            # Update task status
            task.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
            task.completed_at = datetime.now()

            # Calculate execution time
            result.execution_time_ms = (task.completed_at - start_time).total_seconds() * 1000

            # Track costs
            self._update_cost_tracking(result.cost)

            # Cross-learning update
            if self.config.enable_cross_learning:
                await self._update_cross_learning(task, result)

        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}\n{traceback.format_exc()}")
            result.success = False
            result.errors.append(str(e))
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()

            # Retry logic
            if task.retries < task.max_retries:
                task.retries += 1
                task.status = TaskStatus.PENDING
                await self._task_queue.put(task)
                logger.info(f"Retrying task {task.id} (attempt {task.retries}/{task.max_retries})")

        finally:
            # Clean up
            if task.id in self._active_tasks:
                del self._active_tasks[task.id]

            # Store in history
            self._task_history.append({"task": task, "result": result, "timestamp": datetime.now()})

            # Emit metrics
            if self.metrics:
                self.metrics.record_task_completion(
                    domain=self.domain.value,
                    task_type=task.type.value,
                    success=result.success,
                    duration_ms=result.execution_time_ms,
                    cost_usd=result.cost,
                )

        return result

    async def _execute_with_circuit_breaker(self, task: UnifiedTask, routing: Any) -> UnifiedResult:
        """Execute task with circuit breaker protection"""

        async def _execute():
            return await self._execute_core(task, routing)

        return await self.circuit_breaker.call(_execute)

    @abstractmethod
    async def _execute_core(self, task: UnifiedTask, routing: Any) -> UnifiedResult:
        """
        Core execution logic - must be implemented by subclasses

        Args:
            task: Task to execute
            routing: Model routing decision

        Returns:
            Execution result
        """
        pass

    async def _pre_execute(self, task: UnifiedTask) -> None:
        """
        Enhanced pre-execution hook with context loading and persona selection

        Args:
            task: Task about to be executed
        """
        # Load relevant context from memory with enhanced search
        if self.memory and self.config.enable_memory:
            context = await self._load_enhanced_context(task)
            task.metadata["context"] = context

        # Select appropriate persona if enabled
        if self.persona_system and task.persona_context:
            persona = await self.persona_system.select_persona(task.persona_context)
            task.metadata["selected_persona"] = persona

        # Load cross-orchestrator knowledge
        if self.config.enable_cross_learning:
            shared_knowledge = await self._load_shared_knowledge(task)
            task.metadata["shared_knowledge"] = shared_knowledge

        # Validate task requirements
        await self._validate_task(task)

        # Meta-tagging for enhanced organization
        await self._apply_meta_tagging(task)

        # Log execution start
        logger.info(f"Starting execution of task {task.id} ({task.type.value})")

    async def _post_execute(self, task: UnifiedTask, result: UnifiedResult) -> None:
        """
        Enhanced post-execution hook with advanced storage and analysis

        Args:
            task: Completed task
            result: Execution result
        """
        # Store results in memory with enhanced metadata
        if self.memory and self.config.enable_memory and result.success:
            await self._store_enhanced_results(task, result)

        # Cache successful results with intelligent TTL
        if self.config.enable_caching and result.success:
            cache_key = self._generate_cache_key(task)
            ttl = self._calculate_cache_ttl(task, result)
            await self.memory.put_ephemeral(cache_key, result, ttl_s=ttl)

        # Update persona learning if applicable
        if self.persona_system and result.persona_used:
            await self._update_persona_learning(task, result)

        # Log execution completion with enhanced details
        status = "succeeded" if result.success else "failed"
        logger.info(
            f"Task {task.id} {status} in {result.execution_time_ms:.2f}ms "
            f"(confidence: {result.confidence:.2f}, sources: {len(result.citations)})"
        )

    async def _load_enhanced_context(self, task: UnifiedTask) -> Dict[str, Any]:
        """
        Load enhanced context with multi-source knowledge

        Args:
            task: Task to get context for

        Returns:
            Enhanced context dictionary
        """
        context = {
            "related_info": [],
            "recent_tasks": [],
            "integration_data": {},
            "quality_metrics": {},
        }

        # Search for relevant information with enhanced filtering
        if task.content:
            # Multi-domain search for cross-pollination
            domains = [self.domain]
            if self.config.enable_cross_learning:
                domains.append(MemoryDomain.SHARED)

            for domain in domains:
                hits = await self.memory.search(
                    query=task.content,
                    domain=domain,
                    k=5,
                    filters={"tags": task.tags} if task.tags else None,
                )

                context["related_info"].extend(
                    [
                        {
                            "content": hit.content,
                            "source": hit.source_uri,
                            "score": hit.score,
                            "domain": hit.domain.value,
                            "metadata": hit.metadata,
                        }
                        for hit in hits
                    ]
                )

        # Load recent task history with pattern detection
        context["recent_tasks"] = self._get_recent_tasks_with_patterns(limit=5)

        # Load integration-specific context
        context["integration_data"] = await self._load_integration_context(task)

        # Calculate context quality metrics
        context["quality_metrics"] = self._calculate_context_quality(context)

        return context

    async def _store_enhanced_results(self, task: UnifiedTask, result: UnifiedResult) -> None:
        """
        Store task results with enhanced metadata and tagging

        Args:
            task: Completed task
            result: Execution result
        """
        # Create enhanced document chunk
        enhanced_content = {
            "task": task.content,
            "result": result.content if isinstance(result.content, str) else str(result.content),
            "insights": result.insights,
            "recommendations": result.recommendations,
            "execution_metadata": {
                "persona_used": result.persona_used,
                "confidence": result.confidence,
                "data_quality": result.data_quality_score,
                "execution_time": result.execution_time_ms,
                "cost": result.cost,
            },
        }

        chunk = DocChunk(
            content=json.dumps(enhanced_content, indent=2),
            source_uri=f"task://{task.id}",
            domain=self.domain,
            metadata={
                "task_type": task.type.value,
                "timestamp": datetime.now().isoformat(),
                "success": result.success,
                "persona": result.persona_used,
                "tags": task.tags,
                "integration_source": task.source_integration,
                "priority": task.priority.value,
                "confidence": result.confidence,
                "quality_score": result.data_quality_score,
            },
            confidence=result.confidence,
        )

        # Store in vector memory
        await self.memory.upsert_chunks([chunk], self.domain)

        # Store structured facts with enhanced schema
        await self.memory.record_fact(
            table="unified_task_results",
            data={
                "task_id": task.id,
                "task_type": task.type.value,
                "domain": self.domain.value,
                "success": result.success,
                "cost_usd": result.cost,
                "tokens_used": result.tokens_used,
                "execution_time_ms": result.execution_time_ms,
                "confidence": result.confidence,
                "data_quality_score": result.data_quality_score,
                "persona_used": result.persona_used,
                "citation_count": len(result.citations),
                "insight_count": len(result.insights),
                "recommendation_count": len(result.recommendations),
                "tags": json.dumps(task.tags),
                "source_integration": task.source_integration,
            },
        )

    async def _apply_quality_assurance(self, task: UnifiedTask, result: UnifiedResult) -> None:
        """
        Apply quality assurance checks to results

        Args:
            task: Completed task
            result: Execution result
        """
        # Confidence threshold check
        if result.confidence < self.config.quality_thresholds["confidence_min"]:
            result.errors.append(f"Confidence {result.confidence:.2f} below threshold")

        # Citation requirement check
        if len(result.citations) < self.config.quality_thresholds["citation_min"]:
            result.errors.append(f"Insufficient citations: {len(result.citations)}")

        # Source diversity check
        if result.source_attribution:
            diversity = self._calculate_source_diversity(result.source_attribution)
            if diversity < self.config.quality_thresholds["source_diversity"]:
                result.errors.append(f"Low source diversity: {diversity:.2f}")

        # Calculate overall data quality score
        result.data_quality_score = self._calculate_data_quality_score(result)

    async def _apply_meta_tagging(self, task: UnifiedTask) -> None:
        """
        Apply intelligent meta-tagging to tasks

        Args:
            task: Task to tag
        """
        # Auto-generate tags based on content analysis
        content_lower = task.content.lower()

        # Domain-specific tags
        domain_tags = {
            MemoryDomain.SOPHIA: ["business", "intelligence", "analytics", "sales", "strategy"],
            MemoryDomain.ARTEMIS: ["code", "development", "technical", "engineering", "quality"],
            MemoryDomain.SHARED: ["shared", "knowledge", "cross-domain", "collaboration"],
        }

        # Add domain-relevant tags
        for tag in domain_tags.get(self.domain, []):
            if tag in content_lower and tag not in task.tags:
                task.tags.append(tag)

        # Task type tags
        type_tags = {
            TaskType.ORCHESTRATION: ["orchestration", "coordination"],
            TaskType.CODE_GENERATION: ["generation", "creation"],
            TaskType.CODE_REVIEW: ["review", "analysis", "quality"],
            TaskType.WEB_RESEARCH: ["research", "investigation"],
            TaskType.DATA_ANALYSIS: ["data", "analysis", "metrics"],
        }

        for tag in type_tags.get(task.type, []):
            if tag not in task.tags:
                task.tags.append(tag)

        # Priority tags
        if task.priority == ExecutionPriority.CRITICAL:
            task.tags.append("critical")
        elif task.priority == ExecutionPriority.HIGH:
            task.tags.append("high-priority")

    async def _update_cross_learning(self, task: UnifiedTask, result: UnifiedResult) -> None:
        """
        Update cross-orchestrator learning patterns

        Args:
            task: Completed task
            result: Execution result
        """
        if not result.success:
            return

        # Create learning pattern
        pattern = {
            "domain": self.domain.value,
            "task_type": task.type.value,
            "success_factors": {
                "confidence": result.confidence,
                "data_quality": result.data_quality_score,
                "citation_count": len(result.citations),
                "execution_time": result.execution_time_ms,
            },
            "context_patterns": task.metadata.get("context", {}),
            "timestamp": datetime.now().isoformat(),
        }

        # Store pattern for cross-learning
        self._learning_patterns.append(pattern)

        # Share successful patterns with other domains
        if result.confidence > 0.8 and result.data_quality_score > 0.8:
            shared_chunk = DocChunk(
                content=json.dumps(
                    {
                        "pattern": pattern,
                        "insights": result.insights[:3],  # Top insights
                        "best_practices": result.recommendations[:3],  # Top recommendations
                    }
                ),
                source_uri=f"cross-learning://{task.id}",
                domain=MemoryDomain.SHARED,
                metadata={
                    "type": "learning_pattern",
                    "source_domain": self.domain.value,
                    "success_score": (result.confidence + result.data_quality_score) / 2,
                },
                confidence=result.confidence,
            )

            await self.memory.upsert_chunks([chunk], MemoryDomain.SHARED)

    def _calculate_source_diversity(self, sources: List[str]) -> float:
        """Calculate diversity score for data sources"""
        if not sources:
            return 0.0

        unique_sources = set(sources)
        return len(unique_sources) / len(sources)

    def _calculate_data_quality_score(self, result: UnifiedResult) -> float:
        """Calculate overall data quality score"""
        factors = [
            result.confidence,
            min(len(result.citations) / 5.0, 1.0),  # Normalize citations
            min(len(result.source_attribution) / 3.0, 1.0),  # Normalize sources
        ]

        if result.source_attribution:
            factors.append(self._calculate_source_diversity(result.source_attribution))

        return sum(factors) / len(factors)

    def _calculate_cache_ttl(self, task: UnifiedTask, result: UnifiedResult) -> int:
        """Calculate intelligent cache TTL based on result quality"""
        base_ttl = 3600  # 1 hour

        # Extend TTL for high-quality results
        quality_multiplier = (result.confidence + result.data_quality_score) / 2

        # Extend for high-priority tasks
        priority_multiplier = {
            ExecutionPriority.CRITICAL: 2.0,
            ExecutionPriority.HIGH: 1.5,
            ExecutionPriority.NORMAL: 1.0,
            ExecutionPriority.LOW: 0.5,
        }.get(task.priority, 1.0)

        return int(base_ttl * quality_multiplier * priority_multiplier)

    async def _load_shared_knowledge(self, task: UnifiedTask) -> Dict[str, Any]:
        """Load cross-orchestrator shared knowledge"""
        if not self.memory:
            return {}

        # Search shared domain for relevant patterns
        hits = await self.memory.search(
            query=task.content,
            domain=MemoryDomain.SHARED,
            k=3,
            filters={"type": "learning_pattern"},
        )

        return {
            "cross_domain_patterns": [
                {
                    "content": hit.content,
                    "relevance": hit.score,
                    "source_domain": hit.metadata.get("source_domain"),
                    "success_score": hit.metadata.get("success_score", 0),
                }
                for hit in hits
            ]
        }

    async def _load_integration_context(self, task: UnifiedTask) -> Dict[str, Any]:
        """Load context from integration sources"""
        # To be implemented by subclasses based on their specific integrations
        return {}

    def _get_recent_tasks_with_patterns(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent task history with pattern analysis"""
        recent = self._task_history[-limit:] if self._task_history else []

        tasks_with_patterns = []
        for entry in recent:
            task_summary = {
                "task_id": entry["task"].id,
                "type": entry["task"].type.value,
                "success": entry["result"].success,
                "confidence": entry["result"].confidence,
                "timestamp": entry["timestamp"].isoformat(),
                "tags": entry["task"].tags,
            }

            # Add pattern analysis
            if entry["result"].success:
                task_summary["success_patterns"] = {
                    "high_confidence": entry["result"].confidence > 0.8,
                    "good_quality": entry["result"].data_quality_score > 0.8,
                    "sufficient_citations": len(entry["result"].citations) >= 2,
                }

            tasks_with_patterns.append(task_summary)

        return tasks_with_patterns

    def _calculate_context_quality(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Calculate quality metrics for loaded context"""
        return {
            "relevance_score": sum(item.get("score", 0) for item in context.get("related_info", []))
            / max(len(context.get("related_info", [])), 1),
            "source_diversity": len(
                set(item.get("source", "") for item in context.get("related_info", []))
            ),
            "recency_score": len(
                [task for task in context.get("recent_tasks", []) if task.get("success", False)]
            )
            / max(len(context.get("recent_tasks", [])), 1),
        }

    # Rest of the methods from BaseOrchestrator (budget checking, validation, etc.)
    # ... (keeping the existing implementations with minor enhancements)

    async def _validate_task(self, task: UnifiedTask) -> None:
        """Enhanced task validation"""
        if not task.content:
            raise ValueError("Task content cannot be empty")

        if task.budget.get("cost_usd", 0) <= 0:
            raise ValueError("Task must have a positive cost budget")

        if task.budget.get("tokens", 0) <= 0:
            raise ValueError("Task must have a positive token budget")

        # Validate confidence threshold
        if task.confidence_threshold < 0 or task.confidence_threshold > 1:
            raise ValueError("Confidence threshold must be between 0 and 1")

    def _check_budget(self, task: UnifiedTask) -> bool:
        """Check if task fits within budget limits"""
        task_cost = task.budget.get("cost_usd", 0)

        # Check hourly limit
        if self._cost_tracker["hourly"] + task_cost > self.config.budget_limits["hourly_cost_usd"]:
            logger.warning(f"Task {task.id} would exceed hourly budget limit")
            return False

        # Check daily limit
        if self._cost_tracker["daily"] + task_cost > self.config.budget_limits["daily_cost_usd"]:
            logger.warning(f"Task {task.id} would exceed daily budget limit")
            return False

        return True

    def _update_cost_tracking(self, cost: float) -> None:
        """Update cost tracking"""
        self._cost_tracker["hourly"] += cost
        self._cost_tracker["daily"] += cost
        self._cost_tracker["monthly"] += cost
        self._cost_tracker["total"] += cost

    def _generate_cache_key(self, task: UnifiedTask) -> str:
        """Generate enhanced cache key for task"""
        import hashlib

        key_parts = [
            self.domain.value,
            task.type.value,
            task.content[:100],  # First 100 chars
            "|".join(sorted(task.tags)),  # Include tags
        ]

        combined = "|".join(key_parts)
        return f"unified_task_cache:{hashlib.sha256(combined.encode()).hexdigest()[:16]}"

    async def submit_task(self, task: UnifiedTask) -> str:
        """Submit a task to the queue"""
        await self._task_queue.put(task)
        logger.info(f"Task {task.id} submitted to queue")
        return task.id

    async def process_tasks(self) -> None:
        """Process tasks from the queue continuously"""
        while True:
            try:
                # Get next task
                task = await self._task_queue.get()

                # Execute task
                await self.execute(task)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing task: {e}")
                await asyncio.sleep(1)

    def get_status(self) -> Dict[str, Any]:
        """Get enhanced orchestrator status"""
        return {
            "name": self.config.name,
            "domain": self.domain.value,
            "active_tasks": len(self._active_tasks),
            "queue_size": self._task_queue.qsize(),
            "total_processed": len(self._task_history),
            "cost_tracking": self._cost_tracker,
            "circuit_breaker_state": self.circuit_breaker.state,
            "cache_hit_rate": self.memory.metrics.get_cache_hit_rate() if self.memory else 0.0,
            "learning_patterns": len(self._learning_patterns),
            "integration_count": len(self.connectors),
            "quality_metrics": {
                "avg_confidence": (
                    sum(entry["result"].confidence for entry in self._task_history[-10:])
                    / min(len(self._task_history), 10)
                    if self._task_history
                    else 0
                ),
                "avg_quality_score": (
                    sum(entry["result"].data_quality_score for entry in self._task_history[-10:])
                    / min(len(self._task_history), 10)
                    if self._task_history
                    else 0
                ),
            },
        }

    async def shutdown(self) -> None:
        """Graceful shutdown with enhanced cleanup"""
        logger.info(f"Shutting down {self.config.name} orchestrator")

        # Cancel pending tasks
        while not self._task_queue.empty():
            task = await self._task_queue.get()
            task.status = TaskStatus.CANCELLED

        # Wait for active tasks
        while self._active_tasks:
            await asyncio.sleep(0.1)

        # Close connections
        if self.memory:
            await self.memory.close()

        # Save learning patterns
        if self._learning_patterns:
            logger.info(f"Saving {len(self._learning_patterns)} learning patterns")
            # Could save to persistent storage

        logger.info(f"{self.config.name} orchestrator shutdown complete")
