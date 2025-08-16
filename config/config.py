import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl

class Settings(BaseSettings):
    # MCP HTTP server (optional; stdio handled by VS Code)
    host: str = os.getenv("MCP_HOST", "127.0.0.1")
    port: int = int(os.getenv("MCP_PORT", "8765"))

    # Orchestrator Configuration
    ORCHESTRATOR_URL: str = os.getenv("ORCHESTRATOR_URL", "http://localhost:8001")
    MCP_BASE_URL: str = os.getenv("MCP_BASE_URL", "http://localhost:8001")

    # Sessions
    session_dir: str = os.getenv("MCP_SESSION_DIR", ".sophia_sessions")

    # Qdrant (cloud)
    qdrant_url: str = os.getenv("QDRANT_URL", "")
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "repo_docs")

    # Redis (cloud)
    redis_url: str = os.getenv("REDIS_URL", "")
    redis_host: str = os.getenv("REDIS_HOST", "")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: str = os.getenv("REDIS_PASSWORD", "")

    # API Keys (required)
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    LAMBDA_CLOUD_API_KEY: str = os.getenv("LAMBDA_CLOUD_API_KEY", "")
    GITHUB_PAT: str = os.getenv("GITHUB_PAT", "")
    
    # Optional API Keys
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    class Config:
        env_file = ".env"

settings = Settings()
