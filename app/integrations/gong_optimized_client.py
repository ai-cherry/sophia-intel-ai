#!/usr/bin/env python3
"""
Optimized Gong API Client with 2025 Best Practices
Implements correct endpoints, OAuth 2.0, rate limiting, and intelligent retry
"""
import asyncio
import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import aiohttp
import redis.asyncio as redis
from aiohttp import ClientSession
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# Configuration from environment
GONG_ACCESS_KEY = os.getenv("GONG_ACCESS_KEY")
GONG_CLIENT_SECRET = os.getenv("GONG_CLIENT_SECRET")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


class GongEndpoint(Enum):
    """Corrected Gong API endpoints with proper HTTP methods"""
    # User endpoints
    USERS_CURRENT = ("GET", "/v2/users/current")
    USERS_LIST = ("GET", "/v2/users")
    
    # Call endpoints - CORRECTED METHODS
    CALLS_LIST = ("GET", "/v2/calls")  # GET with query params
    CALLS_GET = ("GET", "/v2/calls/{id}")  # GET specific call
    CALLS_TRANSCRIPT = ("POST", "/v2/calls/transcript")  # POST with body
    CALLS_EXTENSIVE = ("POST", "/v2/calls/extensive")  # POST with body
    
    # Other endpoints
    STATS_ACTIVITY = ("POST", "/v2/stats/activity")
    LIBRARY_FOLDERS = ("GET", "/v2/library/folders")
    MEETINGS_LIST = ("GET", "/v2/meetings")
    
    # Webhook endpoints
    WEBHOOKS_LIST = ("GET", "/v2/webhooks")
    WEBHOOKS_CREATE = ("POST", "/v2/webhooks")
    WEBHOOKS_DELETE = ("DELETE", "/v2/webhooks/{id}")


@dataclass
class GongRateLimiter:
    """Rate limiter for Gong API (3 calls/sec, 10k/day)"""
    calls_per_second: int = 3
    daily_limit: int = 10000
    current_daily_count: int = 0
    last_reset: datetime = field(default_factory=datetime.now)
    _semaphore: asyncio.Semaphore = field(default_factory=lambda: asyncio.Semaphore(3))
    
    async def acquire(self):
        """Acquire rate limit permit"""
        async with self._semaphore:
            # Check daily limit
            if datetime.now().date() > self.last_reset.date():
                self.current_daily_count = 0
                self.last_reset = datetime.now()
            
            if self.current_daily_count >= self.daily_limit:
                raise Exception("Daily API limit reached")
            
            self.current_daily_count += 1
            # Enforce per-second rate
            await asyncio.sleep(1.0 / self.calls_per_second)
            

class GongOptimizedClient:
    """
    Optimized Gong client with best practices:
    - Correct HTTP methods for each endpoint
    - OAuth 2.0 support (with fallback to Basic Auth)
    - Rate limiting and exponential backoff
    - Redis caching for frequent queries
    - Efficient batch processing
    """
    
    def __init__(self, use_oauth: bool = False):
        self.base_url = "https://api.gong.io"
        self.access_key = GONG_ACCESS_KEY
        self.client_secret = GONG_CLIENT_SECRET
        self.use_oauth = use_oauth
        self.access_token = None
        self.token_expires = None
        self.rate_limiter = GongRateLimiter()
        self.session: Optional[ClientSession] = None
        self.redis_client: Optional[redis.Redis] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = ClientSession()
        self.redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        if self.use_oauth:
            await self._refresh_oauth_token()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        if self.redis_client:
            await self.redis_client.close()
            
    async def _refresh_oauth_token(self):
        """Get OAuth 2.0 access token using client credentials flow"""
        token_url = f"{self.base_url}/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.access_key,
            "client_secret": self.client_secret,
        }
        
        async with self.session.post(token_url, data=data) as response:
            if response.status == 200:
                token_data = await response.json()
                self.access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires = datetime.now() + timedelta(seconds=expires_in)
            else:
                # Fallback to Basic Auth if OAuth fails
                self.use_oauth = False
                
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        if (self.use_oauth and self.access_token):
            # Check token expiry
            if self.token_expires and datetime.now() >= self.token_expires:
                asyncio.create_task(self._refresh_oauth_token())
            return {"Authorization": f"Bearer {self.access_token}"}
        else:
            # Basic Auth fallback
            import base64
            if not (self.access_key and self.client_secret):
                # Raise a clear error if credentials are missing
                raise RuntimeError("Gong credentials missing: set GONG_ACCESS_KEY and GONG_CLIENT_SECRET in ~/.config/sophia/env")
            credentials = f"{self.access_key}:{self.client_secret}"
            encoded = base64.b64encode(credentials.encode()).decode()
            return {"Authorization": f"Basic {encoded}"}
            
    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception)
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make API request with retry logic"""
        await self.rate_limiter.acquire()
        
        # Check cache for GET requests
        cache_key = None
        if method == "GET" and params:
            cache_key = f"gong:{endpoint}:{hashlib.md5(str(params).encode()).hexdigest()}"
            cached = await self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        
        url = f"{self.base_url}{endpoint}"
        headers = self._get_auth_headers()
        headers["Content-Type"] = "application/json"
        
        async with self.session.request(
            method,
            url,
            params=params,
            json=json_data,
            headers=headers,
        ) as response:
            if response.status == 429:
                # Rate limited - wait and retry
                retry_after = int(response.headers.get("Retry-After", 60))
                await asyncio.sleep(retry_after)
                raise Exception(f"Rate limited, retry after {retry_after}s")
                
            if response.status >= 400:
                error_text = await response.text()
                raise Exception(f"API error {response.status}: {error_text}")
                
            result = await response.json()
            
            # Cache successful GET responses
            if cache_key:
                await self.redis_client.setex(
                    cache_key,
                    300,  # 5 minute cache
                    json.dumps(result)
                )
                
            return result
            
    async def get_calls(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        cursor: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Get calls list using correct GET method with query parameters
        """
        params = {"limit": limit}
        
        if from_date:
            params["fromDateTime"] = from_date.isoformat() + "Z"
        if to_date:
            params["toDateTime"] = to_date.isoformat() + "Z"
        if cursor:
            params["cursor"] = cursor
            
        return await self._make_request("GET", "/v2/calls", params=params)
        
    async def get_call_transcript(self, call_ids: List[str]) -> Dict[str, Any]:
        """
        Get call transcripts using POST method with request body
        """
        json_data = {
            "filter": {
                "callIds": call_ids
            }
        }
        return await self._make_request("POST", "/v2/calls/transcript", json_data=json_data)
        
    async def get_call_extensive(
        self,
        call_ids: Optional[List[str]] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get extensive call data using POST method with request body
        """
        filter_data = {}
        
        if call_ids:
            filter_data["callIds"] = call_ids
        if from_date:
            filter_data["fromDateTime"] = from_date.isoformat() + "Z"
        if to_date:
            filter_data["toDateTime"] = to_date.isoformat() + "Z"
            
        json_data = {"filter": filter_data}
        return await self._make_request("POST", "/v2/calls/extensive", json_data=json_data)
        
    async def batch_process_calls(
        self,
        from_date: datetime,
        to_date: datetime,
        batch_size: int = 100,
        process_func=None,
    ):
        """
        Efficiently batch process calls with pagination
        """
        cursor = None
        total_processed = 0
        
        while True:
            # Get batch of calls
            response = await self.get_calls(
                from_date=from_date,
                to_date=to_date,
                cursor=cursor,
                limit=batch_size,
            )
            
            calls = response.get("calls", [])
            if not calls:
                break
                
            # Process batch
            if process_func:
                await process_func(calls)
                
            total_processed += len(calls)
            
            # Check for next page
            cursor = response.get("records", {}).get("cursor")
            if not cursor:
                break
                
            # Brief pause between batches
            await asyncio.sleep(0.5)
            
        return total_processed
        
    async def setup_webhook(
        self,
        webhook_url: str,
        events: List[str],
        secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Setup Gong webhook for real-time events
        """
        json_data = {
            "url": webhook_url,
            "events": events,
        }
        
        if secret:
            json_data["secret"] = secret
            
        return await self._make_request("POST", "/v2/webhooks", json_data=json_data)
        
    async def test_connection(self) -> bool:
        """
        Test API connection and credentials
        """
        try:
            # Try to get current user
            result = await self._make_request("GET", "/v2/users/current")
            return "user" in result
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False


async def test_optimized_client():
    """Test the optimized Gong client"""
    print("🚀 Testing Optimized Gong Client")
    print("=" * 60)
    
    async with GongOptimizedClient(use_oauth=False) as client:
        # Test connection
        print("\n1. Testing connection...")
        connected = await client.test_connection()
        print(f"   {'✅' if connected else '❌'} Connection: {connected}")
        
        # Get recent calls
        print("\n2. Getting recent calls (GET method)...")
        from_date = datetime.now() - timedelta(days=7)
        to_date = datetime.now()
        
        try:
            calls_response = await client.get_calls(
                from_date=from_date,
                to_date=to_date,
                limit=5
            )
            calls = calls_response.get("calls", [])
            print(f"   ✅ Found {len(calls)} calls")
            
            if calls:
                # Get transcript for first call
                call_id = calls[0].get("id")
                print(f"\n3. Getting transcript for call {call_id}...")
                
                try:
                    transcript = await client.get_call_transcript([call_id])
                    print(f"   ✅ Transcript retrieved")
                except Exception as e:
                    print(f"   ❌ Transcript error: {e}")
                    
        except Exception as e:
            print(f"   ❌ Error getting calls: {e}")
            
    print("\n" + "=" * 60)
    print("✅ Optimized client test complete")


if __name__ == "__main__":
    asyncio.run(test_optimized_client())
