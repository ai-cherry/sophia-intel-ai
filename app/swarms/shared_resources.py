"""
Shared Tools and Resources for Artemis and Sophia AGNO Systems
Provides common functionality while maintaining clear separation
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from agno.agent import Agent

logger = logging.getLogger(__name__)


class PersonalityType(Enum):
    """Different personality types for AI orchestrators"""

    SOPHIA_STRATEGIC = "sophia_strategic"
    ARTEMIS_TACTICAL = "artemis_tactical"
    NEUTRAL_BASE = "neutral_base"


@dataclass
class SharedResourceConfig:
    """Configuration for shared resources"""

    enable_memory: bool = True
    enable_voice: bool = False
    enable_cross_orchestrator_communication: bool = False
    shared_model_pool: bool = True
    resource_isolation_level: str = "moderate"  # strict, moderate, relaxed


class SharedToolsInterface(ABC):
    """Abstract interface for shared tools between orchestrators"""

    @abstractmethod
    async def get_optimal_model_for_role(
        self, role: str, personality: PersonalityType, task_complexity: float = 0.5
    ) -> dict[str, Any]:
        """Get optimal model configuration for a role with personality considerations"""
        pass

    @abstractmethod
    async def create_specialized_agent(
        self, role: str, config: dict[str, Any], personality: PersonalityType
    ) -> Agent:
        """Create specialized agent with personality-specific enhancements"""
        pass

    @abstractmethod
    async def get_shared_memory_client(self, orchestrator_id: str, session_id: str):
        """Get memory client with proper isolation"""
        pass


class SharedResourceManager:
    """Manages shared resources between Artemis and Sophia with proper isolation"""

    def __init__(self, config: SharedResourceConfig = None):
        self.config = config or SharedResourceConfig()
        self.memory_clients = {}
        self.model_pool = {}
        self.resource_locks = {}

    async def initialize(self):
        """Initialize shared resources"""
        logger.info("🔧 Initializing shared resources for Artemis/Sophia orchestrators")

        # Initialize model pool if enabled
        if self.config.shared_model_pool:
            await self._initialize_model_pool()

        # Initialize cross-orchestrator communication if enabled
        if self.config.enable_cross_orchestrator_communication:
            await self._initialize_communication_bridge()

        logger.info("✅ Shared resources initialized successfully")

    async def _initialize_model_pool(self):
        """Initialize shared model pool with proper resource management"""
        # Model configurations available to both orchestrators
        self.model_pool = {
            "strategic_models": {
                "high_complexity": {
                    "model": "claude-3-sonnet",
                    "provider": "portkey",
                    "temperature": 0.7,
                },
                "medium_complexity": {
                    "model": "gpt-4",
                    "provider": "portkey",
                    "temperature": 0.6,
                },
                "low_complexity": {
                    "model": "claude-3-haiku",
                    "provider": "portkey",
                    "temperature": 0.5,
                },
            },
            "tactical_models": {
                "high_precision": {
                    "model": "claude-3-opus",
                    "provider": "portkey",
                    "temperature": 0.3,
                },
                "analysis": {
                    "model": "gpt-4-turbo",
                    "provider": "portkey",
                    "temperature": 0.4,
                },
                "rapid_response": {
                    "model": "claude-3-haiku",
                    "provider": "portkey",
                    "temperature": 0.2,
                },
            },
            "shared_models": {
                "balanced": {
                    "model": "claude-3-sonnet",
                    "provider": "portkey",
                    "temperature": 0.5,
                },
                "creative": {
                    "model": "gpt-4",
                    "provider": "portkey",
                    "temperature": 0.8,
                },
                "analytical": {
                    "model": "claude-3-opus",
                    "provider": "portkey",
                    "temperature": 0.3,
                },
            },
        }

    async def _initialize_communication_bridge(self):
        """Initialize communication bridge between orchestrators"""
        logger.info("🌉 Setting up communication bridge between orchestrators")
        # Implementation for cross-orchestrator communication
        pass

    async def get_model_for_personality(
        self, role: str, personality: PersonalityType, complexity: float = 0.5
    ) -> dict[str, Any]:
        """Get appropriate model based on personality and role"""

        if personality == PersonalityType.SOPHIA_STRATEGIC:
            if complexity > 0.7:
                return self.model_pool["strategic_models"]["high_complexity"]
            elif complexity > 0.4:
                return self.model_pool["strategic_models"]["medium_complexity"]
            else:
                return self.model_pool["strategic_models"]["low_complexity"]

        elif personality == PersonalityType.ARTEMIS_TACTICAL:
            if "security" in role.lower() or "audit" in role.lower():
                return self.model_pool["tactical_models"]["high_precision"]
            elif "analysis" in role.lower():
                return self.model_pool["tactical_models"]["analysis"]
            else:
                return self.model_pool["tactical_models"]["rapid_response"]

        else:
            # Neutral/shared models
            if complexity > 0.7:
                return self.model_pool["shared_models"]["analytical"]
            elif complexity > 0.4:
                return self.model_pool["shared_models"]["balanced"]
            else:
                return self.model_pool["shared_models"]["creative"]

    async def create_agent_with_personality(
        self, role: str, config: dict[str, Any], personality: PersonalityType
    ) -> Agent:
        """Create agent with personality-specific enhancements while maintaining separation"""

        # Base agent configuration
        agent_config = {
            "name": config["role"],
            "model": config["model"],
            "instructions": config["instructions"],
        }

        # Add personality-specific enhancements
        if personality == PersonalityType.SOPHIA_STRATEGIC:
            agent_config["instructions"] = self._enhance_with_sophia_personality(
                config["instructions"], role
            )
            agent_config["extra_data"] = {
                "personality": "sophia_strategic_business_intelligence",
                "orchestrator": "sophia",
                "role": role,
                "domain": "strategic_operations",
                "temperature": config.get("temperature", 0.7),
            }

        elif personality == PersonalityType.ARTEMIS_TACTICAL:
            agent_config["instructions"] = self._enhance_with_artemis_personality(
                config["instructions"], role
            )
            agent_config["extra_data"] = {
                "personality": "artemis_tactical_technical_intelligence",
                "orchestrator": "artemis",
                "role": role,
                "domain": "tactical_operations",
                "temperature": config.get("temperature", 0.5),
            }
        else:
            agent_config["extra_data"] = {
                "personality": "neutral_base",
                "orchestrator": "shared",
                "role": role,
                "domain": "general_operations",
                "temperature": config.get("temperature", 0.6),
            }

        return Agent(**agent_config)

    def _enhance_with_sophia_personality(
        self, base_instructions: str, role: str
    ) -> str:
        """Add Sophia's strategic business intelligence personality"""
        personality_context = """
        You are part of Sophia's strategic business intelligence network with these characteristics:
        - Communication: Strategic, diplomatic, business-focused
        - Expertise: Senior business strategist and market analyst
        - Tone: Professional, insightful, forward-thinking
        - Focus: Business growth, market opportunities, strategic advantage

        Approach problems with business acumen and strategic thinking.
        Provide insights that drive business value and competitive advantage.
        Consider market dynamics, stakeholder impacts, and long-term strategic implications.
        """

        return f"{base_instructions}\n\n{personality_context}"

    def _enhance_with_artemis_personality(
        self, base_instructions: str, role: str
    ) -> str:
        """Add Artemis's tactical technical intelligence personality"""
        personality_context = """
        You are part of Artemis's tactical technical intelligence team with these characteristics:
        - Communication: Direct, tactical, technically precise
        - Expertise: Senior technical architect and systems engineer
        - Tone: Confident, passionate, no-nonsense
        - Focus: Technical excellence, system integrity, operational efficiency

        Address technical challenges with tactical precision and engineering expertise.
        Be direct about technical issues and provide actionable solutions.
        Think like a senior engineer focused on bulletproof systems and optimal performance.
        """

        return f"{base_instructions}\n\n{personality_context}"

    async def get_isolated_memory_client(self, orchestrator_id: str, session_id: str):
        """Get memory client with proper orchestrator isolation"""

        if self.config.resource_isolation_level == "strict":
            # Complete isolation - separate memory spaces
            namespace = f"{orchestrator_id}_isolated_{session_id}"
        elif self.config.resource_isolation_level == "moderate":
            # Moderate isolation - shared global but isolated session
            namespace = f"shared_global:{orchestrator_id}_{session_id}"
        else:  # relaxed
            # Relaxed isolation - shared memory with orchestrator tags
            namespace = f"shared:{session_id}"

        # Return memory client configured for appropriate isolation level
        # Implementation would connect to actual memory system
        return {
            "namespace": namespace,
            "isolation_level": self.config.resource_isolation_level,
            "orchestrator": orchestrator_id,
        }

    async def cleanup_resources(self, orchestrator_id: str):
        """Clean up resources for a specific orchestrator"""
        logger.info(f"🧹 Cleaning up shared resources for {orchestrator_id}")

        # Clean up memory clients
        keys_to_remove = [
            key for key in self.memory_clients if key.startswith(orchestrator_id)
        ]
        for key in keys_to_remove:
            del self.memory_clients[key]

        # Release resource locks
        locks_to_release = [
            lock for lock in self.resource_locks if lock.startswith(orchestrator_id)
        ]
        for lock in locks_to_release:
            del self.resource_locks[lock]

        logger.info(f"✅ Resources cleaned up for {orchestrator_id}")


# Global shared resource manager instance
shared_resources = SharedResourceManager()


class PersonalityAGNOTeam:
    """Enhanced base class for personality-aware AGNO teams"""

    def __init__(self, personality: PersonalityType):
        self.personality = personality
        self.shared_resources = shared_resources

    async def create_personality_agent(
        self, role: str, config: dict[str, Any]
    ) -> Agent:
        """Create agent with appropriate personality enhancements"""

        # Get optimal model for this personality and role
        model_config = await self.shared_resources.get_model_for_personality(
            role, self.personality, config.get("complexity", 0.5)
        )

        # Update config with optimal model
        enhanced_config = {**config, **model_config}

        # Create agent with personality
        return await self.shared_resources.create_agent_with_personality(
            role, enhanced_config, self.personality
        )

    async def get_memory_client(self, orchestrator_id: str, session_id: str):
        """Get appropriately isolated memory client"""
        return await self.shared_resources.get_isolated_memory_client(
            orchestrator_id, session_id
        )


# Utility functions for orchestrator integration
async def initialize_shared_resources(config: SharedResourceConfig = None):
    """Initialize shared resources - call during orchestrator startup"""
    await shared_resources.initialize()
    return shared_resources


async def get_personality_for_orchestrator(orchestrator_name: str) -> PersonalityType:
    """Get appropriate personality type for orchestrator"""
    mapping = {
        "sophia": PersonalityType.SOPHIA_STRATEGIC,
        "artemis": PersonalityType.ARTEMIS_TACTICAL,
    }
    return mapping.get(orchestrator_name.lower(), PersonalityType.NEUTRAL_BASE)
