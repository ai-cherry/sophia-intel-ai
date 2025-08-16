"""Environment configuration and validation"""
import os
from typing import List
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    """Environment configuration with validation"""
    
    # Environment
    env: str = Field(default="development", description="Environment (development/production)")
    debug: bool = Field(default=True, description="Debug mode")
    log_level: str = Field(default="info", description="Log level")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    cors_origins: List[str] = Field(default=["http://localhost:5173"], description="CORS origins")
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = False

def validate_environment() -> Config:
    """Validate environment configuration with fail-fast for production"""
    config = Config()
    
    if config.env == "production":
        # Production requires these keys
        required_keys = [
            ("openrouter_api_key", config.openrouter_api_key),
        ]
        
        missing = [key for key, value in required_keys if not value]
        if missing:
            raise ValueError(f"Production environment missing required keys: {missing}")
    
    return config
