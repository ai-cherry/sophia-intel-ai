#!/usr/bin/env python3
"""
Gong Webhook Handler for Real-time Event Processing
Handles incoming Gong webhooks and triggers appropriate processing pipelines
"""
import hashlib
import hmac
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Header, Request, BackgroundTasks
from pydantic import BaseModel, Field
import redis.asyncio as redis

from app.integrations.gong_optimized_client import GongOptimizedClient
from app.integrations.gong_rag_pipeline import GongRAGPipeline
from app.core.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/gong", tags=["gong"])

# Redis for event queuing
REDIS_URL = "redis://localhost:6380"


class GongEventType(str, Enum):
    """Gong webhook event types"""
    CALL_CREATED = "call.created"
    CALL_UPDATED = "call.updated"
    CALL_ENDED = "call.ended"
    TRANSCRIPT_READY = "transcript.ready"
    CALL_RECORDING_READY = "recording.ready"
    DEAL_CREATED = "deal.created"
    DEAL_UPDATED = "deal.updated"
    ENGAGEMENT_SCORE_UPDATED = "engagement.score.updated"


class GongWebhookPayload(BaseModel):
    """Gong webhook payload structure"""
    event_type: GongEventType
    event_id: str
    timestamp: datetime
    call_id: Optional[str] = None
    deal_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    

class GongWebhookHandler:
    """
    Handles incoming Gong webhooks with:
    - Signature verification for security
    - Event queuing for reliability
    - Async processing for performance
    - Real-time notifications via WebSocket
    """
    
    def __init__(self):
        self.redis_client = None
        self.gong_client = None
        self.rag_pipeline = None
        self.ws_manager = WebSocketManager()
        self.webhook_secret = "your_webhook_secret"  # Should be from env
        
    async def setup(self):
        """Initialize connections"""
        self.redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        self.gong_client = GongOptimizedClient()
        self.rag_pipeline = GongRAGPipeline()
        await self.rag_pipeline.setup()
        
    async def cleanup(self):
        """Cleanup connections"""
        if self.redis_client:
            await self.redis_client.aclose()
            
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature for security
        """
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
        
    async def queue_event(self, event: GongWebhookPayload) -> str:
        """
        Queue event for processing with Redis
        """
        event_key = f"gong:event:{event.event_id}"
        event_data = event.model_dump_json()
        
        # Store event
        await self.redis_client.setex(event_key, 86400, event_data)  # 24h TTL
        
        # Add to processing queue
        queue_key = f"gong:queue:{event.event_type}"
        await self.redis_client.lpush(queue_key, event.event_id)
        
        # Publish for real-time subscribers
        await self.redis_client.publish(f"gong:events:{event.event_type}", event_data)
        
        return event_key
        
    async def process_event(self, event: GongWebhookPayload):
        """
        Process Gong event based on type
        """
        logger.info(f"Processing Gong event: {event.event_type} - {event.event_id}")
        
        try:
            if event.event_type == GongEventType.TRANSCRIPT_READY:
                await self._process_transcript_ready(event)
            elif event.event_type == GongEventType.CALL_ENDED:
                await self._process_call_ended(event)
            elif event.event_type == GongEventType.ENGAGEMENT_SCORE_UPDATED:
                await self._process_engagement_update(event)
            elif event.event_type in [GongEventType.DEAL_CREATED, GongEventType.DEAL_UPDATED]:
                await self._process_deal_event(event)
            else:
                logger.info(f"Event type {event.event_type} not specifically handled")
                
            # Notify via WebSocket
            await self._notify_clients(event)
            
        except Exception as e:
            logger.error(f"Error processing event {event.event_id}: {e}")
            raise
            
    async def _process_transcript_ready(self, event: GongWebhookPayload):
        """
        Process transcript ready event - main intelligence extraction
        """
        call_id = event.call_id
        if not call_id:
            return
            
        logger.info(f"Processing transcript for call {call_id}")
        
        async with self.gong_client as client:
            # Fetch transcript
            transcript_data = await client.get_call_transcript([call_id])
            
            # Fetch call metadata
            call_data = await client.get_call_extensive(call_ids=[call_id])
            
            # Process through RAG pipeline
            insights = await self.rag_pipeline.process_transcript(
                transcript_data,
                call_data.get("calls", [{}])[0] if call_data.get("calls") else {}
            )
            
            # Store insights
            for insight in insights:
                insight_key = f"gong:insight:{call_id}:{insight.insight_type}"
                await self.redis_client.setex(
                    insight_key,
                    604800,  # 7 days
                    json.dumps({
                        "call_id": insight.call_id,
                        "type": insight.insight_type,
                        "title": insight.title,
                        "description": insight.description,
                        "confidence": insight.confidence,
                        "recommendations": insight.recommendations,
                        "timestamp": insight.timestamp.isoformat(),
                    })
                )
                
            logger.info(f"Extracted {len(insights)} insights from call {call_id}")
            
    async def _process_call_ended(self, event: GongWebhookPayload):
        """
        Process call ended event - quick summary generation
        """
        call_id = event.call_id
        if not call_id:
            return
            
        # Queue for transcript processing when ready
        await self.redis_client.lpush("gong:pending_transcripts", call_id)
        
        # Send immediate notification
        notification = {
            "type": "call_ended",
            "call_id": call_id,
            "timestamp": event.timestamp.isoformat(),
            "message": f"Call {call_id} has ended. Transcript processing queued.",
        }
        
        await self.ws_manager.broadcast(json.dumps(notification))
        
    async def _process_engagement_update(self, event: GongWebhookPayload):
        """
        Process engagement score update - risk/opportunity detection
        """
        call_id = event.call_id
        engagement_data = event.data.get("engagement", {})
        
        # Analyze engagement trends
        score = engagement_data.get("score", 0)
        trend = engagement_data.get("trend", "stable")
        
        if score < 40 and trend == "declining":
            # Create risk alert
            alert = {
                "type": "engagement_risk",
                "call_id": call_id,
                "score": score,
                "trend": trend,
                "severity": "high" if score < 25 else "medium",
                "recommendation": "Immediate follow-up recommended",
                "timestamp": event.timestamp.isoformat(),
            }
            
            # Store alert
            await self.redis_client.setex(
                f"gong:alert:{call_id}:engagement",
                86400,
                json.dumps(alert)
            )
            
            # Notify
            await self.ws_manager.broadcast(json.dumps(alert))
            
    async def _process_deal_event(self, event: GongWebhookPayload):
        """
        Process deal events - track deal progression
        """
        deal_id = event.deal_id
        deal_data = event.data
        
        # Store deal update
        await self.redis_client.hset(
            f"gong:deal:{deal_id}",
            mapping={
                "status": deal_data.get("status", "unknown"),
                "amount": str(deal_data.get("amount", 0)),
                "close_date": deal_data.get("close_date", ""),
                "stage": deal_data.get("stage", ""),
                "updated_at": event.timestamp.isoformat(),
            }
        )
        
        # Check for significant changes
        if deal_data.get("stage_changed"):
            notification = {
                "type": "deal_stage_change",
                "deal_id": deal_id,
                "new_stage": deal_data.get("stage"),
                "timestamp": event.timestamp.isoformat(),
            }
            await self.ws_manager.broadcast(json.dumps(notification))
            
    async def _notify_clients(self, event: GongWebhookPayload):
        """
        Send real-time notifications to connected clients
        """
        notification = {
            "source": "gong",
            "event_type": event.event_type,
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "data": {
                "call_id": event.call_id,
                "deal_id": event.deal_id,
                **event.data,
            }
        }
        
        await self.ws_manager.broadcast(json.dumps(notification))


# Initialize handler
webhook_handler = GongWebhookHandler()


@router.on_event("startup")
async def startup_event():
    """Initialize webhook handler on startup"""
    await webhook_handler.setup()
    

@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await webhook_handler.cleanup()
    

@router.post("/")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_gong_signature: Optional[str] = Header(None),
):
    """
    Receive and process Gong webhook events
    """
    # Get raw payload for signature verification
    payload = await request.body()
    
    # Verify signature if provided
    if x_gong_signature:
        if not webhook_handler.verify_signature(payload, x_gong_signature):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse payload
    try:
        data = json.loads(payload)
        event = GongWebhookPayload(**data)
    except Exception as e:
        logger.error(f"Invalid webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    
    # Queue event for processing
    event_key = await webhook_handler.queue_event(event)
    
    # Process in background
    background_tasks.add_task(webhook_handler.process_event, event)
    
    return {
        "status": "accepted",
        "event_id": event.event_id,
        "event_key": event_key,
        "queued_at": datetime.now().isoformat(),
    }


@router.get("/status")
async def webhook_status():
    """
    Get webhook processing status
    """
    if not webhook_handler.redis_client:
        return {"status": "not_initialized"}
        
    # Get queue sizes
    queues = [
        "call.created",
        "call.ended",
        "transcript.ready",
        "deal.created",
        "deal.updated",
    ]
    
    queue_status = {}
    for queue in queues:
        queue_key = f"gong:queue:{queue}"
        size = await webhook_handler.redis_client.llen(queue_key)
        queue_status[queue] = size
        
    return {
        "status": "operational",
        "queues": queue_status,
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/test")
async def test_webhook(background_tasks: BackgroundTasks):
    """
    Test webhook processing with sample data
    """
    # Create test event
    test_event = GongWebhookPayload(
        event_type=GongEventType.TRANSCRIPT_READY,
        event_id=f"test_{datetime.now().timestamp()}",
        timestamp=datetime.now(),
        call_id="test_call_123",
        data={
            "title": "Test Call",
            "duration": 1800,
            "participants": ["Sales Rep", "Customer"],
        }
    )
    
    # Queue and process
    event_key = await webhook_handler.queue_event(test_event)
    background_tasks.add_task(webhook_handler.process_event, test_event)
    
    return {
        "status": "test_event_queued",
        "event": test_event.model_dump(),
        "event_key": event_key,
    }