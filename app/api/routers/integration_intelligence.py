"""
Integration Intelligence API Router - Simplified Version
Connects the new UI to domain teams and Agent Factory for comprehensive business intelligence.

Provides endpoints for:
- Domain team analytics and insights
- OKR tracking and updates (revenue per employee)
- Cross-platform correlation data
- WebSocket connections for real-time updates
- Integration status monitoring
- Agent Factory team management
- Executive dashboard data
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/integration-intelligence", tags=["integration-intelligence"])

# ==============================================================================
# REQUEST/RESPONSE MODELS
# ==============================================================================


class DomainTeamRequest(BaseModel):
    """Request model for creating domain teams"""

    team_type: str = Field(..., description="Type of domain team to create")
    custom_config: Optional[dict[str, Any]] = Field(
        default=None, description="Custom team configuration"
    )


class AnalysisRequest(BaseModel):
    """Request model for domain intelligence analysis"""

    team_id: str = Field(..., min_length=1, description="Domain team identifier")
    platform_data: dict[str, Any] = Field(..., description="Platform data for analysis")
    analysis_type: str = Field(default="comprehensive", description="Type of analysis to perform")

    @validator("analysis_type")
    def validate_analysis_type(cls, v: str) -> str:
        allowed_types = [
            "comprehensive",
            "okr_analysis",
            "customer_journey",
            "productivity",
            "knowledge_analysis",
        ]
        if v not in allowed_types:
            raise ValueError(f"Analysis type must be one of: {', '.join(allowed_types)}")
        return v


class CorrelationRequest(BaseModel):
    """Request model for cross-platform correlation"""

    correlation_type: str = Field(..., description="Type of entity correlation")
    platform_data: dict[str, Any] = Field(..., description="Multi-platform data")

    @validator("correlation_type")
    def validate_correlation_type(cls, v: str) -> str:
        valid_types = [
            "person_matching",
            "project_alignment",
            "revenue_attribution",
            "customer_journey",
            "knowledge_linkage",
        ]
        if v not in valid_types:
            raise ValueError(f"Correlation type must be one of: {', '.join(valid_types)}")
        return v


class OKRUpdateRequest(BaseModel):
    """Request model for OKR metric updates"""

    total_revenue: Optional[float] = Field(default=None, ge=0, description="Total revenue")
    employee_count: Optional[int] = Field(default=None, ge=1, description="Number of employees")
    target_revenue_per_employee: Optional[float] = Field(
        default=None, ge=0, description="Target revenue per employee"
    )
    contributing_factors: Optional[dict[str, float]] = Field(
        default=None, description="Contributing factors to revenue"
    )


class WebSocketMessage(BaseModel):
    """WebSocket message model"""

    event: str = Field(..., description="Event type")
    data: dict[str, Any] = Field(..., description="Event data")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class DashboardDataResponse(BaseModel):
    """Executive dashboard data response"""

    okr_metrics: dict[str, Any] = Field(..., description="OKR metrics and progress")
    team_analytics: list[dict[str, Any]] = Field(..., description="Domain team analytics")
    correlation_insights: list[dict[str, Any]] = Field(
        ..., description="Cross-platform correlations"
    )
    real_time_status: dict[str, Any] = Field(..., description="Real-time system status")
    performance_metrics: dict[str, Any] = Field(..., description="System performance metrics")


class IntegrationStatusResponse(BaseModel):
    """Integration status response"""

    active_teams: list[dict[str, Any]] = Field(..., description="Active domain teams")
    platform_connections: dict[str, Any] = Field(..., description="Platform connection status")
    recent_analyses: list[dict[str, Any]] = Field(..., description="Recent analysis results")
    websocket_connections: int = Field(..., description="Number of active WebSocket connections")
    system_health: dict[str, Any] = Field(..., description="Overall system health")


# ==============================================================================
# WEBSOCKET CONNECTION MANAGER
# ==============================================================================


class IntegrationWebSocketManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: set[WebSocket] = set()
        self.connection_metadata: dict[WebSocket, dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, client_info: Optional[dict[str, Any]] = None):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_metadata[websocket] = client_info or {}
        logger.info(f"WebSocket connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.discard(websocket)
        self.connection_metadata.pop(websocket, None)
        logger.info(f"WebSocket disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast_message(self, message: dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return

        disconnected = set()
        message_str = json.dumps(message)

        for websocket in self.active_connections:
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
                disconnected.add(websocket)

        # Remove disconnected WebSockets
        for ws in disconnected:
            self.disconnect(ws)

    async def send_to_specific(self, websocket: WebSocket, message: dict[str, Any]):
        """Send message to specific WebSocket connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending to specific WebSocket: {e}")
            self.disconnect(websocket)


# Global WebSocket manager
ws_manager = IntegrationWebSocketManager()

# ==============================================================================
# DOMAIN TEAM MANAGEMENT ENDPOINTS
# ==============================================================================


@router.post("/domain-teams/create")
async def create_domain_team(request: DomainTeamRequest):
    """Create a new domain-specialized integration team"""
    try:
        # For now, return a mock response since the full system isn't available
        team_id = f"team_{uuid4().hex[:8]}"

        # Broadcast team creation event
        await ws_manager.broadcast_message(
            {
                "event": "domain_team_created",
                "data": {
                    "team_id": team_id,
                    "team_type": request.team_type,
                    "timestamp": datetime.now().isoformat(),
                },
            }
        )

        return {
            "success": True,
            "team_id": team_id,
            "team_type": request.team_type,
            "message": f"Domain team {request.team_type} created successfully (simulation mode)",
            "mode": "simulation",
            "endpoints": {
                "analyze": f"/api/integration-intelligence/teams/{team_id}/analyze",
                "status": f"/api/integration-intelligence/teams/{team_id}/status",
            },
        }

    except Exception as e:
        logger.error(f"Failed to create domain team: {e}")
        raise HTTPException(status_code=500, detail=f"Team creation failed: {str(e)}")


@router.get("/domain-teams")
async def list_domain_teams():
    """List all active domain teams"""
    # Return simulation data
    return {
        "success": True,
        "teams": [
            {
                "id": "team_bi_001",
                "type": "business_intelligence",
                "domain": "business_intelligence",
                "status": "operational",
                "platforms": ["netsuite", "looker"],
                "okr_focus": "revenue_per_employee",
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": "team_sales_001",
                "type": "sales_intelligence",
                "domain": "sales_intelligence",
                "status": "operational",
                "platforms": ["salesforce", "hubspot"],
                "okr_focus": "revenue_per_employee",
                "created_at": datetime.now().isoformat(),
            },
        ],
        "total_teams": 2,
        "mode": "simulation",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/teams/{team_id}/status")
async def get_team_status(team_id: str):
    """Get detailed status for a specific domain team"""
    try:
        # Return simulation status
        return {
            "success": True,
            "team_status": {
                "team_id": team_id,
                "team_info": {
                    "type": "business_intelligence",
                    "domain": "business_intelligence",
                    "status": "operational",
                    "platforms": ["netsuite", "looker"],
                    "okr_focus": "revenue_per_employee",
                },
                "recent_analyses": 5,
                "last_analysis": {
                    "timestamp": datetime.now().isoformat(),
                    "type": "okr_analysis",
                    "success": True,
                },
                "integration_context": {
                    "platforms": ["netsuite", "looker"],
                    "okr_focus": "revenue_per_employee",
                    "processing_mode": "batch_hourly",
                },
            },
            "mode": "simulation",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get team status: {e}")
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")


# ==============================================================================
# INTELLIGENCE ANALYSIS ENDPOINTS
# ==============================================================================


@router.post("/teams/{team_id}/analyze")
async def execute_domain_analysis(team_id: str, request: AnalysisRequest):
    """Execute domain-specific intelligence analysis"""
    try:
        # Simulate analysis execution
        execution_time = 2.5  # Simulated execution time

        result = {
            "success": True,
            "team_id": team_id,
            "team_type": "business_intelligence",
            "analysis_type": request.analysis_type,
            "result": {
                "analysis_summary": f"Completed {request.analysis_type} analysis",
                "insights": [
                    "Revenue per employee trending upward",
                    "Cross-platform data correlation successful",
                    "Business intelligence metrics within target range",
                ],
                "metrics": {
                    "data_points_analyzed": len(request.platform_data),
                    "platforms_involved": list(request.platform_data.keys()),
                    "accuracy_score": 0.94,
                },
            },
            "execution_time": execution_time,
            "domain_insights": [
                "Financial intelligence analysis reveals revenue optimization opportunities",
                "Revenue per employee metric tracked with precision analytics",
            ],
            "okr_impact": {
                "potential_revenue_per_employee_improvement": 20000,
                "confidence_level": 0.8,
                "impact_timeline": "3-6 months",
            },
            "mode": "simulation",
            "timestamp": datetime.now().isoformat(),
        }

        # Broadcast analysis completion
        await ws_manager.broadcast_message(
            {
                "event": "analysis_completed",
                "data": {
                    "team_id": team_id,
                    "analysis_type": request.analysis_type,
                    "success": result.get("success", False),
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat(),
                },
            }
        )

        return result

    except Exception as e:
        logger.error(f"Analysis execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/correlation/execute")
async def execute_cross_platform_correlation(request: CorrelationRequest):
    """Execute cross-platform entity correlation"""
    try:
        correlation_count = len(request.platform_data) * 10  # Simulated correlation count

        result = {
            "success": True,
            "correlation_type": request.correlation_type,
            "result": {
                "correlation_summary": f"Executed {request.correlation_type} correlation",
                "correlations_found": correlation_count,
                "confidence_scores": [0.85, 0.92, 0.78, 0.96],
                "cross_platform_matches": {
                    "exact_matches": correlation_count // 2,
                    "fuzzy_matches": correlation_count // 3,
                    "potential_matches": correlation_count // 5,
                },
            },
            "execution_time": 1.8,
            "platforms_analyzed": list(request.platform_data.keys()),
            "correlation_count": correlation_count,
            "mode": "simulation",
        }

        # Broadcast correlation completion
        await ws_manager.broadcast_message(
            {
                "event": "correlation_completed",
                "data": {
                    "correlation_type": request.correlation_type,
                    "platforms": list(request.platform_data.keys()),
                    "correlation_count": correlation_count,
                    "timestamp": datetime.now().isoformat(),
                },
            }
        )

        return result

    except Exception as e:
        logger.error(f"Correlation execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Correlation failed: {str(e)}")


@router.get("/analytics/recent")
async def get_recent_analytics(team_type: Optional[str] = None, limit: int = 50, hours: int = 24):
    """Get recent analytics results"""
    # Parameter validation
    if not 1 <= limit <= 500:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 500")
    if not 1 <= hours <= 168:
        raise HTTPException(status_code=400, detail="Hours must be between 1 and 168")

    try:
        # Return simulation data
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Generate sample analytics data
        sample_analytics = []
        for i in range(min(limit, 20)):  # Generate up to 20 sample records
            sample_analytics.append(
                {
                    "id": f"analysis_{i+1}",
                    "team_type": team_type or "business_intelligence",
                    "analysis_type": "okr_analysis",
                    "timestamp": (datetime.now(timezone.utc) - timedelta(hours=i)).isoformat(),
                    "success": True,
                    "execution_time": 2.3 + (i * 0.1),
                    "insights_count": 3 + i,
                    "correlation_count": 10 + (i * 2),
                }
            )

        return {
            "success": True,
            "analytics": sample_analytics,
            "total_results": len(sample_analytics),
            "time_range": {"since": since.isoformat(), "hours": hours},
            "mode": "simulation",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get recent analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics retrieval failed: {str(e)}")


# ==============================================================================
# OKR TRACKING ENDPOINTS
# ==============================================================================


@router.put("/okr/update")
async def update_okr_metrics(request: OKRUpdateRequest):
    """Update OKR metrics and calculate revenue per employee"""
    try:
        # Calculate revenue per employee if both values provided
        revenue_per_employee = 0.0
        if request.total_revenue and request.employee_count:
            revenue_per_employee = request.total_revenue / request.employee_count

        # Calculate efficiency score
        target_rpe = request.target_revenue_per_employee or 150000  # Default target
        efficiency_score = min(revenue_per_employee / target_rpe, 1.0) if target_rpe > 0 else 0.0

        result = {
            "current_metrics": {
                "total_revenue": request.total_revenue or 0.0,
                "employee_count": request.employee_count or 0,
                "revenue_per_employee": revenue_per_employee,
                "target_revenue_per_employee": target_rpe,
                "growth_rate": 0.15,  # Simulated 15% growth
                "efficiency_score": efficiency_score,
            },
            "dashboard": {
                "okr_progress": efficiency_score * 100,
                "quarter_target": target_rpe,
                "performance_trend": "improving",
            },
            "analysis_summary": {
                "total_analyses": 45,  # Simulated data
                "correlations_performed": 23,
                "okr_calculations": 12,
            },
            "mode": "simulation",
            "timestamp": datetime.now().isoformat(),
        }

        # Broadcast OKR update
        await ws_manager.broadcast_message(
            {
                "event": "okr_updated",
                "data": {
                    "revenue_per_employee": revenue_per_employee,
                    "efficiency_score": efficiency_score,
                    "timestamp": datetime.now().isoformat(),
                },
            }
        )

        return result

    except Exception as e:
        logger.error(f"OKR update failed: {e}")
        raise HTTPException(status_code=500, detail=f"OKR update failed: {str(e)}")


@router.get("/okr/current")
async def get_current_okr_metrics():
    """Get current OKR metrics and dashboard data"""
    try:
        # Return simulation data
        return {
            "current_metrics": {
                "total_revenue": 5000000.0,
                "employee_count": 35,
                "revenue_per_employee": 142857.14,
                "target_revenue_per_employee": 150000.0,
                "growth_rate": 0.18,
                "efficiency_score": 0.952,
            },
            "dashboard": {
                "okr_progress": 95.2,
                "quarter_target": 150000.0,
                "performance_trend": "improving",
                "next_milestone": 160000.0,
            },
            "analysis_summary": {
                "total_analyses": 127,
                "correlations_performed": 64,
                "okr_calculations": 35,
            },
            "mode": "simulation",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get OKR metrics: {e}")
        raise HTTPException(status_code=500, detail=f"OKR retrieval failed: {str(e)}")


@router.get("/okr/trends")
async def get_okr_trends(days: int = 30):
    """Get OKR trends over time"""
    # Parameter validation
    if not 1 <= days <= 365:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 365")

    try:
        # Generate simulation trend data
        trends = []
        base_rpe = 135000  # Base revenue per employee

        for i in range(days):
            date = datetime.now(timezone.utc) - timedelta(days=days - i - 1)
            # Simulate gradual improvement with some variance
            daily_rpe = base_rpe + (i * 50) + (i % 7) * 200
            trends.append({"timestamp": date.isoformat(), "revenue_per_employee": daily_rpe})

        return {
            "success": True,
            "trends": trends,
            "days": days,
            "data_points": len(trends),
            "trend_analysis": {
                "overall_direction": "improving",
                "growth_rate": "2.1% monthly",
                "volatility": "low",
            },
            "mode": "simulation",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get OKR trends: {e}")
        raise HTTPException(status_code=500, detail=f"Trends retrieval failed: {str(e)}")


# ==============================================================================
# EXECUTIVE DASHBOARD ENDPOINT
# ==============================================================================


@router.get("/dashboard/executive", response_model=DashboardDataResponse)
async def get_executive_dashboard():
    """Get comprehensive executive dashboard data"""
    try:
        # Return comprehensive simulation data
        return DashboardDataResponse(
            okr_metrics={
                "current_metrics": {
                    "total_revenue": 5000000.0,
                    "employee_count": 35,
                    "revenue_per_employee": 142857.14,
                    "target_revenue_per_employee": 150000.0,
                    "growth_rate": 0.18,
                    "efficiency_score": 0.952,
                },
                "dashboard": {
                    "okr_progress": 95.2,
                    "quarter_target": 150000.0,
                    "performance_trend": "improving",
                },
            },
            team_analytics=[
                {
                    "team_id": "team_bi_001",
                    "team_type": "business_intelligence",
                    "domain": "business_intelligence",
                    "status": "operational",
                    "recent_analyses": 23,
                    "platforms": ["netsuite", "looker"],
                    "okr_focus": "revenue_per_employee",
                },
                {
                    "team_id": "team_sales_001",
                    "team_type": "sales_intelligence",
                    "domain": "sales_intelligence",
                    "status": "operational",
                    "recent_analyses": 18,
                    "platforms": ["salesforce", "hubspot"],
                    "okr_focus": "revenue_per_employee",
                },
            ],
            correlation_insights=[
                {
                    "correlation_type": "revenue_attribution",
                    "platforms": ["netsuite", "salesforce"],
                    "timestamp": datetime.now().isoformat(),
                    "execution_time": 2.3,
                },
                {
                    "correlation_type": "customer_journey",
                    "platforms": ["hubspot", "slack"],
                    "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "execution_time": 3.1,
                },
            ],
            real_time_status={
                "active_websocket_connections": len(ws_manager.active_connections),
                "domain_teams_active": 2,
                "integration_orchestrator_status": "simulation_mode",
                "last_update": datetime.now().isoformat(),
            },
            performance_metrics={
                "total_operations": 245,
                "active_agents": 8,
                "tactical_teams": 3,
                "domain_teams": 2,
                "integration_readiness": "simulation_mode",
            },
        )

    except Exception as e:
        logger.error(f"Failed to get executive dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard retrieval failed: {str(e)}")


# ==============================================================================
# INTEGRATION STATUS ENDPOINTS
# ==============================================================================


@router.get("/status/integration", response_model=IntegrationStatusResponse)
async def get_integration_status():
    """Get comprehensive integration system status"""
    try:
        return IntegrationStatusResponse(
            active_teams=[
                {
                    "id": "team_bi_001",
                    "type": "business_intelligence",
                    "domain": "business_intelligence",
                    "status": "operational",
                    "platforms": ["netsuite", "looker"],
                    "okr_focus": "revenue_per_employee",
                    "created_at": datetime.now().isoformat(),
                }
            ],
            platform_connections={
                "netsuite": {"status": "connected", "last_sync": datetime.now().isoformat()},
                "looker": {"status": "connected", "last_sync": datetime.now().isoformat()},
                "salesforce": {"status": "connected", "last_sync": datetime.now().isoformat()},
                "hubspot": {"status": "connected", "last_sync": datetime.now().isoformat()},
                "slack": {"status": "simulation", "last_sync": datetime.now().isoformat()},
                "gong": {"status": "simulation", "last_sync": datetime.now().isoformat()},
            },
            recent_analyses=[
                {
                    "id": "analysis_001",
                    "type": "okr_analysis",
                    "team_id": "team_bi_001",
                    "timestamp": datetime.now().isoformat(),
                    "success": True,
                }
            ],
            websocket_connections=len(ws_manager.active_connections),
            system_health={
                "overall_status": "simulation",
                "agent_factory_status": "simulation",
                "memory_system_status": "simulation",
                "websocket_manager_status": "operational",
                "total_operations": 245,
                "uptime": "simulation",
                "last_health_check": datetime.now().isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Failed to get integration status: {e}")
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")


@router.get("/health")
async def integration_health_check():
    """Health check endpoint for integration intelligence system"""
    try:
        return {
            "status": "operational",
            "service": "integration_intelligence",
            "version": "1.0.0",
            "mode": "simulation",
            "imports_available": False,
            "memory_available": False,
            "active_websocket_connections": len(ws_manager.active_connections),
            "message": "Integration intelligence router operational in simulation mode",
            "available_endpoints": [
                "POST /api/integration-intelligence/domain-teams/create",
                "GET /api/integration-intelligence/domain-teams",
                "GET /api/integration-intelligence/teams/{team_id}/status",
                "POST /api/integration-intelligence/teams/{team_id}/analyze",
                "POST /api/integration-intelligence/correlation/execute",
                "GET /api/integration-intelligence/analytics/recent",
                "PUT /api/integration-intelligence/okr/update",
                "GET /api/integration-intelligence/okr/current",
                "GET /api/integration-intelligence/okr/trends",
                "GET /api/integration-intelligence/dashboard/executive",
                "GET /api/integration-intelligence/status/integration",
                "WS /api/integration-intelligence/ws/real-time-updates",
            ],
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "degraded", "error": str(e), "timestamp": datetime.now().isoformat()}


# ==============================================================================
# WEBSOCKET ENDPOINTS
# ==============================================================================


@router.websocket("/ws/real-time-updates")
async def websocket_real_time_updates(websocket: WebSocket):
    """WebSocket endpoint for real-time integration updates"""
    client_info = {
        "connected_at": datetime.now().isoformat(),
        "client_type": "integration_dashboard",
    }

    await ws_manager.connect(websocket, client_info)

    try:
        # Send initial status
        await ws_manager.send_to_specific(
            websocket,
            {
                "event": "connection_established",
                "data": {
                    "message": "Connected to Integration Intelligence real-time updates (simulation mode)",
                    "mode": "simulation",
                    "available_events": [
                        "domain_team_created",
                        "analysis_completed",
                        "correlation_completed",
                        "okr_updated",
                        "system_status_change",
                    ],
                    "timestamp": datetime.now().isoformat(),
                },
            },
        )

        # Keep connection alive and handle incoming messages
        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)

                if data.get("type") == "ping":
                    await websocket.send_json(
                        {"type": "pong", "timestamp": datetime.now().isoformat()}
                    )
                elif data.get("type") == "subscribe":
                    await websocket.send_json(
                        {
                            "type": "subscription_confirmed",
                            "events": data.get("events", []),
                            "mode": "simulation",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket message handling error: {e}")
                break

    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(websocket)


@router.websocket("/ws/team/{team_id}")
async def websocket_team_specific(websocket: WebSocket, team_id: str):
    """WebSocket endpoint for team-specific real-time updates"""
    client_info = {
        "connected_at": datetime.now().isoformat(),
        "client_type": "team_monitor",
        "team_id": team_id,
    }

    await ws_manager.connect(websocket, client_info)

    try:
        # Send initial team status
        await ws_manager.send_to_specific(
            websocket,
            {
                "event": "team_status",
                "data": {
                    "team_id": team_id,
                    "status": "operational",
                    "mode": "simulation",
                    "message": f"Connected to team {team_id} updates",
                },
            },
        )

        # Keep connection alive
        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)

                if data.get("type") == "get_status":
                    await websocket.send_json(
                        {
                            "event": "team_status",
                            "data": {
                                "team_id": team_id,
                                "status": "operational",
                                "mode": "simulation",
                                "last_update": datetime.now().isoformat(),
                            },
                        }
                    )

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Team WebSocket error: {e}")
                break

    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(websocket)


# ==============================================================================
# SIMULATION MODE NOTIFICATION
# ==============================================================================

logger.info("🎭 Integration Intelligence Router loaded in SIMULATION MODE")
logger.info("📊 All endpoints return simulated data for development and testing")
logger.info("🔌 WebSocket functionality is operational")
logger.info("🚀 Ready to serve integration intelligence requests")
