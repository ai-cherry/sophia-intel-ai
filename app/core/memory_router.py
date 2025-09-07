"""
Memory Router - Intelligent routing and load balancing for memory operations
Provides intelligent routing, load balancing, and failover across memory tiers
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from app.core.unified_memory import (
    MemoryContext,
    MemoryEntry,
    MemoryMetadata,
    MemoryPriority,
    MemorySearchRequest,
    MemorySearchResult,
    MemoryTier,
    unified_memory,
)

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Memory routing strategies"""

    PERFORMANCE_FIRST = "performance_first"  # Route to fastest available tier
    RELIABILITY_FIRST = "reliability_first"  # Route to most reliable tier
    COST_OPTIMIZED = "cost_optimized"  # Route to most cost-effective tier
    BALANCED = "balanced"  # Balance performance, reliability, cost
    INTELLIGENT = "intelligent"  # AI-driven routing decisions


class LoadBalancingAlgorithm(Enum):
    """Load balancing algorithms"""

    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RESPONSE_TIME_BASED = "response_time_based"
    CAPACITY_BASED = "capacity_based"


@dataclass
class TierHealth:
    """Health status for a memory tier"""

    tier: MemoryTier
    available: bool = True
    response_time_ms: float = 0.0
    error_rate: float = 0.0
    capacity_usage: float = 0.0
    connection_count: int = 0
    last_health_check: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    consecutive_failures: int = 0
    quality_score: float = 1.0


@dataclass
class RoutingMetrics:
    """Routing performance metrics"""

    total_requests: int = 0
    successful_routes: int = 0
    failed_routes: int = 0
    average_response_time_ms: float = 0.0
    tier_usage_count: Dict[str, int] = field(default_factory=dict)
    routing_decisions: Dict[str, int] = field(default_factory=dict)
    fallback_count: int = 0
    circuit_breaker_trips: int = 0


@dataclass
class RoutingRule:
    """Custom routing rule"""

    rule_id: str
    name: str
    conditions: Dict[str, Any]  # Conditions to match
    target_tiers: List[MemoryTier]  # Preferred tiers in order
    priority: int = 5  # Rule priority (1-10)
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class CircuitBreaker:
    """Circuit breaker for memory tier protection"""

    def __init__(self, tier: MemoryTier, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.tier = tier
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

    def should_allow_request(self) -> bool:
        """Check if request should be allowed through"""
        if self.state == "closed":
            return True
        elif self.state == "open":
            if self._should_attempt_recovery():
                self.state = "half_open"
                return True
            return False
        else:  # half_open
            return True

    def record_success(self):
        """Record successful operation"""
        self.failure_count = 0
        self.state = "closed"

    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc)

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened for tier {self.tier.value}")

    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if self.last_failure_time is None:
            return True

        time_since_failure = (datetime.now(timezone.utc) - self.last_failure_time).total_seconds()
        return time_since_failure >= self.recovery_timeout


class MemoryRouter:
    """
    Intelligent Memory Router with load balancing and failover capabilities
    Routes memory operations to optimal tiers based on various strategies
    """

    def __init__(self):
        self.memory_interface = unified_memory
        self.routing_strategy = RoutingStrategy.INTELLIGENT
        self.load_balancing_algorithm = LoadBalancingAlgorithm.RESPONSE_TIME_BASED

        # Health monitoring
        self.tier_health: Dict[MemoryTier, TierHealth] = {}
        self.circuit_breakers: Dict[MemoryTier, CircuitBreaker] = {}

        # Routing rules and metrics
        self.custom_rules: List[RoutingRule] = []
        self.metrics = RoutingMetrics()

        # Configuration
        self.config = {
            "health_check_interval": 30,  # seconds
            "circuit_breaker_threshold": 5,
            "circuit_breaker_timeout": 60,
            "max_retries": 3,
            "timeout_seconds": 30,
            "tier_weights": {
                MemoryTier.L1_CACHE: 1.0,
                MemoryTier.L2_SEMANTIC: 0.8,
                MemoryTier.L3_PERSISTENT: 0.6,
                MemoryTier.L4_ARCHIVE: 0.4,
            },
        }

        # Initialize components
        self._initialize_health_monitoring()
        self._initialize_circuit_breakers()

        # Start background tasks
        self._health_check_task = None

    async def initialize(self):
        """Initialize memory router"""
        try:
            # Start health monitoring
            if not self._health_check_task:
                self._health_check_task = asyncio.create_task(self._health_check_loop())

            logger.info("Memory router initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize memory router: {e}")
            raise

    async def route_store_operation(
        self, content: str, metadata: MemoryMetadata, embedding: Optional[List[float]] = None
    ) -> Tuple[str, List[MemoryTier]]:
        """Route a store operation to optimal tiers"""

        start_time = time.time()

        try:
            # Determine optimal tiers based on routing strategy
            target_tiers = await self._determine_store_tiers(metadata)

            # Apply custom routing rules
            target_tiers = self._apply_routing_rules(target_tiers, metadata, "store")

            # Filter healthy tiers
            healthy_tiers = await self._filter_healthy_tiers(target_tiers)

            if not healthy_tiers:
                # Fallback to any available tier
                healthy_tiers = await self._get_fallback_tiers()
                self.metrics.fallback_count += 1

            # Attempt to store in each tier
            successful_tiers = []
            memory_id = metadata.memory_id

            for tier in healthy_tiers:
                try:
                    if await self._store_in_tier(tier, memory_id, content, metadata, embedding):
                        successful_tiers.append(tier)
                        self.circuit_breakers[tier].record_success()
                        self._update_tier_metrics(tier, time.time() - start_time, True)
                    else:
                        self.circuit_breakers[tier].record_failure()
                        self._update_tier_metrics(tier, time.time() - start_time, False)

                except Exception as e:
                    logger.error(f"Failed to store in tier {tier.value}: {e}")
                    self.circuit_breakers[tier].record_failure()
                    self._update_tier_metrics(tier, time.time() - start_time, False)

            # Update routing metrics
            self.metrics.total_requests += 1
            if successful_tiers:
                self.metrics.successful_routes += 1
            else:
                self.metrics.failed_routes += 1

            return memory_id, successful_tiers

        except Exception as e:
            logger.error(f"Route store operation failed: {e}")
            self.metrics.failed_routes += 1
            return metadata.memory_id, []

    async def route_retrieve_operation(
        self, memory_id: str, priority: MemoryPriority = MemoryPriority.STANDARD
    ) -> Optional[MemoryEntry]:
        """Route a retrieve operation to optimal tier"""

        start_time = time.time()

        try:
            # Determine tier access order based on priority
            tier_order = self._get_tier_access_order(priority)

            # Filter healthy tiers
            healthy_tiers = await self._filter_healthy_tiers(tier_order)

            # Try each tier in order
            for tier in healthy_tiers:
                try:
                    if not self.circuit_breakers[tier].should_allow_request():
                        continue

                    entry = await self._retrieve_from_tier(tier, memory_id)
                    if entry:
                        self.circuit_breakers[tier].record_success()
                        self._update_tier_metrics(tier, time.time() - start_time, True)

                        # Update routing metrics
                        self.metrics.total_requests += 1
                        self.metrics.successful_routes += 1

                        return entry

                except Exception as e:
                    logger.error(f"Failed to retrieve from tier {tier.value}: {e}")
                    self.circuit_breakers[tier].record_failure()
                    self._update_tier_metrics(tier, time.time() - start_time, False)

            # No successful retrieval
            self.metrics.total_requests += 1
            self.metrics.failed_routes += 1
            return None

        except Exception as e:
            logger.error(f"Route retrieve operation failed: {e}")
            self.metrics.failed_routes += 1
            return None

    async def route_search_operation(
        self, request: MemorySearchRequest
    ) -> List[MemorySearchResult]:
        """Route a search operation across appropriate tiers"""

        start_time = time.time()

        try:
            # Determine which tiers to search based on request
            search_tiers = await self._determine_search_tiers(request)

            # Apply load balancing for parallel searches
            balanced_tiers = self._apply_load_balancing(search_tiers)

            # Filter healthy tiers
            healthy_tiers = await self._filter_healthy_tiers(balanced_tiers)

            if not healthy_tiers:
                return []

            # Execute parallel searches
            search_tasks = []
            for tier in healthy_tiers:
                if self.circuit_breakers[tier].should_allow_request():
                    search_tasks.append(self._search_tier(tier, request))

            if not search_tasks:
                return []

            # Gather results
            tier_results = await asyncio.gather(*search_tasks, return_exceptions=True)

            # Aggregate and rank results
            all_results = []
            for i, results in enumerate(tier_results):
                tier = healthy_tiers[i]
                if isinstance(results, Exception):
                    logger.warning(f"Search failed for tier {tier.value}: {results}")
                    self.circuit_breakers[tier].record_failure()
                    self._update_tier_metrics(tier, time.time() - start_time, False)
                else:
                    self.circuit_breakers[tier].record_success()
                    self._update_tier_metrics(tier, time.time() - start_time, True)
                    if isinstance(results, list):
                        all_results.extend(results)

            # Deduplicate and rank
            unique_results = self._deduplicate_search_results(all_results)
            ranked_results = self._rank_search_results(unique_results, request)

            # Update metrics
            self.metrics.total_requests += 1
            if all_results:
                self.metrics.successful_routes += 1
            else:
                self.metrics.failed_routes += 1

            return ranked_results[: request.max_results]

        except Exception as e:
            logger.error(f"Route search operation failed: {e}")
            self.metrics.failed_routes += 1
            return []

    async def add_routing_rule(self, rule: RoutingRule) -> bool:
        """Add custom routing rule"""
        try:
            # Validate rule
            if not self._validate_routing_rule(rule):
                return False

            # Add to rules list (sorted by priority)
            self.custom_rules.append(rule)
            self.custom_rules.sort(key=lambda r: r.priority, reverse=True)

            logger.info(f"Added routing rule: {rule.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to add routing rule: {e}")
            return False

    async def remove_routing_rule(self, rule_id: str) -> bool:
        """Remove custom routing rule"""
        try:
            initial_count = len(self.custom_rules)
            self.custom_rules = [r for r in self.custom_rules if r.rule_id != rule_id]

            if len(self.custom_rules) < initial_count:
                logger.info(f"Removed routing rule: {rule_id}")
                return True
            else:
                logger.warning(f"Routing rule not found: {rule_id}")
                return False

        except Exception as e:
            logger.error(f"Failed to remove routing rule: {e}")
            return False

    async def get_routing_status(self) -> Dict[str, Any]:
        """Get comprehensive routing status"""

        return {
            "routing_strategy": self.routing_strategy.value,
            "load_balancing_algorithm": self.load_balancing_algorithm.value,
            "tier_health": {
                tier.value: {
                    "available": health.available,
                    "response_time_ms": health.response_time_ms,
                    "error_rate": health.error_rate,
                    "capacity_usage": health.capacity_usage,
                    "connection_count": health.connection_count,
                    "quality_score": health.quality_score,
                    "consecutive_failures": health.consecutive_failures,
                }
                for tier, health in self.tier_health.items()
            },
            "circuit_breakers": {
                tier.value: {
                    "state": cb.state,
                    "failure_count": cb.failure_count,
                    "last_failure": (
                        cb.last_failure_time.isoformat() if cb.last_failure_time else None
                    ),
                }
                for tier, cb in self.circuit_breakers.items()
            },
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "successful_routes": self.metrics.successful_routes,
                "failed_routes": self.metrics.failed_routes,
                "success_rate": (
                    (self.metrics.successful_routes / self.metrics.total_requests)
                    if self.metrics.total_requests > 0
                    else 0
                ),
                "average_response_time_ms": self.metrics.average_response_time_ms,
                "tier_usage_count": self.metrics.tier_usage_count,
                "fallback_count": self.metrics.fallback_count,
                "circuit_breaker_trips": self.metrics.circuit_breaker_trips,
            },
            "active_routing_rules": len([r for r in self.custom_rules if r.enabled]),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # Private helper methods

    def _initialize_health_monitoring(self):
        """Initialize health monitoring for all tiers"""
        for tier in MemoryTier:
            self.tier_health[tier] = TierHealth(tier=tier)

    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for all tiers"""
        for tier in MemoryTier:
            self.circuit_breakers[tier] = CircuitBreaker(
                tier=tier,
                failure_threshold=self.config["circuit_breaker_threshold"],
                recovery_timeout=self.config["circuit_breaker_timeout"],
            )

    async def _health_check_loop(self):
        """Background health check loop"""
        while True:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.config["health_check_interval"])
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(10)  # Short delay before retry

    async def _perform_health_checks(self):
        """Perform health checks on all tiers"""

        health_tasks = []
        for tier in MemoryTier:
            health_tasks.append(self._check_tier_health(tier))

        await asyncio.gather(*health_tasks, return_exceptions=True)

    async def _check_tier_health(self, tier: MemoryTier):
        """Check health of a specific tier"""

        start_time = time.time()
        health = self.tier_health[tier]

        try:
            # Attempt a simple health check operation
            if tier == MemoryTier.L1_CACHE:
                if self.memory_interface.redis_manager:
                    health_result = await self.memory_interface.redis_manager.health_check()
                    health.available = health_result.get("healthy", False)
                else:
                    health.available = False

            elif tier == MemoryTier.L2_SEMANTIC:
                if self.memory_interface.vector_manager:
                    # Test primary vector DB
                    from app.core.vector_db_config import VectorDBType

                    health.available = self.memory_interface.vector_manager.test_connection(
                        VectorDBType.QDRANT
                    )
                else:
                    health.available = False

            elif tier == MemoryTier.L3_PERSISTENT:
                if self.memory_interface.mem0_manager:
                    health.available = self.memory_interface.mem0_manager.test_connection()
                else:
                    health.available = False

            else:
                health.available = False  # L4_ARCHIVE not implemented yet

            # Update metrics
            response_time = (time.time() - start_time) * 1000
            health.response_time_ms = response_time
            health.last_health_check = datetime.now(timezone.utc)

            if health.available:
                health.consecutive_failures = 0
                health.quality_score = min(1.0, health.quality_score + 0.1)
            else:
                health.consecutive_failures += 1
                health.quality_score = max(0.1, health.quality_score - 0.2)

        except Exception as e:
            logger.error(f"Health check failed for tier {tier.value}: {e}")
            health.available = False
            health.consecutive_failures += 1
            health.quality_score = max(0.1, health.quality_score - 0.2)

    async def _determine_store_tiers(self, metadata: MemoryMetadata) -> List[MemoryTier]:
        """Determine optimal storage tiers based on metadata and strategy"""

        if self.routing_strategy == RoutingStrategy.PERFORMANCE_FIRST:
            return self._get_performance_optimized_tiers(metadata)
        elif self.routing_strategy == RoutingStrategy.RELIABILITY_FIRST:
            return self._get_reliability_optimized_tiers(metadata)
        elif self.routing_strategy == RoutingStrategy.COST_OPTIMIZED:
            return self._get_cost_optimized_tiers(metadata)
        elif self.routing_strategy == RoutingStrategy.INTELLIGENT:
            return await self._get_intelligent_tiers(metadata)
        else:  # BALANCED
            return self._get_balanced_tiers(metadata)

    def _get_performance_optimized_tiers(self, metadata: MemoryMetadata) -> List[MemoryTier]:
        """Get tiers optimized for performance"""
        if metadata.priority in [MemoryPriority.CRITICAL, MemoryPriority.HIGH]:
            return [MemoryTier.L1_CACHE, MemoryTier.L2_SEMANTIC]
        else:
            return [MemoryTier.L1_CACHE, MemoryTier.L3_PERSISTENT]

    def _get_reliability_optimized_tiers(self, metadata: MemoryMetadata) -> List[MemoryTier]:
        """Get tiers optimized for reliability"""
        # Store in multiple tiers for redundancy
        return [MemoryTier.L1_CACHE, MemoryTier.L2_SEMANTIC, MemoryTier.L3_PERSISTENT]

    def _get_cost_optimized_tiers(self, metadata: MemoryMetadata) -> List[MemoryTier]:
        """Get tiers optimized for cost"""
        # Use cheaper storage for most content
        if metadata.priority == MemoryPriority.CRITICAL:
            return [MemoryTier.L1_CACHE, MemoryTier.L3_PERSISTENT]
        else:
            return [MemoryTier.L3_PERSISTENT]

    def _get_balanced_tiers(self, metadata: MemoryMetadata) -> List[MemoryTier]:
        """Get balanced tier allocation"""
        if metadata.priority == MemoryPriority.CRITICAL:
            return [MemoryTier.L1_CACHE, MemoryTier.L2_SEMANTIC, MemoryTier.L3_PERSISTENT]
        elif metadata.priority == MemoryPriority.HIGH:
            return [MemoryTier.L1_CACHE, MemoryTier.L2_SEMANTIC]
        else:
            return [MemoryTier.L1_CACHE, MemoryTier.L3_PERSISTENT]

    async def _get_intelligent_tiers(self, metadata: MemoryMetadata) -> List[MemoryTier]:
        """AI-driven tier selection based on patterns and performance"""

        # Start with balanced approach
        base_tiers = self._get_balanced_tiers(metadata)

        # Adjust based on tier health and performance
        healthy_tiers = []
        for tier in base_tiers:
            health = self.tier_health[tier]
            if health.available and health.quality_score > 0.5:
                healthy_tiers.append(tier)

        # Ensure at least one tier
        if not healthy_tiers:
            healthy_tiers = await self._get_fallback_tiers()

        return healthy_tiers

    def _get_tier_access_order(self, priority: MemoryPriority) -> List[MemoryTier]:
        """Get tier access order based on priority"""
        if priority == MemoryPriority.CRITICAL or priority == MemoryPriority.HIGH:
            return [MemoryTier.L1_CACHE, MemoryTier.L2_SEMANTIC, MemoryTier.L3_PERSISTENT]
        else:
            return [MemoryTier.L1_CACHE, MemoryTier.L3_PERSISTENT, MemoryTier.L2_SEMANTIC]

    async def _determine_search_tiers(self, request: MemorySearchRequest) -> List[MemoryTier]:
        """Determine which tiers to search"""

        search_tiers = []

        # L1 Cache for text-based searches
        search_tiers.append(MemoryTier.L1_CACHE)

        # L2 Semantic for vector searches
        if len(request.query) > 20:  # Longer queries benefit from semantic search
            search_tiers.append(MemoryTier.L2_SEMANTIC)

        # L3 Persistent for comprehensive searches
        search_tiers.append(MemoryTier.L3_PERSISTENT)

        return search_tiers

    async def _filter_healthy_tiers(self, tiers: List[MemoryTier]) -> List[MemoryTier]:
        """Filter tiers to only include healthy ones"""
        healthy_tiers = []

        for tier in tiers:
            health = self.tier_health[tier]
            circuit_breaker = self.circuit_breakers[tier]

            if health.available and circuit_breaker.should_allow_request():
                healthy_tiers.append(tier)

        return healthy_tiers

    async def _get_fallback_tiers(self) -> List[MemoryTier]:
        """Get any available tier as fallback"""
        for tier in [MemoryTier.L1_CACHE, MemoryTier.L2_SEMANTIC, MemoryTier.L3_PERSISTENT]:
            if self.tier_health[tier].available:
                return [tier]

        return []  # No tiers available

    def _apply_routing_rules(
        self, tiers: List[MemoryTier], metadata: MemoryMetadata, operation: str
    ) -> List[MemoryTier]:
        """Apply custom routing rules"""

        for rule in self.custom_rules:
            if not rule.enabled:
                continue

            if self._rule_matches(rule, metadata, operation):
                # Rule matches, use rule's target tiers
                return rule.target_tiers

        # No matching rules, return original tiers
        return tiers

    def _rule_matches(self, rule: RoutingRule, metadata: MemoryMetadata, operation: str) -> bool:
        """Check if routing rule matches current context"""

        conditions = rule.conditions

        # Check operation type
        if "operation" in conditions and conditions["operation"] != operation:
            return False

        # Check context
        if "context" in conditions and conditions["context"] != metadata.context.value:
            return False

        # Check priority
        if "priority" in conditions and conditions["priority"] != metadata.priority.value:
            return False

        # Check domain
        if "domain" in conditions and conditions["domain"] != metadata.domain:
            return False

        # Check tags
        if "tags" in conditions:
            required_tags = set(conditions["tags"])
            if not required_tags.issubset(metadata.tags):
                return False

        return True

    def _apply_load_balancing(self, tiers: List[MemoryTier]) -> List[MemoryTier]:
        """Apply load balancing algorithm"""

        if self.load_balancing_algorithm == LoadBalancingAlgorithm.RESPONSE_TIME_BASED:
            # Sort by response time (ascending)
            return sorted(tiers, key=lambda t: self.tier_health[t].response_time_ms)

        elif self.load_balancing_algorithm == LoadBalancingAlgorithm.CAPACITY_BASED:
            # Sort by capacity usage (ascending)
            return sorted(tiers, key=lambda t: self.tier_health[t].capacity_usage)

        elif self.load_balancing_algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
            # Sort by connection count (ascending)
            return sorted(tiers, key=lambda t: self.tier_health[t].connection_count)

        else:
            # Default: return as-is or round-robin
            return tiers

    async def _store_in_tier(
        self,
        tier: MemoryTier,
        memory_id: str,
        content: str,
        metadata: MemoryMetadata,
        embedding: Optional[List[float]],
    ) -> bool:
        """Store content in specific tier"""
        try:
            entry = MemoryEntry(content=content, metadata=metadata, embedding=embedding)
            location = await self.memory_interface._store_in_tier(tier, entry)
            return location is not None
        except Exception as e:
            logger.error(f"Failed to store in tier {tier.value}: {e}")
            return False

    async def _retrieve_from_tier(self, tier: MemoryTier, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve content from specific tier"""
        try:
            return await self.memory_interface._retrieve_from_tier(tier, memory_id)
        except Exception as e:
            logger.error(f"Failed to retrieve from tier {tier.value}: {e}")
            return None

    async def _search_tier(
        self, tier: MemoryTier, request: MemorySearchRequest
    ) -> List[MemorySearchResult]:
        """Search specific tier"""
        try:
            if tier == MemoryTier.L1_CACHE:
                return await self.memory_interface._search_l1_cache(request)
            elif tier == MemoryTier.L2_SEMANTIC:
                return await self.memory_interface._search_l2_semantic(request)
            elif tier == MemoryTier.L3_PERSISTENT:
                return await self.memory_interface._search_l3_persistent(request)
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to search tier {tier.value}: {e}")
            return []

    def _update_tier_metrics(self, tier: MemoryTier, response_time_ms: float, success: bool):
        """Update tier performance metrics"""

        # Update tier usage count
        tier_name = tier.value
        self.metrics.tier_usage_count[tier_name] = (
            self.metrics.tier_usage_count.get(tier_name, 0) + 1
        )

        # Update tier health metrics
        health = self.tier_health[tier]

        # Update response time (exponential moving average)
        alpha = 0.1
        health.response_time_ms = alpha * response_time_ms + (1 - alpha) * health.response_time_ms

        # Update error rate
        if not success:
            health.error_rate = alpha * 1.0 + (1 - alpha) * health.error_rate
        else:
            health.error_rate = alpha * 0.0 + (1 - alpha) * health.error_rate

        # Update overall metrics
        if self.metrics.total_requests > 0:
            current_avg = self.metrics.average_response_time_ms
            total = self.metrics.total_requests
            self.metrics.average_response_time_ms = (
                current_avg * (total - 1) + response_time_ms
            ) / total

    def _deduplicate_search_results(
        self, results: List[MemorySearchResult]
    ) -> List[MemorySearchResult]:
        """Remove duplicate search results"""
        seen_ids = set()
        unique_results = []

        for result in results:
            if result.memory_id not in seen_ids:
                seen_ids.add(result.memory_id)
                unique_results.append(result)

        return unique_results

    def _rank_search_results(
        self, results: List[MemorySearchResult], request: MemorySearchRequest
    ) -> List[MemorySearchResult]:
        """Rank search results by relevance"""

        def ranking_score(result: MemorySearchResult) -> float:
            score = result.relevance_score

            # Boost results from faster tiers
            if result.source_tier == MemoryTier.L1_CACHE:
                score *= 1.1
            elif result.source_tier == MemoryTier.L2_SEMANTIC:
                score *= 1.05

            # Apply access time penalty for slower results
            if result.access_time_ms > 1000:  # > 1 second
                score *= 0.9

            return score

        return sorted(results, key=ranking_score, reverse=True)

    def _validate_routing_rule(self, rule: RoutingRule) -> bool:
        """Validate routing rule configuration"""

        if not rule.rule_id or not rule.name:
            return False

        if not rule.target_tiers:
            return False

        # Validate target tiers are valid
        for tier in rule.target_tiers:
            if not isinstance(tier, MemoryTier):
                return False

        return True


# Global memory router instance
memory_router = MemoryRouter()
