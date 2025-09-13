#!/usr/bin/env python3
"""
MCP HEALTH MONITOR
Real-time monitoring of all MCP server connections
"""
import asyncio
import json
import os
import subprocess
import time
from datetime import datetime
import httpx
import redis
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
console = Console()
class MCPHealthMonitor:
    """Monitor health of all MCP servers"""
    def __init__(self):
        self.servers = {
            "Filesystem MCP": {"port": 8001, "endpoint": "/health", "status": "❓"},
            "Git MCP": {"port": 8002, "endpoint": "/health", "status": "❓"},
            "Memory MCP": {"port": 8003, "endpoint": "/health", "status": "❓"},
            "Embeddings MCP": {"port": 8004, "endpoint": "/health", "status": "❓"},
            "Unified API": {"port": 8003, "endpoint": "/healthz", "status": "❓"},
            "WebSocket": {"port": 8005, "endpoint": "/ws/health", "status": "❓"},
            "Redis Cache": {"port": 6379, "type": "redis", "status": "❓"},
        }
        self.connections = {
            "Claude Desktop": {
                "status": "❓",
                "config": "~/Library/Application Support/Claude/claude_desktop_config.json",
            },
            "IDE Client": {"status": "❓", "config": ".vscode/settings.json"},
            "Sophia Swarm": {"status": "❓", "endpoint": "http://localhost:8003/teams"},
            " Swarm": {
                "status": "❓",
                "endpoint": "http://localhost:8003/",
            },
        }
        self.stats = {
            "uptime": 0,
            "total_requests": 0,
            "failed_checks": 0,
            "last_check": None,
        }
    async def check_http_server(self, name: str, port: int, endpoint: str) -> bool:
        """Check HTTP server health"""
        try:
            async with httpx.AsyncClient(timeout=2) as client:
                response = await client.get(f"http://localhost:{port}{endpoint}")
                return response.status_code in [200, 204]
        except:
            return False
    def check_redis(self) -> bool:
        """Check Redis health"""
        try:
            r = redis.Redis(host="localhost", port=6379, decode_responses=True)
            return r.ping()
        except:
            return False
    def check_process_on_port(self, port: int) -> bool:
        """Check if any process is listening on port"""
        try:
            result = subprocess.run(
                ["lsof", "-i", f":{port}"], capture_output=True, text=True, timeout=2
            )
            return bool(result.stdout.strip())
        except:
            return False
    async def update_server_status(self):
        """Update status of all servers"""
        for name, config in self.servers.items():
            if config.get("type") == "redis":
                if self.check_redis():
                    self.servers[name]["status"] = "✅"
                else:
                    self.servers[name]["status"] = "❌"
            else:
                port = config["port"]
                endpoint = config["endpoint"]
                # First check if anything is on the port
                if not self.check_process_on_port(port):
                    self.servers[name]["status"] = "🔴"  # Not running
                elif await self.check_http_server(name, port, endpoint):
                    self.servers[name]["status"] = "✅"  # Healthy
                else:
                    self.servers[name]["status"] = "🟡"  # Running but not healthy
    async def check_connections(self):
        """Check AI tool connections"""
        # Check Claude config exists
        claude_config = os.path.expanduser(
            "~/Library/Application Support/Claude/claude_desktop_config.json"
        )
        if os.path.exists(claude_config):
            self.connections["Claude Desktop"]["status"] = "✅"
        else:
            self.connections["Claude Desktop"]["status"] = "❌"
        # Check optional IDE settings
        if os.path.exists(".vscode/settings.json"):
            with open(".vscode/settings.json") as f:
                settings = json.load(f)
                if "mcp.servers" in settings:
                    self.connections["IDE Client"]["status"] = "✅"
                else:
                    self.connections["IDE Client"]["status"] = "⚠️"
        else:
            self.connections["IDE Client"]["status"] = "❌"
        # Check Sophia/ endpoints
        for name in ["Sophia Swarm", " Swarm"]:
            endpoint = self.connections[name]["endpoint"]
            try:
                async with httpx.AsyncClient(timeout=2) as client:
                    response = await client.get(endpoint)
                    if response.status_code < 500:
                        self.connections[name]["status"] = "✅"
                    else:
                        self.connections[name]["status"] = "🟡"
            except:
                self.connections[name]["status"] = "❌"
    def create_status_table(self) -> Table:
        """Create status table"""
        table = Table(title="🖥️ MCP Server Status", border_style="blue")
        table.add_column("Server", style="cyan", no_wrap=True)
        table.add_column("Port", style="yellow")
        table.add_column("Status", style="green")
        table.add_column("Health", style="magenta")
        for name, config in self.servers.items():
            status = config["status"]
            health = (
                "Healthy"
                if status == "✅"
                else (
                    "Down"
                    if status == "❌"
                    else "Starting" if status == "🟡" else "Unknown"
                )
            )
            color = "green" if status == "✅" else "red" if status == "❌" else "yellow"
            table.add_row(
                name, str(config.get("port", "N/A")), status, Text(health, style=color)
            )
        return table
    def create_connections_table(self) -> Table:
        """Create connections table"""
        table = Table(title="🔌 AI Tool Connections", border_style="green")
        table.add_column("Tool", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Config/Endpoint", style="blue")
        for name, config in self.connections.items():
            table.add_row(
                name,
                config["status"],
                config.get("config", config.get("endpoint", "N/A")),
            )
        return table
    def create_stats_panel(self) -> Panel:
        """Create statistics panel"""
        self.stats["uptime"] = int(
            time.time() - self.stats.get("start_time", time.time())
        )
        uptime_min = self.stats["uptime"] // 60
        uptime_sec = self.stats["uptime"] % 60
        stats_text = f"""
📊 Monitor Statistics
━━━━━━━━━━━━━━━━━━
⏱️ Uptime: {uptime_min}m {uptime_sec}s
📡 Total Checks: {self.stats['total_requests']}
❌ Failed Checks: {self.stats['failed_checks']}
🕐 Last Check: {self.stats.get('last_check', 'Never')}
        """
        return Panel(stats_text, title="📈 Statistics", border_style="yellow")
    def create_commands_panel(self) -> Panel:
        """Create commands panel"""
        commands = """
🎮 Quick Commands
━━━━━━━━━━━━━━━━
[green]Start All:[/green] ./scripts/start_all_mcp.sh
[yellow]Stop All:[/yellow] ./scripts/stop_all_mcp.sh
[blue]Check Status:[/blue] curl http://localhost:8003/healthz
[cyan]View Logs:[/cyan] tail -f logs/mcp_startup_*.log
[red]Kill All:[/red] pkill -f mcp
[bold]Keyboard Shortcuts:[/bold]
• q: Quit monitor
• r: Refresh now
• s: Save status report
        """
        return Panel(commands, title="⌨️ Commands", border_style="cyan")
    async def monitor_loop(self):
        """Main monitoring loop"""
        self.stats["start_time"] = time.time()
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=12),
        )
        layout["header"].update(
            Panel(
                Text(
                    "🚀 MCP MASTER HEALTH MONITOR",
                    justify="center",
                    style="bold magenta",
                ),
                border_style="magenta",
            )
        )
        with Live(layout, refresh_per_second=1, screen=True) as live:
            while True:
                try:
                    # Update statuses
                    await self.update_server_status()
                    await self.check_connections()
                    self.stats["total_requests"] += 1
                    self.stats["last_check"] = datetime.now().strftime("%H:%M:%S")
                    # Update main layout
                    main_layout = Layout()
                    main_layout.split_row(
                        Layout(self.create_status_table(), name="servers"),
                        Layout(self.create_connections_table(), name="connections"),
                    )
                    layout["main"].update(main_layout)
                    # Update footer
                    footer_layout = Layout()
                    footer_layout.split_row(
                        Layout(self.create_stats_panel()),
                        Layout(self.create_commands_panel()),
                    )
                    layout["footer"].update(footer_layout)
                    # Wait before next update
                    await asyncio.sleep(5)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.stats["failed_checks"] += 1
                    console.print(f"[red]Error: {e}[/red]")
                    await asyncio.sleep(5)
async def main():
    """Main entry point"""
    monitor = MCPHealthMonitor()
    console.print(
        Panel.fit(
            "🚀 Starting MCP Health Monitor\nPress Ctrl+C to exit", border_style="green"
        )
    )
    await monitor.monitor_loop()
    console.print("\n[yellow]Monitor stopped[/yellow]")
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[red]Exiting...[/red]")
