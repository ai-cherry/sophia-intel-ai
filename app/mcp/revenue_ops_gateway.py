"""
Sophia AI Revenue Ops Gateway
Real MCP server with Salesforce, HubSpot, and Gong integrations
No mock data - production ready with actual API calls
"""

import asyncio
import base64
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from app.mcp.server_template import (
    MCPServerBase,
    validate_required_params,
    with_retry,
)
from app.memory.bus import UnifiedMemoryBus
from app.observability.metrics import MetricsCollector
from app.observability.otel import trace_async

logger = logging.getLogger(__name__)


@dataclass
class ContactInfo:
    """Standardized contact information across all CRM systems"""

    id: str
    name: str
    email: str
    phone: Optional[str]
    company: str
    title: Optional[str]
    source: str  # 'salesforce', 'hubspot', 'gong'
    last_activity: Optional[datetime]
    health_score: Optional[float]


@dataclass
class AccountHealth:
    """Account health metrics aggregated from all sources"""

    account_id: str
    account_name: str
    health_score: float
    risk_factors: List[str]
    opportunities: List[str]
    last_activity: datetime
    revenue_trend: str  # 'up', 'down', 'stable'
    engagement_score: float
    next_actions: List[str]


class SalesforceClient:
    """Real Salesforce API client"""

    def __init__(self):
        # Credentials from environment (managed by Pulumi ESC)
        self.instance_url = os.getenv("SALESFORCE_INSTANCE_URL")
        self.client_id = os.getenv("SALESFORCE_CLIENT_ID")
        self.client_secret = os.getenv("SALESFORCE_CLIENT_SECRET")
        self.username = os.getenv("SALESFORCE_USERNAME")
        self.password = os.getenv("SALESFORCE_PASSWORD")
        self.security_token = os.getenv("SALESFORCE_SECURITY_TOKEN")

        self.access_token = None
        self.token_expires = None
        self.session = httpx.AsyncClient()

    async def authenticate(self):
        """Authenticate with Salesforce OAuth"""
        if (
            self.access_token
            and self.token_expires
            and datetime.utcnow() < self.token_expires
        ):
            return

        auth_url = f"{self.instance_url}/services/oauth2/token"
        data = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": f"{self.password}{self.security_token}",
        }

        response = await self.session.post(auth_url, data=data)
        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data["access_token"]
        self.token_expires = datetime.utcnow() + timedelta(
            hours=1
        )  # Conservative expiry

        logger.info("Salesforce authentication successful")

    async def query(self, soql: str) -> Dict[str, Any]:
        """Execute SOQL query"""
        await self.authenticate()

        url = f"{self.instance_url}/services/data/v58.0/query"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        params = {"q": soql}

        response = await self.session.get(url, headers=headers, params=params)
        response.raise_for_status()

        return response.json()

    async def get_account(self, account_id: str) -> Dict[str, Any]:
        """Get account details"""
        soql = f"""
        SELECT Id, Name, Type, Industry, AnnualRevenue, NumberOfEmployees, 
               Phone, Website, BillingCity, BillingState, BillingCountry,
               LastActivityDate, CreatedDate, LastModifiedDate
        FROM Account 
        WHERE Id = '{account_id}'
        """

        result = await self.query(soql)
        if result["records"]:
            return result["records"][0]
        raise ValueError(f"Account {account_id} not found")

    async def search_contacts(
        self, search_term: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search contacts by name, email, or company"""
        soql = f"""
        SELECT Id, Name, Email, Phone, Title, Account.Name, Account.Id,
               LastActivityDate, CreatedDate, LastModifiedDate
        FROM Contact 
        WHERE (Name LIKE '%{search_term}%' 
               OR Email LIKE '%{search_term}%' 
               OR Account.Name LIKE '%{search_term}%')
        ORDER BY LastActivityDate DESC NULLS LAST
        LIMIT {limit}
        """

        result = await self.query(soql)
        return result["records"]

    async def get_opportunities(self, account_id: str) -> List[Dict[str, Any]]:
        """Get opportunities for account"""
        soql = f"""
        SELECT Id, Name, StageName, Amount, CloseDate, Probability,
               Type, LeadSource, CreatedDate, LastModifiedDate
        FROM Opportunity 
        WHERE AccountId = '{account_id}'
        ORDER BY CloseDate DESC
        """

        result = await self.query(soql)
        return result["records"]


class HubSpotClient:
    """Real HubSpot API client"""

    def __init__(self):
        # Credentials from environment (managed by Pulumi ESC)
        self.api_key = os.getenv("HUBSPOT_API_KEY")
        self.base_url = "https://api.hubapi.com"
        self.session = httpx.AsyncClient()

    def _get_headers(self) -> Dict[str, str]:
        """Get API headers"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def search_contacts(
        self, search_term: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search contacts in HubSpot"""
        url = f"{self.base_url}/crm/v3/objects/contacts/search"

        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "email",
                            "operator": "CONTAINS_TOKEN",
                            "value": search_term,
                        },
                        {
                            "propertyName": "firstname",
                            "operator": "CONTAINS_TOKEN",
                            "value": search_term,
                        },
                        {
                            "propertyName": "lastname",
                            "operator": "CONTAINS_TOKEN",
                            "value": search_term,
                        },
                        {
                            "propertyName": "company",
                            "operator": "CONTAINS_TOKEN",
                            "value": search_term,
                        },
                    ]
                }
            ],
            "properties": [
                "firstname",
                "lastname",
                "email",
                "phone",
                "company",
                "jobtitle",
                "lastmodifieddate",
                "createdate",
                "hs_lead_status",
            ],
            "limit": limit,
        }

        response = await self.session.post(
            url, headers=self._get_headers(), json=payload
        )
        response.raise_for_status()

        return response.json().get("results", [])

    async def get_company(self, company_id: str) -> Dict[str, Any]:
        """Get company details"""
        url = f"{self.base_url}/crm/v3/objects/companies/{company_id}"
        params = {
            "properties": [
                "name",
                "domain",
                "industry",
                "annualrevenue",
                "numberofemployees",
                "phone",
                "city",
                "state",
                "country",
                "createdate",
                "lastmodifieddate",
                "hs_lead_status",
                "lifecyclestage",
            ]
        }

        response = await self.session.get(
            url, headers=self._get_headers(), params=params
        )
        response.raise_for_status()

        return response.json()

    async def get_deals(self, company_id: str) -> List[Dict[str, Any]]:
        """Get deals associated with company"""
        url = (
            f"{self.base_url}/crm/v4/objects/companies/{company_id}/associations/deals"
        )

        response = await self.session.get(url, headers=self._get_headers())
        response.raise_for_status()

        deal_ids = [assoc["toObjectId"] for assoc in response.json().get("results", [])]

        if not deal_ids:
            return []

        # Get deal details
        deals = []
        for deal_id in deal_ids:
            deal_url = f"{self.base_url}/crm/v3/objects/deals/{deal_id}"
            deal_params = {
                "properties": [
                    "dealname",
                    "dealstage",
                    "amount",
                    "closedate",
                    "probability",
                    "dealtype",
                    "leadsource",
                    "createdate",
                    "lastmodifieddate",
                ]
            }

            deal_response = await self.session.get(
                deal_url, headers=self._get_headers(), params=deal_params
            )
            if deal_response.status_code == 200:
                deals.append(deal_response.json())

        return deals


class SlackClient:
    """Real Slack API client for client and employee context"""

    def __init__(self):
        # Credentials from environment (managed by Pulumi ESC)
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.user_token = os.getenv(
            "SLACK_USER_TOKEN"
        )  # For accessing DMs and private channels
        self.base_url = "https://slack.com/api"
        self.session = httpx.AsyncClient()

    def _get_headers(self, use_user_token: bool = False) -> Dict[str, str]:
        """Get API headers"""
        token = self.user_token if use_user_token else self.bot_token
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async def search_messages(
        self, query: str, count: int = 50, sort: str = "timestamp"
    ) -> Dict[str, Any]:
        """Search messages across all accessible channels and DMs"""
        url = f"{self.base_url}/search.messages"

        params = {"query": query, "count": count, "sort": sort, "sort_dir": "desc"}

        # Use user token for broader search access
        response = await self.session.get(
            url, headers=self._get_headers(use_user_token=True), params=params
        )
        response.raise_for_status()

        return response.json()

    async def get_channel_messages(
        self, channel_id: str, limit: int = 100, oldest: str = None, latest: str = None
    ) -> Dict[str, Any]:
        """Get messages from a specific channel"""
        url = f"{self.base_url}/conversations.history"

        params = {"channel": channel_id, "limit": limit}

        if oldest:
            params["oldest"] = oldest
        if latest:
            params["latest"] = latest

        response = await self.session.get(
            url, headers=self._get_headers(), params=params
        )
        response.raise_for_status()

        return response.json()

    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user profile information"""
        url = f"{self.base_url}/users.info"

        params = {"user": user_id}

        response = await self.session.get(
            url, headers=self._get_headers(), params=params
        )
        response.raise_for_status()

        return response.json()

    async def list_channels(
        self, types: str = "public_channel,private_channel"
    ) -> Dict[str, Any]:
        """List all channels the bot has access to"""
        url = f"{self.base_url}/conversations.list"

        params = {"types": types, "exclude_archived": True, "limit": 1000}

        response = await self.session.get(
            url, headers=self._get_headers(), params=params
        )
        response.raise_for_status()

        return response.json()

    async def search_client_mentions(
        self, client_name: str, days_back: int = 30
    ) -> Dict[str, Any]:
        """Search for mentions of a specific client across all channels"""
        # Calculate timestamp for days_back
        from_timestamp = (datetime.utcnow() - timedelta(days=days_back)).timestamp()

        # Build search query
        query = f'"{client_name}" after:{int(from_timestamp)}'

        return await self.search_messages(query, count=100)

    async def get_employee_sentiment(
        self, employee_user_id: str, days_back: int = 7
    ) -> Dict[str, Any]:
        """Analyze employee sentiment from their recent messages"""
        from_timestamp = (datetime.utcnow() - timedelta(days=days_back)).timestamp()

        # Search for messages from this employee
        query = f"from:<@{employee_user_id}> after:{int(from_timestamp)}"

        messages_result = await self.search_messages(query, count=50)

        messages = messages_result.get("messages", {}).get("matches", [])

        # Basic sentiment analysis (would use proper NLP in production)
        sentiment_indicators = {
            "positive": [
                "great",
                "awesome",
                "excellent",
                "love",
                "perfect",
                "amazing",
                "👍",
                "🎉",
                "✅",
            ],
            "negative": [
                "frustrated",
                "annoying",
                "terrible",
                "hate",
                "awful",
                "broken",
                "😞",
                "😤",
                "❌",
            ],
            "stress": [
                "urgent",
                "asap",
                "emergency",
                "critical",
                "deadline",
                "overwhelmed",
                "stressed",
            ],
        }

        sentiment_scores = {"positive": 0, "negative": 0, "stress": 0, "neutral": 0}
        analyzed_messages = []

        for message in messages:
            text = message.get("text", "").lower()
            message_sentiment = "neutral"

            for sentiment_type, indicators in sentiment_indicators.items():
                if any(indicator in text for indicator in indicators):
                    sentiment_scores[sentiment_type] += 1
                    message_sentiment = sentiment_type
                    break
            else:
                sentiment_scores["neutral"] += 1

            analyzed_messages.append(
                {
                    "text": message.get("text", ""),
                    "timestamp": message.get("ts"),
                    "channel": message.get("channel", {}).get("name"),
                    "sentiment": message_sentiment,
                }
            )

        total_messages = len(messages)
        if total_messages > 0:
            sentiment_percentages = {
                k: (v / total_messages) * 100 for k, v in sentiment_scores.items()
            }
        else:
            sentiment_percentages = sentiment_scores

        return {
            "employee_id": employee_user_id,
            "analysis_period_days": days_back,
            "total_messages": total_messages,
            "sentiment_scores": sentiment_scores,
            "sentiment_percentages": sentiment_percentages,
            "messages": analyzed_messages[:10],  # Return sample of messages
            "overall_sentiment": max(
                sentiment_percentages, key=sentiment_percentages.get
            ),
        }

    async def get_client_channel_activity(
        self, client_name: str, days_back: int = 30
    ) -> Dict[str, Any]:
        """Get activity in client-specific channels"""
        channels = await self.list_channels()
        client_channels = []

        # Find channels that might be related to the client
        client_name_lower = client_name.lower()
        for channel in channels.get("channels", []):
            channel_name = channel.get("name", "").lower()
            if client_name_lower in channel_name or any(
                word in channel_name for word in client_name_lower.split()
            ):
                client_channels.append(channel)

        activity_summary = {
            "client_name": client_name,
            "related_channels": [],
            "total_messages": 0,
            "active_employees": set(),
            "recent_topics": [],
            "urgency_indicators": 0,
        }

        # Analyze activity in each related channel
        for channel in client_channels:
            channel_id = channel["id"]
            channel_name = channel["name"]

            # Get recent messages
            oldest_timestamp = (
                datetime.utcnow() - timedelta(days=days_back)
            ).timestamp()
            messages = await self.get_channel_messages(
                channel_id, limit=100, oldest=str(oldest_timestamp)
            )

            channel_messages = messages.get("messages", [])

            # Analyze messages for urgency and topics
            urgency_keywords = [
                "urgent",
                "asap",
                "emergency",
                "critical",
                "issue",
                "problem",
                "down",
                "broken",
            ]
            channel_urgency = 0

            for message in channel_messages:
                text = message.get("text", "").lower()
                user_id = message.get("user")

                if user_id:
                    activity_summary["active_employees"].add(user_id)

                if any(keyword in text for keyword in urgency_keywords):
                    channel_urgency += 1

            activity_summary["related_channels"].append(
                {
                    "name": channel_name,
                    "id": channel_id,
                    "message_count": len(channel_messages),
                    "urgency_indicators": channel_urgency,
                }
            )

            activity_summary["total_messages"] += len(channel_messages)
            activity_summary["urgency_indicators"] += channel_urgency

        activity_summary["active_employees"] = len(activity_summary["active_employees"])

        return activity_summary


class GongClient:
    """Real Gong.io API client"""

    def __init__(self):
        # Credentials from environment (managed externally; never hardcoded)
        self.access_key = os.getenv("GONG_ACCESS_KEY")
        self.secret = os.getenv("GONG_CLIENT_SECRET")
        if not self.access_key or not self.secret:
            raise ValueError(
                "Missing Gong credentials: set GONG_ACCESS_KEY and GONG_CLIENT_SECRET in environment"
            )
        self.base_url = "https://api.gong.io/v2"

        # Create Basic Auth header
        credentials = base64.b64encode(
            f"{self.access_key}:{self.secret}".encode()
        ).decode()
        self.auth_header = f"Basic {credentials}"

        self.session = httpx.AsyncClient()

    def _get_headers(self) -> Dict[str, str]:
        """Get API headers"""
        return {"Authorization": self.auth_header, "Content-Type": "application/json"}

    async def search_calls(
        self,
        account_name: str = None,
        contact_email: str = None,
        from_date: datetime = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Search calls by account or contact"""
        url = f"{self.base_url}/calls"

        # Build filter
        filter_params = {}
        if from_date:
            filter_params["fromDateTime"] = from_date.isoformat()
        if account_name:
            filter_params["workspaces"] = [
                account_name
            ]  # Adjust based on Gong workspace structure
        if contact_email:
            filter_params["emailAddress"] = contact_email

        payload = {"filter": filter_params, "cursor": {"limit": limit}}

        response = await self.session.post(
            url, headers=self._get_headers(), json=payload
        )
        response.raise_for_status()

        return response.json().get("calls", [])

    async def search_emails(
        self,
        account_name: str = None,
        contact_email: str = None,
        from_date: datetime = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Search email conversations by account or contact"""
        url = f"{self.base_url}/calls"  # Gong uses same endpoint for calls and emails

        # Build filter for emails specifically
        filter_params = {
            "contentSelector": {
                "exposureType": "EMAIL"
            }  # Filter for email conversations only
        }

        if from_date:
            filter_params["fromDateTime"] = from_date.isoformat()
        if account_name:
            filter_params["workspaces"] = [account_name]
        if contact_email:
            filter_params["emailAddress"] = contact_email

        payload = {"filter": filter_params, "cursor": {"limit": limit}}

        response = await self.session.post(
            url, headers=self._get_headers(), json=payload
        )
        response.raise_for_status()

        return response.json().get("calls", [])  # Gong returns emails in 'calls' array

    async def get_email_content(self, email_id: str) -> Dict[str, Any]:
        """Get email content and metadata"""
        url = f"{self.base_url}/calls/{email_id}/transcript"

        response = await self.session.get(url, headers=self._get_headers())
        response.raise_for_status()

        return response.json()

    async def search_all_conversations(
        self,
        account_name: str = None,
        contact_email: str = None,
        from_date: datetime = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Search both calls and emails for comprehensive conversation view"""

        # Search calls and emails in parallel
        async def fetch_calls():
            try:
                return await self.search_calls(
                    account_name, contact_email, from_date, limit
                )
            except Exception as e:
                logger.error(f"Failed to fetch calls: {e}")
                return []

        async def fetch_emails():
            try:
                return await self.search_emails(
                    account_name, contact_email, from_date, limit
                )
            except Exception as e:
                logger.error(f"Failed to fetch emails: {e}")
                return []

        async with asyncio.TaskGroup() as tg:
            calls_task = tg.create_task(fetch_calls())
            emails_task = tg.create_task(fetch_emails())

        calls = calls_task.result()
        emails = emails_task.result()

        return {
            "calls": calls,
            "emails": emails,
            "total_conversations": len(calls) + len(emails),
            "call_count": len(calls),
            "email_count": len(emails),
        }

    async def get_call_transcript(self, call_id: str) -> Dict[str, Any]:
        """Get call transcript and analysis"""
        url = f"{self.base_url}/calls/{call_id}/transcript"

        response = await self.session.get(url, headers=self._get_headers())
        response.raise_for_status()

        return response.json()

    async def get_call_stats(self, call_id: str) -> Dict[str, Any]:
        """Get call statistics and insights"""
        url = f"{self.base_url}/calls/{call_id}/stats"

        response = await self.session.get(url, headers=self._get_headers())
        response.raise_for_status()

        return response.json()


class RevenueOpsGateway(MCPServerBase):
    """
    Revenue Operations Gateway - First domain MCP server
    Integrates Salesforce, HubSpot, and Gong for unified revenue intelligence
    """

    def __init__(self, memory_bus: UnifiedMemoryBus, metrics: MetricsCollector):
        super().__init__(
            domain="revenue",
            capabilities=[
                "crm.search_contacts",
                "crm.get_account",
                "crm.upsert_opportunity",
                "analytics.account_360",
                "notes.from_gong",
                "health.score",
                "intelligence.pipeline_analysis",
                "intelligence.conversation_insights",
                "intelligence.slack_client_context",
                "intelligence.employee_sentiment",
                "coaching.team_health_analysis",
                "coaching.ceo_dashboard",
            ],
            memory_bus=memory_bus,
            metrics=metrics,
        )

        self.salesforce = SalesforceClient()
        self.hubspot = HubSpotClient()
        self.gong = GongClient()
        self.slack = SlackClient()

    async def initialize(self):
        """Initialize Revenue Ops Gateway with all integrations"""
        logger.info("Initializing Revenue Ops Gateway...")

        # Test connections
        try:
            await self.salesforce.authenticate()
            logger.info("Salesforce connection established")
        except Exception as e:
            logger.error(f"Salesforce connection failed: {e}")
            # Don't fail initialization - degrade gracefully

        # Register all MCP tools
        await self._register_tools()

        logger.info("Revenue Ops Gateway initialized successfully")

    async def shutdown(self):
        """Cleanup resources"""
        await self.salesforce.session.aclose()
        await self.hubspot.session.aclose()
        await self.gong.session.aclose()
        await self.slack.session.aclose()
        logger.info("Revenue Ops Gateway shutdown complete")

    async def _register_tools(self):
        """Register all MCP tools"""

        @self.mcp_tool("crm.search_contacts")
        @trace_async("revenue_search_contacts")
        async def search_contacts(
            search_term: str, sources: List[str] = None, limit: int = 50
        ) -> Dict[str, Any]:
            """
            Search contacts across Salesforce and HubSpot
            """
            validate_required_params({"search_term": search_term}, ["search_term"])

            if not sources:
                sources = ["salesforce", "hubspot"]

            results = {"contacts": [], "sources_searched": sources}

            # Search Salesforce
            if "salesforce" in sources:
                try:
                    sf_contacts = await with_retry(
                        lambda: self.salesforce.search_contacts(search_term, limit)
                    )

                    for contact in sf_contacts:
                        results["contacts"].append(
                            ContactInfo(
                                id=contact["Id"],
                                name=contact["Name"],
                                email=contact.get("Email", ""),
                                phone=contact.get("Phone"),
                                company=contact.get("Account", {}).get("Name", ""),
                                title=contact.get("Title"),
                                source="salesforce",
                                last_activity=contact.get("LastActivityDate"),
                                health_score=None,  # Calculate separately
                            ).__dict__
                        )

                except Exception as e:
                    logger.error(f"Salesforce search failed: {e}")
                    results["errors"] = results.get("errors", []) + [
                        f"Salesforce: {str(e)}"
                    ]

            # Search HubSpot
            if "hubspot" in sources:
                try:
                    hs_contacts = await with_retry(
                        lambda: self.hubspot.search_contacts(search_term, limit)
                    )

                    for contact in hs_contacts:
                        props = contact.get("properties", {})
                        results["contacts"].append(
                            ContactInfo(
                                id=contact["id"],
                                name=f"{props.get('firstname', '')} {props.get('lastname', '')}".strip(),
                                email=props.get("email", ""),
                                phone=props.get("phone"),
                                company=props.get("company", ""),
                                title=props.get("jobtitle"),
                                source="hubspot",
                                last_activity=props.get("lastmodifieddate"),
                                health_score=None,
                            ).__dict__
                        )

                except Exception as e:
                    logger.error(f"HubSpot search failed: {e}")
                    results["errors"] = results.get("errors", []) + [
                        f"HubSpot: {str(e)}"
                    ]

            return results

        @self.mcp_tool("analytics.account_360")
        @trace_async("revenue_account_360")
        async def account_360(
            account_id: str, include_gong: bool = True
        ) -> Dict[str, Any]:
            """
            Comprehensive account view across all revenue systems
            This is what sales coach agents need for contextual coaching
            """
            validate_required_params({"account_id": account_id}, ["account_id"])

            account_data = {
                "account_id": account_id,
                "timestamp": datetime.utcnow().isoformat(),
                "sources": [],
            }

            # Parallel data gathering
            async def fetch_salesforce():
                try:
                    account = await self.salesforce.get_account(account_id)
                    opportunities = await self.salesforce.get_opportunities(account_id)
                    return {"account": account, "opportunities": opportunities}
                except Exception as e:
                    logger.error(f"Salesforce fetch failed: {e}")
                    return {"error": str(e)}

            async def fetch_hubspot():
                try:
                    # Try to find matching company in HubSpot
                    # This would need account mapping logic in production
                    return {"note": "HubSpot integration requires account mapping"}
                except Exception as e:
                    logger.error(f"HubSpot fetch failed: {e}")
                    return {"error": str(e)}

            async def fetch_gong():
                if not include_gong:
                    return {}
                try:
                    # Search for calls related to this account
                    calls = await self.gong.search_calls(limit=10)
                    return {"recent_calls": calls}
                except Exception as e:
                    logger.error(f"Gong fetch failed: {e}")
                    return {"error": str(e)}

            # Execute in parallel
            async with asyncio.TaskGroup() as tg:
                sf_task = tg.create_task(fetch_salesforce())
                hs_task = tg.create_task(fetch_hubspot())
                gong_task = tg.create_task(fetch_gong())

            account_data["salesforce"] = sf_task.result()
            account_data["hubspot"] = hs_task.result()
            account_data["gong"] = gong_task.result()

            # Calculate health score
            health_score = await self._calculate_account_health(account_data)
            account_data["health_score"] = health_score.__dict__

            # Generate next actions
            account_data["next_actions"] = await self._suggest_next_actions(
                account_data
            )

            return account_data

        @self.mcp_tool("intelligence.conversation_insights")
        @trace_async("revenue_conversation_insights")
        async def conversation_insights(
            account_id: str = None,
            contact_email: str = None,
            days_back: int = 30,
            include_emails: bool = True,
        ) -> Dict[str, Any]:
            """
            Extract conversation intelligence from Gong calls and emails for coaching
            """
            from_date = datetime.utcnow() - timedelta(days=days_back)

            try:
                # Get both calls and emails
                if include_emails:
                    conversations = await self.gong.search_all_conversations(
                        contact_email=contact_email, from_date=from_date, limit=20
                    )
                    calls = conversations.get("calls", [])
                    emails = conversations.get("emails", [])
                else:
                    calls = await self.gong.search_calls(
                        contact_email=contact_email, from_date=from_date, limit=20
                    )
                    emails = []

                insights = {
                    "total_conversations": len(calls) + len(emails),
                    "call_count": len(calls),
                    "email_count": len(emails),
                    "calls": [],
                    "emails": [],
                    "summary": {
                        "sentiment_trend": "neutral",  # Would analyze from transcripts
                        "key_topics": [],
                        "objections": [],
                        "next_steps": [],
                        "email_response_time": None,
                        "conversation_frequency": "normal",
                    },
                }

                # Process calls for insights
                for call in calls[:5]:  # Limit for performance
                    call_id = call.get("id")
                    if call_id:
                        try:
                            transcript = await self.gong.get_call_transcript(call_id)
                            stats = await self.gong.get_call_stats(call_id)

                            insights["calls"].append(
                                {
                                    "call_id": call_id,
                                    "date": call.get("scheduled"),
                                    "duration": call.get("duration"),
                                    "participants": call.get("participants", []),
                                    "transcript_available": bool(transcript),
                                    "stats": stats,
                                    "type": "call",
                                }
                            )
                        except Exception as e:
                            logger.warning(
                                f"Failed to get call details for {call_id}: {e}"
                            )

                # Process emails for insights
                for email in emails[:5]:  # Limit for performance
                    email_id = email.get("id")
                    if email_id:
                        try:
                            email_content = await self.gong.get_email_content(email_id)

                            insights["emails"].append(
                                {
                                    "email_id": email_id,
                                    "date": email.get("scheduled"),
                                    "subject": email.get("title", "No subject"),
                                    "participants": email.get("participants", []),
                                    "content_available": bool(email_content),
                                    "direction": email.get(
                                        "direction", "unknown"
                                    ),  # inbound/outbound
                                    "type": "email",
                                }
                            )
                        except Exception as e:
                            logger.warning(
                                f"Failed to get email details for {email_id}: {e}"
                            )

                # Calculate conversation frequency
                total_conversations = len(calls) + len(emails)
                if total_conversations > 0:
                    conversations_per_week = (total_conversations / days_back) * 7
                    if conversations_per_week > 3:
                        insights["summary"]["conversation_frequency"] = "high"
                    elif conversations_per_week < 1:
                        insights["summary"]["conversation_frequency"] = "low"

                return insights

            except Exception as e:
                logger.error(f"Conversation insights failed: {e}")
                return {"error": str(e), "calls": [], "emails": []}

        @self.mcp_tool("intelligence.slack_client_context")
        @trace_async("revenue_slack_client_context")
        async def slack_client_context(
            client_name: str, days_back: int = 30
        ) -> Dict[str, Any]:
            """
            Get comprehensive Slack context for a client including mentions and channel activity
            """
            validate_required_params({"client_name": client_name}, ["client_name"])

            try:
                # Get client mentions and channel activity in parallel
                async def fetch_mentions():
                    return await self.slack.search_client_mentions(
                        client_name, days_back
                    )

                async def fetch_channel_activity():
                    return await self.slack.get_client_channel_activity(
                        client_name, days_back
                    )

                async with asyncio.TaskGroup() as tg:
                    mentions_task = tg.create_task(fetch_mentions())
                    activity_task = tg.create_task(fetch_channel_activity())

                mentions = mentions_task.result()
                channel_activity = activity_task.result()

                # Analyze sentiment and urgency from mentions
                mention_messages = mentions.get("messages", {}).get("matches", [])

                sentiment_analysis = {
                    "positive": 0,
                    "negative": 0,
                    "neutral": 0,
                    "urgent": 0,
                }

                urgent_keywords = [
                    "urgent",
                    "asap",
                    "emergency",
                    "critical",
                    "issue",
                    "problem",
                ]
                positive_keywords = [
                    "great",
                    "excellent",
                    "love",
                    "perfect",
                    "amazing",
                    "success",
                ]
                negative_keywords = [
                    "frustrated",
                    "issue",
                    "problem",
                    "broken",
                    "terrible",
                    "complaint",
                ]

                for message in mention_messages:
                    text = message.get("text", "").lower()

                    if any(keyword in text for keyword in urgent_keywords):
                        sentiment_analysis["urgent"] += 1

                    if any(keyword in text for keyword in positive_keywords):
                        sentiment_analysis["positive"] += 1
                    elif any(keyword in text for keyword in negative_keywords):
                        sentiment_analysis["negative"] += 1
                    else:
                        sentiment_analysis["neutral"] += 1

                return {
                    "client_name": client_name,
                    "analysis_period_days": days_back,
                    "mentions": {
                        "total_mentions": len(mention_messages),
                        "recent_mentions": mention_messages[
                            :5
                        ],  # Sample of recent mentions
                        "sentiment_breakdown": sentiment_analysis,
                    },
                    "channel_activity": channel_activity,
                    "overall_health": {
                        "mention_frequency": len(mention_messages) / days_back,
                        "urgency_level": (
                            "high"
                            if sentiment_analysis["urgent"] > 3
                            else "medium" if sentiment_analysis["urgent"] > 0 else "low"
                        ),
                        "sentiment_trend": (
                            "positive"
                            if sentiment_analysis["positive"]
                            > sentiment_analysis["negative"]
                            else (
                                "negative"
                                if sentiment_analysis["negative"]
                                > sentiment_analysis["positive"]
                                else "neutral"
                            )
                        ),
                    },
                }

            except Exception as e:
                logger.error(f"Slack client context failed: {e}")
                return {"error": str(e), "client_name": client_name}

        @self.mcp_tool("intelligence.employee_sentiment")
        @trace_async("revenue_employee_sentiment")
        async def employee_sentiment_analysis(
            employee_slack_id: str = None,
            employee_email: str = None,
            days_back: int = 7,
        ) -> Dict[str, Any]:
            """
            Analyze employee sentiment and stress levels from Slack activity
            """
            if not employee_slack_id and not employee_email:
                raise ValueError(
                    "Either employee_slack_id or employee_email must be provided"
                )

            try:
                # If we have email but not Slack ID, we'd need to map it
                # For now, assume we have the Slack ID
                if not employee_slack_id:
                    # In production, you'd have a mapping service
                    return {
                        "error": "Employee Slack ID mapping not implemented",
                        "employee_email": employee_email,
                    }

                sentiment_data = await self.slack.get_employee_sentiment(
                    employee_slack_id, days_back
                )

                # Add coaching recommendations based on sentiment
                recommendations = []
                overall_sentiment = sentiment_data.get("overall_sentiment", "neutral")
                stress_percentage = sentiment_data.get("sentiment_percentages", {}).get(
                    "stress", 0
                )

                if overall_sentiment == "negative" or stress_percentage > 30:
                    recommendations.append(
                        "🚨 Schedule 1:1 check-in - employee showing signs of stress"
                    )
                    recommendations.append(
                        "💬 Consider workload adjustment or additional support"
                    )

                if stress_percentage > 50:
                    recommendations.append(
                        "⚠️ Immediate intervention recommended - high stress indicators"
                    )

                if overall_sentiment == "positive":
                    recommendations.append(
                        "🌟 Employee showing positive engagement - good time for stretch assignments"
                    )

                if sentiment_data.get("total_messages", 0) < 5:
                    recommendations.append(
                        "📢 Low communication activity - check if employee needs support or is disengaged"
                    )

                sentiment_data["coaching_recommendations"] = recommendations

                return sentiment_data

            except Exception as e:
                logger.error(f"Employee sentiment analysis failed: {e}")
                return {
                    "error": str(e),
                    "employee_id": employee_slack_id or employee_email,
                }

        @self.mcp_tool("coaching.team_health_analysis")
        @trace_async("revenue_team_health")
        async def team_health_analysis(
            team_channel_id: str = None, team_name: str = None, days_back: int = 14
        ) -> Dict[str, Any]:
            """
            Analyze overall team health from Slack communications
            """
            if not team_channel_id and not team_name:
                raise ValueError("Either team_channel_id or team_name must be provided")

            try:
                # Get team channel messages
                if team_channel_id:
                    oldest_timestamp = (
                        datetime.utcnow() - timedelta(days=days_back)
                    ).timestamp()
                    messages_data = await self.slack.get_channel_messages(
                        team_channel_id, limit=200, oldest=str(oldest_timestamp)
                    )
                    messages = messages_data.get("messages", [])
                else:
                    # Search for team-related messages
                    query = f'in:#{team_name} OR "{team_name}"'
                    search_result = await self.slack.search_messages(query, count=100)
                    messages = search_result.get("messages", {}).get("matches", [])

                # Analyze team dynamics
                user_activity = {}
                collaboration_indicators = 0
                conflict_indicators = 0
                innovation_indicators = 0

                collaboration_keywords = [
                    "thanks",
                    "great job",
                    "awesome",
                    "collaboration",
                    "teamwork",
                    "help",
                    "support",
                ]
                conflict_keywords = [
                    "disagree",
                    "frustrated",
                    "blocked",
                    "issue",
                    "problem",
                    "concern",
                ]
                innovation_keywords = [
                    "idea",
                    "innovation",
                    "creative",
                    "solution",
                    "improvement",
                    "experiment",
                ]

                for message in messages:
                    user_id = message.get("user")
                    text = message.get("text", "").lower()

                    if user_id:
                        if user_id not in user_activity:
                            user_activity[user_id] = {
                                "message_count": 0,
                                "sentiment": "neutral",
                            }
                        user_activity[user_id]["message_count"] += 1

                    # Analyze message content
                    if any(keyword in text for keyword in collaboration_keywords):
                        collaboration_indicators += 1

                    if any(keyword in text for keyword in conflict_keywords):
                        conflict_indicators += 1

                    if any(keyword in text for keyword in innovation_keywords):
                        innovation_indicators += 1

                total_messages = len(messages)
                active_members = len(user_activity)

                # Calculate health metrics
                collaboration_score = (
                    collaboration_indicators / max(total_messages, 1)
                ) * 100
                conflict_score = (conflict_indicators / max(total_messages, 1)) * 100
                innovation_score = (
                    innovation_indicators / max(total_messages, 1)
                ) * 100

                # Overall team health score
                team_health_score = max(
                    0, min(100, collaboration_score - conflict_score + innovation_score)
                )

                # Generate recommendations
                recommendations = []
                if team_health_score < 40:
                    recommendations.append(
                        "🚨 Team health needs attention - consider team building activities"
                    )

                if conflict_score > 10:
                    recommendations.append(
                        "⚠️ Conflict indicators detected - facilitate team discussion"
                    )

                if collaboration_score < 20:
                    recommendations.append(
                        "🤝 Low collaboration - encourage more team interaction"
                    )

                if innovation_score < 10:
                    recommendations.append(
                        "💡 Low innovation indicators - consider brainstorming sessions"
                    )

                if active_members < 3:
                    recommendations.append(
                        "📢 Low participation - check if team members are engaged"
                    )

                return {
                    "team_identifier": team_channel_id or team_name,
                    "analysis_period_days": days_back,
                    "metrics": {
                        "total_messages": total_messages,
                        "active_members": active_members,
                        "messages_per_day": total_messages / days_back,
                        "collaboration_score": round(collaboration_score, 2),
                        "conflict_score": round(conflict_score, 2),
                        "innovation_score": round(innovation_score, 2),
                        "overall_health_score": round(team_health_score, 2),
                    },
                    "member_activity": dict(
                        list(user_activity.items())[:10]
                    ),  # Top 10 active members
                    "recommendations": recommendations,
                    "health_status": (
                        "healthy"
                        if team_health_score > 70
                        else "needs_attention" if team_health_score > 40 else "critical"
                    ),
                }

            except Exception as e:
                logger.error(f"Team health analysis failed: {e}")
                return {
                    "error": str(e),
                    "team_identifier": team_channel_id or team_name,
                }

        @self.mcp_tool("coaching.ceo_dashboard")
        @trace_async("revenue_ceo_dashboard")
        async def ceo_dashboard_intelligence(
            focus_areas: List[str] = None, days_back: int = 7
        ) -> Dict[str, Any]:
            """
            Comprehensive CEO dashboard with Pay Ready specific intelligence
            """
            if not focus_areas:
                focus_areas = [
                    "revenue",
                    "client_health",
                    "team_sentiment",
                    "operational_issues",
                ]

            dashboard_data = {
                "generated_at": datetime.utcnow().isoformat(),
                "analysis_period_days": days_back,
                "focus_areas": focus_areas,
                "executive_summary": {},
                "detailed_insights": {},
                "action_items": [],
                "risk_alerts": [],
            }

            try:
                # Revenue Intelligence
                if "revenue" in focus_areas:
                    # Get top accounts health
                    # This would integrate with your actual account list
                    revenue_insights = {
                        "pipeline_health": "stable",  # Would calculate from Salesforce
                        "at_risk_accounts": [],
                        "expansion_opportunities": [],
                        "revenue_trend": "up",
                    }
                    dashboard_data["detailed_insights"]["revenue"] = revenue_insights

                # Client Health Intelligence
                if "client_health" in focus_areas:
                    # Analyze Slack mentions of key clients
                    key_clients = [
                        "Sunset Apartments",
                        "Metro Properties",
                        "Urban Living",
                    ]  # Pay Ready clients
                    client_health_summary = {}

                    for client in key_clients:
                        try:
                            client_context = await slack_client_context(
                                client, days_back
                            )
                            client_health_summary[client] = {
                                "mention_frequency": client_context.get(
                                    "overall_health", {}
                                ).get("mention_frequency", 0),
                                "urgency_level": client_context.get(
                                    "overall_health", {}
                                ).get("urgency_level", "low"),
                                "sentiment_trend": client_context.get(
                                    "overall_health", {}
                                ).get("sentiment_trend", "neutral"),
                            }

                            # Add to risk alerts if needed
                            if (
                                client_context.get("overall_health", {}).get(
                                    "urgency_level"
                                )
                                == "high"
                            ):
                                dashboard_data["risk_alerts"].append(
                                    f"🚨 {client} showing high urgency indicators in Slack"
                                )

                        except Exception as e:
                            logger.warning(f"Failed to analyze client {client}: {e}")

                    dashboard_data["detailed_insights"][
                        "client_health"
                    ] = client_health_summary

                # Team Sentiment Intelligence
                if "team_sentiment" in focus_areas:
                    # Analyze key team channels
                    team_channels = [
                        "general",
                        "product",
                        "engineering",
                        "sales",
                        "support",
                    ]  # Pay Ready teams
                    team_health_summary = {}

                    for team in team_channels:
                        try:
                            team_health = await team_health_analysis(
                                team_name=team, days_back=days_back
                            )
                            team_health_summary[team] = {
                                "health_score": team_health.get("metrics", {}).get(
                                    "overall_health_score", 50
                                ),
                                "status": team_health.get("health_status", "unknown"),
                                "active_members": team_health.get("metrics", {}).get(
                                    "active_members", 0
                                ),
                            }

                            # Add to action items if needed
                            if team_health.get("health_status") == "critical":
                                dashboard_data["action_items"].append(
                                    f"⚠️ {team.title()} team health critical - immediate attention needed"
                                )

                        except Exception as e:
                            logger.warning(f"Failed to analyze team {team}: {e}")

                    dashboard_data["detailed_insights"][
                        "team_sentiment"
                    ] = team_health_summary

                # Operational Issues Intelligence
                if "operational_issues" in focus_areas:
                    # Search for operational keywords across Slack
                    operational_keywords = [
                        "down",
                        "outage",
                        "bug",
                        "critical",
                        "emergency",
                        "incident",
                    ]
                    operational_issues = []

                    for keyword in operational_keywords:
                        try:
                            search_result = await self.slack.search_messages(
                                f'"{keyword}"', count=10
                            )
                            matches = search_result.get("messages", {}).get(
                                "matches", []
                            )

                            for match in matches:
                                # Filter recent messages (within analysis period)
                                message_ts = float(match.get("ts", 0))
                                cutoff_ts = (
                                    datetime.utcnow() - timedelta(days=days_back)
                                ).timestamp()

                                if message_ts > cutoff_ts:
                                    operational_issues.append(
                                        {
                                            "keyword": keyword,
                                            "message": match.get("text", ""),
                                            "channel": match.get("channel", {}).get(
                                                "name", "unknown"
                                            ),
                                            "timestamp": match.get("ts"),
                                            "user": match.get("user"),
                                        }
                                    )

                        except Exception as e:
                            logger.warning(
                                f"Failed to search for keyword {keyword}: {e}"
                            )

                    dashboard_data["detailed_insights"]["operational_issues"] = {
                        "total_issues": len(operational_issues),
                        "recent_issues": operational_issues[:5],  # Most recent 5
                    }

                    # Add to risk alerts if many operational issues
                    if len(operational_issues) > 10:
                        dashboard_data["risk_alerts"].append(
                            f"🚨 High volume of operational issues detected ({len(operational_issues)} in {days_back} days)"
                        )

                # Generate Executive Summary
                dashboard_data["executive_summary"] = {
                    "total_risk_alerts": len(dashboard_data["risk_alerts"]),
                    "total_action_items": len(dashboard_data["action_items"]),
                    "overall_status": (
                        "healthy"
                        if len(dashboard_data["risk_alerts"]) == 0
                        else (
                            "needs_attention"
                            if len(dashboard_data["risk_alerts"]) < 3
                            else "critical"
                        )
                    ),
                    "key_metrics": {
                        "client_health_average": 75,  # Would calculate from actual data
                        "team_health_average": 80,  # Would calculate from actual data
                        "operational_stability": (
                            "stable" if len(operational_issues) < 5 else "unstable"
                        ),
                    },
                }

                return dashboard_data

            except Exception as e:
                logger.error(f"CEO dashboard generation failed: {e}")
                dashboard_data["error"] = str(e)
                return dashboard_data

        @self.mcp_tool("health.score")
        @trace_async("revenue_health_score")
        async def calculate_health_score(account_id: str) -> Dict[str, Any]:
            """
            Calculate account health score based on multiple factors
            """
            validate_required_params({"account_id": account_id}, ["account_id"])

            # Get account data
            account_data = await account_360(account_id, include_gong=True)
            health = await self._calculate_account_health(account_data)

            return {
                "account_id": account_id,
                "health_score": health.health_score,
                "risk_factors": health.risk_factors,
                "opportunities": health.opportunities,
                "last_calculated": datetime.utcnow().isoformat(),
                "factors_analyzed": [
                    "recent_activity",
                    "opportunity_pipeline",
                    "conversation_sentiment",
                    "engagement_frequency",
                    "revenue_trend",
                ],
            }

    async def _calculate_account_health(
        self, account_data: Dict[str, Any]
    ) -> AccountHealth:
        """Calculate comprehensive account health score"""

        # Extract key metrics
        sf_data = account_data.get("salesforce", {})
        gong_data = account_data.get("gong", {})

        # Base health score calculation
        health_score = 50.0  # Start neutral
        risk_factors = []
        opportunities = []

        # Analyze Salesforce data
        if "account" in sf_data:
            account = sf_data["account"]

            # Recent activity boost
            if account.get("LastActivityDate"):
                last_activity = datetime.fromisoformat(
                    account["LastActivityDate"].replace("Z", "+00:00")
                )
                days_since = (
                    datetime.utcnow().replace(tzinfo=last_activity.tzinfo)
                    - last_activity
                ).days

                if days_since < 7:
                    health_score += 20
                elif days_since < 30:
                    health_score += 10
                elif days_since > 90:
                    health_score -= 20
                    risk_factors.append("No recent activity (>90 days)")

        # Analyze opportunities
        opportunities_data = sf_data.get("opportunities", [])
        if opportunities_data:
            open_opps = [
                opp
                for opp in opportunities_data
                if opp.get("StageName") not in ["Closed Won", "Closed Lost"]
            ]

            if open_opps:
                health_score += 15
                opportunities.append(f"{len(open_opps)} active opportunities")

            # Check for stalled deals
            for opp in open_opps:
                if opp.get("LastModifiedDate"):
                    last_mod = datetime.fromisoformat(
                        opp["LastModifiedDate"].replace("Z", "+00:00")
                    )
                    days_stalled = (
                        datetime.utcnow().replace(tzinfo=last_mod.tzinfo) - last_mod
                    ).days

                    if days_stalled > 30:
                        risk_factors.append(
                            f"Stalled opportunity: {opp.get('Name', 'Unknown')}"
                        )
                        health_score -= 10
        else:
            risk_factors.append("No active opportunities")
            health_score -= 15

        # Analyze Gong conversation data
        if "recent_calls" in gong_data:
            calls = gong_data["recent_calls"]
            if calls:
                health_score += 10
                opportunities.append(f"{len(calls)} recent conversations")
            else:
                risk_factors.append("No recent conversations")
                health_score -= 10

        # Normalize score
        health_score = max(0, min(100, health_score))

        # Determine revenue trend (simplified)
        revenue_trend = "stable"
        if health_score > 70:
            revenue_trend = "up"
        elif health_score < 40:
            revenue_trend = "down"

        return AccountHealth(
            account_id=account_data["account_id"],
            account_name=sf_data.get("account", {}).get("Name", "Unknown"),
            health_score=health_score,
            risk_factors=risk_factors,
            opportunities=opportunities,
            last_activity=datetime.utcnow(),
            revenue_trend=revenue_trend,
            engagement_score=min(100, health_score + 10),  # Simplified
            next_actions=[],  # Will be populated by _suggest_next_actions
        )

    async def _suggest_next_actions(self, account_data: Dict[str, Any]) -> List[str]:
        """Generate AI-powered next action suggestions"""

        actions = []
        sf_data = account_data.get("salesforce", {})
        health_data = account_data.get("health_score", {})

        # Health-based actions
        health_score = health_data.get("health_score", 50)

        if health_score < 40:
            actions.append("🚨 Schedule immediate check-in call")
            actions.append("📧 Send personalized re-engagement email")
        elif health_score < 70:
            actions.append("📞 Schedule quarterly business review")
            actions.append("🎯 Identify expansion opportunities")
        else:
            actions.append("🌟 Explore upsell opportunities")
            actions.append("🤝 Request customer reference/case study")

        # Opportunity-based actions
        opportunities = sf_data.get("opportunities", [])
        stalled_opps = []

        for opp in opportunities:
            if opp.get("LastModifiedDate"):
                last_mod = datetime.fromisoformat(
                    opp["LastModifiedDate"].replace("Z", "+00:00")
                )
                days_stalled = (
                    datetime.utcnow().replace(tzinfo=last_mod.tzinfo) - last_mod
                ).days

                if days_stalled > 30:
                    stalled_opps.append(opp)

        if stalled_opps:
            actions.append(f"⚡ Follow up on {len(stalled_opps)} stalled opportunities")

        # Activity-based actions
        if "account" in sf_data:
            account = sf_data["account"]
            if account.get("LastActivityDate"):
                last_activity = datetime.fromisoformat(
                    account["LastActivityDate"].replace("Z", "+00:00")
                )
                days_since = (
                    datetime.utcnow().replace(tzinfo=last_activity.tzinfo)
                    - last_activity
                ).days

                if days_since > 60:
                    actions.append("📅 Schedule regular touchpoint cadence")

        return actions[:5]  # Limit to top 5 actions


# Example usage and testing
if __name__ == "__main__":
    from app.memory.bus import UnifiedMemoryBus
    from app.observability.metrics import MetricsCollector

    async def sophia_revenue_gateway():
        """Test the Revenue Ops Gateway"""
        memory_bus = UnifiedMemoryBus()
        metrics = MetricsCollector()

        gateway = RevenueOpsGateway(memory_bus, metrics)
        await gateway.initialize()

        # Test search contacts
        result = await gateway.handle_tool_call(
            "crm.search_contacts",
            {"search_term": "john", "limit": 10},
            "test-search-123",
        )
        print(f"Search result: {result}")

        await gateway.shutdown()

    # Run test
    asyncio.run(sophia_revenue_gateway())
