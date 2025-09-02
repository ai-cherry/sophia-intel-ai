"""
AGNO Teams Implementation for Sophia Intel AI
Migrates swarms to AGNO framework with Portkey routing
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any


# Mock AGNO classes until proper package is available
class Team:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.id = f"team_{name}_{hash(name)}"
        self.agents = {}

    def add_agent(self, agent):
        self.agents[agent.name] = agent

    async def run(self, task):
        # Simplified execution
        return {"status": "completed", "task": task.description}

class Agent:
    def __init__(self, name: str, model: str, provider: str = "portkey",
                 temperature: float = 0.7, instructions: str = "", metadata: dict = None):
        self.name = name
        self.model = model
        self.provider = provider
        self.temperature = temperature
        self.instructions = instructions
        self.metadata = metadata or {}
        self._llm = None

    async def run(self, task):
        return f"Agent {self.name} processed: {task.description}"

class Task:
    def __init__(self, description: str, metadata: dict = None):
        self.description = description
        self.metadata = metadata or {}
from portkey_ai import Portkey

from app.core.circuit_breaker import with_circuit_breaker
from app.swarms.enhanced_memory_integration import (
    EnhancedSwarmMemoryClient,
    auto_tag_and_store,
)

logger = logging.getLogger(__name__)

# Initialize Portkey client
portkey = Portkey(
    api_key=os.getenv("PORTKEY_API_KEY"),
    config={
        "retry": {"attempts": 3, "on_status": [429, 500, 502, 503]},
        "cache": {"simple": {"ttl": 3600}},
        "guardrails": {
            "pii": {"enabled": True},
            "prompt_injection": {"enabled": True}
        }
    }
)


class ExecutionStrategy(Enum):
    """Swarm execution strategies"""
    LITE = "lite"  # Fast, minimal agents
    BALANCED = "balanced"  # Default balanced approach
    QUALITY = "quality"  # Comprehensive with consensus
    DEBATE = "debate"  # Debate pattern
    CONSENSUS = "consensus"  # Consensus building


@dataclass
class AGNOTeamConfig:
    """Configuration for AGNO Team"""
    name: str
    strategy: ExecutionStrategy = ExecutionStrategy.BALANCED
    max_agents: int = 5
    timeout: int = 30
    enable_memory: bool = True
    enable_circuit_breaker: bool = True
    auto_tag: bool = True


class SophiaAGNOTeam:
    """
    AGNO Team implementation for Sophia Intel AI
    Provides unified orchestration with Portkey routing
    """

    # Approved models only
    APPROVED_MODELS = {
        "planner": "qwen/qwen3-30b-a3b",
        "generator": "x-ai/grok-4",
        "critic": "x-ai/grok-4",
        "judge": "openai/gpt-5",
        "lead": "x-ai/grok-4",
        "runner": "google/gemini-2.5-flash",
        "architect": "qwen/qwen3-30b-a3b",
        "security": "x-ai/grok-4",
        "performance": "openai/gpt-5",
        "testing": "google/gemini-2.5-flash",
        "debugger": "x-ai/grok-code-fast-1",
        "refactorer": "x-ai/grok-code-fast-1"
    }

    # AGNO API Key
    AGNO_API_KEY = "phi-0cnOaV2N-MKID0LJTszPjAdj7XhunqMQFG4IwLPG9dI"

    def __init__(self, config: AGNOTeamConfig):
        self.config = config
        self.team: Team | None = None
        self.memory_client: EnhancedSwarmMemoryClient | None = None
        self.execution_history = []
        # Routing config will be created lazily when needed
        self.routing_config = None

    async def initialize(self):
        """Initialize AGNO Team with agents and memory"""

        # Create AGNO Team
        self.team = Team(
            name=self.config.name,
            description=f"AGNO Team using {self.config.strategy.value} strategy"
        )

        # Add agents based on strategy with optimal routing
        agents_to_add = self._get_agents_for_strategy()
        for role, fallback_model in agents_to_add.items():
            # Get optimal model for this role
            optimal_model = await self._get_optimal_model_for_role(role, 0.5)
            agent = await self._create_agent(role, optimal_model)
            self.team.add_agent(agent)

        # Initialize memory if enabled
        if self.config.enable_memory:
            self.memory_client = EnhancedSwarmMemoryClient(
                swarm_type=f"agno_{self.config.name}",
                swarm_id=self.team.id
            )

        logger.info(f"Initialized AGNO Team: {self.config.name}")

    def _get_routing_strategy(self):
        """Map execution strategy to routing strategy"""
        # Import locally to avoid circular dependency
        from app.api.portkey_unified_router import RoutingStrategy

        strategy_mapping = {
            ExecutionStrategy.LITE: RoutingStrategy.FASTEST_AVAILABLE,
            ExecutionStrategy.BALANCED: RoutingStrategy.BALANCED,
            ExecutionStrategy.QUALITY: RoutingStrategy.HIGHEST_QUALITY,
            ExecutionStrategy.DEBATE: RoutingStrategy.PERFORMANCE_FIRST,
            ExecutionStrategy.CONSENSUS: RoutingStrategy.BALANCED
        }
        return strategy_mapping.get(self.config.strategy, RoutingStrategy.BALANCED)

    async def _get_optimal_model_for_role(self, role: str, task_complexity: float = 0.5) -> str:
        """Get optimal model for role using unified routing"""
        try:
            # Import locally to avoid circular dependency
            from app.api.portkey_unified_router import get_optimal_model_for_role, unified_router

            if not unified_router.session:
                await unified_router.initialize()

            return await get_optimal_model_for_role(
                agent_role=role,
                execution_strategy=self.config.strategy,
                task_complexity=task_complexity
            )
        except Exception as e:
            logger.warning(f"Failed to get optimal model for {role}: {e}")
            # Fallback to approved model
            return self.APPROVED_MODELS.get(role, self.APPROVED_MODELS["generator"])

    def _get_agents_for_strategy(self) -> dict[str, str]:
        """Get agents configuration based on strategy"""

        if self.config.strategy == ExecutionStrategy.LITE:
            return {
                "runner": self.APPROVED_MODELS["runner"],
                "critic": self.APPROVED_MODELS["critic"]
            }
        elif self.config.strategy == ExecutionStrategy.QUALITY:
            return {
                "planner": self.APPROVED_MODELS["planner"],
                "generator": self.APPROVED_MODELS["generator"],
                "critic": self.APPROVED_MODELS["critic"],
                "judge": self.APPROVED_MODELS["judge"],
                "testing": self.APPROVED_MODELS["testing"]
            }
        elif self.config.strategy == ExecutionStrategy.DEBATE:
            return {
                "generator": self.APPROVED_MODELS["generator"],
                "critic": self.APPROVED_MODELS["critic"],
                "judge": self.APPROVED_MODELS["judge"]
            }
        else:  # BALANCED or default
            return {
                "planner": self.APPROVED_MODELS["planner"],
                "generator": self.APPROVED_MODELS["generator"],
                "critic": self.APPROVED_MODELS["critic"]
            }

    async def _create_agent(self, role: str, model: str) -> Agent:
        """Create AGNO agent with Portkey routing"""

        # Temperature based on role
        temperatures = {
            "planner": 0.3,
            "generator": 0.7,
            "critic": 0.1,
            "judge": 0.2,
            "testing": 0.4,
            "debugger": 0.1
        }

        agent = Agent(
            name=role,
            model=model,
            provider="portkey",
            temperature=temperatures.get(role, 0.5),
            instructions=f"You are a {role} agent in the {self.config.name} team.",
            metadata={
                "role": role,
                "team": self.config.name,
                "strategy": self.config.strategy.value
            }
        )

        # Configure Portkey routing
        agent._llm = portkey.completions

        return agent

    @with_circuit_breaker("agno_execution")
    async def execute_task(
        self,
        task_description: str,
        context: dict[str, Any],
        model_overrides: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """
        Execute task with AGNO Team
        
        Args:
            task_description: Task to execute
            context: Execution context for auto-tagging
            model_overrides: Optional model overrides per role
        """

        if not self.team:
            await self.initialize()

        # Apply model overrides if provided
        if model_overrides:
            for role, model in model_overrides.items():
                if role in self.team.agents:
                    self.team.agents[role].model = model

        # Create task
        task = Task(
            description=task_description,
            metadata=context
        )

        # Store task initiation in memory
        if self.memory_client and self.config.auto_tag:
            await auto_tag_and_store(
                self.memory_client,
                content=f"Task initiated: {task_description}",
                topic="Task Execution",
                execution_context=context
            )

        # Execute based on strategy
        if self.config.strategy == ExecutionStrategy.DEBATE:
            result = await self._execute_debate(task)
        elif self.config.strategy == ExecutionStrategy.CONSENSUS:
            result = await self._execute_consensus(task)
        else:
            result = await self._execute_standard(task)

        # Store result in memory
        if self.memory_client and self.config.auto_tag:
            await auto_tag_and_store(
                self.memory_client,
                content=str(result),
                topic="Task Result",
                execution_context={
                    **context,
                    "success": result.get("success", False),
                    "execution_time": result.get("execution_time", 0)
                }
            )

        # Track execution history
        self.execution_history.append({
            "task": task_description,
            "result": result,
            "timestamp": asyncio.get_event_loop().time()
        })

        return result

    async def _execute_standard(self, task: Task) -> dict[str, Any]:
        """Standard execution flow"""

        start_time = asyncio.get_event_loop().time()

        try:
            # Run task through team
            result = await self.team.run(task)

            return {
                "success": True,
                "result": result,
                "execution_time": asyncio.get_event_loop().time() - start_time,
                "strategy": "standard",
                "agents_used": list(self.team.agents.keys())
            }
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": asyncio.get_event_loop().time() - start_time
            }

    async def _execute_debate(self, task: Task) -> dict[str, Any]:
        """Execute with debate pattern"""

        generator = self.team.agents.get("generator")
        critic = self.team.agents.get("critic")
        judge = self.team.agents.get("judge")

        if not all([generator, critic, judge]):
            return await self._execute_standard(task)

        rounds = []
        for round_num in range(3):
            # Generator proposes
            proposal = await generator.run(task)

            # Critic reviews
            critique = await critic.run(
                Task(f"Review this proposal: {proposal}")
            )

            rounds.append({
                "round": round_num + 1,
                "proposal": proposal,
                "critique": critique
            })

            # Update task with feedback
            task.description = f"{task.description}\n\nFeedback: {critique}"

        # Judge decides
        final_decision = await judge.run(
            Task(f"Based on these rounds, provide final solution: {rounds}")
        )

        return {
            "success": True,
            "result": final_decision,
            "strategy": "debate",
            "rounds": rounds
        }

    async def _execute_consensus(self, task: Task) -> dict[str, Any]:
        """Execute with consensus building"""

        # Get all agent responses
        responses = {}
        for role, agent in self.team.agents.items():
            responses[role] = await agent.run(task)

        # Build consensus
        consensus_task = Task(
            f"Build consensus from these responses: {responses}"
        )

        if "judge" in self.team.agents:
            consensus = await self.team.agents["judge"].run(consensus_task)
        else:
            # Simple majority or merge
            consensus = self._merge_responses(responses)

        return {
            "success": True,
            "result": consensus,
            "strategy": "consensus",
            "individual_responses": responses
        }

    def _merge_responses(self, responses: dict[str, Any]) -> str:
        """Simple response merging for consensus"""
        merged = []
        for role, response in responses.items():
            merged.append(f"{role}: {response}")
        return "\n".join(merged)


class UnifiedOrchestratorFacade:
    """
    Unified facade for AGNO Teams
    Implements chain-of-responsibility pattern
    """

    def __init__(self):
        self.teams: dict[str, SophiaAGNOTeam] = {}
        self.default_config = AGNOTeamConfig(
            name="default",
            strategy=ExecutionStrategy.BALANCED
        )

    async def get_or_create_team(
        self,
        name: str,
        config: AGNOTeamConfig | None = None
    ) -> SophiaAGNOTeam:
        """Get existing team or create new one"""

        if name not in self.teams:
            team_config = config or AGNOTeamConfig(
                name=name,
                strategy=ExecutionStrategy.BALANCED
            )
            team = SophiaAGNOTeam(team_config)
            await team.initialize()
            self.teams[name] = team

        return self.teams[name]

    async def execute(
        self,
        team_name: str,
        task: str,
        context: dict[str, Any],
        strategy: ExecutionStrategy | None = None,
        model_overrides: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """
        Execute task with specified team
        
        Chain of responsibility:
        SimpleAgentOrchestrator → UnifiedOrchestratorFacade → SophiaAGNOTeam
        """

        # Get or create team
        config = AGNOTeamConfig(
            name=team_name,
            strategy=strategy or ExecutionStrategy.BALANCED
        )
        team = await self.get_or_create_team(team_name, config)

        # Execute task
        result = await team.execute_task(
            task_description=task,
            context=context,
            model_overrides=model_overrides
        )

        return result

    async def list_teams(self) -> list[str]:
        """List all active teams"""
        return list(self.teams.keys())

    async def get_team_status(self, team_name: str) -> dict[str, Any]:
        """Get team status and history"""

        if team_name not in self.teams:
            return {"error": "Team not found"}

        team = self.teams[team_name]
        return {
            "name": team.config.name,
            "strategy": team.config.strategy.value,
            "agents": list(team.team.agents.keys()) if team.team else [],
            "execution_count": len(team.execution_history),
            "last_execution": team.execution_history[-1] if team.execution_history else None
        }


# Global facade instance
orchestrator_facade = UnifiedOrchestratorFacade()


# Helper function for migration
async def migrate_legacy_swarm_to_agno(
    swarm_config: dict[str, Any]
) -> SophiaAGNOTeam:
    """Migrate legacy swarm configuration to AGNO Team"""

    # Map legacy config to AGNO config
    strategy_map = {
        "lite": ExecutionStrategy.LITE,
        "balanced": ExecutionStrategy.BALANCED,
        "quality": ExecutionStrategy.QUALITY
    }

    config = AGNOTeamConfig(
        name=swarm_config.get("name", "migrated_swarm"),
        strategy=strategy_map.get(
            swarm_config.get("mode", "balanced"),
            ExecutionStrategy.BALANCED
        ),
        max_agents=swarm_config.get("max_agents", 5),
        timeout=swarm_config.get("timeout", 30),
        enable_memory=swarm_config.get("memory_enabled", True)
    )

    team = SophiaAGNOTeam(config)
    await team.initialize()

    return team
