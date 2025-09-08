"""
Unified Configuration System for Sophia Intel AI
Single source of truth for all configuration values.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field, SecretStr, validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.ai_logger import logger
from app.core.circuit_breaker import with_circuit_breaker


class AppSettings(BaseSettings):
    """
    Central configuration for the entire application.
    Validates all required settings at startup.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # ============================================
    # Server Configuration
    # ============================================

    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="AGENT_API_PORT")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Local development mode
    local_dev_mode: bool = Field(default=False, env="LOCAL_DEV_MODE")
    enable_runner_writes: bool = Field(default=False, env="ENABLE_RUNNER_WRITES")

    # ============================================
    # Database & Storage
    # ============================================

    # Weaviate Vector Database
    weaviate_url: str = Field(default="http://localhost:8080", env="WEAVIATE_URL")
    weaviate_api_key: Optional[SecretStr] = Field(default=None, env="WEAVIATE_API_KEY")

    # Redis Cache
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_ttl: int = Field(default=3600, env="REDIS_TTL")

    # PostgreSQL (for GraphRAG)
    postgres_url: Optional[str] = Field(default=None, env="POSTGRES_URL")

    # SQLite (for Supermemory)
    supermemory_db: str = Field(default="tmp/supermemory.db", env="SUPERMEMORY_DB")

    # ============================================
    # API Keys & Authentication
    # ============================================

    # OpenRouter/OpenAI
    openai_api_key: Optional[SecretStr] = Field(default=None, env="OPENAI_API_KEY")
    openai_base_url: str = Field(
        default="https://openrouter.ai/api/v1", env="OPENAI_BASE_URL"
    )
    openrouter_api_key: Optional[SecretStr] = Field(
        default=None, env="OPENROUTER_API_KEY"
    )

    # Portkey
    portkey_api_key: Optional[SecretStr] = Field(default=None, env="PORTKEY_API_KEY")
    portkey_base_url: str = Field(
        default="https://api.portkey.ai/v1", env="PORTKEY_BASE_URL"
    )

    # Together AI
    together_api_key: Optional[SecretStr] = Field(default=None, env="TOGETHER_API_KEY")

    # Anthropic
    anthropic_api_key: Optional[SecretStr] = Field(
        default=None, env="ANTHROPIC_API_KEY"
    )

    # Agno
    agno_api_key: Optional[SecretStr] = Field(default=None, env="AGNO_API_KEY")

    # ============================================
    # Model Configuration
    # ============================================

    # Embedding Models
    embed_model: str = Field(default="voyage-3-large", env="EMBED_MODEL")
    embed_provider: str = Field(default="voyage", env="EMBED_PROVIDER")
    embed_dimension: int = Field(default=1024, env="EMBED_DIMENSION")

    # Reranking
    rerank_model: str = Field(default="cohere-rerank-v3", env="RERANK_MODEL")
    rerank_provider: str = Field(default="cohere", env="RERANK_PROVIDER")

    # Model Pools
    premium_models: list[str] = Field(
        default=["gpt-4o", "claude-3-opus", "gemini-1.5-pro"], env="PREMIUM_MODELS"
    )
    balanced_models: list[str] = Field(
        default=["gpt-4o-mini", "claude-3-sonnet", "gemini-1.5-flash"],
        env="BALANCED_MODELS",
    )
    fast_models: list[str] = Field(
        default=["gpt-3.5-turbo", "claude-3-haiku", "llama-3-70b"], env="FAST_MODELS"
    )

    # ============================================
    # MCP Servers
    # ============================================

    mcp_filesystem_enabled: bool = Field(default=True, env="MCP_FILESYSTEM")
    mcp_git_enabled: bool = Field(default=True, env="MCP_GIT")
    mcp_supermemory_enabled: bool = Field(default=True, env="MCP_SUPERMEMORY")

    # ============================================
    # Features & Services
    # ============================================

    # Core Features
    graphrag_enabled: bool = Field(default=True, env="GRAPHRAG_ENABLED")
    hybrid_search_enabled: bool = Field(default=True, env="HYBRID_SEARCH_ENABLED")
    evaluation_gates_enabled: bool = Field(default=True, env="EVALUATION_GATES_ENABLED")

    # Indexing
    auto_index_on_startup: bool = Field(default=False, env="AUTO_INDEX_ON_STARTUP")
    index_batch_size: int = Field(default=100, env="INDEX_BATCH_SIZE")
    index_workers: int = Field(default=4, env="INDEX_WORKERS")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests_per_minute: int = Field(default=60, env="RATE_LIMIT_RPM")
    streaming_rate_limit_rpm: int = Field(default=30, env="STREAMING_RATE_LIMIT_RPM")

    # ============================================
    # UI Configuration
    # ============================================

    ui_enabled: bool = Field(default=True, env="UI_ENABLED")
    ui_port: int = Field(default=3000, env="UI_PORT")
    playground_url: str = Field(default="http://localhost:7777", env="PLAYGROUND_URL")

    # CORS
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3002",
            "http://localhost:7777",
        ],
        env="CORS_ORIGINS",
    )

    # ============================================
    # Monitoring & Observability
    # ============================================

    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")

    tracing_enabled: bool = Field(default=False, env="TRACING_ENABLED")
    jaeger_endpoint: Optional[str] = Field(default=None, env="JAEGER_ENDPOINT")

    # ============================================
    # Paths
    # ============================================

    project_root: Path = Field(default=Path.cwd(), env="PROJECT_ROOT")
    logs_dir: Path = Field(default=Path("logs"), env="LOGS_DIR")
    tmp_dir: Path = Field(default=Path("tmp"), env="TMP_DIR")
    data_dir: Path = Field(default=Path("data"), env="DATA_DIR")

    # ============================================
    # Production Settings
    # ============================================

    # Security
    secret_key: SecretStr = Field(
        default=SecretStr("dev-key-change-in-production"), env="SECRET_KEY"
    )
    jwt_secret: SecretStr = Field(default=SecretStr("dev-jwt-secret"), env="JWT_SECRET")
    jwt_expiry_hours: int = Field(default=24, env="JWT_EXPIRY_HOURS")

    # Authentication & Authorization
    require_auth: bool = Field(default=False, env="REQUIRE_AUTH")
    auth_token_header: str = Field(default="Authorization", env="AUTH_TOKEN_HEADER")
    admin_api_key: Optional[SecretStr] = Field(default=None, env="ADMIN_API_KEY")

    # Resource Management
    max_concurrent_requests: int = Field(default=100, env="MAX_CONCURRENT_REQUESTS")
    request_timeout_seconds: int = Field(default=300, env="REQUEST_TIMEOUT_SECONDS")

    # Memory Management
    memory_cleanup_interval: int = Field(default=300, env="MEMORY_CLEANUP_INTERVAL")
    max_memory_usage_mb: int = Field(default=2048, env="MAX_MEMORY_USAGE_MB")

    # Database Connection Pooling
    redis_max_connections: int = Field(default=50, env="REDIS_MAX_CONNECTIONS")
    redis_retry_attempts: int = Field(default=3, env="REDIS_RETRY_ATTEMPTS")
    redis_connection_timeout: int = Field(default=30, env="REDIS_CONNECTION_TIMEOUT")

    # WebSocket Configuration
    websocket_max_connections: int = Field(
        default=1000, env="WEBSOCKET_MAX_CONNECTIONS"
    )
    websocket_heartbeat_interval: int = Field(
        default=30, env="WEBSOCKET_HEARTBEAT_INTERVAL"
    )
    websocket_max_message_size: int = Field(
        default=1024 * 1024, env="WEBSOCKET_MAX_MESSAGE_SIZE"
    )

    # Circuit Breaker Settings
    circuit_breaker_failure_threshold: int = Field(
        default=5, env="CB_FAILURE_THRESHOLD"
    )
    circuit_breaker_timeout_seconds: int = Field(default=60, env="CB_TIMEOUT_SECONDS")
    circuit_breaker_reset_timeout: int = Field(default=300, env="CB_RESET_TIMEOUT")

    # Health Check Configuration
    health_check_interval: int = Field(default=60, env="HEALTH_CHECK_INTERVAL")
    health_check_timeout: int = Field(default=10, env="HEALTH_CHECK_TIMEOUT")

    # Error Handling
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    retry_base_delay: float = Field(default=1.0, env="RETRY_BASE_DELAY")
    retry_max_delay: float = Field(default=60.0, env="RETRY_MAX_DELAY")

    # ============================================
    # Validation
    # ============================================

    @validator("api_port")
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @validator("environment")
    def validate_environment(cls, v):
        allowed = ["development", "staging", "production", "test"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v

    @validator("log_level")
    def validate_log_level(cls, v):
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v.upper()

    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Allow JSON array or comma-separated string for CORS_ORIGINS."""
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return []
            if s.startswith("["):
                # JSON array
                import json
                try:
                    return json.loads(s)
                except Exception:
                    # Fall back to single origin if bad JSON
                    return [s]
            # Comma-separated
            return [o.strip() for o in s.split(",") if o.strip()]
        return v

    @with_circuit_breaker("external_api")
    def validate_required_keys(self) -> dict[str, bool]:
        """Check if required API keys are present."""
        validations = {}

        # Check critical keys
        if self.openai_api_key or self.openrouter_api_key:
            validations["openai"] = True
        else:
            validations["openai"] = False

        if self.portkey_api_key:
            validations["portkey"] = True
        else:
            validations["portkey"] = False

        return validations

    @with_circuit_breaker("database")
    def get_active_features(self) -> dict[str, bool]:
        """Return status of all features."""
        return {
            "mcp_filesystem": self.mcp_filesystem_enabled,
            "mcp_git": self.mcp_git_enabled,
            "mcp_supermemory": self.mcp_supermemory_enabled,
            "graphrag": self.graphrag_enabled,
            "hybrid_search": self.hybrid_search_enabled,
            "evaluation_gates": self.evaluation_gates_enabled,
            "metrics": self.metrics_enabled,
            "tracing": self.tracing_enabled,
            "rate_limiting": self.rate_limit_enabled,
            "ui": self.ui_enabled,
        }

    def print_config(self):
        """Print current configuration (hiding secrets)."""
        logger.info("\n" + "=" * 60)
        logger.info("SOPHIA INTEL AI - CONFIGURATION")
        logger.info("=" * 60)

        logger.info(f"\n🔧 Environment: {self.environment}")
        logger.info(f"📍 API Server: {self.api_host}:{self.api_port}")
        logger.info(f"🎨 UI Port: {self.ui_port}")

        if self.local_dev_mode:
            logger.info("\n⚠️  LOCAL DEVELOPMENT MODE ACTIVE")
            logger.info("   All write operations enabled!")

        logger.info("\n📦 Storage:")
        logger.info(f"  • Weaviate: {self.weaviate_url}")
        logger.info(f"  • Redis: {self.redis_url}")
        logger.info(f"  • Supermemory: {self.supermemory_db}")

        logger.info("\n✅ Active Features:")
        for feature, enabled in self.get_active_features().items():
            status = "✓" if enabled else "✗"
            logger.info(f"  {status} {feature}")

        logger.info("\n🔑 API Keys:")
        validations = self.validate_required_keys()
        for service, valid in validations.items():
            status = "✓" if valid else "✗"
            logger.info(f"  {status} {service}")

        logger.info("=" * 60 + "\n")


# Singleton instance
settings = AppSettings()

# Export commonly used values
API_PORT = settings.api_port
WEAVIATE_URL = settings.weaviate_url
REDIS_URL = settings.redis_url
LOCAL_DEV_MODE = settings.local_dev_mode
