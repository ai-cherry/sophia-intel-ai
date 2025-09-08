"\n🏹 Sophia AI - Unified Environment Configuration\nPhase 2: Environment Configuration Unification\nBuilt on Phase 1 success (unified production entry point)\n"

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class UnifiedEnvironmentConfig:
    """Unified environment configuration management"""

    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.config_cache: dict[str, Any] = {}
        self._load_environment_config()

    def _load_environment_config(self):
        """Load environment-specific configuration"""
        config_file = f"config/{self.environment}/.env.{self.environment}"
        config_path = Path(config_file)
        if config_path.exists():
            logger.info(f"✅ Loading environment config: {config_file}")
        else:
            logger.warning(f"⚠️  Environment config not found: {config_file}")

    def get_database_url(self) -> str:
        """Get unified database URL"""
        return os.getenv(
            "POSTGRES_URL",
            f"postgresql://${DB_USER}:${DB_PASSWORD}@{os.getenv('POSTGRES_HOST', 'postgres')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'sophia_production')}",
        )

    def get_redis_url(self) -> str:
        """Get unified Redis URL"""
        return os.getenv(
            "REDIS_URL",
            f"redis://{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', '6379')}/{os.getenv('REDIS_DB', '0')}",
        )

    def get_mcp_server_config(self) -> dict[str, Any]:
        """Get MCP server configuration"""
        return {
            "host": os.getenv("MCP_HOST", "mcp-server"),
            "base_port": int(os.getenv("MCP_BASE_PORT", "9000")),
            "service_host": os.getenv("SERVICE_HOST", "${BIND_IP}"),
        }

    def get_ai_service_config(self) -> dict[str, str]:
        """Get AI service configuration"""
        return {
            "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
            "anthropic_api_key": os.getenv("OPENROUTER_API_KEY", ""),
            "qdrant_url": os.getenv("QDRANT_URL", "http://qdrant:6333"),
            "qdrant_api_key": os.getenv("QDRANT_API_KEY", ""),
        }

    def get_business_integration_config(self) -> dict[str, str]:
        """Get business integration configuration"""
        return {
            "github_token": os.getenv("GITHUB_TOKEN", ""),
            "linear_api_key": os.getenv("LINEAR_API_KEY", ""),
            "notion_api_token": os.getenv("NOTION_API_TOKEN", ""),
            "asana_access_token": os.getenv("ASANA_ACCESS_TOKEN", ""),
            "slack_bot_token": os.getenv("SLACK_BOT_TOKEN", ""),
            "hubspot_api_key": os.getenv("HUBSPOT_API_KEY", ""),
            "gong_api_key": os.getenv("GONG_API_KEY", ""),
        }

    def get_api_config(self) -> dict[str, Any]:
        """Get API configuration"""
        return {
            "host": os.getenv("API_HOST", "${BIND_IP}"),
            "port": int(os.getenv("API_PORT", "8080")),
            "workers": int(os.getenv("API_WORKERS", "4")),
            "frontend_url": os.getenv("FRONTEND_URL", "https://www.sophia-intel.ai"),
        }

    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == "development"


config = UnifiedEnvironmentConfig()
