"""
SOPHIA Feedback MCP Server
FastAPI server for collecting and managing user and agent feedback.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import asyncio

# Import Sophia components
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sophia.core.feedback_master import SOPHIAFeedbackMaster, FeedbackRecord, FeedbackSummary

logger = logging.getLogger(__name__)

# Pydantic models for request/response
class UserFeedbackRequest(BaseModel):
    """Request model for user feedback."""
    task_id: str = Field(..., description="Unique task identifier")
    rating: int = Field(..., ge=1, le=5, description="User rating (1-5)")
    comments: Optional[str] = Field(None, description="Optional user comments")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class AgentFeedbackRequest(BaseModel):
    """Request model for agent feedback."""
    task_id: str = Field(..., description="Unique task identifier")
    outcome: str = Field(..., description="Task outcome (success, failure, partial, etc.)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class FeedbackResponse(BaseModel):
    """Response model for feedback operations."""
    feedback_id: int
    task_id: str
    source: str
    status: str
    message: str

class FeedbackQuery(BaseModel):
    """Query parameters for feedback retrieval."""
    task_id: Optional[str] = None
    source: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)

class FeedbackSummaryResponse(BaseModel):
    """Response model for feedback summary."""
    total_feedback: int
    average_rating: float
    rating_distribution: Dict[int, int]
    common_issues: List[str]
    improvement_suggestions: List[str]
    time_period: str

# Create router
router = APIRouter()

# Global feedback master instance
feedback_master = None

async def get_feedback_master() -> SOPHIAFeedbackMaster:
    """Dependency to get feedback master instance."""
    global feedback_master
    if feedback_master is None:
        feedback_master = SOPHIAFeedbackMaster()
    return feedback_master

@router.post("/feedback/user", response_model=FeedbackResponse)
async def submit_user_feedback(
    request: UserFeedbackRequest,
    master: SOPHIAFeedbackMaster = Depends(get_feedback_master)
):
    """
    Submit user feedback for a task.
    
    This endpoint allows users to provide ratings and comments for completed tasks.
    """
    try:
        result = await master.record_user_feedback(
            task_id=request.task_id,
            rating=request.rating,
            comments=request.comments,
            metadata=request.metadata
        )
        
        return FeedbackResponse(
            feedback_id=result["feedback_id"],
            task_id=result["task_id"],
            source=result["source"],
            status="success",
            message="User feedback recorded successfully"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to record user feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/feedback/agent", response_model=FeedbackResponse)
async def submit_agent_feedback(
    request: AgentFeedbackRequest,
    master: SOPHIAFeedbackMaster = Depends(get_feedback_master)
):
    """
    Submit agent feedback for a task outcome.
    
    This endpoint allows the system to record task execution outcomes and performance data.
    """
    try:
        result = await master.record_agent_feedback(
            task_id=request.task_id,
            outcome=request.outcome,
            metadata=request.metadata
        )
        
        return FeedbackResponse(
            feedback_id=result["feedback_id"],
            task_id=result["task_id"],
            source=result["source"],
            status="success",
            message="Agent feedback recorded successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to record agent feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/feedback", response_model=List[Dict[str, Any]])
async def get_feedback(
    task_id: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    master: SOPHIAFeedbackMaster = Depends(get_feedback_master)
):
    """
    Retrieve feedback records with optional filtering.
    
    Query parameters:
    - task_id: Filter by specific task ID
    - source: Filter by feedback source (user, agent, system)
    - limit: Maximum number of records to return (1-1000)
    - offset: Number of records to skip
    """
    try:
        if limit > 1000:
            raise HTTPException(status_code=400, detail="Limit cannot exceed 1000")
        
        feedback_records = await master.get_feedback(
            task_id=task_id,
            source=source,
            limit=limit,
            offset=offset
        )
        
        # Convert to dict format for JSON response
        result = []
        for record in feedback_records:
            result.append({
                "id": record.id,
                "task_id": record.task_id,
                "source": record.source,
                "rating": record.rating,
                "comments": record.comments,
                "outcome": record.outcome,
                "metadata": record.metadata,
                "timestamp": record.timestamp.isoformat() if record.timestamp else None
            })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/feedback/summary", response_model=FeedbackSummaryResponse)
async def get_feedback_summary(
    days: int = 30,
    source: Optional[str] = None,
    master: SOPHIAFeedbackMaster = Depends(get_feedback_master)
):
    """
    Get aggregated feedback summary for a time period.
    
    Query parameters:
    - days: Number of days to analyze (default: 30)
    - source: Filter by feedback source (user, agent, system)
    """
    try:
        if days > 365:
            raise HTTPException(status_code=400, detail="Days cannot exceed 365")
        
        summary = await master.aggregate_feedback(days=days, source=source)
        
        return FeedbackSummaryResponse(
            total_feedback=summary.total_feedback,
            average_rating=summary.average_rating,
            rating_distribution=summary.rating_distribution,
            common_issues=summary.common_issues,
            improvement_suggestions=summary.improvement_suggestions,
            time_period=summary.time_period
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get feedback summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/feedback/task/{task_id}")
async def get_task_feedback(
    task_id: str,
    master: SOPHIAFeedbackMaster = Depends(get_feedback_master)
):
    """
    Get feedback summary for a specific task.
    
    Returns all feedback (user and agent) for the specified task ID.
    """
    try:
        summary = await master.get_task_feedback_summary(task_id)
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get task feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/feedback/export")
async def export_feedback(
    format: str = "json",
    days: int = 30,
    master: SOPHIAFeedbackMaster = Depends(get_feedback_master)
):
    """
    Export feedback data for analysis.
    
    Query parameters:
    - format: Export format (json, csv) - currently only json supported
    - days: Number of days to export (default: 30)
    """
    try:
        if format not in ["json"]:
            raise HTTPException(status_code=400, detail="Only JSON format is currently supported")
        
        if days > 365:
            raise HTTPException(status_code=400, detail="Days cannot exceed 365")
        
        export_data = await master.export_feedback_data(format=format, days=days)
        return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/feedback/health")
async def feedback_health_check(
    master: SOPHIAFeedbackMaster = Depends(get_feedback_master)
):
    """
    Health check endpoint for feedback service.
    
    Returns the status of the feedback system and database connectivity.
    """
    try:
        # Test database connectivity by getting a small sample
        test_feedback = await master.get_feedback(limit=1)
        
        return {
            "status": "healthy",
            "service": "feedback",
            "database_connected": True,
            "total_feedback_available": len(test_feedback) > 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Feedback health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "feedback",
            "database_connected": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/feedback/stats")
async def get_feedback_stats(
    master: SOPHIAFeedbackMaster = Depends(get_feedback_master)
):
    """
    Get basic feedback statistics.
    
    Returns quick stats about feedback volume and ratings.
    """
    try:
        # Get recent feedback summary
        summary = await master.aggregate_feedback(days=7)
        
        # Get total feedback count (approximate)
        all_feedback = await master.get_feedback(limit=1)
        
        return {
            "last_7_days": {
                "total_feedback": summary.total_feedback,
                "average_rating": summary.average_rating,
                "rating_distribution": summary.rating_distribution
            },
            "service_status": "operational",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get feedback stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Batch operations
@router.post("/feedback/batch/user")
async def submit_batch_user_feedback(
    requests: List[UserFeedbackRequest],
    master: SOPHIAFeedbackMaster = Depends(get_feedback_master)
):
    """
    Submit multiple user feedback records in batch.
    
    Useful for bulk feedback submission from surveys or batch processing.
    """
    try:
        if len(requests) > 100:
            raise HTTPException(status_code=400, detail="Batch size cannot exceed 100")
        
        results = []
        errors = []
        
        for i, request in enumerate(requests):
            try:
                result = await master.record_user_feedback(
                    task_id=request.task_id,
                    rating=request.rating,
                    comments=request.comments,
                    metadata=request.metadata
                )
                results.append(result)
            except Exception as e:
                errors.append({
                    "index": i,
                    "task_id": request.task_id,
                    "error": str(e)
                })
        
        return {
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process batch user feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/feedback/batch/agent")
async def submit_batch_agent_feedback(
    requests: List[AgentFeedbackRequest],
    master: SOPHIAFeedbackMaster = Depends(get_feedback_master)
):
    """
    Submit multiple agent feedback records in batch.
    
    Useful for bulk outcome reporting from batch processing or system monitoring.
    """
    try:
        if len(requests) > 100:
            raise HTTPException(status_code=400, detail="Batch size cannot exceed 100")
        
        results = []
        errors = []
        
        for i, request in enumerate(requests):
            try:
                result = await master.record_agent_feedback(
                    task_id=request.task_id,
                    outcome=request.outcome,
                    metadata=request.metadata
                )
                results.append(result)
            except Exception as e:
                errors.append({
                    "index": i,
                    "task_id": request.task_id,
                    "error": str(e)
                })
        
        return {
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process batch agent feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Analytics endpoints
@router.get("/feedback/analytics/trends")
async def get_feedback_trends(
    days: int = 30,
    master: SOPHIAFeedbackMaster = Depends(get_feedback_master)
):
    """
    Get feedback trends over time.
    
    Analyzes feedback patterns and provides trend information.
    """
    try:
        if days > 365:
            raise HTTPException(status_code=400, detail="Days cannot exceed 365")
        
        # Get current period summary
        current_summary = await master.aggregate_feedback(days=days)
        
        # Get previous period for comparison (simplified)
        previous_summary = await master.aggregate_feedback(days=days*2)
        
        # Calculate trends (simplified implementation)
        rating_trend = "stable"
        volume_trend = "stable"
        
        if current_summary.total_feedback > 0 and previous_summary.total_feedback > 0:
            rating_change = current_summary.average_rating - previous_summary.average_rating
            volume_change = current_summary.total_feedback - (previous_summary.total_feedback - current_summary.total_feedback)
            
            if rating_change > 0.2:
                rating_trend = "improving"
            elif rating_change < -0.2:
                rating_trend = "declining"
            
            if volume_change > 0:
                volume_trend = "increasing"
            elif volume_change < 0:
                volume_trend = "decreasing"
        
        return {
            "period": f"Last {days} days",
            "current_summary": {
                "total_feedback": current_summary.total_feedback,
                "average_rating": current_summary.average_rating,
                "rating_distribution": current_summary.rating_distribution
            },
            "trends": {
                "rating_trend": rating_trend,
                "volume_trend": volume_trend
            },
            "insights": current_summary.improvement_suggestions,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get feedback trends: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

