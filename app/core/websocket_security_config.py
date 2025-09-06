"""
WebSocket Security Configuration
Centralized configuration for WebSocket security components
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class SecurityConfig:
    """WebSocket security configuration"""

    # Authentication settings
    secret_key: str = os.getenv("WEBSOCKET_JWT_SECRET", "your-secret-key-change-this")
    jwt_algorithm: str = "HS256"
    token_expiry_minutes: int = 60
    session_timeout_minutes: int = 30
    require_authentication: bool = True

    # Rate limiting settings
    enable_rate_limiting: bool = True
    enable_ddos_protection: bool = True
    ddos_threshold_rps: float = 100.0
    emergency_limit_duration_minutes: int = 15

    # Security middleware settings
    enable_threat_detection: bool = True
    audit_retention_days: int = 90
    max_security_events_per_hour: int = 1000

    # Redis connection
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Pay Ready specific security
    pay_ready_strict_isolation: bool = True
    pay_ready_require_mfa: bool = False  # For future implementation

    # Monitoring and alerting
    security_alert_webhook_url: Optional[str] = os.getenv("SECURITY_ALERT_WEBHOOK")
    enable_real_time_monitoring: bool = True

    # Compliance settings
    enable_audit_logging: bool = True
    log_sensitive_data: bool = False  # For GDPR compliance
    enable_encryption_at_rest: bool = True


class SecurityPresets:
    """Predefined security configuration presets"""

    @staticmethod
    def development() -> SecurityConfig:
        """Development environment - relaxed security for testing"""
        return SecurityConfig(
            secret_key="dev-secret-key-not-secure",
            require_authentication=False,
            enable_rate_limiting=True,
            enable_ddos_protection=False,
            enable_threat_detection=True,
            ddos_threshold_rps=1000.0,
            audit_retention_days=7,
            pay_ready_strict_isolation=False,
            enable_audit_logging=True,
            log_sensitive_data=True,  # OK for dev
        )

    @staticmethod
    def staging() -> SecurityConfig:
        """Staging environment - moderate security"""
        return SecurityConfig(
            secret_key=os.getenv("STAGING_JWT_SECRET", "staging-secret-change-this"),
            require_authentication=True,
            enable_rate_limiting=True,
            enable_ddos_protection=True,
            enable_threat_detection=True,
            ddos_threshold_rps=200.0,
            audit_retention_days=30,
            pay_ready_strict_isolation=True,
            enable_audit_logging=True,
            log_sensitive_data=False,
        )

    @staticmethod
    def production() -> SecurityConfig:
        """Production environment - maximum security"""
        return SecurityConfig(
            secret_key=os.getenv("PRODUCTION_JWT_SECRET"),  # Must be set
            require_authentication=True,
            enable_rate_limiting=True,
            enable_ddos_protection=True,
            enable_threat_detection=True,
            ddos_threshold_rps=100.0,
            emergency_limit_duration_minutes=30,
            audit_retention_days=90,
            max_security_events_per_hour=500,
            pay_ready_strict_isolation=True,
            pay_ready_require_mfa=True,
            enable_real_time_monitoring=True,
            enable_audit_logging=True,
            log_sensitive_data=False,
            enable_encryption_at_rest=True,
        )

    @staticmethod
    def high_security() -> SecurityConfig:
        """High security environment for sensitive data"""
        config = SecurityPresets.production()
        config.session_timeout_minutes = 15
        config.token_expiry_minutes = 30
        config.ddos_threshold_rps = 50.0
        config.max_security_events_per_hour = 100
        config.emergency_limit_duration_minutes = 60
        return config


def get_config(environment: str = None) -> SecurityConfig:
    """Get security configuration for environment"""
    environment = environment or os.getenv("ENVIRONMENT", "development")

    if environment == "development":
        return SecurityPresets.development()
    elif environment == "staging":
        return SecurityPresets.staging()
    elif environment == "production":
        return SecurityPresets.production()
    elif environment == "high_security":
        return SecurityPresets.high_security()
    else:
        # Default to development with warning
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Unknown environment '{environment}', using development preset")
        return SecurityPresets.development()


def validate_config(config: SecurityConfig) -> List[str]:
    """Validate security configuration and return any warnings"""
    warnings = []

    if config.secret_key in ["your-secret-key-change-this", "dev-secret-key-not-secure"]:
        warnings.append("Using default/insecure secret key - change for production")

    if len(config.secret_key) < 32:
        warnings.append("Secret key should be at least 32 characters long")

    if not config.require_authentication and config.enable_real_time_monitoring:
        warnings.append("Authentication disabled but real-time monitoring enabled")

    if config.session_timeout_minutes > 120:
        warnings.append("Session timeout > 2 hours may pose security risk")

    if config.audit_retention_days < 30:
        warnings.append("Audit retention < 30 days may not meet compliance requirements")

    if not config.redis_url:
        warnings.append("Redis URL not configured - using in-memory storage only")

    return warnings


# Example usage configurations for different scenarios

PAY_READY_FOCUSED_CONFIG = SecurityConfig(
    # Maximum security for Pay Ready data
    require_authentication=True,
    session_timeout_minutes=15,
    token_expiry_minutes=30,
    enable_rate_limiting=True,
    ddos_threshold_rps=50.0,
    enable_threat_detection=True,
    pay_ready_strict_isolation=True,
    enable_audit_logging=True,
    log_sensitive_data=False,
)

SOPHIA_DASHBOARD_CONFIG = SecurityConfig(
    # Balanced security for Sophia dashboard
    require_authentication=True,
    session_timeout_minutes=30,
    token_expiry_minutes=60,
    enable_rate_limiting=True,
    ddos_threshold_rps=100.0,
    enable_threat_detection=True,
    pay_ready_strict_isolation=True,  # Still protect Pay Ready data
    enable_audit_logging=True,
)

ARTEMIS_TACTICAL_CONFIG = SecurityConfig(
    # High security for tactical operations
    require_authentication=True,
    session_timeout_minutes=20,
    token_expiry_minutes=45,
    enable_rate_limiting=True,
    ddos_threshold_rps=75.0,
    enable_threat_detection=True,
    enable_audit_logging=True,
    enable_real_time_monitoring=True,
)
