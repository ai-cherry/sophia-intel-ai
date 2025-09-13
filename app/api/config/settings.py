"""
Settings Configuration for Sophia AI V9.7
Centralized configuration management with environment variable support.
"""
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    All settings can be overridden via environment variables.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    # Application
    app_name: str = Field(default="Sophia AI V9.7", description="Application name")
    app_version: str = Field(default="9.7.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="production", description="Environment")
    # Database
    database_url: Optional[str] = Field(
        default="postgresql://localhost:5432/postgres",
        description="PostgreSQL database URL",
        env=["DATABASE_URL", "POSTGRES_URL"],
    )
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL",
        env=["REDIS_URL", "REDIS_CONNECTION_STRING"],
    )
    # Vector Database
    qdrant_host: str = Field(default="localhost", description="Qdrant host")
    qdrant_port: int = Field(default=6333, description="Qdrant port")
    qdrant_api_key: Optional[str] = Field(default=None, description="Qdrant API key")
    # Neo4j (Knowledge Graph)
    neo4j_uri: Optional[str] = Field(default=None, description="Neo4j connection URI")
    neo4j_user: Optional[str] = Field(default=None, description="Neo4j username")
    neo4j_password: Optional[str] = Field(default=None, description="Neo4j password")
    # AI Services
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key", env=["OPENAI_API_KEY", "OPENAI_KEY"])
    anthropic_api_key: Optional[str] = Field(
        default=None, description="Anthropic API key", env=["ANTHROPIC_API_KEY", "ANTHROPIC_KEY"]
    )
    # Slack Integration
    slack_bot_token: Optional[str] = Field(default=None, description="Slack bot token")
    slack_signing_secret: Optional[str] = Field(
        default=None, description="Slack signing secret"
    )
    slack_app_token: Optional[str] = Field(default=None, description="Slack app token")
    # Notion Integration
    notion_api_key: Optional[str] = Field(default=None, description="Notion API key")
    notion_database_id: Optional[str] = Field(
        default=None, description="Notion database ID"
    )
    # Asana Integration
    asana_access_token: Optional[str] = Field(
        default=None, description="Asana access token"
    )
    asana_workspace_id: Optional[str] = Field(
        default=None, description="Asana workspace ID"
    )
    # Linear Integration
    linear_api_key: Optional[str] = Field(default=None, description="Linear API key")
    linear_team_id: Optional[str] = Field(default=None, description="Linear team ID")
    # Gong Integration
    gong_api_key: Optional[str] = Field(default=None, description="Gong API key")
    gong_api_secret: Optional[str] = Field(default=None, description="Gong API secret")
    # Performance Settings
    cache_ttl: int = Field(default=3600, description="Default cache TTL in seconds")
    max_workers: int = Field(default=10, description="Maximum worker threads")
    request_timeout: int = Field(default=30, description="Request timeout in seconds")
    # Rate Limiting
    rate_limit_tier: str = Field(default="tier_3", description="Rate limit tier")
    rate_limit_requests_per_minute: int = Field(
        default=200, description="Requests per minute"
    )
    rate_limit_burst: int = Field(default=500, description="Burst limit")
    # Security
    secret_key: str = Field(
        default="dev-secret",
        description="Secret key for JWT tokens",
        env=["SECRET_KEY", "JWT_SECRET"],
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_hours: int = Field(default=24, description="JWT expiration in hours")
    # CORS
    cors_origins: List[str] = Field(
        default=["${SOPHIA_FRONTEND_ENDPOINT}", "https://sophia-intel.ai"],
        description="CORS allowed origins",
    )
    # Monitoring
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    enable_tracing: bool = Field(default=True, description="Enable distributed tracing")
    log_level: str = Field(default="INFO", description="Logging level")
    # File Storage
    upload_max_size: int = Field(
        default=10485760, description="Max upload size in bytes (10MB)"
    )
    upload_allowed_types: List[str] = Field(
        default=["pdf", "docx", "txt", "md", "json", "csv"],
        description="Allowed file types for upload",
    )
    # Email (Optional)
    smtp_host: Optional[str] = Field(default=None, description="SMTP host")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_user: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP")
    # Feature Flags
    enable_slack_integration: bool = Field(
        default=True, description="Enable Slack integration"
    )
    enable_notion_integration: bool = Field(
        default=True, description="Enable Notion integration"
    )
    enable_asana_integration: bool = Field(
        default=True, description="Enable Asana integration"
    )
    enable_linear_integration: bool = Field(
        default=True, description="Enable Linear integration"
    )
    enable_gong_integration: bool = Field(
        default=True, description="Enable Gong integration"
    )
    enable_anthropic_reasoning: bool = Field(
        default=True, description="Enable Anthropic reasoning"
    )
    enable_vector_search: bool = Field(default=True, description="Enable vector search")
    enable_knowledge_graph: bool = Field(
        default=True, description="Enable knowledge graph"
    )
    # Model Configuration
    embedding_model: str = Field(
        default="all-mpnet-base-v2", description="Sentence transformer model"
    )
    anthropic_model: str = Field(
        default="claude-3-opus-20240805", description="Anthropic model"
    )
    openai_model: str = Field(default="gpt-4", description="OpenAI model")
    # Cache Configuration
    cache_prefix: str = Field(default="sophia:v97:", description="Cache key prefix")
    cache_max_connections: int = Field(default=20, description="Max Redis connections")
    # Vector Search Configuration
    vector_collection_name: str = Field(
        default="project_knowledge", description="Vector collection name"
    )
    vector_embedding_size: int = Field(default=768, description="Embedding vector size")
    vector_search_limit: int = Field(
        default=10, description="Default search result limit"
    )
    vector_confidence_threshold: float = Field(
        default=0.7, description="Minimum confidence threshold"
    )
    # Intent Classification Configuration
    intent_confidence_threshold: float = Field(
        default=0.7, description="Intent classification threshold"
    )
    intent_cache_ttl: int = Field(default=3600, description="Intent analysis cache TTL")
    intent_max_reasoning_tokens: int = Field(
        default=1000, description="Max tokens for reasoning"
    )
    # Slack Configuration
    slack_rate_limit_tier: str = Field(
        default="tier_3", description="Slack rate limit tier"
    )
    slack_webhook_timeout: int = Field(default=10, description="Slack webhook timeout")
    slack_retry_attempts: int = Field(default=3, description="Slack API retry attempts")
    # Knowledge Management
    knowledge_auto_capture: bool = Field(
        default=True, description="Auto-capture knowledge"
    )
    knowledge_insight_generation: bool = Field(
        default=True, description="Generate insights"
    )
    knowledge_graph_updates: bool = Field(
        default=True, description="Update knowledge graph"
    )
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    @validator("upload_allowed_types", pre=True)
    def parse_upload_types(cls, v):
        """Parse upload types from string or list"""
        if isinstance(v, str):
            return [file_type.strip() for file_type in v.split(",")]
        return v
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment"""
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v.lower()
    # no inner Config; model_config is used for pydantic v2
    def get_database_config(self) -> dict:
        """Get database configuration dictionary"""
        return {
            "url": self.database_url,
            "pool_size": 20,
            "max_overflow": 30,
            "pool_timeout": 30,
            "pool_recycle": 3600,
            "echo": self.debug,
        }
    def get_redis_config(self) -> dict:
        """Get Redis configuration dictionary"""
        return {
            "url": self.redis_url,
            "max_connections": self.cache_max_connections,
            "retry_on_timeout": True,
            "socket_keepalive": True,
            "health_check_interval": 30,
        }
    def get_qdrant_config(self) -> dict:
        """Get Qdrant configuration dictionary"""
        config = {"host": self.qdrant_host, "port": self.qdrant_port}
        if self.qdrant_api_key:
            config["api_key"] = self.qdrant_api_key
        return config
    def get_cors_config(self) -> dict:
        """Get CORS configuration dictionary"""
        return {
            "allow_origins": self.cors_origins,
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["*"],
        }
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled"""
        feature_map = {
            "slack": self.enable_slack_integration,
            "notion": self.enable_notion_integration,
            "asana": self.enable_asana_integration,
            "linear": self.enable_linear_integration,
            "gong": self.enable_gong_integration,
            "anthropic": self.enable_anthropic_reasoning,
            "vector_search": self.enable_vector_search,
            "knowledge_graph": self.enable_knowledge_graph,
        }
        return feature_map.get(feature, False)
    def get_integration_config(self, integration: str) -> dict:
        """Get configuration for specific integration"""
        configs = {
            "slack": {
                "bot_token": self.slack_bot_token,
                "signing_secret": self.slack_signing_secret,
                "app_token": self.slack_app_token,
                "enabled": self.enable_slack_integration,
                "rate_limit_tier": self.slack_rate_limit_tier,
                "timeout": self.slack_webhook_timeout,
                "retry_attempts": self.slack_retry_attempts,
            },
            "notion": {
                "api_key": self.notion_api_key,
                "database_id": self.notion_database_id,
                "enabled": self.enable_notion_integration,
            },
            "asana": {
                "access_token": self.asana_access_token,
                "workspace_id": self.asana_workspace_id,
                "enabled": self.enable_asana_integration,
            },
            "linear": {
                "api_key": self.linear_api_key,
                "team_id": self.linear_team_id,
                "enabled": self.enable_linear_integration,
            },
            "gong": {
                "api_key": self.gong_api_key,
                "api_secret": self.gong_api_secret,
                "enabled": self.enable_gong_integration,
            },
        }
        return configs.get(integration, {})
# Global settings instance
settings = Settings()
