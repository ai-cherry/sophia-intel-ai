from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
import json
import logging
import time
import redis
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime, timedelta
from app.observability.prometheus_metrics import (
    request_blocked_total,
    jwt_invalid_total,
    rate_limit_exceeded_total
)
from app.config import config
from app.security.input_validator import InputValidator

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Enhanced security middleware with comprehensive protection"""

    def __init__(self, app, config: Dict):
        super().__init__(app)
        self.config = config
        self.rate_limiter = self._init_rate_limiter()
        self.security_headers = self._init_security_headers()
        self.auth = HTTPBearer(auto_error=False)
        self.auth_scheme = f"Bearer {config.get('JWT_SECRET', 'default_secret')}"
    
    def _init_rate_limiter(self):
        """Initialize Redis-based rate limiter"""
        try:
            redis_url = self.config.get('REDIS_URL', 'redis://localhost:6379')
            redis_conn = redis.Redis.from_url(redis_url, decode_responses=True)
            return redis_conn
        except Exception as e:
            logger.error(f"Rate limiter initialization failed: {str(e)}")
            return None

    def _init_security_headers(self):
        """Configure security headers"""
        return {
            'Content-Security-Policy': "default-src 'self' https: 'unsafe-inline'",
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload'
        }

    async def dispatch(self, request: Request, call_next):
        # Step 1: Rate limiting
        if self.rate_limiter:
            ip = request.client.host
            key = f"rate_limit:{ip}:{request.url.path}"
            current_count = self.rate_limiter.get(key)
            if current_count and int(current_count) >= self.config.get('MAX_REQUESTS_PER_MIN', 60):
                rate_limit_exceeded_total.inc()
                logger.warning(f"Request rate limit exceeded for IP: {ip}")
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests, please try again later"
                )
            self.rate_limiter.setex(key, 60, int(current_count or 0) + 1)

        # Step 2: Input sanitization and validation
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.headers.get('content-type', '')
            if 'application/json' in content_type:
                try:
                    body = await request.body()
                    # Allow only send in one message
                    # Parse body for validation
                    try:
                        json_body = json.loads(body)
                        validated = InputValidator.validate_api_parameters(json_body)
                        # Store validated body in request state
                        request.state.validated = validated
                    except Exception as e:
                        request.state.validated = None
                        logger.error(f"Input validation failed: {str(e)}")
                        raise HTTPException(
                            status_code=400,
                            detail="Invalid input format"
                        )
                except Exception as e:
                    logger.error(f"Body processing failed: {str(e)}")
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid request body"
                    )

        # Step 3: Authentication
        auth = self.auth_scheme.strip()
        if auth:
            try:
                token = self.auth.parse_credentials(
                    HTTPAuthorizationCredentials(
                        scheme=auth.split()[0],
                        credentials=auth.split()[1] if len(auth.split()) > 1 else ''
                    )
                )
                if token:
                    try:
                        payload = jwt.decode(
                            token.credentials,
                            self.config.get('JWT_SECRET', 'default_secret'),
                            algorithms=[self.config.get('JWT_ALGORITHM', 'HS256')]
                        )
                        request.state.user_id = payload.get("sub")
                    except jwt.ExpiredSignatureError:
                        jwt_invalid_total.labels(
                            type="expired", 
                            token_type="access"
                        ).inc()
                        logger.warning("Access token expired")
                        raise HTTPException(
                            status_code=401,
                            detail="Token has expired"
                        )
                    except jwt.InvalidTokenError:
                        jwt_invalid_total.labels(
                            type="invalid",
                            token_type="access"
                        ).inc()
                        logger.warning("Invalid access token")
                        raise HTTPException(
                            status_code=401,
                            detail="Invalid token"
                        )
            except HTTPException:
                raise
            except Exception as e:
                jwt_invalid_total.labels(
                    type="processing",
                    token_type="access"
                ).inc()
                logger.error(f"Token processing failed: {str(e)}")

        # Step 4: Security headers
        response = await call_next(request)
        for header, value in self.security_headers.items():
            response.headers[header] = value

        # Step 5: Audit logging
        duration = time.time() - request.state.start_time
        logger.info(
            f"Request {request.method} {request.url.path} "
            f"from {request.client.host} completed in {duration:.2f}s "
            f"status={response.status_code}"
        )

        return response
