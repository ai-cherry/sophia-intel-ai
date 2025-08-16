"""Environment configuration and validation with production guardrails"""
import os
from typing import List
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
import structlog

logger = structlog.get_logger()

class Config(BaseSettings):
    """Environment configuration with fail-fast validation"""
    
    # Environment
    env: str = Field(default="development", description="Environment (development/production)")
    debug: bool = Field(default=True, description="Debug mode")
    log_level: str = Field(default="info", description="Log level")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    cors_origins: List[str] = Field(default=["http://localhost:5173"], description="CORS origins")
    cors_allow_credentials: bool = Field(default=True, description="Allow CORS credentials")
    cors_max_age: int = Field(default=600, description="CORS preflight cache time in seconds")
    
    # OpenRouter (required in production)
    openrouter_api_key: str = Field(default="", description="OpenRouter API key")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1", description="OpenRouter base URL")
    
    # Optional services (can be empty in development)
    qdrant_url: str = Field(default="", description="Qdrant URL")
    qdrant_api_key: str = Field(default="", description="Qdrant API key")
    postgres_url: str = Field(default="", description="PostgreSQL URL")
    brightdata_api_key: str = Field(default="", description="BrightData API key")
    openai_api_key: str = Field(default="", description="OpenAI API key")
    elevenlabs_api_key: str = Field(default="", description="ElevenLabs API key")
    github_pat: str = Field(default="", description="GitHub Personal Access Token")
    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False

def validate_environment() -> Config:
    """Validate environment configuration with fail-fast for production"""
    config = Config()
    
    logger.info("environment_validation", env=config.env, debug=config.debug)
    
    if config.env == "production":
        # Production requires these keys - FAIL FAST
        required_keys = [
            ("openrouter_api_key", config.openrouter_api_key, "OpenRouter API key is required for AI functionality"),
        ]
        
        # Optional but recommended for full functionality
        recommended_keys = [
            ("qdrant_api_key", config.qdrant_api_key, "Qdrant API key recommended for memory functionality"),
            ("postgres_url", config.postgres_url, "PostgreSQL URL recommended for persistent storage"),
            ("github_pat", config.github_pat, "GitHub PAT recommended for code operations"),
        ]
        
        # Check required keys
        missing_required = []
        for key, value, description in required_keys:
            if not value:
                missing_required.append(f"{key}: {description}")
        
        if missing_required:
            error_msg = f"PRODUCTION DEPLOYMENT BLOCKED - Missing required environment variables:\n" + "\n".join(f"  - {msg}" for msg in missing_required)
            logger.error("production_validation_failed", missing_keys=missing_required)
            raise ValueError(error_msg)
        
        # Warn about missing recommended keys
        missing_recommended = []
        for key, value, description in recommended_keys:
            if not value:
                missing_recommended.append(f"{key}: {description}")
        
        if missing_recommended:
            logger.warning("production_validation_warnings", missing_keys=missing_recommended)
        
        # Disable debug mode in production
        if config.debug:
            logger.warning("production_debug_disabled", original_debug=config.debug)
            config.debug = False
        
        logger.info("production_validation_passed", required_keys_present=len(required_keys))
    
    return config
