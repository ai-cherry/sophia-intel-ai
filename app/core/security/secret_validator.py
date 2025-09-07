"""
Secret Validator for Pulumi ESC Integration
Validates API keys, database credentials, and other secrets for correctness and security.
"""

import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import aiohttp
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class ValidationResult(str, Enum):
    """Validation result types"""

    VALID = "valid"
    INVALID = "invalid"
    EXPIRED = "expired"
    RATE_LIMITED = "rate_limited"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"


class SecretType(str, Enum):
    """Types of secrets that can be validated"""

    OPENAI_API_KEY = "openai_api_key"
    ANTHROPIC_API_KEY = "anthropic_api_key"
    DEEPSEEK_API_KEY = "deepseek_api_key"
    OPENROUTER_API_KEY = "openrouter_api_key"
    PERPLEXITY_API_KEY = "perplexity_api_key"
    GROQ_API_KEY = "groq_api_key"
    MISTRAL_API_KEY = "mistral_api_key"
    XAI_API_KEY = "xai_api_key"
    TOGETHER_API_KEY = "together_api_key"
    COHERE_API_KEY = "cohere_api_key"
    GEMINI_API_KEY = "gemini_api_key"
    HUGGINGFACE_API_KEY = "huggingface_api_key"
    REDIS_CONNECTION = "redis_connection"
    QDRANT_API_KEY = "qdrant_api_key"
    WEAVIATE_API_KEY = "weaviate_api_key"
    PORTKEY_API_KEY = "portkey_api_key"
    DATABASE_PASSWORD = "database_password"
    JWT_TOKEN = "jwt_token"
    WEBHOOK_SECRET = "webhook_secret"


@dataclass
class ValidationConfig:
    """Configuration for secret validation"""

    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    rate_limit_per_hour: int = 100
    cache_results: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour
    validate_format_only: bool = False  # Skip external API calls
    validate_permissions: bool = True
    check_rate_limits: bool = True


@dataclass
class ValidationResultData:
    """Detailed validation result"""

    result: ValidationResult
    secret_type: SecretType
    secret_hint: str  # Last 4 characters for identification
    validation_time: datetime
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    additional_info: dict[str, Any] = field(default_factory=dict)
    permissions_validated: bool = False
    rate_limit_info: Optional[dict[str, Any]] = None


class SecretFormatValidator:
    """Validates secret formats without external API calls"""

    @staticmethod
    def validate_openai_key(api_key: str) -> bool:
        """Validate OpenAI API key format"""
        # OpenAI keys start with 'sk-' and are typically 51 characters
        pattern = r"^sk-[A-Za-z0-9]{48}$"
        return bool(re.match(pattern, api_key))

    @staticmethod
    def validate_anthropic_key(api_key: str) -> bool:
        """Validate Anthropic API key format"""
        # Anthropic keys start with 'sk-ant-' and are longer
        pattern = r"^sk-ant-api03-[A-Za-z0-9_-]{95}$"
        return bool(re.match(pattern, api_key))

    @staticmethod
    def validate_deepseek_key(api_key: str) -> bool:
        """Validate Deepseek API key format"""
        # Deepseek keys start with 'sk-' and are 32 characters
        pattern = r"^sk-[a-f0-9]{32}$"
        return bool(re.match(pattern, api_key))

    @staticmethod
    def validate_gemini_key(api_key: str) -> bool:
        """Validate Google Gemini API key format"""
        # Gemini keys are typically 39 characters starting with specific pattern
        pattern = r"^AIzaSy[A-Za-z0-9_-]{33}$"
        return bool(re.match(pattern, api_key))

    @staticmethod
    def validate_huggingface_token(token: str) -> bool:
        """Validate HuggingFace API token format"""
        # HuggingFace tokens start with 'hf_' and are 37 characters total
        pattern = r"^hf_[A-Za-z0-9]{34}$"
        return bool(re.match(pattern, token))

    @staticmethod
    def validate_redis_url(url: str) -> bool:
        """Validate Redis connection URL format"""
        redis_patterns = [
            r"^redis://[^:@]+@[^:]+:\d+$",  # redis://user:pass@host:port
            r"^redis://[^:@]+:\d+$",  # redis://host:port
            r"^rediss://[^:@]+@[^:]+:\d+$",  # SSL version
        ]
        return any(re.match(pattern, url) for pattern in redis_patterns)

    @staticmethod
    def validate_jwt_token(token: str) -> bool:
        """Validate JWT token format"""
        # JWT tokens have three base64 parts separated by dots
        parts = token.split(".")
        if len(parts) != 3:
            return False

        # Check if each part is valid base64-like
        return all(re.match(r"^[A-Za-z0-9_-]+$", part) for part in parts)

    @staticmethod
    def get_validator_for_type(secret_type: SecretType) -> Optional[callable]:
        """Get format validator function for secret type"""
        validators = {
            SecretType.OPENAI_API_KEY: SecretFormatValidator.validate_openai_key,
            SecretType.ANTHROPIC_API_KEY: SecretFormatValidator.validate_anthropic_key,
            SecretType.DEEPSEEK_API_KEY: SecretFormatValidator.validate_deepseek_key,
            SecretType.GEMINI_API_KEY: SecretFormatValidator.validate_gemini_key,
            SecretType.HUGGINGFACE_API_KEY: SecretFormatValidator.validate_huggingface_token,
            SecretType.REDIS_CONNECTION: SecretFormatValidator.validate_redis_url,
            SecretType.JWT_TOKEN: SecretFormatValidator.validate_jwt_token,
        }
        return validators.get(secret_type)


class ExternalAPIValidator:
    """Validates secrets by making actual API calls"""

    def __init__(self, config: ValidationConfig):
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._rate_limits: dict[str, list[float]] = {}
        self._validation_cache: dict[str, ValidationResultData] = {}

    async def __aenter__(self):
        if not self._session:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    def _check_rate_limit(self, secret_type: SecretType) -> bool:
        """Check if we're within rate limits for this secret type"""
        if not self.config.check_rate_limits:
            return True

        type_key = secret_type.value
        now = time.time()
        hour_ago = now - 3600

        # Clean old entries
        if type_key in self._rate_limits:
            self._rate_limits[type_key] = [
                timestamp for timestamp in self._rate_limits[type_key] if timestamp > hour_ago
            ]
        else:
            self._rate_limits[type_key] = []

        # Check current count
        return len(self._rate_limits[type_key]) < self.config.rate_limit_per_hour

    def _record_api_call(self, secret_type: SecretType):
        """Record an API call for rate limiting"""
        if self.config.check_rate_limits:
            type_key = secret_type.value
            if type_key not in self._rate_limits:
                self._rate_limits[type_key] = []
            self._rate_limits[type_key].append(time.time())

    def _get_cached_result(self, secret_key: str) -> Optional[ValidationResultData]:
        """Get cached validation result"""
        if not self.config.cache_results:
            return None

        if secret_key in self._validation_cache:
            result = self._validation_cache[secret_key]
            age = (datetime.utcnow() - result.validation_time).total_seconds()
            if age < self.config.cache_ttl_seconds:
                return result
            else:
                # Remove expired cache entry
                del self._validation_cache[secret_key]

        return None

    def _cache_result(self, secret_key: str, result: ValidationResultData):
        """Cache validation result"""
        if self.config.cache_results:
            self._validation_cache[secret_key] = result

    async def validate_openai_key(self, api_key: str) -> ValidationResultData:
        """Validate OpenAI API key by making API call"""
        secret_hint = api_key[-4:] if len(api_key) >= 4 else "****"
        start_time = time.time()

        try:
            if not self._check_rate_limit(SecretType.OPENAI_API_KEY):
                return ValidationResultData(
                    result=ValidationResult.RATE_LIMITED,
                    secret_type=SecretType.OPENAI_API_KEY,
                    secret_hint=secret_hint,
                    validation_time=datetime.utcnow(),
                    error_message="Rate limit exceeded",
                )

            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

            # Use a lightweight endpoint
            url = "https://api.openai.com/v1/models"

            async with self._session.get(url, headers=headers) as response:
                self._record_api_call(SecretType.OPENAI_API_KEY)
                response_time = (time.time() - start_time) * 1000

                if response.status == 200:
                    data = await response.json()
                    models_count = len(data.get("data", []))

                    return ValidationResultData(
                        result=ValidationResult.VALID,
                        secret_type=SecretType.OPENAI_API_KEY,
                        secret_hint=secret_hint,
                        validation_time=datetime.utcnow(),
                        response_time_ms=response_time,
                        permissions_validated=True,
                        additional_info={"models_available": models_count},
                    )
                elif response.status == 401:
                    return ValidationResultData(
                        result=ValidationResult.INVALID,
                        secret_type=SecretType.OPENAI_API_KEY,
                        secret_hint=secret_hint,
                        validation_time=datetime.utcnow(),
                        response_time_ms=response_time,
                        error_message="Invalid API key",
                    )
                elif response.status == 429:
                    return ValidationResultData(
                        result=ValidationResult.RATE_LIMITED,
                        secret_type=SecretType.OPENAI_API_KEY,
                        secret_hint=secret_hint,
                        validation_time=datetime.utcnow(),
                        response_time_ms=response_time,
                        error_message="OpenAI rate limit exceeded",
                    )
                else:
                    return ValidationResultData(
                        result=ValidationResult.UNKNOWN_ERROR,
                        secret_type=SecretType.OPENAI_API_KEY,
                        secret_hint=secret_hint,
                        validation_time=datetime.utcnow(),
                        response_time_ms=response_time,
                        error_message=f"Unexpected status: {response.status}",
                    )

        except asyncio.TimeoutError:
            return ValidationResultData(
                result=ValidationResult.NETWORK_ERROR,
                secret_type=SecretType.OPENAI_API_KEY,
                secret_hint=secret_hint,
                validation_time=datetime.utcnow(),
                error_message="Request timeout",
            )
        except Exception as e:
            return ValidationResultData(
                result=ValidationResult.UNKNOWN_ERROR,
                secret_type=SecretType.OPENAI_API_KEY,
                secret_hint=secret_hint,
                validation_time=datetime.utcnow(),
                error_message=str(e),
            )

    async def validate_anthropic_key(self, api_key: str) -> ValidationResultData:
        """Validate Anthropic API key"""
        secret_hint = api_key[-4:] if len(api_key) >= 4 else "****"
        start_time = time.time()

        try:
            if not self._check_rate_limit(SecretType.ANTHROPIC_API_KEY):
                return ValidationResultData(
                    result=ValidationResult.RATE_LIMITED,
                    secret_type=SecretType.ANTHROPIC_API_KEY,
                    secret_hint=secret_hint,
                    validation_time=datetime.utcnow(),
                    error_message="Rate limit exceeded",
                )

            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            }

            # Use a minimal request to test the key
            url = "https://api.anthropic.com/v1/messages"
            payload = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "test"}],
            }

            async with self._session.post(url, headers=headers, json=payload) as response:
                self._record_api_call(SecretType.ANTHROPIC_API_KEY)
                response_time = (time.time() - start_time) * 1000

                if response.status == 200:
                    return ValidationResultData(
                        result=ValidationResult.VALID,
                        secret_type=SecretType.ANTHROPIC_API_KEY,
                        secret_hint=secret_hint,
                        validation_time=datetime.utcnow(),
                        response_time_ms=response_time,
                        permissions_validated=True,
                    )
                elif response.status in [400, 422]:  # Bad request but key is valid
                    return ValidationResultData(
                        result=ValidationResult.VALID,
                        secret_type=SecretType.ANTHROPIC_API_KEY,
                        secret_hint=secret_hint,
                        validation_time=datetime.utcnow(),
                        response_time_ms=response_time,
                        permissions_validated=True,
                        additional_info={"note": "Key valid, request format issue"},
                    )
                elif response.status == 401:
                    return ValidationResultData(
                        result=ValidationResult.INVALID,
                        secret_type=SecretType.ANTHROPIC_API_KEY,
                        secret_hint=secret_hint,
                        validation_time=datetime.utcnow(),
                        response_time_ms=response_time,
                        error_message="Invalid API key",
                    )
                else:
                    return ValidationResultData(
                        result=ValidationResult.UNKNOWN_ERROR,
                        secret_type=SecretType.ANTHROPIC_API_KEY,
                        secret_hint=secret_hint,
                        validation_time=datetime.utcnow(),
                        response_time_ms=response_time,
                        error_message=f"Unexpected status: {response.status}",
                    )

        except Exception as e:
            return ValidationResultData(
                result=ValidationResult.UNKNOWN_ERROR,
                secret_type=SecretType.ANTHROPIC_API_KEY,
                secret_hint=secret_hint,
                validation_time=datetime.utcnow(),
                error_message=str(e),
            )

    async def validate_redis_connection(
        self, connection_url: str, password: str = ""
    ) -> ValidationResultData:
        """Validate Redis connection"""
        secret_hint = connection_url[-10:] if len(connection_url) >= 10 else "****"
        start_time = time.time()

        try:
            # Parse Redis URL and add password if provided
            if password and ":" not in connection_url.split("@")[0]:
                # Add password to URL if not present
                if "://" in connection_url:
                    protocol, rest = connection_url.split("://", 1)
                    connection_url = f"{protocol}://:{password}@{rest}"

            # Create Redis client
            redis_client = redis.from_url(
                connection_url, socket_timeout=self.config.timeout_seconds, retry_on_timeout=False
            )

            # Test connection
            await redis_client.ping()
            response_time = (time.time() - start_time) * 1000

            # Get Redis info
            info = await redis_client.info()
            redis_version = info.get("redis_version", "unknown")
            connected_clients = info.get("connected_clients", 0)

            await redis_client.close()

            return ValidationResultData(
                result=ValidationResult.VALID,
                secret_type=SecretType.REDIS_CONNECTION,
                secret_hint=secret_hint,
                validation_time=datetime.utcnow(),
                response_time_ms=response_time,
                permissions_validated=True,
                additional_info={
                    "redis_version": redis_version,
                    "connected_clients": connected_clients,
                },
            )

        except redis.AuthenticationError:
            return ValidationResultData(
                result=ValidationResult.INVALID,
                secret_type=SecretType.REDIS_CONNECTION,
                secret_hint=secret_hint,
                validation_time=datetime.utcnow(),
                error_message="Authentication failed",
            )
        except redis.ConnectionError:
            return ValidationResultData(
                result=ValidationResult.NETWORK_ERROR,
                secret_type=SecretType.REDIS_CONNECTION,
                secret_hint=secret_hint,
                validation_time=datetime.utcnow(),
                error_message="Connection failed",
            )
        except asyncio.TimeoutError:
            return ValidationResultData(
                result=ValidationResult.NETWORK_ERROR,
                secret_type=SecretType.REDIS_CONNECTION,
                secret_hint=secret_hint,
                validation_time=datetime.utcnow(),
                error_message="Connection timeout",
            )
        except Exception as e:
            return ValidationResultData(
                result=ValidationResult.UNKNOWN_ERROR,
                secret_type=SecretType.REDIS_CONNECTION,
                secret_hint=secret_hint,
                validation_time=datetime.utcnow(),
                error_message=str(e),
            )


class ComprehensiveSecretValidator:
    """Comprehensive secret validator combining format and external validation"""

    def __init__(self, config: ValidationConfig = None):
        self.config = config or ValidationConfig()
        self.format_validator = SecretFormatValidator()
        self.external_validator = ExternalAPIValidator(self.config)

        # Validation statistics
        self.stats = {
            "total_validations": 0,
            "format_validations": 0,
            "external_validations": 0,
            "cache_hits": 0,
            "validation_results": {result.value: 0 for result in ValidationResult},
        }

    def identify_secret_type(self, key: str, value: str) -> SecretType:
        """Identify secret type based on key name and value format"""
        key_lower = key.lower()

        # Check key patterns
        if "openai" in key_lower:
            return SecretType.OPENAI_API_KEY
        elif "anthropic" in key_lower:
            return SecretType.ANTHROPIC_API_KEY
        elif "deepseek" in key_lower:
            return SecretType.DEEPSEEK_API_KEY
        elif "gemini" in key_lower:
            return SecretType.GEMINI_API_KEY
        elif "huggingface" in key_lower or "hf_" in value:
            return SecretType.HUGGINGFACE_API_KEY
        elif "redis" in key_lower:
            if "redis://" in value or "rediss://" in value:
                return SecretType.REDIS_CONNECTION
            else:
                return SecretType.DATABASE_PASSWORD
        elif "qdrant" in key_lower:
            return SecretType.QDRANT_API_KEY
        elif "weaviate" in key_lower:
            return SecretType.WEAVIATE_API_KEY
        elif "portkey" in key_lower:
            return SecretType.PORTKEY_API_KEY
        elif "jwt" in key_lower or "token" in key_lower:
            if self.format_validator.validate_jwt_token(value):
                return SecretType.JWT_TOKEN

        # Check value patterns
        if value.startswith("sk-"):
            if value.startswith("sk-ant-"):
                return SecretType.ANTHROPIC_API_KEY
            else:
                return SecretType.OPENAI_API_KEY
        elif value.startswith("hf_"):
            return SecretType.HUGGINGFACE_API_KEY
        elif value.startswith("AIzaSy"):
            return SecretType.GEMINI_API_KEY
        elif "redis://" in value or "rediss://" in value:
            return SecretType.REDIS_CONNECTION

        # Default fallback
        if "password" in key_lower:
            return SecretType.DATABASE_PASSWORD
        elif "webhook" in key_lower and "secret" in key_lower:
            return SecretType.WEBHOOK_SECRET
        else:
            return SecretType.JWT_TOKEN  # Generic token type

    async def validate_secret(
        self,
        key: str,
        value: str,
        secret_type: Optional[SecretType] = None,
        force_external_validation: bool = False,
    ) -> ValidationResultData:
        """Validate a secret comprehensively"""

        # Auto-identify type if not provided
        if secret_type is None:
            secret_type = self.identify_secret_type(key, value)

        secret_hint = value[-4:] if len(value) >= 4 else "****"
        self.stats["total_validations"] += 1

        # Check cache first
        cache_key = f"{secret_type.value}:{secret_hint}"
        if self.config.cache_results:
            cached_result = self.external_validator._get_cached_result(cache_key)
            if cached_result:
                self.stats["cache_hits"] += 1
                return cached_result

        # Format validation first
        format_validator = self.format_validator.get_validator_for_type(secret_type)
        if format_validator:
            self.stats["format_validations"] += 1
            if not format_validator(value):
                result = ValidationResultData(
                    result=ValidationResult.INVALID,
                    secret_type=secret_type,
                    secret_hint=secret_hint,
                    validation_time=datetime.utcnow(),
                    error_message="Invalid format",
                )
                self._update_stats(result)
                return result

        # External validation if not format-only mode
        if not self.config.validate_format_only or force_external_validation:
            result = await self._perform_external_validation(secret_type, value)
        else:
            # Format validation passed, assume valid if we can't do external validation
            result = ValidationResultData(
                result=ValidationResult.VALID,
                secret_type=secret_type,
                secret_hint=secret_hint,
                validation_time=datetime.utcnow(),
                additional_info={"validation_type": "format_only"},
            )

        # Cache result
        if self.config.cache_results:
            self.external_validator._cache_result(cache_key, result)

        self._update_stats(result)
        return result

    async def _perform_external_validation(
        self, secret_type: SecretType, value: str
    ) -> ValidationResultData:
        """Perform external validation based on secret type"""
        self.stats["external_validations"] += 1

        async with self.external_validator:
            if secret_type == SecretType.OPENAI_API_KEY:
                return await self.external_validator.validate_openai_key(value)
            elif secret_type == SecretType.ANTHROPIC_API_KEY:
                return await self.external_validator.validate_anthropic_key(value)
            elif secret_type == SecretType.REDIS_CONNECTION:
                return await self.external_validator.validate_redis_connection(value)
            else:
                # For unsupported types, return format validation result
                secret_hint = value[-4:] if len(value) >= 4 else "****"
                return ValidationResultData(
                    result=ValidationResult.VALID,
                    secret_type=secret_type,
                    secret_hint=secret_hint,
                    validation_time=datetime.utcnow(),
                    additional_info={
                        "validation_type": "format_only",
                        "note": "External validation not implemented",
                    },
                )

    def _update_stats(self, result: ValidationResultData):
        """Update validation statistics"""
        self.stats["validation_results"][result.result.value] += 1

    async def validate_multiple_secrets(
        self, secrets: dict[str, str], batch_size: int = 5
    ) -> dict[str, ValidationResultData]:
        """Validate multiple secrets in batches"""

        results = {}
        secret_items = list(secrets.items())

        # Process in batches to avoid overwhelming external APIs
        for i in range(0, len(secret_items), batch_size):
            batch = secret_items[i : i + batch_size]

            # Validate batch concurrently
            batch_tasks = [self.validate_secret(key, value) for key, value in batch]

            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # Process batch results
            for (key, value), result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    results[key] = ValidationResultData(
                        result=ValidationResult.UNKNOWN_ERROR,
                        secret_type=self.identify_secret_type(key, value),
                        secret_hint=value[-4:] if len(value) >= 4 else "****",
                        validation_time=datetime.utcnow(),
                        error_message=str(result),
                    )
                else:
                    results[key] = result

            # Small delay between batches
            if i + batch_size < len(secret_items):
                await asyncio.sleep(self.config.retry_delay_seconds)

        return results

    def get_validation_report(self) -> dict[str, Any]:
        """Get comprehensive validation report"""
        total = self.stats["total_validations"]
        valid_count = self.stats["validation_results"][ValidationResult.VALID.value]

        return {
            "report_generated": datetime.utcnow().isoformat(),
            "total_validations": total,
            "format_validations": self.stats["format_validations"],
            "external_validations": self.stats["external_validations"],
            "cache_hits": self.stats["cache_hits"],
            "cache_hit_rate": self.stats["cache_hits"] / total if total > 0 else 0,
            "overall_validity_rate": valid_count / total if total > 0 else 0,
            "validation_results": self.stats["validation_results"],
            "configuration": {
                "timeout_seconds": self.config.timeout_seconds,
                "cache_enabled": self.config.cache_results,
                "cache_ttl_seconds": self.config.cache_ttl_seconds,
                "format_only_mode": self.config.validate_format_only,
                "rate_limit_per_hour": self.config.rate_limit_per_hour,
            },
        }

    def get_health_status(self) -> dict[str, Any]:
        """Get validator health status"""
        total = self.stats["total_validations"]
        error_count = (
            self.stats["validation_results"][ValidationResult.NETWORK_ERROR.value]
            + self.stats["validation_results"][ValidationResult.UNKNOWN_ERROR.value]
        )

        health_score = 1.0
        if total > 0:
            error_rate = error_count / total
            health_score = max(0.0, 1.0 - error_rate)

        return {
            "healthy": health_score >= 0.8,
            "health_score": health_score,
            "total_validations": total,
            "error_count": error_count,
            "error_rate": error_count / total if total > 0 else 0,
            "last_validation": datetime.utcnow().isoformat() if total > 0 else None,
        }
