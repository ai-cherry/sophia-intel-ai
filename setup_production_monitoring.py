#!/usr/bin/env python3
"""
Production Monitoring and Alerting System for Gong Integration
Sets up comprehensive monitoring for the complete Gong → n8n → Sophia pipeline
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, List

import httpx

# Configuration
MONITORING_CONFIG = {
    "n8n": {
        "instance_url": "https://scoobyjava.app.n8n.cloud",
        "api_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzN2Y4NTVkMi05ODIwLTQ2ZmMtYjlhMS1kMjdlN2ZhMGQ3MDIiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzUwMjgyMjU5LCJleHAiOjE3NTgwMDYwMDB9.5uLdSTZdIwlSld3WpVGC0TVm97vvzXs3y44FNeRm3N8",
        "webhook_url": "https://scoobyjava.app.n8n.cloud/webhook/gong-webhook",
    },
    "sophia": {
        "api_url": "http://localhost:8000",
        "health_endpoint": "/health",
        "gong_integration_endpoint": "/integrations/gong/health",
    },
    "monitoring": {
        "check_interval": 60,  # seconds
        "alert_threshold_errors": 3,
        "performance_threshold_ms": 5000,
        "success_rate_threshold": 0.85,
    },
}


class GongIntegrationMonitor:
    """Comprehensive production monitoring for Gong integration pipeline"""

    def __init__(self):
        self.monitoring_data = {
            "start_time": datetime.now().isoformat(),
            "checks_performed": 0,
            "alerts_generated": 0,
            "health_history": [],
            "performance_metrics": {
                "webhook_response_times": [],
                "sophia_processing_times": [],
                "success_rate": 1.0,
                "error_count": 0,
            },
        }

        self.n8n_headers = {
            "X-N8N-API-KEY": MONITORING_CONFIG["n8n"]["api_key"],
            "Content-Type": "application/json",
        }

    async def start_monitoring(self):
        """Start continuous monitoring loop"""
        print("🔍 STARTING PRODUCTION MONITORING FOR GONG INTEGRATION")
        print("=" * 60)
        print(f"Monitor Start Time: {self.monitoring_data['start_time']}")
        print(f"Check Interval: {MONITORING_CONFIG['monitoring']['check_interval']}s")
        print("=" * 60)

        while True:
            try:
                await self.perform_health_checks()
                await self.test_integration_pipeline()
                await self.analyze_performance_metrics()
                await self.check_for_alerts()

                # Wait for next check interval
                await asyncio.sleep(MONITORING_CONFIG["monitoring"]["check_interval"])

            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                await asyncio.sleep(30)  # Wait before retrying

    async def perform_health_checks(self):
        """Perform comprehensive health checks"""
        self.monitoring_data["checks_performed"] += 1
        check_time = datetime.now()

        print(
            f"\n🏥 Health Check #{self.monitoring_data['checks_performed']} - {check_time.strftime('%H:%M:%S')}"
        )

        health_status = {
            "timestamp": check_time.isoformat(),
            "n8n": await self._check_n8n_health(),
            "sophia": await self._check_sophia_health(),
            "webhook_endpoint": await self._check_webhook_endpoint(),
            "gong_integration": await self._check_gong_integration_health(),
        }

        # Store health history (keep last 100 checks)
        self.monitoring_data["health_history"].append(health_status)
        if len(self.monitoring_data["health_history"]) > 100:
            self.monitoring_data["health_history"].pop(0)

        # Report health status
        healthy_components = sum(
            1
            for component, status in health_status.items()
            if component != "timestamp" and status.get("healthy", False)
        )
        total_components = len(health_status) - 1  # Exclude timestamp

        if healthy_components == total_components:
            print(
                f"✅ All components healthy ({healthy_components}/{total_components})"
            )
        else:
            print(
                f"⚠️ Health issues detected ({healthy_components}/{total_components} healthy)"
            )
            await self._generate_health_alert(health_status)

    async def _check_n8n_health(self) -> Dict[str, Any]:
        """Check n8n instance health and workflows"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Check n8n instance health
                response = await client.get(
                    f"{MONITORING_CONFIG['n8n']['instance_url']}/api/v1/workflows",
                    headers=self.n8n_headers,
                )

                if response.status_code == 200:
                    workflows = response.json()
                    active_workflows = sum(
                        1 for wf in workflows.get("data", []) if wf.get("active", False)
                    )

                    return {
                        "healthy": True,
                        "status_code": response.status_code,
                        "total_workflows": len(workflows.get("data", [])),
                        "active_workflows": active_workflows,
                        "response_time": response.elapsed.total_seconds(),
                    }
                else:
                    return {
                        "healthy": False,
                        "status_code": response.status_code,
                        "error": "n8n API not responding correctly",
                    }

        except Exception as e:
            return {"healthy": False, "error": str(e)}

    async def _check_sophia_health(self) -> Dict[str, Any]:
        """Check Sophia system health"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{MONITORING_CONFIG['sophia']['api_url']}/health"
                )

                if response.status_code == 200:
                    health_data = response.json()
                    return {
                        "healthy": True,
                        "status_code": response.status_code,
                        "services": health_data.get("services", {}),
                        "response_time": response.elapsed.total_seconds(),
                    }
                else:
                    return {
                        "healthy": False,
                        "status_code": response.status_code,
                        "error": "Sophia API health check failed",
                    }

        except Exception as e:
            return {"healthy": False, "error": str(e)}

    async def _check_webhook_endpoint(self) -> Dict[str, Any]:
        """Check webhook endpoint responsiveness"""
        try:
            start_time = time.time()

            async with httpx.AsyncClient(timeout=15.0) as client:
                test_payload = {
                    "eventType": "monitoring_test",
                    "callId": f"monitor_test_{int(time.time())}",
                    "timestamp": datetime.now().isoformat(),
                    "source": "production_monitoring",
                }

                response = await client.post(
                    MONITORING_CONFIG["n8n"]["webhook_url"], json=test_payload
                )

                response_time = time.time() - start_time

                if response.status_code in [200, 201, 202]:
                    return {
                        "healthy": True,
                        "status_code": response.status_code,
                        "response_time": response_time,
                        "response": response.text[:100],
                    }
                else:
                    return {
                        "healthy": False,
                        "status_code": response.status_code,
                        "response_time": response_time,
                        "error": "Webhook not responding correctly",
                    }

        except Exception as e:
            return {"healthy": False, "error": str(e)}

    async def _check_gong_integration_health(self) -> Dict[str, Any]:
        """Check Gong integration service health"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{MONITORING_CONFIG['sophia']['api_url']}/integrations/gong/health"
                )

                if response.status_code == 200:
                    health_data = response.json()
                    return {
                        "healthy": True,
                        "status_code": response.status_code,
                        "components": health_data.get("components", {}),
                        "response_time": response.elapsed.total_seconds(),
                    }
                else:
                    return {
                        "healthy": False,
                        "status_code": response.status_code,
                        "error": "Gong integration health check failed",
                    }

        except Exception as e:
            return {"healthy": False, "error": str(e)}

    async def test_integration_pipeline(self):
        """Test the complete integration pipeline end-to-end"""
        print("🔄 Testing integration pipeline...")

        try:
            # Test with different event types
            test_events = [
                {
                    "eventType": "call_ended",
                    "callId": f"pipeline_test_call_{int(time.time())}",
                    "participants": ["test@monitoring.com"],
                    "duration": 1200,
                    "timestamp": datetime.now().isoformat(),
                    "source": "pipeline_monitoring_test",
                },
                {
                    "eventType": "deal_at_risk",
                    "dealId": f"pipeline_test_deal_{int(time.time())}",
                    "callId": f"pipeline_test_call_{int(time.time())}",
                    "riskLevel": "high",
                    "timestamp": datetime.now().isoformat(),
                    "source": "pipeline_monitoring_test",
                },
            ]

            pipeline_results = []

            for test_event in test_events:
                start_time = time.time()

                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.post(
                            MONITORING_CONFIG["n8n"]["webhook_url"], json=test_event
                        )

                        processing_time = time.time() - start_time

                        result = {
                            "event_type": test_event["eventType"],
                            "success": response.status_code in [200, 201, 202],
                            "response_time": processing_time,
                            "status_code": response.status_code,
                        }

                        pipeline_results.append(result)

                        if result["success"]:
                            print(
                                f"  ✅ {test_event['eventType']}: {processing_time:.3f}s"
                            )
                        else:
                            print(
                                f"  ❌ {test_event['eventType']}: Failed ({response.status_code})"
                            )
                            self.monitoring_data["performance_metrics"][
                                "error_count"
                            ] += 1

                        # Store performance metrics
                        self.monitoring_data["performance_metrics"][
                            "webhook_response_times"
                        ].append(processing_time)

                except Exception as e:
                    print(f"  ❌ {test_event['eventType']}: Error - {e}")
                    self.monitoring_data["performance_metrics"]["error_count"] += 1

                # Brief pause between tests
                await asyncio.sleep(1)

            # Calculate success rate
            successful_tests = sum(
                1 for result in pipeline_results if result["success"]
            )
            success_rate = (
                successful_tests / len(pipeline_results) if pipeline_results else 0
            )
            self.monitoring_data["performance_metrics"]["success_rate"] = success_rate

            print(f"🎯 Pipeline test complete: {success_rate:.1%} success rate")

        except Exception as e:
            print(f"❌ Pipeline testing error: {e}")

    async def analyze_performance_metrics(self):
        """Analyze performance metrics and identify trends"""
        metrics = self.monitoring_data["performance_metrics"]

        if len(metrics["webhook_response_times"]) > 0:
            recent_times = metrics["webhook_response_times"][
                -10:
            ]  # Last 10 measurements
            avg_response_time = (
                sum(recent_times) / len(recent_times) * 1000
            )  # Convert to ms

            print("📊 Performance Metrics:")
            print(f"   Average Response Time: {avg_response_time:.1f}ms")
            print(f"   Success Rate: {metrics['success_rate']:.1%}")
            print(f"   Total Errors: {metrics['error_count']}")

            # Check performance thresholds
            if (
                avg_response_time
                > MONITORING_CONFIG["monitoring"]["performance_threshold_ms"]
            ):
                await self._generate_performance_alert(
                    "high_response_time", avg_response_time
                )

            if (
                metrics["success_rate"]
                < MONITORING_CONFIG["monitoring"]["success_rate_threshold"]
            ):
                await self._generate_performance_alert(
                    "low_success_rate", metrics["success_rate"]
                )

    async def check_for_alerts(self):
        """Check if any alerts need to be generated"""
        # Check recent health history for consecutive failures
        if len(self.monitoring_data["health_history"]) >= 3:
            recent_health = self.monitoring_data["health_history"][-3:]

            # Check for consecutive failures of any component
            for component in ["n8n", "sophia", "webhook_endpoint", "gong_integration"]:
                consecutive_failures = sum(
                    1
                    for health in recent_health
                    if not health[component].get("healthy", False)
                )

                if (
                    consecutive_failures
                    >= MONITORING_CONFIG["monitoring"]["alert_threshold_errors"]
                ):
                    await self._generate_component_alert(
                        component, consecutive_failures
                    )

    async def _generate_health_alert(self, health_status: Dict[str, Any]):
        """Generate alert for health issues"""
        alert = {
            "type": "health_alert",
            "timestamp": datetime.now().isoformat(),
            "severity": "warning",
            "message": "Component health issues detected",
            "details": health_status,
        }

        self.monitoring_data["alerts_generated"] += 1

        print(f"🚨 HEALTH ALERT #{self.monitoring_data['alerts_generated']}")
        print(f"   Time: {alert['timestamp']}")
        print(f"   Issue: {alert['message']}")

        # Save alert to file
        await self._save_alert(alert)

    async def _generate_performance_alert(self, alert_type: str, metric_value: float):
        """Generate alert for performance issues"""
        alert_messages = {
            "high_response_time": f"High response time detected: {metric_value:.1f}ms",
            "low_success_rate": f"Low success rate detected: {metric_value:.1%}",
        }

        alert = {
            "type": "performance_alert",
            "timestamp": datetime.now().isoformat(),
            "severity": "warning",
            "alert_type": alert_type,
            "metric_value": metric_value,
            "message": alert_messages.get(
                alert_type, f"Performance issue: {alert_type}"
            ),
            "threshold": (
                MONITORING_CONFIG["monitoring"]["performance_threshold_ms"]
                if alert_type == "high_response_time"
                else MONITORING_CONFIG["monitoring"]["success_rate_threshold"]
            ),
        }

        self.monitoring_data["alerts_generated"] += 1

        print(f"⚡ PERFORMANCE ALERT #{self.monitoring_data['alerts_generated']}")
        print(f"   Time: {alert['timestamp']}")
        print(f"   Issue: {alert['message']}")

        await self._save_alert(alert)

    async def _generate_component_alert(self, component: str, failure_count: int):
        """Generate alert for component failures"""
        alert = {
            "type": "component_alert",
            "timestamp": datetime.now().isoformat(),
            "severity": "critical",
            "component": component,
            "failure_count": failure_count,
            "message": f"Component '{component}' has failed {failure_count} consecutive health checks",
            "recommended_action": f"Investigate {component} component immediately",
        }

        self.monitoring_data["alerts_generated"] += 1

        print(f"🔴 CRITICAL ALERT #{self.monitoring_data['alerts_generated']}")
        print(f"   Time: {alert['timestamp']}")
        print(f"   Component: {component}")
        print(f"   Failures: {failure_count} consecutive")
        print(f"   Action: {alert['recommended_action']}")

        await self._save_alert(alert)

    async def _save_alert(self, alert: Dict[str, Any]):
        """Save alert to file for later review"""
        alert_file = f"production_alerts_{datetime.now().strftime('%Y%m%d')}.json"

        try:
            # Load existing alerts
            try:
                with open(alert_file) as f:
                    alerts = json.load(f)
            except FileNotFoundError:
                alerts = []

            # Add new alert
            alerts.append(alert)

            # Save updated alerts
            with open(alert_file, "w") as f:
                json.dump(alerts, f, indent=2)

        except Exception as e:
            print(f"❌ Failed to save alert: {e}")

    def save_monitoring_report(self):
        """Save comprehensive monitoring report"""
        report_file = (
            f"monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        # Calculate summary statistics
        recent_health = (
            self.monitoring_data["health_history"][-10:]
            if self.monitoring_data["health_history"]
            else []
        )

        if recent_health:
            component_health = {}
            for component in ["n8n", "sophia", "webhook_endpoint", "gong_integration"]:
                healthy_count = sum(
                    1
                    for health in recent_health
                    if health[component].get("healthy", False)
                )
                component_health[component] = {
                    "health_percentage": healthy_count / len(recent_health) * 100,
                    "recent_checks": len(recent_health),
                }
        else:
            component_health = {}

        report = {
            "monitoring_period": {
                "start_time": self.monitoring_data["start_time"],
                "end_time": datetime.now().isoformat(),
                "duration_hours": (
                    datetime.now()
                    - datetime.fromisoformat(self.monitoring_data["start_time"])
                ).total_seconds()
                / 3600,
            },
            "summary": {
                "total_checks": self.monitoring_data["checks_performed"],
                "total_alerts": self.monitoring_data["alerts_generated"],
                "current_success_rate": self.monitoring_data["performance_metrics"][
                    "success_rate"
                ],
                "total_errors": self.monitoring_data["performance_metrics"][
                    "error_count"
                ],
            },
            "component_health": component_health,
            "performance_metrics": self.monitoring_data["performance_metrics"],
            "recent_health_history": recent_health[-20:],  # Last 20 checks
            "recommendations": self._generate_recommendations(),
        }

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n📊 Monitoring report saved: {report_file}")
        return report_file

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on monitoring data"""
        recommendations = []

        metrics = self.monitoring_data["performance_metrics"]

        # Performance recommendations
        if metrics["webhook_response_times"]:
            avg_time = sum(metrics["webhook_response_times"][-10:]) / len(
                metrics["webhook_response_times"][-10:]
            )
            if avg_time > 2:
                recommendations.append(
                    "Consider optimizing webhook processing for faster response times"
                )

        # Success rate recommendations
        if metrics["success_rate"] < 0.95:
            recommendations.append("Investigate causes of webhook processing failures")

        # Error count recommendations
        if metrics["error_count"] > 10:
            recommendations.append(
                "Review error logs and implement additional error handling"
            )

        # Health check recommendations
        if len(self.monitoring_data["health_history"]) > 0:
            recent_health = self.monitoring_data["health_history"][-5:]
            unhealthy_components = set()

            for health in recent_health:
                for component, status in health.items():
                    if component != "timestamp" and not status.get("healthy", False):
                        unhealthy_components.add(component)

            for component in unhealthy_components:
                recommendations.append(
                    f"Address {component} health issues for improved reliability"
                )

        if not recommendations:
            recommendations.append("System is performing well - continue monitoring")

        return recommendations


async def main():
    """Main monitoring execution"""
    monitor = GongIntegrationMonitor()

    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
    finally:
        # Save final report
        report_file = monitor.save_monitoring_report()
        print(f"\n📋 Final monitoring report saved to: {report_file}")
        print("\n🎯 Monitoring session complete")


if __name__ == "__main__":
    asyncio.run(main())
