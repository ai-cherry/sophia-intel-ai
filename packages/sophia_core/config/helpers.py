"""
Configuration Helper Functions

Utility functions for checking provider availability, selecting vector stores,
redacting sensitive data, and validating configuration values.
"""

import logging
import re
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from .env import (
    get_database_settings,
    get_feature_flags,
    get_llm_settings,
    get_settings,
)

logger = logging.getLogger(__name__)


class VectorStoreType(Enum):
    """Supported vector store types."""

    WEAVIATE = "weaviate"
    CHROMADB = "chromadb"
    PINECONE = "pinecone"
    QDRANT = "qdrant"


class LLMProvider(Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    TOGETHER = "together"
    GEMINI = "gemini"


def is_provider_enabled(provider: Union[str, LLMProvider]) -> bool:
    """
    Check if an LLM provider is enabled and properly configured.

    Args:
        provider: Provider name or enum value

    Returns:
        bool: True if provider is enabled and has valid configuration
    """
    try:
        # Convert to string if enum
        provider_name = (
            provider.value
            if isinstance(provider, LLMProvider)
            else str(provider).lower()
        )

        # Check if provider is in enabled list
        feature_flags = get_feature_flags()
        if provider_name not in feature_flags.enabled_llm_providers:
            logger.debug(f"Provider {provider_name} not in enabled providers list")
            return False

        # Check if provider has valid API key
        llm_settings = get_llm_settings()
        api_key_attr = f"{provider_name}_api_key"

        if hasattr(llm_settings, api_key_attr):
            api_key = getattr(llm_settings, api_key_attr)
            if api_key is None:
                logger.warning(
                    f"Provider {provider_name} enabled but no API key configured"
                )
                return False

            # Check if key is not empty
            key_value = (
                api_key.get_secret_value()
                if hasattr(api_key, "get_secret_value")
                else api_key
            )
            if not key_value or key_value.strip() == "":
                logger.warning(f"Provider {provider_name} has empty API key")
                return False

            return True
        else:
            logger.error(f"Unknown provider: {provider_name}")
            return False

    except Exception as e:
        logger.error(f"Error checking provider {provider}: {e}")
        return False


def select_vector_store() -> VectorStoreType:
    """
    Select and validate the configured vector store.

    Returns:
        VectorStoreType: The configured vector store type

    Raises:
        ValueError: If vector store type is invalid or not configured
    """
    try:
        db_settings = get_database_settings()
        vector_store_type = db_settings.vector_store_type.lower()

        # Validate vector store type
        try:
            return VectorStoreType(vector_store_type)
        except ValueError:
            available_types = [store.value for store in VectorStoreType]
            raise ValueError(
                f"Invalid vector store type '{vector_store_type}'. "
                f"Available types: {available_types}"
            )

    except Exception as e:
        logger.error(f"Error selecting vector store: {e}")
        raise


def get_enabled_providers() -> List[LLMProvider]:
    """
    Get list of enabled and properly configured LLM providers.

    Returns:
        List[LLMProvider]: List of available providers
    """
    enabled_providers = []

    for provider in LLMProvider:
        if is_provider_enabled(provider):
            enabled_providers.append(provider)

    logger.info(f"Enabled LLM providers: {[p.value for p in enabled_providers]}")
    return enabled_providers


def get_primary_provider() -> Optional[LLMProvider]:
    """
    Get the primary (first available) LLM provider.

    Returns:
        Optional[LLMProvider]: Primary provider or None if none available
    """
    enabled_providers = get_enabled_providers()
    if enabled_providers:
        primary = enabled_providers[0]
        logger.debug(f"Primary LLM provider: {primary.value}")
        return primary

    logger.warning("No enabled LLM providers found")
    return None


# Sensitive data patterns for redaction
SENSITIVE_PATTERNS = {
    "api_key": re.compile(
        r'(api[_-]?key|token|secret)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})',
        re.IGNORECASE,
    ),
    "password": re.compile(
        r'(password|passwd|pwd)["\']?\s*[:=]\s*["\']?([^"\'\s]{3,})', re.IGNORECASE
    ),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "phone": re.compile(r"\b\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "ip_address": re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"),
    "jwt": re.compile(r"eyJ[A-Za-z0-9_=-]+\.eyJ[A-Za-z0-9_=-]+\.[A-Za-z0-9_=-]+"),
}


def redact_sensitive_data(
    data: Union[str, Dict[str, Any]],
    patterns: Optional[Dict[str, re.Pattern]] = None,
    replacement: str = "[REDACTED]",
) -> Union[str, Dict[str, Any]]:
    """
    Redact sensitive information from strings or dictionaries.

    Args:
        data: String or dictionary to redact
        patterns: Custom regex patterns for redaction
        replacement: Replacement string for sensitive data

    Returns:
        Union[str, Dict[str, Any]]: Data with sensitive information redacted
    """
    if patterns is None:
        patterns = SENSITIVE_PATTERNS

    try:
        if isinstance(data, str):
            return _redact_string(data, patterns, replacement)
        elif isinstance(data, dict):
            return _redact_dict(data, patterns, replacement)
        elif isinstance(data, (list, tuple)):
            return type(data)(
                [redact_sensitive_data(item, patterns, replacement) for item in data]
            )
        else:
            return data
    except Exception as e:
        logger.error(f"Error redacting sensitive data: {e}")
        return data


def _redact_string(text: str, patterns: Dict[str, re.Pattern], replacement: str) -> str:
    """Redact sensitive patterns from a string."""
    for pattern_name, pattern in patterns.items():
        if pattern_name in ["api_key", "password"]:
            # For key-value patterns, only redact the value part
            text = pattern.sub(lambda m: f"{m.group(1)}={replacement}", text)
        else:
            # For other patterns, redact the entire match
            text = pattern.sub(replacement, text)

    return text


def _redact_dict(
    data: Dict[str, Any], patterns: Dict[str, re.Pattern], replacement: str
) -> Dict[str, Any]:
    """Redact sensitive patterns from a dictionary."""
    redacted = {}

    for key, value in data.items():
        # Check if key name suggests sensitive data
        key_lower = key.lower()
        if any(
            sensitive in key_lower
            for sensitive in ["key", "token", "secret", "password", "passwd"]
        ):
            redacted[key] = replacement
        elif isinstance(value, str):
            redacted[key] = _redact_string(value, patterns, replacement)
        elif isinstance(value, dict):
            redacted[key] = _redact_dict(value, patterns, replacement)
        elif isinstance(value, (list, tuple)):
            redacted[key] = type(value)(
                [redact_sensitive_data(item, patterns, replacement) for item in value]
            )
        else:
            redacted[key] = value

    return redacted


def get_config_value(
    key: str,
    default: Any = None,
    required: bool = False,
    validator: Optional[Callable[[Any], bool]] = None,
) -> Any:
    """
    Get a configuration value with validation.

    Args:
        key: Configuration key (dot-separated for nested values)
        default: Default value if key not found
        required: Whether the key is required
        validator: Optional validation function

    Returns:
        Any: Configuration value

    Raises:
        ValueError: If required key is missing or validation fails
    """
    try:
        settings = get_settings()

        # Handle dot-separated keys for nested access
        keys = key.split(".")
        value = settings

        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            elif isinstance(value, dict) and k in value:
                value = value[k]
            else:
                if required:
                    raise ValueError(f"Required configuration key '{key}' not found")
                return default

        # Apply validator if provided
        if validator and not validator(value):
            raise ValueError(f"Configuration value for '{key}' failed validation")

        return value

    except Exception as e:
        logger.error(f"Error getting config value '{key}': {e}")
        if required:
            raise
        return default


def validate_config() -> List[str]:
    """
    Validate the current configuration and return list of issues.

    Returns:
        List[str]: List of validation issues (empty if all valid)
    """
    issues = []

    try:
        settings = get_settings()

        # Check required settings
        if not settings.secret_key:
            issues.append("SECRET_KEY is required but not set")

        # Validate database settings
        db_settings = settings.database
        if not db_settings.postgres_password:
            issues.append("POSTGRES_PASSWORD is required but not set")

        # Check if at least one LLM provider is enabled
        enabled_providers = get_enabled_providers()
        if not enabled_providers:
            issues.append("No LLM providers are properly configured and enabled")

        # Validate vector store configuration
        try:
            select_vector_store()
        except ValueError as e:
            issues.append(f"Vector store configuration error: {e}")

        # Check feature flag consistency
        feature_flags = settings.features
        if feature_flags.enable_swarm_mode and not feature_flags.enable_memory_system:
            issues.append("Swarm mode requires memory system to be enabled")

        if (
            feature_flags.enable_distributed_mode
            and not feature_flags.enable_swarm_mode
        ):
            issues.append("Distributed mode requires swarm mode to be enabled")

        # Environment-specific validations
        if settings.is_production:
            if settings.debug:
                issues.append("Debug mode should not be enabled in production")

            if settings.log_level == "DEBUG":
                issues.append("Debug logging should not be enabled in production")

        logger.info(f"Configuration validation completed with {len(issues)} issues")
        return issues

    except Exception as e:
        logger.error(f"Error validating configuration: {e}")
        return [f"Configuration validation failed: {e}"]


def get_provider_config(provider: Union[str, LLMProvider]) -> Dict[str, Any]:
    """
    Get configuration for a specific LLM provider.

    Args:
        provider: Provider name or enum

    Returns:
        Dict[str, Any]: Provider configuration

    Raises:
        ValueError: If provider is not enabled or configured
    """
    provider_name = (
        provider.value if isinstance(provider, LLMProvider) else str(provider).lower()
    )

    if not is_provider_enabled(provider_name):
        raise ValueError(
            f"Provider {provider_name} is not enabled or properly configured"
        )

    llm_settings = get_llm_settings()

    config = {
        "name": provider_name,
        "api_key": getattr(llm_settings, f"{provider_name}_api_key"),
        "base_url": getattr(llm_settings, f"{provider_name}_base_url"),
        "timeout": llm_settings.default_timeout,
        "max_tokens": llm_settings.default_max_tokens,
        "temperature": llm_settings.default_temperature,
    }

    # Add provider-specific configurations
    if provider_name == LLMProvider.OPENAI.value:
        config["organization"] = llm_settings.openai_org_id

    return config
