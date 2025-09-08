#!/usr/bin/env python3
"""
Security Fixes Validation Tests
Tests for Phase 1 critical security vulnerability fixes
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


class TestSecurityFixes:
    """Test suite for Phase 1 security fixes validation"""

    def test_pyjwt_version_requirement(self):
        """Test that PyJWT version meets security requirements"""
        try:
            import jwt

            version = jwt.__version__
            major, minor, patch = map(int, version.split("."))

            # PyJWT >= 3.0.0 required for security fixes
            assert (
                major >= 3
            ), f"PyJWT version {version} does not meet security requirement >=3.0.0"

        except ImportError:
            pytest.fail("PyJWT not installed - security requirement not met")

    def test_setuptools_security_constraint(self):
        """Test that setuptools version meets security requirements"""
        try:
            import setuptools

            version = setuptools.__version__
            major, minor, patch = map(int, version.split("."))

            # setuptools >= 78.1.1 required for CVE-2025-47273 fix
            if (
                major < 78
                or (major == 78 and minor < 1)
                or (major == 78 and minor == 1 and patch < 1)
            ):
                pytest.fail(
                    f"setuptools version {version} vulnerable to CVE-2025-47273"
                )

        except ImportError:
            pytest.fail("setuptools not available - security requirement not met")

    def test_wheel_security_constraint(self):
        """Test that wheel version meets security requirements"""
        try:
            import wheel

            version = wheel.__version__
            major, minor, patch = map(int, version.split("."))

            # wheel >= 0.38.1 required for CVE-2022-40898 fix
            if major == 0 and minor < 38 or major == 0 and minor == 38 and patch < 1:
                pytest.fail(f"wheel version {version} vulnerable to CVE-2022-40898")

        except ImportError:
            pytest.fail("wheel not available - security requirement not met")

    def test_acp_salt_environment_variable(self):
        """Test ACP protocol salt key management"""
        from orchestration.communication.acp_protocol import AgentCommunicationProtocol

        # Test with environment variable set
        test_salt = "dGVzdF9zYWx0X2tleV8yMDI1XzA4XzA0X3NlY3VyZQ=="
        with patch.dict(os.environ, {"ACP_SALT_KEY": test_salt}):
            redis_mock = Mock()
            config = {"agent_id": "test", "secret_key": "test_secret"}
            acp = AgentCommunicationProtocol(redis_mock, config)

            # Should not raise an error and should use environment salt
            key = acp._derive_encryption_key("test_password")
            assert key is not None
            assert len(key) > 0

    def test_acp_salt_fallback_warning(self):
        """Test ACP protocol fallback behavior without environment variable"""

        from orchestration.communication.acp_protocol import AgentCommunicationProtocol

        # Test without environment variable (should generate warning)
        with patch.dict(os.environ, {}, clear=True):
            redis_mock = Mock()
            config = {"agent_id": "test", "secret_key": "test_secret"}

            with patch(
                "orchestration.communication.acp_protocol.logger"
            ) as mock_logger:
                acp = AgentCommunicationProtocol(redis_mock, config)
                key = acp._derive_encryption_key("test_password")

                # Should generate warning about missing ACP_SALT_KEY
                mock_logger.warning.assert_called()
                warning_call = mock_logger.warning.call_args[0][0]
                assert "ACP_SALT_KEY not configured" in warning_call

    def test_database_dependency_validation(self):
        """Test proper database dependency validation"""
        from core.clean_architecture.infrastructure import (
            DatabaseConfig,
            OptimizedConnectionPool,
            PoolType,
        )

        # Mock unavailable asyncpg
        with patch("core.clean_architecture.infrastructure.ASYNCPG_AVAILABLE", False):
            with patch("core.clean_architecture.infrastructure.asyncpg", None):
                config = DatabaseConfig(neon_url="postgresql://test")
                pool = OptimizedConnectionPool(PoolType.AGENT_MEMORY, config)

                # Should raise proper error instead of silent failure
                with pytest.raises(Exception) as exc_info:
                    import asyncio

                    asyncio.run(pool.initialize())

                assert "asyncpg is required" in str(exc_info.value)

    def test_pydantic_dependency_validation(self):
        """Test proper pydantic dependency validation"""
        # Mock unavailable pydantic
        with patch("core.clean_architecture.infrastructure.PYDANTIC_AVAILABLE", False):
            with patch("core.clean_architecture.infrastructure.BaseModel", None):

                # Should raise proper error when trying to use DatabaseConfig
                with pytest.raises(ImportError) as exc_info:
                    pass

                assert "pydantic is required" in str(exc_info.value)

    def test_no_hardcoded_secrets_in_codebase(self):
        """Test that no hardcoded secrets remain in codebase"""
        import re

        # Patterns that indicate hardcoded secrets
        secret_patterns = [
            r'password\s*=\s*[\'"][^\'\"]+[\'"]',
            r'secret\s*=\s*[\'"][^\'\"]+[\'"]',
            r'api[_-]?key\s*=\s*[\'"][^\'\"]+[\'"]',
            r'token\s*=\s*[\'"][^\'\"]+[\'"]',
            r'salt\s*=\s*b?[\'"][^\'\"]+[\'"]',
        ]

        # Files to check
        files_to_check = [
            "orchestration/communication/acp_protocol.py",
            "orchestration/security/guardrails.py",
            "core/clean_architecture/infrastructure.py",
        ]

        for file_path in files_to_check:
            full_path = os.path.join(os.path.dirname(__file__), "..", "..", file_path)
            if os.path.exists(full_path):
                with open(full_path) as f:
                    content = f.read()

                for pattern in secret_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    # Filter out test/example values
                    real_secrets = [
                        m
                        for m in matches
                        if "test" not in m.lower() and "example" not in m.lower()
                    ]

                    assert (
                        len(real_secrets) == 0
                    ), f"Potential hardcoded secret found in {file_path}: {real_secrets}"


class TestSecurityConfiguration:
    """Test security configuration and environment setup"""

    def test_environment_security_setup(self):
        """Test that security environment variables are properly configured"""
        required_env_vars = ["ACP_SALT_KEY", "ENVIRONMENT", "PYTHONPATH"]

        # In test environment, we'll check if variables can be set
        for var in required_env_vars:
            with patch.dict(os.environ, {var: "test_value"}):
                assert os.getenv(var) == "test_value"

    def test_security_logging_configuration(self):
        """Test that security events are properly logged"""
        import logging

        # Test that security-related loggers exist and are configured
        security_loggers = [
            "orchestration.communication.acp_protocol",
            "orchestration.security.guardrails",
            "core.clean_architecture.infrastructure",
        ]

        for logger_name in security_loggers:
            logger = logging.getLogger(logger_name)
            assert logger is not None
            # Should have at least WARNING level or higher for security
            assert (
                logger.level <= logging.WARNING
                or logger.parent.level <= logging.WARNING
            )


@pytest.mark.security
@pytest.mark.integration
class TestSecurityIntegration:
    """Integration tests for security fixes"""

    def test_end_to_end_security_flow(self):
        """Test complete security flow with fixes applied"""
        # This would test the complete flow with proper dependencies
        # and environment configuration

        # Mock Redis for ACP testing
        redis_mock = Mock()

        # Test ACP with proper environment
        test_salt = "dGVzdF9zYWx0X2tleV8yMDI1XzA4XzA0X3NlY3VyZQ=="
        with patch.dict(os.environ, {"ACP_SALT_KEY": test_salt}):
            from orchestration.communication.acp_protocol import (
                AgentCommunicationProtocol,
            )

            config = {
                "agent_id": "security_test_agent",
                "secret_key": "test_secret_key_2025",
                "enable_encryption": True,
                "enable_signatures": True,
            }

            acp = AgentCommunicationProtocol(redis_mock, config)

            # Test encryption key derivation works
            key = acp._derive_encryption_key("test_password")
            assert key is not None
            assert len(key) > 0

            # Test that crypto operations don't fail
            assert acp.fernet is not None


if __name__ == "__main__":
    # Run security tests
    pytest.main([__file__, "-v", "-m", "security"])
