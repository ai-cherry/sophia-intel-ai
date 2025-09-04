"""
AGNO Teams Implementation for Sophia Intel AI
Real AGNO framework integration with Portkey routing
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Dict

# Real AGNO framework imports
from agno.agent import Agent
from agno.team import Team
from agno.models.portkey import Portkey as AGNOPortkey
from portkey_ai import Portkey

from app.core.circuit_breaker import with_circuit_breaker
from app.swarms.enhanced_memory_integration import (
    EnhancedSwarmMemoryClient,
    auto_tag_and_store,
)

logger = logging.getLogger(__name__)

# Portkey virtual keys configuration
PORTKEY_VIRTUAL_KEYS = {
    "deepseek": "deepseek-vk-24102f",
    "openai": "openai-vk-190a60", 
    "anthropic": "anthropic-vk-b42804",
    "openrouter": "vkj-openrouter-cc4151",
    "perplexity": "perplexity-vk-56c172",
    "groq": "groq-vk-6b9b52",
    "mistral": "mistral-vk-f92861",
    "milvus": "milvus-vk-34fa02",
    "xai": "xai-vk-e65d0f",
    "together": "together-ai-670469",
    "qdrant": "qdrant-vk-d2b62a",
    "cohere": "cohere-vk-496fa9"
}

# Initialize Portkey client with new API key
portkey = Portkey(
    api_key="hPxFZGd8AN269n4bznDf2/Onbi8I",
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

    # Approved models with virtual key routing
    APPROVED_MODELS = {
        "planner": {"provider": "deepseek", "model": "deepseek-chat", "virtual_key": "deepseek-vk-24102f"},
        "generator": {"provider": "openai", "model": "gpt-4o-mini", "virtual_key": "openai-vk-190a60"},
        "critic": {"provider": "openai", "model": "gpt-4o-mini", "virtual_key": "openai-vk-190a60"},
        "judge": {"provider": "openai", "model": "gpt-4o", "virtual_key": "openai-vk-190a60"},
        "lead": {"provider": "openai", "model": "gpt-4o-mini", "virtual_key": "openai-vk-190a60"},
        "runner": {"provider": "openai", "model": "gpt-4o-mini", "virtual_key": "openai-vk-190a60"},
        "architect": {"provider": "deepseek", "model": "deepseek-chat", "virtual_key": "deepseek-vk-24102f"},
        "security": {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022", "virtual_key": "anthropic-vk-b42804"},
        "performance": {"provider": "openai", "model": "gpt-4o", "virtual_key": "openai-vk-190a60"},
        "testing": {"provider": "openai", "model": "gpt-4o-mini", "virtual_key": "openai-vk-190a60"},
        "debugger": {"provider": "openai", "model": "gpt-4o-mini", "virtual_key": "openai-vk-190a60"},
        "refactorer": {"provider": "openai", "model": "gpt-4o-mini", "virtual_key": "openai-vk-190a60"}
    }

    # AGNO API Key
    AGNO_API_KEY = "phi-0cnOaV2N-MKID0LJTszPjAdj7XhunqMQFG4IwLPG9dI"

    def __init__(self, config: AGNOTeamConfig):
        self.config = config
        self.team: Optional[Team] = None
        self.memory_client: Optional[EnhancedSwarmMemoryClient] = None
        self.execution_history = []
        # Routing config will be created lazily when needed
        self.routing_config = None

    async def initialize(self):
        """Initialize AGNO Team with agents and memory"""

        # Create agents based on strategy with optimal routing
        agents_to_add = self._get_agents_for_strategy()
        self.agents = []
        
        for role in agents_to_add.keys():
            # Get optimal model config for this role
            model_config = await self._get_optimal_model_for_role(role, 0.5)
            agent = await self._create_agent(role, model_config)
            self.agents.append(agent)

        # Create AGNO Team with the agents
        self.team = Team(
            members=self.agents,
            name=self.config.name,
            description=f"AGNO Team using {self.config.strategy.value} strategy",
            instructions=f"This team operates in {self.config.strategy.value} mode. Collaborate effectively to achieve the given tasks.",
            mode="collaborate"  # Default collaboration mode
        )

        # Initialize memory if enabled
        if self.config.enable_memory:
            self.memory_client = EnhancedSwarmMemoryClient(
                swarm_type=f"agno_{self.config.name}",
                swarm_id=f"team_{self.config.name}_{hash(self.config.name)}"
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

    async def _get_optimal_model_for_role(self, role: str, task_complexity: float = 0.5) -> dict:
        """Get optimal model config for role using unified routing"""
        try:
            # Import locally to avoid circular dependency
            from app.api.portkey_unified_router import get_optimal_model_for_role, unified_router

            # Check if we're in an event loop context
            try:
                loop = asyncio.get_running_loop()
                if loop and loop.is_running():
                    # We're already in an event loop, use the async call directly
                    if not unified_router.session:
                        await unified_router.initialize()

                    model_name = await get_optimal_model_for_role(
                        agent_role=role,
                        execution_strategy=self.config.strategy,
                        task_complexity=task_complexity
                    )
                    
                    # Find matching config for the returned model
                    for model_config in self.APPROVED_MODELS.values():
                        if model_config["model"] in model_name:
                            return model_config
                else:
                    # No event loop running, fall back to default
                    logger.debug(f"No event loop available for model optimization for {role}")
                    return self.APPROVED_MODELS.get(role, self.APPROVED_MODELS["generator"])
                    
            except RuntimeError:
                # No event loop available
                logger.debug(f"No event loop available for model optimization for {role}")
                return self.APPROVED_MODELS.get(role, self.APPROVED_MODELS["generator"])
            
            # Fallback to approved model config
            return self.APPROVED_MODELS.get(role, self.APPROVED_MODELS["generator"])
            
        except Exception as e:
            logger.warning(f"Failed to get optimal model for {role}: {e}")
            # Fallback to approved model config
            return self.APPROVED_MODELS.get(role, self.APPROVED_MODELS["generator"])

    def _get_agents_for_strategy(self) -> dict[str, dict]:
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

    async def _create_agent(self, role: str, model_config: dict) -> Agent:
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

        # Create AGNO Portkey model with virtual key
        model = AGNOPortkey(
            id=model_config["model"],
            name=f"Portkey_{model_config['provider']}_{model_config['model']}",
            portkey_api_key="hPxFZGd8AN269n4bznDf2/Onbi8I",
            virtual_key=model_config["virtual_key"],
            temperature=temperatures.get(role, 0.5),
            max_tokens=4096
        )

        # Create agent with AGNO framework
        agent = Agent(
            name=f"{role}_{self.config.name}",
            model=model,
            role=role,
            instructions=f"You are a {role} agent in the {self.config.name} team. Use your expertise to provide high-quality outputs for the given tasks.",
            description=f"A {role} agent specialized in {self.config.strategy.value} execution strategy.",
            context={
                "role": role,
                "team": self.config.name,
                "strategy": self.config.strategy.value,
                "provider": model_config["provider"],
                "model": model_config["model"],
                "virtual_key": model_config["virtual_key"]
            }
        )

        return agent

    @with_circuit_breaker("agno_execution")
    async def execute_task(
        self,
        task_description: str,
        context: dict[str, Any],
        model_overrides: Optional[dict[str, str]] = None
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

        # Apply model overrides if provided (skip for now, focus on basic functionality)
        # Note: Model overrides can be implemented later using agent.model updates

        # Task is just the description string for AGNO

        # Store task initiation in memory
        if self.memory_client and self.config.auto_tag:
            await auto_tag_and_store(
                self.memory_client,
                content=f"Task initiated: {task_description}",
                topic="Task Execution",
                execution_context=context
            )

        # Execute using AGNO Team
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Use AGNO Team.run() method - this handles the coordination automatically
            response = self.team.run(task_description)
            
            result = {
                "success": True,
                "result": response.content if hasattr(response, 'content') else str(response),
                "execution_time": asyncio.get_event_loop().time() - start_time,
                "strategy": self.config.strategy.value,
                "agents_used": [agent.name for agent in self.agents]
            }
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            result = {
                "success": False,
                "error": str(e),
                "execution_time": asyncio.get_event_loop().time() - start_time,
                "strategy": self.config.strategy.value
            }

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

    async def _create_specialized_agent(self, role: str, config: Dict[str, Any]) -> Agent:
        """Create specialized agent with base configuration - override in subclasses for personality"""
        
        agent = Agent(
            name=config['role'],
            model=config['model'],
            instructions=config['instructions'],
            extra_data={
                "role": config['role'],
                "team": self.config.name,
                "domain": getattr(self, 'domain', {}).get('value', 'general_operations') if hasattr(getattr(self, 'domain', {}), 'get') else str(getattr(self, 'domain', 'general_operations')),
                "personality_type": "base",
                "temperature": config.get('temperature', 0.5),
                "created_at": asyncio.get_event_loop().time() if hasattr(asyncio, 'get_event_loop') else 0
            }
        )
        
        return agent

    # Note: The old execution methods (_execute_standard, _execute_debate, _execute_consensus) 
    # have been replaced with direct AGNO Team.run() calls above.
    # AGNO handles team coordination automatically based on the team mode.


