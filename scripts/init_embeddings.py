#!/usr/bin/env python3
"""
Codebase Embedding Initialization Script

Comprehensive script to generate embeddings for the entire codebase,
build hierarchical indices, create relationship graphs, and generate reports.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.embeddings import (
    AdaptiveChunker,
    ContentType,
    ContextualEmbeddings,
    EmbeddingType,
    HierarchicalIndex,
    MultiModalEmbeddings,
)

app = typer.Typer(help="Initialize embeddings for sophia-intel-ai codebase")
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("embedding_init.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class EmbeddingInitializer:
    """Main class for initializing codebase embeddings"""

    def __init__(
        self,
        repo_path: Path,
        output_dir: Path,
        embedding_provider: str = "openai",
        max_files: Optional[int] = None,
        exclude_patterns: Optional[List[str]] = None,
    ):
        """
        Initialize the embedding system

        Args:
            repo_path: Path to repository root
            output_dir: Output directory for embeddings and indices
            embedding_provider: Embedding provider to use
            max_files: Maximum number of files to process (for testing)
            exclude_patterns: File patterns to exclude
        """
        self.repo_path = Path(repo_path)
        self.output_dir = Path(output_dir)
        self.embedding_provider = embedding_provider
        self.max_files = max_files
        self.exclude_patterns = exclude_patterns or [
            "*.pyc",
            "*.pyo",
            "*.pyd",
            "__pycache__",
            ".git",
            ".pytest_cache",
            "*.log",
            "*.tmp",
            "node_modules",
            ".env",
            "*.lock",
        ]

        # Initialize components
        self.embedding_system = MultiModalEmbeddings(
            cache_dir=str(self.output_dir / "cache"), default_provider=embedding_provider
        )

        self.hierarchical_index = HierarchicalIndex(
            storage_dir=str(self.output_dir / "indices"),
            dimensions=(
                3072 if embedding_provider == "openai" else 1536
            ),  # text-embedding-3-large vs others
        )

        self.contextual_embeddings = ContextualEmbeddings(self.embedding_system)
        self.adaptive_chunker = AdaptiveChunker()

        # Statistics tracking
        self.stats = {
            "start_time": None,
            "end_time": None,
            "total_files": 0,
            "processed_files": 0,
            "skipped_files": 0,
            "error_files": 0,
            "total_chunks": 0,
            "total_embeddings": 0,
            "total_tokens": 0,
            "file_types": {},
            "errors": [],
        }

    def _should_process_file(self, file_path: Path) -> bool:
        """Check if file should be processed"""
        # Skip if file matches exclude patterns
        for pattern in self.exclude_patterns:
            if file_path.match(pattern):
                return False

        # Only process text-based files
        try:
            with open(file_path, encoding="utf-8") as f:
                f.read(1024)  # Try to read first 1KB
            return True
        except (UnicodeDecodeError, PermissionError):
            return False

    def _detect_file_type(self, file_path: Path) -> ContentType:
        """Detect file type for processing"""
        suffix = file_path.suffix.lower()

        code_extensions = {
            ".py",
            ".js",
            ".ts",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".hpp",
            ".go",
            ".rs",
            ".rb",
            ".php",
            ".cs",
            ".swift",
            ".kt",
        }

        doc_extensions = {".md", ".rst", ".txt", ".adoc", ".tex"}

        if suffix in code_extensions:
            return ContentType.CODE
        elif suffix in doc_extensions or file_path.name.lower() in [
            "readme",
            "changelog",
            "license",
        ]:
            return ContentType.DOCUMENTATION
        else:
            return ContentType.PLAIN_TEXT

    def _get_programming_language(self, file_path: Path) -> str:
        """Get programming language from file extension"""
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".cs": "csharp",
            ".swift": "swift",
            ".kt": "kotlin",
        }

        return extension_map.get(file_path.suffix.lower(), "text")

    async def discover_files(self) -> List[Path]:
        """Discover files to process in the repository"""
        console.print("[bold blue]Discovering files...[/bold blue]")

        files = []
        total_found = 0

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:

            task = progress.add_task("Scanning repository...", total=None)

            for file_path in self.repo_path.rglob("*"):
                if file_path.is_file():
                    total_found += 1

                    if self._should_process_file(file_path):
                        files.append(file_path)

                        # Update progress periodically
                        if len(files) % 100 == 0:
                            progress.update(
                                task, description=f"Found {len(files)} processable files"
                            )

                    # Limit for testing
                    if self.max_files and len(files) >= self.max_files:
                        break

        self.stats["total_files"] = len(files)

        # Display summary
        table = Table(title="File Discovery Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")

        table.add_row("Total files found", str(total_found))
        table.add_row("Files to process", str(len(files)))
        table.add_row("Excluded files", str(total_found - len(files)))

        console.print(table)

        return files

    async def process_files(self, files: List[Path]) -> Dict[str, str]:
        """Read and prepare file contents for processing"""
        console.print(f"\n[bold blue]Reading {len(files)} files...[/bold blue]")

        file_contents = {}

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:

            task = progress.add_task("Reading files...", total=len(files))

            for file_path in files:
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()

                    # Use relative path as key
                    relative_path = str(file_path.relative_to(self.repo_path))
                    file_contents[relative_path] = content

                    # Track file type statistics
                    file_type = self._detect_file_type(file_path)
                    self.stats["file_types"][file_type.value] = (
                        self.stats["file_types"].get(file_type.value, 0) + 1
                    )

                    self.stats["processed_files"] += 1

                except Exception as e:
                    logger.error(f"Error reading {file_path}: {e}")
                    self.stats["error_files"] += 1
                    self.stats["errors"].append(
                        {"file": str(file_path), "error": str(e), "stage": "file_reading"}
                    )

                progress.advance(task)

        console.print(f"[green]Successfully read {len(file_contents)} files[/green]")
        return file_contents

    async def generate_chunks(self, file_contents: Dict[str, str]) -> Dict[str, List]:
        """Generate chunks for all files"""
        console.print("\n[bold blue]Generating content chunks...[/bold blue]")

        all_chunks = {}
        total_chunks = 0
        total_tokens = 0

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:

            task = progress.add_task("Chunking files...", total=len(file_contents))

            for file_path, content in file_contents.items():
                try:
                    # Detect content type
                    path_obj = Path(file_path)
                    content_type = self._detect_file_type(path_obj)

                    # Configure chunker for code files
                    if content_type == ContentType.CODE:
                        language = self._get_programming_language(path_obj)
                        chunker = self.adaptive_chunker.code_chunker
                        chunker.language = language
                        chunks = chunker.create_hierarchical_chunks(content, file_path)

                        # Flatten hierarchical chunks
                        file_chunks = []
                        for level, level_chunks in chunks.items():
                            file_chunks.extend(level_chunks)
                    else:
                        # Use adaptive chunker for non-code content
                        file_chunks = self.adaptive_chunker.chunk_content(
                            content, file_path, content_type
                        )

                    all_chunks[file_path] = file_chunks
                    total_chunks += len(file_chunks)
                    total_tokens += sum(chunk.metadata.token_count for chunk in file_chunks)

                except Exception as e:
                    logger.error(f"Error chunking {file_path}: {e}")
                    self.stats["errors"].append(
                        {"file": file_path, "error": str(e), "stage": "chunking"}
                    )

                progress.advance(task)

        self.stats["total_chunks"] = total_chunks
        self.stats["total_tokens"] = total_tokens

        console.print(f"[green]Generated {total_chunks:,} chunks ({total_tokens:,} tokens)[/green]")
        return all_chunks

    async def generate_embeddings(self, all_chunks: Dict[str, List]) -> Dict[str, Any]:
        """Generate embeddings for all chunks"""
        console.print("\n[bold blue]Generating embeddings...[/bold blue]")

        all_embeddings = {}
        total_embedded = 0

        # Flatten all chunks for batch processing
        flat_chunks = []
        for file_path, chunks in all_chunks.items():
            for chunk in chunks:
                flat_chunks.append((file_path, chunk))

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:

            task = progress.add_task("Generating embeddings...", total=len(flat_chunks))

            # Process in batches for efficiency
            batch_size = 20  # Adjust based on API rate limits

            for i in range(0, len(flat_chunks), batch_size):
                batch_chunks = flat_chunks[i : i + batch_size]

                try:
                    # Prepare batch data
                    contents = [chunk.content for _, chunk in batch_chunks]
                    embedding_types = [
                        (
                            EmbeddingType.CODE
                            if chunk.metadata.content_type == ContentType.CODE
                            else EmbeddingType.SEMANTIC
                        )
                        for _, chunk in batch_chunks
                    ]

                    # Generate batch embeddings
                    batch_results = await self.embedding_system.generate_batch_embeddings(
                        contents, embedding_types
                    )

                    # Store results
                    for (file_path, chunk), (vector, metadata) in zip(batch_chunks, batch_results):
                        if file_path not in all_embeddings:
                            all_embeddings[file_path] = []

                        all_embeddings[file_path].append(
                            {"chunk": chunk, "vector": vector, "metadata": metadata}
                        )

                        total_embedded += 1

                    # Update progress
                    for _ in batch_chunks:
                        progress.advance(task)

                    # Small delay to respect rate limits
                    await asyncio.sleep(0.1)

                except Exception as e:
                    logger.error(f"Error generating embeddings for batch {i}: {e}")
                    self.stats["errors"].append(
                        {"batch": i, "error": str(e), "stage": "embedding_generation"}
                    )

                    # Skip failed chunks in progress
                    for _ in batch_chunks:
                        progress.advance(task)

        self.stats["total_embeddings"] = total_embedded

        console.print(f"[green]Generated {total_embedded:,} embeddings[/green]")
        return all_embeddings

    async def build_hierarchical_index(self, all_embeddings: Dict[str, Any]):
        """Build hierarchical FAISS index"""
        console.print("\n[bold blue]Building hierarchical index...[/bold blue]")

        total_indexed = 0

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:

            # Count total embeddings
            total_embeddings = sum(len(embeddings) for embeddings in all_embeddings.values())
            task = progress.add_task("Building index...", total=total_embeddings)

            for file_path, embeddings in all_embeddings.items():
                batch_data = []

                for embedding_data in embeddings:
                    chunk = embedding_data["chunk"]
                    vector = embedding_data["vector"]
                    embedding_metadata = embedding_data["metadata"]

                    # Create unique embedding ID
                    embedding_id = f"{file_path}:{chunk.metadata.chunk_id}"

                    batch_data.append((embedding_id, vector, embedding_metadata))

                if batch_data:
                    # Add batch to hierarchical index
                    added_count = self.hierarchical_index.add_batch_embeddings(batch_data)
                    total_indexed += added_count

                    for _ in range(len(batch_data)):
                        progress.advance(task)

        # Save index to disk
        self.hierarchical_index.save_indices()

        console.print(f"[green]Indexed {total_indexed:,} embeddings[/green]")

    async def build_contextual_graph(self, file_contents: Dict[str, str]) -> Dict[str, Any]:
        """Build contextual relationship graph"""
        console.print("\n[bold blue]Building contextual relationship graph...[/bold blue]")

        # Filter to code files only for graph analysis
        code_contents = {}
        for file_path, content in file_contents.items():
            if self._detect_file_type(Path(file_path)) == ContentType.CODE:
                code_contents[file_path] = content

        console.print(f"Analyzing {len(code_contents)} code files for relationships...")

        # Build contextual index
        contextual_data = await self.contextual_embeddings.build_contextual_index(code_contents)

        # Export graph for visualization
        graph_export_path = self.output_dir / "dependency_graph.json"
        self.contextual_embeddings.export_graph(str(graph_export_path))

        console.print(
            f"[green]Built contextual graph with {len(contextual_data['embeddings'])} nodes[/green]"
        )
        console.print(f"[green]Exported graph to {graph_export_path}[/green]")

        return contextual_data

    def generate_report(self, contextual_data: Dict[str, Any]):
        """Generate comprehensive embedding report"""
        console.print("\n[bold blue]Generating embedding report...[/bold blue]")

        # Calculate final statistics
        self.stats["end_time"] = datetime.now()
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        # Get system stats
        embedding_stats = self.embedding_system.get_stats()
        index_stats = self.hierarchical_index.get_stats()

        # Create comprehensive report
        report = {
            "generation_info": {
                "start_time": self.stats["start_time"].isoformat(),
                "end_time": self.stats["end_time"].isoformat(),
                "duration_seconds": duration,
                "embedding_provider": self.embedding_provider,
            },
            "file_processing": {
                "total_files": self.stats["total_files"],
                "processed_files": self.stats["processed_files"],
                "error_files": self.stats["error_files"],
                "file_types": self.stats["file_types"],
            },
            "chunking": {
                "total_chunks": self.stats["total_chunks"],
                "total_tokens": self.stats["total_tokens"],
                "average_tokens_per_chunk": self.stats["total_tokens"]
                / max(self.stats["total_chunks"], 1),
            },
            "embeddings": {
                "total_embeddings": self.stats["total_embeddings"],
                "embedding_stats": embedding_stats,
            },
            "indexing": {
                "index_stats": index_stats,
            },
            "contextual_analysis": contextual_data.get("stats", {}),
            "errors": self.stats["errors"][:10],  # Include first 10 errors
        }

        # Save report
        report_path = self.output_dir / "embedding_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        # Display summary
        self._display_summary_report(report, duration)

        console.print(f"\n[green]Full report saved to: {report_path}[/green]")

    def _display_summary_report(self, report: Dict[str, Any], duration: float):
        """Display summary report in console"""
        console.print(
            Panel.fit(
                f"[bold green]Sophia AI Embedding Generation Complete![/bold green]\n\n"
                f"Duration: {duration:.1f} seconds\n"
                f"Files processed: {report['file_processing']['processed_files']:,}\n"
                f"Chunks generated: {report['chunking']['total_chunks']:,}\n"
                f"Embeddings created: {report['embeddings']['total_embeddings']:,}\n"
                f"Index size: {report['indexing']['index_stats']['total_vectors']:,} vectors\n"
                f"Cache hits: {report['embeddings']['embedding_stats']['cache_hits']:,}\n"
                f"Contextual nodes: {len(report['contextual_analysis'].get('node_type_distribution', {}))}"
            )
        )

        # File type breakdown
        if report["file_processing"]["file_types"]:
            table = Table(title="File Type Breakdown")
            table.add_column("Type", style="cyan")
            table.add_column("Count", style="green")

            for file_type, count in report["file_processing"]["file_types"].items():
                table.add_row(file_type.title(), str(count))

            console.print(table)

        # Display errors if any
        if report["errors"]:
            console.print(
                f"\n[yellow]Warning: {len(report['errors'])} errors occurred during processing[/yellow]"
            )
            console.print("Check the full report for error details.")

    async def run_full_initialization(self) -> bool:
        """Run complete embedding initialization process"""
        try:
            self.stats["start_time"] = datetime.now()

            # Create output directory
            self.output_dir.mkdir(parents=True, exist_ok=True)

            console.print(
                Panel.fit(
                    f"[bold blue]Sophia AI Embedding Initialization[/bold blue]\n\n"
                    f"Repository: {self.repo_path}\n"
                    f"Output Directory: {self.output_dir}\n"
                    f"Embedding Provider: {self.embedding_provider}\n"
                    f"Max Files: {self.max_files or 'No limit'}"
                )
            )

            # Step 1: Discover files
            files = await self.discover_files()
            if not files:
                console.print("[red]No files found to process![/red]")
                return False

            # Step 2: Process files
            file_contents = await self.process_files(files)
            if not file_contents:
                console.print("[red]No file contents could be read![/red]")
                return False

            # Step 3: Generate chunks
            all_chunks = await self.generate_chunks(file_contents)

            # Step 4: Generate embeddings
            all_embeddings = await self.generate_embeddings(all_chunks)

            # Step 5: Build hierarchical index
            await self.build_hierarchical_index(all_embeddings)

            # Step 6: Build contextual graph
            contextual_data = await self.build_contextual_graph(file_contents)

            # Step 7: Generate report
            self.generate_report(contextual_data)

            console.print(
                "\n[bold green]Embedding initialization completed successfully![/bold green]"
            )
            return True

        except Exception as e:
            logger.error(f"Fatal error during initialization: {e}")
            console.print(f"[red]Fatal error: {e}[/red]")
            return False


@app.command()
def init(
    repo_path: str = typer.Argument(".", help="Path to repository root"),
    output_dir: str = typer.Option("data/embeddings", help="Output directory for embeddings"),
    provider: str = typer.Option("openai", help="Embedding provider (openai, cohere, huggingface)"),
    max_files: Optional[int] = typer.Option(None, help="Maximum files to process (for testing)"),
    exclude_patterns: Optional[str] = typer.Option(None, help="Comma-separated exclude patterns"),
):
    """Initialize embeddings for the sophia-intel-ai codebase"""

    # Parse exclude patterns
    exclude_list = None
    if exclude_patterns:
        exclude_list = [pattern.strip() for pattern in exclude_patterns.split(",")]

    # Create initializer
    initializer = EmbeddingInitializer(
        repo_path=Path(repo_path),
        output_dir=Path(output_dir),
        embedding_provider=provider,
        max_files=max_files,
        exclude_patterns=exclude_list,
    )

    # Run initialization
    success = asyncio.run(initializer.run_full_initialization())

    if not success:
        typer.Exit(1)


@app.command()
def health_check(provider: str = typer.Option("openai", help="Embedding provider to check")):
    """Check health of embedding providers"""

    async def check_health():
        embedding_system = MultiModalEmbeddings(default_provider=provider)
        results = await embedding_system.health_check()

        console.print(Panel("[bold blue]Health Check Results[/bold blue]"))

        table = Table(title="Provider Status")
        table.add_column("Provider", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Error", style="red")

        for provider_name, status in results["providers"].items():
            status_color = "green" if status["status"] == "healthy" else "red"
            table.add_row(
                provider_name,
                f"[{status_color}]{status['status'].upper()}[/{status_color}]",
                status.get("error", ""),
            )

        console.print(table)
        console.print(f"\nOverall Status: {results['overall_status'].upper()}")

    asyncio.run(check_health())


@app.command()
def stats(output_dir: str = typer.Option("data/embeddings", help="Embeddings output directory")):
    """Show statistics for existing embeddings"""

    output_path = Path(output_dir)

    # Check if embeddings exist
    report_file = output_path / "embedding_report.json"
    if not report_file.exists():
        console.print(f"[red]No embedding report found at {report_file}[/red]")
        console.print("Run 'init' command first to generate embeddings.")
        raise typer.Exit(1)

    # Load and display report
    with open(report_file) as f:
        report = json.load(f)

    console.print(Panel("[bold blue]Embedding Statistics[/bold blue]"))

    # Basic stats
    console.print(f"Generated: {report['generation_info']['start_time']}")
    console.print(f"Duration: {report['generation_info']['duration_seconds']:.1f} seconds")
    console.print(f"Provider: {report['generation_info']['embedding_provider']}")

    # Processing stats
    proc_stats = report["file_processing"]
    console.print(f"\nFiles processed: {proc_stats['processed_files']:,}")
    console.print(f"Chunks generated: {report['chunking']['total_chunks']:,}")
    console.print(f"Embeddings created: {report['embeddings']['total_embeddings']:,}")

    # File types
    if proc_stats["file_types"]:
        console.print("\nFile Types:")
        for file_type, count in proc_stats["file_types"].items():
            console.print(f"  {file_type}: {count}")


if __name__ == "__main__":
    app()
