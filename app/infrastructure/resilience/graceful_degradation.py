"""
Graceful Degradation and Fallback Mechanisms
Ensures system continues operating with reduced functionality when components fail
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# ==================== Degradation Levels ====================

class DegradationLevel(Enum):
    """System degradation levels"""
    NORMAL = "normal"           # All features available
    LIMITED = "limited"          # Some features disabled
    ESSENTIAL = "essential"      # Only core features available
    EMERGENCY = "emergency"      # Minimal functionality
    MAINTENANCE = "maintenance"  # System in maintenance mode

class FeatureFlag(Enum):
    """Feature flags for degradation control"""
    SWARM_INTELLIGENCE = "swarm_intelligence"
    MEMORY_INTEGRATION = "memory_integration"
    ADVANCED_ANALYTICS = "advanced_analytics"
    REAL_TIME_STREAMING = "real_time_streaming"
    EXTERNAL_INTEGRATIONS = "external_integrations"
    COLLABORATION_FEATURES = "collaboration_features"
    AI_OPTIMIZATION = "ai_optimization"
    WEBHOOK_NOTIFICATIONS = "webhook_notifications"

# ==================== Graceful Degradation Manager ====================

class GracefulDegradationManager:
    """
    Manages system degradation based on component health
    """

    def __init__(self):
        self.current_level = DegradationLevel.NORMAL
        self.disabled_features: set = set()
        self.component_health: dict[str, float] = {}
        self.degradation_rules = self._initialize_rules()
        self.fallback_strategies = self._initialize_fallbacks()
        self.recovery_attempts: dict[str, int] = {}
        self.last_evaluation = datetime.utcnow()

    def _initialize_rules(self) -> dict[DegradationLevel, dict]:
        """Initialize degradation rules for each level"""
        return {
            DegradationLevel.NORMAL: {
                "min_health_score": 0.8,
                "disabled_features": set(),
                "timeout_multiplier": 1.0,
                "cache_ttl": 300  # 5 minutes
            },
            DegradationLevel.LIMITED: {
                "min_health_score": 0.6,
                "disabled_features": {
                    FeatureFlag.ADVANCED_ANALYTICS,
                    FeatureFlag.COLLABORATION_FEATURES
                },
                "timeout_multiplier": 1.5,
                "cache_ttl": 600  # 10 minutes
            },
            DegradationLevel.ESSENTIAL: {
                "min_health_score": 0.4,
                "disabled_features": {
                    FeatureFlag.SWARM_INTELLIGENCE,
                    FeatureFlag.MEMORY_INTEGRATION,
                    FeatureFlag.ADVANCED_ANALYTICS,
                    FeatureFlag.REAL_TIME_STREAMING,
                    FeatureFlag.COLLABORATION_FEATURES,
                    FeatureFlag.AI_OPTIMIZATION
                },
                "timeout_multiplier": 2.0,
                "cache_ttl": 1800  # 30 minutes
            },
            DegradationLevel.EMERGENCY: {
                "min_health_score": 0.2,
                "disabled_features": {
                    FeatureFlag.SWARM_INTELLIGENCE,
                    FeatureFlag.MEMORY_INTEGRATION,
                    FeatureFlag.ADVANCED_ANALYTICS,
                    FeatureFlag.REAL_TIME_STREAMING,
                    FeatureFlag.EXTERNAL_INTEGRATIONS,
                    FeatureFlag.COLLABORATION_FEATURES,
                    FeatureFlag.AI_OPTIMIZATION,
                    FeatureFlag.WEBHOOK_NOTIFICATIONS
                },
                "timeout_multiplier": 3.0,
                "cache_ttl": 3600  # 1 hour
            },
            DegradationLevel.MAINTENANCE: {
                "min_health_score": 0.0,
                "disabled_features": set(FeatureFlag),  # All features disabled
                "timeout_multiplier": 5.0,
                "cache_ttl": 7200  # 2 hours
            }
        }

    def _initialize_fallbacks(self) -> dict[str, Callable]:
        """Initialize fallback strategies for components"""
        return {
            "orchestra_manager": self._fallback_simple_routing,
            "command_dispatcher": self._fallback_basic_command,
            "memory_system": self._fallback_no_memory,
            "swarm_intelligence": self._fallback_single_agent,
            "external_service": self._fallback_cached_response
        }

    async def evaluate_system_health(
        self,
        component_statuses: dict[str, dict[str, Any]]
    ) -> DegradationLevel:
        """
        Evaluate overall system health and determine degradation level
        """
        # Calculate component health scores
        for component, status in component_statuses.items():
            if status.get("healthy", False):
                error_rate = status.get("error_rate", 0)
                response_time = status.get("avg_response_time", 0)

                # Calculate health score (0-1)
                health_score = 1.0
                health_score -= min(error_rate, 0.5)  # Max 50% penalty for errors
                health_score -= min(response_time / 10, 0.3)  # Max 30% penalty for slow response

                self.component_health[component] = max(0, health_score)
            else:
                self.component_health[component] = 0.0

        # Calculate overall system health
        if self.component_health:
            avg_health = sum(self.component_health.values()) / len(self.component_health)
        else:
            avg_health = 0.0

        # Determine appropriate degradation level
        new_level = DegradationLevel.MAINTENANCE
        for level in [
            DegradationLevel.NORMAL,
            DegradationLevel.LIMITED,
            DegradationLevel.ESSENTIAL,
            DegradationLevel.EMERGENCY
        ]:
            if avg_health >= self.degradation_rules[level]["min_health_score"]:
                new_level = level
                break

        # Update level if changed
        if new_level != self.current_level:
            await self._transition_to_level(new_level)

        self.last_evaluation = datetime.utcnow()
        return self.current_level

    async def _transition_to_level(self, new_level: DegradationLevel):
        """Transition to a new degradation level"""
        old_level = self.current_level
        self.current_level = new_level

        # Update disabled features
        self.disabled_features = self.degradation_rules[new_level]["disabled_features"]

        logger.warning(
            f"System degradation level changed: {old_level.value} -> {new_level.value}"
        )

        # Notify monitoring systems
        await self._notify_level_change(old_level, new_level)

    async def _notify_level_change(
        self,
        old_level: DegradationLevel,
        new_level: DegradationLevel
    ):
        """Notify external systems of degradation level change"""
        # Implementation would send alerts to monitoring systems
        pass

    def is_feature_enabled(self, feature: FeatureFlag) -> bool:
        """Check if a feature is enabled at current degradation level"""
        return feature not in self.disabled_features

    def get_timeout_multiplier(self) -> float:
        """Get timeout multiplier for current degradation level"""
        return self.degradation_rules[self.current_level]["timeout_multiplier"]

    def get_cache_ttl(self) -> int:
        """Get cache TTL for current degradation level"""
        return self.degradation_rules[self.current_level]["cache_ttl"]

    # ==================== Fallback Strategies ====================

    async def _fallback_simple_routing(self, request: dict) -> dict:
        """Fallback to simple routing without Orchestra Manager"""
        return {
            "response": "Processing request with basic routing",
            "fallback": True,
            "mode": "simple"
        }

    async def _fallback_basic_command(self, command: str, context: dict) -> dict:
        """Fallback to basic command processing"""
        return {
            "success": True,
            "response": f"Executed basic command: {command}",
            "fallback": True
        }

    async def _fallback_no_memory(self, query: str) -> list:
        """Fallback when memory system is unavailable"""
        return []  # Return empty memory results

    async def _fallback_single_agent(self, task: dict) -> dict:
        """Fallback to single agent when swarm is unavailable"""
        return {
            "response": "Processed with single agent",
            "agent": "default",
            "fallback": True
        }

    async def _fallback_cached_response(self, service: str, request: dict) -> dict:
        """Return cached response when external service is unavailable"""
        return {
            "response": "Using cached data",
            "cached": True,
            "service": service
        }

    async def execute_with_fallback(
        self,
        component: str,
        primary_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with automatic fallback on failure
        """
        try:
            # Try primary function
            result = await primary_func(*args, **kwargs)

            # Reset recovery attempts on success
            if component in self.recovery_attempts:
                self.recovery_attempts[component] = 0

            return result

        except Exception as e:
            logger.error(f"Primary function failed for {component}: {e}")

            # Track recovery attempts
            self.recovery_attempts[component] = self.recovery_attempts.get(component, 0) + 1

            # Use fallback if available
            if component in self.fallback_strategies:
                logger.info(f"Using fallback strategy for {component}")
                fallback_func = self.fallback_strategies[component]

                try:
                    # Adjust arguments for fallback
                    if component == "orchestra_manager":
                        return await fallback_func(kwargs.get("request", {}))
                    elif component == "command_dispatcher":
                        return await fallback_func(
                            kwargs.get("command", ""),
                            kwargs.get("context", {})
                        )
                    else:
                        return await fallback_func(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed for {component}: {fallback_error}")
                    raise
            else:
                raise

# ==================== Component Fallback Registry ====================

class FallbackRegistry:
    """
    Registry for component-specific fallback handlers
    """

    def __init__(self):
        self.fallbacks: dict[str, list[Callable]] = {}
        self.priorities: dict[str, list[int]] = {}

    def register_fallback(
        self,
        component: str,
        fallback_handler: Callable,
        priority: int = 100
    ):
        """
        Register a fallback handler for a component
        Lower priority values are tried first
        """
        if component not in self.fallbacks:
            self.fallbacks[component] = []
            self.priorities[component] = []

        # Insert in priority order
        insert_index = 0
        for i, p in enumerate(self.priorities[component]):
            if priority < p:
                break
            insert_index = i + 1

        self.fallbacks[component].insert(insert_index, fallback_handler)
        self.priorities[component].insert(insert_index, priority)

    async def execute_with_fallbacks(
        self,
        component: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute component operation with registered fallbacks
        """
        if component not in self.fallbacks:
            raise ValueError(f"No fallbacks registered for component: {component}")

        last_error = None
        for i, fallback in enumerate(self.fallbacks[component]):
            try:
                logger.info(
                    f"Attempting fallback {i+1}/{len(self.fallbacks[component])} "
                    f"for {component}"
                )
                return await fallback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Fallback {i+1} failed for {component}: {e}")
                last_error = e
                continue

        # All fallbacks failed
        raise Exception(
            f"All {len(self.fallbacks[component])} fallbacks failed for {component}. "
            f"Last error: {last_error}"
        )

# ==================== Adaptive Timeout Manager ====================

class AdaptiveTimeoutManager:
    """
    Manages adaptive timeouts based on system performance
    """

    def __init__(self, base_timeout: float = 30.0):
        self.base_timeout = base_timeout
        self.performance_history: dict[str, list[float]] = {}
        self.timeout_adjustments: dict[str, float] = {}
        self.max_history_size = 100

    def record_performance(
        self,
        operation: str,
        execution_time: float,
        success: bool
    ):
        """Record operation performance"""
        if operation not in self.performance_history:
            self.performance_history[operation] = []

        # Weight unsuccessful operations higher
        weighted_time = execution_time * (1.0 if success else 1.5)

        self.performance_history[operation].append(weighted_time)

        # Limit history size
        if len(self.performance_history[operation]) > self.max_history_size:
            self.performance_history[operation].pop(0)

        # Update timeout adjustment
        self._update_timeout_adjustment(operation)

    def _update_timeout_adjustment(self, operation: str):
        """Update timeout adjustment based on performance history"""
        if operation not in self.performance_history:
            return

        history = self.performance_history[operation]
        if len(history) < 10:  # Need minimum samples
            return

        # Calculate P95 execution time
        sorted_times = sorted(history)
        p95_index = int(len(sorted_times) * 0.95)
        p95_time = sorted_times[p95_index]

        # Set timeout to P95 + 20% buffer
        self.timeout_adjustments[operation] = p95_time * 1.2

    def get_timeout(
        self,
        operation: str,
        degradation_multiplier: float = 1.0
    ) -> float:
        """Get adaptive timeout for operation"""
        if operation in self.timeout_adjustments:
            timeout = self.timeout_adjustments[operation]
        else:
            timeout = self.base_timeout

        # Apply degradation multiplier
        return timeout * degradation_multiplier

# ==================== Smart Retry Strategy ====================

class SmartRetryStrategy:
    """
    Intelligent retry strategy with exponential backoff and jitter
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with smart retry logic
        """
        import random

        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                if attempt < self.max_retries - 1:
                    # Calculate delay with exponential backoff
                    delay = min(
                        self.base_delay * (self.exponential_base ** attempt),
                        self.max_delay
                    )

                    # Add jitter to avoid thundering herd
                    jitter = random.uniform(0, delay * 0.1)
                    total_delay = delay + jitter

                    logger.info(
                        f"Retry {attempt + 1}/{self.max_retries} after {total_delay:.2f}s"
                    )

                    await asyncio.sleep(total_delay)

        # All retries exhausted
        raise last_exception

# ==================== Export Components ====================

__all__ = [
    "DegradationLevel",
    "FeatureFlag",
    "GracefulDegradationManager",
    "FallbackRegistry",
    "AdaptiveTimeoutManager",
    "SmartRetryStrategy"
]
