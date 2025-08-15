"""
Configuration validation script for Sophia Intel platform.
Validates all required secrets and configuration values to prevent runtime errors.
"""

import sys
from typing import List, Tuple
from urllib.parse import urlparse
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import settings
from loguru import logger


class ValidationError(Exception):
    """Custom exception for configuration validation errors."""

    pass


class ConfigValidator:
    """Comprehensive configuration validator for Sophia Intel platform."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """
        Validate all configuration settings.

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        logger.info("🔍 Starting comprehensive configuration validation...")

        # Clear previous results
        self.errors.clear()
        self.warnings.clear()

        # Run all validations
        self._validate_api_keys()
        self._validate_security_settings()
        self._validate_database_urls()
        self._validate_service_endpoints()
        self._validate_agent_settings()
        self._validate_environment_settings()

        is_valid = len(self.errors) == 0

        if is_valid:
            logger.success("✅ All configuration validation checks passed!")
        else:
            logger.error(
                f"❌ Configuration validation failed with {len(self.errors)} errors"
            )

        return is_valid, self.errors.copy(), self.warnings.copy()

    def _validate_api_keys(self) -> None:
        """Validate all API keys for correct format and no placeholders."""
        logger.info("Validating API keys...")

        # Required API keys with their expected prefixes
        required_keys = {
            "OPENROUTER_API_KEY": "sk-or-v1-",
            "openrouter_API_KEY": "pk-",
            "LAMBDA_CLOUD_API_KEY": "ll-",
            "EXA_API_KEY": "exa-",
        }

        for key_name, expected_prefix in required_keys.items():
            value = getattr(settings, key_name, None)

            if not value:
                self.errors.append(f"❌ {key_name} is not set or empty")
                continue

            # Check for placeholder values
            if any(
                placeholder in value.lower()
                for placeholder in [
                    "your-",
                    "test-",
                    "dev-",
                    "placeholder",
                    "example",
                    "change",
                ]
            ):
                self.errors.append(
                    f"❌ {key_name} appears to be a placeholder value: {value[:20]}..."
                )
                continue

            # Check format for specific keys
            if key_name == "OPENROUTER_API_KEY" and not value.startswith(
                expected_prefix
            ):
                self.errors.append(
                    f"❌ {key_name} should start with '{expected_prefix}', got: {value[:10]}..."
                )
            elif key_name == "openrouter_API_KEY" and not value.startswith(
                expected_prefix
            ):
                self.errors.append(
                    f"❌ {key_name} should start with '{expected_prefix}', got: {value[:10]}..."
                )
            elif key_name == "LAMBDA_CLOUD_API_KEY" and not value.startswith(expected_prefix):
                self.errors.append(
                    f"❌ {key_name} should start with '{expected_prefix}', got: {value[:10]}..."
                )
            elif key_name == "EXA_API_KEY" and not value.startswith(expected_prefix):
                self.errors.append(
                    f"❌ {key_name} should start with '{expected_prefix}', got: {value[:10]}..."
                )
            else:
                logger.debug(f"✅ {key_name} format is valid")

    def _validate_security_settings(self) -> None:
        """Validate security-related configuration settings."""
        logger.info("Validating security settings...")

        security_keys = ["SECRET_KEY", "ENCRYPTION_KEY", "JWT_SECRET", "API_SALT"]

        for key_name in security_keys:
            value = getattr(settings, key_name, None)

            if not value:
                self.errors.append(f"❌ {key_name} is not set or empty")
                continue

            # Check for development/placeholder values
            if any(
                placeholder in value.lower()
                for placeholder in [
                    "dev-",
                    "test-",
                    "development",
                    "change",
                    "replace",
                    "production",
                ]
            ):
                self.errors.append(
                    f"❌ {key_name} appears to be a development placeholder: {value[:20]}..."
                )
                continue

            # Encryption key specific validation
            if key_name == "ENCRYPTION_KEY":
                if len(value) < 32:
                    self.errors.append(
                        f"❌ {key_name} must be at least 32 characters long, got {len(value)}"
                    )
                elif len(value) != 32:
                    self.warnings.append(
                        f"⚠️ {key_name} should be exactly 32 characters for AES-256, got {len(value)}"
                    )
                else:
                    logger.debug(f"✅ {key_name} length is valid")

            # General security key length validation
            elif len(value) < 16:
                self.errors.append(
                    f"❌ {key_name} is too short, must be at least 16 characters, got {len(value)}"
                )
            else:
                logger.debug(f"✅ {key_name} length is adequate")

    def _validate_database_urls(self) -> None:
        """Validate database connection URLs."""
        logger.info("Validating database URLs...")

        # PostgreSQL URL validation
        db_url = getattr(settings, "DATABASE_URL", None)
        if not db_url:
            self.errors.append("❌ DATABASE_URL is not set")
        else:
            try:
                parsed = urlparse(db_url)
                if parsed.scheme not in ["postgresql", "postgresql+asyncpg"]:
                    self.errors.append(
                        f"❌ DATABASE_URL should use postgresql or postgresql+asyncpg scheme, got: {parsed.scheme}"
                    )
                elif not parsed.hostname:
                    self.errors.append("❌ DATABASE_URL missing hostname")
                elif not parsed.username:
                    self.errors.append("❌ DATABASE_URL missing username")
                elif not parsed.path or parsed.path == "/":
                    self.errors.append("❌ DATABASE_URL missing database name")
                else:
                    logger.debug("✅ DATABASE_URL format is valid")
            except Exception as e:
                self.errors.append(f"❌ Invalid DATABASE_URL format: {e}")

        # Redis URL validation
        redis_url = getattr(settings, "REDIS_URL", None)
        if not redis_url:
            self.errors.append("❌ REDIS_URL is not set")
        else:
            try:
                parsed = urlparse(redis_url)
                if parsed.scheme != "redis":
                    self.errors.append(
                        f"❌ REDIS_URL should use redis scheme, got: {parsed.scheme}"
                    )
                elif not parsed.hostname:
                    self.errors.append("❌ REDIS_URL missing hostname")
                else:
                    logger.debug("✅ REDIS_URL format is valid")
            except Exception as e:
                self.errors.append(f"❌ Invalid REDIS_URL format: {e}")

        # Qdrant URL validation
        qdrant_url = getattr(settings, "QDRANT_URL", None)
        if not qdrant_url:
            self.errors.append("❌ QDRANT_URL is not set")
        else:
            try:
                parsed = urlparse(qdrant_url)
                if parsed.scheme not in ["http", "https"]:
                    self.errors.append(
                        f"❌ QDRANT_URL should use http or https scheme, got: {parsed.scheme}"
                    )
                elif not parsed.hostname:
                    self.errors.append("❌ QDRANT_URL missing hostname")
                else:
                    # Validate Qdrant Cloud URL format if using cloud
                    if "qdrant.io" in parsed.hostname:
                        api_key = getattr(settings, "QDRANT_API_KEY", None)
                        if not api_key:
                            self.warnings.append(
                                "⚠️ Using Qdrant Cloud but QDRANT_API_KEY is not set"
                            )
                    logger.debug("✅ QDRANT_URL format is valid")
            except Exception as e:
                self.errors.append(f"❌ Invalid QDRANT_URL format: {e}")

    def _validate_service_endpoints(self) -> None:
        """Validate service endpoint configurations."""
        logger.info("Validating service endpoints...")

        endpoints = {
            "SOPHIA_API_ENDPOINT": settings.SOPHIA_API_ENDPOINT,
            "SOPHIA_MCP_ENDPOINT": settings.SOPHIA_MCP_ENDPOINT,
            "SOPHIA_FRONTEND_ENDPOINT": settings.SOPHIA_FRONTEND_ENDPOINT,
        }

        for endpoint_name, endpoint_url in endpoints.items():
            if not endpoint_url:
                self.warnings.append(f"⚠️ {endpoint_name} is not set")
                continue

            try:
                parsed = urlparse(endpoint_url)
                if parsed.scheme not in ["http", "https"]:
                    self.errors.append(
                        f"❌ {endpoint_name} should use http or https scheme, got: {parsed.scheme}"
                    )
                elif not parsed.hostname:
                    self.errors.append(f"❌ {endpoint_name} missing hostname")
                else:
                    logger.debug(f"✅ {endpoint_name} format is valid")
            except Exception as e:
                self.errors.append(f"❌ Invalid {endpoint_name} format: {e}")

    def _validate_agent_settings(self) -> None:
        """Validate agent-related configuration settings."""
        logger.info("Validating agent settings...")

        # Agent concurrency validation
        concurrency = getattr(settings, "AGENT_CONCURRENCY", None)
        if concurrency is None:
            self.warnings.append("⚠️ AGENT_CONCURRENCY is not set, using default")
        elif concurrency < 1:
            self.errors.append(
                f"❌ AGENT_CONCURRENCY must be at least 1, got: {concurrency}"
            )
        elif concurrency > 10:
            self.warnings.append(
                f"⚠️ AGENT_CONCURRENCY is very high ({concurrency}), may cause resource issues"
            )

        # Agent timeout validation
        timeout = getattr(settings, "AGENT_TIMEOUT_SECONDS", None)
        if timeout is None:
            self.warnings.append("⚠️ AGENT_TIMEOUT_SECONDS is not set, using default")
        elif timeout < 30:
            self.warnings.append(
                f"⚠️ AGENT_TIMEOUT_SECONDS is very low ({timeout}s), may cause timeouts"
            )
        elif timeout > 900:
            self.warnings.append(
                f"⚠️ AGENT_TIMEOUT_SECONDS is very high ({timeout}s), may cause resource issues"
            )

        # Agno storage database validation
        agno_db = getattr(settings, "AGNO_STORAGE_DB", None)
        if not agno_db:
            self.errors.append("❌ AGNO_STORAGE_DB is not set")
        else:
            # Ensure the directory exists
            db_path = Path(agno_db)
            if not db_path.parent.exists():
                self.warnings.append(
                    f"⚠️ AGNO_STORAGE_DB directory does not exist: {db_path.parent}"
                )

    def _validate_environment_settings(self) -> None:
        """Validate environment-specific settings."""
        logger.info("Validating environment settings...")

        env = getattr(settings, "ENVIRONMENT", None)
        if not env:
            self.warnings.append("⚠️ ENVIRONMENT is not set, using default")
        elif env not in ["development", "staging", "production", "test"]:
            self.warnings.append(f"⚠️ Unknown ENVIRONMENT value: {env}")

        # Log level validation
        log_level = getattr(settings, "LOG_LEVEL", None)
        if log_level and log_level not in [
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ]:
            self.errors.append(f"❌ Invalid LOG_LEVEL: {log_level}")

        # Memory configuration validation
        embedding_dim = getattr(settings, "EMBEDDING_DIMENSION", None)
        if embedding_dim and embedding_dim not in [384, 768, 1536, 3072]:
            self.warnings.append(
                f"⚠️ Unusual EMBEDDING_DIMENSION: {embedding_dim}, common values are 384, 768, 1536, 3072"
            )


def main() -> int:
    """Main validation function."""
    print("🔍 Sophia Intel Configuration Validator")
    print("=" * 50)

    try:
        validator = ConfigValidator()
        is_valid, errors, warnings = validator.validate_all()

        # Print results
        print("\n📊 VALIDATION RESULTS:")
        print(f"Errors: {len(errors)}")
        print(f"Warnings: {len(warnings)}")

        if errors:
            print("\n🚨 ERRORS (must be fixed):")
            for error in errors:
                print(f"  {error}")

        if warnings:
            print("\n⚠️ WARNINGS (should be reviewed):")
            for warning in warnings:
                print(f"  {warning}")

        if is_valid:
            print("\n✅ Configuration validation PASSED!")
            print("Your Sophia Intel platform is properly configured.")
            return 0
        else:
            print(f"\n❌ Configuration validation FAILED with {len(errors)} errors.")
            print("Please fix the errors above before starting the platform.")
            return 1

    except Exception as e:
        print(f"\n💥 Validation script error: {e}")
        logger.exception("Validation script failed")
        return 2


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
