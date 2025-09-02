import os
from typing import List, Dict, Any
from airbyte_cdk import AirbyteSource, ConfiguredAirbyteStream
from app.indexing.chunker import chunk_text

def run_airbyte_etl():
    """Run Airbyte ETL pipeline to process data from Neon staging to Weaviate"""
    # Configure Airbyte source (example for PostgreSQL)
    source = AirbyteSource("airbyte-source-postgres")
    config = {
        "host": os.getenv("NEON_DB_HOST", "localhost"),
        "port": os.getenv("NEON_DB_PORT", "5432"),
        "username": os.getenv("NEON_DB_USER", "postgres"),
        "password": os.getenv("NEON_DB_PASSWORD", "password"),
        "database": os.getenv("NEON_DB_NAME", "staging"),
        "schema": "public"
    }
    
    # Run sync
    source.sync(config)
    
    # Process each stream
    for stream in source.streams:
        for record in stream.records:
            process_record(record)

def process_record(record: Dict[str, Any]):
    """Process a single record into Weaviate-compatible format"""
    # Extract text content
    text = record.get("content", "")
    if not text:
        return
    
    # Chunk text
    chunks = chunk_text(text)
    
    # Convert to SqlEntity nodes (placeholder)
    for chunk in chunks:
        # This would be replaced with actual Weaviate upsert
        print(f"Processing chunk: {chunk[:100]}...")

if __name__ == "__main__":
    run_airbyte_etl()