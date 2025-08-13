"""
Gong Client Shim

# DEPRECATED
This module provides backward compatibility for code that uses the old Gong client.
This is a temporary shim that redirects calls to the new MCP client.

This file will be removed once all consumers are migrated to the new MCP client.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Union

from libs.mcp_client.gong import GongMCPClient

logger = logging.getLogger(__name__)
logger.warning(
    "Using deprecated Gong client shim. Please update to use the MCP client directly.")


class GongClient:
    """
    Legacy Gong client that redirects calls to the new MCP client.

    # DEPRECATED
    This class provides backward compatibility for code that used the old direct Gong client.
    All methods are implemented in terms of the new MCP client.
    """

    def __init__(self, api_key: Optional[str] = None, client_secret: Optional[str] = None):
        """
        Initialize the legacy Gong client shim.

        Args:
            api_key: Ignored, for backward compatibility only
            client_secret: Ignored, for backward compatibility only
        """
        self._mcp_client = GongMCPClient()
        logger.warning(
            "Deprecated GongClient initialized. Update your code to use GongMCPClient from libs.mcp_client.gong"
        )

    # Helper method to run async methods in a synchronous context
    def _run_async(self, coro):
        """Run a coroutine in a synchronous context."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(coro)

    # Legacy method implementations

    def get_call_transcript(self, call_id: str) -> Dict[str, Any]:
        """
        Retrieve a call transcript.

        Args:
            call_id: The ID of the call

        Returns:
            The call transcript data
        """
        logger.warning(
            "Using deprecated get_call_transcript method. Update to MCP client.")
        return self._run_async(self._mcp_client.get_call_transcript(call_id)).dict()

    def get_call_insights(self, call_id: str) -> List[Dict[str, Any]]:
        """
        Get insights for a specific call.

        Args:
            call_id: The ID of the call

        Returns:
            A list of call insights
        """
        logger.warning(
            "Using deprecated get_call_insights method. Update to MCP client.")
        insights = self._run_async(self._mcp_client.get_call_insights(call_id))
        return [insight.dict() for insight in insights]

    def get_call_summary(self, call_id: str) -> Dict[str, Any]:
        """
        Get a summary of a specific call.

        Args:
            call_id: The ID of the call

        Returns:
            A summary of the call
        """
        logger.warning(
            "Using deprecated get_call_summary method. Update to MCP client.")
        return self._run_async(self._mcp_client.get_call_summary(call_id)).dict()

    def search_calls(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Search for calls matching the given query.

        Args:
            query: The search query
            limit: Maximum number of results

        Returns:
            Search results
        """
        logger.warning(
            "Using deprecated search_calls method. Update to MCP client.")
        return self._run_async(self._mcp_client.search_calls(query, limit))

    # Include any other legacy methods that might have existed in the old client
