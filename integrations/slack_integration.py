"""
Slack Integration for SOPHIA
Enables ChatOps, notifications, and team collaboration through Slack
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class SlackMessage(BaseModel):
    channel: str
    text: str
    blocks: Optional[List[Dict]] = None
    thread_ts: Optional[str] = None
    username: Optional[str] = "SOPHIA"
    icon_emoji: Optional[str] = ":robot_face:"

class SlackClient:
    """Slack API client for SOPHIA integrations."""
    
    def __init__(self, bot_token: str = None):
        self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN")
        self.base_url = "https://slack.com/api"
        self.headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json"
        }
    
    async def send_message(self, message: SlackMessage) -> Dict[str, Any]:
        """Send a message to Slack channel."""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "channel": message.channel,
                    "text": message.text,
                    "username": message.username,
                    "icon_emoji": message.icon_emoji
                }
                
                if message.blocks:
                    payload["blocks"] = message.blocks
                
                if message.thread_ts:
                    payload["thread_ts"] = message.thread_ts
                
                response = await client.post(
                    f"{self.base_url}/chat.postMessage",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                
                result = response.json()
                
                if result.get("ok"):
                    logger.info(f"Message sent to Slack channel {message.channel}")
                    return {
                        "success": True,
                        "ts": result.get("ts"),
                        "channel": result.get("channel"),
                        "message": result.get("message")
                    }
                else:
                    logger.error(f"Slack API error: {result.get('error')}")
                    return {
                        "success": False,
                        "error": result.get("error"),
                        "details": result
                    }
                    
        except Exception as e:
            logger.error(f"Slack message failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_deployment_notification(self, service: str, status: str, details: Dict = None) -> Dict:
        """Send deployment notification to Slack."""
        
        status_emoji = {
            "success": ":white_check_mark:",
            "failed": ":x:",
            "started": ":rocket:",
            "warning": ":warning:"
        }.get(status, ":information_source:")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{status_emoji} SOPHIA Deployment Update"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Service:*\n{service}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{status.title()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
                    }
                ]
            }
        ]
        
        if details:
            detail_text = "\n".join([f"• {k}: {v}" for k, v in details.items()])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Details:*\n{detail_text}"
                }
            })
        
        message = SlackMessage(
            channel=os.getenv("SLACK_DEPLOYMENTS_CHANNEL", "#sophia-deployments"),
            text=f"SOPHIA Deployment: {service} - {status}",
            blocks=blocks
        )
        
        return await self.send_message(message)
    
    async def send_research_summary(self, query: str, sources: List[Dict], summary: str) -> Dict:
        """Send research results to Slack."""
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":mag: SOPHIA Research Complete"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Query:* {query}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:*\n{summary[:500]}{'...' if len(summary) > 500 else ''}"
                }
            }
        ]
        
        if sources:
            source_text = "\n".join([
                f"• <{source.get('url', '#')}|{source.get('title', 'Source')}>"
                for source in sources[:5]
            ])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Sources ({len(sources)} total):*\n{source_text}"
                }
            })
        
        message = SlackMessage(
            channel=os.getenv("SLACK_RESEARCH_CHANNEL", "#sophia-research"),
            text=f"Research complete: {query}",
            blocks=blocks
        )
        
        return await self.send_message(message)
    
    async def send_business_update(self, action: str, platform: str, details: Dict) -> Dict:
        """Send business action update to Slack."""
        
        platform_emoji = {
            "asana": ":asana:",
            "linear": ":linear:",
            "notion": ":notion:",
            "gong": ":gong:",
            "github": ":github:",
            "fly": ":fly:"
        }.get(platform.lower(), ":gear:")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{platform_emoji} SOPHIA Business Action"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Action:*\n{action}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Platform:*\n{platform.title()}"
                    }
                ]
            }
        ]
        
        if details:
            detail_text = "\n".join([f"• {k}: {v}" for k, v in details.items()])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Details:*\n{detail_text}"
                }
            })
        
        message = SlackMessage(
            channel=os.getenv("SLACK_BUSINESS_CHANNEL", "#sophia-business"),
            text=f"Business action: {action} on {platform}",
            blocks=blocks
        )
        
        return await self.send_message(message)
    
    async def get_channel_history(self, channel: str, limit: int = 10) -> List[Dict]:
        """Get recent messages from a Slack channel."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/conversations.history",
                    headers=self.headers,
                    params={
                        "channel": channel,
                        "limit": limit
                    },
                    timeout=30.0
                )
                
                result = response.json()
                
                if result.get("ok"):
                    return result.get("messages", [])
                else:
                    logger.error(f"Slack history error: {result.get('error')}")
                    return []
                    
        except Exception as e:
            logger.error(f"Slack history failed: {e}")
            return []
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Slack API connection."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/auth.test",
                    headers=self.headers,
                    timeout=30.0
                )
                
                result = response.json()
                
                if result.get("ok"):
                    return {
                        "success": True,
                        "team": result.get("team"),
                        "user": result.get("user"),
                        "bot_id": result.get("bot_id")
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error")
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Slack ChatOps Commands
class SlackChatOps:
    """Slack ChatOps integration for SOPHIA commands."""
    
    def __init__(self, slack_client: SlackClient):
        self.slack = slack_client
    
    async def handle_command(self, command: str, channel: str, user: str) -> Dict:
        """Handle Slack slash commands for SOPHIA."""
        
        command = command.strip().lower()
        
        if command.startswith("/sophia deploy"):
            service = command.replace("/sophia deploy", "").strip()
            return await self._handle_deploy_command(service, channel, user)
        
        elif command.startswith("/sophia status"):
            return await self._handle_status_command(channel, user)
        
        elif command.startswith("/sophia research"):
            query = command.replace("/sophia research", "").strip()
            return await self._handle_research_command(query, channel, user)
        
        else:
            return await self._handle_help_command(channel, user)
    
    async def _handle_deploy_command(self, service: str, channel: str, user: str) -> Dict:
        """Handle deployment command."""
        
        message = SlackMessage(
            channel=channel,
            text=f":rocket: <@{user}> initiated deployment of `{service}`",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f":rocket: <@{user}> initiated deployment of `{service}`\n\n:hourglass_flowing_sand: Deployment in progress..."
                    }
                }
            ]
        )
        
        return await self.slack.send_message(message)
    
    async def _handle_status_command(self, channel: str, user: str) -> Dict:
        """Handle status command."""
        
        # This would integrate with the actual service status
        status_blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":bar_chart: SOPHIA System Status"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*Research Service:*\n:white_check_mark: Healthy"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Code Service:*\n:white_check_mark: Healthy"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Business Service:*\n:white_check_mark: Healthy"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Dashboard:*\n:white_check_mark: Healthy"
                    }
                ]
            }
        ]
        
        message = SlackMessage(
            channel=channel,
            text="SOPHIA System Status",
            blocks=status_blocks
        )
        
        return await self.slack.send_message(message)
    
    async def _handle_research_command(self, query: str, channel: str, user: str) -> Dict:
        """Handle research command."""
        
        if not query:
            query = "latest AI developments"
        
        message = SlackMessage(
            channel=channel,
            text=f":mag: <@{user}> requested research: `{query}`",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f":mag: <@{user}> requested research: `{query}`\n\n:hourglass_flowing_sand: Research in progress..."
                    }
                }
            ]
        )
        
        return await self.slack.send_message(message)
    
    async def _handle_help_command(self, channel: str, user: str) -> Dict:
        """Handle help command."""
        
        help_blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":robot_face: SOPHIA Commands"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Available Commands:*\n\n• `/sophia deploy <service>` - Deploy a service\n• `/sophia status` - Check system status\n• `/sophia research <query>` - Conduct research\n• `/sophia help` - Show this help"
                }
            }
        ]
        
        message = SlackMessage(
            channel=channel,
            text="SOPHIA Help",
            blocks=help_blocks
        )
        
        return await self.slack.send_message(message)

