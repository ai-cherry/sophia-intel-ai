"""
Swarm Performance Optimizer - Circuit Breaker and Performance Monitoring
Provides robust optimization utilities for AI agent swarms with graceful degradation.
"""

import time
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreaker:
    """Circuit breaker pattern implementation for external service calls."""

    failure_threshold: int = 3
    recovery_timeout: float = 30.0
    success_threshold: int = 2

    # Runtime state
    failure_count: int = 0
    last_failure_time: float = 0
    success_count: int = 0
    state: str = "closed"  # closed, open, half_open

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
            else:
                raise CircuitBreakerOpenException(
                    f"Circuit breaker is open. Resets in {self._time_until_reset():.1f}s"
                )

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit."""
        return self._time_since_failure() >= self.recovery_timeout

    def _time_since_failure(self) -> float:
        """Time since last failure."""
        return time.time() - self.last_failure_time if self.last_failure_time else float('inf')

    def _time_until_reset(self) -> float:
        """Time until automatic reset."""
        return max(0, self.recovery_timeout - self._time_since_failure())

    def _on_success(self):
        """Handle successful call."""
        if self.state == "half_open":
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self._reset()
        else:
            # Reset failure count on regular success
            self.failure_count = 0

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            self.success_count = 0
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

    def _reset(self):
        """Reset circuit breaker to closed state."""
        self.state = "closed"
        self.failure_count = 0
        self.success_count = 0
        logger.info("Circuit breaker reset to closed state")


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""


@dataclass
class PatternPerformanceMetrics:
    """Performance tracking for individual patterns."""

    execution_count: int = 0
    total_execution_time: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    memory_usage_mb: float = 0.0
    last_execution_time: float = 0.0

    def record_execution(self, execution_time: float, success: bool, memory_used_mb: float = 0.0):
        """Record a pattern execution."""
        self.execution_count += 1
        self.total_execution_time += execution_time
        self.last_execution_time = execution_time
        self.memory_usage_mb = max(self.memory_usage_mb, memory_used_mb)

        if success:
            self.success_count += 1
        else:
            self.failure_count += 1

    @property
    def avg_execution_time(self) -> float:
        """Average execution time."""
        return self.total_execution_time / max(self.execution_count, 1)

    @property
    def success_rate(self) -> float:
        """Success rate as percentage."""
        return self.success_count / max(self.execution_count, 1)

    @property
    def is_performing_poorly(self) -> bool:
        """Check if pattern is performing poorly."""
        return (
            self.success_rate < 0.8 or
            self.avg_execution_time > 5.0 or
            self.memory_usage_mb > 200
        )


@dataclass
class SwarmBenchmarkData:
    """Benchmarking data for swarm performance."""

    task_complexity_score: float
    pattern_weights: Dict[str, float] = field(default_factory=dict)
    total_execution_time: float = 0.0
    memory_usage_mb: float = 0.0
    quality_score: float = 0.0
    final_result: Optional[Dict] = None


class GracefulDegradationManager:
    """Manages graceful degradation when components fail."""

    def __init__(self):
        self.degraded_components: Dict[str, Dict[str, Any]] = {}
        self.recovery_attempts: Dict[str, int] = {}
        self.max_recovery_attempts = 3

        # Load degradation strategies from config
        self.degradation_strategies = self._load_degradation_strategies()

    def _load_degradation_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Load degradation strategies from configuration."""
        try:
            with open("app/swarms/swarm_optimization_config.json", 'r') as f:
                config = json.load(f)
                return config.get("degradation_strategies", {})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load degradation strategies: {e}")
            return self._get_default_strategies()

    def _get_default_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Default degradation strategies."""
        return {
            "memory_failure": {
                "action": "disable_memory_operations",
                "fallback_mode": "lite",
                "min_agents_fallback": 3,
                "timeout_multiplier": 0.7
            },
            "consensus_failure": {
                "action": "skip_consensus_round",
                "alternative": "simple_judge_decision",
                "quality_impact": -0.1
            },
            "debate_failure": {
                "action": "use_single_round",
                "alternative": "sequential_critique"
            }
        }

    def mark_component_degraded(self, component_name: str, error_message: str = ""):
        """Mark a component as degraded."""
        self.degraded_components[component_name] = {
            "timestamp": time.time(),
            "error_message": error_message,
            "recovery_attempts": self.recovery_attempts.get(component_name, 0)
        }
        logger.warning(f"Component {component_name} marked as degraded: {error_message}")

    def is_component_available(self, component_name: str) -> bool:
        """Check if a component is available."""
        return component_name not in self.degraded_components

    def get_degradation_strategy(self, component_name: str) -> Dict[str, Any]:
        """Get degradation strategy for a component."""
        return self.degradation_strategies.get(component_name, {
            "action": "skip_operation",
            "alternative": None
        })

    def attempt_component_recovery(self, component_name: str) -> bool:
        """Attempt to recover a degraded component."""
        attempts = self.recovery_attempts.get(component_name, 0)
        if attempts >= self.max_recovery_attempts:
            logger.error(f"Max recovery attempts reached for {component_name}")
            return False

        self.recovery_attempts[component_name] = attempts + 1

        # Simple recovery attempt (in practice, would restart/init the component)
        try:
            if component_name in self.degraded_components:
                del self.degraded_components[component_name]
                logger.info(f"Successfully recovered component {component_name}")
                return True
        except Exception as e:
            logger.warning(f"Recovery attempt failed for {component_name}: {e}")

        return False

    def get_system_health_score(self) -> float:
        """Calculate overall system health score."""
        total_components = len(self.degradation_strategies)
        degraded_count = len(self.degraded_components)

        return 1.0 - (degraded_count / max(total_components, 1))


class SwarmOptimizer:
    """Main optimization manager for swarm operations."""

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.performance_metrics: Dict[str, PatternPerformanceMetrics] = {}
        self.degradation_manager = GracefulDegradationManager()
        self.task_complexity_cache: Dict[str, float] = {}

        # Load optimization configuration
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load optimization configuration."""
        try:
            with open("app/swarms/swarm_optimization_config.json", 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load optimization config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Default optimization configuration."""
        return {
            "circuit_breaker_defaults": {
                "failure_threshold": 3,
                "recovery_timeout": 30.0
            },
            "performance_targets": {
                "max_execution_time": 60.0,
                "max_memory_mb": 500
            }
        }

    def get_circuit_breaker(self, component_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for component."""
        if component_name not in self.circuit_breakers:
            cb_config = self.config.get("circuit_breaker_defaults", {})
            self.circuit_breakers[component_name] = CircuitBreaker(**cb_config)

        return self.circuit_breakers[component_name]

    def get_performance_metrics(self, pattern_name: str) -> PatternPerformanceMetrics:
        """Get or create performance metrics for pattern."""
        if pattern_name not in self.performance_metrics:
            self.performance_metrics[pattern_name] = PatternPerformanceMetrics()

        return self.performance_metrics[pattern_name]

    def calculate_task_complexity(self, task: Dict[str, Any]) -> float:
        """Calculate task complexity score (0-1)."""
        # Cache the result
        task_hash = hash(str(task))
        if task_hash in self.task_complexity_cache:
            return self.task_complexity_cache[task_hash]

        task_text = str(task.get("description", "")).lower()

        # Weight different complexity indicators
        complexity_score = 0.3  # Base complexity

        # Keyword analysis
        simple_keywords = ["fix", "update", "change", "modify", "add", "remove"]
        medium_keywords = ["implement", "create", "integrate", "optimize", "improve"]
        complex_keywords = ["architect", "design", "refactor", "scale", "migrate", "enterprise"]

        # Count matches and adjust score
        simple_matches = sum(1 for kw in simple_keywords if kw in task_text)
        medium_matches = sum(1 for kw in medium_keywords if kw in task_text)
        complex_matches = sum(1 for kw in complex_keywords if kw in task_text)

        if simple_matches > 0:
            complexity_score = min(complexity_score, 0.4)
        if medium_matches > 0:
            complexity_score = max(complexity_score, 0.5)
        if complex_matches > 0:
            complexity_score = max(complexity_score, 0.8)

        # Length-based adjustment
        description_length = len(str(task.get("description", "")))
        length_factor = min(description_length / 1000, 1.0)
        complexity_score = (complexity_score + length_factor * 0.3) / 1.3

        # Cache and return
        self.task_complexity_cache[task_hash] = complexity_score
        return complexity_score

    def get_optimal_swarm_config(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get optimal swarm configuration for a task."""
        complexity = self.calculate_task_complexity(task)
        return self._get_config_for_complexity(complexity, task)

    def _get_config_for_complexity(self, complexity: float, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get configuration based on task complexity."""
        modes = self.config.get("optimization_modes", {})

        # Determine urgency
        urgency = task.get("urgency", "normal").lower()

        # Select mode based on complexity and urgency
        if urgency == "critical" or complexity < 0.3:
            return modes.get("lite", {})
        elif complexity > 0.8:
            return modes.get("quality", {})
        else:
            return modes.get("balanced", {})

    async def benchmark_swarm_execution(self, swarm_func, task: Dict[str, Any],
                                       *args, **kwargs) -> SwarmBenchmarkData:
        """Benchmark a swarm execution for performance optimization."""
        start_time = time.time()
        start_memory = 0  # Would get actual memory usage in production

        try:
            # Execute swarm function
            result = await swarm_func(*args, **kwargs)
        except Exception as e:
            result = None
            logger.error(f"Swarm execution benchmarked failed: {e}")

        execution_time = time.time() - start_time
        memory_used = 0  # Would calculate actual memory usage

        # Create benchmark data
        benchmark = SwarmBenchmarkData(
            task_complexity_score=self.calculate_task_complexity(task),
            total_execution_time=execution_time,
            memory_usage_mb=memory_used,
            quality_score=result.get("quality_score", 0.0) if result else 0.0,
            final_result=result
        )

        # Analyze pattern weights (would be more sophisticated in production)
        if result and result.get("patterns_used"):
            total_patterns = len(result["patterns_used"])
            for pattern in result["patterns_used"]:
                benchmark.pattern_weights[pattern] = 1.0 / total_patterns

        logger.info(f"Benchmarked swarm execution: {execution_time:.2f}s, complexity: {benchmark.task_complexity_score:.2f}")
        return benchmark

    def get_optimization_recommendations(self) -> Dict[str, Any]:
        """Generate optimization recommendations based on performance data."""
        recommendations = {
            "pattern_performance": {},
            "system_health": self.degradation_manager.get_system_health_score(),
            "performance_alerts": [],
            "optimization_suggestions": []
        }

        # Analyze pattern performance
        for pattern_name, metrics in self.performance_metrics.items():
            recommendations["pattern_performance"][pattern_name] = {
                "avg_execution_time": metrics.avg_execution_time,
                "success_rate": metrics.success_rate,
                "memory_usage_mb": metrics.memory_usage_mb,
                "executions": metrics.execution_count
            }

            if metrics.is_performing_poorly:
                recommendations["performance_alerts"].append({
                    "pattern": pattern_name,
                    "issue": "Poor performance metrics",
                    "recommendation": "Consider disabling or optimizing"
                })

        # Generate suggestions
        if recommendations["system_health"] < 0.8:
            recommendations["optimization_suggestions"].append({
                "type": "health",
                "suggestion": "Multiple components degraded - consider lite mode"
            })

        if any(metrics.is_performing_poorly for metrics in self.performance_metrics.values()):
            recommendations["optimization_suggestions"].append({
                "type": "patterns",
                "suggestion": "Some patterns performing poorly - use selective pattern enabling"
            })

        return recommendations

    def reset_metrics(self):
        """Reset performance metrics (useful for testing)."""
        self.performance_metrics.clear()
        self.task_complexity_cache.clear()
        logger.info("Performance metrics and caches reset")


@asynccontextmanager
async def performance_monitoring(optimizer: SwarmOptimizer, pattern_name: str):
    """Context manager for performance monitoring."""
    start_time = time.time()
    start_memory = 0  # Would get actual memory usage

    try:
        yield

        # Record successful execution
        execution_time = time.time() - start_time
        memory_used = 0  # Would calculate actual memory usage
        optimizer.get_performance_metrics(pattern_name).record_execution(
            execution_time, True, memory_used
        )

    except Exception:
        # Record failed execution
        execution_time = time.time() - start_time
        optimizer.get_performance_metrics(pattern_name).record_execution(
            execution_time, False, 0
        )
        raise
