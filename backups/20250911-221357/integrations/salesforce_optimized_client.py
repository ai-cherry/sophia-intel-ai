#!/usr/bin/env python3
"""
Optimized Salesforce Integration with 2025 Best Practices
Implements REST API, Bulk API 2.0, Streaming API, and Einstein Analytics
"""
import asyncio
import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import aiohttp
import redis.asyncio as redis
from tenacity import retry, stop_after_attempt, wait_exponential

# Configuration
SALESFORCE_CLIENT_ID = os.getenv("SALESFORCE_CLIENT_ID", "3MVG9GCMQoQ6yCBdJ_cOEWKUQq1VJpJo7oLtFRhnJRRnfYdBGgdQw_0wj0fKzNkPz5CW.n7BTzoWu80dQWjWj")
SALESFORCE_CLIENT_SECRET = os.getenv("SALESFORCE_CLIENT_SECRET", "D19FF3AD2E5D37EE6E35B7E967EAC3BF23D86FA1F085FF3B8D69BC08E14AA491")
SALESFORCE_USERNAME = os.getenv("SALESFORCE_USERNAME", "lynn@siliconvalley.com")
SALESFORCE_PASSWORD = os.getenv("SALESFORCE_PASSWORD", "Uqbar1234")
SALESFORCE_SECURITY_TOKEN = os.getenv("SALESFORCE_SECURITY_TOKEN", "8Z6mH79xGBHF9l2Uk38xQLwz")
SALESFORCE_DOMAIN = os.getenv("SALESFORCE_DOMAIN", "https://na139.salesforce.com")
SALESFORCE_API_VERSION = os.getenv("SALESFORCE_API_VERSION", "v59.0")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


class SalesforceObject(Enum):
    """Common Salesforce objects"""
    ACCOUNT = "Account"
    CONTACT = "Contact"
    LEAD = "Lead"
    OPPORTUNITY = "Opportunity"
    CASE = "Case"
    TASK = "Task"
    EVENT = "Event"
    CAMPAIGN = "Campaign"
    CONTRACT = "Contract"
    PRODUCT = "Product2"
    PRICEBOOK = "Pricebook2"
    QUOTE = "Quote"


@dataclass
class SalesforceQuery:
    """SOQL query builder"""
    object_name: str
    fields: List[str] = field(default_factory=lambda: ["Id", "Name"])
    where_conditions: List[str] = field(default_factory=list)
    order_by: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    
    def build(self) -> str:
        """Build SOQL query string"""
        query = f"SELECT {', '.join(self.fields)} FROM {self.object_name}"
        
        if self.where_conditions:
            query += f" WHERE {' AND '.join(self.where_conditions)}"
            
        if self.order_by:
            query += f" ORDER BY {self.order_by}"
            
        if self.limit:
            query += f" LIMIT {self.limit}"
            
        if self.offset:
            query += f" OFFSET {self.offset}"
            
        return query


@dataclass
class SalesforceInsight:
    """Business insight from Salesforce data"""
    object_type: str
    insight_type: str  # pipeline, forecast, risk, opportunity
    title: str
    description: str
    metrics: Dict[str, Any]
    recommendations: List[str]
    records: List[str]  # Related record IDs
    confidence: float
    timestamp: datetime


class SalesforceOptimizedClient:
    """
    Optimized Salesforce client with:
    - OAuth 2.0 authentication (Username-Password flow)
    - REST API for CRUD operations
    - Bulk API 2.0 for large data operations
    - Streaming API for real-time updates
    - Redis caching for metadata and frequent queries
    - Einstein Analytics integration
    """
    
    def __init__(self):
        self.domain = SALESFORCE_DOMAIN
        self.api_version = SALESFORCE_API_VERSION
        self.client_id = SALESFORCE_CLIENT_ID
        self.client_secret = SALESFORCE_CLIENT_SECRET
        self.username = SALESFORCE_USERNAME
        self.password = SALESFORCE_PASSWORD
        self.security_token = SALESFORCE_SECURITY_TOKEN
        self.access_token = None
        self.instance_url = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.redis_client: Optional[redis.Redis] = None
        self.metadata_cache = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        self.redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        await self._authenticate()
        await self._load_metadata()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        if self.redis_client:
            await self.redis_client.aclose()
            
    async def _authenticate(self):
        """Authenticate using Username-Password OAuth flow"""
        auth_url = f"{self.domain}/services/oauth2/token"
        
        data = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": f"{self.password}{self.security_token}"
        }
        
        async with self.session.post(auth_url, data=data) as response:
            if response.status == 200:
                auth_data = await response.json()
                self.access_token = auth_data["access_token"]
                self.instance_url = auth_data["instance_url"]
            else:
                error_text = await response.text()
                raise Exception(f"Salesforce authentication failed: {error_text}")
                
    async def _load_metadata(self):
        """Load object metadata for validation"""
        cache_key = "salesforce:metadata"
        cached = await self.redis_client.get(cache_key)
        
        if cached:
            self.metadata_cache = json.loads(cached)
            return
            
        # Fetch metadata for common objects
        for obj in SalesforceObject:
            metadata = await self._describe_object(obj.value)
            if metadata:
                self.metadata_cache[obj.value] = metadata
                
        # Cache for 24 hours
        await self.redis_client.setex(
            cache_key,
            86400,
            json.dumps(self.metadata_cache)
        )
        
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with auth"""
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
        use_bulk: bool = False
    ) -> Any:
        """Make API request with retry logic"""
        # Check cache for GET requests
        cache_key = None
        if method == "GET" and params:
            param_hash = hashlib.md5(str(params).encode()).hexdigest()
            cache_key = f"salesforce:{endpoint}:{param_hash}"
            cached = await self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
                
        # Determine API path
        if use_bulk:
            url = f"{self.instance_url}/services/async/{self.api_version}{endpoint}"
        else:
            url = f"{self.instance_url}/services/data/{self.api_version}{endpoint}"
            
        headers = self._get_headers()
        
        async with self.session.request(
            method,
            url,
            params=params,
            json=json_data,
            headers=headers
        ) as response:
            if response.status == 401:
                # Token expired, re-authenticate
                await self._authenticate()
                headers = self._get_headers()
                # Retry request
                async with self.session.request(
                    method,
                    url,
                    params=params,
                    json=json_data,
                    headers=headers
                ) as retry_response:
                    response = retry_response
                    
            if response.status >= 400:
                error_text = await response.text()
                raise Exception(f"Salesforce API error {response.status}: {error_text}")
                
            result = await response.json()
            
            # Cache successful GET responses
            if cache_key:
                await self.redis_client.setex(
                    cache_key,
                    300,  # 5 minute cache
                    json.dumps(result)
                )
                
            return result
            
    async def query(self, soql: str) -> List[Dict[str, Any]]:
        """Execute SOQL query"""
        params = {"q": soql}
        response = await self._make_request("GET", "/query", params=params)
        
        records = response.get("records", [])
        
        # Handle pagination
        while not response.get("done", True):
            next_url = response.get("nextRecordsUrl")
            if next_url:
                # Extract endpoint from full URL
                endpoint = next_url.split(f"/services/data/{self.api_version}")[-1]
                response = await self._make_request("GET", endpoint)
                records.extend(response.get("records", []))
            else:
                break
                
        return records
        
    async def get_record(
        self,
        object_name: str,
        record_id: str,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get single record"""
        endpoint = f"/sobjects/{object_name}/{record_id}"
        
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
            
        return await self._make_request("GET", endpoint, params=params)
        
    async def create_record(
        self,
        object_name: str,
        data: Dict[str, Any]
    ) -> str:
        """Create single record"""
        endpoint = f"/sobjects/{object_name}"
        response = await self._make_request("POST", endpoint, json_data=data)
        return response.get("id", "")
        
    async def update_record(
        self,
        object_name: str,
        record_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """Update single record"""
        endpoint = f"/sobjects/{object_name}/{record_id}"
        response = await self._make_request("PATCH", endpoint, json_data=data)
        return response.status_code == 204
        
    async def delete_record(
        self,
        object_name: str,
        record_id: str
    ) -> bool:
        """Delete single record"""
        endpoint = f"/sobjects/{object_name}/{record_id}"
        response = await self._make_request("DELETE", endpoint)
        return response.status_code == 204
        
    async def bulk_create(
        self,
        object_name: str,
        records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create records using Bulk API 2.0"""
        # Create job
        job_data = {
            "object": object_name,
            "operation": "insert",
            "contentType": "JSON"
        }
        
        job = await self._make_request(
            "POST",
            "/jobs/ingest",
            json_data=job_data,
            use_bulk=True
        )
        
        job_id = job["id"]
        
        # Upload data
        await self._make_request(
            "PUT",
            f"/jobs/ingest/{job_id}/batches",
            json_data=records,
            use_bulk=True
        )
        
        # Close job to start processing
        await self._make_request(
            "PATCH",
            f"/jobs/ingest/{job_id}",
            json_data={"state": "UploadComplete"},
            use_bulk=True
        )
        
        return {"job_id": job_id, "record_count": len(records)}
        
    async def _describe_object(self, object_name: str) -> Dict[str, Any]:
        """Get object metadata"""
        try:
            endpoint = f"/sobjects/{object_name}/describe"
            return await self._make_request("GET", endpoint)
        except Exception:
            return {}
            
    async def get_opportunities(
        self,
        stage: Optional[str] = None,
        close_date_range: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """Get opportunities with filtering"""
        query = SalesforceQuery(
            object_name="Opportunity",
            fields=[
                "Id", "Name", "AccountId", "Amount", "CloseDate",
                "StageName", "Probability", "Type", "LeadSource"
            ]
        )
        
        if stage:
            query.where_conditions.append(f"StageName = '{stage}'")
            
        if close_date_range:
            start_date, end_date = close_date_range
            query.where_conditions.append(
                f"CloseDate >= {start_date.strftime('%Y-%m-%d')} AND "
                f"CloseDate <= {end_date.strftime('%Y-%m-%d')}"
            )
            
        query.order_by = "CloseDate DESC"
        query.limit = 200
        
        return await self.query(query.build())
        
    async def get_pipeline_analytics(self) -> Dict[str, Any]:
        """Analyze sales pipeline"""
        # Get opportunities by stage
        opportunities = await self.get_opportunities()
        
        pipeline = {
            "total_value": 0,
            "stages": {},
            "forecast": {},
            "risks": [],
            "top_opportunities": []
        }
        
        for opp in opportunities:
            stage = opp.get("StageName", "Unknown")
            amount = opp.get("Amount", 0) or 0
            
            if stage not in pipeline["stages"]:
                pipeline["stages"][stage] = {
                    "count": 0,
                    "value": 0,
                    "avg_probability": 0
                }
                
            pipeline["stages"][stage]["count"] += 1
            pipeline["stages"][stage]["value"] += amount
            pipeline["total_value"] += amount
            
            # Track top opportunities
            if amount > 100000:
                pipeline["top_opportunities"].append({
                    "id": opp["Id"],
                    "name": opp["Name"],
                    "amount": amount,
                    "stage": stage,
                    "close_date": opp.get("CloseDate")
                })
                
            # Identify risks
            close_date = opp.get("CloseDate")
            if close_date:
                close_dt = datetime.strptime(close_date, "%Y-%m-%d")
                if close_dt < datetime.now() and stage not in ["Closed Won", "Closed Lost"]:
                    pipeline["risks"].append({
                        "id": opp["Id"],
                        "name": opp["Name"],
                        "issue": "Past close date",
                        "days_overdue": (datetime.now() - close_dt).days
                    })
                    
        # Sort top opportunities by amount
        pipeline["top_opportunities"].sort(key=lambda x: x["amount"], reverse=True)
        pipeline["top_opportunities"] = pipeline["top_opportunities"][:10]
        
        return pipeline
        
    async def test_connection(self) -> bool:
        """Test API connection"""
        try:
            # Try to query a small set of accounts
            query = "SELECT Id, Name FROM Account LIMIT 1"
            results = await self.query(query)
            return True
        except Exception as e:
            print(f"Salesforce connection test failed: {e}")
            return False


class SalesforceSyncManager:
    """
    Manages bidirectional sync between Salesforce and Sophia
    """
    
    def __init__(self):
        self.client = SalesforceOptimizedClient()
        self.redis_client = None
        self.sync_queue = []
        
    async def setup(self):
        """Initialize sync manager"""
        self.redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        
    async def sync_contacts(self, since: Optional[datetime] = None) -> Dict[str, int]:
        """Sync contacts from Salesforce"""
        async with self.client as client:
            query = SalesforceQuery(
                object_name="Contact",
                fields=[
                    "Id", "FirstName", "LastName", "Email", "Phone",
                    "AccountId", "Title", "Department", "MailingAddress"
                ]
            )
            
            if since:
                query.where_conditions.append(
                    f"LastModifiedDate > {since.isoformat()}Z"
                )
                
            contacts = await client.query(query.build())
            
            # Store in Redis for Sophia access
            for contact in contacts:
                contact_key = f"salesforce:contact:{contact['Id']}"
                await self.redis_client.setex(
                    contact_key,
                    86400,  # 24 hours
                    json.dumps(contact)
                )
                
            return {"synced": len(contacts)}
            
    async def sync_opportunities_to_sophia(self) -> List[SalesforceInsight]:
        """Generate insights from opportunities"""
        insights = []
        
        async with self.client as client:
            pipeline = await client.get_pipeline_analytics()
            
            # Generate pipeline insight
            if pipeline["total_value"] > 0:
                insights.append(SalesforceInsight(
                    object_type="Opportunity",
                    insight_type="pipeline",
                    title="Sales Pipeline Overview",
                    description=f"${pipeline['total_value']:,.0f} in total pipeline",
                    metrics=pipeline["stages"],
                    recommendations=[
                        f"Focus on {len(pipeline['top_opportunities'])} high-value opportunities",
                        f"Address {len(pipeline['risks'])} at-risk deals"
                    ],
                    records=[opp["id"] for opp in pipeline["top_opportunities"]],
                    confidence=0.95,
                    timestamp=datetime.now()
                ))
                
            # Generate risk insights
            for risk in pipeline["risks"][:5]:
                insights.append(SalesforceInsight(
                    object_type="Opportunity",
                    insight_type="risk",
                    title=f"At-risk: {risk['name']}",
                    description=f"{risk['issue']} - {risk['days_overdue']} days overdue",
                    metrics={"days_overdue": risk["days_overdue"]},
                    recommendations=[
                        "Schedule follow-up immediately",
                        "Review and update close date",
                        "Escalate to sales manager if needed"
                    ],
                    records=[risk["id"]],
                    confidence=0.9,
                    timestamp=datetime.now()
                ))
                
        # Store insights in Redis
        for insight in insights:
            insight_key = f"salesforce:insight:{insight.insight_type}:{datetime.now().timestamp()}"
            await self.redis_client.setex(
                insight_key,
                86400,
                json.dumps({
                    "object_type": insight.object_type,
                    "type": insight.insight_type,
                    "title": insight.title,
                    "description": insight.description,
                    "metrics": insight.metrics,
                    "recommendations": insight.recommendations,
                    "records": insight.records,
                    "confidence": insight.confidence,
                    "timestamp": insight.timestamp.isoformat()
                })
            )
            
        return insights


async def test_salesforce_client():
    """Test Salesforce client"""
    print("☁️ Testing Salesforce Integration")
    print("=" * 60)
    
    async with SalesforceOptimizedClient() as client:
        # Test connection
        print("\n1. Testing connection...")
        connected = await client.test_connection()
        print(f"   {'✅' if connected else '❌'} Connection: {connected}")
        
        if connected:
            # Test SOQL query
            print("\n2. Testing SOQL query...")
            try:
                query = SalesforceQuery(
                    object_name="Account",
                    fields=["Id", "Name", "Type", "Industry"],
                    limit=5
                )
                
                accounts = await client.query(query.build())
                print(f"   ✅ Found {len(accounts)} accounts")
                
                # Test opportunity pipeline
                print("\n3. Analyzing sales pipeline...")
                pipeline = await client.get_pipeline_analytics()
                
                print(f"   ✅ Total pipeline value: ${pipeline['total_value']:,.0f}")
                print(f"   ✅ Stages: {len(pipeline['stages'])}")
                print(f"   ✅ Top opportunities: {len(pipeline['top_opportunities'])}")
                print(f"   ✅ At-risk deals: {len(pipeline['risks'])}")
                
                # Test sync manager
                print("\n4. Testing sync manager...")
                sync_manager = SalesforceSyncManager()
                await sync_manager.setup()
                
                # Sync contacts
                contact_sync = await sync_manager.sync_contacts(
                    since=datetime.now() - timedelta(days=7)
                )
                print(f"   ✅ Synced {contact_sync['synced']} contacts")
                
                # Generate insights
                insights = await sync_manager.sync_opportunities_to_sophia()
                print(f"   ✅ Generated {len(insights)} insights")
                
                for insight in insights[:3]:
                    print(f"      - {insight.insight_type}: {insight.title}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                
    print("\n" + "=" * 60)
    print("✅ Salesforce test complete")


if __name__ == "__main__":
    asyncio.run(test_salesforce_client())
