"""
MCP Server Orchestration System
================================

Intelligent orchestration of MCP (Model Context Protocol) servers with
capability mapping, DAG-based execution, and result aggregation.

AI Context:
- Dynamic capability discovery and mapping
- Dependency-aware task execution
- Parallel execution optimization
- Result aggregation and synthesis
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import networkx as nx

logger = logging.getLogger(__name__)


class MCPCapability(Enum):
    """Standard MCP server capabilities"""

    # Data capabilities
    DATABASE_QUERY = "database_query"
    FILE_ACCESS = "file_access"
    WEB_SEARCH = "web_search"
    API_CALL = "api_call"

    # Processing capabilities
    TEXT_ANALYSIS = "text_analysis"
    CODE_EXECUTION = "code_execution"
    IMAGE_PROCESSING = "image_processing"
    DATA_TRANSFORMATION = "data_transformation"

    # Integration capabilities
    SLACK_INTEGRATION = "slack_integration"
    GITHUB_INTEGRATION = "github_integration"
    JIRA_INTEGRATION = "jira_integration"
    EMAIL_INTEGRATION = "email_integration"

    # Specialized capabilities
    MEMORY_STORAGE = "memory_storage"
    VECTOR_SEARCH = "vector_search"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    WORKFLOW_AUTOMATION = "workflow_automation"


class ExecutionStrategy(Enum):
    """Execution strategies for MCP tasks"""

    SEQUENTIAL = "sequential"  # Execute one by one
    PARALLEL = "parallel"  # Execute all at once
    DAG_BASED = "dag_based"  # Execute based on dependencies
    PRIORITY_BASED = "priority_based"  # Execute by priority
    ADAPTIVE = "adaptive"  # Dynamically adjust strategy


@dataclass
class MCPServer:
    """MCP server definition"""

    name: str
    endpoint: str
    capabilities: set[MCPCapability]
    version: str
    status: str = "active"
    metadata: dict[str, Any] = field(default_factory=dict)
    performance_metrics: dict[str, float] = field(default_factory=dict)

    def supports(self, capability: MCPCapability) -> bool:
        """Check if server supports a capability"""
        return capability in self.capabilities

    def get_health_score(self) -> float:
        """Calculate server health score"""
        if self.status != "active":
            return 0.0

        # Based on performance metrics
        if self.performance_metrics:
            success_rate = self.performance_metrics.get("success_rate", 0.5)
            avg_latency = self.performance_metrics.get("avg_latency_ms", 1000)

            # Normalize latency (lower is better)
            latency_score = max(0, 1 - (avg_latency / 5000))

            return (success_rate + latency_score) / 2

        return 0.5  # Default neutral score


@dataclass
class MCPTask:
    """Task to be executed on MCP server"""

    id: str
    capability: MCPCapability
    operation: str
    parameters: dict[str, Any]
    dependencies: list[str] = field(default_factory=list)
    priority: int = 5  # 1-10, higher is more important
    timeout_s: int = 60
    retry_count: int = 3
    result: Optional[Any] = None
    status: str = "pending"
    error: Optional[str] = None


@dataclass
class ExecutionPlan:
    """Execution plan for multiple MCP tasks"""

    tasks: list[MCPTask]
    strategy: ExecutionStrategy
    dag: Optional[nx.DiGraph] = None
    server_assignments: dict[str, str] = field(default_factory=dict)
    estimated_duration_s: float = 0
    parallelism_level: int = 1

    def get_execution_order(self) -> list[list[MCPTask]]:
        """Get tasks organized by execution order"""
        if self.strategy == ExecutionStrategy.DAG_BASED and self.dag:
            # Topological sort for dependency order
            try:
                sorted_ids = list(nx.topological_sort(self.dag))

                # Group by level for parallel execution
                levels = []
                seen = set()

                for task_id in sorted_ids:
                    if task_id not in seen:
                        # Find all tasks at this level (no unsatisfied deps)
                        level = []
                        for tid in sorted_ids:
                            if tid not in seen:
                                task = next((t for t in self.tasks if t.id == tid), None)
                                if task and all(dep in seen for dep in task.dependencies):
                                    level.append(task)
                                    seen.add(tid)
                        if level:
                            levels.append(level)

                return levels

            except nx.NetworkXError:
                logger.error("Cyclic dependency detected in task DAG")
                return [[task] for task in self.tasks]

        elif self.strategy == ExecutionStrategy.PARALLEL:
            return [self.tasks]  # All at once

        elif self.strategy == ExecutionStrategy.PRIORITY_BASED:
            sorted_tasks = sorted(self.tasks, key=lambda t: t.priority, reverse=True)
            return [[task] for task in sorted_tasks]

        else:  # Sequential
            return [[task] for task in self.tasks]


class CapabilityMapper:
    """Maps capabilities to available MCP servers"""

    def __init__(self):
        self.servers: dict[str, MCPServer] = {}
        self.capability_index: dict[MCPCapability, list[str]] = {}

    def register_server(self, server: MCPServer) -> None:
        """Register an MCP server"""
        self.servers[server.name] = server

        # Update capability index
        for capability in server.capabilities:
            if capability not in self.capability_index:
                self.capability_index[capability] = []
            self.capability_index[capability].append(server.name)

        logger.info(
            f"Registered MCP server: {server.name} with {len(server.capabilities)} capabilities"
        )

    def unregister_server(self, server_name: str) -> None:
        """Unregister an MCP server"""
        if server_name in self.servers:
            server = self.servers[server_name]

            # Remove from capability index
            for capability in server.capabilities:
                if capability in self.capability_index:
                    self.capability_index[capability].remove(server_name)

            del self.servers[server_name]
            logger.info(f"Unregistered MCP server: {server_name}")

    def find_servers(self, capability: MCPCapability, min_health: float = 0.3) -> list[MCPServer]:
        """Find servers that support a capability"""
        servers = []

        if capability in self.capability_index:
            for server_name in self.capability_index[capability]:
                server = self.servers.get(server_name)
                if server and server.get_health_score() >= min_health:
                    servers.append(server)

        # Sort by health score
        return sorted(servers, key=lambda s: s.get_health_score(), reverse=True)

    def get_best_server(self, capability: MCPCapability) -> Optional[MCPServer]:
        """Get the best server for a capability"""
        servers = self.find_servers(capability)
        return servers[0] if servers else None


class ExecutionPlanner:
    """Plans execution of MCP tasks"""

    def __init__(self, mapper: CapabilityMapper):
        self.mapper = mapper

    def create_plan(
        self,
        tasks: list[MCPTask],
        strategy: ExecutionStrategy = ExecutionStrategy.ADAPTIVE,
    ) -> ExecutionPlan:
        """Create execution plan for tasks"""

        # Assign servers to tasks
        server_assignments = {}
        for task in tasks:
            server = self.mapper.get_best_server(task.capability)
            if server:
                server_assignments[task.id] = server.name
            else:
                logger.warning(f"No server available for capability: {task.capability}")

        # Determine actual strategy
        if strategy == ExecutionStrategy.ADAPTIVE:
            strategy = self._determine_optimal_strategy(tasks)

        # Build DAG if needed
        dag = None
        if strategy == ExecutionStrategy.DAG_BASED:
            dag = self._build_dag(tasks)

        # Estimate duration
        estimated_duration = self._estimate_duration(tasks, strategy, server_assignments)

        # Determine parallelism level
        parallelism = self._calculate_parallelism(tasks, strategy)

        return ExecutionPlan(
            tasks=tasks,
            strategy=strategy,
            dag=dag,
            server_assignments=server_assignments,
            estimated_duration_s=estimated_duration,
            parallelism_level=parallelism,
        )

    def _determine_optimal_strategy(self, tasks: list[MCPTask]) -> ExecutionStrategy:
        """Determine optimal execution strategy"""

        # Check for dependencies
        has_deps = any(task.dependencies for task in tasks)

        if has_deps:
            # Check for complex dependencies
            dep_count = sum(len(task.dependencies) for task in tasks)
            if dep_count > len(tasks) * 0.5:
                return ExecutionStrategy.DAG_BASED

        # Check task count
        if len(tasks) <= 3:
            return ExecutionStrategy.SEQUENTIAL
        elif len(tasks) > 10:
            return ExecutionStrategy.PARALLEL

        # Check priorities
        priorities = [task.priority for task in tasks]
        if max(priorities) - min(priorities) > 5:
            return ExecutionStrategy.PRIORITY_BASED

        return ExecutionStrategy.PARALLEL

    def _build_dag(self, tasks: list[MCPTask]) -> nx.DiGraph:
        """Build directed acyclic graph from tasks"""
        dag = nx.DiGraph()

        # Add nodes
        for task in tasks:
            dag.add_node(task.id, task=task)

        # Add edges based on dependencies
        for task in tasks:
            for dep in task.dependencies:
                if dep in [t.id for t in tasks]:
                    dag.add_edge(dep, task.id)

        return dag

    def _estimate_duration(
        self,
        tasks: list[MCPTask],
        strategy: ExecutionStrategy,
        assignments: dict[str, str],
    ) -> float:
        """Estimate execution duration"""

        if not tasks:
            return 0

        # Base duration from timeouts
        task_durations = [task.timeout_s for task in tasks]

        if strategy == ExecutionStrategy.SEQUENTIAL:
            return sum(task_durations)
        elif strategy == ExecutionStrategy.PARALLEL:
            return max(task_durations)
        elif strategy == ExecutionStrategy.DAG_BASED:
            # Simplified: longest path through DAG
            return sum(task_durations) * 0.6  # Assume some parallelism
        else:
            return sum(task_durations) * 0.7

    def _calculate_parallelism(self, tasks: list[MCPTask], strategy: ExecutionStrategy) -> int:
        """Calculate optimal parallelism level"""

        if strategy == ExecutionStrategy.SEQUENTIAL:
            return 1
        elif strategy == ExecutionStrategy.PARALLEL:
            return min(len(tasks), 10)  # Cap at 10
        else:
            return min(len(tasks) // 2 + 1, 5)  # Moderate parallelism


class ResultAggregator:
    """Aggregates results from multiple MCP tasks"""

    def __init__(self):
        self.aggregation_strategies = {
            "merge": self._merge_results,
            "chain": self._chain_results,
            "select_best": self._select_best_result,
            "consensus": self._consensus_result,
            "transform": self._transform_results,
        }

    def aggregate(
        self,
        results: list[tuple[MCPTask, Any]],
        strategy: str = "merge",
        options: dict[str, Any] = None,
    ) -> Any:
        """Aggregate results using specified strategy"""

        options = options or {}

        if strategy in self.aggregation_strategies:
            return self.aggregation_strategies[strategy](results, options)
        else:
            logger.warning(f"Unknown aggregation strategy: {strategy}")
            return self._merge_results(results, options)

    def _merge_results(
        self, results: list[tuple[MCPTask, Any]], options: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge all results into a dictionary"""
        merged = {}

        for task, result in results:
            key = options.get("key_prefix", "") + task.id
            merged[key] = {
                "task_id": task.id,
                "capability": task.capability.value,
                "result": result,
                "status": task.status,
            }

        return merged

    def _chain_results(self, results: list[tuple[MCPTask, Any]], options: dict[str, Any]) -> Any:
        """Chain results (output of one is input to next)"""
        if not results:
            return None

        # Sort by task dependencies
        sorted_results = sorted(
            results,
            key=lambda r: len(r[0].dependencies),
        )

        # Return the last result in the chain
        return sorted_results[-1][1] if sorted_results else None

    def _select_best_result(
        self, results: list[tuple[MCPTask, Any]], options: dict[str, Any]
    ) -> Any:
        """Select best result based on criteria"""
        if not results:
            return None

        # Filter successful results
        successful = [
            (task, result)
            for task, result in results
            if task.status == "completed" and result is not None
        ]

        if not successful:
            return None

        # Select based on priority
        best = max(successful, key=lambda r: r[0].priority)
        return best[1]

    def _consensus_result(self, results: list[tuple[MCPTask, Any]], options: dict[str, Any]) -> Any:
        """Find consensus among results"""
        if not results:
            return None

        # For now, return most common result
        from collections import Counter

        result_values = [str(result) for _, result in results if result is not None]
        if result_values:
            consensus = Counter(result_values).most_common(1)[0][0]
            # Find original result object
            for _, result in results:
                if str(result) == consensus:
                    return result

        return None

    def _transform_results(
        self, results: list[tuple[MCPTask, Any]], options: dict[str, Any]
    ) -> Any:
        """Transform results using custom function"""
        transform_fn = options.get("transform_fn")

        if transform_fn and callable(transform_fn):
            return transform_fn(results)
        else:
            return self._merge_results(results, options)


class MCPOrchestrator:
    """Main orchestrator for MCP servers"""

    def __init__(self):
        self.mapper = CapabilityMapper()
        self.planner = ExecutionPlanner(self.mapper)
        self.aggregator = ResultAggregator()
        self.execution_history: list[dict[str, Any]] = []
        self._initialize_default_servers()

    def _initialize_default_servers(self) -> None:
        """Initialize default MCP servers"""

        # File system server
        self.mapper.register_server(
            MCPServer(
                name="filesystem",
                endpoint="mcp://localhost:3000/fs",
                capabilities={
                    MCPCapability.FILE_ACCESS,
                    MCPCapability.DATA_TRANSFORMATION,
                },
                version="1.0.0",
            )
        )

        # Database server
        self.mapper.register_server(
            MCPServer(
                name="database",
                endpoint="mcp://localhost:3001/db",
                capabilities={
                    MCPCapability.DATABASE_QUERY,
                    MCPCapability.DATA_TRANSFORMATION,
                },
                version="1.0.0",
            )
        )

        # Web server
        self.mapper.register_server(
            MCPServer(
                name="web",
                endpoint="mcp://localhost:3002/web",
                capabilities={
                    MCPCapability.WEB_SEARCH,
                    MCPCapability.API_CALL,
                },
                version="1.0.0",
            )
        )

        # GitHub server
        self.mapper.register_server(
            MCPServer(
                name="github",
                endpoint="mcp://localhost:3003/github",
                capabilities={
                    MCPCapability.GITHUB_INTEGRATION,
                    MCPCapability.CODE_EXECUTION,
                },
                version="1.0.0",
            )
        )

        logger.info("Initialized default MCP servers")

    async def execute_task(self, task: MCPTask) -> Any:
        """Execute a single MCP task"""

        # Find server
        server_name = task.id  # Would be from plan
        server = self.mapper.servers.get(server_name)

        if not server:
            server = self.mapper.get_best_server(task.capability)

        if not server:
            task.status = "failed"
            task.error = f"No server available for {task.capability}"
            return None

        # Execute on server
        try:
            # This would make actual MCP call
            # For now, mock execution
            await asyncio.sleep(0.1)  # Simulate network call

            result = {
                "task_id": task.id,
                "server": server.name,
                "result": f"Executed {task.operation}",
                "timestamp": datetime.now().isoformat(),
            }

            task.status = "completed"
            task.result = result

            # Update server metrics
            server.performance_metrics["success_rate"] = server.performance_metrics.get(
                "success_rate", 0.9
            )

            return result

        except Exception as e:
            task.status = "failed"
            task.error = str(e)

            # Update server metrics
            server.performance_metrics["success_rate"] = (
                server.performance_metrics.get("success_rate", 0.5) * 0.9
            )

            # Retry logic
            if task.retry_count > 0:
                task.retry_count -= 1
                task.status = "pending"
                return await self.execute_task(task)

            return None

    async def execute_plan(self, plan: ExecutionPlan, max_workers: int = 5) -> dict[str, Any]:
        """Execute an execution plan"""

        start_time = datetime.now()
        results = []

        # Get execution order
        levels = plan.get_execution_order()

        for level in levels:
            # Execute tasks in level (parallel within level)
            if len(level) == 1:
                # Single task
                result = await self.execute_task(level[0])
                results.append((level[0], result))
            else:
                # Multiple tasks - execute in parallel
                tasks_to_execute = level[:max_workers]

                coroutines = [self.execute_task(task) for task in tasks_to_execute]
                level_results = await asyncio.gather(*coroutines, return_exceptions=True)

                for task, result in zip(tasks_to_execute, level_results):
                    if isinstance(result, Exception):
                        task.status = "failed"
                        task.error = str(result)
                        results.append((task, None))
                    else:
                        results.append((task, result))

        # Record execution
        execution_time = (datetime.now() - start_time).total_seconds()

        execution_record = {
            "plan_id": id(plan),
            "strategy": plan.strategy.value,
            "task_count": len(plan.tasks),
            "execution_time_s": execution_time,
            "success_rate": sum(1 for t in plan.tasks if t.status == "completed") / len(plan.tasks),
            "timestamp": start_time.isoformat(),
        }

        self.execution_history.append(execution_record)

        return {
            "results": results,
            "execution_time": execution_time,
            "success_rate": execution_record["success_rate"],
        }

    async def orchestrate(
        self,
        tasks: list[MCPTask],
        strategy: ExecutionStrategy = ExecutionStrategy.ADAPTIVE,
        aggregation: str = "merge",
        aggregation_options: dict[str, Any] = None,
    ) -> Any:
        """
        Orchestrate execution of multiple MCP tasks

        Args:
            tasks: List of tasks to execute
            strategy: Execution strategy
            aggregation: Result aggregation strategy
            aggregation_options: Options for aggregation

        Returns:
            Aggregated results
        """

        # Create execution plan
        plan = self.planner.create_plan(tasks, strategy)

        logger.info(
            f"Created execution plan: {len(tasks)} tasks, "
            f"strategy: {strategy.value}, "
            f"estimated duration: {plan.estimated_duration_s:.1f}s"
        )

        # Execute plan
        execution_result = await self.execute_plan(plan)

        # Aggregate results
        aggregated = self.aggregator.aggregate(
            execution_result["results"],
            aggregation,
            aggregation_options,
        )

        logger.info(
            f"Execution complete: {execution_result['execution_time']:.2f}s, "
            f"success rate: {execution_result['success_rate']:.1%}"
        )

        return aggregated

    def get_capabilities(self) -> list[MCPCapability]:
        """Get all available capabilities"""
        return list(self.mapper.capability_index.keys())

    def get_server_status(self) -> dict[str, Any]:
        """Get status of all servers"""
        return {
            name: {
                "status": server.status,
                "health": server.get_health_score(),
                "capabilities": [c.value for c in server.capabilities],
                "metrics": server.performance_metrics,
            }
            for name, server in self.mapper.servers.items()
        }


# Global orchestrator instance
_orchestrator = None


def get_mcp_orchestrator() -> MCPOrchestrator:
    """Get or create the global MCP orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MCPOrchestrator()
    return _orchestrator
