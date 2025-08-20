"""
Gong.io API Client
Production-ready client for Gong.io integration with SOPHIA.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

import httpx
from sophia.core.constants import ENV_VARS, SERVICE_ENDPOINTS, TIMEOUTS, RATE_LIMITS

logger = logging.getLogger(__name__)

@dataclass
class GongCall:
    """Represents a Gong call record"""
    call_id: str
    title: str
    started: datetime
    duration: int
    participants: List[str]
    transcript: Optional[str] = None
    summary: Optional[str] = None
    url: Optional[str] = None

@dataclass
class GongSearchResult:
    """Represents Gong search results"""
    query: str
    results: List[Dict[str, Any]]
    total_count: int

class GongClient:
    """
    Production-ready Gong.io API client with comprehensive error handling,
    rate limiting, retries, and timeout management.
    """
    
    def __init__(
        self, 
        base_url: Optional[str] = None, 
        token: Optional[str] = None, 
        timeout: int = TIMEOUTS["DEFAULT"]
    ):
        self.base_url = (
            base_url or 
            os.getenv(ENV_VARS["GONG_BASE_URL"], SERVICE_ENDPOINTS["GONG_DEFAULT_BASE_URL"])
        ).rstrip("/")
        
        self.token = (
            token or 
            os.getenv(ENV_VARS["GONG_ACCESS_TOKEN"]) or 
            os.getenv(ENV_VARS["GONG_API_KEY"])
        )
        
        if not (self.base_url and self.token):
            raise EnvironmentError(
                f"Missing required environment variables: "
                f"{ENV_VARS['GONG_BASE_URL']} and "
                f"({ENV_VARS['GONG_ACCESS_TOKEN']} or {ENV_VARS['GONG_API_KEY']})"
            )
        
        self.timeout = timeout
        self.rate_limit = RATE_LIMITS["GONG_REQUESTS_PER_MINUTE"]
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "User-Agent": "SOPHIA-AI-Orchestrator/1.0.0"
            }
        )
        
        # Rate limiting
        self._request_times: List[float] = []
        self._lock = asyncio.Lock()
    
    async def _rate_limit_check(self) -> None:
        """Enforce rate limiting"""
        async with self._lock:
            now = asyncio.get_event_loop().time()
            # Remove requests older than 1 minute
            self._request_times = [t for t in self._request_times if now - t < 60]
            
            if len(self._request_times) >= self.rate_limit:
                sleep_time = 60 - (now - self._request_times[0])
                if sleep_time > 0:
                    logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)
            
            self._request_times.append(now)
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        retries: int = 3
    ) -> Dict[str, Any]:
        """Make HTTP request with retries and error handling"""
        await self._rate_limit_check()
        
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(retries + 1):
            try:
                response = await self._client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data
                )
                
                if response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited, retrying after {retry_after}s")
                    await asyncio.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                if attempt == retries:
                    logger.error(f"HTTP error after {retries} retries: {e}")
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except httpx.RequestError as e:
                if attempt == retries:
                    logger.error(f"Request error after {retries} retries: {e}")
                    raise
                await asyncio.sleep(2 ** attempt)
        
        raise Exception("Max retries exceeded")
    
    async def get_me(self) -> Dict[str, Any]:
        """Get current user information (health check)"""
        try:
            return await self._make_request("GET", "/v2/users/me")
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            raise
    
    async def list_calls(
        self, 
        since: str, 
        until: str, 
        limit: int = 50,
        workspace_id: Optional[str] = None
    ) -> List[GongCall]:
        """
        List calls within date range
        
        Args:
            since: Start date (ISO format: 2025-08-01T00:00:00Z)
            until: End date (ISO format: 2025-08-20T23:59:59Z)
            limit: Maximum number of calls to return
            workspace_id: Optional workspace ID filter
        """
        params = {
            "fromDateTime": since,
            "toDateTime": until,
            "limit": min(limit, 100)  # Gong API limit
        }
        
        if workspace_id:
            params["workspaceId"] = workspace_id
        
        try:
            data = await self._make_request("GET", "/v2/calls", params=params)
            
            calls = []
            for call_data in data.get("calls", []):
                call = GongCall(
                    call_id=call_data["id"],
                    title=call_data.get("title", "Untitled Call"),
                    started=datetime.fromisoformat(call_data["started"].replace("Z", "+00:00")),
                    duration=call_data.get("duration", 0),
                    participants=[p.get("name", "Unknown") for p in call_data.get("participants", [])],
                    url=call_data.get("url")
                )
                calls.append(call)
            
            return calls
            
        except Exception as e:
            logger.error(f"Failed to list calls: {e}")
            raise
    
    async def get_call(self, call_id: str) -> GongCall:
        """Get detailed call information including transcript"""
        try:
            # Get call details
            call_data = await self._make_request("GET", f"/v2/calls/{call_id}")
            
            # Get transcript if available
            transcript = None
            try:
                transcript_data = await self._make_request("GET", f"/v2/calls/{call_id}/transcript")
                transcript = transcript_data.get("transcript", "")
            except Exception as e:
                logger.warning(f"Could not get transcript for call {call_id}: {e}")
            
            call = GongCall(
                call_id=call_data["id"],
                title=call_data.get("title", "Untitled Call"),
                started=datetime.fromisoformat(call_data["started"].replace("Z", "+00:00")),
                duration=call_data.get("duration", 0),
                participants=[p.get("name", "Unknown") for p in call_data.get("participants", [])],
                transcript=transcript,
                url=call_data.get("url")
            )
            
            return call
            
        except Exception as e:
            logger.error(f"Failed to get call {call_id}: {e}")
            raise
    
    async def search_transcripts(
        self, 
        query: str, 
        limit: int = 20,
        workspace_id: Optional[str] = None
    ) -> GongSearchResult:
        """Search call transcripts"""
        params = {
            "q": query,
            "limit": min(limit, 100),
            "contentType": "transcript"
        }
        
        if workspace_id:
            params["workspaceId"] = workspace_id
        
        try:
            data = await self._make_request("GET", "/v2/calls/search", params=params)
            
            return GongSearchResult(
                query=query,
                results=data.get("results", []),
                total_count=data.get("totalCount", 0)
            )
            
        except Exception as e:
            logger.error(f"Failed to search transcripts: {e}")
            raise
    
    async def create_note(
        self, 
        call_id: str, 
        content: str, 
        note_type: str = "general"
    ) -> Dict[str, Any]:
        """Create a note for a call (write-back capability)"""
        json_data = {
            "content": content,
            "type": note_type,
            "callId": call_id
        }
        
        try:
            return await self._make_request("POST", "/v2/calls/notes", json_data=json_data)
        except Exception as e:
            logger.error(f"Failed to create note for call {call_id}: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        try:
            start_time = asyncio.get_event_loop().time()
            user_info = await self.get_me()
            response_time = asyncio.get_event_loop().time() - start_time
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "user_id": user_info.get("id"),
                "user_email": user_info.get("email"),
                "base_url": self.base_url,
                "rate_limit": self.rate_limit,
                "requests_in_last_minute": len(self._request_times)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "base_url": self.base_url
            }
    
    async def aclose(self) -> None:
        """Close the HTTP client"""
        await self._client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()

