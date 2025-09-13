#!/usr/bin/env python3
"""
Forge - Builder CLI for Agno v2 Stack
Single authoritative CLI for the Builder team
"""

import asyncio
import json
import click
import inspect
import os
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from builder_cli.lib.env import load_central_env
load_central_env()

from builder_cli.lib.agents import create_construction_team, create_data_team
from builder_cli.lib.router import ModelRouter
from builder_cli.lib.bridge import BridgeClient
from builder_cli.lib.mcp import MCPManager
from builder_cli.lib.platinum import PlanningSwarm, CodingSwarm, ReviewSwarm, save_artifact

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

                console.print("\n[green]✓[/green] Construction complete!")
                console.print(f"PR URL: {result.pr_url}")
                console.print(f"Files changed: {len(result.diffs)}")
                console.print(f"Tests added: {result.test_count}")

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

    table.add_row("ConstructionTeam", "collaborate", "Planner, Coder, Reviewer")
    table.add_row("DataEnhancementTeam", "coordinate", "Fetcher, Standardizer, Reconciler")

    console.print(table)


@swarm.group()
def platinum():
    """Platinum swarm: plan → code → review"""
    pass


@platinum.command("init")
@click.option("--task", "-t", required=True, help="Task description")
@click.option("--out", "-o", default="artifacts/platinum/plan.json", help="Where to save the plan JSON")
async def platinum_init(task: str, out: str):
    planner = PlanningSwarm()
    with console.status("Running planning swarm..."):
        plan = await planner.run(task)
    save_artifact(Path(out), plan)
    console.print(f"[green]✓[/green] Plan saved to {out}")


@platinum.command("plan")
@click.option("--task", "-t", required=True, help="Task description")
@click.option("--out", "-o", default="artifacts/platinum/plan.json", help="Where to save the plan JSON")
async def platinum_plan(task: str, out: str):
    await platinum_init.callback(task, out)  # type: ignore[attr-defined]


@platinum.command("code")
@click.option("--plan", "plan_path", default="artifacts/platinum/plan.json", help="Path to plan JSON")
@click.option("--out", "-o", default="artifacts/platinum/patches.json", help="Where to save patches JSON")
async def platinum_code(plan_path: str, out: str):
    # Load plan
    plan_data = json.loads(Path(plan_path).read_text())
    from builder_cli.lib.platinum import PlanSpec
    plan = PlanSpec(**plan_data)
    coder = CodingSwarm()
    with console.status("Generating coding blueprint and patches..."):
        blueprint = await coder.plan(plan)
        patches = await coder.code(plan, blueprint)
    save_artifact(Path(out), [p.model_dump() for p in patches])
    console.print(f"[green]✓[/green] Patches saved to {out}")


@platinum.command("review")
@click.option("--plan", "plan_path", default="artifacts/platinum/plan.json", help="Path to plan JSON")
@click.option("--patches", "patches_path", default="artifacts/platinum/patches.json", help="Path to patches JSON")
@click.option("--out", "-o", default="artifacts/platinum/review.json", help="Where to save review JSON")
async def platinum_review(plan_path: str, patches_path: str, out: str):
    plan_data = json.loads(Path(plan_path).read_text())
    from builder_cli.lib.platinum import PlanSpec, CodePatch
    plan = PlanSpec(**plan_data)
    patches_data = json.loads(Path(patches_path).read_text())
    patches = [CodePatch(**p) for p in patches_data]
    reviewer = ReviewSwarm()
    with console.status("Reviewing patches..."):
        report = await reviewer.run(plan, patches)
    save_artifact(Path(out), report)
    console.print(f"[green]✓[/green] Review report saved to {out}")


@platinum.command("run")
@click.option("--task", "-t", required=True, help="Task description")
@click.option("--out", "-o", default="artifacts/platinum", help="Artifacts directory")
async def platinum_run(task: str, out: str):
    base = Path(out)
    plan_path = base / "plan.json"
    patches_path = base / "patches.json"
    review_path = base / "review.json"
    base.mkdir(parents=True, exist_ok=True)
    # Plan
    planner = PlanningSwarm()
    with console.status("Planning..."):
        plan = await planner.run(task)
    save_artifact(plan_path, plan)
    # Code
    coder = CodingSwarm()
    with console.status("Coding..."):
        blueprint = await coder.plan(plan)
        patches = await coder.code(plan, blueprint)
    save_artifact(patches_path, [p.model_dump() for p in patches])
    # Review
    reviewer = ReviewSwarm()
    with console.status("Reviewing..."):
        report = await reviewer.run(plan, patches)
    save_artifact(review_path, report)
    console.print(f"[green]✓[/green] Completed. Artifacts in {base}")


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

    table = Table(title="Top-25 Weekly Models")
    table.add_column("#", style="dim")
    table.add_column("Model ID", style="cyan")
    table.add_column("Provider", style="magenta")
    table.add_column("Task Mapping", style="green")

    for i, model in enumerate(models, 1):
        model_id = model.id if hasattr(model, "id") else model["id"]
        task_type = router.get_task_type(model_id)
        provider = model.provider if hasattr(model, "provider") else model.get("provider", "-")
        table.add_row(str(i), model_id, provider, task_type)

    console.print(table)

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


@router.command()
@click.option("--verbose", is_flag=True, help="List per-model reasons for filtering")
async def report(verbose: bool):
    """Report router policy stats (banlist, caps, recency)."""
    router = ModelRouter()
    if verbose:
        with console.status("Analyzing models (verbose)..."):
            rows = router.analyze_verbose()
        table = Table(title="Router Policy (Verbose)")
        table.add_column("Model", style="cyan")
        table.add_column("Provider", style="magenta")
        table.add_column("Share", style="white")
        table.add_column("Banned", style="red")
        table.add_column("Missing Caps", style="yellow")
        table.add_column("Short Ctx", style="yellow")
        table.add_column("Stale", style="yellow")
        for r in rows:
            table.add_row(r["id"], r.get("provider", "-"), f"{r.get('share', 0):.3f}",
                          "yes" if r["banned"] else "no",
                          "yes" if r["missing_caps"] else "no",
                          "yes" if r["short_context"] else "no",
                          "yes" if r["stale"] else "no")
        console.print(table)
    else:
        with console.status("Analyzing models..."):
            stats = router.analyze()
        table = Table(title="Router Policy Report")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        for k in ["total", "banned", "missing_caps", "short_context", "stale"]:
            table.add_row(k.replace("_", " ").title(), str(stats.get(k, 0)))
        console.print(table)


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


@mcp.group()
def index():
    """Repository index operations (opt-in via INDEX_ENABLED=true)"""
    pass


@index.command("refresh")
@click.option("--path", "path", default=".", help="Repository root path")
async def index_refresh(path: str):
    if os.getenv("INDEX_ENABLED", "false").lower() not in ("1", "true", "yes"):
        console.print("[yellow]INDEX_ENABLED is not set; skipping indexing[/yellow]")
        raise SystemExit(0)
    from builder_cli.lib.indexer import RepoIndexer
    ix = RepoIndexer(Path(path).resolve())
    with console.status("Indexing repository..."):
        stats = ix.refresh()
    console.print(f"[green]✓[/green] Indexed files={stats.files} symbols={stats.symbols} deps={stats.deps}")


@index.command("status")
@click.option("--path", "path", default=".", help="Repository root path")
async def index_status(path: str):
    from builder_cli.lib.indexer import RepoIndexer
    ix = RepoIndexer(Path(path).resolve())
    stats = ix.status()
    table = Table(title="Repository Index Status")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="green")
    table.add_row("Files", str(stats.files))
    table.add_row("Symbols", str(stats.symbols))
    table.add_row("Deps", str(stats.deps))
    console.print(table)


@index.command("stats")
@click.option("--path", "path", default=".", help="Repository root path")
async def index_stats(path: str):
    # Alias of status for now
    await index_status.callback(path)  # type: ignore[attr-defined]


@cli.group()
def env():
    """Environment and configuration utilities"""
    pass


@env.command()
def doctor():
    """Validate required secrets and environment.

    Checks only for presence; values remain hidden.
    """
    required = [
        "OPENROUTER_API_KEY",
        "POSTGRES_URL",
        "REDIS_URL",
        "NEO4J_URI",
        "NEO4J_USER",
        "NEO4J_PASSWORD",
    ]
    optional = [
        "DASHSCOPE_API_KEY",
        "BRIGHTDATA_API_KEY",
        "SENTRY_DSN",
    ]
    table = Table(title="Environment Doctor")
    table.add_column("Variable", style="cyan")
    table.add_column("Present", style="green")
    import os
    for key in required:
        table.add_row(key, "yes" if os.getenv(key) else "no")
    for key in optional:
        table.add_row(f"(opt) {key}", "yes" if os.getenv(key) else "no")
    console.print(table)
    cfg_path = os.getenv("SOPHIA_ENV_PATH", "(not found)")
    perms_warn = os.getenv("SOPHIA_ENV_PERMS_WARNING")
    console.print(f"\nConfig path: {cfg_path}")
    if perms_warn:
        console.print(f"[yellow]Warning:[/yellow] central env file permissions are {perms_warn}; recommend 0600")


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
        plan_resp = await bridge.plan(task)

    console.print("\n[green]Plan Created:[/green]")
    console.print(json.dumps(plan_resp, indent=2))


@cli.command()
def approve():
    """Open approval dashboard"""
    import webbrowser
    dashboard_url = os.getenv("AGENT_UI_URL", "http://localhost:3000")
    console.print(f"Opening Agent UI at {dashboard_url}")
    webbrowser.open(dashboard_url)


if __name__ == "__main__":
    # Wrap async click callbacks so they run under asyncio
    def _wrap_async(group: click.Group) -> None:
        for name, cmd in getattr(group, "commands", {}).items():
            if hasattr(cmd, "callback") and inspect.iscoroutinefunction(cmd.callback):
                orig = cmd.callback

                def _runner(*args, __orig=orig, **kwargs):
                    return asyncio.run(__orig(*args, **kwargs))

                cmd.callback = _runner  # type: ignore[assignment]
            # Recurse into sub-groups
            if hasattr(cmd, "commands"):
                _wrap_async(cmd)  # type: ignore[arg-type]

    _wrap_async(cli)
    cli()
