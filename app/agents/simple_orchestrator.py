"""
Simple Agent Orchestrator - Sequential execution pattern for agents
Replaces complex LangGraph with straightforward sequential coordination
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

import redis
import requests

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Agent roles in the system"""
    RESEARCHER = "researcher"
    CODER = "coder"
    REVIEWER = "reviewer"
    EXECUTOR = "executor"
    MONITOR = "monitor"


class ExecutionStatus(Enum):
    """Execution status for agents"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentTask:
    """Task definition for an agent"""
    id: str
    role: AgentRole
    description: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class ExecutionContext:
    """Context shared across agent executions"""
    session_id: str
    user_request: str
    workflow_name: str
    agents_chain: List[AgentRole]
    current_step: int = 0
    state: Dict[str, Any] = field(default_factory=dict)
    tasks: List[AgentTask] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None


class SimpleAgentOrchestrator:
    """
    Simple sequential agent orchestrator
    No complex graphs - just sequential execution with state management
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        ollama_url: str = "http://localhost:11434",
        n8n_url: str = "http://localhost:5678"
    ):
        self.redis_client = redis.from_url(redis_url)
        self.ollama_url = ollama_url
        self.n8n_url = n8n_url
        self.agent_executors = self._initialize_executors()
        
    def _initialize_executors(self) -> Dict[AgentRole, Callable]:
        """Initialize agent executor functions"""
        return {
            AgentRole.RESEARCHER: self._execute_researcher,
            AgentRole.CODER: self._execute_coder,
            AgentRole.REVIEWER: self._execute_reviewer,
            AgentRole.EXECUTOR: self._execute_executor,
            AgentRole.MONITOR: self._execute_monitor,
        }
    
    async def execute_workflow(
        self,
        session_id: str,
        user_request: str,
        workflow_name: str = "default",
        agents_chain: Optional[List[AgentRole]] = None
    ) -> ExecutionContext:
        """
        Execute a workflow with sequential agent execution
        
        Default chain: researcher -> coder -> reviewer
        """
        if agents_chain is None:
            agents_chain = [
                AgentRole.RESEARCHER,
                AgentRole.CODER,
                AgentRole.REVIEWER
            ]
        
        # Initialize execution context
        context = ExecutionContext(
            session_id=session_id,
            user_request=user_request,
            workflow_name=workflow_name,
            agents_chain=agents_chain
        )
        
        # Store initial state in Redis
        await self._save_context(context)
        
        try:
            # Execute agents sequentially
            for agent_role in agents_chain:
                logger.info(f"Executing agent: {agent_role.value}")
                
                # Create task for this agent
                task = AgentTask(
                    id=f"{session_id}_{agent_role.value}_{context.current_step}",
                    role=agent_role,
                    description=f"Execute {agent_role.value} for: {user_request}",
                    input_data=context.state
                )
                
                context.tasks.append(task)
                context.current_step += 1
                
                # Execute the agent
                await self._execute_agent(task, context)
                
                # Check if execution should continue
                if task.status == ExecutionStatus.FAILED:
                    logger.error(f"Agent {agent_role.value} failed: {task.error}")
                    break
                
                # Update context state with agent output
                if task.output_data:
                    context.state.update(task.output_data)
                
                # Save progress
                await self._save_context(context)
            
            context.end_time = time.time()
            await self._save_context(context)
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            context.state["error"] = str(e)
            context.end_time = time.time()
            await self._save_context(context)
            raise
        
        return context
    
    async def _execute_agent(self, task: AgentTask, context: ExecutionContext):
        """Execute a single agent task"""
        task.status = ExecutionStatus.RUNNING
        task.started_at = datetime.now()
        
        try:
            # Get the appropriate executor
            executor = self.agent_executors.get(task.role)
            if not executor:
                raise ValueError(f"No executor for role: {task.role}")
            
            # Execute the agent
            result = await executor(task, context)
            
            task.output_data = result
            task.status = ExecutionStatus.COMPLETED
            task.completed_at = datetime.now()
            
        except Exception as e:
            task.status = ExecutionStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            raise
    
    async def _execute_researcher(self, task: AgentTask, context: ExecutionContext) -> Dict[str, Any]:
        """
        Research agent - gathers information and context
        """
        prompt = f"""
        You are a research agent. Analyze this request and provide research findings.
        
        User Request: {context.user_request}
        
        Previous Context: {json.dumps(context.state, indent=2)}
        
        Provide:
        1. Key requirements
        2. Technical considerations
        3. Suggested approach
        4. Potential challenges
        
        Respond in JSON format.
        """
        
        response = await self._call_ollama(prompt)
        
        return {
            "research_findings": response,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_coder(self, task: AgentTask, context: ExecutionContext) -> Dict[str, Any]:
        """
        Coder agent - generates code based on research
        """
        research = context.state.get("research_findings", {})
        
        prompt = f"""
        You are a coding agent. Generate code based on the research findings.
        
        User Request: {context.user_request}
        
        Research Findings: {json.dumps(research, indent=2)}
        
        Generate:
        1. Code implementation
        2. Configuration files if needed
        3. Documentation
        
        Respond in JSON format with 'code', 'config', and 'docs' keys.
        """
        
        response = await self._call_ollama(prompt)
        
        return {
            "generated_code": response,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_reviewer(self, task: AgentTask, context: ExecutionContext) -> Dict[str, Any]:
        """
        Reviewer agent - reviews and validates generated code
        """
        code = context.state.get("generated_code", {})
        
        prompt = f"""
        You are a code review agent. Review the generated code.
        
        User Request: {context.user_request}
        
        Generated Code: {json.dumps(code, indent=2)}
        
        Provide:
        1. Code quality assessment
        2. Security considerations
        3. Performance implications
        4. Suggested improvements
        5. Approval status (approved/needs_revision)
        
        Respond in JSON format.
        """
        
        response = await self._call_ollama(prompt)
        
        return {
            "review_results": response,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_executor(self, task: AgentTask, context: ExecutionContext) -> Dict[str, Any]:
        """
        Executor agent - executes approved code/workflows
        """
        # This would integrate with n8n to execute workflows
        workflow_id = context.state.get("workflow_id", "default")
        
        try:
            # Trigger n8n workflow
            response = requests.post(
                f"{self.n8n_url}/webhook/{workflow_id}",
                json={
                    "context": context.state,
                    "task": task.description
                },
                timeout=30
            )
            
            return {
                "execution_result": response.json() if response.status_code == 200 else {"error": response.text},
                "status_code": response.status_code,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "execution_error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _execute_monitor(self, task: AgentTask, context: ExecutionContext) -> Dict[str, Any]:
        """
        Monitor agent - monitors execution and provides feedback
        """
        execution_result = context.state.get("execution_result", {})
        
        return {
            "monitoring_data": {
                "execution_time": time.time() - context.start_time,
                "agents_executed": context.current_step,
                "final_status": "success" if not execution_result.get("error") else "failed",
                "metrics": self._collect_metrics()
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def _call_ollama(self, prompt: str, model: str = "llama3.2") -> Dict[str, Any]:
        """Call Ollama API for LLM processing"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                try:
                    return json.loads(result.get("response", "{}"))
                except json.JSONDecodeError:
                    return {"raw_response": result.get("response", "")}
            else:
                return {"error": f"Ollama API error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
            return {"error": str(e)}
    
    async def _save_context(self, context: ExecutionContext):
        """Save execution context to Redis"""
        key = f"execution:{context.session_id}"
        value = json.dumps({
            "session_id": context.session_id,
            "user_request": context.user_request,
            "workflow_name": context.workflow_name,
            "agents_chain": [role.value for role in context.agents_chain],
            "current_step": context.current_step,
            "state": context.state,
            "tasks": [
                {
                    "id": task.id,
                    "role": task.role.value,
                    "status": task.status.value,
                    "error": task.error
                }
                for task in context.tasks
            ],
            "start_time": context.start_time,
            "end_time": context.end_time
        })
        
        self.redis_client.setex(key, 3600, value)  # Expire after 1 hour
    
    async def get_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve execution context from Redis"""
        key = f"execution:{session_id}"
        value = self.redis_client.get(key)
        
        if value:
            return json.loads(value)
        return None
    
    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect basic metrics"""
        return {
            "redis_connected": self.redis_client.ping(),
            "memory_usage": self.redis_client.info("memory").get("used_memory_human", "unknown"),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agents"""
        return [role.value for role in AgentRole]
    
    def get_default_workflow(self) -> List[str]:
        """Get default workflow chain"""
        return [
            AgentRole.RESEARCHER.value,
            AgentRole.CODER.value,
            AgentRole.REVIEWER.value
        ]