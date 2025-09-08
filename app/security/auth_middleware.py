"""
Production Authentication Middleware
Handles JWT tokens, API keys, and rate limiting
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.resource_manager import get_managed_redis
from app.models.orchestration_models import create_error_response

logger = logging.getLogger(__name__)


class RateLimiter:
    """Production rate limiter with Redis backend"""

    def __init__(self):
        self.local_cache: dict[str, dict[str, any]] = {}
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()

    async def is_rate_limited(
        self,
        identifier: str,
        limit: int,
        window_seconds: int,
        burst_limit: Optional[int] = None,
    ) -> tuple[bool, dict[str, int]]:
        """
        Check if request should be rate limited

        Args:
            identifier: Unique identifier (IP, user_id, etc.)
            limit: Requests per window
            window_seconds: Time window in seconds
            burst_limit: Optional burst limit for temporary spikes

        Returns:
            (is_limited, rate_info)
        """
        try:
            # Use Redis for distributed rate limiting
            redis = await get_managed_redis()
            current_time = int(time.time())
            window_start = current_time - (current_time % window_seconds)

            key = f"rate_limit:{identifier}:{window_start}"

            # Get current count
            current_count = await redis.get(key)
            current_count = int(current_count) if current_count else 0

            # Check burst limit first
            if burst_limit and current_count >= burst_limit:
                return True, {
                    "requests": current_count,
                    "limit": limit,
                    "burst_limit": burst_limit,
                    "window_seconds": window_seconds,
                    "reset_at": window_start + window_seconds,
                }

            # Check regular limit
            if current_count >= limit:
                return True, {
                    "requests": current_count,
                    "limit": limit,
                    "window_seconds": window_seconds,
                    "reset_at": window_start + window_seconds,
                }

            # Increment counter
            pipe = redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            await pipe.execute()

            return False, {
                "requests": current_count + 1,
                "limit": limit,
                "window_seconds": window_seconds,
                "reset_at": window_start + window_seconds,
            }

        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fall back to local cache
            return await self._local_rate_limit(identifier, limit, window_seconds)

    async def _local_rate_limit(
        self, identifier: str, limit: int, window_seconds: int
    ) -> tuple[bool, dict[str, int]]:
        """Fallback local rate limiting"""
        current_time = time.time()
        window_start = current_time - (current_time % window_seconds)

        # Cleanup old entries
        if current_time - self.last_cleanup > self.cleanup_interval:
            await self._cleanup_local_cache()

        if identifier not in self.local_cache:
            self.local_cache[identifier] = {"count": 0, "window_start": window_start}

        cache_entry = self.local_cache[identifier]

        # Reset if new window
        if cache_entry["window_start"] < window_start:
            cache_entry["count"] = 0
            cache_entry["window_start"] = window_start

        if cache_entry["count"] >= limit:
            return True, {
                "requests": cache_entry["count"],
                "limit": limit,
                "window_seconds": window_seconds,
                "reset_at": int(window_start + window_seconds),
            }

        cache_entry["count"] += 1
        return False, {
            "requests": cache_entry["count"],
            "limit": limit,
            "window_seconds": window_seconds,
            "reset_at": int(window_start + window_seconds),
        }

    async def _cleanup_local_cache(self):
        """Clean up expired local cache entries"""
        current_time = time.time()
        expired_keys = []

        for identifier, data in self.local_cache.items():
            if current_time - data["window_start"] > 3600:  # 1 hour
                expired_keys.append(identifier)

        for key in expired_keys:
            del self.local_cache[key]

        self.last_cleanup = current_time


class JWTHandler:
    """JWT token handler"""

    def __init__(self):
        self.algorithm = "HS256"
        self.secret_key = settings.jwt_secret.get_secret_value()
        self.expiry_hours = settings.jwt_expiry_hours

    def create_token(self, user_id: str, permissions: set[str] = None) -> str:
        """Create JWT token"""
        now = datetime.utcnow()
        payload = {
            "user_id": user_id,
            "permissions": list(permissions or set()),
            "iat": now,
            "exp": now + timedelta(hours=self.expiry_hours),
            "iss": "sophia-intel-ai",
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode JWT token"""
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith("Bearer "):
                token = token[7:]

            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": True},
            )

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"JWT verification error: {e}")
            return None

    def get_user_permissions(self, payload: dict) -> set[str]:
        """Extract user permissions from token payload"""
        return set(payload.get("permissions", []))


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Production authentication middleware"""

    def __init__(self, app):
        super().__init__(app)
        self.jwt_handler = JWTHandler()
        self.rate_limiter = RateLimiter()

        # Paths that don't require authentication
        self.public_paths = {
            "/",
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        }

        # Admin-only paths
        self.admin_paths = {"/admin", "/internal", "/debug"}

        # Rate limiting tiers
        self.rate_limits = {
            "anonymous": {"limit": 60, "window": 3600},  # 60/hour
            "authenticated": {"limit": 1000, "window": 3600},  # 1000/hour
            "admin": {"limit": 10000, "window": 3600},  # 10000/hour
        }

    async def dispatch(self, request: Request, call_next):
        """Main middleware dispatch"""
        start_time = time.time()

        try:
            # Skip auth for public paths
            if self._is_public_path(request.url.path):
                response = await call_next(request)
                return self._add_headers(response, start_time)

            # Skip auth if not required (development mode)
            if not settings.require_auth and settings.environment == "development":
                response = await call_next(request)
                return self._add_headers(response, start_time)

            # Authenticate request
            auth_result = await self._authenticate(request)
            if not auth_result["authenticated"]:
                return self._create_auth_error_response(
                    auth_result.get("error", "Authentication required")
                )

            # Rate limiting
            rate_limit_result = await self._check_rate_limit(request, auth_result)
            if rate_limit_result["limited"]:
                return self._create_rate_limit_response(rate_limit_result)

            # Add auth context to request
            request.state.auth = auth_result
            request.state.rate_limit = rate_limit_result

            # Process request
            response = await call_next(request)
            return self._add_headers(response, start_time, rate_limit_result)

        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content=create_error_response(
                    request_id=request.headers.get("X-Request-ID", "unknown"),
                    error_code="AUTH_MIDDLEWARE_ERROR",
                    error_message="Internal authentication error",
                ).dict(),
            )

    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (no auth required)"""
        path = path.rstrip("/")
        return any(path.startswith(public) for public in self.public_paths)

    async def _authenticate(self, request: Request) -> dict:
        """Authenticate the request"""
        auth_header = request.headers.get(settings.auth_token_header)

        if not auth_header:
            return {"authenticated": False, "error": "Missing authentication header"}

        # Check for admin API key
        if (
            settings.admin_api_key
            and auth_header == f"Bearer {settings.admin_api_key.get_secret_value()}"
        ):
            return {
                "authenticated": True,
                "user_id": "admin",
                "user_type": "admin",
                "permissions": {"admin", "read", "write"},
            }

        # Check JWT token
        jwt_payload = self.jwt_handler.verify_token(auth_header)
        if jwt_payload:
            permissions = self.jwt_handler.get_user_permissions(jwt_payload)
            return {
                "authenticated": True,
                "user_id": jwt_payload.get("user_id"),
                "user_type": "admin" if "admin" in permissions else "user",
                "permissions": permissions,
                "token_payload": jwt_payload,
            }

        return {"authenticated": False, "error": "Invalid authentication token"}

    async def _check_rate_limit(self, request: Request, auth_result: dict) -> dict:
        """Check rate limiting"""
        # Determine user tier
        user_type = auth_result.get("user_type", "anonymous")
        rate_config = self.rate_limits.get(user_type, self.rate_limits["anonymous"])

        # Create identifier (user_id or IP)
        identifier = auth_result.get("user_id") or self._get_client_ip(request)

        # Check rate limit
        is_limited, rate_info = await self.rate_limiter.is_rate_limited(
            identifier=f"{user_type}:{identifier}",
            limit=rate_config["limit"],
            window_seconds=rate_config["window"],
            burst_limit=rate_config.get("burst_limit"),
        )

        return {
            "limited": is_limited,
            "identifier": identifier,
            "user_type": user_type,
            **rate_info,
        }

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers (behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection
        if hasattr(request.client, "host"):
            return request.client.host

        return "unknown"

    def _create_auth_error_response(self, error_message: str) -> JSONResponse:
        """Create authentication error response"""
        return JSONResponse(
            status_code=401,
            content={
                "error": "authentication_required",
                "message": error_message,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    def _create_rate_limit_response(self, rate_info: dict) -> JSONResponse:
        """Create rate limit error response"""
        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limit_exceeded",
                "message": f"Rate limit exceeded: {rate_info['requests']}/{rate_info['limit']} requests",
                "rate_limit": {
                    "requests": rate_info["requests"],
                    "limit": rate_info["limit"],
                    "window_seconds": rate_info["window_seconds"],
                    "reset_at": rate_info["reset_at"],
                },
                "timestamp": datetime.utcnow().isoformat(),
            },
            headers={
                "X-RateLimit-Limit": str(rate_info["limit"]),
                "X-RateLimit-Remaining": str(
                    max(0, rate_info["limit"] - rate_info["requests"])
                ),
                "X-RateLimit-Reset": str(rate_info["reset_at"]),
                "Retry-After": str(rate_info.get("window_seconds", 60)),
            },
        )

    def _add_headers(
        self, response: Response, start_time: float, rate_info: dict = None
    ) -> Response:
        """Add standard headers to response"""
        processing_time = (time.time() - start_time) * 1000

        response.headers["X-Processing-Time"] = f"{processing_time:.2f}ms"
        response.headers["X-API-Version"] = "2.1.0"

        if rate_info:
            response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(
                max(0, rate_info["limit"] - rate_info["requests"])
            )
            response.headers["X-RateLimit-Reset"] = str(rate_info["reset_at"])

        return response


# Convenience function for manual auth checks
async def verify_admin_access(request: Request) -> bool:
    """Verify if request has admin access"""
    if not hasattr(request.state, "auth"):
        return False

    auth_info = request.state.auth
    return auth_info.get("authenticated", False) and "admin" in auth_info.get(
        "permissions", set()
    )


async def get_current_user(request: Request) -> Optional[dict]:
    """Get current authenticated user info"""
    if not hasattr(request.state, "auth"):
        return None

    auth_info = request.state.auth
    if not auth_info.get("authenticated", False):
        return None

    return {
        "user_id": auth_info.get("user_id"),
        "user_type": auth_info.get("user_type"),
        "permissions": auth_info.get("permissions", set()),
    }
