"""Speech router - STT and TTS endpoints"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "sophia"
    speed: Optional[float] = 1.0

class STTResponse(BaseModel):
    text: str
    confidence: Optional[float] = None
    language: Optional[str] = None

class TTSResponse(BaseModel):
    audio_url: str
    duration: Optional[float] = None

@router.get("/api/speech/health")
async def speech_health():
    """Speech service health check"""
    return {
        "service": "sophia-speech",
        "status": "healthy",
        "features": ["stt", "tts"],
        "providers": ["openai", "elevenlabs"]
    }

@router.get("/api/speech/voices")
async def get_voices():
    """Get available voices"""
    return {
        "voices": [
            {"id": "sophia", "name": "SOPHIA", "language": "en", "gender": "female"},
            {"id": "nova", "name": "Nova", "language": "en", "gender": "female"},
            {"id": "alloy", "name": "Alloy", "language": "en", "gender": "neutral"}
        ]
    }

@router.post("/api/speech/stt", response_model=STTResponse)
async def speech_to_text(file: UploadFile = File(...)):
    """Convert speech to text"""
    try:
        logger.info(f"Processing STT for file: {file.filename}")
        
        # For now, return mock response
        # TODO: Integrate with OpenAI Whisper
        return STTResponse(
            text="Hello, this is a mock transcription",
            confidence=0.95,
            language="en"
        )
        
    except Exception as e:
        logger.error(f"STT failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/speech/tts", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    """Convert text to speech"""
    try:
        logger.info(f"Processing TTS for text: {request.text[:50]}...")
        
        # For now, return mock response
        # TODO: Integrate with ElevenLabs
        return TTSResponse(
            audio_url="/tmp/mock_audio.wav",
            duration=len(request.text) * 0.1  # Rough estimate
        )
        
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
