"""
Adaptive Parameters Pattern for self-tuning system behavior.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import logging

from .base import SwarmPattern, PatternConfig, PatternResult

logger = logging.getLogger(__name__)


@dataclass
class AdaptiveConfig(PatternConfig):
    """Configuration for adaptive parameters pattern."""
    parameters_to_adapt: List[str] = field(default_factory=lambda: [
        "temperature", "max_iterations", "team_size"
    ])
    adaptation_rate: float = 0.1
    performance_window: int = 10
    optimization_metric: str = "success_rate"


class AdaptiveParametersPattern(SwarmPattern):
    """
    Automatically adjusts system parameters based on performance.
    """
    
    def __init__(self, config: Optional[AdaptiveConfig] = None):
        super().__init__(config or AdaptiveConfig())
        self.current_parameters = {}
        self.performance_buffer = []
        
    async def _setup(self) -> None:
        """Initialize adaptive system."""
        logger.info("Initializing Adaptive Parameters")
        self._initialize_parameters()
        
    async def _teardown(self) -> None:
        """Cleanup adaptive system."""
        pass
        
    async def execute(self, context: Dict[str, Any], agents: List[Any]) -> PatternResult:
        """Execute with adaptive parameters."""
        # Apply current parameters
        adapted_context = self._apply_parameters(context)
        
        # Execute with adapted parameters
        result = await self._execute_with_parameters(adapted_context, agents)
        
        # Measure performance
        performance = self._measure_performance(result)
        self.performance_buffer.append(performance)
        
        # Adapt parameters if enough history
        if len(self.performance_buffer) >= self.config.performance_window:
            self._adapt_parameters()
            
        return PatternResult(
            success=True,
            data=result,
            metrics={
                "current_parameters": self.current_parameters,
                "performance": performance
            },
            pattern_name="adaptive_parameters"
        )
        
    def _initialize_parameters(self) -> None:
        """Initialize default parameters."""
        self.current_parameters = {
            "temperature": 0.7,
            "max_iterations": 5,
            "team_size": 3
        }
        
    def _apply_parameters(self, context: Dict) -> Dict:
        """Apply current parameters to context."""
        adapted = context.copy()
        adapted.update(self.current_parameters)
        return adapted
        
    async def _execute_with_parameters(self, context: Dict, agents: List) -> Dict:
        """Execute with adapted parameters."""
        return {"parameters": self.current_parameters}
        
    def _measure_performance(self, result: Dict) -> float:
        """Measure performance of execution."""
        return 0.75  # Simulated
        
    def _adapt_parameters(self) -> None:
        """Adapt parameters based on performance trends."""
        avg_performance = sum(self.performance_buffer) / len(self.performance_buffer)
        
        # Simple adaptation logic
        if avg_performance < 0.7:
            # Increase exploration
            self.current_parameters["temperature"] = min(
                self.current_parameters["temperature"] + self.config.adaptation_rate,
                1.0
            )
        elif avg_performance > 0.9:
            # Decrease exploration
            self.current_parameters["temperature"] = max(
                self.current_parameters["temperature"] - self.config.adaptation_rate,
                0.1
            )
            
        # Keep only recent history
        self.performance_buffer = self.performance_buffer[-self.config.performance_window:]
