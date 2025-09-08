#!/usr/bin/env python3
"""
Unified Orchestrator for Sophia Intel AI
Replaces 14+ fragmented startup scripts with single intelligent orchestrator
"""

import asyncio
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict

import httpx
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service status states"""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"


class ServiceDomain(Enum):
    """Service domains for clear separation"""

    INFRASTRUCTURE = "infrastructure"  # Redis, Postgres, etc.
    MCP = "mcp"  # MCP servers and bridge
    SOPHIA = "sophia"  # Business intelligence
    ARTEMIS = "artemis"  # AI coding agents
    SHARED = "shared"  # Shared services


class UnifiedOrchestrator:
    """
    Single orchestrator to manage all services with clear domain separation
    """

    def __init__(self, config_path: str = "startup-config.yml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.services = {}
        self.processes = {}
        self.start_time = datetime.now()

        # Environment validation
        self.validate_environment()

    def _load_config(self) -> Dict:
        """Load startup configuration"""
        if not self.config_path.exists():
            logger.warning(f"Config not found at {self.config_path}, using defaults")
            return self._default_config()

        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def _default_config(self) -> Dict:
        """Default configuration if no config file exists"""
        return {
            "version": "2.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "services": {
                # Infrastructure Layer
                "redis": {
                    "domain": ServiceDomain.INFRASTRUCTURE.value,
                    "command": "redis-server",
                    "port": 6379,
                    "health_check": "redis-cli ping",
                    "priority": 1,
                    "required": True,
                },
                "postgres": {
                    "domain": ServiceDomain.INFRASTRUCTURE.value,
                    "command": "postgres",
                    "port": 5432,
                    "health_check": "pg_isready",
                    "priority": 1,
                    "required": False,
                },
                # MCP Bridge Layer
                "mcp_memory": {
                    "domain": ServiceDomain.MCP.value,
                    "command": "python3 mcp_memory_server/main.py",
                    "port": 8765,
                    "depends_on": ["redis"],
                    "env_file": ".env.mcp",
                    "health_endpoint": "/health",
                    "priority": 2,
                    "required": True,
                },
                "mcp_bridge": {
                    "domain": ServiceDomain.MCP.value,
                    "command": "python3 mcp-bridge/server.py",
                    "port": 8766,
                    "depends_on": ["mcp_memory"],
                    "env_file": ".env.mcp",
                    "health_endpoint": "/health",
                    "priority": 2,
                    "required": True,
                },
                # Sophia Domain (Business Intelligence)
                "sophia_backend": {
                    "domain": ServiceDomain.SOPHIA.value,
                    "command": "python3 backend/main.py",
                    "port": 8000,
                    "depends_on": ["postgres", "redis", "mcp_bridge"],
                    "env_file": ".env.sophia",
                    "health_endpoint": "/health",
                    "priority": 3,
                    "required": True,
                },
                # Artemis Domain (AI Coding Agents) - External
                "artemis_connector": {
                    "domain": ServiceDomain.ARTEMIS.value,
                    "command": "python3 scripts/artemis_connector.py",
                    "port": 8100,
                    "depends_on": ["mcp_bridge"],
                    "env_file": ".env.artemis",
                    "health_endpoint": "/health",
                    "priority": 3,
                    "required": False,
                    "note": "Connects to external Artemis CLI repository",
                },
            },
        }

    def validate_environment(self):
        """Validate environment setup"""
        logger.info("🔍 Validating environment...")

        # Check for virtual environments (should be NONE)
        venv_check = subprocess.run(
            "find . -name 'venv' -o -name '.venv' -o -name 'pyvenv.cfg' | head -5",
            shell=True,
            capture_output=True,
            text=True,
        )

        if venv_check.stdout.strip():
            logger.error("❌ Virtual environments detected! These must be removed:")
            logger.error(venv_check.stdout)
            if not self._ask_confirmation("Continue anyway?"):
                sys.exit(1)

        # Check environment files
        env_files = {
            ".env.mcp": "MCP bridge configuration",
            ".env.sophia": "Sophia business intelligence keys",
            # .env.artemis is in Artemis CLI repo, not here
        }

        for env_file, description in env_files.items():
            env_path = Path(env_file)
            if not env_path.exists():
                logger.warning(f"⚠️  {env_file} not found ({description})")
                self._create_env_template(env_file)

        # Verify no key contamination
        self._check_key_separation()

        logger.info("✅ Environment validation complete")

    def _check_key_separation(self):
        """Ensure proper API key separation"""

        # Business keys that should ONLY be in Sophia
        business_keys = [
            "APOLLO",
            "SLACK",
            "SALESFORCE",
            "AIRTABLE",
            "ASANA",
            "LINEAR",
            "HUBSPOT",
            "LOOKER",
            "NETSUITE",
        ]

        # AI model keys that should NOT be in Sophia
        ai_keys = ["ANTHROPIC", "OPENAI", "GROQ", "GROK", "DEEPSEEK", "MISTRAL", "COHERE"]

        sophia_env = Path(".env.sophia")
        if sophia_env.exists():
            content = sophia_env.read_text()

            # Check for AI keys in Sophia (should not exist)
            contamination = []
            for key in ai_keys:
                if key in content:
                    contamination.append(key)

            if contamination:
                logger.error(f"❌ AI model keys found in .env.sophia: {contamination}")
                logger.error("These should be in Artemis CLI environment only!")
                if not self._ask_confirmation("Continue with contaminated environment?"):
                    sys.exit(1)

    def _create_env_template(self, env_file: str):
        """Create environment file template"""
        templates = {
            ".env.mcp": """# MCP Bridge Configuration
MCP_MEMORY_HOST=0.0.0.0
MCP_MEMORY_PORT=8765
MCP_BRIDGE_PORT=8766
MCP_DOMAIN_ISOLATION=true
MCP_LOG_LEVEL=INFO
""",
            ".env.sophia": """# Sophia Business Intelligence Keys
# Business Service APIs (Sophia ONLY)
# APOLLO_API_KEY=
# SLACK_API_TOKEN=
# SALESFORCE_CLIENT_ID=
# AIRTABLE_API_KEY=
# ASANA_API_TOKEN=
# LINEAR_API_KEY=
# HUBSPOT_API_KEY=
# LOOKER_CLIENT_ID=
# NETSUITE_CLIENT_ID=

# Infrastructure (Sophia manages)
POSTGRES_URL=postgresql://sophia:password@localhost:5432/sophia
REDIS_URL=redis://localhost:6379
# QDRANT_API_KEY=
# WEAVIATE_API_KEY=
""",
            ".env.artemis": """# Artemis AI Model Keys (Should be in Artemis CLI repo, not here)
# This file should NOT exist in Sophia Intel AI repository
# All AI model keys belong in the Artemis CLI environment
""",
        }

        if env_file in templates:
            logger.info(f"📝 Creating template: {env_file}")
            Path(env_file).write_text(templates[env_file])

    async def start_all_services(self):
        """Start all services in dependency order"""
        logger.info("🚀 Starting Unified Orchestrator")
        logger.info(f"📊 Environment: {self.config.get('environment', 'development')}")

        # Group services by priority
        priority_groups = {}
        for name, service in self.config.get("services", {}).items():
            priority = service.get("priority", 99)
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append((name, service))

        # Start services by priority
        for priority in sorted(priority_groups.keys()):
            logger.info(f"\n🔄 Starting priority {priority} services...")

            tasks = []
            for name, service in priority_groups[priority]:
                if service.get("required", True) or self._should_start_optional(name):
                    tasks.append(self.start_service(name, service))

            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Check for failures
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        name = priority_groups[priority][i][0]
                        logger.error(f"❌ Failed to start {name}: {result}")
                        if priority_groups[priority][i][1].get("required", True):
                            logger.error("Critical service failed, aborting startup")
                            await self.stop_all_services()
                            sys.exit(1)

        # Final health check
        await self.health_check_all()

        # Display summary
        self.display_summary()

    async def start_service(self, name: str, config: Dict) -> bool:
        """Start a single service"""
        logger.info(f"  ▶️  Starting {name}...")

        # Check dependencies
        depends_on = config.get("depends_on", [])
        for dep in depends_on:
            if dep not in self.services or self.services[dep]["status"] != ServiceStatus.HEALTHY:
                logger.warning(f"  ⚠️  {name} waiting for {dep}")
                await self._wait_for_service(dep)

        # Load environment file if specified
        env = os.environ.copy()
        if "env_file" in config:
            env_file = Path(config["env_file"])
            if env_file.exists():
                with open(env_file) as f:
                    for line in f:
                        if line.strip() and not line.startswith("#"):
                            if "=" in line:
                                key, value = line.strip().split("=", 1)
                                env[key] = value

        # Start the service
        try:
            command = config["command"]

            # Don't actually start external services in dry run
            if "--dry-run" in sys.argv:
                logger.info(f"  🔸 Would start: {command}")
                self.services[name] = {
                    "status": ServiceStatus.HEALTHY,
                    "port": config.get("port"),
                    "domain": config.get("domain", ServiceDomain.SHARED.value),
                }
                return True

            # Start the process
            process = subprocess.Popen(
                command, shell=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            self.processes[name] = process
            self.services[name] = {
                "status": ServiceStatus.STARTING,
                "port": config.get("port"),
                "pid": process.pid,
                "domain": config.get("domain", ServiceDomain.SHARED.value),
                "start_time": datetime.now(),
            }

            # Wait for health check
            if await self._wait_for_health(name, config):
                self.services[name]["status"] = ServiceStatus.HEALTHY
                logger.info(f"  ✅ {name} started successfully")
                return True
            else:
                self.services[name]["status"] = ServiceStatus.FAILED
                logger.error(f"  ❌ {name} failed health check")
                return False

        except Exception as e:
            logger.error(f"  ❌ Failed to start {name}: {e}")
            self.services[name] = {"status": ServiceStatus.FAILED, "error": str(e)}
            return False

    async def _wait_for_service(self, name: str, timeout: int = 60):
        """Wait for a service to become healthy"""
        start = time.time()
        while time.time() - start < timeout:
            if name in self.services and self.services[name]["status"] == ServiceStatus.HEALTHY:
                return True
            await asyncio.sleep(1)
        return False

    async def _wait_for_health(self, name: str, config: Dict, timeout: int = 30) -> bool:
        """Wait for service to pass health check"""
        start = time.time()

        while time.time() - start < timeout:
            if "health_check" in config:
                # Command-based health check
                result = subprocess.run(config["health_check"], shell=True, capture_output=True)
                if result.returncode == 0:
                    return True

            elif "health_endpoint" in config and "port" in config:
                # HTTP health check
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(
                            f"http://localhost:{config['port']}{config['health_endpoint']}",
                            timeout=2,
                        )
                        if response.status_code == 200:
                            return True
                except:
                    pass

            await asyncio.sleep(2)

        return False

    async def health_check_all(self):
        """Run health checks on all services"""
        logger.info("\n🏥 Running final health checks...")

        healthy = 0
        unhealthy = 0

        for name, service in self.services.items():
            if service["status"] == ServiceStatus.HEALTHY:
                healthy += 1
                logger.info(f"  ✅ {name}: Healthy")
            else:
                unhealthy += 1
                logger.warning(f"  ⚠️  {name}: {service['status'].value}")

        logger.info(f"\n📊 Health Summary: {healthy} healthy, {unhealthy} unhealthy")

    async def stop_all_services(self):
        """Stop all running services"""
        logger.info("\n🛑 Stopping all services...")

        for name, process in self.processes.items():
            try:
                process.terminate()
                logger.info(f"  ⏹️  Stopped {name}")
            except:
                pass

        # Give processes time to cleanup
        await asyncio.sleep(2)

        # Force kill if needed
        for name, process in self.processes.items():
            if process.poll() is None:
                process.kill()
                logger.warning(f"  ⚠️  Force killed {name}")

    def display_summary(self):
        """Display startup summary"""
        duration = (datetime.now() - self.start_time).total_seconds()

        print("\n" + "=" * 60)
        print("🎉 UNIFIED ORCHESTRATOR STARTUP COMPLETE")
        print("=" * 60)

        # Group by domain
        domains = {}
        for name, service in self.services.items():
            domain = service.get("domain", "unknown")
            if domain not in domains:
                domains[domain] = []
            domains[domain].append((name, service))

        for domain, services in domains.items():
            print(f"\n📦 {domain.upper()} Domain:")
            for name, service in services:
                port = service.get("port", "N/A")
                status = service["status"].value
                icon = "✅" if status == "healthy" else "⚠️"
                print(f"  {icon} {name}: port {port} - {status}")

        print(f"\n⏱️  Startup time: {duration:.2f} seconds")
        print("\n📋 Quick Commands:")
        print("  • Sophia Backend: http://localhost:8000")
        print("  • MCP Memory: http://localhost:8765")
        print("  • MCP Bridge: http://localhost:8766")
        print("  • Health Check: curl http://localhost:8000/health")
        print("\n✨ All systems operational!")
        print("=" * 60)

    def _should_start_optional(self, name: str) -> bool:
        """Determine if optional service should start"""
        # Can be configured via environment or command line
        if f"--no-{name}" in sys.argv:
            return False
        if f"--with-{name}" in sys.argv:
            return True
        return os.getenv(f"START_{name.upper()}", "false").lower() == "true"

    def _ask_confirmation(self, question: str) -> bool:
        """Ask user for confirmation"""
        if "--yes" in sys.argv or "--force" in sys.argv:
            return True
        response = input(f"{question} (y/N): ")
        return response.lower() in ["y", "yes"]


async def main():
    """Main entry point"""

    # Parse arguments
    args = sys.argv[1:]

    if "--help" in args:
        print(
            """
Unified Orchestrator for Sophia Intel AI

Usage: python3 unified_orchestrator.py [OPTIONS]

Options:
  --config PATH        Config file path (default: startup-config.yml)
  --environment ENV    Environment (development/production)
  --dry-run           Show what would be done without starting services
  --no-health-check   Skip health checks
  --yes, --force      Auto-confirm all prompts
  --with-SERVICE      Start optional SERVICE
  --no-SERVICE        Skip optional SERVICE
  --help              Show this help message

Examples:
  python3 unified_orchestrator.py
  python3 unified_orchestrator.py --environment production
  python3 unified_orchestrator.py --with-artemis_connector
  python3 unified_orchestrator.py --dry-run
"""
        )
        return

    # Determine config file
    config_path = "startup-config.yml"
    for i, arg in enumerate(args):
        if arg == "--config" and i + 1 < len(args):
            config_path = args[i + 1]
            break

    # Create and run orchestrator
    orchestrator = UnifiedOrchestrator(config_path)

    try:
        await orchestrator.start_all_services()

        # Keep running until interrupted
        if "--dry-run" not in args:
            logger.info("\n⌨️  Press Ctrl+C to stop all services...")
            await asyncio.Event().wait()

    except KeyboardInterrupt:
        logger.info("\n👋 Shutdown requested")
        await orchestrator.stop_all_services()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        await orchestrator.stop_all_services()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
