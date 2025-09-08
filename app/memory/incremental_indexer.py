"""
Incremental Indexing System with SHA-based Change Detection.
Optimizes embedding generation by skipping unchanged content.
"""

import asyncio
import hashlib
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import aiofiles
from tqdm.asyncio import tqdm

from app.core.ai_logger import logger
from app.memory.chunking import discover_source_files, produce_chunks_for_index
from app.memory.index_weaviate import upsert_chunks_dual

# ============================================
# Configuration
# ============================================

INDEX_DB_PATH = "tmp/index_state.db"
BATCH_SIZE = 20
MAX_CONCURRENT_FILES = 10

# ============================================
# Index State Management
# ============================================


@dataclass
class FileState:
    """State of an indexed file."""

    path: str
    sha256: str
    size: int
    modified_time: float
    chunks_count: int
    last_indexed: datetime

    def has_changed(self, current_sha: str, current_size: int) -> bool:
        """Check if file has changed since last index."""
        return self.sha256 != current_sha or self.size != current_size


class IndexStateManager:
    """Manages the state of indexed files."""

    def __init__(self, db_path: str = INDEX_DB_PATH):
        self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self):
        """Ensure database exists with proper schema."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS file_state (
                    path TEXT PRIMARY KEY,
                    sha256 TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    modified_time REAL NOT NULL,
                    chunks_count INTEGER NOT NULL,
                    last_indexed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chunk_state (
                    chunk_id TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    start_line INTEGER NOT NULL,
                    end_line INTEGER NOT NULL,
                    last_indexed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_path) REFERENCES file_state(path)
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_file_path
                ON chunk_state(file_path)
            """
            )

            conn.commit()

    def get_file_state(self, path: str) -> Optional[FileState]:
        """Get the last indexed state of a file."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM file_state WHERE path = ?", (path,))
            row = cursor.fetchone()

            if row:
                return FileState(
                    path=row[0],
                    sha256=row[1],
                    size=row[2],
                    modified_time=row[3],
                    chunks_count=row[4],
                    last_indexed=datetime.fromisoformat(row[5]),
                )
        return None

    def update_file_state(
        self, path: str, sha256: str, size: int, modified_time: float, chunks_count: int
    ):
        """Update the indexed state of a file."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO file_state
                (path, sha256, size, modified_time, chunks_count, last_indexed)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (path, sha256, size, modified_time, chunks_count),
            )
            conn.commit()

    def update_chunk_states(self, chunks: list[dict[str, any]]):
        """Update chunk states."""
        with sqlite3.connect(self.db_path) as conn:
            for chunk in chunks:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO chunk_state
                    (chunk_id, file_path, sha256, start_line, end_line, last_indexed)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (
                        chunk["chunk_id"],
                        chunk["file_path"],
                        chunk["sha256"],
                        chunk["start_line"],
                        chunk["end_line"],
                    ),
                )
            conn.commit()

    def get_unchanged_chunks(self, file_path: str, current_sha: str) -> set[str]:
        """Get chunk IDs that haven't changed."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT chunk_id FROM chunk_state WHERE file_path = ? AND sha256 = ?",
                (file_path, current_sha),
            )
            return {row[0] for row in cursor.fetchall()}

    def remove_file_state(self, path: str):
        """Remove file and its chunks from index state."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM chunk_state WHERE file_path = ?", (path,))
            conn.execute("DELETE FROM file_state WHERE path = ?", (path,))
            conn.commit()

    def get_stats(self) -> dict[str, any]:
        """Get indexing statistics."""
        with sqlite3.connect(self.db_path) as conn:
            file_count = conn.execute("SELECT COUNT(*) FROM file_state").fetchone()[0]
            chunk_count = conn.execute("SELECT COUNT(*) FROM chunk_state").fetchone()[0]
            total_size = conn.execute("SELECT SUM(size) FROM file_state").fetchone()[0] or 0

            return {
                "files_indexed": file_count,
                "chunks_indexed": chunk_count,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
            }


# ============================================
# File Hashing
# ============================================


async def compute_file_sha256(filepath: str) -> tuple[str, int]:
    """
    Compute SHA256 hash of file content asynchronously.

    Returns:
        Tuple of (sha256_hex, file_size)
    """
    sha256 = hashlib.sha256()
    size = 0

    async with aiofiles.open(filepath, "rb") as f:
        while chunk := await f.read(8192):
            sha256.update(chunk)
            size += len(chunk)

    return sha256.hexdigest(), size


def compute_content_sha256(content: str) -> str:
    """Compute SHA256 hash of content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ============================================
# Incremental Indexer
# ============================================


class IncrementalIndexer:
    """
    Incremental indexing with change detection.
    Only re-indexes files that have changed.
    """

    def __init__(
        self, state_manager: Optional[IndexStateManager] = None, batch_size: int = BATCH_SIZE
    ):
        self.state_manager = state_manager or IndexStateManager()
        self.batch_size = batch_size
        self.stats = {
            "files_processed": 0,
            "files_skipped": 0,
            "files_updated": 0,
            "chunks_created": 0,
            "chunks_reused": 0,
            "errors": [],
        }

    async def index_file(
        self, filepath: str, priority: Optional[str] = None, force: bool = False
    ) -> dict[str, any]:
        """
        Index a single file incrementally.

        Args:
            filepath: Path to the file
            priority: Priority level for routing
            force: Force re-indexing even if unchanged

        Returns:
            Indexing result
        """
        result = {"path": filepath, "status": "skipped", "chunks": 0, "changed": False}

        try:
            # Check if file exists
            if not os.path.exists(filepath):
                self.state_manager.remove_file_state(filepath)
                result["status"] = "removed"
                return result

            # Compute current file hash
            current_sha, current_size = await compute_file_sha256(filepath)
            current_mtime = os.path.getmtime(filepath)

            # Check previous state
            prev_state = self.state_manager.get_file_state(filepath)

            # Skip if unchanged (unless forced)
            if not force and prev_state and not prev_state.has_changed(current_sha, current_size):
                self.stats["files_skipped"] += 1
                result["status"] = "unchanged"
                return result

            # Read file content
            async with aiofiles.open(filepath, encoding="utf-8") as f:
                content = await f.read()

            # Generate chunks
            ids, texts, payloads = produce_chunks_for_index(
                filepath=filepath, content=content, priority=priority
            )

            # Add SHA to payloads for change tracking
            for payload in payloads:
                payload["file_sha256"] = current_sha

            # Filter out unchanged chunks if file structure is similar
            if prev_state and not force:
                unchanged_chunks = self.state_manager.get_unchanged_chunks(filepath, current_sha)

                # Filter to only changed chunks
                changed_indices = [
                    i for i, chunk_id in enumerate(ids) if chunk_id not in unchanged_chunks
                ]

                if changed_indices:
                    ids = [ids[i] for i in changed_indices]
                    texts = [texts[i] for i in changed_indices]
                    payloads = [payloads[i] for i in changed_indices]

                    self.stats["chunks_reused"] += len(unchanged_chunks)

            # Index chunks if any
            if ids:
                await upsert_chunks_dual(ids, texts, payloads, lang=payloads[0].get("lang", ""))
                self.stats["chunks_created"] += len(ids)

            # Update state
            self.state_manager.update_file_state(
                path=filepath,
                sha256=current_sha,
                size=current_size,
                modified_time=current_mtime,
                chunks_count=len(ids),
            )

            # Update chunk states
            chunk_states = [
                {
                    "chunk_id": ids[i],
                    "file_path": filepath,
                    "sha256": current_sha,
                    "start_line": payloads[i]["start_line"],
                    "end_line": payloads[i]["end_line"],
                }
                for i in range(len(ids))
            ]
            self.state_manager.update_chunk_states(chunk_states)

            # Update stats
            if prev_state:
                self.stats["files_updated"] += 1
                result["status"] = "updated"
            else:
                self.stats["files_processed"] += 1
                result["status"] = "indexed"

            result["chunks"] = len(ids)
            result["changed"] = True

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            self.stats["errors"].append({"path": filepath, "error": str(e)})

        return result

    async def index_files(
        self,
        filepaths: list[str],
        priority: Optional[str] = None,
        force: bool = False,
        progress: bool = True,
    ) -> dict[str, any]:
        """
        Index multiple files incrementally with concurrency control.

        Args:
            filepaths: List of file paths
            priority: Priority level for all files
            force: Force re-indexing
            progress: Show progress bar

        Returns:
            Indexing statistics
        """
        self.stats = {
            "files_processed": 0,
            "files_skipped": 0,
            "files_updated": 0,
            "chunks_created": 0,
            "chunks_reused": 0,
            "errors": [],
        }

        # Create batches for concurrency control
        batches = [
            filepaths[i : i + MAX_CONCURRENT_FILES]
            for i in range(0, len(filepaths), MAX_CONCURRENT_FILES)
        ]

        # Process batches
        if progress:
            pbar = tqdm(total=len(filepaths), desc="Indexing files")

        for batch in batches:
            tasks = [self.index_file(filepath, priority, force) for filepath in batch]

            results = await asyncio.gather(*tasks)

            if progress:
                pbar.update(len(results))

        if progress:
            pbar.close()

        return self.stats

    async def index_directory(
        self,
        root_dir: str = ".",
        include_patterns: Optional[list[str]] = None,
        exclude_patterns: Optional[list[str]] = None,
        priority: Optional[str] = None,
        force: bool = False,
    ) -> dict[str, any]:
        """
        Index all matching files in a directory.

        Args:
            root_dir: Root directory to search
            include_patterns: File patterns to include
            exclude_patterns: Patterns to exclude
            priority: Priority level
            force: Force re-indexing

        Returns:
            Indexing statistics
        """
        # Discover files
        files = discover_source_files(root_dir, include_patterns, exclude_patterns)

        if not files:
            return {"message": "No files found matching criteria"}

        logger.info(f"📂 Found {len(files)} files to index")

        # Index files
        stats = await self.index_files(files, priority, force)

        # Add summary
        stats["summary"] = {
            "total_files": len(files),
            "indexed": stats["files_processed"],
            "updated": stats["files_updated"],
            "skipped": stats["files_skipped"],
            "errors": len(stats["errors"]),
        }

        return stats


# ============================================
# CLI Interface
# ============================================


async def main():
    """CLI for incremental indexing."""
    import argparse

    parser = argparse.ArgumentParser(description="Incremental code indexer")
    parser.add_argument("--root", default=".", help="Root directory")
    parser.add_argument("--force", action="store_true", help="Force re-indexing")
    parser.add_argument("--priority", choices=["low", "medium", "high"], help="Priority level")
    parser.add_argument("--stats", action="store_true", help="Show index statistics")

    args = parser.parse_args()

    indexer = IncrementalIndexer()

    if args.stats:
        stats = indexer.state_manager.get_stats()
        logger.info("\n📊 Index Statistics:")
        logger.info(f"  Files indexed: {stats['files_indexed']}")
        logger.info(f"  Chunks indexed: {stats['chunks_indexed']}")
        logger.info(f"  Total size: {stats['total_size_mb']:.2f} MB")
    else:
        stats = await indexer.index_directory(
            root_dir=args.root, priority=args.priority, force=args.force
        )

        logger.info("\n✅ Indexing Complete:")
        logger.info(f"  Indexed: {stats['summary']['indexed']} files")
        logger.info(f"  Updated: {stats['summary']['updated']} files")
        logger.info(f"  Skipped: {stats['summary']['skipped']} files (unchanged)")
        logger.info(f"  Chunks created: {stats['chunks_created']}")
        logger.info(f"  Chunks reused: {stats['chunks_reused']}")

        if stats["errors"]:
            logger.info(f"\n⚠️  {len(stats['errors'])} errors occurred")


if __name__ == "__main__":
    asyncio.run(main())
