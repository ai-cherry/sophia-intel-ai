"""
Artemis Portkey-Integrated Unified Factory
Extends the ArtemisUnifiedFactory with Portkey routing for all LLM operations
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from app.artemis.unified_factory import (
    AgentProfile,
    ArtemisUnifiedFactory,
    SwarmType,
    TechnicalAgentRole,
)
from app.core.portkey_config import PortkeyManager, get_portkey_manager
from app.core.vector_db_config import get_vector_db_manager
from app.memory.unified_memory import store_memory

logger = logging.getLogger(__name__)


class PortkeyArtemisFactory(ArtemisUnifiedFactory):
    """
    Enhanced Artemis Factory with Portkey integration for centralized LLM routing
    """

    def __init__(self):
        super().__init__()
        self.portkey_manager: PortkeyManager = get_portkey_manager()
        self.vector_db = get_vector_db_manager()
        self._initialize_portkey_routing()

    def _initialize_portkey_routing(self):
        """Initialize Portkey routing configuration"""
        # Map agent roles to optimal providers
        self.role_provider_mapping = {
            TechnicalAgentRole.CODE_REVIEWER: "openai",
            TechnicalAgentRole.SECURITY_AUDITOR: "anthropic",
            TechnicalAgentRole.PERFORMANCE_OPTIMIZER: "deepseek",
            TechnicalAgentRole.ARCHITECTURE_CRITIC: "anthropic",
            TechnicalAgentRole.VULNERABILITY_SCANNER: "groq",
            TechnicalAgentRole.TACTICAL_ANALYST: "openai",
            TechnicalAgentRole.THREAT_HUNTER: "mistral",
            TechnicalAgentRole.SYSTEM_ARCHITECT: "anthropic",
            TechnicalAgentRole.CODE_REFACTORING_SPECIALIST: "deepseek",
        }

        # Model selection by provider
        self.provider_model_mapping = {
            "openai": "gpt-4-turbo",
            "anthropic": "claude-3-sonnet",
            "deepseek": "deepseek-coder",
            "groq": "llama-3.1-70b-versatile",
            "mistral": "mistral-large",
            "together": "meta-llama/Llama-3-70b-chat",
            "perplexity": "pplx-70b-online",
            "xai": "grok-beta",
            "cohere": "command-r-plus",
            "gemini": "gemini-1.5-pro",
        }

        logger.info("Portkey routing initialized for Artemis Factory")

    async def create_agent_with_portkey(
        self, name: str, role: TechnicalAgentRole, specialty: str = None, **kwargs
    ) -> AgentProfile:
        """
        Create an agent with Portkey-routed LLM access

        Args:
            name: Agent name
            role: Technical role
            specialty: Optional specialty
            **kwargs: Additional configuration

        Returns:
            Configured AgentProfile with Portkey routing
        """
        # Determine optimal provider for role
        provider = self.role_provider_mapping.get(role, "openai")
        model = self.provider_model_mapping.get(provider, "gpt-4")

        # Get virtual key for provider
        virtual_key = self.portkey_manager.get_virtual_key(provider)

        if not virtual_key:
            logger.warning(f"No virtual key for {provider}, falling back to OpenAI")
            provider = "openai"
            virtual_key = self.portkey_manager.get_virtual_key("openai")

        # Create agent profile with Portkey configuration
        agent_profile = AgentProfile(
            id=str(uuid4()),
            name=name,
            role=role.value,
            model=model,
            specialty=specialty or role.value,
            virtual_key=virtual_key,
            capabilities=self._get_role_capabilities(role),
            tools=self._get_role_tools(role),
            tactical_traits={
                "provider": provider,
                "portkey_enabled": True,
                "fallback_providers": self._get_fallback_providers(provider),
            },
        )

        # Store in memory if enabled
        if self.config.enable_memory_integration:
            await self._store_agent_in_memory(agent_profile)

        # Store in vector DB for semantic search
        if self.vector_db.qdrant:
            await self._store_agent_in_vector_db(agent_profile)

        return agent_profile

    def _get_role_capabilities(self, role: TechnicalAgentRole) -> list[str]:
        """Get capabilities based on role"""
        capabilities_map = {
            TechnicalAgentRole.CODE_REVIEWER: [
                "code_analysis",
                "best_practice_validation",
                "bug_detection",
            ],
            TechnicalAgentRole.SECURITY_AUDITOR: [
                "vulnerability_scanning",
                "security_compliance",
                "threat_modeling",
            ],
            TechnicalAgentRole.PERFORMANCE_OPTIMIZER: [
                "performance_profiling",
                "optimization_recommendations",
                "bottleneck_detection",
            ],
            TechnicalAgentRole.ARCHITECTURE_CRITIC: [
                "architecture_review",
                "design_pattern_analysis",
                "scalability_assessment",
            ],
            TechnicalAgentRole.VULNERABILITY_SCANNER: [
                "cve_detection",
                "dependency_scanning",
                "security_patching",
            ],
            TechnicalAgentRole.TACTICAL_ANALYST: [
                "tactical_planning",
                "resource_optimization",
                "mission_coordination",
            ],
            TechnicalAgentRole.THREAT_HUNTER: [
                "threat_detection",
                "anomaly_analysis",
                "incident_response",
            ],
            TechnicalAgentRole.SYSTEM_ARCHITECT: [
                "system_design",
                "integration_planning",
                "technology_selection",
            ],
            TechnicalAgentRole.CODE_REFACTORING_SPECIALIST: [
                "code_restructuring",
                "technical_debt_reduction",
                "pattern_implementation",
            ],
        }
        return capabilities_map.get(role, ["general_analysis"])

    def _get_role_tools(self, role: TechnicalAgentRole) -> list[str]:
        """Get tools based on role"""
        tools_map = {
            TechnicalAgentRole.CODE_REVIEWER: [
                "ast_parser",
                "linter",
                "complexity_analyzer",
            ],
            TechnicalAgentRole.SECURITY_AUDITOR: [
                "vulnerability_scanner",
                "dependency_checker",
                "sast_tool",
            ],
            TechnicalAgentRole.PERFORMANCE_OPTIMIZER: [
                "profiler",
                "benchmark_runner",
                "metrics_collector",
            ],
            TechnicalAgentRole.VULNERABILITY_SCANNER: [
                "cve_database",
                "exploit_checker",
                "patch_manager",
            ],
            TechnicalAgentRole.CODE_REFACTORING_SPECIALIST: [
                "refactoring_tool",
                "test_generator",
                "documentation_builder",
            ],
        }
        return tools_map.get(role, ["text_analyzer"])

    def _get_fallback_providers(self, primary_provider: str) -> list[str]:
        """Get fallback providers for a primary provider"""
        config = self.portkey_manager.get_provider_config(primary_provider)
        return config.fallback_providers if config else []

    async def _store_agent_in_memory(self, agent: AgentProfile):
        """Store agent profile in memory system"""
        try:
            memory_data = {
                "id": agent.id,
                "name": agent.name,
                "role": agent.role,
                "model": agent.model,
                "virtual_key": agent.virtual_key,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            await store_memory(
                memory_id=f"artemis_agent_{agent.id}",
                memory_type="agent_profile",
                content=json.dumps(memory_data),
                metadata={
                    "domain": "ARTEMIS",
                    "role": agent.role,
                    "provider": agent.tactical_traits.get("provider", "unknown"),
                },
            )
            logger.debug(f"Stored agent {agent.name} in memory")
        except Exception as e:
            logger.error(f"Failed to store agent in memory: {e}")

    async def _store_agent_in_vector_db(self, agent: AgentProfile):
        """Store agent profile in vector database for semantic search"""
        try:
            # Create text representation for embedding
            agent_text = f"""
            Agent: {agent.name}
            Role: {agent.role}
            Specialty: {agent.specialty}
            Capabilities: {', '.join(agent.capabilities)}
            Tools: {', '.join(agent.tools)}
            Model: {agent.model}
            """

            # Generate embedding using Portkey
            embedding_response = self.portkey_manager.create_embedding(
                provider="openai", model="text-embedding-3-small", input_text=agent_text
            )

            if embedding_response and hasattr(embedding_response, "data"):
                vector = embedding_response.data[0].embedding

                # Store in Qdrant
                self.vector_db.store_vector(
                    db_type="qdrant",
                    collection="artemis_tactical",
                    vector=vector,
                    payload={
                        "agent_id": agent.id,
                        "name": agent.name,
                        "role": agent.role,
                        "specialty": agent.specialty,
                        "model": agent.model,
                        "provider": agent.tactical_traits.get("provider", "unknown"),
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    },
                    id=agent.id,
                )
                logger.debug(f"Stored agent {agent.name} in vector database")
        except Exception as e:
            logger.error(f"Failed to store agent in vector DB: {e}")

    async def execute_with_portkey(
        self,
        agent: AgentProfile,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Execute a task using Portkey routing

        Args:
            agent: Agent profile
            prompt: Task prompt
            temperature: Generation temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters

        Returns:
            Execution result with metadata
        """
        provider = agent.tactical_traits.get("provider", "openai")

        try:
            # Prepare messages
            messages = [
                {"role": "system", "content": self._generate_system_prompt(agent)},
                {"role": "user", "content": prompt},
            ]

            # Execute with Portkey
            start_time = datetime.now(timezone.utc)
            response = self.portkey_manager.create_completion(
                provider=provider,
                model=agent.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            # Extract response
            if response and hasattr(response, "choices"):
                content = response.choices[0].message.content

                # Cache result if Redis available
                if self.vector_db.redis:
                    cache_key = f"artemis:{agent.id}:{hash(prompt)}"
                    self.vector_db.cache_set(cache_key, content, ttl=3600)

                # Store in Mem0 if available
                if self.vector_db.mem0:
                    self.vector_db.add_memory(
                        user_id=agent.id,
                        content=f"Task: {prompt[:100]}... Response: {content[:200]}...",
                        metadata={
                            "agent": agent.name,
                            "role": agent.role,
                            "provider": provider,
                            "execution_time": execution_time,
                        },
                    )

                return {
                    "success": True,
                    "response": content,
                    "agent": agent.name,
                    "provider": provider,
                    "model": agent.model,
                    "execution_time": execution_time,
                    "tokens_used": (
                        getattr(response.usage, "total_tokens", 0)
                        if hasattr(response, "usage")
                        else 0
                    ),
                }
            else:
                raise ValueError("Invalid response from Portkey")

        except Exception as e:
            logger.error(f"Execution failed for agent {agent.name}: {e}")

            # Try fallback providers
            fallback_providers = agent.tactical_traits.get("fallback_providers", [])
            for fallback in fallback_providers:
                try:
                    logger.info(f"Attempting fallback to {fallback}")
                    agent.tactical_traits["provider"] = fallback
                    agent.model = self.provider_model_mapping.get(fallback, agent.model)
                    return await self.execute_with_portkey(
                        agent, prompt, temperature, max_tokens, **kwargs
                    )
                except Exception as fallback_error:
                    logger.error(f"Fallback to {fallback} failed: {fallback_error}")
                    continue

            return {
                "success": False,
                "error": str(e),
                "agent": agent.name,
                "provider": provider,
            }

    def _generate_system_prompt(self, agent: AgentProfile) -> str:
        """Generate system prompt for agent"""
        return f"""You are {agent.name}, a specialized {agent.role} agent in the Artemis tactical operations system.

Your specialty is: {agent.specialty}

Your capabilities include:
{chr(10).join(f"- {cap}" for cap in agent.capabilities)}

You have access to these tools:
{chr(10).join(f"- {tool}" for tool in agent.tools)}

Operating Parameters:
- Maintain tactical precision in all operations
- Provide clear, actionable intelligence
- Follow security protocols at all times
- Report anomalies immediately
- Optimize for mission success

Your responses should be direct, technical, and focused on the mission objectives."""

    async def create_swarm_with_portkey(
        self, swarm_type: SwarmType, mission_name: str, agent_count: int = 3, **kwargs
    ) -> dict[str, Any]:
        """
        Create a swarm with Portkey-routed agents

        Args:
            swarm_type: Type of swarm
            mission_name: Mission identifier
            agent_count: Number of agents
            **kwargs: Additional configuration

        Returns:
            Swarm configuration with agents
        """
        # Select diverse providers for swarm agents
        providers = self.portkey_manager.get_available_providers()
        selected_providers = (
            providers[:agent_count]
            if len(providers) >= agent_count
            else providers * (agent_count // len(providers) + 1)
        )

        agents = []
        for i in range(agent_count):
            role = list(TechnicalAgentRole)[i % len(TechnicalAgentRole)]
            provider = selected_providers[i % len(selected_providers)]

            agent = await self.create_agent_with_portkey(
                name=f"{mission_name}_agent_{i}",
                role=role,
                specialty=f"{swarm_type.value}_specialist",
            )

            # Override provider for diversity
            agent.tactical_traits["provider"] = provider
            agent.model = self.provider_model_mapping.get(provider, agent.model)
            agent.virtual_key = self.portkey_manager.get_virtual_key(provider)

            agents.append(agent)

        swarm_config = {
            "id": str(uuid4()),
            "type": swarm_type.value,
            "mission": mission_name,
            "agents": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "role": agent.role,
                    "provider": agent.tactical_traits.get("provider"),
                    "model": agent.model,
                }
                for agent in agents
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "portkey_enabled": True,
            "provider_diversity": len(
                {a.tactical_traits.get("provider") for a in agents}
            ),
        }

        # Store swarm configuration
        if self.config.enable_memory_integration:
            await store_memory(
                memory_id=f"artemis_swarm_{swarm_config['id']}",
                memory_type="swarm_config",
                content=json.dumps(swarm_config),
                metadata={
                    "domain": "ARTEMIS",
                    "swarm_type": swarm_type.value,
                    "agent_count": agent_count,
                },
            )

        return swarm_config

    async def health_check(self) -> dict[str, Any]:
        """Perform comprehensive health check"""
        portkey_health = self.portkey_manager.health_check()
        vector_db_health = self.vector_db.health_check()

        return {
            "status": "operational",
            "portkey_providers": portkey_health,
            "vector_databases": vector_db_health,
            "factory": {
                "domain": self.config.domain,
                "max_concurrent_tasks": self.config.max_concurrent_tasks,
                "tactical_mode": self.config.tactical_mode_enabled,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Singleton instance
_portkey_artemis_factory: Optional[PortkeyArtemisFactory] = None


def get_portkey_artemis_factory() -> PortkeyArtemisFactory:
    """Get singleton instance of PortkeyArtemisFactory"""
    global _portkey_artemis_factory
    if _portkey_artemis_factory is None:
        _portkey_artemis_factory = PortkeyArtemisFactory()
    return _portkey_artemis_factory
