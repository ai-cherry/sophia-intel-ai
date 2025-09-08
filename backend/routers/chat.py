"""
Sophia AI Platform v4.0 - Chat Router
Integrates with UnifiedChatService for intelligent query processing
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from models.roles import Role, RolePermissions, require_auth, require_permission
from services.unified_chat import UnifiedChatService

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize unified chat service
chat_service = UnifiedChatService()

# Request/Response models
class ChatQueryRequest(BaseModel):
    """Chat query request model"""
    query: str = Field(..., min_length=1, max_length=2000, description="User query")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")
    stream: bool = Field(default=False, description="Enable streaming response")

class ChatQueryResponse(BaseModel):
    """Chat query response model"""
    response: str = Field(..., description="Generated response")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Information sources")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Response confidence score")
    processing_time: float = Field(..., description="Processing time in seconds")
    intent: Dict[str, Any] = Field(default_factory=dict, description="Detected intent")
    cached: bool = Field(default=False, description="Whether response was cached")
    timestamp: datetime = Field(default_factory=datetime.now)

class ChatHistoryResponse(BaseModel):
    """Chat history response model"""
    conversations: List[Dict[str, Any]] = Field(default_factory=list)
    total_count: int = Field(default=0)
    page: int = Field(default=1)
    page_size: int = Field(default=20)

class ServiceStatsResponse(BaseModel):
    """Service statistics response model"""
    web_circuit: Dict[str, Any] = Field(default_factory=dict)
    mcp_circuit: Dict[str, Any] = Field(default_factory=dict)
    intent_cache_size: int = Field(default=0)
    predictive_cache_size: int = Field(default=0)
    uptime: float = Field(default=0.0)

# Dependency for user context
async def get_user_context() -> Dict[str, Any]:
    """
    Extract user context from request
    In a real implementation, this would extract from JWT token
    """
    # Placeholder implementation
    return {
        "user_id": "demo_user",
        "role": "manager",
        "domains": ["chat", "sales", "marketing", "bi"],
        "preferences": {
            "response_style": "detailed",
            "max_sources": 3
        }
    }

# Chat endpoints
@router.post("/query", 
            response_model=ChatQueryResponse,
            summary="Process chat query",
            description="Process user query with intelligent source blending")
@require_auth
@require_permission("domains.chat")
async def chat_query(
    request: ChatQueryRequest,
    user_context: Dict[str, Any] = Depends(get_user_context)
) -> ChatQueryResponse:
    """
    Process chat query with intelligent blending from multiple sources

    - **query**: User question or request
    - **context**: Additional context for query processing
    - **stream**: Enable streaming response (not implemented yet)
    """
    try:
        logger.info(f"🔍 Processing chat query: {request.query[:100]}...")

        # Merge request context with user context
        full_context = {**user_context, **request.context}

        # Process query through unified chat service
        result = await chat_service.process_query(request.query, full_context)

        # Convert to response model
        response = ChatQueryResponse(
            response=result["response"],
            sources=result.get("sources", []),
            confidence=result.get("confidence", 0.0),
            processing_time=result.get("processing_time", 0.0),
            intent=result.get("intent", {}),
            cached=result.get("cached", False)
        )

        logger.info(f"✅ Query processed successfully: confidence={response.confidence:.2f}")
        return response

    except Exception as e:
        logger.error(f"❌ Chat query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {str(e)}"
        )

@router.get("/history",
           response_model=ChatHistoryResponse,
           summary="Get chat history",
           description="Retrieve user's chat conversation history")
@require_auth
@require_permission("domains.chat")
async def get_chat_history(
    page: int = 1,
    page_size: int = 20,
    user_context: Dict[str, Any] = Depends(get_user_context)
) -> ChatHistoryResponse:
    """
    Get chat history for the current user

    - **page**: Page number (1-based)
    - **page_size**: Number of conversations per page
    """
    try:
        # Placeholder implementation
        # In a real implementation, this would query the database
        conversations = [
            {
                "id": "conv_1",
                "query": "What are our sales numbers?",
                "response": "Based on the latest data...",
                "timestamp": "2025-01-01T10:00:00Z",
                "confidence": 0.85
            },
            {
                "id": "conv_2", 
                "query": "Show me marketing metrics",
                "response": "Here are the marketing insights...",
                "timestamp": "2025-01-01T09:30:00Z",
                "confidence": 0.92
            }
        ]

        return ChatHistoryResponse(
            conversations=conversations,
            total_count=len(conversations),
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"❌ Failed to get chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat history: {str(e)}"
        )

@router.delete("/history/{conversation_id}",
              summary="Delete conversation",
              description="Delete a specific conversation from history")
@require_auth
@require_permission("domains.chat")
async def delete_conversation(
    conversation_id: str,
    user_context: Dict[str, Any] = Depends(get_user_context)
):
    """
    Delete a specific conversation

    - **conversation_id**: ID of the conversation to delete
    """
    try:
        # Placeholder implementation
        logger.info(f"🗑️ Deleting conversation: {conversation_id}")

        return {"message": f"Conversation {conversation_id} deleted successfully"}

    except Exception as e:
        logger.error(f"❌ Failed to delete conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )

@router.get("/stats",
           response_model=ServiceStatsResponse,
           summary="Get service statistics",
           description="Get chat service performance statistics")
@require_auth
@require_permission("system.monitor")
async def get_service_stats() -> ServiceStatsResponse:
    """
    Get chat service statistics and health metrics

    Requires system monitoring permissions
    """
    try:
        stats = chat_service.get_service_stats()

        return ServiceStatsResponse(
            web_circuit=stats.get("web_circuit", {}),
            mcp_circuit=stats.get("mcp_circuit", {}),
            intent_cache_size=stats.get("intent_cache_size", 0),
            predictive_cache_size=stats.get("predictive_cache_size", 0),
            uptime=0.0  # Placeholder
        )

    except Exception as e:
        logger.error(f"❌ Failed to get service stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve service statistics: {str(e)}"
        )

@router.post("/feedback",
            summary="Submit feedback",
            description="Submit feedback for a chat response")
@require_auth
@require_permission("domains.chat")
async def submit_feedback(
    feedback_data: dict,
    user_context: Dict[str, Any] = Depends(get_user_context)
):
    """
    Submit feedback for a chat response
    """
    try:
        conversation_id = feedback_data.get("conversation_id")
        rating = feedback_data.get("rating", 3)
        feedback_text = feedback_data.get("feedback", "")

        if not conversation_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="conversation_id is required"
            )

        if not (1 <= rating <= 5):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="rating must be between 1 and 5"
            )

        # Store feedback (mock implementation)
        feedback_record = {
            "conversation_id": conversation_id,
            "rating": rating,
            "feedback": feedback_text,
            "user_id": user_context.get("user_id"),
            "timestamp": datetime.now().isoformat(),
            "source": "chat_interface"
        }

        logger.info(f"📝 Feedback received: {feedback_record}")

        return {
            "message": "Feedback submitted successfully",
            "feedback_id": f"feedback_{conversation_id}_{int(time.time())}",
            "status": "received"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to submit feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to submit feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )

# Health check endpoint
@router.get("/health",
           summary="Chat service health check",
           description="Check chat service health and dependencies")
async def chat_health_check():
    """Health check for chat service"""
    try:
        stats = chat_service.get_service_stats()

        # Check circuit breaker states
        web_healthy = stats["web_circuit"]["state"] != "open"
        mcp_healthy = stats["mcp_circuit"]["state"] != "open"

        overall_health = "healthy" if (web_healthy and mcp_healthy) else "degraded"

        return {
            "status": overall_health,
            "timestamp": datetime.now().isoformat(),
            "version": "v7.0",
            "services": {
                "web_search": "healthy" if web_healthy else "degraded",
                "mcp_services": "healthy" if mcp_healthy else "degraded"
            },
            "stats": stats
        }

    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

# Register router
from routers import register_router
register_router("chat", router)
