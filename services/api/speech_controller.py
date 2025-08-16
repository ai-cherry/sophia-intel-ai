"""
SOPHIA Intel Speech Controller
Real STT/TTS implementation with OpenAI Whisper and ElevenLabs
"""

import os
import io
import logging
import tempfile
from typing import Optional, Dict, Any
from fastapi import APIRouter, UploadFile, HTTPException, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Import AI clients
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import httpx
except ImportError:
    httpx = None

from services.common.env_schema import get_config

logger = logging.getLogger(__name__)

# Request/Response models
class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    model: Optional[str] = None
    speed: Optional[float] = 1.0

class STTResponse(BaseModel):
    text: str
    language: Optional[str] = None
    duration: Optional[float] = None

class TTSResponse(BaseModel):
    audio_url: Optional[str] = None
    content_type: str = "audio/wav"

# Initialize router
router = APIRouter(prefix="/api/speech", tags=["speech"])

class SpeechService:
    """Speech service with real STT/TTS providers"""
    
    def __init__(self):
        self.config = get_config()
        self._openai_client = None
        self._elevenlabs_client = None
        
    @property
    def openai_client(self) -> Optional[OpenAI]:
        """Lazy-loaded OpenAI client"""
        if self._openai_client is None and OpenAI:
            try:
                self._openai_client = OpenAI(
                    api_key=self.config.OPENAI_API_KEY,
                    base_url=str(self.config.OPENAI_BASE_URL)
                )
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
        return self._openai_client
    
    @property
    def elevenlabs_client(self) -> Optional[httpx.AsyncClient]:
        """Lazy-loaded ElevenLabs HTTP client"""
        if self._elevenlabs_client is None and httpx:
            self._elevenlabs_client = httpx.AsyncClient(
                base_url="https://api.elevenlabs.io/v1",
                headers={
                    "xi-api-key": self.config.ELEVENLABS_API_KEY,
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
        return self._elevenlabs_client
    
    async def speech_to_text(self, audio_file: UploadFile) -> STTResponse:
        """
        Convert speech to text using OpenAI Whisper
        
        Args:
            audio_file: Uploaded audio file
            
        Returns:
            STTResponse: Transcribed text and metadata
            
        Raises:
            HTTPException: If STT fails
        """
        if not self.openai_client:
            raise HTTPException(500, "OpenAI client not available")
        
        try:
            # Read audio data
            audio_data = await audio_file.read()
            
            # Create temporary file for OpenAI API
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                
                # Call OpenAI Whisper API
                with open(temp_file.name, "rb") as audio:
                    response = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio,
                        response_format="verbose_json"
                    )
                
                # Clean up temp file
                os.unlink(temp_file.name)
            
            return STTResponse(
                text=response.text,
                language=getattr(response, 'language', None),
                duration=getattr(response, 'duration', None)
            )
            
        except Exception as e:
            logger.error(f"STT error: {e}")
            raise HTTPException(500, f"Speech-to-text failed: {str(e)}")
    
    async def text_to_speech(self, request: TTSRequest) -> bytes:
        """
        Convert text to speech using ElevenLabs
        
        Args:
            request: TTS request with text and options
            
        Returns:
            bytes: Audio data in WAV format
            
        Raises:
            HTTPException: If TTS fails
        """
        if self.config.TTS_PROVIDER == "elevenlabs":
            return await self._elevenlabs_tts(request)
        elif self.config.TTS_PROVIDER == "openai":
            return await self._openai_tts(request)
        else:
            raise HTTPException(400, f"TTS provider '{self.config.TTS_PROVIDER}' not supported")
    
    async def _elevenlabs_tts(self, request: TTSRequest) -> bytes:
        """ElevenLabs TTS implementation"""
        if not self.elevenlabs_client:
            raise HTTPException(500, "ElevenLabs client not available")
        
        try:
            # Use configured voice ID or default
            voice_id = request.voice_id or self.config.ELEVENLABS_VOICE_ID or "21m00Tcm4TlvDq8ikWAM"
            
            # Prepare request payload
            payload = {
                "text": request.text,
                "model_id": request.model or "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5,
                    "speed": request.speed
                }
            }
            
            # Call ElevenLabs API
            response = await self.elevenlabs_client.post(
                f"/text-to-speech/{voice_id}",
                json=payload
            )
            
            if response.status_code != 200:
                raise HTTPException(500, f"ElevenLabs API error: {response.status_code}")
            
            return response.content
            
        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}")
            raise HTTPException(500, f"Text-to-speech failed: {str(e)}")
    
    async def _openai_tts(self, request: TTSRequest) -> bytes:
        """OpenAI TTS implementation"""
        if not self.openai_client:
            raise HTTPException(500, "OpenAI client not available")
        
        try:
            response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice=request.voice_id or "alloy",
                input=request.text,
                speed=request.speed
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"OpenAI TTS error: {e}")
            raise HTTPException(500, f"Text-to-speech failed: {str(e)}")

# Initialize service
speech_service = SpeechService()

@router.post("/stt", response_model=STTResponse)
async def speech_to_text(
    file: UploadFile = File(..., description="Audio file (webm, mp3, wav, etc.)")
) -> STTResponse:
    """
    Convert speech to text using OpenAI Whisper
    
    - **file**: Audio file to transcribe
    
    Returns transcribed text with metadata
    """
    # Validate file size (max 25MB)
    if file.size and file.size > 25 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 25MB)")
    
    # Validate content type
    allowed_types = [
        "audio/webm", "audio/mp3", "audio/mpeg", "audio/wav", 
        "audio/x-wav", "audio/mp4", "audio/m4a"
    ]
    
    if file.content_type and file.content_type not in allowed_types:
        logger.warning(f"Unexpected content type: {file.content_type}")
    
    return await speech_service.speech_to_text(file)

@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech using configured TTS provider
    
    - **text**: Text to convert to speech
    - **voice_id**: Optional voice ID (provider-specific)
    - **model**: Optional model name
    - **speed**: Speech speed (0.25 to 4.0)
    
    Returns audio stream
    """
    # Validate text length
    if len(request.text) > 4000:
        raise HTTPException(400, "Text too long (max 4000 characters)")
    
    if not request.text.strip():
        raise HTTPException(400, "Text cannot be empty")
    
    # Generate audio
    audio_data = await speech_service.text_to_speech(request)
    
    # Return as streaming response
    return StreamingResponse(
        io.BytesIO(audio_data),
        media_type="audio/wav",
        headers={
            "Content-Disposition": "attachment; filename=speech.wav",
            "Cache-Control": "no-cache"
        }
    )

@router.get("/voices")
async def list_voices():
    """
    List available voices for the configured TTS provider
    """
    config = get_config()
    
    if config.TTS_PROVIDER == "elevenlabs":
        # Return ElevenLabs voice options
        return {
            "provider": "elevenlabs",
            "voices": [
                {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "gender": "female"},
                {"id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "gender": "female"},
                {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "gender": "female"},
                {"id": "ErXwobaYiN019PkySvjV", "name": "Antoni", "gender": "male"},
                {"id": "MF3mGyEYCl7XYWbV9V6O", "name": "Elli", "gender": "female"},
                {"id": "TxGEqnHWrfWFTfGW9XjX", "name": "Josh", "gender": "male"},
            ]
        }
    elif config.TTS_PROVIDER == "openai":
        # Return OpenAI voice options
        return {
            "provider": "openai",
            "voices": [
                {"id": "alloy", "name": "Alloy", "gender": "neutral"},
                {"id": "echo", "name": "Echo", "gender": "male"},
                {"id": "fable", "name": "Fable", "gender": "neutral"},
                {"id": "onyx", "name": "Onyx", "gender": "male"},
                {"id": "nova", "name": "Nova", "gender": "female"},
                {"id": "shimmer", "name": "Shimmer", "gender": "female"},
            ]
        }
    else:
        return {"provider": config.TTS_PROVIDER, "voices": []}

@router.get("/health")
async def speech_health():
    """Health check for speech services"""
    config = get_config()
    
    health_status = {
        "status": "healthy",
        "stt_provider": config.STT_PROVIDER,
        "tts_provider": config.TTS_PROVIDER,
        "features": {
            "speech_to_text": config.FEATURE_VOICE_ENABLED and bool(config.OPENAI_API_KEY),
            "text_to_speech": config.FEATURE_VOICE_ENABLED and (
                (config.TTS_PROVIDER == "elevenlabs" and bool(config.ELEVENLABS_API_KEY)) or
                (config.TTS_PROVIDER == "openai" and bool(config.OPENAI_API_KEY))
            )
        }
    }
    
    return health_status

