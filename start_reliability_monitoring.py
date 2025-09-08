#!/usr/bin/env python3
"""
Sophia AI Reliability Monitor Startup Script
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def main():
    try:
        from mcp_servers.reliability.distributed_reliability_monitor import (
            get_reliability_monitor,
        )

        print("🎯 Starting Sophia AI Distributed Reliability Monitor...")

        # Initialize and start monitoring
        monitor = get_reliability_monitor()
        await monitor.start_monitoring()

        print("✅ Reliability monitoring system active")
        print(
            "📊 Monitor available at: http://104.171.202.103:8080/api/reliability/dashboard"
        )
        print("🔍 Logs available in: logs/reliability/")
        print("⏹️  Press Ctrl+C to stop monitoring")

        # Keep running
        try:
            while True:
                await asyncio.sleep(60)

                # Log periodic status
                report = monitor.get_comprehensive_report()
                if report["current_metrics"]:
                    score = report["current_metrics"]["overall_score"]
                    print(f"📈 Current Reliability Score: {score:.1f}%")

        except KeyboardInterrupt:
            print("\n⏹️  Stopping reliability monitoring...")
            await monitor.stop_monitoring()
            print("✅ Monitoring stopped gracefully")

    except Exception as e:
        print(f"❌ Failed to start reliability monitoring: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
