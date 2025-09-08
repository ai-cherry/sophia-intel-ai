#!/usr/bin/env python3
"""
🏹 Lambda Labs Secrets Management
Production-grade secrets management for Lambda Labs infrastructure
"""

import base64
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

import yaml
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class LambdaLabsSecretsManager:
    """Secrets management for Lambda Labs infrastructure"""

    def __init__(self, config_path: str = "secrets-config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.secrets_dir = Path(
            self.config.get("secrets_dir", "/etc/sophia-ai/secrets")
        )
        self.secrets_dir.mkdir(parents=True, exist_ok=True)

        # Initialize encryption
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)

    def _load_config(self) -> dict[str, Any]:
        """Load secrets configuration"""
        try:
            with open(self.config_path) as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self._get_default_config()

    def _get_default_config(self) -> dict[str, Any]:
        """Get default secrets configuration"""
        return {
            "secrets_dir": "/etc/sophia-ai/secrets",
            "encryption_key_file": "/etc/sophia-ai/encryption.key",
            "secrets": {
                "database": {
                    "postgres_url": "postgresql://${DB_USER}:${DB_PASSWORD}@postgres-service:5432/sophia_ai",
                    "redis_url": "redis://redis-service:6379",
                    "qdrant_url": "http://qdrant-service:6333",
                },
                "api_keys": {
                    "openai_api_key": "",
                    "anthropic_api_key": "",
                    "lambda_labs_api_key": "",
                },
                "integrations": {
                    "hubspot_api_key": "",
                    "gong_api_key": "",
                    "slack_bot_token": "",
                    "github_token": "",
                },
            },
        }

    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key"""
        key_file = Path(
            self.config.get("encryption_key_file", "/etc/sophia-ai/encryption.key")
        )

        if key_file.exists():
            return key_file.read_bytes()
        else:
            # Generate new key
            key = Fernet.generate_key()
            key_file.parent.mkdir(parents=True, exist_ok=True)
            key_file.write_bytes(key)
            key_file.chmod(0o600)  # Read-only for owner
            return key

    def store_secret(self, category: str, key: str, value: str) -> bool:
        """Store an encrypted secret"""
        try:
            encrypted_value = self.cipher.encrypt(value.encode())

            secret_file = self.secrets_dir / f"{category}_{key}.secret"
            secret_file.write_bytes(encrypted_value)
            secret_file.chmod(0o600)

            logger.info(f"Stored secret: {category}/{key}")
            return True

        except Exception as e:
            logger.error(f"Failed to store secret {category}/{key}: {e}")
            return False

    def get_secret(self, category: str, key: str) -> str | None:
        """Retrieve and decrypt a secret"""
        try:
            secret_file = self.secrets_dir / f"{category}_{key}.secret"

            if not secret_file.exists():
                logger.warning(f"Secret not found: {category}/{key}")
                return None

            encrypted_value = secret_file.read_bytes()
            decrypted_value = self.cipher.decrypt(encrypted_value)

            return decrypted_value.decode()

        except Exception as e:
            logger.error(f"Failed to retrieve secret {category}/{key}: {e}")
            return None

    def initialize_secrets(self) -> bool:
        """Initialize all secrets from configuration"""
        try:
            for category, secrets in self.config["secrets"].items():
                for key, value in secrets.items():
                    if value:  # Only store non-empty values
                        self.store_secret(category, key, value)

            logger.info("All secrets initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize secrets: {e}")
            return False

    def create_kubernetes_secret(self, namespace: str = "sophia-ai") -> bool:
        """Create Kubernetes secret from stored secrets"""
        try:
            secret_data = {}

            # Collect all secrets
            for category, secrets in self.config["secrets"].items():
                for key in secrets.keys():
                    secret_value = self.get_secret(category, key)
                    if secret_value:
                        # Convert to Kubernetes secret format
                        k8s_key = key.replace("_", "-")
                        secret_data[k8s_key] = base64.b64encode(
                            secret_value.encode()
                        ).decode()

            # Create Kubernetes secret manifest
            secret_manifest = {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {
                    "name": "sophia-ai-secrets",
                    "namespace": namespace,
                    "labels": {
                        "app": "sophia-ai",
                        "component": "secrets",
                        "managed-by": "lambda-labs-secrets-manager",
                    },
                },
                "type": "Opaque",
                "data": secret_data,
            }

            # Apply the secret
            manifest_file = "/tmp/sophia-ai-secrets.yaml"
            with open(manifest_file, "w") as f:
                yaml.dump(secret_manifest, f)

            result = subprocess.run(
                ["kubectl", "apply", "-f", manifest_file],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                logger.info(f"Kubernetes secret created in namespace: {namespace}")
                os.remove(manifest_file)
                return True
            else:
                logger.error(f"Failed to create Kubernetes secret: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to create Kubernetes secret: {e}")
            return False

    def rotate_secret(self, category: str, key: str, new_value: str) -> bool:
        """Rotate a secret with zero-downtime"""
        try:
            # Store new secret
            if self.store_secret(category, key, new_value):
                # Update Kubernetes secret
                if self.create_kubernetes_secret():
                    # Trigger rolling restart of affected deployments
                    self._restart_affected_deployments(category, key)
                    logger.info(f"Secret rotated successfully: {category}/{key}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to rotate secret {category}/{key}: {e}")
            return False

    def _restart_affected_deployments(self, category: str, key: str):
        """Restart deployments affected by secret rotation"""
        # Map secrets to deployments
        deployment_map = {
            "database": ["super-memory-mcp", "business-intelligence-mcp"],
            "api_keys": ["super-memory-mcp", "business-intelligence-mcp"],
            "integrations": ["business-intelligence-mcp", "github-enhanced-mcp"],
        }

        deployments = deployment_map.get(category, [])

        for deployment in deployments:
            try:
                subprocess.run(
                    [
                        "kubectl",
                        "rollout",
                        "restart",
                        "deployment",
                        deployment,
                        "-n",
                        "sophia-ai",
                    ],
                    check=True,
                )
                logger.info(f"Restarted deployment: {deployment}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to restart deployment {deployment}: {e}")

    def backup_secrets(self, backup_path: str) -> bool:
        """Backup all secrets to encrypted file"""
        try:
            secrets_backup = {}

            for category, secrets in self.config["secrets"].items():
                secrets_backup[category] = {}
                for key in secrets.keys():
                    secret_value = self.get_secret(category, key)
                    if secret_value:
                        secrets_backup[category][key] = secret_value

            # Encrypt backup
            backup_data = json.dumps(secrets_backup)
            encrypted_backup = self.cipher.encrypt(backup_data.encode())

            backup_file = Path(backup_path)
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            backup_file.write_bytes(encrypted_backup)
            backup_file.chmod(0o600)

            logger.info(f"Secrets backed up to: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to backup secrets: {e}")
            return False

    def restore_secrets(self, backup_path: str) -> bool:
        """Restore secrets from encrypted backup"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False

            # Decrypt backup
            encrypted_backup = backup_file.read_bytes()
            backup_data = self.cipher.decrypt(encrypted_backup)
            secrets_backup = json.loads(backup_data.decode())

            # Restore secrets
            for category, secrets in secrets_backup.items():
                for key, value in secrets.items():
                    self.store_secret(category, key, value)

            # Update Kubernetes secrets
            self.create_kubernetes_secret()

            logger.info(f"Secrets restored from: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore secrets: {e}")
            return False

    def list_secrets(self) -> dict[str, Any]:
        """List all available secrets (without values)"""
        secrets_list = {}

        for secret_file in self.secrets_dir.glob("*.secret"):
            parts = secret_file.stem.split("_", 1)
            if len(parts) == 2:
                category, key = parts
                if category not in secrets_list:
                    secrets_list[category] = []
                secrets_list[category].append(key)

        return secrets_list

    def health_check(self) -> dict[str, Any]:
        """Check secrets management health"""
        health = {
            "status": "healthy",
            "encryption_key_exists": Path(
                self.config.get("encryption_key_file", "")
            ).exists(),
            "secrets_dir_exists": self.secrets_dir.exists(),
            "secrets_count": len(list(self.secrets_dir.glob("*.secret"))),
            "kubernetes_secret_exists": False,
        }

        # Check Kubernetes secret
        try:
            result = subprocess.run(
                ["kubectl", "get", "secret", "sophia-ai-secrets", "-n", "sophia-ai"],
                capture_output=True,
                text=True,
            )

            health["kubernetes_secret_exists"] = result.returncode == 0

        except Exception as e:
            logger.warning(f"Failed to check Kubernetes secret: {e}")

        # Overall health status
        if not health["encryption_key_exists"] or not health["secrets_dir_exists"]:
            health["status"] = "unhealthy"
        elif health["secrets_count"] == 0:
            health["status"] = "warning"

        return health

# CLI interface
def main():
    """Main CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Lambda Labs Secrets Manager")
    parser.add_argument(
        "action",
        choices=[
            "init",
            "store",
            "get",
            "rotate",
            "backup",
            "restore",
            "list",
            "health",
        ],
    )
    parser.add_argument("--category", help="Secret category")
    parser.add_argument("--key", help="Secret key")
    parser.add_argument("--value", help="Secret value")
    parser.add_argument("--backup-path", help="Backup file path")
    parser.add_argument("--config", help="Configuration file path")

    args = parser.parse_args()

    manager = LambdaLabsSecretsManager(args.config or "secrets-config.yaml")

    if args.action == "init":
        success = manager.initialize_secrets()
        if success:
            manager.create_kubernetes_secret()
        print(f"Initialization: {'SUCCESS' if success else 'FAILED'}")

    elif args.action == "store":
        if not all([args.category, args.key, args.value]):
            print("Error: --category, --key, and --value required")
            return
        success = manager.store_secret(args.category, args.key, args.value)
        print(f"Store: {'SUCCESS' if success else 'FAILED'}")

    elif args.action == "get":
        if not all([args.category, args.key]):
            print("Error: --category and --key required")
            return
        value = manager.get_secret(args.category, args.key)
        print(value if value else "SECRET NOT FOUND")

    elif args.action == "rotate":
        if not all([args.category, args.key, args.value]):
            print("Error: --category, --key, and --value required")
            return
        success = manager.rotate_secret(args.category, args.key, args.value)
        print(f"Rotation: {'SUCCESS' if success else 'FAILED'}")

    elif args.action == "backup":
        if not args.backup_path:
            print("Error: --backup-path required")
            return
        success = manager.backup_secrets(args.backup_path)
        print(f"Backup: {'SUCCESS' if success else 'FAILED'}")

    elif args.action == "restore":
        if not args.backup_path:
            print("Error: --backup-path required")
            return
        success = manager.restore_secrets(args.backup_path)
        print(f"Restore: {'SUCCESS' if success else 'FAILED'}")

    elif args.action == "list":
        secrets = manager.list_secrets()
        print(json.dumps(secrets, indent=2))

    elif args.action == "health":
        health = manager.health_check()
        print(json.dumps(health, indent=2))

if __name__ == "__main__":
    main()
