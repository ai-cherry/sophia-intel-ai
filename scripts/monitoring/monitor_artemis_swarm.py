#!/usr/bin/env python3
"""
Artemis Swarm Monitor
Real-time monitoring and quality assurance for the Artemis Code Excellence system
"""
import asyncio
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment variable for Portkey API key
# Require PORTKEY_API_KEY to be present rather than hardcoding
if not os.environ.get("PORTKEY_API_KEY"):
    raise RuntimeError(
        "PORTKEY_API_KEY is required for monitor_artemis_swarm. Set it in your shell or ~/.config/artemis/env"
    )

from portkey_ai import Portkey


@dataclass
class ProviderMetrics:
    """Metrics for a single provider"""

    provider: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_latency_ms: int = 0
    errors: List[str] = field(default_factory=list)
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def average_latency_ms(self) -> int:
        if self.successful_requests == 0:
            return 0
        return self.total_latency_ms // self.successful_requests

    @property
    def health_status(self) -> str:
        if self.success_rate >= 95:
            return "🟢 Healthy"
        elif self.success_rate >= 80:
            return "🟡 Degraded"
        elif self.success_rate >= 50:
            return "🟠 Issues"
        else:
            return "🔴 Critical"


class ArtemisMonitor:
    """Monitor for Artemis Swarm health and performance"""

    VIRTUAL_KEYS = {
        "deepseek": "deepseek-vk-24102f",
        "openai": "openai-vk-190a60",
        "anthropic": "anthropic-vk-b42804",
        "groq": "groq-vk-6b9b52",
        "gemini": "gemini-vk-3d6108",
        "together": "together-ai-670469",
        "xai": "xai-vk-e65d0f",
        "mistral": "mistral-vk-f92861",
    }

    MODELS = {
        "deepseek": "deepseek-chat",
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-haiku-20240307",
        "groq": "llama-3.3-70b-versatile",
        "gemini": "gemini-1.5-flash",
        "together": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        "xai": "grok-beta",
        "mistral": "mistral-small-latest",
    }

    def __init__(self):
        """Initialize the monitor"""
        self.api_key = os.environ.get("PORTKEY_API_KEY")
        if not self.api_key:
            raise ValueError("PORTKEY_API_KEY not found")

        self.metrics: Dict[str, ProviderMetrics] = {
            provider: ProviderMetrics(provider=provider)
            for provider in self.VIRTUAL_KEYS.keys()
        }
        self.start_time = datetime.now()

    async def health_check(self, provider: str) -> Dict[str, Any]:
        """Perform health check on a provider"""
        metrics = self.metrics[provider]
        metrics.total_requests += 1

        try:
            client = Portkey(
                api_key=self.api_key, virtual_key=self.VIRTUAL_KEYS[provider]
            )

            model = self.MODELS.get(provider)
            if not model:
                raise ValueError(f"No model for {provider}")

            # Simple health check message
            messages = [
                {
                    "role": "system",
                    "content": "You are a health check bot. Respond with 'OK'.",
                },
                {"role": "user", "content": "Status check"},
            ]

            start = datetime.now()

            # Run sync call in executor
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        model=model, messages=messages, max_tokens=10, temperature=0
                    ),
                ),
                timeout=10.0,
            )

            latency_ms = int((datetime.now() - start).total_seconds() * 1000)

            # Update metrics
            metrics.successful_requests += 1
            metrics.total_latency_ms += latency_ms
            metrics.last_success = datetime.now()

            if hasattr(response, "usage") and response.usage:
                metrics.total_tokens += response.usage.total_tokens

            return {
                "provider": provider,
                "status": "healthy",
                "latency_ms": latency_ms,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            metrics.failed_requests += 1
            metrics.last_failure = datetime.now()
            metrics.errors.append(str(e)[:100])  # Store truncated error

            return {
                "provider": provider,
                "status": "unhealthy",
                "error": str(e)[:200],
                "timestamp": datetime.now().isoformat(),
            }

    async def monitor_all_providers(self) -> Dict[str, Any]:
        """Monitor all providers"""
        tasks = [self.health_check(provider) for provider in self.VIRTUAL_KEYS.keys()]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        health_results = []
        for provider, result in zip(self.VIRTUAL_KEYS.keys(), results):
            if isinstance(result, Exception):
                health_results.append(
                    {
                        "provider": provider,
                        "status": "error",
                        "error": str(result),
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            else:
                health_results.append(result)

        return {
            "timestamp": datetime.now().isoformat(),
            "uptime": str(datetime.now() - self.start_time),
            "health_checks": health_results,
            "summary": self._generate_summary(),
        }

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate monitoring summary"""
        healthy_providers = []
        degraded_providers = []
        critical_providers = []

        total_requests = 0
        total_tokens = 0

        for provider, metrics in self.metrics.items():
            total_requests += metrics.total_requests
            total_tokens += metrics.total_tokens

            if metrics.total_requests > 0:
                if metrics.success_rate >= 95:
                    healthy_providers.append(provider)
                elif metrics.success_rate >= 80:
                    degraded_providers.append(provider)
                else:
                    critical_providers.append(provider)

        return {
            "total_providers": len(self.metrics),
            "healthy": len(healthy_providers),
            "degraded": len(degraded_providers),
            "critical": len(critical_providers),
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "providers_status": {
                "healthy": healthy_providers,
                "degraded": degraded_providers,
                "critical": critical_providers,
            },
        }

    def get_detailed_report(self) -> Dict[str, Any]:
        """Get detailed monitoring report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "uptime": str(datetime.now() - self.start_time),
            "providers": {},
        }

        for provider, metrics in self.metrics.items():
            report["providers"][provider] = {
                "health_status": metrics.health_status,
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "success_rate": f"{metrics.success_rate:.1f}%",
                "average_latency_ms": metrics.average_latency_ms,
                "total_tokens": metrics.total_tokens,
                "last_success": (
                    metrics.last_success.isoformat() if metrics.last_success else None
                ),
                "last_failure": (
                    metrics.last_failure.isoformat() if metrics.last_failure else None
                ),
                "recent_errors": metrics.errors[-5:] if metrics.errors else [],
            }

        report["summary"] = self._generate_summary()

        return report

    def print_dashboard(self):
        """Print monitoring dashboard"""
        print("\n" + "=" * 80)
        print("🎯 ARTEMIS SWARM MONITORING DASHBOARD")
        print("=" * 80)

        uptime = datetime.now() - self.start_time
        print("\n📊 System Status")
        print(f"  Uptime: {uptime}")
        print(f"  Monitoring Since: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        summary = self._generate_summary()
        print("\n🏥 Health Overview")
        print(f"  Total Providers: {summary['total_providers']}")
        print(f"  🟢 Healthy: {summary['healthy']}")
        print(f"  🟡 Degraded: {summary['degraded']}")
        print(f"  🔴 Critical: {summary['critical']}")
        print(f"  Total Requests: {summary['total_requests']}")
        print(f"  Total Tokens: {summary['total_tokens']:,}")

        print("\n📈 Provider Status")
        print("-" * 80)
        print(
            f"{'Provider':<15} {'Status':<15} {'Success Rate':<15} {'Avg Latency':<15} {'Requests':<10}"
        )
        print("-" * 80)

        for provider, metrics in sorted(
            self.metrics.items(), key=lambda x: x[1].success_rate, reverse=True
        ):
            if metrics.total_requests > 0:
                print(
                    f"{provider:<15} "
                    f"{metrics.health_status:<15} "
                    f"{metrics.success_rate:>6.1f}%        "
                    f"{metrics.average_latency_ms:>8}ms      "
                    f"{metrics.total_requests:>10}"
                )

        # Show recent errors
        print("\n⚠️  Recent Issues")
        print("-" * 80)

        has_errors = False
        for provider, metrics in self.metrics.items():
            if metrics.errors and metrics.last_failure:
                time_since = datetime.now() - metrics.last_failure
                if time_since < timedelta(minutes=5):
                    has_errors = True
                    print(f"{provider}: {metrics.errors[-1][:60]}...")

        if not has_errors:
            print("  No recent issues (last 5 minutes)")

        print("\n" + "=" * 80)


async def continuous_monitoring(monitor: ArtemisMonitor, interval: int = 30):
    """Run continuous monitoring"""
    print("🚀 Starting continuous monitoring...")
    print(f"   Checking every {interval} seconds")
    print("   Press Ctrl+C to stop")

    iteration = 0
    while True:
        iteration += 1
        print(
            f"\n🔄 Monitoring Cycle #{iteration} - {datetime.now().strftime('%H:%M:%S')}"
        )

        # Run health checks
        await monitor.monitor_all_providers()

        # Display dashboard
        monitor.print_dashboard()

        # Save detailed report every 5 iterations
        if iteration % 5 == 0:
            report = monitor.get_detailed_report()
            filename = f"artemis_monitor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, "w") as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n💾 Detailed report saved to: {filename}")

        # Wait for next cycle
        await asyncio.sleep(interval)


async def main():
    """Main execution"""
    print("=" * 80)
    print("🎯 ARTEMIS SWARM MONITOR")
    print("=" * 80)

    monitor = ArtemisMonitor()

    # Run initial health check
    print("\n🏥 Running initial health check...")
    results = await monitor.monitor_all_providers()

    # Display initial results
    monitor.print_dashboard()

    # Save initial report
    initial_report = monitor.get_detailed_report()
    filename = (
        f"artemis_monitor_initial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(filename, "w") as f:
        json.dump(initial_report, f, indent=2, default=str)

    print(f"\n💾 Initial report saved to: {filename}")

    # Ask if user wants continuous monitoring
    print("\n" + "=" * 80)
    print("Options:")
    print("1. Run continuous monitoring (checks every 30 seconds)")
    print("2. Exit")

    try:
        choice = input("\nSelect option (1 or 2): ").strip()

        if choice == "1":
            await continuous_monitoring(monitor)
        else:
            print("\n✅ Monitoring complete!")
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoring stopped by user")

        # Save final report
        final_report = monitor.get_detailed_report()
        filename = (
            f"artemis_monitor_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(filename, "w") as f:
            json.dump(final_report, f, indent=2, default=str)

        print(f"💾 Final report saved to: {filename}")
        print("\n✅ Monitoring session complete!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
        sys.exit(0)
