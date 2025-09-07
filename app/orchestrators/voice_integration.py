"""
Sophia Intelligence System - ElevenLabs Voice Integration
Provides text-to-speech capabilities using ElevenLabs API
"""

import base64
import io
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class VoiceSettings:
    """Voice configuration settings"""

    stability: float = 0.75
    similarity_boost: float = 0.8
    style: float = 0.0
    use_speaker_boost: bool = True


@dataclass
class VoiceResponse:
    """Response from voice generation"""

    audio_base64: str
    voice_used: str
    text_length: int
    generation_time: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class SpeechToTextResponse:
    """Response from speech-to-text conversion"""

    text: str
    confidence: float
    duration: float
    success: bool
    language: Optional[str] = None
    error_message: Optional[str] = None


class SophiaVoiceIntegration:
    """
    ElevenLabs Voice Integration for Sophia Intelligence System
    Provides text-to-speech capabilities with multiple voice personas
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ElevenLabs API key not found. Set ELEVENLABS_API_KEY environment variable."
            )
        self.base_url = "https://api.elevenlabs.io/v1"
        self.voices = self._initialize_voices()
        self.persona_voice_mapping = self._initialize_persona_mapping()

    def _initialize_voices(self) -> dict[str, dict]:
        """Initialize available ElevenLabs voices"""
        return {
            "sophia_professional": {
                "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel - Professional
                "name": "Sophia Professional",
                "description": "Clear, professional voice for business contexts",
                "use_cases": ["business", "analytics", "reports"],
            },
            "sophia_conversational": {
                "voice_id": "AZnzlk1XvdvUeBnXmlld",  # Domi - Conversational
                "name": "Sophia Conversational",
                "description": "Warm, engaging voice for interactive conversations",
                "use_cases": ["coaching", "insights", "explanations"],
            },
            "sophia_strategic": {
                "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Bella - Authoritative
                "name": "Sophia Strategic",
                "description": "Confident, strategic voice for high-level insights",
                "use_cases": ["strategic", "competitive", "planning"],
            },
            "sophia_analytical": {
                "voice_id": "ErXwobaYiN019PkySvjV",  # Antoni - Clear
                "name": "Sophia Analytical",
                "description": "Clear, methodical voice for detailed analysis",
                "use_cases": ["analytical", "technical", "deep_dive"],
            },
            "sophia_creative": {
                "voice_id": "MF3mGyEYCl7XYWbV9V6O",  # Elli - Expressive
                "name": "Sophia Creative",
                "description": "Expressive, engaging voice for creative content",
                "use_cases": ["playful", "creative", "storytelling"],
            },
        }

    def _initialize_persona_mapping(self) -> dict[str, str]:
        """Map Sophia personas to voice profiles"""
        return {
            "smart": "sophia_professional",
            "savvy": "sophia_conversational",
            "strategic": "sophia_strategic",
            "analytical": "sophia_analytical",
            "first_principles": "sophia_analytical",
            "playful": "sophia_creative",
        }

    async def text_to_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        persona: Optional[str] = None,
        settings: Optional[VoiceSettings] = None,
    ) -> VoiceResponse:
        """Convert text to speech using ElevenLabs API"""

        start_time = datetime.now()

        # Determine voice to use
        if persona and persona in self.persona_voice_mapping:
            voice_key = self.persona_voice_mapping[persona]
            voice_id = self.voices[voice_key]["voice_id"]
            voice_name = self.voices[voice_key]["name"]
        elif voice_id:
            # Find voice name from ID
            voice_name = next(
                (v["name"] for v in self.voices.values() if v["voice_id"] == voice_id),
                "Unknown Voice",
            )
        else:
            # Default to professional voice
            voice_key = "sophia_professional"
            voice_id = self.voices[voice_key]["voice_id"]
            voice_name = self.voices[voice_key]["name"]

        # Use default settings if not provided
        if not settings:
            settings = VoiceSettings()

        try:
            # Prepare request
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key,
            }

            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": settings.stability,
                    "similarity_boost": settings.similarity_boost,
                    "style": settings.style,
                    "use_speaker_boost": settings.use_speaker_boost,
                },
            }

            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        audio_bytes = await response.read()
                        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

                        generation_time = (datetime.now() - start_time).total_seconds()

                        return VoiceResponse(
                            audio_base64=audio_base64,
                            voice_used=voice_name,
                            text_length=len(text),
                            generation_time=generation_time,
                            success=True,
                        )
                    else:
                        error_text = await response.text()
                        logger.error(f"ElevenLabs API error: {response.status} - {error_text}")

                        return VoiceResponse(
                            audio_base64="",
                            voice_used=voice_name,
                            text_length=len(text),
                            generation_time=(datetime.now() - start_time).total_seconds(),
                            success=False,
                            error_message=f"API Error: {response.status} - {error_text}",
                        )

        except Exception as e:
            logger.error(f"Voice generation error: {str(e)}")
            return VoiceResponse(
                audio_base64="",
                voice_used=voice_name if "voice_name" in locals() else "Unknown",
                text_length=len(text),
                generation_time=(datetime.now() - start_time).total_seconds(),
                success=False,
                error_message=f"Generation failed: {str(e)}",
            )

    async def get_available_voices(self) -> list[dict]:
        """Get list of available voices from ElevenLabs"""
        try:
            url = f"{self.base_url}/voices"
            headers = {"xi-api-key": self.api_key}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("voices", [])
                    else:
                        logger.error(f"Failed to fetch voices: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"Error fetching voices: {str(e)}")
            return []

    async def get_voice_for_persona(self, persona: str) -> Optional[dict]:
        """Get the voice configuration for a specific persona"""
        if persona in self.persona_voice_mapping:
            voice_key = self.persona_voice_mapping[persona]
            return self.voices[voice_key]
        return None

    async def generate_persona_speech(
        self, text: str, persona: str, custom_settings: Optional[dict] = None
    ) -> VoiceResponse:
        """Generate speech with persona-specific voice and settings"""

        # Get persona-specific settings
        settings = self._get_persona_voice_settings(persona, custom_settings)

        # Generate speech
        return await self.text_to_speech(text=text, persona=persona, settings=settings)

    def _get_persona_voice_settings(
        self, persona: str, custom_settings: Optional[dict] = None
    ) -> VoiceSettings:
        """Get voice settings optimized for specific personas"""

        # Base settings for each persona
        persona_settings = {
            "smart": VoiceSettings(
                stability=0.8,  # High stability for data delivery
                similarity_boost=0.7,
                style=0.1,  # Minimal style for professional tone
                use_speaker_boost=True,
            ),
            "savvy": VoiceSettings(
                stability=0.75,  # Balanced for business conversations
                similarity_boost=0.8,
                style=0.2,  # Slight style for engagement
                use_speaker_boost=True,
            ),
            "strategic": VoiceSettings(
                stability=0.85,  # Very stable for authority
                similarity_boost=0.85,
                style=0.15,  # Confident but controlled
                use_speaker_boost=True,
            ),
            "analytical": VoiceSettings(
                stability=0.9,  # Maximum stability for technical content
                similarity_boost=0.7,
                style=0.0,  # No style for pure clarity
                use_speaker_boost=True,
            ),
            "first_principles": VoiceSettings(
                stability=0.85,  # Stable for foundational concepts
                similarity_boost=0.8,
                style=0.1,  # Minimal style for clarity
                use_speaker_boost=True,
            ),
            "playful": VoiceSettings(
                stability=0.6,  # Lower stability for expressiveness
                similarity_boost=0.85,
                style=0.4,  # Higher style for personality
                use_speaker_boost=True,
            ),
        }

        # Get base settings for persona
        base_settings = persona_settings.get(persona, VoiceSettings())

        # Apply custom overrides if provided
        if custom_settings:
            if "stability" in custom_settings:
                base_settings.stability = custom_settings["stability"]
            if "similarity_boost" in custom_settings:
                base_settings.similarity_boost = custom_settings["similarity_boost"]
            if "style" in custom_settings:
                base_settings.style = custom_settings["style"]
            if "use_speaker_boost" in custom_settings:
                base_settings.use_speaker_boost = custom_settings["use_speaker_boost"]

        return base_settings

    async def get_voice_status(self) -> dict:
        """Get the current status of the voice integration"""
        try:
            # Test API connection
            url = f"{self.base_url}/user"
            headers = {"xi-api-key": self.api_key}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        user_data = await response.json()
                        return {
                            "status": "connected",
                            "api_key_valid": True,
                            "character_count": user_data.get("subscription", {}).get(
                                "character_count", 0
                            ),
                            "character_limit": user_data.get("subscription", {}).get(
                                "character_limit", 0
                            ),
                            "voices_available": len(self.voices),
                            "personas_mapped": len(self.persona_voice_mapping),
                        }
                    else:
                        return {
                            "status": "error",
                            "api_key_valid": False,
                            "error": f"API returned status {response.status}",
                        }

        except Exception as e:
            return {"status": "error", "api_key_valid": False, "error": str(e)}

    async def create_audio_response_for_message(
        self, message_content: str, persona: str, message_type: str = "insight"
    ) -> Optional[str]:
        """
        Create audio response for a Sophia message
        Returns base64 encoded audio data
        """

        # Clean message content for speech
        clean_text = self._clean_text_for_speech(message_content)

        # Generate speech
        voice_response = await self.generate_persona_speech(clean_text, persona)

        if voice_response.success:
            return voice_response.audio_base64
        else:
            logger.error(f"Voice generation failed: {voice_response.error_message}")
            return None

    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text content to make it speech-friendly"""

        # Remove markdown formatting
        import re

        # Remove bold/italic markers
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)  # **bold**
        text = re.sub(r"\*([^*]+)\*", r"\1", text)  # *italic*

        # Remove bullet points and convert to sentences
        text = re.sub(r"^[•·\-\*]\s*", "", text, flags=re.MULTILINE)

        # Remove excessive line breaks
        text = re.sub(r"\n+", ". ", text)

        # Remove special characters that don't read well
        text = re.sub(r"[#]+\s*", "", text)  # Remove hashtags
        text = re.sub(r"[📊📞🎯⚠️💡🔍🧠🎪⚛️🚀🎓💼📈🔥]+", "", text)  # Remove emojis

        # Clean up spacing
        text = re.sub(r"\s+", " ", text).strip()

        # Ensure proper sentence ending
        if not text.endswith("."):
            text += "."

        return text

    def get_persona_voice_info(self, persona: str) -> dict:
        """Get voice information for a specific persona"""
        if persona in self.persona_voice_mapping:
            voice_key = self.persona_voice_mapping[persona]
            voice_info = self.voices[voice_key].copy()
            settings = self._get_persona_voice_settings(persona)

            voice_info.update(
                {
                    "settings": {
                        "stability": settings.stability,
                        "similarity_boost": settings.similarity_boost,
                        "style": settings.style,
                        "use_speaker_boost": settings.use_speaker_boost,
                    }
                }
            )

            return voice_info

        return {}

    async def speech_to_text(
        self, audio_base64: str, audio_format: str = "mp3"
    ) -> SpeechToTextResponse:
        """
        Convert speech audio to text using OpenAI Whisper API

        Args:
            audio_base64: Base64 encoded audio data
            audio_format: Audio format (mp3, wav, m4a, etc.)
        """
        start_time = datetime.now()

        try:
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_base64)

            # OpenAI Whisper API endpoint
            url = "https://api.openai.com/v1/audio/transcriptions"

            # Get OpenAI API key from environment
            import os

            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                return SpeechToTextResponse(
                    text="",
                    confidence=0.0,
                    duration=(datetime.now() - start_time).total_seconds(),
                    success=False,
                    error_message="OpenAI API key not configured for speech-to-text",
                )

            headers = {"Authorization": f"Bearer {openai_api_key}"}

            # Prepare multipart form data
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field(
                    "file",
                    io.BytesIO(audio_bytes),
                    filename=f"audio.{audio_format}",
                    content_type=f"audio/{audio_format}",
                )
                data.add_field("model", "whisper-1")
                data.add_field("response_format", "json")
                data.add_field("language", "en")

                async with session.post(url, headers=headers, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        duration = (datetime.now() - start_time).total_seconds()

                        return SpeechToTextResponse(
                            text=result.get("text", ""),
                            confidence=1.0,  # Whisper doesn't return confidence scores
                            duration=duration,
                            success=True,
                            language=result.get("language", "en"),
                        )
                    else:
                        error_text = await response.text()
                        logger.error(f"Speech-to-text API error: {response.status} - {error_text}")

                        return SpeechToTextResponse(
                            text="",
                            confidence=0.0,
                            duration=(datetime.now() - start_time).total_seconds(),
                            success=False,
                            error_message=f"API Error: {response.status} - {error_text}",
                        )

        except Exception as e:
            logger.error(f"Speech-to-text error: {str(e)}")
            return SpeechToTextResponse(
                text="",
                confidence=0.0,
                duration=(datetime.now() - start_time).total_seconds(),
                success=False,
                error_message=f"Processing failed: {str(e)}",
            )

    async def get_voice_capabilities(self) -> dict:
        """Get comprehensive voice capabilities for the system"""
        return {
            "speech_to_text": {
                "available": True,
                "provider": "OpenAI Whisper",
                "supported_formats": ["mp3", "wav", "m4a", "flac", "ogg"],
                "max_file_size": "25MB",
                "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
            },
            "text_to_speech": {
                "available": True,
                "provider": "ElevenLabs",
                "voices_available": len(self.voices),
                "personas_mapped": len(self.persona_voice_mapping),
                "supported_output": ["mp3_base64"],
            },
            "full_duplex": True,
            "real_time_processing": False,  # Batch processing only
        }
