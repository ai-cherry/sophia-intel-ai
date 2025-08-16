"""
Sales Coach Agent that leverages the Gong MCP client for call transcript analysis.

This agent provides sales coaching insights based on Gong call data.
"""

import logging
from typing import Optional

from agents.base_agent import BaseAgent
from libs.mcp_client.gong import GongMCPClient
from schemas.gong import MCPError as GongMCPError

logger = logging.getLogger(__name__)


class SalesCoachAgent(BaseAgent):
    """Agent that provides sales coaching insights using Gong call data via the MCP client."""

    def __init__(self, gong_mcp_base_url: str = "http://localhost:5001", *args, **kwargs):
        """
        Initialize the Sales Coach Agent with a Gong MCP client.

        Args:
            gong_mcp_base_url: Base URL for the Gong MCP server
        """
        super().__init__(*args, **kwargs)
        self._gong_client = GongMCPClient(base_url=gong_mcp_base_url)

    async def get_transcript(self, *, call_id: str):
        """
        Fetch call transcript via Gong MCP.

        Args:
            call_id: The ID of the call to retrieve the transcript for

        Returns:
            The call transcript

        Raises:
            GongMCPError: If there's an error retrieving the transcript
        """
        try:
            return await self._gong_client.get_call_transcript(call_id)
        except GongMCPError as e:
            # Pass through a structured failure for upstream handlers; keep
            # envelope discipline at API layer
            raise

    async def get_call_insights(self, call_id: str):
        """
        Get AI-generated insights for a specific call.

        Args:
            call_id: The ID of the call to get insights for

        Returns:
            A list of call insights

        Raises:
            GongMCPError: If there's an error retrieving the insights
        """
        try:
            return await self._gong_client.get_call_insights(call_id)
        except GongMCPError as e:
            raise

    async def get_call_summary(self, call_id: str):
        """
        Get a summary of a specific call.

        Args:
            call_id: The ID of the call to summarize

        Returns:
            A summary of the call

        Raises:
            GongMCPError: If there's an error retrieving the summary
        """
        try:
            return await self._gong_client.get_call_summary(call_id)
        except GongMCPError as e:
            raise

    async def search_calls(self, query: str, limit: Optional[int] = 10):
        """
        Search for calls matching the given query.

        Args:
            query: The search query
            limit: Maximum number of results to return

        Returns:
            Search results with pagination metadata

        Raises:
            GongMCPError: If there's an error searching calls
        """
        try:
            return await self._gong_client.search_calls(query, limit)
        except GongMCPError as e:
            raise

    async def close(self):
        """Close the client session."""
        await self._gong_client.close()
