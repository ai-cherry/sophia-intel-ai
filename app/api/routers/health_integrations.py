"""
Health monitoring endpoint for all Sophia business integrations
Provides real-time status for Gong, Salesforce, HubSpot, Looker, Slack, Asana, Airtable, Linear
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.env import load_env_once

# Load environment once
load_env_once()

router = APIRouter(prefix="/health", tags=["health"])


class IntegrationHealth(BaseModel):
    """Health status for a single integration"""
    name: str
    status: str  # healthy, degraded, unhealthy, unknown
    last_check: datetime
    last_sync: Optional[datetime] = None
    error: Optional[str] = None
    rate_limit: Optional[Dict[str, Any]] = None
    details: Optional[Dict[str, Any]] = None


class OverallHealth(BaseModel):
    """Overall system health with all integrations"""
    overall: str  # healthy, degraded, unhealthy
    timestamp: datetime
    integrations: Dict[str, Dict[str, Any]]
    total_integrations: int
    healthy_count: int
    degraded_count: int
    unhealthy_count: int


async def check_gong_health() -> Dict[str, Any]:
    """Check Gong API health"""
    try:
        access_key = os.getenv("GONG_ACCESS_KEY")
        access_secret = os.getenv("GONG_ACCESS_SECRET")
        
        if not access_key or not access_secret:
            return {
                "status": "unconfigured",
                "error": "Gong credentials not configured",
                "last_check": datetime.utcnow()
            }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            auth = httpx.BasicAuth(access_key, access_secret)
            response = await client.get(
                "https://api.gong.io/v2/users",
                auth=auth,
                params={"limit": 1}
            )
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "last_check": datetime.utcnow(),
                    "rate_limit": {
                        "remaining": response.headers.get("X-RateLimit-Remaining"),
                        "reset": response.headers.get("X-RateLimit-Reset")
                    }
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"API returned {response.status_code}",
                    "last_check": datetime.utcnow()
                }
                
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.utcnow()
        }


async def check_salesforce_health() -> Dict[str, Any]:
    """Check Salesforce API health"""
    try:
        client_id = os.getenv("SALESFORCE_CLIENT_ID")
        instance_url = os.getenv("SALESFORCE_INSTANCE_URL")
        
        if not client_id:
            return {
                "status": "unconfigured",
                "error": "Salesforce credentials not configured",
                "last_check": datetime.utcnow()
            }
        
        # For now, just check if configured
        # Full implementation would do OAuth flow and test query
        return {
            "status": "configured",
            "last_check": datetime.utcnow(),
            "details": {"instance_url": instance_url}
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.utcnow()
        }


async def check_hubspot_health() -> Dict[str, Any]:
    """Check HubSpot API health"""
    try:
        api_key = os.getenv("HUBSPOT_API_KEY")
        
        if not api_key:
            return {
                "status": "unconfigured",
                "error": "HubSpot API key not configured",
                "last_check": datetime.utcnow()
            }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.hubapi.com/account-info/v3/api-usage/daily",
                headers={"Authorization": f"Bearer {api_key}"},
                params={"limit": 1}
            )
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "last_check": datetime.utcnow(),
                    "rate_limit": {
                        "daily_limit": 500000,  # Standard limit
                        "used_today": response.headers.get("X-HubSpot-RateLimit-Daily-Remaining")
                    }
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"API returned {response.status_code}",
                    "last_check": datetime.utcnow()
                }
                
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.utcnow()
        }


async def check_looker_health() -> Dict[str, Any]:
    """Check Looker API health"""
    try:
        base_url = os.getenv("LOOKERSDK_BASE_URL")
        client_id = os.getenv("LOOKERSDK_CLIENT_ID")
        
        if not base_url or not client_id:
            return {
                "status": "unconfigured",
                "error": "Looker credentials not configured",
                "last_check": datetime.utcnow()
            }
        
        # Basic config check for now
        return {
            "status": "configured",
            "last_check": datetime.utcnow(),
            "details": {"base_url": base_url}
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.utcnow()
        }


async def check_slack_health() -> Dict[str, Any]:
    """Check Slack API health"""
    try:
        bot_token = os.getenv("SLACK_BOT_TOKEN", os.getenv("SLACK_API_TOKEN"))
        
        if not bot_token:
            return {
                "status": "unconfigured",
                "error": "Slack bot token not configured",
                "last_check": datetime.utcnow()
            }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://slack.com/api/auth.test",
                headers={"Authorization": f"Bearer {bot_token}"}
            )
            
            data = response.json()
            if data.get("ok"):
                return {
                    "status": "healthy",
                    "last_check": datetime.utcnow(),
                    "details": {
                        "team": data.get("team"),
                        "user": data.get("user")
                    }
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": data.get("error", "Unknown error"),
                    "last_check": datetime.utcnow()
                }
                
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.utcnow()
        }


async def check_asana_health() -> Dict[str, Any]:
    """Check Asana API health"""
    try:
        access_token = os.getenv("ASANA_ACCESS_TOKEN", os.getenv("ASANA_API_TOKEN"))
        
        if not access_token:
            return {
                "status": "unconfigured",
                "error": "Asana access token not configured",
                "last_check": datetime.utcnow()
            }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://app.asana.com/api/1.0/users/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "last_check": datetime.utcnow(),
                    "details": {
                        "user": data.get("data", {}).get("name"),
                        "email": data.get("data", {}).get("email")
                    }
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"API returned {response.status_code}",
                    "last_check": datetime.utcnow()
                }
                
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.utcnow()
        }


async def check_linear_health() -> Dict[str, Any]:
    """Check Linear API health"""
    try:
        api_key = os.getenv("LINEAR_API_KEY")
        
        if not api_key:
            return {
                "status": "unconfigured",
                "error": "Linear API key not configured",
                "last_check": datetime.utcnow()
            }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.linear.app/graphql",
                headers={"Authorization": api_key},
                json={"query": "{ viewer { id name } }"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    return {
                        "status": "healthy",
                        "last_check": datetime.utcnow(),
                        "details": {
                            "user": data["data"]["viewer"]["name"]
                        }
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": "Invalid response format",
                        "last_check": datetime.utcnow()
                    }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"API returned {response.status_code}",
                    "last_check": datetime.utcnow()
                }
                
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.utcnow()
        }


async def check_airtable_health() -> Dict[str, Any]:
    """Check Airtable API health"""
    try:
        api_key = os.getenv("AIRTABLE_API_KEY")
        base_id = os.getenv("AIRTABLE_BASE_ID")
        
        if not api_key:
            return {
                "status": "unconfigured",
                "error": "Airtable API key not configured",
                "last_check": datetime.utcnow()
            }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test with metadata endpoint
            response = await client.get(
                f"https://api.airtable.com/v0/meta/bases",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "last_check": datetime.utcnow(),
                    "details": {
                        "base_id": base_id,
                        "rate_limit": "5 requests/second"
                    }
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"API returned {response.status_code}",
                    "last_check": datetime.utcnow()
                }
                
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.utcnow()
        }


@router.get("/integrations", response_model=OverallHealth)
async def get_integration_health() -> OverallHealth:
    """
    Comprehensive health check for all Sophia business integrations.
    
    Returns the health status of:
    - Gong (conversation intelligence)
    - Salesforce (CRM)
    - HubSpot (marketing/sales)
    - Looker (analytics)
    - Slack (communications)
    - Asana (project management)
    - Linear (issue tracking)
    - Airtable (databases)
    """
    
    # Check all integrations in parallel
    health_checks = {
        "gong": check_gong_health(),
        "salesforce": check_salesforce_health(),
        "hubspot": check_hubspot_health(),
        "looker": check_looker_health(),
        "slack": check_slack_health(),
        "asana": check_asana_health(),
        "linear": check_linear_health(),
        "airtable": check_airtable_health()
    }
    
    # Execute all checks concurrently
    results = await asyncio.gather(
        *health_checks.values(),
        return_exceptions=True
    )
    
    # Process results
    integrations = {}
    healthy_count = 0
    degraded_count = 0
    unhealthy_count = 0
    
    for service_name, result in zip(health_checks.keys(), results):
        if isinstance(result, Exception):
            integrations[service_name] = {
                "status": "error",
                "error": str(result),
                "last_check": datetime.utcnow()
            }
            unhealthy_count += 1
        else:
            integrations[service_name] = result
            status = result.get("status", "unknown")
            
            if status == "healthy":
                healthy_count += 1
            elif status in ["configured", "degraded"]:
                degraded_count += 1
            else:
                unhealthy_count += 1
    
    # Determine overall status
    total = len(integrations)
    if healthy_count == total:
        overall = "healthy"
    elif unhealthy_count == 0:
        overall = "degraded"
    else:
        overall = "unhealthy"
    
    return OverallHealth(
        overall=overall,
        timestamp=datetime.utcnow(),
        integrations=integrations,
        total_integrations=total,
        healthy_count=healthy_count,
        degraded_count=degraded_count,
        unhealthy_count=unhealthy_count
    )


@router.get("/integrations/{integration_name}")
async def get_specific_integration_health(integration_name: str) -> IntegrationHealth:
    """Get health status for a specific integration"""
    
    health_checkers = {
        "gong": check_gong_health,
        "salesforce": check_salesforce_health,
        "hubspot": check_hubspot_health,
        "looker": check_looker_health,
        "slack": check_slack_health,
        "asana": check_asana_health,
        "linear": check_linear_health,
        "airtable": check_airtable_health
    }
    
    if integration_name not in health_checkers:
        raise HTTPException(
            status_code=404,
            detail=f"Integration '{integration_name}' not found"
        )
    
    result = await health_checkers[integration_name]()
    
    return IntegrationHealth(
        name=integration_name,
        status=result.get("status", "unknown"),
        last_check=result.get("last_check", datetime.utcnow()),
        last_sync=result.get("last_sync"),
        error=result.get("error"),
        rate_limit=result.get("rate_limit"),
        details=result.get("details")
    )