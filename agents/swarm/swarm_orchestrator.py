"""
Agent Swarm Orchestrator for SOPHIA Intel

Coordinates the execution of complex development missions using specialized agents:
- Planner: Task decomposition and strategy
- Coder: Code generation and implementation  
- Reviewer: Code review and quality assurance
- Integrator: System integration and deployment
- Tester: Automated testing and validation
- Documenter: Documentation generation

The orchestrator manages task flow, agent communication, and mission completion.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from .base_agent import AgentTask, AgentType, BaseAgent, Priority, TaskStatus
from .planner.planner_agent import PlannerAgent
from .coder.coder_agent import CoderAgent


class MissionStatus(Enum):
    """Status of a development mission"""
    PENDING = "pending"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    TESTING = "testing"
    INTEGRATION = "integration"
    DOCUMENTATION = "documentation"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Mission:
    """Represents a complete development mission"""
    
    def __init__(
        self,
        mission_id: str,
        description: str,
        requirements: Dict[str, Any],
        priority: Priority = Priority.MEDIUM
    ):
        self.mission_id = mission_id
        self.description = description
        self.requirements = requirements
        self.priority = priority
        self.status = MissionStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        
        # Mission execution data
        self.plan: Optional[Dict[str, Any]] = None
        self.tasks: List[AgentTask] = []
        self.completed_tasks: List[AgentTask] = []
        self.failed_tasks: List[AgentTask] = []
        self.artifacts: List[str] = []
        self.deliverables: Dict[str, Any] = {}
        
        # Progress tracking
        self.progress_percentage = 0.0
        self.current_phase = ""
        self.estimated_completion: Optional[datetime] = None
        
        # Results and metrics
        self.results: Dict[str, Any] = {}
        self.metrics: Dict[str, Any] = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_duration_seconds": 0,
            "agent_utilization": {}
        }


class SwarmOrchestrator:
    """
    Orchestrates the SOPHIA Intel Agent Swarm for complex development missions.
    
    Manages:
    - Mission planning and execution
    - Agent coordination and communication
    - Task scheduling and dependencies
    - Progress monitoring and reporting
    - Result aggregation and delivery
    """
    
    def __init__(self, ai_router_url: str = None):
        # Use environment variable or default
        from config.config import settings
        self.ai_router_url = ai_router_url or (settings.ORCHESTRATOR_URL + "/ai/chat")
        
        # Initialize agents
        self.agents: Dict[AgentType, BaseAgent] = {}
        self.agent_pool: List[BaseAgent] = []
        
        # Mission management
        self.active_missions: Dict[str, Mission] = {}
        self.completed_missions: List[Mission] = []
        self.mission_queue: List[Mission] = []
        
        # Orchestrator state
        self.is_running = False
        self.max_concurrent_missions = 3
        self.task_scheduler_interval = 5  # seconds
        
        # Logging and monitoring
        self.logger = logging.getLogger("swarm.orchestrator")
        self.metrics = {
            "missions_completed": 0,
            "missions_failed": 0,
            "total_tasks_executed": 0,
            "average_mission_duration": 0.0,
            "agent_performance": {}
        }
    
    async def initialize(self) -> None:
        """Initialize the swarm orchestrator and all agents"""
        self.logger.info("Initializing SOPHIA Intel Agent Swarm...")
        
        # Initialize core agents
        await self._initialize_agents()
        
        # Set up agent collaboration
        await self._setup_agent_collaboration()
        
        # Start background tasks
        self.is_running = True
        asyncio.create_task(self._mission_scheduler())
        asyncio.create_task(self._task_scheduler())
        asyncio.create_task(self._progress_monitor())
        
        self.logger.info(f"Agent Swarm initialized with {len(self.agents)} agents")
    
    async def shutdown(self) -> None:
        """Shutdown the swarm orchestrator gracefully"""
        self.logger.info("Shutting down Agent Swarm...")
        
        self.is_running = False
        
        # Complete active missions
        for mission in self.active_missions.values():
            if mission.status == MissionStatus.IN_PROGRESS:
                mission.status = MissionStatus.CANCELLED
        
        # Shutdown all agents
        for agent in self.agents.values():
            await agent.shutdown()
        
        self.logger.info("Agent Swarm shutdown complete")
    
    async def start_mission(
        self,
        description: str,
        requirements: Dict[str, Any],
        priority: Priority = Priority.MEDIUM
    ) -> str:
        """
        Start a new development mission.
        
        Args:
            description: Mission description
            requirements: Mission requirements and constraints
            priority: Mission priority level
            
        Returns:
            Mission ID for tracking
        """
        mission_id = str(uuid.uuid4())
        
        mission = Mission(
            mission_id=mission_id,
            description=description,
            requirements=requirements,
            priority=priority
        )
        
        # Add to mission queue
        self.mission_queue.append(mission)
        self.mission_queue.sort(key=lambda m: m.priority.value, reverse=True)
        
        self.logger.info(f"Mission {mission_id} queued: {description}")
        
        return mission_id
    
    async def get_mission_status(self, mission_id: str) -> Dict[str, Any]:
        """Get the status of a specific mission"""
        # Check active missions
        if mission_id in self.active_missions:
            mission = self.active_missions[mission_id]
            return self._format_mission_status(mission)
        
        # Check completed missions
        for mission in self.completed_missions:
            if mission.mission_id == mission_id:
                return self._format_mission_status(mission)
        
        # Check queued missions
        for mission in self.mission_queue:
            if mission.mission_id == mission_id:
                return self._format_mission_status(mission)
        
        raise ValueError(f"Mission {mission_id} not found")
    
    async def cancel_mission(self, mission_id: str) -> bool:
        """Cancel a mission"""
        # Cancel active mission
        if mission_id in self.active_missions:
            mission = self.active_missions[mission_id]
            mission.status = MissionStatus.CANCELLED
            mission.completed_at = datetime.utcnow()
            
            # Move to completed missions
            self.completed_missions.append(mission)
            del self.active_missions[mission_id]
            
            self.logger.info(f"Mission {mission_id} cancelled")
            return True
        
        # Remove from queue
        for i, mission in enumerate(self.mission_queue):
            if mission.mission_id == mission_id:
                mission.status = MissionStatus.CANCELLED
                self.mission_queue.pop(i)
                self.completed_missions.append(mission)
                self.logger.info(f"Mission {mission_id} removed from queue")
                return True
        
        return False
    
    async def get_swarm_status(self) -> Dict[str, Any]:
        """Get overall swarm status and metrics"""
        return {
            "status": "running" if self.is_running else "stopped",
            "agents": {
                agent_type.value: agent.get_status()
                for agent_type, agent in self.agents.items()
            },
            "missions": {
                "active": len(self.active_missions),
                "queued": len(self.mission_queue),
                "completed": len(self.completed_missions)
            },
            "metrics": self.metrics,
            "capacity": {
                "max_concurrent_missions": self.max_concurrent_missions,
                "current_load": len(self.active_missions) / self.max_concurrent_missions
            }
        }
    
    # Private methods for orchestration
    
    async def _initialize_agents(self) -> None:
        """Initialize all specialized agents"""
        # Initialize Planner Agent
        planner = PlannerAgent(self.ai_router_url)
        await planner.initialize()
        self.agents[AgentType.PLANNER] = planner
        self.agent_pool.append(planner)
        
        # Initialize Coder Agent
        coder = CoderAgent(self.ai_router_url)
        await coder.initialize()
        self.agents[AgentType.CODER] = coder
        self.agent_pool.append(coder)
        
        # TODO: Initialize other agents (Reviewer, Integrator, Tester, Documenter)
        # For now, we'll use placeholder implementations
        
        self.logger.info(f"Initialized {len(self.agents)} agents")
    
    async def _setup_agent_collaboration(self) -> None:
        """Set up collaboration between agents"""
        # Connect all agents as collaborators
        for agent1 in self.agent_pool:
            for agent2 in self.agent_pool:
                if agent1 != agent2:
                    agent1.add_collaborator(agent2)
        
        self.logger.info("Agent collaboration network established")
    
    async def _mission_scheduler(self) -> None:
        """Background task to schedule missions from the queue"""
        while self.is_running:
            try:
                # Check if we can start new missions
                if (len(self.active_missions) < self.max_concurrent_missions and 
                    self.mission_queue):
                    
                    # Get highest priority mission
                    mission = self.mission_queue.pop(0)
                    await self._start_mission_execution(mission)
                
                await asyncio.sleep(self.task_scheduler_interval)
                
            except Exception as e:
                self.logger.error(f"Mission scheduler error: {e}")
                await asyncio.sleep(self.task_scheduler_interval)
    
    async def _task_scheduler(self) -> None:
        """Background task to schedule agent tasks"""
        while self.is_running:
            try:
                # Process tasks for all active missions
                for mission in self.active_missions.values():
                    await self._process_mission_tasks(mission)
                
                # Process agent task queues
                for agent in self.agent_pool:
                    await agent.process_tasks()
                
                await asyncio.sleep(self.task_scheduler_interval)
                
            except Exception as e:
                self.logger.error(f"Task scheduler error: {e}")
                await asyncio.sleep(self.task_scheduler_interval)
    
    async def _progress_monitor(self) -> None:
        """Background task to monitor mission progress"""
        while self.is_running:
            try:
                for mission in list(self.active_missions.values()):
                    await self._update_mission_progress(mission)
                    
                    # Check if mission is complete
                    if await self._is_mission_complete(mission):
                        await self._complete_mission(mission)
                
                await asyncio.sleep(10)  # Check progress every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Progress monitor error: {e}")
                await asyncio.sleep(10)
    
    async def _start_mission_execution(self, mission: Mission) -> None:
        """Start executing a mission"""
        mission.status = MissionStatus.PLANNING
        mission.started_at = datetime.utcnow()
        self.active_missions[mission.mission_id] = mission
        
        self.logger.info(f"Starting mission execution: {mission.mission_id}")
        
        # Create planning task
        planning_task = AgentTask(
            type="mission",
            description=mission.description,
            requirements=mission.requirements,
            priority=mission.priority,
            context={"mission_id": mission.mission_id}
        )
        
        # Assign to planner
        planner = self.agents[AgentType.PLANNER]
        await planner.assign_task(planning_task)
        mission.tasks.append(planning_task)
        mission.current_phase = "Planning"
    
    async def _process_mission_tasks(self, mission: Mission) -> None:
        """Process tasks for a specific mission"""
        # Check for completed planning
        if mission.status == MissionStatus.PLANNING:
            planning_tasks = [t for t in mission.tasks if t.type == "mission"]
            if planning_tasks and planning_tasks[0].status == TaskStatus.COMPLETED:
                # Extract plan and create implementation tasks
                plan_result = planning_tasks[0].result
                if plan_result:
                    mission.plan = plan_result
                    await self._create_implementation_tasks(mission)
                    mission.status = MissionStatus.IN_PROGRESS
        
        # Process implementation tasks
        elif mission.status == MissionStatus.IN_PROGRESS:
            await self._schedule_ready_tasks(mission)
    
    async def _create_implementation_tasks(self, mission: Mission) -> None:
        """Create implementation tasks from the mission plan"""
        if not mission.plan:
            return
        
        subtasks = mission.plan.get("subtasks", [])
        
        for subtask_data in subtasks:
            task = AgentTask(
                type=self._determine_task_type(subtask_data),
                description=subtask_data.get("description", ""),
                requirements=subtask_data.get("requirements", {}),
                priority=self._convert_priority(subtask_data.get("priority", "medium")),
                context={
                    "mission_id": mission.mission_id,
                    "subtask_data": subtask_data
                },
                dependencies=subtask_data.get("dependencies", [])
            )
            
            mission.tasks.append(task)
        
        self.logger.info(f"Created {len(subtasks)} implementation tasks for mission {mission.mission_id}")
    
    async def _schedule_ready_tasks(self, mission: Mission) -> None:
        """Schedule tasks that are ready to execute"""
        for task in mission.tasks:
            if (task.status == TaskStatus.PENDING and 
                await self._are_dependencies_met(task, mission)):
                
                # Find appropriate agent
                best_agent = await self._find_best_agent(task)
                if best_agent and await best_agent.assign_task(task):
                    self.logger.info(f"Assigned task {task.id} to {best_agent.name}")
    
    async def _find_best_agent(self, task: AgentTask) -> Optional[BaseAgent]:
        """Find the best agent for a task"""
        best_agent = None
        best_confidence = 0.0
        
        for agent in self.agent_pool:
            confidence = await agent.can_handle_task(task)
            if confidence > best_confidence:
                best_confidence = confidence
                best_agent = agent
        
        return best_agent if best_confidence > 0.0 else None
    
    async def _are_dependencies_met(self, task: AgentTask, mission: Mission) -> bool:
        """Check if task dependencies are met"""
        if not task.dependencies:
            return True
        
        completed_task_ids = {
            t.id for t in mission.tasks 
            if t.status == TaskStatus.COMPLETED
        }
        
        return all(dep_id in completed_task_ids for dep_id in task.dependencies)
    
    async def _update_mission_progress(self, mission: Mission) -> None:
        """Update mission progress"""
        total_tasks = len(mission.tasks)
        completed_tasks = len([t for t in mission.tasks if t.status == TaskStatus.COMPLETED])
        failed_tasks = len([t for t in mission.tasks if t.status == TaskStatus.FAILED])
        
        if total_tasks > 0:
            mission.progress_percentage = (completed_tasks / total_tasks) * 100
        
        # Update metrics
        mission.metrics.update({
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks
        })
        
        # Estimate completion time
        if completed_tasks > 0 and mission.started_at:
            elapsed = datetime.utcnow() - mission.started_at
            estimated_total = elapsed * (total_tasks / completed_tasks)
            mission.estimated_completion = mission.started_at + estimated_total
    
    async def _is_mission_complete(self, mission: Mission) -> bool:
        """Check if a mission is complete"""
        if not mission.tasks:
            return False
        
        # All tasks must be completed or failed
        incomplete_tasks = [
            t for t in mission.tasks 
            if t.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]
        ]
        
        return len(incomplete_tasks) == 0
    
    async def _complete_mission(self, mission: Mission) -> None:
        """Complete a mission and generate results"""
        mission.completed_at = datetime.utcnow()
        
        # Check if mission succeeded or failed
        failed_tasks = [t for t in mission.tasks if t.status == TaskStatus.FAILED]
        if failed_tasks:
            mission.status = MissionStatus.FAILED
            self.logger.warning(f"Mission {mission.mission_id} failed with {len(failed_tasks)} failed tasks")
        else:
            mission.status = MissionStatus.COMPLETED
            self.logger.info(f"Mission {mission.mission_id} completed successfully")
        
        # Aggregate results
        await self._aggregate_mission_results(mission)
        
        # Move to completed missions
        self.completed_missions.append(mission)
        del self.active_missions[mission.mission_id]
        
        # Update global metrics
        self.metrics["missions_completed"] += 1
        if mission.status == MissionStatus.FAILED:
            self.metrics["missions_failed"] += 1
    
    async def _aggregate_mission_results(self, mission: Mission) -> None:
        """Aggregate results from all mission tasks"""
        results = {
            "mission_id": mission.mission_id,
            "description": mission.description,
            "status": mission.status.value,
            "duration_seconds": (
                (mission.completed_at - mission.started_at).total_seconds()
                if mission.completed_at and mission.started_at else 0
            ),
            "task_results": [],
            "deliverables": {},
            "artifacts": []
        }
        
        # Collect task results
        for task in mission.tasks:
            if task.result:
                results["task_results"].append({
                    "task_id": task.id,
                    "type": task.type,
                    "status": task.status.value,
                    "result": task.result
                })
                
                # Extract deliverables
                if "code_files" in task.result:
                    results["deliverables"].update(task.result["code_files"])
                
                # Extract artifacts
                if "artifacts" in task.result:
                    results["artifacts"].extend(task.result["artifacts"])
        
        mission.results = results
    
    def _format_mission_status(self, mission: Mission) -> Dict[str, Any]:
        """Format mission status for API response"""
        return {
            "mission_id": mission.mission_id,
            "description": mission.description,
            "status": mission.status.value,
            "priority": mission.priority.value,
            "progress_percentage": mission.progress_percentage,
            "current_phase": mission.current_phase,
            "created_at": mission.created_at.isoformat(),
            "started_at": mission.started_at.isoformat() if mission.started_at else None,
            "completed_at": mission.completed_at.isoformat() if mission.completed_at else None,
            "estimated_completion": mission.estimated_completion.isoformat() if mission.estimated_completion else None,
            "tasks": {
                "total": len(mission.tasks),
                "completed": len([t for t in mission.tasks if t.status == TaskStatus.COMPLETED]),
                "failed": len([t for t in mission.tasks if t.status == TaskStatus.FAILED]),
                "in_progress": len([t for t in mission.tasks if t.status == TaskStatus.IN_PROGRESS])
            },
            "metrics": mission.metrics,
            "results": mission.results if mission.status in [MissionStatus.COMPLETED, MissionStatus.FAILED] else None
        }
    
    def _determine_task_type(self, subtask_data: Dict[str, Any]) -> str:
        """Determine task type from subtask data"""
        agent_type = subtask_data.get("agent_type", "coder")
        
        type_mapping = {
            "planner": "complex_task",
            "coder": "backend_task",
            "reviewer": "code_review",
            "integrator": "integration_task",
            "tester": "test_task",
            "documenter": "documentation_task"
        }
        
        return type_mapping.get(agent_type, "backend_task")
    
    def _convert_priority(self, priority_str: str) -> Priority:
        """Convert priority string to Priority enum"""
        priority_mapping = {
            "low": Priority.LOW,
            "medium": Priority.MEDIUM,
            "high": Priority.HIGH,
            "critical": Priority.CRITICAL
        }
        
        return priority_mapping.get(priority_str.lower(), Priority.MEDIUM)

