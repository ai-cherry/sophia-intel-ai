"""
Slack MCP Server - Reference Implementation
Demonstrates standardized MCP service with full Swarm integration
"""
from mcp.saas.common.base_server import (
    BaseMCPServer, ContextRequest, ContextResponse, 
    SearchRequest, SearchResponse
)
from mcp.saas.common.auth import api_key_auth, swarm_auth
from fastapi import Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from loguru import logger
import time
import os
import httpx
import asyncio
import json

class SlackContextRequest(ContextRequest):
    """Slack-specific context request"""
    workspace_id: str = Field(..., description="Slack workspace ID")
    channel_id: Optional[str] = Field(None, description="Slack channel ID")
    thread_ts: Optional[str] = Field(None, description="Slack thread timestamp")
    user_id: Optional[str] = Field(None, description="Slack user ID")

class SlackSearchRequest(SearchRequest):
    """Slack-specific search request"""
    workspace_id: Optional[str] = Field(None, description="Limit search to specific workspace")
    channel_id: Optional[str] = Field(None, description="Limit search to specific channel")
    date_from: Optional[str] = Field(None, description="Search from date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="Search to date (YYYY-MM-DD)")

class SwarmSlackMessage(BaseModel):
    """Message from Swarm to be sent to Slack"""
    channel: str = Field(..., description="Slack channel ID or name")
    text: str = Field(..., description="Message text")
    thread_ts: Optional[str] = Field(None, description="Thread timestamp if replying")
    swarm_stage: str = Field(..., description="Current swarm stage")
    session_id: str = Field(..., description="Swarm session ID")
    blocks: Optional[List[Dict[str, Any]]] = Field(None, description="Slack blocks for rich formatting")

class SlackChannelHistory(BaseModel):
    """Request for Slack channel history"""
    channel_id: str = Field(..., description="Slack channel ID")
    limit: int = Field(default=100, description="Number of messages to fetch")
    cursor: Optional[str] = Field(None, description="Pagination cursor")

class SlackMCPServer(BaseMCPServer):
    """
    Slack MCP Server with comprehensive Swarm integration
    
    Features:
    - Context storage and retrieval from Slack conversations
    - Semantic search across Slack workspaces
    - Swarm agent message posting
    - Channel history retrieval
    - Real-time context extraction
    """
    
    def __init__(self):
        super().__init__(
            title="Slack MCP Server",
            description="Model Context Protocol server for Slack integration with full Swarm support",
            version="1.0.0"
        )
        
        self._setup_slack_client()
        self._setup_storage()
        self._setup_routes()
        
    def _setup_slack_client(self):
        """Initialize Slack API client"""
        self.slack_token = os.getenv("SLACK_API_TOKEN")
        self.slack_signing_secret = os.getenv("SLACK_SIGNING_SECRET")
        
        if self.slack_token:
            self.slack_client = httpx.AsyncClient(
                base_url="https://slack.com/api/",
                headers={"Authorization": f"Bearer {self.slack_token}"},
                timeout=30.0
            )
            logger.info("Slack API client initialized")
        else:
            logger.warning("SLACK_API_TOKEN not provided - some features will be unavailable")
            self.slack_client = None
            
    def _setup_storage(self):
        """Initialize context storage (would integrate with vector DB in production)"""
        self.context_store = {}  # In-memory for demo - replace with Qdrant/PostgreSQL
        self.message_cache = {}  # Cache recent messages for performance
        
    def _setup_routes(self):
        """Setup all Slack-specific routes"""
        
        # Standard MCP routes
        self.register_route(
            "/slack/context",
            "POST",
            self.store_context,
            response_model=ContextResponse,
            dependencies=[Depends(api_key_auth)]
        )
        
        self.register_route(
            "/slack/search",
            "POST",
            self.search_context,
            response_model=SearchResponse,
            dependencies=[Depends(api_key_auth)]
        )
        
        # Swarm integration routes
        self.register_route(
            "/slack/swarm/message",
            "POST",
            self.send_swarm_message,
            dependencies=[Depends(api_key_auth)]
        )
        
        self.register_route(
            "/slack/swarm/extract-context",
            "POST",
            self.extract_conversation_context,
            dependencies=[Depends(api_key_auth)]
        )
        
        # Slack API integration routes
        self.register_route(
            "/slack/channels/{channel_id}/history",
            "GET",
            self.get_channel_history,
            dependencies=[Depends(api_key_auth)]
        )
        
        self.register_route(
            "/slack/workspaces/list",
            "GET",
            self.list_workspaces,
            dependencies=[Depends(api_key_auth)]
        )
        
        # Webhook endpoint for Slack events
        self.register_route(
            "/slack/events",
            "POST",
            self.handle_slack_event
        )
        
    async def store_context(self, request: SlackContextRequest, background_tasks: BackgroundTasks):
        """Store Slack conversation context with vector embeddings"""
        logger.info(f"Storing Slack context: workspace={request.workspace_id}, session={request.session_id}")
        
        try:
            # Generate context ID
            context_id = f"slack_{request.workspace_id}_{request.session_id}_{int(time.time())}"
            
            # Prepare context data
            context_data = {
                "id": context_id,
                "workspace_id": request.workspace_id,
                "channel_id": request.channel_id,
                "thread_ts": request.thread_ts,
                "user_id": request.user_id,
                "content": request.content,
                "metadata": request.metadata,
                "context_type": request.context_type,
                "swarm_stage": request.swarm_stage,
                "session_id": request.session_id,
                "timestamp": time.time(),
                "service": "slack"
            }
            
            # Store in context store (in production, this would use vector DB)
            self.context_store[context_id] = context_data
            
            # Extract entities and keywords for better search
            entities = await self._extract_entities(request.content)
            context_data["entities"] = entities
            
            # Record in Swarm telemetry if applicable
            if request.swarm_stage:
                background_tasks.add_task(
                    self.swarm_telemetry,
                    {
                        "type": "context_storage",
                        "service": "slack",
                        "session_id": request.session_id,
                        "swarm_stage": request.swarm_stage,
                        "content_size": len(request.content),
                        "context_type": request.context_type,
                        "workspace_id": request.workspace_id,
                        "entities_count": len(entities)
                    }
                )
            
            return ContextResponse(
                status="success",
                id=context_id,
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Error storing Slack context: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to store context: {str(e)}")
            
    async def search_context(self, request: SlackSearchRequest):
        """Search Slack conversation context with filters"""
        logger.info(f"Searching Slack context: '{request.query}' (limit={request.limit})")
        
        try:
            results = []
            
            # Simple text search in stored contexts (in production, use vector similarity)
            for context_id, context_data in self.context_store.items():
                # Apply workspace filter
                if request.workspace_id and context_data.get("workspace_id") != request.workspace_id:
                    continue
                    
                # Apply channel filter
                if request.channel_id and context_data.get("channel_id") != request.channel_id:
                    continue
                
                # Apply session filter
                if request.session_id and context_data.get("session_id") != request.session_id:
                    continue
                    
                # Simple text matching (replace with semantic search)
                content = context_data.get("content", "").lower()
                if request.query.lower() in content:
                    results.append({
                        "id": context_id,
                        "content": context_data.get("content", "")[:500],  # Truncate for response
                        "metadata": context_data.get("metadata", {}),
                        "workspace_id": context_data.get("workspace_id"),
                        "channel_id": context_data.get("channel_id"),
                        "timestamp": context_data.get("timestamp"),
                        "swarm_stage": context_data.get("swarm_stage"),
                        "score": 0.8,  # Mock score - use real similarity in production
                        "entities": context_data.get("entities", [])
                    })
            
            # Sort by timestamp (newest first) and limit
            results.sort(key=lambda x: x["timestamp"], reverse=True)
            results = results[:request.limit]
            
            return SearchResponse(
                results=results,
                count=len(results),
                query=request.query
            )
            
        except Exception as e:
            logger.error(f"Error searching Slack context: {e}")
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    
    async def send_swarm_message(self, message: SwarmSlackMessage):
        """Send a message from Swarm agents to Slack"""
        logger.info(f"Sending Swarm message to Slack: {message.swarm_stage} -> #{message.channel}")
        
        if not self.slack_client:
            raise HTTPException(status_code=503, detail="Slack API not configured")
        
        try:
            # Format message with Swarm branding
            formatted_text = f"🤖 *[{message.swarm_stage.upper()}]* {message.text}"
            
            # Prepare Slack message payload
            payload = {
                "channel": message.channel,
                "text": formatted_text,
                "username": f"Swarm {message.swarm_stage.title()}",
                "icon_emoji": self._get_stage_emoji(message.swarm_stage)
            }
            
            if message.thread_ts:
                payload["thread_ts"] = message.thread_ts
                
            if message.blocks:
                payload["blocks"] = message.blocks
                
            # Send to Slack
            response = await self.slack_client.post("chat.postMessage", json=payload)
            
            if response.status_code != 200:
                logger.error(f"Slack API error: {response.status_code} {response.text}")
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"Slack API error: {response.text}"
                )
                
            result = response.json()
            if not result.get("ok", False):
                logger.error(f"Slack API returned error: {result.get('error')}")
                raise HTTPException(status_code=400, detail=result.get("error"))
                
            # Record in Swarm telemetry
            await self.swarm_telemetry({
                "type": "swarm_message_sent",
                "service": "slack",
                "session_id": message.session_id,
                "swarm_stage": message.swarm_stage,
                "channel": message.channel,
                "message_ts": result.get("ts"),
                "message_length": len(message.text)
            })
            
            return {
                "status": "success",
                "ts": result.get("ts"),
                "channel": message.channel,
                "permalink": result.get("permalink")
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error sending Swarm message to Slack: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")
    
    async def extract_conversation_context(self, request: Dict[str, Any]):
        """Extract structured context from Slack conversation for Swarm"""
        channel_id = request.get("channel_id")
        thread_ts = request.get("thread_ts")
        session_id = request.get("session_id")
        swarm_stage = request.get("swarm_stage")
        
        logger.info(f"Extracting conversation context for Swarm: {channel_id}")
        
        try:
            # Fetch conversation history
            history = await self._fetch_conversation_history(channel_id, thread_ts)
            
            # Extract key information
            context = {
                "conversation_summary": await self._summarize_conversation(history),
                "key_decisions": await self._extract_decisions(history),
                "action_items": await self._extract_action_items(history),
                "participants": await self._extract_participants(history),
                "entities": await self._extract_entities_from_history(history),
                "sentiment": await self._analyze_sentiment(history),
                "channel_id": channel_id,
                "thread_ts": thread_ts,
                "message_count": len(history),
                "timestamp": time.time()
            }
            
            # Store extracted context
            if session_id:
                await self.store_context(SlackContextRequest(
                    session_id=session_id,
                    content=json.dumps(context, indent=2),
                    metadata={
                        "extraction_type": "conversation_context",
                        "channel_id": channel_id,
                        "thread_ts": thread_ts
                    },
                    context_type="extracted_conversation",
                    swarm_stage=swarm_stage,
                    workspace_id=request.get("workspace_id", "unknown"),
                    channel_id=channel_id,
                    thread_ts=thread_ts,
                    user_id=request.get("user_id")
                ), BackgroundTasks())
            
            return context
            
        except Exception as e:
            logger.error(f"Error extracting conversation context: {e}")
            raise HTTPException(status_code=500, detail=f"Context extraction failed: {str(e)}")
    
    async def get_channel_history(self, channel_id: str, limit: int = 100, cursor: Optional[str] = None):
        """Fetch Slack channel history"""
        if not self.slack_client:
            raise HTTPException(status_code=503, detail="Slack API not configured")
            
        try:
            params = {"channel": channel_id, "limit": min(limit, 200)}
            if cursor:
                params["cursor"] = cursor
                
            response = await self.slack_client.get("conversations.history", params=params)
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Slack API error")
                
            data = response.json()
            if not data.get("ok", False):
                raise HTTPException(status_code=400, detail=data.get("error"))
                
            return {
                "messages": data.get("messages", []),
                "has_more": data.get("has_more", False),
                "next_cursor": data.get("response_metadata", {}).get("next_cursor")
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching channel history: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def list_workspaces(self):
        """List available Slack workspaces"""
        # This would query your workspace configuration
        # For now, return configured workspace info
        return {
            "workspaces": [
                {
                    "id": os.getenv("SLACK_WORKSPACE_ID", "unknown"),
                    "name": os.getenv("SLACK_WORKSPACE_NAME", "Default Workspace"),
                    "configured": bool(self.slack_token)
                }
            ]
        }
    
    async def handle_slack_event(self, request: Dict[str, Any]):
        """Handle incoming Slack events (webhooks)"""
        # This would handle real-time events from Slack
        # For now, just acknowledge
        if request.get("type") == "url_verification":
            return {"challenge": request.get("challenge")}
        
        # Process other events (messages, reactions, etc.)
        logger.info(f"Received Slack event: {request.get('type')}")
        return {"status": "ok"}
    
    # Helper methods
    
    def _get_stage_emoji(self, stage: str) -> str:
        """Get emoji for Swarm stage"""
        emojis = {
            "architect": ":building_construction:",
            "builder": ":hammer_and_wrench:",
            "tester": ":mag:",
            "operator": ":rocket:"
        }
        return emojis.get(stage.lower(), ":robot_face:")
    
    async def _extract_entities(self, text: str) -> List[str]:
        """Extract entities from text (mock implementation)"""
        # In production, use NLP libraries like spaCy or cloud APIs
        entities = []
        words = text.lower().split()
        
        # Simple entity extraction
        for word in words:
            if word.startswith('@') or word.startswith('#'):
                entities.append(word)
            elif len(word) > 8 and word.isalpha():
                entities.append(word)
                
        return list(set(entities))[:10]  # Limit to top 10
    
    async def _fetch_conversation_history(self, channel_id: str, thread_ts: Optional[str]) -> List[Dict]:
        """Fetch conversation history for context extraction"""
        if not self.slack_client:
            return []
            
        try:
            if thread_ts:
                # Fetch thread replies
                response = await self.slack_client.get(
                    "conversations.replies",
                    params={"channel": channel_id, "ts": thread_ts}
                )
            else:
                # Fetch recent channel messages
                response = await self.slack_client.get(
                    "conversations.history",
                    params={"channel": channel_id, "limit": 50}
                )
                
            if response.status_code == 200 and response.json().get("ok"):
                return response.json().get("messages", [])
                
        except Exception as e:
            logger.error(f"Error fetching conversation history: {e}")
            
        return []
    
    async def _summarize_conversation(self, messages: List[Dict]) -> str:
        """Generate conversation summary"""
        if not messages:
            return "No conversation to summarize"
            
        # Simple summary (in production, use LLM)
        total_messages = len(messages)
        users = set(msg.get("user", "unknown") for msg in messages)
        
        return f"Conversation with {total_messages} messages from {len(users)} participants"
    
    async def _extract_decisions(self, messages: List[Dict]) -> List[str]:
        """Extract key decisions from conversation"""
        decisions = []
        decision_keywords = ["decided", "agreed", "confirmed", "approved", "settled"]
        
        for msg in messages:
            text = msg.get("text", "").lower()
            if any(keyword in text for keyword in decision_keywords):
                decisions.append(msg.get("text", "")[:200])
                
        return decisions[:5]  # Top 5 decisions
    
    async def _extract_action_items(self, messages: List[Dict]) -> List[str]:
        """Extract action items from conversation"""
        action_items = []
        action_keywords = ["todo", "task", "action item", "follow up", "next step"]
        
        for msg in messages:
            text = msg.get("text", "").lower()
            if any(keyword in text for keyword in action_keywords):
                action_items.append(msg.get("text", "")[:200])
                
        return action_items[:5]  # Top 5 action items
    
    async def _extract_participants(self, messages: List[Dict]) -> List[str]:
        """Extract conversation participants"""
        participants = set()
        for msg in messages:
            if user := msg.get("user"):
                participants.add(user)
        return list(participants)
    
    async def _extract_entities_from_history(self, messages: List[Dict]) -> List[str]:
        """Extract entities from conversation history"""
        all_entities = []
        for msg in messages:
            entities = await self._extract_entities(msg.get("text", ""))
            all_entities.extend(entities)
        return list(set(all_entities))[:20]  # Top 20 unique entities
    
    async def _analyze_sentiment(self, messages: List[Dict]) -> str:
        """Analyze conversation sentiment"""
        if not messages:
            return "neutral"
            
        # Simple sentiment analysis (in production, use proper sentiment analysis)
        positive_words = ["good", "great", "excellent", "happy", "success"]
        negative_words = ["bad", "terrible", "problem", "issue", "error"]
        
        positive_count = 0
        negative_count = 0
        
        for msg in messages:
            text = msg.get("text", "").lower()
            positive_count += sum(1 for word in positive_words if word in text)
            negative_count += sum(1 for word in negative_words if word in text)
            
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"


# Create the FastAPI app instance
app = SlackMCPServer().app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)