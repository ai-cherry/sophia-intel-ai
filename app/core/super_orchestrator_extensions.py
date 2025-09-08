"""
SuperOrchestrator Extensions - Methods for complete AI system control
These methods should be added to SuperOrchestrator class
"""

import asyncio
import json
from datetime import datetime
from typing import Any

from app.core.orchestrator_enhancements import (
    RegisteredSystem,
    SystemStatus,
    SystemType,
)


class SuperOrchestratorExtensions:
    """Extension methods for SuperOrchestrator - add these to the main class"""

    def _register_self(self):
        """Register the SuperOrchestrator itself in the registry"""
        orchestrator_system = RegisteredSystem(
            id="super_orchestrator_master",
            name="SuperOrchestrator",
            type=SystemType.SERVICE,
            status=SystemStatus.ACTIVE,
            capabilities=[
                "orchestration",
                "monitoring",
                "natural_language",
                "ai_optimization",
                "self_healing",
                "micro_swarm_control",
                "universal_registry",
                "real_time_updates",
            ],
            metadata={"version": "2.0", "role": "master_controller"},
        )
        asyncio.create_task(self.registry.register(orchestrator_system))

    def _load_swarm_configs(self) -> dict[str, Any]:
        """Load micro-swarm configurations"""
        return {
            "code_embedding": {
                "agents": ["parser", "analyzer", "embedder"],
                "capabilities": ["code_analysis", "ast_parsing", "embedding"],
                "max_parallel": 5,
            },
            "meta_tagging": {
                "agents": ["complexity", "quality", "debt", "tagger"],
                "capabilities": ["quality_check", "tech_debt", "tagging"],
                "max_parallel": 4,
            },
            "planning": {
                "agents": ["architect", "decomposer", "estimator"],
                "capabilities": ["architecture", "task_breakdown", "estimation"],
                "max_parallel": 3,
            },
            "code_generation": {
                "agents": ["generator", "reviewer", "tester", "documenter"],
                "capabilities": ["code_gen", "review", "testing", "docs"],
                "max_parallel": 4,
            },
            "debugging": {
                "agents": ["static_analyzer", "test_runner", "profiler", "security"],
                "capabilities": ["static_analysis", "testing", "profiling", "security"],
                "max_parallel": 5,
            },
        }

    async def register_micro_swarm(self, swarm_type: str, swarm_instance: Any) -> str:
        """
        Register a micro-swarm with full tracking.
        This gives us complete visibility into micro-swarms.
        """
        swarm_id = f"micro_swarm_{swarm_type}_{datetime.now().timestamp()}"

        # Store the swarm instance
        self.micro_swarms[swarm_id] = swarm_instance

        # Register in universal registry
        swarm_system = RegisteredSystem(
            id=swarm_id,
            name=f"MicroSwarm-{swarm_type}",
            type=SystemType.MICRO_SWARM,
            status=SystemStatus.IDLE,
            capabilities=self.swarm_configs.get(swarm_type, {}).get("capabilities", []),
            config=self.swarm_configs.get(swarm_type, {}),
            metadata={
                "swarm_type": swarm_type,
                "created_at": datetime.now().isoformat(),
            },
        )

        await self.registry.register(swarm_system)

        # Register individual agents within the swarm
        agents = self.swarm_configs.get(swarm_type, {}).get("agents", [])
        for agent_name in agents:
            agent_id = f"{swarm_id}_agent_{agent_name}"
            agent_system = RegisteredSystem(
                id=agent_id,
                name=f"{swarm_type}-{agent_name}",
                type=SystemType.AGENT,
                status=SystemStatus.IDLE,
                capabilities=[agent_name],
                metadata={"parent_swarm": swarm_id, "role": agent_name},
            )
            agent_system.connections.add(swarm_id)
            await self.registry.register(agent_system)

        # Log registration
        from app.core.ai_logger import logger

        logger.info(
            "Registered micro-swarm",
            {"swarm_id": swarm_id, "type": swarm_type, "agent_count": len(agents)},
        )

        return swarm_id

    async def process_natural_language(
        self, command: str, context: dict = None
    ) -> dict:
        """
        Process natural language commands for complete system control.
        This is the main interface for natural language control.
        """
        # Add context to help with interpretation
        enhanced_command = command
        if context:
            enhanced_command = f"{command} [Context: {json.dumps(context)}]"

        # Process through NL controller
        result = await self.nl_controller.process_command(enhanced_command)

        # Execute any required actions based on result
        if result.get("success") and "system_id" in result:
            # Update UI with changes
            await self._broadcast_update(
                {
                    "type": "command_executed",
                    "command": command,
                    "result": result,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        return result

    async def spawn_micro_swarm(self, swarm_type: str, task: dict = None) -> dict:
        """
        Spawn a micro-swarm with full visibility and control.
        Integrates with the micro-swarm plan.
        """
        if swarm_type not in self.swarm_configs:
            return {"success": False, "error": f"Unknown swarm type: {swarm_type}"}

        # Import the appropriate swarm implementation
        swarm_instance = None

        if swarm_type == "code_embedding":
            from app.swarms.micro.code_embedding import CodeEmbeddingSwarm

            swarm_instance = CodeEmbeddingSwarm()
        elif swarm_type == "meta_tagging":
            from app.swarms.micro.meta_tagging import MetaTaggingSwarm

            swarm_instance = MetaTaggingSwarm()
        elif swarm_type == "planning":
            from app.swarms.micro.planning import PlanningSwarm

            swarm_instance = PlanningSwarm()
        elif swarm_type == "code_generation":
            from app.swarms.micro.code_generation import CodeGenerationSwarm

            swarm_instance = CodeGenerationSwarm()
        elif swarm_type == "debugging":
            from app.swarms.micro.debugging import DebuggingSwarm

            swarm_instance = DebuggingSwarm()

        if not swarm_instance:
            # Create a generic swarm if specific implementation doesn't exist
            swarm_instance = {"type": swarm_type, "status": "generic"}

        # Register the swarm
        swarm_id = await self.register_micro_swarm(swarm_type, swarm_instance)

        # Update status to active
        await self.registry.update_status(swarm_id, SystemStatus.ACTIVE)

        # If task provided, execute it
        result = {"swarm_id": swarm_id, "status": "spawned"}
        if task:
            result["task_result"] = await self.execute_micro_swarm_task(swarm_id, task)

        return result

    async def execute_micro_swarm_task(self, swarm_id: str, task: dict) -> dict:
        """Execute a task with a specific micro-swarm"""
        if swarm_id not in self.micro_swarms:
            return {"success": False, "error": "Swarm not found"}

        swarm = self.micro_swarms[swarm_id]

        # Update status
        await self.registry.update_status(swarm_id, SystemStatus.PROCESSING)

        try:
            # Execute based on swarm capabilities
            if hasattr(swarm, "execute"):
                result = await swarm.execute(task)
            elif hasattr(swarm, "process"):
                result = await swarm.process(task)
            else:
                # Generic execution
                result = {"status": "executed", "task": task}

            # Update metrics
            system = self.registry.systems.get(swarm_id)
            if system:
                system.metrics["last_execution"] = datetime.now().isoformat()
                system.metrics["total_executions"] = (
                    system.metrics.get("total_executions", 0) + 1
                )

            # Update status back to active
            await self.registry.update_status(swarm_id, SystemStatus.ACTIVE)

            return {"success": True, "result": result}

        except Exception as e:
            # Update to error status
            await self.registry.update_status(swarm_id, SystemStatus.ERROR)
            system = self.registry.systems.get(swarm_id)
            if system:
                system.error_count += 1

            return {"success": False, "error": str(e)}

    async def get_system_overview(self) -> dict:
        """
        Get complete overview of all AI systems.
        This provides the visibility you need.
        """
        overview = {
            "orchestrator": {
                "status": "operational",
                "uptime": datetime.now().isoformat(),
                "version": "2.0",
            },
            "registry": self.registry.get_health_report(),
            "micro_swarms": {
                "total": len(self.micro_swarms),
                "active": len(
                    [
                        s
                        for s in self.registry.get_by_type(SystemType.MICRO_SWARM)
                        if s.status == SystemStatus.ACTIVE
                    ]
                ),
                "types": list(self.swarm_configs.keys()),
            },
            "agents": {
                "total": len(self.registry.get_by_type(SystemType.AGENT)),
                "active": len(
                    [
                        s
                        for s in self.registry.get_by_type(SystemType.AGENT)
                        if s.status == SystemStatus.ACTIVE
                    ]
                ),
            },
            "connections": {
                "websockets": len(self.connections),
                "mcp_servers": len(self.registry.get_by_type(SystemType.MCP_SERVER)),
            },
            "capabilities": self._get_all_capabilities(),
        }

        return overview

    def _get_all_capabilities(self) -> list[str]:
        """Get all unique capabilities across all systems"""
        all_capabilities = set()
        for system in self.registry.systems.values():
            all_capabilities.update(system.capabilities)
        return sorted(all_capabilities)

    async def handle_ui_command(self, websocket, command: dict) -> dict:
        """
        Handle commands from the UI.
        This is the main interface for UI control.
        """
        cmd_type = command.get("type")

        if cmd_type == "natural_language":
            # Process natural language command
            return await self.process_natural_language(
                command.get("text", ""), command.get("context", {})
            )

        elif cmd_type == "spawn_swarm":
            # Spawn a micro-swarm
            return await self.spawn_micro_swarm(
                command.get("swarm_type"), command.get("task")
            )

        elif cmd_type == "get_overview":
            # Get system overview
            return await self.get_system_overview()

        elif cmd_type == "execute_task":
            # Execute task on specific system
            system_id = command.get("system_id")
            task = command.get("task")

            if system_id in self.micro_swarms:
                return await self.execute_micro_swarm_task(system_id, task)
            else:
                return {"success": False, "error": "System not found"}

        elif cmd_type == "subscribe_monitoring":
            # Subscribe to real-time monitoring
            self.monitor.subscribe(websocket)
            return {"success": True, "message": "Subscribed to monitoring"}

        else:
            return {"success": False, "error": f"Unknown command type: {cmd_type}"}

    async def _broadcast_system_state(self):
        """Broadcast complete system state to all UI connections"""
        state = {
            "type": "system_state",
            "overview": await self.get_system_overview(),
            "health": self.registry.get_health_report(),
            "active_tasks": self.tasks.get_pending_tasks(),
            "timestamp": datetime.now().isoformat(),
        }

        await self._broadcast_update(state)


# These methods should be added to the SuperOrchestrator class
# They provide complete visibility and control over all AI systems
