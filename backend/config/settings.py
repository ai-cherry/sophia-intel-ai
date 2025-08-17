"""
Centralized settings management for SOPHIA Intel
Handles environment variables and configuration validation
"""

import os
from typing import List, Optional, Dict, Any
from pydantic import BaseSettings, Field, validator
import json

class DatabaseSettings(BaseSettings):
    """Database configuration settings"""
    postgres_url: str = Field(..., env="DATABASE_URL")
    postgres_pool_size: int = Field(20, env="POSTGRES_POOL_SIZE")
    postgres_max_overflow: int = Field(30, env="POSTGRES_MAX_OVERFLOW")
    
    redis_url: str = Field(..., env="REDIS_URL")
    redis_pool_size: int = Field(10, env="REDIS_POOL_SIZE")
    
    qdrant_url: str = Field(..., env="QDRANT_URL")
    qdrant_api_key: Optional[str] = Field(None, env="QDRANT_API_KEY")

class LambdaLabsSettings(BaseSettings):
    """Lambda Labs configuration settings"""
    api_key: str = Field(..., env="LAMBDA_API_KEY")
    primary_url: str = Field(..., env="LAMBDA_PRIMARY_URL")
    secondary_url: str = Field(..., env="LAMBDA_SECONDARY_URL")
    
    servers_json: str = Field("{}", env="LAMBDA_SERVERS_JSON")
    
    @validator("servers_json")
    def parse_servers_json(cls, v):
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            return {}

class AIServiceSettings(BaseSettings):
    """AI service configuration settings"""
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_api_base: Optional[str] = Field(None, env="OPENAI_API_BASE")
    
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    openrouter_api_key: Optional[str] = Field(None, env="OPENROUTER_API_KEY")
    
    elevenlabs_api_key: Optional[str] = Field(None, env="ELEVENLABS_API_KEY")
    elevenlabs_voice_id: str = Field("21m00Tcm4TlvDq8ikWAM", env="ELEVENLABS_VOICE_ID")

class ResearchSettings(BaseSettings):
    """Research service configuration settings"""
    tavily_api_key: Optional[str] = Field(None, env="TAVILY_API_KEY")
    serp_api_key: Optional[str] = Field(None, env="SERP_API_KEY")
    news_api_key: Optional[str] = Field(None, env="NEWS_API_KEY")
    
    bright_data_username: Optional[str] = Field(None, env="BRIGHT_DATA_USERNAME")
    bright_data_password: Optional[str] = Field(None, env="BRIGHT_DATA_PASSWORD")
    
    zenrows_api_key: Optional[str] = Field(None, env="ZENROWS_API_KEY")
    apify_api_key: Optional[str] = Field(None, env="APIFY_API_KEY")

class SecuritySettings(BaseSettings):
    """Security configuration settings"""
    jwt_secret_key: str = Field("change-in-production", env="JWT_SECRET_KEY")
    jwt_expiration_hours: int = Field(24, env="JWT_EXPIRATION_HOURS")
    
    api_gateway_token: Optional[str] = Field(None, env="API_GATEWAY_TOKEN")
    mcp_auth_token: Optional[str] = Field(None, env="MCP_AUTH_TOKEN")
    
    allowed_origins: List[str] = Field(
        ["http://localhost:3000", "https://sophia-intel.ai"],
        env="ALLOWED_ORIGINS"
    )
    allowed_hosts: List[str] = Field(
        ["localhost", "sophia-intel.ai", "*.sophia-intel.ai"],
        env="ALLOWED_HOSTS"
    )
    
    @validator("allowed_origins", pre=True)
    def parse_origins(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v
    
    @validator("allowed_hosts", pre=True)
    def parse_hosts(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v

class MonitoringSettings(BaseSettings):
    """Monitoring and observability settings"""
    sentry_dsn: Optional[str] = Field(None, env="SENTRY_DSN")
    prometheus_enabled: bool = Field(True, env="PROMETHEUS_ENABLED")
    
    slack_webhook_url: Optional[str] = Field(None, env="SLACK_WEBHOOK_URL")
    email_alerts_enabled: bool = Field(False, env="EMAIL_ALERTS_ENABLED")
    
    log_level: str = Field("INFO", env="LOG_LEVEL")
    structured_logging: bool = Field(True, env="STRUCTURED_LOGGING")

class ApplicationSettings(BaseSettings):
    """Main application settings"""
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    
    orchestrator_url: str = Field("http://localhost:8001", env="ORCHESTRATOR_URL")
    mcp_server_url: str = Field("http://localhost:8002", env="MCP_SERVER_URL")
    
    # Feature flags
    web_access_enabled: bool = Field(True, env="WEB_ACCESS_ENABLED")
    deep_research_enabled: bool = Field(True, env="DEEP_RESEARCH_ENABLED")
    training_enabled: bool = Field(True, env="TRAINING_ENABLED")
    voice_enabled: bool = Field(True, env="VOICE_ENABLED")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

class Settings:
    """Centralized settings container"""
    
    def __init__(self):
        self.app = ApplicationSettings()
        self.database = DatabaseSettings()
        self.lambda_labs = LambdaLabsSettings()
        self.ai_services = AIServiceSettings()
        self.research = ResearchSettings()
        self.security = SecuritySettings()
        self.monitoring = MonitoringSettings()
    
    @property
    def is_production(self) -> bool:
        return self.app.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.app.environment.lower() == "development"
    
    def get_database_url(self) -> str:
        """Get database URL with connection parameters"""
        return self.database.postgres_url
    
    def get_redis_url(self) -> str:
        """Get Redis URL"""
        return self.database.redis_url
    
    def validate_required_settings(self) -> List[str]:
        """Validate that all required settings are present"""
        missing = []
        
        # Check critical settings
        if not self.database.postgres_url:
            missing.append("DATABASE_URL")
        if not self.database.redis_url:
            missing.append("REDIS_URL")
        if not self.lambda_labs.api_key:
            missing.append("LAMBDA_API_KEY")
        if not self.ai_services.openai_api_key:
            missing.append("OPENAI_API_KEY")
        
        return missing

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get global settings instance"""
    return settings

def validate_environment():
    """Validate environment configuration"""
    missing = settings.validate_required_settings()
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    print(f"✅ Environment validation passed")
    print(f"📊 Environment: {settings.app.environment}")
    print(f"🔧 Debug mode: {settings.app.debug}")
    print(f"🌐 Host: {settings.app.host}:{settings.app.port}")
    
    return True

