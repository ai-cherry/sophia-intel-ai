"""
Secure Secrets Management System
Handles all API keys and sensitive configuration data
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Optional
from cryptography.fernet import Fernet
logger = logging.getLogger(__name__)
class SecretsManager:
    """
    Centralized secure secrets management for the Sophia Intel AI platform.
    Provides encrypted storage, environment variable fallback, and secure access patterns.
    """
    def __init__(self, vault_path: Optional[Path] = None):
        """
        Initialize the secrets manager
        Args:
            vault_path: Path to encrypted vault file. Defaults to ~/.sophia/vault.enc
        """
        self.vault_path = vault_path or (Path.home() / ".sophia" / "vault.enc")
        self.key_path = Path.home() / ".sophia" / "key.bin"
        self._cipher = None
        self._cache = {}
        self._ensure_directories()
    def _ensure_directories(self) -> None:
        """Create necessary directories for secure storage"""
        self.vault_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    def _get_or_create_key(self) -> bytes:
        """Get existing encryption key or create new one"""
        if self.key_path.exists():
            with open(self.key_path, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_path, "wb") as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(self.key_path, 0o600)
            return key
    @property
    def cipher(self) -> Fernet:
        """Get or create cipher for encryption/decryption"""
        if self._cipher is None:
            key = self._get_or_create_key()
            self._cipher = Fernet(key)
        return self._cipher
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a secret value from environment, vault, or default
        Priority order:
        1. Environment variable
        2. Cached value
        3. Encrypted vault
        4. Default value
        Args:
            key: Secret key name (e.g., 'OPENAI_API_KEY')
            default: Default value if not found
        Returns:
            Secret value or None if not found
        """
        # Check environment first
        env_value = os.getenv(key)
        if env_value:
            return env_value
        # Check cache
        if key in self._cache:
            return self._cache[key]
        # Check vault
        vault_value = self._get_from_vault(key)
        if vault_value:
            self._cache[key] = vault_value
            return vault_value
        # Return default
        return default
    def set_secret(self, key: str, value: str) -> None:
        """
        Store a secret in the encrypted vault
        Args:
            key: Secret key name
            value: Secret value to store
        """
        # Load existing vault
        vault = self._load_vault()
        # Update value
        vault[key] = value
        # Save vault
        self._save_vault(vault)
        # Update cache
        self._cache[key] = value
        logger.info(f"Secret '{key}' stored securely")
    def _load_vault(self) -> dict[str, Any]:
        """Load and decrypt vault file"""
        if not self.vault_path.exists():
            return {}
        try:
            with open(self.vault_path, "rb") as f:
                encrypted_data = f.read()
            if encrypted_data:
                decrypted_data = self.cipher.decrypt(encrypted_data)
                return json.loads(decrypted_data.decode("utf-8"))
            return {}
        except Exception as e:
            logger.error(f"Failed to load vault: {e}")
            return {}
    def _save_vault(self, vault: dict[str, Any]) -> None:
        """Encrypt and save vault file"""
        try:
            json_data = json.dumps(vault).encode("utf-8")
            encrypted_data = self.cipher.encrypt(json_data)
            with open(self.vault_path, "wb") as f:
                f.write(encrypted_data)
            # Set restrictive permissions
            os.chmod(self.vault_path, 0o600)
        except Exception as e:
            logger.error(f"Failed to save vault: {e}")
            raise
    def _get_from_vault(self, key: str) -> Optional[str]:
        """Get a value from encrypted vault"""
        vault = self._load_vault()
        return vault.get(key)
    def delete_secret(self, key: str) -> bool:
        """
        Remove a secret from the vault
        Args:
            key: Secret key to remove
        Returns:
            True if removed, False if not found
        """
        vault = self._load_vault()
        if key in vault:
            del vault[key]
            self._save_vault(vault)
            # Remove from cache
            if key in self._cache:
                del self._cache[key]
            logger.info(f"Secret '{key}' removed")
            return True
        return False
    def list_secrets(self) -> list[str]:
        """
        List all secret keys (not values) in vault
        Returns:
            List of secret key names
        """
        vault = self._load_vault()
        return list(vault.keys())
    def validate_required_secrets(self, required: list[str]) -> dict[str, bool]:
        """
        Validate that required secrets are available
        Args:
            required: List of required secret keys
        Returns:
            Dict mapping keys to availability status
        """
        status = {}
        for key in required:
            status[key] = self.get_secret(key) is not None
        missing = [k for k, v in status.items() if not v]
        if missing:
            logger.warning(f"Missing required secrets: {missing}")
        return status
    def get_portkey_virtual_keys(self) -> dict[str, str]:
        """
        Get all Portkey virtual keys
        Returns:
            Dictionary of provider to virtual key mappings
        """
        vk_mapping = {
            "deepseek": "VK_DEEPSEEK",
            "openai": "VK_OPENAI",
            "anthropic": "VK_ANTHROPIC",
            "openrouter": "VK_OPENROUTER",
            "perplexity": "VK_PERPLEXITY",
            "groq": "VK_GROQ",
            "mistral": "VK_MISTRAL",
            "xai": "VK_XAI",
            "together": "VK_TOGETHER",
            "cohere": "VK_COHERE",
            "gemini": "VK_GEMINI",
            "huggingface": "VK_HUGGINGFACE",
            "milvus": "VK_MILVUS",
            "qdrant": "VK_QDRANT",
        }
        result = {}
        for provider, env_key in vk_mapping.items():
            vk = self.get_secret(env_key)
            if vk:
                result[provider] = vk
        return result
    def get_integration_credentials(self, integration: str) -> dict[str, Optional[str]]:
        """
        Get credentials for a specific integration
        Args:
            integration: Name of integration (e.g., 'gong', 'asana', 'linear')
        Returns:
            Dictionary of credential components
        """
        integration = integration.upper()
        # Common credential patterns
        patterns = {
            "api_key": f"{integration}_API_KEY",
            "api_secret": f"{integration}_API_SECRET",
            "access_token": f"{integration}_ACCESS_TOKEN",
            "refresh_token": f"{integration}_REFRESH_TOKEN",
            "client_id": f"{integration}_CLIENT_ID",
            "client_secret": f"{integration}_CLIENT_SECRET",
            "webhook_secret": f"{integration}_WEBHOOK_SECRET",
            "base_url": f"{integration}_BASE_URL",
        }
        credentials = {}
        for key, env_var in patterns.items():
            value = self.get_secret(env_var)
            if value:
                credentials[key] = value
        return credentials
    def rotate_secret(self, key: str, new_value: str) -> bool:
        """
        Rotate a secret value with audit logging
        Args:
            key: Secret key to rotate
            new_value: New secret value
        Returns:
            True if rotated successfully
        """
        old_exists = self.get_secret(key) is not None
        # Store new value
        self.set_secret(key, new_value)
        # Log rotation (without exposing values)
        action = "rotated" if old_exists else "created"
        logger.info(
            f"Secret '{key}' {action} at {os.environ.get('USER', 'unknown')}@{os.environ.get('HOSTNAME', 'unknown')}"
        )
        return True
# Global instance for easy access
_secrets_manager = None
def get_secrets_manager() -> SecretsManager:
    """Get global secrets manager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager
# Convenience functions
def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a secret value"""
    return get_secrets_manager().get_secret(key, default)
def set_secret(key: str, value: str) -> None:
    """Store a secret value"""
    get_secrets_manager().set_secret(key, value)
def validate_secrets(required: list[str]) -> dict[str, bool]:
    """Validate required secrets are available"""
    return get_secrets_manager().validate_required_secrets(required)
