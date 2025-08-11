"""
Test configuration for Enhanced MCP Server
Provides minimal configuration for local testing without external dependencies
"""

from pydantic import BaseModel
from typing import Optional
import os


class TestSettings(BaseModel):
    # Environment Configuration
    ENVIRONMENT: str = "test"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Database Configuration (using in-memory for testing)
    DATABASE_URL: str = "sqlite:///test.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Qdrant Configuration (using in-memory for testing)
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = ""

    # MCP Configuration
    MCP_PORT: int = 8001
    MCP_GATEWAY_PORT: int = 8002

    # LLM Configuration
    LLM_PROVIDER: str = "openrouter"
    CACHE_TTL_SECONDS: int = 300
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.7

    # API Keys (using test values)
    OPENAI_API_KEY: str = "test-openai-key"
    ANTHROPIC_API_KEY: str = "test-anthropic-key"
    GEMINI_API_KEY: str = "test-gemini-key"
    GROK_API_KEY: str = "test-grok-key"
    GROQ_API_KEY: str = "test-groq-key"
    DEEPSEEK_API_KEY: str = "test-deepseek-key"
    OPENROUTER_API_KEY: str = "test-openrouter-key"
    PORTKEY_API_KEY: str = "test-portkey-key"
    LAMBDA_API_KEY: str = "test-lambda-key"
    EXA_API_KEY: str = "test-exa-key"

    # Security Configuration (using test values)
    SECRET_KEY: str = "test-secret-key-for-testing-only"
    ENCRYPTION_KEY: str = "test-encryption-key-exactly-32-char"
    JWT_SECRET: str = "test-jwt-secret-for-testing-only"
    API_SALT: str = "test-api-salt"

    # Service Endpoints (using localhost for testing)
    SOPHIA_API_ENDPOINT: str = "http://localhost:8000"
    SOPHIA_MCP_ENDPOINT: str = "http://localhost:8001"
    SOPHIA_FRONTEND_ENDPOINT: str = "http://localhost:3000"
    LAMBDA_GATEWAY_ENDPOINT: str = "http://localhost:8080"


# Create test settings instance
settings = TestSettings()

