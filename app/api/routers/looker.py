"""
Looker Business Intelligence API Router

Provides REST endpoints for Looker integration including dashboards,
looks, data exploration, and content search capabilities.
"""

import logging
from datetime import datetime
from typing import Any, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query

from app.integrations.looker_client import LookerClient, get_looker_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/business/looker", tags=["looker", "business-intelligence"])


def get_client() -> LookerClient:
    """Dependency to get Looker client"""
    try:
        return get_looker_client()
    except Exception as e:
        logger.error(f"Failed to get Looker client: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Looker service unavailable: {str(e)}")


@router.get("/health", summary="Check Looker connection health")
async def health_check(client: LookerClient = Depends(get_client)) -> dict[str, Any]:
    """
    Test Looker API connection and return health status

    Returns:
        Connection status, user info, and Looker version
    """
    try:
        result = client.test_connection()
        return {
            "service": "looker",
            "status": result.get("status"),
            "timestamp": datetime.now().isoformat(),
            "details": result,
        }
    except Exception as e:
        logger.error(f"Looker health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/system", summary="Get Looker system information")
async def get_system_info(client: LookerClient = Depends(get_client)) -> dict[str, Any]:
    """
    Get comprehensive Looker system information including version,
    user details, and content statistics
    """
    try:
        return client.get_system_info()
    except Exception as e:
        logger.error(f"Failed to get system info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboards", summary="List Looker dashboards")
async def get_dashboards(
    limit: int = Query(50, ge=1, le=500, description="Maximum number of dashboards to return"),
    client: LookerClient = Depends(get_client),
) -> dict[str, Any]:
    """
    Get list of Looker dashboards with metadata

    Args:
        limit: Maximum number of dashboards to return (1-500)

    Returns:
        List of dashboard metadata including titles, descriptions, and stats
    """
    try:
        dashboards = client.get_dashboards(limit=limit)

        return {
            "dashboards": [
                {
                    "id": dash.id,
                    "title": dash.title,
                    "description": dash.description,
                    "folder_id": dash.folder_id,
                    "created_at": dash.created_at,
                    "updated_at": dash.updated_at,
                    "view_count": dash.view_count,
                    "favorite_count": dash.favorite_count,
                }
                for dash in dashboards
            ],
            "count": len(dashboards),
            "retrieved_at": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get dashboards: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboards/{dashboard_id}", summary="Get dashboard data")
async def get_dashboard_data(
    dashboard_id: str, client: LookerClient = Depends(get_client)
) -> dict[str, Any]:
    """
    Get data from a specific Looker dashboard including all elements and their data

    Args:
        dashboard_id: Looker dashboard ID

    Returns:
        Dashboard metadata and data from all dashboard elements
    """
    try:
        return client.get_dashboard_data(dashboard_id)
    except Exception as e:
        logger.error(f"Failed to get dashboard {dashboard_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/looks", summary="List Looker looks")
async def get_looks(
    limit: int = Query(50, ge=1, le=500, description="Maximum number of looks to return"),
    client: LookerClient = Depends(get_client),
) -> dict[str, Any]:
    """
    Get list of Looker looks (saved visualizations) with metadata

    Args:
        limit: Maximum number of looks to return (1-500)

    Returns:
        List of look metadata including titles, descriptions, and stats
    """
    try:
        looks = client.get_looks(limit=limit)

        return {
            "looks": [
                {
                    "id": look.id,
                    "title": look.title,
                    "description": look.description,
                    "query_id": look.query_id,
                    "folder_id": look.folder_id,
                    "created_at": look.created_at,
                    "updated_at": look.updated_at,
                    "view_count": look.view_count,
                }
                for look in looks
            ],
            "count": len(looks),
            "retrieved_at": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get looks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/looks/{look_id}", summary="Get look data")
async def get_look_data(
    look_id: str,
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of rows to return"),
    client: LookerClient = Depends(get_client),
) -> dict[str, Any]:
    """
    Get data from a specific Looker look (saved visualization)

    Args:
        look_id: Looker look ID
        limit: Maximum number of data rows to return (1-10000)

    Returns:
        Look metadata and data results
    """
    try:
        return client.get_look_data(look_id, limit=limit)
    except Exception as e:
        logger.error(f"Failed to get look {look_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", summary="List Looker models")
async def get_models(client: LookerClient = Depends(get_client)) -> dict[str, Any]:
    """
    Get list of available Looker models and their explores

    Returns:
        List of models with their available explores for data exploration
    """
    try:
        models = client.get_models()

        return {"models": models, "count": len(models), "retrieved_at": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Failed to get models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explore", summary="Explore data using Looker")
async def explore_data(
    request: dict[str, Any], client: LookerClient = Depends(get_client)
) -> dict[str, Any]:
    """
    Explore data using Looker's explore API

    Request body should include:
    - model: Looker model name (required)
    - explore: Explore name (required)
    - dimensions: List of dimensions to include (required)
    - measures: List of measures to include (required)
    - filters: Optional filters as key-value pairs
    - limit: Optional row limit (default: 500)

    Returns:
        Query metadata and data results
    """
    try:
        # Validate required fields
        required_fields = ["model", "explore", "dimensions", "measures"]
        for field in required_fields:
            if field not in request:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # Extract parameters
        model = request["model"]
        explore = request["explore"]
        dimensions = request["dimensions"]
        measures = request["measures"]
        filters = request.get("filters", {})
        limit = request.get("limit", 500)

        # Validate limit
        if not isinstance(limit, int) or limit < 1 or limit > 10000:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 10000")

        return client.explore_data(
            model=model,
            explore=explore,
            dimensions=dimensions,
            measures=measures,
            filters=filters,
            limit=limit,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to explore data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", summary="Search Looker content")
async def search_content(
    q: str = Query(..., description="Search query"),
    types: Optional[str] = Query(
        None, description="Content types to search (comma-separated: dashboard,look,query)"
    ),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results to return"),
    client: LookerClient = Depends(get_client),
) -> dict[str, Any]:
    """
    Search Looker content including dashboards, looks, and queries

    Args:
        q: Search query string
        types: Optional comma-separated list of content types to search
        limit: Maximum number of results to return (1-500)

    Returns:
        Organized search results by content type
    """
    try:
        # Parse content types
        search_types = None
        if types:
            search_types = [t.strip() for t in types.split(",")]

        return client.search_content(query=q, types=search_types, limit=limit)

    except Exception as e:
        logger.error(f"Failed to search content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queries/{query_id}/run", summary="Run Looker query")
async def run_query(
    query_id: str,
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of rows to return"),
    format_type: str = Query("json", description="Result format (json, csv, etc.)"),
    client: LookerClient = Depends(get_client),
) -> Union[list[dict[str, Any]], str]:
    """
    Run a specific Looker query by ID

    Args:
        query_id: Looker query ID
        limit: Maximum number of data rows to return (1-10000)
        format_type: Result format (default: json)

    Returns:
        Query results in requested format
    """
    try:
        results = client.run_query(query_id, limit=limit, format_type=format_type)

        if format_type == "json":
            return {
                "query_id": query_id,
                "results": results,
                "row_count": len(results) if isinstance(results, list) else None,
                "retrieved_at": datetime.now().isoformat(),
            }
        else:
            return results

    except Exception as e:
        logger.error(f"Failed to run query {query_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
