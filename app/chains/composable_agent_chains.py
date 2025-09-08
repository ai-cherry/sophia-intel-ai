#!/usr/bin/env python3
"""
Composable Agent Chains for Sophia-Intel-AI
Build reusable workflows by chaining agents together
"""
import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent execution status"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class AgentResult:
    """Result from agent execution"""

    agent_name: str
    status: AgentStatus
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChainContext:
    """Context passed between agents in a chain"""

    initial_input: Any
    results: list[AgentResult] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    shared_memory: dict[str, Any] = field(default_factory=dict)

    def get_last_output(self) -> Any:
        """Get output from the last successful agent"""
        for result in reversed(self.results):
            if result.status == AgentStatus.SUCCESS:
                return result.output
        return self.initial_input

    def get_agent_output(self, agent_name: str) -> Optional[Any]:
        """Get output from a specific agent"""
        for result in self.results:
            if result.agent_name == agent_name and result.status == AgentStatus.SUCCESS:
                return result.output
        return None


class BaseAgent:
    """Base class for all agents in chains"""

    def __init__(self, name: str):
        self.name = name
        self.retry_count = 3
        self.timeout = 60  # seconds

    async def execute(self, context: ChainContext) -> AgentResult:
        """Execute the agent with retry logic"""
        start_time = time.time()

        for attempt in range(self.retry_count):
            try:
                # Get input from context
                input_data = context.get_last_output()

                # Run the agent's process method
                output = await asyncio.wait_for(
                    self.process(input_data, context), timeout=self.timeout
                )

                return AgentResult(
                    agent_name=self.name,
                    status=AgentStatus.SUCCESS,
                    output=output,
                    execution_time=time.time() - start_time,
                )

            except asyncio.TimeoutError:
                error = f"Timeout after {self.timeout} seconds"
                logger.error(f"{self.name}: {error}")

                if attempt == self.retry_count - 1:
                    return AgentResult(
                        agent_name=self.name,
                        status=AgentStatus.FAILED,
                        output=None,
                        error=error,
                        execution_time=time.time() - start_time,
                    )

            except Exception as e:
                error = str(e)
                logger.error(f"{self.name} error: {error}")

                if attempt == self.retry_count - 1:
                    return AgentResult(
                        agent_name=self.name,
                        status=AgentStatus.FAILED,
                        output=None,
                        error=error,
                        execution_time=time.time() - start_time,
                    )

            # Wait before retry
            await asyncio.sleep(2**attempt)

    async def process(self, input_data: Any, context: ChainContext) -> Any:
        """Process method to be implemented by subclasses"""
        raise NotImplementedError


# Concrete Agent Implementations


class AnalysisAgent(BaseAgent):
    """Analyzes input and extracts insights"""

    def __init__(self):
        super().__init__("AnalysisAgent")

    async def process(self, input_data: Any, context: ChainContext) -> dict[str, Any]:
        """Analyze input data"""
        # Simulate analysis
        await asyncio.sleep(0.5)

        return {
            "analysis_type": "comprehensive",
            "data_points": len(str(input_data)),
            "insights": [
                "Pattern detected in data",
                "Anomaly identified",
                "Trend analysis complete",
            ],
            "risk_score": 0.3,
            "recommendations": ["Optimize processing", "Implement caching"],
        }


class OptimizationAgent(BaseAgent):
    """Optimizes based on analysis"""

    def __init__(self):
        super().__init__("OptimizationAgent")

    async def process(self, input_data: Any, context: ChainContext) -> dict[str, Any]:
        """Optimize based on analysis"""
        await asyncio.sleep(0.3)

        # Get analysis results
        analysis = input_data if isinstance(input_data, dict) else {}

        optimizations = []
        if analysis.get("risk_score", 0) > 0.5:
            optimizations.append("Implement additional validation")

        optimizations.extend(
            [
                "Cache frequently accessed data",
                "Implement lazy loading",
                "Use connection pooling",
            ]
        )

        return {
            "optimizations": optimizations,
            "expected_improvement": "40% performance gain",
            "implementation_priority": ["high", "medium", "low"],
            "estimated_time": "2 days",
        }


class ValidationAgent(BaseAgent):
    """Validates results"""

    def __init__(self):
        super().__init__("ValidationAgent")

    async def process(self, input_data: Any, context: ChainContext) -> dict[str, Any]:
        """Validate results"""
        await asyncio.sleep(0.2)

        return {
            "validation_status": "passed",
            "checks_performed": [
                "Data integrity",
                "Business rules",
                "Performance metrics",
            ],
            "warnings": [],
            "approved": True,
        }


class ImplementationAgent(BaseAgent):
    """Implements solutions"""

    def __init__(self):
        super().__init__("ImplementationAgent")

    async def process(self, input_data: Any, context: ChainContext) -> dict[str, Any]:
        """Implement solution"""
        await asyncio.sleep(1.0)

        return {
            "implementation_status": "complete",
            "files_created": ["optimization.py", "cache_config.yaml"],
            "code_generated": True,
            "tests_added": True,
            "documentation_updated": True,
        }


class MonitoringAgent(BaseAgent):
    """Monitors system metrics"""

    def __init__(self):
        super().__init__("MonitoringAgent")

    async def process(self, input_data: Any, context: ChainContext) -> dict[str, Any]:
        """Monitor metrics"""
        await asyncio.sleep(0.3)

        return {
            "metrics": {
                "cpu_usage": "45%",
                "memory_usage": "62%",
                "response_time": "120ms",
                "error_rate": "0.1%",
            },
            "alerts": [],
            "health_status": "healthy",
        }


class AgentChain:
    """Composable chain of agents"""

    def __init__(self, name: str = "DefaultChain"):
        self.name = name
        self.agents: list[BaseAgent] = []
        self.parallel_groups: list[list[BaseAgent]] = []
        self.error_handler: Optional[Callable] = None
        self.monitoring_enabled = True

    def add(self, agent: BaseAgent) -> "AgentChain":
        """Add an agent to the chain"""
        self.agents.append(agent)
        return self

    def add_parallel(self, agents: list[BaseAgent]) -> "AgentChain":
        """Add agents to run in parallel"""
        self.parallel_groups.append(agents)
        return self

    def with_error_handler(self, handler: Callable) -> "AgentChain":
        """Add error handler"""
        self.error_handler = handler
        return self

    def with_monitoring(self, enabled: bool = True) -> "AgentChain":
        """Enable/disable monitoring"""
        self.monitoring_enabled = enabled
        return self

    async def execute(self, input_data: Any) -> ChainContext:
        """Execute the agent chain"""
        logger.info(f"Starting chain: {self.name}")
        context = ChainContext(initial_input=input_data)

        # Execute sequential agents
        for agent in self.agents:
            logger.info(f"Executing agent: {agent.name}")
            result = await agent.execute(context)
            context.results.append(result)

            # Handle failures
            if result.status == AgentStatus.FAILED:
                if self.error_handler:
                    await self.error_handler(result, context)
                else:
                    logger.error(f"Agent {agent.name} failed: {result.error}")
                    break

        # Execute parallel groups
        for group in self.parallel_groups:
            logger.info(f"Executing parallel group: {[a.name for a in group]}")
            tasks = [agent.execute(context) for agent in group]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    result = AgentResult(
                        agent_name="UnknownAgent",
                        status=AgentStatus.FAILED,
                        output=None,
                        error=str(result),
                    )
                context.results.append(result)

        # Add monitoring if enabled
        if self.monitoring_enabled:
            monitoring = MonitoringAgent()
            result = await monitoring.execute(context)
            context.results.append(result)

        logger.info(f"Chain {self.name} completed")
        return context


class ChainBuilder:
    """Builder for creating pre-configured chains"""

    @staticmethod
    def analyze_and_optimize() -> AgentChain:
        """Create analyze and optimize chain"""
        return (
            AgentChain("AnalyzeAndOptimize")
            .add(AnalysisAgent())
            .add(OptimizationAgent())
            .add(ValidationAgent())
        )

    @staticmethod
    def implement_and_validate() -> AgentChain:
        """Create implementation and validation chain"""
        return (
            AgentChain("ImplementAndValidate")
            .add(ImplementationAgent())
            .add(ValidationAgent())
            .add(MonitoringAgent())
        )

    @staticmethod
    def full_pipeline() -> AgentChain:
        """Create full pipeline chain"""
        return (
            AgentChain("FullPipeline")
            .add(AnalysisAgent())
            .add(OptimizationAgent())
            .add(ValidationAgent())
            .add(ImplementationAgent())
            .add(MonitoringAgent())
        )

    @staticmethod
    def parallel_analysis() -> AgentChain:
        """Create parallel analysis chain"""
        return (
            AgentChain("ParallelAnalysis")
            .add_parallel([AnalysisAgent(), MonitoringAgent()])
            .add(OptimizationAgent())
            .add(ValidationAgent())
        )


class ChainOrchestrator:
    """Orchestrates multiple chains"""

    def __init__(self):
        self.chains: dict[str, AgentChain] = {}
        self.execution_history: list[dict[str, Any]] = []

    def register_chain(self, name: str, chain: AgentChain):
        """Register a chain"""
        self.chains[name] = chain

    async def execute_chain(self, chain_name: str, input_data: Any) -> ChainContext:
        """Execute a registered chain"""
        if chain_name not in self.chains:
            raise ValueError(f"Chain {chain_name} not found")

        chain = self.chains[chain_name]
        start_time = datetime.now()

        context = await chain.execute(input_data)

        # Record execution
        self.execution_history.append(
            {
                "chain_name": chain_name,
                "timestamp": start_time.isoformat(),
                "duration": (datetime.now() - start_time).total_seconds(),
                "success": all(
                    r.status == AgentStatus.SUCCESS for r in context.results
                ),
                "agents_executed": len(context.results),
            }
        )

        return context

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics for chains"""
        if not self.execution_history:
            return {"total_executions": 0}

        successful = sum(1 for e in self.execution_history if e["success"])
        total = len(self.execution_history)

        return {
            "total_executions": total,
            "successful_executions": successful,
            "success_rate": (successful / total) * 100,
            "average_duration": sum(e["duration"] for e in self.execution_history)
            / total,
            "chains_registered": len(self.chains),
        }


async def main():
    """Test agent chains"""
    print("=" * 60)
    print("Testing Composable Agent Chains")
    print("=" * 60)

    # Test 1: Simple sequential chain
    print("\n1. Testing Sequential Chain")
    chain = ChainBuilder.analyze_and_optimize()
    context = await chain.execute("Test input data")

    print(f"Chain completed with {len(context.results)} agents")
    for result in context.results:
        print(
            f"  - {result.agent_name}: {result.status.value} ({result.execution_time:.2f}s)"
        )

    # Test 2: Parallel execution
    print("\n2. Testing Parallel Chain")
    parallel_chain = ChainBuilder.parallel_analysis()
    context = await parallel_chain.execute("Parallel test data")

    print(f"Parallel chain completed with {len(context.results)} agents")
    for result in context.results:
        print(f"  - {result.agent_name}: {result.status.value}")

    # Test 3: Chain orchestrator
    print("\n3. Testing Chain Orchestrator")
    orchestrator = ChainOrchestrator()
    orchestrator.register_chain("analyze", ChainBuilder.analyze_and_optimize())
    orchestrator.register_chain("implement", ChainBuilder.implement_and_validate())
    orchestrator.register_chain("full", ChainBuilder.full_pipeline())

    # Execute chains
    await orchestrator.execute_chain("analyze", "Orchestrator test")
    await orchestrator.execute_chain("implement", "Implementation test")

    # Show metrics
    print("\nPerformance Metrics:")
    metrics = orchestrator.get_performance_metrics()
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
