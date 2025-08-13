"""
Sales Router for accessing Gong call data through the API.

This router exposes endpoints for retrieving and analyzing Gong call data.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, List, Optional, Any

from libs.mcp_client.gong import GongMCPClient
from schemas.gong import MCPError as GongMCPError

router = APIRouter(
    prefix="/sales",
    tags=["sales"],
)


async def get_gong_client():
    """
    Dependency to get a Gong MCP client.

    Returns:
        A Gong MCP client instance
    """
    client = GongMCPClient()
    try:
        yield client
    finally:
        await client.close()


@router.get("/calls/{call_id}/transcript")
async def get_call_transcript(call_id: str, gong_client: GongMCPClient = Depends(get_gong_client)):
    """
    Retrieve the transcript for a specific call.

    Args:
        call_id: The ID of the call to retrieve the transcript for
        gong_client: Gong MCP client dependency

    Returns:
        The call transcript with standard envelope
    """
    try:
        transcript = await gong_client.get_call_transcript(call_id)
        return {"success": True, "data": transcript}
    except GongMCPError as e:
        raise HTTPException(status_code=e.status_code, detail={"success": False, "error": {
                            "type": e.error_type, "message": e.message, "status": e.status_code}})


@router.get("/calls/{call_id}/insights")
async def get_call_insights(call_id: str, gong_client: GongMCPClient = Depends(get_gong_client)) -> Dict[str, Any]:
    """
    Get AI-generated insights for a specific call.

    Args:
        call_id: The ID of the call to get insights for
        gong_client: Gong MCP client dependency

    Returns:
        A list of call insights
    """
    try:
        insights = await gong_client.get_call_insights(call_id)
        return {"success": True, "data": insights}
    except GongMCPError as e:
        raise HTTPException(status_code=e.status_code, detail={"success": False, "error": {
            "type": e.error_type, "message": e.message, "status": e.status_code}})


@router.get("/calls/{call_id}/summary")
async def get_call_summary(call_id: str, gong_client: GongMCPClient = Depends(get_gong_client)) -> Dict[str, Any]:
    """
    Get a summary of a specific call.

    Args:
        call_id: The ID of the call to summarize
        gong_client: Gong MCP client dependency

    Returns:
        A summary of the call
    """
    try:
        summary = await gong_client.get_call_summary(call_id)
        return {"success": True, "data": summary}
    except GongMCPError as e:
        raise HTTPException(status_code=e.status_code, detail={"success": False, "error": {
            "type": e.error_type, "message": e.message, "status": e.status_code}})


@router.get("/calls/search")
async def search_calls(
    query: str,
    limit: Optional[int] = Query(10, ge=1, le=100),
    gong_client: GongMCPClient = Depends(get_gong_client)
) -> Dict[str, Any]:
    """
    Search for calls matching the given query.

    Args:
        query: The search query
        limit: Maximum number of results to return (1-100)
        gong_client: Gong MCP client dependency

    Returns:
        Search results with pagination metadata
    """
    try:
        results = await gong_client.search_calls(query, limit)
        return {"success": True, "data": results["data"], "meta": results.get("meta", {})}
    except GongMCPError as e:
        raise HTTPException(status_code=e.status_code, detail={"success": False, "error": {
            "type": e.error_type, "message": e.message, "status": e.status_code}})


@router.get("/calls/{call_id}/analyze")
async def analyze_call(call_id: str, gong_client: GongMCPClient = Depends(get_gong_client)) -> Dict[str, Any]:
    """
    Perform a comprehensive analysis of a call.

    Args:
        call_id: The ID of the call to analyze
        gong_client: Gong MCP client dependency

    Returns:
        Analysis results including transcript, insights, and summary
    """
    try:
        transcript = await gong_client.get_call_transcript(call_id)
        insights = await gong_client.get_call_insights(call_id)
        summary = await gong_client.get_call_summary(call_id)

        return {
            "success": True,
            "data": {
                "transcript": transcript,
                "insights": insights,
                "summary": summary
            }
        }
    except GongMCPError as e:
        raise HTTPException(status_code=e.status_code, detail={"success": False, "error": {
            "type": e.error_type, "message": e.message, "status": e.status_code}})
