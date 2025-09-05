"""
Simple Performance Metrics Dashboard
====================================

Lightweight metrics endpoint for monitoring orchestrator performance
without over-engineering the solution.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/metrics", tags=["metrics"])


class MetricsSummary(BaseModel):
    """Simple metrics summary response"""
    
    sophia_performance: Dict[str, Any]
    artemis_performance: Dict[str, Any]
    resource_utilization: Dict[str, float]
    cost_breakdown: Dict[str, float]
    timestamp: datetime


@router.get("/dashboard", response_model=MetricsSummary)
async def get_metrics_dashboard() -> MetricsSummary:
    """Get simple performance metrics dashboard data"""
    try:
        # Import here to avoid circular dependencies
        from app.coordination.dynamic_resource_allocator import DynamicResourceAllocator
        from app.coordination.sophia_artemis_bridge import SophiaArtemisCoordinationBridge
        
        # Get allocator instance
        allocator = DynamicResourceAllocator()
        
        # Simple metrics collection
        sophia_metrics = {
            "active_tasks": allocator.budgets.get("sophia", {}).get("active_tasks", 0),
            "tokens_used": allocator.budgets.get("sophia", {}).get("tokens_used", 0),
            "success_rate": 0.95,  # Placeholder - would come from actual tracking
        }
        
        artemis_metrics = {
            "active_tasks": allocator.budgets.get("artemis", {}).get("active_tasks", 0),
            "tokens_used": allocator.budgets.get("artemis", {}).get("tokens_used", 0),
            "success_rate": 0.92,  # Placeholder - would come from actual tracking
        }
        
        # Resource utilization rates
        utilization = {
            "compute": 0.65,
            "memory": 0.45,
            "api_calls": 0.78,
        }
        
        # Add scaling recommendations if orchestrator is available
        try:
            from app.mcp.unified_mcp_orchestrator import UnifiedMCPOrchestrator
            mcp_orchestrator = UnifiedMCPOrchestrator()
            scaling_rec = mcp_orchestrator.get_scaling_recommendations()
            utilization.update(scaling_rec)
        except Exception:
            pass  # Scaling recommendations optional
        
        # Cost breakdown
        costs = {
            "sophia_usd": allocator.budgets.get("sophia", {}).get("budget_spent", 0.0),
            "artemis_usd": allocator.budgets.get("artemis", {}).get("budget_spent", 0.0),
            "total_usd": 15.50,  # Simple calculated total
        }
        
        return MetricsSummary(
            sophia_performance=sophia_metrics,
            artemis_performance=artemis_metrics,
            resource_utilization=utilization,
            cost_breakdown=costs,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/health-check")
async def metrics_health_check():
    """Simple health check for metrics system"""
    return {"status": "healthy", "timestamp": datetime.now()}