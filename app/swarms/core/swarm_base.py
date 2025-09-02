"""
Unified Swarm Base Architecture - Foundation for all swarm types
Consolidates 57 swarm classes into strategic patterns
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app.models.requests import SwarmResponse
from app.swarms.communication.message_bus import MessageBus

logger = logging.getLogger(__name__)


# =============================================================================
# CORE CONFIGURATION - UNIFIED APPROACH
# =============================================================================

class SwarmType(Enum):
    """Unified swarm classification system"""
    STANDARD = "standard"       # Basic agent swarm
    CODING = "coding"          # Code generation specialized
    MEMORY_ENHANCED = "memory_enhanced"  # Memory-augmented
    GENESIS = "genesis"       # Advanced evolutionary
    FAST = "fast"            # Speed-optimized
    DEBATE = "debate"         # Adversarial debate focused
    CONSENSUS = "consensus"    # Decision-focused

class SwarmExecutionMode(Enum):
    """Execution strategies"""
    LINEAR = "linear"         # Sequential agent execution
    PARALLEL = "parallel"     # All agents in parallel
    DEBATE = "debate"         # Adversarial approach
    CONSENSUS = "consensus"   # Voting/consensus
    HIERARCHICAL = "hierarchical"  # Manager/agent pattern
    EVOLUTIONARY = "evolutionary"  # Generation-based

class SwarmCapability(Enum):
    """Core capabilities that swarms can provide"""
    CODING = "coding"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    CREATIVITY = "creativity"
    DECISION_MAKING = "decision_making"
    MEMORY_PROCESSING = "memory_processing"
    DEBATE = "debate"
    PLANNING = "planning"
    QUALITY_ASSURANCE = "quality_assurance"
    TASK_EXECUTION = "task_execution"


# =============================================================================
# SWARM METRICS & MONITORING
# =============================================================================

@dataclass
class SwarmMetrics:
    """Comprehensive swarm performance tracking"""
    total_requests: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    avg_response_time: float = 0.0
    agent_utilization: dict[str, float] = field(default_factory=dict)
    pattern_usage: dict[str, int] = field(default_factory=dict)
    capability_scores: dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def record_execution(
        self,
        success: bool,
        response_time: float,
        agents_used: list[str],
        patterns_used: list[str]
    ):
        """Record execution metrics"""
        self.total_requests += 1

        if success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1

        # Update response time (rolling average)
        if self.avg_response_time == 0:
            self.avg_response_time = response_time
        else:
            self.avg_response_time = (self.avg_response_time * (self.total_requests - 1) + response_time) / self.total_requests

        # Agent utilization
        agent_weight = 1.0 / len(agents_used) if agents_used else 1.0
        for agent in agents_used:
            current = self.agent_utilization.get(agent, 0.0)
            self.agent_utilization[agent] = current + agent_weight

        # Pattern usage
        for pattern in patterns_used:
            self.pattern_usage[pattern] = self.pattern_usage.get(pattern, 0) + 1

        self.last_updated = datetime.now()

    def get_performance_score(self) -> float:
        """Calculate overall performance score 0-100"""
        if self.total_requests == 0:
            return 0.0

        success_rate = self.successful_executions / self.total_requests
        avg_response_time_score = max(0, min(100, 1000 / max(self.avg_response_time, 0.1)))

        # Weighted score
        return success_rate * 70.0 + avg_response_time_score * 30.0


# =============================================================================
# SWARM CONFIGURATION - UNIFIED SETTINGS
# =============================================================================

@dataclass
class SwarmConfig:
    """Unified configuration for all swarm types"""
    swarm_id: str
    swarm_type: SwarmType
    execution_mode: SwarmExecutionMode = SwarmExecutionMode.PARALLEL

    # Agent configuration
    agent_count: int = 5
    agent_types: list[str] = field(default_factory=lambda: ["planner", "critic", "generator", "runner"])
    capabilities: list[SwarmCapability] = field(default_factory=list)

    # Execution parameters
    max_execution_time: float = 300.0  # 5 minutes
    timeout_per_agent: float = 60.0
    quality_threshold: float = 0.8

    # Patterns to enable
    enabled_patterns: list[str] = field(default_factory=lambda: [
        "quality_gates", "consensus", "strategy_archive", "debate"
    ])

    # Memory integration
    memory_enabled: bool = True
    memory_prediction: bool = False

    # Monitoring
    metrics_enabled: bool = True
    logging_level: str = "INFO"

    # Environment
    session_id: str | None = None
    user_id: str | None = None
    environment: str = "production"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SwarmConfig":
        """Create config from dictionary"""
        # Convert string enums back to proper enums
        if "swarm_type" in data and isinstance(data["swarm_type"], str):
            data["swarm_type"] = SwarmType(data["swarm_type"])
        if "execution_mode" in data and isinstance(data["execution_mode"], str):
            data["execution_mode"] = SwarmExecutionMode(data["execution_mode"])
        if "capabilities" in data and data["capabilities"]:
            data["capabilities"] = [SwarmCapability(c) if isinstance(c, str) else c
                                   for c in data["capabilities"]]

        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Enum):
                data[key] = value.value
            else:
                data[key] = value
        return data


# =============================================================================
# ABSTRACT SWARM BASE CLASS
# =============================================================================

class SwarmBase(ABC):
    """
    Abstract Base Class for all swarm implementations
    Consolidated from ImprovedAgentSwarm, OptimizedSwarm, and various specialized swarms
    """

    def __init__(self, config: SwarmConfig, agents: list[Any] | None = None, message_bus: MessageBus | None = None):
        self.config = config
        self.agents = agents or []
        self.metrics = SwarmMetrics()
        self.is_initialized = False

        # Core components
        self.patterns = {}
        self.memory_client = None
        self.message_bus = message_bus or MessageBus()
        self.orchestrator = None

        # Internal state
        self.execution_history = []

        logger.info(f"🐝 Initialized {config.swarm_type.value} swarm: {config.swarm_id}")

    async def initialize(self) -> bool:
        """Initialize swarm components and agents"""
        if self.is_initialized:
            return True

        # Initialize message bus
        await self.message_bus.initialize()

        # Initialize memory client if enabled
        if self.config.memory_enabled:
            # In real implementation, this would initialize memory client
            self.memory_client = None

        # Initialize patterns
        enabled_patterns = self.config.enabled_patterns
        self.patterns = {}
        for pattern_name in enabled_patterns:
            if pattern_name in _swarm_patterns:
                try:
                    pattern = _swarm_patterns[pattern_name]()
                    self.patterns[pattern_name] = pattern
                    logger.info(f"Intialized pattern: {pattern_name}")
                except Exception as e:
                    logger.warning(f"Failed to initialize pattern {pattern_name}: {str(e)}")

        # Initialize agents
        for agent in self.agents:
            if hasattr(agent, 'initialize'):
                await agent.initialize()

        self.is_initialized = True
        return True

    @abstractmethod
    async def solve_problem(self, problem: dict[str, Any]) -> SwarmResponse:
        """Execute swarm problem-solving logic"""
        pass

    @abstractmethod
    async def get_swarm_capabilities(self) -> list[SwarmCapability]:
        """Get swarm's capabilities"""
        pass

    @abstractmethod
    async def validate_problem(self, problem: dict[str, Any]) -> tuple[bool, str]:
        """Validate if swarm can handle this problem"""
        pass

    # =============================================================================
    # COMMON METHODS - SHARED ACROSS ALL SWARMS
    # =============================================================================

    async def prepare_context(self, problem: dict[str, Any]) -> dict[str, Any]:
        """Prepare execution context with memory and patterns"""

        context = {
            "problem": problem,
            "swarm_id": self.config.swarm_id,
            "swarm_type": self.config.swarm_type.value,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.config.session_id,
            "capabilities": [cap.value for cap in await self.get_swarm_capabilities()],
            "available_patterns": list(self.patterns.keys()),
            "agent_count": len(self.agents),
            "execution_mode": self.config.execution_mode.value
        }

        # Add memory context if enabled
        if self.config.memory_enabled and self.memory_client:
            try:
                memory_context = await self.memory_client.load_swarm_context(self.config.swarm_id)
                context["memory_context"] = memory_context
                logger.info("📚 Loaded memory context for swarm execution")
            except Exception as e:
                logger.warning(f"Failed to load memory context: {e}")
                context["memory_context"] = {}

        return context

    async def apply_patterns(self, problem: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Apply enabled patterns to enhance problem solving"""

        enhanced_problem = dict(problem)  # Copy

        for pattern_name in self.config.enabled_patterns:
            if pattern_name in self.patterns and pattern_name != "quality_gates":
                try:
                    pattern = self.patterns[pattern_name]
                    result = await pattern.apply(enhanced_problem, context)

                    if result.get("success", False):
                        enhanced_problem = result.get("enhanced_problem", enhanced_problem)
                        context[f"pattern_{pattern_name}"] = result
                        logger.info(f"✅ Applied pattern: {pattern_name}")

                    else:
                        logger.warning(f"⚠️ Pattern failed: {pattern_name} - {result.get('error', 'Unknown error')}")

                except Exception as e:
                    logger.error(f"Pattern execution failed {pattern_name}: {e}")

        return enhanced_problem, context

    async def execute_agents(self, problem: dict[str, Any], context: dict[str, Any]) -> list[dict[str, Any]]:
        """Execute agents based on execution mode"""

        mode = self.config.execution_mode

        if mode == SwarmExecutionMode.PARALLEL:
            return await self._execute_parallel(problem, context)
        elif mode == SwarmExecutionMode.LINEAR:
            return await self._execute_linear(problem, context)
        elif mode == SwarmExecutionMode.HIERARCHICAL:
            return await self._execute_hierarchical(problem, context)
        elif mode == SwarmExecutionMode.EVOLUTIONARY:
            return await self._execute_evolutionary(problem, context)
        elif mode == SwarmExecutionMode.DEBATE:
            return await self._execute_debate(problem, context)
        elif mode == SwarmExecutionMode.CONSENSUS:
            return await self._execute_consensus(problem, context)
        else:
            # Default to parallel
            return await self._execute_parallel(problem, context)

    async def _execute_parallel(self, problem: dict[str, Any], context: dict[str, Any]) -> list[dict[str, Any]]:
        """Execute all agents in parallel"""
        if not self.agents:
            return []

        async def execute_agent(agent):
            return await self._execute_single_agent(agent, problem, context)

        tasks = [execute_agent(agent) for agent in self.agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and return valid results
        return [r for r in results if not isinstance(r, Exception)]

    async def _execute_linear(self, problem: dict[str, Any], context: dict[str, Any]) -> list[dict[str, Any]]:
        """Execute agents sequentially"""
        results = []

        for agent in self.agents:
            try:
                result = await self._execute_single_agent(agent, problem, context)
                results.append(result)

                # Pass result to next agent via context
                context["previous_results"] = results

            except Exception as e:
                logger.error(f"Agent execution failed: {e}")
                continue

        return results

    async def _execute_hierarchical(self, problem: dict[str, Any], context: dict[str, Any]) -> list[dict[str, Any]]:
        """Execute in hierarchical pattern (coordinator + workers)"""
        if not self.agents:
            return []

        # First agent is coordinator
        coordinator = self.agents[0]
        workers = self.agents[1:]

        try:
            # Coordinator plans and assigns tasks
            coordinator_result = await self._execute_single_agent(
                coordinator, problem, context
            )

            if coordinator_result.get("success", False):
                task_assignments = coordinator_result.get("task_assignments", [])

                # Execute worker tasks
                worker_results = await self._execute_parallel_impl(workers, task_assignments, context)

                return [coordinator_result] + worker_results

        except Exception as e:
            logger.error(f"Hierarchical execution failed: {e}")

        # Fallback to parallel
        return await self._execute_parallel(problem, context)

    async def _execute_parallel_impl(self, agents: list[Any], task_assignments: list[dict[str, Any]],
                                   context: dict[str, Any]) -> list[dict[str, Any]]:
        """Helper for parallel execution with assignments"""
        # For simplicity, distribute equally
        chunk_size = len(agents) // len(task_assignments) if task_assignments else 1
        agent_chunks = [agents[i:i + chunk_size] for i in range(0, len(agents), chunk_size)]

        async def execute_chunk(chunk, task_idx):
            results = []
            task_context = dict(context)
            if task_idx < len(task_assignments):
                task_context["assigned_task"] = task_assignments[task_idx]

            for agent in chunk:
                try:
                    result = await self._execute_single_agent(agent, task_assignments[task_idx], task_context)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Chunk execution failed: {e}")

            return results

        tasks = [execute_chunk(chunk, i) for i, chunk in enumerate(agent_chunks)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return [r for chunk_results in results
                if not isinstance(chunk_results, Exception)
                for r in chunk_results
                if isinstance(r, dict)]

    async def _execute_evolutionary(self, problem: dict[str, Any], context: dict[str, Any]) -> list[dict[str, Any]]:
        """Execute evolutionary algorithm-based solving"""
        # Placeholder - would implement generations of solutions
        logger.info("🧬 Executing evolutionary swarm logic")
        return await self._execute_parallel(problem, context)

    async def _execute_debate(self, problem: dict[str, Any], context: dict[str, Any]) -> list[dict[str, Any]]:
        """Execute adversarial debate pattern"""
        # Rely on debate pattern if enabled
        if "debate" in self.patterns:
            try:
                debate_pattern = self.patterns["debate"]
                debate_result = await debate_pattern.apply(problem, context)
                return [debate_result]
            except Exception as e:
                logger.error(f"Debate execution failed: {e}")

        # Fallback to parallel
        return await self._execute_parallel(problem, context)

    async def _execute_consensus(self, problem: dict[str, Any], context: dict[str, Any]) -> list[dict[str, Any]]:
        """Execute consensus-based decision making"""
        # Rely on consensus pattern if enabled
        if "consensus" in self.patterns:
            try:
                consensus_pattern = self.patterns["consensus"]
                consensus_result = await consensus_pattern.apply(problem, context)
                return [consensus_result]
            except Exception as e:
                logger.error(f"Consensus execution failed: {e}")

        # Fallback to parallel
        return await self._execute_parallel(problem, context)

    @abstractmethod
    async def _execute_single_agent(self, agent: Any, problem: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Execute single agent - implementation specific"""
        pass

    # =============================================================================
    # QUALITY CONTROL & VALIDATION
    # =============================================================================

    async def apply_quality_gates(self, results: list[dict[str, Any]], problem: dict[str, Any]) -> tuple[bool, list[dict[str, Any]]]:
        """Apply quality gates to results (implementation in patterns)"""

        if "quality_gates" in self.patterns:
            try:
                quality_pattern = self.patterns["quality_gates"]
                quality_result = await quality_pattern.apply({
                    "results": results,
                    "problem": problem,
                    "threshold": self.config.quality_threshold
                }, {})

                if quality_result.get("success", False):
                    passed_results = quality_result.get("filtered_results", results)
                    return True, passed_results
                else:
                    logger.warning(f"Quality gates failed: {quality_result.get('reason', 'Unknown')}")
                    return False, results

            except Exception as e:
                logger.error(f"Quality gates execution failed: {e}")

        # No quality gates or error - return all results
        return True, results

    async def reach_consensus(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Reach consensus from multiple agent results"""

        if not results:
            return {}

        # Simple majority voting for now
        if len(results) == 1:
            return results[0]

        # Count successes
        successful_results = [r for r in results if r.get("success", False)]
        if not successful_results:
            return {
                "success": False,
                "error": "No successful agent results",
                "agent_count": len(results),
                "successful_agents": 0
            }

        # Return best result (by confidence or score)
        sorted_results = sorted(
            successful_results,
            key=lambda x: x.get("confidence", x.get("score", 0)),
            reverse=True
        )

        best_result = sorted_results[0]
        best_result["consensus_info"] = {
            "total_agents": len(results),
            "successful_agents": len(successful_results),
            "consensus_method": "highest_confidence"
        }

        return best_result

    # =============================================================================
    # LIFECYCLE MANAGEMENT
    # =============================================================================

    async def cleanup(self):
        """Cleanup swarm resources"""
        # Cleanup patterns
        for pattern_name, pattern in self.patterns.items():
            if hasattr(pattern, 'cleanup'):
                try:
                    await pattern.cleanup()
                except Exception as e:
                    logger.warning(f"Pattern cleanup failed {pattern_name}: {e}")

        # Cleanup memory client
        if self.memory_client and hasattr(self.memory_client, 'close'):
            try:
                await self.memory_client.close()
            except Exception as e:
                logger.warning(f"Memory client cleanup failed: {e}")

        # Cleanup message bus
        if hasattr(self.message_bus, 'close'):
            try:
                await self.message_bus.close()
            except Exception as e:
                logger.warning(f"Message bus cleanup failed: {e}")

        self.is_initialized = False
        logger.info(f"🧹 Cleaned up swarm: {self.config.swarm_id}")

    def get_swarm_status(self) -> dict[str, Any]:
        """Get current swarm status"""

        return {
            "swarm_id": self.config.swarm_id,
            "swarm_type": self.config.swarm_type.value,
            "is_initialized": self.is_initialized,
            "agent_count": len(self.agents),
            "enabled_patterns": list(self.patterns.keys()),
            "capabilities": [cap.value for cap in self.config.capabilities],
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "success_rate": self.metrics.successful_executions / max(self.metrics.total_requests, 1),
                "performance_score": self.metrics.get_performance_score(),
                "avg_response_time": self.metrics.avg_response_time
            },
            "memory_enabled": self.config.memory_enabled,
            "last_activity": self.metrics.last_updated.isoformat()
        }

    def update_config(self, updates: dict[str, Any]):
        """Update swarm configuration"""
        for key, value in updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        logger.info(f"⚙️ Updated swarm config: {updates}")
        self.metrics.last_updated = datetime.now()


# =============================================================================
# GLOBAL CONFIGURATIONS & UTILITIES
# =============================================================================

DEFAULT_SWARM_CONFIGS = {
    SwarmType.CODING: SwarmConfig(
        swarm_id="coding-swarm-default",
        swarm_type=SwarmType.CODING,
        execution_mode=SwarmExecutionMode.HIERARCHICAL,
        agent_types=["planner", "coder", "reviewer", "tester"],
        capabilities=[SwarmCapability.CODING, SwarmCapability.QUALITY_ASSURANCE],
        enabled_patterns=["quality_gates", "strategy_archive"]
    ),

    SwarmType.MEMORY_ENHANCED: SwarmConfig(
        swarm_id="memory-swarm-default",
        swarm_type=SwarmType.MEMORY_ENHANCED,
        execution_mode=SwarmExecutionMode.PARALLEL,
        agent_types=["planner", "critic", "memory_agent", "generator", "runner"],
        capabilities=[SwarmCapability.MEMORY_PROCESSING, SwarmCapability.RESEARCH, SwarmCapability.ANALYSIS],
        enabled_patterns=["quality_gates", "strategy_archive", "memory_integration"]
    ),

    SwarmType.FAST: SwarmConfig(
        swarm_id="fast-swarm-default",
        swarm_type=SwarmType.FAST,
        execution_mode=SwarmExecutionMode.PARALLEL,
        agent_types=["quick_planner", "fast_coder", "rapid_executor"],
        capabilities=[SwarmCapability.TASK_EXECUTION, SwarmCapability.PLANNING],
        enabled_patterns=["quality_gates"]
    ),

    SwarmType.GENESIS: SwarmConfig(
        swarm_id="genesis-swarm-default",
        swarm_type=SwarmType.GENESIS,
        execution_mode=SwarmExecutionMode.EVOLUTIONARY,
        agent_types=["evolutionary_planner", "innovator", "evolver", "optimizer"],
        capabilities=[SwarmCapability.CREATIVITY, SwarmCapability.QUALITY_ASSURANCE, SwarmCapability.PLAYER],
        enabled_patterns=["strategy_archive", "quality_gates", "evolution"]
    ),

    SwarmType.STANDARD: SwarmConfig(
        swarm_id="standard-swarm-default",
        swarm_type=SwarmType.STANDARD,
        execution_mode=SwarmExecutionMode.PARALLEL,
        agent_types=["planner", "critic", "generator", "runner"],
        capabilities=[SwarmCapability.PLANNING, SwarmCapability.ANALYSIS, SwarmCapability.CREATIVITY],
        enabled_patterns=["quality_gates", "consensus", "strategy_archive"]
    )
}


# =============================================================================
# SWARM FACTORY - CREATION UTILITIES
# =============================================================================

class SwarmFactory:
    """Factory for creating swarm instances"""

    @staticmethod
    def create_swarm(
        swarm_type: SwarmType,
        config: SwarmConfig | None = None,
        agents: list[Any] | None = None,
        message_bus: MessageBus | None = None
    ) -> SwarmBase:
        """Create swarm instance based on type"""
        if isinstance(swarm_type, str):
            swarm_type = SwarmType(swarm_type)

        if config is None:
            config = DEFAULT_SWARM_CONFIGS.get(swarm_type, DEFAULT_SWARM_CONFIGS[SwarmType.STANDARD])
            config = SwarmConfig(**config.__dict__)  # Create copy

        if config.swarm_type != swarm_type:
            config.swarm_type = swarm_type

        # Would instantiate specific swarm classes here
        # For now, return base class (placeholder)
        return SwarmBase(config, agents, message_bus) if agents else SwarmBase(config, None, message_bus)

    @staticmethod
    def create_swarm_from_config(config_dict: dict[str, Any]) -> SwarmBase:
        """Create swarm from configuration dictionary"""
        config = SwarmConfig.from_dict(config_dict)
        return SwarmFactory.create_swarm(config.swarm_type, config)

    @staticmethod
    def optimize_config_for_task(task: dict[str, Any], base_type: SwarmType = SwarmType.STANDARD) -> SwarmConfig:
        """Automatically optimize swarm configuration for a specific task"""
        config = SwarmConfig(**DEFAULT_SWARM_CONFIGS[base_type].__dict__)

        # Task-type optimizations
        task_type = task.get("type", "").lower()
        if "code" in task_type or "programming" in task_type:
            config.swarm_type = SwarmType.CODING
            config.execution_mode = SwarmExecutionMode.HIERARCHICAL
            config.capabilities = [SwarmCapability.CODING, SwarmCapability.QUALITY_ASSURANCE]

        elif "research" in task_type or "analysis" in task_type:
            config.swarm_type = SwarmType.MEMORY_ENHANCED
            config.memory_enabled = True
            config.capabilities = [SwarmCapability.RESEARCH, SwarmCapability.ANALYSIS]

        elif "creative" in task_type or "writing" in task_type:
            config.swarm_type = SwarmType.STANDARD
            config.execution_mode = SwarmExecutionMode.DEBATE
            config.capabilities = [SwarmCapability.CREATIVITY, SwarmCapability.QUALITY_ASSURANCE]

        return config


# =============================================================================
# GLOBAL INSTANCE MANAGEMENT
# =============================================================================

_swarm_instances: dict[str, SwarmBase] = {}

def get_swarm(swarm_id: str) -> SwarmBase | None:
    """Get existing swarm instance"""
    return _swarm_instances.get(swarm_id)

def register_swarm(swarmy_id: str, swarm: SwarmBase):
    """Register swarm instance for reuse"""
    _swarm_instances[swarmy_id] = swarm

def list_active_swarms() -> list[dict[str, Any]]:
    """List all active swarm instances"""
    return [
        {
            "swarm_id": swarm_id,
            "config": swarm.get_swarm_status()
        }
        for swarm_id, swarm in _swarm_instances.items()
    ]

async def cleanup_all_swarms():
    """Cleanup all registered swarm instances"""
    cleanup_tasks = []
    for swarm_id, swarm in _swarm_instances.items():
        cleanup_tasks.append(swarm.cleanup())

    await asyncio.gather(*cleanup_tasks, return_exceptions=True)
    _swarm_instances.clear()

    logger.info(f"🧹 Cleaned up {len(cleanup_tasks)} swarm instances")


# =============================================================================
# EXECUTION UTILITIES
# =============================================================================

def validate_task_compatibility(task: dict[str, Any], swarm: SwarmBase) -> tuple[bool, str]:
    """Validate if a swarm can handle a specific task"""
    swarm_caps = [cap.value for cap in swarm.config.capabilities]
    task_requires = task.get("required_capabilities", [])
    task_optional = task.get("optional_capabilities", [])

    # Check required capabilities
    missing_required = [cap for cap in task_requires if cap not in swarm_caps]
    if missing_required:
        return False, f"Missing required capabilities: {missing_required}"

    # Check optional capabilities (warning but allow)
    missing_optional = [cap for cap in task_optional if cap not in swarm_caps]
    if missing_optional:
        return True, f"Missing optional capabilities (may reduce performance): {missing_optional}"

    return True, "Task is compatible with swarm"


async def execute_swarm_task(
    swarm_id: str,
    task: dict[str, Any],
    **kwargs
) -> SwarmResponse | None:
    """Execute a task on an existing swarm"""
    swarm = get_swarm(swarm_id)
    if not swarm:
        raise ValueError(f"Swarm {swarm_id} not found")

    # Validate compatibility
    compatible, reason = validate_task_compatibility(task, swarm)
    if not compatible:
        raise ValueError(f"Task not compatible with swarm: {reason}")

    # Execute the task
    start_time = asyncio.get_event_loop().time()
    result = await swarm.solve_problem(task)
    response_time = asyncio.get_event_loop().time() - start_time

    # Record metrics
    success = result.success if hasattr(result, 'success') else True
    agents_used = [agent.__class__.__name__ for agent in swarm.agents]
    patterns_used = list(swarm.patterns.keys())

    swarm.metrics.record_execution(success, response_time, agents_used, patterns_used)

    return result


# =============================================================================
# SWARM PATTERN REGISTRY
# =============================================================================

_swarm_patterns: dict[str, Any] = {}

def register_swarm_pattern(name: str, pattern_class: Any):
    """Register a swarm pattern for use by swarms"""
    _swarm_patterns[name] = pattern_class

def get_swarm_pattern(name: str) -> Any | None:
    """Get registered swarm pattern"""
    return _swarm_patterns.get(name)

def list_registered_patterns() -> list[str]:
    """List all registered swarm patterns"""
    return list(_swarm_patterns.keys())


if __name__ == "__main__":
    # Example usage
    print("🐝 Unified Swarm Architecture initialized")
    print(f"Available swarm types: {[t.value for t in SwarmType]}")
    print(f"Default configurations: {len(DEFAULT_SWARM_CONFIGS)}")
    print(f"Registered patterns: {list_registered_patterns()}")
