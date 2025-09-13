import os
from pathlib import Path
from typing import Optional, Dict
class SecureEnvironmentManager:
    """Centralized environment variable access with optional local vault support.
    - Primary source: OS environment
    - Optional source: ~/.config//env (KEY=VALUE lines)
    - No secrets are stored in-repo.
    """
    def __init__(self, vault_path: Optional[str] = None) -> None:
        self.vault_path = Path(vault_path or "~/.config//env").expanduser()
        self._vault_cache: Dict[str, str] = {}
        self._load_vault_if_present()
    def _load_vault_if_present(self) -> None:
        if not self.vault_path.exists() or not self.vault_path.is_file():
            return
        try:
            for line in self.vault_path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                self._vault_cache[k.strip()] = v.strip()
        except Exception:
            # Silent failover to OS env only
            self._vault_cache = {}
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Return environment value for key with fallback to local vault file."""
        if key in os.environ:
            return os.environ.get(key)
        return self._vault_cache.get(key, default)
    def require(self, key: str) -> str:
        """Like get(), but raises if the key is not found."""
        val = self.get(key)
        if not val:
            raise RuntimeError(
                f"Missing required environment variable: {key}. "
                f"Set it in your shell or in {self.vault_path}"
            )
        return val
