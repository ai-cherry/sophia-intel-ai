"""
MCP-Swarm Bridge: Connects AI Agent Swarms to MCP Coordination Protocol
Enables 6-way AI coordination: Claude + Roo + Cline + Swarms
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union

import websockets
from websockets.exceptions import ConnectionClosed

from app.core.ai_logger import logger
from app.observability.prometheus_metrics import (
    swarm_active_participants,
    swarm_coordination_latency_ms,
    swarm_mcp_messages_total,
)
from app.swarms.communication.message_bus import MessageBus
from app.swarms.core.swarm_base import SwarmBase

logger = logging.getLogger(__name__)

class MCPParticipant(Enum):
    """All participants in the MCP coordination network"""
    CLAUDE = "claude"           # Terminal coordinator
    ROO = "roo"                # Cursor frontend
    CLINE = "cline"            # VS Code backend
    SWARM_CODING = "swarm_coding"
    SWARM_DEBATE = "swarm_debate"
    SWARM_MEMORY = "swarm_memory"
    SWARM_CONSENSUS = "swarm_consensus"
    BROADCAST = "broadcast"     # Send to all

@dataclass
class MCPMessage:
    """Unified message format for MCP-Swarm communication"""
    source: str              # Who sent the message
    target: str              # Who should receive it
    type: str               # Message type
    content: Any            # Message payload
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    correlation_id: Optional[str] = None

    def to_json(self) -> str:
        """Convert message to JSON for transmission"""
        return json.dumps({
            "source": self.source,
            "target": self.target,
            "type": self.type,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id
        })

    @classmethod
    def from_json(cls, data: str) -> 'MCPMessage':
        """Create message from JSON string"""
        parsed = json.loads(data)
        return cls(**parsed)

class SwarmMCPBridge:
    """Bridge between Swarm systems and MCP protocol for 6-way coordination"""

    def __init__(self, mcp_url: str = "http://localhost:8000"):
        self.mcp_url = mcp_url
        self.ws_url = "ws://localhost:8000/ws/mcp"
        self.active_swarms: dict[str, SwarmBase] = {}
        self.message_bus = MessageBus()
        self.websocket: websockets.Optional[WebSocketClientProtocol] = None
        self.participants: set[str] = set()
        self.coordination_tasks: dict[str, asyncio.Task] = {}
        self._running = False

    async def initialize(self):
        """Initialize the MCP bridge and connect to server"""
        try:
            # Connect to MCP WebSocket
            self.websocket = await websockets.connect(self.ws_url)
            self._running = True

            # Start listening for messages
            asyncio.create_task(self._listen_for_mcp_messages())

            # Announce bridge is online
            announcement = MCPMessage(
                source="swarm_mcp_bridge",
                target=MCPParticipant.BROADCAST.value,
                type="bridge_online",
                content={
                    "message": "Swarm MCP Bridge initialized",
                    "capabilities": ["swarm_coordination", "task_distribution", "consensus_building"],
                    "timestamp": datetime.now().isoformat()
                }
            )
            await self._send_to_mcp(announcement)

            logger.info("SwarmMCPBridge initialized and connected to MCP server")

        except Exception as e:
            logger.error(f"Failed to initialize MCP bridge: {str(e)}")
            raise

    async def register_swarm(self, swarm_id: str, swarm: SwarmBase) -> bool:
        """Register a swarm with MCP coordination network"""
        try:
            self.active_swarms[swarm_id] = swarm

            # Create participant ID
            participant_id = f"swarm_{swarm_id}"
            self.participants.add(participant_id)

            # Announce swarm to MCP network
            announcement = MCPMessage(
                source=participant_id,
                target=MCPParticipant.BROADCAST.value,
                type="swarm_registration",
                content={
                    "swarm_id": swarm_id,
                    "swarm_type": swarm.swarm_type.value if hasattr(swarm, 'swarm_type') else "unknown",
                    "capabilities": swarm.get_capabilities() if hasattr(swarm, 'get_capabilities') else [],
                    "agent_count": len(swarm.agents) if hasattr(swarm, 'agents') else 0,
                    "status": "online"
                },
                metadata={
                    "registration_time": datetime.now().isoformat()
                }
            )

            await self._send_to_mcp(announcement)

            # Update metrics
            swarm_active_participants.set(len(self.participants))

            logger.info(f"Registered swarm '{swarm_id}' with MCP network")
            return True

        except Exception as e:
            logger.error(f"Failed to register swarm '{swarm_id}': {str(e)}")
            return False

    async def coordinate_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Coordinate task execution across all 6 AI participants.
        This is where the magic happens - true 6-way coordination!
        """
        start_time = datetime.now()
        task_id = task.get("id", f"task_{start_time.timestamp()}")

        try:
            # Determine required participants based on capabilities
            required_capabilities = task.get("capabilities", [])
            participants = await self._determine_participants(required_capabilities)

            logger.info(f"Coordinating task {task_id} with participants: {participants}")

            # Phase 1: Planning with Claude
            planning_msg = MCPMessage(
                source="swarm_coordinator",
                target=MCPParticipant.CLAUDE.value,
                type="planning_request",
                content={
                    "task": task,
                    "participants": participants
                },
                correlation_id=task_id
            )
            await self._send_to_mcp(planning_msg)

            # Phase 2: Parallel execution
            execution_tasks = []

            # Swarm tasks
            for swarm_id in participants.get("swarms", []):
                if swarm_id in self.active_swarms:
                    swarm = self.active_swarms[swarm_id]
                    execution_tasks.append(
                        self._execute_swarm_task(swarm_id, swarm, task)
                    )

            # Tool tasks (Cline, Roo)
            for tool in participants.get("tools", []):
                tool_msg = MCPMessage(
                    source="swarm_coordinator",
                    target=tool,
                    type="task_execution",
                    content=task,
                    correlation_id=task_id
                )
                execution_tasks.append(self._send_to_mcp(tool_msg))

            # Execute all tasks in parallel
            if execution_tasks:
                results = await asyncio.gather(*execution_tasks, return_exceptions=True)
            else:
                results = []

            # Phase 3: Consolidation and validation
            consolidated_results = {
                "task_id": task_id,
                "participants": participants,
                "results": {},
                "errors": [],
                "duration_ms": (datetime.now() - start_time).total_seconds() * 1000
            }

            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    consolidated_results["errors"].append(str(result))
                else:
                    if i < len(participants.get("swarms", [])):
                        swarm_id = participants["swarms"][i]
                        consolidated_results["results"][f"swarm_{swarm_id}"] = result
                    else:
                        tool_idx = i - len(participants.get("swarms", []))
                        tool = participants["tools"][tool_idx]
                        consolidated_results["results"][tool] = result

            # Phase 4: Quality check with debate swarm
            if "swarm_debate" in self.active_swarms:
                quality_check = await self._quality_check_with_debate(consolidated_results)
                consolidated_results["quality_assessment"] = quality_check

            # Update metrics
            swarm_coordination_latency_ms.observe(consolidated_results["duration_ms"])
            swarm_mcp_messages_total.labels(type="coordination_complete").inc()

            logger.info(f"Task {task_id} completed in {consolidated_results['duration_ms']}ms")

            return consolidated_results

        except Exception as e:
            logger.error(f"Task coordination failed for {task_id}: {str(e)}")
            return {
                "task_id": task_id,
                "error": str(e),
                "success": False
            }

    async def _determine_participants(self, capabilities: list[str]) -> dict[str, list[str]]:
        """Determine which swarms and tools should participate"""
        participants = {
            "swarms": [],
            "tools": []
        }

        # Map capabilities to swarms
        capability_swarm_map = {
            "coding": "coding",
            "code_generation": "coding",
            "review": "debate",
            "consensus": "consensus",
            "memory": "memory",
            "knowledge": "memory"
        }

        # Map capabilities to tools
        capability_tool_map = {
            "frontend": MCPParticipant.ROO.value,
            "ui": MCPParticipant.ROO.value,
            "backend": MCPParticipant.CLINE.value,
            "api": MCPParticipant.CLINE.value,
            "coordination": MCPParticipant.CLAUDE.value,
            "quality": MCPParticipant.CLAUDE.value
        }

        # Select swarms
        for capability in capabilities:
            if capability in capability_swarm_map:
                swarm_id = capability_swarm_map[capability]
                if swarm_id in self.active_swarms and swarm_id not in participants["swarms"]:
                    participants["swarms"].append(swarm_id)

        # Select tools
        for capability in capabilities:
            if capability in capability_tool_map:
                tool = capability_tool_map[capability]
                if tool not in participants["tools"]:
                    participants["tools"].append(tool)

        # Always include Claude for coordination if multi-participant
        if len(participants["swarms"]) + len(participants["tools"]) > 2:
            if MCPParticipant.CLAUDE.value not in participants["tools"]:
                participants["tools"].append(MCPParticipant.CLAUDE.value)

        return participants

    async def _execute_swarm_task(self, swarm_id: str, swarm: SwarmBase, task: dict[str, Any]) -> dict[str, Any]:
        """Execute task with specific swarm"""
        try:
            # Convert task to swarm-compatible format
            swarm_task = {
                "prompt": task.get("description", ""),
                "context": task.get("context", {}),
                "requirements": task.get("requirements", {})
            }

            # Execute with swarm
            if hasattr(swarm, 'execute'):
                result = await swarm.execute(swarm_task)
            elif hasattr(swarm, 'process'):
                result = await swarm.process(swarm_task)
            else:
                result = {"error": f"Swarm {swarm_id} has no execution method"}

            # Announce completion to MCP
            completion_msg = MCPMessage(
                source=f"swarm_{swarm_id}",
                target=MCPParticipant.BROADCAST.value,
                type="task_complete",
                content={
                    "swarm_id": swarm_id,
                    "task_id": task.get("id"),
                    "success": result.get("success", True),
                    "summary": result.get("summary", "Task completed")
                }
            )
            await self._send_to_mcp(completion_msg)

            return result

        except Exception as e:
            logger.error(f"Swarm {swarm_id} task execution failed: {str(e)}")
            return {"error": str(e), "success": False}

    async def _quality_check_with_debate(self, results: dict[str, Any]) -> dict[str, Any]:
        """Use debate swarm to quality check results"""
        if "debate" not in self.active_swarms:
            return {"skipped": "Debate swarm not available"}

        debate_swarm = self.active_swarms["debate"]

        # Create debate topic from results
        debate_topic = {
            "question": "Are these results production-ready?",
            "evidence": results["results"],
            "criteria": [
                "Code quality",
                "Security",
                "Performance",
                "Completeness"
            ]
        }

        # Conduct quality debate
        if hasattr(debate_swarm, 'conduct_debate'):
            assessment = await debate_swarm.conduct_debate(debate_topic)
        else:
            assessment = {"decision": "Unable to assess"}

        return assessment

    async def _send_to_mcp(self, message: MCPMessage):
        """Send message to MCP server via WebSocket"""
        if self.websocket:
            try:
                await self.websocket.send(message.to_json())
                swarm_mcp_messages_total.labels(type="sent").inc()
            except Exception as e:
                logger.error(f"Failed to send MCP message: {str(e)}")

    async def _listen_for_mcp_messages(self):
        """Listen for incoming MCP messages"""
        while self._running and self.websocket:
            try:
                message_data = await self.websocket.recv()
                message = MCPMessage.from_json(message_data)

                # Process message based on target
                if message.target in ["broadcast", "swarm_coordinator"]:
                    await self._handle_mcp_message(message)

                # Route to specific swarm if targeted
                if message.target.startswith("swarm_"):
                    swarm_id = message.target.replace("swarm_", "")
                    if swarm_id in self.active_swarms:
                        await self._route_to_swarm(swarm_id, message)

                swarm_mcp_messages_total.labels(type="received").inc()

            except ConnectionClosed:
                logger.warning("MCP WebSocket connection closed")
                self._running = False
                break
            except Exception as e:
                logger.error(f"Error processing MCP message: {str(e)}")

    async def _handle_mcp_message(self, message: MCPMessage):
        """Handle incoming MCP message"""
        logger.debug(f"Received MCP message: {message.type} from {message.source}")

        # Handle different message types
        if message.type == "coordination_request":
            await self.coordinate_task(message.content)
        elif message.type == "status_request":
            await self._send_status_update()
        elif message.type == "participant_announcement":
            self.participants.add(message.source)
            swarm_active_participants.set(len(self.participants))

    async def _route_to_swarm(self, swarm_id: str, message: MCPMessage):
        """Route message to specific swarm"""
        if swarm_id in self.active_swarms:
            swarm = self.active_swarms[swarm_id]
            # Process message with swarm
            # Implementation depends on swarm interface
            logger.debug(f"Routed message to swarm {swarm_id}")

    async def _send_status_update(self):
        """Send status update to MCP network"""
        status = {
            "bridge_status": "online",
            "active_swarms": list(self.active_swarms.keys()),
            "participant_count": len(self.participants),
            "coordination_tasks": len(self.coordination_tasks)
        }

        status_msg = MCPMessage(
            source="swarm_mcp_bridge",
            target=MCPParticipant.BROADCAST.value,
            type="status_update",
            content=status
        )

        await self._send_to_mcp(status_msg)

    async def shutdown(self):
        """Gracefully shutdown the bridge"""
        self._running = False

        # Announce shutdown
        shutdown_msg = MCPMessage(
            source="swarm_mcp_bridge",
            target=MCPParticipant.BROADCAST.value,
            type="bridge_offline",
            content={"message": "Swarm MCP Bridge shutting down"}
        )
        await self._send_to_mcp(shutdown_msg)

        # Close WebSocket
        if self.websocket:
            await self.websocket.close()

        logger.info("SwarmMCPBridge shutdown complete")


# Example usage for demonstration
async def demonstrate_6_way_coordination():
    """Demonstrate 6-way AI coordination with swarms"""

    # Initialize bridge
    bridge = SwarmMCPBridge()
    await bridge.initialize()

    # Import and register swarms
    from app.swarms.debate.multi_agent_debate import MultiAgentDebateSystem
    from app.swarms.improved_swarm import ImprovedAgentSwarm
    from app.swarms.memory_enhanced_swarm import MemoryEnhancedSwarm

    # Use existing swarm implementations
    coding_swarm = ImprovedAgentSwarm()  # Can handle coding tasks
    debate_swarm = MultiAgentDebateSystem()
    memory_swarm = MemoryEnhancedSwarm()

    await bridge.register_swarm("coding", coding_swarm)
    await bridge.register_swarm("debate", debate_swarm)
    await bridge.register_swarm("memory", memory_swarm)

    # Create complex multi-capability task
    task = {
        "id": "demo_001",
        "description": "Create a secure payment processing system",
        "capabilities": [
            "coding",          # Coding swarm generates code
            "backend",         # Cline implements backend
            "frontend",        # Roo creates UI
            "review",          # Debate swarm reviews
            "memory",          # Memory swarm applies patterns
            "coordination"     # Claude coordinates everything
        ],
        "requirements": {
            "security": "PCI DSS compliant",
            "performance": "<100ms latency",
            "ui": "React with Material-UI",
            "testing": "90% coverage required"
        }
    }

    # Execute 6-way coordination
    result = await bridge.coordinate_task(task)

    logger.info("6-Way Coordination Result:")
    logger.info(f"Participants: {result.get('participants')}")
    logger.info(f"Duration: {result.get('duration_ms')}ms")
    logger.info(f"Success: {not result.get('errors')}")

    return result

if __name__ == "__main__":
    # Run demonstration
    asyncio.run(demonstrate_6_way_coordination())
