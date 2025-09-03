"""
Secrets Management and Rate Limiting

This module provides secure secrets management and rate limiting functionality
to protect API keys and prevent abuse of agent resources.
"""

import asyncio
import hashlib
import logging
import os
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Optional

import redis
from cryptography.fernet import Fernet
from pydantic import BaseModel, Field

from app.core.exceptions import (
    AuthorizationError,
    RateLimitError,
    SecretExposureError,
    SecurityError,
)

logger = logging.getLogger(__name__)


class SecretProvider(ABC):
    """Abstract base class for secret providers"""
    
    @abstractmethod
    async def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret by key"""
        pass
    
    @abstractmethod
    async def set_secret(self, key: str, value: str) -> bool:
        """Store a secret"""
        pass
    
    @abstractmethod
    async def delete_secret(self, key: str) -> bool:
        """Delete a secret"""
        pass
    
    @abstractmethod
    async def list_secrets(self) -> list[str]:
        """List available secret keys"""
        pass


class EnvironmentSecretProvider(SecretProvider):
    """Provider that reads secrets from environment variables"""
    
    def __init__(self, prefix: str = "SOPHIA_"):
        self.prefix = prefix
    
    async def get_secret(self, key: str) -> Optional[str]:
        """Get secret from environment"""
        env_key = f"{self.prefix}{key.upper()}"
        return os.getenv(env_key)
    
    async def set_secret(self, key: str, value: str) -> bool:
        """Cannot set environment variables at runtime"""
        logger.warning("Cannot set secrets in environment provider")
        return False
    
    async def delete_secret(self, key: str) -> bool:
        """Cannot delete environment variables at runtime"""
        logger.warning("Cannot delete secrets in environment provider")
        return False
    
    async def list_secrets(self) -> list[str]:
        """List environment secrets"""
        secrets = []
        for key in os.environ:
            if key.startswith(self.prefix):
                secret_key = key[len(self.prefix):].lower()
                secrets.append(secret_key)
        return secrets


class VaultSecretProvider(SecretProvider):
    """HashiCorp Vault secret provider"""
    
    def __init__(self, vault_url: str, vault_token: str, mount_point: str = "secret"):
        self.vault_url = vault_url
        self.vault_token = vault_token
        self.mount_point = mount_point
        # Would use hvac library in production
        self.client = None
    
    async def get_secret(self, key: str) -> Optional[str]:
        """Get secret from Vault"""
        # Simplified implementation
        try:
            # Would use: response = self.client.secrets.kv.v2.read_secret_version(path=key)
            # return response['data']['data'].get('value')
            logger.info(f"Would fetch {key} from Vault")
            return None
        except Exception as e:
            logger.error(f"Failed to get secret from Vault: {e}")
            return None
    
    async def set_secret(self, key: str, value: str) -> bool:
        """Store secret in Vault"""
        try:
            # Would use: self.client.secrets.kv.v2.create_or_update_secret(path=key, secret={'value': value})
            logger.info(f"Would store {key} in Vault")
            return True
        except Exception as e:
            logger.error(f"Failed to set secret in Vault: {e}")
            return False
    
    async def delete_secret(self, key: str) -> bool:
        """Delete secret from Vault"""
        try:
            # Would use: self.client.secrets.kv.v2.delete_metadata_and_all_versions(path=key)
            logger.info(f"Would delete {key} from Vault")
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret from Vault: {e}")
            return False
    
    async def list_secrets(self) -> list[str]:
        """List secrets in Vault"""
        try:
            # Would use: self.client.secrets.kv.v2.list_secrets(path='')
            return []
        except Exception as e:
            logger.error(f"Failed to list secrets from Vault: {e}")
            return []


class AWSSecretsProvider(SecretProvider):
    """AWS Secrets Manager provider"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        # Would use boto3 in production
        self.client = None
    
    async def get_secret(self, key: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager"""
        try:
            # Would use: response = self.client.get_secret_value(SecretId=key)
            # return response['SecretString']
            logger.info(f"Would fetch {key} from AWS Secrets Manager")
            return None
        except Exception as e:
            logger.error(f"Failed to get secret from AWS: {e}")
            return None
    
    async def set_secret(self, key: str, value: str) -> bool:
        """Store secret in AWS Secrets Manager"""
        try:
            # Would use: self.client.create_secret(Name=key, SecretString=value)
            logger.info(f"Would store {key} in AWS Secrets Manager")
            return True
        except Exception as e:
            logger.error(f"Failed to set secret in AWS: {e}")
            return False
    
    async def delete_secret(self, key: str) -> bool:
        """Delete secret from AWS Secrets Manager"""
        try:
            # Would use: self.client.delete_secret(SecretId=key, ForceDeleteWithoutRecovery=True)
            logger.info(f"Would delete {key} from AWS Secrets Manager")
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret from AWS: {e}")
            return False
    
    async def list_secrets(self) -> list[str]:
        """List secrets in AWS Secrets Manager"""
        try:
            # Would use: response = self.client.list_secrets()
            # return [s['Name'] for s in response['SecretList']]
            return []
        except Exception as e:
            logger.error(f"Failed to list secrets from AWS: {e}")
            return []


class EncryptedLocalProvider(SecretProvider):
    """Local encrypted file-based secret provider"""
    
    def __init__(self, secrets_file: str = ".secrets.enc"):
        self.secrets_file = secrets_file
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
        self._secrets_cache = {}
        self._load_secrets()
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key"""
        key_file = ".secrets.key"
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Restrict permissions
            return key
    
    def _load_secrets(self):
        """Load secrets from encrypted file"""
        if os.path.exists(self.secrets_file):
            try:
                with open(self.secrets_file, 'rb') as f:
                    encrypted_data = f.read()
                    decrypted_data = self.cipher.decrypt(encrypted_data)
                    import json
                    self._secrets_cache = json.loads(decrypted_data)
            except Exception as e:
                logger.error(f"Failed to load secrets: {e}")
                self._secrets_cache = {}
    
    def _save_secrets(self):
        """Save secrets to encrypted file"""
        try:
            import json
            data = json.dumps(self._secrets_cache)
            encrypted_data = self.cipher.encrypt(data.encode())
            with open(self.secrets_file, 'wb') as f:
                f.write(encrypted_data)
            os.chmod(self.secrets_file, 0o600)  # Restrict permissions
        except Exception as e:
            logger.error(f"Failed to save secrets: {e}")
    
    async def get_secret(self, key: str) -> Optional[str]:
        """Get secret from encrypted storage"""
        return self._secrets_cache.get(key)
    
    async def set_secret(self, key: str, value: str) -> bool:
        """Store secret in encrypted storage"""
        self._secrets_cache[key] = value
        self._save_secrets()
        return True
    
    async def delete_secret(self, key: str) -> bool:
        """Delete secret from encrypted storage"""
        if key in self._secrets_cache:
            del self._secrets_cache[key]
            self._save_secrets()
            return True
        return False
    
    async def list_secrets(self) -> list[str]:
        """List available secrets"""
        return list(self._secrets_cache.keys())


class SecretsManager:
    """Central secrets management system"""
    
    def __init__(self, provider: Optional[SecretProvider] = None):
        self.provider = provider or EnvironmentSecretProvider()
        self._secret_patterns = [
            r'api[_-]?key',
            r'secret',
            r'password',
            r'token',
            r'credential',
            r'auth',
            r'private[_-]?key'
        ]
    
    async def get_secret(self, key: str) -> str:
        """Get a secret securely"""
        secret = await self.provider.get_secret(key)
        if secret is None:
            raise SecurityError(f"Secret '{key}' not found")
        return secret
    
    async def set_secret(self, key: str, value: str) -> bool:
        """Store a secret securely"""
        # Check for potential exposure
        if self._check_exposure_risk(value):
            raise SecretExposureError()
        
        return await self.provider.set_secret(key, value)
    
    def _check_exposure_risk(self, value: str) -> bool:
        """Check if value might be exposed"""
        # Simple checks - would be more sophisticated
        import re
        
        # Check if it looks like a real secret
        if len(value) < 8:
            return False
        
        # Check for common patterns
        for pattern in self._secret_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return False  # Looks like a secret, allow it
        
        return False
    
    def mask_secret(self, value: str, show_chars: int = 4) -> str:
        """Mask a secret for display"""
        if len(value) <= show_chars * 2:
            return "*" * len(value)
        return value[:show_chars] + "*" * (len(value) - show_chars * 2) + value[-show_chars:]
    
    async def rotate_secret(self, key: str, new_value: str) -> bool:
        """Rotate a secret"""
        # Store old secret with timestamp
        old_secret = await self.provider.get_secret(key)
        if old_secret:
            backup_key = f"{key}_backup_{int(time.time())}"
            await self.provider.set_secret(backup_key, old_secret)
        
        # Set new secret
        return await self.provider.set_secret(key, new_value)


class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        default_limits: Optional[dict] = None
    ):
        self.redis_client = redis_client
        self.default_limits = default_limits or {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "requests_per_day": 10000
        }
        
        # In-memory fallback if Redis not available
        self._memory_store = defaultdict(list)
    
    async def check_rate_limit(
        self,
        key: str,
        limits: Optional[dict] = None
    ) -> tuple[bool, Optional[int]]:
        """Check if rate limit is exceeded"""
        limits = limits or self.default_limits
        
        if self.redis_client:
            return await self._check_redis_limit(key, limits)
        else:
            return self._check_memory_limit(key, limits)
    
    async def _check_redis_limit(
        self,
        key: str,
        limits: dict
    ) -> tuple[bool, Optional[int]]:
        """Check rate limit using Redis"""
        current_time = int(time.time())
        
        for period, limit in limits.items():
            if "minute" in period:
                window = 60
            elif "hour" in period:
                window = 3600
            elif "day" in period:
                window = 86400
            else:
                continue
            
            redis_key = f"rate_limit:{key}:{period}"
            
            # Use sliding window
            pipeline = self.redis_client.pipeline()
            pipeline.zremrangebyscore(redis_key, 0, current_time - window)
            pipeline.zadd(redis_key, {str(current_time): current_time})
            pipeline.zcard(redis_key)
            pipeline.expire(redis_key, window + 1)
            
            results = pipeline.execute()
            count = results[2]
            
            if count > limit:
                # Calculate retry after
                oldest = self.redis_client.zrange(redis_key, 0, 0, withscores=True)
                if oldest:
                    retry_after = int(oldest[0][1] + window - current_time)
                    return False, retry_after
                return False, window
        
        return True, None
    
    def _check_memory_limit(
        self,
        key: str,
        limits: dict
    ) -> tuple[bool, Optional[int]]:
        """Check rate limit using in-memory storage"""
        current_time = time.time()
        
        # Clean old entries
        self._memory_store[key] = [
            t for t in self._memory_store[key]
            if current_time - t < 86400  # Keep last day
        ]
        
        for period, limit in limits.items():
            if "minute" in period:
                window = 60
            elif "hour" in period:
                window = 3600
            elif "day" in period:
                window = 86400
            else:
                continue
            
            # Count requests in window
            count = sum(
                1 for t in self._memory_store[key]
                if current_time - t < window
            )
            
            if count >= limit:
                # Calculate retry after
                if self._memory_store[key]:
                    oldest = min(self._memory_store[key])
                    retry_after = int(oldest + window - current_time)
                    return False, retry_after
                return False, window
        
        # Add current request
        self._memory_store[key].append(current_time)
        return True, None
    
    async def reset_limits(self, key: str):
        """Reset rate limits for a key"""
        if self.redis_client:
            pattern = f"rate_limit:{key}:*"
            for redis_key in self.redis_client.scan_iter(match=pattern):
                self.redis_client.delete(redis_key)
        else:
            self._memory_store[key] = []


class RateLimitDecorator:
    """Decorator for rate limiting"""
    
    def __init__(self, limiter: RateLimiter):
        self.limiter = limiter
    
    def limit(
        self,
        key_func: Optional[callable] = None,
        limits: Optional[dict] = None
    ):
        """Decorator to apply rate limiting"""
        def decorator(func):
            async def async_wrapper(*args, **kwargs):
                # Generate rate limit key
                if key_func:
                    key = key_func(*args, **kwargs)
                else:
                    # Default: use function name and first arg if available
                    key = func.__name__
                    if args and hasattr(args[0], 'agent_id'):
                        key = f"{key}:{args[0].agent_id}"
                
                # Check rate limit
                allowed, retry_after = await self.limiter.check_rate_limit(key, limits)
                
                if not allowed:
                    raise RateLimitError(
                        limit_type="request",
                        current_rate=0,  # Would calculate actual rate
                        max_rate=limits.get("requests_per_minute", 60) if limits else 60,
                        retry_after=retry_after
                    )
                
                # Execute function
                return await func(*args, **kwargs)
            
            def sync_wrapper(*args, **kwargs):
                # For sync functions, use asyncio.run
                import asyncio
                
                # Generate rate limit key
                if key_func:
                    key = key_func(*args, **kwargs)
                else:
                    key = func.__name__
                    if args and hasattr(args[0], 'agent_id'):
                        key = f"{key}:{args[0].agent_id}"
                
                # Check rate limit
                allowed, retry_after = asyncio.run(
                    self.limiter.check_rate_limit(key, limits)
                )
                
                if not allowed:
                    raise RateLimitError(
                        limit_type="request",
                        current_rate=0,
                        max_rate=limits.get("requests_per_minute", 60) if limits else 60,
                        retry_after=retry_after
                    )
                
                # Execute function
                return func(*args, **kwargs)
            
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator


# Global instances
_redis_client = None
try:
    _redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        decode_responses=True
    )
    _redis_client.ping()
except:
    logger.warning("Redis not available, using in-memory rate limiting")
    _redis_client = None

global_secrets_manager = SecretsManager()
global_rate_limiter = RateLimiter(redis_client=_redis_client)
rate_limit = RateLimitDecorator(global_rate_limiter).limit