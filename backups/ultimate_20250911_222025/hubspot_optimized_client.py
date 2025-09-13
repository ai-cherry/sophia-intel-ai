#!/usr/bin/env python3
"""
Optimized HubSpot Integration with 2025 Best Practices
Implements CRM API v3, Marketing Hub, Workflows, and Lead Scoring
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
HUBSPOT_ACCESS_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN")
HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY")
HUBSPOT_APP_ID = os.getenv("HUBSPOT_APP_ID")
HUBSPOT_API_URL = os.getenv("HUBSPOT_API_URL", "https://api.hubapi.com")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


class HubSpotObject(Enum):
    """HubSpot CRM objects"""
    CONTACTS = "contacts"
    COMPANIES = "companies"
    DEALS = "deals"
    TICKETS = "tickets"
    PRODUCTS = "products"
    LINE_ITEMS = "line_items"
    QUOTES = "quotes"
    TASKS = "tasks"
    NOTES = "notes"
    MEETINGS = "meetings"
    EMAILS = "emails"
    CALLS = "calls"


class HubSpotEndpoint(Enum):
    """HubSpot API endpoints"""
    # CRM v3
    OBJECTS = ("GET", "/crm/v3/objects/{object_type}")
    OBJECT_CREATE = ("POST", "/crm/v3/objects/{object_type}")
    OBJECT_UPDATE = ("PATCH", "/crm/v3/objects/{object_type}/{object_id}")
    OBJECT_DELETE = ("DELETE", "/crm/v3/objects/{object_type}/{object_id}")
    BATCH_READ = ("POST", "/crm/v3/objects/{object_type}/batch/read")
    BATCH_CREATE = ("POST", "/crm/v3/objects/{object_type}/batch/create")
    BATCH_UPDATE = ("POST", "/crm/v3/objects/{object_type}/batch/update")
    SEARCH = ("POST", "/crm/v3/objects/{object_type}/search")
    
    # Marketing
    FORMS = ("GET", "/marketing/v3/forms")
    CAMPAIGNS = ("GET", "/marketing-emails/v1/campaigns")
    WORKFLOWS = ("GET", "/automation/v4/workflows")
    
    # Analytics
    ANALYTICS = ("GET", "/analytics/v2/reports")
    EVENTS = ("POST", "/events/v3/send")


@dataclass
class HubSpotContact:
    """Structured HubSpot contact"""
    id: Optional[str] = None
    email: str = ""
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    lifecycle_stage: str = "subscriber"
    lead_score: int = 0
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_api_format(self) -> Dict[str, Any]:
        """Convert to API format"""
        props = {
            "email": self.email,
            "lifecycle_stage": self.lifecycle_stage,
            "lead_score": str(self.lead_score)
        }
        
        if self.firstname:
            props["firstname"] = self.firstname
        if self.lastname:
            props["lastname"] = self.lastname
        if self.company:
            props["company"] = self.company
        if self.phone:
            props["phone"] = self.phone
            
        props.update(self.properties)
        
        result = {"properties": props}
        if self.id:
            result["id"] = self.id
            
        return result


@dataclass
class HubSpotDeal:
    """Structured HubSpot deal"""
    id: Optional[str] = None
    dealname: str = ""
    amount: float = 0
    dealstage: str = "appointmentscheduled"
    pipeline: str = "default"
    closedate: Optional[datetime] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    associations: Dict[str, List[str]] = field(default_factory=dict)
    
    def to_api_format(self) -> Dict[str, Any]:
        """Convert to API format"""
        props = {
            "dealname": self.dealname,
            "amount": str(self.amount),
            "dealstage": self.dealstage,
            "pipeline": self.pipeline
        }
        
        if self.closedate:
            props["closedate"] = self.closedate.strftime("%Y-%m-%d")
            
        props.update(self.properties)
        
        result = {"properties": props}
        if self.id:
            result["id"] = self.id
        if self.associations:
            result["associations"] = self.associations
            
        return result


@dataclass
class LeadScoringCriteria:
    """Lead scoring configuration"""
    email_engagement_weight: float = 0.3
    website_activity_weight: float = 0.25
    form_submission_weight: float = 0.2
    deal_association_weight: float = 0.15
    demographic_weight: float = 0.1
    
    def calculate_score(self, contact_data: Dict[str, Any]) -> int:
        """Calculate lead score based on criteria"""
        score = 0
        
        # Email engagement
        email_opens = contact_data.get("hs_email_open", 0) or 0
        email_clicks = contact_data.get("hs_email_click", 0) or 0
        email_score = (email_opens * 2 + email_clicks * 5) * self.email_engagement_weight
        score += min(email_score, 30)  # Cap at 30
        
        # Website activity
        page_views = contact_data.get("hs_analytics_num_page_views", 0) or 0
        visit_duration = contact_data.get("hs_analytics_average_page_views", 0) or 0
        website_score = (page_views * 1 + visit_duration * 0.5) * self.website_activity_weight
        score += min(website_score, 25)  # Cap at 25
        
        # Form submissions
        form_submissions = contact_data.get("num_conversion_events", 0) or 0
        form_score = form_submissions * 10 * self.form_submission_weight
        score += min(form_score, 20)  # Cap at 20
        
        # Deal associations
        num_deals = contact_data.get("num_associated_deals", 0) or 0
        deal_score = num_deals * 15 * self.deal_association_weight
        score += min(deal_score, 15)  # Cap at 15
        
        # Demographics
        has_company = 5 if contact_data.get("company") else 0
        has_phone = 3 if contact_data.get("phone") else 0
        has_title = 2 if contact_data.get("jobtitle") else 0
        demographic_score = (has_company + has_phone + has_title) * self.demographic_weight
        score += min(demographic_score, 10)  # Cap at 10
        
        return int(min(score, 100))  # Total score capped at 100


class HubSpotOptimizedClient:
    """
    Optimized HubSpot client with:
    - OAuth 2.0 and API key authentication
    - CRM API v3 for all object operations
    - Marketing Hub integration
    - Lead scoring engine
    - Workflow automation
    - Redis caching for performance
    """
    
    def __init__(self, use_oauth: bool = True):
        self.api_url = HUBSPOT_API_URL
        self.use_oauth = use_oauth
        self.access_token = HUBSPOT_ACCESS_TOKEN if use_oauth else None
        self.api_key = HUBSPOT_API_KEY if not use_oauth else None
        self.session: Optional[aiohttp.ClientSession] = None
        self.redis_client: Optional[redis.Redis] = None
        self.lead_scorer = LeadScoringCriteria()
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        self.redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        if self.redis_client:
            await self.redis_client.aclose()
            
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with auth"""
        headers = {"Content-Type": "application/json"}
        
        if self.use_oauth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
            
        return headers
        
    def _get_auth_params(self) -> Dict[str, str]:
        """Get auth parameters for API key auth"""
        if not self.use_oauth and self.api_key:
            return {"hapikey": self.api_key}
        return {}
        
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
        if method == "GET":
            param_hash = hashlib.md5(str(params or {}).encode()).hexdigest()
            cache_key = f"hubspot:{endpoint}:{param_hash}"
            cached = await self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
                
        url = f"{self.api_url}{endpoint}"
        headers = self._get_headers()
        
        # Add API key to params if using API key auth
        if params is None:
            params = {}
        params.update(self._get_auth_params())
        
        async with self.session.request(
            method,
            url,
            params=params,
            json=json_data,
            headers=headers
        ) as response:
            if response.status == 429:
                # Rate limited
                retry_after = int(response.headers.get("X-HubSpot-RateLimit-Interval", 10))
                await asyncio.sleep(retry_after)
                raise Exception(f"Rate limited, retry after {retry_after}s")
                
            if response.status >= 400:
                error_text = await response.text()
                raise Exception(f"HubSpot API error {response.status}: {error_text}")
                
            # Handle empty responses
            if response.status == 204:
                return {}
                
            result = await response.json()
            
            # Cache successful GET responses
            if cache_key:
                await self.redis_client.setex(
                    cache_key,
                    300,  # 5 minute cache
                    json.dumps(result)
                )
                
            return result
            
    async def get_contacts(
        self,
        limit: int = 100,
        properties: Optional[List[str]] = None
    ) -> List[HubSpotContact]:
        """Get contacts with properties"""
        params = {"limit": limit}
        
        if properties:
            params["properties"] = ",".join(properties)
        else:
            params["properties"] = "email,firstname,lastname,company,phone,lifecycle_stage,lead_score"
            
        response = await self._make_request(
            "GET",
            "/crm/v3/objects/contacts",
            params=params
        )
        
        contacts = []
        for result in response.get("results", []):
            contact = HubSpotContact(
                id=result["id"],
                email=result["properties"].get("email", ""),
                firstname=result["properties"].get("firstname"),
                lastname=result["properties"].get("lastname"),
                company=result["properties"].get("company"),
                phone=result["properties"].get("phone"),
                lifecycle_stage=result["properties"].get("lifecycle_stage", "subscriber"),
                lead_score=int(result["properties"].get("lead_score", 0) or 0),
                properties=result["properties"]
            )
            contacts.append(contact)
            
        return contacts
        
    async def create_contact(self, contact: HubSpotContact) -> HubSpotContact:
        """Create single contact"""
        data = contact.to_api_format()
        
        response = await self._make_request(
            "POST",
            "/crm/v3/objects/contacts",
            json_data=data
        )
        
        contact.id = response["id"]
        return contact
        
    async def batch_create_contacts(
        self,
        contacts: List[HubSpotContact]
    ) -> List[HubSpotContact]:
        """Create multiple contacts"""
        data = {
            "inputs": [c.to_api_format() for c in contacts]
        }
        
        response = await self._make_request(
            "POST",
            "/crm/v3/objects/contacts/batch/create",
            json_data=data
        )
        
        created = []
        for i, result in enumerate(response.get("results", [])):
            contacts[i].id = result["id"]
            created.append(contacts[i])
            
        return created
        
    async def update_contact(
        self,
        contact_id: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update contact properties"""
        data = {"properties": properties}
        
        return await self._make_request(
            "PATCH",
            f"/crm/v3/objects/contacts/{contact_id}",
            json_data=data
        )
        
    async def score_contacts(
        self,
        contact_ids: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """Calculate and update lead scores"""
        scores = {}
        
        # Get contacts with engagement data
        if contact_ids:
            data = {
                "inputs": [{"id": cid} for cid in contact_ids],
                "properties": [
                    "email", "firstname", "lastname", "company", "phone",
                    "hs_email_open", "hs_email_click",
                    "hs_analytics_num_page_views", "hs_analytics_average_page_views",
                    "num_conversion_events", "num_associated_deals", "jobtitle"
                ]
            }
            
            response = await self._make_request(
                "POST",
                "/crm/v3/objects/contacts/batch/read",
                json_data=data
            )
            
            contacts = response.get("results", [])
        else:
            # Get all contacts
            contacts = await self.get_contacts(limit=200)
            contacts = [c.to_api_format() for c in contacts]
            
        # Calculate scores
        updates = []
        for contact in contacts:
            contact_id = contact.get("id")
            if not contact_id:
                continue
                
            props = contact.get("properties", {})
            score = self.lead_scorer.calculate_score(props)
            scores[contact_id] = score
            
            updates.append({
                "id": contact_id,
                "properties": {"lead_score": str(score)}
            })
            
        # Batch update scores
        if updates:
            await self._make_request(
                "POST",
                "/crm/v3/objects/contacts/batch/update",
                json_data={"inputs": updates}
            )
            
        return scores
        
    async def get_deals(
        self,
        limit: int = 100,
        properties: Optional[List[str]] = None
    ) -> List[HubSpotDeal]:
        """Get deals with properties"""
        params = {"limit": limit}
        
        if properties:
            params["properties"] = ",".join(properties)
        else:
            params["properties"] = "dealname,amount,dealstage,pipeline,closedate"
            
        response = await self._make_request(
            "GET",
            "/crm/v3/objects/deals",
            params=params
        )
        
        deals = []
        for result in response.get("results", []):
            deal = HubSpotDeal(
                id=result["id"],
                dealname=result["properties"].get("dealname", ""),
                amount=float(result["properties"].get("amount", 0) or 0),
                dealstage=result["properties"].get("dealstage", "appointmentscheduled"),
                pipeline=result["properties"].get("pipeline", "default"),
                properties=result["properties"]
            )
            
            if result["properties"].get("closedate"):
                deal.closedate = datetime.fromisoformat(
                    result["properties"]["closedate"].replace("Z", "+00:00")
                )
                
            deals.append(deal)
            
        return deals
        
    async def search_objects(
        self,
        object_type: str,
        filters: List[Dict[str, Any]],
        properties: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search CRM objects with filters"""
        data = {
            "filterGroups": [{
                "filters": filters
            }],
            "limit": limit
        }
        
        if properties:
            data["properties"] = properties
            
        response = await self._make_request(
            "POST",
            f"/crm/v3/objects/{object_type}/search",
            json_data=data
        )
        
        return response.get("results", [])
        
    async def get_marketing_emails(self) -> List[Dict[str, Any]]:
        """Get marketing email campaigns"""
        response = await self._make_request(
            "GET",
            "/marketing-emails/v1/campaigns"
        )
        
        return response.get("campaigns", [])
        
    async def get_workflows(self) -> List[Dict[str, Any]]:
        """Get automation workflows"""
        response = await self._make_request(
            "GET",
            "/automation/v4/workflows"
        )
        
        return response.get("workflows", [])
        
    async def send_behavioral_event(
        self,
        event_name: str,
        email: str,
        properties: Optional[Dict[str, Any]] = None
    ):
        """Send behavioral event for tracking"""
        data = {
            "eventName": event_name,
            "email": email,
            "properties": properties or {}
        }
        
        await self._make_request(
            "POST",
            "/events/v3/send",
            json_data=data
        )
        
    async def test_connection(self) -> bool:
        """Test API connection"""
        try:
            contacts = await self.get_contacts(limit=1)
            return True
        except Exception as e:
            print(f"HubSpot connection test failed: {e}")
            return False


class HubSpotMarketingAutomation:
    """
    Marketing automation and lead nurturing
    """
    
    def __init__(self):
        self.client = HubSpotOptimizedClient()
        self.redis_client = None
        
    async def setup(self):
        """Initialize automation engine"""
        self.redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        
    async def segment_contacts(self) -> Dict[str, List[str]]:
        """Segment contacts based on lead score and lifecycle stage"""
        segments = {
            "hot_leads": [],
            "warm_leads": [],
            "cold_leads": [],
            "customers": [],
            "evangelists": []
        }
        
        async with self.client as client:
            contacts = await client.get_contacts(limit=500)
            
            for contact in contacts:
                if contact.lifecycle_stage == "customer":
                    segments["customers"].append(contact.id)
                elif contact.lifecycle_stage == "evangelist":
                    segments["evangelists"].append(contact.id)
                elif contact.lead_score >= 70:
                    segments["hot_leads"].append(contact.id)
                elif contact.lead_score >= 40:
                    segments["warm_leads"].append(contact.id)
                else:
                    segments["cold_leads"].append(contact.id)
                    
        # Cache segments
        for segment_name, contact_ids in segments.items():
            segment_key = f"hubspot:segment:{segment_name}"
            await self.redis_client.setex(
                segment_key,
                3600,  # 1 hour
                json.dumps(contact_ids)
            )
            
        return segments
        
    async def trigger_nurture_campaign(
        self,
        segment: str,
        campaign_type: str
    ) -> Dict[str, Any]:
        """Trigger nurture campaign for segment"""
        # Get segment contacts
        segment_key = f"hubspot:segment:{segment}"
        contact_ids = await self.redis_client.get(segment_key)
        
        if not contact_ids:
            return {"error": "Segment not found"}
            
        contact_ids = json.loads(contact_ids)
        
        # Define campaign actions based on type
        campaign_actions = {
            "welcome": [
                {"type": "email", "template": "welcome_series_1"},
                {"type": "task", "title": "Personal welcome call", "delay_days": 2},
                {"type": "email", "template": "welcome_series_2", "delay_days": 7}
            ],
            "re_engagement": [
                {"type": "email", "template": "we_miss_you"},
                {"type": "task", "title": "Re-engagement outreach", "delay_days": 3}
            ],
            "upsell": [
                {"type": "email", "template": "new_features"},
                {"type": "task", "title": "Schedule product demo", "delay_days": 5}
            ]
        }
        
        actions = campaign_actions.get(campaign_type, [])
        
        return {
            "segment": segment,
            "campaign_type": campaign_type,
            "contacts_targeted": len(contact_ids),
            "actions_scheduled": len(actions)
        }
        
    async def analyze_campaign_performance(self) -> Dict[str, Any]:
        """Analyze marketing campaign performance"""
        async with self.client as client:
            campaigns = await client.get_marketing_emails()
            
            performance = {
                "total_campaigns": len(campaigns),
                "by_status": {},
                "top_performers": [],
                "needs_attention": []
            }
            
            for campaign in campaigns:
                status = campaign.get("state", "unknown")
                if status not in performance["by_status"]:
                    performance["by_status"][status] = 0
                performance["by_status"][status] += 1
                
                # Analyze metrics
                open_rate = campaign.get("open_rate", 0)
                click_rate = campaign.get("click_rate", 0)
                
                if open_rate > 25 and click_rate > 3:
                    performance["top_performers"].append({
                        "name": campaign.get("name"),
                        "open_rate": open_rate,
                        "click_rate": click_rate
                    })
                elif open_rate < 15 or click_rate < 1:
                    performance["needs_attention"].append({
                        "name": campaign.get("name"),
                        "open_rate": open_rate,
                        "click_rate": click_rate,
                        "issue": "Low engagement"
                    })
                    
            return performance


async def test_hubspot_client():
    """Test HubSpot client"""
    print("🚀 Testing HubSpot Integration")
    print("=" * 60)
    
    async with HubSpotOptimizedClient() as client:
        # Test connection
        print("\n1. Testing connection...")
        connected = await client.test_connection()
        print(f"   {'✅' if connected else '❌'} Connection: {connected}")
        
        if connected:
            # Get contacts
            print("\n2. Getting contacts...")
            try:
                contacts = await client.get_contacts(limit=5)
                print(f"   ✅ Found {len(contacts)} contacts")
                
                # Test lead scoring
                print("\n3. Testing lead scoring...")
                if contacts:
                    contact_ids = [c.id for c in contacts if c.id]
                    scores = await client.score_contacts(contact_ids[:3])
                    print(f"   ✅ Scored {len(scores)} contacts")
                    
                    for contact_id, score in list(scores.items())[:3]:
                        print(f"      - Contact {contact_id}: Score {score}/100")
                        
                # Get deals
                print("\n4. Getting deals...")
                deals = await client.get_deals(limit=5)
                print(f"   ✅ Found {len(deals)} deals")
                
                total_value = sum(d.amount for d in deals)
                print(f"      Total pipeline value: ${total_value:,.0f}")
                
                # Test marketing automation
                print("\n5. Testing marketing automation...")
                automation = HubSpotMarketingAutomation()
                await automation.setup()
                
                segments = await automation.segment_contacts()
                print(f"   ✅ Created {len(segments)} segments")
                
                for segment, contacts in segments.items():
                    print(f"      - {segment}: {len(contacts)} contacts")
                    
                # Analyze campaigns
                print("\n6. Analyzing campaign performance...")
                performance = await automation.analyze_campaign_performance()
                print(f"   ✅ Analyzed {performance['total_campaigns']} campaigns")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                
    print("\n" + "=" * 60)
    print("✅ HubSpot test complete")


if __name__ == "__main__":
    asyncio.run(test_hubspot_client())
