"""
Pulumi ESC Secret Management Infrastructure
Centralized secret management with automatic rotation, caching, and audit logging.
"""
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import aiohttp
from cryptography.fernet import Fernet
from pydantic import BaseModel, Field
logger = logging.getLogger(__name__)
class SecretScope(str, Enum):
    """Secret access scopes"""
    GLOBAL = "global"
    PROJECT = "project"
    ENVIRONMENT = "environment"
    SERVICE = "service"
class SecretStatus(str, Enum):
    """Secret status enumeration"""
    ACTIVE = "active"
    ROTATING = "rotating"
    DEPRECATED = "deprecated"
    REVOKED = "revoked"
    EXPIRED = "expired"
@dataclass
class SecretMetadata:
    """Metadata for secret management"""
    key: str
    scope: SecretScope
    created_at: datetime
    last_accessed: Optional[datetime] = None
    last_rotated: Optional[datetime] = None
    rotation_interval_days: int = 90
    access_count: int = 0
    status: SecretStatus = SecretStatus.ACTIVE
    tags: Set[str] = field(default_factory=set)
    def is_rotation_due(self) -> bool:
        """Check if secret rotation is due"""
        if not self.last_rotated:
            return True
        return (datetime.utcnow() - self.last_rotated).days >= self.rotation_interval_days
    def mark_accessed(self):
        """Mark secret as accessed"""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1
class SecretCache(BaseModel):
    """Local secret cache with TTL"""
    secrets: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, SecretMetadata] = Field(default_factory=dict)
    cache_ttl: int = Field(default=300)  # 5 minutes
    last_refresh: Optional[datetime] = None
    def is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if not self.last_refresh:
            return False
        return (datetime.utcnow() - self.last_refresh).seconds < self.cache_ttl
    def get_secret(self, key: str) -> Optional[Any]:
        """Get secret from cache if valid"""
        if not self.is_cache_valid():
            return None
        metadata = self.metadata.get(key)
        if metadata:
            metadata.mark_accessed()
        return self.secrets.get(key)
    def set_secret(self, key: str, value: Any, metadata: SecretMetadata):
        """Store secret in cache"""
        self.secrets[key] = value
        self.metadata[key] = metadata
        self.last_refresh = datetime.utcnow()
class ESCSecretsManager:
    """Pulumi ESC Secrets Manager with advanced capabilities"""
    def __init__(
        self,
        api_token: str,
        organization: str,
        project_name: str = "sophia-intel-ai",
        cache_ttl: int = 300,
        encryption_key: Optional[str] = None,
    ):
        self.api_token = api_token
        self.organization = organization
        self.project_name = project_name
        self.base_url = "https://api.pulumi.com"
        self.cache = SecretCache(cache_ttl=cache_ttl)
        # Initialize encryption
        if encryption_key:
            self.cipher = Fernet(
                encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
            )
        else:
            self.cipher = Fernet(Fernet.generate_key())
        # Session for HTTP requests
        self._session: Optional[aiohttp.ClientSession] = None
        # Audit logging
        self.audit_log: List[Dict[str, Any]] = []
        # Secret rotation tracking
        self.rotation_queue: Set[str] = set()
        self.rotation_in_progress: Set[str] = set()
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._session:
            await self._session.close()
    async def _ensure_session(self):
        """Ensure HTTP session exists"""
        if not self._session:
            headers = {
                "Authorization": f"token {self.api_token}",
                "Content-Type": "application/json",
            }
            self._session = aiohttp.ClientSession(headers=headers)
    def _encrypt_value(self, value: str) -> str:
        """Encrypt sensitive value"""
        return self.cipher.encrypt(value.encode()).decode()
    def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt sensitive value"""
        return self.cipher.decrypt(encrypted_value.encode()).decode()
    def _audit_log_access(
        self,
        action: str,
        secret_key: str,
        scope: SecretScope = SecretScope.PROJECT,
        success: bool = True,
        error: Optional[str] = None,
    ):
        """Log secret access for audit"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "secret_key": secret_key,
            "scope": scope.value,
            "success": success,
            "error": error,
            "user": "system",  # Could be extended for user tracking
            "ip_address": "127.0.0.1",  # Could be extracted from request context
        }
        self.audit_log.append(log_entry)
        logger.info(f"Secret audit: {action} {secret_key} - {'SUCCESS' if success else 'FAILED'}")
    async def get_environment_config(self, environment: str) -> Dict[str, Any]:
        """Get complete environment configuration from ESC"""
        await self._ensure_session()
        try:
            url = f"{self.base_url}/api/environments/{self.organization}/{environment}"
            async with self._session.get(url) as response:
                if response.status == 200:
                    config = await response.json()
                    self._audit_log_access("get_environment", environment, success=True)
                    return config.get("values", {})
                else:
                    error_msg = f"Failed to get environment config: {response.status}"
                    self._audit_log_access(
                        "get_environment", environment, success=False, error=error_msg
                    )
                    logger.error(error_msg)
                    return {}
        except Exception as e:
            self._audit_log_access("get_environment", environment, success=False, error=str(e))
            logger.error(f"Error getting environment config: {e}")
            return {}
    async def get_secret(
        self, key: str, environment: str = "dev", use_cache: bool = True, decrypt: bool = False
    ) -> Optional[Any]:
        """Get secret value with caching and audit logging"""
        # Try cache first
        if use_cache:
            cached_value = self.cache.get_secret(key)
            if cached_value is not None:
                self._audit_log_access("get_secret_cached", key, success=True)
                return self._decrypt_value(cached_value) if decrypt else cached_value
        # Fetch from ESC
        config = await self.get_environment_config(environment)
        value = self._extract_secret_from_config(config, key)
        if value is not None:
            # Create metadata
            metadata = SecretMetadata(
                key=key, scope=SecretScope.ENVIRONMENT, created_at=datetime.utcnow()
            )
            # Cache the secret
            encrypted_value = self._encrypt_value(str(value)) if isinstance(value, str) else value
            self.cache.set_secret(key, encrypted_value, metadata)
            self._audit_log_access("get_secret", key, success=True)
            return self._decrypt_value(value) if decrypt and isinstance(value, str) else value
        else:
            self._audit_log_access("get_secret", key, success=False, error="Secret not found")
            return None
    def _extract_secret_from_config(self, config: Dict[str, Any], key: str) -> Optional[Any]:
        """Extract secret from nested configuration"""
        keys = key.split(".")
        current = config
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        return current
    async def set_secret(
        self, key: str, value: Any, environment: str = "dev", encrypt: bool = True
    ) -> bool:
        """Set secret value in ESC"""
        await self._ensure_session()
        try:
            # Encrypt if requested
            if encrypt and isinstance(value, str):
                value = self._encrypt_value(value)
            # Update environment configuration
            url = f"{self.base_url}/api/environments/{self.organization}/{environment}"
            # Get current config
            current_config = await self.get_environment_config(environment)
            # Update the specific key
            self._set_nested_key(current_config, key, value)
            # Send update
            payload = {"values": current_config}
            async with self._session.put(url, json=payload) as response:
                if response.status == 200:
                    # Update cache
                    metadata = SecretMetadata(
                        key=key, scope=SecretScope.ENVIRONMENT, created_at=datetime.utcnow()
                    )
                    self.cache.set_secret(key, value, metadata)
                    self._audit_log_access("set_secret", key, success=True)
                    return True
                else:
                    error_msg = f"Failed to set secret: {response.status}"
                    self._audit_log_access("set_secret", key, success=False, error=error_msg)
                    logger.error(error_msg)
                    return False
        except Exception as e:
            self._audit_log_access("set_secret", key, success=False, error=str(e))
            logger.error(f"Error setting secret: {e}")
            return False
    def _set_nested_key(self, config: Dict[str, Any], key: str, value: Any):
        """Set nested key in configuration dictionary"""
        keys = key.split(".")
        current = config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
    async def rotate_secret(self, key: str, environment: str = "dev") -> bool:
        """Rotate a secret (mark old as deprecated, create new)"""
        if key in self.rotation_in_progress:
            logger.warning(f"Secret rotation already in progress for {key}")
            return False
        try:
            self.rotation_in_progress.add(key)
            # Get current secret
            current_value = await self.get_secret(key, environment, use_cache=False)
            if not current_value:
                logger.error(f"Cannot rotate secret {key}: current value not found")
                return False
            # Generate new secret (implementation depends on secret type)
            new_value = await self._generate_new_secret_value(key, current_value)
            # Update secret
            success = await self.set_secret(f"{key}_new", new_value, environment)
            if success:
                # Mark old secret as deprecated
                metadata = self.cache.metadata.get(key)
                if metadata:
                    metadata.status = SecretStatus.DEPRECATED
                    metadata.last_rotated = datetime.utcnow()
                self._audit_log_access("rotate_secret", key, success=True)
                return True
            else:
                self._audit_log_access(
                    "rotate_secret", key, success=False, error="Failed to set new secret"
                )
                return False
        except Exception as e:
            self._audit_log_access("rotate_secret", key, success=False, error=str(e))
            logger.error(f"Error rotating secret {key}: {e}")
            return False
        finally:
            self.rotation_in_progress.discard(key)
    async def _generate_new_secret_value(self, key: str, current_value: Any) -> Any:
        """Generate new secret value (placeholder implementation)"""
        # This would be implemented based on the type of secret
        # For now, return a placeholder
        if isinstance(current_value, str):
            return f"{current_value}_rotated_{int(time.time())}"
        return current_value
    async def bulk_get_secrets(
        self, keys: List[str], environment: str = "dev", use_cache: bool = True
    ) -> Dict[str, Any]:
        """Get multiple secrets efficiently"""
        result = {}
        cache_misses = []
        # Check cache first
        if use_cache:
            for key in keys:
                cached_value = self.cache.get_secret(key)
                if cached_value is not None:
                    result[key] = cached_value
                else:
                    cache_misses.append(key)
        else:
            cache_misses = keys
        # Fetch missing secrets
        if cache_misses:
            config = await self.get_environment_config(environment)
            for key in cache_misses:
                value = self._extract_secret_from_config(config, key)
                if value is not None:
                    result[key] = value
                    # Update cache
                    metadata = SecretMetadata(
                        key=key, scope=SecretScope.ENVIRONMENT, created_at=datetime.utcnow()
                    )
                    encrypted_value = (
                        self._encrypt_value(str(value)) if isinstance(value, str) else value
                    )
                    self.cache.set_secret(key, encrypted_value, metadata)
        self._audit_log_access("bulk_get_secrets", f"keys:{len(keys)}", success=True)
        return result
    async def invalidate_cache(self):
        """Invalidate the secret cache"""
        self.cache = SecretCache(cache_ttl=self.cache.cache_ttl)
        self._audit_log_access("invalidate_cache", "all", success=True)
        logger.info("Secret cache invalidated")
    def get_audit_log(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get audit log entries"""
        if limit:
            return self.audit_log[-limit:]
        return self.audit_log.copy()
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_secrets = len(self.cache.secrets)
        total_accesses = sum(metadata.access_count for metadata in self.cache.metadata.values())
        return {
            "total_secrets": total_secrets,
            "total_accesses": total_accesses,
            "cache_hit_rate": self.cache_hit_rate if hasattr(self, "cache_hit_rate") else 0.0,
            "last_refresh": (
                self.cache.last_refresh.isoformat() if self.cache.last_refresh else None
            ),
            "is_cache_valid": self.cache.is_cache_valid(),
        }
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on ESC connection"""
        await self._ensure_session()
        try:
            url = f"{self.base_url}/api/user"
            async with self._session.get(url) as response:
                if response.status == 200:
                    return {
                        "status": "healthy",
                        "connection": "ok",
                        "cache_valid": self.cache.is_cache_valid(),
                        "cached_secrets": len(self.cache.secrets),
                        "last_audit_entry": (
                            self.audit_log[-1]["timestamp"] if self.audit_log else None
                        ),
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "connection": "failed",
                        "error": f"HTTP {response.status}",
                    }
        except Exception as e:
            return {"status": "unhealthy", "connection": "failed", "error": str(e)}
