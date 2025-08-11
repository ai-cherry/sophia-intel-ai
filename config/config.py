# config/config.py
from pydantic import BaseModel
from typing import Optional
import os
import yaml
from dotenv import load_dotenv


class Settings(BaseModel):
    # Environment Configuration
    ENVIRONMENT: str = "development"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Database Configuration
    DATABASE_URL: str
    REDIS_URL: str

    # Qdrant Configuration
    QDRANT_URL: str
    QDRANT_API_KEY: Optional[str] = ""

    # MCP Configuration
    MCP_PORT: int = 8001
    MCP_GATEWAY_PORT: int = 8002

    # LLM Configuration
    LLM_PROVIDER: str = "openrouter"
    CACHE_TTL_SECONDS: int = 300
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.7

    # API Keys
    OPENROUTER_API_KEY: str = ""
    PORTKEY_API_KEY: str = ""
    LAMBDA_API_KEY: str = ""
    EXA_API_KEY: str = ""

    # Security Configuration
    SECRET_KEY: str
    ENCRYPTION_KEY: str
    JWT_SECRET: str
    API_SALT: str

    # Service Endpoints
    SOPHIA_API_ENDPOINT: str
    SOPHIA_MCP_ENDPOINT: str
    SOPHIA_FRONTEND_ENDPOINT: str
    LAMBDA_GATEWAY_ENDPOINT: str

    # Agent Configuration
    AGNO_STORAGE_DB: str = "data/agents.db"
    AGENT_CONCURRENCY: int = 2
    AGENT_TIMEOUT_SECONDS: int = 300

    # Memory Configuration
    MEMORY_COLLECTION_NAME: str = "code_memory"
    EMBEDDING_DIMENSION: int = 384
    MAX_CONTEXT_LENGTH: int = 10000

    # Monitoring Configuration
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    LOG_LEVEL: str = "INFO"


def load_settings() -> Settings:
    """Load settings from YAML file with environment variable overrides."""
    load_dotenv()  # loads .env if present

    with open("config/sophia.yaml", "r") as f:
        data = yaml.safe_load(f) or {}

    # Apply environment variable overrides with proper type conversion
    for key, value in data.items():
        if key in os.environ:
            env_value = os.environ[key]

            # Type conversion based on original value type
            if isinstance(value, bool):
                data[key] = env_value.lower() in ("true", "1", "yes", "on")
            elif isinstance(value, int):
                try:
                    data[key] = int(env_value)
                except ValueError:
                    data[key] = value  # Keep original if conversion fails
            elif isinstance(value, float):
                try:
                    data[key] = float(env_value)
                except ValueError:
                    data[key] = value  # Keep original if conversion fails
            else:
                data[key] = env_value

    return Settings(**data)


settings = load_settings()
