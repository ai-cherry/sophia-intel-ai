"""
Voice API Router - ElevenLabs Integration for Sophia and Artemis
Provides text-to-speech capabilities for both AI systems
"""

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.orchestrators.voice_integration import SophiaVoiceIntegration, VoiceSettings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["Voice"])


# Pydantic Models
class VoiceSynthesisRequest(BaseModel):
    text: str = Field(..., description="Text to convert to speech", max_length=5000)
    system: str = Field(..., description="AI system: 'sophia' or 'artemis'")
    persona: Optional[str] = Field(None, description="Voice persona to use")
    voice_id: Optional[str] = Field(None, description="Specific ElevenLabs voice ID")
    settings: Optional[dict[str, Any]] = Field(None, description="Custom voice settings")


class VoiceStatusResponse(BaseModel):
    status: str
    api_key_valid: bool
    character_count: Optional[int] = None
    character_limit: Optional[int] = None
    voices_available: int
    personas_mapped: int
    error: Optional[str] = None


class VoicePersonaResponse(BaseModel):
    persona: str
    voice_id: str
    name: str
    description: str
    use_cases: list[str]
    settings: dict[str, Any]


class VoiceSynthesisResponse(BaseModel):
    success: bool
    audio_base64: str
    voice_used: str
    text_length: int
    generation_time: float
    system_used: str
    persona_used: Optional[str] = None
    error_message: Optional[str] = None


class SpeechToTextRequest(BaseModel):
    audio_base64: str = Field(..., description="Base64 encoded audio data")
    audio_format: str = Field(default="mp3", description="Audio format (mp3, wav, m4a, flac, ogg)")
    system: str = Field(..., description="AI system: 'sophia' or 'artemis'")


class SpeechToTextApiResponse(BaseModel):
    success: bool
    text: str
    confidence: float
    duration: float
    system_used: str
    language: Optional[str] = None
    error_message: Optional[str] = None


class VoiceCapabilitiesResponse(BaseModel):
    speech_to_text: dict[str, Any]
    text_to_speech: dict[str, Any]
    full_duplex: bool
    real_time_processing: bool


# Initialize voice integration
sophia_voice = SophiaVoiceIntegration()


@router.get("/status", response_model=VoiceStatusResponse, summary="Get voice integration status")
async def get_voice_status():
    """Get the current status of voice integration for both systems"""
    try:
        status = await sophia_voice.get_voice_status()
        return VoiceStatusResponse(**status)
    except Exception as e:
        logger.error(f"Voice status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Voice status check failed: {str(e)}")


@router.get(
    "/personas", response_model=list[VoicePersonaResponse], summary="List available voice personas"
)
async def get_voice_personas():
    """Get all available voice personas for both Sophia and Artemis"""
    try:
        personas = []

        # Sophia personas
        sophia_personas = [
            "smart",
            "savvy",
            "strategic",
            "analytical",
            "first_principles",
            "playful",
        ]
        for persona in sophia_personas:
            voice_info = sophia_voice.get_persona_voice_info(persona)
            if voice_info:
                personas.append(
                    VoicePersonaResponse(
                        persona=f"sophia_{persona}",
                        voice_id=voice_info["voice_id"],
                        name=voice_info["name"],
                        description=voice_info["description"],
                        use_cases=voice_info["use_cases"],
                        settings=voice_info["settings"],
                    )
                )

        # Artemis personas (technical variations)
        artemis_personas = {
            "artemis_technical": {
                "voice_id": "ErXwobaYiN019PkySvjV",  # Antoni - Clear
                "name": "Artemis Technical",
                "description": "Clear, methodical voice for technical analysis",
                "use_cases": ["coding", "debugging", "technical_review"],
                "settings": {
                    "stability": 0.9,
                    "similarity_boost": 0.8,
                    "style": 0.0,
                    "use_speaker_boost": True,
                },
            },
            "artemis_commander": {
                "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Bella - Authoritative
                "name": "Artemis Commander",
                "description": "Authoritative voice for system commands",
                "use_cases": ["commands", "alerts", "system_status"],
                "settings": {
                    "stability": 0.85,
                    "similarity_boost": 0.85,
                    "style": 0.2,
                    "use_speaker_boost": True,
                },
            },
        }

        for persona, info in artemis_personas.items():
            personas.append(VoicePersonaResponse(persona=persona, **info))

        return personas
    except Exception as e:
        logger.error(f"Failed to get voice personas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get voice personas: {str(e)}")


@router.post("/synthesize", response_model=VoiceSynthesisResponse, summary="Convert text to speech")
async def synthesize_speech(request: VoiceSynthesisRequest):
    """Convert text to speech using ElevenLabs API"""
    try:
        # Validate system
        if request.system not in ["sophia", "artemis"]:
            raise HTTPException(status_code=400, detail="System must be 'sophia' or 'artemis'")

        # Handle Artemis voice synthesis
        if request.system == "artemis":
            return await _synthesize_artemis_voice(request)

        # Handle Sophia voice synthesis
        else:
            return await _synthesize_sophia_voice(request)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice synthesis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Voice synthesis failed: {str(e)}")


async def _synthesize_sophia_voice(request: VoiceSynthesisRequest) -> VoiceSynthesisResponse:
    """Handle Sophia voice synthesis"""

    # Create voice settings if provided
    settings = None
    if request.settings:
        settings = VoiceSettings(
            stability=request.settings.get("stability", 0.75),
            similarity_boost=request.settings.get("similarity_boost", 0.8),
            style=request.settings.get("style", 0.0),
            use_speaker_boost=request.settings.get("use_speaker_boost", True),
        )

    # Generate speech
    if request.persona:
        # Remove 'sophia_' prefix if present
        persona = request.persona.replace("sophia_", "")
        result = await sophia_voice.generate_persona_speech(
            text=request.text, persona=persona, custom_settings=request.settings
        )
    else:
        result = await sophia_voice.text_to_speech(
            text=request.text, voice_id=request.voice_id, settings=settings
        )

    return VoiceSynthesisResponse(
        success=result.success,
        audio_base64=result.audio_base64,
        voice_used=result.voice_used,
        text_length=result.text_length,
        generation_time=result.generation_time,
        system_used="sophia",
        persona_used=request.persona,
        error_message=result.error_message,
    )


async def _synthesize_artemis_voice(request: VoiceSynthesisRequest) -> VoiceSynthesisResponse:
    """Handle Artemis voice synthesis"""

    # Artemis uses specific voice configurations
    artemis_voice_mapping = {
        "artemis_technical": "ErXwobaYiN019PkySvjV",  # Antoni - Clear
        "artemis_commander": "EXAVITQu4vr4xnSDxMaL",  # Bella - Authoritative
    }

    # Default to technical voice if no persona specified
    voice_id = request.voice_id
    if not voice_id:
        persona = request.persona or "artemis_technical"
        voice_id = artemis_voice_mapping.get(persona, artemis_voice_mapping["artemis_technical"])

    # Artemis-specific voice settings (more technical/authoritative)
    settings = VoiceSettings(
        stability=0.9,  # High stability for technical precision
        similarity_boost=0.8,
        style=0.1,  # Minimal style for clarity
        use_speaker_boost=True,
    )

    # Apply custom settings if provided
    if request.settings:
        settings.stability = request.settings.get("stability", settings.stability)
        settings.similarity_boost = request.settings.get(
            "similarity_boost", settings.similarity_boost
        )
        settings.style = request.settings.get("style", settings.style)
        settings.use_speaker_boost = request.settings.get(
            "use_speaker_boost", settings.use_speaker_boost
        )

    # Add Artemis personality to the text
    artemis_text = _add_artemis_personality(request.text)

    # Generate speech using Sophia's voice integration with Artemis settings
    result = await sophia_voice.text_to_speech(
        text=artemis_text, voice_id=voice_id, settings=settings
    )

    return VoiceSynthesisResponse(
        success=result.success,
        audio_base64=result.audio_base64,
        voice_used=f"Artemis ({result.voice_used})",
        text_length=result.text_length,
        generation_time=result.generation_time,
        system_used="artemis",
        persona_used=request.persona,
        error_message=result.error_message,
    )


def _add_artemis_personality(text: str) -> str:
    """Add Artemis technical personality to text"""

    # Artemis speaking patterns - more direct and technical
    if not text.strip().endswith((".", "!", "?")):
        text += "."

    # Add technical confidence markers
    technical_phrases = {
        "analyzing": "deep-scanning",
        "checking": "verifying systems integrity",
        "working": "executing protocols",
        "done": "operation complete",
        "error": "system anomaly detected",
        "success": "mission accomplished",
    }

    for original, artemis_version in technical_phrases.items():
        text = text.replace(original, artemis_version)

    return text


@router.get("/test", summary="Test voice integration")
async def test_voice_integration():
    """Test voice integration for both systems"""
    try:
        results = {}

        # Test Sophia
        sophia_test = await sophia_voice.text_to_speech(
            text="This is Sophia testing voice integration.", persona="smart"
        )
        results["sophia"] = {
            "success": sophia_test.success,
            "voice_used": sophia_test.voice_used,
            "generation_time": sophia_test.generation_time,
            "error": sophia_test.error_message if not sophia_test.success else None,
        }

        # Test Artemis (using same integration with different settings)
        artemis_test = await sophia_voice.text_to_speech(
            text="This is Artemis testing voice integration protocols.",
            voice_id="ErXwobaYiN019PkySvjV",  # Technical voice
            settings=VoiceSettings(stability=0.9, similarity_boost=0.8, style=0.1),
        )
        results["artemis"] = {
            "success": artemis_test.success,
            "voice_used": f"Artemis ({artemis_test.voice_used})",
            "generation_time": artemis_test.generation_time,
            "error": artemis_test.error_message if not artemis_test.success else None,
        }

        # Overall status
        overall_success = results["sophia"]["success"] and results["artemis"]["success"]

        return {
            "overall_success": overall_success,
            "timestamp": datetime.now().isoformat(),
            "systems_tested": ["sophia", "artemis"],
            "results": results,
        }

    except Exception as e:
        logger.error(f"Voice integration test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Voice integration test failed: {str(e)}")


@router.get("/available-voices", summary="Get available ElevenLabs voices")
async def get_available_voices():
    """Get list of available voices from ElevenLabs"""
    try:
        voices = await sophia_voice.get_available_voices()
        return {"voices": voices, "count": len(voices), "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Failed to get available voices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get available voices: {str(e)}")


@router.post(
    "/transcribe", response_model=SpeechToTextApiResponse, summary="Convert speech to text"
)
async def transcribe_speech(request: SpeechToTextRequest):
    """Convert speech audio to text using OpenAI Whisper"""
    try:
        # Validate system
        if request.system not in ["sophia", "artemis"]:
            raise HTTPException(status_code=400, detail="System must be 'sophia' or 'artemis'")

        # Use Sophia's speech-to-text capability for both systems
        result = await sophia_voice.speech_to_text(
            audio_base64=request.audio_base64, audio_format=request.audio_format
        )

        return SpeechToTextApiResponse(
            success=result.success,
            text=result.text,
            confidence=result.confidence,
            duration=result.duration,
            system_used=request.system,
            language=result.language,
            error_message=result.error_message,
        )

    except Exception as e:
        logger.error(f"Speech transcription failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Speech transcription failed: {str(e)}")


@router.get(
    "/capabilities", response_model=VoiceCapabilitiesResponse, summary="Get voice capabilities"
)
async def get_voice_capabilities():
    """Get comprehensive voice capabilities for both systems"""
    try:
        capabilities = await sophia_voice.get_voice_capabilities()
        return VoiceCapabilitiesResponse(**capabilities)
    except Exception as e:
        logger.error(f"Failed to get voice capabilities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get voice capabilities: {str(e)}")


@router.post("/full-duplex", summary="Full voice conversation (speech in, speech out)")
async def full_duplex_conversation(request: dict[str, Any]):
    """
    Complete voice conversation: speech-to-text → AI processing → text-to-speech
    """
    try:
        # Extract parameters
        audio_base64 = request.get("audio_base64")
        audio_format = request.get("audio_format", "mp3")
        system = request.get("system", "sophia")
        persona = request.get("persona", "smart" if system == "sophia" else "artemis_technical")

        if not audio_base64:
            raise HTTPException(status_code=400, detail="audio_base64 is required")

        # Step 1: Speech to Text
        transcription = await sophia_voice.speech_to_text(audio_base64, audio_format)

        if not transcription.success:
            return {
                "success": False,
                "error": f"Speech recognition failed: {transcription.error_message}",
                "transcription": None,
                "ai_response": None,
                "audio_response": None,
            }

        # Step 2: AI Processing (simplified - would integrate with actual AI systems)
        ai_response_text = (
            f"I heard you say: '{transcription.text}'. This is {system} responding to your message."
        )

        # Step 3: Text to Speech
        if system == "sophia":
            synthesis = await sophia_voice.generate_persona_speech(ai_response_text, persona)
        else:
            # Artemis synthesis
            synthesis = await _synthesize_artemis_voice(
                VoiceSynthesisRequest(text=ai_response_text, system="artemis", persona=persona)
            )

        return {
            "success": True,
            "transcription": {
                "text": transcription.text,
                "confidence": transcription.confidence,
                "duration": transcription.duration,
            },
            "ai_response": {"text": ai_response_text, "system": system, "persona": persona},
            "audio_response": {
                "success": synthesis.success,
                "audio_base64": synthesis.audio_base64
                if hasattr(synthesis, "audio_base64")
                else synthesis.get("audio_base64", ""),
                "voice_used": synthesis.voice_used
                if hasattr(synthesis, "voice_used")
                else synthesis.get("voice_used", "Unknown"),
                "generation_time": synthesis.generation_time
                if hasattr(synthesis, "generation_time")
                else synthesis.get("generation_time", 0),
            },
        }

    except Exception as e:
        logger.error(f"Full duplex conversation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Full duplex conversation failed: {str(e)}")
