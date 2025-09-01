"""
WebSocket Manager for Real-time Updates
Handles WebSocket connections for live swarm execution, memory updates, and metrics
"""

import asyncio
import json
from typing import Dict, Set, Any, Optional
from datetime import datetime
import logging
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class WSConnection:
    """WebSocket connection info"""
    websocket: WebSocket
    client_id: str
    session_id: str
    subscriptions: Set[str]
    connected_at: datetime

class WebSocketManager:
    """
    Manages WebSocket connections for real-time updates
    """
    
    def __init__(self):
        # Active connections
        self.connections: Dict[str, WSConnection] = {}
        
        # Channel subscriptions
        self.channels: Dict[str, Set[str]] = {}
        
        # Message queue for reliability
        self.message_queue: Dict[str, list] = {}
        
        # Metrics
        self.metrics = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_failed": 0
        }
        
    async def initialize(self):
        """Initialize WebSocket manager"""
        logger.info("WebSocket Manager initialized")
    
    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        session_id: str
    ) -> WSConnection:
        """
        Accept new WebSocket connection
        
        Args:
            websocket: FastAPI WebSocket instance
            client_id: Unique client identifier
            session_id: Session identifier
            
        Returns:
            WSConnection instance
        """
        await websocket.accept()
        
        connection = WSConnection(
            websocket=websocket,
            client_id=client_id,
            session_id=session_id,
            subscriptions=set(),
            connected_at=datetime.utcnow()
        )
        
        self.connections[client_id] = connection
        self.metrics["total_connections"] += 1
        self.metrics["active_connections"] += 1
        
        # Send welcome message
        await self.send_to_client(client_id, {
            "type": "connected",
            "client_id": client_id,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Send any queued messages
        await self._send_queued_messages(client_id)
        
        logger.info(f"WebSocket connected: {client_id}")
        return connection
    
    async def disconnect(self, client_id: str):
        """
        Handle WebSocket disconnection
        
        Args:
            client_id: Client to disconnect
        """
        if client_id in self.connections:
            connection = self.connections[client_id]
            
            # Remove from all channels
            for channel in connection.subscriptions:
                if channel in self.channels:
                    self.channels[channel].discard(client_id)
            
            # Close WebSocket
            try:
                await connection.websocket.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")
            
            # Remove connection
            del self.connections[client_id]
            self.metrics["active_connections"] -= 1
            
            logger.info(f"WebSocket disconnected: {client_id}")
    
    async def subscribe(self, client_id: str, channel: str):
        """
        Subscribe client to a channel
        
        Args:
            client_id: Client identifier
            channel: Channel name to subscribe to
        """
        if client_id not in self.connections:
            logger.warning(f"Client {client_id} not connected")
            return
        
        # Add to client's subscriptions
        self.connections[client_id].subscriptions.add(channel)
        
        # Add to channel's subscribers
        if channel not in self.channels:
            self.channels[channel] = set()
        self.channels[channel].add(client_id)
        
        # Confirm subscription
        await self.send_to_client(client_id, {
            "type": "subscribed",
            "channel": channel,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.debug(f"Client {client_id} subscribed to {channel}")
    
    async def unsubscribe(self, client_id: str, channel: str):
        """
        Unsubscribe client from a channel
        
        Args:
            client_id: Client identifier
            channel: Channel to unsubscribe from
        """
        if client_id in self.connections:
            self.connections[client_id].subscriptions.discard(channel)
        
        if channel in self.channels:
            self.channels[channel].discard(client_id)
        
        logger.debug(f"Client {client_id} unsubscribed from {channel}")
    
    async def send_to_client(self, client_id: str, message: Dict[str, Any]):
        """
        Send message to specific client
        
        Args:
            client_id: Target client
            message: Message to send
        """
        if client_id not in self.connections:
            # Queue message for when client reconnects
            if client_id not in self.message_queue:
                self.message_queue[client_id] = []
            self.message_queue[client_id].append(message)
            return
        
        connection = self.connections[client_id]
        
        try:
            await connection.websocket.send_json(message)
            self.metrics["messages_sent"] += 1
        except Exception as e:
            logger.error(f"Failed to send message to {client_id}: {e}")
            self.metrics["messages_failed"] += 1
            
            # Queue message for retry
            if client_id not in self.message_queue:
                self.message_queue[client_id] = []
            self.message_queue[client_id].append(message)
            
            # Disconnect failed client
            await self.disconnect(client_id)
    
    async def broadcast(self, channel: str, message: Dict[str, Any]):
        """
        Broadcast message to all subscribers of a channel
        
        Args:
            channel: Channel to broadcast to
            message: Message to broadcast
        """
        if channel not in self.channels:
            logger.debug(f"No subscribers for channel {channel}")
            return
        
        # Add channel info to message
        message["channel"] = channel
        message["broadcast_time"] = datetime.utcnow().isoformat()
        
        # Send to all subscribers
        tasks = []
        for client_id in self.channels[channel].copy():
            tasks.append(self.send_to_client(client_id, message))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.debug(f"Broadcasted to {len(tasks)} clients on {channel}")
    
    async def broadcast_swarm_event(
        self,
        session_id: str,
        event_type: str,
        data: Dict[str, Any]
    ):
        """
        Broadcast swarm execution event
        
        Args:
            session_id: Session executing the swarm
            event_type: Type of swarm event
            data: Event data
        """
        message = {
            "type": "swarm_event",
            "event_type": event_type,
            "session_id": session_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast(f"swarm_{session_id}", message)
    
    async def broadcast_memory_update(
        self,
        memory_id: str,
        operation: str,
        data: Dict[str, Any]
    ):
        """
        Broadcast memory update event
        
        Args:
            memory_id: Memory item ID
            operation: Operation performed (create, update, delete)
            data: Memory data
        """
        message = {
            "type": "memory_update",
            "memory_id": memory_id,
            "operation": operation,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast("memory_updates", message)
    
    async def broadcast_metrics(self, metrics: Dict[str, Any]):
        """
        Broadcast system metrics
        
        Args:
            metrics: Current system metrics
        """
        message = {
            "type": "metrics",
            "data": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast("system_metrics", message)
    
    async def _send_queued_messages(self, client_id: str):
        """Send any queued messages to reconnected client"""
        if client_id not in self.message_queue:
            return
        
        messages = self.message_queue[client_id]
        if not messages:
            return
        
        logger.info(f"Sending {len(messages)} queued messages to {client_id}")
        
        for message in messages:
            await self.send_to_client(client_id, message)
        
        # Clear queue
        del self.message_queue[client_id]
    
    async def handle_client_message(
        self,
        client_id: str,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle incoming message from client
        
        Args:
            client_id: Source client
            message: Received message
            
        Returns:
            Response to send back
        """
        msg_type = message.get("type")
        
        if msg_type == "ping":
            return {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
        
        elif msg_type == "subscribe":
            channel = message.get("channel")
            if channel:
                await self.subscribe(client_id, channel)
                return {"type": "subscribed", "channel": channel}
        
        elif msg_type == "unsubscribe":
            channel = message.get("channel")
            if channel:
                await self.unsubscribe(client_id, channel)
                return {"type": "unsubscribed", "channel": channel}
        
        elif msg_type == "get_metrics":
            return {
                "type": "metrics",
                "data": self.get_metrics()
            }
        
        else:
            return {
                "type": "error",
                "message": f"Unknown message type: {msg_type}"
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get WebSocket manager metrics"""
        return {
            **self.metrics,
            "channels": {
                channel: len(subscribers)
                for channel, subscribers in self.channels.items()
            },
            "queued_messages": {
                client: len(messages)
                for client, messages in self.message_queue.items()
            }
        }
    
    async def websocket_endpoint(self, websocket: WebSocket, client_id: str, session_id: str):
        """
        FastAPI WebSocket endpoint handler
        
        Usage in FastAPI:
        @app.websocket("/ws/{client_id}/{session_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str, session_id: str):
            await ws_manager.websocket_endpoint(websocket, client_id, session_id)
        """
        connection = await self.connect(websocket, client_id, session_id)
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_json()
                
                # Handle message
                response = await self.handle_client_message(client_id, data)
                
                # Send response
                if response:
                    await self.send_to_client(client_id, response)
                    
        except WebSocketDisconnect:
            await self.disconnect(client_id)
        except Exception as e:
            logger.error(f"WebSocket error for {client_id}: {e}")
            await self.disconnect(client_id)