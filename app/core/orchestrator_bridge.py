"""
Enhanced Orchestrator Coordination Bridge
Manages cross-orchestrator coordination with advanced metrics collection,
task routing optimization, resource balancing, and context preservation
"""

import asyncio
import json
import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from threading import Lock, RLock
from typing import Any, Optional

from app.core.ai_logger import logger
from app.core.redis_manager import RedisManager
from app.core.websocket_manager import WebSocketManager
from app.orchestrators.base_orchestrator import (
    BaseOrchestrator,
    ExecutionPriority,
    Task,
)

# ==================== TYPES AND ENUMS ====================


class OrchestratorType(Enum):
    """Types of orchestrators in the system"""

    SOPHIA = "sophia"
    ARTEMIS = "artemis"
    HYBRID = "hybrid"


class TaskRoutingStrategy(Enum):
    """Task routing strategies for load balancing"""

    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    DOMAIN_AFFINITY = "domain_affinity"
    PRIORITY_WEIGHTED = "priority_weighted"
    INTELLIGENT = "intelligent"


class BridgeHealthStatus(Enum):
    """Health status of the coordination bridge"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"


@dataclass
class TaskRoutingDecision:
    """Decision made by the task routing system"""

    task_id: str
    source_orchestrator: str
    target_orchestrator: str
    routing_strategy: TaskRoutingStrategy
    decision_reason: str
    confidence: float
    expected_performance: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OrchestratorMetrics:
    """Real-time metrics for an orchestrator"""

    orchestrator_id: str
    orchestrator_type: OrchestratorType
    active_tasks: int
    max_tasks: int
    queue_size: int
    average_response_time_ms: float
    success_rate: float
    cpu_utilization: float
    memory_utilization: float
    last_heartbeat: datetime

    # Performance tracking
    completed_tasks_1h: int = 0
    failed_tasks_1h: int = 0
    throughput_per_minute: float = 0.0

    @property
    def utilization_percent(self) -> float:
        """Calculate task utilization percentage"""
        return (self.active_tasks / self.max_tasks) * 100 if self.max_tasks > 0 else 0

    @property
    def available_capacity(self) -> int:
        """Calculate available task capacity"""
        return max(0, self.max_tasks - self.active_tasks)

    @property
    def is_overloaded(self) -> bool:
        """Check if orchestrator is overloaded"""
        return self.utilization_percent > 80 or self.queue_size > 5


@dataclass
class BridgeMetrics:
    """Metrics for the coordination bridge itself"""

    total_tasks_routed: int = 0
    successful_routes: int = 0
    failed_routes: int = 0
    average_routing_time_ms: float = 0.0
    context_preservation_rate: float = 100.0
    serialization_time_ms: float = 0.0
    deserialization_time_ms: float = 0.0

    # Health indicators
    health_score: float = 100.0
    last_health_check: datetime = field(default_factory=datetime.utcnow)
    active_connections: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate routing success rate"""
        if self.total_tasks_routed == 0:
            return 100.0
        return (self.successful_routes / self.total_tasks_routed) * 100


@dataclass
class TaskFlowEvent:
    """Event representing a task flow between orchestrators"""

    event_id: str
    event_type: str  # 'route', 'complete', 'fail', 'queue'
    task_id: str
    source_orchestrator: str
    target_orchestrator: str
    task_type: str
    priority: ExecutionPriority
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[float] = None
    context_preserved: bool = True
    pay_ready_context: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class PerformanceBottleneck:
    """Represents a performance bottleneck in the system"""

    def __init__(
        self,
        bottleneck_id: str,
        bottleneck_type: str,
        severity: str,
        orchestrator_affected: str,
        description: str,
        impact_score: float,
        suggested_actions: list[str],
    ):
        self.id = bottleneck_id
        self.type = bottleneck_type
        self.severity = severity
        self.orchestrator_affected = orchestrator_affected
        self.description = description
        self.impact_score = impact_score
        self.suggested_actions = suggested_actions
        self.detected_at = datetime.utcnow()
        self.resolved_at: Optional[datetime] = None


# ==================== ENHANCED ORCHESTRATOR BRIDGE ====================


class EnhancedOrchestratorBridge:
    """
    Enhanced coordination bridge managing cross-orchestrator interactions
    with advanced metrics, routing optimization, and performance monitoring
    """

    def __init__(
        self,
        redis_manager: RedisManager,
        websocket_manager: Optional[WebSocketManager] = None,
        enable_metrics: bool = True,
        enable_bottleneck_detection: bool = True,
        routing_strategy: TaskRoutingStrategy = TaskRoutingStrategy.INTELLIGENT,
    ):
        self.redis_manager = redis_manager
        self.websocket_manager = websocket_manager
        self.enable_metrics = enable_metrics
        self.enable_bottleneck_detection = enable_bottleneck_detection
        self.routing_strategy = routing_strategy

        # Orchestrator registry
        self.orchestrators: dict[str, BaseOrchestrator] = {}
        self.orchestrator_metrics: dict[str, OrchestratorMetrics] = {}
        self.orchestrator_types: dict[str, OrchestratorType] = {}

        # Bridge state and metrics
        self.bridge_metrics = BridgeMetrics()
        self.is_running = False
        self.health_status = BridgeHealthStatus.OFFLINE

        # Task tracking
        self.active_tasks: dict[str, TaskFlowEvent] = {}
        self.task_history: deque = deque(maxlen=1000)  # Keep last 1000 task events
        self.routing_decisions: deque = deque(maxlen=500)

        # Performance monitoring
        self.performance_samples: dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.bottlenecks: list[PerformanceBottleneck] = []

        # Threading locks
        self.metrics_lock = RLock()
        self.routing_lock = Lock()

        # Background tasks
        self.monitoring_task: Optional[asyncio.Task] = None
        self.metrics_collection_task: Optional[asyncio.Task] = None

    # ==================== ORCHESTRATOR MANAGEMENT ====================

    def register_orchestrator(
        self,
        orchestrator: BaseOrchestrator,
        orchestrator_type: OrchestratorType,
        max_tasks: int = 8,
    ) -> None:
        """Register an orchestrator with the bridge"""
        orchestrator_id = orchestrator.id
        self.orchestrators[orchestrator_id] = orchestrator
        self.orchestrator_types[orchestrator_id] = orchestrator_type

        # Initialize metrics
        self.orchestrator_metrics[orchestrator_id] = OrchestratorMetrics(
            orchestrator_id=orchestrator_id,
            orchestrator_type=orchestrator_type,
            active_tasks=0,
            max_tasks=max_tasks,
            queue_size=0,
            average_response_time_ms=0.0,
            success_rate=100.0,
            cpu_utilization=0.0,
            memory_utilization=0.0,
            last_heartbeat=datetime.utcnow(),
        )

        logger.info(f"Registered {orchestrator_type.value} orchestrator: {orchestrator_id}")

    def unregister_orchestrator(self, orchestrator_id: str) -> None:
        """Unregister an orchestrator from the bridge"""
        if orchestrator_id in self.orchestrators:
            del self.orchestrators[orchestrator_id]
            del self.orchestrator_metrics[orchestrator_id]
            del self.orchestrator_types[orchestrator_id]
            logger.info(f"Unregistered orchestrator: {orchestrator_id}")

    # ==================== TASK ROUTING ====================

    def route_task(
        self, task: Task, source_orchestrator_id: str, preferred_target: Optional[str] = None
    ) -> TaskRoutingDecision:
        """
        Route a task to the optimal orchestrator based on the routing strategy
        """
        with self.routing_lock:
            start_time = time.time()

            try:
                # Determine target orchestrator
                target_orchestrator_id = self._select_target_orchestrator(
                    task, source_orchestrator_id, preferred_target
                )

                # Create routing decision
                decision = TaskRoutingDecision(
                    task_id=task.id,
                    source_orchestrator=source_orchestrator_id,
                    target_orchestrator=target_orchestrator_id,
                    routing_strategy=self.routing_strategy,
                    decision_reason=self._get_routing_reason(task, target_orchestrator_id),
                    confidence=self._calculate_routing_confidence(task, target_orchestrator_id),
                    expected_performance=self._estimate_performance(task, target_orchestrator_id),
                )

                # Record routing decision
                self.routing_decisions.append(decision)

                # Update metrics
                routing_time_ms = (time.time() - start_time) * 1000
                self._update_routing_metrics(routing_time_ms, success=True)

                # Create task flow event
                flow_event = TaskFlowEvent(
                    event_id=f"route_{task.id}_{int(time.time())}",
                    event_type="route",
                    task_id=task.id,
                    source_orchestrator=source_orchestrator_id,
                    target_orchestrator=target_orchestrator_id,
                    task_type=task.type.value if hasattr(task.type, "value") else str(task.type),
                    priority=task.priority,
                    pay_ready_context=self._is_pay_ready_task(task),
                    metadata={
                        "routing_strategy": self.routing_strategy.value,
                        "confidence": decision.confidence,
                        "routing_time_ms": routing_time_ms,
                    },
                )

                self.active_tasks[task.id] = flow_event
                self.task_history.append(flow_event)

                # Notify via WebSocket if available
                if self.websocket_manager:
                    asyncio.create_task(self._broadcast_task_event(flow_event))

                return decision

            except Exception as e:
                logger.error(f"Task routing failed: {e}")
                routing_time_ms = (time.time() - start_time) * 1000
                self._update_routing_metrics(routing_time_ms, success=False)
                raise

    def _select_target_orchestrator(
        self, task: Task, source_orchestrator_id: str, preferred_target: Optional[str] = None
    ) -> str:
        """Select the best target orchestrator for a task"""

        if preferred_target and preferred_target in self.orchestrators:
            return preferred_target

        available_orchestrators = [
            orch_id
            for orch_id, metrics in self.orchestrator_metrics.items()
            if orch_id != source_orchestrator_id and not metrics.is_overloaded
        ]

        if not available_orchestrators:
            # Fallback: use least overloaded orchestrator
            available_orchestrators = [
                orch_id for orch_id in self.orchestrators if orch_id != source_orchestrator_id
            ]

        if not available_orchestrators:
            raise RuntimeError("No available target orchestrators")

        # Apply routing strategy
        if self.routing_strategy == TaskRoutingStrategy.LEAST_LOADED:
            return self._select_least_loaded(available_orchestrators)
        elif self.routing_strategy == TaskRoutingStrategy.DOMAIN_AFFINITY:
            return self._select_by_domain_affinity(task, available_orchestrators)
        elif self.routing_strategy == TaskRoutingStrategy.PRIORITY_WEIGHTED:
            return self._select_by_priority(task, available_orchestrators)
        elif self.routing_strategy == TaskRoutingStrategy.INTELLIGENT:
            return self._select_intelligently(task, available_orchestrators)
        else:
            # Round robin fallback
            return available_orchestrators[
                len(self.routing_decisions) % len(available_orchestrators)
            ]

    def _select_least_loaded(self, orchestrators: list[str]) -> str:
        """Select orchestrator with lowest utilization"""
        return min(
            orchestrators,
            key=lambda orch_id: self.orchestrator_metrics[orch_id].utilization_percent,
        )

    def _select_by_domain_affinity(self, task: Task, orchestrators: list[str]) -> str:
        """Select orchestrator based on domain affinity"""
        # Pay Ready tasks prefer Sophia for business context
        if self._is_pay_ready_task(task):
            sophia_orchestrators = [
                orch_id
                for orch_id in orchestrators
                if self.orchestrator_types.get(orch_id) == OrchestratorType.SOPHIA
            ]
            if sophia_orchestrators:
                return self._select_least_loaded(sophia_orchestrators)

        # Technical tasks prefer Artemis
        if self._is_technical_task(task):
            artemis_orchestrators = [
                orch_id
                for orch_id in orchestrators
                if self.orchestrator_types.get(orch_id) == OrchestratorType.ARTEMIS
            ]
            if artemis_orchestrators:
                return self._select_least_loaded(artemis_orchestrators)

        return self._select_least_loaded(orchestrators)

    def _select_by_priority(self, task: Task, orchestrators: list[str]) -> str:
        """Select orchestrator based on task priority and performance"""
        if task.priority == ExecutionPriority.HIGH:
            # High priority tasks get the best performing orchestrator
            return max(
                orchestrators,
                key=lambda orch_id: (
                    self.orchestrator_metrics[orch_id].success_rate
                    - self.orchestrator_metrics[orch_id].utilization_percent * 0.5
                ),
            )
        else:
            return self._select_least_loaded(orchestrators)

    def _select_intelligently(self, task: Task, orchestrators: list[str]) -> str:
        """Intelligent selection combining multiple factors"""
        scores = {}

        for orch_id in orchestrators:
            metrics = self.orchestrator_metrics[orch_id]

            # Base score from performance metrics
            score = (
                metrics.success_rate * 0.3
                + (100 - metrics.utilization_percent) * 0.4
                + (1000 / max(metrics.average_response_time_ms, 1)) * 0.2
                + metrics.throughput_per_minute * 0.1
            )

            # Domain affinity bonus
            if (
                self._is_pay_ready_task(task)
                and self.orchestrator_types.get(orch_id) == OrchestratorType.SOPHIA
            ) or (
                self._is_technical_task(task)
                and self.orchestrator_types.get(orch_id) == OrchestratorType.ARTEMIS
            ):
                score *= 1.2

            # Priority bonus for high-priority tasks
            if task.priority == ExecutionPriority.HIGH and metrics.success_rate > 90:
                score *= 1.1

            scores[orch_id] = score

        return max(scores, key=scores.get)

    # ==================== METRICS AND MONITORING ====================

    def update_orchestrator_metrics(
        self,
        orchestrator_id: str,
        active_tasks: int,
        queue_size: int,
        avg_response_time: float,
        success_rate: float,
        cpu_util: float = 0.0,
        memory_util: float = 0.0,
    ) -> None:
        """Update metrics for a specific orchestrator"""
        with self.metrics_lock:
            if orchestrator_id in self.orchestrator_metrics:
                metrics = self.orchestrator_metrics[orchestrator_id]
                metrics.active_tasks = active_tasks
                metrics.queue_size = queue_size
                metrics.average_response_time_ms = avg_response_time
                metrics.success_rate = success_rate
                metrics.cpu_utilization = cpu_util
                metrics.memory_utilization = memory_util
                metrics.last_heartbeat = datetime.utcnow()

                # Update performance samples
                self.performance_samples[orchestrator_id].append(
                    {
                        "timestamp": time.time(),
                        "response_time": avg_response_time,
                        "success_rate": success_rate,
                        "utilization": metrics.utilization_percent,
                    }
                )

    def get_coordination_metrics(self) -> dict[str, Any]:
        """Get comprehensive coordination metrics"""
        with self.metrics_lock:
            total_tasks = sum(m.active_tasks for m in self.orchestrator_metrics.values())
            total_capacity = sum(m.max_tasks for m in self.orchestrator_metrics.values())
            total_queue = sum(m.queue_size for m in self.orchestrator_metrics.values())

            avg_response_time = (
                statistics.mean(
                    [m.average_response_time_ms for m in self.orchestrator_metrics.values()]
                )
                if self.orchestrator_metrics
                else 0.0
            )

            avg_success_rate = (
                statistics.mean([m.success_rate for m in self.orchestrator_metrics.values()])
                if self.orchestrator_metrics
                else 100.0
            )

            return {
                "total_tasks_processed": self.bridge_metrics.total_tasks_routed,
                "task_flow_rate_per_minute": self._calculate_flow_rate(),
                "average_response_time_ms": avg_response_time,
                "resource_utilization_percent": (
                    (total_tasks / total_capacity * 100) if total_capacity > 0 else 0
                ),
                "bridge_health_score": self.bridge_metrics.health_score,
                "synchronization_lag_ms": self._calculate_sync_lag(),
                "active_bottlenecks": len([b for b in self.bottlenecks if not b.resolved_at]),
                "success_rate_percent": avg_success_rate,
                "peak_throughput": self._calculate_peak_throughput(),
                "last_updated": datetime.utcnow().isoformat(),
                "orchestrator_count": len(self.orchestrators),
                "total_queue_depth": total_queue,
                "bridge_uptime_hours": self._calculate_uptime_hours(),
            }

    # ==================== BOTTLENECK DETECTION ====================

    async def detect_bottlenecks(self) -> list[PerformanceBottleneck]:
        """Detect performance bottlenecks in the coordination system"""
        if not self.enable_bottleneck_detection:
            return []

        detected_bottlenecks = []

        with self.metrics_lock:
            for orch_id, metrics in self.orchestrator_metrics.items():
                # Queue saturation detection
                if metrics.queue_size >= 7:  # Approaching 8-task limit
                    bottleneck = PerformanceBottleneck(
                        bottleneck_id=f"queue_saturation_{orch_id}_{int(time.time())}",
                        bottleneck_type="queue_saturation",
                        severity="high" if metrics.queue_size >= 8 else "medium",
                        orchestrator_affected=orch_id,
                        description=f"{orch_id} queue approaching capacity with {metrics.queue_size} tasks",
                        impact_score=min(10.0, metrics.queue_size / metrics.max_tasks * 10),
                        suggested_actions=[
                            "Consider scaling orchestrator instances",
                            "Implement task redistribution",
                            "Review task priorities",
                        ],
                    )
                    detected_bottlenecks.append(bottleneck)

                # Response time degradation
                if metrics.average_response_time_ms > 5000:  # 5+ second responses
                    bottleneck = PerformanceBottleneck(
                        bottleneck_id=f"response_time_{orch_id}_{int(time.time())}",
                        bottleneck_type="response_time_degradation",
                        severity="medium",
                        orchestrator_affected=orch_id,
                        description=f"{orch_id} showing elevated response times: {metrics.average_response_time_ms:.0f}ms",
                        impact_score=min(10.0, metrics.average_response_time_ms / 1000),
                        suggested_actions=[
                            "Investigate task complexity",
                            "Check resource allocation",
                            "Review system performance",
                        ],
                    )
                    detected_bottlenecks.append(bottleneck)

            # Bridge synchronization lag
            sync_lag = self._calculate_sync_lag()
            if sync_lag > 200:  # 200ms+ sync lag
                bottleneck = PerformanceBottleneck(
                    bottleneck_id=f"sync_lag_{int(time.time())}",
                    bottleneck_type="sync_lag",
                    severity="low" if sync_lag < 500 else "medium",
                    orchestrator_affected="coordination_bridge",
                    description=f"Cross-domain context transfer experiencing {sync_lag}ms lag",
                    impact_score=min(10.0, sync_lag / 100),
                    suggested_actions=[
                        "Optimize bridge serialization",
                        "Review network connectivity",
                        "Check Redis performance",
                    ],
                )
                detected_bottlenecks.append(bottleneck)

        # Update bottleneck list
        self.bottlenecks.extend(detected_bottlenecks)

        # Notify if new bottlenecks detected
        if detected_bottlenecks and self.websocket_manager:
            await self._broadcast_bottleneck_alert(detected_bottlenecks)

        return detected_bottlenecks

    # ==================== HELPER METHODS ====================

    def _is_pay_ready_task(self, task: Task) -> bool:
        """Check if task is related to Pay Ready business context"""
        pay_ready_keywords = ["pay_ready", "payment", "billing", "revenue", "sales", "business"]
        task_content = str(task.content).lower()
        return any(keyword in task_content for keyword in pay_ready_keywords)

    def _is_technical_task(self, task: Task) -> bool:
        """Check if task is technical in nature"""
        technical_keywords = [
            "code",
            "debug",
            "optimize",
            "refactor",
            "test",
            "deploy",
            "technical",
        ]
        task_content = str(task.content).lower()
        return any(keyword in task_content for keyword in technical_keywords)

    def _get_routing_reason(self, task: Task, target_orchestrator: str) -> str:
        """Get human-readable reason for routing decision"""
        target_type = self.orchestrator_types.get(target_orchestrator, OrchestratorType.HYBRID)

        if self.routing_strategy == TaskRoutingStrategy.DOMAIN_AFFINITY:
            if self._is_pay_ready_task(task) and target_type == OrchestratorType.SOPHIA:
                return "Pay Ready context requires Sophia business intelligence"
            elif self._is_technical_task(task) and target_type == OrchestratorType.ARTEMIS:
                return "Technical task routed to Artemis code excellence"

        if self.routing_strategy == TaskRoutingStrategy.LEAST_LOADED:
            return f"Selected least loaded orchestrator ({self.orchestrator_metrics[target_orchestrator].utilization_percent:.1f}% utilization)"

        return f"Routed via {self.routing_strategy.value} strategy"

    def _calculate_routing_confidence(self, task: Task, target_orchestrator: str) -> float:
        """Calculate confidence score for routing decision"""
        metrics = self.orchestrator_metrics.get(target_orchestrator)
        if not metrics:
            return 0.5

        # Base confidence from performance metrics
        confidence = (
            metrics.success_rate / 100 * 0.4
            + (100 - metrics.utilization_percent) / 100 * 0.3
            + min(1.0, 1000 / max(metrics.average_response_time_ms, 1)) * 0.3
        )

        # Domain affinity bonus
        if (
            self._is_pay_ready_task(task)
            and self.orchestrator_types.get(target_orchestrator) == OrchestratorType.SOPHIA
        ) or (
            self._is_technical_task(task)
            and self.orchestrator_types.get(target_orchestrator) == OrchestratorType.ARTEMIS
        ):
            confidence *= 1.1

        return min(1.0, max(0.0, confidence))

    def _estimate_performance(self, task: Task, target_orchestrator: str) -> float:
        """Estimate expected performance score for task on target orchestrator"""
        metrics = self.orchestrator_metrics.get(target_orchestrator)
        if not metrics:
            return 0.5

        base_performance = (
            metrics.success_rate * 0.4
            + (100 - metrics.utilization_percent) * 0.3
            + min(100, 1000 / max(metrics.average_response_time_ms, 1)) * 0.3
        )

        return min(100.0, max(0.0, base_performance))

    def _update_routing_metrics(self, routing_time_ms: float, success: bool) -> None:
        """Update bridge routing metrics"""
        self.bridge_metrics.total_tasks_routed += 1
        if success:
            self.bridge_metrics.successful_routes += 1
        else:
            self.bridge_metrics.failed_routes += 1

        # Update average routing time
        current_avg = self.bridge_metrics.average_routing_time_ms
        current_count = self.bridge_metrics.total_tasks_routed
        self.bridge_metrics.average_routing_time_ms = (
            current_avg * (current_count - 1) + routing_time_ms
        ) / current_count

    def _calculate_flow_rate(self) -> float:
        """Calculate tasks per minute flow rate"""
        recent_tasks = [
            event
            for event in self.task_history
            if event.timestamp > datetime.utcnow() - timedelta(minutes=1)
        ]
        return len(recent_tasks)

    def _calculate_sync_lag(self) -> int:
        """Calculate synchronization lag in milliseconds"""
        # Mock calculation - in production would measure actual sync times
        return int(
            self.bridge_metrics.serialization_time_ms + self.bridge_metrics.deserialization_time_ms
        )

    def _calculate_peak_throughput(self) -> float:
        """Calculate peak throughput over recent time window"""
        # Analyze throughput over 5-minute windows
        now = time.time()
        peak_throughput = 0.0

        for window_start in range(int(now - 300), int(now), 60):  # 5-minute window, 1-minute steps
            window_tasks = [
                event
                for event in self.task_history
                if window_start <= event.timestamp.timestamp() < window_start + 60
            ]
            window_throughput = len(window_tasks)
            peak_throughput = max(peak_throughput, window_throughput)

        return peak_throughput

    def _calculate_uptime_hours(self) -> float:
        """Calculate bridge uptime in hours"""
        # Mock implementation - in production would track actual start time
        return 168.5  # Mock 1 week uptime

    async def _broadcast_task_event(self, event: TaskFlowEvent) -> None:
        """Broadcast task flow event via WebSocket"""
        if not self.websocket_manager:
            return

        try:
            message = {
                "type": "task_flow_event",
                "event": {
                    "id": event.event_id,
                    "type": event.event_type,
                    "task_id": event.task_id,
                    "source": event.source_orchestrator,
                    "target": event.target_orchestrator,
                    "task_type": event.task_type,
                    "priority": (
                        event.priority.value
                        if hasattr(event.priority, "value")
                        else str(event.priority)
                    ),
                    "timestamp": event.timestamp.isoformat(),
                    "context_preserved": event.context_preserved,
                    "pay_ready_context": event.pay_ready_context,
                    "metadata": event.metadata,
                },
            }
            await self.websocket_manager.broadcast_to_channel("coordination", message)
        except Exception as e:
            logger.error(f"Failed to broadcast task event: {e}")

    async def _broadcast_bottleneck_alert(self, bottlenecks: list[PerformanceBottleneck]) -> None:
        """Broadcast bottleneck alert via WebSocket"""
        if not self.websocket_manager:
            return

        try:
            message = {
                "type": "bottleneck_alert",
                "bottlenecks": [
                    {
                        "id": b.id,
                        "type": b.type,
                        "severity": b.severity,
                        "orchestrator": b.orchestrator_affected,
                        "description": b.description,
                        "impact_score": b.impact_score,
                        "suggested_actions": b.suggested_actions,
                        "detected_at": b.detected_at.isoformat(),
                    }
                    for b in bottlenecks
                ],
            }
            await self.websocket_manager.broadcast_to_channel("coordination", message)
        except Exception as e:
            logger.error(f"Failed to broadcast bottleneck alert: {e}")

    # ==================== LIFECYCLE MANAGEMENT ====================

    async def start(self) -> None:
        """Start the coordination bridge"""
        if self.is_running:
            return

        self.is_running = True
        self.health_status = BridgeHealthStatus.HEALTHY

        # Start background monitoring tasks
        if self.enable_bottleneck_detection:
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())

        if self.enable_metrics:
            self.metrics_collection_task = asyncio.create_task(self._metrics_collection_loop())

        logger.info("Enhanced Orchestrator Bridge started")

    async def stop(self) -> None:
        """Stop the coordination bridge"""
        self.is_running = False
        self.health_status = BridgeHealthStatus.OFFLINE

        # Cancel background tasks
        if self.monitoring_task:
            self.monitoring_task.cancel()
        if self.metrics_collection_task:
            self.metrics_collection_task.cancel()

        logger.info("Enhanced Orchestrator Bridge stopped")

    async def _monitoring_loop(self) -> None:
        """Background task for continuous monitoring"""
        while self.is_running:
            try:
                await self.detect_bottlenecks()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)  # Back off on errors

    async def _metrics_collection_loop(self) -> None:
        """Background task for metrics collection and health checks"""
        while self.is_running:
            try:
                # Update bridge health score
                self._update_bridge_health()

                # Persist metrics to Redis if available
                if self.redis_manager:
                    await self._persist_metrics()

                await asyncio.sleep(60)  # Update every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collection loop error: {e}")
                await asyncio.sleep(120)  # Back off on errors

    def _update_bridge_health(self) -> None:
        """Update bridge health score based on current metrics"""
        try:
            # Calculate health based on multiple factors
            success_rate_factor = self.bridge_metrics.success_rate / 100
            performance_factor = min(
                1.0, 1000 / max(self.bridge_metrics.average_routing_time_ms, 1)
            )

            orchestrator_health = []
            for metrics in self.orchestrator_metrics.values():
                orch_health = (
                    metrics.success_rate / 100 * 0.4
                    + (100 - metrics.utilization_percent) / 100 * 0.3
                    + min(1.0, 1000 / max(metrics.average_response_time_ms, 1)) * 0.3
                )
                orchestrator_health.append(orch_health)

            avg_orchestrator_health = (
                statistics.mean(orchestrator_health) if orchestrator_health else 1.0
            )

            # Overall health score
            self.bridge_metrics.health_score = (
                success_rate_factor * 0.3 + performance_factor * 0.2 + avg_orchestrator_health * 0.5
            ) * 100

            # Update health status
            if self.bridge_metrics.health_score >= 90:
                self.health_status = BridgeHealthStatus.HEALTHY
            elif self.bridge_metrics.health_score >= 70:
                self.health_status = BridgeHealthStatus.DEGRADED
            else:
                self.health_status = BridgeHealthStatus.CRITICAL

        except Exception as e:
            logger.error(f"Health update error: {e}")
            self.health_status = BridgeHealthStatus.DEGRADED

    async def _persist_metrics(self) -> None:
        """Persist metrics to Redis for historical analysis"""
        try:
            timestamp = int(time.time())
            metrics_data = {
                "timestamp": timestamp,
                "bridge_metrics": {
                    "health_score": self.bridge_metrics.health_score,
                    "total_tasks": self.bridge_metrics.total_tasks_routed,
                    "success_rate": self.bridge_metrics.success_rate,
                    "routing_time_ms": self.bridge_metrics.average_routing_time_ms,
                },
                "orchestrator_metrics": {
                    orch_id: {
                        "active_tasks": metrics.active_tasks,
                        "utilization": metrics.utilization_percent,
                        "success_rate": metrics.success_rate,
                        "response_time": metrics.average_response_time_ms,
                        "queue_size": metrics.queue_size,
                    }
                    for orch_id, metrics in self.orchestrator_metrics.items()
                },
            }

            # Store in Redis with expiration (keep 7 days of metrics)
            await self.redis_manager.setex(
                f"coordination_metrics:{timestamp}", 604800, json.dumps(metrics_data)  # 7 days
            )

        except Exception as e:
            logger.error(f"Failed to persist metrics: {e}")


# ==================== FACTORY FUNCTION ====================


def create_orchestrator_bridge(
    redis_manager: RedisManager, websocket_manager: Optional[WebSocketManager] = None, **kwargs
) -> EnhancedOrchestratorBridge:
    """Factory function to create an enhanced orchestrator bridge"""
    return EnhancedOrchestratorBridge(
        redis_manager=redis_manager, websocket_manager=websocket_manager, **kwargs
    )
