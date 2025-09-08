"""
WebSocket enhancements for chat service - chunked streaming and keepalive
"""

import asyncio
import json
import time
from typing import AsyncGenerator, Optional

from fastapi import WebSocket
from pydantic import BaseModel


class StreamConfig(BaseModel):
    """Configuration for streaming behavior"""
    chunk_size: int = 10  # Words per chunk
    chunk_delay: float = 0.05  # Seconds between chunks
    typing_effect: bool = True  # Simulate typing
    keepalive_interval: int = 30  # Seconds between pings


class EnhancedWebSocketManager:
    """
    Enhanced WebSocket manager with chunked streaming and keepalive
    """
    
    def __init__(self, config: Optional[StreamConfig] = None):
        self.config = config or StreamConfig()
        self.keepalive_tasks: dict[str, asyncio.Task] = {}
        
    async def stream_tokens_chunked(
        self, 
        text: str, 
        correlation_id: str,
        model: str = "unknown"
    ) -> AsyncGenerator[dict, None]:
        """
        Stream text in word chunks for better UX
        
        Args:
            text: Full text to stream
            correlation_id: Request correlation ID
            model: Model name for metadata
            
        Yields:
            Token envelope dictionaries
        """
        words = text.split()
        sequence = 0
        
        for i in range(0, len(words), self.config.chunk_size):
            # Get chunk of words
            chunk_words = words[i:i + self.config.chunk_size]
            chunk = ' '.join(chunk_words)
            
            # Add space if not last chunk
            if i + self.config.chunk_size < len(words):
                chunk += ' '
            
            # Create token envelope
            envelope = {
                "type": "token",
                "correlation_id": correlation_id,
                "data": {
                    "chunk": chunk,
                    "sequence": sequence,
                    "metadata": {
                        "model": model,
                        "chunk_size": len(chunk_words),
                        "total_words": len(words),
                        "progress": min(100, int((i + len(chunk_words)) / len(words) * 100))
                    }
                }
            }
            
            yield envelope
            sequence += 1
            
            # Add delay for typing effect
            if self.config.typing_effect:
                await asyncio.sleep(self.config.chunk_delay)
        
        # Send completion envelope
        yield {
            "type": "usage",
            "correlation_id": correlation_id,
            "data": {
                "tokens_used": len(words),  # Approximate
                "sequence_final": sequence - 1,
                "status": "complete",
                "total_chunks": sequence
            }
        }
    
    async def start_keepalive(self, websocket: WebSocket, user_id: str):
        """
        Start keepalive task for WebSocket connection
        
        Args:
            websocket: WebSocket connection
            user_id: User identifier
        """
        async def keepalive_loop():
            """Send periodic pings to maintain connection"""
            try:
                while True:
                    await asyncio.sleep(self.config.keepalive_interval)
                    
                    # Send ping message
                    ping_message = {
                        "type": "ping",
                        "timestamp": time.time(),
                        "user_id": user_id
                    }
                    
                    await websocket.send_json(ping_message)
                    
            except asyncio.CancelledError:
                # Task cancelled, cleanup
                pass
            except Exception as e:
                # Connection likely closed
                print(f"Keepalive error for {user_id}: {e}")
        
        # Create and store task
        task = asyncio.create_task(keepalive_loop())
        self.keepalive_tasks[user_id] = task
    
    async def stop_keepalive(self, user_id: str):
        """
        Stop keepalive task for user
        
        Args:
            user_id: User identifier
        """
        if user_id in self.keepalive_tasks:
            task = self.keepalive_tasks[user_id]
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            del self.keepalive_tasks[user_id]
    
    async def handle_pong(self, websocket: WebSocket, pong_data: dict):
        """
        Handle pong response from client
        
        Args:
            websocket: WebSocket connection
            pong_data: Pong message data
        """
        # Could track latency here
        latency = time.time() - pong_data.get("timestamp", time.time())
        
        # Send latency info back
        await websocket.send_json({
            "type": "latency",
            "data": {
                "rtt_ms": int(latency * 1000),
                "timestamp": time.time()
            }
        })
    
    async def stream_with_replay_buffer(
        self,
        text: str,
        correlation_id: str,
        cache_client,
        ttl: int = 300
    ):
        """
        Stream text while building replay buffer in cache
        
        Args:
            text: Full text to stream
            correlation_id: Request correlation ID
            cache_client: Redis client for caching
            ttl: Cache TTL in seconds
        """
        chunks = []
        
        # Stream and collect chunks
        async for envelope in self.stream_tokens_chunked(text, correlation_id):
            if envelope["type"] == "token":
                chunks.append(envelope["data"]["chunk"])
            yield envelope
        
        # Store complete stream for replay
        if cache_client:
            replay_data = {
                "full_response": ''.join(chunks),
                "chunks": chunks,
                "correlation_id": correlation_id,
                "timestamp": time.time(),
                "model": envelope.get("data", {}).get("metadata", {}).get("model", "unknown")
            }
            
            try:
                await cache_client.setex(
                    f"stream:{correlation_id}",
                    ttl,
                    json.dumps(replay_data)
                )
            except Exception as e:
                print(f"Failed to cache stream for replay: {e}")
    
    async def replay_stream(
        self,
        correlation_id: str,
        cache_client,
        start_sequence: int = 0
    ) -> AsyncGenerator[dict, None]:
        """
        Replay a cached stream from specific sequence
        
        Args:
            correlation_id: Original correlation ID
            cache_client: Redis client
            start_sequence: Starting sequence number
            
        Yields:
            Replayed token envelopes
        """
        if not cache_client:
            yield {
                "type": "error",
                "correlation_id": correlation_id,
                "data": {
                    "message": "Cache not available for replay",
                    "code": "CACHE_UNAVAILABLE"
                }
            }
            return
        
        try:
            # Get cached stream
            cached_data = await cache_client.get(f"stream:{correlation_id}")
            if not cached_data:
                yield {
                    "type": "error",
                    "correlation_id": correlation_id,
                    "data": {
                        "message": "No cached stream found",
                        "code": "STREAM_NOT_FOUND"
                    }
                }
                return
            
            replay_data = json.loads(cached_data)
            chunks = replay_data.get("chunks", [])
            model = replay_data.get("model", "unknown")
            
            # Send status envelope
            yield {
                "type": "status",
                "correlation_id": correlation_id,
                "data": {
                    "status": "replaying",
                    "total_chunks": len(chunks),
                    "start_sequence": start_sequence
                }
            }
            
            # Replay chunks from start_sequence
            for sequence, chunk in enumerate(chunks[start_sequence:], start=start_sequence):
                yield {
                    "type": "token",
                    "correlation_id": correlation_id,
                    "data": {
                        "chunk": chunk,
                        "sequence": sequence,
                        "metadata": {
                            "model": model,
                            "replayed": True,
                            "original_timestamp": replay_data.get("timestamp")
                        }
                    }
                }
                
                # Small delay for replay effect
                await asyncio.sleep(0.02)
            
            # Send completion
            yield {
                "type": "usage",
                "correlation_id": correlation_id,
                "data": {
                    "sequence_final": len(chunks) - 1,
                    "status": "replay_complete",
                    "replayed_from": start_sequence
                }
            }
            
        except Exception as e:
            yield {
                "type": "error",
                "correlation_id": correlation_id,
                "data": {
                    "message": f"Replay error: {str(e)}",
                    "code": "REPLAY_ERROR"
                }
            }


class WebSocketMetrics:
    """Track WebSocket performance metrics"""
    
    def __init__(self):
        self.connections = 0
        self.messages_sent = 0
        self.messages_received = 0
        self.bytes_sent = 0
        self.bytes_received = 0
        self.stream_latencies = []
        self.connection_durations = []
        
    def record_connection(self, duration: float):
        """Record connection duration"""
        self.connection_durations.append(duration)
        
    def record_stream_latency(self, latency: float):
        """Record streaming latency"""
        self.stream_latencies.append(latency)
        
    def get_stats(self) -> dict:
        """Get current metrics"""
        return {
            "active_connections": self.connections,
            "total_messages_sent": self.messages_sent,
            "total_messages_received": self.messages_received,
            "total_bytes_sent": self.bytes_sent,
            "total_bytes_received": self.bytes_received,
            "avg_stream_latency": sum(self.stream_latencies) / len(self.stream_latencies) if self.stream_latencies else 0,
            "avg_connection_duration": sum(self.connection_durations) / len(self.connection_durations) if self.connection_durations else 0
        }