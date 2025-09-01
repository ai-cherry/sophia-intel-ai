"""
Authentication Layer for Natural Language Interface
Provides API key validation, rate limiting, and security headers
"""

import hashlib
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict
import json
import os

from fastapi import HTTPException, Security, Header, Request
from fastapi.security import APIKeyHeader, APIKeyQuery
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


@dataclass
class APIKeyConfig:
    """Configuration for an API key"""
    key_hash: str
    name: str
    created_at: str
    rate_limit: int  # requests per minute
    is_active: bool
    permissions: List[str]
    metadata: Optional[Dict[str, Any]] = None


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.cleanup_interval = 60  # seconds
        self.last_cleanup = time.time()
    
    def is_allowed(self, key: str, limit: int, window: int = 60) -> bool:
        """
        Check if request is allowed under rate limit
        
        Args:
            key: API key or identifier
            limit: Maximum requests allowed
            window: Time window in seconds
            
        Returns:
            True if request is allowed, False otherwise
        """
        current_time = time.time()
        
        # Cleanup old entries periodically
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup()
        
        # Get request timestamps for this key
        timestamps = self.requests[key]
        
        # Remove timestamps outside the window
        cutoff_time = current_time - window
        timestamps = [t for t in timestamps if t > cutoff_time]
        
        # Check if under limit
        if len(timestamps) < limit:
            timestamps.append(current_time)
            self.requests[key] = timestamps
            return True
        
        return False
    
    def _cleanup(self):
        """Remove old entries from memory"""
        current_time = time.time()
        cutoff_time = current_time - 300  # Keep last 5 minutes
        
        for key in list(self.requests.keys()):
            self.requests[key] = [t for t in self.requests[key] if t > cutoff_time]
            if not self.requests[key]:
                del self.requests[key]
        
        self.last_cleanup = current_time
    
    def get_remaining(self, key: str, limit: int, window: int = 60) -> int:
        """Get remaining requests for a key"""
        current_time = time.time()
        cutoff_time = current_time - window
        timestamps = [t for t in self.requests.get(key, []) if t > cutoff_time]
        return max(0, limit - len(timestamps))


class SecureNLProcessor:
    """
    Security layer for NL processing with API key validation
    """
    
    def __init__(
        self,
        api_keys_file: str = "api_keys.json",
        enable_auth: bool = True,
        default_rate_limit: int = 60
    ):
        """
        Initialize secure NL processor
        
        Args:
            api_keys_file: Path to JSON file containing API keys
            enable_auth: Whether to enable authentication (can be disabled for dev)
            default_rate_limit: Default rate limit per minute
        """
        self.enable_auth = enable_auth
        self.default_rate_limit = default_rate_limit
        self.rate_limiter = RateLimiter()
        self.api_keys = {}
        
        # Load API keys
        self._load_api_keys(api_keys_file)
        
        # API key extractors
        self.api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
        self.api_key_query = APIKeyQuery(name="api_key", auto_error=False)
    
    def _load_api_keys(self, api_keys_file: str):
        """Load API keys from file"""
        try:
            if os.path.exists(api_keys_file):
                with open(api_keys_file, 'r') as f:
                    keys_data = json.load(f)
                    
                for key_id, config in keys_data.items():
                    self.api_keys[key_id] = APIKeyConfig(**config)
                    
                logger.info(f"Loaded {len(self.api_keys)} API keys")
            else:
                # Create default API key for development
                default_key = "dev-api-key-12345"
                default_hash = hashlib.sha256(default_key.encode()).hexdigest()
                
                self.api_keys["dev"] = APIKeyConfig(
                    key_hash=default_hash,
                    name="Development Key",
                    created_at=datetime.now().isoformat(),
                    rate_limit=100,
                    is_active=True,
                    permissions=["all"]
                )
                
                logger.warning("No API keys file found, using default development key")
                
        except Exception as e:
            logger.error(f"Error loading API keys: {e}")
            # Continue without API keys if loading fails
    
    def _hash_api_key(self, api_key: str) -> str:
        """Hash an API key for comparison"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def validate_api_key(
        self,
        api_key_header: Optional[str] = None,
        api_key_query: Optional[str] = None
    ) -> APIKeyConfig:
        """
        Validate API key from header or query parameter
        
        Args:
            api_key_header: API key from header
            api_key_query: API key from query parameter
            
        Returns:
            APIKeyConfig if valid
            
        Raises:
            HTTPException if invalid
        """
        # Skip validation if auth is disabled
        if not self.enable_auth:
            return APIKeyConfig(
                key_hash="",
                name="No Auth",
                created_at=datetime.now().isoformat(),
                rate_limit=self.default_rate_limit,
                is_active=True,
                permissions=["all"]
            )
        
        # Get API key from header or query
        api_key = api_key_header or api_key_query
        
        if not api_key:
            logger.warning("No API key provided")
            raise HTTPException(
                status_code=401,
                detail="API key required",
                headers={"WWW-Authenticate": "APIKey"}
            )
        
        # Hash the provided key
        key_hash = self._hash_api_key(api_key)
        
        # Find matching API key config
        for key_config in self.api_keys.values():
            if key_config.key_hash == key_hash and key_config.is_active:
                return key_config
        
        logger.warning(f"Invalid API key attempted: {api_key[:8]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "APIKey"}
        )
    
    def check_rate_limit(self, api_key: str, config: APIKeyConfig) -> bool:
        """
        Check if request is within rate limit
        
        Args:
            api_key: The API key
            config: API key configuration
            
        Returns:
            True if allowed, raises HTTPException if not
        """
        if not self.rate_limiter.is_allowed(api_key, config.rate_limit):
            remaining = self.rate_limiter.get_remaining(api_key, config.rate_limit)
            
            logger.warning(f"Rate limit exceeded for key: {config.name}")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(config.rate_limit),
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(int(time.time()) + 60)
                }
            )
        
        return True
    
    def check_permission(self, config: APIKeyConfig, permission: str) -> bool:
        """
        Check if API key has required permission
        
        Args:
            config: API key configuration
            permission: Required permission
            
        Returns:
            True if allowed, raises HTTPException if not
        """
        if "all" in config.permissions or permission in config.permissions:
            return True
        
        logger.warning(f"Permission denied for key {config.name}: {permission}")
        raise HTTPException(
            status_code=403,
            detail=f"Permission denied: {permission}"
        )
    
    async def authenticate_request(
        self,
        request: Request,
        api_key_header: Optional[str] = Security(api_key_header),
        api_key_query: Optional[str] = Security(api_key_query)
    ) -> APIKeyConfig:
        """
        Full authentication flow for a request
        
        Args:
            request: FastAPI request object
            api_key_header: API key from header
            api_key_query: API key from query
            
        Returns:
            APIKeyConfig if authenticated
        """
        # Validate API key
        config = self.validate_api_key(api_key_header, api_key_query)
        
        # Check rate limit
        api_key = api_key_header or api_key_query or "anonymous"
        self.check_rate_limit(api_key, config)
        
        # Log successful authentication
        logger.info(f"Authenticated request from {config.name} to {request.url.path}")
        
        return config


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security middleware to add security headers to all responses
    """
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response"""
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        # Add custom headers
        response.headers["X-Service-Name"] = "Sophia-Intel-AI-NL"
        response.headers["X-Service-Version"] = "1.0.0"
        
        return response


# Singleton instance
_secure_processor = None


def get_secure_processor(
    api_keys_file: str = "api_keys.json",
    enable_auth: bool = None
) -> SecureNLProcessor:
    """
    Get singleton instance of secure processor
    
    Args:
        api_keys_file: Path to API keys file
        enable_auth: Override auth enable setting
        
    Returns:
        SecureNLProcessor instance
    """
    global _secure_processor
    
    if _secure_processor is None:
        # Check environment variable for auth setting
        if enable_auth is None:
            enable_auth = os.getenv("ENABLE_AUTH", "true").lower() == "true"
        
        _secure_processor = SecureNLProcessor(
            api_keys_file=api_keys_file,
            enable_auth=enable_auth
        )
    
    return _secure_processor


# Dependency for FastAPI
async def require_api_key(
    api_key_header: Optional[str] = Header(None, alias="X-API-Key"),
    api_key_query: Optional[str] = None
) -> APIKeyConfig:
    """
    FastAPI dependency to require API key
    
    Args:
        api_key_header: API key from header
        api_key_query: API key from query parameter
        
    Returns:
        APIKeyConfig if valid
    """
    processor = get_secure_processor()
    return processor.validate_api_key(api_key_header, api_key_query)


def create_api_key(name: str, rate_limit: int = 60) -> Dict[str, str]:
    """
    Helper function to create a new API key
    
    Args:
        name: Name for the API key
        rate_limit: Rate limit per minute
        
    Returns:
        Dictionary with key details
    """
    import secrets
    
    # Generate random API key
    api_key = f"sk-{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    config = {
        "key_hash": key_hash,
        "name": name,
        "created_at": datetime.now().isoformat(),
        "rate_limit": rate_limit,
        "is_active": True,
        "permissions": ["read", "write"]
    }
    
    return {
        "api_key": api_key,
        "config": config,
        "note": "Save this API key securely, it won't be shown again"
    }


# Example usage
if __name__ == "__main__":
    # Create example API keys file
    example_keys = {
        "key1": create_api_key("Production API", rate_limit=100)["config"],
        "key2": create_api_key("Development API", rate_limit=60)["config"]
    }
    
    with open("api_keys_example.json", "w") as f:
        json.dump(example_keys, f, indent=2)
    
    print("Example API keys file created: api_keys_example.json")
    
    # Test authentication
    processor = SecureNLProcessor(enable_auth=False)
    config = processor.validate_api_key(None, None)
    print(f"Auth disabled mode: {config.name}")