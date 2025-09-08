import asyncio
import logging
import os
import subprocess

from app.indexing.indexer import index_file

# Configure logger
logger = logging.getLogger(__name__)


def get_changed_files() -> list[str]:
    """
    Get list of changed files using git diff.

    Returns:
        List of changed file paths, empty list if no changes or on error
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

        if not result.stdout:
            logger.info("No changed files detected")
            return []

        changed_files = result.stdout.splitlines()

        # Warn if too many files changed
        if len(changed_files) > 1000:
            logger.warning(
                f"Large number of changed files detected: {len(changed_files)}"
            )

        return changed_files

    except subprocess.CalledProcessError as e:
        logger.error(f"Git diff failed with return code {e.returncode}: {e.stderr}")
        return []
    except subprocess.TimeoutExpired:
        logger.error("Git diff timed out after 30 seconds")
        return []
    except Exception as e:
        logger.error(f"Unexpected error getting changed files: {str(e)}")
        return []


async def incremental_index(batch_size: int = 100):
    """
    Reindex only changed files.

    Args:
        batch_size: Number of files to process in each batch
    """
    changed_files = get_changed_files()

    if not changed_files:
        logger.info("No files to reindex")
        return

    logger.info(f"Starting incremental indexing for {len(changed_files)} files")

    # Process files in batches for large changesets
    indexed_count = 0
    failed_count = 0

    for i in range(0, len(changed_files), batch_size):
        batch = changed_files[i : i + batch_size]
        logger.info(f"Processing batch {i // batch_size + 1} ({len(batch)} files)")

        for file_path in batch:
            if not os.path.exists(file_path):
                logger.warning(f"File no longer exists: {file_path}")
                continue

            try:
                await index_file(file_path)
                logger.info(f"Reindexed: {file_path}")
                indexed_count += 1
            except Exception as e:
                logger.error(f"Failed to reindex {file_path}: {str(e)}")
                failed_count += 1

    logger.info(
        f"Incremental indexing complete. Indexed: {indexed_count}, Failed: {failed_count}"
    )


if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the async function
    asyncio.run(incremental_index())
