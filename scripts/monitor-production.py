#!/usr/bin/env python3
"""
Production Monitoring Script for Sophia AI Lambda Labs Deployment
Audit-compliant monitoring with comprehensive health checks and alerting
"""

import asyncio
import aiohttp
import json
import logging
import os
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('/tmp/monitor-production.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ServiceHealth:
    """Service health status"""
    name: str
    url: str
    status: str
    response_time_ms: float
    last_check: datetime
    error_message: Optional[str] = None

@dataclass
class InstanceMetrics:
    """Instance performance metrics"""
    instance_id: str
    instance_ip: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    gpu_utilization: float
    gpu_memory: float
    gpu_temperature: float
    timestamp: datetime

@dataclass
class CostMetrics:
    """Cost tracking metrics"""
    current_cost_per_hour: float
    total_instances: int
    cost_limit_per_hour: float
    projected_daily_cost: float
    projected_monthly_cost: float
    timestamp: datetime

class ProductionMonitor:
    """Production monitoring system for Sophia AI Lambda Labs deployment"""

    def __init__(self):
        self.lambda_api_key = os.getenv("LAMBDA_API_KEY")
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        self.cost_limit = float(os.getenv("LAMBDA_MAX_COST_PER_HOUR", "15.00"))
        self.alert_threshold_cpu = float(os.getenv("ALERT_THRESHOLD_CPU", "90.0"))
        self.alert_threshold_memory = float(os.getenv("ALERT_THRESHOLD_MEMORY", "85.0"))
        self.alert_threshold_gpu = float(os.getenv("ALERT_THRESHOLD_GPU", "95.0"))

        self.instances: List[Dict[str, Any]] = []
        self.service_health: List[ServiceHealth] = []
        self.metrics_history: List[InstanceMetrics] = []
        self.cost_history: List[CostMetrics] = []

        # Alert state tracking
        self.last_alerts = {}
        self.alert_cooldown = 300  # 5 minutes

    async def discover_instances(self) -> List[Dict[str, Any]]:
        """Discover running Lambda Labs instances"""
        if not self.lambda_api_key:
            logger.warning("Lambda Labs API key not configured")
            return []

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.lambda_api_key}"}
                async with session.get(
                    "https://cloud.lambdalabs.com/api/v1/instances",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        instances = [
                            inst for inst in data.get("data", [])
                            if inst.get("status") == "running" and 
                               inst.get("name", "").startswith("sophia-ai")
                        ]
                        logger.info(f"Discovered {len(instances)} Sophia AI instances")
                        return instances
                    else:
                        logger.error(f"Failed to fetch instances: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error discovering instances: {e}")

        return []

    async def check_service_health(self, instance_ip: str, port: int, service_name: str) -> ServiceHealth:
        """Check health of a specific service"""
        url = f"http://{instance_ip}:{port}/health"
        start_time = time.time()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_time = (time.time() - start_time) * 1000

                    if response.status == 200:
                        return ServiceHealth(
                            name=service_name,
                            url=url,
                            status="healthy",
                            response_time_ms=response_time,
                            last_check=datetime.now()
                        )
                    else:
                        return ServiceHealth(
                            name=service_name,
                            url=url,
                            status="unhealthy",
                            response_time_ms=response_time,
                            last_check=datetime.now(),
                            error_message=f"HTTP {response.status}"
                        )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ServiceHealth(
                name=service_name,
                url=url,
                status="error",
                response_time_ms=response_time,
                last_check=datetime.now(),
                error_message=str(e)
            )

    async def get_instance_metrics(self, instance_ip: str, instance_id: str) -> Optional[InstanceMetrics]:
        """Get performance metrics from instance"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{instance_ip}:9090/metrics",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return InstanceMetrics(
                            instance_id=instance_id,
                            instance_ip=instance_ip,
                            cpu_percent=data.get("cpu_percent", 0),
                            memory_percent=data.get("memory_percent", 0),
                            disk_percent=data.get("disk_percent", 0),
                            gpu_utilization=data.get("gpu_utilization", 0),
                            gpu_memory=data.get("gpu_memory", 0),
                            gpu_temperature=data.get("gpu_temperature", 0),
                            timestamp=datetime.now()
                        )
        except Exception as e:
            logger.warning(f"Failed to get metrics from {instance_ip}: {e}")

        return None

    async def get_cost_metrics(self) -> Optional[CostMetrics]:
        """Get cost metrics from Lambda Labs manager"""
        if not self.instances:
            return None

        try:
            # Use first instance to get cost data
            instance_ip = self.instances[0].get("ip")
            if not instance_ip:
                return None

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{instance_ip}:8002/cost-analysis",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        current_cost = data.get("current_cost_per_hour", 0)
                        return CostMetrics(
                            current_cost_per_hour=current_cost,
                            total_instances=len(self.instances),
                            cost_limit_per_hour=self.cost_limit,
                            projected_daily_cost=current_cost * 24,
                            projected_monthly_cost=current_cost * 24 * 30,
                            timestamp=datetime.now()
                        )
        except Exception as e:
            logger.warning(f"Failed to get cost metrics: {e}")

        return None

    async def send_alert(self, alert_type: str, message: str, severity: str = "warning"):
        """Send alert notification"""
        alert_key = f"{alert_type}_{severity}"
        current_time = time.time()

        # Check cooldown
        if alert_key in self.last_alerts:
            if current_time - self.last_alerts[alert_key] < self.alert_cooldown:
                return

        self.last_alerts[alert_key] = current_time

        # Log alert
        logger.warning(f"ALERT [{severity.upper()}] {alert_type}: {message}")

        # Send to Slack if configured
        if self.slack_webhook:
            await self.send_slack_alert(alert_type, message, severity)

    async def send_slack_alert(self, alert_type: str, message: str, severity: str):
        """Send alert to Slack"""
        color_map = {
            "info": "#36a64f",
            "warning": "#ff9500", 
            "critical": "#ff0000"
        }

        payload = {
            "attachments": [{
                "color": color_map.get(severity, "#ff9500"),
                "title": f"Sophia AI Alert: {alert_type}",
                "text": message,
                "footer": "Sophia AI Production Monitor",
                "ts": int(time.time())
            }]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.slack_webhook,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        logger.error(f"Failed to send Slack alert: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")

    async def check_alerts(self, metrics: InstanceMetrics, cost_metrics: Optional[CostMetrics]):
        """Check for alert conditions"""

        # CPU alert
        if metrics.cpu_percent > self.alert_threshold_cpu:
            await self.send_alert(
                "High CPU Usage",
                f"Instance {metrics.instance_id} CPU usage: {metrics.cpu_percent:.1f}%",
                "warning"
            )

        # Memory alert
        if metrics.memory_percent > self.alert_threshold_memory:
            await self.send_alert(
                "High Memory Usage",
                f"Instance {metrics.instance_id} memory usage: {metrics.memory_percent:.1f}%",
                "warning"
            )

        # GPU alert
        if metrics.gpu_utilization > self.alert_threshold_gpu:
            await self.send_alert(
                "High GPU Usage",
                f"Instance {metrics.instance_id} GPU usage: {metrics.gpu_utilization:.1f}%",
                "warning"
            )

        # GPU temperature alert
        if metrics.gpu_temperature > 85:
            await self.send_alert(
                "High GPU Temperature",
                f"Instance {metrics.instance_id} GPU temperature: {metrics.gpu_temperature:.1f}°C",
                "critical"
            )

        # Cost alert
        if cost_metrics and cost_metrics.current_cost_per_hour > self.cost_limit:
            await self.send_alert(
                "Cost Limit Exceeded",
                f"Current cost: ${cost_metrics.current_cost_per_hour:.2f}/hour > ${self.cost_limit:.2f}/hour",
                "critical"
            )

    async def emergency_shutdown(self, instance_id: str, reason: str):
        """Emergency shutdown of instance"""
        logger.critical(f"EMERGENCY SHUTDOWN: {instance_id} - {reason}")

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.lambda_api_key}"}
                payload = {"instance_ids": [instance_id]}

                async with session.post(
                    "https://cloud.lambdalabs.com/api/v1/instance-operations/terminate",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Successfully terminated instance {instance_id}")
                        await self.send_alert(
                            "Emergency Shutdown",
                            f"Instance {instance_id} terminated: {reason}",
                            "critical"
                        )
                    else:
                        logger.error(f"Failed to terminate instance {instance_id}: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error during emergency shutdown: {e}")

    async def generate_report(self) -> Dict[str, Any]:
        """Generate monitoring report"""
        current_time = datetime.now()

        # Calculate averages from recent metrics
        recent_metrics = [
            m for m in self.metrics_history 
            if (current_time - m.timestamp).total_seconds() < 3600  # Last hour
        ]

        avg_cpu = statistics.mean([m.cpu_percent for m in recent_metrics]) if recent_metrics else 0
        avg_memory = statistics.mean([m.memory_percent for m in recent_metrics]) if recent_metrics else 0
        avg_gpu = statistics.mean([m.gpu_utilization for m in recent_metrics]) if recent_metrics else 0

        # Service health summary
        healthy_services = sum(1 for s in self.service_health if s.status == "healthy")
        total_services = len(self.service_health)

        # Cost summary
        latest_cost = self.cost_history[-1] if self.cost_history else None

        return {
            "timestamp": current_time.isoformat(),
            "summary": {
                "total_instances": len(self.instances),
                "healthy_services": f"{healthy_services}/{total_services}",
                "avg_cpu_percent": round(avg_cpu, 1),
                "avg_memory_percent": round(avg_memory, 1),
                "avg_gpu_utilization": round(avg_gpu, 1),
                "current_cost_per_hour": latest_cost.current_cost_per_hour if latest_cost else 0,
                "projected_monthly_cost": latest_cost.projected_monthly_cost if latest_cost else 0
            },
            "instances": [
                {
                    "id": inst["id"],
                    "ip": inst["ip"],
                    "type": inst["instance_type"]["name"],
                    "region": inst["region"]["name"],
                    "status": inst["status"]
                }
                for inst in self.instances
            ],
            "services": [asdict(s) for s in self.service_health],
            "recent_metrics": [asdict(m) for m in recent_metrics[-10:]],  # Last 10 metrics
            "cost_metrics": asdict(latest_cost) if latest_cost else None
        }

    async def monitoring_cycle(self):
        """Single monitoring cycle"""
        logger.info("Starting monitoring cycle...")

        # Discover instances
        self.instances = await self.discover_instances()

        if not self.instances:
            logger.warning("No Sophia AI instances found")
            return

        # Check service health for each instance
        self.service_health = []
        for instance in self.instances:
            instance_ip = instance.get("ip")
            if not instance_ip:
                continue

            # Check all services
            services = [
                (8000, "Backend API"),
                (8001, "MCP Server"),
                (8002, "Lambda Manager"),
                (9090, "Monitoring"),
                (6333, "Qdrant")
            ]

            for port, name in services:
                health = await self.check_service_health(instance_ip, port, name)
                self.service_health.append(health)

        # Get performance metrics
        for instance in self.instances:
            instance_ip = instance.get("ip")
            instance_id = instance.get("id")

            if instance_ip and instance_id:
                metrics = await self.get_instance_metrics(instance_ip, instance_id)
                if metrics:
                    self.metrics_history.append(metrics)

                    # Get cost metrics
                    cost_metrics = await self.get_cost_metrics()
                    if cost_metrics:
                        self.cost_history.append(cost_metrics)

                    # Check for alerts
                    await self.check_alerts(metrics, cost_metrics)

                    # Emergency shutdown conditions
                    if cost_metrics and cost_metrics.current_cost_per_hour > self.cost_limit * 1.5:
                        await self.emergency_shutdown(
                            instance_id,
                            f"Cost exceeded 150% of limit: ${cost_metrics.current_cost_per_hour:.2f}/hour"
                        )

                    if metrics.gpu_temperature > 90:
                        await self.emergency_shutdown(
                            instance_id,
                            f"GPU temperature critical: {metrics.gpu_temperature:.1f}°C"
                        )

        # Cleanup old data (keep last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.metrics_history = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        self.cost_history = [c for c in self.cost_history if c.timestamp > cutoff_time]

        logger.info("Monitoring cycle complete")

    async def run_continuous(self, interval: int = 60):
        """Run continuous monitoring"""
        logger.info(f"Starting continuous monitoring (interval: {interval}s)")

        while True:
            try:
                await self.monitoring_cycle()

                # Generate and save report
                report = await self.generate_report()
                with open("/tmp/monitoring-report.json", "w") as f:
                    json.dump(report, f, indent=2, default=str)

                await asyncio.sleep(interval)

            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}")
                await asyncio.sleep(interval)

    async def run_once(self):
        """Run single monitoring cycle and generate report"""
        await self.monitoring_cycle()
        report = await self.generate_report()

        print(json.dumps(report, indent=2, default=str))

        # Save report
        with open("/tmp/monitoring-report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info("Report saved to /tmp/monitoring-report.json")

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Sophia AI Production Monitor")
    parser.add_argument("--continuous", action="store_true", help="Run continuous monitoring")
    parser.add_argument("--interval", type=int, default=60, help="Monitoring interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run once and exit")

    args = parser.parse_args()

    monitor = ProductionMonitor()

    if args.continuous:
        await monitor.run_continuous(args.interval)
    else:
        await monitor.run_once()

if __name__ == "__main__":
    asyncio.run(main())
