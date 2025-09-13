#!/usr/bin/env python3
"""
AlertManager Load Test
Verifies AlertManager can handle 500 alerts/second at peak load
"""
import argparse
import asyncio
import random
import sys
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List
import aiohttp
class AlertManagerLoadTest:
    def __init__(self, alertmanager_url: str, api_version: str = "v2"):
        self.base_url = f"{alertmanager_url}/api/{api_version}"
        self.alerts_url = f"{self.base_url}/alerts"
        self.headers = {"Content-Type": "application/json"}
        self.metrics = {
            "sent": 0,
            "successful": 0,
            "failed": 0,
            "latencies": [],
            "errors": [],
        }
    async def send_alert(
        self, session: aiohttp.ClientSession, alert_data: List[Dict]
    ) -> Dict:
        """Send alert batch to AlertManager"""
        start_time = time.time()
        try:
            async with session.post(
                self.alerts_url,
                json=alert_data,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                latency = time.time() - start_time
                self.metrics["latencies"].append(latency)
                if response.status == 200:
                    self.metrics["successful"] += len(alert_data)
                    return {"status": "success", "latency": latency}
                else:
                    self.metrics["failed"] += len(alert_data)
                    error_text = await response.text()
                    self.metrics["errors"].append(
                        {
                            "status": response.status,
                            "error": error_text,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                    return {
                        "status": "failed",
                        "code": response.status,
                        "latency": latency,
                    }
        except Exception as e:
            latency = time.time() - start_time
            self.metrics["failed"] += len(alert_data)
            self.metrics["errors"].append(
                {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
            )
            return {"status": "error", "error": str(e), "latency": latency}
    def create_test_alert(self, index: int) -> Dict[str, Any]:
        """Generate test alert with realistic data"""
        domains = ["", "sophia", "infrastructure"]
        severities = ["CRITICAL", "WARNING", "INFO"]
        namespaces = [
            "-system",
            "sophia-system",
            "monitoring",
            "default",
            "kube-system",
        ]
        services = [
            "api-gateway",
            "model-serving",
            "inference-pipeline",
            "data-processor",
            "cache",
        ]
        alert_type = index % 10
        domain = domains[index % 3]
        # Create different alert patterns
        if alert_type < 3:  # 30% Circuit breaker alerts
            alertname = "CircuitBreakerOpen"
            severity = "CRITICAL"
        elif alert_type < 6:  # 30% High latency
            alertname = "HighLatency"
            severity = "WARNING"
        elif alert_type < 8:  # 20% Error rate
            alertname = "HighErrorRate"
            severity = "WARNING"
        else:  # 20% Resource alerts
            alertname = random.choice(["HighCPU", "HighMemory", "DiskSpace"])
            severity = random.choice(severities)
        return {
            "labels": {
                "alertname": f"{alertname}_{index % 100}",
                "severity": severity,
                "domain": domain,
                "namespace": namespaces[index % 5],
                "service": f"{services[index % 5]}-{index % 20}",
                "instance": f"node-{index % 10}.cluster.local",
                "job": "monitoring",
                "test_id": str(uuid.uuid4()),
                "test_run": "load_test",
            },
            "annotations": {
                "description": f"Load test alert #{index}: {alertname} on {services[index % 5]}",
                "value": str(random.uniform(0, 100)),
                "test_timestamp": datetime.utcnow().isoformat(),
            },
            "startsAt": datetime.utcnow().isoformat() + "Z",
            "endsAt": (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z",
            "generatorURL": f"http://prometheus.monitoring:9090/graph?test={index}",
        }
    async def generate_load(
        self, alerts_per_second: int, duration_seconds: int, batch_size: int = 10
    ):
        """Generate specified load on AlertManager"""
        print(
            f"Starting load test: {alerts_per_second} alerts/sec for {duration_seconds} seconds"
        )
        print(f"Total alerts to send: {alerts_per_second * duration_seconds}")
        print(f"Batch size: {batch_size}")
        print("-" * 60)
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            alert_counter = 0
            while time.time() - start_time < duration_seconds:
                loop_start = time.time()
                tasks = []
                # Create batches of alerts
                for _ in range(alerts_per_second // batch_size):
                    batch = []
                    for _ in range(batch_size):
                        batch.append(self.create_test_alert(alert_counter))
                        alert_counter += 1
                    tasks.append(self.send_alert(session, batch))
                # Handle remainder
                remainder = alerts_per_second % batch_size
                if remainder > 0:
                    batch = []
                    for _ in range(remainder):
                        batch.append(self.create_test_alert(alert_counter))
                        alert_counter += 1
                    tasks.append(self.send_alert(session, batch))
                # Send all batches concurrently
                results = await asyncio.gather(*tasks)
                self.metrics["sent"] += alerts_per_second
                # Progress update
                elapsed = time.time() - start_time
                if int(elapsed) % 10 == 0 and int(elapsed) > 0:
                    success_rate = (
                        (self.metrics["successful"] / self.metrics["sent"] * 100)
                        if self.metrics["sent"] > 0
                        else 0
                    )
                    avg_latency = (
                        sum(self.metrics["latencies"]) / len(self.metrics["latencies"])
                        if self.metrics["latencies"]
                        else 0
                    )
                    print(
                        f"Progress: {int(elapsed)}s | Sent: {self.metrics['sent']} | Success: {success_rate:.1f}% | Avg Latency: {avg_latency:.3f}s"
                    )
                # Sleep to maintain rate
                loop_duration = time.time() - loop_start
                if loop_duration < 1.0:
                    await asyncio.sleep(1.0 - loop_duration)
        return self.metrics
    def print_results(self):
        """Print load test results"""
        print("\n" + "=" * 60)
        print("LOAD TEST RESULTS")
        print("=" * 60)
        print(f"Total Alerts Sent: {self.metrics['sent']}")
        print(f"Successful: {self.metrics['successful']}")
        print(f"Failed: {self.metrics['failed']}")
        if self.metrics["sent"] > 0:
            success_rate = (self.metrics["successful"] / self.metrics["sent"]) * 100
            print(f"Success Rate: {success_rate:.2f}%")
        if self.metrics["latencies"]:
            latencies = sorted(self.metrics["latencies"])
            p50 = latencies[len(latencies) // 2]
            p95 = latencies[int(len(latencies) * 0.95)]
            p99 = latencies[int(len(latencies) * 0.99)]
            print("\nLatency Statistics:")
            print(f"  Min: {min(latencies):.3f}s")
            print(f"  P50: {p50:.3f}s")
            print(f"  P95: {p95:.3f}s")
            print(f"  P99: {p99:.3f}s")
            print(f"  Max: {max(latencies):.3f}s")
            print(f"  Avg: {sum(latencies) / len(latencies):.3f}s")
        if self.metrics["errors"]:
            print("\nErrors (showing first 5):")
            for error in self.metrics["errors"][:5]:
                print(f"  - {error}")
        # Performance verdict
        print("\n" + "-" * 60)
        if (
            self.metrics["successful"] / self.metrics["sent"] >= 0.99
            and max(self.metrics["latencies"]) < 5
        ):
            print("✅ PASS: AlertManager handled the load successfully")
            return 0
        else:
            print("❌ FAIL: AlertManager struggled with the load")
            return 1
async def main():
    parser = argparse.ArgumentParser(description="AlertManager Load Test")
    parser.add_argument(
        "--url", default="http://alertmanager.monitoring:9093", help="AlertManager URL"
    )
    parser.add_argument(
        "--rate", type=int, default=100, help="Alerts per second (default: 100)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Test duration in seconds (default: 60)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for sending alerts (default: 10)",
    )
    parser.add_argument(
        "--scenario",
        choices=["normal", "peak", "burst", "sustained"],
        default="normal",
        help="Load test scenario",
    )
    args = parser.parse_args()
    # Adjust parameters based on scenario
    scenarios = {
        "normal": {"rate": 10, "duration": 300},
        "peak": {"rate": 100, "duration": 60},
        "burst": {"rate": 500, "duration": 10},
        "sustained": {"rate": 50, "duration": 600},
    }
    if args.scenario in scenarios:
        scenario_config = scenarios[args.scenario]
        rate = scenario_config["rate"]
        duration = scenario_config["duration"]
        print(
            f"Running {args.scenario} scenario: {rate} alerts/sec for {duration} seconds"
        )
    else:
        rate = args.rate
        duration = args.duration
    tester = AlertManagerLoadTest(args.url)
    try:
        await tester.generate_load(rate, duration, args.batch_size)
        return tester.print_results()
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        tester.print_results()
        return 1
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1
if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
