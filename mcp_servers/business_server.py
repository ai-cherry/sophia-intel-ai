"""
Business Server - MCP server for business intelligence operations
Integrates with Gong, HubSpot, Slack, Salesforce, Notion, and other business tools.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import asyncio
import httpx

logger = logging.getLogger(__name__)

# Pydantic models
class BusinessDataRequest(BaseModel):
    source: str  # gong, hubspot, slack, salesforce, notion
    data_type: str  # calls, contacts, deals, messages, pages
    date_range: Optional[Dict[str, str]] = None  # start_date, end_date
    filters: Optional[Dict[str, Any]] = None

class BusinessDataResponse(BaseModel):
    source: str
    data_type: str
    data: List[Dict[str, Any]]
    total_records: int
    retrieved_at: datetime

class CustomerInsightRequest(BaseModel):
    customer_id: Optional[str] = None
    customer_email: Optional[str] = None
    include_calls: Optional[bool] = True
    include_emails: Optional[bool] = True
    include_deals: Optional[bool] = True
    days_back: Optional[int] = 30

class CustomerInsight(BaseModel):
    customer_id: str
    customer_name: str
    customer_email: str
    recent_interactions: List[Dict[str, Any]]
    deal_status: Optional[Dict[str, Any]] = None
    engagement_score: Optional[float] = None
    insights: List[str]
    last_interaction: Optional[datetime] = None

class SalesMetricsRequest(BaseModel):
    metric_types: List[str]  # revenue, deals_closed, call_volume, etc.
    time_period: str  # daily, weekly, monthly, quarterly
    date_range: Optional[Dict[str, str]] = None

class SalesMetrics(BaseModel):
    metrics: Dict[str, Any]
    time_period: str
    generated_at: datetime

class TeamPerformanceRequest(BaseModel):
    team_members: Optional[List[str]] = None
    metrics: Optional[List[str]] = None
    date_range: Optional[Dict[str, str]] = None

# Create router
router = APIRouter()

async def get_api_manager():
    """Get API manager for business service integrations."""
    from sophia.core.api_manager import SOPHIAAPIManager
    return SOPHIAAPIManager()

async def get_model_router():
    """Get model router for data analysis and insights."""
    from sophia.core.ultimate_model_router import UltimateModelRouter
    return UltimateModelRouter()

async def get_gong_client():
    """Get Gong API client."""
    access_key = os.getenv("GONG_ACCESS_KEY")
    client_secret = os.getenv("GONG_CLIENT_SECRET")
    
    if not access_key or not client_secret:
        logger.warning("Gong credentials not configured")
        return None
    
    # TODO: Implement proper Gong client
    return {"access_key": access_key, "client_secret": client_secret}

async def get_hubspot_client():
    """Get HubSpot API client."""
    api_key = os.getenv("HUBSPOT_API_KEY")
    
    if not api_key:
        logger.warning("HubSpot API key not configured")
        return None
    
    # TODO: Implement proper HubSpot client
    return {"api_key": api_key}

async def get_salesforce_client():
    """Get Salesforce API client."""
    # TODO: Implement Salesforce OAuth client
    logger.warning("Salesforce client not yet implemented")
    return None

async def get_slack_client():
    """Get Slack API client."""
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    
    if not bot_token:
        logger.warning("Slack bot token not configured")
        return None
    
    # TODO: Implement proper Slack client
    return {"bot_token": bot_token}

async def get_notion_client():
    """Get Notion API client."""
    api_key = os.getenv("NOTION_API_KEY")
    
    if not api_key:
        logger.warning("Notion API key not configured")
        return None
    
    # TODO: Implement proper Notion client
    return {"api_key": api_key}

@router.post("/data", response_model=BusinessDataResponse)
async def fetch_business_data(
    request: BusinessDataRequest,
    api_manager = Depends(get_api_manager)
):
    """
    Fetch data from specified business source.
    """
    try:
        data = []
        
        if request.source == "gong":
            data = await fetch_gong_data(request)
        elif request.source == "hubspot":
            data = await fetch_hubspot_data(request)
        elif request.source == "slack":
            data = await fetch_slack_data(request)
        elif request.source == "salesforce":
            data = await fetch_salesforce_data(request)
        elif request.source == "notion":
            data = await fetch_notion_data(request)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported source: {request.source}")
        
        return BusinessDataResponse(
            source=request.source,
            data_type=request.data_type,
            data=data,
            total_records=len(data),
            retrieved_at=datetime.now(timezone.utc)
        )
        
    except Exception as e:
        logger.error(f"Business data fetch failed: {e}")
        raise HTTPException(status_code=500, detail=f"Data fetch failed: {str(e)}")

async def fetch_gong_data(request: BusinessDataRequest) -> List[Dict[str, Any]]:
    """Fetch data from Gong API."""
    try:
        gong_client = await get_gong_client()
        if not gong_client:
            return []
        
        # TODO: Implement actual Gong API calls
        if request.data_type == "calls":
            # Mock call data
            return [
                {
                    "call_id": "call_123",
                    "title": "Customer Discovery Call",
                    "duration": 3600,
                    "participants": ["john@company.com", "customer@client.com"],
                    "date": "2024-01-15T10:00:00Z",
                    "outcome": "Qualified",
                    "next_steps": "Send proposal"
                }
            ]
        
        return []
        
    except Exception as e:
        logger.error(f"Gong data fetch failed: {e}")
        return []

async def fetch_hubspot_data(request: BusinessDataRequest) -> List[Dict[str, Any]]:
    """Fetch data from HubSpot API."""
    try:
        hubspot_client = await get_hubspot_client()
        if not hubspot_client:
            return []
        
        # TODO: Implement actual HubSpot API calls
        if request.data_type == "contacts":
            # Mock contact data
            return [
                {
                    "contact_id": "contact_123",
                    "email": "customer@client.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "company": "Client Corp",
                    "lifecycle_stage": "customer",
                    "last_activity": "2024-01-15T10:00:00Z"
                }
            ]
        elif request.data_type == "deals":
            # Mock deal data
            return [
                {
                    "deal_id": "deal_123",
                    "deal_name": "Q1 Enterprise Deal",
                    "amount": 50000,
                    "stage": "proposal",
                    "close_date": "2024-02-15",
                    "probability": 0.7
                }
            ]
        
        return []
        
    except Exception as e:
        logger.error(f"HubSpot data fetch failed: {e}")
        return []

async def fetch_slack_data(request: BusinessDataRequest) -> List[Dict[str, Any]]:
    """Fetch data from Slack API."""
    try:
        slack_client = await get_slack_client()
        if not slack_client:
            return []
        
        # TODO: Implement actual Slack API calls
        if request.data_type == "messages":
            # Mock message data
            return [
                {
                    "message_id": "msg_123",
                    "channel": "#sales",
                    "user": "john.doe",
                    "text": "Great call with the client today!",
                    "timestamp": "2024-01-15T10:00:00Z",
                    "reactions": ["thumbsup", "fire"]
                }
            ]
        
        return []
        
    except Exception as e:
        logger.error(f"Slack data fetch failed: {e}")
        return []

async def fetch_salesforce_data(request: BusinessDataRequest) -> List[Dict[str, Any]]:
    """Fetch data from Salesforce API."""
    try:
        # TODO: Implement Salesforce API integration
        logger.warning("Salesforce integration not yet implemented")
        return []
        
    except Exception as e:
        logger.error(f"Salesforce data fetch failed: {e}")
        return []

async def fetch_notion_data(request: BusinessDataRequest) -> List[Dict[str, Any]]:
    """Fetch data from Notion API."""
    try:
        notion_client = await get_notion_client()
        if not notion_client:
            return []
        
        # TODO: Implement actual Notion API calls
        if request.data_type == "pages":
            # Mock page data
            return [
                {
                    "page_id": "page_123",
                    "title": "Q1 Sales Strategy",
                    "created_time": "2024-01-01T00:00:00Z",
                    "last_edited_time": "2024-01-15T10:00:00Z",
                    "properties": {
                        "Status": "In Progress",
                        "Owner": "Sales Team"
                    }
                }
            ]
        
        return []
        
    except Exception as e:
        logger.error(f"Notion data fetch failed: {e}")
        return []

@router.post("/customer-insights", response_model=CustomerInsight)
async def get_customer_insights(
    request: CustomerInsightRequest,
    api_manager = Depends(get_api_manager),
    model_router = Depends(get_model_router)
):
    """
    Generate comprehensive customer insights from multiple sources.
    """
    try:
        # Fetch data from multiple sources
        interactions = []
        
        if request.include_calls:
            # Fetch call data from Gong
            call_request = BusinessDataRequest(
                source="gong",
                data_type="calls",
                filters={"customer_email": request.customer_email}
            )
            call_data = await fetch_gong_data(call_request)
            interactions.extend([{**call, "type": "call"} for call in call_data])
        
        if request.include_emails:
            # Fetch email data from HubSpot
            email_request = BusinessDataRequest(
                source="hubspot",
                data_type="emails",
                filters={"customer_email": request.customer_email}
            )
            # TODO: Implement email fetching
            pass
        
        if request.include_deals:
            # Fetch deal data from HubSpot/Salesforce
            deal_request = BusinessDataRequest(
                source="hubspot",
                data_type="deals",
                filters={"customer_email": request.customer_email}
            )
            deal_data = await fetch_hubspot_data(deal_request)
        
        # Generate insights using AI
        insights = await generate_customer_insights(
            request.customer_email, interactions, model_router
        )
        
        # Calculate engagement score
        engagement_score = calculate_engagement_score(interactions)
        
        # Find last interaction
        last_interaction = None
        if interactions:
            last_interaction = max(
                interactions,
                key=lambda x: x.get("date", x.get("timestamp", ""))
            ).get("date", interactions[0].get("timestamp"))
            if isinstance(last_interaction, str):
                last_interaction = datetime.fromisoformat(last_interaction.replace("Z", "+00:00"))
        
        return CustomerInsight(
            customer_id=request.customer_id or "unknown",
            customer_name="John Doe",  # TODO: Extract from data
            customer_email=request.customer_email or "unknown",
            recent_interactions=interactions,
            deal_status=deal_data[0] if 'deal_data' in locals() and deal_data else None,
            engagement_score=engagement_score,
            insights=insights,
            last_interaction=last_interaction
        )
        
    except Exception as e:
        logger.error(f"Customer insights generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Insights generation failed: {str(e)}")

async def generate_customer_insights(customer_email: str, interactions: List[Dict], model_router) -> List[str]:
    """Generate AI-powered customer insights."""
    try:
        if not interactions:
            return ["No recent interactions found"]
        
        # Prepare data for analysis
        interaction_summary = f"Customer: {customer_email}\n\n"
        interaction_summary += f"Recent Interactions ({len(interactions)} total):\n\n"
        
        for i, interaction in enumerate(interactions[:5], 1):  # Limit to 5 most recent
            interaction_summary += f"{i}. {interaction.get('type', 'unknown').title()}\n"
            interaction_summary += f"   Date: {interaction.get('date', interaction.get('timestamp', 'unknown'))}\n"
            if interaction.get('title'):
                interaction_summary += f"   Title: {interaction['title']}\n"
            if interaction.get('outcome'):
                interaction_summary += f"   Outcome: {interaction['outcome']}\n"
            if interaction.get('next_steps'):
                interaction_summary += f"   Next Steps: {interaction['next_steps']}\n"
            interaction_summary += "\n"
        
        model_config = model_router.select_model("analysis")
        
        insights_prompt = f"""
Analyze the following customer interaction data and provide actionable business insights:

{interaction_summary}

Please provide 3-5 specific insights about:
1. Customer engagement level and trends
2. Sales opportunity assessment
3. Relationship health and risk factors
4. Recommended next actions
5. Areas requiring attention

Format as a list of concise, actionable insights.

Insights:
"""
        
        response = await model_router.call_model(
            model_config,
            insights_prompt,
            temperature=0.3,
            max_tokens=1024
        )
        
        # Parse insights from response
        insights = []
        for line in response.split('\n'):
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                insights.append(line.lstrip('-•0123456789. '))
        
        return insights if insights else ["Analysis completed - no specific insights generated"]
        
    except Exception as e:
        logger.error(f"Insight generation failed: {e}")
        return ["Insight generation failed"]

def calculate_engagement_score(interactions: List[Dict]) -> float:
    """Calculate customer engagement score based on interactions."""
    if not interactions:
        return 0.0
    
    score = 0.0
    
    # Score based on interaction frequency
    score += min(len(interactions) * 0.1, 0.5)  # Max 0.5 for frequency
    
    # Score based on interaction types
    for interaction in interactions:
        interaction_type = interaction.get('type', '')
        if interaction_type == 'call':
            score += 0.3
        elif interaction_type == 'email':
            score += 0.2
        elif interaction_type == 'meeting':
            score += 0.4
    
    # Score based on outcomes
    for interaction in interactions:
        outcome = interaction.get('outcome', '').lower()
        if 'qualified' in outcome or 'positive' in outcome:
            score += 0.2
        elif 'closed' in outcome or 'won' in outcome:
            score += 0.5
    
    return min(score, 1.0)  # Cap at 1.0

@router.post("/sales-metrics", response_model=SalesMetrics)
async def get_sales_metrics(
    request: SalesMetricsRequest,
    api_manager = Depends(get_api_manager)
):
    """
    Generate sales performance metrics from business data.
    """
    try:
        metrics = {}
        
        # TODO: Implement actual metrics calculation from real data
        # For now, return mock metrics
        
        if "revenue" in request.metric_types:
            metrics["revenue"] = {
                "current_period": 125000,
                "previous_period": 110000,
                "growth_rate": 0.136,
                "target": 150000,
                "achievement": 0.833
            }
        
        if "deals_closed" in request.metric_types:
            metrics["deals_closed"] = {
                "current_period": 15,
                "previous_period": 12,
                "growth_rate": 0.25,
                "target": 20,
                "achievement": 0.75
            }
        
        if "call_volume" in request.metric_types:
            metrics["call_volume"] = {
                "current_period": 85,
                "previous_period": 78,
                "growth_rate": 0.09,
                "average_duration": 45.5
            }
        
        return SalesMetrics(
            metrics=metrics,
            time_period=request.time_period,
            generated_at=datetime.now(timezone.utc)
        )
        
    except Exception as e:
        logger.error(f"Sales metrics generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics generation failed: {str(e)}")

@router.get("/integrations/status")
async def get_integration_status():
    """Get status of all business integrations."""
    integrations = {
        "gong": {
            "status": "configured" if os.getenv("GONG_ACCESS_KEY") else "not_configured",
            "capabilities": ["calls", "recordings", "analytics"]
        },
        "hubspot": {
            "status": "configured" if os.getenv("HUBSPOT_API_KEY") else "not_configured",
            "capabilities": ["contacts", "deals", "companies", "emails"]
        },
        "slack": {
            "status": "configured" if os.getenv("SLACK_BOT_TOKEN") else "not_configured",
            "capabilities": ["messages", "channels", "users"]
        },
        "salesforce": {
            "status": "not_implemented",
            "capabilities": ["leads", "opportunities", "accounts", "contacts"]
        },
        "notion": {
            "status": "configured" if os.getenv("NOTION_API_KEY") else "not_configured",
            "capabilities": ["pages", "databases", "blocks"]
        }
    }
    
    return {
        "integrations": integrations,
        "total_configured": sum(1 for i in integrations.values() if i["status"] == "configured"),
        "total_available": len(integrations)
    }

@router.get("/health")
async def business_server_health():
    """Health check for business server."""
    return {
        "status": "healthy",
        "service": "business_server",
        "integrations": {
            "gong": "configured" if os.getenv("GONG_ACCESS_KEY") else "missing",
            "hubspot": "configured" if os.getenv("HUBSPOT_API_KEY") else "missing",
            "slack": "configured" if os.getenv("SLACK_BOT_TOKEN") else "missing",
            "notion": "configured" if os.getenv("NOTION_API_KEY") else "missing"
        },
        "capabilities": [
            "multi_source_data_fetch",
            "customer_insights",
            "sales_metrics",
            "team_performance"
        ]
    }

