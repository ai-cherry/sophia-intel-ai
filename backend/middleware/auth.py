"""
Authentication middleware for SOPHIA Intel API
Implements JWT-based authentication with bearer token validation
"""

import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "sophia-intel-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# API Token Configuration
API_GATEWAY_TOKEN = os.getenv("API_GATEWAY_TOKEN")
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN")

security = HTTPBearer(auto_error=False)

class AuthenticationError(HTTPException):
    """Custom authentication error"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=401, detail=detail)

class AuthorizationError(HTTPException):
    """Custom authorization error"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(status_code=403, detail=detail)

def create_jwt_token(user_data: Dict[str, Any]) -> str:
    """Create a JWT token for authenticated user"""
    payload = {
        "user_data": user_data,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow(),
        "iss": "sophia-intel"
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload.get("user_data", {})
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")

def verify_api_token(token: str, service: str = "api") -> bool:
    """Verify API token for service access"""
    if service == "api" and API_GATEWAY_TOKEN:
        return token == API_GATEWAY_TOKEN
    elif service == "mcp" and MCP_AUTH_TOKEN:
        return token == MCP_AUTH_TOKEN
    return False

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user from JWT token"""
    if not credentials:
        raise AuthenticationError("Missing authentication credentials")
    
    token = credentials.credentials
    
    # Try JWT token first
    try:
        user_data = verify_jwt_token(token)
        logger.info(f"JWT authentication successful for user: {user_data.get('user_id', 'unknown')}")
        return user_data
    except AuthenticationError:
        pass
    
    # Try API token authentication
    if verify_api_token(token, "api"):
        logger.info("API token authentication successful")
        return {"user_id": "api_user", "role": "api", "authenticated_via": "api_token"}
    
    raise AuthenticationError("Invalid authentication credentials")

async def verify_mcp_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> bool:
    """Verify MCP service token"""
    if not credentials:
        raise AuthenticationError("Missing MCP authentication token")
    
    token = credentials.credentials
    
    if verify_api_token(token, "mcp"):
        logger.info("MCP token authentication successful")
        return True
    
    raise AuthenticationError("Invalid MCP authentication token")

def require_role(required_role: str):
    """Decorator to require specific role for endpoint access"""
    def role_checker(user_data: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = user_data.get("role", "user")
        if user_role != required_role and user_role != "admin":
            raise AuthorizationError(f"Role '{required_role}' required")
        return user_data
    return role_checker

# Middleware for request authentication
async def auth_middleware(request: Request, call_next):
    """Authentication middleware for all requests"""
    # Skip authentication for health checks and public endpoints
    public_paths = ["/health", "/docs", "/openapi.json", "/"]
    
    if request.url.path in public_paths:
        response = await call_next(request)
        return response
    
    # Check for authentication header
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning(f"Unauthenticated request to {request.url.path}")
        # For development, allow unauthenticated requests
        if os.getenv("ENVIRONMENT") != "production":
            response = await call_next(request)
            return response
        else:
            raise AuthenticationError("Missing or invalid authorization header")
    
    response = await call_next(request)
    return response

