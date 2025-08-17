"""
Security middleware for SOPHIA Intel API
Implements security headers, input validation, and CORS policies
"""

import os
import re
import bleach
from typing import Dict, Any, List
from fastapi import Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

# Security configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,https://sophia-intel.ai,https://www.sophia-intel.ai,https://dashboard.sophia-intel.ai").split(",")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,sophia-intel.ai,*.sophia-intel.ai,*.up.railway.app").split(",")

# Content Security Policy
CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data: https:; "
    "connect-src 'self' https://api.openai.com https://api.anthropic.com https://api.elevenlabs.io; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self';"
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = CSP_POLICY
        
        # HSTS for HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Remove server information
        response.headers.pop("server", None)
        
        return response

class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize input data"""
    
    # Dangerous patterns to detect
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',                # JavaScript URLs
        r'on\w+\s*=',                 # Event handlers
        r'<iframe[^>]*>.*?</iframe>',  # Iframes
        r'<object[^>]*>.*?</object>',  # Objects
        r'<embed[^>]*>.*?</embed>',    # Embeds
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip validation for certain content types
        content_type = request.headers.get("content-type", "")
        if "multipart/form-data" in content_type or "application/octet-stream" in content_type:
            return await call_next(request)
        
        # Validate request body for JSON requests
        if "application/json" in content_type:
            try:
                body = await request.body()
                if body:
                    body_str = body.decode("utf-8")
                    
                    # Check for dangerous patterns
                    for pattern in self.DANGEROUS_PATTERNS:
                        if re.search(pattern, body_str, re.IGNORECASE):
                            logger.warning(f"Dangerous pattern detected in request: {pattern}")
                            raise HTTPException(
                                status_code=400,
                                detail="Invalid input detected"
                            )
                    
                    # Sanitize HTML content
                    sanitized_body = bleach.clean(body_str, tags=[], attributes={}, strip=True)
                    if sanitized_body != body_str:
                        logger.info("HTML content sanitized in request")
            except UnicodeDecodeError:
                logger.warning("Unable to decode request body for validation")
        
        return await call_next(request)

def sanitize_html_input(text: str) -> str:
    """Sanitize HTML input to prevent XSS attacks"""
    if not text:
        return text
    
    # Allow basic formatting tags but strip dangerous content
    allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
    allowed_attributes = {}
    
    return bleach.clean(text, tags=allowed_tags, attributes=allowed_attributes, strip=True)

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_url(url: str) -> bool:
    """Validate URL format"""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return re.match(pattern, url) is not None

def setup_cors_middleware(app):
    """Setup CORS middleware with secure configuration"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID"],
    )

def setup_trusted_host_middleware(app):
    """Setup trusted host middleware"""
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=ALLOWED_HOSTS
    )

def setup_security_middleware(app):
    """Setup all security middleware"""
    # Order matters - add in reverse order of execution
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(InputValidationMiddleware)
    setup_cors_middleware(app)
    setup_trusted_host_middleware(app)

# Rate limiting configuration
RATE_LIMITS = {
    "default": {"requests": 100, "window": 60},  # 100 requests per minute
    "chat": {"requests": 30, "window": 60},      # 30 chat requests per minute
    "research": {"requests": 20, "window": 60},   # 20 research requests per minute
    "mcp": {"requests": 200, "window": 60},       # 200 MCP requests per minute
}

class RateLimitExceeded(HTTPException):
    """Rate limit exceeded exception"""
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(status_code=429, detail=detail)

# Simple in-memory rate limiting (use Redis in production)
rate_limit_storage: Dict[str, Dict[str, Any]] = {}

def check_rate_limit(client_id: str, endpoint_type: str = "default") -> bool:
    """Check if client has exceeded rate limit"""
    import time
    
    current_time = time.time()
    limit_config = RATE_LIMITS.get(endpoint_type, RATE_LIMITS["default"])
    
    if client_id not in rate_limit_storage:
        rate_limit_storage[client_id] = {}
    
    client_data = rate_limit_storage[client_id]
    
    # Clean old entries
    window_start = current_time - limit_config["window"]
    client_data[endpoint_type] = [
        timestamp for timestamp in client_data.get(endpoint_type, [])
        if timestamp > window_start
    ]
    
    # Check if limit exceeded
    if len(client_data[endpoint_type]) >= limit_config["requests"]:
        return False
    
    # Add current request
    client_data[endpoint_type].append(current_time)
    return True

def get_client_id(request: Request) -> str:
    """Get client identifier for rate limiting"""
    # Try to get user ID from authentication
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    
    # Fall back to IP address
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return f"ip:{forwarded_for.split(',')[0].strip()}"
    
    client_host = request.client.host if request.client else "unknown"
    return f"ip:{client_host}"

