"""
Gong MCP Server

This module provides a FastAPI server that serves as the Model Context Protocol (MCP)
for interacting with the Gong API.
"""

import os
import logging
import json
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

import httpx
import backoff
from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends

from schemas.gong import (
    CallTranscript,
    CallInsight,
    CallSummary,
    PaginationMeta,
    PaginatedResponse
)

logger = logging.getLogger(__name__)

# Create FastAPI app and router
app = FastAPI(title="Gong MCP Server")
router = APIRouter(prefix="")


class GongAPI:
    """Class for interacting with the Gong API."""

    def __init__(self):
        """Initialize the Gong API client."""
        self.base_url = os.environ.get(
            "GONG_API_URL", "https://api.gong.io/v2")
        self.access_key = os.environ.get("GONG_ACCESS_KEY")
        self.client_secret = os.environ.get("GONG_CLIENT_SECRET")

        if not self.access_key or not self.client_secret:
            logger.warning(
                "Gong API credentials not found in environment variables")

        self.client = httpx.AsyncClient(timeout=30.0)
        self.health_mode = os.environ.get("GONG_HEALTH_MODE", "strict")
        logger.info(
            f"Initialized Gong API client with health mode: {self.health_mode}")

    @backoff.on_exception(
        backoff.expo,
        (httpx.HTTPError, httpx.TimeoutException),
        max_tries=3,
        giveup=lambda e: isinstance(
            e, httpx.HTTPStatusError) and e.response.status_code < 500
    )
    async def _make_request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """
        Make a request to the Gong API with exponential backoff.

        Args:
            method: The HTTP method to use
            path: The path to make the request to
            **kwargs: Additional arguments to pass to the request

        Returns:
            The response from the API

        Raises:
            HTTPException: If the request fails
        """
        url = f"{self.base_url}{path}"
        headers = kwargs.pop("headers", {})
        headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_key}"
        })

        try:
            response = await self.client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error in Gong API request: {e.response.text}")
            status_code = e.response.status_code

            try:
                error_data = e.response.json()
                error_message = error_data.get("message", str(e))
            except json.JSONDecodeError:
                error_message = str(e)

            # Map error types
            if status_code == 401 or status_code == 403:
                error_type = "missing_api_key"
            elif 400 <= status_code < 500:
                error_type = "request_error"
            else:
                error_type = "upstream_error"

            raise HTTPException(
                status_code=status_code,
                detail={
                    "error_type": error_type,
                    "error": error_message
                }
            )
        except httpx.RequestError as e:
            logger.error(f"Request error in Gong API request: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error_type": "request_error",
                    "error": f"Failed to connect to Gong API: {str(e)}"
                }
            )

    async def get_call_transcript(self, call_id: str) -> Dict[str, Any]:
        """
        Retrieve a call transcript from the Gong API.

        Args:
            call_id: The ID of the call to retrieve the transcript for

        Returns:
            The call transcript
        """
        path = f"/calls/{call_id}/transcript"
        response = await self._make_request("GET", path)

        # Transform the response to match our schema
        try:
            transcript_data = response.get("data", {})
            # Process the raw data to match our schema
            return {
                "call_id": call_id,
                "title": transcript_data.get("title"),
                "date": transcript_data.get("date"),
                "duration": transcript_data.get("duration", 0),
                "participants": transcript_data.get("participants", []),
                "segments": transcript_data.get("segments", [])
            }
        except Exception as e:
            logger.error(f"Error processing transcript data: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error_type": "internal_error",
                    "error": f"Failed to process transcript data: {str(e)}"
                }
            )

    async def get_call_insights(self, call_id: str) -> List[Dict[str, Any]]:
        """
        Get insights for a specific call from the Gong API.

        Args:
            call_id: The ID of the call to get insights for

        Returns:
            A list of call insights
        """
        path = f"/calls/{call_id}/insights"
        response = await self._make_request("GET", path)
        return response.get("data", [])

    async def get_call_summary(self, call_id: str) -> Dict[str, Any]:
        """
        Get a summary of a specific call from the Gong API.

        Args:
            call_id: The ID of the call to summarize

        Returns:
            A summary of the call
        """
        path = f"/calls/{call_id}/summary"
        response = await self._make_request("GET", path)

        # Transform the response to match our schema
        summary_data = response.get("data", {})
        return {
            "call_id": call_id,
            "title": summary_data.get("title"),
            "date": summary_data.get("date"),
            "duration": summary_data.get("duration", 0),
            "summary_text": summary_data.get("summary", ""),
            "topics": summary_data.get("topics", []),
            "action_items": summary_data.get("action_items", []),
            "sentiment_score": summary_data.get("sentiment", None)
        }

    async def search_calls(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Search for calls matching the given query.

        Args:
            query: The search query
            limit: Maximum number of results to return

        Returns:
            Search results with pagination metadata
        """
        path = "/calls/search"
        params = {"query": query, "limit": limit}
        response = await self._make_request("GET", path, params=params)

        # Ensure pagination metadata is present
        results = response.get("data", [])
        meta = response.get("meta", {})
        if "has_more" not in meta:
            meta["has_more"] = False
        if "next_cursor" not in meta:
            meta["next_cursor"] = None

        return {
            "data": results,
            "meta": meta
        }

    async def health_check(self) -> Dict[str, str]:
        """
        Check the health of the Gong API.

        Returns:
            A dictionary with health status information
        """
        try:
            # Make a lightweight request to check API accessibility
            await self._make_request("GET", "/health")
            return {"status": "healthy"}
        except HTTPException as e:
            # Handle based on health mode
            if self.health_mode == "strict":
                # In strict mode, propagate the error
                raise e
            else:
                # In degraded mode, return 200 with degraded status
                logger.warning(
                    f"Gong API health check failed, reporting degraded: {str(e)}")
                return {"status": "degraded", "reason": str(e.detail)}


@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    logger.info("Starting Gong MCP server")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down Gong MCP server")


# Dependency to get the Gong API instance
def get_gong_api():
    """Get an instance of the Gong API client."""
    return GongAPI()


@router.get("/calls/{call_id}/transcript", response_model_exclude_none=True)
async def get_call_transcript(call_id: str, gong_api: GongAPI = Depends(get_gong_api)):
    """
    Retrieve the transcript for a specific call.

    Args:
        call_id: The ID of the call to retrieve the transcript for
        gong_api: The Gong API client

    Returns:
        The call transcript
    """
    try:
        transcript = await gong_api.get_call_transcript(call_id)
        return {"data": transcript}
    except Exception as e:
        logger.error(f"Error retrieving transcript: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": "upstream_error",
                "error": f"Failed to retrieve transcript: {str(e)}"
            }
        )


@router.get("/calls/{call_id}/insights", response_model_exclude_none=True)
async def get_call_insights(call_id: str, gong_api: GongAPI = Depends(get_gong_api)):
    """
    Get AI-generated insights for a specific call.

    Args:
        call_id: The ID of the call to get insights for
        gong_api: The Gong API client

    Returns:
        A list of call insights
    """
    try:
        insights = await gong_api.get_call_insights(call_id)
        return {"data": insights}
    except Exception as e:
        logger.error(f"Error retrieving insights: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": "upstream_error",
                "error": f"Failed to retrieve insights: {str(e)}"
            }
        )


@router.get("/calls/{call_id}/summary", response_model_exclude_none=True)
async def get_call_summary(call_id: str, gong_api: GongAPI = Depends(get_gong_api)):
    """
    Get a summary of a specific call.

    Args:
        call_id: The ID of the call to summarize
        gong_api: The Gong API client

    Returns:
        A summary of the call
    """
    try:
        summary = await gong_api.get_call_summary(call_id)
        return {"data": summary}
    except Exception as e:
        logger.error(f"Error retrieving summary: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": "upstream_error",
                "error": f"Failed to retrieve summary: {str(e)}"
            }
        )


@router.get("/calls/search", response_model_exclude_none=True)
async def search_calls(
    query: str,
    limit: int = Query(10, ge=1, le=100),
    gong_api: GongAPI = Depends(get_gong_api)
):
    """
    Search for calls matching the given query.

    Args:
        query: The search query
        limit: Maximum number of results to return (1-100)
        gong_api: The Gong API client

    Returns:
        Search results with pagination metadata
    """
    try:
        results = await gong_api.search_calls(query, limit)
        return results
    except Exception as e:
        logger.error(f"Error searching calls: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": "upstream_error",
                "error": f"Failed to search calls: {str(e)}"
            }
        )


@router.get("/health")
async def health_check(gong_api: GongAPI = Depends(get_gong_api)):
    """
    Check the health of the Gong MCP server and underlying Gong API.

    Args:
        gong_api: The Gong API client

    Returns:
        Health status information
    """
    try:
        start_time = time.time()
        health_status = await gong_api.health_check()
        response_time = time.time() - start_time

        health_status["response_time"] = round(response_time, 3)
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": "internal_error",
                "error": f"Health check failed: {str(e)}"
            }
        )


# Include the router in the app
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
