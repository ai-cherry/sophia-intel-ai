import os
import argparse
from typing import List, Dict, Any
import hashlib

from services.memory_client import MemoryClient
from connectors.github_conn import GitHubConnector
from services.config_loader import load_config

def chunk_text(text: str, chunk_size: int = 120, overlap: int = 20) -> List[str]:
    """
    Splits a text into overlapping chunks.
    """
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks

async def index_repo(
    owner: str,
    repo: str,
    mode: str = "full",
    qdrant_url: str = None,
    qdrant_api_key: str = None,
):
    """
    Indexes a repository by reading its files, chunking them, and upserting them into Qdrant.
    """
    config = load_config()
    github_connector = GitHubConnector(config)
    memory_client = MemoryClient(qdrant_url or config["qdrant"]["url"], qdrant_api_key or config["qdrant"]["api_key"])

    # In a real implementation, we would get the list of files from the repo.
    # For this example, we'll just index the README.md.
    files_to_index = ["README.md"]

    for file_path in files_to_index:
        try:
            content_bytes = await github_connector.read_file(owner, repo, file_path)
            content = content_bytes.decode("utf-8")
            
            chunks = chunk_text(content)
            
            metadata = [
                {
                    "repo": f"{owner}/{repo}",
                    "branch": "main", # Assuming main branch for now
                    "path": file_path,
                    "chunk": i,
                    "hash": hashlib.sha256(chunk.encode()).hexdigest(),
                    "ts": "now()", # Placeholder for timestamp
                }
                for i, chunk in enumerate(chunks)
            ]
            
            memory_client.upsert_documents(chunks, metadata)
            print(f"Indexed {len(chunks)} chunks from {file_path}")

        except Exception as e:
            print(f"Could not index {file_path}: {e}")

    await github_connector.close()

if __name__ == "__main__":
    import asyncio

    parser = argparse.ArgumentParser(description="Index a GitHub repository into Qdrant.")
    parser.add_argument("owner", type=str, help="The owner of the repository.")
    parser.add_argument("repo", type=str, help="The name of the repository.")
    parser.add_argument("--mode", type=str, default="full", choices=["full", "changed"], help="Indexing mode.")
    
    args = parser.parse_args()
    
    qdrant_url = os.getenv("QDRANT_URL")
    if qdrant_url:
        asyncio.run(index_repo(args.owner, args.repo, args.mode, qdrant_url))
    else:
        print("QDRANT_URL not set. Skipping indexing.")