"""
Gong MCP Client

This client provides a typed interface for interacting with the Gong MCP server.
"""

import httpx
import logging
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin

from schemas.gong import (
    CallTranscript,
    CallInsight,
    CallSummary,
    MCPError
)

logger = logging.getLogger(__name__)


class GongMCPClient:
    """Client for interacting with the Gong MCP server."""

    def __init__(self, base_url: str = "http://localhost:5001"):
        """
        Initialize the Gong MCP client.

        Args:
            base_url: The base URL of the Gong MCP server
        """
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.debug(f"Initialized Gong MCP client with base URL: {base_url}")

    async def _make_request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """
        Make a request to the Gong MCP server.

        Args:
            method: The HTTP method to use
            path: The path to make the request to
            **kwargs: Additional arguments to pass to the request

        Returns:
            The response from the server

        Raises:
            MCPError: If the request fails
        """
        url = urljoin(self.base_url, path)
        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.headers.get(
                "content-type") == "application/json" else {}
            error_type = error_data.get("error_type", "upstream_error")
            error_message = error_data.get("error", str(e))
            logger.error(f"HTTP error in Gong MCP request: {error_message}")
            raise MCPError(
                error_type=error_type,
                message=error_message,
                status_code=e.response.status_code
            )
        except httpx.RequestError as e:
            logger.error(f"Request error in Gong MCP request: {str(e)}")
            raise MCPError(
                error_type="request_error",
                message=f"Failed to connect to Gong MCP server: {str(e)}",
                status_code=500
            )
        except Exception as e:
            logger.error(f"Unexpected error in Gong MCP request: {str(e)}")
            raise MCPError(
                error_type="internal_error",
                message=f"Unexpected error: {str(e)}",
                status_code=500
            )

    async def get_call_transcript(self, call_id: str) -> CallTranscript:
        """
        Retrieve a call transcript.

        Args:
            call_id: The ID of the call to retrieve the transcript for

        Returns:
            The call transcript
        """
        path = f"/calls/{call_id}/transcript"
        response = await self._make_request("GET", path)
        return CallTranscript(**response.get("data", {}))

    async def get_call_insights(self, call_id: str) -> List[CallInsight]:
        """
        Get AI-generated insights for a specific call.

        Args:
            call_id: The ID of the call to get insights for

        Returns:
            A list of call insights
        """
        path = f"/calls/{call_id}/insights"
        response = await self._make_request("GET", path)
        insights = response.get("data", [])
        return [CallInsight(**insight) for insight in insights]

    async def get_call_summary(self, call_id: str) -> CallSummary:
        """
        Get a summary of a specific call.

        Args:
            call_id: The ID of the call to summarize

        Returns:
            A summary of the call
        """
        path = f"/calls/{call_id}/summary"
        response = await self._make_request("GET", path)
        return CallSummary(**response.get("data", {}))

    async def search_calls(self, query: str, limit: Optional[int] = 10) -> Dict[str, Any]:
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
        return await self._make_request("GET", path, params=params)

    async def health_check(self) -> Dict[str, str]:
        """
        Check the health of the Gong MCP server.

        Returns:
            A dictionary with health status information
        """
        path = "/health"
        return await self._make_request("GET", path)

    async def close(self) -> None:
        """Close the client session."""
        if self.client:
            await self.client.aclose()
