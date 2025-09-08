"""
Environment Configuration Module

Handles loading environment variables and Pydantic settings validation
for LLM providers, databases, and feature flags.
"""

import logging
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Union

from dotenv import load_dotenv
from pydantic import BaseSettings, Field, SecretStr, validator

logger = logging.getLogger(__name__)


def load_dotenv_safe(dotenv_path: Optional[Union[str, Path]] = None) -> bool:
    """
    Safely load environment variables from .env file.
    
    Args:
        dotenv_path: Path to .env file. If None, looks for .env in current directory.
        
    Returns:
        bool: True if .env file was loaded successfully, False otherwise.
    """
    try:
        if dotenv_path is None:
            # Look for .env in current working directory and parent directories
            current_path = Path.cwd()
            for path in [current_path] + list(current_path.parents):
                env_file = path / ".env"
                if env_file.exists():
                    dotenv_path = env_file
                    break

        if dotenv_path and Path(dotenv_path).exists():
            load_dotenv(dotenv_path)
            logger.info(f"Loaded environment variables from {dotenv_path}")
            return True
        else:
            logger.warning("No .env file found - using system environment variables only")
            return False
    except Exception as e:
        logger.error(f"Error loading .env file: {e}")
        return False


class LLMSettings(BaseSettings):
    """LLM Provider Configuration Settings."""

    # OpenAI
    openai_api_key: Optional[SecretStr] = Field(None, env="OPENAI_API_KEY")
    openai_org_id: Optional[str] = Field(None, env="OPENAI_ORG_ID")
    openai_base_url: Optional[str] = Field("https://api.openai.com/v1", env="OPENAI_BASE_URL")

    # Anthropic
    anthropic_api_key: Optional[SecretStr] = Field(None, env="ANTHROPIC_API_KEY")
    anthropic_base_url: Optional[str] = Field("https://api.anthropic.com", env="ANTHROPIC_BASE_URL")

    # OpenRouter
    openrouter_api_key: Optional[SecretStr] = Field(None, env="OPENROUTER_API_KEY")
    openrouter_base_url: Optional[str] = Field("https://openrouter.ai/api/v1", env="OPENROUTER_BASE_URL")

    # Together AI
    together_api_key: Optional[SecretStr] = Field(None, env="TOGETHER_API_KEY")
    together_base_url: Optional[str] = Field("https://api.together.xyz/v1", env="TOGETHER_BASE_URL")

    # Gemini
    gemini_api_key: Optional[SecretStr] = Field(None, env="GEMINI_API_KEY")
    gemini_base_url: Optional[str] = Field("https://generativelanguage.googleapis.com/v1", env="GEMINI_BASE_URL")

    # Default model configurations
    default_model: str = Field("gpt-3.5-turbo", env="DEFAULT_LLM_MODEL")
    default_temperature: float = Field(0.7, env="DEFAULT_TEMPERATURE", ge=0.0, le=2.0)
    default_max_tokens: int = Field(4096, env="DEFAULT_MAX_TOKENS", gt=0)
    default_timeout: int = Field(30, env="DEFAULT_LLM_TIMEOUT", gt=0)

    # Rate limiting
    rate_limit_requests_per_minute: int = Field(60, env="RATE_LIMIT_RPM", gt=0)
    rate_limit_tokens_per_minute: int = Field(90000, env="RATE_LIMIT_TPM", gt=0)

    class Config:
        env_prefix = "LLM_"
        case_sensitive = False


class DatabaseSettings(BaseSettings):
    """Database Configuration Settings."""

    # PostgreSQL
    postgres_host: str = Field("localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(5432, env="POSTGRES_PORT", gt=0, le=65535)
    postgres_db: str = Field("sophia", env="POSTGRES_DB")
    postgres_user: str = Field("sophia_user", env="POSTGRES_USER")
    postgres_password: SecretStr = Field(..., env="POSTGRES_PASSWORD")
    postgres_ssl_mode: str = Field("prefer", env="POSTGRES_SSL_MODE")

    # Redis
    redis_host: str = Field("localhost", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT", gt=0, le=65535)
    redis_db: int = Field(0, env="REDIS_DB", ge=0)
    redis_password: Optional[SecretStr] = Field(None, env="REDIS_PASSWORD")

    # Vector Store (Weaviate/ChromaDB)
    vector_store_type: str = Field("weaviate", env="VECTOR_STORE_TYPE")
    vector_store_url: str = Field("http://localhost:8080", env="VECTOR_STORE_URL")
    vector_store_api_key: Optional[SecretStr] = Field(None, env="VECTOR_STORE_API_KEY")

    # Connection pooling
    max_pool_size: int = Field(20, env="DB_MAX_POOL_SIZE", gt=0)
    pool_timeout: int = Field(30, env="DB_POOL_TIMEOUT", gt=0)
    pool_recycle: int = Field(3600, env="DB_POOL_RECYCLE", gt=0)

    @validator("vector_store_type")
    def validate_vector_store_type(cls, v):
        allowed_types = ["weaviate", "chromadb", "pinecone", "qdrant"]
        if v.lower() not in allowed_types:
            raise ValueError(f"vector_store_type must be one of {allowed_types}")
        return v.lower()

    @property
    def postgres_url(self) -> str:
        """Generate PostgreSQL connection URL."""
        password = self.postgres_password.get_secret_value()
        return f"postgresql://{self.postgres_user}:{password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}?sslmode={self.postgres_ssl_mode}"

    @property
    def redis_url(self) -> str:
        """Generate Redis connection URL."""
        if self.redis_password:
            password = self.redis_password.get_secret_value()
            return f"redis://:{password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    class Config:
        env_prefix = "DB_"
        case_sensitive = False


class FeatureFlagSettings(BaseSettings):
    """Feature Flag Configuration Settings."""

    # Core features
    enable_memory_system: bool = Field(True, env="ENABLE_MEMORY_SYSTEM")
    enable_tool_calling: bool = Field(True, env="ENABLE_TOOL_CALLING")
    enable_swarm_mode: bool = Field(False, env="ENABLE_SWARM_MODE")
    enable_distributed_mode: bool = Field(False, env="ENABLE_DISTRIBUTED_MODE")

    # Observability
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")
    enable_tracing: bool = Field(False, env="ENABLE_TRACING")
    enable_debug_logging: bool = Field(False, env="ENABLE_DEBUG_LOGGING")

    # Security
    enable_api_key_rotation: bool = Field(True, env="ENABLE_API_KEY_ROTATION")
    enable_request_validation: bool = Field(True, env="ENABLE_REQUEST_VALIDATION")
    enable_rate_limiting: bool = Field(True, env="ENABLE_RATE_LIMITING")

    # Performance
    enable_caching: bool = Field(True, env="ENABLE_CACHING")
    enable_connection_pooling: bool = Field(True, env="ENABLE_CONNECTION_POOLING")
    enable_async_processing: bool = Field(True, env="ENABLE_ASYNC_PROCESSING")

    # Providers
    enabled_llm_providers: List[str] = Field(
        default=["openai", "anthropic"],
        env="ENABLED_LLM_PROVIDERS"
    )

    @validator("enabled_llm_providers", pre=True)
    def parse_providers_list(cls, v):
        if isinstance(v, str):
            return [provider.strip().lower() for provider in v.split(",")]
        return [provider.lower() for provider in v]

    class Config:
        env_prefix = "FEATURE_"
        case_sensitive = False


class Settings(BaseSettings):
    """Main Application Settings."""

    # Application
    app_name: str = Field("Sophia Intelligence AI", env="APP_NAME")
    app_version: str = Field("1.0.0", env="APP_VERSION")
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")

    # API
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT", gt=0, le=65535)
    api_prefix: str = Field("/api/v1", env="API_PREFIX")

    # Security
    secret_key: SecretStr = Field(..., env="SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(1440, env="JWT_EXPIRE_MINUTES", gt=0)  # 24 hours

    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")
    log_file: Optional[str] = Field(None, env="LOG_FILE")

    # Nested settings
    llm: LLMSettings = LLMSettings()
    database: DatabaseSettings = DatabaseSettings()
    features: FeatureFlagSettings = FeatureFlagSettings()

    @validator("environment")
    def validate_environment(cls, v):
        allowed_envs = ["development", "testing", "staging", "production"]
        if v.lower() not in allowed_envs:
            raise ValueError(f"environment must be one of {allowed_envs}")
        return v.lower()

    @validator("log_level")
    def validate_log_level(cls, v):
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"log_level must be one of {allowed_levels}")
        return v.upper()

    @validator("log_format")
    def validate_log_format(cls, v):
        allowed_formats = ["json", "text"]
        if v.lower() not in allowed_formats:
            raise ValueError(f"log_format must be one of {allowed_formats}")
        return v.lower()

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    class Config:
        case_sensitive = False
        # Load from .env file by default
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
_settings: Optional[Settings] = None


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings instance.
    
    Returns:
        Settings: Validated application settings.
    """
    global _settings

    if _settings is None:
        # Load environment variables first
        load_dotenv_safe()

        try:
            _settings = Settings()
            logger.info(f"Settings loaded successfully for environment: {_settings.environment}")
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            raise

    return _settings


def reload_settings() -> Settings:
    """
    Force reload of settings (clears cache).
    
    Returns:
        Settings: Newly loaded settings instance.
    """
    global _settings
    _settings = None
    get_settings.cache_clear()
    return get_settings()


# Export commonly used settings getters
def get_llm_settings() -> LLMSettings:
    """Get LLM configuration settings."""
    return get_settings().llm


def get_database_settings() -> DatabaseSettings:
    """Get database configuration settings."""
    return get_settings().database


def get_feature_flags() -> FeatureFlagSettings:
    """Get feature flag settings."""
    return get_settings().features
