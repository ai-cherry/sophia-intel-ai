"""
Sophia Intel AI - Unified Configuration Management

This module provides centralized configuration management using Pydantic BaseSettings
with environment variable support, validation, and service URL generation.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

try:
    from pydantic import BaseSettings, Field, validator, root_validator
    from pydantic.env_settings import SettingsSourceCallable
    PYDANTIC_V2 = False
except ImportError:
    try:
        from pydantic_settings import BaseSettings, SettingsConfigDict
        from pydantic import Field, field_validator
        from pydantic.fields import FieldInfo
        # Pydantic v2 compatibility
        validator = field_validator
        root_validator = field_validator  
        SettingsSourceCallable = None  # Not used in v2
        PYDANTIC_V2 = True
    except ImportError:
        raise ImportError("pydantic or pydantic-settings is required. Install with: pip install pydantic-settings")

from .service_registry import ServiceRegistry, ServiceType

logger = logging.getLogger(__name__)


class SophiaConfig(BaseSettings):
    """
    Unified configuration for Sophia Intel AI.
    
    This configuration class uses Pydantic BaseSettings to automatically
    load values from environment variables with proper validation and
    type conversion.
    """
    
    # =====================================
    # CORE APPLICATION SETTINGS
    # =====================================
    app_name: str = Field(default="Sophia Intel AI", env="APP_NAME")
    app_env: str = Field(default="development", env="APP_ENV")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # =====================================
    # SERVICE PORTS
    # =====================================
    # Core Services
    unified_api_port: int = Field(default=8000, env="SOPHIA_API_PORT")
    agent_ui_port: int = Field(default=3000, env="SOPHIA_UI_PORT")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    
    # MCP Services
    mcp_memory_port: int = Field(default=8081, env="MCP_MEMORY_PORT")
    mcp_filesystem_port: int = Field(default=8082, env="MCP_FILESYSTEM_PORT")
    mcp_web_port: int = Field(default=8083, env="MCP_WEB_PORT")
    mcp_git_port: int = Field(default=8084, env="MCP_GIT_PORT")
    
    # Vector Databases
    weaviate_port: int = Field(default=8080, env="WEAVIATE_PORT")
    neo4j_port: int = Field(default=7687, env="NEO4J_PORT")
    
    # Development Services
    jupyter_port: int = Field(default=8888, env="JUPYTER_PORT")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    grafana_port: int = Field(default=3001, env="GRAFANA_PORT")
    
    # Proxy Services
    nginx_proxy_port: int = Field(default=80, env="NGINX_PORT")
    traefik_port: int = Field(default=8088, env="TRAEFIK_PORT")
    
    # =====================================
    # HOST CONFIGURATION
    # =====================================
    default_host: str = Field(default="localhost", env="DEFAULT_HOST")
    api_host: str = Field(default="0.0.0.0", env="HOST")
    
    # =====================================
    # DATABASE CONFIGURATION
    # =====================================
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/sophia",
        env="DATABASE_URL"
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    
    # Vector Databases
    weaviate_url: str = Field(
        default="http://localhost:8080",
        env="WEAVIATE_URL"
    )
    weaviate_api_key: Optional[str] = Field(default=None, env="WEAVIATE_API_KEY")
    
    neo4j_uri: str = Field(
        default="bolt://localhost:7687",
        env="NEO4J_URI"
    )
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: Optional[str] = Field(default=None, env="NEO4J_PASSWORD")
    
    # =====================================
    # AI PROVIDER CONFIGURATION
    # =====================================
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # AIMLAPI Configuration
    aimlapi_api_key: Optional[str] = Field(default=None, env="AIMLAPI_API_KEY")
    aimlapi_base: str = Field(
        default="https://api.aimlapi.com/v1",
        env="AIMLAPI_BASE"
    )
    aimlapi_timeout: int = Field(default=30, env="AIMLAPI_TIMEOUT")
    aimlapi_max_retries: int = Field(default=3, env="AIMLAPI_MAX_RETRIES")
    aiml_enhanced_enabled: bool = Field(default=True, env="AIML_ENHANCED_ENABLED")
    
    # Legacy local proxy configuration removed — Portkey is the only gateway
    
    # Portkey Configuration
    portkey_api_key: Optional[str] = Field(default=None, env="PORTKEY_API_KEY")
    portkey_base_url: str = Field(
        default="https://api.portkey.ai/v1",
        env="PORTKEY_BASE_URL"
    )
    
    # =====================================
    # INTEGRATION CONFIGURATION
    # =====================================
    # Slack
    slack_enabled: bool = Field(default=False, env="SLACK_ENABLED")
    slack_bot_token: Optional[str] = Field(default=None, env="SLACK_BOT_TOKEN")
    slack_app_token: Optional[str] = Field(default=None, env="SLACK_APP_TOKEN")
    slack_signing_secret: Optional[str] = Field(default=None, env="SLACK_SIGNING_SECRET")
    
    # Asana
    asana_enabled: bool = Field(default=False, env="ASANA_ENABLED")
    asana_pat_token: Optional[str] = Field(default=None, env="ASANA_PAT_TOKEN")
    asana_workspace_id: Optional[str] = Field(default=None, env="ASANA_WORKSPACE_ID")
    
    # Linear
    linear_enabled: bool = Field(default=False, env="LINEAR_ENABLED")
    linear_api_key: Optional[str] = Field(default=None, env="LINEAR_API_KEY")
    linear_team_id: Optional[str] = Field(default=None, env="LINEAR_TEAM_ID")
    
    # GitHub
    github_enabled: bool = Field(default=False, env="GITHUB_ENABLED")
    github_vk: Optional[str] = Field(default=None, env="GITHUB_VK")
    
    # =====================================
    # WORKSPACE CONFIGURATION
    # =====================================
    workspace_path: str = Field(
        default="/Users/lynnmusil/sophia-intel-ai",
        env="WORKSPACE_PATH"
    )
    workspace_name: str = Field(default="sophia", env="WORKSPACE_NAME")
    
    # =====================================
    # SECURITY CONFIGURATION
    # =====================================
    jwt_secret: str = Field(
        default="your-secure-jwt-secret-here",
        env="JWT_SECRET"
    )
    api_key: Optional[str] = Field(default=None, env="API_KEY")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    
    # =====================================
    # FEATURE FLAGS
    # =====================================
    enable_chat: bool = Field(default=True, env="ENABLE_CHAT")
    enable_projects: bool = Field(default=True, env="ENABLE_PROJECTS")
    enable_analytics: bool = Field(default=True, env="ENABLE_ANALYTICS")
    enable_ai_insights: bool = Field(default=True, env="ENABLE_AI_INSIGHTS")
    
    # MCP Feature Flags
    mcp_memory_enabled: bool = Field(default=True, env="MCP_MEMORY_ENABLED")
    mcp_filesystem_enabled: bool = Field(default=True, env="MCP_FILESYSTEM_ENABLED")
    mcp_web_enabled: bool = Field(default=True, env="MCP_WEB_ENABLED")
    mcp_git_enabled: bool = Field(default=True, env="MCP_GIT_ENABLED")
    
    # =====================================
    # MONITORING CONFIGURATION
    # =====================================
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    prometheus_enabled: bool = Field(default=False, env="PROMETHEUS_ENABLED")
    grafana_enabled: bool = Field(default=False, env="GRAFANA_ENABLED")
    
    # =====================================
    # PYDANTIC CONFIGURATION
    # =====================================
    if PYDANTIC_V2:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="allow"
        )
    else:
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False
            extra = "allow"  # Allow extra fields for extensibility
    
    # =====================================
    # VALIDATION METHODS
    # =====================================
    
    def validate_log_level(cls, v):
        """Validate log level is valid."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()
    
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    def validate_workspace_path(cls, v):
        """Validate workspace path exists."""
        path = Path(v).expanduser()
        if not path.exists():
            logger.warning(f"Workspace path {path} does not exist")
        return str(path)
    
    # Apply decorators conditionally based on Pydantic version
    if not PYDANTIC_V2:
        validate_log_level = validator("log_level")(validate_log_level)
        parse_cors_origins = validator("cors_origins", pre=True)(parse_cors_origins)
        validate_workspace_path = validator("workspace_path")(validate_workspace_path)
    else:
        validate_log_level = field_validator("log_level")(validate_log_level)
        parse_cors_origins = field_validator("cors_origins", mode="before")(parse_cors_origins)
        validate_workspace_path = field_validator("workspace_path")(validate_workspace_path)
    
    # =====================================
    # SERVICE URL METHODS
    # =====================================
    
    def get_service_url(self, service_name: str, protocol: str = "http") -> str:
        """
        Get the complete URL for a service.
        
        Args:
            service_name: Name of the service
            protocol: Protocol to use (http, https, ws, wss)
            
        Returns:
            Complete service URL
        """
        port_attr = f"{service_name}_port"
        if hasattr(self, port_attr):
            port = getattr(self, port_attr)
            return f"{protocol}://{self.default_host}:{port}"
        
        # Fallback to service registry
        service = ServiceRegistry.get_service(service_name)
        if service:
            return f"{protocol}://{self.default_host}:{service.port}"
        
        raise ValueError(f"Unknown service: {service_name}")
    
    def get_all_service_urls(self, protocol: str = "http") -> Dict[str, str]:
        """Get URLs for all services."""
        urls = {}
        
        # Get URLs from registry
        for service_name in ServiceRegistry.SERVICES:
            try:
                urls[service_name] = self.get_service_url(service_name, protocol)
            except ValueError:
                logger.warning(f"Could not generate URL for service: {service_name}")
        
        return urls
    
    def get_database_urls(self) -> Dict[str, str]:
        """Get all database connection URLs."""
        return {
            "postgres": self.database_url,
            "redis": self.redis_url,
            "weaviate": self.weaviate_url,
            "neo4j": self.neo4j_uri,
        }
    
    # =====================================
    # PORT MANAGEMENT METHODS
    # =====================================
    
    def get_all_ports(self) -> Dict[str, int]:
        """Get all configured ports."""
        ports = {}
        
        # Extract ports from config attributes
        for attr_name in dir(self):
            if attr_name.endswith("_port") and not attr_name.startswith("_"):
                service_name = attr_name[:-5]  # Remove "_port" suffix
                ports[service_name] = getattr(self, attr_name)
        
        return ports
    
    def check_port_conflicts(self) -> List[tuple[str, str, int]]:
        """Check for port conflicts in configuration."""
        ports = self.get_all_ports()
        conflicts = []
        port_map = {}
        
        for service, port in ports.items():
            if port in port_map:
                conflicts.append((port_map[port], service, port))
            else:
                port_map[port] = service
        
        return conflicts
    
    # =====================================
    # ENVIRONMENT EXPORT
    # =====================================
    
    def to_env_dict(self) -> Dict[str, str]:
        """
        Export configuration as environment variables dictionary.
        
        Returns:
            Dictionary suitable for os.environ.update()
        """
        env_dict = {}
        
        # Use Pydantic's field info to get environment variable names
        for field_name, field_info in self.__fields__.items():
            value = getattr(self, field_name)
            if value is not None:
                # Get env var name from field definition
                env_name = field_info.field_info.extra.get("env", field_name.upper())
                
                # Convert value to string
                if isinstance(value, bool):
                    env_dict[env_name] = "true" if value else "false"
                elif isinstance(value, list):
                    env_dict[env_name] = ",".join(str(v) for v in value)
                else:
                    env_dict[env_name] = str(value)
        
        return env_dict
    
    def export_to_file(self, filepath: str) -> None:
        """Export configuration to a .env file."""
        env_dict = self.to_env_dict()
        
        with open(filepath, "w") as f:
            f.write("# Sophia Intel AI Configuration\n")
            f.write("# Generated automatically - do not edit directly\n\n")
            
            for key, value in sorted(env_dict.items()):
                f.write(f"{key}={value}\n")
    
    # =====================================
    # VALIDATION HELPERS
    # =====================================
    
    def validate_required_env_vars(self) -> List[str]:
        """
        Validate that required environment variables are set.
        
        Returns:
            List of missing required variables
        """
        missing = []
        
        # Check AI API keys
        if not self.openai_api_key or self.openai_api_key == "sk-YOUR-OPENAI-KEY-HERE":
            missing.append("OPENAI_API_KEY")
        
        if not self.anthropic_api_key or self.anthropic_api_key == "sk-ant-YOUR-ANTHROPIC-KEY-HERE":
            missing.append("ANTHROPIC_API_KEY")
        
        # Check database URLs
        if "localhost" in self.database_url and "password" in self.database_url:
            missing.append("DATABASE_URL (appears to be default value)")
        
        return missing
    
    def get_enabled_services(self) -> List[str]:
        """Get list of enabled services based on feature flags."""
        enabled = []
        
        # Core services (always enabled)
        enabled.extend(["unified_api", "agent_ui", "postgres", "redis"])
        
        # MCP services
        if self.mcp_memory_enabled:
            enabled.append("mcp_memory")
        if self.mcp_filesystem_enabled:
            enabled.append("mcp_filesystem")
        if self.mcp_web_enabled:
            enabled.append("mcp_web")
        if self.mcp_git_enabled:
            enabled.append("mcp_git")
        
        # Development services
        if self.prometheus_enabled:
            enabled.append("prometheus")
        if self.grafana_enabled:
            enabled.append("grafana")
        
        # Integration services
        if self.slack_enabled:
            enabled.append("slack")
        if self.asana_enabled:
            enabled.append("asana")
        if self.linear_enabled:
            enabled.append("linear")
        if self.github_enabled:
            enabled.append("github")
        
        return enabled


# =====================================
# SINGLETON CONFIGURATION INSTANCE
# =====================================

@lru_cache()
def get_config() -> SophiaConfig:
    """
    Get the singleton configuration instance.
    
    This function is cached to ensure we only create one configuration
    instance per process, which is important for performance and consistency.
    
    Returns:
        Cached SophiaConfig instance
    """
    return SophiaConfig()


# =====================================
# CONFIGURATION VALIDATION
# =====================================

def validate_configuration() -> Dict[str, Any]:
    """
    Validate the current configuration and return a summary.
    
    Returns:
        Dictionary with validation results
    """
    config = get_config()
    
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "port_conflicts": [],
        "missing_env_vars": [],
        "enabled_services": [],
    }
    
    try:
        # Check for port conflicts
        conflicts = config.check_port_conflicts()
        if conflicts:
            result["port_conflicts"] = conflicts
            result["errors"].extend([
                f"Port conflict: {svc1} and {svc2} both use port {port}"
                for svc1, svc2, port in conflicts
            ])
        
        # Check required environment variables
        missing = config.validate_required_env_vars()
        if missing:
            result["missing_env_vars"] = missing
            result["warnings"].extend([
                f"Missing or default value for: {var}"
                for var in missing
            ])
        
        # Get enabled services
        result["enabled_services"] = config.get_enabled_services()
        
        # Mark as invalid if there are critical errors
        if result["errors"]:
            result["valid"] = False
        
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Configuration validation error: {str(e)}")
    
    return result


# Export commonly used functions
__all__ = [
    "SophiaConfig",
    "get_config",
    "validate_configuration",
]
