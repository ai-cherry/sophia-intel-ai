"""
Micro-Swarm API Endpoints
Complete API interface for the micro-swarm architecture with natural language processing,
scheduling, monitoring, and integration management
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.swarms.core.natural_language_interface import get_natural_language_interface
from app.swarms.core.scheduler import Priority, ScheduledTask, ScheduleType, get_scheduler
from app.swarms.core.slack_delivery import (
    DeliveryConfig,
    DeliveryFormat,
    DeliveryPriority,
    get_delivery_engine,
)
from app.swarms.core.swarm_integration import get_artemis_orchestrator, get_sophia_orchestrator

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/micro-swarms", tags=["Micro-Swarms"])

# Initialize core services
nl_interface = get_natural_language_interface()
scheduler = get_scheduler()
delivery_engine = get_delivery_engine()
sophia_orchestrator = get_sophia_orchestrator()
artemis_orchestrator = get_artemis_orchestrator()


# Pydantic Models
class NaturalLanguageRequest(BaseModel):
    """Natural language request model"""

    message: str = Field(..., description="Natural language request")
    user_id: Optional[str] = Field(None, description="User identifier")
    channel_id: Optional[str] = Field(None, description="Channel identifier")
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")


class SwarmExecutionRequest(BaseModel):
    """Direct swarm execution request"""

    content: str = Field(..., description="Task content")
    domain: str = Field("sophia", description="Domain: sophia or artemis")
    swarm_type: str = Field("auto_detect", description="Specific swarm type")
    agents: Optional[List[str]] = Field(None, description="Specific agents to use")
    coordination_pattern: str = Field("sequential", description="Coordination pattern")
    max_cost_usd: float = Field(2.0, description="Maximum cost limit")
    timeout_minutes: int = Field(10, description="Timeout in minutes")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ScheduleTaskRequest(BaseModel):
    """Schedule task request"""

    name: str = Field(..., description="Task name")
    content: str = Field(..., description="Task content")
    domain: str = Field("sophia", description="Domain: sophia or artemis")
    swarm_type: str = Field("business_intelligence", description="Swarm type")
    schedule_type: str = Field("recurring", description="Schedule type")
    interval_hours: Optional[int] = Field(24, description="Interval in hours for recurring tasks")
    cron_expression: Optional[str] = Field(None, description="Cron expression")
    priority: str = Field("normal", description="Priority: low, normal, high, critical")
    max_cost_usd: float = Field(2.0, description="Maximum cost per execution")
    timeout_minutes: int = Field(15, description="Timeout in minutes")
    business_hours_only: bool = Field(False, description="Execute only during business hours")
    weekdays_only: bool = Field(False, description="Execute only on weekdays")


class SlackDeliveryRequest(BaseModel):
    """Slack delivery configuration"""

    channel: str = Field(..., description="Slack channel")
    format: str = Field("summary", description="Delivery format")
    priority: str = Field("normal", description="Delivery priority")
    mention_users: Optional[List[str]] = Field(None, description="Users to mention")
    include_confidence: bool = Field(True, description="Include confidence scores")
    include_cost: bool = Field(False, description="Include cost information")


# API Endpoints


@router.post("/chat", summary="Natural Language Chat Interface")
async def chat_interface(request: NaturalLanguageRequest):
    """
    Process natural language requests and return AI swarm analysis

    This endpoint accepts natural language requests and automatically:
    - Parses intent and determines appropriate swarm type
    - Routes to Sophia (business) or Artemis (technical) domain
    - Executes micro-swarm with appropriate coordination
    - Returns formatted response with analysis

    Example requests:
    - "Analyze our Q4 sales performance and identify growth opportunities"
    - "Review the code quality in our main repository"
    - "What's the competitive landscape for our product?"
    """
    try:
        conversation_id = request.conversation_id or f"api_{datetime.now().timestamp()}"

        response = await nl_interface.chat(
            message=request.message,
            conversation_id=conversation_id,
            user_id=request.user_id,
            channel_id=request.channel_id,
        )

        return {
            "success": True,
            "response": response,
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Chat interface error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process request: {str(e)}",
        )


@router.post("/execute", summary="Direct Swarm Execution")
async def execute_swarm(request: SwarmExecutionRequest):
    """
    Execute a specific swarm configuration directly

    Use this endpoint when you know exactly which swarm type and configuration you want.
    Supports both Sophia (business intelligence) and Artemis (technical) domains.

    Available swarm types:
    - Sophia: business_intelligence, strategic_planning, business_health, comprehensive_analysis
    - Artemis: code_review, architecture_review, security_assessment, technical_strategy, full_technical
    """
    try:
        # Select orchestrator based on domain
        if request.domain.lower() == "artemis":
            orchestrator = artemis_orchestrator
        else:
            orchestrator = sophia_orchestrator

        # Execute swarm
        result = await orchestrator.execute_swarm(
            content=request.content, swarm_type=request.swarm_type, context=request.context or {}
        )

        return {
            "success": result.success,
            "content": result.content,
            "confidence": result.confidence,
            "cost_usd": result.cost,
            "execution_time_ms": result.execution_time_ms,
            "metadata": result.metadata,
            "domain": request.domain,
            "swarm_type": request.swarm_type,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Swarm execution error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute swarm: {str(e)}",
        )


@router.post("/schedule", summary="Schedule Recurring Analysis")
async def schedule_task(request: ScheduleTaskRequest):
    """
    Schedule recurring swarm analysis

    Create automated analysis that runs on a schedule. Perfect for:
    - Daily business intelligence reports
    - Weekly code quality reviews
    - Monthly competitive analysis
    - Quarterly strategic planning
    """
    try:
        # Convert request to ScheduledTask
        task = ScheduledTask(
            task_id=f"api_scheduled_{int(datetime.now().timestamp())}",
            name=request.name,
            description=f"Scheduled {request.swarm_type} analysis",
            swarm_type=f"{request.domain}.{request.swarm_type}",
            task_content=request.content,
            schedule_type=ScheduleType(request.schedule_type),
            interval_minutes=request.interval_hours * 60 if request.interval_hours else None,
            cron_expression=request.cron_expression,
            priority=Priority[request.priority.upper()],
            max_cost_usd=request.max_cost_usd,
            timeout_minutes=request.timeout_minutes,
            business_hours_only=request.business_hours_only,
            weekdays_only=request.weekdays_only,
            created_by="api",
        )

        # Schedule the task
        task_id = scheduler.schedule_task(task)

        return {
            "success": True,
            "task_id": task_id,
            "message": f"Successfully scheduled recurring {request.swarm_type} analysis",
            "next_execution": task.next_execution.isoformat() if task.next_execution else None,
            "schedule_details": {
                "type": request.schedule_type,
                "interval_hours": request.interval_hours,
                "priority": request.priority,
                "max_cost_usd": request.max_cost_usd,
            },
        }

    except Exception as e:
        logger.error(f"Schedule task error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule task: {str(e)}",
        )


@router.get("/schedule/{task_id}/status", summary="Get Scheduled Task Status")
async def get_task_status(task_id: str):
    """Get status of a scheduled task"""
    try:
        status = scheduler.get_task_status(task_id)

        if not status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found"
            )

        return {"success": True, "task_status": status}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get task status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}",
        )


@router.delete("/schedule/{task_id}", summary="Cancel Scheduled Task")
async def cancel_task(task_id: str):
    """Cancel a scheduled task"""
    try:
        success = scheduler.unschedule_task(task_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found"
            )

        return {"success": True, "message": f"Task {task_id} has been cancelled"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel task error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}",
        )


@router.post("/deliver-to-slack", summary="Deliver Results to Slack")
async def deliver_to_slack(execution_result: Dict[str, Any], delivery_config: SlackDeliveryRequest):
    """
    Deliver swarm results to Slack with rich formatting

    Takes execution results and delivers them to specified Slack channels
    with configurable formatting and notification levels.
    """
    try:
        # Create delivery configuration
        config = DeliveryConfig(
            channel=delivery_config.channel,
            format=DeliveryFormat(delivery_config.format),
            priority=DeliveryPriority(delivery_config.priority),
            mention_users=delivery_config.mention_users or [],
            include_confidence=delivery_config.include_confidence,
            include_cost=delivery_config.include_cost,
        )

        # Mock SwarmResult from execution_result (in real implementation, would have actual SwarmResult)
        from app.swarms.core.micro_swarm_base import SwarmResult

        swarm_result = SwarmResult(
            success=execution_result.get("success", True),
            final_output=execution_result.get("content", ""),
            confidence=execution_result.get("confidence", 0.8),
            reasoning_chain=[],
            agent_contributions={},
            consensus_achieved=execution_result.get("consensus_achieved", True),
            iterations_used=execution_result.get("iterations_used", 1),
            total_cost=execution_result.get("cost_usd", 0.0),
            execution_time_ms=execution_result.get("execution_time_ms", 0.0),
        )

        # Deliver to Slack
        delivery_result = await delivery_engine.deliver_result(
            swarm_result=swarm_result,
            config=config,
            context={
                "swarm_name": execution_result.get("swarm_type", "Micro-Swarm"),
                "task_description": execution_result.get("task_description", "Analysis"),
            },
        )

        return {
            "success": delivery_result.success,
            "channel": delivery_result.channel,
            "message_timestamp": delivery_result.message_ts,
            "format_used": delivery_result.format_used.value,
            "character_count": delivery_result.character_count,
            "error_message": delivery_result.error_message,
        }

    except Exception as e:
        logger.error(f"Slack delivery error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deliver to Slack: {str(e)}",
        )


@router.get("/status", summary="System Status Overview")
async def get_system_status():
    """
    Get comprehensive status of the micro-swarm system

    Returns status information for all major components:
    - Natural language interface
    - Scheduler
    - Delivery engine
    - Orchestrators
    - Active swarms
    """
    try:
        # Get status from all major components
        scheduler_status = scheduler.get_scheduler_status()
        delivery_stats = delivery_engine.get_delivery_statistics()
        nl_stats = nl_interface.get_interface_statistics()
        sophia_status = sophia_orchestrator.get_status()
        artemis_status = artemis_orchestrator.get_status()

        return {
            "system": {
                "status": "operational",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
            },
            "scheduler": scheduler_status,
            "delivery_engine": delivery_stats,
            "natural_language_interface": nl_stats,
            "orchestrators": {"sophia": sophia_status, "artemis": artemis_status},
            "integration_status": {
                "sophia_integrations": sophia_orchestrator.get_integration_status(),
                "artemis_integrations": artemis_orchestrator.get_integration_status(),
            },
        }

    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system status: {str(e)}",
        )


@router.get("/conversations/{conversation_id}", summary="Get Conversation Summary")
async def get_conversation(conversation_id: str):
    """Get summary of a conversation with the natural language interface"""
    try:
        summary = nl_interface.get_conversation_summary(conversation_id)

        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found",
            )

        return {"success": True, "conversation_summary": summary}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation: {str(e)}",
        )


@router.delete("/conversations/{conversation_id}", summary="Clear Conversation")
async def clear_conversation(conversation_id: str):
    """Clear a conversation history"""
    try:
        success = nl_interface.clear_conversation(conversation_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found",
            )

        return {"success": True, "message": f"Conversation {conversation_id} cleared"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clear conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear conversation: {str(e)}",
        )


@router.get("/swarm-types", summary="List Available Swarm Types")
async def list_swarm_types():
    """List all available swarm types and their descriptions"""
    return {
        "sophia_swarms": {
            "business_intelligence": {
                "description": "Comprehensive business analysis with market intelligence and competitive insights",
                "agents": ["Hermes", "Athena", "Minerva"],
                "coordination": "sequential",
                "typical_use_cases": [
                    "Market analysis",
                    "Competitive intelligence",
                    "Customer insights",
                    "Business performance analysis",
                ],
            },
            "strategic_planning": {
                "description": "Strategic planning and decision-making with debate-driven consensus",
                "agents": ["Athena", "Odin", "Minerva"],
                "coordination": "debate",
                "typical_use_cases": [
                    "Strategic roadmap planning",
                    "Investment decisions",
                    "Business transformation",
                    "Risk assessment",
                ],
            },
            "business_health": {
                "description": "Business health diagnostics and operational optimization",
                "agents": ["Asclepius", "Hermes", "Minerva"],
                "coordination": "hierarchical",
                "typical_use_cases": [
                    "Organizational health assessment",
                    "Process optimization",
                    "Performance diagnostics",
                    "Operational efficiency",
                ],
            },
            "comprehensive_analysis": {
                "description": "Full-spectrum analysis using all mythology agents",
                "agents": ["Hermes", "Asclepius", "Athena", "Odin", "Minerva"],
                "coordination": "consensus",
                "typical_use_cases": [
                    "Critical business decisions",
                    "Annual planning",
                    "Major investment analysis",
                    "Complete business review",
                ],
            },
        },
        "artemis_swarms": {
            "code_review": {
                "description": "Comprehensive code quality and security analysis",
                "agents": ["Code Analyst", "Quality Engineer", "Security Engineer"],
                "coordination": "parallel",
                "typical_use_cases": [
                    "Pull request review",
                    "Code quality assessment",
                    "Security vulnerability scanning",
                    "Technical debt analysis",
                ],
            },
            "architecture_review": {
                "description": "System architecture and design evaluation",
                "agents": ["Technical Architect", "Quality Engineer", "Security Engineer"],
                "coordination": "sequential",
                "typical_use_cases": [
                    "Architecture design review",
                    "Scalability assessment",
                    "System design validation",
                    "Technology strategy",
                ],
            },
            "security_assessment": {
                "description": "Security-focused analysis and vulnerability assessment",
                "agents": ["Security Engineer", "Code Analyst", "DevOps Engineer"],
                "coordination": "hierarchical",
                "typical_use_cases": [
                    "Security audit",
                    "Penetration testing analysis",
                    "Compliance validation",
                    "Threat modeling",
                ],
            },
            "technical_strategy": {
                "description": "Technical strategy and roadmap planning",
                "agents": ["Technical Architect", "DevOps Engineer", "Quality Engineer"],
                "coordination": "debate",
                "typical_use_cases": [
                    "Technology roadmap",
                    "Platform strategy",
                    "Technical debt prioritization",
                    "Infrastructure planning",
                ],
            },
            "full_technical": {
                "description": "Comprehensive technical analysis with all agents",
                "agents": [
                    "Technical Architect",
                    "Code Analyst",
                    "Quality Engineer",
                    "DevOps Engineer",
                    "Security Engineer",
                ],
                "coordination": "consensus",
                "typical_use_cases": [
                    "Major system overhaul",
                    "Complete technical audit",
                    "Critical deployment review",
                    "Technical due diligence",
                ],
            },
        },
    }


@router.post("/start-scheduler", summary="Start the Task Scheduler")
async def start_scheduler(background_tasks: BackgroundTasks):
    """Start the task scheduler in the background"""
    try:
        if not scheduler.running:
            background_tasks.add_task(scheduler.start)
            return {"success": True, "message": "Scheduler started successfully"}
        else:
            return {"success": True, "message": "Scheduler is already running"}
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start scheduler: {str(e)}",
        )


@router.post("/stop-scheduler", summary="Stop the Task Scheduler")
async def stop_scheduler():
    """Stop the task scheduler"""
    try:
        await scheduler.stop()
        return {"success": True, "message": "Scheduler stopped successfully"}
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop scheduler: {str(e)}",
        )


# Health check endpoint
@router.get("/health", summary="Health Check")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "components": {
            "scheduler": scheduler.running,
            "natural_language_interface": len(nl_interface.conversations),
            "delivery_engine": len(delivery_engine.delivery_history),
            "orchestrators": {
                "sophia": len(sophia_orchestrator._active_tasks),
                "artemis": len(artemis_orchestrator._active_tasks),
            },
        },
    }


# Include router in main application
def get_micro_swarm_router() -> APIRouter:
    """Get the micro-swarm API router"""
    return router
