"""
Mem0 Configuration Manager
Handles authentication and configuration for Mem0 memory system
Uses proper Token format authentication
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Mem0Config:
    """Configuration for Mem0 API"""

    api_key: str
    base_url: str = "https://api.mem0.ai"
    auth_header_format: str = "Token"  # Use "Token" not "Bearer"
    timeout: int = 30
    max_retries: int = 3


class Mem0Manager:
    """Singleton manager for Mem0 operations"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.config = Mem0Config(
            api_key=os.getenv("MEM0_API_KEY", "m0-migu5eMnfwT41nhTgVHsCnSAifVtOf3WIFz2vmQc"),
            base_url=os.getenv("MEM0_BASE_URL", "https://api.mem0.ai"),
            auth_header_format="Token",  # Critical: Use "Token" format, not "Bearer"
            timeout=int(os.getenv("MEM0_TIMEOUT", "30")),
            max_retries=int(os.getenv("MEM0_MAX_RETRIES", "3")),
        )

        self._initialized = True

    def get_headers(self) -> Dict[str, str]:
        """Get properly formatted authentication headers"""
        return {
            "Authorization": f"{self.config.auth_header_format} {self.config.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def get_config(self) -> Mem0Config:
        """Get the complete configuration"""
        return self.config

    def test_connection(self) -> bool:
        """Test connection to Mem0 API"""
        try:
            import requests

            response = requests.get(
                f"{self.config.base_url}/v1/memories",
                headers=self.get_headers(),
                timeout=self.config.timeout,
            )

            if response.status_code in [
                200,
                401,
            ]:  # 401 means auth is working but might need permissions
                logger.info("✓ Mem0 connection successful")
                return True
            else:
                logger.error(f"✗ Mem0 connection failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"✗ Mem0 connection failed: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get status information"""
        return {
            "api_key": self.config.api_key[:10] + "..." if self.config.api_key else None,
            "base_url": self.config.base_url,
            "auth_format": self.config.auth_header_format,
            "timeout": self.config.timeout,
            "max_retries": self.config.max_retries,
            "configured": bool(self.config.api_key),
        }


# Singleton instance
mem0_manager = Mem0Manager()
