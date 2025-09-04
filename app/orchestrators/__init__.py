"""
Sophia Intelligence System - Orchestrators Package
Central coordination system for AI-powered business intelligence
"""

from .sophia_orchestrator import (
    SophiaIntelligenceOrchestrator,
    SophiaQuery,
    SophiaResponse,
    QueryType,
    ContextualDomain
)

from .artemis_orchestrator import (
    ArtemisResearchOrchestrator,
    ResearchRequest,
    ResearchResult,
    ResearchType,
    ResearchDepth
)

from .persona_system import (
    SophiaPersonaSystem,
    PersonaContext,
    PersonaResponse
)

from .voice_integration import (
    SophiaVoiceIntegration,
    VoiceSettings,
    VoiceResponse
)

__all__ = [
    # Sophia Orchestrator
    'SophiaIntelligenceOrchestrator',
    'SophiaQuery',
    'SophiaResponse',
    'QueryType',
    'ContextualDomain',
    
    # Artemis Orchestrator
    'ArtemisResearchOrchestrator',
    'ResearchRequest',
    'ResearchResult',
    'ResearchType',
    'ResearchDepth',
    
    # Persona System
    'SophiaPersonaSystem',
    'PersonaContext',
    'PersonaResponse',
    
    # Voice Integration
    'SophiaVoiceIntegration',
    'VoiceSettings',
    'VoiceResponse'
]