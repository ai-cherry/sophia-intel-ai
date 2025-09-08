#!/usr/bin/env python3
"""
Sophia AI Platform - Secure Environment File Manager
Manages encrypted environment files with backup and rotation capabilities
"""

import base64
import hashlib
import os
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecureEnvManager:
    """Secure environment file manager with encryption and rotation"""

    def __init__(self):
        self.secrets_dir = Path("/opt/sophia/secrets")
        self.env_file = self.secrets_dir / ".env"
        self.encrypted_file = self.secrets_dir / ".env.encrypted"
        self.backup_dir = self.secrets_dir / "backups"
        self.keys_dir = self.secrets_dir / "keys"

        # Create directories
        self.backup_dir.mkdir(exist_ok=True)
        self.keys_dir.mkdir(exist_ok=True)

        # Set permissions
        os.chmod(self.backup_dir, 0o700)
        os.chmod(self.keys_dir, 0o700)

        # Load or generate encryption key
        self.encryption_key = self.load_or_generate_key()

    def load_or_generate_key(self) -> bytes:
        """Load or generate encryption key using Fernet"""
        key_file = self.secrets_dir / "master.key"

        if key_file.exists():
            # Read existing key and derive Fernet key
            with open(key_file, "rb") as f:
                master_key = f.read().strip()

            # Derive Fernet key from master key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"sophia_ai_salt",  # Fixed salt for consistency
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(master_key))
        else:
            # Generate new Fernet key
            key = Fernet.generate_key()

            # Save to master key file
            with open(key_file, "wb") as f:
                f.write(key)
            os.chmod(key_file, 0o600)

        return key

    def encrypt_env_file(self) -> bool:
        """Encrypt the .env file"""
        if not self.env_file.exists():
            print(f"❌ Environment file not found: {self.env_file}")
            return False

        try:
            # Read plaintext env file
            with open(self.env_file) as f:
                plaintext = f.read()

            # Encrypt
            fernet = Fernet(self.encryption_key)
            encrypted = fernet.encrypt(plaintext.encode())

            # Write encrypted file
            with open(self.encrypted_file, "wb") as f:
                f.write(encrypted)

            # Set permissions
            os.chmod(self.encrypted_file, 0o600)

            # Remove plaintext file for security
            self.env_file.unlink()

            print(f"✅ Environment file encrypted: {self.encrypted_file}")
            return True

        except Exception as e:
            print(f"❌ Encryption failed: {e}")
            return False

    def decrypt_env_file(self, target_path: Optional[Path] = None) -> Optional[str]:
        """Decrypt the .env file"""
        if not self.encrypted_file.exists():
            print(f"❌ Encrypted file not found: {self.encrypted_file}")
            return None

        try:
            # Read encrypted file
            with open(self.encrypted_file, "rb") as f:
                encrypted = f.read()

            # Decrypt
            fernet = Fernet(self.encryption_key)
            decrypted = fernet.decrypt(encrypted).decode()

            # Write to target if specified
            if target_path:
                with open(target_path, "w") as f:
                    f.write(decrypted)
                os.chmod(target_path, 0o600)
                print(f"✅ Environment file decrypted to: {target_path}")

            return decrypted

        except Exception as e:
            print(f"❌ Decryption failed: {e}")
            return None

    def rotate_secrets(self, service: Optional[str] = None) -> bool:
        """Rotate secrets for specific service or all"""
        try:
            # Backup current env
            self.backup_env()

            # Decrypt current env
            env_content = self.decrypt_env_file()
            if not env_content:
                return False

            env_dict = self.parse_env(env_content)

            # Rotate specified secrets
            if service:
                # Rotate specific service
                key_patterns = {
                    "openai": ["OPENAI_API_KEY"],
                    "anthropic": ["ANTHROPIC_API_KEY"],
                    "github": ["GITHUB_TOKEN"],
                    "jwt": ["JWT_SECRET_KEY"],
                    "encryption": ["ENCRYPTION_KEY", "API_KEY_SALT"],
                    "mcp": ["MCP_AUTH_TOKEN"],
                }

                if service in key_patterns:
                    for key in key_patterns[service]:
                        if key in env_dict:
                            # Generate new secure value
                            if "JWT" in key or "SECRET" in key or "TOKEN" in key:
                                env_dict[key] = base64.b64encode(os.urandom(32)).decode()
                            else:
                                env_dict[key] = (
                                    f"rotated_{hashlib.sha256(os.urandom(32)).hexdigest()[:32]}"
                                )
                            print(f"✅ Rotated: {key}")
                else:
                    print(f"❌ Unknown service: {service}")
                    return False
            else:
                # Rotate all security-related keys
                security_keys = [
                    "JWT_SECRET_KEY",
                    "API_KEY_SALT",
                    "ENCRYPTION_KEY",
                    "MCP_AUTH_TOKEN",
                    "BACKUP_ENCRYPTION_KEY",
                ]

                for key in security_keys:
                    if key in env_dict:
                        env_dict[key] = base64.b64encode(os.urandom(32)).decode()
                        print(f"✅ Rotated: {key}")

                # Generate new deployment ID
                env_dict["DEPLOYMENT_ID"] = str(uuid.uuid4())
                print("✅ Generated new deployment ID")

            # Write new env file
            self.write_env(env_dict)

            # Encrypt
            success = self.encrypt_env_file()

            if success:
                print("✅ Secret rotation complete")

            return success

        except Exception as e:
            print(f"❌ Secret rotation failed: {e}")
            return False

    def backup_env(self) -> bool:
        """Backup current environment file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if self.encrypted_file.exists():
                backup_path = self.backup_dir / f".env.encrypted.{timestamp}"
                subprocess.run(["cp", str(self.encrypted_file), str(backup_path)], check=True)
                os.chmod(backup_path, 0o600)
                print(f"✅ Backup created: {backup_path}")

                # Clean old backups (keep last 10)
                backups = sorted(self.backup_dir.glob(".env.encrypted.*"))
                if len(backups) > 10:
                    for old_backup in backups[:-10]:
                        old_backup.unlink()
                        print(f"🗑️ Removed old backup: {old_backup}")

                return True
            else:
                print("⚠️ No encrypted file to backup")
                return False

        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False

    def parse_env(self, content: str) -> Dict[str, str]:
        """Parse env file content into dictionary"""
        env_dict = {}
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_dict[key.strip()] = value.strip()
        return env_dict

    def write_env(self, env_dict: Dict[str, str]) -> bool:
        """Write env dictionary to file"""
        try:
            lines = []

            # Add header
            lines.append("# ============================================")
            lines.append("# SOPHIA AI PLATFORM - MASTER ENVIRONMENT FILE")
            lines.append("# ============================================")
            lines.append("# SECURITY: This file contains ALL credentials")
            lines.append("# Never commit, never expose, always encrypt")
            lines.append(f"# Generated: {datetime.utcnow().isoformat()}Z")
            lines.append("# ============================================")
            lines.append("")

            # Group by category
            categories = {
                "DEPLOYMENT": ["ENVIRONMENT", "DEPLOYMENT_ID", "INSTANCE_ID", "REGION"],
                "LAMBDA_LABS": [k for k in env_dict.keys() if "LAMBDA" in k],
                "DATABASE": [
                    k
                    for k in env_dict.keys()
                    if any(db in k for db in ["NEON", "QDRANT", "REDIS", "DATABASE"])
                ],
                "AI_PROVIDERS": [
                    k
                    for k in env_dict.keys()
                    if any(
                        ai in k
                        for ai in [
                            "OPENAI",
                            "ANTHROPIC",
                            "MISTRAL",
                            "LLAMA",
                            "HUGGING",
                            "GROK",
                            "DEEPSEEK",
                            "EXA",
                        ]
                    )
                ],
                "SECURITY": [
                    k
                    for k in env_dict.keys()
                    if any(sec in k for sec in ["JWT", "KEY", "SECRET", "TOKEN", "AUTH"])
                ],
                "WORKFLOW": [
                    k
                    for k in env_dict.keys()
                    if any(wf in k for wf in ["N8N", "ESTUARY", "GITHUB", "PULUMI"])
                ],
                "MONITORING": [
                    k
                    for k in env_dict.keys()
                    if any(mon in k for mon in ["SENTRY", "PROMETHEUS", "GRAFANA", "DATADOG"])
                ],
                "MCP": [k for k in env_dict.keys() if "MCP" in k],
                "FEATURES": [k for k in env_dict.keys() if "ENABLE_" in k],
                "RESOURCES": [k for k in env_dict.keys() if "MAX_" in k],
                "OTHER": [],
            }

            # Categorize remaining keys
            categorized_keys = set()
            for category_keys in categories.values():
                categorized_keys.update(category_keys)

            categories["OTHER"] = [k for k in env_dict.keys() if k not in categorized_keys]

            # Write categories
            for category, keys in categories.items():
                if keys:
                    lines.append(f"# === {category.replace('_', ' ')} ===")
                    for key in sorted(keys):
                        if key in env_dict:
                            lines.append(f"{key}={env_dict[key]}")
                    lines.append("")

            # Write to file
            with open(self.env_file, "w") as f:
                f.write("\n".join(lines))

            os.chmod(self.env_file, 0o600)
            print(f"✅ Environment file written: {self.env_file}")
            return True

        except Exception as e:
            print(f"❌ Failed to write env file: {e}")
            return False

    def verify_env(self) -> bool:
        """Verify all required environment variables are set"""
        required_vars = [
            "LAMBDA_API_KEY",
            "DATABASE_URL",
            "OPENAI_API_KEY",
            "JWT_SECRET_KEY",
            "MCP_AUTH_TOKEN",
            "ENCRYPTION_KEY",
        ]

        # Decrypt and check
        env_content = self.decrypt_env_file()
        if not env_content:
            return False

        env_dict = self.parse_env(env_content)

        missing = []
        for var in required_vars:
            if var not in env_dict or not env_dict[var]:
                missing.append(var)

        if missing:
            print(f"❌ Missing required variables: {', '.join(missing)}")
            return False

        print("✅ All required environment variables are set")
        return True

    def export_for_runtime(self) -> bool:
        """Export decrypted env for runtime use"""
        try:
            runtime_env = self.secrets_dir / ".env.runtime"

            # Decrypt to runtime location
            env_content = self.decrypt_env_file(runtime_env)
            if not env_content:
                return False

            # Set restrictive permissions
            os.chmod(runtime_env, 0o400)

            # Create systemd environment file
            systemd_env = Path("/etc/systemd/system/sophia.env")
            env_dict = self.parse_env(env_content)

            try:
                with open(systemd_env, "w") as f:
                    for key, value in env_dict.items():
                        # Escape special characters for systemd
                        value = value.replace('"', '\\"')
                        f.write(f'{key}="{value}"\n')

                os.chmod(systemd_env, 0o600)
                print("✅ Systemd environment file created")
            except PermissionError:
                print("⚠️ Cannot create systemd file (requires sudo)")

            print("✅ Environment exported for runtime")
            return True

        except Exception as e:
            print(f"❌ Runtime export failed: {e}")
            return False

    def get_status(self) -> Dict:
        """Get status of environment management system"""
        status = {
            "encrypted_file_exists": self.encrypted_file.exists(),
            "backup_count": len(list(self.backup_dir.glob(".env.encrypted.*"))),
            "last_backup": None,
            "encryption_key_exists": (self.secrets_dir / "master.key").exists(),
            "runtime_file_exists": (self.secrets_dir / ".env.runtime").exists(),
        }

        # Get last backup time
        backups = list(self.backup_dir.glob(".env.encrypted.*"))
        if backups:
            latest_backup = max(backups, key=lambda x: x.stat().st_mtime)
            status["last_backup"] = datetime.fromtimestamp(
                latest_backup.stat().st_mtime
            ).isoformat()

        return status

    def generate_report(self) -> str:
        """Generate status report"""
        status = self.get_status()

        report = f"""
🔐 SOPHIA AI SECURE ENVIRONMENT MANAGER
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'=' * 50}

📊 STATUS:
   Encrypted File: {'✅' if status['encrypted_file_exists'] else '❌'}
   Encryption Key: {'✅' if status['encryption_key_exists'] else '❌'}
   Runtime File: {'✅' if status['runtime_file_exists'] else '❌'}
   Backup Count: {status['backup_count']}
   Last Backup: {status['last_backup'] or 'Never'}

📁 DIRECTORY STRUCTURE:
   Secrets Dir: {self.secrets_dir}
   Encrypted File: {self.encrypted_file}
   Backup Dir: {self.backup_dir}
   Keys Dir: {self.keys_dir}

🔧 OPERATIONS AVAILABLE:
   • encrypt_env_file() - Encrypt plaintext .env
   • decrypt_env_file() - Decrypt to plaintext
   • rotate_secrets() - Rotate security keys
   • backup_env() - Create backup
   • verify_env() - Verify required vars
   • export_for_runtime() - Export for app use

🛡️ SECURITY FEATURES:
   • Fernet encryption (AES 128)
   • PBKDF2 key derivation
   • Automatic backup rotation
   • Secure file permissions (600)
   • Runtime isolation
"""

        return report


def main():
    """CLI interface for secure environment manager"""
    import sys

    manager = SecureEnvManager()

    if len(sys.argv) < 2:
        print("Usage: python env_manager.py <command> [args]")
        print("Commands:")
        print("  status          - Show system status")
        print("  encrypt         - Encrypt .env file")
        print("  decrypt [path]  - Decrypt to file or stdout")
        print("  backup          - Create backup")
        print("  rotate [service]- Rotate secrets")
        print("  verify          - Verify required variables")
        print("  export          - Export for runtime")
        return

    command = sys.argv[1]

    if command == "status":
        print(manager.generate_report())

    elif command == "encrypt":
        manager.encrypt_env_file()

    elif command == "decrypt":
        target = Path(sys.argv[2]) if len(sys.argv) > 2 else None
        content = manager.decrypt_env_file(target)
        if not target and content:
            print(content)

    elif command == "backup":
        manager.backup_env()

    elif command == "rotate":
        service = sys.argv[2] if len(sys.argv) > 2 else None
        manager.rotate_secrets(service)

    elif command == "verify":
        manager.verify_env()

    elif command == "export":
        manager.export_for_runtime()

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
