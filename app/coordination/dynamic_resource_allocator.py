"""
Dynamic Resource Allocator
==========================

Intelligent resource allocation system that dynamically distributes computational
resources, budget, and capacity between Sophia and Artemis orchestrators based on:
- Current demand and queue depth
- Historical usage patterns
- Business priority levels
- Performance metrics and SLA requirements
- Cost optimization targets

Features:
- Real-time resource reallocation
- Predictive capacity planning
- Cost-aware resource optimization
- Performance-based scaling decisions
- Emergency resource pooling
"""

import asyncio
import json
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of resources to allocate"""

    COMPUTE_TOKENS = "compute_tokens"
    API_CALLS = "api_calls"
    MEMORY_MB = "memory_mb"
    STORAGE_GB = "storage_gb"
    CONCURRENT_TASKS = "concurrent_tasks"
    BUDGET_USD = "budget_usd"


class OrchestratorType(Enum):
    """Orchestrator types for resource allocation"""

    SOPHIA = "sophia"
    ARTEMIS = "artemis"
    SHARED_POOL = "shared_pool"


class AllocationStrategy(Enum):
    """Resource allocation strategies"""

    EQUAL_SPLIT = "equal_split"  # 50/50 baseline
    DEMAND_BASED = "demand_based"  # Based on queue depth
    HISTORICAL_PATTERN = "historical_pattern"  # Based on usage history
    PRIORITY_WEIGHTED = "priority_weighted"  # Based on task priorities
    COST_OPTIMIZED = "cost_optimized"  # Minimize costs while meeting SLAs
    PERFORMANCE_OPTIMIZED = "performance_optimized"  # Maximize throughput


class ResourcePriority(Enum):
    """Resource allocation priority levels"""

    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class ResourceBudget:
    """Resource budget for an orchestrator"""

    orchestrator: OrchestratorType
    compute_tokens: int = 1000000
    api_calls: int = 10000
    memory_mb: int = 8192
    storage_gb: int = 100
    concurrent_tasks: int = 10
    budget_usd: float = 100.0

    # Usage tracking
    tokens_used: int = 0
    api_calls_used: int = 0
    memory_used: int = 0
    storage_used: int = 0
    active_tasks: int = 0
    budget_spent: float = 0.0

    # Allocation metadata
    last_updated: datetime = field(default_factory=datetime.now)
    allocation_strategy: AllocationStrategy = AllocationStrategy.EQUAL_SPLIT

    def get_utilization_rate(self, resource_type: ResourceType) -> float:
        """Get utilization rate for a specific resource type"""
        utilization_map = {
            ResourceType.COMPUTE_TOKENS: self.tokens_used / max(self.compute_tokens, 1),
            ResourceType.API_CALLS: self.api_calls_used / max(self.api_calls, 1),
            ResourceType.MEMORY_MB: self.memory_used / max(self.memory_mb, 1),
            ResourceType.STORAGE_GB: self.storage_used / max(self.storage_gb, 1),
            ResourceType.CONCURRENT_TASKS: self.active_tasks / max(self.concurrent_tasks, 1),
            ResourceType.BUDGET_USD: self.budget_spent / max(self.budget_usd, 0.01),
        }

        return min(utilization_map.get(resource_type, 0.0), 1.0)

    def get_available_resources(self, resource_type: ResourceType) -> float:
        """Get available resources for a specific type"""
        availability_map = {
            ResourceType.COMPUTE_TOKENS: self.compute_tokens - self.tokens_used,
            ResourceType.API_CALLS: self.api_calls - self.api_calls_used,
            ResourceType.MEMORY_MB: self.memory_mb - self.memory_used,
            ResourceType.STORAGE_GB: self.storage_gb - self.storage_used,
            ResourceType.CONCURRENT_TASKS: self.concurrent_tasks - self.active_tasks,
            ResourceType.BUDGET_USD: self.budget_usd - self.budget_spent,
        }

        return max(availability_map.get(resource_type, 0.0), 0.0)


@dataclass
class AllocationRequest:
    """Request for resource allocation"""

    id: str = field(default_factory=lambda: str(uuid4()))
    orchestrator: OrchestratorType = OrchestratorType.SOPHIA
    resource_type: ResourceType = ResourceType.COMPUTE_TOKENS
    amount: float = 0.0
    priority: ResourcePriority = ResourcePriority.NORMAL
    estimated_duration_minutes: int = 10
    justification: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    # Request metadata
    user_id: Optional[str] = None
    task_id: Optional[str] = None
    cost_sensitivity: float = 0.5  # 0.0 = cost insensitive, 1.0 = very cost sensitive
    performance_requirement: float = 0.5  # 0.0 = best effort, 1.0 = guaranteed performance


@dataclass
class UsageMetrics:
    """Usage metrics for resource allocation decisions"""

    orchestrator: OrchestratorType
    timestamp: datetime = field(default_factory=datetime.now)

    # Queue metrics
    queue_depth: int = 0
    average_wait_time_seconds: float = 0.0
    tasks_completed_last_hour: int = 0
    tasks_failed_last_hour: int = 0

    # Performance metrics
    average_response_time_seconds: float = 0.0
    success_rate: float = 1.0
    resource_efficiency: float = 0.0  # Output per resource unit

    # Cost metrics
    cost_per_task: float = 0.0
    budget_burn_rate_per_hour: float = 0.0

    # Capacity metrics
    peak_concurrent_tasks: int = 0
    average_concurrent_tasks: int = 0
    resource_saturation_events: int = 0


class DynamicResourceAllocator:
    """
    Dynamic resource allocation system for Sophia and Artemis orchestrators
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # Resource budgets for each orchestrator
        self.budgets: Dict[OrchestratorType, ResourceBudget] = {}

        # Usage metrics history (last 24 hours)
        self.usage_history: Dict[OrchestratorType, deque] = {
            OrchestratorType.SOPHIA: deque(maxlen=1440),  # 24 hours * 60 minutes
            OrchestratorType.ARTEMIS: deque(maxlen=1440),
        }

        # Allocation requests queue
        self.pending_requests: List[AllocationRequest] = []
        self.allocation_history: List[Dict[str, Any]] = []

        # Current allocation strategy
        self.current_strategy: AllocationStrategy = AllocationStrategy.DEMAND_BASED

        # Performance metrics
        self.metrics = {
            "total_allocations": 0,
            "successful_allocations": 0,
            "denied_allocations": 0,
            "resource_rebalances": 0,
            "cost_savings": 0.0,
            "performance_improvements": 0.0,
        }

        logger.info("Dynamic Resource Allocator initialized")

        # Initialize default budgets
        self._initialize_default_budgets()

        # Start background monitoring
        asyncio.create_task(self._monitor_and_rebalance())

    def _initialize_default_budgets(self):
        """Initialize default resource budgets"""

        # Get total resources from config or use defaults
        total_resources = self.config.get(
            "total_resources",
            {
                "compute_tokens": 2000000,
                "api_calls": 20000,
                "memory_mb": 16384,
                "storage_gb": 200,
                "concurrent_tasks": 20,
                "budget_usd": 200.0,
            },
        )

        # Equal split baseline (50/50)
        sophia_budget = ResourceBudget(
            orchestrator=OrchestratorType.SOPHIA,
            compute_tokens=total_resources["compute_tokens"] // 2,
            api_calls=total_resources["api_calls"] // 2,
            memory_mb=total_resources["memory_mb"] // 2,
            storage_gb=total_resources["storage_gb"] // 2,
            concurrent_tasks=total_resources["concurrent_tasks"] // 2,
            budget_usd=total_resources["budget_usd"] / 2,
        )

        artemis_budget = ResourceBudget(
            orchestrator=OrchestratorType.ARTEMIS,
            compute_tokens=total_resources["compute_tokens"] // 2,
            api_calls=total_resources["api_calls"] // 2,
            memory_mb=total_resources["memory_mb"] // 2,
            storage_gb=total_resources["storage_gb"] // 2,
            concurrent_tasks=total_resources["concurrent_tasks"] // 2,
            budget_usd=total_resources["budget_usd"] / 2,
        )

        self.budgets[OrchestratorType.SOPHIA] = sophia_budget
        self.budgets[OrchestratorType.ARTEMIS] = artemis_budget

        logger.info("Initialized default resource budgets (50/50 split)")

    async def request_resources(self, request: AllocationRequest) -> Dict[str, Any]:
        """Request resource allocation"""

        logger.info(
            f"Resource allocation request: {request.orchestrator.value} requesting "
            f"{request.amount} {request.resource_type.value}"
        )

        # Check if resources are available
        budget = self.budgets.get(request.orchestrator)
        if not budget:
            return self._create_allocation_response(request, False, "Orchestrator not found")

        available = budget.get_available_resources(request.resource_type)

        if available >= request.amount:
            # Allocate resources
            success = self._allocate_resources(budget, request.resource_type, request.amount)

            if success:
                self.metrics["successful_allocations"] += 1
                self.metrics["total_allocations"] += 1

                # Log allocation
                self.allocation_history.append(
                    {
                        "request_id": request.id,
                        "orchestrator": request.orchestrator.value,
                        "resource_type": request.resource_type.value,
                        "amount": request.amount,
                        "timestamp": datetime.now().isoformat(),
                        "success": True,
                    }
                )

                return self._create_allocation_response(request, True, "Resources allocated")
            else:
                return self._create_allocation_response(request, False, "Allocation failed")

        else:
            # Try emergency rebalancing
            if request.priority in [ResourcePriority.CRITICAL, ResourcePriority.HIGH]:
                logger.info("Attempting emergency rebalancing for high-priority request")

                rebalanced = await self._emergency_rebalance(request)
                if rebalanced:
                    return await self.request_resources(request)  # Retry after rebalancing

            self.metrics["denied_allocations"] += 1
            self.metrics["total_allocations"] += 1

            return self._create_allocation_response(
                request,
                False,
                f"Insufficient resources. Available: {available}, Requested: {request.amount}",
            )

    def _allocate_resources(
        self, budget: ResourceBudget, resource_type: ResourceType, amount: float
    ) -> bool:
        """Allocate resources from budget"""
        try:
            if resource_type == ResourceType.COMPUTE_TOKENS:
                budget.tokens_used += int(amount)
            elif resource_type == ResourceType.API_CALLS:
                budget.api_calls_used += int(amount)
            elif resource_type == ResourceType.MEMORY_MB:
                budget.memory_used += int(amount)
            elif resource_type == ResourceType.STORAGE_GB:
                budget.storage_used += int(amount)
            elif resource_type == ResourceType.CONCURRENT_TASKS:
                budget.active_tasks += int(amount)
            elif resource_type == ResourceType.BUDGET_USD:
                budget.budget_spent += amount

            budget.last_updated = datetime.now()
            return True

        except Exception as e:
            logger.error(f"Failed to allocate resources: {e}")
            return False

    def release_resources(
        self, orchestrator: OrchestratorType, resource_type: ResourceType, amount: float
    ) -> bool:
        """Release allocated resources"""
        budget = self.budgets.get(orchestrator)
        if not budget:
            return False

        try:
            if resource_type == ResourceType.COMPUTE_TOKENS:
                budget.tokens_used = max(0, budget.tokens_used - int(amount))
            elif resource_type == ResourceType.API_CALLS:
                budget.api_calls_used = max(0, budget.api_calls_used - int(amount))
            elif resource_type == ResourceType.MEMORY_MB:
                budget.memory_used = max(0, budget.memory_used - int(amount))
            elif resource_type == ResourceType.STORAGE_GB:
                budget.storage_used = max(0, budget.storage_used - int(amount))
            elif resource_type == ResourceType.CONCURRENT_TASKS:
                budget.active_tasks = max(0, budget.active_tasks - int(amount))
            elif resource_type == ResourceType.BUDGET_USD:
                budget.budget_spent = max(0.0, budget.budget_spent - amount)

            budget.last_updated = datetime.now()
            logger.info(f"Released {amount} {resource_type.value} from {orchestrator.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to release resources: {e}")
            return False

    async def record_usage_metrics(self, metrics: UsageMetrics):
        """Record usage metrics for allocation decisions"""
        self.usage_history[metrics.orchestrator].append(metrics)

        # Trigger rebalancing if needed
        if self._should_rebalance_based_on_metrics(metrics):
            logger.info("Metrics indicate rebalancing needed")
            await self._rebalance_resources()

    def _should_rebalance_based_on_metrics(self, metrics: UsageMetrics) -> bool:
        """Determine if rebalancing is needed based on metrics"""

        # Rebalance if queue is building up
        if metrics.queue_depth > 5:
            return True

        # Rebalance if wait times are high
        if metrics.average_wait_time_seconds > 30:
            return True

        # Rebalance if success rate is dropping
        if metrics.success_rate < 0.95:
            return True

        # Rebalance if resource saturation is occurring
        if metrics.resource_saturation_events > 0:
            return True

        return False

    async def _rebalance_resources(self):
        """Rebalance resources between orchestrators"""
        logger.info("Starting resource rebalancing")

        try:
            # Get current metrics
            sophia_metrics = self._get_latest_metrics(OrchestratorType.SOPHIA)
            artemis_metrics = self._get_latest_metrics(OrchestratorType.ARTEMIS)

            if not sophia_metrics or not artemis_metrics:
                logger.warning("Insufficient metrics for rebalancing")
                return

            # Calculate rebalancing based on current strategy
            new_allocations = self._calculate_optimal_allocation(sophia_metrics, artemis_metrics)

            # Apply new allocations
            await self._apply_allocations(new_allocations)

            self.metrics["resource_rebalances"] += 1
            logger.info("Resource rebalancing completed")

        except Exception as e:
            logger.error(f"Resource rebalancing failed: {e}")

    def _get_latest_metrics(self, orchestrator: OrchestratorType) -> Optional[UsageMetrics]:
        """Get latest metrics for an orchestrator"""
        history = self.usage_history.get(orchestrator)
        return history[-1] if history else None

    def _calculate_optimal_allocation(
        self, sophia_metrics: UsageMetrics, artemis_metrics: UsageMetrics
    ) -> Dict[OrchestratorType, ResourceBudget]:
        """Calculate optimal resource allocation based on metrics and strategy"""

        total_resources = self._calculate_total_resources()

        if self.current_strategy == AllocationStrategy.DEMAND_BASED:
            return self._demand_based_allocation(sophia_metrics, artemis_metrics, total_resources)
        elif self.current_strategy == AllocationStrategy.PERFORMANCE_OPTIMIZED:
            return self._performance_based_allocation(
                sophia_metrics, artemis_metrics, total_resources
            )
        elif self.current_strategy == AllocationStrategy.COST_OPTIMIZED:
            return self._cost_optimized_allocation(sophia_metrics, artemis_metrics, total_resources)
        else:
            return self._equal_split_allocation(total_resources)

    def _demand_based_allocation(
        self,
        sophia_metrics: UsageMetrics,
        artemis_metrics: UsageMetrics,
        total_resources: Dict[str, float],
    ) -> Dict[OrchestratorType, ResourceBudget]:
        """Allocate resources based on demand (queue depth and throughput)"""

        sophia_demand = sophia_metrics.queue_depth + sophia_metrics.tasks_completed_last_hour
        artemis_demand = artemis_metrics.queue_depth + artemis_metrics.tasks_completed_last_hour

        total_demand = sophia_demand + artemis_demand

        if total_demand == 0:
            return self._equal_split_allocation(total_resources)

        # Calculate allocation ratios
        sophia_ratio = sophia_demand / total_demand
        artemis_ratio = artemis_demand / total_demand

        # Apply bounds (minimum 20%, maximum 80%)
        sophia_ratio = max(0.2, min(0.8, sophia_ratio))
        artemis_ratio = 1.0 - sophia_ratio

        logger.info(
            f"Demand-based allocation: Sophia {sophia_ratio:.1%}, Artemis {artemis_ratio:.1%}"
        )

        return {
            OrchestratorType.SOPHIA: self._create_budget_from_ratio(sophia_ratio, total_resources),
            OrchestratorType.ARTEMIS: self._create_budget_from_ratio(
                artemis_ratio, total_resources
            ),
        }

    def _performance_based_allocation(
        self,
        sophia_metrics: UsageMetrics,
        artemis_metrics: UsageMetrics,
        total_resources: Dict[str, float],
    ) -> Dict[OrchestratorType, ResourceBudget]:
        """Allocate resources to optimize overall performance"""

        # Factor in success rate and response time
        sophia_performance = sophia_metrics.success_rate / max(
            sophia_metrics.average_response_time_seconds, 0.1
        )
        artemis_performance = artemis_metrics.success_rate / max(
            artemis_metrics.average_response_time_seconds, 0.1
        )

        total_performance = sophia_performance + artemis_performance

        if total_performance == 0:
            return self._equal_split_allocation(total_resources)

        # Allocate more resources to the more efficient orchestrator
        sophia_ratio = sophia_performance / total_performance
        artemis_ratio = artemis_performance / total_performance

        # Apply bounds
        sophia_ratio = max(0.2, min(0.8, sophia_ratio))
        artemis_ratio = 1.0 - sophia_ratio

        logger.info(
            f"Performance-based allocation: Sophia {sophia_ratio:.1%}, Artemis {artemis_ratio:.1%}"
        )

        return {
            OrchestratorType.SOPHIA: self._create_budget_from_ratio(sophia_ratio, total_resources),
            OrchestratorType.ARTEMIS: self._create_budget_from_ratio(
                artemis_ratio, total_resources
            ),
        }

    def _cost_optimized_allocation(
        self,
        sophia_metrics: UsageMetrics,
        artemis_metrics: UsageMetrics,
        total_resources: Dict[str, float],
    ) -> Dict[OrchestratorType, ResourceBudget]:
        """Allocate resources to minimize costs while maintaining performance"""

        # Factor in cost per task and resource efficiency
        sophia_efficiency = sophia_metrics.resource_efficiency / max(
            sophia_metrics.cost_per_task, 0.01
        )
        artemis_efficiency = artemis_metrics.resource_efficiency / max(
            artemis_metrics.cost_per_task, 0.01
        )

        total_efficiency = sophia_efficiency + artemis_efficiency

        if total_efficiency == 0:
            return self._equal_split_allocation(total_resources)

        # Allocate more resources to the more cost-efficient orchestrator
        sophia_ratio = sophia_efficiency / total_efficiency
        artemis_ratio = artemis_efficiency / total_efficiency

        # Apply bounds
        sophia_ratio = max(0.2, min(0.8, sophia_ratio))
        artemis_ratio = 1.0 - sophia_ratio

        logger.info(
            f"Cost-optimized allocation: Sophia {sophia_ratio:.1%}, Artemis {artemis_ratio:.1%}"
        )

        return {
            OrchestratorType.SOPHIA: self._create_budget_from_ratio(sophia_ratio, total_resources),
            OrchestratorType.ARTEMIS: self._create_budget_from_ratio(
                artemis_ratio, total_resources
            ),
        }

    def _equal_split_allocation(
        self, total_resources: Dict[str, float]
    ) -> Dict[OrchestratorType, ResourceBudget]:
        """50/50 equal split allocation"""
        return {
            OrchestratorType.SOPHIA: self._create_budget_from_ratio(0.5, total_resources),
            OrchestratorType.ARTEMIS: self._create_budget_from_ratio(0.5, total_resources),
        }

    def _create_budget_from_ratio(
        self, ratio: float, total_resources: Dict[str, float]
    ) -> ResourceBudget:
        """Create resource budget from allocation ratio"""
        return ResourceBudget(
            orchestrator=OrchestratorType.SOPHIA if ratio > 0.5 else OrchestratorType.ARTEMIS,
            compute_tokens=int(total_resources["compute_tokens"] * ratio),
            api_calls=int(total_resources["api_calls"] * ratio),
            memory_mb=int(total_resources["memory_mb"] * ratio),
            storage_gb=int(total_resources["storage_gb"] * ratio),
            concurrent_tasks=int(total_resources["concurrent_tasks"] * ratio),
            budget_usd=total_resources["budget_usd"] * ratio,
            allocation_strategy=self.current_strategy,
            last_updated=datetime.now(),
        )

    def _calculate_total_resources(self) -> Dict[str, float]:
        """Calculate total available resources"""
        sophia_budget = self.budgets.get(OrchestratorType.SOPHIA)
        artemis_budget = self.budgets.get(OrchestratorType.ARTEMIS)

        if not sophia_budget or not artemis_budget:
            return {}

        return {
            "compute_tokens": sophia_budget.compute_tokens + artemis_budget.compute_tokens,
            "api_calls": sophia_budget.api_calls + artemis_budget.api_calls,
            "memory_mb": sophia_budget.memory_mb + artemis_budget.memory_mb,
            "storage_gb": sophia_budget.storage_gb + artemis_budget.storage_gb,
            "concurrent_tasks": sophia_budget.concurrent_tasks + artemis_budget.concurrent_tasks,
            "budget_usd": sophia_budget.budget_usd + artemis_budget.budget_usd,
        }

    async def _apply_allocations(self, new_allocations: Dict[OrchestratorType, ResourceBudget]):
        """Apply new resource allocations"""
        for orchestrator, new_budget in new_allocations.items():
            current_budget = self.budgets.get(orchestrator)
            if current_budget:
                # Preserve usage tracking
                new_budget.tokens_used = current_budget.tokens_used
                new_budget.api_calls_used = current_budget.api_calls_used
                new_budget.memory_used = current_budget.memory_used
                new_budget.storage_used = current_budget.storage_used
                new_budget.active_tasks = current_budget.active_tasks
                new_budget.budget_spent = current_budget.budget_spent

                # Update budget
                self.budgets[orchestrator] = new_budget

                logger.info(f"Updated resource allocation for {orchestrator.value}")

    async def _emergency_rebalance(self, urgent_request: AllocationRequest) -> bool:
        """Emergency resource rebalancing for critical requests"""
        logger.warning(f"Emergency rebalancing for critical request: {urgent_request.id}")

        # Try to borrow resources from the other orchestrator
        other_orchestrator = (
            OrchestratorType.ARTEMIS
            if urgent_request.orchestrator == OrchestratorType.SOPHIA
            else OrchestratorType.SOPHIA
        )

        other_budget = self.budgets.get(other_orchestrator)
        if not other_budget:
            return False

        # Check if other orchestrator can spare resources
        other_available = other_budget.get_available_resources(urgent_request.resource_type)
        other_utilization = other_budget.get_utilization_rate(urgent_request.resource_type)

        # Only borrow if other orchestrator has low utilization and enough resources
        if other_utilization < 0.7 and other_available >= urgent_request.amount:
            # Transfer resources temporarily
            requesting_budget = self.budgets.get(urgent_request.orchestrator)
            if requesting_budget:
                # Move resources
                self._transfer_resources(
                    other_budget,
                    requesting_budget,
                    urgent_request.resource_type,
                    urgent_request.amount,
                )

                logger.info(
                    f"Emergency resource transfer completed: {urgent_request.amount} "
                    f"{urgent_request.resource_type.value} from {other_orchestrator.value} "
                    f"to {urgent_request.orchestrator.value}"
                )
                return True

        return False

    def _transfer_resources(
        self,
        from_budget: ResourceBudget,
        to_budget: ResourceBudget,
        resource_type: ResourceType,
        amount: float,
    ):
        """Transfer resources between budgets"""

        if resource_type == ResourceType.COMPUTE_TOKENS:
            from_budget.compute_tokens -= int(amount)
            to_budget.compute_tokens += int(amount)
        elif resource_type == ResourceType.API_CALLS:
            from_budget.api_calls -= int(amount)
            to_budget.api_calls += int(amount)
        elif resource_type == ResourceType.MEMORY_MB:
            from_budget.memory_mb -= int(amount)
            to_budget.memory_mb += int(amount)
        elif resource_type == ResourceType.STORAGE_GB:
            from_budget.storage_gb -= int(amount)
            to_budget.storage_gb += int(amount)
        elif resource_type == ResourceType.CONCURRENT_TASKS:
            from_budget.concurrent_tasks -= int(amount)
            to_budget.concurrent_tasks += int(amount)
        elif resource_type == ResourceType.BUDGET_USD:
            from_budget.budget_usd -= amount
            to_budget.budget_usd += amount

        # Update timestamps
        from_budget.last_updated = datetime.now()
        to_budget.last_updated = datetime.now()

    def _create_allocation_response(
        self, request: AllocationRequest, success: bool, message: str
    ) -> Dict[str, Any]:
        """Create response for allocation request"""
        return {
            "request_id": request.id,
            "success": success,
            "message": message,
            "orchestrator": request.orchestrator.value,
            "resource_type": request.resource_type.value,
            "amount_requested": request.amount,
            "timestamp": datetime.now().isoformat(),
            "budget_status": self._get_budget_status(request.orchestrator) if success else None,
        }

    def _get_budget_status(self, orchestrator: OrchestratorType) -> Dict[str, Any]:
        """Get current budget status for an orchestrator"""
        budget = self.budgets.get(orchestrator)
        if not budget:
            return {}

        return {
            "compute_tokens": {
                "total": budget.compute_tokens,
                "used": budget.tokens_used,
                "available": budget.compute_tokens - budget.tokens_used,
                "utilization": budget.get_utilization_rate(ResourceType.COMPUTE_TOKENS),
            },
            "api_calls": {
                "total": budget.api_calls,
                "used": budget.api_calls_used,
                "available": budget.api_calls - budget.api_calls_used,
                "utilization": budget.get_utilization_rate(ResourceType.API_CALLS),
            },
            "budget_usd": {
                "total": budget.budget_usd,
                "spent": budget.budget_spent,
                "available": budget.budget_usd - budget.budget_spent,
                "utilization": budget.get_utilization_rate(ResourceType.BUDGET_USD),
            },
            "concurrent_tasks": {
                "limit": budget.concurrent_tasks,
                "active": budget.active_tasks,
                "available": budget.concurrent_tasks - budget.active_tasks,
            },
        }

    async def _monitor_and_rebalance(self):
        """Background task to monitor usage and rebalance resources"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes

                # Check if automatic rebalancing is needed
                if self._should_perform_scheduled_rebalance():
                    await self._rebalance_resources()

            except Exception as e:
                logger.error(f"Background monitoring error: {e}")

    def _should_perform_scheduled_rebalance(self) -> bool:
        """Determine if scheduled rebalancing should be performed"""

        # Check if enough time has passed since last rebalance
        for budget in self.budgets.values():
            if datetime.now() - budget.last_updated < timedelta(minutes=10):
                return False

        # Check utilization imbalances
        sophia_budget = self.budgets.get(OrchestratorType.SOPHIA)
        artemis_budget = self.budgets.get(OrchestratorType.ARTEMIS)

        if not sophia_budget or not artemis_budget:
            return False

        # Calculate average utilization
        sophia_util = sum(sophia_budget.get_utilization_rate(rt) for rt in ResourceType) / len(
            ResourceType
        )
        artemis_util = sum(artemis_budget.get_utilization_rate(rt) for rt in ResourceType) / len(
            ResourceType
        )

        # Rebalance if utilization is significantly different
        utilization_diff = abs(sophia_util - artemis_util)
        return utilization_diff > 0.3  # 30% utilization difference threshold

    def set_allocation_strategy(self, strategy: AllocationStrategy):
        """Set the resource allocation strategy"""
        self.current_strategy = strategy
        logger.info(f"Allocation strategy changed to: {strategy.value}")

    def get_allocation_status(self) -> Dict[str, Any]:
        """Get current allocation status and metrics"""
        return {
            "current_strategy": self.current_strategy.value,
            "metrics": self.metrics.copy(),
            "budgets": {
                orchestrator.value: {
                    "resource_limits": {
                        "compute_tokens": budget.compute_tokens,
                        "api_calls": budget.api_calls,
                        "budget_usd": budget.budget_usd,
                        "concurrent_tasks": budget.concurrent_tasks,
                    },
                    "utilization": {
                        resource_type.value: budget.get_utilization_rate(resource_type)
                        for resource_type in ResourceType
                    },
                    "last_updated": budget.last_updated.isoformat(),
                }
                for orchestrator, budget in self.budgets.items()
            },
            "recent_allocations": self.allocation_history[-10:] if self.allocation_history else [],
        }

    def predict_resource_needs(
        self, hours_ahead: int = 4
    ) -> Dict[OrchestratorType, Dict[str, float]]:
        """Predict resource needs based on historical patterns"""
        predictions = {}

        for orchestrator in [OrchestratorType.SOPHIA, OrchestratorType.ARTEMIS]:
            history = self.usage_history.get(orchestrator, [])

            if len(history) < 10:  # Need at least 10 data points
                predictions[orchestrator] = {"confidence": 0.0, "predicted_load": 0.5}
                continue

            # Simple trend analysis (would use more sophisticated ML in production)
            recent_metrics = list(history)[-10:]
            avg_queue_depth = sum(m.queue_depth for m in recent_metrics) / len(recent_metrics)
            avg_tasks_completed = sum(m.tasks_completed_last_hour for m in recent_metrics) / len(
                recent_metrics
            )

            # Predict load based on trends
            trend = (recent_metrics[-1].queue_depth - recent_metrics[0].queue_depth) / len(
                recent_metrics
            )
            predicted_queue = max(0, avg_queue_depth + (trend * hours_ahead))

            predicted_load = min(1.0, predicted_queue / 10.0)  # Normalize to 0-1
            confidence = min(1.0, len(history) / 100.0)  # Confidence based on data points

            predictions[orchestrator] = {
                "predicted_load": predicted_load,
                "predicted_queue_depth": predicted_queue,
                "predicted_tasks_per_hour": avg_tasks_completed * (1 + predicted_load),
                "confidence": confidence,
                "hours_ahead": hours_ahead,
            }

        return predictions


# Global resource allocator instance
_resource_allocator = None


def get_resource_allocator() -> DynamicResourceAllocator:
    """Get singleton resource allocator instance"""
    global _resource_allocator
    if _resource_allocator is None:
        _resource_allocator = DynamicResourceAllocator()
    return _resource_allocator


# Convenience functions


async def request_compute_tokens(
    orchestrator: OrchestratorType,
    amount: int,
    priority: ResourcePriority = ResourcePriority.NORMAL,
) -> Dict[str, Any]:
    """Request compute tokens for an orchestrator"""
    allocator = get_resource_allocator()
    request = AllocationRequest(
        orchestrator=orchestrator,
        resource_type=ResourceType.COMPUTE_TOKENS,
        amount=amount,
        priority=priority,
    )
    return await allocator.request_resources(request)


async def request_budget(
    orchestrator: OrchestratorType,
    amount: float,
    priority: ResourcePriority = ResourcePriority.NORMAL,
) -> Dict[str, Any]:
    """Request budget allocation for an orchestrator"""
    allocator = get_resource_allocator()
    request = AllocationRequest(
        orchestrator=orchestrator,
        resource_type=ResourceType.BUDGET_USD,
        amount=amount,
        priority=priority,
    )
    return await allocator.request_resources(request)


async def release_compute_tokens(orchestrator: OrchestratorType, amount: int) -> bool:
    """Release compute tokens back to the pool"""
    allocator = get_resource_allocator()
    return allocator.release_resources(orchestrator, ResourceType.COMPUTE_TOKENS, amount)


def switch_to_cost_optimization():
    """Switch to cost optimization strategy"""
    allocator = get_resource_allocator()
    allocator.set_allocation_strategy(AllocationStrategy.COST_OPTIMIZED)


def switch_to_performance_optimization():
    """Switch to performance optimization strategy"""
    allocator = get_resource_allocator()
    allocator.set_allocation_strategy(AllocationStrategy.PERFORMANCE_OPTIMIZED)


# Example usage
async def example_resource_allocation():
    """Example of resource allocation usage"""

    allocator = get_resource_allocator()

    # Request resources for Sophia
    sophia_request = await request_compute_tokens(
        OrchestratorType.SOPHIA, 50000, ResourcePriority.HIGH
    )
    print("Sophia token request:", sophia_request)

    # Request resources for Artemis
    artemis_request = await request_budget(OrchestratorType.ARTEMIS, 25.0, ResourcePriority.NORMAL)
    print("Artemis budget request:", artemis_request)

    # Check allocation status
    status = allocator.get_allocation_status()
    print("Allocation status:", json.dumps(status, indent=2, default=str))

    # Simulate usage metrics
    sophia_metrics = UsageMetrics(
        orchestrator=OrchestratorType.SOPHIA,
        queue_depth=3,
        tasks_completed_last_hour=45,
        average_response_time_seconds=2.1,
        success_rate=0.97,
        cost_per_task=0.12,
    )

    await allocator.record_usage_metrics(sophia_metrics)

    # Get predictions
    predictions = allocator.predict_resource_needs(hours_ahead=6)
    print("Resource predictions:", json.dumps(predictions, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(example_resource_allocation())
