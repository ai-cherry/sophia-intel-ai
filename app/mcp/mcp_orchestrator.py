"""
MCP Orchestrator with DAG-based Execution
=========================================

Advanced Model Context Protocol orchestration system with dependency-aware execution,
parallel processing, and intelligent result aggregation.

Features:
- DAG-based execution planning
- MCP server capability mapping
- Parallel execution with dependencies
- Result aggregation and fusion
- Integration with orchestrators and personas

AI Context:
- Manages complex multi-step workflows
- Optimizes execution based on server capabilities
- Provides resilient error handling and retries
- Integrates with meta-tagging and embedding systems
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    TypeVar,
)
from uuid import uuid4

import networkx as nx

from app.memory.hierarchical_memory import (
    HierarchicalMemorySystem,
    MemoryEntry,
    QueryContext,
    QueryType,
)
from app.personas.persona_manager import PersonaType

# Import existing infrastructure
from app.scaffolding.meta_tagging import MetaTag

logger = logging.getLogger(__name__)

T = TypeVar("T")


class MCPServerType(Enum):
    """Types of MCP servers available"""

    FILESYSTEM = "filesystem"  # File operations
    DATABASE = "database"  # SQL operations
    WEB_SEARCH = "web_search"  # Internet search
    CODE_ANALYSIS = "code_analysis"  # Code intelligence
    KNOWLEDGE_BASE = "knowledge_base"  # RAG operations
    COMPUTATION = "computation"  # Mathematical operations
    INTEGRATION = "integration"  # API integrations
    MONITORING = "monitoring"  # System observability


class ExecutionStatus(Enum):
    """Status of DAG node execution"""

    PENDING = "pending"
    READY = "ready"  # Dependencies satisfied
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"  # Due to failed dependencies
    RETRYING = "retrying"


class NodeType(Enum):
    """Types of DAG nodes"""

    MCP_CALL = "mcp_call"  # Single MCP server call
    AGGREGATION = "aggregation"  # Combine multiple results
    TRANSFORMATION = "transformation"  # Data transformation
    CONDITIONAL = "conditional"  # Conditional execution
    PARALLEL_BATCH = "parallel_batch"  # Parallel execution group
    CACHE_CHECK = "cache_check"  # Memory system check


@dataclass
class MCPCapability:
    """MCP server capability definition"""

    server_type: MCPServerType
    server_url: str
    capabilities: List[str]
    max_concurrent: int = 5
    timeout_seconds: int = 30
    retry_count: int = 3
    health_check_url: Optional[str] = None
    authentication: Optional[Dict[str, str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DAGNode:
    """DAG execution node"""

    id: str
    node_type: NodeType
    name: str
    description: Optional[str] = None

    # MCP-specific fields
    server_type: Optional[MCPServerType] = None
    mcp_method: Optional[str] = None
    mcp_params: Dict[str, Any] = field(default_factory=dict)

    # Execution fields
    dependencies: Set[str] = field(default_factory=set)
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retry_count: int = 0

    # Metadata
    meta_tags: List[MetaTag] = field(default_factory=list)
    priority: int = 5  # 1 (high) to 10 (low)
    timeout_seconds: int = 30
    cache_key: Optional[str] = None


@dataclass
class ExecutionPlan:
    """DAG execution plan"""

    id: str
    name: str
    description: Optional[str] = None
    nodes: Dict[str, DAGNode] = field(default_factory=dict)
    execution_order: List[List[str]] = field(default_factory=list)  # Parallel levels
    created_at: datetime = field(default_factory=datetime.utcnow)
    persona_domain: PersonaType = PersonaType.SOPHIA
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result of DAG execution"""

    plan_id: str
    status: ExecutionStatus
    results: Dict[str, Any] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    nodes_executed: int = 0
    nodes_skipped: int = 0
    nodes_failed: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MCPServerRegistry:
    """Registry of available MCP servers"""

    def __init__(self):
        self.servers: Dict[MCPServerType, List[MCPCapability]] = defaultdict(list)
        self.server_health: Dict[str, bool] = {}
        self._initialize_default_servers()

    def _initialize_default_servers(self):
        """Initialize with default MCP servers"""
        default_servers = [
            MCPCapability(
                server_type=MCPServerType.FILESYSTEM,
                server_url="mcp://filesystem",
                capabilities=["read_file", "write_file", "list_directory", "search_files"],
                max_concurrent=10,
            ),
            MCPCapability(
                server_type=MCPServerType.DATABASE,
                server_url="mcp://database",
                capabilities=["query", "execute", "schema", "analyze"],
                max_concurrent=5,
            ),
            MCPCapability(
                server_type=MCPServerType.WEB_SEARCH,
                server_url="mcp://web_search",
                capabilities=["search", "scrape", "analyze_page"],
                max_concurrent=3,
                timeout_seconds=60,
            ),
            MCPCapability(
                server_type=MCPServerType.CODE_ANALYSIS,
                server_url="mcp://code_analysis",
                capabilities=[
                    "analyze_code",
                    "find_functions",
                    "dependency_graph",
                    "quality_check",
                ],
                max_concurrent=5,
            ),
        ]

        for server in default_servers:
            self.register_server(server)

    def register_server(self, capability: MCPCapability):
        """Register MCP server capability"""
        self.servers[capability.server_type].append(capability)
        self.server_health[capability.server_url] = True  # Assume healthy initially
        logger.info(
            f"Registered MCP server: {capability.server_type.value} at {capability.server_url}"
        )

    def get_servers(self, server_type: MCPServerType) -> List[MCPCapability]:
        """Get available servers for type"""
        return [s for s in self.servers[server_type] if self.server_health.get(s.server_url, False)]

    def get_server_for_capability(
        self, server_type: MCPServerType, method: str
    ) -> Optional[MCPCapability]:
        """Find best server for specific capability"""
        servers = self.get_servers(server_type)

        for server in servers:
            if method in server.capabilities:
                return server

        # Fallback to any server of the type
        return servers[0] if servers else None

    async def health_check(self, server_url: str) -> bool:
        """Check server health"""
        # Mock implementation - would make actual health check call
        try:
            # Simulate health check
            await asyncio.sleep(0.1)
            self.server_health[server_url] = True
            return True
        except Exception as e:
            logger.error(f"Health check failed for {server_url}: {e}")
            self.server_health[server_url] = False
            return False

    async def health_check_all(self):
        """Health check all registered servers"""
        tasks = [self.health_check(url) for url in self.server_health.keys()]
        await asyncio.gather(*tasks)


class DAGBuilder:
    """Builder for creating execution DAGs"""

    def __init__(self):
        self.nodes: Dict[str, DAGNode] = {}
        self.graph = nx.DiGraph()

    def add_mcp_node(
        self,
        node_id: str,
        name: str,
        server_type: MCPServerType,
        method: str,
        params: Dict[str, Any],
        dependencies: Optional[Set[str]] = None,
        **kwargs,
    ) -> "DAGBuilder":
        """Add MCP call node"""
        node = DAGNode(
            id=node_id,
            node_type=NodeType.MCP_CALL,
            name=name,
            server_type=server_type,
            mcp_method=method,
            mcp_params=params,
            dependencies=dependencies or set(),
            **kwargs,
        )

        self.nodes[node_id] = node
        self.graph.add_node(node_id)

        # Add edges for dependencies
        for dep in node.dependencies:
            self.graph.add_edge(dep, node_id)

        return self

    def add_aggregation_node(
        self,
        node_id: str,
        name: str,
        dependencies: Set[str],
        aggregation_function: str = "merge",
        **kwargs,
    ) -> "DAGBuilder":
        """Add result aggregation node"""
        node = DAGNode(
            id=node_id,
            node_type=NodeType.AGGREGATION,
            name=name,
            dependencies=dependencies,
            mcp_params={"function": aggregation_function},
            **kwargs,
        )

        self.nodes[node_id] = node
        self.graph.add_node(node_id)

        for dep in dependencies:
            self.graph.add_edge(dep, node_id)

        return self

    def add_conditional_node(
        self,
        node_id: str,
        name: str,
        condition: str,
        dependencies: Set[str],
        true_branch: List[str],
        false_branch: List[str] = None,
        **kwargs,
    ) -> "DAGBuilder":
        """Add conditional execution node"""
        node = DAGNode(
            id=node_id,
            node_type=NodeType.CONDITIONAL,
            name=name,
            dependencies=dependencies,
            mcp_params={
                "condition": condition,
                "true_branch": true_branch,
                "false_branch": false_branch or [],
            },
            **kwargs,
        )

        self.nodes[node_id] = node
        self.graph.add_node(node_id)

        for dep in dependencies:
            self.graph.add_edge(dep, node_id)

        return self

    def build(
        self, plan_id: str, name: str, persona_domain: PersonaType = PersonaType.SOPHIA
    ) -> ExecutionPlan:
        """Build execution plan"""
        # Validate DAG (no cycles)
        if not nx.is_directed_acyclic_graph(self.graph):
            raise ValueError("Execution plan contains cycles")

        # Generate topological execution order with parallel levels
        execution_order = []
        remaining_nodes = set(self.nodes.keys())

        while remaining_nodes:
            # Find nodes with no remaining dependencies
            ready_nodes = []
            for node_id in remaining_nodes:
                node = self.nodes[node_id]
                if not (node.dependencies & remaining_nodes):
                    ready_nodes.append(node_id)

            if not ready_nodes:
                raise ValueError("Circular dependency detected")

            execution_order.append(ready_nodes)
            remaining_nodes -= set(ready_nodes)

        return ExecutionPlan(
            id=plan_id,
            name=name,
            nodes=self.nodes.copy(),
            execution_order=execution_order,
            persona_domain=persona_domain,
        )


class MCPOrchestrator:
    """Main MCP orchestration engine"""

    def __init__(
        self,
        memory_system: Optional[HierarchicalMemorySystem] = None,
        max_concurrent_nodes: int = 10,
        default_timeout: int = 300,
    ):
        self.server_registry = MCPServerRegistry()
        self.memory_system = memory_system
        self.max_concurrent_nodes = max_concurrent_nodes
        self.default_timeout = default_timeout
        self.active_executions: Dict[str, ExecutionPlan] = {}
        self.execution_semaphore = asyncio.Semaphore(max_concurrent_nodes)

        # Metrics
        self.metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time_ms": 0.0,
            "cache_hit_ratio": 0.0,
            "server_call_counts": defaultdict(int),
        }

    async def execute_plan(self, plan: ExecutionPlan) -> ExecutionResult:
        """Execute DAG plan with parallel processing"""
        start_time = datetime.utcnow()
        self.metrics["total_executions"] += 1
        self.active_executions[plan.id] = plan

        result = ExecutionResult(
            plan_id=plan.id, status=ExecutionStatus.RUNNING, start_time=start_time
        )

        try:
            # Execute in topological order with parallelism
            for level_nodes in plan.execution_order:
                # Execute all nodes in this level in parallel
                tasks = []
                for node_id in level_nodes:
                    node = plan.nodes[node_id]
                    task = self._execute_node(node, plan, result)
                    tasks.append(task)

                # Wait for all nodes in this level to complete
                level_results = await asyncio.gather(*tasks, return_exceptions=True)

                # Check for failures
                for i, node_result in enumerate(level_results):
                    node_id = level_nodes[i]
                    node = plan.nodes[node_id]

                    if isinstance(node_result, Exception):
                        node.status = ExecutionStatus.FAILED
                        node.error = str(node_result)
                        result.errors[node_id] = str(node_result)
                        result.nodes_failed += 1

                        # Skip dependent nodes
                        await self._skip_dependent_nodes(node_id, plan)
                    else:
                        node.status = ExecutionStatus.COMPLETED
                        node.result = node_result
                        result.results[node_id] = node_result
                        result.nodes_executed += 1

            # Determine overall status
            if result.nodes_failed == 0:
                result.status = ExecutionStatus.COMPLETED
                self.metrics["successful_executions"] += 1
            else:
                result.status = ExecutionStatus.FAILED
                self.metrics["failed_executions"] += 1

        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.errors["orchestrator"] = str(e)
            self.metrics["failed_executions"] += 1
            logger.error(f"Plan execution failed: {e}")

        finally:
            end_time = datetime.utcnow()
            result.end_time = end_time
            result.execution_time_ms = (end_time - start_time).total_seconds() * 1000

            # Update metrics
            self._update_metrics(result)

            # Clean up
            if plan.id in self.active_executions:
                del self.active_executions[plan.id]

        return result

    async def _execute_node(
        self, node: DAGNode, plan: ExecutionPlan, result: ExecutionResult
    ) -> Any:
        """Execute individual DAG node"""
        async with self.execution_semaphore:
            node.start_time = datetime.utcnow()
            node.status = ExecutionStatus.RUNNING

            try:
                # Check cache first if cache key provided
                if node.cache_key and self.memory_system:
                    cached_result = await self._check_cache(node, plan)
                    if cached_result is not None:
                        result.cache_hits += 1
                        return cached_result

                result.cache_misses += 1

                # Execute based on node type
                if node.node_type == NodeType.MCP_CALL:
                    node_result = await self._execute_mcp_call(node, plan)
                elif node.node_type == NodeType.AGGREGATION:
                    node_result = await self._execute_aggregation(node, plan)
                elif node.node_type == NodeType.CONDITIONAL:
                    node_result = await self._execute_conditional(node, plan)
                elif node.node_type == NodeType.TRANSFORMATION:
                    node_result = await self._execute_transformation(node, plan)
                else:
                    raise ValueError(f"Unknown node type: {node.node_type}")

                # Cache result if cache key provided
                if node.cache_key and self.memory_system:
                    await self._cache_result(node, node_result, plan)

                node.end_time = datetime.utcnow()
                return node_result

            except Exception as e:
                node.end_time = datetime.utcnow()
                node.error = str(e)

                # Retry logic
                if node.retry_count < 3:
                    node.retry_count += 1
                    node.status = ExecutionStatus.RETRYING
                    logger.warning(f"Retrying node {node.id}, attempt {node.retry_count}")

                    # Exponential backoff
                    await asyncio.sleep(2**node.retry_count)
                    return await self._execute_node(node, plan, result)

                raise e

    async def _execute_mcp_call(self, node: DAGNode, plan: ExecutionPlan) -> Any:
        """Execute MCP server call"""
        server = self.server_registry.get_server_for_capability(node.server_type, node.mcp_method)

        if not server:
            raise ValueError(f"No server available for {node.server_type.value}:{node.mcp_method}")

        self.metrics["server_call_counts"][server.server_url] += 1

        # Mock MCP call - in reality, would use MCP protocol
        try:
            await asyncio.sleep(0.1)  # Simulate network call

            # Simulate different response types
            if node.mcp_method == "read_file":
                return {
                    "content": f"File content for {node.mcp_params.get('path', 'unknown')}",
                    "size": 1024,
                }
            elif node.mcp_method == "search":
                return {"results": [f"Search result {i}" for i in range(5)], "total": 5}
            elif node.mcp_method == "query":
                return {"rows": [{"id": i, "value": f"row_{i}"} for i in range(3)], "count": 3}
            else:
                return {"status": "success", "data": node.mcp_params}

        except asyncio.TimeoutError:
            raise ValueError(f"MCP call timeout for {node.mcp_method}")

    async def _execute_aggregation(self, node: DAGNode, plan: ExecutionPlan) -> Any:
        """Execute result aggregation"""
        aggregation_func = node.mcp_params.get("function", "merge")

        # Collect results from dependencies
        dependency_results = {}
        for dep_id in node.dependencies:
            dep_node = plan.nodes[dep_id]
            if dep_node.status == ExecutionStatus.COMPLETED:
                dependency_results[dep_id] = dep_node.result

        # Apply aggregation function
        if aggregation_func == "merge":
            merged = {}
            for dep_id, result in dependency_results.items():
                if isinstance(result, dict):
                    merged.update(result)
                else:
                    merged[dep_id] = result
            return merged

        elif aggregation_func == "list":
            return list(dependency_results.values())

        elif aggregation_func == "count":
            return len(dependency_results)

        elif aggregation_func == "sum":
            values = [r for r in dependency_results.values() if isinstance(r, (int, float))]
            return sum(values)

        else:
            return dependency_results

    async def _execute_conditional(self, node: DAGNode, plan: ExecutionPlan) -> Any:
        """Execute conditional logic"""
        condition = node.mcp_params.get("condition", "true")
        true_branch = node.mcp_params.get("true_branch", [])
        false_branch = node.mcp_params.get("false_branch", [])

        # Evaluate condition (simplified - could be more complex)
        condition_result = await self._evaluate_condition(condition, node, plan)

        selected_branch = true_branch if condition_result else false_branch

        return {
            "condition": condition,
            "condition_result": condition_result,
            "selected_branch": selected_branch,
            "executed": len(selected_branch) > 0,
        }

    async def _execute_transformation(self, node: DAGNode, plan: ExecutionPlan) -> Any:
        """Execute data transformation"""
        # Get input from dependencies
        inputs = {}
        for dep_id in node.dependencies:
            dep_node = plan.nodes[dep_id]
            if dep_node.status == ExecutionStatus.COMPLETED:
                inputs[dep_id] = dep_node.result

        # Apply transformation (mock implementation)
        transformation = node.mcp_params.get("transform", "identity")

        if transformation == "flatten":
            flattened = {}
            for input_data in inputs.values():
                if isinstance(input_data, dict):
                    flattened.update(input_data)
            return flattened

        elif transformation == "extract_keys":
            keys = node.mcp_params.get("keys", [])
            extracted = {}
            for input_data in inputs.values():
                if isinstance(input_data, dict):
                    for key in keys:
                        if key in input_data:
                            extracted[key] = input_data[key]
            return extracted

        else:
            return inputs

    async def _evaluate_condition(self, condition: str, node: DAGNode, plan: ExecutionPlan) -> bool:
        """Evaluate conditional expression"""
        # Simple condition evaluation - could be enhanced with expression parser
        if condition == "true":
            return True
        elif condition == "false":
            return False
        elif condition.startswith("has_result:"):
            dep_id = condition.split(":", 1)[1]
            dep_node = plan.nodes.get(dep_id)
            return dep_node and dep_node.status == ExecutionStatus.COMPLETED
        else:
            # Default to true for unknown conditions
            return True

    async def _skip_dependent_nodes(self, failed_node_id: str, plan: ExecutionPlan):
        """Skip nodes that depend on failed node"""
        # Use networkx to find all descendants
        if hasattr(self, "_plan_graph"):
            descendants = nx.descendants(self._plan_graph, failed_node_id)
            for desc_id in descendants:
                if desc_id in plan.nodes:
                    node = plan.nodes[desc_id]
                    node.status = ExecutionStatus.SKIPPED
                    node.error = f"Dependency {failed_node_id} failed"

    async def _check_cache(self, node: DAGNode, plan: ExecutionPlan) -> Optional[Any]:
        """Check memory system for cached result"""
        if not self.memory_system or not node.cache_key:
            return None

        context = QueryContext(
            query_type=QueryType.EXACT_MATCH,
            persona_domain=plan.persona_domain,
            priority=node.priority,
        )

        entry = await self.memory_system.get(node.cache_key, context)
        return entry.content if entry else None

    async def _cache_result(self, node: DAGNode, result: Any, plan: ExecutionPlan):
        """Cache node result in memory system"""
        if not self.memory_system or not node.cache_key:
            return

        context = QueryContext(
            query_type=QueryType.EXACT_MATCH,
            persona_domain=plan.persona_domain,
            priority=node.priority,
        )

        from app.memory.hierarchical_memory import AccessPattern

        entry = MemoryEntry(
            id=node.cache_key,
            content=result,
            tier=None,  # Will be determined by system
            persona_domain=plan.persona_domain,
            access_pattern=AccessPattern.WARM,
            meta_tags=node.meta_tags,
        )

        await self.memory_system.set(node.cache_key, entry, context)

    def _update_metrics(self, result: ExecutionResult):
        """Update orchestrator metrics"""
        # Update average execution time
        total_time = self.metrics["average_execution_time_ms"] * (
            self.metrics["total_executions"] - 1
        )
        self.metrics["average_execution_time_ms"] = (
            total_time + result.execution_time_ms
        ) / self.metrics["total_executions"]

        # Update cache hit ratio
        total_cache_ops = result.cache_hits + result.cache_misses
        if total_cache_ops > 0:
            result_cache_ratio = result.cache_hits / total_cache_ops
            self.metrics["cache_hit_ratio"] = (
                self.metrics["cache_hit_ratio"] + result_cache_ratio
            ) / 2

    async def create_simple_plan(
        self,
        name: str,
        mcp_calls: List[Dict[str, Any]],
        persona_domain: PersonaType = PersonaType.SOPHIA,
    ) -> ExecutionPlan:
        """Create simple sequential execution plan"""
        builder = DAGBuilder()

        for i, call in enumerate(mcp_calls):
            node_id = f"step_{i}"
            dependencies = {f"step_{i-1}"} if i > 0 else set()

            builder.add_mcp_node(
                node_id=node_id,
                name=call.get("name", f"Step {i}"),
                server_type=MCPServerType(call["server_type"]),
                method=call["method"],
                params=call.get("params", {}),
                dependencies=dependencies,
                cache_key=call.get("cache_key"),
            )

        return builder.build(plan_id=str(uuid4()), name=name, persona_domain=persona_domain)

    async def get_execution_status(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of execution"""
        if plan_id not in self.active_executions:
            return None

        plan = self.active_executions[plan_id]
        status = {"plan_id": plan_id, "name": plan.name, "status": "running", "nodes": {}}

        for node_id, node in plan.nodes.items():
            status["nodes"][node_id] = {
                "name": node.name,
                "status": node.status.value,
                "start_time": node.start_time.isoformat() if node.start_time else None,
                "end_time": node.end_time.isoformat() if node.end_time else None,
                "error": node.error,
            }

        return status

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive orchestrator health check"""
        await self.server_registry.health_check_all()

        healthy_servers = sum(1 for h in self.server_registry.server_health.values() if h)
        total_servers = len(self.server_registry.server_health)

        return {
            "status": "healthy" if healthy_servers == total_servers else "degraded",
            "servers": {
                "healthy": healthy_servers,
                "total": total_servers,
                "details": self.server_registry.server_health,
            },
            "active_executions": len(self.active_executions),
            "metrics": self.metrics,
            "memory_system": (
                await self.memory_system.health_check() if self.memory_system else None
            ),
        }


# Factory function for easy instantiation
async def create_mcp_orchestrator(
    memory_system: Optional[HierarchicalMemorySystem] = None,
    config: Optional[Dict[str, Any]] = None,
) -> MCPOrchestrator:
    """Create and initialize MCP orchestrator"""

    default_config = {"max_concurrent_nodes": 10, "default_timeout": 300}

    if config:
        default_config.update(config)

    orchestrator = MCPOrchestrator(memory_system=memory_system, **default_config)

    # Register additional servers from config
    if config and "additional_servers" in config:
        for server_config in config["additional_servers"]:
            capability = MCPCapability(**server_config)
            orchestrator.server_registry.register_server(capability)

    return orchestrator


# Usage example
async def main():
    """Example usage of MCP orchestrator"""

    # Create orchestrator
    orchestrator = await create_mcp_orchestrator()

    # Create execution plan
    plan = await orchestrator.create_simple_plan(
        name="File Analysis Workflow",
        mcp_calls=[
            {
                "name": "Read Config",
                "server_type": "filesystem",
                "method": "read_file",
                "params": {"path": "/config/app.json"},
                "cache_key": "config_file",
            },
            {
                "name": "Analyze Code",
                "server_type": "code_analysis",
                "method": "analyze_code",
                "params": {"directory": "/src"},
                "cache_key": "code_analysis",
            },
            {
                "name": "Search Documentation",
                "server_type": "web_search",
                "method": "search",
                "params": {"query": "API documentation"},
            },
        ],
    )

    # Execute plan
    result = await orchestrator.execute_plan(plan)

    print(f"Execution completed: {result.status.value}")
    print(f"Nodes executed: {result.nodes_executed}")
    print(f"Execution time: {result.execution_time_ms:.2f}ms")

    # Health check
    health = await orchestrator.health_check()
    print(f"Orchestrator status: {health['status']}")


if __name__ == "__main__":
    asyncio.run(main())
