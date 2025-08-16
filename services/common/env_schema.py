"""
SOPHIA Intel Environment Schema Validation
Pydantic-based environment validation with fail-fast startup checks
"""

import os
import json
from typing import Optional
from pydantic import BaseModel, AnyHttpUrl, Field, validator
import logging

logger = logging.getLogger(__name__)

class EnvSchema(BaseModel):
    """
    Environment schema for SOPHIA Intel services
    Validates all required configuration at startup
    """
    
    # Core environment
    ENV: str = Field(..., pattern="^(dev|staging|prod)$", description="Environment: dev, staging, or prod")
    DEBUG: bool = Field(default=False, description="Debug mode flag")
    LOG_LEVEL: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    
    # API Configuration
    API_HOST: str = Field(default="0.0.0.0", description="API server host")
    API_PORT: int = Field(default=5000, ge=1, le=65535, description="API server port")
    API_WORKERS: int = Field(default=1, ge=1, le=32, description="Number of API workers")
    
    # AI Services
    OPENROUTER_API_KEY: str = Field(..., min_length=10, description="OpenRouter API key for AI models")
    OPENROUTER_BASE_URL: AnyHttpUrl = Field(default="https://openrouter.ai/api/v1", description="OpenRouter API base URL")
    OPENROUTER_MODEL: str = Field(default="anthropic/claude-3.5-sonnet", description="Default OpenRouter model")
    
    OPENAI_API_KEY: str = Field(..., min_length=10, description="OpenAI API key for STT/TTS")
    OPENAI_BASE_URL: AnyHttpUrl = Field(default="https://api.openai.com/v1", description="OpenAI API base URL")
    
    ELEVENLABS_API_KEY: str = Field(..., min_length=10, description="ElevenLabs API key for TTS")
    ELEVENLABS_VOICE_ID: Optional[str] = Field(default=None, description="ElevenLabs voice ID")
    
    # MCP Services
    MCP_CODE_URL: AnyHttpUrl = Field(..., description="MCP Code Server URL")
    MCP_RESEARCH_URL: AnyHttpUrl = Field(..., description="BrightData Research MCP URL") 
    MCP_EMBEDDING_URL: AnyHttpUrl = Field(..., description="Embedding MCP URL")
    MCP_TELEMETRY_URL: AnyHttpUrl = Field(..., description="Telemetry MCP URL")
    MCP_NOTION_URL: AnyHttpUrl = Field(..., description="Notion Sync MCP URL")
    
    # Vector Database
    QDRANT_URL: AnyHttpUrl = Field(..., description="Qdrant vector database URL")
    QDRANT_API_KEY: str = Field(..., min_length=10, description="Qdrant API key")
    QDRANT_COLLECTION: str = Field(default="sophia_memory_prod", description="Qdrant collection name")
    QDRANT_TIMEOUT: int = Field(default=30, ge=5, le=300, description="Qdrant timeout in seconds")
    
    # Database
    DATABASE_URL: AnyHttpUrl = Field(..., description="PostgreSQL database URL")
    REDIS_URL: AnyHttpUrl = Field(..., description="Redis cache URL")
    
    # GitHub Integration
    GITHUB_PAT: str = Field(..., min_length=10, description="GitHub Personal Access Token")
    GITHUB_ORG: str = Field(default="ai-cherry", description="GitHub organization")
    GITHUB_REPO: str = Field(default="sophia-intel", description="GitHub repository")
    
    # Research Services
    BRIGHTDATA_API_KEY: str = Field(..., min_length=10, description="BrightData API key for web scraping")
    NOTION_API_KEY: str = Field(..., min_length=10, description="Notion API key")
    
    # Voice Configuration
    TTS_PROVIDER: str = Field(default="elevenlabs", pattern="^(elevenlabs|openai|none)$", description="Text-to-speech provider")
    STT_PROVIDER: str = Field(default="whisper", pattern="^(whisper|openai-realtime)$", description="Speech-to-text provider")
    
    # Feature Flags
    FEATURE_VOICE_ENABLED: bool = Field(default=True, description="Enable voice features")
    FEATURE_RESEARCH_ENABLED: bool = Field(default=True, description="Enable research features")
    FEATURE_CODE_GENERATION: bool = Field(default=True, description="Enable code generation")
    FEATURE_MEMORY_ENABLED: bool = Field(default=True, description="Enable memory features")
    FEATURE_TELEMETRY_ENABLED: bool = Field(default=True, description="Enable telemetry")
    
    # Security & CORS
    JWT_SECRET_KEY: Optional[str] = Field(default=None, description="JWT secret key")
    CORS_ORIGINS: str = Field(default="http://localhost:3000,https://www.sophia-intel.ai", description="CORS allowed origins")
    
    # Production Guardrails
    MOCK_SERVICES: bool = Field(default=False, description="Enable mock services (dev only)")
    MOCK_EMBEDDINGS: bool = Field(default=False, description="Enable mock embeddings (dev only)")
    ALLOW_HASH_EMBEDDINGS: bool = Field(default=False, description="Allow hash-based embeddings (dev only)")
    
    @validator('MOCK_SERVICES', 'MOCK_EMBEDDINGS', 'ALLOW_HASH_EMBEDDINGS')
    def validate_production_guardrails(cls, v, values):
        """Ensure no mock services in production"""
        if values.get('ENV') == 'prod' and v:
            raise ValueError("Mock services not allowed in production environment")
        return v
    
    @validator('DEBUG')
    def validate_debug_in_production(cls, v, values):
        """Warn about debug mode in production"""
        if values.get('ENV') == 'prod' and v:
            logger.warning("DEBUG=true is not recommended in production")
        return v
    
    class Config:
        env_file = '.env'
        case_sensitive = True


def load_and_validate() -> EnvSchema:
    """
    Load and validate environment configuration
    
    Returns:
        EnvSchema: Validated environment configuration
        
    Raises:
        SystemExit: If validation fails (fail-fast behavior)
    """
    try:
        # Get all environment variables that match schema fields
        env_data = {}
        for field_name in EnvSchema.__fields__.keys():
            value = os.getenv(field_name)
            if value is not None:
                # Convert string booleans
                if field_name in ['DEBUG', 'FEATURE_VOICE_ENABLED', 'FEATURE_RESEARCH_ENABLED', 
                                'FEATURE_CODE_GENERATION', 'FEATURE_MEMORY_ENABLED', 'FEATURE_TELEMETRY_ENABLED',
                                'MOCK_SERVICES', 'MOCK_EMBEDDINGS', 'ALLOW_HASH_EMBEDDINGS']:
                    env_data[field_name] = value.lower() in ('true', '1', 'yes', 'on')
                elif field_name in ['API_PORT', 'API_WORKERS', 'QDRANT_TIMEOUT']:
                    env_data[field_name] = int(value)
                else:
                    env_data[field_name] = value
        
        # Validate with Pydantic
        config = EnvSchema(**env_data)
        
        logger.info(f"Environment validation successful for {config.ENV} environment")
        logger.info(f"Features enabled: voice={config.FEATURE_VOICE_ENABLED}, research={config.FEATURE_RESEARCH_ENABLED}, "
                   f"code={config.FEATURE_CODE_GENERATION}, memory={config.FEATURE_MEMORY_ENABLED}")
        
        return config
        
    except Exception as e:
        error_msg = f"[ENV] Invalid/missing configuration: {e}"
        logger.error(error_msg)
        raise SystemExit(error_msg)


def get_config_export(config: EnvSchema) -> dict:
    """
    Export non-secret configuration for debugging and drift detection
    
    Args:
        config: Validated environment configuration
        
    Returns:
        dict: Non-secret configuration data
    """
    export_data = config.dict()
    
    # Mask sensitive fields
    sensitive_fields = [
        'OPENROUTER_API_KEY', 'OPENAI_API_KEY', 'ELEVENLABS_API_KEY',
        'QDRANT_API_KEY', 'GITHUB_PAT', 'BRIGHTDATA_API_KEY', 'NOTION_API_KEY',
        'JWT_SECRET_KEY', 'DATABASE_URL', 'REDIS_URL'
    ]
    
    for field in sensitive_fields:
        if field in export_data and export_data[field]:
            # Show first 4 and last 4 characters
            value = str(export_data[field])
            if len(value) > 8:
                export_data[field] = f"{value[:4]}...{value[-4:]}"
            else:
                export_data[field] = "***masked***"
    
    return {
        "config": export_data,
        "validation_timestamp": os.environ.get('VALIDATION_TIMESTAMP', 'unknown'),
        "schema_version": "1.0.0"
    }


# Global configuration instance (loaded once)
ENV_CONFIG: Optional[EnvSchema] = None

def get_config() -> EnvSchema:
    """
    Get the global configuration instance
    Loads and validates on first call
    
    Returns:
        EnvSchema: Global configuration instance
    """
    global ENV_CONFIG
    if ENV_CONFIG is None:
        ENV_CONFIG = load_and_validate()
    return ENV_CONFIG


if __name__ == "__main__":
    # CLI usage for testing
    import sys
    
    try:
        config = load_and_validate()
        print("✅ Environment validation passed")
        print(f"Environment: {config.ENV}")
        print(f"API: {config.API_HOST}:{config.API_PORT}")
        print(f"Features: voice={config.FEATURE_VOICE_ENABLED}, research={config.FEATURE_RESEARCH_ENABLED}")
        
        # Export config for debugging
        export = get_config_export(config)
        print(f"Config export available with {len(export['config'])} fields")
        
        sys.exit(0)
        
    except SystemExit as e:
        print(f"❌ Environment validation failed: {e}")
        sys.exit(1)

