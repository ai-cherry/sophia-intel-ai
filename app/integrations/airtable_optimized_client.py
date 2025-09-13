#!/usr/bin/env python3
"""
Optimized Airtable Integration with 2025 Best Practices
Implements batch operations, metadata API, formula queries, and knowledge base sync
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
from config.unified_manager import get_config_manager
from tenacity import retry, stop_after_attempt, wait_exponential

# Configuration is loaded via UnifiedConfigManager in __init__


class AirtableEndpoint(Enum):
    """Airtable API endpoints"""
    # Bases
    BASES_LIST = ("GET", "/meta/bases")
    BASE_SCHEMA = ("GET", "/meta/bases/{baseId}/tables")
    
    # Tables
    TABLE_LIST = ("GET", "/{baseId}/{tableIdOrName}")
    RECORD_CREATE = ("POST", "/{baseId}/{tableIdOrName}")
    RECORD_UPDATE = ("PATCH", "/{baseId}/{tableIdOrName}/{recordId}")
    RECORD_DELETE = ("DELETE", "/{baseId}/{tableIdOrName}/{recordId}")
    BATCH_CREATE = ("POST", "/{baseId}/{tableIdOrName}")
    BATCH_UPDATE = ("PATCH", "/{baseId}/{tableIdOrName}")
    BATCH_DELETE = ("DELETE", "/{baseId}/{tableIdOrName}")


@dataclass
class AirtableRecord:
    """Structured Airtable record"""
    id: Optional[str] = None
    fields: Dict[str, Any] = field(default_factory=dict)
    created_time: Optional[datetime] = None
    table_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to API format"""
        result = {"fields": self.fields}
        if self.id:
            result["id"] = self.id
        return result


@dataclass
class AirtableFormula:
    """Formula builder for complex queries"""
    conditions: List[str] = field(default_factory=list)
    
    def add_condition(self, field: str, operator: str, value: Any):
        """Add filter condition"""
        if isinstance(value, str):
            value = f'"{value}"'
        elif isinstance(value, bool):
            value = "TRUE()" if value else "FALSE()"
        elif value is None:
            value = "BLANK()"
            
        condition = f"{{{field}}}{operator}{value}"
        self.conditions.append(condition)
        return self
        
    def build(self) -> str:
        """Build formula string"""
        if not self.conditions:
            return ""
        if len(self.conditions) == 1:
            return self.conditions[0]
        return f"AND({','.join(self.conditions)})"


@dataclass
class AirtableSync:
    """Sync configuration for knowledge base"""
    table_name: str
    sync_fields: List[str]
    last_sync: Optional[datetime] = None
    sync_interval: int = 300  # 5 minutes
    filter_formula: Optional[str] = None


class AirtableOptimizedClient:
    """
    Optimized Airtable client with:
    - Personal Access Token authentication
    - Batch operations for efficiency
    - Metadata API for schema discovery
    - Formula-based filtering
    - Redis caching for frequent queries
    - Automatic retry with exponential backoff
    """
    
    def __init__(self):
        cm = get_config_manager()
        cfg = cm.get_integration_config("airtable")
        # Normalize fields
        api_url = os.getenv("AIRTABLE_API_URL", "https://api.airtable.com/v0")
        self.base_id = cfg.get("base_id") or os.getenv("AIRTABLE_BASE_ID")
        self.api_url = api_url
        self.pat = cfg.get("api_key") or os.getenv("AIRTABLE_PAT")
        self.enabled = bool(cfg.get("enabled")) or bool(self.pat and self.base_id)
        self.session: Optional[aiohttp.ClientSession] = None
        self.redis_client: Optional[redis.Redis] = None
        self.schema_cache = {}
        if not self.enabled:
            raise ValueError("Airtable integration not enabled. Set AIRTABLE_ENABLED=true and provide AIRTABLE_PAT and AIRTABLE_BASE_ID.")
        if not self.pat or not self.base_id:
            raise ValueError("Airtable credentials missing (AIRTABLE_PAT and AIRTABLE_BASE_ID)")
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        cm = get_config_manager()
        redis_url = cm.get("REDIS_URL", os.getenv("REDIS_URL", "redis://localhost:6379"))
        self.redis_client = await redis.from_url(redis_url, decode_responses=True)
        await self._load_schema()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        if self.redis_client:
            await self.redis_client.aclose()
            
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with auth"""
        return {
            "Authorization": f"Bearer {self.pat}",
            "Content-Type": "application/json"
        }
        
    async def _load_schema(self):
        """Load table schema for validation"""
        if self.schema_cache:
            return
            
        cache_key = f"airtable:schema:{self.base_id}"
        cached = await self.redis_client.get(cache_key)
        
        if cached:
            self.schema_cache = json.loads(cached)
        else:
            # Fetch schema from metadata API
            url = f"https://api.airtable.com/v0/meta/bases/{self.base_id}/tables"
            headers = self._get_headers()
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    self.schema_cache = {
                        table["name"]: table
                        for table in data.get("tables", [])
                    }
                    
                    # Cache for 1 hour
                    await self.redis_client.setex(
                        cache_key,
                        3600,
                        json.dumps(self.schema_cache)
                    )
                    
    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(3)
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Union[Dict, List]] = None
    ) -> Any:
        """Make API request with retry logic"""
        # Check cache for GET requests
        cache_key = None
        if method == "GET" and params:
            param_hash = hashlib.md5(str(params).encode()).hexdigest()
            cache_key = f"airtable:{endpoint}:{param_hash}"
            cached = await self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
                
        url = f"{self.api_url}{endpoint}"
        headers = self._get_headers()
        
        async with self.session.request(
            method,
            url,
            params=params,
            json=json_data,
            headers=headers
        ) as response:
            if response.status == 429:
                # Rate limited - wait and retry
                retry_after = float(response.headers.get("Retry-After", 30))
                await asyncio.sleep(retry_after)
                raise Exception(f"Rate limited, retry after {retry_after}s")
                
            if response.status >= 400:
                error_text = await response.text()
                raise Exception(f"Airtable API error {response.status}: {error_text}")
                
            result = await response.json()
            
            # Cache successful GET responses
            if cache_key:
                await self.redis_client.setex(
                    cache_key,
                    300,  # 5 minute cache
                    json.dumps(result)
                )
                
            return result
            
    async def list_records(
        self,
        table_name: str,
        max_records: int = 100,
        view: Optional[str] = None,
        formula: Optional[str] = None,
        sort: Optional[List[Dict[str, str]]] = None,
        fields: Optional[List[str]] = None
    ) -> List[AirtableRecord]:
        """List records with filtering and sorting"""
        params = {"maxRecords": max_records}
        
        if view:
            params["view"] = view
        if formula:
            params["filterByFormula"] = formula
        if sort:
            params["sort"] = json.dumps(sort)
        if fields:
            params["fields"] = fields
            
        all_records = []
        offset = None
        
        while True:
            if offset:
                params["offset"] = offset
                
            response = await self._make_request(
                "GET",
                f"/{self.base_id}/{table_name}",
                params=params
            )
            
            records = response.get("records", [])
            for record in records:
                all_records.append(AirtableRecord(
                    id=record["id"],
                    fields=record["fields"],
                    created_time=datetime.fromisoformat(
                        record["createdTime"].replace("Z", "+00:00")
                    ),
                    table_name=table_name
                ))
                
            # Check for pagination
            offset = response.get("offset")
            if not offset:
                break
                
        return all_records
        
    async def create_record(
        self,
        table_name: str,
        fields: Dict[str, Any]
    ) -> AirtableRecord:
        """Create single record"""
        data = {"fields": fields}
        
        response = await self._make_request(
            "POST",
            f"/{self.base_id}/{table_name}",
            json_data=data
        )
        
        return AirtableRecord(
            id=response["id"],
            fields=response["fields"],
            created_time=datetime.fromisoformat(
                response["createdTime"].replace("Z", "+00:00")
            ),
            table_name=table_name
        )
        
    async def batch_create(
        self,
        table_name: str,
        records: List[Dict[str, Any]],
        typecast: bool = False
    ) -> List[AirtableRecord]:
        """Create multiple records (max 10 per request)"""
        created_records = []
        
        # Process in batches of 10
        for i in range(0, len(records), 10):
            batch = records[i:i+10]
            data = {
                "records": [{"fields": r} for r in batch],
                "typecast": typecast
            }
            
            response = await self._make_request(
                "POST",
                f"/{self.base_id}/{table_name}",
                json_data=data
            )
            
            for record in response.get("records", []):
                created_records.append(AirtableRecord(
                    id=record["id"],
                    fields=record["fields"],
                    created_time=datetime.fromisoformat(
                        record["createdTime"].replace("Z", "+00:00")
                    ),
                    table_name=table_name
                ))
                
        return created_records
        
    async def update_record(
        self,
        table_name: str,
        record_id: str,
        fields: Dict[str, Any],
        replace: bool = False
    ) -> AirtableRecord:
        """Update single record"""
        data = {"fields": fields}
        
        method = "PUT" if replace else "PATCH"
        response = await self._make_request(
            method,
            f"/{self.base_id}/{table_name}/{record_id}",
            json_data=data
        )
        
        return AirtableRecord(
            id=response["id"],
            fields=response["fields"],
            table_name=table_name
        )
        
    async def batch_update(
        self,
        table_name: str,
        updates: List[Dict[str, Any]],
        replace: bool = False
    ) -> List[AirtableRecord]:
        """Update multiple records"""
        updated_records = []
        
        # Process in batches of 10
        for i in range(0, len(updates), 10):
            batch = updates[i:i+10]
            data = {
                "records": batch,
                "typecast": False
            }
            
            method = "PUT" if replace else "PATCH"
            response = await self._make_request(
                method,
                f"/{self.base_id}/{table_name}",
                json_data=data
            )
            
            for record in response.get("records", []):
                updated_records.append(AirtableRecord(
                    id=record["id"],
                    fields=record["fields"],
                    table_name=table_name
                ))
                
        return updated_records
        
    async def delete_record(
        self,
        table_name: str,
        record_id: str
    ) -> bool:
        """Delete single record"""
        response = await self._make_request(
            "DELETE",
            f"/{self.base_id}/{table_name}/{record_id}"
        )
        
        return response.get("deleted", False)
        
    async def search_records(
        self,
        table_name: str,
        search_field: str,
        search_value: str,
        exact_match: bool = False
    ) -> List[AirtableRecord]:
        """Search records by field value"""
        if exact_match:
            formula = f"{{{search_field}}}='{search_value}'"
        else:
            formula = f"FIND(LOWER('{search_value}'), LOWER({{{search_field}}}))"
            
        return await self.list_records(
            table_name,
            formula=formula
        )
        
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get table schema from cache"""
        if not self.schema_cache:
            await self._load_schema()
        return self.schema_cache.get(table_name, {})
        
    async def test_connection(self) -> bool:
        """Test API connection"""
        try:
            # Try to fetch first record from first available table
            if self.schema_cache:
                table_name = list(self.schema_cache.keys())[0]
                records = await self.list_records(table_name, max_records=1)
                return True
            return False
        except Exception as e:
            print(f"Airtable connection test failed: {e}")
            return False


class AirtableKnowledgeBase:
    """
    Knowledge base synchronization for Airtable data
    Maintains a synchronized view of important tables for AI processing
    """
    
    def __init__(self):
        self.client = AirtableOptimizedClient()
        self.redis_client = None
        self.sync_configs: List[AirtableSync] = []
        
    async def setup(self):
        """Initialize knowledge base"""
        self.redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        
        # Define tables to sync
        self.sync_configs = [
            AirtableSync(
                table_name="Contacts",
                sync_fields=["Name", "Email", "Company", "Role", "Status"],
                filter_formula="NOT({Status}='Archived')"
            ),
            AirtableSync(
                table_name="Projects",
                sync_fields=["Name", "Status", "Owner", "Due Date", "Priority"],
                filter_formula="OR({Status}='Active', {Status}='Planning')"
            ),
            AirtableSync(
                table_name="Tasks",
                sync_fields=["Title", "Assignee", "Status", "Priority", "Due Date"],
                filter_formula="NOT({Status}='Completed')"
            ),
        ]
        
    async def sync_table(self, sync_config: AirtableSync) -> int:
        """Sync single table to knowledge base"""
        async with self.client as client:
            # Check if sync is needed
            cache_key = f"airtable:sync:{sync_config.table_name}:last"
            last_sync_str = await self.redis_client.get(cache_key)
            
            if last_sync_str:
                last_sync = datetime.fromisoformat(last_sync_str)
                if datetime.now() - last_sync < timedelta(seconds=sync_config.sync_interval):
                    return 0  # Skip sync
                    
            # Fetch records
            records = await client.list_records(
                sync_config.table_name,
                formula=sync_config.filter_formula,
                fields=sync_config.sync_fields
            )
            
            # Store in knowledge base
            knowledge_key = f"airtable:knowledge:{sync_config.table_name}"
            knowledge_data = [
                {
                    "id": record.id,
                    "fields": record.fields,
                    "table": sync_config.table_name
                }
                for record in records
            ]
            
            await self.redis_client.setex(
                knowledge_key,
                86400,  # 24 hours
                json.dumps(knowledge_data)
            )
            
            # Update last sync time
            await self.redis_client.set(cache_key, datetime.now().isoformat())
            
            return len(records)
            
    async def sync_all(self) -> Dict[str, int]:
        """Sync all configured tables"""
        results = {}
        
        for sync_config in self.sync_configs:
            count = await self.sync_table(sync_config)
            results[sync_config.table_name] = count
            
        return results
        
    async def query_knowledge(
        self,
        query: str,
        table_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query knowledge base"""
        results = []
        
        # Determine which tables to search
        tables = [table_name] if table_name else [s.table_name for s in self.sync_configs]
        
        for table in tables:
            knowledge_key = f"airtable:knowledge:{table}"
            data = await self.redis_client.get(knowledge_key)
            
            if data:
                records = json.loads(data)
                
                # Simple text search (can be enhanced with vector search)
                for record in records:
                    record_text = json.dumps(record["fields"]).lower()
                    if query.lower() in record_text:
                        results.append(record)
                        
        return results
        
    async def get_insights(self) -> Dict[str, Any]:
        """Generate insights from knowledge base"""
        insights = {
            "summary": {},
            "alerts": [],
            "trends": []
        }
        
        for sync_config in self.sync_configs:
            knowledge_key = f"airtable:knowledge:{sync_config.table_name}"
            data = await self.redis_client.get(knowledge_key)
            
            if data:
                records = json.loads(data)
                insights["summary"][sync_config.table_name] = {
                    "total": len(records),
                    "last_sync": sync_config.last_sync.isoformat() if sync_config.last_sync else None
                }
                
                # Detect overdue items
                if "Due Date" in sync_config.sync_fields:
                    overdue = [
                        r for r in records
                        if r["fields"].get("Due Date") and
                        datetime.fromisoformat(r["fields"]["Due Date"]) < datetime.now()
                    ]
                    
                    if overdue:
                        insights["alerts"].append({
                            "type": "overdue",
                            "table": sync_config.table_name,
                            "count": len(overdue),
                            "items": overdue[:5]  # First 5
                        })
                        
        return insights


async def test_airtable_client():
    """Test Airtable client"""
    print("📊 Testing Airtable Integration")
    print("=" * 60)
    
    async with AirtableOptimizedClient() as client:
        # Test connection
        print("\n1. Testing connection...")
        connected = await client.test_connection()
        print(f"   {'✅' if connected else '❌'} Connection: {connected}")
        
        if connected:
            # Get schema
            print("\n2. Loading table schema...")
            try:
                schema = client.schema_cache
                print(f"   ✅ Found {len(schema)} tables")
                
                if schema:
                    # List records from first table
                    table_name = list(schema.keys())[0]
                    print(f"\n3. Listing records from '{table_name}'...")
                    
                    records = await client.list_records(table_name, max_records=5)
                    print(f"   ✅ Retrieved {len(records)} records")
                    
                    # Test formula query
                    print("\n4. Testing formula query...")
                    formula_builder = AirtableFormula()
                    formula_builder.add_condition("Status", "=", "Active")
                    formula = formula_builder.build()
                    
                    filtered = await client.list_records(
                        table_name,
                        formula=formula,
                        max_records=5
                    )
                    print(f"   ✅ Formula query returned {len(filtered)} records")
                    
                    # Test knowledge base sync
                    print("\n5. Testing knowledge base sync...")
                    kb = AirtableKnowledgeBase()
                    await kb.setup()
                    
                    sync_results = await kb.sync_all()
                    print(f"   ✅ Synced tables: {sync_results}")
                    
                    # Get insights
                    insights = await kb.get_insights()
                    print(f"   ✅ Generated insights with {len(insights['alerts'])} alerts")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                
    print("\n" + "=" * 60)
    print("✅ Airtable test complete")


if __name__ == "__main__":
    asyncio.run(test_airtable_client())
