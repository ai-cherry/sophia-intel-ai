"""
Sophia AI Platform v4.0 - Domains Router
Manages business domains and user access to different platform areas
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.roles import Domain, Role, RolePermissions, require_auth, require_permission
from pydantic import BaseModel, Field
logger = logging.getLogger(__name__)
# Initialize router
router = APIRouter(prefix="/domains", tags=["domains"])
# Request/Response models
class DomainInfo(BaseModel):
    """Domain information model"""
    name: str = Field(..., description="Domain name")
    display_name: str = Field(..., description="Human-readable display name")
    description: str = Field(..., description="Domain description")
    icon: str = Field(..., description="Domain icon identifier")
    category: str = Field(..., description="Domain category/group")
    permissions_required: List[str] = Field(
        default_factory=list, description="Required permissions"
    )
    features: List[str] = Field(default_factory=list, description="Available features")
    status: str = Field(default="active", description="Domain status")
class DomainAccessResponse(BaseModel):
    """Domain access response model"""
    accessible_domains: List[DomainInfo] = Field(default_factory=list)
    domain_groups: Dict[str, List[str]] = Field(default_factory=dict)
    user_role: str = Field(..., description="User role")
    total_domains: int = Field(default=0)
class DomainStatsResponse(BaseModel):
    """Domain statistics response model"""
    domain_name: str = Field(..., description="Domain name")
    active_users: int = Field(default=0, description="Active users in domain")
    total_queries: int = Field(default=0, description="Total queries processed")
    avg_response_time: float = Field(default=0.0, description="Average response time")
    success_rate: float = Field(default=0.0, description="Success rate percentage")
    last_activity: Optional[datetime] = Field(
        None, description="Last activity timestamp"
    )
# Domain configuration
DOMAIN_CONFIG = {
    Domain.CHAT: {
        "display_name": "AI Chat",
        "description": "Intelligent chat interface with multi-source integration",
        "icon": "chat",
        "category": "Core",
        "permissions_required": ["domains.chat"],
        "features": [
            "unified_search",
            "intent_analysis",
            "source_blending",
            "conversation_history",
        ],
    },
    Domain.SALES: {
        "display_name": "Sales Intelligence",
        "description": "Sales analytics, pipeline management, and CRM integration",
        "icon": "trending-up",
        "category": "Sales & Marketing",
        "permissions_required": ["domains.sales"],
        "features": [
            "pipeline_analytics",
            "gong_integration",
            "deal_insights",
            "forecasting",
        ],
    },
    Domain.MARKETING: {
        "display_name": "Marketing Analytics",
        "description": "Marketing campaign analysis and performance metrics",
        "icon": "megaphone",
        "category": "Sales & Marketing",
        "permissions_required": ["domains.marketing"],
        "features": [
            "campaign_analytics",
            "lead_scoring",
            "attribution_analysis",
            "roi_tracking",
        ],
    },
    Domain.BI: {
        "display_name": "Business Intelligence",
        "description": "Advanced analytics and business insights",
        "icon": "bar-chart",
        "category": "Intelligence",
        "permissions_required": ["domains.bi"],
        "features": [
            "custom_dashboards",
            "predictive_analytics",
            "data_visualization",
            "kpi_monitoring",
        ],
    },
    Domain.DEVOPS: {
        "display_name": "DevOps & Monitoring",
        "description": "System monitoring, deployment, and infrastructure management",
        "icon": "server",
        "category": "Technical",
        "permissions_required": ["domains.devops"],
        "features": [
            "system_monitoring",
            "deployment_tracking",
            "log_analysis",
            "performance_metrics",
        ],
    },
    Domain.TRAINING: {
        "display_name": "AI Training",
        "description": "Model training, knowledge base management, and AI optimization",
        "icon": "brain",
        "category": "Intelligence",
        "permissions_required": ["domains.training"],
        "features": [
            "model_training",
            "knowledge_base",
            "persona_management",
            "training_analytics",
        ],
    },
    Domain.ADMIN: {
        "display_name": "Administration",
        "description": "User management, system configuration, and platform administration",
        "icon": "settings",
        "category": "Core",
        "permissions_required": ["domains.admin", "admin.view"],
        "features": [
            "user_management",
            "role_configuration",
            "system_settings",
            "audit_logs",
        ],
    },
    Domain.SUPPORT: {
        "display_name": "Customer Support",
        "description": "Support ticket management and customer communication",
        "icon": "help-circle",
        "category": "Operations",
        "permissions_required": ["domains.support"],
        "features": [
            "ticket_management",
            "slack_integration",
            "customer_insights",
            "response_templates",
        ],
    },
    Domain.RESEARCH: {
        "display_name": "Research & Analysis",
        "description": "Market research, competitive analysis, and trend monitoring",
        "icon": "search",
        "category": "Intelligence",
        "permissions_required": ["domains.research"],
        "features": [
            "market_research",
            "competitor_analysis",
            "trend_monitoring",
            "research_reports",
        ],
    },
    Domain.FINANCE: {
        "display_name": "Financial Analytics",
        "description": "Financial reporting, budget analysis, and revenue tracking",
        "icon": "dollar-sign",
        "category": "Operations",
        "permissions_required": ["domains.finance"],
        "features": [
            "financial_reporting",
            "budget_analysis",
            "revenue_tracking",
            "cost_optimization",
        ],
    },
}
# Dependency for user context
async def get_user_context() -> Dict[str, Any]:
    """Extract user context from request"""
    # Placeholder implementation
    return {
        "user_id": "demo_user",
        "role": Role.MANAGER,  # Use enum
        "domains": ["chat", "sales", "marketing", "bi"],
        "preferences": {},
    }
# Domain endpoints
@router.get(
    "/",
    response_model=DomainAccessResponse,
    summary="Get accessible domains",
    description="Get list of domains accessible to the current user",
)
@require_auth
async def get_accessible_domains(
    user_context: Dict[str, Any] = Depends(get_user_context),
) -> DomainAccessResponse:
    """
    Get domains accessible to the current user based on their role and permissions
    """
    try:
        user_role = user_context.get("role", Role.GUEST)
        # Get accessible domains using RolePermissions
        accessible_domain_names = RolePermissions.get_accessible_domains(user_role)
        domain_groups = RolePermissions.get_domain_groups_for_role(user_role)
        # Build domain info list
        accessible_domains = []
        for domain_name in accessible_domain_names:
            try:
                domain_enum = Domain(domain_name)
                config = DOMAIN_CONFIG.get(domain_enum, {})
                domain_info = DomainInfo(
                    name=domain_name,
                    display_name=config.get("display_name", domain_name.title()),
                    description=config.get("description", f"{domain_name} domain"),
                    icon=config.get("icon", "circle"),
                    category=config.get("category", "Other"),
                    permissions_required=config.get("permissions_required", []),
                    features=config.get("features", []),
                    status="active",
                )
                accessible_domains.append(domain_info)
            except ValueError:
                # Skip invalid domain names
                logger.warning(f"Invalid domain name: {domain_name}")
                continue
        return DomainAccessResponse(
            accessible_domains=accessible_domains,
            domain_groups=domain_groups,
            user_role=(
                user_role.value if isinstance(user_role, Role) else str(user_role)
            ),
            total_domains=len(accessible_domains),
        )
    except Exception as e:
        logger.error(f"❌ Failed to get accessible domains: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve accessible domains: {str(e)}",
        )
@router.get(
    "/{domain_name}",
    response_model=DomainInfo,
    summary="Get domain information",
    description="Get detailed information about a specific domain",
)
@require_auth
async def get_domain_info(
    domain_name: str, user_context: Dict[str, Any] = Depends(get_user_context)
) -> DomainInfo:
    """
    Get detailed information about a specific domain
    - **domain_name**: Name of the domain to retrieve
    """
    try:
        user_role = user_context.get("role", Role.GUEST)
        # Check if user has access to this domain
        if not RolePermissions.can_access(user_role, f"domains.{domain_name}"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to domain: {domain_name}",
            )
        # Get domain configuration
        try:
            domain_enum = Domain(domain_name)
            config = DOMAIN_CONFIG.get(domain_enum, {})
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Domain not found: {domain_name}",
            )
        return DomainInfo(
            name=domain_name,
            display_name=config.get("display_name", domain_name.title()),
            description=config.get("description", f"{domain_name} domain"),
            icon=config.get("icon", "circle"),
            category=config.get("category", "Other"),
            permissions_required=config.get("permissions_required", []),
            features=config.get("features", []),
            status="active",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get domain info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve domain information: {str(e)}",
        )
@router.get(
    "/{domain_name}/stats",
    response_model=DomainStatsResponse,
    summary="Get domain statistics",
    description="Get usage statistics for a specific domain",
)
@require_auth
@require_permission("system.monitor")
async def get_domain_stats(
    domain_name: str,
    days: int = Query(
        default=30, ge=1, le=365, description="Number of days for statistics"
    ),
) -> DomainStatsResponse:
    """
    Get usage statistics for a specific domain
    - **domain_name**: Name of the domain
    - **days**: Number of days to include in statistics
    Requires system monitoring permissions
    """
    try:
        # Validate domain exists
        try:
            Domain(domain_name)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Domain not found: {domain_name}",
            )
        # Placeholder implementation - in real system, query analytics database
        return DomainStatsResponse(
            domain_name=domain_name,
            active_users=42,  # Mock data
            total_queries=1337,
            avg_response_time=0.85,
            success_rate=94.5,
            last_activity=datetime.now(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get domain stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve domain statistics: {str(e)}",
        )
@router.post(
    "/{domain_name}/activate",
    summary="Activate domain",
    description="Activate a domain for the current user",
)
@require_auth
async def activate_domain(
    domain_name: str, user_context: Dict[str, Any] = Depends(get_user_context)
):
    """
    Activate a domain for the current user
    - **domain_name**: Name of the domain to activate
    """
    try:
        user_role = user_context.get("role", Role.GUEST)
        # Check if user has access to this domain
        if not RolePermissions.can_access(user_role, f"domains.{domain_name}"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to domain: {domain_name}",
            )
        # Validate domain exists
        try:
            Domain(domain_name)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Domain not found: {domain_name}",
            )
        # Placeholder implementation - in real system, update user preferences
        logger.info(
            f"🟢 Domain activated: {domain_name} for user {user_context.get('user_id')}"
        )
        return {
            "message": f"Domain {domain_name} activated successfully",
            "domain": domain_name,
            "status": "active",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to activate domain: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate domain: {str(e)}",
        )
@router.get(
    "/categories/list",
    summary="Get domain categories",
    description="Get list of all domain categories",
)
@require_auth
async def get_domain_categories() -> Dict[str, List[str]]:
    """Get list of all domain categories with their domains"""
    try:
        categories = {}
        for domain, config in DOMAIN_CONFIG.items():
            category = config.get("category", "Other")
            if category not in categories:
                categories[category] = []
            categories[category].append(domain.value)
        return categories
    except Exception as e:
        logger.error(f"❌ Failed to get domain categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve domain categories: {str(e)}",
        )
# Health check endpoint
@router.get(
    "/health",
    summary="Domains service health check",
    description="Check domains service health",
)
async def domains_health_check():
    """Health check for domains service"""
    try:
        total_domains = len(DOMAIN_CONFIG)
        categories = len(
            set(config.get("category", "Other") for config in DOMAIN_CONFIG.values())
        )
        return {
            "status": "healthy",
            "service": "domains",
            "version": "4.0.0",
            "metrics": {
                "total_domains": total_domains,
                "categories": categories,
                "active_domains": total_domains,  # All domains are active in this implementation
            },
        }
    except Exception as e:
        logger.error(f"❌ Domains health check failed: {e}")
        return {"status": "unhealthy", "service": "domains", "error": str(e)}
# Register router
from routers import register_router
register_router("domains", router)
