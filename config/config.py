import os

class Settings:
    # MCP HTTP server (optional; stdio handled by VS Code)
    host: str = os.getenv("MCP_HOST", "127.0.0.1")
    port: int = int(os.getenv("MCP_PORT", "8765"))

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

settings = Settings()
