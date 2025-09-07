"""
Rate Limit Monitoring and Management System
Tracks actual rate limits for each provider and optimizes routing
"""

import asyncio
import json
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class RateLimitInfo:
    """Track rate limit information for a virtual key"""

    virtual_key: str
    provider: str

    # Configured limits
    configured_tpm: int = 0
    configured_rpm: int = 0

    # Observed limits
    observed_tpm: int = 0
    observed_rpm: int = 0

    # Current usage
    tokens_used_minute: int = 0
    requests_this_minute: int = 0

    # Rate limit events
    last_rate_limit: Optional[datetime] = None
    rate_limit_count: int = 0

    # Performance metrics
    avg_latency: float = 0.0
    success_rate: float = 1.0

    # Sliding windows for tracking
    token_window: deque = field(default_factory=lambda: deque(maxlen=60))  # Last 60 seconds
    request_window: deque = field(default_factory=lambda: deque(maxlen=60))  # Last 60 seconds
    latency_window: deque = field(default_factory=lambda: deque(maxlen=100))  # Last 100 requests

    def update_usage(self, tokens: int, latency: float):
        """Update usage statistics"""

        now = time.time()

        # Add to windows
        self.token_window.append((now, tokens))
        self.request_window.append((now, 1))
        self.latency_window.append(latency)

        # Calculate current rates
        one_minute_ago = now - 60

        # Tokens per minute
        recent_tokens = sum(t for ts, t in self.token_window if ts > one_minute_ago)
        self.tokens_used_minute = recent_tokens

        # Requests per minute
        recent_requests = sum(r for ts, r in self.request_window if ts > one_minute_ago)
        self.requests_this_minute = recent_requests

        # Update average latency
        if self.latency_window:
            self.avg_latency = sum(self.latency_window) / len(self.latency_window)

    def record_rate_limit(self):
        """Record a rate limit event"""
        self.last_rate_limit = datetime.now()
        self.rate_limit_count += 1

        # Update observed limits based on when we hit them
        if self.tokens_used_minute > 0:
            self.observed_tpm = min(self.tokens_used_minute, self.configured_tpm)
        if self.requests_this_minute > 0:
            self.observed_rpm = min(self.requests_this_minute, self.configured_rpm)

    def get_availability(self) -> float:
        """Get current availability (0-1) based on usage vs limits"""

        # Token availability
        token_availability = 1.0
        if self.configured_tpm > 0:
            token_availability = max(0, 1 - (self.tokens_used_minute / self.configured_tpm))

        # Request availability
        request_availability = 1.0
        if self.configured_rpm > 0:
            request_availability = max(0, 1 - (self.requests_this_minute / self.configured_rpm))

        # Combined availability (minimum of both)
        return min(token_availability, request_availability) * self.success_rate

    def can_handle_request(self, estimated_tokens: int) -> bool:
        """Check if this key can handle a request"""

        # Check token capacity
        if self.configured_tpm > 0 and (
            self.tokens_used_minute + estimated_tokens > self.configured_tpm * 0.9
        ):  # 90% threshold
            return False

        # Check request capacity
        if self.configured_rpm > 0:
            if self.requests_this_minute + 1 > self.configured_rpm * 0.9:  # 90% threshold
                return False

        # Check if recently rate limited
        if self.last_rate_limit:
            time_since_limit = (datetime.now() - self.last_rate_limit).seconds
            if time_since_limit < 60:  # Wait at least 60 seconds after rate limit
                return False

        return True


class RateLimitMonitor:
    """Monitor and manage rate limits across all virtual keys"""

    def __init__(self):
        self.rate_limits: dict[str, RateLimitInfo] = {}
        self.request_history: list[dict[str, Any]] = []
        self.monitoring_enabled = True

        # Load configured limits
        self._load_configured_limits()

        # Start background monitoring
        self._start_monitoring()

    def _load_configured_limits(self):
        """Load configured rate limits from virtual keys config"""

        from app.swarms.core.portkey_virtual_keys import PROVIDER_CONFIGS

        for virtual_key, config in PROVIDER_CONFIGS.items():
            self.rate_limits[virtual_key] = RateLimitInfo(
                virtual_key=virtual_key,
                provider=config.get("provider", "unknown"),
                configured_tpm=config.get("tpm_limit", 0),
                configured_rpm=config.get("rpm_limit", 0),
            )

        logger.info(f"Loaded rate limit configs for {len(self.rate_limits)} virtual keys")

    def _start_monitoring(self):
        """Start background monitoring tasks"""
        import threading

        async def monitor_loop():
            while self.monitoring_enabled:
                await asyncio.sleep(10)  # Check every 10 seconds
                self._cleanup_old_data()
                self._analyze_patterns()

        # Try to start monitoring in background
        try:
            asyncio.get_running_loop()
            asyncio.create_task(monitor_loop())
        except RuntimeError:
            # No event loop running, create one in a thread for monitoring
            def run_monitor():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(monitor_loop())

            monitor_thread = threading.Thread(target=run_monitor, daemon=True)
            monitor_thread.start()

    def record_request(
        self,
        virtual_key: str,
        tokens_used: int,
        latency: float,
        success: bool,
        error: Optional[str] = None,
    ):
        """Record a request and its metrics"""

        if virtual_key not in self.rate_limits:
            logger.warning(f"Unknown virtual key: {virtual_key}")
            return

        rate_info = self.rate_limits[virtual_key]

        # Update usage
        rate_info.update_usage(tokens_used, latency)

        # Update success rate
        if not success:
            rate_info.success_rate *= 0.95  # Decay success rate

            # Check if it was a rate limit error
            if error and "rate limit" in error.lower():
                rate_info.record_rate_limit()
        else:
            rate_info.success_rate = min(1.0, rate_info.success_rate * 1.02)  # Slowly recover

        # Record in history
        self.request_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "virtual_key": virtual_key,
                "tokens": tokens_used,
                "latency": latency,
                "success": success,
                "error": error,
            }
        )

        # Keep history manageable
        if len(self.request_history) > 10000:
            self.request_history = self.request_history[-5000:]

    def get_best_key_for_task(
        self,
        estimated_tokens: int,
        preferred_providers: Optional[list[str]] = None,
        min_availability: float = 0.1,
    ) -> Optional[str]:
        """Get the best virtual key for a task based on current limits"""

        candidates = []

        for virtual_key, rate_info in self.rate_limits.items():
            # Filter by preferred providers
            if preferred_providers and rate_info.provider not in preferred_providers:
                continue

            # Check if it can handle the request
            if not rate_info.can_handle_request(estimated_tokens):
                continue

            # Check minimum availability
            availability = rate_info.get_availability()
            if availability < min_availability:
                continue

            # Calculate score
            score = (
                availability * 0.4
                + (1 / max(rate_info.avg_latency, 0.1)) * 0.3  # Availability is important
                + rate_info.success_rate  # Lower latency is better
                * 0.3  # Higher success rate is better
            )

            candidates.append((virtual_key, score, rate_info))

        if not candidates:
            return None

        # Sort by score and return best
        candidates.sort(key=lambda x: x[1], reverse=True)
        best_key, score, info = candidates[0]

        logger.debug(
            f"Selected {info.provider} (score: {score:.2f}, "
            f"availability: {info.get_availability():.2%})"
        )

        return best_key

    def get_provider_status(self, provider: str) -> dict[str, Any]:
        """Get current status for a specific provider"""

        for virtual_key, rate_info in self.rate_limits.items():
            if rate_info.provider == provider:
                return {
                    "provider": provider,
                    "virtual_key": virtual_key,
                    "availability": rate_info.get_availability(),
                    "tokens_used": rate_info.tokens_used_minute,
                    "tokens_limit": rate_info.configured_tpm,
                    "requests_used": rate_info.requests_this_minute,
                    "requests_limit": rate_info.configured_rpm,
                    "avg_latency": round(rate_info.avg_latency, 3),
                    "success_rate": round(rate_info.success_rate, 3),
                    "rate_limit_count": rate_info.rate_limit_count,
                    "last_rate_limit": (
                        rate_info.last_rate_limit.isoformat() if rate_info.last_rate_limit else None
                    ),
                }

        return {"provider": provider, "status": "not_configured"}

    def get_all_status(self) -> dict[str, Any]:
        """Get status for all providers"""

        status = {
            "timestamp": datetime.now().isoformat(),
            "providers": {},
            "summary": {
                "total_providers": len(self.rate_limits),
                "available_providers": 0,
                "total_tpm_available": 0,
                "total_rpm_available": 0,
            },
        }

        for _virtual_key, rate_info in self.rate_limits.items():
            provider_status = self.get_provider_status(rate_info.provider)
            status["providers"][rate_info.provider] = provider_status

            if rate_info.get_availability() > 0.1:
                status["summary"]["available_providers"] += 1
                status["summary"]["total_tpm_available"] += (
                    rate_info.configured_tpm - rate_info.tokens_used_minute
                )
                status["summary"]["total_rpm_available"] += (
                    rate_info.configured_rpm - rate_info.requests_this_minute
                )

        return status

    def _cleanup_old_data(self):
        """Clean up old data from sliding windows"""

        now = time.time()
        cutoff = now - 120  # Keep 2 minutes of data

        for rate_info in self.rate_limits.values():
            # Clean token window
            while rate_info.token_window and rate_info.token_window[0][0] < cutoff:
                rate_info.token_window.popleft()

            # Clean request window
            while rate_info.request_window and rate_info.request_window[0][0] < cutoff:
                rate_info.request_window.popleft()

    def _analyze_patterns(self):
        """Analyze usage patterns and adjust observed limits"""

        for rate_info in self.rate_limits.values():
            # If we've been hitting rate limits, adjust our observed limits
            if rate_info.rate_limit_count > 5:
                # Reduce observed limits by 10%
                rate_info.observed_tpm = int(rate_info.observed_tpm * 0.9)
                rate_info.observed_rpm = int(rate_info.observed_rpm * 0.9)
                rate_info.rate_limit_count = 0  # Reset counter

                logger.info(
                    f"Adjusted {rate_info.provider} limits: "
                    f"TPM: {rate_info.observed_tpm}, RPM: {rate_info.observed_rpm}"
                )

    def export_metrics(self, filepath: str = "rate_limit_metrics.json"):
        """Export current metrics to file"""

        metrics = {"exported_at": datetime.now().isoformat(), "providers": {}}

        for _virtual_key, rate_info in self.rate_limits.items():
            metrics["providers"][rate_info.provider] = {
                "configured_tpm": rate_info.configured_tpm,
                "configured_rpm": rate_info.configured_rpm,
                "observed_tpm": rate_info.observed_tpm,
                "observed_rpm": rate_info.observed_rpm,
                "current_usage": {
                    "tokens_per_minute": rate_info.tokens_used_minute,
                    "requests_per_minute": rate_info.requests_this_minute,
                },
                "performance": {
                    "avg_latency": round(rate_info.avg_latency, 3),
                    "success_rate": round(rate_info.success_rate, 3),
                    "availability": round(rate_info.get_availability(), 3),
                },
                "rate_limits": {
                    "hit_count": rate_info.rate_limit_count,
                    "last_hit": (
                        rate_info.last_rate_limit.isoformat() if rate_info.last_rate_limit else None
                    ),
                },
            }

        with open(filepath, "w") as f:
            json.dump(metrics, f, indent=2)

        logger.info(f"Exported metrics to {filepath}")
        return filepath


# Global instance
_monitor_instance: Optional[RateLimitMonitor] = None


def get_rate_monitor() -> RateLimitMonitor:
    """Get or create the global rate limit monitor"""
    global _monitor_instance

    if _monitor_instance is None:
        _monitor_instance = RateLimitMonitor()

    return _monitor_instance


# Example usage
if __name__ == "__main__":
    monitor = get_rate_monitor()

    # Simulate some requests
    monitor.record_request("openai-vk-190a60", tokens_used=500, latency=1.2, success=True)
    monitor.record_request("groq-vk-6b9b52", tokens_used=200, latency=0.3, success=True)
    monitor.record_request(
        "anthropic-vk-b42804",
        tokens_used=1000,
        latency=2.1,
        success=False,
        error="rate limit exceeded",
    )

    # Get best key for a task
    best_key = monitor.get_best_key_for_task(estimated_tokens=1000)
    print(f"Best key for 1000 tokens: {best_key}")

    # Get all status
    status = monitor.get_all_status()
    print(json.dumps(status, indent=2))

    # Export metrics
    monitor.export_metrics()
