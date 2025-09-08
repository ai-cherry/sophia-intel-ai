#!/usr/bin/env python3
"""
UNIFIED CREDENTIAL MANAGER
Centralized, encrypted credential management for all Sophia-Intel-AI services
"""

import hashlib
import json
import logging
import os
import secrets
from base64 import b64encode
from pathlib import Path
from typing import Any, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class UnifiedCredentialManager:
    """
    Secure credential management with encryption and access control
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = (
            config_path or Path(__file__).parent.parent.parent / "config" / "credentials.enc"
        )
        self.config_path.parent.mkdir(exist_ok=True)

        # Generate or load encryption key
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)

        # Load existing credentials
        self.credentials = self._load_credentials()

    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key based on system info"""
        key_file = self.config_path.parent / ".key"

        if key_file.exists():
            with open(key_file, "rb") as f:
                return f.read()

        # Generate new key from system entropy
        password = os.urandom(32)
        salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        key = b64encode(kdf.derive(password))

        # Store key securely
        with open(key_file, "wb") as f:
            f.write(key)

        # Secure file permissions
        os.chmod(key_file, 0o600)

        logger.info("🔐 New encryption key generated and stored securely")
        return key

    def _load_credentials(self) -> dict[str, Any]:
        """Load and decrypt credentials"""
        if not self.config_path.exists():
            return self._initialize_default_credentials()

        try:
            with open(self.config_path, "rb") as f:
                encrypted_data = f.read()

            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())

        except Exception as e:
            logger.warning(f"Failed to load credentials, using defaults: {e}")
            return self._initialize_default_credentials()

    def _initialize_default_credentials(self) -> dict[str, Any]:
        """Initialize with secure defaults"""
        default_credentials = {
            "redis": {
                "host": "localhost",
                "port": 6379,
                "password": self._generate_secure_password(),
                "db": 0,
                "url": None,  # Will be constructed
            },
            "database": {
                "sqlite_path": str(Path(__file__).parent.parent.parent / "data" / "sophia.db"),
                "postgres_url": None,  # Optional PostgreSQL
                "encryption_key": self._generate_secure_password(),
            },
            "api_keys": {
                "portkey_api_key": os.getenv("PORTKEY_API_KEY", ""),
                "openrouter_api_key": os.getenv("OPENROUTER_API_KEY", ""),
                "linear_api_key": os.getenv("LINEAR_API_KEY", ""),
                "airtable_api_key": os.getenv("AIRTABLE_API_KEY", ""),
            },
            "security": {
                "jwt_secret": self._generate_secure_password(),
                "api_rate_limit": 1000,
                "max_connections": 100,
                "session_timeout": 3600,
            },
            "mcp": {
                "enabled_domains": ["artemis", "sophia", "shared"],
                "max_concurrent_operations": 50,
                "operation_timeout": 30,
                "health_check_interval": 30,
            },
            "metadata": {"created": "2025-09-06T00:00:00Z", "version": "1.0.0", "checksum": None},
        }

        # Calculate checksum for integrity
        default_credentials["metadata"]["checksum"] = self._calculate_checksum(default_credentials)

        # Save encrypted credentials
        self._save_credentials(default_credentials)

        logger.info("🔒 Default credentials initialized with strong encryption")
        return default_credentials

    def _generate_secure_password(self, length: int = 32) -> str:
        """Generate cryptographically secure password"""
        return secrets.token_urlsafe(length)

    def _calculate_checksum(self, data: dict[str, Any]) -> str:
        """Calculate SHA-256 checksum of credentials"""
        # Exclude metadata from checksum calculation
        data_copy = data.copy()
        if "metadata" in data_copy:
            del data_copy["metadata"]

        json_str = json.dumps(data_copy, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def _save_credentials(self, credentials: dict[str, Any]):
        """Encrypt and save credentials"""
        try:
            # Update checksum
            credentials["metadata"]["checksum"] = self._calculate_checksum(credentials)

            # Encrypt and save
            json_data = json.dumps(credentials, indent=2).encode()
            encrypted_data = self.cipher.encrypt(json_data)

            with open(self.config_path, "wb") as f:
                f.write(encrypted_data)

            # Secure file permissions
            os.chmod(self.config_path, 0o600)

            self.credentials = credentials
            logger.info("💾 Credentials saved and encrypted successfully")

        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            raise

    def get_redis_config(self) -> dict[str, Any]:
        """Get Redis configuration with URL construction"""
        redis_config = self.credentials["redis"].copy()

        # Allow overriding via environment for containerized/dev setups
        env_url = os.getenv("REDIS_URL")
        if env_url:
            redis_config["url"] = env_url
            return redis_config

        # Construct Redis URL if not provided
        if not redis_config["url"]:
            if redis_config["password"]:
                redis_config["url"] = (
                    f"redis://:{redis_config['password']}@{redis_config['host']}:{redis_config['port']}/{redis_config['db']}"
                )
            else:
                redis_config["url"] = (
                    f"redis://{redis_config['host']}:{redis_config['port']}/{redis_config['db']}"
                )

        return redis_config

    def get_database_config(self) -> dict[str, Any]:
        """Get database configuration"""
        return self.credentials["database"].copy()

    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for specific service"""
        return self.credentials["api_keys"].get(service)

    def set_api_key(self, service: str, api_key: str):
        """Set API key for specific service"""
        self.credentials["api_keys"][service] = api_key
        self._save_credentials(self.credentials)
        logger.info(f"🔑 API key updated for {service}")

    def get_security_config(self) -> dict[str, Any]:
        """Get security configuration"""
        return self.credentials["security"].copy()

    def get_mcp_config(self) -> dict[str, Any]:
        """Get MCP configuration"""
        return self.credentials["mcp"].copy()

    def update_redis_password(self, new_password: Optional[str] = None):
        """Update Redis password"""
        if new_password is None:
            new_password = self._generate_secure_password()

        self.credentials["redis"]["password"] = new_password
        self.credentials["redis"]["url"] = None  # Force URL reconstruction
        self._save_credentials(self.credentials)

        logger.info("🔐 Redis password updated")
        return new_password

    def verify_integrity(self) -> bool:
        """Verify credential integrity"""
        stored_checksum = self.credentials.get("metadata", {}).get("checksum")
        if not stored_checksum:
            logger.warning("⚠️ No checksum found in credentials")
            return False

        calculated_checksum = self._calculate_checksum(self.credentials)

        if stored_checksum != calculated_checksum:
            logger.error("❌ Credential integrity check failed!")
            return False

        logger.info("✅ Credential integrity verified")
        return True

    def export_config_for_service(self, service: str) -> dict[str, Any]:
        """Export configuration for specific service"""
        configs = {
            "redis": self.get_redis_config(),
            "unified_server": {
                "redis": self.get_redis_config(),
                "database": self.get_database_config(),
                "api_keys": self.credentials["api_keys"],
                "security": self.get_security_config(),
                "mcp": self.get_mcp_config(),
            },
            "mcp_orchestrator": {
                "redis": self.get_redis_config(),
                "mcp": self.get_mcp_config(),
                "security": self.get_security_config(),
            },
        }

        return configs.get(service, {})

    def get_redis_auth_string(self) -> str:
        """Get Redis authentication string for configuration files"""
        redis_config = self.get_redis_config()
        if redis_config["password"]:
            return f"requirepass {redis_config['password']}"
        return "# No authentication required"

    def create_redis_config_file(self, output_path: Optional[Path] = None) -> Path:
        """Create Redis configuration file with authentication"""
        if output_path is None:
            output_path = Path(__file__).parent.parent.parent / "config" / "redis.conf"

        output_path.parent.mkdir(exist_ok=True)

        redis_config = self.get_redis_config()

        config_content = f"""# Sophia Intel AI - Optimized Redis Configuration
# Generated automatically - DO NOT EDIT MANUALLY

# Network and Security
bind 127.0.0.1
port {redis_config["port"]}
protected-mode yes
{self.get_redis_auth_string()}

# Memory and Performance
maxmemory 256mb
maxmemory-policy allkeys-lru
tcp-keepalive 300
timeout 0

# Persistence
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename sophia-redis.rdb
dir {Path(__file__).parent.parent.parent / "data"}

# Logging
loglevel notice
logfile {Path(__file__).parent.parent.parent / "logs" / "redis.log"}

# Client Configuration
tcp-backlog 511
databases 16

# Advanced
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
hll-sparse-max-bytes 3000
"""

        with open(output_path, "w") as f:
            f.write(config_content)

        # Secure file permissions
        os.chmod(output_path, 0o600)

        logger.info(f"📄 Redis configuration created at {output_path}")
        return output_path

    def get_connection_info(self) -> dict[str, Any]:
        """Get connection info for services"""
        return {
            "redis": {
                "url": self.get_redis_config()["url"],
                "health_check": "Redis PING command",
                "required_for": ["memory", "cache", "sessions"],
            },
            "database": {
                "sqlite_path": self.get_database_config()["sqlite_path"],
                "encrypted": True,
                "required_for": ["persistent_storage", "user_data"],
            },
            "mcp": {
                "domains": self.get_mcp_config()["enabled_domains"],
                "max_operations": self.get_mcp_config()["max_concurrent_operations"],
                "required_for": ["ai_assistants", "automation"],
            },
        }


# Global instance for easy access
_credential_manager = None


def get_credential_manager() -> UnifiedCredentialManager:
    """Get the global credential manager instance"""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = UnifiedCredentialManager()
    return _credential_manager
