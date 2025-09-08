"""
Mode Normalization and Configuration Management
Ensures consistent optimization modes across all swarm implementations
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class UnifiedMode(Enum):
    """Unified optimization modes used across all swarms"""

    LITE = "lite"  # Fast execution, minimal processing
    BALANCED = "balanced"  # Default balanced approach
    QUALITY = "quality"  # High quality, thorough processing


@dataclass
class ModeConfig:
    """Configuration for a specific mode"""

    name: str
    timeout: int  # seconds
    max_agents: int
    max_rounds: int
    enabled_patterns: list
    use_memory: bool
    use_critic: bool
    use_judge: bool
    use_consensus: bool
    circuit_breaker_threshold: float


class ModeNormalizer:
    """
    Normalizes and manages optimization modes across different swarm implementations
    """

    # Mode aliases mapping to unified modes
    MODE_ALIASES = {
        # Lite/Fast modes
        "fast": UnifiedMode.LITE,
        "speed": UnifiedMode.LITE,
        "lite": UnifiedMode.LITE,
        "quick": UnifiedMode.LITE,
        "minimal": UnifiedMode.LITE,
        # Balanced/Normal modes
        "balanced": UnifiedMode.BALANCED,
        "normal": UnifiedMode.BALANCED,
        "standard": UnifiedMode.BALANCED,
        "default": UnifiedMode.BALANCED,
        # Quality/Thorough modes
        "quality": UnifiedMode.QUALITY,
        "thorough": UnifiedMode.QUALITY,
        "comprehensive": UnifiedMode.QUALITY,
        "full": UnifiedMode.QUALITY,
        "complete": UnifiedMode.QUALITY,
    }

    # Default configurations for each mode
    DEFAULT_CONFIGS = {
        UnifiedMode.LITE: ModeConfig(
            name="lite",
            timeout=30,
            max_agents=2,
            max_rounds=1,
            enabled_patterns=["safety_boundaries"],
            use_memory=False,
            use_critic=False,
            use_judge=False,
            use_consensus=False,
            circuit_breaker_threshold=0.5,
        ),
        UnifiedMode.BALANCED: ModeConfig(
            name="balanced",
            timeout=120,
            max_agents=5,
            max_rounds=3,
            enabled_patterns=[
                "safety_boundaries",
                "dynamic_role_assignment",
                "quality_gates",
            ],
            use_memory=True,
            use_critic=True,
            use_judge=False,
            use_consensus=False,
            circuit_breaker_threshold=0.7,
        ),
        UnifiedMode.QUALITY: ModeConfig(
            name="quality",
            timeout=300,
            max_agents=10,
            max_rounds=5,
            enabled_patterns=[
                "safety_boundaries",
                "dynamic_role_assignment",
                "adversarial_debate",
                "quality_gates",
                "consensus_mechanisms",
                "strategy_archive",
                "adaptive_parameters",
                "knowledge_transfer",
            ],
            use_memory=True,
            use_critic=True,
            use_judge=True,
            use_consensus=True,
            circuit_breaker_threshold=0.9,
        ),
    }

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "app/swarms/swarm_optimization_config.json"
        self.custom_configs = self._load_custom_configs()

    def _load_custom_configs(self) -> dict[UnifiedMode, ModeConfig]:
        """Load custom configurations from file"""
        try:
            with open(self.config_path) as f:
                data = json.load(f)

            custom = {}
            for mode_name, config in data.get("optimization_modes", {}).items():
                unified_mode = self.normalize_mode(mode_name)
                custom[unified_mode] = ModeConfig(
                    name=mode_name,
                    timeout=config.get(
                        "timeout", self.DEFAULT_CONFIGS[unified_mode].timeout
                    ),
                    max_agents=config.get(
                        "max_agents", self.DEFAULT_CONFIGS[unified_mode].max_agents
                    ),
                    max_rounds=config.get(
                        "max_rounds", self.DEFAULT_CONFIGS[unified_mode].max_rounds
                    ),
                    enabled_patterns=config.get(
                        "enabled_patterns",
                        self.DEFAULT_CONFIGS[unified_mode].enabled_patterns,
                    ),
                    use_memory=config.get(
                        "use_memory", self.DEFAULT_CONFIGS[unified_mode].use_memory
                    ),
                    use_critic=config.get(
                        "use_critic", self.DEFAULT_CONFIGS[unified_mode].use_critic
                    ),
                    use_judge=config.get(
                        "use_judge", self.DEFAULT_CONFIGS[unified_mode].use_judge
                    ),
                    use_consensus=config.get(
                        "use_consensus",
                        self.DEFAULT_CONFIGS[unified_mode].use_consensus,
                    ),
                    circuit_breaker_threshold=config.get(
                        "circuit_breaker_threshold",
                        self.DEFAULT_CONFIGS[unified_mode].circuit_breaker_threshold,
                    ),
                )

            logger.info(f"Loaded custom configs for modes: {list(custom.keys())}")
            return custom

        except Exception as e:
            logger.warning(f"Failed to load custom configs: {e}, using defaults")
            return {}

    def normalize_mode(self, mode: str) -> UnifiedMode:
        """
        Normalize any mode string to a UnifiedMode enum

        Args:
            mode: Mode string (can be fast, speed, lite, balanced, quality, etc.)

        Returns:
            UnifiedMode enum value
        """
        if isinstance(mode, UnifiedMode):
            return mode

        mode_lower = mode.lower().strip()
        return self.MODE_ALIASES.get(mode_lower, UnifiedMode.BALANCED)

    def get_config(self, mode: Any) -> ModeConfig:
        """
        Get configuration for a mode

        Args:
            mode: Mode (string or UnifiedMode enum)

        Returns:
            ModeConfig for the specified mode
        """
        unified_mode = self.normalize_mode(str(mode))

        # Check custom configs first
        if unified_mode in self.custom_configs:
            return self.custom_configs[unified_mode]

        # Fall back to defaults
        return self.DEFAULT_CONFIGS[unified_mode]

    def adapt_for_swarm(self, mode: Any, swarm_type: str) -> dict[str, Any]:
        """
        Adapt mode configuration for specific swarm implementation

        Args:
            mode: Mode to adapt
            swarm_type: Type of swarm (coding, improved, simple)

        Returns:
            Dictionary of configuration parameters for the swarm
        """
        config = self.get_config(mode)

        if swarm_type == "coding":
            # Adapt for CodingSwarmOrchestrator
            return {
                "optimization": config.name,  # Will match "lite" for fast mode
                "timeout": config.timeout,
                "max_rounds": config.max_rounds,
                "use_critic": config.use_critic,
                "use_judge": config.use_judge,
                "use_memory": config.use_memory,
            }

        elif swarm_type == "improved":
            # Adapt for ImprovedAgentSwarm
            return {
                "optimization_mode": config.name,
                "enabled_patterns": config.enabled_patterns,
                "max_agents": config.max_agents,
                "timeout": config.timeout,
                "use_consensus": config.use_consensus,
            }

        elif swarm_type == "simple":
            # Adapt for SimpleAgentOrchestrator
            return {
                "mode": config.name,
                "timeout": config.timeout,
                "max_agents": config.max_agents,
            }

        else:
            # Generic configuration
            return {
                "mode": config.name,
                "timeout": config.timeout,
                "max_agents": config.max_agents,
                "max_rounds": config.max_rounds,
                "patterns": config.enabled_patterns,
            }

    def should_use_fast_path(self, mode: Any) -> bool:
        """
        Determine if fast path should be used for given mode

        Args:
            mode: Mode to check

        Returns:
            True if fast path should be used
        """
        unified_mode = self.normalize_mode(str(mode))
        return unified_mode == UnifiedMode.LITE

    def get_circuit_breaker_config(self, mode: Any) -> dict[str, Any]:
        """
        Get circuit breaker configuration for mode

        Args:
            mode: Mode to get config for

        Returns:
            Circuit breaker configuration
        """
        config = self.get_config(mode)

        return {
            "failure_threshold": int(5 * (1 - config.circuit_breaker_threshold)),
            "recovery_timeout": config.timeout // 2,
            "expected_exception": Exception,
            "name": f"cb_{config.name}",
        }

    def get_degradation_strategy(self, current_mode: Any) -> UnifiedMode:
        """
        Get degradation strategy - what mode to fall back to

        Args:
            current_mode: Current mode

        Returns:
            Mode to degrade to
        """
        unified_mode = self.normalize_mode(str(current_mode))

        if unified_mode == UnifiedMode.QUALITY:
            return UnifiedMode.BALANCED
        elif unified_mode == UnifiedMode.BALANCED:
            return UnifiedMode.LITE
        else:
            return UnifiedMode.LITE  # Already at lowest

    def calculate_mode_cost(self, mode: Any) -> float:
        """
        Calculate relative cost of a mode (0.0 to 1.0)

        Args:
            mode: Mode to calculate cost for

        Returns:
            Relative cost (0.0 = cheapest, 1.0 = most expensive)
        """
        config = self.get_config(mode)

        # Calculate based on timeout, agents, rounds, and patterns
        timeout_cost = config.timeout / 300  # Normalized to max timeout
        agent_cost = config.max_agents / 10  # Normalized to max agents
        round_cost = config.max_rounds / 5  # Normalized to max rounds
        pattern_cost = len(config.enabled_patterns) / 8  # Normalized to max patterns

        # Weighted average
        return (
            timeout_cost * 0.3
            + agent_cost * 0.3
            + round_cost * 0.2
            + pattern_cost * 0.2
        )

    def select_mode_for_task(
        self,
        task_complexity: float,
        urgency: str = "normal",
        resource_availability: float = 1.0,
    ) -> UnifiedMode:
        """
        Select optimal mode based on task characteristics

        Args:
            task_complexity: Complexity score (0.0 to 1.0)
            urgency: Urgency level (low, normal, high, critical)
            resource_availability: Available resources (0.0 to 1.0)

        Returns:
            Recommended UnifiedMode
        """
        # Map urgency to urgency score
        urgency_scores = {"low": 0.0, "normal": 0.5, "high": 0.75, "critical": 1.0}
        urgency_score = urgency_scores.get(urgency, 0.5)

        # Calculate mode score
        # High complexity + low urgency + high resources = Quality
        # Low complexity + high urgency + low resources = Lite

        quality_score = (
            task_complexity * 0.5
            + (1 - urgency_score) * 0.3
            + resource_availability * 0.2
        )

        if quality_score > 0.7:
            return UnifiedMode.QUALITY
        elif quality_score > 0.4:
            return UnifiedMode.BALANCED
        else:
            return UnifiedMode.LITE

    def merge_configs(self, base_config: dict, overrides: dict) -> dict:
        """
        Merge configuration with overrides

        Args:
            base_config: Base configuration
            overrides: Override values

        Returns:
            Merged configuration
        """
        merged = base_config.copy()

        for key, value in overrides.items():
            if (
                key in merged
                and isinstance(merged[key], dict)
                and isinstance(value, dict)
            ):
                merged[key] = self.merge_configs(merged[key], value)
            else:
                merged[key] = value

        return merged


# Singleton instance
_normalizer_instance = None


def get_mode_normalizer() -> ModeNormalizer:
    """Get singleton ModeNormalizer instance"""
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = ModeNormalizer()
    return _normalizer_instance
