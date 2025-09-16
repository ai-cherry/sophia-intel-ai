#!/usr/bin/env python3
"""
Optimized CRM Suite Integration (Airtable, Salesforce, HubSpot)
Implements best practices for each platform with unified interface
"""
import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import aiohttp
import redis.asyncio as redis
from simple_salesforce import Salesforce
from pyairtable import Api as AirtableApi
from hubspot import HubSpot
from tenacity import retry, stop_after_attempt, wait_exponential

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Airtable
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY", "patuojzcFCHtcwkH3.2d1b20fd467f58319534f2abb02899d32390e1db02ffa226aa08c084bd21ce5d")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "appYOUR_BASE_ID")

# Salesforce  
SALESFORCE_USERNAME = os.getenv("SALESFORCE_USERNAME", "your_username")
SALESFORCE_PASSWORD = os.getenv("SALESFORCE_PASSWORD", "your_password")
SALESFORCE_TOKEN = os.getenv("SALESFORCE_TOKEN", "your_token")
SALESFORCE_ACCESS_TOKEN = os.getenv("SALESFORCE_ACCESS_TOKEN", "6Cel800DDn000006Cu0y888Ux0000000MrlQC4spG19TPoqHKbMqJgoE535XYy6jdku0a8STJwI45vcRKiu1gsfm4TtDKbtZKXEBchnXJbw")
SALESFORCE_INSTANCE_URL = os.getenv("SALESFORCE_INSTANCE_URL", "https://YOUR_INSTANCE.salesforce.com")

# HubSpot
HUBSPOT_ACCESS_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN", "pat-na1-c1671bea-646a-4a61-a2da-33bd33528dc7")


@dataclass
class CRMRecord:
    """Unified CRM record structure"""
    id: str
    source: str  # airtable, salesforce, hubspot
    type: str  # contact, company, deal, etc.
    data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]


class AirtableOptimizedClient:
    """
    Optimized Airtable client for knowledge base and data sync
    """
    
    def __init__(self):
        self.api = AirtableApi(AIRTABLE_API_KEY)
        self.base_id = AIRTABLE_BASE_ID
        self.redis_client = None
        
    async def setup(self):
        """Initialize client"""
        self.redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        
    async def get_records(
        self,
        table_name: str,
        view: Optional[str] = None,
        formula: Optional[str] = None,
        max_records: int = 100
    ) -> List[Dict[str, Any]]:
        """Get records from Airtable"""
        cache_key = f"airtable:{self.base_id}:{table_name}:{view}:{formula}"
        
        # Check cache
        cached = await self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
            
        # Fetch from API
        table = self.api.table(self.base_id, table_name)
        records = []
        
        for page in table.iterate(
            view=view,
            formula=formula,
            max_records=max_records
        ):
            for record in page:
                records.append({
                    "id": record["id"],
                    "fields": record["fields"],
                    "created_time": record["createdTime"]
                })
                
        # Cache for 5 minutes
        await self.redis_client.setex(
            cache_key,
            300,
            json.dumps(records)
        )
        
        return records
        
    async def create_record(
        self,
        table_name: str,
        fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create record in Airtable"""
        table = self.api.table(self.base_id, table_name)
        record = table.create(fields)
        
        # Invalidate cache
        pattern = f"airtable:{self.base_id}:{table_name}:*"
        async for key in self.redis_client.scan_iter(match=pattern):
            await self.redis_client.delete(key)
            
        return record
        
    async def update_record(
        self,
        table_name: str,
        record_id: str,
        fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update record in Airtable"""
        table = self.api.table(self.base_id, table_name)
        record = table.update(record_id, fields)
        
        # Invalidate cache
        pattern = f"airtable:{self.base_id}:{table_name}:*"
        async for key in self.redis_client.scan_iter(match=pattern):
            await self.redis_client.delete(key)
            
        return record
        
    async def sync_to_knowledge_base(
        self,
        table_name: str,
        sync_field: str = "Knowledge"
    ):
        """Sync Airtable data to Sophia's knowledge base"""
        records = await self.get_records(table_name)
        
        for record in records:
            if knowledge := record["fields"].get(sync_field):
                # Store in Redis knowledge base
                key = f"knowledge:{table_name}:{record['id']}"
                await self.redis_client.setex(
                    key,
                    86400,  # 24 hours
                    json.dumps({
                        "source": "airtable",
                        "table": table_name,
                        "content": knowledge,
                        "metadata": record["fields"],
                        "updated": datetime.now().isoformat()
                    })
                )


class SalesforceOptimizedClient:
    """
    Optimized Salesforce client for CRM sync and opportunity tracking
    """
    
    def __init__(self):
        self.sf = None
        self.redis_client = None
        
    async def setup(self):
        """Initialize client"""
        self.redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        
        # Initialize Salesforce connection
        if SALESFORCE_ACCESS_TOKEN:
            self.sf = Salesforce(
                instance_url=SALESFORCE_INSTANCE_URL,
                session_id=SALESFORCE_ACCESS_TOKEN
            )
        else:
            self.sf = Salesforce(
                username=SALESFORCE_USERNAME,
                password=SALESFORCE_PASSWORD,
                security_token=SALESFORCE_TOKEN
            )
            
    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(3)
    )
    async def query(self, soql: str) -> List[Dict[str, Any]]:
        """Execute SOQL query"""
        cache_key = f"salesforce:query:{soql}"
        
        # Check cache
        cached = await self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
            
        # Execute query
        result = self.sf.query(soql)
        records = result.get("records", [])
        
        # Cache for 5 minutes
        await self.redis_client.setex(
            cache_key,
            300,
            json.dumps(records)
        )
        
        return records
        
    async def get_opportunities(
        self,
        stage: Optional[str] = None,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """Get opportunities"""
        date_filter = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        soql = f"""
            SELECT Id, Name, Amount, StageName, CloseDate, 
                   AccountId, Account.Name, Probability, NextStep
            FROM Opportunity
            WHERE LastModifiedDate >= {date_filter}T00:00:00Z
        """
        
        if stage:
            esc_stage = stage.replace("'", "\\'")
            soql += f" AND StageName = '{esc_stage}'"
            
        return await self.query(soql)
        
    async def get_contacts(
        self,
        account_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get contacts"""
        soql = """
            SELECT Id, FirstName, LastName, Email, Phone,
                   AccountId, Account.Name, Title, Department
            FROM Contact
        """
        
        if account_id:
            import re
            if not re.fullmatch(r"[a-zA-Z0-9]{15,18}", account_id or ""):
                raise ValueError("Invalid Salesforce AccountId format")
            soql += f" WHERE AccountId = '{account_id}'"
            
        return await self.query(soql)
        
    async def create_opportunity(
        self,
        name: str,
        amount: float,
        stage: str,
        close_date: str,
        account_id: str
    ) -> Dict[str, Any]:
        """Create opportunity"""
        result = self.sf.Opportunity.create({
            "Name": name,
            "Amount": amount,
            "StageName": stage,
            "CloseDate": close_date,
            "AccountId": account_id
        })
        
        # Invalidate cache
        pattern = "salesforce:query:*Opportunity*"
        async for key in self.redis_client.scan_iter(match=pattern):
            await self.redis_client.delete(key)
            
        return result
        
    async def update_opportunity(
        self,
        opportunity_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update opportunity"""
        result = self.sf.Opportunity.update(opportunity_id, updates)
        
        # Invalidate cache
        pattern = "salesforce:query:*Opportunity*"
        async for key in self.redis_client.scan_iter(match=pattern):
            await self.redis_client.delete(key)
            
        return result == 204
        
    async def track_opportunity_changes(self):
        """Track opportunity changes for insights"""
        opportunities = await self.get_opportunities(days_back=7)
        
        for opp in opportunities:
            # Store opportunity snapshot
            key = f"salesforce:opportunity:{opp['Id']}:snapshot"
            await self.redis_client.setex(
                key,
                604800,  # 7 days
                json.dumps({
                    "id": opp["Id"],
                    "name": opp["Name"],
                    "amount": opp.get("Amount", 0),
                    "stage": opp["StageName"],
                    "probability": opp.get("Probability", 0),
                    "close_date": opp["CloseDate"],
                    "snapshot_time": datetime.now().isoformat()
                })
            )


class HubSpotOptimizedClient:
    """
    Optimized HubSpot client for marketing automation and lead scoring
    """
    
    def __init__(self):
        self.client = HubSpot(access_token=HUBSPOT_ACCESS_TOKEN)
        self.redis_client = None
        
    async def setup(self):
        """Initialize client"""
        self.redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        
    async def get_contacts(
        self,
        limit: int = 100,
        properties: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Get contacts"""
        cache_key = f"hubspot:contacts:{limit}:{properties}"
        
        # Check cache
        cached = await self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
            
        # Fetch from API
        if properties is None:
            properties = ["email", "firstname", "lastname", "company", "lifecyclestage"]
            
        response = self.client.crm.contacts.basic_api.get_page(
            limit=limit,
            properties=properties
        )
        
        contacts = [contact.to_dict() for contact in response.results]
        
        # Cache for 5 minutes
        await self.redis_client.setex(
            cache_key,
            300,
            json.dumps(contacts)
        )
        
        return contacts
        
    async def get_companies(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get companies"""
        cache_key = f"hubspot:companies:{limit}"
        
        # Check cache
        cached = await self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
            
        # Fetch from API
        response = self.client.crm.companies.basic_api.get_page(limit=limit)
        companies = [company.to_dict() for company in response.results]
        
        # Cache for 5 minutes
        await self.redis_client.setex(
            cache_key,
            300,
            json.dumps(companies)
        )
        
        return companies
        
    async def get_deals(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get deals"""
        cache_key = f"hubspot:deals:{limit}"
        
        # Check cache
        cached = await self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
            
        # Fetch from API
        response = self.client.crm.deals.basic_api.get_page(limit=limit)
        deals = [deal.to_dict() for deal in response.results]
        
        # Cache for 5 minutes
        await self.redis_client.setex(
            cache_key,
            300,
            json.dumps(deals)
        )
        
        return deals
        
    async def score_lead(
        self,
        contact_id: str
    ) -> Dict[str, Any]:
        """Score a lead based on engagement and properties"""
        # Get contact details
        contact = self.client.crm.contacts.basic_api.get_by_id(
            contact_id,
            properties=["email", "lifecyclestage", "hs_analytics_source", 
                       "num_conversion_events", "hs_email_opens"]
        )
        
        # Calculate lead score
        score = 0
        factors = {}
        
        properties = contact.properties
        
        # Lifecycle stage scoring
        lifecycle_stage = properties.get("lifecyclestage", "")
        if lifecycle_stage == "marketingqualifiedlead":
            score += 30
            factors["lifecycle"] = 30
        elif lifecycle_stage == "lead":
            score += 20
            factors["lifecycle"] = 20
        elif lifecycle_stage == "subscriber":
            score += 10
            factors["lifecycle"] = 10
            
        # Engagement scoring
        email_opens = int(properties.get("hs_email_opens", 0))
        score += min(email_opens * 2, 20)
        factors["email_engagement"] = min(email_opens * 2, 20)
        
        conversions = int(properties.get("num_conversion_events", 0))
        score += min(conversions * 5, 25)
        factors["conversions"] = min(conversions * 5, 25)
        
        # Store lead score
        score_key = f"hubspot:lead_score:{contact_id}"
        await self.redis_client.setex(
            score_key,
            86400,  # 24 hours
            json.dumps({
                "contact_id": contact_id,
                "score": score,
                "factors": factors,
                "scored_at": datetime.now().isoformat()
            })
        )
        
        return {
            "contact_id": contact_id,
            "score": score,
            "factors": factors,
            "recommendation": self._get_lead_recommendation(score)
        }
        
    def _get_lead_recommendation(self, score: int) -> str:
        """Get recommendation based on lead score"""
        if score >= 70:
            return "Hot lead - immediate follow-up recommended"
        elif score >= 50:
            return "Warm lead - schedule demo or consultation"
        elif score >= 30:
            return "Nurture with targeted content"
        else:
            return "Continue monitoring engagement"
            
    async def create_marketing_campaign(
        self,
        name: str,
        subject: str,
        content: str,
        list_id: str
    ) -> Dict[str, Any]:
        """Create marketing campaign (email)"""
        # This would integrate with HubSpot Marketing Hub
        # Simplified for demonstration
        
        campaign_data = {
            "name": name,
            "subject": subject,
            "content": content,
            "list_id": list_id,
            "created_at": datetime.now().isoformat()
        }
        
        # Store campaign
        campaign_key = f"hubspot:campaign:{name}"
        await self.redis_client.setex(
            campaign_key,
            604800,  # 7 days
            json.dumps(campaign_data)
        )
        
        return campaign_data


class UnifiedCRMOrchestrator:
    """
    Orchestrates data across all CRM platforms
    """
    
    def __init__(self):
        self.airtable = AirtableOptimizedClient()
        self.salesforce = SalesforceOptimizedClient()
        self.hubspot = HubSpotOptimizedClient()
        self.redis_client = None
        
    async def setup(self):
        """Initialize all clients"""
        self.redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        await self.airtable.setup()
        await self.salesforce.setup()
        await self.hubspot.setup()
        
    async def sync_all_contacts(self) -> Dict[str, int]:
        """Sync contacts across all platforms"""
        results = {
            "airtable": 0,
            "salesforce": 0,
            "hubspot": 0,
            "unified": 0
        }
        
        # Get contacts from each platform
        try:
            airtable_contacts = await self.airtable.get_records("Contacts")
            results["airtable"] = len(airtable_contacts)
        except:
            airtable_contacts = []
            
        try:
            salesforce_contacts = await self.salesforce.get_contacts()
            results["salesforce"] = len(salesforce_contacts)
        except:
            salesforce_contacts = []
            
        try:
            hubspot_contacts = await self.hubspot.get_contacts()
            results["hubspot"] = len(hubspot_contacts)
        except:
            hubspot_contacts = []
            
        # Create unified contact records
        unified_contacts = []
        
        for contact in airtable_contacts:
            unified_contacts.append(CRMRecord(
                id=contact["id"],
                source="airtable",
                type="contact",
                data=contact["fields"],
                created_at=datetime.fromisoformat(contact["created_time"]),
                updated_at=datetime.now(),
                metadata={}
            ))
            
        for contact in salesforce_contacts:
            unified_contacts.append(CRMRecord(
                id=contact["Id"],
                source="salesforce",
                type="contact",
                data=contact,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata={}
            ))
            
        for contact in hubspot_contacts:
            unified_contacts.append(CRMRecord(
                id=contact["id"],
                source="hubspot",
                type="contact",
                data=contact.get("properties", {}),
                created_at=datetime.fromisoformat(contact["created_at"]),
                updated_at=datetime.fromisoformat(contact["updated_at"]),
                metadata={}
            ))
            
        # Store unified records
        for record in unified_contacts:
            key = f"crm:unified:contact:{record.source}:{record.id}"
            await self.redis_client.setex(
                key,
                86400,  # 24 hours
                json.dumps({
                    "id": record.id,
                    "source": record.source,
                    "type": record.type,
                    "data": record.data,
                    "created_at": record.created_at.isoformat(),
                    "updated_at": record.updated_at.isoformat(),
                    "metadata": record.metadata
                })
            )
            
        results["unified"] = len(unified_contacts)
        return results


async def test_crm_suite():
    """Test CRM suite integrations"""
    print("🏢 Testing CRM Suite Integrations")
    print("=" * 60)
    
    orchestrator = UnifiedCRMOrchestrator()
    await orchestrator.setup()
    
    # Test each platform
    print("\n1. Testing Airtable...")
    try:
        records = await orchestrator.airtable.get_records("Contacts", max_records=5)
        print(f"   ✅ Airtable: {len(records)} records")
    except Exception as e:
        print(f"   ❌ Airtable: {e}")
        
    print("\n2. Testing Salesforce...")
    try:
        opps = await orchestrator.salesforce.get_opportunities(days_back=7)
        print(f"   ✅ Salesforce: {len(opps)} opportunities")
    except Exception as e:
        print(f"   ❌ Salesforce: {e}")
        
    print("\n3. Testing HubSpot...")
    try:
        contacts = await orchestrator.hubspot.get_contacts(limit=5)
        print(f"   ✅ HubSpot: {len(contacts)} contacts")
    except Exception as e:
        print(f"   ❌ HubSpot: {e}")
        
    print("\n4. Testing unified sync...")
    try:
        results = await orchestrator.sync_all_contacts()
        print(f"   ✅ Unified sync complete:")
        for platform, count in results.items():
            print(f"      {platform}: {count} records")
    except Exception as e:
        print(f"   ❌ Sync error: {e}")
        
    print("\n" + "=" * 60)
    print("✅ CRM Suite test complete")


if __name__ == "__main__":
    asyncio.run(test_crm_suite())
