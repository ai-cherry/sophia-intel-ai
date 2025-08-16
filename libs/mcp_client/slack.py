"""
Slack-specific MCP Client
Implements Slack-specific features while following the standardized interface
"""

import os
import time
from typing import Any, Dict, List, Optional

from libs.mcp_client.base_client import BaseMCPClient, MCPServiceConfig


class SlackClient(BaseMCPClient):
    """
    Slack MCP Client with service-specific features

    Features:
    - Workspace-aware context storage
    - Channel and thread-specific search
    - Message posting through Swarm
    - Real-time event handling
    """

    def __init__(self, service_name: str = "slack", config: Optional[MCPServiceConfig] = None):
        super().__init__(service_name, config)
        self.workspace_id = os.getenv("SLACK_WORKSPACE_ID")

    def _get_service_filters(self, filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Get Slack-specific search filters"""
        slack_filters = {}

        if filters:
            if "workspace_id" in filters:
                slack_filters["workspace_id"] = filters["workspace_id"]
            elif self.workspace_id:
                slack_filters["workspace_id"] = self.workspace_id

            if "channel_id" in filters:
                slack_filters["channel_id"] = filters["channel_id"]
            if "date_from" in filters:
                slack_filters["date_from"] = filters["date_from"]
            if "date_to" in filters:
                slack_filters["date_to"] = filters["date_to"]
        elif self.workspace_id:
            slack_filters["workspace_id"] = self.workspace_id

        return slack_filters

    def _get_context_fields(self) -> Dict[str, Any]:
        """Get Slack-specific context fields"""
        fields = {}

        if self.workspace_id:
            fields["workspace_id"] = self.workspace_id

        # Could add channel_id, user_id, thread_ts if available in context
        return fields

    async def send_message_to_channel(
        self, channel: str, text: str, thread_ts: Optional[str] = None, blocks: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """Send message to Slack channel through Swarm integration"""
        payload = {
            "channel": channel,
            "text": text,
            "swarm_stage": self.swarm_stage or "unknown",
            "session_id": self.session_id or f"manual_{int(time.time())}",
        }

        if thread_ts:
            payload["thread_ts"] = thread_ts
        if blocks:
            payload["blocks"] = blocks

        return await self.execute_swarm_action("send_message", payload)

    async def extract_conversation_context(
        self, channel_id: str, thread_ts: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Extract conversation context for Swarm analysis"""
        payload = {
            "channel_id": channel_id,
            "workspace_id": self.workspace_id,
            "session_id": self.session_id,
            "swarm_stage": self.swarm_stage,
        }

        if thread_ts:
            payload["thread_ts"] = thread_ts

        return await self.execute_swarm_action("extract_context", payload)

    async def get_channel_history(
        self, channel_id: str, limit: int = 100, cursor: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get Slack channel history"""
        try:
            params = {"limit": limit}
            if cursor:
                params["cursor"] = cursor

            response = await self._make_request("GET", f"/slack/channels/{channel_id}/history", params)
            return response
        except Exception:
            return None

    async def list_workspaces(self) -> Optional[Dict[str, Any]]:
        """List available Slack workspaces"""
        try:
            response = await self._make_request("GET", "/slack/workspaces/list")
            return response
        except Exception:
            return None

    # Backward compatibility methods for existing Swarm system

    def code_map(self, paths: List[str]) -> Dict[str, Any]:
        """Backward compatibility - Slack doesn't have code mapping"""
        return {"message": "Code mapping not available for Slack"}

    def next_actions(self, tool_name: str, context: str = "", swarm_stage: Optional[str] = None) -> Dict[str, Any]:
        """Suggest next actions based on Slack context"""
        # This could analyze recent Slack activity and suggest actions
        return {
            "suggestions": [
                "Check for unread messages in active channels",
                "Review thread conversations for decisions",
                "Send status updates to relevant channels",
            ],
            "context": "slack_activity_analysis",
        }

    def learn(self, event: Dict[str, Any]) -> None:
        """Learn from Slack events (synchronous for backward compatibility)"""
        try:
            # Store learning event - we'll handle this synchronously for compatibility
            # In a real implementation, this could queue the event for async processing
            pass
        except Exception:
            pass  # Don't fail on learning errors
