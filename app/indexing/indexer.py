import logging
from pathlib import Path
from typing import Any

from app.embedding.embedding_service import TogetherEmbeddingService
from app.indexing.chunker import chunk_text
from app.models.metadata import MemoryMetadata
from app.weaviate.weaviate_client import WeaviateClient

logger = logging.getLogger(__name__)


class RepositoryIndexer:
    def __init__(
        self,
        embedding_service: TogetherEmbeddingService,
        weaviate_client: WeaviateClient,
        max_chunk_size: int = 1000,
        max_chunks: int = 100,
    ):
        self.embedding_service = embedding_service
        self.weaviate_client = weaviate_client
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

                # Generate embeddings
                embeddings = await self.embedding_service.generate_embeddings(
                    texts=chunks, model="togethercomputer/m2-bert-80M-8k-retrieval"
                )

                # Store in Weaviate
                for i, (chunk, embedding) in enumerate(
                    zip(chunks, embeddings, strict=False)
                ):
                    metadata = {
                        "file_path": str(file_path.relative_to(repo_path)),
                        "file_type": file_path.suffix,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "repo_path": str(repo_path),
                    }

                    await self.weaviate_client.store_embedding(
                        embedding=embedding, text=chunk, metadata=metadata
                    )

                results.append(
                    {"file": str(file_path), "chunks": len(chunks), "status": "indexed"}
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
        """
        Search across indexed repository content
        """
        # Generate query embedding
        query_embedding = (
            await self.embedding_service.generate_embeddings(
                texts=[query], model="togethercomputer/m2-bert-80M-8k-retrieval"
            )
        )[0]

        # Search in Weaviate
        results = await self.weaviate_client.search_embeddings(
            query_embedding=query_embedding, top_k=top_k, repo_path=repo_path
        )

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append(
                {
                    "id": result["id"],
                    "text": result["text"],
                    "score": result["score"],
                    "metadata": result["metadata"],
                }
            )

        return formatted_results


async def index_file(file_path: str, metadata: Optional[MemoryMetadata] = None) -> None:
    """
    Helper function to index a single file.

    Args:
        file_path: Path to the file to index
        metadata: Optional metadata to associate with the indexed file
    """
    # Initialize services (you may want to cache these)
    from app.embedding.embedding_service import TogetherEmbeddingService
    from app.weaviate.weaviate_client import WeaviateClient

    embedding_service = TogetherEmbeddingService()
    weaviate_client = WeaviateClient()
    RepositoryIndexer(embedding_service, weaviate_client)

    # Read file content
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        logger.error(f"File does not exist: {file_path}")
        return

    try:
        content = file_path_obj.read_text(encoding="utf-8", errors="replace")

        # Chunk the content
        chunks = chunk_text(content)

        # Generate embeddings
        embeddings = await embedding_service.generate_embeddings(
            texts=chunks, model="togethercomputer/m2-bert-80M-8k-retrieval"
        )

        # Store in Weaviate with metadata
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=False)):
            chunk_metadata = {
                "file_path": str(file_path),
                "file_type": file_path_obj.suffix,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }

            # Merge with provided metadata if available
            if metadata:
                chunk_metadata.update(metadata.dict())

            await weaviate_client.store_embedding(
                embedding=embedding, text=chunk, metadata=chunk_metadata
            )

        logger.info(f"Successfully indexed {file_path} with {len(chunks)} chunks")

    except Exception as e:
        logger.error(f"Error indexing file {file_path}: {str(e)}")
        raise
