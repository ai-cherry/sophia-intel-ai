"""Unified Pay Ready BI dashboard API endpoints."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter

from app.models.bi_dashboard import (
    AgnoWorkspace,
    BusinessMetric,
    FlowwiseFactory,
)
from app.services.agno_workspaces import agno_workspace_service
from app.services.business_metrics import business_metric_store
from app.services.flowwise_gateway import flowwise_gateway

router = APIRouter(prefix="/api/bi", tags=["business-intelligence"])
flowwise_router = APIRouter(prefix="/api/flowwise", tags=["flowwise"])
agno_router = APIRouter(prefix="/api/agno", tags=["agno"])


@router.get("/metrics", response_model=list[BusinessMetric])
async def list_metrics() -> list[BusinessMetric]:
    metrics = business_metric_store.list_metrics()
    asyncio.create_task(business_metric_store.refresh_embeddings(metrics))
    return metrics


@flowwise_router.get("/factories", response_model=list[FlowwiseFactory])
async def list_flowwise_factories() -> list[FlowwiseFactory]:
    return await flowwise_gateway.fetch_factories()


@agno_router.get("/workspaces", response_model=list[AgnoWorkspace])
async def list_agno_workspaces() -> list[AgnoWorkspace]:
    return await agno_workspace_service.fetch_workspaces()
