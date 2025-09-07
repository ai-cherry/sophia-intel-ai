"""
Centralized Vector Database Configuration Manager
Handles connections to Qdrant, Weaviate, Milvus, Redis, and Mem0
"""

import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import redis
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Set up logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import weaviate, but handle gracefully if it fails
try:
    import weaviate
    from weaviate.auth import AuthApiKey

    WEAVIATE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Weaviate not available: {e}")
    WEAVIATE_AVAILABLE = False
    weaviate = None
    AuthApiKey = None

# Try to import mem0
try:
    import mem0

    MEM0_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Mem0 not available: {e}")
    MEM0_AVAILABLE = False
    mem0 = None


class VectorDBType(Enum):
    """Supported vector database types"""

    QDRANT = "qdrant"
    WEAVIATE = "weaviate"
    MILVUS = "milvus"
    REDIS = "redis"
    MEM0 = "mem0"


class MemoryType(Enum):
    """Types of memory storage"""

    SHORT_TERM = "short_term"  # Redis cache
    SEMANTIC = "semantic"  # Vector DB
    LONG_TERM = "long_term"  # Mem0 persistent
    EPISODIC = "episodic"  # Event-based memory


@dataclass
class VectorDBConfig:
    """Configuration for each vector database"""

    url: str
    api_key: Optional[str] = None
    collection_name: str = "sophia_vectors"
    dimension: int = 1536  # OpenAI embedding dimension
    metric: str = "cosine"
    additional_config: dict[str, Any] = None


class VectorDatabaseManager:
    """Singleton manager for all vector database operations"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Load configurations from environment
        self.configs = {
            VectorDBType.QDRANT: VectorDBConfig(
                url=os.getenv(
                    "QDRANT_URL",
                    "https://a2a5dc3b-bf37-4907-9398-d49f5c6813ed.us-west-2-0.aws.cloud.qdrant.io",
                ),
                api_key=os.getenv(
                    "QDRANT_API_KEY",
                    "ccabdaed-b564-4157-8846-b8f227c7f29b|hRnj-WYa5pxZlPuu2S2LmrX2LziBOdChyLP5Hq578N-HIi16EZIshA",
                ),
                collection_name=os.getenv("QDRANT_COLLECTION", "sophia_vectors"),
                additional_config={
                    "management_key": os.getenv(
                        "QDRANT_MANAGEMENT_KEY",
                        "bff3e4ed-e0eb-42a4-b182-ed4785aade38|W6JDZ09cvVxer84XEgUuEnHhn81KRvowiQDWV0rF5gDeW5RUMHdQcQ",
                    ),
                    "account_id": os.getenv(
                        "QDRANT_ACCOUNT_ID", "8d8807c8-b27d-4652-a6b6-949a9ec43dd1"
                    ),
                },
            ),
            VectorDBType.WEAVIATE: VectorDBConfig(
                url=os.getenv(
                    "WEAVIATE_URL", "https://w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud"
                ),
                api_key=os.getenv("WEAVIATE_API_KEY", "VMKjGMQUnXQIDiFOciZZOhr7amBfCHMh7hNf"),
                collection_name="SophiaVectors",
                additional_config={
                    "grpc_url": os.getenv(
                        "WEAVIATE_GRPC_URL",
                        "grpc-w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud",
                    )
                },
            ),
            VectorDBType.REDIS: VectorDBConfig(
                url=f"{os.getenv('REDIS_HOST', 'redis-15014.fcrce172.us-east-1-1.ec2.redns.redis-cloud.com')}:{os.getenv('REDIS_PORT', '15014')}",
                api_key=os.getenv(
                    "REDIS_USER_KEY", "S666q3cr9wmzpetc6iud02iqv26774azveodh2pfadrd7pgq8l7"
                ),
                additional_config={
                    "account_key": os.getenv(
                        "REDIS_ACCOUNT_KEY", "A4mmxx43yms087hucu51sxbau5mi9hmnz6u33k43mpauhof6rz2"
                    )
                },
            ),
            VectorDBType.MEM0: VectorDBConfig(
                url="https://api.mem0.ai",
                api_key=os.getenv("MEM0_API_KEY", "m0-migu5eMnfwT41nhTgVHsCnSAifVtOf3WIFz2vmQc"),
                collection_name=os.getenv("MEM0_ACCOUNT_NAME", "scoobyjava-default-org"),
                additional_config={
                    "account_id": os.getenv(
                        "MEM0_ACCOUNT_ID", "org_gHuEO2H7ymIIgivcWeKI2psRFHUnbZ54RQNYVb4T"
                    )
                },
            ),
        }

        # Initialize clients
        self.clients = {}
        self._initialize_clients()

        self._initialized = True

    def _initialize_clients(self):
        """Initialize connections to all configured vector databases"""

        # Initialize Qdrant
        try:
            config = self.configs[VectorDBType.QDRANT]
            self.clients[VectorDBType.QDRANT] = QdrantClient(
                url=config.url, api_key=config.api_key, timeout=30
            )
            logger.info("✓ Qdrant client initialized")
        except Exception as e:
            logger.error(f"✗ Failed to initialize Qdrant: {e}")
            self.clients[VectorDBType.QDRANT] = None

        # Initialize Weaviate
        if WEAVIATE_AVAILABLE:
            try:
                config = self.configs[VectorDBType.WEAVIATE]
                auth_config = AuthApiKey(api_key=config.api_key)
                self.clients[VectorDBType.WEAVIATE] = weaviate.Client(
                    url=config.url,
                    auth_client_secret=auth_config,
                    additional_headers={"X-Weaviate-Api-Key": config.api_key},
                )
                logger.info("✓ Weaviate client initialized")
            except Exception as e:
                logger.error(f"✗ Failed to initialize Weaviate: {e}")
                self.clients[VectorDBType.WEAVIATE] = None
        else:
            logger.warning("Weaviate library not available, skipping initialization")
            self.clients[VectorDBType.WEAVIATE] = None

        # Initialize Redis
        try:
            config = self.configs[VectorDBType.REDIS]
            host, port = config.url.split(":")
            self.clients[VectorDBType.REDIS] = redis.Redis(
                host=host,
                port=int(port),
                password=config.api_key,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            self.clients[VectorDBType.REDIS].ping()
            logger.info("✓ Redis client initialized")
        except Exception as e:
            logger.error(f"✗ Failed to initialize Redis: {e}")
            self.clients[VectorDBType.REDIS] = None

        # Initialize Mem0
        if MEM0_AVAILABLE:
            try:
                config = self.configs[VectorDBType.MEM0]
                self.clients[VectorDBType.MEM0] = mem0.Memory(api_key=config.api_key)
                logger.info("✓ Mem0 client initialized")
            except Exception as e:
                logger.error(f"✗ Failed to initialize Mem0: {e}")
                self.clients[VectorDBType.MEM0] = None
        else:
            logger.warning("Mem0 library not available, skipping initialization")
            self.clients[VectorDBType.MEM0] = None

    def get_client(self, db_type: VectorDBType):
        """Get a specific vector database client"""
        return self.clients.get(db_type)

    def create_collection(self, db_type: VectorDBType, collection_name: Optional[str] = None):
        """Create a collection in the specified vector database"""
        config = self.configs[db_type]
        collection = collection_name or config.collection_name

        if db_type == VectorDBType.QDRANT:
            client = self.clients[db_type]
            if client:
                try:
                    client.create_collection(
                        collection_name=collection,
                        vectors_config=VectorParams(
                            size=config.dimension, distance=Distance.COSINE
                        ),
                    )
                    logger.info(f"✓ Created Qdrant collection: {collection}")
                    return True
                except Exception as e:
                    logger.error(f"✗ Failed to create Qdrant collection: {e}")
                    return False

        elif db_type == VectorDBType.WEAVIATE:
            client = self.clients[db_type]
            if client:
                try:
                    class_obj = {
                        "class": collection,
                        "vectorizer": "text2vec-openai",
                        "moduleConfig": {
                            "text2vec-openai": {"model": "text-embedding-ada-002", "type": "text"}
                        },
                    }
                    client.schema.create_class(class_obj)
                    logger.info(f"✓ Created Weaviate class: {collection}")
                    return True
                except Exception as e:
                    logger.error(f"✗ Failed to create Weaviate class: {e}")
                    return False

        return False

    def store_vector(
        self,
        db_type: VectorDBType,
        vector: list[float],
        metadata: dict[str, Any],
        collection_name: Optional[str] = None,
    ):
        """Store a vector with metadata in the specified database"""
        config = self.configs[db_type]
        collection = collection_name or config.collection_name

        if db_type == VectorDBType.QDRANT:
            client = self.clients[db_type]
            if client:
                try:
                    import uuid

                    from qdrant_client.models import PointStruct

                    point = PointStruct(id=str(uuid.uuid4()), vector=vector, payload=metadata)

                    client.upsert(collection_name=collection, points=[point])
                    logger.info(f"✓ Stored vector in Qdrant collection: {collection}")
                    return True
                except Exception as e:
                    logger.error(f"✗ Failed to store vector in Qdrant: {e}")
                    return False

        elif db_type == VectorDBType.REDIS:
            client = self.clients[db_type]
            if client:
                try:

                    key = f"vector:{metadata.get('id', 'unknown')}"

                    # Store vector as JSON
                    data = {"vector": vector, "metadata": metadata}
                    client.set(key, json.dumps(data))

                    # Add to index for searching
                    client.zadd(f"{collection}:index", {key: 0})

                    logger.info(f"✓ Stored vector in Redis: {key}")
                    return True
                except Exception as e:
                    logger.error(f"✗ Failed to store vector in Redis: {e}")
                    return False

        elif db_type == VectorDBType.MEM0:
            client = self.clients[db_type]
            if client:
                try:
                    # Mem0 handles vectorization internally
                    client.add(
                        messages=metadata.get("content", ""),
                        user_id=metadata.get("user_id", "system"),
                        metadata=metadata,
                    )
                    logger.info("✓ Stored memory in Mem0")
                    return True
                except Exception as e:
                    logger.error(f"✗ Failed to store in Mem0: {e}")
                    return False

        return False

    def search_vectors(
        self,
        db_type: VectorDBType,
        query_vector: list[float],
        top_k: int = 5,
        collection_name: Optional[str] = None,
    ):
        """Search for similar vectors in the specified database"""
        config = self.configs[db_type]
        collection = collection_name or config.collection_name

        if db_type == VectorDBType.QDRANT:
            client = self.clients[db_type]
            if client:
                try:
                    results = client.search(
                        collection_name=collection, query_vector=query_vector, limit=top_k
                    )
                    logger.info(f"✓ Searched Qdrant collection: {collection}")
                    return results
                except Exception as e:
                    logger.error(f"✗ Failed to search Qdrant: {e}")
                    return []

        elif db_type == VectorDBType.WEAVIATE:
            client = self.clients[db_type]
            if client:
                try:
                    results = (
                        client.query.get(collection, ["content", "metadata"])
                        .with_near_vector({"vector": query_vector})
                        .with_limit(top_k)
                        .do()
                    )
                    logger.info(f"✓ Searched Weaviate class: {collection}")
                    return results
                except Exception as e:
                    logger.error(f"✗ Failed to search Weaviate: {e}")
                    return []

        elif db_type == VectorDBType.MEM0:
            client = self.clients[db_type]
            if client:
                try:
                    # Mem0 uses text queries, not vectors
                    results = client.search(
                        query=query_vector if isinstance(query_vector, str) else "", limit=top_k
                    )
                    logger.info("✓ Searched Mem0 memories")
                    return results
                except Exception as e:
                    logger.error(f"✗ Failed to search Mem0: {e}")
                    return []

        return []

    def test_connection(self, db_type: VectorDBType) -> bool:
        """Test connection to a specific vector database"""
        client = self.clients.get(db_type)

        if db_type == VectorDBType.QDRANT and client:
            try:
                client.get_collections()
                logger.info("✓ Qdrant connection successful")
                return True
            except Exception as e:
                logger.error(f"✗ Qdrant connection failed: {e}")
                return False

        elif db_type == VectorDBType.WEAVIATE and client:
            try:
                client.schema.get()
                logger.info("✓ Weaviate connection successful")
                return True
            except Exception as e:
                logger.error(f"✗ Weaviate connection failed: {e}")
                return False

        elif db_type == VectorDBType.REDIS and client:
            try:
                client.ping()
                logger.info("✓ Redis connection successful")
                return True
            except Exception as e:
                logger.error(f"✗ Redis connection failed: {e}")
                return False

        elif db_type == VectorDBType.MEM0 and client:
            try:
                # Test by getting memories (should return empty if none exist)
                client.get_all(user_id="test")
                logger.info("✓ Mem0 connection successful")
                return True
            except Exception as e:
                logger.error(f"✗ Mem0 connection failed: {e}")
                return False

        return False

    def test_all_connections(self) -> dict[str, bool]:
        """Test all vector database connections"""
        results = {}
        for db_type in VectorDBType:
            if db_type != VectorDBType.MILVUS:  # Skip Milvus for now
                results[db_type.value] = self.test_connection(db_type)
        return results

    def get_status(self) -> dict[str, Any]:
        """Get status of all vector databases"""
        status = {}
        for db_type, config in self.configs.items():
            status[db_type.value] = {
                "url": config.url[:30] + "..." if len(config.url) > 30 else config.url,
                "configured": bool(config.api_key),
                "connected": self.clients.get(db_type) is not None,
                "collection": config.collection_name,
            }
        return status


# Singleton instance
vector_db_manager = VectorDatabaseManager()
