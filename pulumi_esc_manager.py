#!/usr/bin/env python3
"""
Sophia AI Platform v3.3 - Pulumi ESC Integration
Enterprise-grade secret management using Pulumi ESC for centralized credential handling
"""

import json
import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("sophia.esc")


class Environment(Enum):
    """Environment types"""

    DEVELOPMENT = "dev"
    STAGING = "staging"
    PRODUCTION = "prod"
    TEST = "test"


@dataclass
class PulumiESCConfig:
    """Configuration for Pulumi ESC"""

    organization: str = "ai-cherry"
    project: str = "sophia-platform"
    stack: str = "prod"
    environment: str = "sophia-prod"
    region: str = "us-west-2"


class PulumiESCManager:
    """
    Manages secrets and configuration using Pulumi ESC
    Replaces local encryption with enterprise-grade secret management
    """

    def __init__(self, environment: Environment = Environment.PRODUCTION):
        self.environment = environment
        self.config = PulumiESCConfig()

        # Update config based on environment
        if environment == Environment.DEVELOPMENT:
            self.config.stack = "dev"
            self.config.environment = "sophia-dev"
        elif environment == Environment.STAGING:
            self.config.stack = "staging"
            self.config.environment = "sophia-staging"
        elif environment == Environment.TEST:
            self.config.stack = "test"
            self.config.environment = "sophia-test"

        # Local cache directory for performance
        self.cache_dir = Path("/opt/sophia/.esc-cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Ensure Pulumi ESC is installed
        self._ensure_esc_installed()

    def _ensure_esc_installed(self) -> bool:
        """Ensure Pulumi ESC CLI is installed"""
        try:
            result = subprocess.run(["esc", "version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logger.info(f"✅ Pulumi ESC version: {result.stdout.strip()}")
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("❌ Pulumi ESC not installed")
            self._install_esc()
            return False

    def _install_esc(self):
        """Install Pulumi ESC CLI"""
        logger.info("📦 Installing Pulumi ESC...")
        install_script = """
        curl -fsSL https://get.pulumi.com/esc/install.sh | sh
        export PATH=$PATH:$HOME/.pulumi/bin
        """
        subprocess.run(install_script, shell=True, check=True)
        logger.info("✅ Pulumi ESC installed")

    def login(self, access_token: Optional[str] = None) -> bool:
        """
        Login to Pulumi ESC
        Uses PULUMI_ACCESS_TOKEN env var or provided token
        """
        try:
            if access_token:
                os.environ["PULUMI_ACCESS_TOKEN"] = access_token
            elif not os.getenv("PULUMI_ACCESS_TOKEN"):
                logger.error("❌ No Pulumi access token provided")
                return False

            result = subprocess.run(["esc", "login"], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                logger.info("✅ Logged in to Pulumi ESC")
                return True
            else:
                logger.error(f"❌ Login failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return False

    def open_environment(self) -> Dict[str, Any]:
        """
        Open Pulumi ESC environment and retrieve all secrets/config
        """
        try:
            # Open environment and get values
            cmd = [
                "esc",
                "open",
                f"{self.config.organization}/{self.config.environment}",
                "--format",
                "json",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                logger.error(f"❌ Failed to open environment: {result.stderr}")
                return {}

            # Parse JSON output
            env_data = json.loads(result.stdout)

            # Cache the values for offline access
            self._cache_environment(env_data)

            logger.info(f"✅ Opened environment: {self.config.environment}")
            return env_data

        except Exception as e:
            logger.error(f"❌ Error opening environment: {e}")
            # Try to load from cache
            return self._load_cached_environment()

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a specific secret from Pulumi ESC
        """
        try:
            cmd = [
                "esc",
                "open",
                f"{self.config.organization}/{self.config.environment}",
                "--value",
                key,
                "--format",
                "json",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                value = json.loads(result.stdout)
                return value
            else:
                logger.warning(f"⚠️ Secret {key} not found, using default")
                return default

        except Exception as e:
            logger.error(f"❌ Error getting secret {key}: {e}")
            return default

    def set_secret(self, key: str, value: str) -> bool:
        """
        Set or update a secret in Pulumi ESC
        """
        try:
            # First, get current environment configuration
            env_file = self._get_environment_file()

            # Update the value
            env_file["values"][key] = {"secret": value}

            # Save back to Pulumi ESC
            return self._update_environment(env_file)

        except Exception as e:
            logger.error(f"❌ Error setting secret {key}: {e}")
            return False

    def set_secrets_batch(self, secrets: Dict[str, str]) -> bool:
        """
        Set multiple secrets at once (more efficient)
        """
        try:
            # Get current environment configuration
            env_file = self._get_environment_file()

            # Update all values
            for key, value in secrets.items():
                env_file["values"][key] = {"secret": value}

            # Save back to Pulumi ESC
            return self._update_environment(env_file)

        except Exception as e:
            logger.error(f"❌ Error setting secrets batch: {e}")
            return False

    def _get_environment_file(self) -> Dict[str, Any]:
        """Get the environment configuration file"""
        cmd = ["esc", "environment", "get", f"{self.config.organization}/{self.config.environment}"]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            raise RuntimeError(f"Failed to get environment: {result.stderr}")

        return yaml.safe_load(result.stdout)

    def _update_environment(self, env_config: Dict[str, Any]) -> bool:
        """Update the environment configuration"""
        try:
            # Write to temporary file
            temp_file = self.cache_dir / "temp_env.yaml"
            with open(temp_file, "w") as f:
                yaml.dump(env_config, f)

            # Update in Pulumi ESC
            cmd = [
                "esc",
                "environment",
                "set",
                f"{self.config.organization}/{self.config.environment}",
                str(temp_file),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            # Clean up temp file
            temp_file.unlink()

            if result.returncode == 0:
                logger.info("✅ Environment updated successfully")
                return True
            else:
                logger.error(f"❌ Failed to update environment: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"❌ Error updating environment: {e}")
            return False

    def rotate_secret(self, key: str, generator: Optional[callable] = None) -> bool:
        """
        Rotate a specific secret
        """
        try:
            # Generate new value
            if generator:
                new_value = generator()
            else:
                # Default generator for different secret types
                if "JWT" in key or "SECRET" in key or "TOKEN" in key:
                    import secrets

                    new_value = secrets.token_urlsafe(32)
                elif "PASSWORD" in key:
                    import secrets

                    new_value = secrets.token_urlsafe(16)
                else:
                    logger.warning(f"No generator for {key}, using random string")
                    import secrets

                    new_value = secrets.token_urlsafe(24)

            # Update the secret
            if self.set_secret(key, new_value):
                logger.info(f"✅ Rotated secret: {key}")
                return True
            else:
                logger.error(f"❌ Failed to rotate secret: {key}")
                return False

        except Exception as e:
            logger.error(f"❌ Error rotating secret {key}: {e}")
            return False

    def sync_from_github_secrets(self, github_org: str = "ai-cherry") -> bool:
        """
        Sync secrets from GitHub Organization Secrets to Pulumi ESC
        """
        try:
            # This would require GitHub API integration
            # For now, we'll create a template for manual sync

            github_secrets = [
                "OPENAI_API_KEY",
                "ANTHROPIC_API_KEY",
                "LAMBDA_API_KEY",
                "EXA_API_KEY",
                "GROK_API_KEY",
                "DEEPSEEK_API_KEY",
                "MISTRAL_API_KEY",
                "ARIZE_SPACE_ID",
                "ARIZE_API_KEY",
                "OPENROUTER_API_KEY",
                "PORTKEY_API_KEY",
                "PORTKEY_CONFIG",
                "APIFY_API_TOKEN",
                "DOCKER_USER_NAME",
                "DOCKER_PERSONAL_ACCESS_TOKEN",
                "HUGGINGFACE_API_TOKEN",
                "PHANTOM_BUSTER_API_KEY",
                "TOGETHER_AI_API_KEY",
                "TWINGLY_API_KEY",
                "TAVILY_API_KEY",
                "ZENROWS_API_KEY",
                "GONG_ACCESS_KEY",
                "GONG_CLIENT_SECRET",
            ]

            # Create sync template
            sync_template = {"values": {}}

            for secret in github_secrets:
                sync_template["values"][secret] = {"secret": f"${{github.secrets.{secret}}}"}

            # Save template for manual configuration
            template_file = self.cache_dir / "github_sync_template.yaml"
            with open(template_file, "w") as f:
                yaml.dump(sync_template, f)

            logger.info(f"✅ GitHub sync template created: {template_file}")
            logger.info("📋 Manual step: Configure GitHub Actions to sync these secrets")

            return True

        except Exception as e:
            logger.error(f"❌ Error creating GitHub sync template: {e}")
            return False

    def _cache_environment(self, env_data: Dict[str, Any]):
        """Cache environment data for offline access"""
        cache_file = self.cache_dir / f"{self.config.environment}_cache.json"

        with open(cache_file, "w") as f:
            json.dump({"timestamp": datetime.now().isoformat(), "data": env_data}, f, indent=2)

        # Set restrictive permissions
        os.chmod(cache_file, 0o600)

    def _load_cached_environment(self) -> Dict[str, Any]:
        """Load cached environment data"""
        cache_file = self.cache_dir / f"{self.config.environment}_cache.json"

        if not cache_file.exists():
            logger.warning("⚠️ No cached environment data available")
            return {}

        try:
            with open(cache_file) as f:
                cached = json.load(f)

            # Check if cache is recent (within 1 hour)
            cache_time = datetime.fromisoformat(cached["timestamp"])
            if datetime.now() - cache_time > timedelta(hours=1):
                logger.warning("⚠️ Cached environment data is stale")

            logger.info("✅ Using cached environment data")
            return cached["data"]

        except Exception as e:
            logger.error(f"❌ Error loading cached environment: {e}")
            return {}

    def export_to_local_env(self, output_file: Optional[Path] = None) -> bool:
        """
        Export Pulumi ESC environment to local .env file for development
        """
        try:
            env_data = self.open_environment()
            if not env_data:
                return False

            if output_file is None:
                output_file = Path("/opt/sophia/secrets/.env.runtime")

            # Write environment variables
            with open(output_file, "w") as f:
                f.write("# Sophia AI Environment Variables\n")
                f.write(f"# Generated from Pulumi ESC: {self.config.environment}\n")
                f.write(f"# Timestamp: {datetime.now().isoformat()}\n\n")

                for key, value in env_data.items():
                    if isinstance(value, str):
                        f.write(f"{key}={value}\n")

            # Set restrictive permissions
            os.chmod(output_file, 0o600)

            logger.info(f"✅ Environment exported to: {output_file}")
            return True

        except Exception as e:
            logger.error(f"❌ Error exporting environment: {e}")
            return False

    def validate_secrets(self) -> Dict[str, bool]:
        """
        Validate that all required secrets are present and properly formatted
        """
        required_secrets = {
            "OPENAI_API_KEY": r"^sk-[a-zA-Z0-9]{48}$",
            "ANTHROPIC_API_KEY": r"^sk-ant-[a-zA-Z0-9]{93}$",
            "LAMBDA_API_KEY": r"^[a-f0-9]{32}$",
            "EXA_API_KEY": r"^[a-f0-9-]{36}$",
        }

        validation_results = {}

        try:
            env_data = self.open_environment()

            for secret, pattern in required_secrets.items():
                if secret in env_data:
                    import re

                    if re.match(pattern, env_data[secret]):
                        validation_results[secret] = True
                        logger.info(f"✅ {secret}: Valid format")
                    else:
                        validation_results[secret] = False
                        logger.error(f"❌ {secret}: Invalid format")
                else:
                    validation_results[secret] = False
                    logger.error(f"❌ {secret}: Missing")

            return validation_results

        except Exception as e:
            logger.error(f"❌ Error validating secrets: {e}")
            return {secret: False for secret in required_secrets.keys()}

    def create_environment_template(self) -> bool:
        """
        Create a Pulumi ESC environment template for Sophia AI
        """
        try:
            template = {
                "values": {
                    # AI Provider APIs
                    "OPENAI_API_KEY": {"secret": "${github.secrets.OPENAI_API_KEY}"},
                    "ANTHROPIC_API_KEY": {"secret": "${github.secrets.ANTHROPIC_API_KEY}"},
                    "DEEPSEEK_API_KEY": {"secret": "${github.secrets.DEEPSEEK_API_KEY}"},
                    "MISTRAL_API_KEY": {"secret": "${github.secrets.MISTRAL_API_KEY}"},
                    "GROK_API_KEY": {"secret": "${github.secrets.GROK_API_KEY}"},
                    # Infrastructure
                    "LAMBDA_API_KEY": {"secret": "${github.secrets.LAMBDA_API_KEY}"},
                    "AWS_ACCESS_KEY_ID": {"secret": "${github.secrets.AWS_ACCESS_KEY_ID}"},
                    "AWS_SECRET_ACCESS_KEY": {"secret": "${github.secrets.AWS_SECRET_ACCESS_KEY}"},
                    # Database
                    "DATABASE_URL": {"secret": "${github.secrets.DATABASE_URL}"},
                    "REDIS_URL": {"secret": "${github.secrets.REDIS_URL}"},
                    # Search & Data
                    "EXA_API_KEY": {"secret": "${github.secrets.EXA_API_KEY}"},
                    "TAVILY_API_KEY": {"secret": "${github.secrets.TAVILY_API_KEY}"},
                    # Third-party Services
                    "ARIZE_SPACE_ID": {"secret": "${github.secrets.ARIZE_SPACE_ID}"},
                    "ARIZE_API_KEY": {"secret": "${github.secrets.ARIZE_API_KEY}"},
                    "OPENROUTER_API_KEY": {"secret": "${github.secrets.OPENROUTER_API_KEY}"},
                    "PORTKEY_API_KEY": {"secret": "${github.secrets.PORTKEY_API_KEY}"},
                    "GONG_ACCESS_KEY": {"secret": "${github.secrets.GONG_ACCESS_KEY}"},
                    "GONG_CLIENT_SECRET": {"secret": "${github.secrets.GONG_CLIENT_SECRET}"},
                    # Security
                    "JWT_SECRET_KEY": {"secret": "${github.secrets.JWT_SECRET_KEY}"},
                    "ENCRYPTION_KEY": {"secret": "${github.secrets.ENCRYPTION_KEY}"},
                    "API_KEY_SALT": {"secret": "${github.secrets.API_KEY_SALT}"},
                    # Environment Configuration
                    "ENVIRONMENT": self.environment.value,
                    "DEPLOYMENT_ID": "${pulumi.deployment.id}",
                    "REGION": self.config.region,
                    "LOG_LEVEL": "INFO" if self.environment == Environment.PRODUCTION else "DEBUG",
                }
            }

            # Save template
            template_file = self.cache_dir / f"sophia_{self.environment.value}_template.yaml"
            with open(template_file, "w") as f:
                yaml.dump(template, f, default_flow_style=False)

            logger.info(f"✅ Environment template created: {template_file}")
            logger.info("📋 Use this template to create your Pulumi ESC environment")

            return True

        except Exception as e:
            logger.error(f"❌ Error creating environment template: {e}")
            return False


def main():
    """CLI interface for Pulumi ESC manager"""
    import argparse

    parser = argparse.ArgumentParser(description="Sophia AI Pulumi ESC Manager v3.3")
    parser.add_argument(
        "action",
        choices=["login", "open", "get", "set", "rotate", "sync", "export", "validate", "template"],
    )
    parser.add_argument(
        "--env", default="production", choices=["production", "development", "staging", "test"]
    )
    parser.add_argument("--key", help="Secret key (for get/set/rotate)")
    parser.add_argument("--value", help="Secret value (for set)")
    parser.add_argument("--token", help="Pulumi access token")
    parser.add_argument("--output", help="Output file for export")

    args = parser.parse_args()

    # Map environment names
    env_map = {
        "production": Environment.PRODUCTION,
        "development": Environment.DEVELOPMENT,
        "staging": Environment.STAGING,
        "test": Environment.TEST,
    }

    manager = PulumiESCManager(environment=env_map[args.env])

    if args.action == "login":
        if manager.login(args.token):
            print("✅ Successfully logged in to Pulumi ESC")
        else:
            print("❌ Login failed")

    elif args.action == "open":
        env_data = manager.open_environment()
        if env_data:
            print(f"✅ Environment opened: {len(env_data)} variables")
            for key in sorted(env_data.keys()):
                print(f"  • {key}")
        else:
            print("❌ Failed to open environment")

    elif args.action == "get":
        if args.key:
            value = manager.get_secret(args.key)
            if value:
                print(
                    f"✅ {args.key}: {value[:10]}..."
                    if len(value) > 10
                    else f"✅ {args.key}: {value}"
                )
            else:
                print(f"❌ Secret {args.key} not found")
        else:
            print("❌ Please specify --key")

    elif args.action == "set":
        if args.key and args.value:
            if manager.set_secret(args.key, args.value):
                print(f"✅ Set secret: {args.key}")
            else:
                print(f"❌ Failed to set secret: {args.key}")
        else:
            print("❌ Please specify --key and --value")

    elif args.action == "rotate":
        if args.key:
            if manager.rotate_secret(args.key):
                print(f"✅ Rotated secret: {args.key}")
            else:
                print(f"❌ Failed to rotate secret: {args.key}")
        else:
            print("❌ Please specify --key")

    elif args.action == "sync":
        if manager.sync_from_github_secrets():
            print("✅ GitHub sync template created")
        else:
            print("❌ Failed to create sync template")

    elif args.action == "export":
        output_file = Path(args.output) if args.output else None
        if manager.export_to_local_env(output_file):
            print("✅ Environment exported successfully")
        else:
            print("❌ Export failed")

    elif args.action == "validate":
        results = manager.validate_secrets()
        valid_count = sum(results.values())
        total_count = len(results)
        print(f"📊 Validation: {valid_count}/{total_count} secrets valid")

        for secret, valid in results.items():
            status = "✅" if valid else "❌"
            print(f"  {status} {secret}")

    elif args.action == "template":
        if manager.create_environment_template():
            print("✅ Environment template created")
        else:
            print("❌ Failed to create template")


if __name__ == "__main__":
    main()
