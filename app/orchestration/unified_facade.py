"""
Unified Orchestrator Facade
Central routing and coordination for all swarm types and MCP assistants
"""

import json
import logging
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from app.core.circuit_breaker import with_circuit_breaker
from app.memory.unified_memory_store import UnifiedMemoryStore
from app.security.mcp_security import MCPSecurityFramework
from app.swarms.improved_swarm import ImprovedAgentSwarm

# from app.swarms.patterns.performance_monitoring import performance_monitoring  # Module not yet implemented
from app.swarms.simple_agent_orchestrator import SimpleAgentOrchestrator
from app.swarms.swarm_optimizer import SwarmOptimizer

logger = logging.getLogger(__name__)

class SwarmType(Enum):
    """Available swarm types"""
    CODING_DEBATE = "coding-debate"
    IMPROVED_SOLVE = "improved-solve"
    SIMPLE_AGENTS = "simple-agents"
    MCP_COORDINATED = "mcp-coordinated"

class OptimizationMode(Enum):
    """Normalized optimization modes"""
    LITE = "lite"  # Fast, minimal processing
    BALANCED = "balanced"  # Default, balanced approach
    QUALITY = "quality"  # High quality, thorough processing

@dataclass
class SwarmRequest:
    """Unified swarm execution request"""
    swarm_type: SwarmType
    task: str
    mode: OptimizationMode = OptimizationMode.BALANCED
    urgency: str = "normal"
    use_memory: bool = True
    stream: bool = True
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: dict[str, Any] = None
    mcp_assistants: list[str] = None  # ["claude", "roo", "cline"]

@dataclass
class SwarmEvent:
    """Streaming event from swarm execution"""
    event_type: str  # started, step, critic, judge, completed, error
    swarm: str
    timestamp: str
    data: dict[str, Any]

class UnifiedOrchestratorFacade:
    """
    Central orchestrator that routes to appropriate swarm implementations
    and coordinates with MCP assistants
    """

    def __init__(self):
        # Initialize swarm implementations
        self.coding_swarm = None
        self.improved_swarm = None
        self.simple_agents = None

        # Shared components
        self.optimizer = SwarmOptimizer()
        self.memory_store = UnifiedMemoryStore()
        self.security = MCPSecurityFramework()

        # MCP assistant coordination
        self.mcp_coordinators = {}

        # Circuit breakers for each component
        self.circuit_breakers = {
            "memory": self.optimizer.get_circuit_breaker("memory"),
            "llm": self.optimizer.get_circuit_breaker("llm"),
            "mcp": self.optimizer.get_circuit_breaker("mcp")
        }

        # Performance metrics
        self.metrics = {
            "executions": 0,
            "success_rate": 0.0,
            "avg_duration": 0.0
        }

    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing Unified Orchestrator Facade")

        # Initialize security
        await self.security.initialize()

        # Initialize memory store
        await self.memory_store.initialize()

        # Initialize swarms
        self.coding_swarm = SwarmOrchestrator(config={
            "use_memory": True,
            "optimization": "balanced"
        })

        self.improved_swarm = ImprovedAgentSwarm(
            config=self._load_swarm_config()
        )

        self.simple_agents = SimpleAgentOrchestrator()

        # Initialize MCP coordinators
        await self._initialize_mcp_coordinators()

        logger.info("Unified Orchestrator Facade initialized")

    def _load_swarm_config(self) -> dict:
        """Load swarm optimization config"""
        try:
            with open("app/swarms/swarm_optimization_config.json") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load swarm config: {e}, using defaults")
            return {
                "optimization_modes": {
                    "lite": {"timeout": 30, "max_agents": 2},
                    "balanced": {"timeout": 120, "max_agents": 5},
                    "quality": {"timeout": 300, "max_agents": 10}
                }
            }

    async def _initialize_mcp_coordinators(self):
        """Initialize MCP assistant coordinators"""
        from app.mcp.assistant_coordinator import MCPAssistantCoordinator

        assistants = ["claude", "roo", "cline"]
        for assistant in assistants:
            try:
                coordinator = MCPAssistantCoordinator(assistant_id=assistant)
                await coordinator.initialize()
                self.mcp_coordinators[assistant] = coordinator
                logger.info(f"Initialized MCP coordinator for {assistant}")
            except Exception as e:
                logger.error(f"Failed to initialize {assistant} coordinator: {e}")

    def _normalize_mode(self, mode: str) -> OptimizationMode:
        """Normalize mode strings to enum"""
        mode_map = {
            "fast": OptimizationMode.LITE,
            "speed": OptimizationMode.LITE,
            "lite": OptimizationMode.LITE,
            "balanced": OptimizationMode.BALANCED,
            "normal": OptimizationMode.BALANCED,
            "quality": OptimizationMode.QUALITY,
            "thorough": OptimizationMode.QUALITY
        }
        return mode_map.get(mode.lower(), OptimizationMode.BALANCED)

    async def _get_optimal_config(self, request: SwarmRequest) -> dict:
        """Get optimal configuration based on task and mode"""
        # Calculate task complexity
        complexity = self.optimizer.calculate_task_complexity(request.task)

        # Adjust mode based on urgency and complexity
        if request.urgency == "critical" and complexity < 0.5:
            mode = OptimizationMode.LITE
        elif complexity > 0.8:
            mode = OptimizationMode.QUALITY
        else:
            mode = request.mode

        # Get configuration for mode
        config = self.optimizer.get_optimal_swarm_config(request.task)
        config["mode"] = mode.value

        return config

    @with_circuit_breaker("database")
    async def _inject_memory_context(self, request: SwarmRequest) -> dict:
        """Inject relevant memory context for the task"""
        if not request.use_memory:
            return {}

        try:
            cb = self.circuit_breakers["memory"]
            async with performance_monitoring(self.optimizer, "memory_search"):
                results = await cb.call(
                    self.memory_store.search_memory,
                    query=request.task,
                    limit=5
                )

            return {
                "memory_context": results,
                "context_count": len(results)
            }
        except Exception as e:
            logger.warning(f"Failed to inject memory context: {e}")
            # Apply degradation strategy
            strategy = self.optimizer.degradation_manager.get_degradation_strategy("memory")
            if strategy["fallback_mode"] == "skip":
                return {}
            raise

    async def _store_execution_results(self, request: SwarmRequest, result: dict):
        """Store execution results in memory"""
        if not request.use_memory:
            return

        try:
            cb = self.circuit_breakers["memory"]
            async with performance_monitoring(self.optimizer, "memory_store"):
                await cb.call(
                    self.memory_store.store_memory,
                    content=json.dumps(result),
                    metadata={
                        "type": "swarm_execution",
                        "swarm_type": request.swarm_type.value,
                        "mode": request.mode.value,
                        "task": request.task[:100],
                        "session_id": request.session_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to store results: {e}")

    async def execute(
        self,
        request: SwarmRequest
    ) -> AsyncGenerator[SwarmEvent, None]:
        """
        Execute swarm request with streaming events
        """
        self.metrics["executions"] += 1
        start_time = datetime.utcnow()

        # Emit start event
        yield SwarmEvent(
            event_type="started",
            swarm=request.swarm_type.value,
            timestamp=start_time.isoformat(),
            data={
                "session_id": request.session_id,
                "mode": request.mode.value,
                "task_preview": request.task[:100]
            }
        )

        try:
            # Get optimal configuration
            config = await self._get_optimal_config(request)

            # Inject memory context
            context = await self._inject_memory_context(request)

            # Route to appropriate swarm
            if request.swarm_type == SwarmType.CODING_DEBATE:
                result = await self._execute_coding_swarm(request, config, context)
            elif request.swarm_type == SwarmType.IMPROVED_SOLVE:
                result = await self._execute_improved_swarm(request, config, context)
            elif request.swarm_type == SwarmType.SIMPLE_AGENTS:
                result = await self._execute_simple_agents(request, config, context)
            elif request.swarm_type == SwarmType.MCP_COORDINATED:
                result = await self._execute_mcp_coordinated(request, config, context)
            else:
                raise ValueError(f"Unknown swarm type: {request.swarm_type}")

            # Store results
            await self._store_execution_results(request, result)

            # Emit completion event
            duration = (datetime.utcnow() - start_time).total_seconds()
            yield SwarmEvent(
                event_type="completed",
                swarm=request.swarm_type.value,
                timestamp=datetime.utcnow().isoformat(),
                data={
                    "result": result,
                    "duration": duration,
                    "mode": config["mode"]
                }
            )

            # Update metrics
            self.metrics["success_rate"] = (
                self.metrics["success_rate"] * (self.metrics["executions"] - 1) +
                1.0
            ) / self.metrics["executions"]

        except Exception as e:
            logger.error(f"Swarm execution failed: {e}")

            # Apply degradation
            strategy = self.optimizer.degradation_manager.get_degradation_strategy(
                request.swarm_type.value
            )

            # Emit error event
            yield SwarmEvent(
                event_type="error",
                swarm=request.swarm_type.value,
                timestamp=datetime.utcnow().isoformat(),
                data={
                    "error": str(e),
                    "degradation_strategy": strategy
                }
            )

            # Update failure metrics
            self.metrics["success_rate"] = (
                self.metrics["success_rate"] * (self.metrics["executions"] - 1)
            ) / self.metrics["executions"]

    async def _execute_coding_swarm(
        self,
        request: SwarmRequest,
        config: dict,
        context: dict
    ) -> dict:
        """Execute coding debate swarm"""
        cb = self.circuit_breakers["llm"]

        async with performance_monitoring(self.optimizer, "coding_swarm"):
            # Update swarm config with normalized mode
            self.coding_swarm.config["optimization"] = config["mode"]
            self.coding_swarm.config["memory_context"] = context

            # Execute with circuit breaker
            result = await cb.call(
                self.coding_swarm.run_debate,
                task=request.task,
                max_rounds=config.get("max_rounds", 3),
                timeout=config.get("timeout", 120)
            )

            return result

    async def _execute_improved_swarm(
        self,
        request: SwarmRequest,
        config: dict,
        context: dict
    ) -> dict:
        """Execute improved pattern-based swarm"""
        cb = self.circuit_breakers["llm"]

        async with performance_monitoring(self.optimizer, "improved_swarm"):
            # Configure patterns based on mode
            self.improved_swarm.optimization_mode = config["mode"]

            # Update enabled patterns
            if config["mode"] == "lite":
                self.improved_swarm.enabled_patterns = ["safety_boundaries"]
            elif config["mode"] == "balanced":
                self.improved_swarm.enabled_patterns = [
                    "safety_boundaries",
                    "dynamic_role_assignment",
                    "quality_gates"
                ]
            else:  # quality
                self.improved_swarm.enabled_patterns = [
                    "safety_boundaries",
                    "dynamic_role_assignment",
                    "adversarial_debate",
                    "quality_gates",
                    "consensus_mechanisms",
                    "strategy_archive"
                ]

            # Execute
            result = await cb.call(
                self.improved_swarm.solve_with_improvements,
                problem=request.task,
                context=context
            )

            return result

    async def _execute_simple_agents(
        self,
        request: SwarmRequest,
        config: dict,
        context: dict
    ) -> dict:
        """Execute simple sequential agents"""
        cb = self.circuit_breakers["llm"]

        async with performance_monitoring(self.optimizer, "simple_agents"):
            result = await cb.call(
                self.simple_agents.execute_workflow,
                workflow_id="sequential",
                task=request.task,
                context=context,
                config=config
            )

            return result

    async def _execute_mcp_coordinated(
        self,
        request: SwarmRequest,
        config: dict,
        context: dict
    ) -> dict:
        """Execute task with MCP assistant coordination"""
        cb = self.circuit_breakers["mcp"]

        async with performance_monitoring(self.optimizer, "mcp_coordinated"):
            # Determine which assistants to use
            assistants = request.mcp_assistants or ["claude", "roo", "cline"]

            # Create coordination plan
            plan = await self._create_mcp_coordination_plan(
                request.task,
                assistants,
                config["mode"]
            )

            # Execute plan with assistants
            results = {}
            for step in plan["steps"]:
                assistant = step["assistant"]
                if assistant in self.mcp_coordinators:
                    coordinator = self.mcp_coordinators[assistant]

                    result = await cb.call(
                        coordinator.execute_task,
                        task=step["task"],
                        context={**context, "previous_results": results}
                    )

                    results[assistant] = result

                    # Stream progress
                    # (This would yield events in real implementation)

            return {
                "plan": plan,
                "results": results,
                "synthesis": await self._synthesize_mcp_results(results)
            }

    async def _create_mcp_coordination_plan(
        self,
        task: str,
        assistants: list[str],
        mode: str
    ) -> dict:
        """Create execution plan for MCP assistants"""
        plan = {
            "task": task,
            "mode": mode,
            "steps": []
        }

        # Analyze task to determine assistant roles
        if "code" in task.lower() or "implement" in task.lower():
            # Code-heavy task
            plan["steps"].append({
                "assistant": "roo",
                "task": f"Analyze codebase and patterns for: {task}",
                "role": "code_analysis"
            })
            plan["steps"].append({
                "assistant": "cline",
                "task": f"Create implementation plan for: {task}",
                "role": "planning"
            })
            plan["steps"].append({
                "assistant": "claude",
                "task": f"Review and synthesize approach for: {task}",
                "role": "synthesis"
            })
        else:
            # General task
            plan["steps"].append({
                "assistant": "claude",
                "task": f"Initial analysis of: {task}",
                "role": "analysis"
            })
            if mode != "lite":
                plan["steps"].append({
                    "assistant": "cline",
                    "task": f"Execute task autonomously: {task}",
                    "role": "execution"
                })

        return plan

    async def _synthesize_mcp_results(self, results: dict) -> dict:
        """Synthesize results from multiple MCP assistants"""
        synthesis = {
            "consensus": None,
            "conflicts": [],
            "recommendations": []
        }

        # Analyze results for consensus and conflicts
        # (Implementation would analyze actual results)

        return synthesis

    async def get_metrics(self) -> dict:
        """Get current orchestrator metrics"""
        return {
            **self.metrics,
            "circuit_breakers": {
                name: cb.get_state()
                for name, cb in self.circuit_breakers.items()
            },
            "optimizer_health": self.optimizer.get_system_health(),
            "mcp_coordinators": list(self.mcp_coordinators.keys())
        }


class MCPAssistantCoordinator:
    """Coordinator for individual MCP assistant"""

    def __init__(self, assistant_id: str):
        self.assistant_id = assistant_id
        self.client = None

    async def initialize(self):
        """Initialize connection to MCP assistant"""
        # This would connect to the actual MCP bridge adapter

    async def execute_task(self, task: str, context: dict) -> dict:
        """Execute task with this assistant"""
        # This would call the appropriate MCP adapter
        return {
            "assistant": self.assistant_id,
            "task": task,
            "result": f"Executed by {self.assistant_id}",
            "timestamp": datetime.utcnow().isoformat()
        }
