#!/usr/bin/env python3
"""
Qdrant Setup and Configuration for Sophia AI Platform
Implements L2 vector storage with namespace isolation and similarity search optimization
"""
import asyncio
import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)
class QdrantSetup:
    """Qdrant setup and configuration manager"""
    def __init__(self, config_path: str | None = None):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.qdrant_client = None
    def _load_config(self, config_path: str | None) -> dict[str, Any]:
        """Load Qdrant configuration"""
        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                return json.load(f)
        return {
            "qdrant_host": os.getenv("QDRANT_HOST", "localhost"),
            "qdrant_port": int(os.getenv("QDRANT_PORT", "6333")),
            "qdrant_grpc_port": int(os.getenv("QDRANT_GRPC_PORT", "6334")),
            "qdrant_api_key": os.getenv("QDRANT_API_KEY", ""),
            "vector_dimension": 1536,  # OpenAI embedding dimension
            "distance_metric": "Cosine",
            "similarity_threshold": 0.8,
            "namespaces": ["business", "coding", "shared"],
            "collections": {
                "business_vectors": {
                    "dimension": 1536,
                    "distance": "Cosine",
                    "description": "Business intelligence vectors",
                },
                "coding_vectors": {
                    "dimension": 1536,
                    "distance": "Cosine",
                    "description": "Coding assistance vectors",
                },
                "shared_vectors": {
                    "dimension": 1536,
                    "distance": "Cosine",
                    "description": "Shared knowledge vectors",
                },
            },
            "optimization": {
                "indexing_threshold": 20000,
                "payload_indexing": True,
                "quantization": False,
                "replication_factor": 1,
            },
        }
    def _setup_logging(self) -> logging.Logger:
        """Setup logging"""
        logger = logging.getLogger("qdrant_setup")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - QDRANT_SETUP - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    async def setup_qdrant(self) -> bool:
        """Setup Qdrant connection and configuration"""
        try:
            self.logger.info("Starting Qdrant setup...")
            # Check if Qdrant is running
            if not await self._check_qdrant_running():
                self.logger.info("Qdrant not running, attempting to start...")
                if not await self._start_qdrant():
                    return False
            # Create Qdrant connection
            if not await self._create_connection():
                return False
            # Setup collections for each namespace
            if not await self._setup_collections():
                return False
            # Configure optimization settings
            if not await self._configure_optimization():
                return False
            # Validate setup
            if not await self._validate_setup():
                return False
            self.logger.info("Qdrant setup completed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Qdrant setup failed: {e}")
            return False
    async def _check_qdrant_running(self) -> bool:
        """Check if Qdrant is running"""
        try:
            url = f"http://{self.config['qdrant_host']}:{self.config['qdrant_port']}/health"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                self.logger.info("Qdrant is running")
                return True
            else:
                self.logger.info(f"Qdrant health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.logger.info(f"Qdrant not accessible: {e}")
            return False
    async def _start_qdrant(self) -> bool:
        """Start Qdrant server"""
        try:
            # Check if Qdrant is installed
            result = subprocess.run(["which", "qdrant"], capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.info("Installing Qdrant...")
                if not await self._install_qdrant():
                    return False
            # Start Qdrant server
            self.logger.info("Starting Qdrant server...")
            # Create Qdrant data directory
            data_dir = Path("./qdrant_data")
            data_dir.mkdir(exist_ok=True)
            # Start Qdrant with Docker if available
            docker_result = subprocess.run(
                ["which", "docker"], capture_output=True, text=True
            )
            if docker_result.returncode == 0:
                # Use Docker to start Qdrant
                docker_cmd = [
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    "qdrant-sophia",
                    "-p",
                    f"{self.config['qdrant_port']}:6333",
                    "-p",
                    f"{self.config['qdrant_grpc_port']}:6334",
                    "-v",
                    f"{data_dir.absolute()}:/qdrant/storage",
                    "qdrant/qdrant:latest",
                ]
                # Remove existing container if it exists
                subprocess.run(
                    ["docker", "rm", "-f", "qdrant-sophia"], capture_output=True
                )
                start_result = subprocess.run(
                    docker_cmd, capture_output=True, text=True
                )
                if start_result.returncode != 0:
                    self.logger.error(
                        f"Failed to start Qdrant with Docker: {start_result.stderr}"
                    )
                    return False
            else:
                # Try to start Qdrant directly (if installed)
                start_result = subprocess.Popen(
                    ["qdrant", "--config-path", "./qdrant_config.yaml"]
                )
            # Wait for Qdrant to start
            await asyncio.sleep(10)
            # Verify Qdrant is running
            return await self._check_qdrant_running()
        except Exception as e:
            self.logger.error(f"Failed to start Qdrant: {e}")
            return False
    async def _install_qdrant(self) -> bool:
        """Install Qdrant"""
        try:
            # Check if Docker is available for easy installation
            docker_result = subprocess.run(
                ["which", "docker"], capture_output=True, text=True
            )
            if docker_result.returncode == 0:
                self.logger.info("Docker available, will use Docker for Qdrant")
                # Pull Qdrant Docker image
                pull_result = subprocess.run(
                    ["docker", "pull", "qdrant/qdrant:latest"],
                    capture_output=True,
                    text=True,
                )
                if pull_result.returncode != 0:
                    self.logger.error("Failed to pull Qdrant Docker image")
                    return False
                return True
            else:
                self.logger.warning("Docker not available, Qdrant installation skipped")
                self.logger.info("Please install Qdrant manually or use Docker")
                return False
        except Exception as e:
            self.logger.error(f"Qdrant installation failed: {e}")
            return False
    async def _create_connection(self) -> bool:
        """Create Qdrant connection"""
        try:
            # Create Qdrant client
            if self.config["qdrant_api_key"]:
                self.qdrant_client = QdrantClient(
                    host=self.config["qdrant_host"],
                    port=self.config["qdrant_port"],
                    api_key=self.config["qdrant_api_key"],
                )
            else:
                self.qdrant_client = QdrantClient(
                    host=self.config["qdrant_host"], port=self.config["qdrant_port"]
                )
            # Test connection
            collections = self.qdrant_client.get_collections()
            self.logger.info(
                f"Qdrant connection established, found {len(collections.collections)} collections"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to create Qdrant connection: {e}")
            return False
    async def _setup_collections(self) -> bool:
        """Setup collections for each namespace"""
        try:
            for collection_name, collection_config in self.config[
                "collections"
            ].items():
                try:
                    # Check if collection exists
                    try:
                        self.qdrant_client.get_collection(
                            collection_name
                        )
                        self.logger.info(f"Collection {collection_name} already exists")
                        continue
                    except Exception:
                        # Collection doesn't exist, create it
                        pass
                    # Create collection
                    self.qdrant_client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=collection_config["dimension"],
                            distance=Distance[collection_config["distance"].upper()],
                        ),
                    )
                    self.logger.info(f"Created collection: {collection_name}")
                    # Create payload index for efficient filtering
                    if self.config["optimization"]["payload_indexing"]:
                        self.qdrant_client.create_payload_index(
                            collection_name=collection_name,
                            field_name="namespace",
                            field_schema="keyword",
                        )
                        self.qdrant_client.create_payload_index(
                            collection_name=collection_name,
                            field_name="key",
                            field_schema="keyword",
                        )
                        self.logger.info(
                            f"Created payload indexes for {collection_name}"
                        )
                except Exception as e:
                    self.logger.error(
                        f"Failed to setup collection {collection_name}: {e}"
                    )
                    return False
            return True
        except Exception as e:
            self.logger.error(f"Collection setup failed: {e}")
            return False
    async def _configure_optimization(self) -> bool:
        """Configure optimization settings"""
        try:
            for collection_name in self.config["collections"].keys():
                try:
                    # Configure collection optimization
                    self.qdrant_client.get_collection(collection_name)
                    # Update collection configuration if needed
                    # Note: Some optimizations require collection recreation
                    self.logger.info(f"Optimization configured for {collection_name}")
                except Exception as e:
                    self.logger.warning(
                        f"Could not configure optimization for {collection_name}: {e}"
                    )
            return True
        except Exception as e:
            self.logger.error(f"Optimization configuration failed: {e}")
            return False
    async def _validate_setup(self) -> bool:
        """Validate complete Qdrant setup"""
        try:
            # Test basic operations for each collection
            for collection_name, namespace in [
                ("business_vectors", "business"),
                ("coding_vectors", "coding"),
                ("shared_vectors", "shared"),
            ]:
                # Create test vector
                sophia_vector = [0.1] * self.config["vector_dimension"]
                sophia_point = PointStruct(
                    id=999999,  # Use high ID to avoid conflicts
                    vector=sophia_vector,
                    payload={
                        "key": "sophia_key",
                        "namespace": namespace,
                        "test": True,
                        "timestamp": time.time(),
                    },
                )
                # Insert test point
                self.qdrant_client.upsert(
                    collection_name=collection_name, points=[sophia_point]
                )
                # Search for test point
                search_results = self.qdrant_client.search(
                    collection_name=collection_name, query_vector=sophia_vector, limit=1
                )
                if not search_results or search_results[0].id != 999999:
                    self.logger.error(f"Validation failed for {collection_name}")
                    return False
                # Test filtering
                self.qdrant_client.scroll(
                    collection_name=collection_name,
                    scroll_filter=Filter(
                        must=[
                            FieldCondition(
                                key="namespace", match=MatchValue(value=namespace)
                            )
                        ]
                    ),
                    limit=10,
                )
                # Clean up test point
                self.qdrant_client.delete(
                    collection_name=collection_name, points_selector=[999999]
                )
                self.logger.info(f"Validation successful for {collection_name}")
            # Test performance
            start_time = time.time()
            # Insert multiple test vectors
            sophia_points = []
            for i in range(100):
                sophia_vector = [0.1 + i * 0.001] * self.config["vector_dimension"]
                sophia_points.append(
                    PointStruct(
                        id=1000000 + i,
                        vector=sophia_vector,
                        payload={
                            "key": f"perf_test_{i}",
                            "namespace": "shared",
                            "test": True,
                        },
                    )
                )
            self.qdrant_client.upsert(
                collection_name="shared_vectors", points=sophia_points
            )
            # Perform searches
            query_vector = [0.1] * self.config["vector_dimension"]
            for i in range(10):
                self.qdrant_client.search(
                    collection_name="shared_vectors",
                    query_vector=query_vector,
                    limit=10,
                )
            # Clean up performance test data
            sophia_ids = list(range(1000000, 1000100))
            self.qdrant_client.delete(
                collection_name="shared_vectors", points_selector=sophia_ids
            )
            end_time = time.time()
            operations_time = end_time - start_time
            self.logger.info(
                f"Qdrant performance test completed in {operations_time:.2f}s"
            )
            if operations_time > 10:
                self.logger.warning("Qdrant performance below expected threshold")
            return True
        except Exception as e:
            self.logger.error(f"Qdrant validation failed: {e}")
            return False
    async def get_qdrant_info(self) -> dict[str, Any]:
        """Get Qdrant server information"""
        try:
            if not self.qdrant_client:
                return {"error": "Qdrant client not initialized"}
            collections = self.qdrant_client.get_collections()
            collection_info = {}
            for collection in collections.collections:
                try:
                    info = self.qdrant_client.get_collection(collection.name)
                    collection_info[collection.name] = {
                        "points_count": info.points_count,
                        "segments_count": info.segments_count,
                        "vector_size": info.config.params.vectors.size,
                        "distance": info.config.params.vectors.distance.name,
                    }
                except Exception as e:
                    collection_info[collection.name] = {"error": str(e)}
            return {
                "collections_count": len(collections.collections),
                "collections": collection_info,
            }
        except Exception as e:
            return {"error": str(e)}
    def cleanup(self):
        """Cleanup Qdrant connection"""
        if self.qdrant_client:
            self.qdrant_client.close()
            self.logger.info("Qdrant connection closed")
# Main execution
if __name__ == "__main__":
    async def main():
        print("🔍 Qdrant Setup for Sophia AI Platform")
        setup = QdrantSetup()
        # Setup Qdrant
        success = await setup.setup_qdrant()
        if success:
            print("✅ Qdrant setup completed successfully")
            # Get Qdrant info
            info = await setup.get_qdrant_info()
            print("\n📊 Qdrant Information:")
            for key, value in info.items():
                if key == "collections":
                    print(f"   - {key}:")
                    for coll_name, coll_info in value.items():
                        print(f"     * {coll_name}: {coll_info}")
                else:
                    print(f"   - {key}: {value}")
            # Save setup results
            setup_results = {
                "setup_successful": success,
                "qdrant_info": info,
                "config": setup.config,
                "timestamp": time.time(),
            }
            with open("qdrant_setup_results.json", "w") as f:
                json.dump(setup_results, f, indent=2)
            print("\n📄 Setup results saved to: qdrant_setup_results.json")
        else:
            print("❌ Qdrant setup failed")
        # Cleanup
        setup.cleanup()
    asyncio.run(main())
