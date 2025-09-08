"""
WebSocket Rate Limiter
Implements sliding window rate limiting with domain-specific limits, DDoS protection,
and Pay Ready business cycle awareness
"""

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import redis.asyncio as aioredis

from .websocket_auth import AuthenticatedUser, TenantType, UserRole

logger = logging.getLogger(__name__)


class RateLimitType(str, Enum):
    """Rate limit types"""

    PER_SECOND = "per_second"
    PER_MINUTE = "per_minute"
    PER_HOUR = "per_hour"
    BURST = "burst"


class DomainType(str, Enum):
    """Domain types for different rate limiting"""

    SOPHIA_INTEL = "sophia_intel"
    ARTEMIS_TACTICAL = "artemis_tactical"
    PAY_READY = "pay_ready"
    SYSTEM_METRICS = "system_metrics"
    GENERAL = "general"


@dataclass
class RateLimit:
    """Rate limit configuration"""

    limit: int
    window_seconds: int
    limit_type: RateLimitType
    burst_allowance: int = 0


@dataclass
class ClientRateState:
    """Client rate limiting state"""

    client_id: str
    user: Optional[AuthenticatedUser] = None
    request_times: deque = field(default_factory=deque)
    burst_tokens: int = 0
    last_request: float = 0
    total_requests: int = 0
    blocked_until: Optional[float] = None
    violation_count: int = 0
    created_at: float = field(default_factory=time.time)


@dataclass
class DDoSMetrics:
    """DDoS detection metrics"""

    requests_per_second: float = 0.0
    unique_clients: int = 0
    blocked_requests: int = 0
    suspicious_patterns: int = 0
    alert_level: str = "normal"  # normal, elevated, critical


class PayReadyBusinessCycle:
    """Pay Ready business cycle awareness for intelligent rate limiting"""

    def __init__(self):
        # Business hours: Monday-Friday 6 AM to 10 PM PST
        self.business_hours = {"start_hour": 6, "end_hour": 22, "weekdays_only": True}

        # Critical business periods with higher limits
        self.critical_periods = [
            {"hour": 9, "multiplier": 2.0, "name": "market_open"},
            {"hour": 16, "multiplier": 1.5, "name": "market_close"},
            {"hour": 17, "multiplier": 1.8, "name": "end_of_day_processing"},
        ]

    def get_business_multiplier(self) -> tuple[float, str]:
        """Get rate limit multiplier based on business cycle"""
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()  # 0 = Monday, 6 = Sunday

        # Weekend - reduced activity
        if weekday > 4:  # Saturday, Sunday
            return 0.5, "weekend"

        # Outside business hours - reduced activity
        if hour < self.business_hours["start_hour"] or hour >= self.business_hours["end_hour"]:
            return 0.3, "after_hours"

        # Check critical periods
        for period in self.critical_periods:
            if abs(hour - period["hour"]) <= 1:  # Within 1 hour of critical time
                return period["multiplier"], period["name"]

        # Regular business hours
        return 1.0, "business_hours"


class WebSocketRateLimiter:
    """
    WebSocket rate limiter with sliding window, DDoS protection, and business intelligence
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        enable_ddos_protection: bool = True,
        ddos_threshold_rps: float = 100.0,
        cleanup_interval: int = 300,
    ):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.enable_ddos_protection = enable_ddos_protection
        self.ddos_threshold_rps = ddos_threshold_rps
        self.cleanup_interval = cleanup_interval

        # In-memory rate limiting state
        self.client_states: dict[str, ClientRateState] = {}
        self.global_metrics = DDoSMetrics()

        # Pay Ready business cycle handler
        self.business_cycle = PayReadyBusinessCycle()

        # Rate limit configurations by domain and role
        self.rate_limits = self._initialize_rate_limits()

        # Backoff strategies
        self.backoff_multipliers = {
            1: 5,  # 5 seconds
            2: 30,  # 30 seconds
            3: 300,  # 5 minutes
            4: 1800,  # 30 minutes
            5: 3600,  # 1 hour
        }

    def _initialize_rate_limits(self) -> dict[str, dict[str, RateLimit]]:
        """Initialize rate limit configurations"""
        return {
            # Per-role limits
            UserRole.ADMIN: {
                DomainType.SOPHIA_INTEL: RateLimit(100, 60, RateLimitType.PER_MINUTE, 20),
                DomainType.ARTEMIS_TACTICAL: RateLimit(100, 60, RateLimitType.PER_MINUTE, 20),
                DomainType.PAY_READY: RateLimit(200, 60, RateLimitType.PER_MINUTE, 50),
                DomainType.SYSTEM_METRICS: RateLimit(60, 60, RateLimitType.PER_MINUTE, 10),
                DomainType.GENERAL: RateLimit(200, 60, RateLimitType.PER_MINUTE, 30),
            },
            UserRole.SOPHIA_OPERATOR: {
                DomainType.SOPHIA_INTEL: RateLimit(60, 60, RateLimitType.PER_MINUTE, 15),
                DomainType.SYSTEM_METRICS: RateLimit(30, 60, RateLimitType.PER_MINUTE, 5),
                DomainType.GENERAL: RateLimit(100, 60, RateLimitType.PER_MINUTE, 20),
            },
            UserRole.PAY_READY_ANALYST: {
                DomainType.PAY_READY: RateLimit(120, 60, RateLimitType.PER_MINUTE, 30),
                DomainType.SYSTEM_METRICS: RateLimit(30, 60, RateLimitType.PER_MINUTE, 5),
                DomainType.GENERAL: RateLimit(80, 60, RateLimitType.PER_MINUTE, 15),
            },
            UserRole.ARTEMIS_OPERATOR: {
                DomainType.ARTEMIS_TACTICAL: RateLimit(80, 60, RateLimitType.PER_MINUTE, 20),
                DomainType.SYSTEM_METRICS: RateLimit(30, 60, RateLimitType.PER_MINUTE, 5),
                DomainType.GENERAL: RateLimit(60, 60, RateLimitType.PER_MINUTE, 10),
            },
            UserRole.VIEWER: {
                DomainType.SYSTEM_METRICS: RateLimit(20, 60, RateLimitType.PER_MINUTE, 3),
                DomainType.GENERAL: RateLimit(30, 60, RateLimitType.PER_MINUTE, 5),
            },
            UserRole.GUEST: {DomainType.GENERAL: RateLimit(10, 60, RateLimitType.PER_MINUTE, 2)},
        }

    async def initialize(self):
        """Initialize the rate limiter"""
        try:
            self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("WebSocket rate limiter initialized with Redis")
        except Exception as e:
            logger.warning(f"Redis connection failed, using in-memory rate limiting: {e}")
            self.redis = None

        # Start background tasks
        if self.enable_ddos_protection:
            asyncio.create_task(self._ddos_monitor_loop())
        asyncio.create_task(self._cleanup_loop())

    async def check_rate_limit(
        self,
        client_id: str,
        user: Optional[AuthenticatedUser] = None,
        domain: DomainType = DomainType.GENERAL,
        request_data: Optional[dict[str, Any]] = None,
    ) -> tuple[bool, Optional[dict[str, Any]]]:
        """
        Check if request should be rate limited

        Args:
            client_id: Client identifier
            user: Authenticated user (if available)
            domain: Domain type for specific rate limiting
            request_data: Optional request data for analysis

        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        now = time.time()

        # Get or create client state
        if client_id not in self.client_states:
            self.client_states[client_id] = ClientRateState(client_id=client_id, user=user)

        client_state = self.client_states[client_id]
        client_state.user = user  # Update user info
        client_state.last_request = now
        client_state.total_requests += 1

        # Check if client is currently blocked
        if client_state.blocked_until and now < client_state.blocked_until:
            remaining = int(client_state.blocked_until - now)
            return False, {
                "error": "rate_limited",
                "blocked_for_seconds": remaining,
                "violation_count": client_state.violation_count,
                "message": f"Rate limited. Try again in {remaining} seconds.",
            }

        # Clear block if expired
        if client_state.blocked_until and now >= client_state.blocked_until:
            client_state.blocked_until = None

        # Get rate limit configuration
        rate_limit = self._get_rate_limit(user, domain)
        if not rate_limit:
            # No limits for this user/domain combination
            return True, None

        # Apply business cycle multiplier for Pay Ready
        multiplier = 1.0
        cycle_info = "normal"
        if domain == DomainType.PAY_READY and user and user.tenant_type == TenantType.PAY_READY:
            multiplier, cycle_info = self.business_cycle.get_business_multiplier()

        adjusted_limit = int(rate_limit.limit * multiplier)

        # Sliding window rate limiting
        window_start = now - rate_limit.window_seconds

        # Clean old requests from window
        while client_state.request_times and client_state.request_times[0] < window_start:
            client_state.request_times.popleft()

        # Add current request
        client_state.request_times.append(now)

        # Check if over limit
        current_requests = len(client_state.request_times)

        # Handle burst tokens
        if current_requests > adjusted_limit:
            if client_state.burst_tokens > 0:
                client_state.burst_tokens -= 1
                logger.debug(
                    f"Used burst token for {client_id}, remaining: {client_state.burst_tokens}"
                )
            else:
                # Rate limit exceeded
                client_state.violation_count += 1
                backoff_seconds = self._calculate_backoff(client_state.violation_count)
                client_state.blocked_until = now + backoff_seconds

                # Log violation
                await self._log_rate_limit_violation(
                    client_id, user, domain, current_requests, adjusted_limit
                )

                return False, {
                    "error": "rate_limited",
                    "current_requests": current_requests,
                    "limit": adjusted_limit,
                    "window_seconds": rate_limit.window_seconds,
                    "blocked_for_seconds": backoff_seconds,
                    "violation_count": client_state.violation_count,
                    "business_cycle": cycle_info,
                    "message": f"Rate limit exceeded: {current_requests}/{adjusted_limit} requests in {rate_limit.window_seconds}s",
                }

        # Replenish burst tokens gradually
        if client_state.burst_tokens < rate_limit.burst_allowance:
            time_since_last = now - (
                client_state.request_times[-2] if len(client_state.request_times) > 1 else now - 1
            )
            if time_since_last > 10:  # Replenish every 10 seconds
                client_state.burst_tokens = min(
                    rate_limit.burst_allowance, client_state.burst_tokens + 1
                )

        # Update global metrics for DDoS detection
        self._update_global_metrics(now)

        return True, {
            "allowed": True,
            "current_requests": current_requests,
            "limit": adjusted_limit,
            "window_seconds": rate_limit.window_seconds,
            "burst_tokens": client_state.burst_tokens,
            "business_cycle": cycle_info,
            "multiplier": multiplier,
        }

    def _get_rate_limit(
        self, user: Optional[AuthenticatedUser], domain: DomainType
    ) -> Optional[RateLimit]:
        """Get rate limit configuration for user and domain"""
        if not user:
            # Anonymous users get guest limits
            guest_limits = self.rate_limits.get(UserRole.GUEST, {})
            return guest_limits.get(domain, guest_limits.get(DomainType.GENERAL))

        user_limits = self.rate_limits.get(user.role, {})
        return user_limits.get(domain, user_limits.get(DomainType.GENERAL))

    def _calculate_backoff(self, violation_count: int) -> int:
        """Calculate backoff time based on violation count"""
        return self.backoff_multipliers.get(
            min(violation_count, max(self.backoff_multipliers.keys())),
            3600,  # Default to 1 hour for severe violations
        )

    def _update_global_metrics(self, now: float):
        """Update global DDoS metrics"""
        if not self.enable_ddos_protection:
            return

        # Calculate requests per second over last 5 seconds
        window_start = now - 5.0
        recent_requests = 0
        unique_clients = set()

        for client_state in self.client_states.values():
            if client_state.last_request >= window_start:
                recent_requests += len([t for t in client_state.request_times if t >= window_start])
                unique_clients.add(client_state.client_id)

        self.global_metrics.requests_per_second = recent_requests / 5.0
        self.global_metrics.unique_clients = len(unique_clients)

        # Update alert level
        if self.global_metrics.requests_per_second > self.ddos_threshold_rps:
            if self.global_metrics.requests_per_second > self.ddos_threshold_rps * 2:
                self.global_metrics.alert_level = "critical"
            else:
                self.global_metrics.alert_level = "elevated"
        else:
            self.global_metrics.alert_level = "normal"

    async def _log_rate_limit_violation(
        self,
        client_id: str,
        user: Optional[AuthenticatedUser],
        domain: DomainType,
        current_requests: int,
        limit: int,
    ):
        """Log rate limit violation for security monitoring"""
        violation_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": client_id,
            "user_id": user.user_id if user else None,
            "username": user.username if user else None,
            "tenant_id": user.tenant_id if user else None,
            "tenant_type": user.tenant_type.value if user else None,
            "ip_address": user.ip_address if user else None,
            "domain": domain.value,
            "current_requests": current_requests,
            "limit": limit,
            "violation_type": "rate_limit_exceeded",
        }

        logger.warning(f"Rate limit violation: {violation_data}")

        # Store in Redis for security analysis
        if self.redis:
            try:
                await self.redis.lpush("websocket_violations", str(violation_data))
                await self.redis.ltrim("websocket_violations", 0, 1000)  # Keep last 1000
            except Exception as e:
                logger.error(f"Failed to log violation to Redis: {e}")

    async def detect_ddos_patterns(self) -> Optional[dict[str, Any]]:
        """Detect potential DDoS attack patterns"""
        if not self.enable_ddos_protection:
            return None

        time.time()
        alert_data = None

        # Detect high request rate
        if self.global_metrics.requests_per_second > self.ddos_threshold_rps:
            alert_data = {
                "type": "high_request_rate",
                "severity": self.global_metrics.alert_level,
                "requests_per_second": self.global_metrics.requests_per_second,
                "threshold": self.ddos_threshold_rps,
                "unique_clients": self.global_metrics.unique_clients,
            }

        # Detect suspicious client patterns
        suspicious_clients = []
        for client_id, state in self.client_states.items():
            if state.violation_count >= 3:  # Multiple violations
                suspicious_clients.append(
                    {
                        "client_id": client_id,
                        "violations": state.violation_count,
                        "total_requests": state.total_requests,
                        "user_id": state.user.user_id if state.user else None,
                        "ip_address": state.user.ip_address if state.user else None,
                    }
                )

        if suspicious_clients:
            alert_data = alert_data or {}
            alert_data["suspicious_clients"] = suspicious_clients
            alert_data["type"] = "suspicious_patterns"

        return alert_data

    async def apply_emergency_limits(self, duration_seconds: int = 300):
        """Apply emergency rate limits during DDoS attack"""
        logger.critical("Applying emergency rate limits due to DDoS detection")

        # Reduce all limits by 80%
        emergency_multiplier = 0.2

        for role_limits in self.rate_limits.values():
            for domain_limit in role_limits.values():
                domain_limit.limit = int(domain_limit.limit * emergency_multiplier)
                domain_limit.burst_allowance = 0

        # Schedule restoration
        async def restore_limits():
            await asyncio.sleep(duration_seconds)
            await self._restore_normal_limits()

        asyncio.create_task(restore_limits())

    async def _restore_normal_limits(self):
        """Restore normal rate limits after emergency period"""
        logger.info("Restoring normal rate limits")
        self.rate_limits = self._initialize_rate_limits()

    async def _ddos_monitor_loop(self):
        """Background task to monitor for DDoS attacks"""
        while True:
            try:
                alert_data = await self.detect_ddos_patterns()
                if alert_data and alert_data.get("severity") == "critical":
                    await self.apply_emergency_limits()

                    # Log critical security event
                    logger.critical(f"DDoS attack detected: {alert_data}")

                await asyncio.sleep(5)  # Check every 5 seconds
            except Exception as e:
                logger.error(f"Error in DDoS monitor: {e}")
                await asyncio.sleep(60)

    async def _cleanup_loop(self):
        """Background task to cleanup old client states"""
        while True:
            try:
                now = time.time()
                expired_clients = []

                for client_id, state in self.client_states.items():
                    # Remove clients inactive for more than 1 hour
                    if now - state.last_request > 3600:
                        expired_clients.append(client_id)

                for client_id in expired_clients:
                    del self.client_states[client_id]

                if expired_clients:
                    logger.info(f"Cleaned up {len(expired_clients)} expired client states")

                await asyncio.sleep(self.cleanup_interval)
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)

    def get_metrics(self) -> dict[str, Any]:
        """Get rate limiter metrics"""
        now = time.time()

        active_clients = len(
            [
                s
                for s in self.client_states.values()
                if now - s.last_request < 300  # Active in last 5 minutes
            ]
        )

        blocked_clients = len(
            [s for s in self.client_states.values() if s.blocked_until and now < s.blocked_until]
        )

        return {
            "total_clients": len(self.client_states),
            "active_clients": active_clients,
            "blocked_clients": blocked_clients,
            "global_metrics": {
                "requests_per_second": self.global_metrics.requests_per_second,
                "unique_clients": self.global_metrics.unique_clients,
                "blocked_requests": self.global_metrics.blocked_requests,
                "alert_level": self.global_metrics.alert_level,
            },
            "ddos_protection": self.enable_ddos_protection,
            "ddos_threshold_rps": self.ddos_threshold_rps,
        }

    async def reset_client_limits(self, client_id: str):
        """Reset rate limits for a specific client (admin function)"""
        if client_id in self.client_states:
            state = self.client_states[client_id]
            state.request_times.clear()
            state.violation_count = 0
            state.blocked_until = None
            state.burst_tokens = 0
            logger.info(f"Reset rate limits for client: {client_id}")

    async def get_client_status(self, client_id: str) -> Optional[dict[str, Any]]:
        """Get detailed status for a specific client"""
        if client_id not in self.client_states:
            return None

        state = self.client_states[client_id]
        now = time.time()

        return {
            "client_id": client_id,
            "user_id": state.user.user_id if state.user else None,
            "username": state.user.username if state.user else None,
            "tenant_id": state.user.tenant_id if state.user else None,
            "total_requests": state.total_requests,
            "violation_count": state.violation_count,
            "current_window_requests": len(state.request_times),
            "burst_tokens": state.burst_tokens,
            "is_blocked": state.blocked_until and now < state.blocked_until,
            "blocked_until": state.blocked_until,
            "last_request": state.last_request,
            "created_at": state.created_at,
        }
