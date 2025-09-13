"""
WebSocket Security Middleware
Provides input validation, cross-tenant isolation, audit logging, threat detection,
and security event monitoring
"""
import asyncio
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
import redis.asyncio as aioredis
from .websocket_auth import AuthenticatedUser, TenantType, UserRole
logger = logging.getLogger(__name__)
class SecurityEventType(str, Enum):
    """Security event types"""
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    CROSS_TENANT_VIOLATION = "cross_tenant_violation"
    MALICIOUS_INPUT = "malicious_input"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    DATA_EXFILTRATION_ATTEMPT = "data_exfiltration_attempt"
    INJECTION_ATTEMPT = "injection_attempt"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"
class ThreatLevel(str, Enum):
    """Threat severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
@dataclass
class SecurityEvent:
    """Security event record"""
    event_id: str
    event_type: SecurityEventType
    threat_level: ThreatLevel
    timestamp: datetime
    client_id: str
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    ip_address: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)
    raw_message: Optional[str] = None
    blocked: bool = False
    response_action: Optional[str] = None
@dataclass
class InputValidationRule:
    """Input validation rule"""
    field_name: str
    pattern: str
    max_length: int
    required: bool = False
    sanitize: bool = True
    description: str = ""
@dataclass
class TenantIsolationRule:
    """Tenant isolation rule"""
    resource_pattern: str
    allowed_tenant_types: set[TenantType]
    cross_tenant_roles: set[UserRole]
    description: str = ""
class WebSocketSecurityMiddleware:
    """
    Comprehensive WebSocket security middleware
    """
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        audit_retention_days: int = 90,
        max_events_per_hour: int = 1000,
        enable_threat_detection: bool = True,
    ):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.audit_retention_days = audit_retention_days
        self.max_events_per_hour = max_events_per_hour
        self.enable_threat_detection = enable_threat_detection
        # Security events tracking
        self.recent_events: list[SecurityEvent] = []
        self.blocked_clients: dict[str, datetime] = {}
        # Initialize validation rules
        self.validation_rules = self._initialize_validation_rules()
        self.isolation_rules = self._initialize_isolation_rules()
        # Threat detection patterns
        self.threat_patterns = self._initialize_threat_patterns()
        # Suspicious pattern tracking
        self.pattern_tracking: dict[str, dict[str, int]] = {}
    def _initialize_validation_rules(self) -> dict[str, list[InputValidationRule]]:
        """Initialize input validation rules by message type"""
        return {
            "subscribe": [
                InputValidationRule(
                    "channel",
                    r"^[a-zA-Z0-9_\-.:]+$",
                    100,
                    True,
                    True,
                    "Channel name validation",
                )
            ],
            "pay_ready_query": [
                InputValidationRule(
                    "account_id",
                    r"^[a-zA-Z0-9_\-]{1,50}$",
                    50,
                    True,
                    True,
                    "Pay Ready account ID",
                ),
                InputValidationRule(
                    "filters",
                    r"^[\w\s\-_.,:|=<>()]+$",
                    500,
                    False,
                    True,
                    "Query filters",
                ),
            ],
            "sophia_intelligence_query": [
                InputValidationRule(
                    "query_text",
                    r"^[\w\s\-_.,?!]+$",
                    1000,
                    True,
                    True,
                    "Intelligence query text",
                ),
                InputValidationRule(
                    "team_id",
                    r"^[a-zA-Z0-9_\-]{1,30}$",
                    30,
                    False,
                    True,
                    "Team identifier",
                ),
            ],
            "_operation": [
                InputValidationRule(
                    "operation_type",
                    r"^(deploy|monitor|analyze|tactical)$",
                    20,
                    True,
                    False,
                    " operation type",
                ),
                InputValidationRule(
                    "target",
                    r"^[a-zA-Z0-9_\-.:]+$",
                    100,
                    False,
                    True,
                    "Operation target",
                ),
            ],
            "general": [
                InputValidationRule(
                    "message",
                    r"^[\w\s\-_.,?!()\[\]{}:;\"'@#$%^&*+=|\\/<>~`]+$",
                    2000,
                    False,
                    True,
                    "General message content",
                )
            ],
        }
    def _initialize_isolation_rules(self) -> list[TenantIsolationRule]:
        """Initialize tenant isolation rules"""
        return [
            TenantIsolationRule(
                "pay_ready.*",
                {TenantType.PAY_READY, TenantType.ENTERPRISE},
                {UserRole.ADMIN},
                "Pay Ready data isolation",
            ),
            TenantIsolationRule(
                "sophia_intelligence.*",
                {TenantType.SOPHIA_INTEL, TenantType.ENTERPRISE},
                {UserRole.ADMIN, UserRole.SOPHIA_OPERATOR},
                "Sophia intelligence isolation",
            ),
            TenantIsolationRule(
                "_tactical.*",
                {TenantType._TACTICAL, TenantType.ENTERPRISE},
                {UserRole.ADMIN, UserRole._OPERATOR},
                " tactical isolation",
            ),
            TenantIsolationRule(
                "stuck_accounts.*",
                {TenantType.PAY_READY, TenantType.ENTERPRISE},
                {UserRole.ADMIN, UserRole.PAY_READY_ANALYST},
                "Stuck accounts sensitive data",
            ),
            TenantIsolationRule(
                "team_performance.*",
                {TenantType.SOPHIA_INTEL, TenantType.ENTERPRISE},
                {UserRole.ADMIN, UserRole.SOPHIA_OPERATOR},
                "Team performance data",
            ),
        ]
    def _initialize_threat_patterns(self) -> dict[str, list[str]]:
        """Initialize threat detection patterns"""
        return {
            "sql_injection": [
                r"(\bUNION\b.*\bSELECT\b)",
                r"(\bDROP\b.*\bTABLE\b)",
                r"(\bINSERT\b.*\bINTO\b)",
                r"(\bDELETE\b.*\bFROM\b)",
                r"(\bUPDATE\b.*\bSET\b)",
                r"(';.*--)",
                r"('\s*(or|OR)\s*')",
            ],
            "xss_injection": [
                r"<script[^>]*>.*</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe[^>]*>",
                r"<object[^>]*>",
                r"<embed[^>]*>",
            ],
            "command_injection": [
                r"(\||&|;|\$\(|\`)",
                r"(rm\s+(-rf|\*|\.))",
                r"(cat\s+/etc/passwd)",
                r"(wget|curl)\s+http",
                r"(nc|netcat)\s+-",
            ],
            "path_traversal": [
                r"(\.\./){2,}",
                r"(\\.\\.\\){2,}",
                r"/etc/passwd",
                r"\\windows\\system32",
                r"\.\.[\\/]",
            ],
            "data_exfiltration": [
                r"(base64|atob|btoa)",
                r"(SELECT\s+\*\s+FROM)",
                r"(EXEC|EXECUTE)\s+",
                r"(xp_cmdshell|sp_)",
                r"(copy|xcopy|scp|rsync)",
            ],
        }
    async def initialize(self):
        """Initialize security middleware"""
        try:
            self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("WebSocket security middleware initialized with Redis")
        except Exception as e:
            logger.warning(
                f"Redis connection failed, using in-memory security tracking: {e}"
            )
            self.redis = None
        # Start background tasks
        asyncio.create_task(self._cleanup_loop())
        if self.enable_threat_detection:
            asyncio.create_task(self._threat_analysis_loop())
    async def validate_input(
        self,
        message: dict[str, Any],
        message_type: str,
        user: Optional[AuthenticatedUser] = None,
    ) -> tuple[bool, dict[str, Any], Optional[SecurityEvent]]:
        """
        Validate incoming message input
        Args:
            message: Message to validate
            message_type: Type of message
            user: Authenticated user
        Returns:
            Tuple of (is_valid, sanitized_message, security_event)
        """
        try:
            # Get validation rules for message type
            rules = self.validation_rules.get(
                message_type, self.validation_rules.get("general", [])
            )
            sanitized_message = {}
            validation_errors = []
            security_issues = []
            for field, value in message.items():
                if not isinstance(value, (str, int, float, bool, list, dict)):
                    validation_errors.append(f"Invalid data type for field: {field}")
                    continue
                # Find applicable rule
                applicable_rule = None
                for rule in rules:
                    if rule.field_name == field or rule.field_name == "*":
                        applicable_rule = rule
                        break
                if not applicable_rule:
                    # No specific rule, use general validation
                    if isinstance(value, str):
                        # Basic sanitization
                        sanitized_value = self._sanitize_string(value)
                        if len(sanitized_value) > 2000:  # Default max length
                            validation_errors.append(
                                f"Field {field} exceeds maximum length"
                            )
                            continue
                        sanitized_message[field] = sanitized_value
                    else:
                        sanitized_message[field] = value
                    continue
                # Apply specific validation rule
                if isinstance(value, str):
                    # Check required field
                    if applicable_rule.required and not value.strip():
                        validation_errors.append(f"Required field {field} is empty")
                        continue
                    # Check length
                    if len(value) > applicable_rule.max_length:
                        validation_errors.append(
                            f"Field {field} exceeds maximum length of {applicable_rule.max_length}"
                        )
                        continue
                    # Check pattern
                    if applicable_rule.pattern and not re.match(
                        applicable_rule.pattern, value
                    ):
                        validation_errors.append(
                            f"Field {field} contains invalid characters"
                        )
                        continue
                    # Threat detection
                    threat_detected = await self._detect_threats_in_text(value)
                    if threat_detected:
                        security_issues.extend(threat_detected)
                    # Sanitize if needed
                    if applicable_rule.sanitize:
                        sanitized_message[field] = self._sanitize_string(value)
                    else:
                        sanitized_message[field] = value
                else:
                    sanitized_message[field] = value
            # Create security event if issues found
            security_event = None
            if security_issues:
                security_event = SecurityEvent(
                    event_id=self._generate_event_id(),
                    event_type=SecurityEventType.MALICIOUS_INPUT,
                    threat_level=(
                        ThreatLevel.HIGH
                        if len(security_issues) > 2
                        else ThreatLevel.MEDIUM
                    ),
                    timestamp=datetime.utcnow(),
                    client_id=message.get("client_id", "unknown"),
                    user_id=user.user_id if user else None,
                    tenant_id=user.tenant_id if user else None,
                    ip_address=user.ip_address if user else None,
                    details={
                        "message_type": message_type,
                        "security_issues": security_issues,
                        "validation_errors": validation_errors,
                    },
                    raw_message=json.dumps(message),
                    blocked=True,
                )
                await self._log_security_event(security_event)
            # Return validation result
            is_valid = len(validation_errors) == 0 and len(security_issues) == 0
            return is_valid, sanitized_message, security_event
        except Exception as e:
            logger.error(f"Input validation error: {e}")
            return False, {}, None
    def _sanitize_string(self, value: str) -> str:
        """Sanitize string input"""
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\';\\]', "", value)
        # Normalize whitespace
        sanitized = " ".join(sanitized.split())
        # Truncate if too long
        if len(sanitized) > 10000:
            sanitized = sanitized[:10000]
        return sanitized.strip()
    async def _detect_threats_in_text(self, text: str) -> list[str]:
        """Detect threat patterns in text"""
        threats = []
        text_upper = text.upper()
        for threat_type, patterns in self.threat_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_upper, re.IGNORECASE):
                    threats.append(f"{threat_type}: {pattern}")
        return threats
    async def check_tenant_isolation(
        self,
        user: AuthenticatedUser,
        resource_identifier: str,
        operation: str = "access",
    ) -> tuple[bool, Optional[SecurityEvent]]:
        """
        Check tenant isolation for resource access
        Args:
            user: Authenticated user
            resource_identifier: Resource being accessed
            operation: Type of operation (access, modify, delete)
        Returns:
            Tuple of (access_allowed, security_event)
        """
        try:
            # Check against isolation rules
            for rule in self.isolation_rules:
                if re.match(rule.resource_pattern, resource_identifier):
                    # Check if user's tenant type is allowed
                    if user.tenant_type not in rule.allowed_tenant_types:
                        # Check if user's role allows cross-tenant access
                        if user.role not in rule.cross_tenant_roles:
                            # Access denied - create security event
                            security_event = SecurityEvent(
                                event_id=self._generate_event_id(),
                                event_type=SecurityEventType.CROSS_TENANT_VIOLATION,
                                threat_level=ThreatLevel.HIGH,
                                timestamp=datetime.utcnow(),
                                client_id=f"user_{user.user_id}",
                                user_id=user.user_id,
                                tenant_id=user.tenant_id,
                                ip_address=user.ip_address,
                                details={
                                    "resource": resource_identifier,
                                    "operation": operation,
                                    "user_tenant_type": user.tenant_type.value,
                                    "user_role": user.role.value,
                                    "rule_description": rule.description,
                                    "allowed_tenant_types": [
                                        t.value for t in rule.allowed_tenant_types
                                    ],
                                    "cross_tenant_roles": [
                                        r.value for r in rule.cross_tenant_roles
                                    ],
                                },
                                blocked=True,
                                response_action="access_denied",
                            )
                            await self._log_security_event(security_event)
                            logger.warning(
                                f"Tenant isolation violation: User {user.username} "
                                f"from {user.tenant_type.value} attempted to access {resource_identifier}"
                            )
                            return False, security_event
            return True, None
        except Exception as e:
            logger.error(f"Tenant isolation check error: {e}")
            return False, None
    async def detect_anomalous_behavior(
        self, user: AuthenticatedUser, message_type: str, message_data: dict[str, Any]
    ) -> Optional[SecurityEvent]:
        """
        Detect anomalous behavior patterns
        Args:
            user: Authenticated user
            message_type: Type of message
            message_data: Message content
        Returns:
            SecurityEvent if anomaly detected
        """
        try:
            anomalies = []
            # Track patterns per user
            user_key = f"{user.user_id}_{user.tenant_id}"
            if user_key not in self.pattern_tracking:
                self.pattern_tracking[user_key] = {}
            user_patterns = self.pattern_tracking[user_key]
            # Count message types
            user_patterns[message_type] = user_patterns.get(message_type, 0) + 1
            # Detect unusual message frequency
            current_hour = datetime.utcnow().hour
            hour_key = f"{message_type}_{current_hour}"
            user_patterns[hour_key] = user_patterns.get(hour_key, 0) + 1
            # Check for suspicious patterns
            if user_patterns[hour_key] > 100:  # More than 100 messages per hour
                anomalies.append("high_frequency_messaging")
            # Check for Pay Ready specific anomalies
            if "pay_ready" in message_type and user.tenant_type != TenantType.PAY_READY:
                anomalies.append("cross_tenant_pay_ready_access")
            # Check for privilege escalation attempts
            if "admin" in str(message_data).lower() and user.role not in [
                UserRole.ADMIN
            ]:
                anomalies.append("privilege_escalation_attempt")
            # Check for data exfiltration patterns
            message_str = json.dumps(message_data)
            if (
                len(message_str) > 5000
                or "SELECT" in message_str.upper()
                or "DUMP" in message_str.upper()
            ):
                anomalies.append("potential_data_exfiltration")
            # Create security event if anomalies detected
            if anomalies:
                threat_level = (
                    ThreatLevel.CRITICAL if len(anomalies) > 2 else ThreatLevel.MEDIUM
                )
                security_event = SecurityEvent(
                    event_id=self._generate_event_id(),
                    event_type=SecurityEventType.ANOMALOUS_BEHAVIOR,
                    threat_level=threat_level,
                    timestamp=datetime.utcnow(),
                    client_id=f"user_{user.user_id}",
                    user_id=user.user_id,
                    tenant_id=user.tenant_id,
                    ip_address=user.ip_address,
                    details={
                        "anomalies": anomalies,
                        "message_type": message_type,
                        "user_patterns": user_patterns,
                        "message_size": len(message_str),
                    },
                    raw_message=(
                        message_str if len(message_str) < 1000 else message_str[:1000]
                    ),
                    blocked=threat_level == ThreatLevel.CRITICAL,
                )
                await self._log_security_event(security_event)
                return security_event
            return None
        except Exception as e:
            logger.error(f"Anomaly detection error: {e}")
            return None
    async def _log_security_event(self, event: SecurityEvent):
        """Log security event for monitoring and compliance"""
        try:
            # Add to recent events
            self.recent_events.append(event)
            # Keep only recent events in memory
            if len(self.recent_events) > 1000:
                self.recent_events = self.recent_events[-1000:]
            # Log to application logs
            log_data = {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "threat_level": event.threat_level.value,
                "timestamp": event.timestamp.isoformat(),
                "client_id": event.client_id,
                "user_id": event.user_id,
                "tenant_id": event.tenant_id,
                "ip_address": event.ip_address,
                "blocked": event.blocked,
                "details": event.details,
            }
            logger.warning(f"SECURITY EVENT: {log_data}")
            # Store in Redis for centralized monitoring
            if self.redis:
                await self.redis.lpush(
                    "websocket_security_events", json.dumps(log_data)
                )
                await self.redis.ltrim("websocket_security_events", 0, 10000)
                # Set expiration for compliance
                await self.redis.expire(
                    "websocket_security_events", self.audit_retention_days * 24 * 3600
                )
            # Block client if critical threat
            if event.threat_level == ThreatLevel.CRITICAL and event.client_id:
                await self._block_client(event.client_id, 3600)  # Block for 1 hour
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    async def _block_client(self, client_id: str, duration_seconds: int):
        """Block client for security violation"""
        block_until = datetime.utcnow() + timedelta(seconds=duration_seconds)
        self.blocked_clients[client_id] = block_until
        logger.critical(f"Blocked client {client_id} until {block_until}")
        # Store block in Redis
        if self.redis:
            await self.redis.setex(
                f"blocked_client:{client_id}", duration_seconds, block_until.isoformat()
            )
    async def is_client_blocked(
        self, client_id: str
    ) -> tuple[bool, Optional[datetime]]:
        """Check if client is currently blocked"""
        # Check in-memory blocks
        if client_id in self.blocked_clients:
            block_until = self.blocked_clients[client_id]
            if datetime.utcnow() < block_until:
                return True, block_until
            else:
                del self.blocked_clients[client_id]
        # Check Redis blocks
        if self.redis:
            try:
                block_data = await self.redis.get(f"blocked_client:{client_id}")
                if block_data:
                    block_until = datetime.fromisoformat(block_data)
                    if datetime.utcnow() < block_until:
                        return True, block_until
            except Exception as e:
                logger.error(f"Error checking Redis block status: {e}")
        return False, None
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        hash_input = f"{timestamp}_{id(self)}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
        return f"WS_{timestamp}_{hash_value}"
    async def _cleanup_loop(self):
        """Background cleanup task"""
        while True:
            try:
                now = datetime.utcnow()
                # Clean expired client blocks
                expired_blocks = []
                for client_id, block_until in self.blocked_clients.items():
                    if now > block_until:
                        expired_blocks.append(client_id)
                for client_id in expired_blocks:
                    del self.blocked_clients[client_id]
                # Clean old pattern tracking
                now - timedelta(hours=1)
                for user_key in list(self.pattern_tracking.keys()):
                    user_patterns = self.pattern_tracking[user_key]
                    expired_patterns = [
                        k
                        for k in user_patterns
                        if k.endswith(f"_{(now - timedelta(hours=2)).hour}")
                    ]
                    for pattern in expired_patterns:
                        del user_patterns[pattern]
                # Clean old security events
                cutoff = now - timedelta(hours=24)
                self.recent_events = [
                    e for e in self.recent_events if e.timestamp > cutoff
                ]
                await asyncio.sleep(300)  # Run every 5 minutes
            except Exception as e:
                logger.error(f"Error in security cleanup: {e}")
                await asyncio.sleep(60)
    async def _threat_analysis_loop(self):
        """Background threat analysis task"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                # Analyze recent events for patterns
                recent_cutoff = datetime.utcnow() - timedelta(minutes=10)
                recent_events = [
                    e for e in self.recent_events if e.timestamp > recent_cutoff
                ]
                if len(recent_events) > 50:  # High event rate
                    logger.warning(
                        f"High security event rate: {len(recent_events)} events in 10 minutes"
                    )
                # Check for coordinated attacks
                ip_counts = {}
                for event in recent_events:
                    if event.ip_address:
                        ip_counts[event.ip_address] = (
                            ip_counts.get(event.ip_address, 0) + 1
                        )
                for ip, count in ip_counts.items():
                    if count > 10:  # Same IP with many violations
                        logger.critical(
                            f"Potential coordinated attack from IP: {ip} ({count} events)"
                        )
            except Exception as e:
                logger.error(f"Error in threat analysis: {e}")
                await asyncio.sleep(60)
    def get_security_metrics(self) -> dict[str, Any]:
        """Get security metrics"""
        now = datetime.utcnow()
        recent_cutoff = now - timedelta(hours=1)
        recent_events = [e for e in self.recent_events if e.timestamp > recent_cutoff]
        event_types = {}
        threat_levels = {}
        for event in recent_events:
            event_types[event.event_type.value] = (
                event_types.get(event.event_type.value, 0) + 1
            )
            threat_levels[event.threat_level.value] = (
                threat_levels.get(event.threat_level.value, 0) + 1
            )
        active_blocks = len([b for b in self.blocked_clients.values() if b > now])
        return {
            "total_security_events": len(self.recent_events),
            "recent_events_1h": len(recent_events),
            "event_types": event_types,
            "threat_levels": threat_levels,
            "active_blocks": active_blocks,
            "total_blocked_clients": len(self.blocked_clients),
            "pattern_tracking_users": len(self.pattern_tracking),
            "threat_detection_enabled": self.enable_threat_detection,
        }
    async def unblock_client(self, client_id: str) -> bool:
        """Manually unblock a client (admin function)"""
        try:
            if client_id in self.blocked_clients:
                del self.blocked_clients[client_id]
            if self.redis:
                await self.redis.delete(f"blocked_client:{client_id}")
            logger.info(f"Manually unblocked client: {client_id}")
            return True
        except Exception as e:
            logger.error(f"Error unblocking client {client_id}: {e}")
            return False
    async def get_recent_security_events(
        self,
        limit: int = 100,
        threat_level: Optional[ThreatLevel] = None,
        event_type: Optional[SecurityEventType] = None,
    ) -> list[dict[str, Any]]:
        """Get recent security events with filtering"""
        events = (
            self.recent_events[-limit:] if not threat_level and not event_type else []
        )
        if threat_level or event_type:
            events = [
                e
                for e in self.recent_events[-1000:]  # Check last 1000 events
                if (not threat_level or e.threat_level == threat_level)
                and (not event_type or e.event_type == event_type)
            ][-limit:]
        return [
            {
                "event_id": e.event_id,
                "event_type": e.event_type.value,
                "threat_level": e.threat_level.value,
                "timestamp": e.timestamp.isoformat(),
                "client_id": e.client_id,
                "user_id": e.user_id,
                "tenant_id": e.tenant_id,
                "ip_address": e.ip_address,
                "blocked": e.blocked,
                "details": e.details,
            }
            for e in events
        ]
