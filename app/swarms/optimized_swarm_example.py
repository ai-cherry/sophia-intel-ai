"""
Optimized Swarm Example - Demonstrates Best Practices for Swarm Implementation
Shows how to implement all the optimization patterns together effectively.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from app.swarms.performance_optimizer import (
    CircuitBreakerOpenException,
    GracefulDegradationManager,
    SwarmOptimizer,
    performance_monitoring,
)

logger = logging.getLogger(__name__)


@dataclass
class OptimizedSwarmConfig:
    """Configuration for optimized swarm."""

    name: str = "optimized_swarm"
    max_agents: int = 5
    timeout_seconds: float = 30.0
    optimization_mode: str = "balanced"
    enabled_patterns: list[str] = field(default_factory=lambda: ["safety", "quality_gates"])
    memory_enabled: bool = True
    circuit_breaker_config: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.optimization_mode not in ["lite", "balanced", "quality"]:
            raise ValueError(f"Invalid optimization mode: {self.optimization_mode}")

        if self.max_agents < 2:
            raise ValueError("Max agents must be at least 2")


class OptimizedSwarm:
    """
    Example of an optimized swarm implementation demonstrating best practices.

    This class shows how to integrate all the optimization patterns:
    - Circuit breaker protection
    - Graceful degradation
    - Performance monitoring
    - Dynamic configuration
    """

    def __init__(self, config: OptimizedSwarmConfig, optimizer: Optional[SwarmOptimizer] = None):
        self.config = config
        self.optimizer = optimizer or SwarmOptimizer()

        # Initialize components
        self.circuit_breaker = self.optimizer.get_circuit_breaker(f"{config.name}_memory")
        self.degradation_manager = GracefulDegradationManager()

        # Agent simulation (in practice these would be real agent objects)
        self.agents = self._initialize_agents()

        # Pattern execution results
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "average_execution_time": 0.0,
            "patterns_used": [],
            "failures": []
        }

        logger.info(f"Optimized swarm {config.name} initialized with mode: {config.optimization_mode}")

    def _initialize_agents(self) -> list[dict[str, Any]]:
        """Initialize agents based on configuration."""
        agents = []

        for i in range(self.config.max_agents):
            agent = {
                "id": f"agent_{i + 1}",
                "role": "worker" if i < self.config.max_agents - 2 else "validator",
                "capabilities": ["code_generation", "analysis"],
                "performance_score": 0.8 + (i * 0.05)  # Decreasing performance for diversity
            }
            agents.append(agent)

        return agents

    async def solve_problem(self, problem: dict[str, Any]) -> dict[str, Any]:
        """
        Solve a problem using the optimized swarm approach.

        Args:
            problem: Problem definition dictionary

        Returns:
            Solution with optimization metadata
        """
        start_time = time.time()

        try:
            # Step 1: Dynamic configuration based on task
            task_config = self.optimizer.get_optimal_swarm_config(problem)
            runtime_config = self._merge_configs(self.config.__dict__, task_config)

            # Step 2: Circuit breaker protection for memory operations
            memory_result = None
            if runtime_config.get("memory_enabled", True):
                try:
                    memory_result = await self.circuit_breaker.call(
                        self._perform_memory_operations,
                        problem
                    )
                except CircuitBreakerOpenException:
                    logger.warning("Memory operations circuit breaker is open - disabling memory")
                    self.degradation_manager.mark_component_degraded(
                        "memory", "Circuit breaker open"
                    )

            # Step 3: Execute patterns with graceful degradation
            pattern_results = {}
            patterns_used = []
            enabled_patterns = runtime_config.get("enabled_patterns", [])

            # Execute patterns with individual timeout and error handling
            if "safety" in enabled_patterns:
                async with performance_monitoring(self.optimizer, "safety"):
                    pattern_results["safety"] = await self._execute_safety_check(problem)
                    patterns_used.append("safety")

            if "quality_gates" in enabled_patterns:
                async with performance_monitoring(self.optimizer, "quality_gates"):
                    pattern_results["quality_gates"] = await self._execute_quality_gates(
                        problem, memory_result
                    )
                    patterns_used.append("quality_gates")

            # Additional patterns with degradation check
            for pattern in ["debate", "consensus", "strategy_archive"]:
                if pattern in enabled_patterns and self.degradation_manager.is_component_available(pattern):
                    try:
                        async with performance_monitoring(self.optimizer, pattern):
                            pattern_results[pattern] = await getattr(
                                self, f"_execute_{pattern.replace('_', '')}",
                                lambda p: self._execute_generic_pattern(p, pattern)
                            )(problem)
                            patterns_used.append(pattern)
                    except Exception as e:
                        logger.warning(f"Pattern {pattern} failed - marking degraded")
                        self.degradation_manager.mark_component_degraded(
                            pattern, str(e)
                        )

            # Step 4: Generate final solution
            solution = await self._generate_solution(problem, pattern_results)

            # Step 5: Post-processing (memory storage with circuit breaker)
            if runtime_config.get("memory_enabled", True):
                try:
                    await self.circuit_breaker.call(
                        self._store_solution,
                        problem, solution
                    )
                except CircuitBreakerOpenException:
                    logger.debug("Skipping solution storage due to circuit breaker")

            execution_time = time.time() - start_time

            # Step 6: Return comprehensive result
            result = {
                "problem": problem,
                "solution": solution,
                "patterns_used": patterns_used,
                "pattern_results": pattern_results,
                "execution_time_sec": execution_time,
                "optimization_mode": runtime_config.get("optimization_mode"),
                "degradation_applied": not all(
                    self.degradation_manager.is_component_available(p) for p in patterns_used
                ),
                "system_health_score": self.degradation_manager.get_system_health_score()
            }

            # Update execution statistics
            self._update_execution_stats(result, True)

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            self._update_execution_stats({
                "problem": problem,
                "execution_time_sec": execution_time,
                "error": str(e)
            }, False)

            logger.error(f"Swarm execution failed: {e}")

            # Return best-effort result even on failure
            return {
                "problem": problem,
                "solution": {"error": f"Execution failed: {str(e)}"},
                "patterns_used": [],
                "execution_time_sec": execution_time,
                "failure": True,
                "error_message": str(e),
                "optimization_mode": self.config.optimization_mode,
                "system_health_score": self.degradation_manager.get_system_health_score()
            }

    async def _perform_memory_operations(self, problem: dict[str, Any]) -> dict[str, Any]:
        """Perform memory-enhanced operations with protection."""
        # Simulate memory search and retrieval
        await asyncio.sleep(0.1)  # Simulate network round-trip

        return {
            "related_problems": ["similar_task_1", "similar_task_2"],
            "historical_solutions": ["solution_a", "solution_b"],
            "learned_patterns": ["pattern_x", "pattern_y"],
            "confidence_score": 0.85
        }

    async def _execute_safety_check(self, problem: dict[str, Any]) -> dict[str, Any]:
        """Execute safety pattern."""
        await asyncio.sleep(0.05)  # Fast safety check

        # Simple keyword-based safety check
        risky_keywords = ["delete", "system", "network", "admin", "root"]
        problem_text = str(problem).lower()

        risk_score = sum(0.2 for kw in risky_keywords if kw in problem_text)
        is_safe = risk_score < 0.5

        return {
            "risk_score": risk_score,
            "is_safe": is_safe,
            "risky_keywords_found": [kw for kw in risky_keywords if kw in problem_text],
            "approval_required": risk_score > 0.7
        }

    async def _execute_quality_gates(self, problem: dict[str, Any],
                                   memory_result: Optional[dict] = None) -> dict[str, Any]:
        """Execute quality gates pattern."""
        await asyncio.sleep(0.3)  # Quality assessment time

        # Simulate quality assessment with memory integration
        base_quality = 0.7
        memory_boost = 0.1 if memory_result and memory_result.get("confidence_score", 0) > 0.8 else 0

        quality_score = base_quality + memory_boost

        return {
            "quality_score": quality_score,
            "memory_boost_applied": memory_boost > 0,
            "assessment_criteria": ["code_quality", "architecture", "testability"],
            "passed": quality_score > 0.6,
            "recommendations": [
                "Add error handling" if quality_score < 0.8 else None,
                "Consider modular design" if "complex" in str(problem).lower() else None
            ]
        }

    async def _execute_debate(self, problem: dict[str, Any]) -> dict[str, Any]:
        """Execute debate pattern."""
        await asyncio.sleep(2.5)  # Debate is time-intensive

        return {
            "debate_rounds": 3,
            "arguments_pro": ["Efficiency argument", "Scalability argument"],
            "arguments_con": ["Maintainability concern", "Complexity concern"],
            "winner": "pro_arguments",
            "confidence_score": 0.8
        }

    async def _execute_consensus(self, problem: dict[str, Any]) -> dict[str, Any]:
        """Execute consensus pattern."""
        await asyncio.sleep(1.8)  # Consensus process time

        return {
            "agent_votes": {"agent_1": "option_a", "agent_2": "option_a"},
            "agreement_threshold": 0.7,
            "consensus_reached": True,
            "final_decision": "option_a",
            "agreement_level": 0.85
        }

    async def _execute_strategy_archive(self, problem: dict[str, Any]) -> dict[str, Any]:
        """Execute strategy archive pattern."""
        await asyncio.sleep(0.4)  # Strategy retrieval time

        return {
            "patterns_found": ["pattern_x", "pattern_y"],
            "best_pattern": "pattern_x",
            "pattern_success_rate": 0.85,
            "applied_pattern": True
        }

    async def _execute_generic_pattern(self, problem: dict[str, Any], pattern_name: str) -> dict[str, Any]:
        """Execute generic pattern implementation."""
        await asyncio.sleep(0.1)  # Generic pattern time

        return {
            "pattern_name": pattern_name,
            "executed": True,
            "result": f"Generic {pattern_name} result"
        }

    async def _generate_solution(self, problem: dict[str, Any], pattern_results: dict[Any, Any]) -> dict[str, Any]:
        """Generate final solution from pattern results."""
        await asyncio.sleep(0.2)  # Solution synthesis time

        # Check safety pattern result
        safety_result = pattern_results.get("safety", {})
        if safety_result and not safety_result.get("is_safe", True):
            return {
                "solution": "Task rejected for safety reasons",
                "safety_blocked": True,
                "risk_score": safety_result.get("risk_score", 0)
            }

        # Quality check
        quality_result = pattern_results.get("quality_gates", {})
        solution_confidence = quality_result.get("quality_score", 0.5)

        return {
            "solution": f"Solution for: {problem.get('description', 'unknown problem')}",
            "confidence_score": solution_confidence,
            "patterns_informed": list(pattern_results.keys()),
            "safety_approved": safety_result.get("is_safe", True),
            "quality_passes": quality_result.get("passed", False)
        }

    async def _store_solution(self, problem: dict[str, Any], solution: dict[str, Any]):
        """Store solution in memory with protection."""
        # Simulate memory storage with appropriate delay
        await asyncio.sleep(0.15)

        # In practice, this would store the solution for future learning
        logger.debug(f"Stored solution for problem: {problem.get('description', '')[:50]}...")

    def _merge_configs(self, base_config: dict[str, Any], task_config: dict[str, Any]) -> dict[str, Any]:
        """Merge base configuration with task-specific configuration."""
        merged = base_config.copy()
        merged.update(task_config)
        return merged

    def _update_execution_stats(self, result: dict[str, Any], success: bool):
        """Update execution statistics."""
        self.execution_stats["total_executions"] += 1

        if success:
            self.execution_stats["successful_executions"] += 1

        execution_time = result.get("execution_time_sec", 0)
        # Update rolling average
        if self.execution_stats["total_executions"] == 1:
            self.execution_stats["average_execution_time"] = execution_time
        else:
            self.execution_stats["average_execution_time"] = (
                (self.execution_stats["average_execution_time"] * (self.execution_stats["total_executions"] - 1)) +
                execution_time
            ) / self.execution_stats["total_executions"]

        if not success:
            self.execution_stats["failures"].append({
                "problem": result["problem"],
                "error": result.get("error", "unknown"),
                "timestamp": time.time()
            })

        patterns_used = result.get("patterns_used", [])
        for pattern in patterns_used:
            if pattern not in self.execution_stats["patterns_used"]:
                self.execution_stats["patterns_used"].append(pattern)

    def get_performance_report(self) -> dict[str, Any]:
        """Generate comprehensive performance report."""
        success_rate = self.execution_stats["successful_executions"] / max(self.execution_stats["total_executions"], 1)

        return {
            "total_executions": self.execution_stats["total_executions"],
            "success_rate": success_rate,
            "average_execution_time": self.execution_stats["average_execution_time"],
            "patterns_most_used": self.execution_stats["patterns_used"],
            "recent_failures": self.execution_stats["failures"][-5:],  # Last 5 failures
            "optimizer_recommendations": self.optimizer.get_optimization_recommendations(),
            "degradation_status": {
                "system_health_score": self.degradation_manager.get_system_health_score(),
                "degraded_components": list(self.degradation_manager.degraded_components.keys())
            }
        }

    def reset_statistics(self):
        """Reset execution statistics for clean benchmarking."""
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "average_execution_time": 0.0,
            "patterns_used": [],
            "failures": []
        }
        self.optimizer.reset_metrics()


# Example usage and benchmarking functions
async def demonstrate_optimized_swarm():
    """Demonstrate the optimized swarm with various task types."""

    # Create optimizer and swarm configuration
    optimizer = SwarmOptimizer()

    # Lite mode configuration
    lite_config = OptimizedSwarmConfig(
        name="lite_swarm",
        max_agents=3,
        timeout_seconds=10.0,
        optimization_mode="lite",
        enabled_patterns=["safety", "quality_gates"]
    )

    # Quality mode configuration
    quality_config = OptimizedSwarmConfig(
        name="quality_swarm",
        max_agents=8,
        timeout_seconds=60.0,
        optimization_mode="quality",
        enabled_patterns=["safety", "quality_gates", "debate", "consensus", "strategy_archive"]
    )

    lite_swarm = OptimizedSwarm(lite_config, optimizer)
    quality_swarm = OptimizedSwarm(quality_config, optimizer)

    # Test tasks
    test_tasks = [
        {"description": "Add error handling to function", "type": "simple", "urgency": "normal"},
        {"description": "Implement user authentication system", "type": "complex", "urgency": "normal"},
        {"description": "DEBUG: Fix critical system crash", "type": "simple", "urgency": "critical"}
    ]

    results = []

    for task in test_tasks:
        logger.info(f"\n{'='*60}")
        logger.info(f"Task: {task['description']}")
        logger.info(f"Complexity: {task.get('complexity', 'unknown')}")
        logger.info(f"Urgency: {task['urgency']}")
        logger.info('='*60)

        # Select swarm based on task characteristics (in practice would be automated)
        swarm = quality_swarm if task.get('type') == 'complex' else lite_swarm

        logger.info(f"Selected Swarm: {swarm.config.name} ({swarm.config.optimization_mode} mode)")

        try:
            # Benchmark the execution
            benchmark = await optimizer.benchmark_swarm_execution(
                swarm.solve_problem, task, task
            )

            result = benchmark.final_result
            results.append(result)

            logger.info("✅ Execution successful")
            logger.info(f"Solution: {result.get('solution', {}).get('solution', 'N/A')[:100]}...")
            logger.info(f"Patterns used: {result.get('patterns_used', [])}")
            logger.info(f"Execution time: {result.get('execution_time_sec', 0):.3f}s")
            logger.info(f"System health: {result.get('system_health_score', 0):.2f}")

        except Exception as e:
            logger.info(f"❌ Execution failed: {e}")

    # Generate final performance report
    logger.info(f"\n{'='*60}")
    logger.info("FINAL PERFORMANCE REPORT")
    logger.info('='*60)

    lite_report = lite_swarm.get_performance_report()
    quality_report = quality_swarm.get_performance_report()

    logger.info("\nLite Swarm Performance:")
    logger.info(f"  Total executions: {lite_report['total_executions']}")
    logger.info(f"  Success rate: {lite_report.get('success_rate', 0):.3f}")
    logger.info(f"  Avg exec time: {lite_report.get('average_execution_time', 0):.2f}s")

    logger.info("\nQuality Swarm Performance:")
    logger.info(f"  Total executions: {quality_report['total_executions']}")
    logger.info(f"  Success rate: {quality_report.get('success_rate', 0):.3f}")
    logger.info(f"  Avg exec time: {quality_report.get('average_execution_time', 0):.2f}s")

    # Optimizer recommendations
    recommendations = optimizer.get_optimization_recommendations()
    logger.info("\nOptimizer Recommendations:")
    logger.info(f"  System health: {recommendations['system_health']:.2f}")
    logger.info(f"  Performance alerts: {len(recommendations['performance_alerts'])}")
    logger.info(f"  Optimization suggestions: {len(recommendations['optimization_suggestions'])}")


async def compare_swarm_modes():
    """Compare different swarm modes on the same task."""
    logger.info(f"\n{'='*80}")
    logger.info("SWARM MODE COMPARISON")
    logger.info('='*80)

    # Complex task for comparison
    complex_task = {
        "description": "Design and implement scalable microservices architecture with advanced features",
        "type": "complex",
        "urgency": "normal"
    }

    optimizer = SwarmOptimizer()
    modes = ["lite", "balanced", "quality"]

    for mode in modes:
        config = OptimizedSwarmConfig(
            name=f"{mode}_comparison",
            max_agents=5 if mode == "balanced" else (3 if mode == "lite" else 8),
            timeout_seconds=10 if mode == "lite" else (30 if mode == "balanced" else 60),
            optimization_mode=mode,
            enabled_patterns=get_patterns_for_mode(mode)
        )

        swarm = OptimizedSwarm(config, optimizer)

        logger.info(f"\n{mode.upper()} MODE:")
        logger.info("-" * 30)

        benchmark = await optimizer.benchmark_swarm_execution(
            swarm.solve_problem, complex_task, complex_task
        )

        if benchmark.final_result:
            result = benchmark.final_result
            logger.info(f"   Execution time: {result.get('execution_time_sec', 0):.2f}s")
            logger.info(f"   Patterns used: {len(result.get('patterns_used', []))}")
            logger.info(f"   System health: {result.get('system_health_score', 0):.3f}")
        else:
            logger.info("   ❌ Failed to execute")


def get_patterns_for_mode(mode: str) -> list[str]:
    """Get appropriate patterns for each mode."""
    if mode == "lite":
        return ["safety", "quality_gates"]
    elif mode == "balanced":
        return ["safety", "quality_gates", "debate", "strategy_archive"]
    else:  # quality
        return ["safety", "quality_gates", "debate", "consensus", "strategy_archive"]


if __name__ == "__main__":
    logger.info("🚀 Optimized Swarm Demonstration")
    logger.info("=" * 60)

    # Run demonstrations
    asyncio.run(demonstrate_optimized_swarm())
    asyncio.run(compare_swarm_modes())

    logger.info(f"\n{'='*60}")
    logger.info("✅ Demonstration complete!")
    logger.info("=" * 60)
