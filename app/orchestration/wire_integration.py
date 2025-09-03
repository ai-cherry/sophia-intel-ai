"""
Wire Integration Script
Connects MCP bridges, swarms, and orchestrator with proper mode normalization
"""

import asyncio
import logging
from typing import Any

from app.orchestration.mode_normalizer import get_mode_normalizer
from app.orchestration.unified_facade import (
    OptimizationMode,
    SwarmRequest,
    SwarmType,
    UnifiedOrchestratorFacade,
)
# from app.swarms.patterns.performance_monitoring import performance_monitoring  # Module not yet implemented
from app.swarms.swarm_optimizer import SwarmOptimizer

logger = logging.getLogger(__name__)

class IntegratedSwarmSystem:
    """
    Fully integrated swarm system with MCP bridges and normalized modes
    """

    def __init__(self):
        self.facade = UnifiedOrchestratorFacade()
        self.normalizer = get_mode_normalizer()
        self.optimizer = SwarmOptimizer()

    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing Integrated Swarm System")

        # Initialize facade (which initializes swarms and MCP)
        await self.facade.initialize()

        # Apply mode normalization fixes
        await self._apply_mode_fixes()

        # Wire circuit breakers and monitoring
        await self._wire_monitoring()

        logger.info("Integrated Swarm System initialized")

    async def _apply_mode_fixes(self):
        """Apply mode normalization fixes to swarm components"""

        # Fix coding swarm configuration
        if self.facade.coding_swarm:
            # Ensure it recognizes lite mode
            self.facade.coding_swarm.config["mode_normalizer"] = self.normalizer
            logger.info("Applied mode normalizer to coding swarm")

        # Fix improved swarm configuration
        if self.facade.improved_swarm:
            # Wire the optimizer for dynamic mode selection
            self.facade.improved_swarm.optimizer = self.optimizer
            logger.info("Wired optimizer to improved swarm")

        # Configure MCP coordinators with normalized modes
        for name, coordinator in self.facade.mcp_coordinators.items():
            coordinator.mode_normalizer = self.normalizer
            logger.info(f"Applied mode normalizer to {name} coordinator")

    async def _wire_monitoring(self):
        """Wire performance monitoring and circuit breakers"""

        # Wrap swarm methods with monitoring
        if self.facade.coding_swarm:
            original_run = self.facade.coding_swarm.run_debate

            async def monitored_run(*args, **kwargs):
                async with performance_monitoring(self.optimizer, "coding_debate"):
                    return await original_run(*args, **kwargs)

            self.facade.coding_swarm.run_debate = monitored_run

        if self.facade.improved_swarm:
            original_solve = self.facade.improved_swarm.solve_with_improvements

            async def monitored_solve(*args, **kwargs):
                async with performance_monitoring(self.optimizer, "improved_solve"):
                    return await original_solve(*args, **kwargs)

            self.facade.improved_swarm.solve_with_improvements = monitored_solve

        logger.info("Wired performance monitoring to swarms")

    async def execute_with_mode_selection(
        self,
        task: str,
        swarm_type: str = "auto",
        urgency: str = "normal",
        use_memory: bool = True
    ) -> dict[str, Any]:
        """
        Execute task with automatic mode selection
        
        Args:
            task: Task to execute
            swarm_type: Type of swarm or "auto" for automatic selection
            urgency: Task urgency (low, normal, high, critical)
            use_memory: Whether to use memory system
            
        Returns:
            Execution results
        """
        # Calculate task complexity
        complexity = self.optimizer.calculate_task_complexity(task)

        # Select optimal mode
        mode = self.normalizer.select_mode_for_task(
            task_complexity=complexity,
            urgency=urgency,
            resource_availability=self.optimizer.get_system_health()
        )

        logger.info(f"Selected mode {mode.value} for task (complexity: {complexity:.2f})")

        # Auto-select swarm type if needed
        if swarm_type == "auto":
            if "code" in task.lower() or "implement" in task.lower():
                swarm_type = "coding-debate"
            elif complexity > 0.7:
                swarm_type = "improved-solve"
            else:
                swarm_type = "simple-agents"

        # Map string to enum
        swarm_type_enum = {
            "coding-debate": SwarmType.CODING_DEBATE,
            "improved-solve": SwarmType.IMPROVED_SOLVE,
            "simple-agents": SwarmType.SIMPLE_AGENTS,
            "mcp-coordinated": SwarmType.MCP_COORDINATED
        }.get(swarm_type, SwarmType.SIMPLE_AGENTS)

        # Create request
        request = SwarmRequest(
            swarm_type=swarm_type_enum,
            task=task,
            mode=OptimizationMode(mode.value),
            urgency=urgency,
            use_memory=use_memory,
            stream=False  # For simplicity in this example
        )

        # Execute via facade
        results = []
        async for event in self.facade.execute(request):
            results.append(event)
            if event.event_type == "completed":
                return event.data["result"]
            elif event.event_type == "error":
                raise Exception(f"Execution failed: {event.data['error']}")

        return {"status": "incomplete", "events": results}

    async def execute_mcp_coordinated(
        self,
        task: str,
        assistants: list = None,
        mode: str = "balanced"
    ) -> dict[str, Any]:
        """
        Execute task with MCP assistant coordination
        
        Args:
            task: Task to execute
            assistants: List of assistants to use (default: all)
            mode: Optimization mode
            
        Returns:
            Coordinated execution results
        """
        # Normalize mode
        unified_mode = self.normalizer.normalize_mode(mode)

        # Create request for MCP coordination
        request = SwarmRequest(
            swarm_type=SwarmType.MCP_COORDINATED,
            task=task,
            mode=OptimizationMode(unified_mode.value),
            mcp_assistants=assistants or ["claude", "roo", "cline"],
            use_memory=True,
            stream=False
        )

        # Execute
        results = []
        async for event in self.facade.execute(request):
            results.append(event)
            if event.event_type == "completed":
                return event.data["result"]
            elif event.event_type == "error":
                raise Exception(f"Execution failed: {event.data['error']}")

        return {"status": "incomplete", "events": results}

    async def demonstrate_mode_normalization(self):
        """Demonstrate that mode normalization is working"""

        test_modes = ["fast", "lite", "speed", "balanced", "quality", "thorough"]

        print("\n=== Mode Normalization Demo ===")
        for mode in test_modes:
            normalized = self.normalizer.normalize_mode(mode)
            config = self.normalizer.get_config(normalized)
            print(f"{mode:12} -> {normalized.value:8} (timeout: {config.timeout}s, agents: {config.max_agents})")

        # Test fast mode detection in coding swarm
        print("\n=== Fast Mode Detection ===")
        for mode in ["lite", "fast", "speed", "balanced", "quality"]:
            self.facade.coding_swarm.config["optimization"] = mode
            is_fast = self.facade.coding_swarm._is_fast_mode()
            print(f"{mode:8} -> fast_mode: {is_fast}")

    async def get_system_status(self) -> dict[str, Any]:
        """Get comprehensive system status"""

        status = {
            "facade_metrics": await self.facade.get_metrics(),
            "optimizer_health": self.optimizer.get_system_health(),
            "mode_costs": {
                mode.value: self.normalizer.calculate_mode_cost(mode)
                for mode in [OptimizationMode.LITE, OptimizationMode.BALANCED, OptimizationMode.QUALITY]
            },
            "mcp_coordinators": list(self.facade.mcp_coordinators.keys()),
            "circuit_breakers": {
                name: cb.get_state()
                for name, cb in self.facade.circuit_breakers.items()
            }
        }

        return status


async def main():
    """Main demonstration"""

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create and initialize system
    system = IntegratedSwarmSystem()
    await system.initialize()

    # Demonstrate mode normalization
    await system.demonstrate_mode_normalization()

    # Example: Execute a coding task with automatic mode selection
    print("\n=== Example: Coding Task ===")
    result = await system.execute_with_mode_selection(
        task="Implement a binary search algorithm in Python",
        urgency="normal"
    )
    print(f"Result: {result}")

    # Example: Execute with MCP coordination
    print("\n=== Example: MCP Coordinated Task ===")
    result = await system.execute_mcp_coordinated(
        task="Analyze and refactor the authentication module",
        assistants=["roo", "cline"],
        mode="quality"
    )
    print(f"Result: {result}")

    # Get system status
    print("\n=== System Status ===")
    status = await system.get_system_status()
    print(f"Health: {status['optimizer_health']:.2f}")
    print(f"Mode Costs: {status['mode_costs']}")
    print(f"Circuit Breakers: {status['circuit_breakers']}")


if __name__ == "__main__":
    asyncio.run(main())
