"""
Unified SOPHIA Intel Configuration Settings
Single source of truth for all application configuration
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field


class SophiaConfig(BaseSettings):
    """Unified configuration for SOPHIA Intel"""
    
    # Environment
    ENVIRONMENT: str = Field(default="production", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Database Configuration
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Neon Database (Production)
    NEON_API_TOKEN: Optional[str] = Field(None, env="NEON_API_TOKEN")
    NEON_PROJECT: str = Field(default="sophia", env="NEON_PROJECT")
    NEON_DATABASE_URL: Optional[str] = Field(None, env="NEON_DATABASE_URL")
    
    # AI Service APIs
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    OPENROUTER_API_KEY: Optional[str] = Field(None, env="OPENROUTER_API_KEY")
    LLAMA_API_KEY: Optional[str] = Field(None, env="LLAMA_API_KEY")
    
    # Graph Database
    NEO4J_URI: Optional[str] = Field(None, env="NEO4J_URI")
    NEO4J_CLIENT_ID: Optional[str] = Field(None, env="NEO4J_CLIENT_ID")
    NEO4J_CLIENT_SECRET: Optional[str] = Field(None, env="NEO4J_CLIENT_SECRET")
    
    # Deployment Services
    RAILWAY_TOKEN: Optional[str] = Field(None, env="RAILWAY_TOKEN")
    LAMBDA_API_KEY: Optional[str] = Field(None, env="LAMBDA_API_KEY")
    DNSIMPLE_API_KEY: Optional[str] = Field(None, env="DNSIMPLE_API_KEY")
    
    # Pay Ready Data Sources
    SALESFORCE_API_KEY: Optional[str] = Field(None, env="SALESFORCE_API_KEY")
    SALESFORCE_INSTANCE_URL: Optional[str] = Field(None, env="SALESFORCE_INSTANCE_URL")
    SALESFORCE_USERNAME: Optional[str] = Field(None, env="SALESFORCE_USERNAME")
    
    HUBSPOT_API_KEY: Optional[str] = Field(None, env="HUBSPOT_API_KEY")
    HUBSPOT_PORTAL_ID: Optional[str] = Field(None, env="HUBSPOT_PORTAL_ID")
    
    GONG_API_KEY: Optional[str] = Field(None, env="GONG_API_KEY")
    GONG_ACCESS_TOKEN: Optional[str] = Field(None, env="GONG_ACCESS_TOKEN")
    
    INTERCOM_API_KEY: Optional[str] = Field(None, env="INTERCOM_API_KEY")
    INTERCOM_APP_ID: Optional[str] = Field(None, env="INTERCOM_APP_ID")
    
    LOOKER_API_KEY: Optional[str] = Field(None, env="LOOKER_API_KEY")
    LOOKER_BASE_URL: Optional[str] = Field(None, env="LOOKER_BASE_URL")
    
    SLACK_BOT_TOKEN: Optional[str] = Field(None, env="SLACK_BOT_TOKEN")
    SLACK_APP_TOKEN: Optional[str] = Field(None, env="SLACK_APP_TOKEN")
    
    ASANA_API_KEY: Optional[str] = Field(None, env="ASANA_API_KEY")
    ASANA_WORKSPACE_ID: Optional[str] = Field(None, env="ASANA_WORKSPACE_ID")
    
    LINEAR_API_KEY: Optional[str] = Field(None, env="LINEAR_API_KEY")
    LINEAR_TEAM_ID: Optional[str] = Field(None, env="LINEAR_TEAM_ID")
    
    FACTOR_AI_API_KEY: Optional[str] = Field(None, env="FACTOR_AI_API_KEY")
    FACTOR_AI_WORKSPACE: Optional[str] = Field(None, env="FACTOR_AI_WORKSPACE")
    
    NOTION_API_KEY: Optional[str] = Field(None, env="NOTION_API_KEY")
    NOTION_DATABASE_ID: Optional[str] = Field(None, env="NOTION_DATABASE_ID")
    
    NETSUITE_API_KEY: Optional[str] = Field(None, env="NETSUITE_API_KEY")
    NETSUITE_ACCOUNT_ID: Optional[str] = Field(None, env="NETSUITE_ACCOUNT_ID")
    
    # Security
    JWT_SECRET_KEY: str = Field(default="change-in-production", env="JWT_SECRET_KEY")
    ENCRYPTION_KEY: str = Field(default="change-in-production", env="ENCRYPTION_KEY")
    API_KEY_SALT: str = Field(default="change-in-production", env="API_KEY_SALT")
    
    # Monitoring & Observability
    GRAFANA_API_KEY: Optional[str] = Field(None, env="GRAFANA_API_KEY")
    PROMETHEUS_ENDPOINT: str = Field(default="http://localhost:9090", env="PROMETHEUS_ENDPOINT")
    SENTRY_DSN: Optional[str] = Field(None, env="SENTRY_DSN")
    
    # Application Settings
    PORT: int = Field(default=8000, env="PORT")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    WORKERS: int = Field(default=4, env="WORKERS")
    MAX_CONNECTIONS: int = Field(default=1000, env="MAX_CONNECTIONS")
    REQUEST_TIMEOUT: int = Field(default=300, env="REQUEST_TIMEOUT")
    
    # Celery Configuration
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")
    CELERY_TASK_SERIALIZER: str = Field(default="json", env="CELERY_TASK_SERIALIZER")
    CELERY_RESULT_SERIALIZER: str = Field(default="json", env="CELERY_RESULT_SERIALIZER")
    CELERY_ACCEPT_CONTENT: List[str] = Field(default=["json"], env="CELERY_ACCEPT_CONTENT")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=1000, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    RATE_LIMIT_BURST: int = Field(default=100, env="RATE_LIMIT_BURST")
    
    # File Storage
    UPLOAD_MAX_SIZE: int = Field(default=10485760, env="UPLOAD_MAX_SIZE")  # 10MB
    ALLOWED_FILE_TYPES: str = Field(default="pdf,doc,docx,txt,csv,json", env="ALLOWED_FILE_TYPES")
    
    # Feature Flags
    ENABLE_ADVANCED_RAG: bool = Field(default=True, env="ENABLE_ADVANCED_RAG")
    ENABLE_CROSS_PLATFORM_CORRELATION: bool = Field(default=True, env="ENABLE_CROSS_PLATFORM_CORRELATION")
    ENABLE_QUALITY_ASSURANCE: bool = Field(default=True, env="ENABLE_QUALITY_ASSURANCE")
    ENABLE_REAL_TIME_LEARNING: bool = Field(default=True, env="ENABLE_REAL_TIME_LEARNING")
    ENABLE_BACKGROUND_AGENTS: bool = Field(default=True, env="ENABLE_BACKGROUND_AGENTS")
    
    # Business Intelligence Settings
    PAY_READY_DOMAIN_FOCUS: bool = Field(default=True, env="PAY_READY_DOMAIN_FOCUS")
    BUSINESS_CONTEXT_WEIGHT: float = Field(default=0.8, env="BUSINESS_CONTEXT_WEIGHT")
    CONFIDENCE_THRESHOLD: float = Field(default=0.7, env="CONFIDENCE_THRESHOLD")
    QUALITY_THRESHOLD: float = Field(default=0.75, env="QUALITY_THRESHOLD")
    
    # Performance Tuning
    DATABASE_POOL_SIZE: int = Field(default=20, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=30, env="DATABASE_MAX_OVERFLOW")
    REDIS_POOL_SIZE: int = Field(default=50, env="REDIS_POOL_SIZE")
    HTTP_TIMEOUT: int = Field(default=30, env="HTTP_TIMEOUT")
    WEBSOCKET_TIMEOUT: int = Field(default=300, env="WEBSOCKET_TIMEOUT")
    
    # Backup & Recovery
    BACKUP_ENABLED: bool = Field(default=True, env="BACKUP_ENABLED")
    BACKUP_SCHEDULE: str = Field(default="0 2 * * *", env="BACKUP_SCHEDULE")
    BACKUP_RETENTION_DAYS: int = Field(default=30, env="BACKUP_RETENTION_DAYS")
    
    class Config:
        env_file = ".env.unified"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def get_database_url(self) -> str:
        """Get the appropriate database URL based on environment"""
        if self.ENVIRONMENT == "production" and self.NEON_DATABASE_URL:
            return self.NEON_DATABASE_URL
        return self.DATABASE_URL
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled"""
        feature_map = {
            'advanced_rag': self.ENABLE_ADVANCED_RAG,
            'cross_platform_correlation': self.ENABLE_CROSS_PLATFORM_CORRELATION,
            'quality_assurance': self.ENABLE_QUALITY_ASSURANCE,
            'real_time_learning': self.ENABLE_REAL_TIME_LEARNING,
            'background_agents': self.ENABLE_BACKGROUND_AGENTS
        }
        return feature_map.get(feature, False)


# Global configuration instance
config = SophiaConfig()

# Backward compatibility
settings = config

def get_settings() -> SophiaConfig:
    """Get global settings instance"""
    return config

def validate_environment():
    """Validate environment configuration"""
    missing = []
    
    # Check critical settings
    if not config.DATABASE_URL:
        missing.append("DATABASE_URL")
    if not config.REDIS_URL:
        missing.append("REDIS_URL")
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    print(f"✅ Environment validation passed")
    print(f"📊 Environment: {config.ENVIRONMENT}")
    print(f"🔧 Debug mode: {config.DEBUG}")
    print(f"🌐 Host: {config.HOST}:{config.PORT}")
    
    return True

