"""
Integration Adapter for Experimental Evolution Engine - ADR-002
Provides safe integration between existing swarm orchestrators and experimental evolution.

⚠️ EXPERIMENTAL INTEGRATION ⚠️

This adapter allows existing swarm orchestrators to optionally use experimental
evolution features while maintaining backward compatibility and safety.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.swarms.memory_integration import SwarmMemoryClient, SwarmMemoryEventType

from .experimental_evolution_engine import (
    ExperimentalEvolutionEngine,
    ExperimentalMode,
    SwarmChromosome,
    create_experimental_evolution_engine,
)

logger = logging.getLogger(__name__)


@dataclass
class SwarmEvolutionConfig:
    """Configuration for swarm evolution integration."""

    # Evolution settings
    enable_evolution: bool = False
    experimental_mode: ExperimentalMode = ExperimentalMode.DISABLED
    acknowledge_experimental: bool = False
    dry_run_mode: bool = True

    # Integration settings
    evolution_frequency: int = 10  # Evolve every N executions
    min_executions_before_evolution: int = 5
    performance_tracking_window: int = 20

    # Safety settings
    enable_automatic_rollback: bool = True
    max_performance_degradation: float = 0.1
    safety_monitoring_enabled: bool = True


class ExperimentalSwarmEvolutionAdapter:
    """
    Adapter to integrate experimental evolution with existing swarm orchestrators.

    This adapter provides a safe way to add experimental evolution capabilities
    to existing swarm systems without breaking existing functionality.

    Features:
    - Optional evolution (disabled by default)
    - Performance monitoring and safety controls
    - Automatic rollback on degradation
    - Memory integration for historical learning
    - Backward compatibility with existing swarms
    """

    def __init__(
        self,
        swarm_type: str,
        config: Optional[SwarmEvolutionConfig] = None,
        memory_client: Optional[SwarmMemoryClient] = None,
    ):
        """
        Initialize evolution adapter for a swarm type.

        Args:
            swarm_type: Type of swarm (coding_team, coding_swarm, etc.)
            config: Evolution configuration
            memory_client: Optional memory client
        """
        self.swarm_type = swarm_type
        self.config = config or SwarmEvolutionConfig()
        self.memory_client = memory_client

        # Evolution engine (created lazily if needed)
        self.evolution_engine: Optional[ExperimentalEvolutionEngine] = None
        self.evolution_initialized = False

        # Performance tracking
        self.execution_count = 0
        self.performance_history: list[dict[str, Any]] = []
        self.last_evolution_execution = 0

        # Current best configuration
        self.current_best_chromosome: Optional[SwarmChromosome] = None
        self.baseline_performance: Optional[float] = None

        # Safety monitoring
        self.safety_violations: list[dict[str, Any]] = []
        self.evolution_active = False

        logger.info(f"🧪 Experimental evolution adapter initialized for {swarm_type}")
        if not self.config.enable_evolution:
            logger.info("Evolution is DISABLED - swarm will use standard configuration")
        elif not self.config.acknowledge_experimental:
            logger.warning("⚠️ Experimental evolution not acknowledged - will remain disabled")

    async def initialize_evolution(self, base_swarm_config: dict[str, Any]) -> bool:
        """
        Initialize experimental evolution engine if configured.

        Args:
            base_swarm_config: Base configuration for the swarm

        Returns:
            True if evolution was initialized, False otherwise
        """
        if not self._should_initialize_evolution():
            return False

        try:
            # Create evolution engine
            self.evolution_engine = create_experimental_evolution_engine(
                mode=self.config.experimental_mode,
                enable_experimental=self.config.enable_evolution,
                acknowledge_experimental=self.config.acknowledge_experimental,
                memory_client=self.memory_client,
                dry_run_mode=self.config.dry_run_mode,
                enable_rollback=self.config.enable_automatic_rollback,
            )

            # Create base chromosome from swarm config
            base_chromosome = self._create_base_chromosome(base_swarm_config)

            # Initialize population
            success = await self.evolution_engine.initialize_experimental_population(
                swarm_type=self.swarm_type, base_chromosome=base_chromosome, population_size=5
            )

            if success:
                self.evolution_initialized = True
                self.evolution_active = True
                self.current_best_chromosome = base_chromosome

                logger.info(f"🧪 Experimental evolution initialized for {self.swarm_type}")

                # Log initialization in memory
                if self.memory_client:
                    await self.memory_client.log_swarm_event(
                        SwarmMemoryEventType.EVOLUTION_EVENT,
                        {
                            "event_type": "adapter_evolution_initialized",
                            "swarm_type": self.swarm_type,
                            "experimental_mode": self.config.experimental_mode.value,
                            "dry_run_mode": self.config.dry_run_mode,
                        },
                    )

                return True
            else:
                logger.error(f"Failed to initialize experimental evolution for {self.swarm_type}")
                return False

        except Exception as e:
            logger.error(f"Error initializing experimental evolution for {self.swarm_type}: {e}")
            return False

    def _should_initialize_evolution(self) -> bool:
        """Check if evolution should be initialized."""
        if not self.config.enable_evolution:
            return False
        if not self.config.acknowledge_experimental:
            return False
        return not self.evolution_initialized

    def _create_base_chromosome(self, swarm_config: dict[str, Any]) -> SwarmChromosome:
        """Create base chromosome from swarm configuration."""
        # Extract agent configuration
        agents = swarm_config.get("agents", ["agent_1", "agent_2", "agent_3"])

        # Create agent parameters with defaults
        agent_parameters = {}
        for agent in agents:
            agent_parameters[agent] = {
                "creativity": 0.7,
                "focus": 0.8,
                "collaboration": 0.6,
                "risk_tolerance": 0.3,
                "learning_rate": 0.5,
            }

        # Create chromosome
        chromosome = SwarmChromosome(
            chromosome_id=f"{self.swarm_type}_base_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            swarm_type=self.swarm_type,
            generation=1,
            agent_roles=agents,
            agent_parameters=agent_parameters,
            coordination_style=swarm_config.get("coordination_style", "peer_to_peer"),
            communication_pattern=swarm_config.get("communication_pattern", "adaptive"),
            consensus_mechanism=swarm_config.get("consensus_mechanism", "majority"),
            quality_threshold=swarm_config.get("quality_threshold", 0.8),
            speed_preference=swarm_config.get("speed_preference", 0.5),
            risk_tolerance=swarm_config.get("risk_tolerance", 0.3),
            learning_rate=swarm_config.get("learning_rate", 0.5),
            memory_utilization=swarm_config.get("memory_utilization", 0.7),
            pattern_recognition_sensitivity=swarm_config.get(
                "pattern_recognition_sensitivity", 0.6
            ),
        )

        return chromosome

    async def record_execution_performance(self, execution_result: dict[str, Any]) -> None:
        """
        Record performance of a swarm execution.

        Args:
            execution_result: Results from swarm execution including metrics
        """
        self.execution_count += 1

        # Extract performance metrics
        performance_data = {
            "execution_id": execution_result.get("execution_id", f"exec_{self.execution_count}"),
            "timestamp": datetime.now().isoformat(),
            "quality_score": execution_result.get("quality_score", 0.5),
            "speed_score": execution_result.get("speed_score", 0.5),
            "efficiency_score": execution_result.get("efficiency_score", 0.5),
            "reliability_score": execution_result.get("reliability_score", 0.5),
            "success": execution_result.get("success", False),
            "execution_time": execution_result.get("execution_time", 0),
            "error_count": len(execution_result.get("errors", [])),
            "agent_performance": execution_result.get("agent_performance", {}),
        }

        # Add to history
        self.performance_history.append(performance_data)

        # Keep only recent history
        max_history = self.config.performance_tracking_window * 2
        if len(self.performance_history) > max_history:
            self.performance_history = self.performance_history[-max_history:]

        # Update baseline if this is early execution
        if self.baseline_performance is None and len(self.performance_history) >= 3:
            recent_scores = [p["quality_score"] for p in self.performance_history[-3:]]
            self.baseline_performance = sum(recent_scores) / len(recent_scores)

        # Check if evolution should be triggered
        await self._check_evolution_trigger()

    async def _check_evolution_trigger(self) -> None:
        """Check if evolution should be triggered."""
        if not self.evolution_active or not self.evolution_engine:
            return

        # Check minimum executions
        if self.execution_count < self.config.min_executions_before_evolution:
            return

        # Check evolution frequency
        executions_since_evolution = self.execution_count - self.last_evolution_execution
        if executions_since_evolution < self.config.evolution_frequency:
            return

        # Check if we have enough performance data
        if len(self.performance_history) < self.config.performance_tracking_window:
            return

        logger.info(
            f"🧪 Triggering experimental evolution for {self.swarm_type} after {executions_since_evolution} executions"
        )
        await self._perform_evolution()

    async def _perform_evolution(self) -> None:
        """Perform experimental evolution."""
        if not self.evolution_engine:
            return

        try:
            # Get recent performance data
            recent_performance = self.performance_history[
                -self.config.performance_tracking_window :
            ]
            avg_performance = {
                "quality_score": sum(p["quality_score"] for p in recent_performance)
                / len(recent_performance),
                "speed_score": sum(p["speed_score"] for p in recent_performance)
                / len(recent_performance),
                "efficiency_score": sum(p["efficiency_score"] for p in recent_performance)
                / len(recent_performance),
                "reliability_score": sum(p["reliability_score"] for p in recent_performance)
                / len(recent_performance),
            }

            # Perform evolution
            best_chromosome = await self.evolution_engine.experimental_evolve_population(
                swarm_type=self.swarm_type, performance_data=avg_performance
            )

            if best_chromosome:
                # Check if evolution improved performance
                if await self._validate_evolution_improvement(best_chromosome, avg_performance):
                    self.current_best_chromosome = best_chromosome
                    self.last_evolution_execution = self.execution_count

                    logger.info(
                        f"🧪 Evolution successful for {self.swarm_type} - fitness: {best_chromosome.fitness_score:.3f}"
                    )

                    # Store evolution result in memory
                    if self.memory_client:
                        await self.memory_client.log_swarm_event(
                            SwarmMemoryEventType.EVOLUTION_EVENT,
                            {
                                "event_type": "adapter_evolution_completed",
                                "swarm_type": self.swarm_type,
                                "fitness_score": best_chromosome.fitness_score,
                                "generation": best_chromosome.generation,
                                "improvement_validated": True,
                            },
                        )
                else:
                    logger.warning(
                        f"🧪 Evolution did not improve performance for {self.swarm_type}"
                    )
            else:
                logger.warning(f"🧪 Evolution failed for {self.swarm_type}")

        except Exception as e:
            logger.error(f"🧪 Error during evolution for {self.swarm_type}: {e}")
            self.safety_violations.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "type": "evolution_error",
                    "error": str(e),
                    "swarm_type": self.swarm_type,
                }
            )

    async def _validate_evolution_improvement(
        self, chromosome: SwarmChromosome, recent_performance: dict[str, float]
    ) -> bool:
        """Validate that evolution improved performance."""
        if not self.config.safety_monitoring_enabled:
            return True  # Skip validation if disabled

        # Compare with baseline
        if self.baseline_performance is None:
            return True  # No baseline to compare

        current_avg_quality = recent_performance["quality_score"]
        improvement = chromosome.fitness_score - current_avg_quality

        # Check for degradation
        degradation_threshold = self.config.max_performance_degradation
        if improvement < -degradation_threshold:
            logger.warning(
                f"🧪 Evolution degraded performance for {self.swarm_type}: {improvement:.3f}"
            )

            if self.config.enable_automatic_rollback:
                await self._trigger_rollback("performance_degradation")

            return False

        return True

    async def _trigger_rollback(self, reason: str) -> None:
        """Trigger rollback to previous configuration."""
        logger.warning(f"🧪 Triggering evolution rollback for {self.swarm_type}: {reason}")

        self.safety_violations.append(
            {
                "timestamp": datetime.now().isoformat(),
                "type": "evolution_rollback",
                "reason": reason,
                "swarm_type": self.swarm_type,
            }
        )

        # Store rollback event in memory
        if self.memory_client:
            await self.memory_client.log_swarm_event(
                SwarmMemoryEventType.EVOLUTION_EVENT,
                {
                    "event_type": "adapter_evolution_rollback",
                    "swarm_type": self.swarm_type,
                    "reason": reason,
                    "safety_intervention": True,
                },
            )

    def get_current_swarm_config(self) -> dict[str, Any]:
        """
        Get current swarm configuration (evolved or base).

        Returns:
            Current swarm configuration dictionary
        """
        if not self.current_best_chromosome:
            # Return default configuration
            return {
                "agents": ["agent_1", "agent_2", "agent_3"],
                "coordination_style": "peer_to_peer",
                "communication_pattern": "adaptive",
                "consensus_mechanism": "majority",
                "quality_threshold": 0.8,
                "evolution_enabled": False,
            }

        # Return configuration from best chromosome
        chromosome = self.current_best_chromosome
        return {
            "agents": chromosome.agent_roles,
            "agent_parameters": chromosome.agent_parameters,
            "coordination_style": chromosome.coordination_style,
            "communication_pattern": chromosome.communication_pattern,
            "consensus_mechanism": chromosome.consensus_mechanism,
            "quality_threshold": chromosome.quality_threshold,
            "speed_preference": chromosome.speed_preference,
            "risk_tolerance": chromosome.risk_tolerance,
            "learning_rate": chromosome.learning_rate,
            "memory_utilization": chromosome.memory_utilization,
            "pattern_recognition_sensitivity": chromosome.pattern_recognition_sensitivity,
            "evolution_enabled": True,
            "chromosome_id": chromosome.chromosome_id,
            "generation": chromosome.generation,
            "fitness_score": chromosome.fitness_score,
            "experimental_variant": chromosome.experimental_variant,
        }

    def get_evolution_status(self) -> dict[str, Any]:
        """Get current evolution status and metrics."""
        status = {
            "swarm_type": self.swarm_type,
            "evolution_enabled": self.config.enable_evolution,
            "evolution_initialized": self.evolution_initialized,
            "evolution_active": self.evolution_active,
            "experimental_mode": self.config.experimental_mode.value,
            "execution_count": self.execution_count,
            "last_evolution": self.last_evolution_execution,
            "executions_since_evolution": self.execution_count - self.last_evolution_execution,
            "performance_history_length": len(self.performance_history),
            "baseline_performance": self.baseline_performance,
            "safety_violations": len(self.safety_violations),
            "dry_run_mode": self.config.dry_run_mode,
        }

        if self.current_best_chromosome:
            status.update(
                {
                    "current_chromosome": {
                        "chromosome_id": self.current_best_chromosome.chromosome_id,
                        "generation": self.current_best_chromosome.generation,
                        "fitness_score": self.current_best_chromosome.fitness_score,
                        "experimental_variant": self.current_best_chromosome.experimental_variant,
                    }
                }
            )

        if self.evolution_engine:
            engine_status = self.evolution_engine.get_experimental_status(self.swarm_type)
            status["engine_status"] = engine_status

        return status

    def get_performance_summary(self) -> dict[str, Any]:
        """Get performance summary and trends."""
        if not self.performance_history:
            return {"status": "no_data"}

        recent = (
            self.performance_history[-self.config.performance_tracking_window :]
            if len(self.performance_history) >= self.config.performance_tracking_window
            else self.performance_history
        )

        avg_metrics = {
            "quality_score": sum(p["quality_score"] for p in recent) / len(recent),
            "speed_score": sum(p["speed_score"] for p in recent) / len(recent),
            "efficiency_score": sum(p["efficiency_score"] for p in recent) / len(recent),
            "reliability_score": sum(p["reliability_score"] for p in recent) / len(recent),
            "success_rate": sum(1 for p in recent if p["success"]) / len(recent),
        }

        # Calculate trends
        if len(self.performance_history) >= 10:
            first_half = self.performance_history[: len(self.performance_history) // 2]
            second_half = self.performance_history[len(self.performance_history) // 2 :]

            first_avg = sum(p["quality_score"] for p in first_half) / len(first_half)
            second_avg = sum(p["quality_score"] for p in second_half) / len(second_half)
            trend = second_avg - first_avg
        else:
            trend = 0.0

        return {
            "total_executions": len(self.performance_history),
            "recent_window_size": len(recent),
            "average_metrics": avg_metrics,
            "performance_trend": trend,
            "baseline_performance": self.baseline_performance,
            "improvement_from_baseline": avg_metrics["quality_score"]
            - (self.baseline_performance or avg_metrics["quality_score"]),
        }

    async def shutdown(self):
        """Gracefully shutdown the evolution adapter."""
        logger.info(f"🧪 Shutting down experimental evolution adapter for {self.swarm_type}")

        if self.evolution_engine:
            await self.evolution_engine.experimental_shutdown()

        # Final status log
        if self.memory_client:
            try:
                final_status = self.get_evolution_status()
                await self.memory_client.log_swarm_event(
                    SwarmMemoryEventType.EVOLUTION_EVENT,
                    {
                        "event_type": "adapter_shutdown",
                        "swarm_type": self.swarm_type,
                        "final_status": final_status,
                        "total_executions": self.execution_count,
                        "safety_violations": len(self.safety_violations),
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to log final status: {e}")

        logger.info(f"🧪 Evolution adapter shutdown complete for {self.swarm_type}")


def create_evolution_adapter(
    swarm_type: str,
    enable_evolution: bool = False,
    experimental_mode: ExperimentalMode = ExperimentalMode.DISABLED,
    acknowledge_experimental: bool = False,
    memory_client: Optional[SwarmMemoryClient] = None,
    **kwargs,
) -> ExperimentalSwarmEvolutionAdapter:
    """
    Factory function to create an experimental swarm evolution adapter.

    Args:
        swarm_type: Type of swarm
        enable_evolution: Whether to enable experimental evolution
        experimental_mode: Experimental mode to use
        acknowledge_experimental: Must be True to enable experimental features
        memory_client: Optional memory client
        **kwargs: Additional configuration options

    Returns:
        ExperimentalSwarmEvolutionAdapter instance
    """
    config = SwarmEvolutionConfig(
        enable_evolution=enable_evolution,
        experimental_mode=experimental_mode,
        acknowledge_experimental=acknowledge_experimental,
        **kwargs,
    )

    adapter = ExperimentalSwarmEvolutionAdapter(
        swarm_type=swarm_type, config=config, memory_client=memory_client
    )

    if enable_evolution and acknowledge_experimental:
        logger.warning(
            f"🧪 EXPERIMENTAL EVOLUTION ADAPTER CREATED for {swarm_type}\n"
            f"⚠️  Mode: {experimental_mode.value}\n"
            "⚠️  This is experimental - monitor performance closely!\n"
            "⚠️  Automatic rollback is enabled for safety."
        )

    return adapter
