"""
Enhanced Authentication System for SOPHIA Intel
Implements Bearer token authentication with proper security
"""

import os
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)

class SOPHIAAuthenticator:
    """Enhanced authentication system for SOPHIA Intel"""
    
    def __init__(self):
        self.jwt_secret = os.getenv("JWT_SECRET_KEY", "sophia-intel-production-jwt-secret-2025")
        self.api_gateway_token = os.getenv("API_GATEWAY_TOKEN", "sophia-intel-api-gateway-token-2025")
        self.mcp_auth_token = os.getenv("MCP_AUTH_TOKEN", "sophia-intel-mcp-auth-token-2025")
        
        # Token expiration settings
        self.access_token_expire_minutes = 60 * 24  # 24 hours
        self.refresh_token_expire_days = 30
        
        # Security settings
        self.algorithm = "HS256"
        self.bearer_scheme = HTTPBearer()
        
        # Valid API keys for different access levels
        self.valid_api_keys = {
            "admin": self._generate_admin_key(),
            "user": self._generate_user_key(),
            "service": self._generate_service_key()
        }
        
        logger.info("SOPHIA Authentication system initialized")
    
    def _generate_admin_key(self) -> str:
        """Generate admin API key"""
        base = f"sophia-admin-{self.api_gateway_token}"
        return hashlib.sha256(base.encode()).hexdigest()[:32]
    
    def _generate_user_key(self) -> str:
        """Generate user API key"""
        base = f"sophia-user-{self.api_gateway_token}"
        return hashlib.sha256(base.encode()).hexdigest()[:32]
    
    def _generate_service_key(self) -> str:
        """Generate service API key"""
        base = f"sophia-service-{self.mcp_auth_token}"
        return hashlib.sha256(base.encode()).hexdigest()[:32]
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def verify_api_key(self, api_key: str) -> Optional[str]:
        """Verify API key and return access level"""
        for level, valid_key in self.valid_api_keys.items():
            if api_key == valid_key:
                return level
        return None
    
    def authenticate_request(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> Dict[str, Any]:
        """Authenticate incoming request"""
        token = credentials.credentials
        
        # Try JWT token first
        try:
            payload = self.verify_token(token)
            return {
                "authenticated": True,
                "user_id": payload.get("sub"),
                "access_level": payload.get("access_level", "user"),
                "auth_type": "jwt"
            }
        except HTTPException:
            pass
        
        # Try API key authentication
        access_level = self.verify_api_key(token)
        if access_level:
            return {
                "authenticated": True,
                "user_id": f"{access_level}_user",
                "access_level": access_level,
                "auth_type": "api_key"
            }
        
        # Authentication failed
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    def require_admin(self, auth_data: Dict = Depends(lambda self: self.authenticate_request)) -> Dict[str, Any]:
        """Require admin access level"""
        if auth_data["access_level"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return auth_data
    
    def get_api_keys(self) -> Dict[str, str]:
        """Get API keys for frontend configuration"""
        return {
            "admin_key": self.valid_api_keys["admin"],
            "user_key": self.valid_api_keys["user"],
            "service_key": self.valid_api_keys["service"]
        }
    
    def generate_session_token(self, user_id: str, access_level: str = "user") -> Dict[str, str]:
        """Generate session tokens for a user"""
        token_data = {
            "sub": user_id,
            "access_level": access_level,
            "iat": datetime.utcnow()
        }
        
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60
        }

# Global authenticator instance
authenticator = SOPHIAAuthenticator()

def get_authenticator() -> SOPHIAAuthenticator:
    """Get global authenticator instance"""
    return authenticator

# Dependency functions for FastAPI
def authenticate_request(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> Dict[str, Any]:
    """FastAPI dependency for request authentication"""
    return authenticator.authenticate_request(credentials)

def require_admin(auth_data: Dict = Depends(authenticate_request)) -> Dict[str, Any]:
    """FastAPI dependency for admin access"""
    return authenticator.require_admin(auth_data)

def optional_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[Dict[str, Any]]:
    """Optional authentication for public endpoints"""
    if not credentials:
        return None
    
    try:
        return authenticator.authenticate_request(credentials)
    except HTTPException:
        return None

