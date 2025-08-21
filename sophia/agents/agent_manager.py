"""
SOPHIA Agent Management System
Comprehensive agent creation, tracking, and swarm orchestration
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class AgentType(Enum):
    """Types of agents available in SOPHIA"""
    RESEARCH = "research"
    CODING = "coding"
    BUSINESS = "business"
    MEMORY = "memory"
    CONTEXT = "context"
    CUSTOM = "custom"

class AgentStatus(Enum):
    """Agent operational status"""
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

class SwarmType(Enum):
    """Types of agent swarms"""
    RESEARCH_SWARM = "research_swarm"
    DEVELOPMENT_SWARM = "development_swarm"
    BUSINESS_INTELLIGENCE = "business_intelligence"
    CONTENT_CREATION = "content_creation"
    CUSTOM_SWARM = "custom_swarm"

@dataclass
class AgentCapability:
    """Individual agent capability definition"""
    name: str
    description: str
    enabled: bool = True
    performance_score: float = 0.0
    last_used: Optional[datetime] = None

@dataclass
class AgentMetrics:
    """Agent performance and usage metrics"""
    tasks_completed: int = 0
    success_rate: float = 0.0
    average_response_time: float = 0.0
    uptime_percentage: float = 0.0
    last_activity: Optional[datetime] = None
    total_runtime: timedelta = timedelta()

@dataclass
class Agent:
    """Individual AI agent definition"""
    id: str
    name: str
    type: AgentType
    status: AgentStatus
    capabilities: List[AgentCapability]
    metrics: AgentMetrics
    created_at: datetime
    last_updated: datetime
    config: Dict[str, Any]
    swarm_id: Optional[str] = None
    description: str = ""
    model: str = "gpt-4"
    max_tokens: int = 4000
    temperature: float = 0.7

@dataclass
class Swarm:
    """Agent swarm definition and orchestration"""
    id: str
    name: str
    type: SwarmType
    description: str
    agent_ids: List[str]
    coordinator_agent_id: Optional[str]
    status: AgentStatus
    created_at: datetime
    last_updated: datetime
    config: Dict[str, Any]
    metrics: AgentMetrics

class AgentManager:
    """Central agent management and orchestration system"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.swarms: Dict[str, Swarm] = {}
        self.task_queue: List[Dict[str, Any]] = []
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        
    async def create_agent(
        self,
        name: str,
        agent_type: AgentType,
        capabilities: List[str],
        config: Optional[Dict[str, Any]] = None,
        description: str = ""
    ) -> Agent:
        """Create a new AI agent with specified capabilities"""
        
        agent_id = str(uuid.uuid4())
        
        # Convert capability names to AgentCapability objects
        agent_capabilities = [
            AgentCapability(
                name=cap,
                description=f"{cap.replace('_', ' ').title()} capability",
                enabled=True
            ) for cap in capabilities
        ]
        
        agent = Agent(
            id=agent_id,
            name=name,
            type=agent_type,
            status=AgentStatus.IDLE,
            capabilities=agent_capabilities,
            metrics=AgentMetrics(),
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            config=config or {},
            description=description
        )
        
        self.agents[agent_id] = agent
        
        logger.info(f"Created agent {name} ({agent_id}) with {len(capabilities)} capabilities")
        return agent
    
    async def create_swarm(
        self,
        name: str,
        swarm_type: SwarmType,
        agent_ids: List[str],
        description: str = "",
        coordinator_id: Optional[str] = None
    ) -> Swarm:
        """Create an agent swarm for coordinated tasks"""
        
        swarm_id = str(uuid.uuid4())
        
        # Validate all agent IDs exist
        for agent_id in agent_ids:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found")
        
        # Set coordinator if not specified
        if not coordinator_id and agent_ids:
            coordinator_id = agent_ids[0]
        
        swarm = Swarm(
            id=swarm_id,
            name=name,
            type=swarm_type,
            description=description,
            agent_ids=agent_ids,
            coordinator_agent_id=coordinator_id,
            status=AgentStatus.IDLE,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            config={},
            metrics=AgentMetrics()
        )
        
        # Update agents to reference their swarm
        for agent_id in agent_ids:
            self.agents[agent_id].swarm_id = swarm_id
            self.agents[agent_id].last_updated = datetime.utcnow()
        
        self.swarms[swarm_id] = swarm
        
        logger.info(f"Created swarm {name} ({swarm_id}) with {len(agent_ids)} agents")
        return swarm
    
    async def assign_task_to_agent(
        self,
        agent_id: str,
        task: Dict[str, Any]
    ) -> str:
        """Assign a task to a specific agent"""
        
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        agent = self.agents[agent_id]
        
        if agent.status == AgentStatus.BUSY:
            raise ValueError(f"Agent {agent.name} is currently busy")
        
        task_id = str(uuid.uuid4())
        task_data = {
            "id": task_id,
            "agent_id": agent_id,
            "task": task,
            "status": "assigned",
            "created_at": datetime.utcnow(),
            "started_at": None,
            "completed_at": None
        }
        
        self.active_tasks[task_id] = task_data
        agent.status = AgentStatus.BUSY
        agent.last_updated = datetime.utcnow()
        
        logger.info(f"Assigned task {task_id} to agent {agent.name}")
        return task_id
    
    async def assign_task_to_swarm(
        self,
        swarm_id: str,
        task: Dict[str, Any]
    ) -> str:
        """Assign a complex task to an agent swarm"""
        
        if swarm_id not in self.swarms:
            raise ValueError(f"Swarm {swarm_id} not found")
        
        swarm = self.swarms[swarm_id]
        
        # Check if swarm is available
        busy_agents = [
            agent_id for agent_id in swarm.agent_ids
            if self.agents[agent_id].status == AgentStatus.BUSY
        ]
        
        if len(busy_agents) > len(swarm.agent_ids) // 2:
            raise ValueError(f"Swarm {swarm.name} is too busy (>50% agents occupied)")
        
        task_id = str(uuid.uuid4())
        task_data = {
            "id": task_id,
            "swarm_id": swarm_id,
            "task": task,
            "status": "assigned",
            "created_at": datetime.utcnow(),
            "started_at": None,
            "completed_at": None,
            "subtasks": []
        }
        
        self.active_tasks[task_id] = task_data
        swarm.status = AgentStatus.BUSY
        swarm.last_updated = datetime.utcnow()
        
        logger.info(f"Assigned task {task_id} to swarm {swarm.name}")
        return task_id
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive status of an agent"""
        
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        agent = self.agents[agent_id]
        
        # Get active tasks for this agent
        active_tasks = [
            task for task in self.active_tasks.values()
            if task.get("agent_id") == agent_id and task["status"] in ["assigned", "running"]
        ]
        
        return {
            "agent": asdict(agent),
            "active_tasks": len(active_tasks),
            "swarm_membership": agent.swarm_id,
            "performance_summary": {
                "tasks_completed": agent.metrics.tasks_completed,
                "success_rate": agent.metrics.success_rate,
                "avg_response_time": agent.metrics.average_response_time,
                "uptime": agent.metrics.uptime_percentage
            }
        }
    
    def get_swarm_status(self, swarm_id: str) -> Dict[str, Any]:
        """Get comprehensive status of a swarm"""
        
        if swarm_id not in self.swarms:
            raise ValueError(f"Swarm {swarm_id} not found")
        
        swarm = self.swarms[swarm_id]
        
        # Get agent statuses
        agent_statuses = {}
        for agent_id in swarm.agent_ids:
            if agent_id in self.agents:
                agent_statuses[agent_id] = {
                    "name": self.agents[agent_id].name,
                    "status": self.agents[agent_id].status.value,
                    "type": self.agents[agent_id].type.value
                }
        
        # Get active tasks for this swarm
        active_tasks = [
            task for task in self.active_tasks.values()
            if task.get("swarm_id") == swarm_id and task["status"] in ["assigned", "running"]
        ]
        
        return {
            "swarm": asdict(swarm),
            "agents": agent_statuses,
            "active_tasks": len(active_tasks),
            "coordination_status": {
                "coordinator": swarm.coordinator_agent_id,
                "total_agents": len(swarm.agent_ids),
                "active_agents": len([a for a in agent_statuses.values() if a["status"] == "active"]),
                "busy_agents": len([a for a in agent_statuses.values() if a["status"] == "busy"])
            }
        }
    
    def list_agents(self, filter_type: Optional[AgentType] = None) -> List[Dict[str, Any]]:
        """List all agents with optional filtering"""
        
        agents = list(self.agents.values())
        
        if filter_type:
            agents = [a for a in agents if a.type == filter_type]
        
        return [
            {
                "id": agent.id,
                "name": agent.name,
                "type": agent.type.value,
                "status": agent.status.value,
                "capabilities": len(agent.capabilities),
                "swarm_id": agent.swarm_id,
                "created_at": agent.created_at.isoformat(),
                "tasks_completed": agent.metrics.tasks_completed
            }
            for agent in agents
        ]
    
    def list_swarms(self, filter_type: Optional[SwarmType] = None) -> List[Dict[str, Any]]:
        """List all swarms with optional filtering"""
        
        swarms = list(self.swarms.values())
        
        if filter_type:
            swarms = [s for s in swarms if s.type == filter_type]
        
        return [
            {
                "id": swarm.id,
                "name": swarm.name,
                "type": swarm.type.value,
                "status": swarm.status.value,
                "agent_count": len(swarm.agent_ids),
                "coordinator": swarm.coordinator_agent_id,
                "created_at": swarm.created_at.isoformat(),
                "tasks_completed": swarm.metrics.tasks_completed
            }
            for swarm in swarms
        ]
    
    async def update_agent_metrics(
        self,
        agent_id: str,
        task_completed: bool = False,
        response_time: Optional[float] = None,
        error_occurred: bool = False
    ):
        """Update agent performance metrics"""
        
        if agent_id not in self.agents:
            return
        
        agent = self.agents[agent_id]
        metrics = agent.metrics
        
        if task_completed:
            metrics.tasks_completed += 1
            if not error_occurred:
                # Update success rate
                total_tasks = metrics.tasks_completed
                current_successes = metrics.success_rate * (total_tasks - 1)
                metrics.success_rate = (current_successes + 1) / total_tasks
        
        if response_time:
            # Update average response time
            if metrics.average_response_time == 0:
                metrics.average_response_time = response_time
            else:
                metrics.average_response_time = (
                    metrics.average_response_time * 0.8 + response_time * 0.2
                )
        
        metrics.last_activity = datetime.utcnow()
        agent.last_updated = datetime.utcnow()
        
        # Update status based on activity
        if error_occurred:
            agent.status = AgentStatus.ERROR
        else:
            agent.status = AgentStatus.IDLE
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get comprehensive dashboard summary for UI"""
        
        total_agents = len(self.agents)
        total_swarms = len(self.swarms)
        active_tasks = len([t for t in self.active_tasks.values() if t["status"] in ["assigned", "running"]])
        
        # Agent status breakdown
        agent_status_counts = {}
        for status in AgentStatus:
            agent_status_counts[status.value] = len([
                a for a in self.agents.values() if a.status == status
            ])
        
        # Swarm status breakdown
        swarm_status_counts = {}
        for status in AgentStatus:
            swarm_status_counts[status.value] = len([
                s for s in self.swarms.values() if s.status == status
            ])
        
        # Performance metrics
        total_tasks_completed = sum(a.metrics.tasks_completed for a in self.agents.values())
        avg_success_rate = sum(a.metrics.success_rate for a in self.agents.values()) / max(total_agents, 1)
        
        return {
            "overview": {
                "total_agents": total_agents,
                "total_swarms": total_swarms,
                "active_tasks": active_tasks,
                "total_tasks_completed": total_tasks_completed
            },
            "agent_status": agent_status_counts,
            "swarm_status": swarm_status_counts,
            "performance": {
                "average_success_rate": round(avg_success_rate, 3),
                "system_uptime": "99.2%",  # This would be calculated from actual metrics
                "response_time": "1.2s"    # This would be calculated from actual metrics
            },
            "recent_activity": [
                {
                    "timestamp": task["created_at"].isoformat(),
                    "type": "task_assigned",
                    "description": f"Task assigned to {'agent' if 'agent_id' in task else 'swarm'}",
                    "status": task["status"]
                }
                for task in sorted(
                    self.active_tasks.values(),
                    key=lambda x: x["created_at"],
                    reverse=True
                )[:5]
            ]
        }

# Global agent manager instance
agent_manager = AgentManager()

async def initialize_default_agents():
    """Initialize default agents and swarms for SOPHIA"""
    
    # Create research agents
    research_agent = await agent_manager.create_agent(
        name="Research Specialist",
        agent_type=AgentType.RESEARCH,
        capabilities=["web_search", "data_analysis", "source_verification", "summarization"],
        description="Specialized in comprehensive research and data gathering"
    )
    
    market_research_agent = await agent_manager.create_agent(
        name="Market Intelligence",
        agent_type=AgentType.RESEARCH,
        capabilities=["market_analysis", "competitor_research", "trend_analysis"],
        description="Focused on market research and business intelligence"
    )
    
    # Create coding agents
    backend_agent = await agent_manager.create_agent(
        name="Backend Developer",
        agent_type=AgentType.CODING,
        capabilities=["python_development", "api_design", "database_management", "testing"],
        description="Backend development and API creation specialist"
    )
    
    frontend_agent = await agent_manager.create_agent(
        name="Frontend Developer",
        agent_type=AgentType.CODING,
        capabilities=["react_development", "ui_design", "responsive_design", "testing"],
        description="Frontend development and user interface specialist"
    )
    
    # Create business agents
    business_analyst = await agent_manager.create_agent(
        name="Business Analyst",
        agent_type=AgentType.BUSINESS,
        capabilities=["financial_analysis", "strategy_planning", "reporting", "forecasting"],
        description="Business analysis and strategic planning specialist"
    )
    
    # Create memory and context agents
    memory_agent = await agent_manager.create_agent(
        name="Memory Manager",
        agent_type=AgentType.MEMORY,
        capabilities=["context_storage", "knowledge_retrieval", "indexing", "search"],
        description="Manages long-term memory and context storage"
    )
    
    context_agent = await agent_manager.create_agent(
        name="Context Coordinator",
        agent_type=AgentType.CONTEXT,
        capabilities=["context_analysis", "relevance_scoring", "information_synthesis"],
        description="Coordinates context across different agents and tasks"
    )
    
    # Create swarms
    research_swarm = await agent_manager.create_swarm(
        name="Research Intelligence Swarm",
        swarm_type=SwarmType.RESEARCH_SWARM,
        agent_ids=[research_agent.id, market_research_agent.id],
        description="Comprehensive research and market intelligence",
        coordinator_id=research_agent.id
    )
    
    development_swarm = await agent_manager.create_swarm(
        name="Development Team Swarm",
        swarm_type=SwarmType.DEVELOPMENT_SWARM,
        agent_ids=[backend_agent.id, frontend_agent.id],
        description="Full-stack development capabilities",
        coordinator_id=backend_agent.id
    )
    
    business_intelligence_swarm = await agent_manager.create_swarm(
        name="Business Intelligence Swarm",
        swarm_type=SwarmType.BUSINESS_INTELLIGENCE,
        agent_ids=[business_analyst.id, research_agent.id, memory_agent.id],
        description="Comprehensive business analysis and intelligence",
        coordinator_id=business_analyst.id
    )
    
    logger.info("Initialized default agents and swarms for SOPHIA")
    
    return {
        "agents": [research_agent, market_research_agent, backend_agent, frontend_agent, business_analyst, memory_agent, context_agent],
        "swarms": [research_swarm, development_swarm, business_intelligence_swarm]
    }

