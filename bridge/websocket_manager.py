"""
WebSocket Manager for Real-time Updates
Handles live streaming of agent execution plans and logs
"""

import json
import asyncio
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
import structlog

logger = structlog.get_logger()


class ConnectionManager:
    """Manages WebSocket connections for live updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.task_subscriptions: Dict[str, List[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket connected", total_connections=len(self.active_connections))
        
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.remove(websocket)
        # Remove from task subscriptions
        for task_id in list(self.task_subscriptions.keys()):
            if websocket in self.task_subscriptions[task_id]:
                self.task_subscriptions[task_id].remove(websocket)
                if not self.task_subscriptions[task_id]:
                    del self.task_subscriptions[task_id]
        logger.info("WebSocket disconnected", total_connections=len(self.active_connections))
        
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific client"""
        await websocket.send_text(message)
        
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        message_text = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(message_text)
            except:
                # Connection might be closed
                pass
                
    async def broadcast_task_update(self, task_id: str, update: dict):
        """Send update to clients subscribed to a specific task"""
        if task_id in self.task_subscriptions:
            message = json.dumps({
                "type": "task_update",
                "task_id": task_id,
                "data": update
            })
            for connection in self.task_subscriptions[task_id]:
                try:
                    await connection.send_text(message)
                except:
                    pass
                    
    def subscribe_to_task(self, task_id: str, websocket: WebSocket):
        """Subscribe a WebSocket to task updates"""
        if task_id not in self.task_subscriptions:
            self.task_subscriptions[task_id] = []
        if websocket not in self.task_subscriptions[task_id]:
            self.task_subscriptions[task_id].append(websocket)
            
    async def stream_plan_progress(self, task_id: str, plan_section: dict):
        """Stream plan sections as they're generated"""
        await self.broadcast_task_update(task_id, {
            "status": "generating",
            "section": plan_section
        })
        
    async def stream_log_entry(self, log_entry: dict):
        """Stream log entries to all connected clients"""
        await self.broadcast({
            "type": "log",
            "data": log_entry
        })


# Global instance
manager = ConnectionManager()