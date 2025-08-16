"""Speech router - STT and TTS with rate limiting"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from pydantic import BaseModel
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.middleware import limiter
import structlog

logger = structlog.get_logger()
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
        "providers": ["openai", "elevenlabs"],
        "rate_limits": {
            "stt": "5/minute",
            "tts": "5/minute"
        }
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
@limiter.limit("5/minute")  # Rate limit: 5 STT requests per minute per IP
async def speech_to_text(request: Request, file: UploadFile = File(...)):
    """Convert speech to text - Rate Limited"""
    try:
        logger.info("stt_request", 
                   filename=file.filename,
                   content_type=file.content_type,
                   client_ip=get_remote_address(request))
        
        # TODO: Integrate with OpenAI Whisper
        # For now, return mock response with clear indication
        logger.warning("stt_mock_response", message="Using mock STT - integrate OpenAI Whisper for production")
        
        return STTResponse(
            text="Mock transcription: Hello, this is a test transcription from SOPHIA",
            confidence=0.95,
            language="en"
        )
        
    except Exception as e:
        logger.error("stt_failed", error=str(e), filename=file.filename)
        raise HTTPException(status_code=500, detail=f"STT failed: {str(e)}")

@router.post("/api/speech/tts", response_model=TTSResponse)
@limiter.limit("5/minute")  # Rate limit: 5 TTS requests per minute per IP
async def text_to_speech(request: Request, tts_request: TTSRequest):
    """Convert text to speech - Rate Limited"""
    try:
        logger.info("tts_request", 
                   text_length=len(tts_request.text),
                   voice=tts_request.voice,
                   client_ip=get_remote_address(request))
        
        # TODO: Integrate with ElevenLabs
        # For now, return mock response with clear indication
        logger.warning("tts_mock_response", message="Using mock TTS - integrate ElevenLabs for production")
        
        return TTSResponse(
            audio_url="/tmp/mock_sophia_audio.wav",
            duration=len(tts_request.text) * 0.1  # Rough estimate
        )
        
    except Exception as e:
        logger.error("tts_failed", error=str(e), text_length=len(tts_request.text))
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")
