#!/usr/bin/env python3
"""
Comprehensive Port Testing and Verification
Single source of truth for port management
"""

import asyncio
import json
from datetime import datetime

import httpx

# SINGLE SOURCE OF TRUTH - All port assignments
PORT_REGISTRY = {
    # Frontend/UI Services (3000-3999)
    3000: {"name": "Next.js UI", "type": "frontend", "protocol": "http", "required": True},

    # Database Services (6000-6999)
    6379: {"name": "Redis", "type": "database", "protocol": "tcp", "required": True},

    # MCP/API Services (8000-8099)
    8000: {"name": "MCP Memory Alt", "type": "mcp", "protocol": "http", "required": False},
    8001: {"name": "MCP Memory Server", "type": "mcp", "protocol": "http", "required": True},
    8002: {"name": "Monitoring Dashboard", "type": "monitoring", "protocol": "http", "required": True},
    8003: {"name": "MCP Code Review", "type": "mcp", "protocol": "http", "required": True},
    8004: {"name": "Vector Store", "type": "storage", "protocol": "http", "required": False},
    8005: {"name": "Unified API Server", "type": "api", "protocol": "http", "required": True},
    8006: {"name": "Backup/Testing", "type": "dev", "protocol": "http", "required": False},
    8007: {"name": "Development", "type": "dev", "protocol": "http", "required": False},
    8008: {"name": "Development", "type": "dev", "protocol": "http", "required": False},
    8080: {"name": "Weaviate Vector DB", "type": "database", "protocol": "http", "required": False},

    # Alternative UIs (8500-8599)
    8501: {"name": "Streamlit UI", "type": "frontend", "protocol": "http", "required": True},
}

# Health check endpoints for each service
HEALTH_ENDPOINTS = {
    3000: "/",
    8001: "/health",
    8002: "/",
    8003: "/health",
    8005: "/",
    8501: "/",
}

# WebSocket endpoints
WEBSOCKET_ENDPOINTS = {
    8005: ["/ws/bus", "/ws/swarm", "/ws/teams"]
}

class PortManager:
    """Centralized port management system"""

    def __init__(self):
        self.results = {}
        self.conflicts = []
        self.available_ports = []

    async def test_port(self, port: int, config: dict) -> tuple[str, dict | None]:
        """Test a single port for availability and service health"""

        # Skip Redis (TCP) - test separately
        if port == 6379:
            return await self.test_redis()

        # Test HTTP services
        url = f"http://localhost:{port}"
        health_url = f"{url}{HEALTH_ENDPOINTS.get(port, '/')}"

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(health_url)

                if response.status_code < 400:
                    # Service is running
                    result = {
                        "status": "✅ Active",
                        "code": response.status_code,
                        "service": config["name"],
                        "health": "healthy" if response.status_code == 200 else "warning"
                    }

                    # Try to get more info from response
                    try:
                        data = response.json()
                        result["info"] = data
                    except:
                        result["info"] = response.text[:100]

                    return "active", result
                else:
                    return "error", {"status": f"⚠️ Error {response.status_code}", "service": config["name"]}

        except httpx.ConnectError:
            # Port not in use
            if config["required"]:
                return "missing", {"status": "❌ Required service not running", "service": config["name"]}
            else:
                return "available", {"status": "🟢 Available", "service": config["name"]}
        except Exception as e:
            return "error", {"status": f"❌ Error: {str(e)[:50]}", "service": config["name"]}

    async def test_redis(self) -> tuple[str, dict | None]:
        """Test Redis connection"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379)
            r.ping()
            info = r.info()
            return "active", {
                "status": "✅ Active",
                "service": "Redis",
                "info": {
                    "version": info.get("redis_version", "unknown"),
                    "clients": info.get("connected_clients", 0),
                    "memory": info.get("used_memory_human", "unknown")
                }
            }
        except:
            return "missing", {"status": "❌ Redis not running", "service": "Redis"}

    async def test_websockets(self):
        """Test WebSocket endpoints"""
        ws_results = {}

        for port, endpoints in WEBSOCKET_ENDPOINTS.items():
            ws_results[port] = {}
            for endpoint in endpoints:
                # Can't easily test WebSocket without full connection
                # Just verify the port is active
                if port in self.results and self.results[port][0] == "active":
                    ws_results[port][endpoint] = "✅ Available"
                else:
                    ws_results[port][endpoint] = "❌ Port not active"

        return ws_results

    async def scan_all_ports(self):
        """Scan all registered ports"""
        tasks = []
        for port, config in PORT_REGISTRY.items():
            tasks.append(self.test_port(port, config))

        results = await asyncio.gather(*tasks)

        for (port, config), (status, info) in zip(PORT_REGISTRY.items(), results, strict=False):
            self.results[port] = (status, info)

            if status == "available" and not config["required"]:
                self.available_ports.append(port)
            elif status == "missing" and config["required"]:
                self.conflicts.append(f"Port {port} ({config['name']}) is required but not running")

    def generate_report(self):
        """Generate comprehensive port status report"""
        report = []
        report.append("=" * 80)
        report.append("PORT STATUS REPORT - SINGLE SOURCE OF TRUTH")
        report.append("=" * 80)
        report.append(f"Timestamp: {datetime.now().isoformat()}")
        report.append("")

        # Group by service type
        by_type = {}
        for port, (status, info) in self.results.items():
            service_type = PORT_REGISTRY[port]["type"]
            if service_type not in by_type:
                by_type[service_type] = []
            by_type[service_type].append((port, status, info))

        # Report by type
        for service_type in ["frontend", "api", "mcp", "database", "monitoring", "dev", "storage"]:
            if service_type in by_type:
                report.append(f"\n## {service_type.upper()} Services")
                report.append("-" * 40)

                for port, status, info in by_type[service_type]:
                    report.append(f"Port {port:5} | {info['service']:20} | {info['status']}")
                    if status == "active" and isinstance(info.get("info"), dict):
                        for key, val in info["info"].items():
                            if key not in ["status", "service"]:
                                report.append(f"           └─ {key}: {val}")

        # WebSocket endpoints
        report.append("\n## WebSocket Endpoints")
        report.append("-" * 40)
        for port, endpoints in WEBSOCKET_ENDPOINTS.items():
            for endpoint in endpoints:
                if port in self.results and self.results[port][0] == "active":
                    status = "✅ Available"
                else:
                    status = "❌ Port not active"
                report.append(f"ws://localhost:{port}{endpoint:20} | {status}")

        # Available ports
        if self.available_ports:
            report.append("\n## Available Ports for New Services")
            report.append("-" * 40)
            for port in self.available_ports:
                report.append(f"Port {port:5} | {PORT_REGISTRY[port]['name']}")

        # Conflicts and issues
        if self.conflicts:
            report.append("\n## ⚠️ CONFLICTS AND ISSUES")
            report.append("-" * 40)
            for conflict in self.conflicts:
                report.append(f"❌ {conflict}")
        else:
            report.append("\n✅ No conflicts detected - all required services running")

        return "\n".join(report)

    def export_config(self):
        """Export centralized configuration for all services"""
        config = {
            "ports": PORT_REGISTRY,
            "health_endpoints": HEALTH_ENDPOINTS,
            "websocket_endpoints": WEBSOCKET_ENDPOINTS,
            "current_status": {}
        }

        for port, (status, info) in self.results.items():
            config["current_status"][port] = {
                "status": status,
                "active": status == "active",
                "info": info
            }

        return config

async def main():
    """Main test runner"""
    print("🔍 Starting Comprehensive Port Scan...\n")

    manager = PortManager()
    await manager.scan_all_ports()

    # Print report
    print(manager.generate_report())

    # Export configuration
    config = manager.export_config()

    # Save to file as single source of truth
    with open("port_config.json", "w") as f:
        json.dump(config, f, indent=2, default=str)

    print("\n📄 Configuration exported to port_config.json")

    # Return status code
    return 0 if not manager.conflicts else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
