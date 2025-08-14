"""
Authentication and authorization for MCP servers
Provides API key authentication and role-based access control
"""
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional, List
import os
import hashlib
import hmac
from loguru import logger

# Security scheme
security = HTTPBearer()

# API key configuration
API_KEYS = {}
if os.getenv("MCP_API_KEYS"):
    # Format: "key1:role1,key2:role2" 
    for key_role in os.getenv("MCP_API_KEYS", "").split(","):
        if ":" in key_role:
            key, role = key_role.strip().split(":", 1)
            API_KEYS[key] = role
        else:
            # Default role if no role specified
            API_KEYS[key_role.strip()] = "user"

# Default admin key from environment
ADMIN_KEY = os.getenv("MCP_ADMIN_KEY")
if ADMIN_KEY:
    API_KEYS[ADMIN_KEY] = "admin"

class AuthContext:
    """Authentication context for requests"""
    
    def __init__(self, api_key: str, role: str, permissions: List[str]):
        self.api_key = api_key
        self.role = role
        self.permissions = permissions
        self.user_id = hashlib.sha256(api_key.encode()).hexdigest()[:16]

def get_role_permissions(role: str) -> List[str]:
    """Get permissions for a role"""
    role_permissions = {
        "admin": ["read", "write", "delete", "manage", "swarm"],
        "user": ["read", "write", "swarm"],
        "readonly": ["read"],
        "swarm": ["read", "write", "swarm"],  # Special role for swarm agents
    }
    return role_permissions.get(role, ["read"])

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> AuthContext:
    """
    Verify API key and return authentication context
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        AuthContext: Authentication context
        
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    api_key = credentials.credentials
    
    # Check if API key exists
    if api_key not in API_KEYS:
        logger.warning(f"Invalid API key attempted: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    role = API_KEYS[api_key]
    permissions = get_role_permissions(role)
    
    logger.debug(f"Authenticated user with role: {role}")
    
    return AuthContext(api_key=api_key, role=role, permissions=permissions)

async def require_permission(required_permission: str):
    """
    Dependency to require specific permission
    
    Args:
        required_permission: Permission required to access endpoint
        
    Returns:
        Function that checks permission
    """
    async def permission_checker(auth: AuthContext = Depends(verify_api_key)) -> AuthContext:
        if required_permission not in auth.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{required_permission}' required",
            )
        return auth
    
    return permission_checker

# Convenience dependencies for common permissions
api_key_auth = Depends(verify_api_key)

def admin_auth():
    return require_permission("manage")

def swarm_auth():
    return require_permission("swarm")

def write_auth():
    return require_permission("write")

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify webhook signature (for services like Slack, GitHub, etc.)
    
    Args:
        payload: Request payload bytes
        signature: Signature from webhook header
        secret: Webhook secret
        
    Returns:
        bool: True if signature is valid
    """
    if not secret:
        logger.warning("Webhook secret not configured")
        return False
        
    # Calculate expected signature
    expected = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Remove 'sha256=' prefix if present
    if signature.startswith('sha256='):
        signature = signature[7:]
        
    return hmac.compare_digest(expected, signature)

async def verify_service_token(service_name: str, token: str) -> bool:
    """
    Verify service-specific token (for service-to-service communication)
    
    Args:
        service_name: Name of the service
        token: Service token
        
    Returns:
        bool: True if token is valid
    """
    expected_token = os.getenv(f"{service_name.upper()}_SERVICE_TOKEN")
    if not expected_token:
        logger.warning(f"Service token not configured for {service_name}")
        return False
        
    return hmac.compare_digest(expected_token, token)

class ServiceAuth:
    """Authentication for service-to-service communication"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.token = os.getenv(f"{service_name.upper()}_SERVICE_TOKEN")
    
    async def __call__(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
        """Verify service token"""
        if not self.token:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=f"Service authentication not configured for {self.service_name}"
            )
        
        if not credentials or not await verify_service_token(self.service_name, credentials.credentials):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid service token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return self.service_name

def create_api_key(role: str = "user") -> str:
    """
    Create a new API key (for administrative purposes)
    
    Args:
        role: Role to assign to the key
        
    Returns:
        str: Generated API key
    """
    import secrets
    key = f"mcp_{secrets.token_urlsafe(32)}"
    API_KEYS[key] = role
    return key

def revoke_api_key(api_key: str) -> bool:
    """
    Revoke an API key
    
    Args:
        api_key: API key to revoke
        
    Returns:
        bool: True if key was revoked
    """
    if api_key in API_KEYS:
        del API_KEYS[api_key]
        logger.info(f"Revoked API key: {api_key[:8]}...")
        return True
    return False

def list_api_keys() -> Dict[str, str]:
    """
    List all API keys and their roles (for admin purposes)
    
    Returns:
        Dict[str, str]: Mapping of key prefixes to roles
    """
    return {key[:8] + "...": role for key, role in API_KEYS.items()}