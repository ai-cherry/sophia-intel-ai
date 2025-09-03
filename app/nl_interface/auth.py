"""
Secure Authentication Layer for NL Interface
Provides API key validation, rate limiting, and security features for production
"""

import hashlib
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Optional

from app.core.circuit_breaker import with_circuit_breaker

logger = logging.getLogger(__name__)


@dataclass
class APIKey:
    """API key representation"""
    key_hash: str
    user_id: str
    client_name: str
    quotas: dict[str, int]
    usage: dict[str, int]
    created_at: datetime
    last_used: datetime
    is_active: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "APIKey":
        """Create API key from dictionary"""
        return cls(
            key_hash=data["key_hash"],
            user_id=data["user_id"],
            client_name=data["client_name"],
            quotas=data["quotas"],
            usage=data["usage"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_used=datetime.fromisoformat(data["last_used"]),
            is_active=data["is_active"]
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "key_hash": self.key_hash,
            "user_id": self.user_id,
            "client_name": self.client_name,
            "quotas": self.quotas,
            "usage": self.usage,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat(),
            "is_active": self.is_active
        }


class SecureNLProcessor:
    """
    Enhanced NL Processor with authentication and security features
    Wraps existing QuickNLP but adds production security layers
    """

    def __init__(self, base_processor, config: Optional[dict[str, Any]] = None):
        self.base_processor = base_processor
        self.config = config or {}
        self.api_keys: dict[str, APIKey] = {}
        self.requests_per_second: dict[str, list] = {}
        self.is_auth_enabled = self.config.get("enable_auth", True)

        # Security configuration
        self.max_requests_per_minute = self.config.get("max_requests_per_minute", 60)
        self.rate_limit_window = self.config.get("rate_limit_window_seconds", 60)
        self.enable_cors = self.config.get("enable_cors", True)
        self.enable_rate_limiting = self.config.get("enable_rate_limiting", True)

        # Load API keys on initialization
        self._load_api_keys()

        logger.info(f"SecureNLProcessor initialized - Auth enabled: {self.is_auth_enabled}")

    def _load_api_keys(self):
        """Load API keys from configuration"""
        # Default keys for development
        default_keys = self.config.get("default_api_keys", [
            {
                "key": "dev-key-12345",
                "user_id": "developer",
                "client_name": "Development Environment",
                "quotas": {"requests_per_hour": 1000, "requests_per_day": 10000},
                "usage": {"requests_today": 0, "requests_this_hour": 0}
            }
        ])

        for key_data in default_keys:
            key_hash = self._hash_api_key(key_data["key"])
            api_key = APIKey(
                key_hash=key_hash,
                user_id=key_data["user_id"],
                client_name=key_data["client_name"],
                quotas=key_data["quotas"],
                usage=key_data["usage"],
                created_at=datetime.now(),
                last_used=datetime.now(),
                is_active=True
            )
            self.api_keys[key_hash] = api_key

            logger.info(f"Loaded API key for user: {key_data['user_id']}")

    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()

    def validate_api_key(self, api_key: str) -> tuple[bool, str, dict[str, Any]]:
        """
        Validate API key and return user information
        Returns: (is_valid, message, user_info)
        """
        if not self.is_auth_enabled:
            return True, "Authentication disabled", {
                "user_id": "anonymous",
                "client_name": "Anonymous User"
            }

        key_hash = self._hash_api_key(api_key)
        api_key_obj = self.api_keys.get(key_hash)

        if not api_key_obj:
            logger.warning("Invalid API key attempt")
            return False, "Invalid API key", {}

        if not api_key_obj.is_active:
            logger.warning(f"Disabled API key used by user: {api_key_obj.user_id}")
            return False, "API key is disabled", {}

        # Rate limiting check
        if self.enable_rate_limiting:
            is_allowed, rate_limit_message = self._check_rate_limits(api_key_obj)
            if not is_allowed:
                logger.warning(f"Rate limit exceeded for user: {api_key_obj.user_id}")
                return False, rate_limit_message, {}

        # Update last used time
        api_key_obj.last_used = datetime.now()

        user_info = {
            "user_id": api_key_obj.user_id,
            "client_name": api_key_obj.client_name,
            "quotas": api_key_obj.quotas,
            "usage": api_key_obj.usage
        }

        return True, "Valid API key", user_info

    def _check_rate_limits(self, api_key: APIKey) -> tuple[bool, str]:
        """Check rate limits for API key"""
        now = datetime.now()

        # Rate limiting cleanup (remove old timestamps)
        cutoff_time = now - timedelta(seconds=self.rate_limit_window)

        # Track requests per second
        client_key = api_key.user_id
        if client_key not in self.requests_per_second:
            self.requests_per_second[client_key] = []

        # Filter old requests
        self.requests_per_second[client_key] = [
            ts for ts in self.requests_per_second[client_key]
            if ts > cutoff_time
        ]

        # Check rate limits
        current_requests = len(self.requests_per_second[client_key])
        if current_requests >= self.max_requests_per_minute:
            return False, f"Rate limit exceeded: {current_requests}/{self.max_requests_per_minute} requests per minute"

        # Add current request
        self.requests_per_second[client_key].append(time.time())

        return True, ""

    def record_usage(self, user_id: str, endpoint: str = "process"):
        """Record API usage for billing/reporting"""
        api_key = next((key for key in self.api_keys.values() if key.user_id == user_id), None)
        if not api_key:
            return

        # Update usage counters (simplified)
        api_key.usage["requests_today"] = api_key.usage.get("requests_today", 0) + 1
        api_key.usage["requests_this_hour"] = api_key.usage.get("requests_this_hour", 0) + 1

        # Reset hourly counter if it's a new hour
        # (In production, you'd want a more sophisticated reset mechanism)

    @with_circuit_breaker("auth")
    def process_secure(self, text: str, api_key: str, **kwargs) -> dict[str, Any]:
        """
        Process NL command with security validation
        """
        # Validate API key first
        is_valid, message, user_info = self.validate_api_key(api_key)
        if not is_valid:
            return {
                "success": False,
                "error": message,
                "response": "Authentication failed",
                "user_info": user_info
            }

        try:
            # Record usage
            self.record_usage(user_info["user_id"])

            # Process with base processor
            result = self.base_processor.process(text, **kwargs)

            # Add security metadata
            result["user_info"] = user_info
            result["api_key_validated"] = True
            result["processed_at"] = datetime.now().isoformat()

            # Security headers for CORS if enabled
            if self.enable_cors:
                result["cors_headers"] = {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "X-API-Key, Content-Type",
                    "Access-Control-Allow-Methods": "POST, GET, OPTIONS"
                }

            return result

        except Exception as e:
            logger.error(f"Error in secure processing: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "response": "Processing failed",
                "processed_at": datetime.now().isoformat()
            }

    def get_usage_statistics(self, user_id: Optional[str] = None) -> dict[str, Any]:
        """Get usage statistics for all users or specific user"""
        stats = {
            "total_api_keys": len(self.api_keys),
            "active_api_keys": len([k for k in self.api_keys.values() if k.is_active]),
            "rate_limit_window_seconds": self.rate_limit_window,
            "user_stats": {}
        }

        for api_key in self.api_keys.values():
            if user_id and api_key.user_id != user_id:
                continue

            stats["user_stats"][api_key.user_id] = {
                "client_name": api_key.client_name,
                "quotas": api_key.quotas,
                "usage": api_key.usage,
                "last_used": api_key.last_used.isoformat(),
                "is_active": api_key.is_active
            }

        return stats

    def add_api_key(self, api_key: str, user_id: str, client_name: str,
                   quotas: Optional[dict[str, int]] = None) -> dict[str, Any]:
        """Add new API key"""
        key_hash = self._hash_api_key(api_key)

        if key_hash in self.api_keys:
            return {"success": False, "error": "API key already exists"}

        api_key_obj = APIKey(
            key_hash=key_hash,
            user_id=user_id,
            client_name=client_name,
            quotas=quotas or {"requests_per_hour": 100, "requests_per_day": 1000},
            usage={"requests_today": 0, "requests_this_hour": 0},
            created_at=datetime.now(),
            last_used=datetime.now(),
            is_active=True
        )

        self.api_keys[key_hash] = api_key_obj

        logger.info(f"Added new API key for user: {user_id}")
        return {"success": True, "message": "API key added successfully"}

    def disable_api_key(self, user_id: str) -> dict[str, Any]:
        """Disable API key for user"""
        api_key = next((key for key in self.api_keys.values() if key.user_id == user_id), None)
        if not api_key:
            return {"success": False, "error": "User not found"}

        api_key.is_active = False
        logger.info(f"Disabled API key for user: {user_id}")
        return {"success": True, "message": "API key disabled"}


def create_secure_processor(base_processor, config: Optional[dict[str, Any]] = None) -> SecureNLProcessor:
    """Factory function to create secure processor"""
    config = config or {
        "enable_auth": True,
        "enable_rate_limiting": True,
        "enable_cors": True,
        "max_requests_per_minute": 60,
        "rate_limit_window_seconds": 60,
        "default_api_keys": [
            {
                "key": "dev-key-12345",
                "user_id": "developer",
                "client_name": "Development Environment",
                "quotas": {"requests_per_hour": 1000, "requests_per_day": 10000},
                "usage": {"requests_today": 0, "requests_this_hour": 0}
            }
        ]
    }

    return SecureNLProcessor(base_processor, config)


# FastAPI Dependency
async def get_secure_processor():
    """Dependency to get secure processor instance"""
    # In production, this would be properly initialized and cached
    from app.nl_interface.quicknlp import QuickNLP
    base_processor = QuickNLP()
    return create_secure_processor(base_processor)


# Middleware function for rate limiting
def rate_limiter(client_id: str, max_calls: int = 60, window_seconds: int = 60):
    """Decorator for rate limiting"""
    calls: dict[str, list] = {}

    def decorator(func):
        @wraps(func)
        async def wrapped(*args, **kwargs):
            now = time.time()
            if client_id not in calls:
                calls[client_id] = []
            else:
                # Remove old calls
                calls[client_id] = [t for t in calls[client_id]
                                   if now - t < window_seconds]

            if len(calls[client_id]) >= max_calls:
                # Rate limit exceeded
                logger.warning(f"Rate limit exceeded for client: {client_id}")
                return {
                    "success": False,
                    "error": f"Rate limit exceeded ({max_calls} calls per {window_seconds}s)",
                    "rate_limited": True
                }

            calls[client_id].append(now)
            return await func(*args, **kwargs)
        return wrapped

    return decorator
