"""
FastAPI endpoints for cross-orchestrator coordination monitoring and analytics
Provides real-time metrics, task flow analytics, and performance monitoring
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.api.middleware.auth import get_current_user
from app.core.ai_logger import logger
from app.core.websocket_manager import WebSocketManager

router = APIRouter(prefix="/orchestrator-coordination", tags=["coordination"])

# WebSocket manager for real-time updates
ws_manager: WebSocketManager | None = None


# Pydantic models for API responses
class OrchestratorStatus(BaseModel):
    """Status information for an orchestrator"""

    id: str
    name: str
    type: str  # 'sophia' or 'artemis'
    status: str  # 'active', 'idle', 'overloaded', 'error'
    active_tasks: int
    max_tasks: int
    queue_size: int
    performance_score: float
    uptime_hours: float
    last_heartbeat: datetime
    domain: str
    resource_usage: dict[str, float]


class TaskBridge(BaseModel):
    """Information about task flow between orchestrators"""

    id: str
    source_orchestrator: str
    target_orchestrator: str
    task_type: str
    priority: str  # 'high', 'medium', 'low'
    status: str  # 'pending', 'in_transit', 'delivered', 'failed'
    context_preserved: bool
    pay_ready_context: bool
    created_at: datetime
    completed_at: datetime | None = None
    processing_time_ms: int | None = None


class CoordinationMetrics(BaseModel):
    """Overall coordination system metrics"""

    total_tasks_processed: int
    task_flow_rate_per_minute: float
    average_response_time_ms: float
    resource_utilization_percent: float
    bridge_health_score: float
    synchronization_lag_ms: int
    active_bottlenecks: int
    success_rate_percent: float
    peak_throughput: float
    last_updated: datetime


class TaskFlowAnalytics(BaseModel):
    """Analytics data for task flow visualization"""

    orchestrator_utilization: dict[str, float]
    task_distribution: dict[str, int]
    priority_breakdown: dict[str, int]
    processing_times: dict[str, list[float]]
    bottleneck_analysis: dict[str, Any]
    flow_efficiency: float
    resource_allocation: dict[str, dict[str, Any]]


class ResourceAllocation(BaseModel):
    """Resource allocation status for orchestrators"""

    orchestrator_id: str
    allocated_tasks: int
    available_capacity: int
    utilization_percent: float
    queue_depth: int
    average_wait_time_ms: float
    predicted_capacity: int
    scaling_recommendation: str | None = None


class PerformanceBottleneck(BaseModel):
    """Information about identified performance bottlenecks"""

    id: str
    type: str  # 'queue_saturation', 'resource_contention', 'sync_lag'
    severity: str  # 'low', 'medium', 'high', 'critical'
    orchestrator_affected: str
    description: str
    impact_score: float
    suggested_action: str
    detected_at: datetime
    resolved_at: datetime | None = None


# Mock data generators (in production, these would interface with actual orchestrators)
def get_mock_orchestrator_status() -> list[OrchestratorStatus]:
    """Generate mock orchestrator status data"""
    return [
        OrchestratorStatus(
            id="sophia-001",
            name="Sophia Business Intelligence",
            type="sophia",
            status="active",
            active_tasks=6,
            max_tasks=8,
            queue_size=3,
            performance_score=94.2,
            uptime_hours=168.5,
            last_heartbeat=datetime.utcnow(),
            domain="Business Intelligence & Analytics",
            resource_usage={
                "cpu_percent": 67.3,
                "memory_percent": 72.1,
                "io_percent": 34.6,
            },
        ),
        OrchestratorStatus(
            id="artemis-001",
            name="Artemis Code Excellence",
            type="artemis",
            status="active",
            active_tasks=4,
            max_tasks=8,
            queue_size=7,
            performance_score=87.8,
            uptime_hours=165.2,
            last_heartbeat=datetime.utcnow(),
            domain="Software Development & Technical Excellence",
            resource_usage={
                "cpu_percent": 54.7,
                "memory_percent": 68.9,
                "io_percent": 42.1,
            },
        ),
    ]


def get_mock_task_bridges() -> list[TaskBridge]:
    """Generate mock task bridge data"""
    now = datetime.utcnow()
    return [
        TaskBridge(
            id="bridge-001",
            source_orchestrator="sophia-001",
            target_orchestrator="artemis-001",
            task_type="Pay Ready Implementation",
            priority="high",
            status="in_transit",
            context_preserved=True,
            pay_ready_context=True,
            created_at=now - timedelta(minutes=5),
            processing_time_ms=2840,
        ),
        TaskBridge(
            id="bridge-002",
            source_orchestrator="artemis-001",
            target_orchestrator="sophia-001",
            task_type="Performance Analytics",
            priority="medium",
            status="delivered",
            context_preserved=True,
            pay_ready_context=False,
            created_at=now - timedelta(minutes=8),
            completed_at=now - timedelta(minutes=2),
            processing_time_ms=1650,
        ),
        TaskBridge(
            id="bridge-003",
            source_orchestrator="sophia-001",
            target_orchestrator="artemis-001",
            task_type="Code Quality Assessment",
            priority="low",
            status="pending",
            context_preserved=True,
            pay_ready_context=False,
            created_at=now - timedelta(minutes=1),
        ),
    ]


def get_mock_coordination_metrics() -> CoordinationMetrics:
    """Generate mock coordination metrics"""
    return CoordinationMetrics(
        total_tasks_processed=1456,
        task_flow_rate_per_minute=23.4,
        average_response_time_ms=287,
        resource_utilization_percent=87.3,
        bridge_health_score=96.2,
        synchronization_lag_ms=120,
        active_bottlenecks=2,
        success_rate_percent=96.7,
        peak_throughput=45.8,
        last_updated=datetime.utcnow(),
    )


def get_mock_performance_bottlenecks() -> list[PerformanceBottleneck]:
    """Generate mock bottleneck analysis"""
    now = datetime.utcnow()
    return [
        PerformanceBottleneck(
            id="bottleneck-001",
            type="queue_saturation",
            severity="medium",
            orchestrator_affected="artemis-001",
            description="Artemis queue approaching capacity with 7/8 tasks active",
            impact_score=6.7,
            suggested_action="Consider scaling artemis instances or redistributing tasks",
            detected_at=now - timedelta(minutes=12),
        ),
        PerformanceBottleneck(
            id="bottleneck-002",
            type="sync_lag",
            severity="low",
            orchestrator_affected="coordination-bridge",
            description="Cross-domain context transfer experiencing slight delays",
            impact_score=3.2,
            suggested_action="Optimize bridge serialization/deserialization",
            detected_at=now - timedelta(minutes=8),
        ),
    ]


# API Endpoints


@router.get("/status", response_model=list[OrchestratorStatus])
async def get_orchestrator_status(current_user=Depends(get_current_user)):
    """
    Get current status of all orchestrators

    Returns real-time status information including:
    - Active/queued tasks
    - Resource utilization
    - Performance metrics
    - Health indicators
    """
    try:
        orchestrators = get_mock_orchestrator_status()
        logger.info(f"Retrieved status for {len(orchestrators)} orchestrators")
        return orchestrators
    except Exception as e:
        logger.error(f"Error retrieving orchestrator status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task-bridges", response_model=list[TaskBridge])
async def get_task_bridges(
    status: str | None = None,
    orchestrator_id: str | None = None,
    current_user=Depends(get_current_user),
):
    """
    Get task bridge information for cross-orchestrator coordination

    Args:
        status: Filter by bridge status (pending, in_transit, delivered, failed)
        orchestrator_id: Filter by specific orchestrator

    Returns information about task flow between orchestrators
    """
    try:
        bridges = get_mock_task_bridges()

        # Apply filters
        if status:
            bridges = [b for b in bridges if b.status == status]
        if orchestrator_id:
            bridges = [
                b
                for b in bridges
                if b.source_orchestrator == orchestrator_id
                or b.target_orchestrator == orchestrator_id
            ]

        logger.info(f"Retrieved {len(bridges)} task bridges")
        return bridges
    except Exception as e:
        logger.error(f"Error retrieving task bridges: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=CoordinationMetrics)
async def get_coordination_metrics(
    time_range: str = "1h", current_user=Depends(get_current_user)
):
    """
    Get overall coordination system metrics

    Args:
        time_range: Time range for metrics (1h, 6h, 24h, 7d)

    Returns comprehensive coordination performance metrics
    """
    try:
        metrics = get_mock_coordination_metrics()
        logger.info(f"Retrieved coordination metrics for time range: {time_range}")
        return metrics
    except Exception as e:
        logger.error(f"Error retrieving coordination metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics", response_model=TaskFlowAnalytics)
async def get_task_flow_analytics(
    time_range: str = "1h", current_user=Depends(get_current_user)
):
    """
    Get detailed task flow analytics for visualization

    Args:
        time_range: Time range for analytics (1h, 6h, 24h, 7d)

    Returns analytics data optimized for dashboard visualization
    """
    try:
        # Mock analytics data
        analytics = TaskFlowAnalytics(
            orchestrator_utilization={"sophia-001": 75.0, "artemis-001": 50.0},
            task_distribution={
                "business_intelligence": 45,
                "code_generation": 32,
                "analytics": 28,
                "optimization": 18,
            },
            priority_breakdown={"high": 12, "medium": 34, "low": 27},
            processing_times={
                "sophia-001": [280, 340, 195, 420, 310],
                "artemis-001": [150, 890, 450, 275, 680],
            },
            bottleneck_analysis={
                "queue_saturation_risk": 0.67,
                "sync_lag_average": 120,
                "resource_contention": 0.23,
            },
            flow_efficiency=87.3,
            resource_allocation={
                "sophia-001": {
                    "allocated": 6,
                    "available": 2,
                    "utilization": 0.75,
                    "queue": 3,
                },
                "artemis-001": {
                    "allocated": 4,
                    "available": 4,
                    "utilization": 0.50,
                    "queue": 7,
                },
            },
        )

        logger.info(f"Retrieved task flow analytics for time range: {time_range}")
        return analytics
    except Exception as e:
        logger.error(f"Error retrieving task flow analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resource-allocation", response_model=list[ResourceAllocation])
async def get_resource_allocation(current_user=Depends(get_current_user)):
    """
    Get current resource allocation status for all orchestrators

    Returns detailed resource allocation information including:
    - Task distribution
    - Capacity utilization
    - Queue depths
    - Scaling recommendations
    """
    try:
        allocations = [
            ResourceAllocation(
                orchestrator_id="sophia-001",
                allocated_tasks=6,
                available_capacity=2,
                utilization_percent=75.0,
                queue_depth=3,
                average_wait_time_ms=1200,
                predicted_capacity=8,
                scaling_recommendation=None,
            ),
            ResourceAllocation(
                orchestrator_id="artemis-001",
                allocated_tasks=4,
                available_capacity=4,
                utilization_percent=50.0,
                queue_depth=7,
                average_wait_time_ms=2800,
                predicted_capacity=8,
                scaling_recommendation="Consider scaling up due to high queue depth",
            ),
        ]

        logger.info(
            f"Retrieved resource allocation for {len(allocations)} orchestrators"
        )
        return allocations
    except Exception as e:
        logger.error(f"Error retrieving resource allocation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bottlenecks", response_model=list[PerformanceBottleneck])
async def get_performance_bottlenecks(
    severity: str | None = None, current_user=Depends(get_current_user)
):
    """
    Get identified performance bottlenecks in the coordination system

    Args:
        severity: Filter by severity level (low, medium, high, critical)

    Returns list of current and recent performance bottlenecks
    """
    try:
        bottlenecks = get_mock_performance_bottlenecks()

        if severity:
            bottlenecks = [b for b in bottlenecks if b.severity == severity]

        logger.info(f"Retrieved {len(bottlenecks)} performance bottlenecks")
        return bottlenecks
    except Exception as e:
        logger.error(f"Error retrieving performance bottlenecks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bridge-health-check")
async def bridge_health_check(current_user=Depends(get_current_user)):
    """
    Trigger a comprehensive health check of the coordination bridge

    Returns health check results and any issues found
    """
    try:
        # Mock health check
        health_result = {
            "bridge_status": "healthy",
            "connection_latency_ms": 45,
            "context_preservation_rate": 98.7,
            "serialization_performance": "optimal",
            "resource_usage": {"cpu_percent": 23.1, "memory_mb": 145.6},
            "recommendations": [
                "Consider increasing bridge connection pool size",
                "Monitor serialization buffer usage",
            ],
            "last_check": datetime.utcnow(),
        }

        logger.info("Performed bridge health check")
        return health_result
    except Exception as e:
        logger.error(f"Error performing bridge health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time updates
@router.websocket("/ws")
async def websocket_coordination_updates(websocket: WebSocket):
    """
    WebSocket endpoint for real-time coordination updates

    Provides streaming updates for:
    - Orchestrator status changes
    - Task flow events
    - Performance metrics
    - Bottleneck alerts
    """
    await websocket.accept()
    client_id = f"coordination-{id(websocket)}"

    try:
        # Send initial data
        initial_data = {
            "type": "initial",
            "orchestrators": [o.dict() for o in get_mock_orchestrator_status()],
            "metrics": get_mock_coordination_metrics().dict(),
            "timestamp": datetime.utcnow().isoformat(),
        }
        await websocket.send_json(initial_data)

        # Keep connection alive and send periodic updates
        while True:
            await asyncio.sleep(5)  # Update every 5 seconds

            update_data = {
                "type": "update",
                "orchestrators": [o.dict() for o in get_mock_orchestrator_status()],
                "task_bridges": [b.dict() for b in get_mock_task_bridges()],
                "metrics": get_mock_coordination_metrics().dict(),
                "timestamp": datetime.utcnow().isoformat(),
            }
            await websocket.send_json(update_data)

    except WebSocketDisconnect:
        logger.info(f"WebSocket client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        await websocket.close()


def set_websocket_manager(manager: WebSocketManager):
    """Set the WebSocket manager for real-time updates"""
    global ws_manager
    ws_manager = manager
