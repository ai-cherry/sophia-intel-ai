#!/usr/bin/env python3
"""
Centralized MCP Startup System - Phase 2
Enhanced startup with Central Registry integration
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_bridge.central_registry_integration import initialize_bridge_integration

# Import central registry components
from app.mcp.central_registry import (
    ConnectionType,
    MCPServerRegistration,
    ServerStatus,
    get_central_registry,
)
from app.mcp.optimized_mcp_orchestrator import MCPCapabilityType, MCPDomain

# Import original master controller for server management
from scripts.mcp_master_startup import MCPMasterController


class CentralizedMCPController(MCPMasterController):
    """
    Enhanced MCP controller with Central Registry integration
    Extends the original controller with centralized management
    """

    def __init__(self):
        super().__init__()
        self.central_registry = None
        self.registered_servers = {}

    async def initialize_central_registry(self) -> bool:
        """Initialize the central registry"""
        try:
            self.log("🔧 Initializing Central MCP Registry...")
            self.central_registry = await get_central_registry()

            self.log("✅ Central Registry initialized successfully")
            return True

        except Exception as e:
            self.log(f"❌ Failed to initialize Central Registry: {e}", "ERROR")
            return False

    async def register_servers_with_central_registry(self, server_results: Dict[str, bool]):
        """Register all running servers with the central registry"""
        if not self.central_registry:
            self.log("❌ Central Registry not available for server registration", "ERROR")
            return

        self.log("\n📝 Registering servers with Central Registry...")

        for server_id, is_running in server_results.items():
            if not is_running:
                continue

            try:
                config = self.mcp_configs[server_id]

                # Map server to domain and capabilities
                domain, capabilities = self._map_server_to_registry_config(server_id, config)

                # Create registration
                registration = MCPServerRegistration(
                    server_id=f"master_{server_id}",
                    name=config["name"],
                    domain=domain,
                    capabilities=capabilities,
                    endpoint=f"http://localhost:{config.get('port', 8000)}",
                    connection_type=ConnectionType.HTTP,
                    priority=1,
                    max_connections=config.get("max_connections", 20),
                    timeout_seconds=30,
                    description=f"Master-started {config['name']}",
                    tags={"master_started", "centralized", server_id},
                )

                # Register with central registry
                success = await self.central_registry.register_server(registration)

                if success:
                    self.registered_servers[registration.server_id] = registration
                    self.log(f"  ✅ Registered {config['name']} with Central Registry")

                    # Update status to healthy
                    await self.central_registry.update_server_status(
                        registration.server_id, ServerStatus.HEALTHY
                    )
                else:
                    self.log(f"  ❌ Failed to register {config['name']}", "ERROR")

            except Exception as e:
                self.log(f"  ❌ Registration error for {server_id}: {e}", "ERROR")

    def _map_server_to_registry_config(self, server_id: str, config: Dict) -> tuple:
        """Map server configuration to registry domain and capabilities"""

        # Domain mapping
        if server_id in ["filesystem", "git", "embeddings"]:
            domain = MCPDomain.ARTEMIS
        elif server_id in ["memory", "unified_api"]:
            domain = MCPDomain.SOPHIA
        else:
            domain = MCPDomain.SHARED

        # Capability mapping
        capability_mapping = {
            "filesystem": [MCPCapabilityType.FILESYSTEM],
            "git": [MCPCapabilityType.GIT],
            "memory": [MCPCapabilityType.MEMORY],
            "embeddings": [MCPCapabilityType.EMBEDDINGS],
            "unified_api": [MCPCapabilityType.BUSINESS_ANALYTICS, MCPCapabilityType.CODE_ANALYSIS],
            "websocket": [MCPCapabilityType.WEB_SEARCH],  # Using as general communication
            "redis": [MCPCapabilityType.DATABASE],
        }

        capabilities = capability_mapping.get(server_id, [MCPCapabilityType.DATABASE])

        return domain, capabilities

    async def initialize_bridge_integration(self) -> bool:
        """Initialize MCP bridge integration"""
        try:
            self.log("🌉 Initializing MCP Bridge integration...")

            success = await initialize_bridge_integration()

            if success:
                self.log("✅ Bridge integration initialized successfully")
                return True
            else:
                self.log("❌ Bridge integration failed", "ERROR")
                return False

        except Exception as e:
            self.log(f"❌ Bridge integration error: {e}", "ERROR")
            return False

    async def perform_health_monitoring(self):
        """Perform ongoing health monitoring with registry updates"""
        if not self.central_registry:
            return

        self.log("\n🔍 Starting health monitoring with Central Registry integration...")

        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                for server_id, registration in self.registered_servers.items():
                    original_id = server_id.replace("master_", "")

                    if original_id in self.mcp_configs:
                        config = self.mcp_configs[original_id]

                        # Perform health check
                        is_healthy = await self.check_server_health(original_id, config)

                        # Update registry status
                        status = ServerStatus.HEALTHY if is_healthy else ServerStatus.UNHEALTHY
                        await self.central_registry.update_server_status(server_id, status)

                        if not is_healthy:
                            self.log(f"⚠️ Health check failed for {config['name']}", "WARNING")

            except Exception as e:
                self.log(f"Health monitoring error: {e}", "ERROR")
                await asyncio.sleep(30)  # Shorter wait on error

    async def generate_enhanced_status_report(self, results: Dict[str, bool]):
        """Generate enhanced status report with central registry information"""
        # Call original status report
        self.generate_status_report(results)

        # Add central registry information
        if self.central_registry:
            self.log("\n" + "=" * 70)
            self.log("📊 CENTRAL REGISTRY STATUS")
            self.log("=" * 70)

            try:
                registry_status = await self.central_registry.get_registry_status()

                self.log(f"Total registered servers: {registry_status['total_servers']}")
                self.log(
                    f"Registry health: {'✅ Healthy' if registry_status['redis_connected'] else '❌ Unhealthy'}"
                )

                # Show domain distribution
                domain_dist = registry_status.get("domain_distribution", {})
                self.log("\nServers by domain:")
                for domain, count in domain_dist.items():
                    self.log(f"  • {domain}: {count} servers")

                # Show capability distribution
                capability_dist = registry_status.get("capability_distribution", {})
                self.log("\nCapabilities available:")
                active_capabilities = [cap for cap, count in capability_dist.items() if count > 0]
                for cap in active_capabilities[:5]:  # Show first 5
                    self.log(f"  • {cap}")
                if len(active_capabilities) > 5:
                    self.log(f"  • ... and {len(active_capabilities) - 5} more")

            except Exception as e:
                self.log(f"Failed to get registry status: {e}", "ERROR")

        # Add API endpoints information
        self.log("\n" + "=" * 70)
        self.log("🔌 CENTRALIZED API ENDPOINTS")
        self.log("=" * 70)

        self.log("\n📡 Central Registry API:")
        self.log("  • Registry Status: GET http://localhost:8000/api/mcp/registry/status")
        self.log("  • Discover Servers: GET http://localhost:8000/api/mcp/registry/servers")
        self.log(
            "  • Server Details: GET http://localhost:8000/api/mcp/registry/servers/{server_id}"
        )
        self.log(
            "  • Load Balancing: GET http://localhost:8000/api/mcp/registry/load-balance/{domain}/{capability}"
        )

        self.log("\n🌉 Bridge Integration:")
        self.log("  • Bridge Status: GET http://localhost:8000/api/mcp/bridge/status")

        self.log("\n📊 Enhanced Monitoring:")
        self.log("  • MCP Status: GET http://localhost:8000/api/mcp/status")
        self.log("  • Cache Stats: GET http://localhost:8000/api/cache/stats")
        self.log("  • WebSocket Stats: GET http://localhost:8000/api/websocket/stats")

    async def run_centralized(self):
        """Main execution with centralized features"""
        try:
            # Initialize central registry first
            registry_success = await self.initialize_central_registry()
            if not registry_success:
                self.log("⚠️ Continuing without Central Registry", "WARNING")

            # Start all servers (from parent class)
            results = await self.start_all_servers()

            # Register servers with central registry if available
            if self.central_registry:
                await self.register_servers_with_central_registry(results)

            # Initialize bridge integration
            if registry_success:
                bridge_success = await self.initialize_bridge_integration()
                if not bridge_success:
                    self.log("⚠️ Bridge integration failed, continuing without it", "WARNING")

            # Create configurations (from parent class)
            self.create_claude_config()
            self.create_cursor_config()

            # Generate enhanced status report
            await self.generate_enhanced_status_report(results)

            # Start health monitoring
            if any(results.values()):
                self.log("\n" + "=" * 70)
                self.log("✅ CENTRALIZED MCP SYSTEM RUNNING")
                self.log("Press Ctrl+C to stop all servers")
                self.log("=" * 70)

                # Start health monitoring in background
                monitor_task = asyncio.create_task(self.perform_health_monitoring())

                # Keep servers running
                try:
                    await monitor_task
                except KeyboardInterrupt:
                    monitor_task.cancel()
                    raise

        except KeyboardInterrupt:
            self.log("\n🛑 Shutting down centralized MCP system...")
            await self.shutdown_centralized()

    async def shutdown_centralized(self):
        """Enhanced shutdown with central registry cleanup"""
        try:
            # Unregister servers from central registry
            if self.central_registry and self.registered_servers:
                self.log("📝 Unregistering servers from Central Registry...")

                for server_id in list(self.registered_servers.keys()):
                    try:
                        await self.central_registry.unregister_server(server_id)
                        self.log(f"  ✅ Unregistered {server_id}")
                    except Exception as e:
                        self.log(f"  ❌ Failed to unregister {server_id}: {e}", "ERROR")

            # Shutdown central registry
            if self.central_registry:
                await self.central_registry.shutdown()
                self.log("✅ Central Registry shut down")

        except Exception as e:
            self.log(f"Error during centralized shutdown: {e}", "ERROR")

        # Call parent shutdown
        self.shutdown()


async def main():
    """Main entry point for centralized MCP startup"""
    print("🚀 CENTRALIZED MCP STARTUP SYSTEM")
    print("=" * 50)
    print("Phase 2: Central Registry Integration")
    print("=" * 50)

    controller = CentralizedMCPController()
    await controller.run_centralized()


if __name__ == "__main__":
    asyncio.run(main())
