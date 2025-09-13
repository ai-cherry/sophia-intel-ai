from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class AIMLSettings:
    base_url: str
    api_key: str | None
    enabled: bool
    router_token: str | None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.base_url)


def get_settings() -> AIMLSettings:
    """Load AIMLAPI settings from environment.

    Uses env vars:
      - AIMLAPI_BASE (default https://api.aimlapi.com/v1)
      - AIMLAPI_API_KEY (required when enabled)
      - AIML_ENHANCED_ENABLED (default false)
      - AIML_ROUTER_TOKEN (optional bearer gate)
    """
    base = os.getenv("AIMLAPI_BASE", "https://api.aimlapi.com/v1").rstrip("/")
    key = os.getenv("AIMLAPI_API_KEY")
    enabled = os.getenv("AIML_ENHANCED_ENABLED", "false").lower() in ("1", "true", "yes")
    token = os.getenv("AIML_ROUTER_TOKEN")
    return AIMLSettings(base_url=base, api_key=key, enabled=enabled, router_token=token)

