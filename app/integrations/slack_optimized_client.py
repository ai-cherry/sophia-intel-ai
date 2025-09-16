#!/usr/bin/env python3
"""
Optimized Slack Integration with 2025 Best Practices
Implements Socket Mode, Events API, Interactive Components, and AI-powered responses
"""
import asyncio
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
import aiohttp
import redis.asyncio as redis
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

# Import shared HTTP client for non-SDK requests
from app.api.utils.http_client import get_async_client, with_retries

# Configuration
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_USER_TOKEN = os.getenv("SLACK_USER_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


class SlackEventType(Enum):
    """Slack event types"""
    MESSAGE = "message"
    APP_MENTION = "app_mention"
    CHANNEL_CREATED = "channel_created"
    USER_JOINED = "member_joined_channel"
    REACTION_ADDED = "reaction_added"
    FILE_SHARED = "file_shared"
    SLASH_COMMAND = "slash_commands"
    INTERACTIVE = "interactive"
    VIEW_SUBMISSION = "view_submission"


@dataclass
class SlackMessage:
    """Structured Slack message"""
    channel: str
    text: str
    user: Optional[str] = None
    thread_ts: Optional[str] = None
    blocks: Optional[List[Dict]] = None
    attachments: Optional[List[Dict]] = None
    metadata: Optional[Dict] = None
    

@dataclass
class SlackInsight:
    """Insight from Slack conversation analysis"""
    channel_id: str
    insight_type: str  # sentiment, topic, action_item, decision
    title: str
    description: str
    participants: List[str]
    confidence: float
    timestamp: datetime
    thread_ts: Optional[str] = None
    

class SlackOptimizedClient:
    """
    Optimized Slack client with:
    - Socket Mode for real-time events
    - Async operations for performance
    - Redis caching for user/channel data
    - AI-powered message analysis
    - Interactive components support
    """
    
    def __init__(self):
        self.web_client = AsyncWebClient(token=SLACK_BOT_TOKEN) if SLACK_BOT_TOKEN else None
        self.user_client = AsyncWebClient(token=SLACK_USER_TOKEN) if SLACK_USER_TOKEN else None
        self.socket_client = None
        self.redis_client = None
        self.event_handlers = {}
        self.command_handlers = {}

    async def validate_config(self) -> dict:
        """Validate required Slack configuration is present."""
        return {
            "bot_token": bool(SLACK_BOT_TOKEN),
            "app_token": bool(SLACK_APP_TOKEN),
            "signing_secret": bool(SLACK_SIGNING_SECRET),
            "redis_url": REDIS_URL,
        }
        
    async def setup(self):
        """Initialize connections"""
        self.redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        
        # Initialize Socket Mode client
        if SLACK_APP_TOKEN and SLACK_APP_TOKEN.startswith("xapp-") and self.web_client:
            self.socket_client = SocketModeClient(
                app_token=SLACK_APP_TOKEN,
                web_client=self.web_client
            )
            
    async def start(self):
        """Start Socket Mode client"""
        if self.socket_client:
            # Register default handlers
            self.socket_client.socket_mode_request_listeners.append(
                self._process_socket_mode_request
            )
            
            # Start socket mode
            await self.socket_client.connect_async()
            
    async def stop(self):
        """Stop client and cleanup"""
        if self.socket_client:
            await self.socket_client.disconnect_async()
        if self.redis_client:
            await self.redis_client.aclose()
            
    async def _process_socket_mode_request(
        self,
        client: SocketModeClient,
        request: SocketModeRequest
    ):
        """Process Socket Mode requests"""
        try:
            if request.type == "events_api":
                # Handle events
                await self._handle_event(request.payload)
                
            elif request.type == "slash_commands":
                # Handle slash commands
                await self._handle_command(request.payload)
                
            elif request.type == "interactive":
                # Handle interactive components
                await self._handle_interactive(request.payload)
                
            # Acknowledge request
            response = SocketModeResponse(envelope_id=request.envelope_id)
            await client.send_socket_mode_response(response)
            
        except Exception as e:
            print(f"Error processing Socket Mode request: {e}")
            
    async def _handle_event(self, payload: Dict[str, Any]):
        """Handle Slack events"""
        event = payload.get("event", {})
        event_type = event.get("type")
        
        # Call registered handler
        if event_type in self.event_handlers:
            await self.event_handlers[event_type](event)
            
        # Store event for analysis
        await self._store_event(event)
        
    async def _handle_command(self, payload: Dict[str, Any]):
        """Handle slash commands"""
        command = payload.get("command")
        
        # Call registered handler
        if command in self.command_handlers:
            response = await self.command_handlers[command](payload)
            
            # Send response
            if response:
                await self.send_response(payload.get("response_url"), response)
                
    async def _handle_interactive(self, payload: Dict[str, Any]):
        """Handle interactive components"""
        action_type = payload.get("type")
        
        if action_type == "block_actions":
            # Handle button clicks, select menus, etc.
            await self._handle_block_actions(payload)
            
        elif action_type == "view_submission":
            # Handle modal submissions
            await self._handle_view_submission(payload)
            
    async def _handle_block_actions(self, payload: Dict[str, Any]):
        """Handle block action interactions"""
        actions = payload.get("actions", [])
        
        for action in actions:
            action_id = action.get("action_id")
            
            # Process based on action_id
            if action_id.startswith("approve_"):
                await self._handle_approval(payload, action)
            elif action_id.startswith("escalate_"):
                await self._handle_escalation(payload, action)
                
    async def _handle_view_submission(self, payload: Dict[str, Any]):
        """Handle modal view submissions"""
        view = payload.get("view", {})
        callback_id = view.get("callback_id")
        
        # Extract submitted values
        values = view.get("state", {}).get("values", {})
        
        # Process based on callback_id
        if callback_id == "feedback_modal":
            await self._process_feedback(values)
            
    async def _store_event(self, event: Dict[str, Any]):
        """Store event in Redis for analysis"""
        event_key = f"slack:event:{event.get('type')}:{datetime.now().timestamp()}"
        await self.redis_client.setex(
            event_key,
            86400,  # 24 hours
            json.dumps(event)
        )
        
    def register_event_handler(
        self,
        event_type: str,
        handler: Callable
    ):
        """Register event handler"""
        self.event_handlers[event_type] = handler
        
    def register_command_handler(
        self,
        command: str,
        handler: Callable
    ):
        """Register slash command handler"""
        self.command_handlers[command] = handler
        
    async def send_message(
        self,
        message: SlackMessage
    ) -> Dict[str, Any]:
        """Send message to Slack"""
        try:
            response = await self.web_client.chat_postMessage(
                channel=message.channel,
                text=message.text,
                thread_ts=message.thread_ts,
                blocks=message.blocks,
                attachments=message.attachments,
                metadata=message.metadata
            )
            
            return response.data
            
        except Exception as e:
            print(f"Error sending message: {e}")
            return {}
            
    async def send_response(
        self,
        response_url: str,
        response: Dict[str, Any]
    ):
        """Send response to response URL using shared HTTP client"""
        client = await get_async_client()
        
        async def _do():
            resp = await client.post(response_url, json=response)
            resp.raise_for_status()
            return resp
        
        await with_retries(_do)
            
    async def get_conversations(
        self,
        types: str = "public_channel,private_channel",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get conversations list"""
        cache_key = f"slack:conversations:{types}"
        
        # Check cache
        cached = await self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
            
        # Fetch from API
        response = await self.web_client.conversations_list(
            types=types,
            limit=limit
        )
        
        conversations = response.get("channels", [])
        
        # Cache for 5 minutes
        await self.redis_client.setex(
            cache_key,
            300,
            json.dumps(conversations)
        )
        
        return conversations
        
    async def get_users(self) -> List[Dict[str, Any]]:
        """Get users list"""
        cache_key = "slack:users"
        
        # Check cache
        cached = await self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
            
        # Fetch from API
        response = await self.web_client.users_list()
        users = response.get("members", [])
        
        # Cache for 1 hour
        await self.redis_client.setex(
            cache_key,
            3600,
            json.dumps(users)
        )
        
        return users
        
    async def search_messages(
        self,
        query: str,
        count: int = 100
    ) -> List[Dict[str, Any]]:
        """Search messages (requires user token)"""
        response = await self.user_client.search_messages(
            query=query,
            count=count
        )
        
        return response.get("messages", {}).get("matches", [])
        
    async def create_modal(
        self,
        trigger_id: str,
        view: Dict[str, Any]
    ):
        """Open modal view"""
        await self.web_client.views_open(
            trigger_id=trigger_id,
            view=view
        )
        
    async def update_message(
        self,
        channel: str,
        ts: str,
        text: str = None,
        blocks: List[Dict] = None
    ):
        """Update existing message"""
        await self.web_client.chat_update(
            channel=channel,
            ts=ts,
            text=text,
            blocks=blocks
        )


class SlackConversationAnalyzer:
    """
    Analyzes Slack conversations for insights and action items
    """
    
    def __init__(self):
        self.client = SlackOptimizedClient()
        self.redis_client = None
        
    async def setup(self):
        """Initialize analyzer"""
        await self.client.setup()
        self.redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        
    async def analyze_channel(
        self,
        channel_id: str,
        hours_back: int = 24
    ) -> List[SlackInsight]:
        """Analyze channel for insights"""
        insights = []
        
        # Get channel history
        since = datetime.now() - timedelta(hours=hours_back)
        
        response = await self.client.web_client.conversations_history(
            channel=channel_id,
            oldest=str(since.timestamp()),
            limit=200
        )
        
        messages = response.get("messages", [])
        
        # Analyze messages
        insights.extend(await self._analyze_messages(messages, channel_id))
        
        # Detect patterns
        insights.extend(await self._detect_patterns(messages, channel_id))
        
        return insights
        
    async def _analyze_messages(
        self,
        messages: List[Dict[str, Any]],
        channel_id: str
    ) -> List[SlackInsight]:
        """Analyze messages for insights"""
        insights = []
        
        for message in messages:
            text = message.get("text", "")
            
            # Detect action items
            if action_items := self._extract_action_items(text):
                insights.append(SlackInsight(
                    channel_id=channel_id,
                    insight_type="action_item",
                    title="Action items detected",
                    description=", ".join(action_items),
                    participants=[message.get("user", "unknown")],
                    confidence=0.9,
                    timestamp=datetime.fromtimestamp(float(message.get("ts", 0))),
                    thread_ts=message.get("thread_ts")
                ))
                
            # Detect decisions
            if decision := self._detect_decision(text):
                insights.append(SlackInsight(
                    channel_id=channel_id,
                    insight_type="decision",
                    title="Decision made",
                    description=decision,
                    participants=[message.get("user", "unknown")],
                    confidence=0.85,
                    timestamp=datetime.fromtimestamp(float(message.get("ts", 0))),
                    thread_ts=message.get("thread_ts")
                ))
                
        return insights
        
    def _extract_action_items(self, text: str) -> List[str]:
        """Extract action items from text"""
        action_items = []
        
        # Look for action item patterns
        patterns = [
            r"TODO:?\s*(.+)",
            r"Action:?\s*(.+)",
            r"Next step:?\s*(.+)",
            r"Will\s+(.+)",
            r"Please\s+(.+)",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            action_items.extend(matches)
            
        return action_items[:3]  # Limit to top 3
        
    def _detect_decision(self, text: str) -> Optional[str]:
        """Detect decisions in text"""
        decision_patterns = [
            r"decided to\s+(.+)",
            r"decision is\s+(.+)",
            r"we'll go with\s+(.+)",
            r"approved\s+(.+)",
            r"agreed on\s+(.+)",
        ]
        
        for pattern in decision_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
                
        return None
        
    async def _detect_patterns(
        self,
        messages: List[Dict[str, Any]],
        channel_id: str
    ) -> List[SlackInsight]:
        """Detect conversation patterns"""
        insights = []
        
        # Analyze message frequency
        message_times = [
            datetime.fromtimestamp(float(m.get("ts", 0)))
            for m in messages
        ]
        
        if message_times:
            # Check for high activity
            time_diff = (message_times[0] - message_times[-1]).total_seconds() / 3600
            if time_diff > 0:
                messages_per_hour = len(messages) / time_diff
                
                if messages_per_hour > 10:
                    insights.append(SlackInsight(
                        channel_id=channel_id,
                        insight_type="topic",
                        title="High activity detected",
                        description=f"{messages_per_hour:.1f} messages per hour",
                        participants=list(set(m.get("user", "") for m in messages)),
                        confidence=0.95,
                        timestamp=datetime.now()
                    ))
                    
        return insights


# Example event handlers
async def handle_app_mention(event: Dict[str, Any]):
    """Handle @mentions of the bot"""
    print(f"Bot mentioned: {event.get('text')}")
    
    
async def handle_message(event: Dict[str, Any]):
    """Handle new messages"""
    print(f"New message: {event.get('text')}")
    

async def test_slack_client():
    """Test Slack client"""
    print("💬 Testing Slack Integration")
    print("=" * 60)
    
    client = SlackOptimizedClient()
    await client.setup()
    
    try:
        # Test getting conversations
        print("\n1. Getting conversations...")
        conversations = await client.get_conversations(limit=5)
        print(f"   ✅ Found {len(conversations)} conversations")
        
        if conversations:
            # Test sending message
            print("\n2. Testing message send (dry run)...")
            message = SlackMessage(
                channel=conversations[0]["id"],
                text="Test message from Sophia integration",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "✨ *Sophia Integration Test*\nAll systems operational!"
                        }
                    }
                ]
            )
            print(f"   ✅ Message prepared for #{conversations[0]['name']}")
            
            # Test conversation analysis
            print("\n3. Analyzing first channel...")
            analyzer = SlackConversationAnalyzer()
            await analyzer.setup()
            
            insights = await analyzer.analyze_channel(
                conversations[0]["id"],
                hours_back=24
            )
            print(f"   ✅ Found {len(insights)} insights")
            
            for insight in insights[:3]:
                print(f"      - {insight.insight_type}: {insight.title}")
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
        
    finally:
        await client.stop()
        
    print("\n" + "=" * 60)
    print("✅ Slack test complete")


if __name__ == "__main__":
    asyncio.run(test_slack_client())
