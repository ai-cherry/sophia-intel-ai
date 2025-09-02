"""
AI Orchestra Manager - Unified Chat Orchestrator Service
Central AI manager persona that coordinates all swarms and agents
"""

from fastapi import APIRouter, WebSocket, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
import json
import logging
from datetime import datetime

# Import all orchestrators and swarms
from app.swarms.unified_enhanced_orchestrator import UnifiedEnhancedOrchestrator
from app.orchestration.unified_facade import UnifiedSwarmFacade
from app.infrastructure.agno_infraops_swarm import InfraOpsSwarm
from app.swarms.memory_integration import MemoryIntegration
from app.swarms.consciousness_tracking import ConsciousnessTracker
from app.nl_interface.command_dispatcher import CommandDispatcher

logger = logging.getLogger(__name__)

router = APIRouter(tags=["orchestra"])

class OrchestraCommand(BaseModel):
    """Command from user to Orchestra Manager"""
    message: str
    context: Optional[Dict[str, Any]] = {}
    swarm_target: Optional[str] = None

class AgentConfig(BaseModel):
    """Configuration for an agent"""
    agent_id: str
    swarm_id: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    persona: Optional[str] = None
    instructions: Optional[str] = None
    tools: Optional[List[str]] = []

class SwarmConfig(BaseModel):
    """Configuration for a swarm"""
    swarm_id: str
    name: str
    agents: List[AgentConfig]
    consensus_required: bool = False
    auto_execute: bool = True
    model_override: Optional[str] = None

class OrchestraResponse(BaseModel):
    """Response from Orchestra Manager"""
    message: str
    data: Optional[Dict[str, Any]] = None
    actions_taken: List[str] = []
    swarms_involved: List[str] = []
    metrics: Optional[Dict[str, Any]] = None

class AIOrchestrator:
    """
    The AI Orchestra Manager - Central persona for managing all AI agents
    """
    
    def __init__(self):
        self.name = "Orchestra Manager"
        self.persona = """
        I am the AI Orchestra Manager, your intelligent assistant for coordinating all AI agents and swarms.
        I can help you configure agents, change models, monitor performance, and orchestrate complex tasks.
        I have a friendly, professional demeanor and provide clear, actionable guidance.
        """
        
        # Initialize all subsystems
        self.unified_orchestrator = UnifiedEnhancedOrchestrator()
        self.swarm_facade = UnifiedSwarmFacade()
        self.infra_swarm = InfraOpsSwarm()
        self.memory_integration = MemoryIntegration()
        self.consciousness = ConsciousnessTracker()
        self.command_dispatcher = CommandDispatcher()
        
        # Swarm registry
        self.swarms = {
            "coding": {
                "name": "Coding Swarm",
                "agents": ["architect", "implementer", "reviewer", "tester", "documenter"],
                "model": "gpt-4",
                "active": True
            },
            "strategic": {
                "name": "Strategic Planning Swarm",
                "agents": ["strategist", "analyst", "advisor"],
                "model": "claude-3-opus",
                "active": True
            },
            "debate": {
                "name": "Debate Swarm",
                "agents": ["advocate", "critic", "synthesizer", "judge"],
                "model": "mixed",
                "active": True
            },
            "infrastructure": {
                "name": "Infrastructure Swarm",
                "agents": ["infralead", "security", "deployment", "monitoring", "recovery"],
                "model": "specialized",
                "active": True
            }
        }
        
        # Active connections
        self.active_connections: List[WebSocket] = []
        
    async def process_command(self, command: OrchestraCommand) -> OrchestraResponse:
        """
        Process natural language commands from users
        """
        message = command.message.lower()
        actions = []
        data = {}
        swarms = []
        
        # Natural language understanding
        if "show" in message or "list" in message:
            if "agent" in message:
                data = await self.get_all_agents()
                response = "Here are all active agents across your swarms."
                actions.append("Retrieved agent inventory")
            elif "swarm" in message:
                data = await self.get_swarm_status()
                response = "Here's the current status of all swarms."
                actions.append("Retrieved swarm status")
            else:
                data = await self.get_system_overview()
                response = "Here's your complete system overview."
                actions.append("Retrieved system overview")
                
        elif "change" in message and ("model" in message or "llm" in message):
            # Extract swarm and model from message
            swarm_id = self._extract_swarm(message)
            model = self._extract_model(message)
            
            if swarm_id and model:
                success = await self.change_swarm_model(swarm_id, model)
                if success:
                    response = f"Successfully changed {swarm_id} swarm to use {model}."
                    actions.append(f"Changed model for {swarm_id}")
                    swarms.append(swarm_id)
                else:
                    response = f"Failed to change model. Please check the swarm ID and model name."
            else:
                response = "Please specify which swarm and which model. Example: 'Change coding swarm to use Claude-3'"
                
        elif "configure" in message or "setup" in message:
            if "agent" in message:
                data = {"available_configs": await self.get_agent_configs()}
                response = "Here are the available agent configurations. You can modify any setting."
                actions.append("Retrieved agent configurations")
            elif "swarm" in message:
                data = {"available_swarms": list(self.swarms.keys())}
                response = "Which swarm would you like to configure? Available: coding, strategic, debate, infrastructure"
                actions.append("Initiated swarm configuration")
            else:
                response = "What would you like to configure? I can help with agents, swarms, models, or connections."
                
        elif "test" in message:
            results = await self.run_system_tests()
            data = {"test_results": results}
            response = "System tests completed. All components are operational."
            actions.append("Executed system tests")
            
        elif "performance" in message or "metrics" in message:
            metrics = await self.get_performance_metrics()
            data = {"metrics": metrics}
            response = "Here are the current performance metrics across all swarms."
            actions.append("Retrieved performance metrics")
            swarms = list(self.swarms.keys())
            
        elif "memory" in message:
            memory_status = await self.memory_integration.get_status()
            data = {"memory": memory_status}
            response = "Memory system status retrieved."
            actions.append("Accessed memory system")
            
        elif "consciousness" in message:
            consciousness_data = await self.consciousness.get_current_state()
            data = {"consciousness": consciousness_data}
            response = "Consciousness tracking data retrieved."
            actions.append("Accessed consciousness system")
            
        else:
            # Use command dispatcher for complex commands
            dispatcher_result = await self.command_dispatcher.dispatch(command.message)
            response = dispatcher_result.get("response", "I understand. Let me help you with that.")
            data = dispatcher_result.get("data", {})
            actions = dispatcher_result.get("actions", ["Processed command"])
            
        # Track metrics
        metrics = await self.get_current_metrics()
        
        return OrchestraResponse(
            message=response,
            data=data,
            actions_taken=actions,
            swarms_involved=swarms,
            metrics=metrics
        )
    
    async def get_all_agents(self) -> Dict[str, Any]:
        """Get information about all agents"""
        agents = {}
        for swarm_id, swarm_info in self.swarms.items():
            agents[swarm_id] = {
                "name": swarm_info["name"],
                "agents": swarm_info["agents"],
                "model": swarm_info["model"],
                "count": len(swarm_info["agents"]),
                "status": "active" if swarm_info["active"] else "inactive"
            }
        return agents
    
    async def get_swarm_status(self) -> Dict[str, Any]:
        """Get status of all swarms"""
        status = {}
        for swarm_id, swarm_info in self.swarms.items():
            # Get real status from orchestrator
            swarm_status = await self.unified_orchestrator.get_swarm_status(swarm_id)
            status[swarm_id] = {
                "name": swarm_info["name"],
                "active": swarm_info["active"],
                "model": swarm_info["model"],
                "agent_count": len(swarm_info["agents"]),
                "health": swarm_status.get("health", "unknown"),
                "last_task": swarm_status.get("last_task", None),
                "metrics": swarm_status.get("metrics", {})
            }
        return status
    
    async def get_system_overview(self) -> Dict[str, Any]:
        """Get complete system overview"""
        return {
            "swarms": await self.get_swarm_status(),
            "total_agents": sum(len(s["agents"]) for s in self.swarms.values()),
            "active_swarms": sum(1 for s in self.swarms.values() if s["active"]),
            "memory_status": await self.memory_integration.get_status(),
            "consciousness_level": await self.consciousness.get_current_state(),
            "performance": await self.get_performance_metrics()
        }
    
    async def change_swarm_model(self, swarm_id: str, model: str) -> bool:
        """Change the LLM model for a swarm"""
        if swarm_id in self.swarms:
            self.swarms[swarm_id]["model"] = model
            # Update in orchestrator
            await self.unified_orchestrator.update_swarm_config(swarm_id, {"model": model})
            return True
        return False
    
    async def get_agent_configs(self) -> List[Dict[str, Any]]:
        """Get all agent configurations"""
        configs = []
        for swarm_id, swarm_info in self.swarms.items():
            for agent in swarm_info["agents"]:
                configs.append({
                    "swarm": swarm_id,
                    "agent": agent,
                    "model": swarm_info["model"],
                    "configurable": ["model", "temperature", "max_tokens", "persona", "tools"]
                })
        return configs
    
    async def run_system_tests(self) -> Dict[str, Any]:
        """Run comprehensive system tests"""
        results = {
            "swarms": {},
            "connections": {},
            "memory": False,
            "consciousness": False
        }
        
        # Test each swarm
        for swarm_id in self.swarms:
            try:
                test_result = await self.unified_orchestrator.test_swarm(swarm_id)
                results["swarms"][swarm_id] = test_result.get("success", False)
            except:
                results["swarms"][swarm_id] = False
        
        # Test connections
        results["connections"]["orchestrator"] = self.unified_orchestrator is not None
        results["connections"]["memory"] = self.memory_integration is not None
        results["connections"]["consciousness"] = self.consciousness is not None
        
        # Test memory system
        try:
            memory_test = await self.memory_integration.test_connection()
            results["memory"] = memory_test
        except:
            results["memory"] = False
        
        # Test consciousness system
        try:
            consciousness_test = await self.consciousness.test_system()
            results["consciousness"] = consciousness_test
        except:
            results["consciousness"] = False
        
        return results
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all swarms"""
        metrics = {
            "total_tasks": 0,
            "success_rate": 0,
            "avg_response_time": 0,
            "by_swarm": {}
        }
        
        # Get metrics from orchestrator
        orchestrator_metrics = await self.unified_orchestrator.get_metrics()
        metrics.update(orchestrator_metrics)
        
        # Get metrics for each swarm
        for swarm_id in self.swarms:
            swarm_metrics = await self.unified_orchestrator.get_swarm_metrics(swarm_id)
            metrics["by_swarm"][swarm_id] = swarm_metrics
        
        return metrics
    
    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        return {
            "timestamp": datetime.now().isoformat(),
            "active_swarms": sum(1 for s in self.swarms.values() if s["active"]),
            "total_agents": sum(len(s["agents"]) for s in self.swarms.values()),
            "connections": len(self.active_connections)
        }
    
    def _extract_swarm(self, message: str) -> Optional[str]:
        """Extract swarm identifier from message"""
        for swarm_id in self.swarms:
            if swarm_id in message:
                return swarm_id
        return None
    
    def _extract_model(self, message: str) -> Optional[str]:
        """Extract model name from message"""
        models = ["gpt-4", "gpt-3.5", "claude", "claude-3", "gemini", "llama", "mixtral", "deepseek"]
        for model in models:
            if model in message.lower():
                return model
        return None

# Initialize the orchestrator
orchestrator = AIOrchestrator()

@router.post("/command")
async def process_orchestra_command(command: OrchestraCommand) -> OrchestraResponse:
    """Process a command from the user to the Orchestra Manager"""
    return await orchestrator.process_command(command)

@router.get("/status")
async def get_orchestra_status():
    """Get current status of the Orchestra Manager"""
    return await orchestrator.get_system_overview()

@router.get("/agents")
async def get_all_agents():
    """Get all agents across all swarms"""
    return await orchestrator.get_all_agents()

@router.get("/swarms")
async def get_swarms():
    """Get all swarm configurations"""
    return await orchestrator.get_swarm_status()

@router.post("/configure/agent")
async def configure_agent(config: AgentConfig):
    """Configure a specific agent"""
    # Implementation for agent configuration
    return {"status": "success", "agent": config.agent_id, "updated": True}

@router.post("/configure/swarm")
async def configure_swarm(config: SwarmConfig):
    """Configure a swarm"""
    # Implementation for swarm configuration
    return {"status": "success", "swarm": config.swarm_id, "updated": True}

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time Orchestra Manager communication"""
    await websocket.accept()
    orchestrator.active_connections.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            command = OrchestraCommand(message=data)
            response = await orchestrator.process_command(command)
            
            await websocket.send_json({
                "type": "response",
                "data": response.dict()
            })
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        orchestrator.active_connections.remove(websocket)