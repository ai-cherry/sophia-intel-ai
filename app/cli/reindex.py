"""
CLI tool for reindexing source code into Weaviate.
Usage: python -m app.cli.reindex [options]
"""

import asyncio
import click
from pathlib import Path
from typing import List, Optional
from tqdm import tqdm
from app.memory.chunking import discover_source_files, produce_chunks_for_index
from app.memory.index_weaviate import upsert_chunks_dual, ensure_schema
from app.memory.embed_router import clear_cache, DIM_A, DIM_B
import os

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
    priority: Optional[str]
):
    """Reindex source code into Weaviate with dual-tier embeddings."""
    
    # Clear cache if requested
    if clear_cache:
        click.echo("🧹 Clearing embedding cache...")
        clear_cache()
    
    # Ensure collections exist
    click.echo("📦 Ensuring Weaviate collections exist...")
    collection_a = os.getenv("WEAVIATE_COLLECTION_A", "CodeChunk_A")
    collection_b = os.getenv("WEAVIATE_COLLECTION_B", "CodeChunk_B")
    ensure_schema(collection_a, DIM_A)
    ensure_schema(collection_b, DIM_B)
    
    # Discover files
    click.echo(f"🔍 Discovering source files in {root}...")
    files = discover_source_files(
        root_dir=root,
        include_patterns=list(include) if include else None,
        exclude_patterns=list(exclude) if exclude else None
    )
    
    if not files:
        click.echo("❌ No files found matching criteria")
        return
    
    click.echo(f"📂 Found {len(files)} files to index")
    
    # Process files in batches
    total_chunks = 0
    tier_a_count = 0
    tier_b_count = 0
    errors = []
    
    with tqdm(total=len(files), desc="Indexing files") as pbar:
        batch_ids = []
        batch_texts = []
        batch_payloads = []
        
        for filepath in files:
            try:
                # Generate chunks for this file
                ids, texts, payloads = produce_chunks_for_index(
                    filepath=filepath,
                    priority=priority
                )
                
                # Add to batch
                batch_ids.extend(ids)
                batch_texts.extend(texts)
                batch_payloads.extend(payloads)
                
                # Process batch if it's full
                if len(batch_ids) >= batch_size:
                    asyncio.run(_index_batch(
                        batch_ids, batch_texts, batch_payloads
                    ))
                    
                    # Count tier distribution
                    for payload in batch_payloads:
                        if payload.get("priority") == "high":
                            tier_a_count += 1
                        else:
                            tier_b_count += 1
                    
                    total_chunks += len(batch_ids)
                    
                    # Clear batch
                    batch_ids = []
                    batch_texts = []
                    batch_payloads = []
                
                pbar.update(1)
                
            except Exception as e:
                errors.append((filepath, str(e)))
                pbar.set_description(f"Error: {filepath}")
    
        # Process remaining batch
        if batch_ids:
            asyncio.run(_index_batch(
                batch_ids, batch_texts, batch_payloads
            ))
            
            # Count final batch
            for payload in batch_payloads:
                if payload.get("priority") == "high":
                    tier_a_count += 1
                else:
                    tier_b_count += 1
            
            total_chunks += len(batch_ids)
    
    # Report results
    click.echo("\n📊 Indexing Complete:")
    click.echo(f"  ✅ Total chunks indexed: {total_chunks}")
    click.echo(f"  🎯 Tier A (high accuracy): {tier_a_count}")
    click.echo(f"  ⚡ Tier B (fast): {tier_b_count}")
    
    if errors:
        click.echo(f"\n⚠️  {len(errors)} files had errors:")
        for filepath, error in errors[:5]:  # Show first 5 errors
            click.echo(f"  - {filepath}: {error}")
        if len(errors) > 5:
            click.echo(f"  ... and {len(errors) - 5} more")

async def _index_batch(ids: List[str], texts: List[str], payloads: List[dict]):
    """Index a batch of chunks."""
    await upsert_chunks_dual(
        ids=ids,
        texts=texts,
        payloads=payloads,
        lang=payloads[0].get("lang", "") if payloads else ""
    )

if __name__ == "__main__":
    reindex()