"""
Unified Configuration Manager for Sophia Intel AI
Single source of truth for all configuration
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class UnifiedConfigManager:
    """
    Centralized configuration management
    Priority order:
    1. Environment variables
    2. ~/.config/sophia/env (secure storage)
    3. config/integrations/*.json files
    4. Default values
    """
    
    def __init__(self):
        self.config_dir = Path(__file__).parent
        self.secure_env_path = Path.home() / ".config/sophia/env"
        self.integrations_dir = self.config_dir / "integrations"
        self._cache = {}
        
        # Load environment in priority order
        self._load_environment()
        
    def _load_environment(self):
        """Load environment variables from secure location"""
        # First, try secure location
        if self.secure_env_path.exists():
            load_dotenv(self.secure_env_path)
            logger.info(f"Loaded secure environment from {self.secure_env_path}")
        else:
            # Create secure directory if it doesn't exist
            self.secure_env_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Look for .env.example to guide user
            example_path = Path(__file__).parent.parent / ".env.example"
            if example_path.exists():
                logger.warning(f"No secure env found. Copy {example_path} to {self.secure_env_path}")
        
        # Override with actual environment variables (highest priority)
        # This allows CI/CD and Docker to work properly
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        # Check environment first
        env_value = os.getenv(key)
        if env_value is not None:
            return self._parse_value(env_value)
        
        # Check cache
        if key in self._cache:
            return self._cache[key]
        
        return default
    
    def _parse_value(self, value: str) -> Any:
        """Parse string value to appropriate type"""
        # Handle booleans
        if value.lower() in ("true", "yes", "1"):
            return True
        elif value.lower() in ("false", "no", "0"):
            return False
        
        # Try to parse as JSON
        try:
            return json.loads(value)
        except:
            pass
        
        # Return as string
        return value
    
    def get_integration_config(self, name: str) -> Dict[str, Any]:
        """Get configuration for a specific integration"""
        cache_key = f"integration_{name}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        config = {}
        
        # Load from JSON file if exists
        json_path = self.integrations_dir / f"{name}.json"
        if json_path.exists():
            try:
                with open(json_path) as f:
                    config = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load {name} config: {e}")
        
        # Override with environment variables
        env_prefix = name.upper()
        
        # Check if integration is enabled
        enabled_key = f"{env_prefix}_ENABLED"
        if os.getenv(enabled_key):
            config["enabled"] = self.get(enabled_key, False)
        
        # Get API keys/tokens
        token_keys = [
            f"{env_prefix}_API_KEY",
            f"{env_prefix}_API_TOKEN",
            f"{env_prefix}_BOT_TOKEN",
            f"{env_prefix}_PAT_TOKEN",
            f"{env_prefix}_TOKEN"
        ]
        
        for key in token_keys:
            value = os.getenv(key)
            if value:
                config[key.lower()] = value
        
        # Special handling for Slack
        if name == "slack":
            config["bot_token"] = os.getenv("SLACK_BOT_TOKEN")
            config["app_token"] = os.getenv("SLACK_APP_TOKEN")
            config["signing_secret"] = os.getenv("SLACK_SIGNING_SECRET")
            config["client_id"] = os.getenv("SLACK_CLIENT_ID")
            config["client_secret"] = os.getenv("SLACK_CLIENT_SECRET")
        
        # Special handling for Asana
        elif name == "asana":
            config["pat_token"] = os.getenv("ASANA_PAT_TOKEN") or os.getenv("ASANA_API_TOKEN")
            config["workspace_id"] = os.getenv("ASANA_WORKSPACE_ID")
        
        # Special handling for Linear
        elif name == "linear":
            config["api_key"] = os.getenv("LINEAR_API_KEY")
            config["team_id"] = os.getenv("LINEAR_TEAM_ID")
        
        # Special handling for Airtable
        elif name == "airtable":
            config["api_key"] = os.getenv("AIRTABLE_API_KEY")
            config["base_id"] = os.getenv("AIRTABLE_BASE_ID")
        
        # Cache the config
        self._cache[cache_key] = config
        
        return config
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return {
            "postgres": {
                "url": self.get("DATABASE_URL", "postgresql://localhost:5432/sophia"),
                "pool_size": self.get("DB_POOL_SIZE", 10)
            },
            "redis": {
                "url": self.get("REDIS_URL", "redis://localhost:6379/0"),
                "max_connections": self.get("REDIS_MAX_CONNECTIONS", 50)
            },
            "weaviate": {
                "url": self.get("WEAVIATE_URL"),
                "api_key": self.get("WEAVIATE_API_KEY")
            },
            "neo4j": {
                "uri": self.get("NEO4J_URI"),
                "user": self.get("NEO4J_USER"),
                "password": self.get("NEO4J_PASSWORD")
            }
        }
    
    def get_mcp_config(self) -> Dict[str, int]:
        """Get MCP service ports configuration"""
        return {
            "memory": self.get("MCP_MEMORY_PORT", 8081),
            "filesystem": self.get("MCP_FILESYSTEM_PORT", 8082),
            "web": self.get("MCP_WEB_PORT", 8083),
            "git": self.get("MCP_GIT_PORT", 8084)
        }
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI provider configuration"""
        return {
            "openai": {
                "api_key": self.get("OPENAI_API_KEY"),
                "model": self.get("OPENAI_MODEL", "gpt-4")
            },
            "anthropic": {
                "api_key": self.get("ANTHROPIC_API_KEY"),
                "model": self.get("ANTHROPIC_MODEL", "claude-3-opus")
            }
        }
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration"""
        return {
            "host": self.get("HOST", "0.0.0.0"),
            "port": self.get("PORT", 8000),
            "workers": self.get("WORKERS", 4),
            "debug": self.get("DEBUG", False),
            "log_level": self.get("LOG_LEVEL", "INFO"),
            "cors_origins": self.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
        }
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """Get feature flags"""
        return {
            "chat": self.get("ENABLE_CHAT", True),
            "projects": self.get("ENABLE_PROJECTS", True),
            "analytics": self.get("ENABLE_ANALYTICS", True),
            "ai_insights": self.get("ENABLE_AI_INSIGHTS", True)
        }
    
    def is_integration_enabled(self, name: str) -> bool:
        """Check if an integration is enabled"""
        config = self.get_integration_config(name)
        return config.get("enabled", False)
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return issues"""
        issues = {
            "errors": [],
            "warnings": [],
            "info": []
        }
        
        # Check for secure environment
        if not self.secure_env_path.exists():
            issues["warnings"].append(f"Secure environment not found at {self.secure_env_path}")
        
        # Check for required AI keys
        if not self.get("OPENAI_API_KEY") and not self.get("ANTHROPIC_API_KEY"):
            issues["errors"].append("No AI provider API key configured")
        
        # Check integration configurations
        for integration in ["slack", "asana", "linear"]:
            config = self.get_integration_config(integration)
            if config.get("enabled"):
                # Check for required tokens
                if integration == "slack" and not config.get("bot_token"):
                    issues["errors"].append(f"Slack enabled but SLACK_BOT_TOKEN not set")
                elif integration == "asana" and not config.get("pat_token"):
                    issues["errors"].append(f"Asana enabled but ASANA_PAT_TOKEN not set")
                elif integration == "linear" and not config.get("api_key"):
                    issues["errors"].append(f"Linear enabled but LINEAR_API_KEY not set")
        
        # Check database configuration
        if not self.get("DATABASE_URL"):
            issues["warnings"].append("DATABASE_URL not configured, using default")
        
        return issues
    
    def export_safe_config(self) -> Dict[str, Any]:
        """Export configuration without sensitive values"""
        safe_config = {
            "app_name": self.get("APP_NAME", "Sophia Intel AI"),
            "environment": self.get("APP_ENV", "development"),
            "server": self.get_server_config(),
            "features": self.get_feature_flags(),
            "integrations": {},
            "mcp_ports": self.get_mcp_config()
        }
        
        # Add integration status without secrets
        for name in ["slack", "asana", "linear", "airtable"]:
            config = self.get_integration_config(name)
            safe_config["integrations"][name] = {
                "enabled": config.get("enabled", False),
                "configured": bool(self._get_integration_token(name, config))
            }
        
        return safe_config
    
    def _get_integration_token(self, name: str, config: Dict[str, Any]) -> Optional[str]:
        """Get the appropriate token for an integration"""
        if name == "slack":
            return config.get("bot_token")
        elif name == "asana":
            return config.get("pat_token")
        elif name == "linear":
            return config.get("api_key")
        elif name == "airtable":
            return config.get("api_key")
        return None


# Singleton instance
_instance = None

def get_config_manager() -> UnifiedConfigManager:
    """Get or create the singleton config manager"""
    global _instance
    if _instance is None:
        _instance = UnifiedConfigManager()
    return _instance

# Convenience function for backward compatibility
def get_config() -> UnifiedConfigManager:
    """Alias for get_config_manager"""
    return get_config_manager()