"""
Simple Agent Orchestrator - Sequential execution pattern for agents
Replaces complex LangGraph with straightforward sequential coordination
Enhanced with connection pooling for improved performance
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import aiohttp
from aioredis import Redis, create_redis_pool

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


class OptimizedAgentOrchestrator(SimpleAgentOrchestrator):
    """
    Optimized Agent Orchestrator with connection pooling
    Provides improved performance through connection reuse and async operations
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        ollama_url: str = "http://localhost:11434",
        n8n_url: str = "http://localhost:5678",
        pool_size: int = 10,
        pool_max_size: int = 20
    ):
        """
        Initialize optimized orchestrator with connection pools
        
        Args:
            redis_url: Redis connection URL
            ollama_url: Ollama API URL
            n8n_url: n8n workflow URL
            pool_size: Initial connection pool size
            pool_max_size: Maximum connection pool size
        """
        # Initialize parent class
        super().__init__(redis_url, ollama_url, n8n_url)
        
        # Connection pool settings
        self.pool_size = pool_size
        self.pool_max_size = pool_max_size
        
        # HTTP session for connection pooling
        self.http_session = None
        
        # Redis async pool
        self.redis_pool = None
        
        # Performance metrics
        self.metrics = {
            "ollama_calls": 0,
            "redis_calls": 0,
            "n8n_calls": 0,
            "total_time": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # Response cache for Ollama
        self._response_cache = {}
        self._cache_ttl = 300  # 5 minutes
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
        
    async def connect(self):
        """Initialize connection pools"""
        try:
            # Create HTTP session with connection pooling
            connector = aiohttp.TCPConnector(
                limit=self.pool_max_size,
                limit_per_host=self.pool_size,
                ttl_dns_cache=300
            )
            
            timeout = aiohttp.ClientTimeout(total=30)
            
            self.http_session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "User-Agent": "Sophia-Intel-AI/1.0",
                    "Accept": "application/json"
                }
            )
            
            # Create Redis async pool
            self.redis_pool = await create_redis_pool(
                self.redis_client.connection_pool.connection_kwargs['host'],
                minsize=5,
                maxsize=self.pool_size,
                encoding='utf-8'
            )
            
            logger.info("Connection pools initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize connection pools: {e}")
            # Fall back to standard connections
            
    async def disconnect(self):
        """Close connection pools"""
        try:
            if self.http_session:
                await self.http_session.close()
                
            if self.redis_pool:
                self.redis_pool.close()
                await self.redis_pool.wait_closed()
                
            logger.info("Connection pools closed")
            
        except Exception as e:
            logger.error(f"Error closing connection pools: {e}")
            
    async def _call_ollama(self, prompt: str, model: str = "llama3.2") -> Dict[str, Any]:
        """
        Optimized Ollama call with connection pooling and caching
        """
        start_time = time.time()
        
        # Check cache first
        cache_key = f"{model}:{hashlib.md5(prompt.encode()).hexdigest()}"
        
        if cache_key in self._response_cache:
            cache_entry = self._response_cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self._cache_ttl:
                self.metrics["cache_hits"] += 1
                logger.debug("Cache hit for Ollama prompt")
                return cache_entry["response"]
        
        self.metrics["cache_misses"] += 1
        self.metrics["ollama_calls"] += 1
        
        try:
            if self.http_session:
                # Use pooled connection
                async with self.http_session.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "format": "json",
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "max_tokens": 1000
                        }
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        try:
                            parsed_response = json.loads(result.get("response", "{}"))
                        except json.JSONDecodeError:
                            parsed_response = {"raw_response": result.get("response", "")}
                        
                        # Cache the response
                        self._response_cache[cache_key] = {
                            "response": parsed_response,
                            "timestamp": time.time()
                        }
                        
                        # Clean cache if too large
                        if len(self._response_cache) > 100:
                            self._cleanup_cache()
                        
                        elapsed = time.time() - start_time
                        self.metrics["total_time"] += elapsed
                        logger.debug(f"Ollama call completed in {elapsed:.2f}s")
                        
                        return parsed_response
                    else:
                        return {"error": f"Ollama API error: {response.status}"}
            else:
                # Fall back to standard method
                return await super()._call_ollama(prompt, model)
                
        except Exception as e:
            logger.error(f"Optimized Ollama call failed: {e}")
            # Fall back to standard method
            return await super()._call_ollama(prompt, model)
            
    async def _save_context(self, context: ExecutionContext):
        """
        Optimized context save with async Redis
        """
        self.metrics["redis_calls"] += 1
        
        try:
            if self.redis_pool:
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
                
                await self.redis_pool.setex(key, 3600, value)
                logger.debug(f"Context saved for session {context.session_id[:8]}")
            else:
                # Fall back to sync Redis
                await super()._save_context(context)
                
        except Exception as e:
            logger.error(f"Error saving context: {e}")
            # Fall back to sync Redis
            await super()._save_context(context)
            
    async def get_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Optimized context retrieval with async Redis
        """
        self.metrics["redis_calls"] += 1
        
        try:
            if self.redis_pool:
                key = f"execution:{session_id}"
                value = await self.redis_pool.get(key)
                
                if value:
                    return json.loads(value)
                return None
            else:
                # Fall back to sync Redis
                return await super().get_context(session_id)
                
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return None
            
    def _cleanup_cache(self):
        """Clean up old cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._response_cache.items()
            if current_time - entry["timestamp"] > self._cache_ttl
        ]
        
        for key in expired_keys:
            del self._response_cache[key]
            
        logger.debug(f"Cleaned {len(expired_keys)} expired cache entries")
        
    async def execute_workflow(
        self,
        session_id: str,
        user_request: str,
        workflow_name: str = "default",
        agents_chain: Optional[List[AgentRole]] = None
    ) -> ExecutionContext:
        """
        Optimized workflow execution with batching and parallel processing where possible
        """
        start_time = time.time()
        
        try:
            # Execute with optimizations
            result = await super().execute_workflow(
                session_id,
                user_request,
                workflow_name,
                agents_chain
            )
            
            elapsed = time.time() - start_time
            logger.info(f"Workflow completed in {elapsed:.2f}s - Metrics: {self.get_metrics()}")
            
            return result
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            raise
            
    async def _trigger_n8n_workflow(
        self,
        workflow_id: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Trigger n8n workflow with pooled connection
        """
        self.metrics["n8n_calls"] += 1
        
        try:
            if self.http_session:
                async with self.http_session.post(
                    f"{self.n8n_url}/webhook/{workflow_id}",
                    json=payload
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"n8n error: {response.status}"}
            else:
                # Fall back to sync requests
                response = requests.post(
                    f"{self.n8n_url}/webhook/{workflow_id}",
                    json=payload,
                    timeout=30
                )
                return response.json() if response.status_code == 200 else {"error": response.text}
                
        except Exception as e:
            logger.error(f"n8n workflow trigger failed: {e}")
            return {"error": str(e)}
            
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        metrics = self.metrics.copy()
        
        # Calculate cache hit rate
        total_cache_requests = metrics["cache_hits"] + metrics["cache_misses"]
        metrics["cache_hit_rate"] = (
            metrics["cache_hits"] / total_cache_requests
            if total_cache_requests > 0 else 0
        )
        
        # Average call time
        total_calls = metrics["ollama_calls"] + metrics["redis_calls"] + metrics["n8n_calls"]
        metrics["avg_call_time"] = (
            metrics["total_time"] / total_calls
            if total_calls > 0 else 0
        )
        
        return metrics
        
    def reset_metrics(self):
        """Reset performance metrics"""
        self.metrics = {
            "ollama_calls": 0,
            "redis_calls": 0,
            "n8n_calls": 0,
            "total_time": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        logger.info("Metrics reset")


# Import hashlib for cache key generation
import hashlib


# Example usage
async def example_optimized_usage():
    """Example of using the optimized orchestrator"""
    
    async with OptimizedAgentOrchestrator() as orchestrator:
        # Execute workflow
        context = await orchestrator.execute_workflow(
            session_id="test-session-456",
            user_request="Build a REST API",
            workflow_name="development_workflow",
            agents_chain=[
                AgentRole.RESEARCHER,
                AgentRole.CODER,
                AgentRole.REVIEWER
            ]
        )
        
        print(f"Workflow completed: {context.session_id}")
        print(f"Performance metrics: {orchestrator.get_metrics()}")


if __name__ == "__main__":
    # Run optimized example
    asyncio.run(example_optimized_usage())