import logging
from pathlib import Path
from typing import Any, Optional

from app.indexing.chunker import chunk_text
from app.models.metadata import MemoryMetadata
from app.memory.unified_memory_router import (
    DocChunk,
    MemoryDomain,
    get_memory_router,
)
logger = logging.getLogger(__name__)
class RepositoryIndexer:
    def __init__(
        self,
        max_chunk_size: int = 1000,
        max_chunks: int = 100,
    ):
        # Use the unified memory router (handles embeddings + vector store)
        self.memory = get_memory_router()
        self.max_chunk_size = max_chunk_size
        self.max_chunks = max_chunks
    async def index_repository(
        self,
        repo_path: str,
        include_patterns: list[str] = None,
        exclude_patterns: list[str] = None,
    ) -> dict[str, Any]:
        """
        Index an entire repository with file type filtering
        """
        if exclude_patterns is None:
            exclude_patterns = [".git", ".venv", "__pycache__"]
        if include_patterns is None:
            include_patterns = ["*.py", "*.md", "*.txt"]
        repo_path = Path(repo_path).resolve()
        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        # Get all files matching patterns
        files = []
        for pattern in include_patterns:
            files.extend(repo_path.rglob(pattern))
        # Filter out excluded paths
        filtered_files = []
        for file in files:
            if any(exclude in str(file) for exclude in exclude_patterns):
                continue
            if file.is_file():
                filtered_files.append(file)
        logger.info(f"Indexing {len(filtered_files)} files from {repo_path}")
        # Process each file
        results = []
        for file_path in filtered_files:
            try:
                # Get file content
                content = file_path.read_text(encoding="utf-8", errors="replace")
                # Chunk the content
                chunks = chunk_text(content, self.max_chunk_size)
                # Build DocChunks; the router will embed and upsert
                doc_chunks: list[DocChunk] = []
                rel = str(file_path.relative_to(repo_path))
                for i, chunk_text_value in enumerate(chunks):
                    source_uri = f"repo://{repo_path}/{rel}#chunk-{i}"
                    metadata = {
                        "file_path": rel,
                        "file_type": file_path.suffix,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "repo_path": str(repo_path),
                    }
                    doc_chunks.append(
                        DocChunk(
                            content=chunk_text_value,
                            source_uri=source_uri,
                            domain=MemoryDomain.SHARED,
                            metadata=metadata,
                        )
                    )
                upsert_report = await self.memory.upsert_chunks(
                    doc_chunks, MemoryDomain.SHARED
                )
                results.append(
                    {
                        "file": str(file_path),
                        "chunks": len(doc_chunks),
                        "status": "indexed" if upsert_report.success else "partial",
                        "stored": upsert_report.chunks_stored,
                        "errors": upsert_report.errors,
                    }
                )
            except Exception as e:
                logger.error(f"Error indexing {file_path}: {str(e)}")
                results.append(
                    {"file": str(file_path), "status": "failed", "error": str(e)}
                )
        return {
            "repository": str(repo_path),
            "files_indexed": len(results),
            "results": results,
        }
    async def search_repository(
        self, query: str, top_k: int = 5, repo_path: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """Search across indexed repository content (hybrid semantic)."""
        hits = await self.memory.search(query, domain=MemoryDomain.SHARED, k=top_k)
        # Optional repo_path filter
        if repo_path:
            hits = [h for h in hits if (h.metadata or {}).get("repo_path") == str(Path(repo_path))]
        # Format results
        formatted = [
            {
                "id": h.source_uri,
                "text": h.content,
                "score": h.score,
                "metadata": h.metadata,
            }
            for h in hits
        ]
        return formatted
async def index_file(file_path: str, metadata: Optional[MemoryMetadata] = None) -> None:
    """
    Helper function to index a single file.
    Args:
        file_path: Path to the file to index
        metadata: Optional metadata to associate with the indexed file
    """
    # Initialize services (you may want to cache these)
    router = get_memory_router()
    # Read file content
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        logger.error(f"File does not exist: {file_path}")
        return
    try:
        content = file_path_obj.read_text(encoding="utf-8", errors="replace")
        # Chunk the content
        chunks = chunk_text(content)
        doc_chunks = []
        for i, chunk_text_value in enumerate(chunks):
            cm = {
                "file_path": str(file_path),
                "file_type": file_path_obj.suffix,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            if metadata:
                cm.update(metadata.dict())
            doc_chunks.append(
                DocChunk(
                    content=chunk_text_value,
                    source_uri=f"file://{file_path}#chunk-{i}",
                    domain=MemoryDomain.SHARED,
                    metadata=cm,
                )
            )
        await router.upsert_chunks(doc_chunks, MemoryDomain.SHARED)
        logger.info(f"Successfully indexed {file_path} with {len(chunks)} chunks")
    except Exception as e:
        logger.error(f"Error indexing file {file_path}: {str(e)}")
        raise
