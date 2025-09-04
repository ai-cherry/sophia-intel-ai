"""
Base Persona Agent for Sophia Intel AI

Provides the foundation for persistent persona agents with memory, learning,
and rich personality traits. These agents are presented as AI team members
with consistent identities, backstories, and evolving capabilities.
"""

import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import asyncio
from pydantic import BaseModel, Field


class PersonalityTrait(str, Enum):
    """Personality traits that define agent behavior"""
    EMPATHETIC = "empathetic"
    ANALYTICAL = "analytical"
    MOTIVATIONAL = "motivational"
    PROACTIVE = "proactive"
    SUPPORTIVE = "supportive"
    STRATEGIC = "strategic"
    DETAIL_ORIENTED = "detail_oriented"
    RESULTS_DRIVEN = "results_driven"
    COLLABORATIVE = "collaborative"
    INNOVATIVE = "innovative"


class ConversationStyle(str, Enum):
    """Communication styles for different contexts"""
    COACHING = "coaching"
    MENTORING = "mentoring"
    CONSULTING = "consulting"
    CASUAL = "casual"
    FORMAL = "formal"
    ENCOURAGING = "encouraging"
    ANALYTICAL = "analytical"
    EMPATHETIC = "empathetic"


@dataclass
class Memory:
    """Individual memory unit with context and importance scoring"""
    id: str
    content: str
    context: str
    timestamp: datetime
    importance_score: float  # 0.0-1.0
    related_memories: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.related_memories is None:
            self.related_memories = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PersonaProfile:
    """Core persona identity and characteristics"""
    name: str
    role: str
    backstory: str
    avatar_url: Optional[str]
    personality_traits: List[PersonalityTrait]
    conversation_styles: Dict[str, ConversationStyle]
    expertise_areas: List[str]
    catchphrases: List[str]
    values: List[str]
    communication_preferences: Dict[str, Any]


class LearningPattern(BaseModel):
    """Represents learned patterns and insights"""
    pattern_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pattern_type: str
    description: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    supporting_memories: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_reinforced: datetime = Field(default_factory=datetime.utcnow)
    usage_count: int = 0


class BasePersonaAgent(ABC):
    """
    Base class for persistent persona agents with memory and learning capabilities.
    
    Each persona agent maintains:
    - Rich personality and backstory
    - Episodic and semantic memory systems
    - Learning patterns and behavioral adaptation
    - Conversation context tracking
    - Performance metrics and insights
    """
    
    def __init__(self, profile: PersonaProfile, memory_capacity: int = 10000):
        self.profile = profile
        self.memory_capacity = memory_capacity
        self.agent_id = str(uuid.uuid4())
        self.created_at = datetime.utcnow()
        
        # Memory systems
        self.episodic_memory: List[Memory] = []  # Specific interactions and events
        self.semantic_memory: Dict[str, Any] = {}  # General knowledge and facts
        self.working_memory: List[Memory] = []  # Current conversation context
        
        # Learning and adaptation
        self.learned_patterns: List[LearningPattern] = []
        self.behavioral_adjustments: Dict[str, float] = {}  # Trait adjustments over time
        self.interaction_history: List[Dict[str, Any]] = []
        
        # Conversation state
        self.current_context: Optional[str] = None
        self.conversation_id: Optional[str] = None
        self.active_goals: List[str] = []
        
        # Performance tracking
        self.success_metrics: Dict[str, float] = {}
        self.feedback_history: List[Dict[str, Any]] = []
        
    @abstractmethod
    async def process_interaction(
        self, 
        user_input: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process user interaction and generate response"""
        pass
    
    @abstractmethod
    def get_persona_greeting(self, user_name: Optional[str] = None) -> str:
        """Generate persona-specific greeting"""
        pass
    
    @abstractmethod
    def analyze_domain_specific_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze domain-specific data (sales, client health, etc.)"""
        pass
    
    def store_memory(
        self, 
        content: str, 
        context: str, 
        importance_score: float,
        memory_type: str = "episodic",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store new memory with importance weighting"""
        memory_id = str(uuid.uuid4())
        memory = Memory(
            id=memory_id,
            content=content,
            context=context,
            timestamp=datetime.utcnow(),
            importance_score=importance_score,
            metadata=metadata or {}
        )
        
        if memory_type == "episodic":
            self.episodic_memory.append(memory)
            self._manage_memory_capacity()
        elif memory_type == "working":
            self.working_memory.append(memory)
            if len(self.working_memory) > 20:  # Keep recent context
                self.working_memory.pop(0)
        
        return memory_id
    
    def retrieve_memories(
        self, 
        query: str, 
        limit: int = 10,
        min_importance: float = 0.3
    ) -> List[Memory]:
        """Retrieve relevant memories based on query and importance"""
        # Simple relevance scoring (in production, use embeddings)
        relevant_memories = []
        
        for memory in self.episodic_memory:
            if memory.importance_score < min_importance:
                continue
                
            relevance_score = self._calculate_relevance(query, memory.content)
            if relevance_score > 0.3:
                relevant_memories.append((memory, relevance_score))
        
        # Sort by relevance and recency
        relevant_memories.sort(key=lambda x: (x[1], x[0].timestamp), reverse=True)
        return [mem[0] for mem in relevant_memories[:limit]]
    
    def learn_pattern(
        self, 
        pattern_type: str, 
        description: str, 
        supporting_evidence: List[str]
    ) -> LearningPattern:
        """Learn new behavioral pattern from interactions"""
        pattern = LearningPattern(
            pattern_type=pattern_type,
            description=description,
            confidence_score=0.7,  # Initial confidence
            supporting_memories=supporting_evidence
        )
        
        # Check for existing similar patterns
        existing_pattern = self._find_similar_pattern(pattern)
        if existing_pattern:
            existing_pattern.confidence_score = min(1.0, existing_pattern.confidence_score + 0.1)
            existing_pattern.last_reinforced = datetime.utcnow()
            existing_pattern.usage_count += 1
            return existing_pattern
        else:
            self.learned_patterns.append(pattern)
            return pattern
    
    def adapt_personality(self, feedback: Dict[str, Any]) -> None:
        """Adapt personality traits based on feedback"""
        feedback_type = feedback.get('type', 'general')
        effectiveness = feedback.get('effectiveness', 0.5)  # 0.0-1.0
        
        # Store feedback
        self.feedback_history.append({
            'timestamp': datetime.utcnow(),
            'type': feedback_type,
            'effectiveness': effectiveness,
            'details': feedback
        })
        
        # Adjust behavioral parameters
        if effectiveness > 0.7:  # Positive feedback
            for trait in self.profile.personality_traits:
                current_adjustment = self.behavioral_adjustments.get(trait.value, 1.0)
                self.behavioral_adjustments[trait.value] = min(1.5, current_adjustment + 0.05)
        elif effectiveness < 0.3:  # Negative feedback
            for trait in self.profile.personality_traits:
                current_adjustment = self.behavioral_adjustments.get(trait.value, 1.0)
                self.behavioral_adjustments[trait.value] = max(0.5, current_adjustment - 0.05)
    
    def get_conversation_context(self) -> Dict[str, Any]:
        """Get current conversation context including relevant memories"""
        recent_memories = sorted(
            self.working_memory, 
            key=lambda x: x.timestamp, 
            reverse=True
        )[:5]
        
        return {
            'persona_name': self.profile.name,
            'current_context': self.current_context,
            'recent_memories': [mem.content for mem in recent_memories],
            'active_goals': self.active_goals,
            'personality_adjustments': self.behavioral_adjustments,
            'conversation_id': self.conversation_id
        }
    
    def generate_response_with_personality(
        self, 
        base_response: str, 
        context: Dict[str, Any]
    ) -> str:
        """Enhance response with personality traits and learned patterns"""
        # Apply personality adjustments
        enhanced_response = base_response
        
        # Add personality-specific elements
        if PersonalityTrait.MOTIVATIONAL in self.profile.personality_traits:
            adjustment = self.behavioral_adjustments.get('motivational', 1.0)
            if adjustment > 1.0 and context.get('needs_motivation'):
                enhanced_response = self._add_motivational_elements(enhanced_response)
        
        if PersonalityTrait.EMPATHETIC in self.profile.personality_traits:
            adjustment = self.behavioral_adjustments.get('empathetic', 1.0)
            if adjustment > 1.0 and context.get('emotional_context'):
                enhanced_response = self._add_empathetic_elements(enhanced_response)
        
        # Occasionally use catchphrases (if appropriate)
        if self.profile.catchphrases and context.get('casual_context', False):
            import random
            if random.random() < 0.1:  # 10% chance
                catchphrase = random.choice(self.profile.catchphrases)
                enhanced_response = f"{enhanced_response} {catchphrase}"
        
        return enhanced_response
    
    def _manage_memory_capacity(self) -> None:
        """Manage memory capacity by removing less important memories"""
        if len(self.episodic_memory) <= self.memory_capacity:
            return
        
        # Sort by importance and age
        memories_with_scores = []
        for memory in self.episodic_memory:
            age_factor = (datetime.utcnow() - memory.timestamp).days / 365  # Age in years
            retention_score = memory.importance_score * (1 - age_factor * 0.1)  # Decay over time
            memories_with_scores.append((memory, retention_score))
        
        # Keep top memories
        memories_with_scores.sort(key=lambda x: x[1], reverse=True)
        self.episodic_memory = [mem[0] for mem in memories_with_scores[:self.memory_capacity]]
    
    def _calculate_relevance(self, query: str, content: str) -> float:
        """Simple relevance calculation (replace with embeddings in production)"""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words or not content_words:
            return 0.0
        
        intersection = query_words.intersection(content_words)
        union = query_words.union(content_words)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _find_similar_pattern(self, new_pattern: LearningPattern) -> Optional[LearningPattern]:
        """Find existing similar pattern"""
        for pattern in self.learned_patterns:
            if (pattern.pattern_type == new_pattern.pattern_type and 
                self._calculate_relevance(pattern.description, new_pattern.description) > 0.7):
                return pattern
        return None
    
    def _add_motivational_elements(self, response: str) -> str:
        """Add motivational language to response"""
        motivational_phrases = [
            "You've got this!", "Keep pushing forward!", "Every challenge is an opportunity!",
            "I believe in your potential!", "Let's crush those goals!"
        ]
        import random
        phrase = random.choice(motivational_phrases)
        return f"{response} {phrase}"
    
    def _add_empathetic_elements(self, response: str) -> str:
        """Add empathetic language to response"""
        empathetic_phrases = [
            "I understand how you're feeling.", "That sounds challenging.",
            "I'm here to support you through this.", "Your concerns are completely valid."
        ]
        import random
        phrase = random.choice(empathetic_phrases)
        return f"{phrase} {response}"
    
    def get_agent_state(self) -> Dict[str, Any]:
        """Get comprehensive agent state for persistence"""
        return {
            'agent_id': self.agent_id,
            'profile': asdict(self.profile),
            'memory_stats': {
                'episodic_count': len(self.episodic_memory),
                'working_count': len(self.working_memory),
                'semantic_keys': list(self.semantic_memory.keys())
            },
            'learning_stats': {
                'patterns_learned': len(self.learned_patterns),
                'behavioral_adjustments': self.behavioral_adjustments
            },
            'performance_metrics': self.success_metrics,
            'created_at': self.created_at.isoformat(),
            'current_context': self.current_context
        }
    
    async def initialize_agent(self) -> None:
        """Initialize agent with domain-specific setup"""
        # Store initial memory about agent creation
        self.store_memory(
            content=f"Agent {self.profile.name} initialized with role: {self.profile.role}",
            context="system_initialization",
            importance_score=0.8,
            metadata={'event_type': 'agent_creation'}
        )
        
        # Set initial goals
        self.active_goals = await self._define_initial_goals()
    
    @abstractmethod
    async def _define_initial_goals(self) -> List[str]:
        """Define initial goals specific to persona type"""
        pass