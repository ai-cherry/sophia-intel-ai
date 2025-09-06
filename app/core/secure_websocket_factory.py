"""
Secure WebSocket Factory
Factory class for creating secure WebSocket manager instances with proper configuration
"""

import logging
from typing import Optional

from .websocket_manager import WebSocketManager
from .websocket_security_config import SecurityConfig, get_config, validate_config

logger = logging.getLogger(__name__)


class SecureWebSocketFactory:
    """
    Factory for creating secure WebSocket managers with comprehensive security features
    """

    @staticmethod
    async def create_manager(
        config: Optional[SecurityConfig] = None, environment: Optional[str] = None
    ) -> WebSocketManager:
        """
        Create and initialize a secure WebSocket manager

        Args:
            config: Security configuration (if None, uses environment-based config)
            environment: Environment name (development, staging, production, high_security)

        Returns:
            Initialized WebSocketManager instance
        """
        # Get configuration
        if config is None:
            config = get_config(environment)

        # Validate configuration
        warnings = validate_config(config)
        for warning in warnings:
            logger.warning(f"Security config warning: {warning}")

        # Log security configuration
        logger.info(
            f"Creating secure WebSocket manager: "
            f"auth={config.require_authentication}, "
            f"rate_limit={config.enable_rate_limiting}, "
            f"ddos_protection={config.enable_ddos_protection}, "
            f"threat_detection={config.enable_threat_detection}"
        )

        # Create WebSocket manager with security components
        manager = WebSocketManager(
            secret_key=config.secret_key,
            redis_url=config.redis_url,
            enable_security=config.require_authentication,
            enable_rate_limiting=config.enable_rate_limiting,
            enable_ddos_protection=config.enable_ddos_protection,
        )

        # Configure authentication settings
        if manager.authenticator:
            manager.authenticator.token_expiry_minutes = config.token_expiry_minutes
            manager.authenticator.session_timeout_minutes = config.session_timeout_minutes

        # Configure rate limiting settings
        if manager.rate_limiter:
            manager.rate_limiter.ddos_threshold_rps = config.ddos_threshold_rps
            manager.rate_limiter.enable_ddos_protection = config.enable_ddos_protection

        # Configure security middleware settings
        if manager.security_middleware:
            manager.security_middleware.enable_threat_detection = config.enable_threat_detection
            manager.security_middleware.audit_retention_days = config.audit_retention_days
            manager.security_middleware.max_events_per_hour = config.max_security_events_per_hour

        # Set manager-specific settings
        manager.require_authentication = config.require_authentication

        # Initialize all components
        await manager.initialize()

        logger.info("Secure WebSocket manager created and initialized successfully")
        return manager

    @staticmethod
    async def create_pay_ready_manager() -> WebSocketManager:
        """Create WebSocket manager optimized for Pay Ready security requirements"""
        from .websocket_security_config import PAY_READY_FOCUSED_CONFIG

        return await SecureWebSocketFactory.create_manager(PAY_READY_FOCUSED_CONFIG)

    @staticmethod
    async def create_sophia_dashboard_manager() -> WebSocketManager:
        """Create WebSocket manager for Sophia dashboard with balanced security"""
        from .websocket_security_config import SOPHIA_DASHBOARD_CONFIG

        return await SecureWebSocketFactory.create_manager(SOPHIA_DASHBOARD_CONFIG)

    @staticmethod
    async def create_artemis_tactical_manager() -> WebSocketManager:
        """Create WebSocket manager for Artemis tactical operations"""
        from .websocket_security_config import ARTEMIS_TACTICAL_CONFIG

        return await SecureWebSocketFactory.create_manager(ARTEMIS_TACTICAL_CONFIG)

    @staticmethod
    def get_security_recommendations(environment: str) -> dict:
        """Get security recommendations for environment"""
        config = get_config(environment)
        warnings = validate_config(config)

        recommendations = {
            "environment": environment,
            "current_config": {
                "authentication_required": config.require_authentication,
                "rate_limiting_enabled": config.enable_rate_limiting,
                "ddos_protection_enabled": config.enable_ddos_protection,
                "threat_detection_enabled": config.enable_threat_detection,
                "pay_ready_isolation": config.pay_ready_strict_isolation,
                "audit_logging_enabled": config.enable_audit_logging,
            },
            "warnings": warnings,
            "recommendations": [],
        }

        # Generate specific recommendations
        if environment == "production":
            if not config.secret_key or len(config.secret_key) < 32:
                recommendations["recommendations"].append(
                    "Set strong JWT secret key (32+ characters) via PRODUCTION_JWT_SECRET env var"
                )

            if config.session_timeout_minutes > 30:
                recommendations["recommendations"].append(
                    "Consider reducing session timeout to 30 minutes or less for production"
                )

            if not config.enable_real_time_monitoring:
                recommendations["recommendations"].append(
                    "Enable real-time monitoring for production environment"
                )

        if config.pay_ready_strict_isolation:
            recommendations["recommendations"].append(
                "Pay Ready strict isolation is enabled - ensure proper tenant validation"
            )

        if not config.redis_url:
            recommendations["recommendations"].append(
                "Configure Redis for distributed session management and rate limiting"
            )

        return recommendations


# Example usage and integration helpers


async def setup_websocket_security(app, environment: str = None):
    """
    Helper function to set up WebSocket security in FastAPI application

    Usage:
        from app.core.secure_websocket_factory import setup_websocket_security

        @app.on_event("startup")
        async def startup_event():
            ws_manager = await setup_websocket_security(app, "production")
    """
    # Create secure WebSocket manager
    ws_manager = await SecureWebSocketFactory.create_manager(environment=environment)

    # Store in app state
    app.state.ws_manager = ws_manager

    # Log security status
    security_status = await ws_manager.get_security_status()
    logger.info(f"WebSocket security status: {security_status}")

    return ws_manager


def create_websocket_routes(app, ws_manager: WebSocketManager):
    """
    Create secure WebSocket routes

    Usage:
        create_websocket_routes(app, ws_manager)
    """
    from fastapi import Query

    @app.websocket("/ws/{client_id}/{session_id}")
    async def websocket_endpoint(
        websocket,
        client_id: str,
        session_id: str,
        token: str = Query(None, description="JWT authentication token"),
    ):
        """Secure WebSocket endpoint with authentication"""
        await ws_manager.websocket_endpoint(websocket, client_id, session_id, token)

    @app.get("/ws/security/status")
    async def websocket_security_status():
        """Get WebSocket security status (admin only)"""
        return await ws_manager.get_security_status()

    @app.get("/ws/metrics")
    async def websocket_metrics():
        """Get WebSocket metrics (admin only)"""
        return ws_manager.get_metrics()

    @app.post("/ws/security/emergency-lockdown")
    async def emergency_lockdown(duration_minutes: int = 15):
        """Emergency security lockdown (admin only)"""
        await ws_manager.emergency_security_lockdown(duration_minutes)
        return {"status": "lockdown_activated", "duration_minutes": duration_minutes}

    @app.get("/ws/audit/export")
    async def export_audit_logs(hours: int = 24):
        """Export audit logs for compliance (admin only)"""
        return await ws_manager.audit_log_export(hours)


# Security monitoring and alerting


class WebSocketSecurityMonitor:
    """Real-time security monitoring for WebSocket connections"""

    def __init__(self, ws_manager: WebSocketManager):
        self.ws_manager = ws_manager
        self.alert_thresholds = {
            "high_violation_rate": 10,  # violations per minute
            "ddos_alert_level": "elevated",
            "blocked_clients": 5,
            "security_events_per_hour": 100,
        }

    async def check_security_health(self) -> dict:
        """Check overall security health"""
        status = await self.ws_manager.get_security_status()
        metrics = self.ws_manager.get_metrics()

        alerts = []

        # Check for high violation rates
        total_violations = status.get("security_violations", 0)
        if total_violations > self.alert_thresholds["high_violation_rate"]:
            alerts.append(
                {
                    "level": "high",
                    "type": "high_violation_rate",
                    "value": total_violations,
                    "threshold": self.alert_thresholds["high_violation_rate"],
                }
            )

        # Check DDoS alert level
        ddos_level = status.get("ddos_alert_level", "normal")
        if ddos_level != "normal":
            alerts.append(
                {
                    "level": "critical" if ddos_level == "critical" else "medium",
                    "type": "ddos_alert",
                    "value": ddos_level,
                }
            )

        # Check blocked clients
        blocked_clients = status.get("blocked_clients", 0)
        if blocked_clients > self.alert_thresholds["blocked_clients"]:
            alerts.append(
                {
                    "level": "medium",
                    "type": "high_blocked_clients",
                    "value": blocked_clients,
                    "threshold": self.alert_thresholds["blocked_clients"],
                }
            )

        return {
            "health_status": "healthy" if not alerts else "alert",
            "alerts": alerts,
            "metrics_summary": {
                "total_connections": status.get("total_connections", 0),
                "authenticated_connections": status.get("authenticated_connections", 0),
                "security_violations": total_violations,
                "blocked_clients": blocked_clients,
            },
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        }

    async def send_alert(self, alert_data: dict):
        """Send security alert (implement webhook or notification system)"""
        logger.critical(f"WEBSOCKET SECURITY ALERT: {alert_data}")

        # TODO: Implement actual alerting (Slack, email, webhook, etc.)
        # This is where you would integrate with your monitoring/alerting system
