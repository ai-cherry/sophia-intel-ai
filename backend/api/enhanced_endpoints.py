"""
Enhanced API endpoints for SOPHIA Intel with comprehensive UX optimization
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Dict, Any, List, Optional, AsyncGenerator
import asyncio
import json
import time
from datetime import datetime

from backend.domains.chat.service import ChatService
from backend.domains.chat.models import ChatRequest, ChatResponse
from backend.domains.intelligence.sophia_awareness import SophiaAwarenessSystem
from backend.domains.persona.service import PersonaService
from backend.domains.mcp.service import MCPService
from backend.services.infrastructure_automation import InfrastructureAutomationService
from backend.monitoring.observability_service import ObservabilityService
from backend.middleware.auth import get_current_user
from backend.config.settings import get_settings

router = APIRouter(prefix="/api/v1", tags=["Enhanced SOPHIA Intel"])

# Initialize services
settings = get_settings()
chat_service = ChatService(settings)
sophia_awareness = SophiaAwarenessSystem(settings)
persona_service = PersonaService(settings)
mcp_service = MCPService(settings)
infra_service = InfrastructureAutomationService(settings)
observability = ObservabilityService(settings)


@router.get("/sophia/status", summary="SOPHIA System Status")
async def get_sophia_status():
    """Get comprehensive SOPHIA system status with all capabilities"""
    try:
        # Get system awareness
        capabilities = await sophia_awareness.get_capability_summary()
        
        # Get infrastructure status
        infra_status = await infra_service.get_system_health()
        
        # Get MCP server status
        mcp_status = await mcp_service.get_health_status()
        
        # Get observability metrics
        metrics = await observability.get_system_metrics()
        
        return {
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "sophia_awareness": capabilities,
            "infrastructure": infra_status,
            "mcp_servers": mcp_status,
            "performance_metrics": metrics,
            "version": "1.0.0",
            "uptime": time.time() - settings.startup_time if hasattr(settings, 'startup_time') else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"System status check failed: {str(e)}")


@router.post("/sophia/chat/enhanced", summary="Enhanced Chat with Full SOPHIA Capabilities")
async def enhanced_chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """Enhanced chat endpoint with full SOPHIA capabilities and UX optimization"""
    try:
        # Start performance tracking
        start_time = time.time()
        
        # Add user context if authenticated
        if current_user:
            request.user_id = current_user.get("user_id", request.user_id)
        
        # Process chat request with enhanced capabilities
        response = await chat_service.process_chat_request(request)
        
        # Add SOPHIA awareness context if requested
        if request.message.lower().startswith(("what can you", "your capabilities", "what are you")):
            awareness_context = await sophia_awareness.get_capability_summary()
            response.sophia_context = awareness_context
        
        # Add persona enhancement if voice is requested
        if request.voice:
            persona_enhancement = await persona_service.enhance_response_with_persona(
                response.message, request.user_id
            )
            response.persona_enhancement = persona_enhancement
        
        # Track performance metrics
        response_time = time.time() - start_time
        background_tasks.add_task(
            observability.track_request,
            endpoint="/sophia/chat/enhanced",
            response_time=response_time,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        return response
        
    except Exception as e:
        await observability.track_error(
            endpoint="/sophia/chat/enhanced",
            error=str(e),
            user_id=request.user_id,
            session_id=request.session_id
        )
        raise HTTPException(status_code=500, detail=f"Enhanced chat failed: {str(e)}")


@router.post("/sophia/chat/stream", summary="Streaming Chat with Real-time Response")
async def stream_chat(request: ChatRequest):
    """Streaming chat endpoint with real-time response generation"""
    try:
        async def generate_stream():
            """Generate streaming response chunks"""
            try:
                async for chunk in chat_service.stream_chat_response(request):
                    # Format chunk for SSE
                    chunk_data = {
                        "type": "chunk",
                        "content": chunk.content if hasattr(chunk, 'content') else str(chunk),
                        "timestamp": datetime.utcnow().isoformat(),
                        "session_id": request.session_id
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                
                # Send completion signal
                completion_data = {
                    "type": "complete",
                    "session_id": request.session_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                yield f"data: {json.dumps(completion_data)}\n\n"
                
            except Exception as e:
                error_data = {
                    "type": "error",
                    "error": str(e),
                    "session_id": request.session_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming chat failed: {str(e)}")


@router.get("/sophia/infrastructure/dashboard", summary="Infrastructure Dashboard Data")
async def get_infrastructure_dashboard():
    """Get comprehensive infrastructure dashboard data"""
    try:
        # Get Lambda Labs server status
        lambda_status = await infra_service.get_lambda_labs_status()
        
        # Get service health across all platforms
        service_health = await infra_service.get_service_health_summary()
        
        # Get performance metrics
        performance_metrics = await observability.get_performance_dashboard_data()
        
        # Get recent operations
        recent_operations = await infra_service.get_recent_operations(limit=10)
        
        return {
            "lambda_labs": lambda_status,
            "services": service_health,
            "performance": performance_metrics,
            "recent_operations": recent_operations,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard data retrieval failed: {str(e)}")


@router.post("/sophia/infrastructure/action", summary="Execute Infrastructure Action")
async def execute_infrastructure_action(
    action_request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """Execute infrastructure actions with SOPHIA's supreme authority"""
    try:
        # Verify user has appropriate permissions (SOPHIA has supreme authority)
        if not current_user or current_user.get("role") not in ["admin", "sophia"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions for infrastructure actions")
        
        action_type = action_request.get("action_type")
        target = action_request.get("target")
        parameters = action_request.get("parameters", {})
        
        # Execute action based on type
        if action_type == "lambda_labs":
            result = await infra_service.execute_lambda_labs_action(target, parameters)
        elif action_type == "service_management":
            result = await infra_service.execute_service_action(target, parameters)
        elif action_type == "database_operation":
            result = await infra_service.execute_database_operation(target, parameters)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action type: {action_type}")
        
        # Track the action
        background_tasks.add_task(
            observability.track_infrastructure_action,
            action_type=action_type,
            target=target,
            user_id=current_user.get("user_id"),
            result=result
        )
        
        return {
            "success": True,
            "action_type": action_type,
            "target": target,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Infrastructure action failed: {str(e)}")


@router.get("/sophia/persona/profiles", summary="Get Available Persona Profiles")
async def get_persona_profiles(user_id: Optional[str] = None):
    """Get available persona profiles for enhanced interaction"""
    try:
        profiles = await persona_service.get_available_personas(user_id)
        return {
            "personas": profiles,
            "default_persona": await persona_service.get_default_persona(),
            "voice_options": await persona_service.get_voice_options()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Persona profiles retrieval failed: {str(e)}")


@router.post("/sophia/persona/customize", summary="Customize Persona Settings")
async def customize_persona(
    customization_request: Dict[str, Any],
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """Customize persona settings for enhanced user experience"""
    try:
        user_id = current_user.get("user_id") if current_user else customization_request.get("user_id")
        
        result = await persona_service.customize_persona(
            user_id=user_id,
            persona_settings=customization_request
        )
        
        return {
            "success": True,
            "persona_settings": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Persona customization failed: {str(e)}")


@router.get("/sophia/analytics/dashboard", summary="Analytics Dashboard")
async def get_analytics_dashboard(
    timeframe: str = "24h",
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """Get comprehensive analytics dashboard data"""
    try:
        # Get usage analytics
        usage_analytics = await observability.get_usage_analytics(timeframe)
        
        # Get performance analytics
        performance_analytics = await observability.get_performance_analytics(timeframe)
        
        # Get user behavior analytics
        user_analytics = await observability.get_user_behavior_analytics(timeframe)
        
        # Get system health trends
        health_trends = await observability.get_health_trends(timeframe)
        
        return {
            "usage": usage_analytics,
            "performance": performance_analytics,
            "user_behavior": user_analytics,
            "health_trends": health_trends,
            "timeframe": timeframe,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics dashboard failed: {str(e)}")


@router.post("/sophia/voice/generate", summary="Generate Voice Response")
async def generate_voice_response(
    voice_request: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """Generate voice response using ElevenLabs integration"""
    try:
        text = voice_request.get("text")
        voice_settings = voice_request.get("voice_settings", {})
        user_id = voice_request.get("user_id")
        
        # Generate voice response
        voice_response = await persona_service.generate_voice_response(
            text=text,
            voice_settings=voice_settings,
            user_id=user_id
        )
        
        # Track voice generation
        background_tasks.add_task(
            observability.track_voice_generation,
            user_id=user_id,
            text_length=len(text),
            voice_settings=voice_settings
        )
        
        return voice_response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice generation failed: {str(e)}")


@router.get("/sophia/health/comprehensive", summary="Comprehensive Health Check")
async def comprehensive_health_check():
    """Comprehensive health check for all SOPHIA systems"""
    try:
        health_status = {
            "overall_status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        # Check chat service
        try:
            chat_health = await chat_service.health_check()
            health_status["components"]["chat_service"] = {"status": "healthy", "details": chat_health}
        except Exception as e:
            health_status["components"]["chat_service"] = {"status": "unhealthy", "error": str(e)}
            health_status["overall_status"] = "degraded"
        
        # Check infrastructure services
        try:
            infra_health = await infra_service.health_check()
            health_status["components"]["infrastructure"] = {"status": "healthy", "details": infra_health}
        except Exception as e:
            health_status["components"]["infrastructure"] = {"status": "unhealthy", "error": str(e)}
            health_status["overall_status"] = "degraded"
        
        # Check MCP services
        try:
            mcp_health = await mcp_service.get_health_status()
            health_status["components"]["mcp_services"] = {"status": "healthy", "details": mcp_health}
        except Exception as e:
            health_status["components"]["mcp_services"] = {"status": "unhealthy", "error": str(e)}
            health_status["overall_status"] = "degraded"
        
        # Check observability
        try:
            obs_health = await observability.health_check()
            health_status["components"]["observability"] = {"status": "healthy", "details": obs_health}
        except Exception as e:
            health_status["components"]["observability"] = {"status": "unhealthy", "error": str(e)}
            health_status["overall_status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        return {
            "overall_status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.websocket("/sophia/ws/chat")
async def websocket_chat_endpoint(websocket):
    """WebSocket endpoint for real-time chat interaction"""
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Create chat request
            chat_request = ChatRequest(**message_data)
            
            # Process chat request
            if chat_request.stream:
                # Stream response
                async for chunk in chat_service.stream_chat_response(chat_request):
                    await websocket.send_text(json.dumps({
                        "type": "chunk",
                        "content": chunk.content if hasattr(chunk, 'content') else str(chunk),
                        "session_id": chat_request.session_id
                    }))
                
                # Send completion
                await websocket.send_text(json.dumps({
                    "type": "complete",
                    "session_id": chat_request.session_id
                }))
            else:
                # Regular response
                response = await chat_service.process_chat_request(chat_request)
                await websocket.send_text(json.dumps({
                    "type": "response",
                    "message": response.message,
                    "session_id": response.session_id,
                    "performance_metrics": response.performance_metrics
                }))
                
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "error": str(e)
        }))
    finally:
        await websocket.close()


# Add router to main application
def get_enhanced_router():
    """Get the enhanced API router"""
    return router

