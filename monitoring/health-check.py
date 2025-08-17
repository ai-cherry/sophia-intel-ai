#!/usr/bin/env python3
"""
SOPHIA Intel Health Check and Monitoring System
Production-grade monitoring with alerts, metrics, and observability
"""

import asyncio
import aiohttp
import json
import time
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("monitoring/logs/health-check.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Health check result data structure"""

    service: str
    url: str
    status: str
    response_time: float
    status_code: Optional[int]
    error: Optional[str]
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class MonitoringConfig:
    """Monitoring configuration"""

    services: Dict[str, str]
    thresholds: Dict[str, float]
    alert_webhooks: List[str]
    check_interval: int
    retention_days: int


class HealthMonitor:
    """Comprehensive health monitoring system"""

    def __init__(self, config_path: str = "monitoring/config.json"):
        self.config = self._load_config(config_path)
        self.results_history: List[HealthCheckResult] = []
        self.session: Optional[aiohttp.ClientSession] = None

    def _load_config(self, config_path: str) -> MonitoringConfig:
        """Load monitoring configuration"""
        default_config = {
            "services": {
                "frontend": "https://www.sophia-intel.ai",
                "frontend_fallback": "https://www.sophia-intel.ai",
                "api": "https://api.sophia-intel.ai",
                "api_health": "https://api.sophia-intel.ai/health",
            },
            "thresholds": {"response_time": 3.0, "error_rate": 0.05, "uptime": 0.999},
            "alert_webhooks": [],
            "check_interval": 300,  # 5 minutes
            "retention_days": 30,
        }

        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            logger.warning(f"Could not load config from {config_path}: {e}")

        return MonitoringConfig(**default_config)

    async def check_service_health(self, service: str, url: str) -> HealthCheckResult:
        """Check health of a single service"""
        start_time = time.time()

        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with self.session.get(url, timeout=timeout) as response:
                response_time = time.time() - start_time

                # Try to get response body for API endpoints
                metadata = {}
                if "/health" in url:
                    try:
                        body = await response.text()
                        metadata["response_body"] = body[:500]  # Limit size
                        if response.content_type == "application/json":
                            metadata["json_response"] = await response.json()
                    except Exception as e:
                        metadata["body_error"] = str(e)

                return HealthCheckResult(
                    service=service,
                    url=url,
                    status="healthy" if response.status < 400 else "unhealthy",
                    response_time=response_time,
                    status_code=response.status,
                    error=None,
                    timestamp=datetime.now(),
                    metadata=metadata,
                )

        except asyncio.TimeoutError:
            return HealthCheckResult(
                service=service,
                url=url,
                status="timeout",
                response_time=time.time() - start_time,
                status_code=None,
                error="Request timeout",
                timestamp=datetime.now(),
                metadata={},
            )
        except Exception as e:
            return HealthCheckResult(
                service=service,
                url=url,
                status="error",
                response_time=time.time() - start_time,
                status_code=None,
                error=str(e),
                timestamp=datetime.now(),
                metadata={},
            )

    async def run_health_checks(self) -> List[HealthCheckResult]:
        """Run health checks for all configured services"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        tasks = []
        for service, url in self.config.services.items():
            task = self.check_service_health(service, url)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        self.results_history.extend(results)

        # Clean up old results
        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
        self.results_history = [r for r in self.results_history if r.timestamp > cutoff_date]

        return results

    def analyze_results(self, results: List[HealthCheckResult]) -> Dict[str, Any]:
        """Analyze health check results and generate insights"""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_services": len(results),
            "healthy_services": len([r for r in results if r.status == "healthy"]),
            "unhealthy_services": len([r for r in results if r.status != "healthy"]),
            "average_response_time": sum(r.response_time for r in results) / len(results),
            "services": {},
            "alerts": [],
        }

        for result in results:
            analysis["services"][result.service] = {
                "status": result.status,
                "response_time": result.response_time,
                "status_code": result.status_code,
                "url": result.url,
            }

            # Check for alerts
            if result.status != "healthy":
                analysis["alerts"].append(
                    {
                        "type": "service_down",
                        "service": result.service,
                        "message": f"Service {result.service} is {result.status}",
                        "error": result.error,
                    }
                )

            if result.response_time > self.config.thresholds["response_time"]:
                analysis["alerts"].append(
                    {
                        "type": "slow_response",
                        "service": result.service,
                        "message": f"Service {result.service} response time is {result.response_time:.2f}s",
                        "threshold": self.config.thresholds["response_time"],
                    }
                )

        return analysis

    def generate_report(self, analysis: Dict[str, Any]) -> str:
        """Generate human-readable monitoring report"""
        report = []
        report.append("🏥 SOPHIA Intel Health Check Report")
        report.append("=" * 40)
        report.append(f"Timestamp: {analysis['timestamp']}")
        report.append(f"Services Checked: {analysis['total_services']}")
        report.append(f"Healthy: {analysis['healthy_services']}")
        report.append(f"Unhealthy: {analysis['unhealthy_services']}")
        report.append(f"Average Response Time: {analysis['average_response_time']:.2f}s")
        report.append("")

        # Service details
        report.append("📊 Service Status:")
        for service, details in analysis["services"].items():
            status_emoji = "✅" if details["status"] == "healthy" else "❌"
            report.append(f"{status_emoji} {service}: {details['status']} ({details['response_time']:.2f}s)")

        # Alerts
        if analysis["alerts"]:
            report.append("")
            report.append("🚨 Alerts:")
            for alert in analysis["alerts"]:
                report.append(f"- {alert['type']}: {alert['message']}")
        else:
            report.append("")
            report.append("✅ No alerts - all systems operational!")

        return "\n".join(report)

    async def save_results(self, results: List[HealthCheckResult], analysis: Dict[str, Any]):
        """Save monitoring results to files"""
        # Ensure directories exist
        os.makedirs("monitoring/logs", exist_ok=True)
        os.makedirs("monitoring/reports", exist_ok=True)

        # Save raw results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"monitoring/logs/results_{timestamp}.json"

        with open(results_file, "w") as f:
            json.dump([asdict(r) for r in results], f, indent=2, default=str)

        # Save analysis
        analysis_file = f"monitoring/reports/analysis_{timestamp}.json"
        with open(analysis_file, "w") as f:
            json.dump(analysis, f, indent=2, default=str)

        # Save human-readable report
        report = self.generate_report(analysis)
        report_file = f"monitoring/reports/report_{timestamp}.txt"
        with open(report_file, "w") as f:
            f.write(report)

        # Update latest report
        with open("monitoring/reports/latest_report.txt", "w") as f:
            f.write(report)

        logger.info(f"Results saved to {results_file}")
        logger.info(f"Analysis saved to {analysis_file}")
        logger.info(f"Report saved to {report_file}")

    async def run_monitoring_cycle(self):
        """Run a complete monitoring cycle"""
        logger.info("Starting SOPHIA Intel health monitoring cycle")

        try:
            # Run health checks
            results = await self.run_health_checks()

            # Analyze results
            analysis = self.analyze_results(results)

            # Save results
            await self.save_results(results, analysis)

            # Print report
            report = self.generate_report(analysis)
            print(report)

            # Send alerts if needed
            if analysis["alerts"]:
                await self.send_alerts(analysis)

            logger.info("Monitoring cycle completed successfully")

        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
            raise
        finally:
            if self.session:
                await self.session.close()

    async def send_alerts(self, analysis: Dict[str, Any]):
        """Send alerts via configured webhooks"""
        if not self.config.alert_webhooks:
            logger.info("No alert webhooks configured")
            return

        alert_payload = {
            "timestamp": analysis["timestamp"],
            "service": "SOPHIA Intel",
            "alerts": analysis["alerts"],
            "summary": f"{analysis['unhealthy_services']} of {analysis['total_services']} services unhealthy",
        }

        for webhook_url in self.config.alert_webhooks:
            try:
                async with self.session.post(webhook_url, json=alert_payload) as response:
                    if response.status == 200:
                        logger.info(f"Alert sent to {webhook_url}")
                    else:
                        logger.warning(f"Failed to send alert to {webhook_url}: {response.status}")
            except Exception as e:
                logger.error(f"Error sending alert to {webhook_url}: {e}")


async def main():
    """Main monitoring function"""
    monitor = HealthMonitor()
    await monitor.run_monitoring_cycle()


if __name__ == "__main__":
    asyncio.run(main())
