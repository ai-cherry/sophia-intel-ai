#!/usr/bin/env python3
"""
Repository Indexer for AI Dev Toolkit
Aug 2025 - Cloud-Centric AI Environment
This script indexes the repository code and documentation to enable
semantic search and retrieval through the MCP server. It supports
multiple indexing backends:
- Haystack 2.0: Semantic search with Supabase vectors (-91% latency)
- LlamaIndex 0.13: Hybrid vector/graph indexing (+20% precision)
- Qdrant: Vector DB for high-performance semantic search
"""
import os
import sys
import time
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
import datetime
import subprocess
import glob
import shutil
import re
# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("repo_indexer")
# Constants
ROOT_DIR = Path(__file__).parent.parent.absolute()
INDEX_DIR = ROOT_DIR / "indexing" / "repo_embeddings"
CONFIG_PATH = ROOT_DIR / "indexing" / "config.json"
# Supported indexing systems
INDEXING_SYSTEMS = ["haystack", "llamaindex", "qdrant", "simple"]
# Default configuration
DEFAULT_CONFIG = {
    "indexing_system": os.environ.get("INDEXING_SYSTEM", "haystack"),
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "file_types": [".py", ".md", ".sh", ".js", ".ts", ".json", ".yml", ".yaml"],
    "exclude_dirs": ["node_modules", "__pycache__", ".git", ".github/workflows", "venv", ".venv"],
    "exclude_patterns": [".*\\.pyc$", ".*\\.d\\.ts$", ".*\\.min\\.js$"],
    "embedding_model": "BAAI/bge-small-en-v1.5",
    "vector_dimensions": 384,
    "reindex_period_days": 1
}
def load_config() -> Dict[str, Any]:
    """Load indexing configuration"""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
                logger.info(f"Loaded configuration from {CONFIG_PATH}")
                # Update with any missing default values
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
    logger.info(f"Using default configuration")
    return DEFAULT_CONFIG.copy()
def save_config(config: Dict[str, Any]) -> None:
    """Save indexing configuration"""
    try:
        os.makedirs(CONFIG_PATH.parent, exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
        logger.info(f"Saved configuration to {CONFIG_PATH}")
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
def find_files_to_index(config: Dict[str, Any]) -> List[Path]:
    """Find all files to be indexed based on config"""
    files_to_index = []
    exclude_dirs = set(config["exclude_dirs"])
    file_types = set(config["file_types"])
    exclude_patterns = [re.compile(pattern) for pattern in config["exclude_patterns"]]
    logger.info(f"Looking for files to index in {ROOT_DIR}")
    for root, dirs, files in os.walk(ROOT_DIR):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(ROOT_DIR)
            # Check if file has correct extension
            if Path(file).suffix in file_types:
                # Check if file matches any exclude pattern
                if any(pattern.match(str(rel_path)) for pattern in exclude_patterns):
                    continue
                files_to_index.append(file_path)
    logger.info(f"Found {len(files_to_index)} files to index")
    return files_to_index
def check_dependencies(system: str) -> bool:
    """Check if required dependencies for the specified indexing system are installed"""
    try:
        if system == "haystack":
            import haystack_ai
            return True
        elif system == "llamaindex":
            import llama_index
            return True
        elif system == "qdrant":
            import qdrant_client
            return True
        elif system == "simple":
            # Simple indexer just uses built-in libraries
            return True
        else:
            logger.error(f"Unknown indexing system: {system}")
            return False
    except ImportError:
        logger.error(f"Required dependencies for {system} are not installed")
        return False
def install_dependencies(system: str) -> bool:
    """Install required dependencies for the specified indexing system"""
    packages = []
    if system == "haystack":
        packages = ["haystack-ai>=2.0.0", "sentence-transformers>=2.2.2"]
    elif system == "llamaindex":
        packages = ["llama-index>=0.13.0", "sentence-transformers>=2.2.2"]
    elif system == "qdrant":
        packages = ["qdrant-client>=1.5.0", "sentence-transformers>=2.2.2"]
    elif system == "simple":
        # No special requirements for simple indexer
        return True
    else:
        logger.error(f"Unknown indexing system: {system}")
        return False
    logger.info(f"Installing dependencies for {system}: {', '.join(packages)}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False
def process_file(file_path: Path, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Process a file into chunks for indexing"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.warning(f"Could not read {file_path}: {e}")
        return []
    # Get relative path for storage
    rel_path = file_path.relative_to(ROOT_DIR)
    # Split into chunks
    chunk_size = config["chunk_size"]
    chunk_overlap = config["chunk_overlap"]
    # Simple chunking by characters with overlap
    chunks = []
    for i in range(0, len(content), chunk_size - chunk_overlap):
        chunk_text = content[i:i + chunk_size]
        if len(chunk_text) < 50:  # Skip very small chunks
            continue
        chunk_data = {
            "text": chunk_text,
            "metadata": {
                "source": str(rel_path),
                "start": i,
                "end": i + len(chunk_text),
                "chunk_id": f"{rel_path}_{i}",
                "file_type": file_path.suffix[1:] if file_path.suffix else "unknown"
            }
        }
        chunks.append(chunk_data)
    logger.debug(f"Processed {file_path} into {len(chunks)} chunks")
    return chunks
def index_with_haystack(chunks: List[Dict[str, Any]], config: Dict[str, Any]) -> bool:
    """Index content using Haystack"""
    try:
        from haystack_ai.document_stores import SupabaseVectorStore, InMemoryDocumentStore
        from haystack_ai.embedders import HuggingFaceEmbedder
        from haystack_ai import Pipeline
        from haystack_ai.components.indexers import DocumentWriter
        from haystack_ai.dataclasses import Document
        # Create document store
        use_supabase = "SUPABASE_URL" in os.environ and "SUPABASE_KEY" in os.environ
        if use_supabase:
            logger.info("Using Supabase vector store for Haystack")
            document_store = SupabaseVectorStore(
                supabase_url=os.environ["SUPABASE_URL"],
                supabase_key=os.environ["SUPABASE_KEY"],
                table_name="repo_embeddings",
                embedding_dim=config["vector_dimensions"]
            )
        else:
            logger.info("Using in-memory document store for Haystack (Supabase credentials not found)")
            document_store = InMemoryDocumentStore(embedding_dim=config["vector_dimensions"])
        # Create embedder
        embedder = HuggingFaceEmbedder(model=config["embedding_model"])
        # Create pipeline
        indexing_pipeline = Pipeline()
        indexing_pipeline.add_component("embedder", embedder)
        indexing_pipeline.add_component("writer", DocumentWriter(document_store))
        indexing_pipeline.connect("embedder", "writer")
        # Convert chunks to documents
        documents = []
        for chunk in chunks:
            doc = Document(
                content=chunk["text"],
                meta=chunk["metadata"]
            )
            documents.append(doc)
        # Run indexing
        logger.info(f"Indexing {len(documents)} documents with Haystack")
        indexing_pipeline.run({"embedder": {"documents": documents}})
        # Save document store if in-memory
        if not use_supabase:
            index_path = INDEX_DIR / "haystack_documents.pickle"
            os.makedirs(index_path.parent, exist_ok=True)
            document_store.save(index_path)
            logger.info(f"Saved document store to {index_path}")
        logger.info(f"Successfully indexed {len(documents)} documents with Haystack")
        return True
    except Exception as e:
        logger.error(f"Error indexing with Haystack: {e}")
        import traceback
        traceback.print_exc()
        return False
def index_with_llamaindex(chunks: List[Dict[str, Any]], config: Dict[str, Any]) -> bool:
    """Index content using LlamaIndex"""
    try:
        from llama_index.core import Document, SimpleDirectoryReader, VectorStoreIndex
        from llama_index.core.node_parser import SimpleNodeParser
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        from llama_index.vector_stores.qdrant import QdrantVectorStore
        # Create LlamaIndex documents
        documents = []
        for chunk in chunks:
            doc = Document(
                text=chunk["text"],
                metadata=chunk["metadata"]
            )
            documents.append(doc)
        # Create embedder
        embed_model = HuggingFaceEmbedding(model_name=config["embedding_model"])
        # Create node parser
        node_parser = SimpleNodeParser.from_defaults()
        # Create nodes
        nodes = node_parser.get_nodes_from_documents(documents)
        # Create vector store
        try:
            import qdrant_client
            from qdrant_client.http import models
            # Use Qdrant for vector storage
            qdrant_path = INDEX_DIR / "llamaindex_qdrant"
            os.makedirs(qdrant_path, exist_ok=True)
            client = qdrant_client.QdrantClient(path=str(qdrant_path))
            vector_store = QdrantVectorStore(
                client=client, 
                collection_name="repo_index",
                enable_hybrid=True
            )
            # Create index
            index = VectorStoreIndex(
                nodes=nodes,
                embed_model=embed_model,
                vector_store=vector_store
            )
            logger.info("Created LlamaIndex with Qdrant vector store")
        except ImportError:
            # Fall back to simple in-memory storage
            index = VectorStoreIndex.from_documents(
                documents=documents,
                embed_model=embed_model
            )
            # Save index
            index_path = INDEX_DIR / "llamaindex_storage"
            os.makedirs(index_path, exist_ok=True)
            index.storage_context.persist(persist_dir=str(index_path))
            logger.info(f"Created LlamaIndex with in-memory storage, saved to {index_path}")
        logger.info(f"Successfully indexed {len(documents)} documents with LlamaIndex")
        return True
    except Exception as e:
        logger.error(f"Error indexing with LlamaIndex: {e}")
        import traceback
        traceback.print_exc()
        return False
def index_with_qdrant(chunks: List[Dict[str, Any]], config: Dict[str, Any]) -> bool:
    """Index content using Qdrant directly"""
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http import models
        from sentence_transformers import SentenceTransformer
        # Initialize Qdrant client
        qdrant_path = INDEX_DIR / "qdrant_storage"
        os.makedirs(qdrant_path, exist_ok=True)
        client = QdrantClient(path=str(qdrant_path))
        # Initialize embedding model
        model = SentenceTransformer(config["embedding_model"])
        # Create or recreate collection
        collection_name = "repo_index"
        # Check if collection exists
        try:
            client.get_collection(collection_name)
            client.delete_collection(collection_name)
            logger.info(f"Deleted existing collection: {collection_name}")
        except Exception:
            pass
        # Create collection
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=config["vector_dimensions"], 
                distance=models.Distance.COSINE
            )
        )
        # Prepare data for batch uploading
        vectors = []
        ids = []
        metadatas = []
        # Process chunks in batches of 100
        batch_size = 100
        batch_count = 0
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_texts = [chunk["text"] for chunk in batch]
            # Generate embeddings
            batch_embeddings = model.encode(batch_texts)
            # Prepare data for this batch
            for j, chunk in enumerate(batch):
                vectors.append(batch_embeddings[j].tolist())
                ids.append(i + j)
                metadatas.append(chunk["metadata"])
            # Upload batch
            client.upsert(
                collection_name=collection_name,
                points=models.Batch(
                    ids=ids,
                    vectors=vectors,
                    payloads=metadatas
                )
            )
            logger.info(f"Indexed batch {batch_count} with {len(batch)} documents")
            batch_count += 1
            # Reset for next batch
            vectors = []
            ids = []
            metadatas = []
        logger.info(f"Successfully indexed {len(chunks)} documents with Qdrant")
        return True
    except Exception as e:
        logger.error(f"Error indexing with Qdrant: {e}")
        import traceback
        traceback.print_exc()
        return False
def index_with_simple(chunks: List[Dict[str, Any]], config: Dict[str, Any]) -> bool:
    """Index content using simple file-based storage"""
    try:
        simple_index_path = INDEX_DIR / "simple_index"
        os.makedirs(simple_index_path, exist_ok=True)
        # Create inverted index (simple word -> document mapping)
        inverted_index = {}
        document_store = {}
        # Process each chunk
        for i, chunk in enumerate(chunks):
            doc_id = f"doc_{i}"
            document_store[doc_id] = {
                "text": chunk["text"],
                "metadata": chunk["metadata"]
            }
            # Create simple word index
            words = re.findall(r'\b\w+\b', chunk["text"].lower())
            for word in words:
                if len(word) > 2:  # Skip short words
                    if word not in inverted_index:
                        inverted_index[word] = []
                    if doc_id not in inverted_index[word]:
                        inverted_index[word].append(doc_id)
        # Save the indexes
        with open(simple_index_path / "inverted_index.json", "w") as f:
            json.dump(inverted_index, f)
        with open(simple_index_path / "document_store.json", "w") as f:
            json.dump(document_store, f)
        # Save index metadata
        with open(simple_index_path / "metadata.json", "w") as f:
            json.dump({
                "timestamp": datetime.datetime.now().isoformat(),
                "document_count": len(document_store),
                "word_count": len(inverted_index),
                "config": config
            }, f, indent=2)
        logger.info(f"Successfully created simple index with {len(document_store)} documents and {len(inverted_index)} indexed words")
        return True
    except Exception as e:
        logger.error(f"Error creating simple index: {e}")
        return False
def index_repository(config: Dict[str, Any]) -> bool:
    """Main function to index the repository"""
    start_time = time.time()
    logger.info(f"Starting repository indexing using {config['indexing_system']}")
    # Check if chosen indexing system is supported
    if config["indexing_system"] not in INDEXING_SYSTEMS:
        logger.error(f"Unsupported indexing system: {config['indexing_system']}")
        return False
    # Check/install dependencies
    if not check_dependencies(config["indexing_system"]):
        logger.info(f"Installing dependencies for {config['indexing_system']}")
        if not install_dependencies(config["indexing_system"]):
            logger.error(f"Failed to install required dependencies")
            return False
    # Create index directory if it doesn't exist
    os.makedirs(INDEX_DIR, exist_ok=True)
    # Find files to index
    files = find_files_to_index(config)
    if not files:
        logger.warning("No files found to index")
        return False
    # Process files into chunks
    all_chunks = []
    for file in files:
        chunks = process_file(file, config)
        all_chunks.extend(chunks)
    logger.info(f"Processed {len(files)} files into {len(all_chunks)} chunks")
    # Index using the chosen system
    success = False
    if config["indexing_system"] == "haystack":
        success = index_with_haystack(all_chunks, config)
    elif config["indexing_system"] == "llamaindex":
        success = index_with_llamaindex(all_chunks, config)
    elif config["indexing_system"] == "qdrant":
        success = index_with_qdrant(all_chunks, config)
    elif config["indexing_system"] == "simple":
        success = index_with_simple(all_chunks, config)
    # Save indexing metadata
    if success:
        metadata_path = INDEX_DIR / f"{config['indexing_system']}_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump({
                "timestamp": datetime.datetime.now().isoformat(),
                "indexing_system": config["indexing_system"],
                "file_count": len(files),
                "chunk_count": len(all_chunks),
                "duration_seconds": time.time() - start_time,
                "config": {k: v for k, v in config.items() if k != "exclude_patterns"}  # Don't save regex patterns
            }, f, indent=2)
        logger.info(f"Indexing completed successfully in {time.time() - start_time:.2f} seconds")
    else:
        logger.error("Indexing failed")
    return success
def main():
    """Script entry point"""
    parser = argparse.ArgumentParser(description="Repository Indexer for AI Dev Toolkit")
    parser.add_argument("--system", type=str, choices=INDEXING_SYSTEMS,
                      help=f"Indexing system to use (default: from config or env)")
    parser.add_argument("--force", action="store_true",
                      help="Force reindexing even if recently indexed")
    parser.add_argument("--chunk-size", type=int,
                      help="Size of text chunks for indexing (default: from config)")
    parser.add_argument("--chunk-overlap", type=int,
                      help="Overlap between chunks (default: from config)")
    parser.add_argument("--list-indexed", action="store_true",
                      help="List indexed files and exit")
    args = parser.parse_args()
    # Load configuration
    config = load_config()
    # Override with command line arguments
    if args.system:
        config["indexing_system"] = args.system
    if args.chunk_size:
        config["chunk_size"] = args.chunk_size
    if args.chunk_overlap:
        config["chunk_overlap"] = args.chunk_overlap
    # Check for environment variable override
    if "INDEXING_SYSTEM" in os.environ and not args.system:
        indexing_system = os.environ["INDEXING_SYSTEM"].lower()
        if indexing_system in INDEXING_SYSTEMS:
            config["indexing_system"] = indexing_system
            logger.info(f"Using indexing system from environment: {indexing_system}")
    # Save updated config
    save_config(config)
    # List indexed files if requested
    if args.list_indexed:
        print(f"Repository indexing system: {config['indexing_system']}")
        metadata_path = INDEX_DIR / f"{config['indexing_system']}_metadata.json"
        if metadata_path.exists():
            try:
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                    print(f"Last indexed: {metadata.get('timestamp', 'Unknown')}")
                    print(f"File count: {metadata.get('file_count', 0)}")
                    print(f"Chunk count: {metadata.get('chunk_count', 0)}")
                    print(f"Duration: {metadata.get('duration_seconds', 0):.2f} seconds")
            except Exception as e:
                print(f"Error reading metadata: {e}")
        else:
            print("No index found. Repository has not been indexed yet.")
        sys.exit(0)
    # Check if we need to reindex
    if not args.force:
        metadata_path = INDEX_DIR / f"{config['indexing_system']}_metadata.json"
        if metadata_path.exists():
            try:
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                    last_index = datetime.datetime.fromisoformat(metadata.get("timestamp", "2000-01-01T00:00:00"))
                    days_since_last_index = (datetime.datetime.now() - last_index).total_seconds() / (24 * 3600)
                    if days_since_last_index < config["reindex_period_days"]:
                        logger.info(f"Repository was indexed {days_since_last_index:.1f} days ago, which is less than the configured period of {config['reindex_period_days']} days")
                        logger.info("Skipping indexing. Use --force to reindex anyway.")
                        sys.exit(0)
                    else:
                        logger.info(f"Repository was last indexed {days_since_last_index:.1f} days ago. Proceeding with indexing.")
            except Exception as e:
                logger.warning(f"Error reading metadata, proceeding with indexing: {e}")
    # Run the indexing
    success = index_repository(config)
    sys.exit(0 if success else 1)
if __name__ == "__main__":
    main()
