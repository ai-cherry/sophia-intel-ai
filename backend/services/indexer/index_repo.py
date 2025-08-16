#!/usr/bin/env python3
"""
SOPHIA Code Indexer - Repository to Qdrant Vector Storage
Indexes code repositories into 384-dimensional embeddings for semantic search
"""
import asyncio
import hashlib
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
import yaml
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


@dataclass
class CodeChunk:
    """Represents a chunk of code with metadata"""

    file_path: str
    content: str
    language: str
    start_line: int
    end_line: int
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    docstring: Optional[str] = None


class CodeIndexer:
    """Indexes code repositories into Qdrant vector database"""

    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        qdrant_api_key: Optional[str] = None,
        collection_name: str = "sophia_code",
        model_name: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize the code indexer

        Args:
            qdrant_url: Qdrant server URL
            qdrant_api_key: Qdrant API key (optional)
            collection_name: Name of the Qdrant collection
            model_name: SentenceTransformer model for embeddings (384-dim)
        """
        self.qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        self.collection_name = collection_name
        self.model = SentenceTransformer(model_name)
        self.vector_size = 384  # MiniLM-L6-v2 produces 384-dim vectors

        # Load configuration
        self.config = self._load_config()

        # Initialize collection
        self._ensure_collection()

    def _load_config(self) -> Dict[str, Any]:
        """Load indexer configuration"""
        config_path = Path(__file__).parent.parent.parent / "config" / "indexer.yaml"

        default_config = {
            "include_extensions": [".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".cpp", ".c", ".h"],
            "exclude_patterns": ["__pycache__", ".git", "node_modules", ".venv", "venv", "dist", "build"],
            "max_chunk_size": 1000,
            "overlap_size": 100,
            "batch_size": 50,
        }

        if config_path.exists():
            with open(config_path, "r") as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)

        return default_config

    def _ensure_collection(self):
        """Ensure Qdrant collection exists with proper configuration"""
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Using existing Qdrant collection: {self.collection_name}")

        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")
            raise

    def _should_include_file(self, file_path: Path) -> bool:
        """Check if file should be included in indexing"""
        # Check extension
        if file_path.suffix not in self.config["include_extensions"]:
            return False

        # Check exclude patterns
        for pattern in self.config["exclude_patterns"]:
            if pattern in str(file_path):
                return False

        return True

    def _extract_code_chunks(self, file_path: Path, content: str) -> List[CodeChunk]:
        """Extract meaningful chunks from code file"""
        chunks = []
        lines = content.split("\n")

        # Simple chunking strategy - can be enhanced with AST parsing
        chunk_size = self.config["max_chunk_size"]
        overlap = self.config["overlap_size"]

        for i in range(0, len(lines), chunk_size - overlap):
            chunk_lines = lines[i : i + chunk_size]
            chunk_content = "\n".join(chunk_lines)

            if chunk_content.strip():  # Skip empty chunks
                chunks.append(
                    CodeChunk(
                        file_path=str(file_path),
                        content=chunk_content,
                        language=self._detect_language(file_path),
                        start_line=i + 1,
                        end_line=min(i + chunk_size, len(lines)),
                    )
                )

        return chunks

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension"""
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
        }
        return extension_map.get(file_path.suffix, "unknown")

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate 384-dimensional embedding for text"""
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()

    def _create_point_id(self, file_path: str, start_line: int) -> str:
        """Create unique point ID for Qdrant"""
        content = f"{file_path}:{start_line}"
        return hashlib.md5(content.encode()).hexdigest()

    async def index_repository(self, repo_path: str, repo_name: str) -> Dict[str, Any]:
        """
        Index entire repository into Qdrant

        Args:
            repo_path: Path to repository
            repo_name: Name identifier for the repository

        Returns:
            Indexing statistics
        """
        repo_path = Path(repo_path)
        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")

        logger.info(f"Starting indexing of repository: {repo_name} at {repo_path}")

        stats = {"repo_name": repo_name, "files_processed": 0, "chunks_created": 0, "points_uploaded": 0, "errors": []}

        all_points = []

        # Walk through repository files
        for file_path in repo_path.rglob("*"):
            if not file_path.is_file() or not self._should_include_file(file_path):
                continue

            try:
                # Read file content
                async with aiofiles.open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = await f.read()

                # Extract chunks
                chunks = self._extract_code_chunks(file_path, content)
                stats["chunks_created"] += len(chunks)

                # Create Qdrant points
                for chunk in chunks:
                    embedding = self._generate_embedding(chunk.content)

                    point = PointStruct(
                        id=self._create_point_id(chunk.file_path, chunk.start_line),
                        vector=embedding,
                        payload={
                            "repo_name": repo_name,
                            "file_path": chunk.file_path,
                            "content": chunk.content,
                            "language": chunk.language,
                            "start_line": chunk.start_line,
                            "end_line": chunk.end_line,
                            "function_name": chunk.function_name,
                            "class_name": chunk.class_name,
                            "docstring": chunk.docstring,
                            "file_size": len(content),
                            "chunk_size": len(chunk.content),
                        },
                    )
                    all_points.append(point)

                stats["files_processed"] += 1

                # Batch upload to Qdrant
                if len(all_points) >= self.config["batch_size"]:
                    await self._upload_points(all_points)
                    stats["points_uploaded"] += len(all_points)
                    all_points = []

            except Exception as e:
                error_msg = f"Error processing {file_path}: {e}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)

        # Upload remaining points
        if all_points:
            await self._upload_points(all_points)
            stats["points_uploaded"] += len(all_points)

        logger.info(f"Indexing complete: {stats}")
        return stats

    async def _upload_points(self, points: List[PointStruct]):
        """Upload points to Qdrant in batch"""
        try:
            self.qdrant_client.upsert(collection_name=self.collection_name, points=points)
        except Exception as e:
            logger.error(f"Failed to upload points to Qdrant: {e}")
            raise

    async def search_code(
        self, query: str, repo_name: Optional[str] = None, language: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for code using semantic similarity

        Args:
            query: Search query
            repo_name: Filter by repository name
            language: Filter by programming language
            limit: Maximum number of results

        Returns:
            List of matching code chunks with metadata
        """
        # Generate query embedding
        query_embedding = self._generate_embedding(query)

        # Build filter conditions
        filter_conditions = {}
        if repo_name:
            filter_conditions["repo_name"] = repo_name
        if language:
            filter_conditions["language"] = language

        # Search in Qdrant
        search_result = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=filter_conditions if filter_conditions else None,
            limit=limit,
            with_payload=True,
        )

        # Format results
        results = []
        for hit in search_result:
            result = {
                "score": hit.score,
                "file_path": hit.payload["file_path"],
                "content": hit.payload["content"],
                "language": hit.payload["language"],
                "start_line": hit.payload["start_line"],
                "end_line": hit.payload["end_line"],
                "repo_name": hit.payload["repo_name"],
            }
            results.append(result)

        return results

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the indexed collection"""
        try:
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            return {
                "collection_name": self.collection_name,
                "points_count": collection_info.points_count,
                "vector_size": collection_info.config.params.vectors.size,
                "distance": collection_info.config.params.vectors.distance,
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}


# CLI interface for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SOPHIA Code Indexer")
    parser.add_argument("--repo-path", required=True, help="Path to repository")
    parser.add_argument("--repo-name", required=True, help="Repository name")
    parser.add_argument("--qdrant-url", default="http://localhost:6333", help="Qdrant URL")
    parser.add_argument("--search", help="Search query")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Initialize indexer
    indexer = CodeIndexer(qdrant_url=args.qdrant_url)

    if args.search:
        # Search mode
        results = asyncio.run(indexer.search_code(args.search, repo_name=args.repo_name))
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(
                f"\n{i}. {result['file_path']}:{result['start_line']}-{result['end_line']} (score: {result['score']:.3f})"
            )
            print(f"   Language: {result['language']}")
            print(f"   Content preview: {result['content'][:200]}...")
    else:
        # Index mode
        stats = asyncio.run(indexer.index_repository(args.repo_path, args.repo_name))
        print(f"Indexing complete: {stats}")

        # Show collection stats
        collection_stats = indexer.get_collection_stats()
        print(f"Collection stats: {collection_stats}")
