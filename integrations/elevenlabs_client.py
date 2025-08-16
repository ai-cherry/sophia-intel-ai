#!/usr/bin/env python3
"""
Production-Grade ElevenLabs Streaming Client for SOPHIA Voice Command Center
Implements WebSocket-based real-time text-to-speech with smart Asian American female persona
"""

import os
import json
import asyncio
import websockets
import logging
import time
from typing import Optional, Dict, Any, AsyncGenerator, Callable
from dataclasses import dataclass
from pathlib import Path
import base64
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class VoiceConfig:
    """Configuration for SOPHIA's voice persona"""
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel - professional, clear, calm
    model_id: str = "eleven_turbo_v2_5"  # Latest high-quality model
    stability: float = 0.3  # Low for natural intonation
    similarity_boost: float = 0.8  # High for clarity and intelligibility
    style: float = 0.2  # Low for professional, not overly dramatic
    use_speaker_boost: bool = True  # Enhanced clarity
    
    # Persona characteristics for smart Asian American female
    persona_traits: Dict[str, str] = None
    
    def __post_init__(self):
        if self.persona_traits is None:
            self.persona_traits = {
                "tone": "friendly and professional",
                "personality": "intelligent, curious, and helpful",
                "communication_style": "clear, concise, and engaging",
                "expertise": "AI, technology, and business intelligence",
                "cultural_background": "Asian American perspective with global awareness",
                "interaction_approach": "asks thoughtful questions and presents smart ideas"
            }

class SOPHIAVoicePersona:
    """Smart Asian American female persona for SOPHIA"""
    
    def __init__(self):
        self.persona_prompts = {
            "greeting": "Hi there! I'm SOPHIA, your AI assistant. How can I help you today?",
            "confirmation": "Got it! Let me take care of that for you.",
            "thinking": "That's an interesting question. Let me think about this...",
            "analysis": "Based on my analysis, here's what I found:",
            "suggestion": "I have a few ideas that might help:",
            "question": "I'd love to learn more about this. Can you tell me:",
            "completion": "Mission accomplished! Is there anything else you'd like me to help with?",
            "error": "I encountered a small hiccup, but I'm working on it. Let me try a different approach.",
            "curiosity": "That's fascinating! I'm curious about:",
            "insight": "Here's an interesting insight I discovered:"
        }
        
        self.conversation_enhancers = [
            "By the way,",
            "Interestingly,",
            "I should mention,",
            "You might find it helpful to know,",
            "From my perspective,",
            "Based on what I've learned,",
            "I'm thinking we could also",
            "Another approach might be"
        ]
    
    def enhance_response(self, text: str, context: str = "general") -> str:
        """Enhance text with persona characteristics"""
        # Add appropriate persona context based on response type
        if context == "greeting":
            return f"{self.persona_prompts['greeting']} {text}"
        elif context == "confirmation":
            return f"{self.persona_prompts['confirmation']} {text}"
        elif context == "analysis":
            return f"{self.persona_prompts['analysis']} {text}"
        elif context == "suggestion":
            return f"{self.persona_prompts['suggestion']} {text}"
        elif context == "completion":
            return f"{text} {self.persona_prompts['completion']}"
        else:
            # For general responses, add subtle personality
            return text
    
    def add_conversational_flair(self, text: str) -> str:
        """Add natural conversational elements"""
        # Add occasional conversational enhancers for longer responses
        if len(text) > 100 and not any(enhancer in text for enhancer in self.conversation_enhancers):
            import random
            if random.random() < 0.3:  # 30% chance to add flair
                enhancer = random.choice(self.conversation_enhancers)
                sentences = text.split('. ')
                if len(sentences) > 1:
                    # Insert enhancer in the middle
                    mid_point = len(sentences) // 2
                    sentences.insert(mid_point, f"{enhancer} ")
                    text = '. '.join(sentences)
        
        return text

class ElevenLabsStreamingClient:
    """Production-grade streaming client for ElevenLabs API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ElevenLabs API key is required")
        
        self.voice_config = VoiceConfig()
        self.persona = SOPHIAVoicePersona()
        self.websocket = None
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 1.0
        
        # WebSocket endpoint
        self.ws_url = f"wss://api.elevenlabs.io/v1/text-to-speech/{self.voice_config.voice_id}/stream-input?model_id={self.voice_config.model_id}"
        
        logger.info(f"ElevenLabs client initialized with voice: {self.voice_config.voice_id}")
    
    async def connect(self) -> bool:
        """Establish WebSocket connection with authentication"""
        try:
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            self.websocket = await websockets.connect(
                self.ws_url,
                extra_headers=headers,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            
            # Send initial configuration
            config_message = {
                "text": " ",  # Initial space to start the stream
                "voice_settings": {
                    "stability": self.voice_config.stability,
                    "similarity_boost": self.voice_config.similarity_boost,
                    "style": self.voice_config.style,
                    "use_speaker_boost": self.voice_config.use_speaker_boost
                },
                "generation_config": {
                    "chunk_length_schedule": [120, 160, 250, 290]  # Optimized for low latency
                }
            }
            
            await self.websocket.send(json.dumps(config_message))
            self.is_connected = True
            self.reconnect_attempts = 0
            
            logger.info("Successfully connected to ElevenLabs WebSocket")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to ElevenLabs: {str(e)}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Gracefully disconnect from WebSocket"""
        if self.websocket:
            try:
                # Send end-of-stream signal
                await self.websocket.send(json.dumps({"text": ""}))
                await self.websocket.close()
            except Exception as e:
                logger.warning(f"Error during disconnect: {str(e)}")
            finally:
                self.websocket = None
                self.is_connected = False
                logger.info("Disconnected from ElevenLabs WebSocket")
    
    async def reconnect(self) -> bool:
        """Attempt to reconnect with exponential backoff"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            return False
        
        self.reconnect_attempts += 1
        delay = self.reconnect_delay * (2 ** (self.reconnect_attempts - 1))
        
        logger.info(f"Attempting reconnection {self.reconnect_attempts}/{self.max_reconnect_attempts} in {delay}s")
        await asyncio.sleep(delay)
        
        return await self.connect()
    
    async def stream_text_to_speech(
        self, 
        text: str, 
        context: str = "general",
        chunk_callback: Optional[Callable[[bytes], None]] = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream text to speech with real-time audio generation
        
        Args:
            text: Text to convert to speech
            context: Context for persona enhancement
            chunk_callback: Optional callback for each audio chunk
            
        Yields:
            Audio chunks as bytes
        """
        if not self.is_connected:
            if not await self.connect():
                raise ConnectionError("Failed to connect to ElevenLabs")
        
        try:
            # Enhance text with SOPHIA persona
            enhanced_text = self.persona.enhance_response(text, context)
            enhanced_text = self.persona.add_conversational_flair(enhanced_text)
            
            logger.info(f"Streaming text to speech: {enhanced_text[:100]}...")
            
            # Send text for processing
            text_message = {"text": enhanced_text}
            await self.websocket.send(json.dumps(text_message))
            
            # Send end-of-stream signal
            await self.websocket.send(json.dumps({"text": ""}))
            
            # Receive and yield audio chunks
            total_chunks = 0
            start_time = time.time()
            
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    
                    if "audio" in data:
                        # Decode base64 audio chunk
                        audio_chunk = base64.b64decode(data["audio"])
                        total_chunks += 1
                        
                        # Call callback if provided
                        if chunk_callback:
                            chunk_callback(audio_chunk)
                        
                        yield audio_chunk
                    
                    elif "isFinal" in data and data["isFinal"]:
                        # Stream completed
                        duration = time.time() - start_time
                        logger.info(f"Stream completed: {total_chunks} chunks in {duration:.2f}s")
                        break
                    
                    elif "error" in data:
                        logger.error(f"ElevenLabs error: {data['error']}")
                        raise Exception(f"ElevenLabs API error: {data['error']}")
                
                except json.JSONDecodeError:
                    # Handle binary audio data
                    if isinstance(message, bytes):
                        total_chunks += 1
                        if chunk_callback:
                            chunk_callback(message)
                        yield message
                
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed, attempting reconnection")
            if await self.reconnect():
                # Retry the request
                async for chunk in self.stream_text_to_speech(text, context, chunk_callback):
                    yield chunk
            else:
                raise ConnectionError("Failed to reconnect to ElevenLabs")
        
        except Exception as e:
            logger.error(f"Error during text-to-speech streaming: {str(e)}")
            raise
    
    async def synthesize_speech(self, text: str, context: str = "general") -> bytes:
        """
        Synthesize complete speech audio from text
        
        Args:
            text: Text to convert to speech
            context: Context for persona enhancement
            
        Returns:
            Complete audio as bytes
        """
        audio_chunks = []
        
        async for chunk in self.stream_text_to_speech(text, context):
            audio_chunks.append(chunk)
        
        return b''.join(audio_chunks)
    
    def get_voice_info(self) -> Dict[str, Any]:
        """Get information about the current voice configuration"""
        return {
            "voice_id": self.voice_config.voice_id,
            "model_id": self.voice_config.model_id,
            "voice_name": "Rachel (SOPHIA Persona)",
            "persona_type": "Smart Asian American Female",
            "settings": {
                "stability": self.voice_config.stability,
                "similarity_boost": self.voice_config.similarity_boost,
                "style": self.voice_config.style,
                "use_speaker_boost": self.voice_config.use_speaker_boost
            },
            "persona_traits": self.voice_config.persona_traits
        }

# Utility functions for testing and integration

async def test_voice_synthesis(text: str = "Hello! I'm SOPHIA, your intelligent AI assistant. How can I help you today?"):
    """Test the voice synthesis with sample text"""
    client = ElevenLabsStreamingClient()
    
    try:
        print(f"Testing voice synthesis with text: {text}")
        
        # Test streaming
        audio_chunks = []
        start_time = time.time()
        
        async for chunk in client.stream_text_to_speech(text, "greeting"):
            audio_chunks.append(chunk)
            print(f"Received audio chunk: {len(chunk)} bytes")
        
        duration = time.time() - start_time
        total_audio = b''.join(audio_chunks)
        
        print(f"Synthesis completed:")
        print(f"- Duration: {duration:.2f} seconds")
        print(f"- Total audio: {len(total_audio)} bytes")
        print(f"- Chunks: {len(audio_chunks)}")
        
        # Save test audio
        test_file = Path("/tmp/sophia_voice_test.mp3")
        with open(test_file, "wb") as f:
            f.write(total_audio)
        
        print(f"Test audio saved to: {test_file}")
        return test_file
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        raise
    finally:
        await client.disconnect()

def create_voice_client() -> ElevenLabsStreamingClient:
    """Factory function to create a configured voice client"""
    return ElevenLabsStreamingClient()

if __name__ == "__main__":
    # Test the voice client
    asyncio.run(test_voice_synthesis())

