#!/usr/bin/env python3
import asyncio
import httpx
from datetime import datetime


async def monitor():
    """Monitor system health"""
    services = {
        "UI": "http://localhost:3000",
        "API": "http://localhost:8000/api/agents",
        "Telemetry": "http://localhost:5003/api/telemetry/health",
        "MCP Memory": "http://localhost:8081/health",
        "MCP Vector": "http://localhost:8085/health",
    }

    while True:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Health Check")
        print("-" * 40)

        for name, url in services.items():
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        print(f"✅ {name:<15} OK")
                    else:
                        print(f"⚠️  {name:<15} Status {resp.status_code}")
            except Exception:
                print(f"❌ {name:<15} DOWN")

        await asyncio.sleep(10)


if __name__ == "__main__":
    try:
        asyncio.run(monitor())
    except KeyboardInterrupt:
        print("\nMonitoring stopped")

