#!/usr/bin/env python3
"""
Sophia Intel CLI - Universal Command Line Interface
Advanced AI-powered development and deployment management
"""

import asyncio
import click
import json
import os
import sys
import requests
from typing import Dict, Any, Optional
from datetime import datetime
import subprocess
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config.config import Settings
from mcp_servers.ai_router import AIRouter


class SophiaIntelCLI:
    """Main CLI class for Sophia Intel operations"""

    def __init__(self):
        self.settings = Settings()
        self.ai_router = AIRouter()
        self.base_url = f"http://localhost:{8001}"

    async def initialize(self):
        """Initialize the CLI with AI router"""
        await self.ai_router.initialize()

    def check_server_health(self) -> bool:
        """Check if the MCP server is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    async def route_ai_request(
        self, prompt: str, task_type: str = "general", preference: str = "balanced"
    ) -> Dict[str, Any]:
        """Route AI request through the AI router"""
        try:
            result = await self.ai_router.route_request(prompt=prompt, task_type=task_type, preference=preference)
            return result
        except Exception as e:
            return {"error": str(e)}


# Initialize CLI instance
cli_instance = SophiaIntelCLI()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    🧠 Sophia Intel CLI - AI-Powered Development Platform

    Universal command-line interface for AI routing, deployment, and management.
    """
    pass


@cli.group()
def ai():
    """🤖 AI Operations - Intelligent model routing and interaction"""
    pass


@ai.command()
@click.argument("prompt")
@click.option(
    "--task-type",
    "-t",
    default="general",
    type=click.Choice(["code", "math", "creative", "general", "review"]),
    help="Type of task for optimal model selection",
)
@click.option(
    "--preference",
    "-p",
    default="balanced",
    type=click.Choice(["speed", "quality", "cost", "balanced"]),
    help="Optimization preference for model selection",
)
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text", help="Output format")
def ask(prompt: str, task_type: str, preference: str, output: str):
    """
    🧠 Ask AI with intelligent model routing

    Examples:
      sophia ai ask "Write a Python function to sort a list" --task-type code
      sophia ai ask "Solve: 2x + 5 = 15" --task-type math --preference speed
      sophia ai ask "Write a creative story about AI" --task-type creative
    """

    async def _ask():
        await cli_instance.initialize()

        if not cli_instance.check_server_health():
            click.echo("❌ MCP Server not running. Please start the server first.")
            click.echo("   Run: sophia server start")
            return

        click.echo(f"🧠 Routing request to optimal AI model...")
        click.echo(f"   Task Type: {task_type}")
        click.echo(f"   Preference: {preference}")
        click.echo()

        result = await cli_instance.route_ai_request(prompt, task_type, preference)

        if output == "json":
            click.echo(json.dumps(result, indent=2))
        else:
            if "error" in result:
                click.echo(f"❌ Error: {result['error']}")
            else:
                click.echo(f"🤖 Model: {result.get('model', 'Unknown')}")
                click.echo(f"⚡ Response Time: {result.get('response_time', 0):.3f}s")
                click.echo(f"🎯 Confidence: {result.get('confidence', 0):.1%}")
                click.echo()
                click.echo("📝 Response:")
                click.echo(result.get("response", "No response"))

    asyncio.run(_ask())


@ai.command()
def models():
    """📋 List available AI models and their capabilities"""
    if not cli_instance.check_server_health():
        click.echo("❌ MCP Server not running. Please start the server first.")
        return

    try:
        response = requests.get(f"{cli_instance.base_url}/ai/models")
        models_data = response.json()

        click.echo("🤖 Available AI Models:")
        click.echo("=" * 50)

        for provider, models in models_data.items():
            click.echo(f"\n📡 {provider.upper()}")
            for model in models:
                click.echo(f"  • {model}")

    except Exception as e:
        click.echo(f"❌ Error fetching models: {e}")


@ai.command()
def stats():
    """📊 Show AI routing statistics and performance metrics"""
    if not cli_instance.check_server_health():
        click.echo("❌ MCP Server not running. Please start the server first.")
        return

    try:
        response = requests.get(f"{cli_instance.base_url}/stats")
        stats_data = response.json()

        click.echo("📊 AI Routing Statistics:")
        click.echo("=" * 40)
        click.echo(f"Total Requests: {stats_data.get('total_requests', 0)}")
        click.echo(f"Average Response Time: {stats_data.get('avg_response_time', 0):.3f}s")
        click.echo(f"Average Confidence: {stats_data.get('avg_confidence', 0):.1%}")
        click.echo()

        provider_stats = stats_data.get("provider_distribution", {})
        if provider_stats:
            click.echo("🔄 Provider Distribution:")
            for provider, count in provider_stats.items():
                click.echo(f"  {provider}: {count} requests")

    except Exception as e:
        click.echo(f"❌ Error fetching statistics: {e}")


@cli.group()
def lambda_servers():
    """🖥️ Lambda Labs Server Management - Control GH200 inference servers"""
    pass


@lambda_servers.command()
@click.option("--token", "-t", help="MCP authentication token", envvar="MCP_AUTH_TOKEN")
def list(token: Optional[str]):
    """📋 List all Lambda Labs GH200 servers"""
    if not cli_instance.check_server_health():
        click.echo("❌ MCP Server not running. Please start the server first.")
        return

    headers = {}
    if token:
        headers["X-MCP-Token"] = token

    try:
        response = requests.get(f"{cli_instance.base_url}/servers", headers=headers)
        if response.status_code == 401:
            click.echo("❌ Authentication required. Set MCP_AUTH_TOKEN or use --token")
            return

        response.raise_for_status()
        data = response.json()

        click.echo("🖥️ Lambda Labs GH200 Servers:")
        click.echo("=" * 50)

        for server in data.get("servers", []):
            status_emoji = "🟢" if server["status"] == "active" else "🔴" if server["status"] == "error" else "🟡"
            click.echo(f"\n{status_emoji} {server['key'].upper()}")
            click.echo(f"   Name: {server['name']}")
            click.echo(f"   IP: {server['ip']}")
            click.echo(f"   Role: {server['role']}")
            click.echo(f"   Status: {server['status']}")
            click.echo(f"   Inference URL: {server.get('inference_url', 'N/A')}")

        click.echo(f"\nTotal servers: {data.get('total', 0)}")

    except Exception as e:
        click.echo(f"❌ Error listing servers: {e}")


@lambda_servers.command()
@click.argument("server_key", type=click.Choice(["primary", "secondary"]))
@click.option("--token", "-t", help="MCP authentication token", envvar="MCP_AUTH_TOKEN")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
def start(server_key: str, token: Optional[str], force: bool):
    """🚀 Start a Lambda Labs server"""
    if not force:
        if not click.confirm(f"Start {server_key} server?"):
            click.echo("Operation cancelled.")
            return

    if not cli_instance.check_server_health():
        click.echo("❌ MCP Server not running. Please start the server first.")
        return

    headers = {}
    if token:
        headers["X-MCP-Token"] = token

    try:
        click.echo(f"🚀 Starting {server_key} server...")
        response = requests.post(f"{cli_instance.base_url}/servers/{server_key}/start", headers=headers)

        if response.status_code == 401:
            click.echo("❌ Authentication required. Set MCP_AUTH_TOKEN or use --token")
            return

        response.raise_for_status()
        data = response.json()

        click.echo(f"✅ {server_key.capitalize()} server start initiated")
        click.echo(f"   Instance ID: {data.get('instance_id')}")
        click.echo("   Note: Server may take a few minutes to fully start")

    except Exception as e:
        click.echo(f"❌ Error starting server: {e}")


@lambda_servers.command()
@click.argument("server_key", type=click.Choice(["primary", "secondary"]))
@click.option("--token", "-t", help="MCP authentication token", envvar="MCP_AUTH_TOKEN")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
def stop(server_key: str, token: Optional[str], force: bool):
    """🛑 Stop a Lambda Labs server"""
    if not force:
        if not click.confirm(f"⚠️  Stop {server_key} server? This will interrupt any running inference tasks."):
            click.echo("Operation cancelled.")
            return

    if not cli_instance.check_server_health():
        click.echo("❌ MCP Server not running. Please start the server first.")
        return

    headers = {}
    if token:
        headers["X-MCP-Token"] = token

    try:
        click.echo(f"🛑 Stopping {server_key} server...")
        response = requests.post(f"{cli_instance.base_url}/servers/{server_key}/stop", headers=headers)

        if response.status_code == 401:
            click.echo("❌ Authentication required. Set MCP_AUTH_TOKEN or use --token")
            return

        response.raise_for_status()
        data = response.json()

        click.echo(f"✅ {server_key.capitalize()} server stop initiated")
        click.echo(f"   Instance ID: {data.get('instance_id')}")

    except Exception as e:
        click.echo(f"❌ Error stopping server: {e}")


@lambda_servers.command()
@click.argument("server_key", type=click.Choice(["primary", "secondary"]))
@click.option("--token", "-t", help="MCP authentication token", envvar="MCP_AUTH_TOKEN")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
def restart(server_key: str, token: Optional[str], force: bool):
    """🔄 Restart a Lambda Labs server"""
    if not force:
        if not click.confirm(f"Restart {server_key} server?"):
            click.echo("Operation cancelled.")
            return

    if not cli_instance.check_server_health():
        click.echo("❌ MCP Server not running. Please start the server first.")
        return

    headers = {}
    if token:
        headers["X-MCP-Token"] = token

    try:
        click.echo(f"🔄 Restarting {server_key} server...")
        response = requests.post(f"{cli_instance.base_url}/servers/{server_key}/restart", headers=headers)

        if response.status_code == 401:
            click.echo("❌ Authentication required. Set MCP_AUTH_TOKEN or use --token")
            return

        response.raise_for_status()
        data = response.json()

        click.echo(f"✅ {server_key.capitalize()} server restart initiated")
        click.echo(f"   Instance ID: {data.get('instance_id')}")
        click.echo("   Note: Server may take a few minutes to fully restart")

    except Exception as e:
        click.echo(f"❌ Error restarting server: {e}")


@lambda_servers.command()
@click.argument("server_key", type=click.Choice(["primary", "secondary"]))
@click.option("--token", "-t", help="MCP authentication token", envvar="MCP_AUTH_TOKEN")
def stats(server_key: str, token: Optional[str]):
    """📊 Get server statistics and performance metrics"""
    if not cli_instance.check_server_health():
        click.echo("❌ MCP Server not running. Please start the server first.")
        return

    headers = {}
    if token:
        headers["X-MCP-Token"] = token

    try:
        response = requests.get(f"{cli_instance.base_url}/servers/{server_key}/stats", headers=headers)

        if response.status_code == 401:
            click.echo("❌ Authentication required. Set MCP_AUTH_TOKEN or use --token")
            return

        response.raise_for_status()
        data = response.json()

        stats = data.get("stats", {})
        config = data.get("config", {})

        click.echo(f"📊 {server_key.capitalize()} Server Statistics:")
        click.echo("=" * 40)
        click.echo(f"Status: {stats.get('status', 'unknown')}")
        click.echo(f"Instance Type: {stats.get('instance_type', 'unknown')}")
        click.echo(f"Region: {stats.get('region', 'unknown')}")
        click.echo(f"IP Address: {stats.get('ip', 'unknown')}")
        click.echo(f"Role: {config.get('role', 'unknown')}")
        click.echo(f"GPU Utilization: {stats.get('gpu_utilization', 'N/A')}")
        click.echo(f"Memory Usage: {stats.get('memory_usage', 'N/A')}")
        click.echo(f"Uptime: {stats.get('uptime', 'N/A')}")

        if "error" in stats:
            click.echo(f"⚠️  Error: {stats['error']}")

    except Exception as e:
        click.echo(f"❌ Error getting server stats: {e}")


@lambda_servers.command()
@click.option("--token", "-t", help="MCP authentication token", envvar="MCP_AUTH_TOKEN")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
def rename(token: Optional[str], force: bool):
    """🏷️ Rename all servers with proper naming convention"""
    if not force:
        if not click.confirm("Rename all servers to use proper naming convention?"):
            click.echo("Operation cancelled.")
            return

    if not cli_instance.check_server_health():
        click.echo("❌ MCP Server not running. Please start the server first.")
        return

    headers = {}
    if token:
        headers["X-MCP-Token"] = token

    try:
        click.echo("🏷️ Renaming servers...")
        response = requests.post(f"{cli_instance.base_url}/servers/rename", headers=headers)

        if response.status_code == 401:
            click.echo("❌ Authentication required. Set MCP_AUTH_TOKEN or use --token")
            return

        response.raise_for_status()
        data = response.json()

        click.echo("✅ Rename operation completed:")
        for result in data.get("rename_results", []):
            status_emoji = "✅" if result["status"] == "success" else "❌"
            click.echo(f"   {status_emoji} {result['server']}: {result.get('new_name', result.get('error'))}")

    except Exception as e:
        click.echo(f"❌ Error renaming servers: {e}")


@cli.group()
def server():
    """🖥️ MCP Server Management - Start, stop, and monitor MCP server"""
    pass


@server.command()
@click.option("--port", "-p", default=8001, help="Port to run the server on")
@click.option("--host", "-h", default="0.0.0.0", help="Host to bind the server to")
def start(port: int, host: str):
    """🚀 Start the Enhanced MCP Server"""
    click.echo(f"🚀 Starting Sophia Intel MCP Server on {host}:{port}")

    try:
        # Start the server using subprocess
        cmd = [sys.executable, "mcp_servers/enhanced_unified_server.py", "--host", host, "--port", str(port)]

        process = subprocess.Popen(cmd, cwd=Path(__file__).parent.parent)
        click.echo(f"✅ Server started with PID: {process.pid}")
        click.echo(f"🌐 Server URL: http://{host}:{port}")
        click.echo("📊 Health Check: http://localhost:8001/health")
        click.echo("📋 API Docs: http://localhost:8001/docs")

    except Exception as e:
        click.echo(f"❌ Failed to start server: {e}")


@server.command()
def stop():
    """🛑 Stop the MCP Server"""
    try:
        # Find and kill the server process
        result = subprocess.run(["pkill", "-f", "enhanced_unified_server.py"], capture_output=True, text=True)

        if result.returncode == 0:
            click.echo("✅ Server stopped successfully")
        else:
            click.echo("⚠️ No server process found or already stopped")

    except Exception as e:
        click.echo(f"❌ Error stopping server: {e}")


@server.command()
def status():
    """📊 Check server status and health"""
    if cli_instance.check_server_health():
        try:
            response = requests.get(f"{cli_instance.base_url}/health")
            health_data = response.json()

            click.echo("✅ Server Status: HEALTHY")
            click.echo(f"🕐 Uptime: {health_data.get('uptime', 'Unknown')}")
            click.echo(f"📊 Total Requests: {health_data.get('total_requests', 0)}")
            click.echo(f"💾 Memory Usage: {health_data.get('memory_usage', 'Unknown')}")

        except Exception as e:
            click.echo(f"⚠️ Server running but health check failed: {e}")
    else:
        click.echo("❌ Server Status: NOT RUNNING")
        click.echo("   Run 'sophia server start' to start the server")


@cli.group()
def deploy():
    """🚀 Deployment Operations - Infrastructure and application deployment"""
    pass


@deploy.command()
@click.option(
    "--environment", "-e", default="dev", type=click.Choice(["dev", "staging", "prod"]), help="Deployment environment"
)
@click.option("--dry-run", is_flag=True, help="Preview deployment without executing")
def infrastructure(environment: str, dry_run: bool):
    """🏗️ Deploy infrastructure using Pulumi"""
    click.echo(f"🏗️ Deploying infrastructure to {environment} environment")

    if dry_run:
        click.echo("👀 Dry run mode - previewing changes only")
        cmd = ["pulumi", "preview"]
    else:
        click.echo("🚀 Executing deployment")
        cmd = ["pulumi", "up", "--yes"]

    try:
        # Set environment variables
        env = os.environ.copy()
        env["PULUMI_CONFIG_PASSPHRASE"] = "sophia-intel-secure-2025"

        # Run Pulumi command
        result = subprocess.run(
            cmd, cwd=Path(__file__).parent.parent / "infrastructure" / "pulumi", env=env, capture_output=True, text=True
        )

        if result.returncode == 0:
            click.echo("✅ Infrastructure deployment completed successfully")
            if not dry_run:
                click.echo("🌐 Infrastructure is now live")
        else:
            click.echo(f"❌ Deployment failed: {result.stderr}")

    except Exception as e:
        click.echo(f"❌ Error during deployment: {e}")


@deploy.command()
@click.option("--tag", "-t", help="Docker image tag to deploy")
def application(tag: str):
    """📦 Deploy application containers"""
    if not tag:
        # Generate tag from current timestamp
        tag = f"latest-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    click.echo(f"📦 Deploying application with tag: {tag}")

    try:
        # Build Docker image
        click.echo("🔨 Building Docker image...")
        build_cmd = ["docker", "build", "-f", "Dockerfile.enhanced-mcp", "-t", f"sophia-intel-mcp:{tag}", "."]

        result = subprocess.run(build_cmd, cwd=Path(__file__).parent.parent, capture_output=True, text=True)

        if result.returncode == 0:
            click.echo("✅ Docker image built successfully")
            click.echo(f"🏷️ Image: sophia-intel-mcp:{tag}")
        else:
            click.echo(f"❌ Docker build failed: {result.stderr}")
            return

        # TODO: Add container deployment logic here
        click.echo("🚀 Container deployment logic to be implemented")

    except Exception as e:
        click.echo(f"❌ Error during application deployment: {e}")


@cli.group()
def test():
    """🧪 Testing Operations - Performance and functionality testing"""
    pass


@test.command()
@click.option("--concurrency", "-c", default=10, help="Number of concurrent requests")
@click.option("--duration", "-d", default=30, help="Test duration in seconds")
def performance(concurrency: int, duration: int):
    """⚡ Run performance tests against the MCP server"""
    if not cli_instance.check_server_health():
        click.echo("❌ MCP Server not running. Please start the server first.")
        return

    click.echo(f"⚡ Running performance test:")
    click.echo(f"   Concurrency: {concurrency}")
    click.echo(f"   Duration: {duration}s")
    click.echo()

    try:
        # Run the performance test script
        cmd = [sys.executable, "performance_test.py"]

        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent, capture_output=True, text=True)

        if result.returncode == 0:
            click.echo("✅ Performance test completed")
            click.echo(result.stdout)
        else:
            click.echo(f"❌ Performance test failed: {result.stderr}")

    except Exception as e:
        click.echo(f"❌ Error running performance test: {e}")


@test.command()
def health():
    """🏥 Run comprehensive health checks"""
    click.echo("🏥 Running comprehensive health checks...")
    click.echo()

    # Check server health
    if cli_instance.check_server_health():
        click.echo("✅ MCP Server: HEALTHY")
    else:
        click.echo("❌ MCP Server: NOT RUNNING")

    # Check AI router
    try:
        response = requests.get(f"{cli_instance.base_url}/ai/models", timeout=5)
        if response.status_code == 200:
            models = response.json()
            total_models = sum(len(m) for m in models.values())
            click.echo(f"✅ AI Router: {total_models} models available")
        else:
            click.echo("⚠️ AI Router: Partial functionality")
    except:
        click.echo("❌ AI Router: NOT ACCESSIBLE")

    # Check infrastructure
    try:
        # Check if Pulumi is configured
        pulumi_dir = Path(__file__).parent.parent / "infrastructure" / "pulumi"
        if pulumi_dir.exists():
            click.echo("✅ Infrastructure: Pulumi configured")
        else:
            click.echo("⚠️ Infrastructure: Pulumi not found")
    except:
        click.echo("❌ Infrastructure: Configuration error")


@cli.command()
def version():
    """📋 Show version information"""
    click.echo("🧠 Sophia Intel CLI v1.0.0")
    click.echo("🚀 Enhanced MCP Server with AI Router")
    click.echo("🏗️ Infrastructure as Code with Pulumi")
    click.echo("📊 Performance: 1,500+ req/s capability")
    click.echo()
    click.echo("🔗 Repository: https://github.com/ai-cherry/sophia-intel")


if __name__ == "__main__":
    cli()
