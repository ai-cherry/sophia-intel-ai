"""
Agent Factory - Dynamic AI Agent and Swarm Creation System
Integrates with existing AGNO framework and MCP server
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

# Import existing swarm infrastructure
from app.swarms.core.swarm_base import SwarmType, SwarmExecutionMode, SwarmConfig, SwarmMetrics
from app.swarms.agno_teams import SophiaAGNOTeam, AGNOTeamConfig, ExecutionStrategy
from app.swarms.patterns.base import SwarmPattern

logger = logging.getLogger(__name__)

# ==============================================================================
# AGENT FACTORY MODELS
# ==============================================================================

class AgentRole(str, Enum):
    PLANNER = "planner"
    GENERATOR = "generator" 
    CRITIC = "critic"
    JUDGE = "judge"
    RUNNER = "runner"
    ARCHITECT = "architect"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TESTING = "testing"

class AgentDefinition(BaseModel):
    """Configuration for a single agent"""
    name: str
    role: AgentRole
    model: str
    temperature: float = 0.7
    instructions: str
    capabilities: List[str] = []
    constraints: Optional[List[str]] = None
    metadata: Dict[str, Any] = {}

class SwarmBlueprint(BaseModel):
    """Complete specification for creating a swarm"""
    name: str
    description: str = ""
    swarm_type: SwarmType = SwarmType.STANDARD
    execution_mode: SwarmExecutionMode = SwarmExecutionMode.HIERARCHICAL
    agents: List[AgentDefinition]
    pattern: str = "hierarchical"
    memory_enabled: bool = True
    namespace: str = "artemis"
    tags: List[str] = []
    created_by: str = "factory"
    version: str = "1.0"

class SwarmTemplate(BaseModel):
    """Pre-built swarm template"""
    id: str
    name: str
    description: str
    type: SwarmType
    category: str
    agents: List[AgentDefinition]
    pattern: str
    recommended_for: List[str]
    metadata: Dict[str, Any] = {}

class FactoryExecutionResult(BaseModel):
    """Result from factory swarm execution"""
    swarm_id: str
    task: str
    result: Dict[str, Any]
    execution_time: float
    token_usage: Dict[str, int]
    cost_estimate: float
    agents_used: List[str]
    success: bool
    errors: List[str] = []
    metrics: Dict[str, Any] = {}

# ==============================================================================
# AGENT FACTORY CORE CLASS
# ==============================================================================

class AgentFactory:
    """
    Dynamic Agent and Swarm Factory
    Integrates with existing AGNO infrastructure
    """
    
    def __init__(self):
        self.created_swarms: Dict[str, SwarmBlueprint] = {}
        self.execution_history: List[FactoryExecutionResult] = []
        self.templates = self._initialize_templates()
        self.agno_teams: Dict[str, SophiaAGNOTeam] = {}
        
    def _initialize_templates(self) -> Dict[str, SwarmTemplate]:
        """Initialize built-in swarm templates"""
        return {
            "coding": SwarmTemplate(
                id="coding",
                name="Coding Swarm",
                description="Code generation, review, and optimization",
                type=SwarmType.CODING,
                category="development",
                pattern="hierarchical",
                recommended_for=["code_generation", "code_review", "debugging"],
                agents=[
                    AgentDefinition(
                        name="Code Planner",
                        role=AgentRole.PLANNER,
                        model="qwen/qwen3-30b-a3b",
                        temperature=0.3,
                        instructions="Analyze requirements and create implementation plan. Focus on architecture and design patterns.",
                        capabilities=["planning", "architecture", "design_patterns"]
                    ),
                    AgentDefinition(
                        name="Code Generator", 
                        role=AgentRole.GENERATOR,
                        model="x-ai/grok-code-fast-1",
                        temperature=0.7,
                        instructions="Generate clean, efficient code based on the plan. Follow best practices and include error handling.",
                        capabilities=["code_generation", "best_practices", "error_handling"]
                    ),
                    AgentDefinition(
                        name="Code Reviewer",
                        role=AgentRole.CRITIC,
                        model="openai/gpt-5-chat",
                        temperature=0.2,
                        instructions="Review generated code for bugs, security issues, and improvements. Be thorough but constructive.",
                        capabilities=["code_review", "security_analysis", "optimization"]
                    )
                ]
            ),
            
            "debate": SwarmTemplate(
                id="debate",
                name="Debate Swarm",
                description="Adversarial analysis and decision making",
                type=SwarmType.DEBATE,
                category="analysis",
                pattern="debate",
                recommended_for=["decision_making", "analysis", "risk_assessment"],
                agents=[
                    AgentDefinition(
                        name="Advocate",
                        role=AgentRole.GENERATOR,
                        model="anthropic/claude-sonnet-4", 
                        temperature=0.8,
                        instructions="Argue strongly in favor of the proposed solution. Present compelling evidence.",
                        capabilities=["argumentation", "evidence_gathering", "persuasion"]
                    ),
                    AgentDefinition(
                        name="Critic",
                        role=AgentRole.CRITIC,
                        model="openai/gpt-5-chat",
                        temperature=0.8, 
                        instructions="Challenge the proposal with counter-arguments. Identify weaknesses and risks.",
                        capabilities=["critical_analysis", "risk_identification", "counter_arguments"]
                    ),
                    AgentDefinition(
                        name="Judge",
                        role=AgentRole.JUDGE,
                        model="x-ai/grok-4",
                        temperature=0.3,
                        instructions="Evaluate both sides objectively and provide balanced conclusion.",
                        capabilities=["evaluation", "synthesis", "decision_making"]
                    )
                ]
            ),
            
            "consensus": SwarmTemplate(
                id="consensus",
                name="Consensus Building Swarm", 
                description="Multi-perspective analysis and consensus building",
                type=SwarmType.CONSENSUS,
                category="collaboration",
                pattern="consensus",
                recommended_for=["complex_decisions", "multi_stakeholder", "strategic_planning"],
                agents=[
                    AgentDefinition(
                        name="Technical Analyst",
                        role=AgentRole.GENERATOR,
                        model="deepseek/deepseek-chat",
                        temperature=0.5,
                        instructions="Provide analysis from technical perspective. Focus on feasibility and implementation.",
                        capabilities=["technical_analysis", "feasibility_assessment", "implementation_planning"]
                    ),
                    AgentDefinition(
                        name="Business Analyst", 
                        role=AgentRole.GENERATOR,
                        model="qwen/qwen3-30b-a3b",
                        temperature=0.5,
                        instructions="Provide analysis from business perspective. Focus on value and ROI.",
                        capabilities=["business_analysis", "roi_calculation", "market_assessment"]
                    ),
                    AgentDefinition(
                        name="User Experience Analyst",
                        role=AgentRole.GENERATOR,
                        model="anthropic/claude-sonnet-4",
                        temperature=0.5,
                        instructions="Provide analysis from user experience perspective. Focus on usability and adoption.",
                        capabilities=["ux_analysis", "usability_assessment", "adoption_strategies"]
                    ),
                    AgentDefinition(
                        name="Synthesizer",
                        role=AgentRole.JUDGE,
                        model="openai/gpt-5-chat", 
                        temperature=0.3,
                        instructions="Synthesize all perspectives into unified recommendation. Balance competing concerns.",
                        capabilities=["synthesis", "consensus_building", "strategic_recommendations"]
                    )
                ]
            )
        }
    
    async def get_templates(self) -> List[SwarmTemplate]:
        """Get all available swarm templates"""
        return list(self.templates.values())
    
    async def create_swarm_from_blueprint(self, blueprint: SwarmBlueprint) -> str:
        """Create a new swarm from blueprint and return swarm ID"""
        swarm_id = str(uuid4())
        
        # Validate blueprint
        await self._validate_blueprint(blueprint)
        
        # Create AGNO team configuration
        agno_config = AGNOTeamConfig(
            name=blueprint.name,
            strategy=self._map_execution_mode_to_strategy(blueprint.execution_mode),
            max_agents=len(blueprint.agents),
            enable_memory=blueprint.memory_enabled,
            auto_tag=True
        )
        
        # Create AGNO team
        agno_team = SophiaAGNOTeam(agno_config)
        await agno_team.initialize()
        
        # Store references
        self.created_swarms[swarm_id] = blueprint
        self.agno_teams[swarm_id] = agno_team
        
        logger.info(f"Created swarm {swarm_id} from blueprint: {blueprint.name}")
        
        return swarm_id
    
    async def execute_swarm(self, swarm_id: str, task: str, context: Dict[str, Any] = None) -> FactoryExecutionResult:
        """Execute a factory-created swarm"""
        if swarm_id not in self.created_swarms:
            raise HTTPException(status_code=404, detail=f"Swarm {swarm_id} not found")
        
        blueprint = self.created_swarms[swarm_id]
        agno_team = self.agno_teams[swarm_id]
        
        start_time = datetime.now()
        
        try:
            # Execute via AGNO team
            from app.swarms.agno_teams import Task
            agno_task = Task(description=task, metadata=context or {})
            
            result = await agno_team.execute(agno_task)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Create execution result
            exec_result = FactoryExecutionResult(
                swarm_id=swarm_id,
                task=task,
                result=result,
                execution_time=execution_time,
                token_usage=result.get("token_usage", {}),
                cost_estimate=self._estimate_cost(blueprint, result),
                agents_used=[agent.name for agent in blueprint.agents],
                success=result.get("status") == "completed",
                errors=result.get("errors", []),
                metrics=result.get("metrics", {})
            )
            
            # Store execution history
            self.execution_history.append(exec_result)
            
            return exec_result
            
        except Exception as e:
            logger.error(f"Swarm execution failed: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            
            exec_result = FactoryExecutionResult(
                swarm_id=swarm_id,
                task=task,
                result={"error": str(e)},
                execution_time=execution_time,
                token_usage={},
                cost_estimate=0.0,
                agents_used=[],
                success=False,
                errors=[str(e)]
            )
            
            self.execution_history.append(exec_result)
            return exec_result
    
    async def get_swarm_info(self, swarm_id: str) -> Dict[str, Any]:
        """Get information about a created swarm"""
        if swarm_id not in self.created_swarms:
            raise HTTPException(status_code=404, detail=f"Swarm {swarm_id} not found")
        
        blueprint = self.created_swarms[swarm_id]
        
        # Get execution history for this swarm
        executions = [exec_result for exec_result in self.execution_history if exec_result.swarm_id == swarm_id]
        
        return {
            "swarm_id": swarm_id,
            "blueprint": asdict(blueprint),
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "executions": len(executions),
            "success_rate": sum(1 for e in executions if e.success) / len(executions) if executions else 0,
            "average_execution_time": sum(e.execution_time for e in executions) / len(executions) if executions else 0,
            "total_cost": sum(e.cost_estimate for e in executions)
        }
    
    async def list_swarms(self) -> List[Dict[str, Any]]:
        """List all created swarms"""
        swarms = []
        for swarm_id in self.created_swarms:
            swarm_info = await self.get_swarm_info(swarm_id)
            swarms.append(swarm_info)
        return swarms
    
    async def delete_swarm(self, swarm_id: str) -> bool:
        """Delete a created swarm"""
        if swarm_id not in self.created_swarms:
            raise HTTPException(status_code=404, detail=f"Swarm {swarm_id} not found")
        
        # Clean up
        del self.created_swarms[swarm_id]
        if swarm_id in self.agno_teams:
            del self.agno_teams[swarm_id]
        
        # Remove from execution history
        self.execution_history = [e for e in self.execution_history if e.swarm_id != swarm_id]
        
        logger.info(f"Deleted swarm {swarm_id}")
        return True
    
    async def _validate_blueprint(self, blueprint: SwarmBlueprint) -> None:
        """Validate swarm blueprint"""
        if not blueprint.name:
            raise HTTPException(status_code=400, detail="Swarm name is required")
        
        if len(blueprint.agents) < 1:
            raise HTTPException(status_code=400, detail="At least one agent is required")
        
        if len(blueprint.agents) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 agents allowed")
        
        # Validate agent configurations
        agent_names = []
        for agent in blueprint.agents:
            if not agent.name:
                raise HTTPException(status_code=400, detail="All agents must have names")
            
            if agent.name in agent_names:
                raise HTTPException(status_code=400, detail=f"Duplicate agent name: {agent.name}")
            agent_names.append(agent.name)
            
            if not agent.model:
                raise HTTPException(status_code=400, detail=f"Agent {agent.name} must have a model")
            
            if not (0.0 <= agent.temperature <= 1.0):
                raise HTTPException(status_code=400, detail=f"Agent {agent.name} temperature must be between 0.0 and 1.0")
    
    def _map_execution_mode_to_strategy(self, mode: SwarmExecutionMode) -> ExecutionStrategy:
        """Map SwarmExecutionMode to AGNO ExecutionStrategy"""
        mapping = {
            SwarmExecutionMode.LINEAR: ExecutionStrategy.LITE,
            SwarmExecutionMode.PARALLEL: ExecutionStrategy.BALANCED,
            SwarmExecutionMode.DEBATE: ExecutionStrategy.DEBATE,
            SwarmExecutionMode.CONSENSUS: ExecutionStrategy.CONSENSUS,
            SwarmExecutionMode.HIERARCHICAL: ExecutionStrategy.QUALITY,
            SwarmExecutionMode.EVOLUTIONARY: ExecutionStrategy.QUALITY
        }
        return mapping.get(mode, ExecutionStrategy.BALANCED)
    
    def _estimate_cost(self, blueprint: SwarmBlueprint, result: Dict[str, Any]) -> float:
        """Estimate cost of execution"""
        # Simple cost estimation based on token usage and model pricing
        token_usage = result.get("token_usage", {})
        total_tokens = token_usage.get("total_tokens", 1000)  # Default estimate
        
        # Base cost per 1000 tokens (rough estimates)
        model_costs = {
            "openai/gpt-5-chat": 0.005,
            "anthropic/claude-sonnet-4": 0.003, 
            "x-ai/grok-code-fast-1": 0.001,
            "x-ai/grok-4": 0.002,
            "deepseek/deepseek-chat": 0.0005,
            "qwen/qwen3-30b-a3b": 0.002
        }
        
        total_cost = 0.0
        for agent in blueprint.agents:
            cost_per_1k = model_costs.get(agent.model, 0.002)  # Default cost
            agent_tokens = total_tokens / len(blueprint.agents)  # Rough split
            total_cost += (agent_tokens / 1000) * cost_per_1k
        
        return round(total_cost, 4)

# Global factory instance
factory = AgentFactory()

# ==============================================================================
# FASTAPI ROUTER
# ==============================================================================

router = APIRouter(prefix="/api/factory", tags=["agent-factory"])

@router.get("/templates")
async def get_templates():
    """Get all available swarm templates"""
    templates = await factory.get_templates()
    return [asdict(template) for template in templates]

@router.get("/patterns")  
async def get_patterns():
    """Get all available execution patterns"""
    return [
        {
            "name": "hierarchical",
            "description": "Manager coordinates agent execution in hierarchy",
            "compatible_swarms": ["coding", "consensus", "standard"]
        },
        {
            "name": "debate",
            "description": "Agents argue opposing viewpoints to reach conclusion", 
            "compatible_swarms": ["debate", "analysis"]
        },
        {
            "name": "consensus", 
            "description": "All agents contribute to collaborative decision",
            "compatible_swarms": ["consensus", "collaboration"]
        },
        {
            "name": "sequential",
            "description": "Agents execute one after another in sequence",
            "compatible_swarms": ["coding", "standard"]
        },
        {
            "name": "parallel",
            "description": "All agents execute simultaneously", 
            "compatible_swarms": ["analysis", "research"]
        },
        {
            "name": "evolutionary",
            "description": "Agents evolve solutions through iterations",
            "compatible_swarms": ["optimization", "creative"]
        }
    ]

@router.post("/create")
async def create_swarm(blueprint: SwarmBlueprint):
    """Create a new swarm from blueprint"""
    try:
        swarm_id = await factory.create_swarm_from_blueprint(blueprint)
        
        return {
            "swarm_id": swarm_id,
            "status": "created",
            "name": blueprint.name,
            "agents": len(blueprint.agents),
            "pattern": blueprint.pattern,
            "endpoints": {
                "execute": f"/api/factory/swarms/{swarm_id}/execute",
                "status": f"/api/factory/swarms/{swarm_id}/status",
                "info": f"/api/factory/swarms/{swarm_id}"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to create swarm: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create swarm: {str(e)}")

@router.post("/swarms/{swarm_id}/execute")
async def execute_swarm(swarm_id: str, request: Dict[str, Any]):
    """Execute a factory-created swarm"""
    task = request.get("task", "")
    context = request.get("context", {})
    
    if not task:
        raise HTTPException(status_code=400, detail="Task is required")
    
    try:
        result = await factory.execute_swarm(swarm_id, task, context)
        return asdict(result)
        
    except Exception as e:
        logger.error(f"Failed to execute swarm {swarm_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

@router.get("/swarms/{swarm_id}")
async def get_swarm_info(swarm_id: str):
    """Get information about a specific swarm"""
    return await factory.get_swarm_info(swarm_id)

@router.get("/swarms")
async def list_swarms():
    """List all created swarms"""
    return await factory.list_swarms()

@router.delete("/swarms/{swarm_id}")
async def delete_swarm(swarm_id: str):
    """Delete a created swarm"""
    success = await factory.delete_swarm(swarm_id)
    return {"success": success, "swarm_id": swarm_id}

@router.get("/health")
async def health_check():
    """Health check for factory service"""
    return {
        "status": "healthy",
        "active_swarms": len(factory.created_swarms),
        "total_executions": len(factory.execution_history),
        "templates_available": len(factory.templates),
        "timestamp": datetime.now().isoformat()
    }