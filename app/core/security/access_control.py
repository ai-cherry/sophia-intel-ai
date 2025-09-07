"""
Access Control System for ESC Integration
Role-based access control for secrets and configuration management.
"""

import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

import jwt
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class AccessLevel(str, Enum):
    """Access levels for resources"""

    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class ResourceType(str, Enum):
    """Types of resources that can be accessed"""

    SECRET = "secret"
    CONFIG = "config"
    ENVIRONMENT = "environment"
    AUDIT_LOG = "audit_log"
    SYSTEM = "system"


class Permission(str, Enum):
    """Specific permissions"""

    SECRET_READ = "secret:read"
    SECRET_WRITE = "secret:write"
    SECRET_DELETE = "secret:delete"
    SECRET_ROTATE = "secret:rotate"
    CONFIG_READ = "config:read"
    CONFIG_WRITE = "config:write"
    CONFIG_REFRESH = "config:refresh"
    ENVIRONMENT_READ = "environment:read"
    ENVIRONMENT_WRITE = "environment:write"
    AUDIT_READ = "audit:read"
    AUDIT_WRITE = "audit:write"
    SYSTEM_ADMIN = "system:admin"


@dataclass
class Role:
    """Role definition with permissions"""

    name: str
    permissions: set[Permission]
    description: str = ""
    resource_patterns: list[str] = field(default_factory=list)  # Regex patterns for resource access
    environments: list[str] = field(default_factory=list)  # Allowed environments


@dataclass
class User:
    """User with roles and metadata"""

    user_id: str
    username: str
    roles: set[str]
    email: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_access: Optional[datetime] = None
    active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessRequest:
    """Access request context"""

    user_id: str
    resource_type: ResourceType
    resource_id: str
    permission: Permission
    environment: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AccessResult:
    """Access control result"""

    granted: bool
    reason: str
    user_id: str
    permission: Permission
    resource_id: str
    roles_evaluated: set[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)


class RoleManager:
    """Manages roles and permissions"""

    def __init__(self):
        self.roles: dict[str, Role] = {}
        self._initialize_default_roles()

    def _initialize_default_roles(self):
        """Initialize default roles for the system"""

        # Read-only role
        self.roles["reader"] = Role(
            name="reader",
            permissions={
                Permission.SECRET_READ,
                Permission.CONFIG_READ,
                Permission.ENVIRONMENT_READ,
                Permission.AUDIT_READ,
            },
            description="Read-only access to secrets and configuration",
            environments=["dev", "staging", "production"],
        )

        # Developer role
        self.roles["developer"] = Role(
            name="developer",
            permissions={
                Permission.SECRET_READ,
                Permission.SECRET_WRITE,
                Permission.CONFIG_READ,
                Permission.CONFIG_WRITE,
                Permission.CONFIG_REFRESH,
                Permission.ENVIRONMENT_READ,
            },
            description="Developer access for dev environment",
            environments=["dev"],
            resource_patterns=[r"dev\..*", r".*\.dev\..*"],
        )

        # Staging admin role
        self.roles["staging_admin"] = Role(
            name="staging_admin",
            permissions={
                Permission.SECRET_READ,
                Permission.SECRET_WRITE,
                Permission.SECRET_ROTATE,
                Permission.CONFIG_READ,
                Permission.CONFIG_WRITE,
                Permission.CONFIG_REFRESH,
                Permission.ENVIRONMENT_READ,
                Permission.ENVIRONMENT_WRITE,
                Permission.AUDIT_READ,
            },
            description="Admin access for staging environment",
            environments=["dev", "staging"],
            resource_patterns=[r"(dev|staging)\..*", r".*\.(dev|staging)\..*"],
        )

        # Production admin role
        self.roles["production_admin"] = Role(
            name="production_admin",
            permissions={
                Permission.SECRET_READ,
                Permission.SECRET_WRITE,
                Permission.SECRET_ROTATE,
                Permission.CONFIG_READ,
                Permission.CONFIG_WRITE,
                Permission.CONFIG_REFRESH,
                Permission.ENVIRONMENT_READ,
                Permission.ENVIRONMENT_WRITE,
                Permission.AUDIT_READ,
                Permission.AUDIT_WRITE,
            },
            description="Admin access for production environment",
            environments=["production"],
            resource_patterns=[r"production\..*", r".*\.production\..*"],
        )

        # System admin role
        self.roles["system_admin"] = Role(
            name="system_admin",
            permissions=set(Permission),  # All permissions
            description="Full system administrator access",
            environments=["dev", "staging", "production"],
            resource_patterns=[r".*"],  # All resources
        )

        # Service account role
        self.roles["service_account"] = Role(
            name="service_account",
            permissions={Permission.SECRET_READ, Permission.CONFIG_READ, Permission.CONFIG_REFRESH},
            description="Service account for application runtime",
            environments=["dev", "staging", "production"],
        )

    def add_role(self, role: Role):
        """Add a custom role"""
        self.roles[role.name] = role
        logger.info(f"Added role: {role.name}")

    def get_role(self, role_name: str) -> Optional[Role]:
        """Get role by name"""
        return self.roles.get(role_name)

    def get_user_permissions(self, user: User) -> set[Permission]:
        """Get all permissions for a user based on their roles"""
        permissions = set()
        for role_name in user.roles:
            role = self.roles.get(role_name)
            if role:
                permissions.update(role.permissions)
        return permissions

    def get_user_environments(self, user: User) -> set[str]:
        """Get all environments a user has access to"""
        environments = set()
        for role_name in user.roles:
            role = self.roles.get(role_name)
            if role:
                environments.update(role.environments)
        return environments


class AccessTokenManager:
    """Manages access tokens for API authentication"""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.token_expiry_hours = 24

    def generate_token(self, user: User, expires_in_hours: Optional[int] = None) -> str:
        """Generate JWT token for user"""
        expires_in = expires_in_hours or self.token_expiry_hours
        expiry = datetime.utcnow() + timedelta(hours=expires_in)

        payload = {
            "user_id": user.user_id,
            "username": user.username,
            "roles": list(user.roles),
            "exp": expiry,
            "iat": datetime.utcnow(),
            "iss": "sophia-esc-access-control",
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def validate_token(self, token: str) -> Optional[dict[str, Any]]:
        """Validate JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    def refresh_token(self, token: str) -> Optional[str]:
        """Refresh an existing token"""
        payload = self.validate_token(token)
        if payload:
            # Create new token with same user info but new expiry
            user = User(
                user_id=payload["user_id"],
                username=payload["username"],
                roles=set(payload["roles"]),
            )
            return self.generate_token(user)
        return None


class AccessControlManager:
    """Main access control manager"""

    def __init__(self, secret_key: Optional[str] = None):
        self.role_manager = RoleManager()
        self.token_manager = AccessTokenManager(secret_key or Fernet.generate_key().decode())

        # User registry
        self.users: dict[str, User] = {}

        # Access audit trail
        self.access_log: list[AccessResult] = []
        self.max_log_entries = 10000

        # Rate limiting
        self.rate_limits: dict[str, list[float]] = {}
        self.max_requests_per_minute = 60

        # Session management
        self.active_sessions: dict[str, dict[str, Any]] = {}

        logger.info("Access Control Manager initialized")

    def add_user(self, user: User):
        """Add user to the system"""
        self.users[user.user_id] = user
        logger.info(f"Added user: {user.username} ({user.user_id})")

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None

    async def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return token"""
        # This is a simplified implementation
        # In production, you would hash passwords and verify against a database
        user = self.get_user_by_username(username)
        if user and user.active:
            # Generate token
            token = self.token_manager.generate_token(user)

            # Create session
            session_id = hashlib.sha256(f"{user.user_id}_{time.time()}".encode()).hexdigest()
            self.active_sessions[session_id] = {
                "user_id": user.user_id,
                "token": token,
                "created_at": datetime.utcnow(),
                "last_access": datetime.utcnow(),
            }

            user.last_access = datetime.utcnow()
            logger.info(f"User authenticated: {username}")
            return token

        logger.warning(f"Authentication failed for user: {username}")
        return None

    def authenticate_token(self, token: str) -> Optional[User]:
        """Authenticate user by token"""
        payload = self.token_manager.validate_token(token)
        if payload:
            user = self.get_user(payload["user_id"])
            if user and user.active:
                user.last_access = datetime.utcnow()
                return user
        return None

    def _check_rate_limit(self, user_id: str) -> bool:
        """Check if user is within rate limits"""
        now = time.time()
        minute_ago = now - 60

        # Clean old entries
        if user_id in self.rate_limits:
            self.rate_limits[user_id] = [
                timestamp for timestamp in self.rate_limits[user_id] if timestamp > minute_ago
            ]
        else:
            self.rate_limits[user_id] = []

        # Check current count
        return len(self.rate_limits[user_id]) < self.max_requests_per_minute

    def _record_request(self, user_id: str):
        """Record API request for rate limiting"""
        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = []
        self.rate_limits[user_id].append(time.time())

    def _matches_resource_pattern(self, resource_id: str, patterns: list[str]) -> bool:
        """Check if resource ID matches any of the patterns"""
        import re

        return any(re.match(pattern, resource_id) for pattern in patterns)

    async def check_access(self, request: AccessRequest) -> AccessResult:
        """Check if user has access to perform the requested action"""

        # Get user
        user = self.get_user(request.user_id)
        if not user:
            result = AccessResult(
                granted=False,
                reason="User not found",
                user_id=request.user_id,
                permission=request.permission,
                resource_id=request.resource_id,
                roles_evaluated=set(),
            )
            self._log_access(result)
            return result

        if not user.active:
            result = AccessResult(
                granted=False,
                reason="User inactive",
                user_id=request.user_id,
                permission=request.permission,
                resource_id=request.resource_id,
                roles_evaluated=set(),
            )
            self._log_access(result)
            return result

        # Check rate limit
        if not self._check_rate_limit(user.user_id):
            result = AccessResult(
                granted=False,
                reason="Rate limit exceeded",
                user_id=request.user_id,
                permission=request.permission,
                resource_id=request.resource_id,
                roles_evaluated=user.roles,
            )
            self._log_access(result)
            return result

        # Record request
        self._record_request(user.user_id)

        # Check permissions through roles
        has_permission = False
        allowed_environments = set()
        evaluated_roles = set()

        for role_name in user.roles:
            role = self.role_manager.get_role(role_name)
            if role:
                evaluated_roles.add(role_name)

                # Check permission
                if request.permission in role.permissions:
                    # Check environment access
                    if request.environment in role.environments:
                        # Check resource pattern match
                        if not role.resource_patterns or self._matches_resource_pattern(
                            request.resource_id, role.resource_patterns
                        ):
                            has_permission = True
                            break

                allowed_environments.update(role.environments)

        # Determine result
        if has_permission:
            result = AccessResult(
                granted=True,
                reason="Access granted",
                user_id=request.user_id,
                permission=request.permission,
                resource_id=request.resource_id,
                roles_evaluated=evaluated_roles,
            )
        else:
            # Determine specific reason for denial
            user_permissions = self.role_manager.get_user_permissions(user)

            if request.permission not in user_permissions:
                reason = f"Missing permission: {request.permission.value}"
            elif request.environment not in allowed_environments:
                reason = f"No access to environment: {request.environment}"
            else:
                reason = f"No access to resource: {request.resource_id}"

            result = AccessResult(
                granted=False,
                reason=reason,
                user_id=request.user_id,
                permission=request.permission,
                resource_id=request.resource_id,
                roles_evaluated=evaluated_roles,
            )

        self._log_access(result)
        return result

    def _log_access(self, result: AccessResult):
        """Log access attempt"""
        self.access_log.append(result)

        # Trim log if it gets too large
        if len(self.access_log) > self.max_log_entries:
            self.access_log = self.access_log[-self.max_log_entries :]

        log_level = logging.INFO if result.granted else logging.WARNING
        logger.log(
            log_level,
            f"Access {'granted' if result.granted else 'denied'}: "
            f"user={result.user_id}, permission={result.permission.value}, "
            f"resource={result.resource_id}, reason={result.reason}",
        )

    def get_user_permissions_summary(self, user_id: str) -> dict[str, Any]:
        """Get summary of user permissions"""
        user = self.get_user(user_id)
        if not user:
            return {"error": "User not found"}

        permissions = self.role_manager.get_user_permissions(user)
        environments = self.role_manager.get_user_environments(user)

        return {
            "user_id": user.user_id,
            "username": user.username,
            "active": user.active,
            "roles": list(user.roles),
            "permissions": [p.value for p in permissions],
            "environments": list(environments),
            "last_access": user.last_access.isoformat() if user.last_access else None,
        }

    def get_access_log(
        self, user_id: Optional[str] = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get access log entries"""
        entries = self.access_log

        if user_id:
            entries = [entry for entry in entries if entry.user_id == user_id]

        entries = entries[-limit:] if limit else entries

        return [
            {
                "granted": entry.granted,
                "reason": entry.reason,
                "user_id": entry.user_id,
                "permission": entry.permission.value,
                "resource_id": entry.resource_id,
                "roles_evaluated": list(entry.roles_evaluated),
                "timestamp": entry.timestamp.isoformat(),
            }
            for entry in entries
        ]

    def get_system_statistics(self) -> dict[str, Any]:
        """Get system access control statistics"""
        total_requests = len(self.access_log)
        granted_requests = len([entry for entry in self.access_log if entry.granted])

        # Permission usage statistics
        permission_stats = {}
        for entry in self.access_log:
            perm = entry.permission.value
            if perm not in permission_stats:
                permission_stats[perm] = {"total": 0, "granted": 0}
            permission_stats[perm]["total"] += 1
            if entry.granted:
                permission_stats[perm]["granted"] += 1

        return {
            "total_users": len(self.users),
            "active_users": len([u for u in self.users.values() if u.active]),
            "total_roles": len(self.role_manager.roles),
            "active_sessions": len(self.active_sessions),
            "total_access_requests": total_requests,
            "granted_requests": granted_requests,
            "denial_rate": (
                (total_requests - granted_requests) / total_requests if total_requests > 0 else 0
            ),
            "permission_usage": permission_stats,
            "rate_limit_users": len(self.rate_limits),
        }


# Default instance for application use
_default_access_control: Optional[AccessControlManager] = None


def get_access_control() -> AccessControlManager:
    """Get default access control manager"""
    global _default_access_control
    if _default_access_control is None:
        _default_access_control = AccessControlManager()
    return _default_access_control


def initialize_default_users():
    """Initialize default users for testing"""
    access_control = get_access_control()

    # System admin user
    admin_user = User(
        user_id="admin", username="admin", roles={"system_admin"}, email="admin@sophia-intel-ai.com"
    )
    access_control.add_user(admin_user)

    # Developer user
    dev_user = User(
        user_id="dev", username="developer", roles={"developer"}, email="dev@sophia-intel-ai.com"
    )
    access_control.add_user(dev_user)

    # Service account
    service_user = User(
        user_id="service",
        username="service_account",
        roles={"service_account"},
        email="service@sophia-intel-ai.com",
    )
    access_control.add_user(service_user)

    logger.info("Default users initialized")


# Decorator for access control
def require_permission(permission: Permission, resource_type: ResourceType = ResourceType.SECRET):
    """Decorator to require specific permission for API endpoints"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would be implemented to extract user from request context
            # and check permissions before executing the function
            # For now, it's a placeholder
            return await func(*args, **kwargs)

        return wrapper

    return decorator
