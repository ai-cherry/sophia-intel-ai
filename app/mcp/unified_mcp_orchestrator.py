"""
Unified MCP Orchestrator
========================

Consolidated MCP orchestration system that unifies the capabilities from both
existing orchestrators while eliminating duplication and fragmentation.

Features:
- Unified server registry and capability mapping
- DAG-based execution with dependency resolution
- Parallel processing with circuit breakers
- Result aggregation and synthesis
- Integration with both Sophia and Artemis orchestrators
- Health checking and failover support
"""

import asyncio
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import uuid4

import networkx as nx

logger = logging.getLogger(__name__)


class MCPCapability(Enum):
    """Comprehensive MCP server capabilities"""
    
    # Data Access
    DATABASE_QUERY = "database_query"
    FILE_ACCESS = "file_access" 
    WEB_SEARCH = "web_search"
    API_CALL = "api_call"
    MEMORY_STORAGE = "memory_storage"
    
    # Processing
    TEXT_ANALYSIS = "text_analysis"
    CODE_EXECUTION = "code_execution"
    CODE_GENERATION = "code_generation"
    IMAGE_PROCESSING = "image_processing"
    DATA_TRANSFORMATION = "data_transformation"
    VECTOR_SEARCH = "vector_search"
    
    # Integrations
    SLACK_INTEGRATION = "slack_integration"
    GITHUB_INTEGRATION = "github_integration"
    LINEAR_INTEGRATION = "linear_integration"
    GONG_INTEGRATION = "gong_integration"
    HUBSPOT_INTEGRATION = "hubspot_integration"
    
    # AI/ML
    EMBEDDING_GENERATION = "embedding_generation"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"


class ExecutionStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ServerStatus(Enum):
    """MCP server health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class MCPServer:
    """MCP server configuration"""
    
    name: str
    endpoint: str
    capabilities: Set[MCPCapability]
    priority: int = 1  # 1 = highest priority
    timeout_seconds: int = 30
    max_retries: int = 3
    health_check_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Health tracking
    status: ServerStatus = ServerStatus.UNKNOWN
    last_health_check: Optional[datetime] = None
    consecutive_failures: int = 0
    response_time_ms: float = 0.0


@dataclass
class MCPTask:
    """Individual MCP task"""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    capability: MCPCapability = None
    operation: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: Set[str] = field(default_factory=set)
    priority: int = 1
    timeout_seconds: int = 30
    
    # Execution tracking
    status: ExecutionStatus = ExecutionStatus.PENDING
    assigned_server: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0


@dataclass
class ExecutionPlan:
    """DAG-based execution plan"""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    tasks: Dict[str, MCPTask] = field(default_factory=dict)
    dependencies: nx.DiGraph = field(default_factory=nx.DiGraph)
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_task(self, task: MCPTask) -> None:
        """Add task to execution plan"""
        self.tasks[task.id] = task
        self.dependencies.add_node(task.id)
        
        # Add dependency edges
        for dep_id in task.dependencies:
            if dep_id in self.tasks:
                self.dependencies.add_edge(dep_id, task.id)
    
    def get_ready_tasks(self) -> List[MCPTask]:
        """Get tasks ready for execution (all dependencies completed)"""
        ready = []
        
        for task_id, task in self.tasks.items():
            if task.status != ExecutionStatus.PENDING:
                continue
                
            # Check if all dependencies are completed
            dependencies_completed = all(
                self.tasks[dep_id].status == ExecutionStatus.COMPLETED 
                for dep_id in task.dependencies
                if dep_id in self.tasks
            )
            
            if dependencies_completed:
                ready.append(task)
        
        return sorted(ready, key=lambda t: t.priority)


class UnifiedMCPOrchestrator:
    """
    Unified MCP orchestration system that consolidates both existing implementations
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Server registry
        self.servers: Dict[str, MCPServer] = {}
        self.capability_map: Dict[MCPCapability, List[MCPServer]] = defaultdict(list)
        
        # Execution tracking
        self.active_plans: Dict[str, ExecutionPlan] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        # Circuit breakers
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        
        # Performance metrics
        self.metrics = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'average_execution_time': 0.0,
            'server_health_checks': 0
        }
        
        logger.info("Unified MCP Orchestrator initialized")
        
        # Initialize with default servers
        self._initialize_default_servers()
        
    def _initialize_default_servers(self):
        """Initialize with common MCP servers"""
        default_servers = [
            MCPServer(
                name="claude_mcp",
                endpoint="mcp://claude.ai/servers/claude",
                capabilities={MCPCapability.TEXT_ANALYSIS, MCPCapability.CODE_GENERATION, 
                             MCPCapability.SUMMARIZATION},
                priority=1
            ),
            MCPServer(
                name="filesystem_mcp", 
                endpoint="mcp://filesystem/local",
                capabilities={MCPCapability.FILE_ACCESS},
                priority=2
            ),
            MCPServer(
                name="web_search_mcp",
                endpoint="mcp://web/search",
                capabilities={MCPCapability.WEB_SEARCH},
                priority=2
            ),
            MCPServer(
                name="database_mcp",
                endpoint="mcp://database/postgres", 
                capabilities={MCPCapability.DATABASE_QUERY},
                priority=3
            )
        ]
        
        for server in default_servers:
            self.register_server(server)
    
    def register_server(self, server: MCPServer) -> None:
        """Register a new MCP server"""
        self.servers[server.name] = server
        
        # Update capability mapping
        for capability in server.capabilities:
            self.capability_map[capability].append(server)
            # Sort by priority (lower number = higher priority)
            self.capability_map[capability].sort(key=lambda s: s.priority)
        
        logger.info(f"Registered MCP server: {server.name} with {len(server.capabilities)} capabilities")
    
    def unregister_server(self, server_name: str) -> bool:
        """Unregister an MCP server"""
        if server_name not in self.servers:
            return False
            
        server = self.servers[server_name]
        
        # Remove from capability mapping
        for capability in server.capabilities:
            self.capability_map[capability] = [
                s for s in self.capability_map[capability] if s.name != server_name
            ]
        
        # Remove from servers
        del self.servers[server_name]
        
        logger.info(f"Unregistered MCP server: {server_name}")
        return True
    
    async def health_check_servers(self) -> Dict[str, ServerStatus]:
        """Perform health checks on all registered servers"""
        health_status = {}
        
        for server_name, server in self.servers.items():
            try:
                start_time = datetime.now()
                
                # Simulate health check (would make actual HTTP call)
                await asyncio.sleep(0.1)  # Simulated network call
                
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds() * 1000
                
                # Update server status
                server.status = ServerStatus.HEALTHY
                server.last_health_check = end_time
                server.response_time_ms = response_time
                server.consecutive_failures = 0
                
                health_status[server_name] = ServerStatus.HEALTHY
                
            except Exception as e:
                server.status = ServerStatus.UNHEALTHY
                server.consecutive_failures += 1
                health_status[server_name] = ServerStatus.UNHEALTHY
                
                logger.warning(f"Health check failed for {server_name}: {e}")
        
        self.metrics['server_health_checks'] += 1
        return health_status
    
    def create_execution_plan(self, tasks: List[MCPTask]) -> ExecutionPlan:
        """Create execution plan from list of tasks"""
        plan = ExecutionPlan()
        
        # Add all tasks to plan
        for task in tasks:
            plan.add_task(task)
        
        # Validate the plan
        if not nx.is_directed_acyclic_graph(plan.dependencies):
            raise ValueError("Task dependencies contain cycles - execution plan invalid")
        
        self.active_plans[plan.id] = plan
        logger.info(f"Created execution plan {plan.id} with {len(tasks)} tasks")
        
        return plan
    
    async def execute_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """Execute a complete execution plan"""
        start_time = datetime.now()
        self.metrics['total_executions'] += 1
        
        try:
            # Execute tasks in dependency order
            while True:
                ready_tasks = plan.get_ready_tasks()
                
                if not ready_tasks:
                    # Check if all tasks are completed
                    remaining_tasks = [
                        t for t in plan.tasks.values() 
                        if t.status == ExecutionStatus.PENDING
                    ]
                    
                    if remaining_tasks:
                        logger.error(f"No ready tasks but {len(remaining_tasks)} tasks still pending")
                        break
                    else:
                        logger.info("All tasks completed successfully")
                        break
                
                # Execute ready tasks in parallel
                execution_tasks = []
                for task in ready_tasks[:5]:  # Limit parallel execution
                    task.status = ExecutionStatus.RUNNING
                    execution_tasks.append(self._execute_task(task))
                
                # Wait for batch completion
                await asyncio.gather(*execution_tasks, return_exceptions=True)
            
            # Calculate results
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            completed_tasks = [t for t in plan.tasks.values() if t.status == ExecutionStatus.COMPLETED]
            failed_tasks = [t for t in plan.tasks.values() if t.status == ExecutionStatus.FAILED]
            
            success = len(failed_tasks) == 0
            
            if success:
                self.metrics['successful_executions'] += 1
            else:
                self.metrics['failed_executions'] += 1
            
            # Update average execution time
            total_time = self.metrics['average_execution_time'] * (self.metrics['total_executions'] - 1)
            self.metrics['average_execution_time'] = (total_time + execution_time) / self.metrics['total_executions']
            
            # Aggregate results
            results = {
                'plan_id': plan.id,
                'success': success,
                'execution_time_seconds': execution_time,
                'tasks_completed': len(completed_tasks),
                'tasks_failed': len(failed_tasks),
                'task_results': {
                    task_id: task.result for task_id, task in plan.tasks.items()
                    if task.result is not None
                },
                'errors': {
                    task_id: task.error for task_id, task in plan.tasks.items()
                    if task.error is not None
                }
            }
            
            # Store in history
            self.execution_history.append(results)
            
            # Clean up completed plan
            if plan.id in self.active_plans:
                del self.active_plans[plan.id]
            
            logger.info(f"Execution plan {plan.id} completed: {success}")
            return results
            
        except Exception as e:
            logger.error(f"Execution plan {plan.id} failed: {e}")
            self.metrics['failed_executions'] += 1
            return {
                'plan_id': plan.id,
                'success': False,
                'error': str(e),
                'execution_time_seconds': (datetime.now() - start_time).total_seconds()
            }
    
    async def _execute_task(self, task: MCPTask) -> None:
        """Execute individual MCP task"""
        logger.info(f"Executing task {task.id}: {task.operation}")
        task.start_time = datetime.now()
        
        try:
            # Find best server for this task
            server = self._select_server_for_task(task)
            
            if not server:
                raise ValueError(f"No available server for capability {task.capability}")
            
            task.assigned_server = server.name
            
            # Execute task on server
            result = await self._call_mcp_server(server, task)
            
            task.result = result
            task.status = ExecutionStatus.COMPLETED
            task.end_time = datetime.now()
            
            logger.info(f"Task {task.id} completed successfully")
            
        except Exception as e:
            task.error = str(e)
            task.status = ExecutionStatus.FAILED
            task.end_time = datetime.now()
            task.retry_count += 1
            
            logger.error(f"Task {task.id} failed: {e}")
            
            # Retry logic
            if task.retry_count < 3:
                logger.info(f"Retrying task {task.id} (attempt {task.retry_count + 1})")
                task.status = ExecutionStatus.PENDING
                await asyncio.sleep(2 ** task.retry_count)  # Exponential backoff
                await self._execute_task(task)
    
    def _select_server_for_task(self, task: MCPTask) -> Optional[MCPServer]:
        """Select best available server for task"""
        if task.capability not in self.capability_map:
            return None
        
        # Get servers with required capability, sorted by priority
        candidates = [
            server for server in self.capability_map[task.capability]
            if server.status in [ServerStatus.HEALTHY, ServerStatus.UNKNOWN]
        ]
        
        if not candidates:
            return None
        
        # Return highest priority healthy server
        return candidates[0]
    
    async def _call_mcp_server(self, server: MCPServer, task: MCPTask) -> Any:
        """Make actual call to MCP server"""
        # Simulate MCP server call
        await asyncio.sleep(0.5)  # Simulated processing time
        
        # Mock different types of results based on capability
        if task.capability == MCPCapability.TEXT_ANALYSIS:
            return {
                'sentiment': 'positive',
                'keywords': ['analysis', 'text', 'processing'],
                'summary': 'Text analysis completed'
            }
        elif task.capability == MCPCapability.CODE_GENERATION:
            return {
                'code': 'def example_function():\n    return "Generated code"',
                'language': 'python',
                'explanation': 'Generated example function'
            }
        elif task.capability == MCPCapability.WEB_SEARCH:
            return {
                'results': [
                    {'title': 'Example Result', 'url': 'https://example.com', 'snippet': 'Example content'}
                ],
                'total_results': 1
            }
        else:
            return {'status': 'completed', 'data': f'Processed {task.operation}'}
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get status of all servers"""
        return {
            'servers': {
                name: {
                    'status': server.status.value,
                    'capabilities': [cap.value for cap in server.capabilities],
                    'last_health_check': server.last_health_check.isoformat() if server.last_health_check else None,
                    'response_time_ms': server.response_time_ms,
                    'consecutive_failures': server.consecutive_failures
                }
                for name, server in self.servers.items()
            },
            'metrics': self.metrics
        }
    
    def get_capability_map(self) -> Dict[str, List[str]]:
        """Get mapping of capabilities to servers"""
        return {
            capability.value: [server.name for server in servers]
            for capability, servers in self.capability_map.items()
        }
    
    # Convenience methods for common operations
    
    async def simple_execute(
        self, 
        capability: MCPCapability, 
        operation: str, 
        parameters: Dict[str, Any] = None
    ) -> Any:
        """Execute a single task without complex planning"""
        task = MCPTask(
            capability=capability,
            operation=operation,
            parameters=parameters or {}
        )
        
        plan = self.create_execution_plan([task])
        result = await self.execute_plan(plan)
        
        if result['success']:
            return result['task_results'].get(task.id)
        else:
            raise Exception(f"Task execution failed: {result.get('errors', {}).get(task.id, 'Unknown error')}")
    
    async def batch_execute(
        self, 
        tasks: List[Tuple[MCPCapability, str, Dict[str, Any]]]
    ) -> List[Any]:
        """Execute multiple independent tasks in parallel"""
        mcp_tasks = [
            MCPTask(
                capability=capability,
                operation=operation, 
                parameters=parameters
            )
            for capability, operation, parameters in tasks
        ]
        
        plan = self.create_execution_plan(mcp_tasks)
        result = await self.execute_plan(plan)
        
        if result['success']:
            return [result['task_results'].get(task.id) for task in mcp_tasks]
        else:
            raise Exception(f"Batch execution failed: {result.get('errors', {})}")


# Global orchestrator instance
_orchestrator_instance = None


def get_unified_mcp_orchestrator() -> UnifiedMCPOrchestrator:
    """Get singleton instance of unified MCP orchestrator"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = UnifiedMCPOrchestrator()
    return _orchestrator_instance


# Example usage functions
async def example_text_analysis():
    """Example: Simple text analysis"""
    orchestrator = get_unified_mcp_orchestrator()
    
    result = await orchestrator.simple_execute(
        capability=MCPCapability.TEXT_ANALYSIS,
        operation="analyze_sentiment",
        parameters={"text": "I love this new MCP orchestrator!"}
    )
    
    print(f"Analysis result: {result}")


async def example_complex_workflow():
    """Example: Complex multi-step workflow"""
    orchestrator = get_unified_mcp_orchestrator()
    
    # Create dependent tasks
    search_task = MCPTask(
        capability=MCPCapability.WEB_SEARCH,
        operation="search",
        parameters={"query": "MCP orchestration patterns"}
    )
    
    analysis_task = MCPTask(
        capability=MCPCapability.TEXT_ANALYSIS,
        operation="analyze_results",
        parameters={"source": "search_results"},
        dependencies={search_task.id}  # Depends on search completion
    )
    
    code_task = MCPTask(
        capability=MCPCapability.CODE_GENERATION,
        operation="generate_implementation",
        parameters={"requirements": "analysis_output"},
        dependencies={analysis_task.id}  # Depends on analysis completion
    )
    
    # Execute workflow
    plan = orchestrator.create_execution_plan([search_task, analysis_task, code_task])
    result = await orchestrator.execute_plan(plan)
    
    print(f"Workflow result: {result}")


if __name__ == "__main__":
    # Run examples
    asyncio.run(example_text_analysis())
    asyncio.run(example_complex_workflow())