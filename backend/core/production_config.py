"""
Production Configuration Module
Implements secure configuration management with Pulumi ESC integration
Following GitHub Organization Secrets → Pulumi ESC → Application pattern
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProductionConfig:
    """Production configuration with secure secret management"""

    # Application settings
    environment: str
    debug: bool
    log_level: str

    # Server configuration
    host: str
    port: int
    workers: int

    # Security settings
    cors_origins: list
    trusted_hosts: list
    rate_limit_enabled: bool

    # AI Framework settings
    agno_log_level: str
    langgraph_cache_size: int
    max_agent_workers: int

    # Database configuration (from Pulumi ESC)
    database_url: Optional[str] = None
    redis_url: Optional[str] = None

    # External API keys (from Pulumi ESC)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # Monitoring and observability
    enable_metrics: bool = True
    enable_tracing: bool = True
    metrics_port: int = 9090

class SecureConfigManager:
    """Manages secure configuration with Pulumi ESC integration"""

    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self._config_cache: Optional[ProductionConfig] = None

    def get_config(self) -> ProductionConfig:
        """Get production configuration with secure secret management"""

        if self._config_cache is not None:
            return self._config_cache

        logger.info(f"Loading configuration for environment: {self.environment}")

        # Load configuration based on environment
        if self.environment == "production":
            config = self._load_production_config()
        elif self.environment == "staging":
            config = self._load_staging_config()
        else:
            config = self._load_development_config()

        # Validate configuration
        self._validate_config(config)

        # Cache configuration
        self._config_cache = config

        logger.info("Configuration loaded successfully")
        return config

    def _load_production_config(self) -> ProductionConfig:
        """Load production configuration with Pulumi ESC secrets"""

        return ProductionConfig(
            # Application settings
            environment="production",
            debug=False,
            log_level=os.getenv("LOG_LEVEL", "INFO"),

            # Server configuration
            host=os.getenv("SOPHIA_HOST", "${BIND_IP}"),
            port=int(os.getenv("SOPHIA_PORT", "8000")),
            workers=int(os.getenv("SOPHIA_WORKERS", "4")),

            # Security settings
            cors_origins=self._parse_list(os.getenv("CORS_ORIGINS", "")),
            trusted_hosts=self._parse_list(os.getenv("TRUSTED_HOSTS", "sophia-ai.sophia-intel.ai")),
            rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",

            # AI Framework settings
            agno_log_level=os.getenv("AGNO_LOG_LEVEL", "INFO"),
            langgraph_cache_size=int(os.getenv("LANGGRAPH_CACHE_SIZE", "1000")),
            max_agent_workers=int(os.getenv("MAX_AGENT_WORKERS", "10")),

            # Database configuration (from Pulumi ESC)
            database_url=os.getenv("DATABASE_URL"),
            redis_url=os.getenv("REDIS_URL"),

            # External API keys (from Pulumi ESC via GitHub Secrets)
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("OPENROUTER_API_KEY"),

            # Monitoring
            enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true",
            enable_tracing=os.getenv("ENABLE_TRACING", "true").lower() == "true",
            metrics_port=int(os.getenv("METRICS_PORT", "9090"))
        )

    def _load_staging_config(self) -> ProductionConfig:
        """Load staging configuration"""

        return ProductionConfig(
            # Application settings
            environment="staging",
            debug=True,
            log_level=os.getenv("LOG_LEVEL", "DEBUG"),

            # Server configuration
            host=os.getenv("SOPHIA_HOST", "${BIND_IP}"),
            port=int(os.getenv("SOPHIA_PORT", "8000")),
            workers=int(os.getenv("SOPHIA_WORKERS", "2")),

            # Security settings
            cors_origins=["*"],  # More permissive for staging
            trusted_hosts=["*"],
            rate_limit_enabled=False,

            # AI Framework settings
            agno_log_level=os.getenv("AGNO_LOG_LEVEL", "DEBUG"),
            langgraph_cache_size=int(os.getenv("LANGGRAPH_CACHE_SIZE", "500")),
            max_agent_workers=int(os.getenv("MAX_AGENT_WORKERS", "5")),

            # Database configuration
            database_url=os.getenv("DATABASE_URL"),
            redis_url=os.getenv("REDIS_URL"),

            # External API keys
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("OPENROUTER_API_KEY"),

            # Monitoring
            enable_metrics=True,
            enable_tracing=True,
            metrics_port=int(os.getenv("METRICS_PORT", "9090"))
        )

    def _load_development_config(self) -> ProductionConfig:
        """Load development configuration"""

        return ProductionConfig(
            # Application settings
            environment="development",
            debug=True,
            log_level=os.getenv("LOG_LEVEL", "DEBUG"),

            # Server configuration
            host=os.getenv("SOPHIA_HOST", "${BIND_IP}"),
            port=int(os.getenv("SOPHIA_PORT", "8000")),
            workers=1,  # Single worker for development

            # Security settings
            cors_origins=["*"],  # Permissive for development
            trusted_hosts=["*"],
            rate_limit_enabled=False,

            # AI Framework settings
            agno_log_level=os.getenv("AGNO_LOG_LEVEL", "DEBUG"),
            langgraph_cache_size=int(os.getenv("LANGGRAPH_CACHE_SIZE", "100")),
            max_agent_workers=int(os.getenv("MAX_AGENT_WORKERS", "2")),

            # Database configuration (optional for development)
            database_url=os.getenv("DATABASE_URL", "sqlite:///./sophia_dev.db"),
            redis_url=os.getenv("REDIS_URL", "${REDIS_URL}"),

            # External API keys (optional for development)
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("OPENROUTER_API_KEY"),

            # Monitoring
            enable_metrics=False,  # Disabled for development
            enable_tracing=False,
            metrics_port=int(os.getenv("METRICS_PORT", "9090"))
        )

    def _parse_list(self, value: str) -> list:
        """Parse comma-separated string into list"""
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    def _validate_config(self, config: ProductionConfig) -> None:
        """Validate configuration for production readiness"""

        if config.environment == "production":
            # Production-specific validations
            if not config.trusted_hosts or config.trusted_hosts == ["*"]:
                logger.warning("Production should have specific trusted hosts configured")

            if config.debug:
                logger.warning("Debug mode should be disabled in production")

            if not config.rate_limit_enabled:
                logger.warning("Rate limiting should be enabled in production")

            # Validate required secrets are available
            required_secrets = []
            if not config.openai_api_key:
                required_secrets.append("OPENAI_API_KEY")

            if required_secrets:
                logger.warning(f"Missing required secrets: {required_secrets}")

        # General validations
        if config.port < 1 or config.port > 65535:
            raise ValueError(f"Invalid port number: {config.port}")

        if config.workers < 1:
            raise ValueError(f"Invalid worker count: {config.workers}")

        logger.info("Configuration validation completed")

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Securely retrieve secret from environment (populated by Pulumi ESC)"""

        value = os.getenv(key, default)

        if value:
            logger.debug(f"Secret '{key}' retrieved successfully")
        else:
            logger.warning(f"Secret '{key}' not found")

        return value

    def validate_secrets(self) -> Dict[str, bool]:
        """Validate that required secrets are available"""

        required_secrets = [
            "OPENAI_API_KEY",
            "OPENROUTER_API_KEY",
            "DATABASE_URL",
            "REDIS_URL"
        ]

        results = {}
        for secret in required_secrets:
            results[secret] = bool(os.getenv(secret))

        return results

# Global configuration manager instance
config_manager = SecureConfigManager()

def get_production_config() -> ProductionConfig:
    """Get production configuration instance"""
    return config_manager.get_config()

def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get secret value securely"""
    return config_manager.get_secret(key, default)

def validate_production_secrets() -> Dict[str, bool]:
    """Validate production secrets are available"""
    return config_manager.validate_secrets()

__all__ = [
    "ProductionConfig",
    "SecureConfigManager", 
    "get_production_config",
    "get_secret",
    "validate_production_secrets"
]
