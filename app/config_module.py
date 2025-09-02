"""
Configuration module for Sophia Intel AI
"""

import os
from typing import Any


class Config:
    """Application configuration"""

    def __init__(self):
        self.JWT_SECRET = os.getenv("JWT_SECRET", "sophia-intel-secret-key")
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
        self.PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY")
        self.LOCAL_DEV_MODE = os.getenv("LOCAL_DEV_MODE", "false").lower() == "true"
        self.AGENT_API_PORT = int(os.getenv("AGENT_API_PORT", "8003"))

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return getattr(self, key, default)

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary"""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith("_")
        }

# Global config instance
config = Config()
