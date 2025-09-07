#!/usr/bin/env python3
"""
MCP Bridge - Central Registry Integration
Integrates the MCP bridge with the new central registry system
"""

import asyncio
import json
import logging

# Import central registry components
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.mcp.central_registry import (
    CentralMCPRegistry,
    ConnectionType,
    MCPServerRegistration,
    ServerStatus,
    get_central_registry,
)
from app.mcp.optimized_mcp_orchestrator import MCPCapabilityType, MCPDomain

logger = logging.getLogger(__name__)


class BridgeRegistrationManager:
    """
    Manages registration of bridge servers with the central registry
    Reads bridge configuration and automatically registers servers
    """

    def __init__(self, config_path: str = "config/connections.json"):
        self.config_path = Path(__file__).parent / config_path
        self.registry: Optional[CentralMCPRegistry] = None
        self.registered_servers: Dict[str, MCPServerRegistration] = {}

    async def initialize(self) -> bool:
        """Initialize bridge registration manager"""
        try:
            # Get central registry instance
            self.registry = await get_central_registry()

            # Load and register bridge servers
            await self._load_and_register_bridge_servers()

            logger.info(
                f"✅ Bridge registration manager initialized with {len(self.registered_servers)} servers"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize bridge registration manager: {e}")
            return False

    async def _load_and_register_bridge_servers(self):
        """Load bridge configuration and register servers"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Bridge configuration not found: {self.config_path}")
                return

            with open(self.config_path) as f:
                config = json.load(f)

            # Process each IDE connection
            for ide_name, ide_config in config.get("ide_connections", {}).items():
                if not ide_config.get("enabled", True):
                    continue

                await self._register_ide_servers(ide_name, ide_config)

        except Exception as e:
            logger.error(f"Failed to load bridge configuration: {e}")

    async def _register_ide_servers(self, ide_name: str, ide_config: Dict[str, Any]):
        """Register servers for a specific IDE"""
        try:
            # Handle Claude Desktop MCP servers
            if ide_name == "claude_desktop":
                await self._register_claude_desktop_servers(ide_config)

            # Handle Roo/Cursor servers
            elif ide_name == "roo_cursor":
                await self._register_roo_cursor_servers(ide_config)

            # Handle Cline servers
            elif ide_name == "cline":
                await self._register_cline_servers(ide_config)

        except Exception as e:
            logger.error(f"Failed to register servers for {ide_name}: {e}")

    async def _register_claude_desktop_servers(self, ide_config: Dict[str, Any]):
        """Register Claude Desktop MCP servers"""
        mcp_servers = ide_config.get("mcp_servers", {})

        for server_id, server_config in mcp_servers.items():
            try:
                # Map capabilities to MCPCapabilityType
                capabilities = []
                for cap_name in server_config.get("capabilities", []):
                    if cap_name == "code_completion" or cap_name == "code_review":
                        capabilities.append(MCPCapabilityType.CODE_ANALYSIS)
                    elif cap_name == "business_analysis":
                        capabilities.append(MCPCapabilityType.BUSINESS_ANALYTICS)
                    elif cap_name == "knowledge_retrieval":
                        capabilities.append(MCPCapabilityType.EMBEDDINGS)

                # Determine domain from server ID
                if "artemis" in server_id:
                    domain = MCPDomain.ARTEMIS
                elif "sophia" in server_id:
                    domain = MCPDomain.SOPHIA
                else:
                    domain = MCPDomain.SHARED

                # Create registration
                registration = MCPServerRegistration(
                    server_id=f"bridge_{server_id}",
                    name=server_id.replace("_", " ").title(),
                    domain=domain,
                    capabilities=capabilities,
                    endpoint=f"stdio://{server_config.get('command', 'python')}",
                    connection_type=ConnectionType.STDIO,
                    priority=1 if server_config.get("priority") == "high" else 5,
                    max_connections=server_config.get("connection_config", {}).get(
                        "max_connections", 5
                    ),
                    timeout_seconds=server_config.get("connection_config", {}).get("timeout", 60),
                    description=f"Claude Desktop bridge server for {server_id}",
                    tags={"bridge", "claude_desktop", ide_config.get("priority", "medium")},
                )

                # Register with central registry
                success = await self.registry.register_server(registration)
                if success:
                    self.registered_servers[registration.server_id] = registration
                    logger.info(f"✅ Registered Claude Desktop server: {registration.server_id}")

            except Exception as e:
                logger.error(f"Failed to register Claude Desktop server {server_id}: {e}")

    async def _register_roo_cursor_servers(self, ide_config: Dict[str, Any]):
        """Register Roo/Cursor MCP servers"""
        mcp_servers = ide_config.get("mcp_servers", [])

        for server_config in mcp_servers:
            try:
                server_name = server_config.get("name", "unknown")

                # Map capabilities
                capabilities = []
                for cap_name in server_config.get("capabilities", []):
                    if cap_name in ["code", "refactor", "analyze", "test", "debug"]:
                        capabilities.append(MCPCapabilityType.CODE_ANALYSIS)
                    elif cap_name in ["file_read", "file_write", "directory_operations"]:
                        capabilities.append(MCPCapabilityType.FILESYSTEM)
                    elif cap_name in ["search", "retrieve"]:
                        capabilities.append(MCPCapabilityType.EMBEDDINGS)

                # Determine domain
                domain_str = server_config.get("domain", "shared")
                domain = MCPDomain(domain_str)

                # Create registration
                registration = MCPServerRegistration(
                    server_id=f"bridge_{server_name.replace('-', '_')}",
                    name=server_name.replace("-", " ").title(),
                    domain=domain,
                    capabilities=capabilities,
                    endpoint=server_config.get("endpoint", "ws://localhost:8000/mcp"),
                    connection_type=ConnectionType.WEBSOCKET,
                    priority=server_config.get("priority", 5),
                    max_connections=server_config.get("connection_config", {}).get(
                        "max_connections", 10
                    ),
                    timeout_seconds=server_config.get("connection_config", {}).get(
                        "connection_timeout", 30
                    ),
                    description=f"Roo/Cursor bridge server for {server_name}",
                    tags={"bridge", "roo_cursor", "websocket"},
                )

                # Register with central registry
                success = await self.registry.register_server(registration)
                if success:
                    self.registered_servers[registration.server_id] = registration
                    logger.info(f"✅ Registered Roo/Cursor server: {registration.server_id}")

            except Exception as e:
                logger.error(
                    f"Failed to register Roo/Cursor server {server_config.get('name', 'unknown')}: {e}"
                )

    async def _register_cline_servers(self, ide_config: Dict[str, Any]):
        """Register Cline MCP servers"""
        mcp_servers = ide_config.get("mcp_servers", [])

        for server_config in mcp_servers:
            try:
                server_name = server_config.get("name", "unknown")

                # Map capabilities
                capabilities = []
                for cap_name in server_config.get("capabilities", []):
                    if "analysis" in cap_name or "intelligence" in cap_name:
                        capabilities.append(MCPCapabilityType.CODE_ANALYSIS)
                    elif "tagging" in cap_name or "classification" in cap_name:
                        capabilities.append(MCPCapabilityType.EMBEDDINGS)
                    elif "design" in cap_name:
                        capabilities.append(MCPCapabilityType.CODE_ANALYSIS)

                # Determine domain
                domain_str = server_config.get("domain", "artemis")
                domain = MCPDomain(domain_str)

                # Create registration
                registration = MCPServerRegistration(
                    server_id=f"bridge_{server_name.replace('-', '_')}",
                    name=server_name.replace("-", " ").title(),
                    domain=domain,
                    capabilities=capabilities,
                    endpoint=server_config.get("endpoint", "ws://localhost:8000/mcp"),
                    connection_type=ConnectionType.WEBSOCKET,
                    priority=server_config.get("priority", 10),
                    max_connections=server_config.get("connection_config", {}).get(
                        "max_connections", 5
                    ),
                    timeout_seconds=server_config.get("connection_config", {}).get(
                        "connection_timeout", 30
                    ),
                    description=f"Cline bridge server for {server_name}",
                    tags={"bridge", "cline", "intelligence"},
                )

                # Register with central registry
                success = await self.registry.register_server(registration)
                if success:
                    self.registered_servers[registration.server_id] = registration
                    logger.info(f"✅ Registered Cline server: {registration.server_id}")

            except Exception as e:
                logger.error(
                    f"Failed to register Cline server {server_config.get('name', 'unknown')}: {e}"
                )

    async def update_server_status(self, server_id: str, status: ServerStatus):
        """Update status of a bridge server"""
        if self.registry and server_id in self.registered_servers:
            await self.registry.update_server_status(server_id, status)

    async def get_bridge_status(self) -> Dict[str, Any]:
        """Get status of all bridge servers"""
        if not self.registry:
            return {"error": "Registry not initialized"}

        bridge_servers = []
        for server_id, registration in self.registered_servers.items():
            server_details = await self.registry.get_server_details(server_id)
            if server_details:
                bridge_servers.append(server_details)

        return {
            "timestamp": datetime.now().isoformat(),
            "total_bridge_servers": len(self.registered_servers),
            "bridge_servers": bridge_servers,
            "registry_connected": self.registry is not None,
        }

    async def shutdown(self):
        """Shutdown and cleanup bridge servers"""
        try:
            # Unregister all bridge servers
            for server_id in list(self.registered_servers.keys()):
                if self.registry:
                    await self.registry.unregister_server(server_id)
                del self.registered_servers[server_id]

            logger.info("🔌 Bridge registration manager shut down gracefully")

        except Exception as e:
            logger.error(f"Error during bridge shutdown: {e}")


class BridgeHealthMonitor:
    """
    Monitors health of bridge connections and updates central registry
    """

    def __init__(self, registration_manager: BridgeRegistrationManager):
        self.registration_manager = registration_manager
        self.monitoring_enabled = True
        self.health_check_interval = 30  # seconds

    async def start_monitoring(self):
        """Start health monitoring for bridge servers"""
        logger.info("🔍 Starting bridge health monitoring")
        asyncio.create_task(self._health_monitoring_loop())

    async def _health_monitoring_loop(self):
        """Main health monitoring loop"""
        while self.monitoring_enabled:
            try:
                await asyncio.sleep(self.health_check_interval)

                # Check health of all registered bridge servers
                for server_id, registration in self.registration_manager.registered_servers.items():
                    try:
                        is_healthy = await self._check_server_health(server_id, registration)
                        status = ServerStatus.HEALTHY if is_healthy else ServerStatus.DEGRADED

                        await self.registration_manager.update_server_status(server_id, status)

                    except Exception as e:
                        logger.error(f"Health check failed for {server_id}: {e}")
                        await self.registration_manager.update_server_status(
                            server_id, ServerStatus.UNHEALTHY
                        )

            except Exception as e:
                logger.error(f"Health monitoring loop error: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _check_server_health(
        self, server_id: str, registration: MCPServerRegistration
    ) -> bool:
        """Check health of a specific bridge server"""
        try:
            # For bridge servers, we'll do basic connectivity checks
            # In a full implementation, this would test actual connections

            if registration.connection_type == ConnectionType.WEBSOCKET:
                # For WebSocket servers, we could test connection
                # For now, just return True as a placeholder
                return True

            elif registration.connection_type == ConnectionType.STDIO:
                # For STDIO servers, we could test command availability
                # For now, just return True as a placeholder
                return True

            else:
                return True

        except Exception as e:
            logger.error(f"Health check error for {server_id}: {e}")
            return False

    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_enabled = False
        logger.info("🛑 Bridge health monitoring stopped")


# Global instances
_bridge_manager: Optional[BridgeRegistrationManager] = None
_health_monitor: Optional[BridgeHealthMonitor] = None


async def initialize_bridge_integration() -> bool:
    """Initialize MCP bridge integration with central registry"""
    global _bridge_manager, _health_monitor

    try:
        # Initialize bridge registration manager
        _bridge_manager = BridgeRegistrationManager()
        success = await _bridge_manager.initialize()

        if not success:
            return False

        # Initialize health monitor
        _health_monitor = BridgeHealthMonitor(_bridge_manager)
        await _health_monitor.start_monitoring()

        logger.info("✅ MCP Bridge integration with Central Registry initialized")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to initialize bridge integration: {e}")
        return False


async def get_bridge_manager() -> Optional[BridgeRegistrationManager]:
    """Get bridge registration manager"""
    return _bridge_manager


async def get_health_monitor() -> Optional[BridgeHealthMonitor]:
    """Get bridge health monitor"""
    return _health_monitor


async def shutdown_bridge_integration():
    """Shutdown bridge integration"""
    global _bridge_manager, _health_monitor

    try:
        if _health_monitor:
            _health_monitor.stop_monitoring()
            _health_monitor = None

        if _bridge_manager:
            await _bridge_manager.shutdown()
            _bridge_manager = None

        logger.info("🔌 MCP Bridge integration shut down gracefully")

    except Exception as e:
        logger.error(f"Error during bridge integration shutdown: {e}")


if __name__ == "__main__":

    async def main():
        logging.basicConfig(level=logging.INFO)

        # Initialize bridge integration
        success = await initialize_bridge_integration()

        if success:
            print("Bridge integration initialized successfully")

            # Keep running for demonstration
            try:
                await asyncio.sleep(60)
            except KeyboardInterrupt:
                pass

            await shutdown_bridge_integration()
        else:
            print("Failed to initialize bridge integration")

    asyncio.run(main())
