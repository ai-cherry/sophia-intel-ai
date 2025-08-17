"""
Persona Domain - Voice and personality management for SOPHIA
Handles ElevenLabs voice generation and persona enhancement
"""

from .service import PersonaService
from .models import PersonaSettings, VoiceSettings, PersonaResponse
from .voice_manager import VoiceManager

__all__ = [
    "PersonaService",
    "PersonaSettings", 
    "VoiceSettings",
    "PersonaResponse",
    "VoiceManager"
]

