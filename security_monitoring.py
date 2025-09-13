#!/usr/bin/env python3
"""
Security Monitoring for Sophia Dashboard
This script sets up and runs security monitoring tools for the Sophia Dashboard,
including:
1. API monitoring for suspicious activity
2. Authentication failure tracking
3. Rate limiting monitoring
4. Access control violation detection
"""
import argparse
import asyncio
import datetime
import json
import logging
import signal
import sys
import time
from typing import Any
import aiohttp
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("security_monitoring.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
# Default API URL
DEFAULT_API_URL = "http://localhost:8000"
# Alert thresholds
THRESHOLDS = {
    "auth_failures": 5,  # Alert after 5 auth failures from same IP
    "rate_limit_hits": 3,  # Alert after 3 rate limit hits from same IP
    "access_violations": 2,  # Alert after 2 access violations from same user
    "suspicious_activity_score": 0.7,  # Alert if suspicious activity score exceeds this threshold
}
class SecurityMonitor:
    def __init__(
        self, api_url: str = DEFAULT_API_URL, alert_webhook: str | None = None
    ):
        self.api_url = api_url
        self.alert_webhook = alert_webhook
        self.auth_failures: dict[str, int] = {}  # IP -> count
        self.rate_limit_hits: dict[str, int] = {}  # IP -> count
        self.access_violations: dict[str, int] = {}  # user_id -> count
        self.running = False
    async def start_monitoring(self):
        """Start all monitoring tasks"""
        self.running = True
        logger.info("Starting Sophia Dashboard security monitoring")
        # Set up signal handlers for graceful shutdown
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._handle_shutdown)
        try:
            # Start all monitoring tasks
            await asyncio.gather(
                self._monitor_auth_failures(),
                self._monitor_api_access(),
                self._monitor_rate_limits(),
                self._scan_logs(),
            )
        except asyncio.CancelledError:
            logger.info("Monitoring tasks cancelled")
        finally:
            self.running = False
            logger.info("Security monitoring stopped")
    async def _monitor_auth_failures(self):
        """Monitor authentication failures"""
        logger.info("Starting authentication failure monitoring")
        while self.running:
            try:
                # In a real implementation, this would connect to logs or an event stream
                # For this example, we'll simulate by periodically checking an endpoint
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.api_url}/api/monitoring/auth-failures"
                    ) as response:
                        if response.status == 200:
                            failures = await response.json()
                            # Process each failure
                            for failure in failures:
                                ip = failure.get("ip_address")
                                if ip:
                                    self.auth_failures[ip] = (
                                        self.auth_failures.get(ip, 0) + 1
                                    )
                                    # Check threshold
                                    if (
                                        self.auth_failures[ip]
                                        >= THRESHOLDS["auth_failures"]
                                    ):
                                        await self._send_alert(
                                            "auth_failure",
                                            f"Multiple authentication failures from IP: {ip}",
                                            {"ip": ip, "count": self.auth_failures[ip]},
                                        )
                                        # Reset counter after alert
                                        self.auth_failures[ip] = 0
            except Exception as e:
                logger.error(f"Error in auth failure monitoring: {e}")
            # Wait before next check
            await asyncio.sleep(30)
    async def _monitor_api_access(self):
        """Monitor API access for suspicious activity"""
        logger.info("Starting API access monitoring")
        while self.running:
            try:
                # In a real implementation, this would analyze access patterns
                # For this example, we'll simulate by periodically checking an endpoint
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.api_url}/api/monitoring/access-violations"
                    ) as response:
                        if response.status == 200:
                            violations = await response.json()
                            # Process each violation
                            for violation in violations:
                                user_id = violation.get("user_id")
                                if user_id:
                                    self.access_violations[user_id] = (
                                        self.access_violations.get(user_id, 0) + 1
                                    )
                                    # Check threshold
                                    if (
                                        self.access_violations[user_id]
                                        >= THRESHOLDS["access_violations"]
                                    ):
                                        await self._send_alert(
                                            "access_violation",
                                            f"Multiple access violations by user: {user_id}",
                                            {
                                                "user_id": user_id,
                                                "count": self.access_violations[
                                                    user_id
                                                ],
                                            },
                                        )
                                        # Reset counter after alert
                                        self.access_violations[user_id] = 0
            except Exception as e:
                logger.error(f"Error in API access monitoring: {e}")
            # Wait before next check
            await asyncio.sleep(60)
    async def _monitor_rate_limits(self):
        """Monitor rate limit hits"""
        logger.info("Starting rate limit monitoring")
        while self.running:
            try:
                # In a real implementation, this would connect to the rate limiter's metrics
                # For this example, we'll simulate by periodically checking an endpoint
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.api_url}/api/monitoring/rate-limits"
                    ) as response:
                        if response.status == 200:
                            rate_limits = await response.json()
                            # Process each rate limit hit
                            for hit in rate_limits:
                                ip = hit.get("ip_address")
                                if ip:
                                    self.rate_limit_hits[ip] = (
                                        self.rate_limit_hits.get(ip, 0) + 1
                                    )
                                    # Check threshold
                                    if (
                                        self.rate_limit_hits[ip]
                                        >= THRESHOLDS["rate_limit_hits"]
                                    ):
                                        await self._send_alert(
                                            "rate_limit",
                                            f"Multiple rate limit hits from IP: {ip}",
                                            {
                                                "ip": ip,
                                                "count": self.rate_limit_hits[ip],
                                            },
                                        )
                                        # Reset counter after alert
                                        self.rate_limit_hits[ip] = 0
            except Exception as e:
                logger.error(f"Error in rate limit monitoring: {e}")
            # Wait before next check
            await asyncio.sleep(45)
    async def _scan_logs(self):
        """Periodically scan logs for suspicious patterns"""
        logger.info("Starting log scanning")
        while self.running:
            try:
                # In a real implementation, this would analyze actual log files
                # For this example, we'll simulate the results
                # Simulate finding suspicious activity
                if time.time() % 300 < 10:  # Randomly trigger every ~5 minutes
                    suspicious_score = 0.8  # Simulated score
                    if suspicious_score >= THRESHOLDS["suspicious_activity_score"]:
                        await self._send_alert(
                            "suspicious_activity",
                            "Suspicious activity detected in logs",
                            {
                                "score": suspicious_score,
                                "indicators": [
                                    "unusual access pattern",
                                    "off-hours activity",
                                ],
                            },
                        )
            except Exception as e:
                logger.error(f"Error in log scanning: {e}")
            # Wait before next scan
            await asyncio.sleep(120)
    async def _send_alert(self, alert_type: str, message: str, details: dict[str, Any]):
        """Send security alert"""
        timestamp = datetime.datetime.now().isoformat()
        alert = {
            "type": alert_type,
            "message": message,
            "timestamp": timestamp,
            "details": details,
        }
        # Log the alert
        logger.warning(f"SECURITY ALERT: {message}")
        # Write to alerts file
        with open("security_alerts.jsonl", "a") as f:
            f.write(json.dumps(alert) + "\n")
        # Send to webhook if configured
        if self.alert_webhook:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.alert_webhook,
                        json=alert,
                        headers={"Content-Type": "application/json"},
                    ) as response:
                        if response.status != 200:
                            logger.error(
                                f"Failed to send alert to webhook: {response.status}"
                            )
            except Exception as e:
                logger.error(f"Error sending alert to webhook: {e}")
    def _handle_shutdown(self, sig, frame):
        """Handle shutdown signals"""
        logger.info(f"Received shutdown signal {sig}, stopping...")
        self.running = False
        sys.exit(0)
def main():
    parser = argparse.ArgumentParser(description="Sophia Dashboard Security Monitoring")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="API URL to monitor")
    parser.add_argument("--webhook", help="Webhook URL for alerts")
    args = parser.parse_args()
    monitor = SecurityMonitor(args.api_url, args.webhook)
    try:
        asyncio.run(monitor.start_monitoring())
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
if __name__ == "__main__":
    main()
