"""
Base Agent Class for SOPHIA Intel Agent Swarm

Provides common functionality for all specialized agents in the swarm.
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import aiohttp
from pydantic import BaseModel


class AgentType(Enum):
    """Types of agents in the swarm"""
    PLANNER = "planner"
    CODER = "coder"
    REVIEWER = "reviewer"
    INTEGRATOR = "integrator"
    TESTER = "tester"
    DOCUMENTER = "documenter"


class TaskStatus(Enum):
    """Status of agent tasks"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class Priority(Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentTask:
    """Represents a task for an agent"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    description: str = ""
    requirements: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)


@dataclass
class AgentCapability:
    """Defines what an agent can do"""
    name: str
    description: str
    input_types: List[str]
    output_types: List[str]
    estimated_duration: int  # in seconds
    confidence_score: float  # 0.0 to 1.0


class BaseAgent(ABC):
    """
    Base class for all agents in the SOPHIA Intel swarm.
    
    Provides common functionality including:
    - Task management
    - Communication with other agents
    - AI model integration via router
    - Logging and monitoring
    """
    
    def __init__(
        self,
        agent_type: AgentType,
        name: str,
        description: str,
        capabilities: List[AgentCapability],
        ai_router_url: str = "http://localhost:5000/api/ai/route"
    ):
        self.agent_type = agent_type
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.ai_router_url = ai_router_url
        
        # Task management
        self.current_tasks: Dict[str, AgentTask] = {}
        self.completed_tasks: List[AgentTask] = []
        self.failed_tasks: List[AgentTask] = []
        
        # Communication
        self.message_queue: List[Dict[str, Any]] = []
        self.collaborators: Dict[str, 'BaseAgent'] = {}
        
        # Monitoring
        self.logger = logging.getLogger(f"agent.{self.agent_type.value}")
        self.metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "average_completion_time": 0.0,
            "success_rate": 0.0
        }
        
        # HTTP session for AI router communication
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self) -> None:
        """Initialize the agent"""
        self.session = aiohttp.ClientSession()
        self.logger.info(f"Agent {self.name} initialized with {len(self.capabilities)} capabilities")
    
    async def shutdown(self) -> None:
        """Shutdown the agent gracefully"""
        if self.session:
            await self.session.close()
        self.logger.info(f"Agent {self.name} shutdown complete")
    
    @abstractmethod
    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Execute a specific task. Must be implemented by each agent.
        
        Args:
            task: The task to execute
            
        Returns:
            Dict containing the task result
        """
        pass
    
    async def can_handle_task(self, task: AgentTask) -> float:
        """
        Determine if this agent can handle a task and with what confidence.
        
        Args:
            task: The task to evaluate
            
        Returns:
            Confidence score (0.0 to 1.0), 0.0 means cannot handle
        """
        for capability in self.capabilities:
            if task.type in capability.input_types:
                return capability.confidence_score
        return 0.0
    
    async def assign_task(self, task: AgentTask) -> bool:
        """
        Assign a task to this agent.
        
        Args:
            task: The task to assign
            
        Returns:
            True if task was accepted, False otherwise
        """
        confidence = await self.can_handle_task(task)
        if confidence == 0.0:
            self.logger.warning(f"Cannot handle task {task.id}: {task.type}")
            return False
        
        task.assigned_agent = self.name
        task.status = TaskStatus.PENDING
        self.current_tasks[task.id] = task
        
        self.logger.info(f"Accepted task {task.id}: {task.description}")
        return True
    
    async def process_tasks(self) -> None:
        """Process all pending tasks"""
        pending_tasks = [
            task for task in self.current_tasks.values()
            if task.status == TaskStatus.PENDING
        ]
        
        # Sort by priority
        pending_tasks.sort(key=lambda t: t.priority.value, reverse=True)
        
        for task in pending_tasks:
            await self._execute_task_with_monitoring(task)
    
    async def _execute_task_with_monitoring(self, task: AgentTask) -> None:
        """Execute a task with monitoring and error handling"""
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.utcnow()
        
        try:
            self.logger.info(f"Starting task {task.id}: {task.description}")
            
            # Execute the task
            result = await self.execute_task(task)
            
            # Mark as completed
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result = result
            
            # Move to completed tasks
            self.completed_tasks.append(task)
            del self.current_tasks[task.id]
            
            # Update metrics
            self.metrics["tasks_completed"] += 1
            self._update_metrics()
            
            self.logger.info(f"Completed task {task.id} successfully")
            
        except Exception as e:
            # Mark as failed
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.error = str(e)
            
            # Move to failed tasks
            self.failed_tasks.append(task)
            del self.current_tasks[task.id]
            
            # Update metrics
            self.metrics["tasks_failed"] += 1
            self._update_metrics()
            
            self.logger.error(f"Task {task.id} failed: {e}")
    
    async def communicate_with_ai(
        self,
        prompt: str,
        task_type: str = "code_generation",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Communicate with AI models via the router.
        
        Args:
            prompt: The prompt to send
            task_type: Type of task for optimal model selection
            context: Additional context for the request
            
        Returns:
            AI response content
        """
        if not self.session:
            raise RuntimeError("Agent not initialized")
        
        request_data = {
            "task_type": task_type,
            "prompt": prompt,
            "context": context or {},
            "preferences": {
                "cost_preference": "balanced",
                "quality_requirement": "high",
                "max_latency_ms": 10000
            },
            "metadata": {
                "agent_type": self.agent_type.value,
                "agent_name": self.name
            }
        }
        
        try:
            async with self.session.post(
                self.ai_router_url,
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("execution_result", {}).get("content", "")
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"AI router error: {response.status} - {error_text}")
                    
        except Exception as e:
            self.logger.error(f"AI communication failed: {e}")
            raise
    
    async def send_message(self, recipient: str, message: Dict[str, Any]) -> None:
        """
        Send a message to another agent.
        
        Args:
            recipient: Name of the recipient agent
            message: Message content
        """
        if recipient in self.collaborators:
            await self.collaborators[recipient].receive_message(self.name, message)
        else:
            self.logger.warning(f"Unknown recipient: {recipient}")
    
    async def receive_message(self, sender: str, message: Dict[str, Any]) -> None:
        """
        Receive a message from another agent.
        
        Args:
            sender: Name of the sender agent
            message: Message content
        """
        self.message_queue.append({
            "sender": sender,
            "message": message,
            "timestamp": datetime.utcnow()
        })
        self.logger.info(f"Received message from {sender}")
    
    def add_collaborator(self, agent: 'BaseAgent') -> None:
        """Add another agent as a collaborator"""
        self.collaborators[agent.name] = agent
        agent.collaborators[self.name] = self
        self.logger.info(f"Added collaborator: {agent.name}")
    
    def _update_metrics(self) -> None:
        """Update agent performance metrics"""
        total_tasks = self.metrics["tasks_completed"] + self.metrics["tasks_failed"]
        if total_tasks > 0:
            self.metrics["success_rate"] = self.metrics["tasks_completed"] / total_tasks
        
        # Calculate average completion time
        completed_tasks = [t for t in self.completed_tasks if t.completed_at and t.started_at]
        if completed_tasks:
            total_time = sum(
                (t.completed_at - t.started_at).total_seconds()
                for t in completed_tasks
            )
            self.metrics["average_completion_time"] = total_time / len(completed_tasks)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "name": self.name,
            "type": self.agent_type.value,
            "description": self.description,
            "current_tasks": len(self.current_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "metrics": self.metrics,
            "capabilities": [
                {
                    "name": cap.name,
                    "description": cap.description,
                    "confidence": cap.confidence_score
                }
                for cap in self.capabilities
            ]
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', type='{self.agent_type.value}')>"

