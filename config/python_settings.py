from __future__ import annotations

import os
from typing import Literal, Optional

try:
    # Pydantic v2 is preferred if available
    from pydantic import BaseModel, ValidationError
except Exception:  # pragma: no cover - fallback to minimal shim
    BaseModel = object  # type: ignore
    ValidationError = Exception  # type: ignore


class Settings(BaseModel):  # type: ignore[misc]
    APP_ENV: Literal["dev", "staging", "prod"] = "dev"
    SERVICE_NAME: str = "sophia-intel-ai"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    AI_ROUTER: Literal["portkey", "openrouter", "direct"] = "direct"
    AI_PROVIDER: Literal["openai", "anthropic", "gemini", "mistral", "groq", "xai", "cohere", "ai21"] = (
        "openai"
    )

    HTTP_DEFAULT_TIMEOUT_MS: int = 15000
    HTTP_RETRY_MAX: int = 3
    HTTP_BACKOFF_BASE_MS: int = 200

    POSTGRES_URL: Optional[str] = None
    REDIS_URL: Optional[str] = None
    WEAVIATE_URL: Optional[str] = None
    NEO4J_URL: Optional[str] = None

    MCP_TOKEN: Optional[str] = None
    MCP_DEV_BYPASS: Literal["0", "1"] = "0"
    RATE_LIMIT_RPM: int = 120
    READ_ONLY: Literal["0", "1"] = "0"

    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_GEMINI_API_KEY: Optional[str] = None
    MISTRAL_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    XAI_API_KEY: Optional[str] = None
    COHERE_API_KEY: Optional[str] = None
    AI21_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    PORTKEY_API_KEY: Optional[str] = None


def load_env_file(path: str) -> dict[str, str]:
    """Parse a simple KEY=VALUE env file (no exports, comments allowed)."""
    env: dict[str, str] = {}
    if not os.path.exists(path):
        return env
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def settings_from_env(dev_env_file: str = ".env.master") -> Settings:
    # Load process env
    merged: dict[str, str] = {}

    # In dev, read from .env.master first (lowest precedence) then overlay process env
    if os.getenv("APP_ENV", "dev") == "dev" and os.path.exists(dev_env_file):
        merged.update(load_env_file(dev_env_file))

    # Overlay with real environment variables (highest precedence)
    for k, v in os.environ.items():
        merged[k] = v

    try:
        return Settings(**merged)  # type: ignore[arg-type]
    except ValidationError as e:  # pragma: no cover
        raise RuntimeError(f"Invalid environment configuration: {e}")


if __name__ == "__main__":  # Manual validation helper
    s = settings_from_env()
    print("Environment OK:")
    for k, v in s.__dict__.items():
        if isinstance(v, str) and v and v.lower().endswith("_key"):
            print(f"- {k}=***")
        else:
            print(f"- {k}={v}")

