"""
Base Persona Agent Module
Provides the foundation for all AI persona agents in the system
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ConversationStyle(Enum):
    """Conversation styles for persona interactions"""

    PROFESSIONAL = "professional"
    CASUAL = "casual"
    COACHING = "coaching"
    ANALYTICAL = "analytical"
    ENCOURAGING = "encouraging"
    CONSULTING = "consulting"
    SUPPORTIVE = "supportive"
    TECHNICAL = "technical"
    MOTIVATIONAL = "motivational"


class PersonalityTrait(Enum):
    """Personality traits for personas"""

    MOTIVATIONAL = "motivational"
    ANALYTICAL = "analytical"
    SUPPORTIVE = "supportive"
    STRATEGIC = "strategic"
    RESULTS_DRIVEN = "results_driven"
    EMPATHETIC = "empathetic"
    DETAIL_ORIENTED = "detail_oriented"
    CREATIVE = "creative"
    DECISIVE = "decisive"
    PATIENT = "patient"
    ENTHUSIASTIC = "enthusiastic"
    DIPLOMATIC = "diplomatic"


@dataclass
class PersonaProfile:
    """Complete profile for a persona agent"""

    name: str
    role: str
    backstory: str
    avatar_url: str = ""
    personality_traits: list[PersonalityTrait] = field(default_factory=list)
    conversation_styles: dict[str, ConversationStyle] = field(default_factory=dict)
    expertise_areas: list[str] = field(default_factory=list)
    catchphrases: list[str] = field(default_factory=list)
    values: list[str] = field(default_factory=list)
    communication_preferences: dict[str, str] = field(default_factory=dict)


@dataclass
class Memory:
    """Memory entry for persona agents"""

    content: str
    context: str
    timestamp: datetime
    importance_score: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert memory to dictionary"""
        return {
            "content": self.content,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "importance_score": self.importance_score,
            "metadata": self.metadata,
        }


class BasePersonaAgent(ABC):
    """
    Base class for all persona agents
    Provides memory management, personality, and interaction framework
    """

    def __init__(self, profile: PersonaProfile, memory_capacity: int = 10000):
        """Initialize base persona agent"""
        self.profile = profile
        self.memory_capacity = memory_capacity

        # Personality attributes (for backward compatibility)
        self.personality = {
            "name": profile.name,
            "title": profile.role,
            "tagline": (
                profile.backstory[:100] + "..."
                if len(profile.backstory) > 100
                else profile.backstory
            ),
            "traits": [trait.value for trait in profile.personality_traits],
            "conversation_styles": {
                k: v.value for k, v in profile.conversation_styles.items()
            },
            "expertise": profile.expertise_areas,
            "catchphrases": profile.catchphrases,
            "values": profile.values,
            "communication_preferences": profile.communication_preferences,
        }

        # Memory systems
        self.episodic_memory: list[Memory] = []
        self.semantic_memory: dict[str, Any] = {}
        self.working_memory: dict[str, Any] = {}
        self.procedural_memory: dict[str, Any] = {}

        # Learning and adaptation
        self.learning_patterns: dict[str, float] = {}
        self.pattern_confidence: dict[str, float] = {}
        self.interaction_count = 0
        self.conversation_count = 0

        # Initialize agent-specific components
        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize agent-specific components (can be overridden)"""
        pass

    async def initialize(self):
        """Initialize the persona agent"""
        logger.info(f"Initializing persona agent: {self.profile.name}")
        # Any async initialization logic can go here
        return True

    def store_memory(
        self,
        content: str,
        context: str,
        importance_score: float,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """Store a memory in episodic memory"""
        memory = Memory(
            content=content,
            context=context,
            timestamp=datetime.now(),
            importance_score=importance_score,
            metadata=metadata or {},
        )

        self.episodic_memory.append(memory)

        # Manage memory capacity
        if len(self.episodic_memory) > self.memory_capacity:
            # Remove least important memories
            self.episodic_memory.sort(key=lambda m: m.importance_score, reverse=True)
            self.episodic_memory = self.episodic_memory[: self.memory_capacity]

    def recall_memories(self, context: str, limit: int = 5) -> list[Memory]:
        """Recall relevant memories based on context"""
        relevant_memories = [
            m
            for m in self.episodic_memory
            if context.lower() in m.context.lower()
            or context.lower() in m.content.lower()
        ]

        # Sort by importance and recency
        relevant_memories.sort(
            key=lambda m: (m.importance_score, m.timestamp.timestamp()), reverse=True
        )

        return relevant_memories[:limit]

    async def interact(self, message: str, context: dict[str, Any]) -> str:
        """Main interaction method for the persona"""
        self.interaction_count += 1
        self.conversation_count += 1

        # Store the interaction
        self.store_memory(
            content=f"User: {message}",
            context="conversation",
            importance_score=0.5,
            metadata=context,
        )

        # Process the interaction (to be implemented by subclasses)
        response_data = await self.process_interaction(message, context)

        # Generate response with personality
        response = self.generate_response_with_personality(response_data)

        # Store the response
        self.store_memory(
            content=f"Agent: {response}",
            context="conversation",
            importance_score=0.5,
            metadata={"response_data": response_data},
        )

        return response

    @abstractmethod
    async def process_interaction(
        self, user_input: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Process user interaction - must be implemented by subclasses"""
        pass

    @abstractmethod
    def get_persona_greeting(self, user_name: Optional[str] = None) -> str:
        """Generate persona-specific greeting - must be implemented by subclasses"""
        pass

    def generate_response_with_personality(self, response_data: dict[str, Any]) -> str:
        """Generate response with persona's personality"""
        # Default implementation - can be overridden
        if isinstance(response_data, dict) and "message" in response_data:
            return response_data["message"]
        return str(response_data)

    def learn_from_feedback(self, feedback: dict[str, Any]):
        """Learn from user feedback"""
        rating = feedback.get("rating", 3)
        interaction_id = feedback.get("interaction_id")

        # Update learning patterns
        pattern_key = f"feedback_{interaction_id}"
        self.learning_patterns[pattern_key] = rating / 5.0

        # Update confidence scores
        if rating >= 4:
            self.pattern_confidence[pattern_key] = min(
                self.pattern_confidence.get(pattern_key, 0.5) + 0.1, 1.0
            )
        else:
            self.pattern_confidence[pattern_key] = max(
                self.pattern_confidence.get(pattern_key, 0.5) - 0.1, 0.0
            )

    def get_stats(self) -> dict[str, Any]:
        """Get persona statistics"""
        return {
            "interaction_count": self.interaction_count,
            "conversation_count": self.conversation_count,
            "memory_count": len(self.episodic_memory),
            "learning_patterns": len(self.learning_patterns),
            "average_confidence": sum(self.pattern_confidence.values())
            / max(len(self.pattern_confidence), 1),
        }

    def export_memories(self) -> str:
        """Export memories as JSON"""
        memories = [m.to_dict() for m in self.episodic_memory]
        return json.dumps(memories, indent=2, default=str)

    def import_memories(self, memories_json: str):
        """Import memories from JSON"""
        memories_data = json.loads(memories_json)
        for mem_data in memories_data:
            memory = Memory(
                content=mem_data["content"],
                context=mem_data["context"],
                timestamp=datetime.fromisoformat(mem_data["timestamp"]),
                importance_score=mem_data["importance_score"],
                metadata=mem_data.get("metadata", {}),
            )
            self.episodic_memory.append(memory)

    def _initialize_methodologies(self) -> dict[str, dict[str, Any]]:
        """Initialize agent-specific methodologies (for subclasses)"""
        return {}

    def _initialize_coaching_templates(self) -> dict[str, str]:
        """Initialize coaching templates (for subclasses)"""
        return {}


# Export key components
__all__ = [
    "BasePersonaAgent",
    "ConversationStyle",
    "PersonalityTrait",
    "PersonaProfile",
    "Memory",
]
