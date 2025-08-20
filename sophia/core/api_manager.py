"""
SOPHIA V4 API Manager
Central manager for all external services used by Sophia.
Initializes clients for databases, vector stores, secret managers, and other APIs.
"""

import os
import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
import json

logger = logging.getLogger(__name__)

@dataclass
class ServiceClient:
    """Wrapper for service client instances."""
    name: str
    client: Any
    api_key_env_var: str
    endpoint: str
    status: str = "unknown"

class SOPHIAAPIManager:
    """
    Central manager for all external services used by Sophia.
    Initializes clients for databases, vector stores, secret managers, and other APIs.
    """

    def __init__(self):
        """Initialize all service clients."""
        logger.info("Initializing SOPHIA API Manager...")
        
        # Database connections
        self.postgres_pool = None
        self.redis_client = None
        self.qdrant_client = None
        self.weaviate_client = None
        self.neo4j_driver = None
        self.mem0_client = None
        
        # Service clients registry
        self.service_clients: Dict[str, ServiceClient] = {}
        
        # Initialize all services
        self._init_databases()
        self._init_vector_stores()
        self._init_search_services()
        self._init_business_services()
        self._init_ai_services()
        self._init_infrastructure_services()
        self._init_data_services()
        
        logger.info("SOPHIA API Manager initialization complete")

    def _init_databases(self):
        """Initialize database connections."""
        try:
            # PostgreSQL (Neon)
            self.postgres_pool = self._init_postgres()
            
            # Redis
            self.redis_client = self._init_redis()
            
            logger.info("Database connections initialized")
        except Exception as e:
            logger.error(f"Failed to initialize databases: {e}")

    def _init_vector_stores(self):
        """Initialize vector database connections."""
        try:
            # Qdrant
            self.qdrant_client = self._init_qdrant()
            
            # Weaviate
            self.weaviate_client = self._init_weaviate()
            
            # Neo4j
            self.neo4j_driver = self._init_neo4j()
            
            logger.info("Vector stores initialized")
        except Exception as e:
            logger.error(f"Failed to initialize vector stores: {e}")

    def _init_search_services(self):
        """Initialize search and research services."""
        search_services = {
            "serper": {
                "api_key_env": "SERPER_API_KEY",
                "endpoint": "https://google.serper.dev/search"
            },
            "bright_data": {
                "api_key_env": "BRIGHT_DATA_API_KEY", 
                "endpoint": "https://api.brightdata.com"
            },
            "zenrows": {
                "api_key_env": "ZENROWS_API_KEY",
                "endpoint": "https://api.zenrows.com/v1/"
            },
            "tavily": {
                "api_key_env": "TAVILY_API_KEY",
                "endpoint": "https://api.tavily.com"
            },
            "apify": {
                "api_key_env": "APIFY_API_TOKEN",
                "endpoint": "https://api.apify.com/v2"
            }
        }
        
        for service_name, config in search_services.items():
            api_key = os.getenv(config["api_key_env"])
            if api_key:
                self.service_clients[service_name] = ServiceClient(
                    name=service_name,
                    client=None,  # Will be initialized on first use
                    api_key_env_var=config["api_key_env"],
                    endpoint=config["endpoint"],
                    status="configured"
                )
                logger.info(f"Search service {service_name} configured")

    def _init_business_services(self):
        """Initialize business service integrations."""
        business_services = {
            "gong": {
                "api_key_env": "GONG_ACCESS_KEY",
                "endpoint": "https://api.gong.io/v2"
            },
            "hubspot": {
                "api_key_env": "HUBSPOT_API_KEY",
                "endpoint": "https://api.hubapi.com"
            },
            "slack": {
                "api_key_env": "SLACK_BOT_TOKEN",
                "endpoint": "https://slack.com/api"
            },
            "salesforce": {
                "api_key_env": "SALESFORCE_ACCESS_TOKEN",
                "endpoint": "https://your-org.salesforce.com"
            },
            "notion": {
                "api_key_env": "NOTION_API_KEY",
                "endpoint": "https://api.notion.com/v1"
            }
        }
        
        for service_name, config in business_services.items():
            api_key = os.getenv(config["api_key_env"])
            if api_key:
                self.service_clients[service_name] = ServiceClient(
                    name=service_name,
                    client=None,
                    api_key_env_var=config["api_key_env"],
                    endpoint=config["endpoint"],
                    status="configured"
                )
                logger.info(f"Business service {service_name} configured")

    def _init_ai_services(self):
        """Initialize AI and ML services."""
        ai_services = {
            "openrouter": {
                "api_key_env": "OPENROUTER_API_KEY",
                "endpoint": "https://openrouter.ai/api/v1"
            },
            "huggingface": {
                "api_key_env": "HUGGINGFACE_API_TOKEN",
                "endpoint": "https://api-inference.huggingface.co"
            },
            "groq": {
                "api_key_env": "GROQ_API_KEY",
                "endpoint": "https://api.groq.com/openai/v1"
            },
            "together": {
                "api_key_env": "TOGETHER_AI_API_KEY",
                "endpoint": "https://api.together.xyz/v1"
            },
            "arize": {
                "api_key_env": "ARIZE_API_KEY",
                "endpoint": "https://app.arize.com/v1"
            }
        }
        
        for service_name, config in ai_services.items():
            api_key = os.getenv(config["api_key_env"])
            if api_key:
                self.service_clients[service_name] = ServiceClient(
                    name=service_name,
                    client=None,
                    api_key_env_var=config["api_key_env"],
                    endpoint=config["endpoint"],
                    status="configured"
                )
                logger.info(f"AI service {service_name} configured")

    def _init_infrastructure_services(self):
        """Initialize infrastructure and deployment services."""
        # Lambda Labs IPs
        lambda_ips_str = os.getenv("LAMBDA_IPS", "")
        self.lambda_ips = [ip.strip() for ip in lambda_ips_str.split(",") if ip.strip()]
        
        # Fly.io app IDs
        fly_apps_str = os.getenv("FLY_APP_IDS", "")
        self.fly_app_ids = [app.strip() for app in fly_apps_str.split(",") if app.strip()]
        
        # GitHub
        github_token = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_PAT")
        if github_token:
            self.service_clients["github"] = ServiceClient(
                name="github",
                client=None,
                api_key_env_var="GITHUB_TOKEN",
                endpoint="https://api.github.com",
                status="configured"
            )
        
        # Kong Konnect
        kong_token = os.getenv("KONG_KONNECT_TOKEN")
        if kong_token:
            self.service_clients["kong"] = ServiceClient(
                name="kong",
                client=None,
                api_key_env_var="KONG_KONNECT_TOKEN",
                endpoint="https://us.api.konghq.com",
                status="configured"
            )

    def _init_data_services(self):
        """Initialize data integration services."""
        # Airbyte
        airbyte_client_id = os.getenv("AIRBYTE_CLIENT_ID")
        if airbyte_client_id:
            self.service_clients["airbyte"] = ServiceClient(
                name="airbyte",
                client=None,
                api_key_env_var="AIRBYTE_CLIENT_ID",
                endpoint="https://api.airbyte.com/v1",
                status="configured"
            )
        
        # N8N
        n8n_api_key = os.getenv("N8N_API_KEY")
        if n8n_api_key:
            self.service_clients["n8n"] = ServiceClient(
                name="n8n",
                client=None,
                api_key_env_var="N8N_API_KEY",
                endpoint=os.getenv("N8N_WEBHOOK_URL", "https://your-n8n-instance.com"),
                status="configured"
            )

    def _init_postgres(self):
        """Initialize connection to Neon PostgreSQL."""
        try:
            import asyncpg
            
            dsn = os.getenv("NEON_POSTGRES_DSN") or os.getenv("DATABASE_URL")
            if not dsn:
                logger.warning("No PostgreSQL DSN found")
                return None
            
            # Return connection pool (will be created async)
            return dsn
        except ImportError:
            logger.warning("asyncpg not installed. Run: pip install asyncpg")
            return None

    def _init_redis(self):
        """Initialize Redis connection."""
        try:
            import redis
            
            redis_url = os.getenv("REDIS_URL")
            if not redis_url:
                logger.warning("No Redis URL found")
                return None
            
            return redis.from_url(redis_url)
        except ImportError:
            logger.warning("redis not installed. Run: pip install redis")
            return None

    def _init_qdrant(self):
        """Initialize Qdrant client."""
        try:
            from qdrant_client import QdrantClient
            
            qdrant_url = os.getenv("QDRANT_URL")
            qdrant_api_key = os.getenv("QDRANT_API_KEY")
            
            if not qdrant_url:
                logger.warning("No Qdrant URL found")
                return None
            
            return QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        except ImportError:
            logger.warning("qdrant-client not installed. Run: pip install qdrant-client")
            return None

    def _init_weaviate(self):
        """Initialize Weaviate client."""
        try:
            import weaviate
            
            weaviate_url = os.getenv("WEAVIATE_URL")
            weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
            
            if not weaviate_url:
                logger.warning("No Weaviate URL found")
                return None
            
            # TODO: Implement proper Weaviate client initialization
            return None
        except ImportError:
            logger.warning("weaviate-client not installed. Run: pip install weaviate-client")
            return None

    def _init_neo4j(self):
        """Initialize Neo4j driver."""
        try:
            from neo4j import GraphDatabase
            
            neo4j_uri = os.getenv("NEO4J_URI")
            neo4j_user = os.getenv("NEO4J_USER")
            neo4j_password = os.getenv("NEO4J_PASSWORD")
            
            if not all([neo4j_uri, neo4j_user, neo4j_password]):
                logger.warning("Neo4j credentials not complete")
                return None
            
            return GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        except ImportError:
            logger.warning("neo4j not installed. Run: pip install neo4j")
            return None

    def _init_mem0(self):
        """Initialize Mem0 client."""
        try:
            # TODO: Implement Mem0 client initialization
            mem0_api_key = os.getenv("MEM0_API_KEY")
            if not mem0_api_key:
                logger.warning("No Mem0 API key found")
                return None
            
            # Placeholder for mem0 client
            return None
        except ImportError:
            logger.warning("mem0 not installed")
            return None

    # Service interaction methods
    async def query_postgres(self, sql: str, *params):
        """Execute a SQL query against Neon PostgreSQL."""
        if not self.postgres_pool:
            raise RuntimeError("PostgreSQL not configured")
        
        try:
            import asyncpg
            
            if isinstance(self.postgres_pool, str):
                # Create pool on first use
                self.postgres_pool = await asyncpg.create_pool(self.postgres_pool)
            
            async with self.postgres_pool.acquire() as conn:
                return await conn.fetch(sql, *params)
        except Exception as e:
            logger.error(f"PostgreSQL query failed: {e}")
            raise

    def upsert_qdrant(self, collection: str, vectors: list, payloads: list):
        """Upsert vectors into Qdrant."""
        if not self.qdrant_client:
            raise RuntimeError("Qdrant not configured")
        
        try:
            points = [
                {"id": idx, "vector": vec, "payload": payloads[idx]} 
                for idx, vec in enumerate(vectors)
            ]
            return self.qdrant_client.upsert(collection_name=collection, points=points)
        except Exception as e:
            logger.error(f"Qdrant upsert failed: {e}")
            raise

    def get_redis(self, key: str):
        """Retrieve a value from Redis."""
        if not self.redis_client:
            raise RuntimeError("Redis not configured")
        
        try:
            return self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Redis get failed: {e}")
            raise

    def set_redis(self, key: str, value: str, ex: Optional[int] = None):
        """Set a value in Redis."""
        if not self.redis_client:
            raise RuntimeError("Redis not configured")
        
        try:
            return self.redis_client.set(key, value, ex=ex)
        except Exception as e:
            logger.error(f"Redis set failed: {e}")
            raise

    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all configured services."""
        status = {
            "databases": {
                "postgres": bool(self.postgres_pool),
                "redis": bool(self.redis_client),
                "qdrant": bool(self.qdrant_client),
                "weaviate": bool(self.weaviate_client),
                "neo4j": bool(self.neo4j_driver),
                "mem0": bool(self.mem0_client)
            },
            "infrastructure": {
                "lambda_ips": len(self.lambda_ips),
                "fly_apps": len(self.fly_app_ids)
            },
            "services": {
                name: client.status for name, client in self.service_clients.items()
            }
        }
        return status

    def get_configured_services(self) -> List[str]:
        """Get list of all configured service names."""
        services = list(self.service_clients.keys())
        
        # Add database services
        if self.postgres_pool:
            services.append("postgres")
        if self.redis_client:
            services.append("redis")
        if self.qdrant_client:
            services.append("qdrant")
        if self.weaviate_client:
            services.append("weaviate")
        if self.neo4j_driver:
            services.append("neo4j")
        if self.mem0_client:
            services.append("mem0")
            
        return sorted(services)

    async def health_check(self) -> Dict[str, Any]:
        """Perform health checks on all configured services."""
        health_status = {}
        
        # Check databases
        if self.redis_client:
            try:
                self.redis_client.ping()
                health_status["redis"] = "healthy"
            except Exception as e:
                health_status["redis"] = f"unhealthy: {e}"
        
        if self.qdrant_client:
            try:
                self.qdrant_client.get_collections()
                health_status["qdrant"] = "healthy"
            except Exception as e:
                health_status["qdrant"] = f"unhealthy: {e}"
        
        # TODO: Add health checks for other services
        
        return health_status

