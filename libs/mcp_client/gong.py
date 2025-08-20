"""
Gong MCP Client Implementation

This module provides the Model Context Protocol (MCP) client for Gong integration.
Designed specifically for AI/LLM consumption with context awareness and async support.
"""

import os
import json
import base64
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass

# Import schemas
from schemas.gong import (
    CallTranscript, CallInsight, CallSummary, CallTopic, 
    Participant, TranscriptSegment, MCPError, PaginatedResponse
)

logger = logging.getLogger(__name__)


@dataclass
class MCPContext:
    """Context information for MCP operations"""
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class GongMCPClient:
    """
    Model Context Protocol client for Gong integration.
    
    Provides context-aware, async access to Gong API data optimized for AI consumption.
    """
    
    def __init__(self, context: Optional[MCPContext] = None):
        """
        Initialize the Gong MCP client.
        
        Args:
            context: Optional MCP context for conversation tracking
        """
        self.access_key = os.getenv('GONG_ACCESS_KEY')
        self.client_secret = os.getenv('GONG_CLIENT_SECRET')
        self.base_url = "https://api.gong.io/v2"
        self.context = context or MCPContext()
        
        # Session management
        self._session: Optional[aiohttp.ClientSession] = None
        self._auth_header: Optional[str] = None
        self._rate_limit_reset: Optional[datetime] = None
        
        # Validate credentials
        if not self.access_key or not self.client_secret:
            logger.warning("Gong credentials not configured. Some operations will fail.")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session is created"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
    
    async def close(self):
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _get_auth_header(self) -> str:
        """Get or create Basic Auth header"""
        if self._auth_header is None:
            if not self.access_key or not self.client_secret:
                raise MCPError("authentication_error", "Gong credentials not configured", 401)
            
            auth_string = f"{self.access_key}:{self.client_secret}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            self._auth_header = f"Basic {auth_b64}"
        
        return self._auth_header
    
    async def _check_rate_limit(self):
        """Check if we're rate limited"""
        if self._rate_limit_reset and datetime.now() < self._rate_limit_reset:
            wait_seconds = (self._rate_limit_reset - datetime.now()).total_seconds()
            logger.warning(f"Rate limited. Waiting {wait_seconds:.1f} seconds...")
            await asyncio.sleep(wait_seconds)
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make authenticated request to Gong API with MCP error handling.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            **kwargs: Additional request parameters
            
        Returns:
            JSON response data
            
        Raises:
            MCPError: For various API errors
        """
        await self._ensure_session()
        await self._check_rate_limit()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json",
            **kwargs.pop('headers', {})
        }
        
        try:
            async with self._session.request(method, url, headers=headers, **kwargs) as response:
                # Handle rate limiting
                if response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    self._rate_limit_reset = datetime.now() + timedelta(seconds=retry_after)
                    raise MCPError("rate_limit_exceeded", f"Rate limited. Retry after {retry_after}s", 429)
                
                # Handle authentication errors
                if response.status == 401:
                    raise MCPError("authentication_error", "Invalid Gong credentials", 401)
                
                # Handle not found
                if response.status == 404:
                    raise MCPError("not_found", "Resource not found", 404)
                
                # Handle other client errors
                if 400 <= response.status < 500:
                    error_text = await response.text()
                    raise MCPError("client_error", f"Client error: {error_text}", response.status)
                
                # Handle server errors
                if response.status >= 500:
                    error_text = await response.text()
                    raise MCPError("server_error", f"Server error: {error_text}", response.status)
                
                # Success - parse JSON
                if response.content_type == 'application/json':
                    return await response.json()
                else:
                    return {"data": await response.text()}
                    
        except aiohttp.ClientError as e:
            raise MCPError("network_error", f"Network error: {str(e)}", 500)
        except asyncio.TimeoutError:
            raise MCPError("timeout_error", "Request timeout", 408)
    
    # Core API Methods
    
    async def get_calls(self, limit: int = 10, cursor: Optional[str] = None, 
                       filters: Optional[Dict] = None) -> PaginatedResponse:
        """
        Get calls with MCP context awareness.
        
        Args:
            limit: Maximum number of calls to return
            cursor: Pagination cursor
            filters: Optional filters (e.g., date range, participants)
            
        Returns:
            Paginated response with calls data
        """
        params = {"limit": min(limit, 100)}  # Gong API limit
        
        if cursor:
            params["cursor"] = cursor
        
        if filters:
            params["filter"] = json.dumps(filters)
        
        try:
            data = await self._make_request("GET", "/calls", params=params)
            
            # Log context for MCP tracking
            logger.info(f"MCP Context: {self.context.conversation_id} - Retrieved {len(data.get('calls', []))} calls")
            
            return PaginatedResponse(
                data=data.get('calls', []),
                meta={
                    "has_more": data.get('records', {}).get('totalRecords', 0) > limit,
                    "next_cursor": data.get('records', {}).get('cursor')
                }
            )
            
        except MCPError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_calls: {e}")
            raise MCPError("unexpected_error", str(e), 500)
    
    async def get_call_transcript(self, call_id: str) -> CallTranscript:
        """
        Get detailed transcript for a specific call.
        
        Args:
            call_id: The Gong call ID
            
        Returns:
            Structured call transcript
        """
        try:
            data = await self._make_request("GET", f"/calls/{call_id}/transcript")
            
            # Parse participants
            participants = []
            for p in data.get('parties', []):
                participants.append(Participant(
                    id=p.get('id', ''),
                    name=p.get('name', 'Unknown'),
                    email=p.get('emailAddress'),
                    role=p.get('role', 'participant'),
                    company=p.get('companyName')
                ))
            
            # Parse transcript segments
            segments = []
            for segment in data.get('transcript', []):
                segments.append(TranscriptSegment(
                    start_time=segment.get('start', 0),
                    end_time=segment.get('end', 0),
                    speaker_id=segment.get('speakerId', ''),
                    text=segment.get('text', '')
                ))
            
            return CallTranscript(
                call_id=call_id,
                title=data.get('title'),
                date=datetime.fromisoformat(data.get('started', '').replace('Z', '+00:00')),
                duration=data.get('duration', 0),
                participants=participants,
                segments=segments
            )
            
        except MCPError:
            raise
        except Exception as e:
            logger.error(f"Error parsing transcript for call {call_id}: {e}")
            raise MCPError("parsing_error", f"Failed to parse transcript: {str(e)}", 500)
    
    async def get_call_insights(self, call_id: str) -> List[CallInsight]:
        """
        Get AI-generated insights for a specific call.
        
        Args:
            call_id: The Gong call ID
            
        Returns:
            List of call insights
        """
        try:
            data = await self._make_request("GET", f"/calls/{call_id}/insights")
            
            insights = []
            for insight_data in data.get('insights', []):
                insights.append(CallInsight(
                    id=insight_data.get('id', ''),
                    call_id=call_id,
                    category=insight_data.get('category', 'general'),
                    text=insight_data.get('text', ''),
                    confidence=insight_data.get('confidence', 0.0),
                    segment_ids=insight_data.get('segmentIds', []),
                    timestamp=insight_data.get('timestamp', 0.0)
                ))
            
            return insights
            
        except MCPError:
            raise
        except Exception as e:
            logger.error(f"Error getting insights for call {call_id}: {e}")
            raise MCPError("insights_error", f"Failed to get insights: {str(e)}", 500)
    
    async def get_call_summary(self, call_id: str) -> CallSummary:
        """
        Get AI-generated summary for a specific call.
        
        Args:
            call_id: The Gong call ID
            
        Returns:
            Structured call summary
        """
        try:
            data = await self._make_request("GET", f"/calls/{call_id}/summary")
            
            # Parse topics
            topics = []
            for topic_data in data.get('topics', []):
                topics.append(CallTopic(
                    name=topic_data.get('name', ''),
                    importance=topic_data.get('importance', 0.0),
                    segments=topic_data.get('segments', [])
                ))
            
            return CallSummary(
                call_id=call_id,
                title=data.get('title'),
                date=datetime.fromisoformat(data.get('started', '').replace('Z', '+00:00')),
                duration=data.get('duration', 0),
                summary_text=data.get('summary', ''),
                topics=topics,
                action_items=data.get('actionItems', []),
                sentiment_score=data.get('sentiment', {}).get('score')
            )
            
        except MCPError:
            raise
        except Exception as e:
            logger.error(f"Error getting summary for call {call_id}: {e}")
            raise MCPError("summary_error", f"Failed to get summary: {str(e)}", 500)
    
    async def search_calls(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Search calls using natural language query.
        
        Args:
            query: Search query (can include client names, topics, etc.)
            limit: Maximum results to return
            
        Returns:
            Search results with metadata
        """
        try:
            # Build search filters based on query
            filters = {}
            
            # Simple keyword matching for now
            # In production, this would use more sophisticated NLP
            if any(client in query.lower() for client in ['moss', 'greystar', 'bh management']):
                # Client-specific search
                filters['title'] = {'contains': query}
            
            response = await self.get_calls(limit=limit, filters=filters if filters else None)
            
            return {
                "query": query,
                "results": response.data,
                "total_found": len(response.data),
                "has_more": response.meta.has_more,
                "context": {
                    "conversation_id": self.context.conversation_id,
                    "timestamp": self.context.timestamp.isoformat()
                }
            }
            
        except MCPError:
            raise
        except Exception as e:
            logger.error(f"Error searching calls with query '{query}': {e}")
            raise MCPError("search_error", f"Search failed: {str(e)}", 500)
    
    # Convenience methods for SOPHIA integration
    
    async def get_client_calls(self, client_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get calls for a specific client (optimized for SOPHIA).
        
        Args:
            client_name: Name of the client (e.g., "Moss & Co")
            limit: Maximum calls to return
            
        Returns:
            List of client calls with essential data
        """
        try:
            search_result = await self.search_calls(client_name, limit)
            
            # Filter and format for SOPHIA consumption
            client_calls = []
            for call in search_result['results']:
                if client_name.lower() in call.get('title', '').lower():
                    client_calls.append({
                        'id': call.get('id'),
                        'title': call.get('title'),
                        'date': call.get('started'),
                        'duration': call.get('duration'),
                        'participants': len(call.get('parties', [])),
                        'url': call.get('url')
                    })
            
            return client_calls
            
        except MCPError:
            raise
        except Exception as e:
            logger.error(f"Error getting client calls for '{client_name}': {e}")
            return []
    
    async def get_recent_calls_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get summary of recent calls for SOPHIA dashboard.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Summary statistics and key calls
        """
        try:
            # Calculate date filter
            since_date = datetime.now() - timedelta(days=days)
            filters = {
                'fromDateTime': since_date.isoformat(),
                'toDateTime': datetime.now().isoformat()
            }
            
            response = await self.get_calls(limit=50, filters=filters)
            calls = response.data
            
            # Generate summary statistics
            total_calls = len(calls)
            total_duration = sum(call.get('duration', 0) for call in calls)
            
            # Group by client/company
            clients = {}
            for call in calls:
                title = call.get('title', '')
                # Simple client extraction - could be improved with NLP
                for client in ['Moss', 'Greystar', 'BH Management', 'Pay Ready']:
                    if client.lower() in title.lower():
                        if client not in clients:
                            clients[client] = []
                        clients[client].append(call)
                        break
            
            return {
                'period_days': days,
                'total_calls': total_calls,
                'total_duration_minutes': total_duration // 60,
                'clients': {name: len(calls) for name, calls in clients.items()},
                'recent_calls': calls[:5],  # Most recent 5
                'context': {
                    'generated_at': datetime.now().isoformat(),
                    'conversation_id': self.context.conversation_id
                }
            }
            
        except MCPError:
            raise
        except Exception as e:
            logger.error(f"Error generating recent calls summary: {e}")
            return {
                'error': str(e),
                'period_days': days,
                'total_calls': 0
            }


# Convenience function for SOPHIA integration
async def create_gong_client(conversation_id: Optional[str] = None) -> GongMCPClient:
    """
    Create a Gong MCP client with conversation context.
    
    Args:
        conversation_id: Optional conversation ID for context tracking
        
    Returns:
        Configured GongMCPClient instance
    """
    context = MCPContext(conversation_id=conversation_id)
    return GongMCPClient(context=context)

