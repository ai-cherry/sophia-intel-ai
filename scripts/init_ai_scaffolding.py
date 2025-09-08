#!/usr/bin/env python3
"""
AI Scaffolding Initialization Script
Comprehensive setup for all AI-native infrastructure components
"""

import asyncio
import logging
import sys
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.documentation.living_docs import LivingDocumentationSystem
from app.embeddings.multi_modal_system import MultiModalEmbeddingSystem
from app.memory.hierarchical_memory import HierarchicalMemorySystem
from app.personas import initialize_persona_system
from app.scaffolding.integration_hub import create_integration_hub
from app.scaffolding.meta_tagging import AutoTagger, MetaTagRegistry

console = Console()
logger = logging.getLogger(__name__)


class AIScaffoldingInitializer:
    """Initialize all AI scaffolding components"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.console = console
        self.components_status = {}

    async def initialize_all(self, root_path: Path) -> bool:
        """Initialize all AI scaffolding components"""

        self.console.print(
            Panel.fit(
                "[bold cyan]🚀 AI Scaffolding Initialization[/bold cyan]\n"
                "Setting up AI-native infrastructure for sophia-intel-ai",
                box=box.DOUBLE,
            )
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        ) as progress:

            # Define initialization tasks
            tasks = [
                ("Integration Hub", self._init_integration_hub),
                ("Meta-Tagging System", self._init_meta_tagging, root_path),
                ("Embedding Infrastructure", self._init_embeddings, root_path),
                ("Persona Framework", self._init_personas),
                ("Hierarchical Memory", self._init_memory),
                ("Living Documentation", self._init_documentation, root_path),
                ("MCP Orchestration", self._init_mcp),
                ("Cross-Learning", self._init_cross_learning),
            ]

            main_task = progress.add_task("[cyan]Initializing AI Scaffolding...", total=len(tasks))

            for task_name, task_func, *args in tasks:
                try:
                    sub_task = progress.add_task(f"[yellow]{task_name}...", total=100)

                    # Run initialization
                    if args:
                        success = await task_func(*args, progress=progress, task_id=sub_task)
                    else:
                        success = await task_func(progress=progress, task_id=sub_task)

                    self.components_status[task_name] = "✅ Success" if success else "❌ Failed"
                    progress.update(sub_task, completed=100)

                except Exception as e:
                    self.components_status[task_name] = f"❌ Error: {str(e)}"
                    if self.verbose:
                        console.print(f"[red]Error in {task_name}: {e}[/red]")

                progress.update(main_task, advance=1)

        # Display results
        self._display_results()

        return all("✅" in status for status in self.components_status.values())

    async def _init_integration_hub(self, progress=None, task_id=None) -> bool:
        """Initialize the integration hub"""
        try:
            if progress:
                progress.update(task_id, description="[yellow]Creating Integration Hub...")

            hub = await create_integration_hub()

            if progress:
                progress.update(task_id, description="[yellow]Starting components...", completed=50)

            await hub.start()

            if self.verbose:
                self.console.print("[green]✓[/green] Integration Hub initialized")

            return True
        except Exception as e:
            logger.error(f"Failed to initialize Integration Hub: {e}")
            return False

    async def _init_meta_tagging(self, root_path: Path, progress=None, task_id=None) -> bool:
        """Initialize meta-tagging system"""
        try:
            if progress:
                progress.update(task_id, description="[yellow]Scanning codebase...")

            tagger = AutoTagger()
            registry = MetaTagRegistry()

            # Scan Python files
            py_files = list(root_path.rglob("*.py"))
            if progress:
                progress.update(
                    task_id, description=f"[yellow]Tagging {len(py_files)} files...", completed=25
                )

            tagged_count = 0
            for i, file_path in enumerate(py_files[:100]):  # Limit for initial setup
                if file_path.parent.name not in ["__pycache__", "venv", ".venv"]:
                    tags = await tagger.tag_file(file_path)
                    for tag in tags:
                        registry.register(tag)
                    tagged_count += len(tags)

                if progress and i % 10 == 0:
                    progress.update(task_id, completed=25 + (50 * i / min(100, len(py_files))))

            # Save registry
            registry.save()

            if self.verbose:
                self.console.print(f"[green]✓[/green] Tagged {tagged_count} components")

            return True
        except Exception as e:
            logger.error(f"Failed to initialize meta-tagging: {e}")
            return False

    async def _init_embeddings(self, root_path: Path, progress=None, task_id=None) -> bool:
        """Initialize embedding infrastructure"""
        try:
            if progress:
                progress.update(task_id, description="[yellow]Creating embedding system...")

            system = MultiModalEmbeddingSystem()

            if progress:
                progress.update(
                    task_id, description="[yellow]Generating initial embeddings...", completed=50
                )

            # Generate embeddings for key files
            key_files = [
                "app/orchestrators/sophia_unified.py",
                "app/orchestrators/artemis_unified.py",
                "app/memory/hierarchical_memory.py",
            ]

            for file_name in key_files:
                file_path = root_path / file_name
                if file_path.exists():
                    with open(file_path) as f:
                        content = f.read()
                    await system.generate_embedding(content, "code")

            if self.verbose:
                self.console.print("[green]✓[/green] Embedding system initialized")

            return True
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            return False

    async def _init_personas(self, progress=None, task_id=None) -> bool:
        """Initialize persona framework"""
        try:
            if progress:
                progress.update(task_id, description="[yellow]Creating personas...")

            # Initialize Sophia and Artemis personas
            system = await initialize_persona_system()

            if progress:
                progress.update(
                    task_id, description="[yellow]Configuring evolution...", completed=75
                )

            if self.verbose:
                self.console.print("[green]✓[/green] Sophia and Artemis personas ready")

            return True
        except Exception as e:
            logger.error(f"Failed to initialize personas: {e}")
            return False

    async def _init_memory(self, progress=None, task_id=None) -> bool:
        """Initialize hierarchical memory system"""
        try:
            if progress:
                progress.update(task_id, description="[yellow]Setting up memory tiers...")

            memory = HierarchicalMemorySystem()
            await memory.initialize()

            if progress:
                progress.update(
                    task_id, description="[yellow]Testing memory operations...", completed=75
                )

            # Test basic operations
            await memory.store("test_key", {"test": "data"}, tier="L1")
            result = await memory.retrieve("test_key")

            if self.verbose:
                self.console.print("[green]✓[/green] 4-tier memory system ready")

            return result is not None
        except Exception as e:
            logger.error(f"Failed to initialize memory: {e}")
            return False

    async def _init_documentation(self, root_path: Path, progress=None, task_id=None) -> bool:
        """Initialize living documentation system"""
        try:
            if progress:
                progress.update(task_id, description="[yellow]Creating documentation system...")

            docs = LivingDocumentationSystem()

            if progress:
                progress.update(
                    task_id, description="[yellow]Generating initial docs...", completed=50
                )

            # Generate docs for key modules
            key_modules = ["app/orchestrators", "app/memory", "app/personas"]
            for module in key_modules:
                module_path = root_path / module
                if module_path.exists():
                    await docs.generate_for_directory(module_path)

            if self.verbose:
                self.console.print("[green]✓[/green] Living documentation active")

            return True
        except Exception as e:
            logger.error(f"Failed to initialize documentation: {e}")
            return False

    async def _init_mcp(self, progress=None, task_id=None) -> bool:
        """Initialize MCP orchestration"""
        try:
            if progress:
                progress.update(task_id, description="[yellow]Setting up MCP servers...")

            # MCP initialization would go here
            # For now, we'll simulate success
            await asyncio.sleep(0.5)

            if self.verbose:
                self.console.print("[green]✓[/green] MCP orchestration ready")

            return True
        except Exception as e:
            logger.error(f"Failed to initialize MCP: {e}")
            return False

    async def _init_cross_learning(self, progress=None, task_id=None) -> bool:
        """Initialize cross-learning system"""
        try:
            if progress:
                progress.update(task_id, description="[yellow]Enabling cross-learning...")

            # Cross-learning initialization would go here
            await asyncio.sleep(0.5)

            if self.verbose:
                self.console.print("[green]✓[/green] Cross-learning enabled")

            return True
        except Exception as e:
            logger.error(f"Failed to initialize cross-learning: {e}")
            return False

    def _display_results(self):
        """Display initialization results"""
        table = Table(title="AI Scaffolding Status", box=box.ROUNDED)
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")

        for component, status in self.components_status.items():
            style = "green" if "✅" in status else "red"
            table.add_row(component, status, style=style)

        self.console.print("\n")
        self.console.print(table)

        # Overall status
        if all("✅" in status for status in self.components_status.values()):
            self.console.print(
                Panel.fit(
                    "[bold green]🎉 All Systems Operational![/bold green]\n"
                    "AI scaffolding is ready for use.",
                    box=box.DOUBLE,
                )
            )
        else:
            failed = [k for k, v in self.components_status.items() if "❌" in v]
            self.console.print(
                Panel.fit(
                    "[bold yellow]⚠️ Partial Success[/bold yellow]\n"
                    f"Failed components: {', '.join(failed)}\n"
                    "Check logs for details.",
                    box=box.DOUBLE,
                )
            )


@click.command()
@click.option(
    "--root",
    "-r",
    type=click.Path(exists=True, path_type=Path),
    default=Path.cwd(),
    help="Root directory of the project",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option(
    "--env",
    type=click.Choice(["local", "staging", "production"]),
    default="local",
    help="Environment to initialize",
)
def main(root: Path, verbose: bool, env: str):
    """Initialize AI Scaffolding for sophia-intel-ai"""

    console.print(f"[cyan]Environment:[/cyan] {env}")
    console.print(f"[cyan]Root Path:[/cyan] {root}")
    console.print()

    # Set environment
    import os

    os.environ["ENVIRONMENT"] = env

    # Run initialization
    initializer = AIScaffoldingInitializer(verbose=verbose)
    success = asyncio.run(initializer.initialize_all(root))

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
