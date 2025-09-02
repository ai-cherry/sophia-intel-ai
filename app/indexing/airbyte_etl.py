"""
ETL pipeline module for processing data from Neon staging database to Weaviate.

This module provides functionality to:
- Extract data from PostgreSQL using Airbyte
- Process and chunk the extracted data
- Index processed chunks into Weaviate with appropriate metadata
"""
import os
import tempfile
import shutil
import logging
from typing import List, Dict, Any
from airbyte_cdk import AirbyteSource
from app.indexing.chunker import chunk_text
from app.indexing.indexer import index_file
from app.models.metadata import MemoryMetadata
from datetime import datetime

def run_airbyte_etl():
    """Run Airbyte ETL pipeline to process data from Neon staging to Weaviate"""
    # Configure Airbyte source (example for PostgreSQL)
    source = AirbyteSource("airbyte-source-postgres")
    
    # Require all database configuration from environment variables
    try:
        config = {
            "host": os.environ["NEON_DB_HOST"],
            "port": os.environ["NEON_DB_PORT"],
            "username": os.environ["NEON_DB_USER"],
            "password": os.environ["NEON_DB_PASSWORD"],
            "database": os.environ["NEON_DB_NAME"],
            "schema": "public",
            "output_directory": tempfile.mkdtemp()  # Temporary directory for extraction
        }
    except KeyError as exc:
        raise RuntimeError(f"Missing DB configuration: {exc}") from exc
    
    try:
        # Run sync
        source.sync(config)
        
        # Process each file in the output directory
        output_dir = config["output_directory"]
        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            if os.path.isfile(file_path):
                process_file(file_path)
    except Exception as e:
        logging.error(f"Airbyte ETL failed: {str(e)}")
        raise
    finally:
        # Cleanup temporary directory
        shutil.rmtree(config["output_directory"], ignore_errors=True)

def process_file(file_path: str):
    """Process a single file through chunker and indexer with metadata"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        if not content:
            return
            
        # Chunk the content
        chunks = chunk_text(content)
        
        # Process each chunk
        for i, chunk in enumerate(chunks):
            # Create metadata for this chunk
            metadata = MemoryMetadata(
                type="doc",
                source=file_path,
                timestamp=datetime.utcnow(),
                tags=["etl", "processed"]
            )
            
            # Create temporary file for indexing
            temp_file = f"{file_path}.chunk_{i}"
            with open(temp_file, 'w') as f_chunk:
                f_chunk.write(chunk)
            
            # Index the chunk
            index_file(temp_file, metadata=metadata)
            
            # Cleanup temporary file
            os.remove(temp_file)
    except Exception as e:
        logging.error(f"Failed to process file {file_path}: {str(e)}")
        raise

if __name__ == "__main__":
    run_airbyte_etl()