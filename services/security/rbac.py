"""
SOPHIA Intel - Role-Based Access Control (RBAC) and Security
Stage C: Scale Safely - Token-scoped repo access, tenant filtering, audit logs
"""
import time
import jwt
import hashlib
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)

class Permission(Enum):
    # API Permissions
    API_READ = "api:read"
    API_WRITE = "api:write"
    API_ADMIN = "api:admin"
    
    # Memory Permissions
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    MEMORY_DELETE = "memory:delete"
    
    # Repository Permissions
    REPO_READ = "repo:read"
    REPO_WRITE = "repo:write"
    REPO_ADMIN = "repo:admin"
    
    # Voice Permissions
    VOICE_STT = "voice:stt"
    VOICE_TTS = "voice:tts"
    
    # Orchestration Permissions
    ORCHESTRATION_CHAT = "orchestration:chat"
    ORCHESTRATION_CODE = "orchestration:code"
    ORCHESTRATION_RESEARCH = "orchestration:research"
    
    # Admin Permissions
    TENANT_ADMIN = "tenant:admin"
    USER_ADMIN = "user:admin"
    AUDIT_READ = "audit:read"

class Role(Enum):
    GUEST = "guest"
    USER = "user"
    DEVELOPER = "developer"
    ADMIN = "admin"
    SYSTEM = "system"

@dataclass
class User:
    id: str
    tenant_id: str
    email: str
    role: Role
    permissions: Set[Permission]
    created_at: datetime
    last_active: datetime
    metadata: Dict[str, Any]

@dataclass
class AccessToken:
    user_id: str
    tenant_id: str
    permissions: Set[Permission]
    expires_at: datetime
    scopes: List[str]  # Repository scopes, API scopes, etc.
    metadata: Dict[str, Any]

@dataclass
class AuditEvent:
    id: str
    user_id: str
    tenant_id: str
    action: str
    resource: str
    result: str  # success, failure, denied
    timestamp: datetime
    ip_address: str
    user_agent: str
    metadata: Dict[str, Any]

class RBACManager:
    """
    SOPHIA Intel RBAC Manager
    - Token-scoped repository access
    - Tenant isolation enforcement
    - Comprehensive audit logging
    - Permission-based access control
    """
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.users: Dict[str, User] = {}
        self.audit_log: List[AuditEvent] = []
        self.role_permissions = self._initialize_role_permissions()
        
    def _initialize_role_permissions(self) -> Dict[Role, Set[Permission]]:
        """Initialize default permissions for each role"""
        return {
            Role.GUEST: {
                Permission.API_READ,
            },
            
            Role.USER: {
                Permission.API_READ,
                Permission.API_WRITE,
                Permission.MEMORY_READ,
                Permission.MEMORY_WRITE,
                Permission.VOICE_STT,
                Permission.VOICE_TTS,
                Permission.ORCHESTRATION_CHAT,
            },
            
            Role.DEVELOPER: {
                Permission.API_READ,
                Permission.API_WRITE,
                Permission.MEMORY_READ,
                Permission.MEMORY_WRITE,
                Permission.REPO_READ,
                Permission.REPO_WRITE,
                Permission.VOICE_STT,
                Permission.VOICE_TTS,
                Permission.ORCHESTRATION_CHAT,
                Permission.ORCHESTRATION_CODE,
                Permission.ORCHESTRATION_RESEARCH,
            },
            
            Role.ADMIN: {
                # All permissions
                *list(Permission)
            },
            
            Role.SYSTEM: {
                # All permissions for system operations
                *list(Permission)
            }
        }
    
    def create_user(self, user_id: str, tenant_id: str, email: str, role: Role) -> User:
        """Create a new user"""
        user = User(
            id=user_id,
            tenant_id=tenant_id,
            email=email,
            role=role,
            permissions=self.role_permissions.get(role, set()),
            created_at=datetime.utcnow(),
            last_active=datetime.utcnow(),
            metadata={}
        )
        
        self.users[user_id] = user
        
        # Audit log
        self._log_audit_event(
            user_id="system",
            tenant_id=tenant_id,
            action="user_created",
            resource=f"user:{user_id}",
            result="success",
            metadata={"role": role.value, "email": email}
        )
        
        return user
    
    def generate_access_token(
        self, 
        user_id: str, 
        scopes: List[str] = None,
        expires_in_hours: int = 24
    ) -> str:
        """Generate JWT access token with scoped permissions"""
        user = self.users.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        # Create token payload
        payload = {
            "user_id": user_id,
            "tenant_id": user.tenant_id,
            "role": user.role.value,
            "permissions": [p.value for p in user.permissions],
            "scopes": scopes or [],
            "exp": expires_at.timestamp(),
            "iat": datetime.utcnow().timestamp(),
            "iss": "sophia-intel"
        }
        
        # Generate JWT token
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        
        # Audit log
        self._log_audit_event(
            user_id=user_id,
            tenant_id=user.tenant_id,
            action="token_generated",
            resource="access_token",
            result="success",
            metadata={"scopes": scopes, "expires_at": expires_at.isoformat()}
        )
        
        return token
    
    def validate_token(self, token: str) -> Optional[AccessToken]:
        """Validate and decode access token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            
            # Check expiration
            if datetime.utcnow().timestamp() > payload["exp"]:
                return None
            
            # Convert permissions back to enum
            permissions = {Permission(p) for p in payload["permissions"]}
            
            access_token = AccessToken(
                user_id=payload["user_id"],
                tenant_id=payload["tenant_id"],
                permissions=permissions,
                expires_at=datetime.fromtimestamp(payload["exp"]),
                scopes=payload.get("scopes", []),
                metadata={"role": payload.get("role")}
            )
            
            return access_token
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def check_permission(
        self, 
        token: AccessToken, 
        permission: Permission,
        resource: str = None
    ) -> bool:
        """Check if token has required permission for resource"""
        # Basic permission check
        if permission not in token.permissions:
            return False
        
        # Scope-based checks for repository access
        if permission in [Permission.REPO_READ, Permission.REPO_WRITE, Permission.REPO_ADMIN]:
            if resource and not self._check_repo_scope(token, resource):
                return False
        
        return True
    
    def _check_repo_scope(self, token: AccessToken, repo_resource: str) -> bool:
        """Check if token has scope for repository resource"""
        # Extract repository from resource (e.g., "repo:sophia-intel/main")
        if ":" in repo_resource:
            repo_name = repo_resource.split(":", 1)[1]
        else:
            repo_name = repo_resource
        
        # Check if token has scope for this repository
        repo_scopes = [s for s in token.scopes if s.startswith("repo:")]
        
        if not repo_scopes:
            return False  # No repository scopes
        
        # Check for wildcard or specific repo access
        for scope in repo_scopes:
            scope_repo = scope.replace("repo:", "")
            if scope_repo == "*" or scope_repo == repo_name:
                return True
        
        return False
    
    def enforce_tenant_isolation(self, token: AccessToken, resource_tenant_id: str) -> bool:
        """Enforce tenant isolation - users can only access their tenant's resources"""
        return token.tenant_id == resource_tenant_id
    
    def _log_audit_event(
        self,
        user_id: str,
        tenant_id: str,
        action: str,
        resource: str,
        result: str,
        ip_address: str = "unknown",
        user_agent: str = "unknown",
        metadata: Dict[str, Any] = None
    ):
        """Log audit event"""
        event = AuditEvent(
            id=hashlib.md5(f"{user_id}:{action}:{resource}:{time.time()}".encode()).hexdigest(),
            user_id=user_id,
            tenant_id=tenant_id,
            action=action,
            resource=resource,
            result=result,
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )
        
        self.audit_log.append(event)
        
        # Keep only last 10000 events to prevent memory issues
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-10000:]
        
        # Log to structured logger
        logger.info(
            f"Audit: {action}",
            extra={
                "audit_id": event.id,
                "user_id": user_id,
                "tenant_id": tenant_id,
                "action": action,
                "resource": resource,
                "result": result,
                "metadata": metadata
            }
        )
    
    def get_audit_log(
        self, 
        tenant_id: str, 
        user_id: str = None,
        action: str = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Get audit log with filtering"""
        events = [e for e in self.audit_log if e.tenant_id == tenant_id]
        
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        
        if action:
            events = [e for e in events if e.action == action]
        
        # Sort by timestamp (newest first)
        events.sort(key=lambda x: x.timestamp, reverse=True)
        
        return events[:limit]
    
    def update_user_activity(self, user_id: str):
        """Update user's last active timestamp"""
        if user_id in self.users:
            self.users[user_id].last_active = datetime.utcnow()

# Decorators for Flask routes
def require_permission(permission: Permission, resource_param: str = None):
    """Decorator to require specific permission for route"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            from flask import request, g, jsonify
            
            # Get token from request
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"error": "Missing or invalid authorization header"}), 401
            
            token_str = auth_header.replace('Bearer ', '')
            token = rbac_manager.validate_token(token_str)
            
            if not token:
                return jsonify({"error": "Invalid or expired token"}), 401
            
            # Check permission
            resource = None
            if resource_param:
                resource = kwargs.get(resource_param) or request.json.get(resource_param)
            
            if not rbac_manager.check_permission(token, permission, resource):
                rbac_manager._log_audit_event(
                    user_id=token.user_id,
                    tenant_id=token.tenant_id,
                    action=f"access_denied:{permission.value}",
                    resource=resource or "unknown",
                    result="denied",
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', 'unknown')
                )
                return jsonify({"error": "Insufficient permissions"}), 403
            
            # Store token in request context
            g.access_token = token
            
            # Log successful access
            rbac_manager._log_audit_event(
                user_id=token.user_id,
                tenant_id=token.tenant_id,
                action=f"access_granted:{permission.value}",
                resource=resource or request.path,
                result="success",
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', 'unknown')
            )
            
            # Update user activity
            rbac_manager.update_user_activity(token.user_id)
            
            return func(*args, **kwargs)
        
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

def require_tenant_isolation(tenant_param: str = "tenant_id"):
    """Decorator to enforce tenant isolation"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            from flask import request, g, jsonify
            
            if not hasattr(g, 'access_token'):
                return jsonify({"error": "Access token required"}), 401
            
            # Get tenant ID from request
            resource_tenant_id = kwargs.get(tenant_param) or request.json.get(tenant_param)
            
            if not resource_tenant_id:
                return jsonify({"error": f"Missing {tenant_param} parameter"}), 400
            
            # Enforce tenant isolation
            if not rbac_manager.enforce_tenant_isolation(g.access_token, resource_tenant_id):
                rbac_manager._log_audit_event(
                    user_id=g.access_token.user_id,
                    tenant_id=g.access_token.tenant_id,
                    action="tenant_isolation_violation",
                    resource=f"tenant:{resource_tenant_id}",
                    result="denied",
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', 'unknown')
                )
                return jsonify({"error": "Access denied: tenant isolation violation"}), 403
            
            return func(*args, **kwargs)
        
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

# Global RBAC manager (would be initialized with proper secret in production)
rbac_manager = RBACManager(secret_key="sophia-intel-secret-key-change-in-production")

# Initialize default system user
system_user = rbac_manager.create_user(
    user_id="system",
    tenant_id="system",
    email="system@sophia-intel.ai",
    role=Role.SYSTEM
)

