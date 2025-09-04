"""
Secure Configuration Management for MCP Server

This module handles all configuration and sensitive data management
using environment variables and secure practices.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseSettings, SecretStr, validator
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings with secure credential management.
    
    All sensitive data should be loaded from environment variables
    or secure vaults, never hardcoded.
    """
    
    # API Keys (SecretStr prevents accidental logging)
    openrouter_api_key: SecretStr
    portkey_api_key: SecretStr
    together_api_key: Optional[SecretStr] = None
    openai_api_key: Optional[SecretStr] = None
    anthropic_api_key: Optional[SecretStr] = None
    
    # Server Configuration
    agent_api_port: int = 3333
    host: str = "127.0.0.1"
    environment: str = "development"
    debug: bool = False
    
    # Security Settings
    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Database Configuration
    database_url: str = "sqlite:///./mcp_audit.db"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    
    # File Operations Security
    repo_root: Path = Path.cwd()
    allowed_file_extensions: list[str] = [".py", ".js", ".ts", ".json", ".md", ".txt", ".yaml", ".yml"]
    max_file_size_mb: int = 10
    backup_enabled: bool = True
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 30
    rate_limit_period: int = 60  # seconds
    
    # Redis Configuration (for distributed rate limiting)
    redis_url: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Performance
    cache_ttl: int = 300  # seconds
    max_concurrent_requests: int = 100
    request_timeout: int = 30  # seconds
    
    @validator("repo_root", pre=True)
    def validate_repo_root(cls, v):
        """Ensure repo_root is a valid directory"""
        path = Path(v) if isinstance(v, str) else v
        if not path.exists():
            raise ValueError(f"Repository root {path} does not exist")
        return path.resolve()
    
    @validator("environment")
    def validate_environment(cls, v):
        """Ensure environment is valid"""
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Custom environment variable names
        fields = {
            "openrouter_api_key": {"env": "OPENROUTER_API_KEY"},
            "portkey_api_key": {"env": "PORTKEY_API_KEY"},
            "together_api_key": {"env": "TOGETHER_API_KEY"},
            "openai_api_key": {"env": "OPENAI_API_KEY"},
            "anthropic_api_key": {"env": "ANTHROPIC_API_KEY"},
            "jwt_secret_key": {"env": "JWT_SECRET_KEY"},
            "agent_api_port": {"env": "AGENT_API_PORT"},
            "database_url": {"env": "DATABASE_URL"},
            "redis_url": {"env": "REDIS_URL"},
            "repo_root": {"env": "REPO_ROOT"},
        }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    This ensures we only load and validate settings once,
    improving performance and consistency.
    """
    return Settings()


def validate_api_keys():
    """
    Validate that required API keys are present and not exposed.
    
    Raises:
        ValueError: If required keys are missing or invalid
    """
    settings = get_settings()
    
    required_keys = [
        ("OpenRouter", settings.openrouter_api_key),
        ("Portkey", settings.portkey_api_key),
    ]
    
    for name, key in required_keys:
        if not key:
            raise ValueError(f"{name} API key is required but not configured")
        
        # Check for common invalid patterns
        key_str = key.get_secret_value()
        if key_str.startswith("sk-") and len(key_str) < 20:
            raise ValueError(f"{name} API key appears to be invalid")
    
    return True


def get_secure_headers() -> dict:
    """
    Get security headers for responses.
    
    Returns:
        Dictionary of security headers
    """
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }


# Export commonly used functions and classes
__all__ = [
    "Settings",
    "get_settings",
    "validate_api_keys",
    "get_secure_headers",
]