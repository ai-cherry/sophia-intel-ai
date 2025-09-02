import os
import re
import json
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.embedding.embedding_service import TogetherEmbeddingService
from app.weaviate.weaviate_client import WeaviateClient
from app.indexing.chunker import chunk_text

logger = logging.getLogger(__name__)

class RepositoryIndexer:
    def __init__(
        self,
        embedding_service: TogetherEmbeddingService,
        weaviate_client: WeaviateClient,
        max_chunk_size: int = 1000,
        max_chunks: int = 100
    ):
        self.embedding_service = embedding_service
        self.weaviate_client = weaviate_client
        self.max_chunk_size = max_chunk_size
        self.max_chunks = max_chunks

    async def index_repository(
        self,
        repo_path: str,
        include_patterns: List[str] = ["*.py", "*.md", "*.txt"],
        exclude_patterns: List[str] = [".git", ".venv", "__pycache__"]
    ) -> Dict[str, Any]:
        """
        Index an entire repository with file type filtering
        """
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
                content = file_path.read_text(encoding='utf-8', errors='replace')
                
                # Chunk the content
                chunks = chunk_text(content, self.max_chunk_size)
                
                # Generate embeddings
                embeddings = await self.embedding_service.generate_embeddings(
                    texts=chunks,
                    model="togethercomputer/m2-bert-80M-8k-retrieval"
                )
                
                # Store in Weaviate
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    metadata = {
                        "file_path": str(file_path.relative_to(repo_path)),
                        "file_type": file_path.suffix,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "repo_path": str(repo_path)
                    }
                    
                    await self.weaviate_client.store_embedding(
                        embedding=embedding,
                        text=chunk,
                        metadata=metadata
                    )
                
                results.append({
                    "file": str(file_path),
                    "chunks": len(chunks),
                    "status": "indexed"
                })
                
            except Exception as e:
                logger.error(f"Error indexing {file_path}: {str(e)}")
                results.append({
                    "file": str(file_path),
                    "status": "failed",
                    "error": str(e)
                })
        
        return {
            "repository": str(repo_path),
            "files_indexed": len(results),
            "results": results
        }

    async def search_repository(
        self,
        query: str,
        top_k: int = 5,
        repo_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search across indexed repository content
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embeddings(
            texts=[query],
            model="togethercomputer/m2-bert-80M-8k-retrieval"
        )[0]
        
        # Search in Weaviate
        results = await self.weaviate_client.search_embeddings(
            query_embedding=query_embedding,
            top_k=top_k,
            repo_path=repo_path
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result["id"],
                "text": result["text"],
                "score": result["score"],
                "metadata": result["metadata"]
            })
        
        return formatted_results