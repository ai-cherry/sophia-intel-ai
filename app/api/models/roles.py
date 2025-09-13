"""
Sophia AI Platform v4.0 - Role-Based Access Control System
Extensible role system with granular permissions and wildcard support
"""
import logging
from enum import Enum
from typing import Dict, List, Set
from pydantic import BaseModel
logger = logging.getLogger(__name__)
class Role(str, Enum):
    """User roles in the Sophia AI platform"""
    CEO = "ceo"
    MANAGER = "manager"
    ANALYST = "analyst"
    TRAINER = "trainer"
    SUPPORT = "support"
    DEVELOPER = "developer"
    GUEST = "guest"
class Domain(str, Enum):
    """Available domains in the platform"""
    CHAT = "chat"
    SALES = "sales"
    MARKETING = "marketing"
    DEVOPS = "devops"
    TRAINING = "training"
    ADMIN = "admin"
    BI = "bi"
    RESEARCH = "research"
    SUPPORT = "support"
    FINANCE = "finance"
    HR = "hr"
    CRM = "crm"
    MONITORING = "monitoring"
    GITHUB = "github"
class Permission(BaseModel):
    """Permission model with domain and action"""
    domain: str
    action: str
    def __str__(self) -> str:
        return f"{self.domain}.{self.action}"
class RolePermissions:
    """Centralized role permission matrix with intelligent access control"""
    # Permission matrix - role to set of permissions
    PERMISSIONS: Dict[Role, Set[str]] = {
        Role.CEO: {
            "*",  # CEO has all permissions
        },
        Role.MANAGER: {
            "domains.*",  # All domain access
            "chat.*",  # All chat permissions
            "training.view",
            "training.basic",
            "users.view",
            "users.modify",
            "analytics.*",
            "reports.*",
        },
        Role.ANALYST: {
            "domains.sales",
            "domains.marketing",
            "domains.bi",
            "domains.finance",
            "chat.view",
            "chat.basic",
            "training.view",
            "analytics.view",
            "analytics.basic",
            "reports.view",
            "reports.generate",
        },
        Role.TRAINER: {
            "domains.training",
            "domains.support",
            "chat.view",
            "chat.basic",
            "chat.train",
            "training.*",  # All training permissions
            "analytics.view",
        },
        Role.SUPPORT: {
            "domains.support",
            "domains.crm",
            "chat.view",
            "chat.basic",
            "chat.support",
            "training.view",
            "users.view",
        },
        Role.DEVELOPER: {
            "*",  # Developers have all permissions for development
        },
        Role.GUEST: {"domains.sales", "chat.view", "training.view"},  # Limited access
    }
    # Domain groupings for UI organization
    DOMAIN_GROUPS = {
        "Business Intelligence": ["sales", "marketing", "finance", "bi"],
        "Operations": ["devops", "monitoring", "github", "admin"],
        "Customer Success": ["support", "crm", "training"],
        "Human Resources": ["hr", "training"],
        "Research & Development": ["research", "training", "devops"],
    }
    @classmethod
    def can_access(cls, role: Role, permission: str) -> bool:
        """
        Check if role has permission (supports wildcards)
        Args:
            role: User role
            permission: Permission string (e.g., "domains.sales" or "training.basic")
        Returns:
            bool: True if role has permission
        """
        if not isinstance(role, Role):
            logger.warning(f"Invalid role type: {type(role)}")
            return False
        role_perms = cls.PERMISSIONS.get(role, set())
        # Check exact match
        if permission in role_perms:
            return True
        # Check wildcard permissions
        permission_parts = permission.split(".")
        for perm in role_perms:
            if perm.endswith("*"):
                perm_prefix = perm[:-1]
                if permission.startswith(perm_prefix):
                    return True
        return False
    @classmethod
    def get_accessible_domains(cls, role: Role) -> List[str]:
        """
        Get list of domains accessible to a role
        Args:
            role: User role
        Returns:
            List[str]: List of accessible domain names
        """
        if not isinstance(role, Role):
            return []
        role_perms = cls.PERMISSIONS.get(role, set())
        domains = set()
        for perm in role_perms:
            if perm.startswith("domains."):
                if perm.endswith("*"):
                    # Add all domains for wildcard
                    domains.update([d.value for d in Domain])
                else:
                    # Add specific domain
                    domain = perm.split(".", 1)[1]
                    domains.add(domain)
        return sorted(list(domains))
    @classmethod
    def get_domain_groups_for_role(cls, role: Role) -> Dict[str, List[str]]:
        """
        Get domain groups filtered by role permissions
        Args:
            role: User role
        Returns:
            Dict[str, List[str]]: Filtered domain groups
        """
        accessible_domains = set(cls.get_accessible_domains(role))
        filtered_groups = {}
        for group_name, domains in cls.DOMAIN_GROUPS.items():
            filtered_domains = [d for d in domains if d in accessible_domains]
            if filtered_domains:
                filtered_groups[group_name] = filtered_domains
        return filtered_groups
    @classmethod
    def validate_role_permissions(
        cls, role: Role, required_permissions: List[str]
    ) -> Dict[str, bool]:
        """
        Validate multiple permissions for a role
        Args:
            role: User role
            required_permissions: List of permission strings
        Returns:
            Dict[str, bool]: Permission validation results
        """
        results = {}
        for perm in required_permissions:
            results[perm] = cls.can_access(role, perm)
        return results
    @classmethod
    def get_role_capabilities(cls, role: Role) -> Dict[str, any]:
        """
        Get comprehensive role capabilities summary
        Args:
            role: User role
        Returns:
            Dict: Role capabilities including domains, permissions, and groups
        """
        return {
            "role": role.value,
            "permissions": list(cls.PERMISSIONS.get(role, set())),
            "accessible_domains": cls.get_accessible_domains(role),
            "domain_groups": cls.get_domain_groups_for_role(role),
            "is_admin": role in [Role.CEO, Role.DEVELOPER],
            "can_train": cls.can_access(role, "training.modify"),
            "can_manage_users": cls.can_access(role, "users.modify"),
        }
# Authentication decorators for FastAPI
from functools import wraps
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
security = HTTPBearer()
def require_auth(func):
    """Decorator to require authentication"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Placeholder for actual authentication logic
        # In real implementation, validate JWT token here
        return await func(*args, **kwargs)
    return wrapper
def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Placeholder for permission check
            # In real implementation, extract user role from token
            # and check permission using RolePermissions.can_access()
            return await func(*args, **kwargs)
        return wrapper
    return decorator
def require_role(required_role: Role):
    """Decorator to require specific role"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Placeholder for role check
            # In real implementation, extract user role from token
            return await func(*args, **kwargs)
        return wrapper
    return decorator
# FastAPI dependency for permission verification
async def verify_permissions(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    FastAPI dependency to verify user permissions
    Args:
        credentials: HTTP Bearer token credentials
    Returns:
        dict: User permissions dictionary
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # In production, decode JWT token and extract user role
        # For now, return mock permissions for testing
        # Mock user with developer role for testing
        actual_role = Role.DEVELOPER
        # Get all permissions for the role
        role_permissions = RolePermissions.PERMISSIONS.get(actual_role, set())
        # Convert to permission dictionary
        permissions = {}
        for perm in role_permissions:
            if perm == "*":
                # Full access
                permissions = {
                    "chat": True,
                    "domains": True,
                    "admin": True,
                    "analytics": True,
                    "training": True,
                    "users": True,
                    "reports": True,
                }
                break
            elif "." in perm:
                domain, action = perm.split(".", 1)
                if action == "*":
                    permissions[domain] = True
                else:
                    permissions[f"{domain}_{action}"] = True
            else:
                permissions[perm] = True
        return permissions
    except Exception as e:
        logger.error(f"Permission verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
# Example usage and testing
if __name__ == "__main__":
    # Test role permissions
    print("🧪 Testing Role Permissions System")
    # Test CEO permissions
    ceo_can_admin = RolePermissions.can_access(Role.CEO, "admin.delete")
    print(f"CEO can admin.delete: {ceo_can_admin}")
    # Test wildcard permissions
    ceo_can_domains = RolePermissions.can_access(Role.CEO, "domains.sales")
    print(f"CEO can access domains.sales: {ceo_can_domains}")
    # Test analyst permissions
    analyst_domains = RolePermissions.get_accessible_domains(Role.ANALYST)
    print(f"Analyst accessible domains: {analyst_domains}")
    # Test domain groups
    manager_groups = RolePermissions.get_domain_groups_for_role(Role.MANAGER)
    print(f"Manager domain groups: {manager_groups}")
    # Test role capabilities
    dev_capabilities = RolePermissions.get_role_capabilities(Role.DEVELOPER)
    print(f"Developer capabilities: {dev_capabilities}")
