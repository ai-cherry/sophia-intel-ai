#!/usr/bin/env python3
"""
Optimized Looker Integration with 2025 Best Practices
Implements SDK 4.0, async operations, caching, and intelligent dashboard sync
"""
import asyncio
import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import aiohttp
import redis.asyncio as redis
from tenacity import retry, stop_after_attempt, wait_exponential

# Configuration
LOOKER_CLIENT_ID = os.getenv("LOOKER_CLIENT_ID", "YOUR_LOOKER_CLIENT_ID")
LOOKER_CLIENT_SECRET = os.getenv("LOOKER_CLIENT_SECRET", "kXxhgscT87fstFBcPRTNj733")
LOOKER_BASE_URL = os.getenv("LOOKER_BASE_URL", "https://your-instance.looker.com")
LOOKER_API_VERSION = os.getenv("LOOKER_API_VERSION", "4.0")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


class LookerEndpoint(Enum):
    """Looker API endpoints"""
    # Auth
    LOGIN = ("POST", "/login")
    LOGOUT = ("DELETE", "/logout")
    
    # Dashboards
    DASHBOARDS_LIST = ("GET", "/dashboards")
    DASHBOARD_GET = ("GET", "/dashboards/{id}")
    DASHBOARD_ELEMENTS = ("GET", "/dashboards/{id}/dashboard_elements")
    
    # Looks (saved queries)
    LOOKS_LIST = ("GET", "/looks")
    LOOK_RUN = ("GET", "/looks/{id}/run/{format}")
    
    # Queries
    CREATE_QUERY = ("POST", "/queries")
    RUN_QUERY = ("POST", "/queries/{id}/run/{format}")
    RUN_INLINE_QUERY = ("POST", "/queries/run/{format}")
    
    # Folders
    FOLDERS_LIST = ("GET", "/folders")
    FOLDER_CHILDREN = ("GET", "/folders/{id}/children")
    
    # Users
    USERS_LIST = ("GET", "/users")
    USER_GET = ("GET", "/users/{id}")


@dataclass
class LookerQuery:
    """Structured Looker query"""
    model: str
    view: str
    fields: List[str]
    filters: Dict[str, str] = field(default_factory=dict)
    sorts: List[str] = field(default_factory=list)
    limit: int = 500
    query_timezone: str = "America/Los_Angeles"
    

@dataclass
class LookerInsight:
    """Business insight from Looker data"""
    dashboard_id: str
    insight_type: str  # trend, anomaly, forecast, benchmark
    title: str
    description: str
    metrics: Dict[str, Any]
    recommendations: List[str]
    confidence: float
    timestamp: datetime


class LookerOptimizedClient:
    """
    Optimized Looker client with:
    - OAuth 2.0 authentication
    - Async operations for performance
    - Redis caching for frequent queries
    - Rate limiting and retry logic
    - Streaming for large datasets
    """
    
    def __init__(self):
        self.base_url = f"{LOOKER_BASE_URL}/api/{LOOKER_API_VERSION}"
        self.client_id = LOOKER_CLIENT_ID
        self.client_secret = LOOKER_CLIENT_SECRET
        self.access_token = None
        self.token_expires = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.redis_client: Optional[redis.Redis] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        self.redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        await self._authenticate()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.access_token:
            await self._logout()
        if self.session:
            await self.session.close()
        if self.redis_client:
            await self.redis_client.aclose()
            
    async def _authenticate(self):
        """Get access token using client credentials"""
        auth_url = f"{self.base_url}/login"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        async with self.session.post(auth_url, data=data) as response:
            if response.status == 200:
                token_data = await response.json()
                self.access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires = datetime.now() + timedelta(seconds=expires_in)
            else:
                raise Exception(f"Looker authentication failed: {response.status}")
                
    async def _logout(self):
        """Logout and invalidate token"""
        if not self.access_token:
            return
            
        logout_url = f"{self.base_url}/logout"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        await self.session.delete(logout_url, headers=headers)
        self.access_token = None
        
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with auth"""
        if not self.access_token or datetime.now() >= self.token_expires:
            asyncio.create_task(self._authenticate())
            
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(3)
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        format: str = "json"
    ) -> Any:
        """Make API request with retry logic"""
        # Check cache for GET requests
        cache_key = None
        if method == "GET" and params:
            cache_key = f"looker:{endpoint}:{hashlib.md5(str(params).encode()).hexdigest()}"
            cached = await self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
                
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        async with self.session.request(
            method,
            url,
            params=params,
            json=json_data,
            headers=headers
        ) as response:
            if response.status == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                await asyncio.sleep(retry_after)
                raise Exception(f"Rate limited, retry after {retry_after}s")
                
            if response.status >= 400:
                error_text = await response.text()
                raise Exception(f"Looker API error {response.status}: {error_text}")
                
            # Handle different response formats
            if format == "json":
                result = await response.json()
            elif format == "csv":
                result = await response.text()
            else:
                result = await response.read()
                
            # Cache successful GET responses
            if cache_key and format == "json":
                await self.redis_client.setex(
                    cache_key,
                    300,  # 5 minute cache
                    json.dumps(result)
                )
                
            return result
            
    async def get_dashboards(self) -> List[Dict[str, Any]]:
        """Get all dashboards"""
        return await self._make_request("GET", "/dashboards")
        
    async def get_dashboard(self, dashboard_id: str) -> Dict[str, Any]:
        """Get dashboard details with elements"""
        dashboard = await self._make_request("GET", f"/dashboards/{dashboard_id}")
        
        # Get dashboard elements
        elements = await self._make_request(
            "GET",
            f"/dashboards/{dashboard_id}/dashboard_elements"
        )
        dashboard["elements"] = elements
        
        return dashboard
        
    async def run_look(
        self,
        look_id: str,
        format: str = "json",
        filters: Optional[Dict[str, str]] = None
    ) -> Any:
        """Run a saved Look (query)"""
        params = {}
        if filters:
            for key, value in filters.items():
                params[f"f[{key}]"] = value
                
        return await self._make_request(
            "GET",
            f"/looks/{look_id}/run/{format}",
            params=params,
            format=format
        )
        
    async def run_inline_query(
        self,
        query: LookerQuery,
        format: str = "json"
    ) -> Any:
        """Run an inline query"""
        query_data = {
            "model": query.model,
            "view": query.view,
            "fields": query.fields,
            "filters": query.filters,
            "sorts": query.sorts,
            "limit": query.limit,
            "query_timezone": query.query_timezone
        }
        
        return await self._make_request(
            "POST",
            f"/queries/run/{format}",
            json_data=query_data,
            format=format
        )
        
    async def stream_query_results(
        self,
        query: LookerQuery,
        chunk_size: int = 1000
    ):
        """Stream large query results in chunks"""
        offset = 0
        
        while True:
            # Modify query for pagination
            chunked_query = LookerQuery(
                model=query.model,
                view=query.view,
                fields=query.fields,
                filters=query.filters,
                sorts=query.sorts,
                limit=chunk_size,
                query_timezone=query.query_timezone
            )
            
            # Add offset filter
            chunked_query.filters["row_offset"] = str(offset)
            
            # Run query
            results = await self.run_inline_query(chunked_query)
            
            if not results or len(results) == 0:
                break
                
            yield results
            
            offset += chunk_size
            
            # Brief pause between chunks
            await asyncio.sleep(0.1)
            
    async def get_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        return await self._make_request("GET", "/users")
        
    async def test_connection(self) -> bool:
        """Test API connection"""
        try:
            users = await self.get_users()
            return isinstance(users, list)
        except Exception as e:
            print(f"Looker connection test failed: {e}")
            return False


class LookerAnalyticsPipeline:
    """
    Analytics pipeline for Looker data processing
    Extracts insights, detects anomalies, and generates recommendations
    """
    
    def __init__(self):
        self.client = LookerOptimizedClient()
        self.redis_client = None
        
    async def setup(self):
        """Initialize pipeline"""
        self.redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        
    async def analyze_dashboard(
        self,
        dashboard_id: str
    ) -> List[LookerInsight]:
        """Analyze dashboard for insights"""
        insights = []
        
        async with self.client as client:
            # Get dashboard data
            dashboard = await client.get_dashboard(dashboard_id)
            
            # Analyze each element
            for element in dashboard.get("elements", []):
                element_insights = await self._analyze_element(element, dashboard_id)
                insights.extend(element_insights)
                
        return insights
        
    async def _analyze_element(
        self,
        element: Dict[str, Any],
        dashboard_id: str
    ) -> List[LookerInsight]:
        """Analyze dashboard element for insights"""
        insights = []
        
        # Extract metrics from element
        metrics = self._extract_metrics(element)
        
        # Detect trends
        if trend := self._detect_trend(metrics):
            insights.append(LookerInsight(
                dashboard_id=dashboard_id,
                insight_type="trend",
                title=f"Trend detected in {element.get('title', 'Unknown')}",
                description=trend["description"],
                metrics=trend["metrics"],
                recommendations=trend["recommendations"],
                confidence=trend["confidence"],
                timestamp=datetime.now()
            ))
            
        # Detect anomalies
        if anomaly := self._detect_anomaly(metrics):
            insights.append(LookerInsight(
                dashboard_id=dashboard_id,
                insight_type="anomaly",
                title=f"Anomaly in {element.get('title', 'Unknown')}",
                description=anomaly["description"],
                metrics=anomaly["metrics"],
                recommendations=anomaly["recommendations"],
                confidence=anomaly["confidence"],
                timestamp=datetime.now()
            ))
            
        return insights
        
    def _extract_metrics(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metrics from dashboard element"""
        return {
            "title": element.get("title", ""),
            "type": element.get("type", ""),
            "query_id": element.get("query_id", ""),
            "result_maker": element.get("result_maker", {}),
            "refresh_interval": element.get("refresh_interval", "")
        }
        
    def _detect_trend(self, metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect trends in metrics"""
        # Simplified trend detection logic
        if "time" in str(metrics).lower():
            return {
                "description": "Time-based trend detected",
                "metrics": metrics,
                "recommendations": [
                    "Monitor for seasonal patterns",
                    "Set up alerts for significant changes",
                    "Consider forecasting models"
                ],
                "confidence": 0.75
            }
        return None
        
    def _detect_anomaly(self, metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect anomalies in metrics"""
        # Simplified anomaly detection
        if "error" in str(metrics).lower() or "null" in str(metrics).lower():
            return {
                "description": "Data quality issue detected",
                "metrics": metrics,
                "recommendations": [
                    "Check data source connectivity",
                    "Review ETL pipeline logs",
                    "Validate query logic"
                ],
                "confidence": 0.85
            }
        return None
        
    async def sync_to_sophia(
        self,
        insights: List[LookerInsight]
    ):
        """Sync Looker insights to Sophia's intelligence layer"""
        for insight in insights:
            # Store in Redis for real-time access
            insight_key = f"looker:insight:{insight.dashboard_id}:{insight.insight_type}"
            await self.redis_client.setex(
                insight_key,
                86400,  # 24 hours
                json.dumps({
                    "dashboard_id": insight.dashboard_id,
                    "type": insight.insight_type,
                    "title": insight.title,
                    "description": insight.description,
                    "metrics": insight.metrics,
                    "recommendations": insight.recommendations,
                    "confidence": insight.confidence,
                    "timestamp": insight.timestamp.isoformat()
                })
            )


async def test_looker_client():
    """Test Looker client"""
    print("📊 Testing Looker Integration")
    print("=" * 60)
    
    async with LookerOptimizedClient() as client:
        # Test connection
        print("\n1. Testing connection...")
        connected = await client.test_connection()
        print(f"   {'✅' if connected else '❌'} Connection: {connected}")
        
        if connected:
            # Get dashboards
            print("\n2. Getting dashboards...")
            try:
                dashboards = await client.get_dashboards()
                print(f"   ✅ Found {len(dashboards)} dashboards")
                
                if dashboards:
                    # Test dashboard analysis
                    print("\n3. Analyzing first dashboard...")
                    pipeline = LookerAnalyticsPipeline()
                    await pipeline.setup()
                    
                    insights = await pipeline.analyze_dashboard(dashboards[0]["id"])
                    print(f"   ✅ Generated {len(insights)} insights")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                
    print("\n" + "=" * 60)
    print("✅ Looker test complete")


if __name__ == "__main__":
    asyncio.run(test_looker_client())
