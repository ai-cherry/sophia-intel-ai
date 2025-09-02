#!/usr/bin/env python3
"""
Real-time MCP Server Monitor for watching Cline and other AI agents work
"""

import asyncio
import json
from datetime import datetime

import httpx
import websockets
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

class MCPMonitor:
    def __init__(self):
        self.agents = {}
        self.messages = []
        self.server_status = {}
        self.active_connections = set()

    async def check_server_health(self):
        """Check health of all MCP servers"""
        servers = {
            "MCP Code Review": "http://localhost:8003/health",
            "Unified API": "http://localhost:8005/health",
            "MCP Memory": "http://localhost:8001/health",
            "WebSocket Bus": "ws://localhost:8005/ws/bus"
        }

        async with httpx.AsyncClient() as client:
            for name, url in servers.items():
                if url.startswith("http"):
                    try:
                        response = await client.get(url, timeout=2.0)
                        self.server_status[name] = "✅ Online" if response.status_code == 200 else "⚠️ Error"
                    except:
                        self.server_status[name] = "❌ Offline"
                elif url.startswith("ws"):
                    self.server_status[name] = "🔄 WebSocket"

    async def monitor_websocket(self, agent_id="monitor"):
        """Connect to WebSocket bus for real-time monitoring"""
        uri = f"ws://localhost:8005/ws/bus?agent_id={agent_id}"

        try:
            async with websockets.connect(uri) as websocket:
                self.active_connections.add(agent_id)
                console.print(f"[green]Connected to WebSocket bus as {agent_id}[/green]")

                async for message in websocket:
                    data = json.loads(message)
                    self.process_message(data)

        except Exception as e:
            console.print(f"[red]WebSocket error: {e}[/red]")
            self.active_connections.discard(agent_id)

    def process_message(self, data):
        """Process incoming message from MCP bus"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Track agent activity
        sender = data.get("sender", "unknown")
        if sender not in self.agents:
            self.agents[sender] = {"messages": 0, "last_seen": timestamp}

        self.agents[sender]["messages"] += 1
        self.agents[sender]["last_seen"] = timestamp

        # Store message for display
        self.messages.append({
            "time": timestamp,
            "sender": sender,
            "type": data.get("type", "unknown"),
            "content": str(data.get("content", ""))[:100] + "..."
        })

        # Keep only last 20 messages
        if len(self.messages) > 20:
            self.messages.pop(0)

    def create_display(self):
        """Create rich display layout"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )

        # Header
        header = Panel(
            Text("🔍 MCP Real-Time Monitor - Watching AI Agents Work", justify="center", style="bold cyan"),
            title="[bold]Sophia Intel AI[/bold]"
        )
        layout["header"].update(header)

        # Main area split
        layout["main"].split_row(
            Layout(name="servers", ratio=1),
            Layout(name="agents", ratio=1),
            Layout(name="messages", ratio=2)
        )

        # Server status
        server_table = Table(title="Server Status", show_header=True)
        server_table.add_column("Server", style="cyan")
        server_table.add_column("Status", style="green")

        for name, status in self.server_status.items():
            server_table.add_row(name, status)

        layout["main"]["servers"].update(Panel(server_table, title="[bold]MCP Servers[/bold]"))

        # Active agents
        agent_table = Table(title="Active Agents", show_header=True)
        agent_table.add_column("Agent", style="magenta")
        agent_table.add_column("Messages", style="yellow")
        agent_table.add_column("Last Seen", style="green")

        for agent, info in self.agents.items():
            # Highlight Cline specifically
            agent_display = f"[bold red]{agent}[/bold red]" if "cline" in agent.lower() else agent
            agent_table.add_row(agent_display, str(info["messages"]), info["last_seen"])

        layout["main"]["agents"].update(Panel(agent_table, title="[bold]Agent Activity[/bold]"))

        # Recent messages
        msg_table = Table(title="Recent Messages", show_header=True)
        msg_table.add_column("Time", style="dim", width=8)
        msg_table.add_column("From", style="cyan", width=12)
        msg_table.add_column("Type", style="yellow", width=10)
        msg_table.add_column("Content", style="white")

        for msg in self.messages[-10:]:  # Show last 10 messages
            # Highlight Cline messages
            sender = f"[bold red]{msg['sender']}[/bold red]" if "cline" in msg['sender'].lower() else msg['sender']
            msg_table.add_row(msg["time"], sender, msg["type"], msg["content"])

        layout["main"]["messages"].update(Panel(msg_table, title="[bold]Message Stream[/bold]"))

        # Footer
        footer = Panel(
            f"Connected: {len(self.active_connections)} | Messages: {sum(a['messages'] for a in self.agents.values())} | Press Ctrl+C to exit",
            style="dim"
        )
        layout["footer"].update(footer)

        return layout

    async def run(self):
        """Main monitoring loop"""
        # Start health checks
        asyncio.create_task(self.periodic_health_check())

        # Start WebSocket monitoring
        asyncio.create_task(self.monitor_websocket("monitor"))
        asyncio.create_task(self.monitor_websocket("cline_watcher"))

        # Display loop
        with Live(self.create_display(), refresh_per_second=2, console=console) as live:
            while True:
                await asyncio.sleep(0.5)
                live.update(self.create_display())

    async def periodic_health_check(self):
        """Periodically check server health"""
        while True:
            await self.check_server_health()
            await asyncio.sleep(10)

async def test_mcp_connection():
    """Quick test of MCP connections"""
    console.print("[yellow]Testing MCP Server Connections...[/yellow]\n")

    # Test each server
    tests = {
        "MCP Code Review (8003)": "http://localhost:8003/health",
        "Unified API (8005)": "http://localhost:8005/health",
        "WebSocket Bus": "ws://localhost:8005/ws/bus",
    }

    async with httpx.AsyncClient() as client:
        for name, url in tests.items():
            if url.startswith("http"):
                try:
                    response = await client.get(url, timeout=2.0)
                    if response.status_code == 200:
                        console.print(f"✅ {name}: [green]Connected[/green]")
                        console.print(f"   Response: {response.text[:100]}")
                    else:
                        console.print(f"⚠️ {name}: [yellow]Status {response.status_code}[/yellow]")
                except Exception as e:
                    console.print(f"❌ {name}: [red]Failed - {e}[/red]")
            elif url.startswith("ws"):
                try:
                    async with websockets.connect(f"{url}?agent_id=test", timeout=2.0) as ws:
                        console.print(f"✅ {name}: [green]WebSocket Connected[/green]")
                        await ws.close()
                except Exception as e:
                    console.print(f"❌ {name}: [red]WebSocket Failed - {e}[/red]")

    console.print("\n[cyan]Starting Real-Time Monitor...[/cyan]\n")

async def main():
    """Main entry point"""
    # First test connections
    await test_mcp_connection()

    # Then start monitoring
    monitor = MCPMonitor()
    try:
        await monitor.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitor stopped by user[/yellow]")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[red]Exiting...[/red]")
