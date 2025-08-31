"""
Vector Store Infrastructure for Sophia Intel AI
Deploys Weaviate and consolidated embedding services with 2025 SOTA models.
"""

import pulumi
from pulumi import StackReference, Output
import sys
import os

# Add shared components to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from shared import FlyApp, FlyAppConfig, WeaviateVector

def main():
    """Deploy vector store infrastructure."""
    
    config = pulumi.Config()
    environment = config.get("environment") or "dev"
    weaviate_memory_gb = config.get_int("weaviate_memory_gb") or 2
    cache_size = config.get_int("embedding_cache_size") or 10000
    
    # Reference other stacks
    shared_stack = StackReference(f"shared-{environment}")
    database_stack = StackReference(f"database-{environment}")
    
    # Deploy Weaviate Vector Database
    weaviate_db = WeaviateVector("weaviate-main")
    
    # Vector Store Service Configuration
    vector_service_config = FlyAppConfig(
        name=f"sophia-vector-store-{environment}",
        image="ghcr.io/sophia-intel-ai/vector-store:latest",
        port=8080,
        scale=2,  # Multiple instances for availability
        memory_mb=2048,  # More memory for embedding operations
        cpu_cores=2.0,   # More CPU for vector processing
        env_vars={
            "ENVIRONMENT": environment,
            "LOG_LEVEL": "INFO" if environment == "prod" else "DEBUG",
            
            # Database connections
            "WEAVIATE_URL": weaviate_db.weaviate_url,
            "WEAVIATE_API_KEY": weaviate_db.weaviate_api_key,
            "REDIS_URL": database_stack.get_output("redis_url"),
            
            # Modern Embedding Configuration (2025 SOTA)
            "EMBEDDING_TIER_S_MODEL": "voyage-3-large",  # Superior quality
            "EMBEDDING_TIER_A_MODEL": "cohere/embed-multilingual-v3.0",  # Advanced
            "EMBEDDING_TIER_B_MODEL": "BAAI/bge-base-en-v1.5",  # Basic/fast
            
            # Intelligent routing thresholds
            "TOKEN_THRESHOLD_S": "4096",  # Use Tier-S above this
            "TOKEN_THRESHOLD_A": "1024",  # Use Tier-A above this
            "ENABLE_QUANTIZATION": "true",
            
            # Caching configuration
            "EMBEDDING_CACHE_SIZE": str(cache_size),
            "CACHE_TTL_HOURS": "24",
            "BATCH_SIZE_S": "16",
            "BATCH_SIZE_A": "32", 
            "BATCH_SIZE_B": "128",
            
            # Gateway integration
            "PORTKEY_API_KEY": pulumi.Config().require_secret("portkey_api_key"),
            "PORTKEY_BASE_URL": "https://api.portkey.ai/v1",
            
            # Performance tuning
            "MAX_CONCURRENT_REQUESTS": "50",
            "REQUEST_TIMEOUT_SECONDS": "120"
        }
    )
    
    # Deploy Vector Store Service
    vector_store_service = FlyApp("vector-store-service", vector_service_config)
    
    # Export outputs for other stacks
    pulumi.export("vector_store_url", vector_store_service.public_url)
    pulumi.export("vector_store_internal_url", vector_store_service.internal_url)
    pulumi.export("weaviate_url", weaviate_db.weaviate_url)
    pulumi.export("weaviate_collections", weaviate_db.collections)
    
    # Embedding service configuration
    pulumi.export("embedding_config", {
        "three_tier_routing": {
            "tier_s": {
                "model": "voyage-3-large",
                "dimension": 1024,
                "max_tokens": 8192,
                "use_cases": ["production", "critical", "security", "financial"]
            },
            "tier_a": {
                "model": "cohere/embed-multilingual-v3.0", 
                "dimension": 768,
                "max_tokens": 2048,
                "use_cases": ["standard", "multilingual", "semantic_search"]
            },
            "tier_b": {
                "model": "BAAI/bge-base-en-v1.5",
                "dimension": 768,
                "max_tokens": 512,
                "use_cases": ["fast", "bulk_processing", "development"]
            }
        },
        "intelligent_routing": {
            "quality_keywords": ["production", "critical", "security", "financial"],
            "speed_keywords": ["test", "debug", "quick", "draft"],
            "language_priorities": {
                "python": "tier_s",
                "rust": "tier_s", 
                "go": "tier_s",
                "typescript": "tier_a",
                "javascript": "tier_a",
                "markdown": "tier_b"
            }
        },
        "performance": {
            "cache_enabled": True,
            "quantization_enabled": True,
            "batch_processing": True,
            "parallel_execution": True
        }
    })
    
    # Vector search capabilities
    pulumi.export("search_capabilities", {
        "hybrid_search": {
            "vector_search": True,
            "bm25_search": True,
            "reranking": True,
            "cross_encoder": True
        },
        "similarity_metrics": [
            "cosine",
            "euclidean",
            "dot_product"
        ],
        "search_features": [
            "semantic_search",
            "similarity_search", 
            "hybrid_retrieval",
            "multi_vector_search",
            "filtered_search"
        ]
    })
    
    pulumi.export("environment", environment)

if __name__ == "__main__":
    main()