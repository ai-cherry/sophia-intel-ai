"""
AGNO Chain Builder
Composable agent pipeline system with YAML configuration support
"""

import asyncio
import yaml
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, AsyncGenerator, Callable
from enum import Enum
from pathlib import Path

from app.infrastructure.agno.agent_runtime import AGNOAgent, AgentStatus

logger = logging.getLogger(__name__)

# ==================== Chain Configuration ====================

@dataclass
class ChainNode:
    """Configuration for a single node in the chain"""
    agent_id: str
    agent_type: str
    agent_class: str
    config: Dict[str, Any] = field(default_factory=dict)
    inputs: List[str] = field(default_factory=list)  # Input node IDs
    outputs: List[str] = field(default_factory=list)  # Output node IDs
    condition: Optional[str] = None  # Conditional execution expression
    retry_policy: Dict[str, Any] = field(default_factory=lambda: {"max_retries": 3, "delay": 1.0})

@dataclass
class ChainConfig:
    """Configuration for an entire agent chain"""
    chain_id: str
    name: str
    description: str
    nodes: List[ChainNode]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[float] = None
    parallel_execution: bool = False

# ==================== Chain Execution Context ====================

@dataclass
class ChainContext:
    """Execution context passed between chain nodes"""
    chain_id: str
    execution_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    node_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

# ==================== Chain Events ====================

class ChainEventType(Enum):
    """Types of chain events"""
    CHAIN_STARTED = "chain.started"
    CHAIN_COMPLETED = "chain.completed"
    CHAIN_FAILED = "chain.failed"
    NODE_STARTED = "node.started"
    NODE_COMPLETED = "node.completed"
    NODE_FAILED = "node.failed"
    NODE_SKIPPED = "node.skipped"

@dataclass
class ChainEvent:
    """Event emitted during chain execution"""
    event_type: ChainEventType
    chain_id: str
    execution_id: str
    node_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)

# ==================== Chain Builder ====================

class AGNOChainBuilder:
    """
    Builder for creating and executing AGNO agent chains
    Supports YAML configuration and dynamic chain composition
    """
    
    def __init__(self):
        """Initialize chain builder"""
        self.agent_registry: Dict[str, type] = {}
        self.chain_templates: Dict[str, ChainConfig] = {}
        self.active_chains: Dict[str, 'ChainExecutor'] = {}
        
        # Register default agents
        self._register_default_agents()
        
        logger.info("AGNO Chain Builder initialized")
    
    def _register_default_agents(self):
        """Register default agent types"""
        from app.infrastructure.agno.agent_runtime import WatcherAgent, LearnerAgent, ExecutorAgent
        
        self.register_agent("watcher", WatcherAgent)
        self.register_agent("learner", LearnerAgent)
        self.register_agent("executor", ExecutorAgent)
    
    def register_agent(self, agent_type: str, agent_class: type):
        """
        Register an agent class for use in chains
        
        Args:
            agent_type: Type identifier for the agent
            agent_class: Agent class (must inherit from AGNOAgent)
        """
        if not issubclass(agent_class, AGNOAgent):
            raise ValueError(f"{agent_class} must inherit from AGNOAgent")
        
        self.agent_registry[agent_type] = agent_class
        logger.info(f"Registered agent type: {agent_type} -> {agent_class.__name__}")
    
    def load_chain_from_yaml(self, yaml_path: Union[str, Path]) -> ChainConfig:
        """
        Load chain configuration from YAML file
        
        Args:
            yaml_path: Path to YAML configuration file
            
        Returns:
            ChainConfig object
        """
        yaml_path = Path(yaml_path)
        
        with open(yaml_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Parse nodes
        nodes = []
        for node_data in config_data.get('nodes', []):
            node = ChainNode(
                agent_id=node_data['id'],
                agent_type=node_data['type'],
                agent_class=node_data.get('class', node_data['type']),
                config=node_data.get('config', {}),
                inputs=node_data.get('inputs', []),
                outputs=node_data.get('outputs', []),
                condition=node_data.get('condition'),
                retry_policy=node_data.get('retry_policy', {"max_retries": 3, "delay": 1.0})
            )
            nodes.append(node)
        
        # Create chain config
        chain_config = ChainConfig(
            chain_id=config_data['chain_id'],
            name=config_data['name'],
            description=config_data.get('description', ''),
            nodes=nodes,
            metadata=config_data.get('metadata', {}),
            timeout=config_data.get('timeout'),
            parallel_execution=config_data.get('parallel_execution', False)
        )
        
        # Store template
        self.chain_templates[chain_config.chain_id] = chain_config
        
        logger.info(f"Loaded chain configuration: {chain_config.name} ({len(nodes)} nodes)")
        
        return chain_config
    
    def create_chain_from_config(self, config: ChainConfig) -> 'ChainExecutor':
        """
        Create a chain executor from configuration
        
        Args:
            config: Chain configuration
            
        Returns:
            ChainExecutor instance
        """
        executor = ChainExecutor(
            config=config,
            agent_registry=self.agent_registry
        )
        
        self.active_chains[config.chain_id] = executor
        
        return executor
    
    def create_chain(
        self,
        chain_id: str,
        name: str,
        nodes: List[Dict[str, Any]],
        **kwargs
    ) -> 'ChainExecutor':
        """
        Create a chain programmatically
        
        Args:
            chain_id: Unique chain ID
            name: Chain name
            nodes: List of node configurations
            **kwargs: Additional chain configuration
            
        Returns:
            ChainExecutor instance
        """
        # Parse nodes
        chain_nodes = []
        for node_data in nodes:
            node = ChainNode(
                agent_id=node_data['id'],
                agent_type=node_data['type'],
                agent_class=node_data.get('class', node_data['type']),
                config=node_data.get('config', {}),
                inputs=node_data.get('inputs', []),
                outputs=node_data.get('outputs', []),
                condition=node_data.get('condition'),
                retry_policy=node_data.get('retry_policy', {"max_retries": 3, "delay": 1.0})
            )
            chain_nodes.append(node)
        
        # Create config
        config = ChainConfig(
            chain_id=chain_id,
            name=name,
            description=kwargs.get('description', ''),
            nodes=chain_nodes,
            metadata=kwargs.get('metadata', {}),
            timeout=kwargs.get('timeout'),
            parallel_execution=kwargs.get('parallel_execution', False)
        )
        
        return self.create_chain_from_config(config)
    
    def get_chain(self, chain_id: str) -> Optional['ChainExecutor']:
        """Get active chain by ID"""
        return self.active_chains.get(chain_id)
    
    def list_chains(self) -> List[Dict[str, Any]]:
        """List all active chains"""
        chains = []
        for chain_id, executor in self.active_chains.items():
            chains.append({
                "chain_id": chain_id,
                "name": executor.config.name,
                "status": executor.status.value if executor.status else "unknown",
                "node_count": len(executor.config.nodes)
            })
        return chains


# ==================== Chain Executor ====================

class ChainExecutor:
    """
    Executor for running agent chains
    Handles node orchestration, data flow, and error recovery
    """
    
    def __init__(
        self,
        config: ChainConfig,
        agent_registry: Dict[str, type]
    ):
        """
        Initialize chain executor
        
        Args:
            config: Chain configuration
            agent_registry: Registry of available agent types
        """
        self.config = config
        self.agent_registry = agent_registry
        self.agents: Dict[str, AGNOAgent] = {}
        self.status: Optional[AgentStatus] = None
        self.execution_count = 0
        self.event_handlers: List[Callable[[ChainEvent], None]] = []
        
        # Build execution graph
        self.execution_graph = self._build_execution_graph()
        
        logger.info(f"Chain executor created: {config.name}")
    
    def _build_execution_graph(self) -> Dict[str, List[str]]:
        """Build execution dependency graph"""
        graph = {}
        
        for node in self.config.nodes:
            graph[node.agent_id] = node.outputs
        
        return graph
    
    async def initialize(self):
        """Initialize all agents in the chain"""
        for node in self.config.nodes:
            # Get agent class
            agent_class = self.agent_registry.get(node.agent_class)
            if not agent_class:
                raise ValueError(f"Unknown agent class: {node.agent_class}")
            
            # Create agent instance
            agent = agent_class(
                agent_id=node.agent_id,
                **node.config
            )
            
            self.agents[node.agent_id] = agent
            
            logger.info(f"Initialized agent: {node.agent_id} ({node.agent_type})")
        
        self.status = AgentStatus.READY
    
    async def execute(
        self,
        initial_data: Optional[Dict[str, Any]] = None
    ) -> ChainContext:
        """
        Execute the chain
        
        Args:
            initial_data: Initial data to pass to the chain
            
        Returns:
            Chain execution context with results
        """
        # Create execution context
        import uuid
        execution_id = str(uuid.uuid4())
        context = ChainContext(
            chain_id=self.config.chain_id,
            execution_id=execution_id,
            data=initial_data or {},
            metadata=self.config.metadata.copy()
        )
        
        # Emit start event
        await self._emit_event(ChainEvent(
            event_type=ChainEventType.CHAIN_STARTED,
            chain_id=self.config.chain_id,
            execution_id=execution_id,
            data={"initial_data": initial_data}
        ))
        
        try:
            # Execute based on mode
            if self.config.parallel_execution:
                await self._execute_parallel(context)
            else:
                await self._execute_sequential(context)
            
            # Emit completion event
            await self._emit_event(ChainEvent(
                event_type=ChainEventType.CHAIN_COMPLETED,
                chain_id=self.config.chain_id,
                execution_id=execution_id,
                data={"results": context.node_results}
            ))
            
        except Exception as e:
            # Log error
            context.errors.append({
                "error": str(e),
                "type": type(e).__name__
            })
            
            # Emit failure event
            await self._emit_event(ChainEvent(
                event_type=ChainEventType.CHAIN_FAILED,
                chain_id=self.config.chain_id,
                execution_id=execution_id,
                data={"error": str(e)}
            ))
            
            logger.error(f"Chain execution failed: {e}")
        
        finally:
            self.execution_count += 1
        
        return context
    
    async def _execute_sequential(self, context: ChainContext):
        """Execute nodes sequentially"""
        for node in self.config.nodes:
            await self._execute_node(node, context)
    
    async def _execute_parallel(self, context: ChainContext):
        """Execute nodes in parallel where possible"""
        # Group nodes by dependency level
        levels = self._topological_sort()
        
        # Execute each level in parallel
        for level in levels:
            tasks = []
            for node_id in level:
                node = next(n for n in self.config.nodes if n.agent_id == node_id)
                tasks.append(self._execute_node(node, context))
            
            await asyncio.gather(*tasks)
    
    def _topological_sort(self) -> List[List[str]]:
        """Topological sort for parallel execution"""
        # Simple level-based sorting
        levels = []
        remaining = set(n.agent_id for n in self.config.nodes)
        processed = set()
        
        while remaining:
            level = []
            for node in self.config.nodes:
                if node.agent_id in remaining:
                    # Check if all inputs are processed
                    if all(inp in processed for inp in node.inputs):
                        level.append(node.agent_id)
            
            if not level:
                # Circular dependency or disconnected nodes
                level = list(remaining)
            
            levels.append(level)
            processed.update(level)
            remaining.difference_update(level)
        
        return levels
    
    async def _execute_node(
        self,
        node: ChainNode,
        context: ChainContext
    ):
        """Execute a single node"""
        # Check condition
        if node.condition and not self._evaluate_condition(node.condition, context):
            logger.info(f"Skipping node {node.agent_id}: condition not met")
            
            await self._emit_event(ChainEvent(
                event_type=ChainEventType.NODE_SKIPPED,
                chain_id=self.config.chain_id,
                execution_id=context.execution_id,
                node_id=node.agent_id,
                data={"condition": node.condition}
            ))
            
            return
        
        # Get agent
        agent = self.agents.get(node.agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {node.agent_id}")
        
        # Emit start event
        await self._emit_event(ChainEvent(
            event_type=ChainEventType.NODE_STARTED,
            chain_id=self.config.chain_id,
            execution_id=context.execution_id,
            node_id=node.agent_id
        ))
        
        # Prepare input data
        input_data = self._prepare_node_input(node, context)
        
        # Execute with retry
        result = None
        error = None
        
        for attempt in range(node.retry_policy["max_retries"]):
            try:
                # Start agent if needed
                if agent.status != AgentStatus.RUNNING:
                    await agent.start()
                
                # Execute agent with input data
                agent.config.update({"input_data": input_data})
                result = await agent.execute()
                
                # Success - break retry loop
                break
                
            except Exception as e:
                error = e
                logger.warning(f"Node {node.agent_id} attempt {attempt + 1} failed: {e}")
                
                if attempt < node.retry_policy["max_retries"] - 1:
                    await asyncio.sleep(node.retry_policy["delay"])
        
        # Handle result
        if result is not None:
            # Store result
            context.node_results[node.agent_id] = result
            
            # Update context data
            if isinstance(result, dict):
                context.data.update(result)
            
            # Emit completion event
            await self._emit_event(ChainEvent(
                event_type=ChainEventType.NODE_COMPLETED,
                chain_id=self.config.chain_id,
                execution_id=context.execution_id,
                node_id=node.agent_id,
                data={"result": result}
            ))
            
        else:
            # Node failed
            context.errors.append({
                "node_id": node.agent_id,
                "error": str(error)
            })
            
            # Emit failure event
            await self._emit_event(ChainEvent(
                event_type=ChainEventType.NODE_FAILED,
                chain_id=self.config.chain_id,
                execution_id=context.execution_id,
                node_id=node.agent_id,
                data={"error": str(error)}
            ))
            
            # Raise if not configured to continue on error
            if not context.metadata.get("continue_on_error", False):
                raise error
    
    def _prepare_node_input(
        self,
        node: ChainNode,
        context: ChainContext
    ) -> Dict[str, Any]:
        """Prepare input data for a node"""
        input_data = {}
        
        # Get data from input nodes
        for input_id in node.inputs:
            if input_id in context.node_results:
                input_data[input_id] = context.node_results[input_id]
        
        # Add context data
        input_data["context"] = context.data.copy()
        
        return input_data
    
    def _evaluate_condition(
        self,
        condition: str,
        context: ChainContext
    ) -> bool:
        """Evaluate node execution condition"""
        try:
            # Simple evaluation (in production, use safe eval)
            # This is a simplified version - implement proper sandboxed evaluation
            namespace = {
                "context": context.data,
                "results": context.node_results,
                "errors": len(context.errors)
            }
            
            # Warning: eval is dangerous - use ast.literal_eval or similar in production
            return eval(condition, {"__builtins__": {}}, namespace)
            
        except Exception as e:
            logger.warning(f"Condition evaluation failed: {e}")
            return False
    
    async def _emit_event(self, event: ChainEvent):
        """Emit a chain event"""
        for handler in self.event_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Event handler failed: {e}")
    
    def on_event(self, handler: Callable[[ChainEvent], None]):
        """Register an event handler"""
        self.event_handlers.append(handler)
    
    async def stop(self):
        """Stop all agents in the chain"""
        for agent in self.agents.values():
            if agent.status == AgentStatus.RUNNING:
                await agent.stop()
        
        self.status = AgentStatus.STOPPED
    
    def get_status(self) -> Dict[str, Any]:
        """Get chain status"""
        return {
            "chain_id": self.config.chain_id,
            "name": self.config.name,
            "status": self.status.value if self.status else "unknown",
            "execution_count": self.execution_count,
            "nodes": [
                {
                    "id": node.agent_id,
                    "type": node.agent_type,
                    "status": self.agents[node.agent_id].status.value if node.agent_id in self.agents else "unknown"
                }
                for node in self.config.nodes
            ]
        }


# ==================== Example YAML Configuration ====================

EXAMPLE_CHAIN_YAML = """
chain_id: example-analysis-chain
name: Document Analysis Chain
description: Analyzes documents through multiple stages

nodes:
  - id: watcher-1
    type: watcher
    class: watcher
    config:
      watch_target: /data/documents
      pattern: "*.txt"
    outputs: [analyzer-1]

  - id: analyzer-1
    type: analyzer
    class: analyzer
    config:
      analysis_type: sentiment
    inputs: [watcher-1]
    outputs: [summarizer-1]

  - id: summarizer-1
    type: summarizer
    class: summarizer
    config:
      max_length: 100
    inputs: [analyzer-1]
    outputs: [notifier-1]

  - id: notifier-1
    type: notifier
    class: notifier
    config:
      channel: email
      recipients: [admin@example.com]
    inputs: [summarizer-1]

metadata:
  owner: data-team
  version: 1.0.0
  
timeout: 300
parallel_execution: false
"""