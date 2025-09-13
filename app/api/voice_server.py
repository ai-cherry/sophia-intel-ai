"""WebRTC Voice Server - Real-time voice processing for Builder app"""

import asyncio
import json
import logging
import os
from typing import Optional, Dict, Any
import aiohttp
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

logger = logging.getLogger(__name__)

app = FastAPI(title="Voice Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Voice service configuration
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel voice default


class VoiceConfig(BaseModel):
    """Voice configuration"""
    use_deepgram: bool = True
    use_elevenlabs: bool = True
    voice_id: str = ELEVENLABS_VOICE_ID
    language: str = "en-US"


class DeepgramASR:
    """Deepgram speech-to-text handler"""
    
    def __init__(self):
        self.api_key = DEEPGRAM_API_KEY
        self.ws_url = "wss://api.deepgram.com/v1/listen"
    
    async def connect(self, websocket: WebSocket) -> Optional[aiohttp.ClientWebSocketResponse]:
        """Connect to Deepgram WebSocket"""
        if not self.api_key:
            logger.warning("Deepgram API key not set")
            return None
            
        params = {
            "encoding": "linear16",
            "sample_rate": "16000",
            "channels": "1",
            "punctuate": "true",
            "interim_results": "true",
            "model": "nova-2",
            "language": "en-US"
        }
        
        headers = {
            "Authorization": f"Token {self.api_key}"
        }
        
        session = aiohttp.ClientSession()
        try:
            ws = await session.ws_connect(
                self.ws_url,
                headers=headers,
                params=params
            )
            return ws
        except Exception as e:
            logger.error(f"Failed to connect to Deepgram: {e}")
            await session.close()
            return None


class ElevenLabsTTS:
    """ElevenLabs text-to-speech handler"""
    
    def __init__(self):
        self.api_key = ELEVENLABS_API_KEY
        self.voice_id = ELEVENLABS_VOICE_ID
        self.ws_url = f"wss://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream-input"
    
    async def connect(self) -> Optional[aiohttp.ClientWebSocketResponse]:
        """Connect to ElevenLabs WebSocket"""
        if not self.api_key:
            logger.warning("ElevenLabs API key not set")
            return None
            
        params = {
            "model_id": "eleven_turbo_v2",
            "voice_settings": json.dumps({
                "stability": 0.5,
                "similarity_boost": 0.75
            })
        }
        
        headers = {
            "xi-api-key": self.api_key
        }
        
        session = aiohttp.ClientSession()
        try:
            ws = await session.ws_connect(
                self.ws_url,
                headers=headers,
                params=params
            )
            return ws
        except Exception as e:
            logger.error(f"Failed to connect to ElevenLabs: {e}")
            await session.close()
            return None
    
    async def synthesize(self, text: str) -> Optional[bytes]:
        """Synthesize speech from text (REST API fallback)"""
        if not self.api_key:
            return None
            
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "model_id": "eleven_turbo_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=data)
                if response.status_code == 200:
                    return response.content
            except Exception as e:
                logger.error(f"TTS synthesis failed: {e}")
        return None


@app.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    """Main WebSocket endpoint for voice communication"""
    await websocket.accept()
    
    asr = DeepgramASR()
    tts = ElevenLabsTTS()
    
    deepgram_ws = None
    elevenlabs_ws = None
    
    try:
        # Connect to voice services
        deepgram_ws = await asr.connect(websocket)
        elevenlabs_ws = await tts.connect()
        
        # Handle bidirectional audio streaming
        async def handle_client_audio():
            """Forward client audio to Deepgram"""
            try:
                while True:
                    data = await websocket.receive_bytes()
                    if deepgram_ws:
                        await deepgram_ws.send_bytes(data)
            except WebSocketDisconnect:
                pass
            except Exception as e:
                logger.error(f"Client audio error: {e}")
        
        async def handle_deepgram_response():
            """Process Deepgram transcripts"""
            if not deepgram_ws:
                return
                
            try:
                async for msg in deepgram_ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        
                        # Extract transcript
                        if "channel" in data:
                            transcript = data["channel"]["alternatives"][0]["transcript"]
                            if transcript:
                                # Send transcript to client
                                await websocket.send_json({
                                    "type": "transcript",
                                    "text": transcript,
                                    "is_final": data.get("is_final", False)
                                })
                                
                                # Process command if final
                                if data.get("is_final"):
                                    response = await process_voice_command(transcript)
                                    if response:
                                        # Send response text
                                        await websocket.send_json({
                                            "type": "response",
                                            "text": response
                                        })
                                        
                                        # Generate speech
                                        audio = await tts.synthesize(response)
                                        if audio:
                                            await websocket.send_bytes(audio)
            except Exception as e:
                logger.error(f"Deepgram response error: {e}")
        
        # Run handlers concurrently
        await asyncio.gather(
            handle_client_audio(),
            handle_deepgram_response()
        )
        
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cleanup connections
        if deepgram_ws:
            await deepgram_ws.close()
        if elevenlabs_ws:
            await elevenlabs_ws.close()
        await websocket.close()


async def process_voice_command(transcript: str) -> Optional[str]:
    """Process voice command and generate response"""
    # Send to Builder API for processing
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/builder/team/run",
                json={
                    "team_id": "default",
                    "task": transcript,
                    "context": {"source": "voice"}
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("result", {}).get("summary", "Task completed")
    except Exception as e:
        logger.error(f"Failed to process command: {e}")
    
    return "I couldn't process that command. Please try again."


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "deepgram_configured": bool(DEEPGRAM_API_KEY),
        "elevenlabs_configured": bool(ELEVENLABS_API_KEY),
        "voice_id": ELEVENLABS_VOICE_ID
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)