#!/usr/bin/env python3
"""
Memory Pruning Background Script
SOLO DEVELOPER USE ONLY - NOT FOR DISTRIBUTION

Periodically prunes stale memories with low relevance scores
to maintain optimal memory system performance.
"""

import argparse
import asyncio
import datetime
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="logs/memory_prune.log",
    filemode="a",
)
logger = logging.getLogger("memory_prune")

# Constants
RELEVANCE_THRESHOLD = 0.7  # Prune memories with relevance below this
PRUNE_BATCH_SIZE = 100  # Process this many memories at a time
MAX_PRUNE_COUNT = 1000  # Maximum memories to prune in one run
MEMORY_CONFIG = {"vector_store": "qdrant", "collection_name": "mem0_collection"}

# Import Mem0 with fallback
try:
    from mem0 import Memory

    HAS_MEM0 = True
except ImportError:
    HAS_MEM0 = False
    logger.error("Mem0 not installed, pruning will not be performed")


async def prune_memories(
    threshold: float = RELEVANCE_THRESHOLD,
    batch_size: int = PRUNE_BATCH_SIZE,
    max_count: int = MAX_PRUNE_COUNT,
) -> Dict[str, Any]:
    """
    Prune stale memories with relevance below threshold
    """
    if not HAS_MEM0:
        return {"status": "error", "message": "Mem0 not installed", "pruned": 0, "total": 0}

    try:
        logger.info(f"Initializing memory system with config: {MEMORY_CONFIG}")
        mem = Memory.from_config(MEMORY_CONFIG)

        # Get count of memories
        total_count = await mem.count()
        logger.info(f"Total memories: {total_count}")

        if total_count == 0:
            return {"status": "success", "message": "No memories to prune", "pruned": 0, "total": 0}

        # Find stale memories
        stale_query = {"relevance": {"$lt": threshold}}
        stale_count = await mem.count(stale_query)
        logger.info(f"Found {stale_count} stale memories with relevance < {threshold}")

        if stale_count == 0:
            return {
                "status": "success",
                "message": "No stale memories found",
                "pruned": 0,
                "total": total_count,
            }

        # Limit the number of memories to prune
        prune_count = min(stale_count, max_count)
        logger.info(f"Will prune up to {prune_count} memories")

        # Prune in batches
        pruned = 0
        for i in range(0, prune_count, batch_size):
            batch_size_adjusted = min(batch_size, prune_count - i)
            logger.debug(f"Processing batch {i//batch_size + 1}, size {batch_size_adjusted}")

            # Get batch of stale memories
            stale_memories = await mem.search(stale_query, limit=batch_size_adjusted)

            # Delete each memory
            for memory in stale_memories:
                memory_id = memory.get("_id")
                if memory_id:
                    try:
                        await mem.delete(memory_id)
                        pruned += 1
                        logger.debug(
                            f"Pruned memory {memory_id} with relevance {memory.get('relevance')}"
                        )
                    except Exception as e:
                        logger.error(f"Failed to delete memory {memory_id}: {e}")

        # Get new count after pruning
        new_count = await mem.count()

        logger.info(f"Pruning complete. Pruned {pruned} memories. New total: {new_count}")
        return {
            "status": "success",
            "message": f"Pruned {pruned} memories",
            "pruned": pruned,
            "total": new_count,
        }

    except Exception as e:
        logger.error(f"Error pruning memories: {e}")
        return {"status": "error", "message": str(e), "pruned": 0, "total": 0}


def main():
    parser = argparse.ArgumentParser(description="Prune stale memories with low relevance scores")
    parser.add_argument(
        "--threshold",
        type=float,
        default=RELEVANCE_THRESHOLD,
        help=f"Relevance threshold (default: {RELEVANCE_THRESHOLD})",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=PRUNE_BATCH_SIZE,
        help=f"Batch size for processing (default: {PRUNE_BATCH_SIZE})",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=MAX_PRUNE_COUNT,
        help=f"Maximum memories to prune (default: {MAX_PRUNE_COUNT})",
    )
    parser.add_argument("--force", action="store_true", help="Force pruning even if recently run")
    args = parser.parse_args()

    logger.info("Starting memory pruning process")

    if not HAS_MEM0:
        logger.error("Mem0 not installed, aborting")
        return

    # Check if pruning is needed
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)

    last_prune_file = cache_dir / "last_memory_prune"
    current_time = time.time()

    if not args.force and last_prune_file.exists():
        with open(last_prune_file) as f:
            try:
                last_prune = float(f.read().strip())
                hours_since_prune = (current_time - last_prune) / 3600

                if hours_since_prune < 24:  # Prune once per day by default
                    logger.info(f"Skipping pruning, last run was {hours_since_prune:.1f} hours ago")
                    return
            except Exception:
                pass  # Continue with pruning if file is invalid

    # Run pruning
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(
        prune_memories(threshold=args.threshold, batch_size=args.batch, max_count=args.max)
    )

    if result["status"] == "success":
        # Record prune time
        with open(last_prune_file, "w") as f:
            f.write(str(current_time))

        # Save prune stats
        with open(cache_dir / "last_prune_stats.json", "w") as f:
            json.dump(
                {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "threshold": args.threshold,
                    "pruned": result["pruned"],
                    "total_remaining": result["total"],
                },
                f,
            )

        logger.info(f"Pruning completed: {result['message']}")
    else:
        logger.error(f"Pruning failed: {result['message']}")


if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    main()
