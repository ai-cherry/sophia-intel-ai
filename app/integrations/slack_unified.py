"""
Slack Integration with Unified Configuration
Uses UnifiedConfigManager for all configuration
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import asyncio

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    from slack_sdk.socket_mode import SocketModeClient
    from slack_sdk.socket_mode.response import SocketModeResponse
    from slack_sdk.socket_mode.request import SocketModeRequest
    SLACK_SDK_AVAILABLE = True
except ImportError:
    SLACK_SDK_AVAILABLE = False
    WebClient = None
    SlackApiError = None
    SocketModeClient = None

from config.unified_manager import get_config_manager

logger = logging.getLogger(__name__)


@dataclass
class SlackChannel:
    """Slack channel information"""
    id: str
    name: str
    is_archived: bool
    num_members: int
    topic: Optional[str] = None
    purpose: Optional[str] = None


@dataclass
class SlackMessage:
    """Slack message"""
    channel: str
    text: str
    user: Optional[str] = None
    thread_ts: Optional[str] = None
    attachments: Optional[List[Dict]] = None


class UnifiedSlackClient:
    """Slack client using unified configuration"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.config = self.config_manager.get_integration_config("slack")
        
        if not SLACK_SDK_AVAILABLE:
            raise ImportError("slack_sdk not installed. Run: pip install slack-sdk")
        
        if not self.config.get("enabled"):
            raise ValueError("Slack integration is not enabled. Set SLACK_ENABLED=true")
        
        # Get tokens from config
        self.bot_token = self.config.get("bot_token")
        self.app_token = self.config.get("app_token")
        self.signing_secret = self.config.get("signing_secret")
        
        if not self.bot_token:
            raise ValueError("SLACK_BOT_TOKEN not configured")
        
        # Initialize clients
        self.web_client = WebClient(token=self.bot_token)
        self.socket_client = None
        
        if self.app_token:
            try:
                self.socket_client = SocketModeClient(
                    app_token=self.app_token,
                    web_client=self.web_client
                )
            except Exception as e:
                logger.warning(f"Could not initialize Socket Mode: {e}")
        
        logger.info("Unified Slack client initialized successfully")
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Slack connection and return auth info"""
        try:
            response = self.web_client.auth_test()
            return {
                "success": True,
                "team": response.get("team"),
                "team_id": response.get("team_id"),
                "user": response.get("user"),
                "user_id": response.get("user_id"),
                "bot_id": response.get("bot_id")
            }
        except SlackApiError as e:
            logger.error(f"Slack auth test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_channels(self, limit: int = 100) -> List[SlackChannel]:
        """List all channels"""
        try:
            response = self.web_client.conversations_list(
                limit=limit,
                exclude_archived=False
            )
            
            channels = []
            for channel in response.get("channels", []):
                channels.append(SlackChannel(
                    id=channel["id"],
                    name=channel["name"],
                    is_archived=channel.get("is_archived", False),
                    num_members=channel.get("num_members", 0),
                    topic=channel.get("topic", {}).get("value"),
                    purpose=channel.get("purpose", {}).get("value")
                ))
            
            return channels
            
        except SlackApiError as e:
            logger.error(f"Failed to list channels: {e}")
            return []
    
    async def send_message(self, channel: str, text: str, **kwargs) -> bool:
        """Send a message to a channel"""
        try:
            response = self.web_client.chat_postMessage(
                channel=channel,
                text=text,
                **kwargs
            )
            return response["ok"]
        except SlackApiError as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    async def get_channel_history(
        self, 
        channel: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get channel message history"""
        try:
            response = self.web_client.conversations_history(
                channel=channel,
                limit=limit
            )
            return response.get("messages", [])
        except SlackApiError as e:
            logger.error(f"Failed to get channel history: {e}")
            return []
    
    async def analyze_channel_health(self, channel_id: str) -> Dict[str, Any]:
        """Analyze channel health and activity"""
        try:
            # Get channel info
            info_response = self.web_client.conversations_info(channel=channel_id)
            channel_info = info_response.get("channel", {})
            
            # Get recent messages
            messages = await self.get_channel_history(channel_id, limit=50)
            
            # Calculate metrics
            is_active = len(messages) > 10
            avg_response_time = None  # Would need more complex analysis
            has_unanswered = self._check_unanswered_questions(messages)
            
            return {
                "channel_id": channel_id,
                "name": channel_info.get("name"),
                "is_archived": channel_info.get("is_archived", False),
                "member_count": channel_info.get("num_members", 0),
                "is_active": is_active,
                "message_count_recent": len(messages),
                "has_unanswered_questions": has_unanswered,
                "health_score": self._calculate_health_score(
                    is_active, 
                    has_unanswered,
                    channel_info.get("is_archived", False)
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze channel health: {e}")
            return {"error": str(e)}
    
    def _check_unanswered_questions(self, messages: List[Dict]) -> bool:
        """Check if there are unanswered questions"""
        for msg in messages:
            text = msg.get("text", "")
            # Simple heuristic: questions without replies
            if "?" in text and msg.get("reply_count", 0) == 0:
                return True
        return False
    
    def _calculate_health_score(
        self, 
        is_active: bool, 
        has_unanswered: bool,
        is_archived: bool
    ) -> int:
        """Calculate channel health score (0-100)"""
        if is_archived:
            return 0
        
        score = 50
        if is_active:
            score += 30
        if not has_unanswered:
            score += 20
        
        return min(100, score)
    
    async def get_team_activity_summary(self) -> Dict[str, Any]:
        """Get overall team activity summary"""
        try:
            channels = await self.list_channels()
            
            active_channels = [c for c in channels if not c.is_archived]
            total_members = sum(c.num_members for c in active_channels)
            
            # Identify potential issues
            issues = []
            for channel in active_channels:
                if channel.num_members == 0:
                    issues.append(f"Empty channel: #{channel.name}")
                elif channel.num_members > 100:
                    issues.append(f"Large channel (may need moderation): #{channel.name}")
            
            return {
                "total_channels": len(channels),
                "active_channels": len(active_channels),
                "archived_channels": len(channels) - len(active_channels),
                "total_members": total_members,
                "avg_members_per_channel": total_members / len(active_channels) if active_channels else 0,
                "potential_issues": issues
            }
            
        except Exception as e:
            logger.error(f"Failed to get team activity summary: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """Clean up resources"""
        if self.socket_client:
            try:
                self.socket_client.close()
            except:
                pass


# Backward compatibility wrapper
class SlackClient(UnifiedSlackClient):
    """Alias for backward compatibility"""
    pass


# Helper function for quick access
def get_slack_client() -> UnifiedSlackClient:
    """Get or create a Slack client instance"""
    return UnifiedSlackClient()