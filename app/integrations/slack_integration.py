"""
Slack API Integration Client

Provides comprehensive Slack integration for Sophia Intelligence Platform.
Supports messaging, channel management, user interactions, and workspace operations.
"""

import json
import logging
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Optional

try:
    import aiohttp
    import httpx

    HTTP_CLIENT_AVAILABLE = True
except ImportError as e:
    aiohttp = None
    httpx = None
    HTTP_CLIENT_AVAILABLE = False
    HTTP_IMPORT_ERROR = str(e)


logger = logging.getLogger(__name__)

# Provide a safe default for INTEGRATIONS if not imported from a central config
try:  # noqa: SIM105
    INTEGRATIONS  # type: ignore[name-defined]
except NameError:  # pragma: no cover - runtime guard
    INTEGRATIONS = {}


class SlackMessageType(Enum):
    """Types of Slack messages"""

    TEXT = "text"
    RICH_TEXT = "rich_text"
    ATTACHMENT = "attachment"
    BLOCK = "blocks"


class SlackChannelType(Enum):
    """Types of Slack channels"""

    PUBLIC = "public_channel"
    PRIVATE = "private_channel"
    IM = "im"
    MPIM = "mpim"
    GROUP = "group"


@dataclass
class SlackChannel:
    """Slack channel information"""

    id: str
    name: str
    is_private: bool
    is_member: bool
    topic: Optional[str] = None
    purpose: Optional[str] = None
    num_members: Optional[int] = None
    created: Optional[int] = None


@dataclass
class SlackUser:
    """Slack user information"""

    id: str
    name: str
    real_name: Optional[str] = None
    display_name: Optional[str] = None
    email: Optional[str] = None
    is_bot: bool = False
    is_admin: bool = False
    is_owner: bool = False
    profile_image: Optional[str] = None


@dataclass
class SlackMessage:
    """Slack message data"""

    channel: str
    text: str
    user: Optional[str] = None
    timestamp: Optional[str] = None
    thread_ts: Optional[str] = None
    message_type: SlackMessageType = SlackMessageType.TEXT
    attachments: Optional[list[dict[str, Any]]] = None
    blocks: Optional[list[dict[str, Any]]] = None


class SlackIntegrationError(Exception):
    """Custom exception for Slack integration errors"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        response_data: Optional[dict] = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.response_data = response_data


class SlackClient:
    """
    Slack API Client for Sophia Intelligence Platform

    Handles all Slack API interactions including messaging, channel management,
    user operations, and workspace administration.
    """

    def __init__(self):
        """Initialize the Slack client with configuration from integrations_config"""
        if not HTTP_CLIENT_AVAILABLE:
            raise SlackIntegrationError(
                f"HTTP client libraries not available: {HTTP_IMPORT_ERROR}. "
                "Please install: pip install aiohttp httpx"
            )

        self.config = INTEGRATIONS.get("slack", {})
        if not self.config.get("enabled", False):
            raise SlackIntegrationError(
                f"Slack integration is not enabled. Status: {self.config.get('status', 'unknown')}"
            )

        self.bot_token = self.config.get("bot_token")
        self.app_token = self.config.get("app_token")
        self.client_id = self.config.get("client_id")
        self.client_secret = self.config.get("client_secret")
        self.signing_secret = self.config.get("signing_secret")

        if not self.bot_token:
            raise SlackIntegrationError(
                "Slack bot token is required but not found in configuration"
            )

        self.base_url = "https://slack.com/api"
        self.headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json; charset=utf-8",
        }

        logger.info("Slack client initialized successfully")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Make an authenticated request to the Slack API"""
        url = f"{self.base_url}/{endpoint}"

        try:
            async with httpx.AsyncClient() as client:
                if method.upper() == "GET":
                    response = await client.get(
                        url, headers=self.headers, params=params
                    )
                elif method.upper() == "POST":
                    response = await client.post(url, headers=self.headers, json=data)
                else:
                    raise SlackIntegrationError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                result = response.json()

                # Check if Slack API returned an error
                if not result.get("ok", False):
                    error_msg = result.get("error", "Unknown Slack API error")
                    error_details = result.get("response_metadata", {})

                    # Handle specific error cases
                    if error_msg == "account_inactive":
                        raise SlackIntegrationError(
                            "Slack account is inactive. Please check your Slack workspace status and bot permissions.",
                            error_code=error_msg,
                            response_data=result,
                        )
                    elif error_msg == "invalid_auth":
                        raise SlackIntegrationError(
                            "Invalid authentication token. Please check your bot token configuration.",
                            error_code=error_msg,
                            response_data=result,
                        )
                    elif error_msg == "missing_scope":
                        raise SlackIntegrationError(
                            f"Missing required scope. Details: {error_details}",
                            error_code=error_msg,
                            response_data=result,
                        )
                    else:
                        raise SlackIntegrationError(
                            f"Slack API error: {error_msg}",
                            error_code=error_msg,
                            response_data=result,
                        )

                return result

        except httpx.HTTPError as e:
            raise SlackIntegrationError(
                f"HTTP error during Slack API request: {str(e)}"
            )
        except json.JSONDecodeError as e:
            raise SlackIntegrationError(
                f"Failed to decode Slack API response: {str(e)}"
            )

    async def test_connection(self) -> dict[str, Any]:
        """Test the Slack API connection and return auth information"""
        try:
            result = await self._make_request("GET", "auth.test")
            return {
                "success": True,
                "team": result.get("team"),
                "team_id": result.get("team_id"),
                "user": result.get("user"),
                "user_id": result.get("user_id"),
                "bot_id": result.get("bot_id"),
            }
        except SlackIntegrationError as e:
            return {
                "success": False,
                "error": str(e),
                "error_code": e.error_code,
                "response_data": e.response_data,
            }

    async def send_message(
        self,
        channel: str,
        text: str,
        thread_ts: Optional[str] = None,
        blocks: Optional[list[dict[str, Any]]] = None,
        attachments: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """Send a message to a Slack channel"""
        data = {"channel": channel, "text": text}

        if thread_ts:
            data["thread_ts"] = thread_ts
        if blocks:
            data["blocks"] = blocks
        if attachments:
            data["attachments"] = attachments

        try:
            result = await self._make_request("POST", "chat.postMessage", data=data)
            return {
                "success": True,
                "message_ts": result.get("ts"),
                "channel": result.get("channel"),
                "message": result.get("message", {}),
            }
        except SlackIntegrationError as e:
            return {
                "success": False,
                "error": str(e),
                "error_code": e.error_code,
                "response_data": e.response_data,
            }

    async def update_message(
        self,
        channel: str,
        ts: str,
        text: str,
        blocks: Optional[list[dict[str, Any]]] = None,
        attachments: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """Update an existing message"""
        data = {"channel": channel, "ts": ts, "text": text}

        if blocks:
            data["blocks"] = blocks
        if attachments:
            data["attachments"] = attachments

        try:
            result = await self._make_request("POST", "chat.update", data=data)
            return {
                "success": True,
                "message_ts": result.get("ts"),
                "channel": result.get("channel"),
                "message": result.get("message", {}),
            }
        except SlackIntegrationError as e:
            return {"success": False, "error": str(e), "error_code": e.error_code}

    async def delete_message(self, channel: str, ts: str) -> dict[str, Any]:
        """Delete a message"""
        data = {"channel": channel, "ts": ts}

        try:
            result = await self._make_request("POST", "chat.delete", data=data)
            return {
                "success": True,
                "channel": result.get("channel"),
                "ts": result.get("ts"),
            }
        except SlackIntegrationError as e:
            return {"success": False, "error": str(e), "error_code": e.error_code}

    async def list_channels(
        self, exclude_archived: bool = True, types: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """List channels in the workspace"""
        params = {}
        if exclude_archived:
            params["exclude_archived"] = "true"
        if types:
            params["types"] = ",".join(types)
        else:
            params["types"] = "public_channel,private_channel"

        try:
            result = await self._make_request(
                "GET", "conversations.list", params=params
            )
            channels = []
            for channel_data in result.get("channels", []):
                channel = SlackChannel(
                    id=channel_data.get("id"),
                    name=channel_data.get("name"),
                    is_private=channel_data.get("is_private", False),
                    is_member=channel_data.get("is_member", False),
                    topic=channel_data.get("topic", {}).get("value"),
                    purpose=channel_data.get("purpose", {}).get("value"),
                    num_members=channel_data.get("num_members"),
                    created=channel_data.get("created"),
                )
                channels.append(asdict(channel))

            return {"success": True, "channels": channels, "total": len(channels)}
        except SlackIntegrationError as e:
            return {"success": False, "error": str(e), "error_code": e.error_code}

    async def get_channel_info(self, channel: str) -> dict[str, Any]:
        """Get information about a specific channel"""
        params = {"channel": channel}

        try:
            result = await self._make_request(
                "GET", "conversations.info", params=params
            )
            channel_data = result.get("channel", {})

            channel_info = SlackChannel(
                id=channel_data.get("id"),
                name=channel_data.get("name"),
                is_private=channel_data.get("is_private", False),
                is_member=channel_data.get("is_member", False),
                topic=channel_data.get("topic", {}).get("value"),
                purpose=channel_data.get("purpose", {}).get("value"),
                num_members=channel_data.get("num_members"),
                created=channel_data.get("created"),
            )

            return {"success": True, "channel": asdict(channel_info)}
        except SlackIntegrationError as e:
            return {"success": False, "error": str(e), "error_code": e.error_code}

    async def list_users(self) -> dict[str, Any]:
        """List users in the workspace"""
        try:
            result = await self._make_request("GET", "users.list")
            users = []
            for user_data in result.get("members", []):
                if user_data.get("deleted", False):
                    continue  # Skip deleted users

                profile = user_data.get("profile", {})
                user = SlackUser(
                    id=user_data.get("id"),
                    name=user_data.get("name"),
                    real_name=user_data.get("real_name") or profile.get("real_name"),
                    display_name=profile.get("display_name"),
                    email=profile.get("email"),
                    is_bot=user_data.get("is_bot", False),
                    is_admin=user_data.get("is_admin", False),
                    is_owner=user_data.get("is_owner", False),
                    profile_image=profile.get("image_192"),
                )
                users.append(asdict(user))

            return {"success": True, "users": users, "total": len(users)}
        except SlackIntegrationError as e:
            return {"success": False, "error": str(e), "error_code": e.error_code}

    async def get_user_info(self, user: str) -> dict[str, Any]:
        """Get information about a specific user"""
        params = {"user": user}

        try:
            result = await self._make_request("GET", "users.info", params=params)
            user_data = result.get("user", {})
            profile = user_data.get("profile", {})

            user_info = SlackUser(
                id=user_data.get("id"),
                name=user_data.get("name"),
                real_name=user_data.get("real_name") or profile.get("real_name"),
                display_name=profile.get("display_name"),
                email=profile.get("email"),
                is_bot=user_data.get("is_bot", False),
                is_admin=user_data.get("is_admin", False),
                is_owner=user_data.get("is_owner", False),
                profile_image=profile.get("image_192"),
            )

            return {"success": True, "user": asdict(user_info)}
        except SlackIntegrationError as e:
            return {"success": False, "error": str(e), "error_code": e.error_code}

    async def get_conversation_history(
        self,
        channel: str,
        limit: int = 100,
        oldest: Optional[str] = None,
        latest: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get conversation history from a channel"""
        params = {"channel": channel, "limit": limit}
        if oldest:
            params["oldest"] = oldest
        if latest:
            params["latest"] = latest

        try:
            result = await self._make_request(
                "GET", "conversations.history", params=params
            )
            messages = result.get("messages", [])

            return {
                "success": True,
                "messages": messages,
                "has_more": result.get("has_more", False),
                "response_metadata": result.get("response_metadata", {}),
            }
        except SlackIntegrationError as e:
            return {"success": False, "error": str(e), "error_code": e.error_code}

    async def join_channel(self, channel: str) -> dict[str, Any]:
        """Join a channel"""
        data = {"channel": channel}

        try:
            result = await self._make_request("POST", "conversations.join", data=data)
            return {"success": True, "channel": result.get("channel", {})}
        except SlackIntegrationError as e:
            return {"success": False, "error": str(e), "error_code": e.error_code}

    async def leave_channel(self, channel: str) -> dict[str, Any]:
        """Leave a channel"""
        data = {"channel": channel}

        try:
            await self._make_request("POST", "conversations.leave", data=data)
            return {"success": True}
        except SlackIntegrationError as e:
            return {"success": False, "error": str(e), "error_code": e.error_code}


# Convenience functions for quick operations
async def send_slack_message(channel: str, text: str, **kwargs) -> dict[str, Any]:
    """Convenience function to send a Slack message"""
    try:
        client = SlackClient()
        return await client.send_message(channel, text, **kwargs)
    except SlackIntegrationError as e:
        return {
            "success": False,
            "error": str(e),
            "error_code": getattr(e, "error_code", None),
        }


async def test_slack_connection() -> dict[str, Any]:
    """Convenience function to test Slack connection"""
    try:
        client = SlackClient()
        return await client.test_connection()
    except SlackIntegrationError as e:
        return {
            "success": False,
            "error": str(e),
            "error_code": getattr(e, "error_code", None),
        }


async def get_slack_channels() -> dict[str, Any]:
    """Convenience function to get Slack channels"""
    try:
        client = SlackClient()
        return await client.list_channels()
    except SlackIntegrationError as e:
        return {
            "success": False,
            "error": str(e),
            "error_code": getattr(e, "error_code", None),
        }
