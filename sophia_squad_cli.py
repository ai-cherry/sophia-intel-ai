#!/usr/bin/env python3
"""
Sophia Squad CLI - Professional Multi-Agent Management System
Complete orchestration and monitoring for all three squad systems
"""

import click
import httpx
import json
import asyncio
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional, Dict, Any
import subprocess
import os
import sys

console = Console()

# Configuration
GATEWAY_URL = "http://localhost:8000"
SERVICES = {
    "aimlapi": {"port": 8090, "name": "AIMLAPI Squad"},
    "litellm": {"port": 8091, "name": "LiteLLM Squad"},
    "openrouter": {"port": 8092, "name": "OpenRouter Squad"},
    "gateway": {"port": 8000, "name": "Unified Gateway"},
    "redis": {"port": 6379, "name": "Redis Cache"},
    "mcp-memory": {"port": 8081, "name": "MCP Memory"},
    "mcp-filesystem": {"port": 8082, "name": "MCP Filesystem"},
    "mcp-git": {"port": 8084, "name": "MCP Git"}
}

class SophiaClient:
    """Client for interacting with Sophia services"""
    
    def __init__(self):
        self.gateway_url = GATEWAY_URL
        
    async def check_health(self) -> Dict:
        """Check health of all services"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.gateway_url}/health", timeout=5.0)
                return response.json() if response.status_code == 200 else {}
        except:
            return {}
    
    async def get_services(self) -> Dict:
        """Get service configurations"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.gateway_url}/services", timeout=5.0)
                return response.json() if response.status_code == 200 else {}
        except:
            return {}
    
    async def get_metrics(self) -> Dict:
        """Get system metrics"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.gateway_url}/metrics", timeout=5.0)
                return response.json() if response.status_code == 200 else {}
        except:
            return {}
    
    async def process_task(self, task: str, model: Optional[str] = None, requirements: Optional[Dict] = None) -> Dict:
        """Process a task through the unified gateway"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "task": task,
                    "model": model,
                    "requirements": requirements or {}
                }
                response = await client.post(
                    f"{self.gateway_url}/process",
                    json=payload,
                    timeout=30.0
                )
                return response.json() if response.status_code == 200 else {"error": response.text}
        except Exception as e:
            return {"error": str(e)}

client = SophiaClient()

@click.group()
@click.version_option(version="2.0.0", prog_name="Sophia Squad")
def cli():
    """Sophia Squad - Professional Multi-Agent Management System"""
    pass

@cli.command()
def status():
    """Show status of all services"""
    console.print(Panel.fit("🚀 [bold cyan]Sophia Squad Systems Status[/bold cyan]", border_style="cyan"))
    
    async def get_status():
        health = await client.check_health()
        services = await client.get_services()
        metrics = await client.get_metrics()
        
        # Create status table
        table = Table(title="Service Status", show_header=True, header_style="bold magenta")
        table.add_column("Service", style="cyan", width=20)
        table.add_column("Port", justify="center", width=8)
        table.add_column("Status", justify="center", width=12)
        table.add_column("CPU %", justify="right", width=8)
        table.add_column("Memory MB", justify="right", width=10)
        
        for service_key, service_info in SERVICES.items():
            # Get health status
            health_status = "❌ Down"
            if services:
                for svc_type, svc_data in services.items():
                    if service_info["port"] == svc_data.get("port"):
                        health_status = "✅ Running" if svc_data.get("healthy") else "❌ Down"
                        break
            
            # Get metrics
            cpu = "-"
            memory = "-"
            if metrics and "services" in metrics:
                for svc_type, svc_metrics in metrics["services"].items():
                    if service_key in svc_type.lower():
                        cpu = f"{svc_metrics.get('cpu_percent', 0):.1f}"
                        memory = f"{svc_metrics.get('memory_mb', 0):.1f}"
                        break
            
            table.add_row(
                service_info["name"],
                str(service_info["port"]),
                health_status,
                cpu,
                memory
            )
        
        console.print(table)
        
        # System metrics
        if metrics and "system" in metrics:
            sys_metrics = metrics["system"]
            console.print(f"\n[bold]System Resources:[/bold]")
            console.print(f"  CPU Usage: {sys_metrics.get('cpu_percent', 0):.1f}%")
            console.print(f"  Memory Usage: {sys_metrics.get('memory_percent', 0):.1f}%")
            console.print(f"  Available Memory: {sys_metrics.get('memory_available_gb', 0):.2f} GB")
    
    asyncio.run(get_status())

@cli.command()
@click.argument('service', type=click.Choice(['all', 'aimlapi', 'litellm', 'openrouter', 'gateway', 'mcp']))
def start(service):
    """Start services"""
    console.print(f"[cyan]Starting {service}...[/cyan]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        if service == "all":
            # Start all services
            tasks = [
                ("Starting Redis", "redis-server --daemonize yes"),
                ("Starting MCP servers", "cd ~/sophia-intel-ai && ./start_mcp_servers.sh"),
                ("Starting AIMLAPI Squad", "cd ~/sophia-intel-ai && ./sophia-squad/launch_complete.sh"),
                ("Starting LiteLLM Squad", "cd ~/sophia-intel-ai && LITELLM_PORT=8091 ./launch_unified_squad.sh start"),
                ("Starting OpenRouter Squad", "cd ~/sophia-intel-ai && ./launch_openrouter_squad.sh start"),
                ("Starting Unified Gateway", "cd ~/sophia-intel-ai && python3 sophia_unified_orchestrator.py &")
            ]
            
            for desc, cmd in tasks:
                task = progress.add_task(desc, total=1)
                result = subprocess.run(cmd, shell=True, capture_output=True)
                progress.update(task, completed=1)
                if result.returncode == 0:
                    console.print(f"  ✅ {desc}")
                else:
                    console.print(f"  ❌ {desc} - Failed")
        
        elif service == "gateway":
            subprocess.Popen(
                ["python3", "sophia_unified_orchestrator.py"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            console.print("✅ Unified Gateway started")
        
        else:
            # Start specific service
            commands = {
                "aimlapi": "cd sophia-squad && ./launch_complete.sh",
                "litellm": "LITELLM_PORT=8091 ./launch_unified_squad.sh start",
                "openrouter": "./launch_openrouter_squad.sh start",
                "mcp": "./start_mcp_servers.sh"
            }
            
            if service in commands:
                subprocess.run(commands[service], shell=True)
                console.print(f"✅ {service} started")

@cli.command()
@click.argument('service', type=click.Choice(['all', 'aimlapi', 'litellm', 'openrouter', 'gateway']))
def stop(service):
    """Stop services"""
    console.print(f"[yellow]Stopping {service}...[/yellow]")
    
    if service == "all":
        # Stop all services
        commands = [
            "pkill -f sophia_unified_orchestrator",
            "pkill -f openrouter_server",
            "pkill -f litellm_server",
            "pkill -f enhanced_aimlapi_server",
            "pkill -f 'mcp.*server'"
        ]
        for cmd in commands:
            subprocess.run(cmd, shell=True)
        console.print("✅ All services stopped")
    else:
        # Stop specific service
        commands = {
            "gateway": "pkill -f sophia_unified_orchestrator",
            "openrouter": "pkill -f openrouter_server",
            "litellm": "pkill -f litellm_server",
            "aimlapi": "pkill -f enhanced_aimlapi_server"
        }
        if service in commands:
            subprocess.run(commands[service], shell=True)
            console.print(f"✅ {service} stopped")

@cli.command()
@click.argument('task')
@click.option('--model', '-m', help='Specific model to use')
@click.option('--web-search', is_flag=True, help='Enable web search')
@click.option('--long-context', is_flag=True, help='Enable long context support')
@click.option('--cost-optimize', is_flag=True, help='Optimize for cost')
def ask(task, model, web_search, long_context, cost_optimize):
    """Process a task through the unified gateway"""
    console.print(f"[cyan]Processing task...[/cyan]")
    
    requirements = {}
    if web_search:
        requirements["web_search"] = True
    if long_context:
        requirements["long_context"] = True
    if cost_optimize:
        requirements["cost_optimization"] = True
    
    async def process():
        with console.status("[bold green]Thinking...") as status:
            result = await client.process_task(task, model, requirements)
            
            if "error" in result:
                console.print(f"[red]Error: {result['error']}[/red]")
            else:
                # Display result in a nice panel
                panel_content = f"""[bold]Service:[/bold] {result.get('service', 'unknown')}
[bold]Model:[/bold] {result.get('model', 'unknown')}
[bold]Cost:[/bold] ${result.get('cost', 0):.4f} 
[bold]Cached:[/bold] {'Yes' if result.get('cached') else 'No'}

[bold]Response:[/bold]
{result.get('response', 'No response')}"""
                
                console.print(Panel(panel_content, title="🤖 Response", border_style="green"))
    
    asyncio.run(process())

@cli.command()
def config():
    """Show configuration"""
    config_file = Path.home() / ".config" / "sophia" / "env"
    
    if config_file.exists():
        console.print(Panel.fit("📋 [bold cyan]Current Configuration[/bold cyan]", border_style="cyan"))
        
        # Parse and display config (hiding sensitive parts of keys)
        with open(config_file) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    if "KEY" in key or "TOKEN" in key:
                        # Mask sensitive values
                        if len(value) > 8:
                            value = value[:4] + "..." + value[-4:]
                    console.print(f"  {key} = {value}")
    else:
        console.print("[yellow]No configuration file found[/yellow]")

@cli.command()
def test():
    """Run system tests"""
    console.print(Panel.fit("🧪 [bold cyan]Running System Tests[/bold cyan]", border_style="cyan"))
    
    async def run_tests():
        # Test 1: Gateway Health
        console.print("\n[bold]Test 1: Gateway Health[/bold]")
        health = await client.check_health()
        if health:
            console.print("  ✅ Gateway is responsive")
        else:
            console.print("  ❌ Gateway not responding")
            return
        
        # Test 2: Service Discovery
        console.print("\n[bold]Test 2: Service Discovery[/bold]")
        services = await client.get_services()
        if services:
            console.print(f"  ✅ Found {len(services)} services")
        else:
            console.print("  ❌ Service discovery failed")
        
        # Test 3: Simple Task
        console.print("\n[bold]Test 3: Simple Task Processing[/bold]")
        result = await client.process_task("Say hello")
        if "error" not in result:
            console.print(f"  ✅ Task processed via {result.get('service')}")
        else:
            console.print(f"  ❌ Task failed: {result.get('error')}")
        
        # Test 4: Model-specific Request
        console.print("\n[bold]Test 4: Model-specific Request[/bold]")
        result = await client.process_task("Test", model="grok-4")
        if "error" not in result:
            console.print(f"  ✅ Routed to correct service: {result.get('service')}")
        else:
            console.print(f"  ⚠️  Model routing unavailable")
    
    asyncio.run(run_tests())

if __name__ == "__main__":
    cli()