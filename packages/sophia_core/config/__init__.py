"""
Configuration Management Module

Provides centralized configuration management with environment variables,
Pydantic settings validation, and helper utilities for feature flags and provider selection.
"""

from .env import (
    Settings,
    LLMSettings, 
    DatabaseSettings,
    FeatureFlagSettings,
    get_settings,
    load_dotenv_safe
)

from .helpers import (
    is_provider_enabled,
    select_vector_store,
    redact_sensitive_data,
    get_config_value,
    validate_config
)

__all__ = [
    # Environment and settings
    "Settings",
    "LLMSettings",
    "DatabaseSettings", 
    "FeatureFlagSettings",
    "get_settings",
    "load_dotenv_safe",
    
    # Helper functions
    "is_provider_enabled",
    "select_vector_store",
    "redact_sensitive_data", 
    "get_config_value",
    "validate_config"
]