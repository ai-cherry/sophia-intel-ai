#!/usr/bin/env python3
"""
Role-Based Access Control (RBAC) Middleware for Sophia Intel AI
Provides fine-grained access control based on user roles and permissions
"""

import logging
from functools import wraps
from typing import Callable, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.models.user_configuration import (
    AccessLevel,
    FeatureAccess,
    UserConfiguration,
)

logger = logging.getLogger(__name__)
security = HTTPBearer()

# CEO email for special permissions
CEO_EMAIL = "lynn@sophia-intel.ai"

# In-memory cache for user sessions (replace with Redis in production)
USER_SESSION_CACHE: dict[str, UserConfiguration] = {}


class RBACMiddleware(BaseHTTPMiddleware):
    """Middleware for role-based access control"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and check permissions"""
        # Skip auth for public endpoints
        public_paths = [
            "/health",
            "/docs",
            "/openapi.json",
            "/static",
            "/auth/login",
            "/auth/register",
        ]
        
        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)
        
        # Extract and validate token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                content="Missing or invalid authorization header",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        
        token = auth_header.replace("Bearer ", "")
        
        try:
            # Validate token and get user (simplified for demo)
            user = await self.get_user_from_token(token)
            if not user:
                return Response(
                    content="Invalid authentication token",
                    status_code=status.HTTP_401_UNAUTHORIZED,
                )
            
            # Check if user is active
            if not user.is_active:
                return Response(
                    content="User account is deactivated",
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            
            # Store user in request state for downstream use
            request.state.user = user
            
            # Check route-specific permissions
            if not await self.check_route_permission(request, user):
                return Response(
                    content="Insufficient permissions for this resource",
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            
            # Log access
            logger.info(
                f"User {user.email} accessed {request.method} {request.url.path}"
            )
            
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"RBAC middleware error: {e}")
            return Response(
                content="Authentication error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    async def get_user_from_token(self, token: str) -> Optional[UserConfiguration]:
        """Get user from authentication token"""
        # This is a simplified implementation
        # In production, decode JWT and fetch user from database
        
        # For demo, check cache
        if token in USER_SESSION_CACHE:
            return USER_SESSION_CACHE[token]
        
        # TODO: Implement actual JWT decoding and database lookup
        return None
    
    async def check_route_permission(
        self, request: Request, user: UserConfiguration
    ) -> bool:
        """Check if user has permission for the requested route"""
        path = request.url.path
        method = request.method
        
        # Define route permission mappings
        route_permissions = {
            # Brain endpoints
            "/api/brain": {
                "GET": FeatureAccess.BRAIN_VIEW,
                "POST": FeatureAccess.BRAIN_EDIT,
                "PUT": FeatureAccess.BRAIN_EDIT,
                "DELETE": FeatureAccess.BRAIN_EDIT,
            },
            "/api/brain-controls": {
                "GET": FeatureAccess.BRAIN_VIEW,
                "POST": FeatureAccess.BRAIN_EDIT,
                "PUT": FeatureAccess.BRAIN_EDIT,
                "DELETE": FeatureAccess.BRAIN_EDIT,
            },
            # Agent endpoints
            "/api/agents": {
                "GET": FeatureAccess.AGENTS_VIEW,
                "POST": FeatureAccess.AGENTS_CREATE,
                "PUT": FeatureAccess.AGENTS_EDIT,
                "DELETE": FeatureAccess.AGENTS_EDIT,
            },
            # Integration endpoints
            "/api/integrations": {
                "GET": FeatureAccess.INTEGRATIONS_VIEW,
                "POST": FeatureAccess.INTEGRATIONS_MANAGE,
                "PUT": FeatureAccess.INTEGRATIONS_MANAGE,
                "DELETE": FeatureAccess.INTEGRATIONS_MANAGE,
            },
            # Analytics endpoints
            "/api/analytics": {
                "GET": FeatureAccess.ANALYTICS_VIEW,
                "POST": FeatureAccess.ANALYTICS_EXPORT,
            },
            # Workflow endpoints
            "/api/workflows": {
                "GET": FeatureAccess.WORKFLOWS_VIEW,
                "POST": FeatureAccess.WORKFLOWS_CREATE,
                "PUT": FeatureAccess.WORKFLOWS_CREATE,
                "DELETE": FeatureAccess.WORKFLOWS_CREATE,
            },
            "/api/workflows/execute": {
                "POST": FeatureAccess.WORKFLOWS_EXECUTE,
            },
            # User management endpoints
            "/api/users": {
                "GET": FeatureAccess.USERS_VIEW,
                "POST": FeatureAccess.USERS_MANAGE,
                "PUT": FeatureAccess.USERS_MANAGE,
                "DELETE": FeatureAccess.USERS_MANAGE,
            },
            # Settings endpoints
            "/api/settings": {
                "GET": FeatureAccess.SETTINGS_VIEW,
                "POST": FeatureAccess.SETTINGS_MANAGE,
                "PUT": FeatureAccess.SETTINGS_MANAGE,
            },
            # Billing endpoints
            "/api/billing": {
                "GET": FeatureAccess.BILLING_VIEW,
                "POST": FeatureAccess.BILLING_MANAGE,
            },
        }
        
        # Check for exact match first
        for route_pattern, permissions in route_permissions.items():
            if path.startswith(route_pattern):
                required_permission = permissions.get(method)
                if required_permission:
                    return user.has_feature(required_permission)
        
        # Default: allow if no specific permission required
        return True


def require_access_level(min_level: AccessLevel):
    """Decorator to require minimum access level"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user = getattr(request.state, "user", None)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )
            
            # Check access level hierarchy
            level_hierarchy = {
                AccessLevel.VIEWER: 0,
                AccessLevel.ANALYST: 1,
                AccessLevel.DEVELOPER: 2,
                AccessLevel.ADMIN: 3,
                AccessLevel.OWNER: 4,
            }
            
            user_level = level_hierarchy.get(user.access_level, 0)
            required_level = level_hierarchy.get(min_level, 0)
            
            if user_level < required_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires {min_level.value} access or higher",
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_feature(feature: FeatureAccess):
    """Decorator to require specific feature access"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user = getattr(request.state, "user", None)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )
            
            if not user.has_feature(feature):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires {feature.value} permission",
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def ceo_only(func: Callable) -> Callable:
    """Decorator to restrict access to CEO only"""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )
        
        if user.email != CEO_EMAIL and user.access_level != AccessLevel.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This action is restricted to CEO only",
            )
        
        return await func(request, *args, **kwargs)
    return wrapper


class PermissionChecker:
    """Utility class for checking permissions"""
    
    @staticmethod
    def can_modify_schema(user: UserConfiguration) -> bool:
        """Check if user can modify database schemas"""
        return user.email == CEO_EMAIL or user.access_level == AccessLevel.OWNER
    
    @staticmethod
    def can_manage_users(user: UserConfiguration) -> bool:
        """Check if user can manage other users"""
        return user.has_feature(FeatureAccess.USERS_MANAGE)
    
    @staticmethod
    def can_execute_workflows(user: UserConfiguration) -> bool:
        """Check if user can execute workflows"""
        return user.has_feature(FeatureAccess.WORKFLOWS_EXECUTE)
    
    @staticmethod
    def can_access_billing(user: UserConfiguration) -> bool:
        """Check if user can access billing information"""
        return user.has_feature(FeatureAccess.BILLING_VIEW)
    
    @staticmethod
    def can_export_data(user: UserConfiguration) -> bool:
        """Check if user can export data"""
        return (
            user.has_feature(FeatureAccess.ANALYTICS_EXPORT)
            and user.data_access_policy.export_allowed
        )
    
    @staticmethod
    def get_data_access_limits(user: UserConfiguration) -> dict:
        """Get user's data access limitations"""
        policy = user.data_access_policy
        return {
            "allow_pii": policy.allow_pii_access,
            "allowed_sources": policy.allowed_data_sources,
            "restricted_tables": policy.restricted_tables,
            "max_export_rows": policy.max_export_rows,
            "retention_days": policy.data_retention_days,
        }


def get_current_user(request: Request) -> UserConfiguration:
    """Get current user from request"""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user


def check_data_source_access(
    user: UserConfiguration, data_source: str
) -> bool:
    """Check if user can access a specific data source"""
    return user.can_access_data_source(data_source)


# Example usage in routes:
"""
@router.post("/api/brain/schema")
@ceo_only
async def modify_schema(request: Request, schema: dict):
    # Only CEO can execute this
    pass

@router.get("/api/users")
@require_feature(FeatureAccess.USERS_VIEW)
async def list_users(request: Request):
    # Requires users_view permission
    pass

@router.post("/api/workflows/execute")
@require_access_level(AccessLevel.ANALYST)
async def execute_workflow(request: Request, workflow_id: str):
    # Requires at least analyst level
    pass
"""