"""
Authentication middleware for API endpoints
"""
from __future__ import annotations
from datetime import datetime, timedelta
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings
# Security scheme for Swagger UI
security = HTTPBearer(auto_error=False)
class AuthenticationError(HTTPException):
    """Custom authentication exception"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=401, detail=detail)
class AuthorizationError(HTTPException):
    """Custom authorization exception"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(status_code=403, detail=detail)
def create_jwt_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiry_hours)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret.get_secret_value(), algorithm="HS256"
    )
    return encoded_jwt
def decode_jwt_token(token: str) -> dict:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret.get_secret_value(), algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.JWTError:
        raise AuthenticationError("Invalid token")
async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Verify API key authentication
    Returns the authenticated user/service identifier
    """
    # Skip auth if not required
    if not settings.require_auth:
        return "anonymous"
    if not credentials:
        raise AuthenticationError("No credentials provided")
    token = credentials.credentials
    # Check if it's an API key
    if settings.admin_api_key and token == settings.admin_api_key.get_secret_value():
        return "admin"
    # Try to decode as JWT
    try:
        payload = decode_jwt_token(token)
        return payload.get("sub", "authenticated_user")
    except AuthenticationError:
        # If both API key and JWT validation fail
        raise AuthenticationError("Invalid API key or token")
async def verify_admin_access(user: str = Depends(verify_api_key)) -> str:
    """
    Verify admin access for sensitive operations
    """
    if not settings.require_auth:
        return "admin"  # In dev mode, allow admin access
    if user != "admin":
        raise AuthorizationError("Admin access required")
    return user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str | None:
    """
    Get current user from credentials (optional auth)
    Returns None if no auth provided, useful for endpoints that work with or without auth
    """
    if not credentials:
        return None
    try:
        return await verify_api_key(credentials)
    except AuthenticationError:
        return None
class RateLimitMiddleware:
    """
    Rate limiting middleware
    """
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}
        self.window_start = datetime.utcnow()
    async def check_rate_limit(
        self, request: Request, user: str = Depends(get_current_user)
    ):
        """Check if request should be rate limited"""
        # Use IP address if no user
        identifier = user or request.client.host
        now = datetime.utcnow()
        # Reset window if needed
        if (now - self.window_start).seconds > 60:
            self.request_counts = {}
            self.window_start = now
        # Check rate limit
        current_count = self.request_counts.get(identifier, 0)
        if current_count >= self.requests_per_minute:
            raise HTTPException(
                status_code=429, detail="Rate limit exceeded. Please try again later."
            )
        # Increment count
        self.request_counts[identifier] = current_count + 1
        return identifier
# Global rate limiter instance
rate_limiter = RateLimitMiddleware(requests_per_minute=settings.max_concurrent_requests)
# Dependency for rate limiting
async def check_rate_limit(
    request: Request, user: str | None = Depends(get_current_user)
) -> str:
    """Rate limit dependency"""
    return await rate_limiter.check_rate_limit(request, user)
