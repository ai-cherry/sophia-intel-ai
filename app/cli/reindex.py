"""
Enhanced CLI tool for incremental reindexing with change detection.
Usage: python -m app.cli.reindex [options]
"""

import asyncio
import os

import click

from app.memory.embed_router import DIM_A, DIM_B
from app.memory.embed_router import clear_cache as clear_embed_cache
from app.memory.incremental_indexer import IncrementalIndexer, IndexStateManager
from app.memory.index_weaviate import ensure_schema


@click.command()
@click.option(
    '--root', '-r',
    default='.',
    help='Root directory to index (default: current directory)'
)
@click.option(
    '--include', '-i',
    multiple=True,
    help='File patterns to include (e.g., "*.py", "*.ts")'
)
@click.option(
    '--exclude', '-e',
    multiple=True,
    help='Patterns to exclude (e.g., "*test*", "*.min.js")'
)
@click.option(
    '--clear-cache', '-c',
    is_flag=True,
    help='Clear embedding cache before indexing'
)
@click.option(
    '--force', '-f',
    is_flag=True,
    help='Force re-indexing even if files are unchanged'
)
@click.option(
    '--stats', '-s',
    is_flag=True,
    help='Show index statistics'
)
@click.option(
    '--batch-size', '-b',
    default=20,
    help='Batch size for indexing (default: 20)'
)
@click.option(
    '--priority', '-p',
    type=click.Choice(['high', 'medium', 'low']),
    help='Override priority for all chunks'
)
def reindex(
    root: str,
    include: tuple,
    exclude: tuple,
    clear_cache: bool,
    batch_size: int,
    priority: str | None,
    force: bool,
    stats: bool
):
    """Incrementally reindex source code with change detection."""

    # Show stats if requested
    if stats:
        state_manager = IndexStateManager()
        stats_data = state_manager.get_stats()
        click.echo("\n📊 Index Statistics:")
        click.echo(f"  Files indexed: {stats_data['files_indexed']}")
        click.echo(f"  Chunks indexed: {stats_data['chunks_indexed']}")
        click.echo(f"  Total size: {stats_data['total_size_mb']:.2f} MB")
        return

    # Clear cache if requested
    if clear_cache:
        click.echo("🧹 Clearing embedding cache...")
        clear_embed_cache()

    # Ensure collections exist
    click.echo("📦 Ensuring Weaviate collections exist...")
    collection_a = os.getenv("WEAVIATE_COLLECTION_A", "CodeChunk_A")
    collection_b = os.getenv("WEAVIATE_COLLECTION_B", "CodeChunk_B")
    ensure_schema(collection_a, DIM_A)
    ensure_schema(collection_b, DIM_B)

    # Initialize incremental indexer
    indexer = IncrementalIndexer(batch_size=batch_size)

    click.echo(f"🔍 Scanning directory: {root}")
    click.echo(f"  Force re-index: {force}")
    click.echo(f"  Priority: {priority or 'auto'}")

    # Run incremental indexing
    async def run_indexing():
        return await indexer.index_directory(
            root_dir=root,
            include_patterns=list(include) if include else None,
            exclude_patterns=list(exclude) if exclude else None,
            priority=priority,
            force=force
        )

    stats_result = asyncio.run(run_indexing())

    # Report results
    click.echo("\n✅ Indexing Complete:")
    if 'summary' in stats_result:
        summary = stats_result['summary']
        click.echo(f"  📁 Total files: {summary['total_files']}")
        click.echo(f"  ✨ New/Updated: {summary['indexed'] + summary['updated']}")
        click.echo(f"  ⏭️  Skipped (unchanged): {summary['skipped']}")

    click.echo(f"  📝 Chunks created: {stats_result.get('chunks_created', 0)}")
    click.echo(f"  ♻️  Chunks reused: {stats_result.get('chunks_reused', 0)}")

    if stats_result.get('errors'):
        errors = stats_result['errors']
        click.echo(f"\n⚠️  {len(errors)} errors occurred:")
        for error_info in errors[:5]:
            click.echo(f"  - {error_info['path']}: {error_info['error']}")
        if len(errors) > 5:
            click.echo(f"  ... and {len(errors) - 5} more")

    # Performance summary
    total_processed = stats_result.get('files_processed', 0) + stats_result.get('files_updated', 0)
    if total_processed > 0:
        savings = (stats_result.get('files_skipped', 0) / (total_processed + stats_result.get('files_skipped', 0))) * 100
        click.echo(f"\n⚡ Performance: {savings:.1f}% files skipped due to incremental indexing")

# Remove the old _index_batch function as it's now handled by IncrementalIndexer

if __name__ == "__main__":
    reindex()
