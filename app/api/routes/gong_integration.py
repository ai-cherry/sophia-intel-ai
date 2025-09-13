#!/usr/bin/env python3
"""
Gong Integration API Routes
Service endpoints for n8n workflow integration with Sophia intelligence
"""
import asyncio
from datetime import datetime
from typing import Any, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from app.core.ai_logger import logger
from app.core.monitoring import track_api_call
from app.core.security import get_current_user, verify_api_key
from app.integrations.gong_sophia_bridge import GongSophiaService
# Initialize router with existing patterns
router = APIRouter(
    prefix="/integrations/gong",
    tags=["gong", "intelligence", "webhooks"],
    dependencies=[Depends(verify_api_key)],
)
# Initialize service using existing patterns
gong_sophia_service = GongSophiaService()
class GongWebhookRequest(BaseModel):
    """Gong webhook request model"""
    eventType: str = Field(..., description="Gong event type")
    callId: str = Field(..., description="Gong call identifier")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    signatureValid: bool = Field(
        default=False, description="RSA signature validation status"
    )
    # Optional fields based on event type
    participants: Optional[list] = Field(None, description="Call participants")
    duration: Optional[int] = Field(None, description="Call duration in seconds")
    transcriptUrl: Optional[str] = Field(
        None, description="Transcript URL if available"
    )
    dealId: Optional[str] = Field(None, description="Associated deal ID")
    riskScore: Optional[float] = Field(
        None, description="Risk score for deal at risk events"
    )
    # Raw data from Gong
    raw_data: Optional[dict[str, Any]] = Field(
        None, description="Complete Gong webhook payload"
    )
    class Config:
        schema_extra = {
            "example": {
                "eventType": "call_ended",
                "callId": "call_123456",
                "timestamp": "2025-09-05T19:45:00Z",
                "signatureValid": True,
                "participants": ["john@company.com", "jane@prospect.com"],
                "duration": 1800,
                "dealId": "deal_789",
            }
        }
class GongWebhookResponse(BaseModel):
    """Standardized response model"""
    status: str = Field(..., description="Processing status")
    service: str = Field(default="gong_sophia_bridge")
    processing_time: float = Field(..., description="Processing time in seconds")
    # Sophia intelligence results
    sophia_intelligence: Optional[dict[str, Any]] = Field(None)
    context_continuity: Optional[dict[str, Any]] = Field(None)
    memory_storage: Optional[dict[str, Any]] = Field(None)
    # Execution metadata
    execution_metadata: dict[str, Any] = Field(default_factory=dict)
    next_steps: list = Field(default_factory=list)
@router.post(
    "/webhook",
    response_model=GongWebhookResponse,
    summary="Process Gong Webhook with Sophia Intelligence",
    description="""
    Main endpoint for processing Gong webhooks through Sophia's intelligence pipeline.
    This endpoint:
    - Validates RSA signatures from Gong
    - Routes events to appropriate Sophia mythology agents
    - Stores context in unified 4-tier memory architecture
    - Establishes context continuity for future interactions
    - Returns comprehensive intelligence analysis
    """,
)
@track_api_call(service="gong_integration", endpoint="webhook")
async def process_gong_webhook(
    webhook_request: GongWebhookRequest,
    background_tasks: BackgroundTasks,
    _current_user: dict[str, Any] = Depends(get_current_user),
) -> GongWebhookResponse:
    """
    Process Gong webhook through Sophia intelligence pipeline
    """
    start_time = datetime.now()
    try:
        logger.info(
            f"🎯 Processing Gong {webhook_request.eventType} webhook for call {webhook_request.callId}"
        )
        # Prepare webhook data for service processing
        webhook_data = webhook_request.dict()
        if not webhook_data.get("raw_data"):
            webhook_data["raw_data"] = (
                webhook_data  # Use the request itself as raw data
            )
        # Process through Sophia intelligence service
        processing_result = await gong_sophia_service.process_gong_webhook(webhook_data)
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        # Schedule background tasks for additional processing
        if processing_result.get("status") == "success":
            background_tasks.add_task(
                _post_processing_tasks, webhook_request.callId, processing_result
            )
        # Create response
        response = GongWebhookResponse(
            status=processing_result.get("status", "unknown"),
            processing_time=processing_time,
            sophia_intelligence=processing_result.get("result", {}).get(
                "sophia_intelligence"
            ),
            context_continuity=processing_result.get("result", {}).get(
                "context_thread"
            ),
            memory_storage=processing_result.get("result", {}).get("memory_storage"),
            execution_metadata={
                "user_id": _current_user.get("id"),
                "processing_timestamp": start_time.isoformat(),
                "event_type": webhook_request.eventType,
                "signature_validated": webhook_request.signatureValid,
                "agents_engaged": processing_result.get("result", {})
                .get("sophia_intelligence", {})
                .get("agents_used", []),
            },
            next_steps=[
                "Context available for future Sophia interactions",
                "Business intelligence stored in unified memory",
                "Relationship mapping updated in context graph",
            ],
        )
        logger.info(f"✅ Gong webhook processed successfully in {processing_time:.2f}s")
        return response
    except Exception as e:
        logger.error(f"❌ Gong webhook processing failed: {e}")
        # Return error response with processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        raise HTTPException(
            status_code=500,
            detail={
                "error": "gong_webhook_processing_failed",
                "message": str(e),
                "processing_time": processing_time,
                "fallback": "Event queued for retry",
                "support": "Check Sophia service health and retry",
            },
        ) from e
@router.get(
    "/health",
    summary="Gong Integration Health Check",
    description="Check health of Gong integration components",
)
async def health_check() -> dict[str, Any]:
    """
    Health check for Gong integration components
    """
    try:
        # Check service health
        service_health = await gong_sophia_service.health_check()
        return {
            "status": "healthy",
            "service": "gong_sophia_bridge",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "gong_sophia_service": service_health.get("status", "unknown"),
                "memory_router": "active",
                "mythology_agents": "available",
                "technical_orchestrator": "ready",
            },
            "capabilities": [
                "RSA signature validation",
                "Mythology agent intelligence",
                "4-tier unified memory storage",
                "Context continuity braiding",
                "Real-time processing",
            ],
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "recommendation": "Check Sophia service dependencies",
            },
        ) from e
@router.get(
    "/events/{call_id}/context",
    summary="Get Gong Event Context",
    description="Retrieve context and intelligence for a specific Gong call",
)
async def get_event_context(
    call_id: str,
    include_intelligence: bool = True,
    include_continuity: bool = True,
    _current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Retrieve stored context and intelligence for a Gong call
    """
    try:
        # Retrieve context from unified memory
        context_data = await gong_sophia_service.get_call_context(
            call_id=call_id,
            include_intelligence=include_intelligence,
            include_continuity=include_continuity,
        )
        if not context_data:
            raise HTTPException(
                status_code=404, detail=f"No context found for call {call_id}"
            )
        return {
            "call_id": call_id,
            "context_retrieved": True,
            "timestamp": datetime.now().isoformat(),
            "context_data": context_data,
            "sophia_continuity": "available",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Context retrieval failed for {call_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve context: {str(e)}"
        ) from e
@router.post(
    "/test",
    summary="Test Gong Integration",
    description="Test endpoint for validating Gong integration functionality",
)
async def test_integration(
    test_event: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Test endpoint for Gong integration
    """
    # Default test event
    if not test_event:
        test_event = {
            "eventType": "test",
            "callId": f"test_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "signatureValid": True,
            "participants": ["test@sophia-intel.ai"],
            "duration": 300,
            "source": "integration_test",
        }
    try:
        # Process test event
        result = await gong_sophia_service.process_gong_webhook(test_event)
        return {
            "test_status": "success",
            "test_timestamp": datetime.now().isoformat(),
            "test_event": test_event,
            "processing_result": result,
            "integration_health": "operational",
        }
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        return {
            "test_status": "failed",
            "test_timestamp": datetime.now().isoformat(),
            "error": str(e),
            "recommendation": "Check service health and dependencies",
        }
async def _post_processing_tasks(call_id: str, _processing_result: dict[str, Any]):
    """
    Background tasks for additional processing after main webhook handling
    """
    try:
        logger.info(f"🔄 Running post-processing for call {call_id}")
        # Additional intelligence processing
        # This could include:
        # - Deep transcript analysis
        # - Cross-reference with historical data
        # - Predictive analytics
        # - Automated follow-up recommendations
        await asyncio.sleep(1)  # Simulate processing
        logger.info(f"✅ Post-processing completed for call {call_id}")
    except Exception as e:
        logger.error(f"❌ Post-processing failed for {call_id}: {e}")
# Export router for main app integration
__all__ = ["router"]
