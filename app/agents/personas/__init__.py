"""
Sophia Intel AI - Persistent Persona Agents

This module provides specialized AI agents with rich personalities, persistent memory,
and learning capabilities. These agents are presented as AI team members with
consistent identities and evolving expertise.

Available Personas:
- Marcus "The Catalyst" Rodriguez: Sales Coach & Performance Catalyst
- Dr. Sarah "The Guardian" Chen: Client Success Strategist & Health Guardian

Each persona agent provides:
- Rich personality with backstory and values
- Persistent memory and learning from interactions
- Domain-specific expertise and coaching
- Adaptive behavior based on feedback
- Integration with CRM and business data
"""

from .base_persona import (
    BasePersonaAgent,
    PersonaProfile,
    PersonalityTrait,
    ConversationStyle,
    Memory,
    LearningPattern,
    HealthStatus,
)

from .sales_coach import SalesCoachAgent
from .client_health import ClientHealthAgent
from .integration import PersonaManager

# Persona registry for easy access and instantiation
PERSONA_REGISTRY = {
    "sales_coach": {
        "class": SalesCoachAgent,
        "name": "Marcus Rodriguez",
        "role": "Sales Coach",
        "description": "Motivational sales mentor specializing in deal coaching and performance improvement",
        "expertise": ["Enterprise Sales", "Deal Strategy", "Team Coaching", "CRM Analytics"],
        "personality": "Energetic, results-driven, empathetic mentor"
    },
    "client_health": {
        "class": ClientHealthAgent,
        "name": "Dr. Sarah Chen", 
        "role": "Client Success Strategist",
        "description": "Empathetic client health specialist focused on retention and success optimization",
        "expertise": ["Client Health Analytics", "Churn Prevention", "Success Planning", "Relationship Management"],
        "personality": "Empathetic, analytical, proactive guardian"
    }
}


def create_persona_agent(persona_type: str) -> BasePersonaAgent:
    """
    Create and initialize a persona agent by type.
    
    Args:
        persona_type: Type of persona to create ("sales_coach", "client_health")
        
    Returns:
        Initialized persona agent instance
        
    Raises:
        ValueError: If persona_type is not recognized
    """
    if persona_type not in PERSONA_REGISTRY:
        available_types = list(PERSONA_REGISTRY.keys())
        raise ValueError(f"Unknown persona type '{persona_type}'. Available types: {available_types}")
    
    persona_info = PERSONA_REGISTRY[persona_type]
    persona_class = persona_info["class"]
    
    return persona_class()


def get_available_personas() -> dict:
    """
    Get information about all available persona agents.
    
    Returns:
        Dictionary containing persona information
    """
    return PERSONA_REGISTRY.copy()


def list_persona_types() -> list:
    """
    Get list of available persona types.
    
    Returns:
        List of persona type strings
    """
    return list(PERSONA_REGISTRY.keys())


async def initialize_persona_team() -> dict:
    """
    Initialize the complete persona team with all available agents.
    
    Returns:
        Dictionary mapping persona types to initialized agents
    """
    persona_team = {}
    
    for persona_type in PERSONA_REGISTRY:
        agent = create_persona_agent(persona_type)
        await agent.initialize_agent()
        persona_team[persona_type] = agent
    
    return persona_team


# Export main classes and functions
__all__ = [
    'BasePersonaAgent',
    'PersonaProfile', 
    'PersonalityTrait',
    'ConversationStyle',
    'Memory',
    'LearningPattern',
    'SalesCoachAgent',
    'ClientHealthAgent',
    'PersonaManager',
    'create_persona_agent',
    'get_available_personas',
    'list_persona_types',
    'initialize_persona_team',
    'PERSONA_REGISTRY'
]