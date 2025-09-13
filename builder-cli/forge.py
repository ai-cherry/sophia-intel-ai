#!/usr/bin/env python3
"""
Forge - Builder CLI for Agno v2 Stack
Single authoritative CLI for the Builder team
"""

import asyncio
import click
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from builder_cli.lib.agents import create_construction_team, create_data_team
from builder_cli.lib.router import ModelRouter
from builder_cli.lib.bridge import BridgeClient
from builder_cli.lib.mcp import MCPManager

console = Console()

@click.group()
@click.version_option(version="2.0.0")
def cli():
    """Forge - Builder CLI for Agno v2 Stack"""
    pass

@cli.group()
def swarm():
    """Manage agent swarms"""
    pass

@swarm.command()
@click.argument("team_name", type=click.Choice(["construction", "data"]))
@click.option("--task", "-t", required=True, help="Task description")
@click.option("--output", "-o", help="Output directory for artifacts")
async def run(team_name: str, task: str, output: Optional[str]):
    """Run a team swarm on a task"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task_id = progress.add_task(f"Running {team_name} team...", total=None)
        
        try:
            if team_name == "construction":
                team = await create_construction_team()
                result = await team.execute(task)
                
                # Display results
                console.print("\n[green]✓[/green] Construction complete!")
                console.print(f"PR URL: {result.pr_url}")
                console.print(f"Files changed: {len(result.diffs)}")
                console.print(f"Tests added: {result.test_count}")
                
                # Save artifacts
                if output:
                    output_path = Path(output)
                    output_path.mkdir(exist_ok=True)
                    for i, diff in enumerate(result.diffs):
                        (output_path / f"diff_{i}.patch").write_text(diff)
                        
            elif team_name == "data":
                team = await create_data_team()
                result = await team.execute(task)
                
                console.print("\n[green]✓[/green] Data enhancement complete!")
                console.print(f"Records processed: {result.record_count}")
                console.print(f"Lineage ID: {result.lineage_id}")
                
        except Exception as e:
            console.print(f"[red]✗[/red] Team execution failed: {e}")
            sys.exit(1)
        finally:
            progress.remove_task(task_id)

@swarm.command()
def list():
    """List available teams"""
    table = Table(title="Available Teams")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Agents", style="green")
    
    table.add_row(
        "ConstructionTeam",
        "collaborate",
        "Planner, Coder, Reviewer"
    )
    table.add_row(
        "DataEnhancementTeam",
        "coordinate",
        "Fetcher, Standardizer, Reconciler"
    )
    
    console.print(table)

@cli.group()
def router():
    """Model router management"""
    pass

@router.command()
async def check():
    """Verify Top-25 models and banlist"""
    router = ModelRouter()
    
    with console.status("Fetching Top-25 models..."):
        models = await router.fetch_top_models()
    
    console.print(f"[green]✓[/green] {len(models)} models loaded")
    
    # Display model table
    table = Table(title="Top-25 Weekly Models")
    table.add_column("#", style="dim")
    table.add_column("Model ID", style="cyan")
    table.add_column("Provider", style="magenta")
    table.add_column("Task Mapping", style="green")
    
    for i, model in enumerate(models, 1):
        task_type = router.get_task_type(model["id"])
        table.add_row(
            str(i),
            model["id"],
            model["provider"],
            task_type
        )
    
    console.print(table)
    
    # Verify banlist
    banned = router.check_banlist()
    if banned:
        console.print(f"\n[yellow]⚠[/yellow] {len(banned)} models in banlist rejected")

@router.command()
async def refresh():
    """Refresh model cache"""
    router = ModelRouter()
    
    with console.status("Refreshing model cache..."):
        await router.refresh_cache()
    
    console.print("[green]✓[/green] Model cache refreshed")

@cli.group()
def mcp():
    """MCP server management"""
    pass

@mcp.command()
@click.argument("server", type=click.Choice(["filesystem", "git", "memory", "all"]))
async def start(server: str):
    """Start MCP servers"""
    manager = MCPManager()
    
    servers_to_start = [server] if server != "all" else ["filesystem", "git", "memory"]
    
    for srv in servers_to_start:
        with console.status(f"Starting {srv} server..."):
            port = await manager.start_server(srv)
        console.print(f"[green]✓[/green] {srv} server started on port {port}")

@mcp.command()
async def status():
    """Check MCP server status"""
    manager = MCPManager()
    statuses = await manager.get_status()
    
    table = Table(title="MCP Server Status")
    table.add_column("Server", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Port", style="magenta")
    
    for srv, info in statuses.items():
        status = "[green]Running[/green]" if info["running"] else "[red]Stopped[/red]"
        table.add_row(srv, status, str(info.get("port", "-")))
    
    console.print(table)

@cli.command()
@click.option("--file", "-f", required=True, help="File to generate code for")
@click.option("--task", "-t", required=True, help="Task description")
async def codegen(file: str, task: str):
    """Generate code using Agno v2 agents"""
    bridge = BridgeClient()
    
    with console.status("Generating code..."):
        result = await bridge.codegen(file, task)
    
    console.print("\n[green]✓[/green] Code generated!")
    console.print(f"File: {result.file_path}")
    console.print("\nDiff preview:")
    console.print(result.diff)
    
    if click.confirm("\nApply changes?"):
        await bridge.apply(result)
        console.print("[green]✓[/green] Changes applied")

@cli.command()
@click.option("--pr", "-p", required=True, help="PR number or URL")
async def review(pr: str):
    """Review a pull request"""
    bridge = BridgeClient()
    
    with console.status(f"Reviewing PR {pr}..."):
        result = await bridge.review(pr)
    
    if result.approved:
        console.print(f"[green]✓ APPROVED[/green]")
    else:
        console.print(f"[red]✗ BLOCKED[/red]")
    
    console.print("\nFindings:")
    for finding in result.findings:
        console.print(f"  • {finding}")
    
    if result.fixes:
        console.print("\nRequired fixes:")
        for fix in result.fixes:
            console.print(f"  • {fix}")

@cli.command()
async def plan():
    """Enter planning mode for complex tasks"""
    console.print("[cyan]Planning Mode[/cyan]")
    console.print("Describe your task (Ctrl+D when done):\n")
    
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    task = "\n".join(lines)
    
    bridge = BridgeClient()
    with console.status("Creating plan..."):
        plan = await bridge.plan(task)
    
    console.print("\n[green]Plan Created:[/green]")
    console.print(plan.markdown)
    
    if click.confirm("\nProceed with implementation?"):
        with console.status("Implementing..."):
            result = await bridge.implement(plan)
        console.print(f"[green]✓[/green] Implementation complete: {result.pr_url}")

@cli.group()
def graph():
    """Neo4j graph operations"""
    pass

@graph.command()
@click.argument("query")
async def query(query: str):
    """Execute a Cypher query"""
    bridge = BridgeClient()
    
    with console.status("Executing query..."):
        results = await bridge.graph_query(query)
    
    console.print(f"[green]✓[/green] {len(results)} results found")
    
    for result in results:
        console.print(result)

@cli.command()
def approve():
    """Open approval dashboard"""
    import webbrowser
    dashboard_url = os.getenv("AGENT_UI_URL", "http://localhost:3000")
    console.print(f"Opening Agent UI at {dashboard_url}")
    webbrowser.open(dashboard_url)

if __name__ == "__main__":
    # Support both sync and async commands
    if len(sys.argv) > 1 and sys.argv[1] in ["codegen", "review", "plan"]:
        asyncio.run(cli())
    else:
        cli()