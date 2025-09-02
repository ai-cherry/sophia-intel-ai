#!/usr/bin/env python3
"""
Cline Activity Monitor - Real-time tracking of Cline's work through MCP bridge
"""

import asyncio
import json
import redis
from datetime import datetime
from typing import Dict, Any, List
import httpx
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()

class ClineActivityMonitor:
    """Monitor Cline's real-time activity through MCP bridge and Redis"""
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.cline_activities = []
        self.mcp_messages = []
        self.server_status = {}
        self.active_agents = {}
        self.stats = {
            "messages_processed": 0,
            "cline_actions": 0,
            "errors": 0,
            "api_calls": 0
        }
        
    async def monitor_redis_activity(self):
        """Monitor Redis for Cline activity patterns"""
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe('mcp:*', 'swarm:*', 'cline:*', 'agent:*')
        
        console.print("[green]Monitoring Redis channels for Cline activity...[/green]")
        
        for message in pubsub.listen():
            if message['type'] == 'message':
                self.process_redis_message(message)
    
    def process_redis_message(self, message):
        """Process Redis pub/sub messages"""
        channel = message['channel']
        data = message['data']
        
        # Track Cline-specific activities
        if 'cline' in channel.lower() or 'cline' in str(data).lower():
            self.cline_activities.append({
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "channel": channel,
                "action": data[:100] if isinstance(data, str) else str(data)[:100],
                "type": "CLINE_ACTION"
            })
            self.stats["cline_actions"] += 1
        
        # Track general MCP messages
        self.mcp_messages.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "channel": channel,
            "data": str(data)[:100]
        })
        
        self.stats["messages_processed"] += 1
        
        # Keep lists manageable
        if len(self.cline_activities) > 50:
            self.cline_activities.pop(0)
        if len(self.mcp_messages) > 100:
            self.mcp_messages.pop(0)
    
    async def check_mcp_servers(self):
        """Check status of all MCP servers"""
        servers = {
            "MCP Code Review": "http://localhost:8003/health",
            "Unified API": "http://localhost:8005/",
            "MCP Memory": "http://localhost:8001/health",
            "Streamlit UI": "http://localhost:8501/",
            "Next.js UI": "http://localhost:3000/"
        }
        
        async with httpx.AsyncClient() as client:
            for name, url in servers.items():
                try:
                    response = await client.get(url, timeout=1.0)
                    self.server_status[name] = {
                        "status": "✅ Online",
                        "code": response.status_code,
                        "latency": f"{response.elapsed.total_seconds()*1000:.0f}ms"
                    }
                except:
                    self.server_status[name] = {
                        "status": "❌ Offline",
                        "code": None,
                        "latency": "N/A"
                    }
    
    async def detect_cline_patterns(self):
        """Detect Cline working patterns from API calls"""
        # Monitor unified API for Cline-specific patterns
        api_endpoints = [
            "/teams/run",  # Team executions
            "/mcp/embeddings",  # Embedding requests
            "/swarms/execute",  # Swarm executions
        ]
        
        async with httpx.AsyncClient() as client:
            for endpoint in api_endpoints:
                try:
                    # Just check if endpoint is responsive
                    response = await client.options(f"http://localhost:8005{endpoint}", timeout=1.0)
                    if response.status_code < 400:
                        self.stats["api_calls"] += 1
                except:
                    pass
    
    def create_display(self) -> Layout:
        """Create rich display layout for monitoring"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=4)
        )
        
        # Header
        header = Panel(
            Text("🔍 Cline Real-Time Activity Monitor", justify="center", style="bold cyan"),
            title="[bold]MCP Bridge Monitor[/bold]"
        )
        layout["header"].update(header)
        
        # Main area
        layout["main"].split_row(
            Layout(name="servers", ratio=1),
            Layout(name="activity", ratio=2),
            Layout(name="stats", ratio=1)
        )
        
        # Server status
        server_table = Table(show_header=True, title="MCP Servers")
        server_table.add_column("Server", style="cyan", width=15)
        server_table.add_column("Status", style="green", width=10)
        server_table.add_column("Latency", style="yellow", width=8)
        
        for name, info in self.server_status.items():
            server_table.add_row(
                name,
                info["status"],
                info["latency"]
            )
        
        layout["main"]["servers"].update(Panel(server_table))
        
        # Cline activity
        activity_table = Table(show_header=True, title="Cline Activity Stream")
        activity_table.add_column("Time", style="dim", width=8)
        activity_table.add_column("Type", style="magenta", width=12)
        activity_table.add_column("Action", style="white")
        
        # Show recent Cline activities
        for activity in self.cline_activities[-10:]:
            activity_table.add_row(
                activity["timestamp"],
                activity["type"],
                activity["action"]
            )
        
        if not self.cline_activities:
            activity_table.add_row("--:--:--", "WAITING", "Waiting for Cline activity...")
        
        layout["main"]["activity"].update(Panel(activity_table))
        
        # Statistics
        stats_table = Table(show_header=False, title="Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="yellow")
        
        stats_table.add_row("Messages", str(self.stats["messages_processed"]))
        stats_table.add_row("Cline Actions", str(self.stats["cline_actions"]))
        stats_table.add_row("API Calls", str(self.stats["api_calls"]))
        stats_table.add_row("Errors", str(self.stats["errors"]))
        
        layout["main"]["stats"].update(Panel(stats_table))
        
        # Footer - Recent MCP messages
        footer_text = "Recent MCP Messages:\n"
        for msg in self.mcp_messages[-3:]:
            footer_text += f"[dim]{msg['timestamp']}[/dim] {msg['channel']}: {msg['data']}\n"
        
        layout["footer"].update(Panel(footer_text, title="Message Bus"))
        
        return layout
    
    async def run(self):
        """Main monitoring loop"""
        console.print("[yellow]Starting Cline Activity Monitor...[/yellow]\n")
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self.monitor_redis_activity()),
            asyncio.create_task(self.periodic_server_check()),
            asyncio.create_task(self.periodic_pattern_detection())
        ]
        
        # Display loop
        with Live(self.create_display(), refresh_per_second=2, console=console) as live:
            try:
                while True:
                    await asyncio.sleep(0.5)
                    live.update(self.create_display())
            except KeyboardInterrupt:
                console.print("\n[yellow]Stopping monitor...[/yellow]")
                for task in tasks:
                    task.cancel()
    
    async def periodic_server_check(self):
        """Periodically check server health"""
        while True:
            await self.check_mcp_servers()
            await asyncio.sleep(5)
    
    async def periodic_pattern_detection(self):
        """Periodically detect Cline patterns"""
        while True:
            await self.detect_cline_patterns()
            await asyncio.sleep(10)

def simulate_cline_activity():
    """Simulate Cline activity for testing"""
    import threading
    import time
    import random
    
    def publish_test_messages():
        r = redis.Redis(host='localhost', port=6379)
        activities = [
            "Analyzing code structure",
            "Running tests",
            "Generating embeddings",
            "Executing swarm task",
            "Updating documentation",
            "Refactoring module",
            "Creating unit tests",
            "Optimizing performance"
        ]
        
        while True:
            time.sleep(random.randint(2, 8))
            activity = random.choice(activities)
            channel = random.choice(['cline:action', 'agent:cline', 'mcp:broadcast'])
            
            message = json.dumps({
                "agent": "cline",
                "action": activity,
                "timestamp": datetime.now().isoformat()
            })
            
            try:
                r.publish(channel, message)
            except:
                pass
    
    # Start simulator in background
    thread = threading.Thread(target=publish_test_messages, daemon=True)
    thread.start()
    console.print("[dim]Test message simulator started[/dim]")

async def main():
    """Main entry point"""
    monitor = ClineActivityMonitor()
    
    # Check if we should simulate activity
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--simulate":
        simulate_cline_activity()
    
    await monitor.run()

if __name__ == "__main__":
    import sys
    
    console.print("""
[bold cyan]Cline Activity Monitor[/bold cyan]
========================
Monitor real-time activity of Cline through MCP bridge

Usage:
  python monitor_cline_activity.py           # Monitor real activity
  python monitor_cline_activity.py --simulate # Include test messages

Press Ctrl+C to exit
""")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[red]Monitor stopped[/red]")