"""
Real-time Gong Integration for Sales Intelligence Swarm

This module provides WebSocket-based real-time connectivity to Gong for:
- Live call monitoring and streaming
- Real-time transcription updates
- Event-driven notifications
- Audio buffer management
"""

import asyncio
import json
import logging
import time
import base64
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, AsyncGenerator
from dataclasses import dataclass, asdict
from enum import Enum

import aiohttp
import websockets
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class CallEvent(str, Enum):
    """Types of call events from Gong"""
    CALL_STARTED = "call_started"
    CALL_ENDED = "call_ended"
    TRANSCRIPT_UPDATE = "transcript_update"
    PARTICIPANT_JOINED = "participant_joined"
    PARTICIPANT_LEFT = "participant_left"
    AUDIO_CHUNK = "audio_chunk"
    METADATA_UPDATE = "metadata_update"


@dataclass
class CallParticipant:
    """Call participant information"""
    user_id: str
    email: str
    name: str
    role: str  # host, participant, guest
    joined_at: datetime
    is_internal: bool = True


@dataclass
class TranscriptSegment:
    """Individual transcript segment"""
    speaker_id: str
    speaker_name: str
    text: str
    start_time: float
    end_time: float
    confidence: float
    is_final: bool = True


@dataclass
class CallMetadata:
    """Call metadata and context"""
    call_id: str
    call_url: str
    title: str
    scheduled_start: datetime
    actual_start: Optional[datetime]
    duration_seconds: Optional[int]
    participants: List[CallParticipant]
    meeting_platform: str  # zoom, teams, etc.
    recording_status: str
    tags: List[str]


@dataclass
class RealtimeCallData:
    """Complete real-time call data structure"""
    metadata: CallMetadata
    transcripts: List[TranscriptSegment]
    last_update: datetime
    is_active: bool
    audio_buffer: Optional[bytes] = None


class GongWebSocketHandler:
    """Handles WebSocket connections to Gong's real-time API"""
    
    def __init__(self, access_key: str, client_secret: str, base_url: str = "wss://api.gong.io/v2"):
        self.access_key = access_key
        self.client_secret = client_secret
        self.base_url = base_url
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.event_handlers: Dict[CallEvent, List[Callable]] = {event: [] for event in CallEvent}
        self.active_calls: Dict[str, RealtimeCallData] = {}
        
    async def authenticate(self) -> str:
        """Authenticate with Gong and get WebSocket token"""
        auth_url = "https://api.gong.io/v2/auth/token"
        auth_string = base64.b64encode(f"{self.access_key}:{self.client_secret}".encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_string}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(auth_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("access_token")
                else:
                    raise Exception(f"Authentication failed: {response.status}")

    def register_event_handler(self, event: CallEvent, handler: Callable):
        """Register a callback for specific call events"""
        self.event_handlers[event].append(handler)

    async def connect_to_call(self, call_id: str) -> None:
        """Establish WebSocket connection for specific call"""
        try:
            token = await self.authenticate()
            ws_url = f"{self.base_url}/calls/{call_id}/stream"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "X-API-Version": "2024-01-01"
            }
            
            async with websockets.connect(ws_url, extra_headers=headers) as websocket:
                self.connections[call_id] = websocket
                logger.info(f"Connected to call {call_id}")
                
                # Start listening for messages
                await self._listen_for_messages(call_id, websocket)
                
        except Exception as e:
            logger.error(f"Failed to connect to call {call_id}: {e}")
            raise

    async def _listen_for_messages(self, call_id: str, websocket):
        """Listen for real-time messages from Gong WebSocket"""
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._process_message(call_id, data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received for call {call_id}: {message}")
                except Exception as e:
                    logger.error(f"Error processing message for call {call_id}: {e}")
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket connection closed for call {call_id}")
        except Exception as e:
            logger.error(f"WebSocket error for call {call_id}: {e}")
        finally:
            if call_id in self.connections:
                del self.connections[call_id]

    async def _process_message(self, call_id: str, data: Dict[str, Any]):
        """Process incoming WebSocket messages"""
        event_type = CallEvent(data.get("event_type", ""))
        
        # Update active call data
        if call_id not in self.active_calls:
            self.active_calls[call_id] = self._create_empty_call_data(call_id)
        
        call_data = self.active_calls[call_id]
        
        # Process based on event type
        if event_type == CallEvent.CALL_STARTED:
            await self._handle_call_started(call_id, data, call_data)
        elif event_type == CallEvent.TRANSCRIPT_UPDATE:
            await self._handle_transcript_update(call_id, data, call_data)
        elif event_type == CallEvent.AUDIO_CHUNK:
            await self._handle_audio_chunk(call_id, data, call_data)
        elif event_type == CallEvent.CALL_ENDED:
            await self._handle_call_ended(call_id, data, call_data)
        elif event_type == CallEvent.PARTICIPANT_JOINED:
            await self._handle_participant_joined(call_id, data, call_data)
        elif event_type == CallEvent.PARTICIPANT_LEFT:
            await self._handle_participant_left(call_id, data, call_data)
        
        # Notify registered handlers
        for handler in self.event_handlers[event_type]:
            try:
                await handler(call_id, data, call_data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")

    def _create_empty_call_data(self, call_id: str) -> RealtimeCallData:
        """Create empty call data structure"""
        return RealtimeCallData(
            metadata=CallMetadata(
                call_id=call_id,
                call_url="",
                title="",
                scheduled_start=datetime.now(),
                actual_start=None,
                duration_seconds=None,
                participants=[],
                meeting_platform="unknown",
                recording_status="unknown",
                tags=[]
            ),
            transcripts=[],
            last_update=datetime.now(),
            is_active=True
        )

    async def _handle_call_started(self, call_id: str, data: Dict, call_data: RealtimeCallData):
        """Handle call start event"""
        call_data.metadata.actual_start = datetime.now()
        call_data.metadata.title = data.get("title", "")
        call_data.metadata.call_url = data.get("call_url", "")
        call_data.metadata.meeting_platform = data.get("platform", "unknown")
        call_data.last_update = datetime.now()
        
        logger.info(f"Call started: {call_id} - {call_data.metadata.title}")

    async def _handle_transcript_update(self, call_id: str, data: Dict, call_data: RealtimeCallData):
        """Handle real-time transcript updates"""
        segment_data = data.get("transcript", {})
        
        segment = TranscriptSegment(
            speaker_id=segment_data.get("speaker_id", ""),
            speaker_name=segment_data.get("speaker_name", ""),
            text=segment_data.get("text", ""),
            start_time=segment_data.get("start_time", 0.0),
            end_time=segment_data.get("end_time", 0.0),
            confidence=segment_data.get("confidence", 0.0),
            is_final=segment_data.get("is_final", True)
        )
        
        # Update or append transcript segment
        if segment.is_final:
            call_data.transcripts.append(segment)
        else:
            # Update provisional transcript
            for i, existing in enumerate(call_data.transcripts):
                if (existing.speaker_id == segment.speaker_id and 
                    abs(existing.start_time - segment.start_time) < 1.0):
                    call_data.transcripts[i] = segment
                    break
            else:
                call_data.transcripts.append(segment)
        
        call_data.last_update = datetime.now()

    async def _handle_audio_chunk(self, call_id: str, data: Dict, call_data: RealtimeCallData):
        """Handle audio chunk for real-time processing"""
        audio_data = data.get("audio_data")
        if audio_data:
            # Decode base64 audio
            call_data.audio_buffer = base64.b64decode(audio_data)
            call_data.last_update = datetime.now()

    async def _handle_call_ended(self, call_id: str, data: Dict, call_data: RealtimeCallData):
        """Handle call end event"""
        call_data.is_active = False
        call_data.metadata.duration_seconds = data.get("duration_seconds")
        call_data.last_update = datetime.now()
        
        logger.info(f"Call ended: {call_id} - Duration: {call_data.metadata.duration_seconds}s")

    async def _handle_participant_joined(self, call_id: str, data: Dict, call_data: RealtimeCallData):
        """Handle participant joining"""
        participant_data = data.get("participant", {})
        participant = CallParticipant(
            user_id=participant_data.get("user_id", ""),
            email=participant_data.get("email", ""),
            name=participant_data.get("name", ""),
            role=participant_data.get("role", "participant"),
            joined_at=datetime.now(),
            is_internal=participant_data.get("is_internal", True)
        )
        
        call_data.metadata.participants.append(participant)
        call_data.last_update = datetime.now()

    async def _handle_participant_left(self, call_id: str, data: Dict, call_data: RealtimeCallData):
        """Handle participant leaving"""
        user_id = data.get("user_id", "")
        call_data.metadata.participants = [
            p for p in call_data.metadata.participants 
            if p.user_id != user_id
        ]
        call_data.last_update = datetime.now()

    def get_call_data(self, call_id: str) -> Optional[RealtimeCallData]:
        """Get current call data"""
        return self.active_calls.get(call_id)

    def get_active_calls(self) -> List[str]:
        """Get list of active call IDs"""
        return [call_id for call_id, data in self.active_calls.items() if data.is_active]

    async def disconnect_from_call(self, call_id: str):
        """Disconnect from specific call"""
        if call_id in self.connections:
            await self.connections[call_id].close()
            del self.connections[call_id]
        
        if call_id in self.active_calls:
            self.active_calls[call_id].is_active = False

    async def disconnect_all(self):
        """Disconnect from all calls"""
        for call_id in list(self.connections.keys()):
            await self.disconnect_from_call(call_id)


class GongRealtimeConnector:
    """Main connector class for Gong real-time integration"""
    
    def __init__(self, access_key: str, client_secret: str):
        self.ws_handler = GongWebSocketHandler(access_key, client_secret)
        self.webhook_callbacks: Dict[str, List[Callable]] = {}
        
    async def start_monitoring_call(self, call_id: str, callbacks: Dict[CallEvent, List[Callable]] = None):
        """Start monitoring a specific call"""
        if callbacks:
            for event, handlers in callbacks.items():
                for handler in handlers:
                    self.ws_handler.register_event_handler(event, handler)
        
        await self.ws_handler.connect_to_call(call_id)

    async def get_live_calls(self) -> AsyncGenerator[RealtimeCallData, None]:
        """Stream live call data"""
        while True:
            for call_data in self.ws_handler.active_calls.values():
                if call_data.is_active:
                    yield call_data
            await asyncio.sleep(1)  # Poll every second

    def setup_webhook_handler(self, event_type: str, callback: Callable):
        """Setup webhook handler for Gong events"""
        if event_type not in self.webhook_callbacks:
            self.webhook_callbacks[event_type] = []
        self.webhook_callbacks[event_type].append(callback)

    async def process_webhook(self, webhook_data: Dict[str, Any]):
        """Process incoming webhook from Gong"""
        event_type = webhook_data.get("eventType", "")
        
        if event_type in self.webhook_callbacks:
            for callback in self.webhook_callbacks[event_type]:
                try:
                    await callback(webhook_data)
                except Exception as e:
                    logger.error(f"Error processing webhook {event_type}: {e}")


# Utility functions for integration
def create_gong_connector(access_key: str = None, client_secret: str = None) -> GongRealtimeConnector:
    """Create a Gong connector with live credentials from integrations config"""
    import os
    
    # Try provided parameters first
    if access_key and client_secret:
        return GongRealtimeConnector(access_key, client_secret)
    
    # Try environment variables
    access_key = access_key or os.getenv("GONG_ACCESS_KEY")
    client_secret = client_secret or os.getenv("GONG_CLIENT_SECRET")
    
    # Use live integrations config as fallback
    if not access_key or not client_secret:
        try:
            from app.api.integrations_config import INTEGRATIONS, get_platform_client
            gong_config = get_platform_client("gong")
            access_key = gong_config["access_key"]
            client_secret = gong_config["client_secret"]
            logger.info("Using live Gong credentials from integrations config")
        except Exception as e:
            logger.error(f"Failed to load live Gong credentials: {e}")
            raise ValueError("Gong credentials not available from any source")
    
    if not access_key or not client_secret:
        raise ValueError("Gong credentials not provided")
    
    return GongRealtimeConnector(access_key, client_secret)


# Example usage and testing
async def example_usage():
    """Example of how to use the Gong real-time connector"""
    
    # Create connector
    connector = create_gong_connector()
    
    # Define event handlers
    async def on_transcript_update(call_id: str, data: Dict, call_data: RealtimeCallData):
        print(f"New transcript for {call_id}: {data}")
    
    async def on_call_started(call_id: str, data: Dict, call_data: RealtimeCallData):
        print(f"Call started: {call_id}")
    
    # Start monitoring
    callbacks = {
        CallEvent.TRANSCRIPT_UPDATE: [on_transcript_update],
        CallEvent.CALL_STARTED: [on_call_started]
    }
    
    call_id = "example-call-id"
    await connector.start_monitoring_call(call_id, callbacks)
    
    # Stream live data
    async for call_data in connector.get_live_calls():
        print(f"Live call data: {call_data.metadata.title}")
        if len(call_data.transcripts) > 10:
            break


if __name__ == "__main__":
    asyncio.run(example_usage())