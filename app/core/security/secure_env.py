import os
from pathlib import Path
from typing import Optional, Dict
class SecureEnvironmentManager:
    """Centralized environment variable access.
    - Single source: OS environment (loaded by ./sophia from ./.env.master)
    - No fallbacks to home config or dot-env files.
    """
    def __init__(self, vault_path: Optional[str] = None) -> None:
        self._vault_cache: Dict[str, str] = {}
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Return environment value for key (no fallback)."""
        if key in os.environ:
            return os.environ.get(key)
        return default
    def require(self, key: str) -> str:
        """Like get(), but raises if the key is not found."""
        val = self.get(key)
        if not val:
            raise RuntimeError(
                f"Missing required environment variable: {key}. "
                f"Set it in ./.env.master and start via ./sophia"
            )
        return val
