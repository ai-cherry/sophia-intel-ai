"""
Vector Store Infrastructure for Sophia Intel AI
Deploys Weaviate and consolidated embedding services with 2025 SOTA models.

Following ADR-006: Configuration Management Standardization
- Uses Pulumi ESC environments for unified configuration
- Environment-specific scaling and model configurations
- Encrypted secret management for API keys
"""

import pulumi
from pulumi import StackReference, Output
import sys
import os

# Add shared components to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from shared import FlyApp, FlyAppConfig, WeaviateVector

def main():
    """Deploy vector store infrastructure using ESC configuration."""
    
    # Get environment from ESC
    environment = os.getenv("PULUMI_ESC_ENVIRONMENT", "dev")
    
    # Environment-specific configuration using ESC
    if environment == "prod":
        weaviate_memory_gb = 16
        cache_size = 100000
        vector_instances = 3
        vector_memory_mb = 4096
        vector_cpu_cores = 4.0
    elif environment == "staging":
        weaviate_memory_gb = 4
        cache_size = 50000
        vector_instances = 2
        vector_memory_mb = 2048
        vector_cpu_cores = 2.0
    else:  # dev
        weaviate_memory_gb = 2
        cache_size = 10000
        vector_instances = 1
        vector_memory_mb = 1024
        vector_cpu_cores = 1.0
    
    # Reference other stacks
    shared_stack = StackReference(f"shared-{environment}")
    database_stack = StackReference(f"database-{environment}")
    
    # Deploy Weaviate Vector Database
    weaviate_db = WeaviateVector("weaviate-main")
    
    # Vector Store Service Configuration using ESC
    vector_service_config = FlyAppConfig(
        name=f"sophia-vector-store-{environment}",
        image="ghcr.io/sophia-intel-ai/vector-store:latest",
        port=8080,
        scale=vector_instances,
        memory_mb=vector_memory_mb,
        cpu_cores=vector_cpu_cores,
        env_vars={
            "ENVIRONMENT": environment,
            "LOG_LEVEL": "INFO" if environment == "prod" else "DEBUG",
            
            # Database connections from ESC
            "WEAVIATE_URL": weaviate_db.weaviate_url,
            "WEAVIATE_API_KEY": weaviate_db.weaviate_api_key,
            "WEAVIATE_BATCH_SIZE": weaviate_db.batch_size,
            "WEAVIATE_TIMEOUT": weaviate_db.timeout,
            "REDIS_URL": database_stack.get_output("redis_url"),
            
            # Modern Embedding Configuration (2025 SOTA) from ESC
            "EMBEDDING_TIER_S_MODEL": pulumi.Config().get("EMBED_MODEL_TIER_S") or "voyage-3-large",
            "EMBEDDING_TIER_A_MODEL": pulumi.Config().get("EMBED_MODEL_TIER_A") or "cohere/embed-multilingual-v3.0",
            "EMBEDDING_TIER_B_MODEL": pulumi.Config().get("EMBED_MODEL_TIER_B") or "BAAI/bge-base-en-v1.5",
            
            # Intelligent routing thresholds (environment-aware)
            "TOKEN_THRESHOLD_S": "8192" if environment == "prod" else "4096",
            "TOKEN_THRESHOLD_A": "2048" if environment == "prod" else "1024",
            "ENABLE_QUANTIZATION": "true",
            "ENABLE_INTELLIGENT_ROUTING": "true",
            
            # Caching configuration (environment-aware)
            "EMBEDDING_CACHE_SIZE": str(cache_size),
            "CACHE_TTL_HOURS": "48" if environment == "prod" else "24",
            "BATCH_SIZE_S": "32" if environment == "prod" else "16",
            "BATCH_SIZE_A": "64" if environment == "prod" else "32",
            "BATCH_SIZE_B": "256" if environment == "prod" else "128",
            
            # Gateway integration from ESC
            "PORTKEY_API_KEY": pulumi.Config().get_secret("PORTKEY_API_KEY"),
            "PORTKEY_BASE_URL": pulumi.Config().get("PORTKEY_BASE_URL") or "https://api.portkey.ai/v1",
            "PORTKEY_TOGETHER_VK": pulumi.Config().get_secret("PORTKEY_TOGETHER_VK"),
            
            # Performance tuning (environment-aware)
            "MAX_CONCURRENT_REQUESTS": str(vector_instances * 25),
            "REQUEST_TIMEOUT_SECONDS": "180" if environment == "prod" else "120",
            "WORKER_PROCESSES": str(vector_cpu_cores),
            
            # Model provider API keys from ESC
            "ANTHROPIC_API_KEY": pulumi.Config().get_secret("ANTHROPIC_API_KEY"),
            "OPENAI_API_KEY": pulumi.Config().get_secret("OPENAI_API_KEY"),
            "GROQ_API_KEY": pulumi.Config().get_secret("GROQ_API_KEY"),
            "TOGETHER_API_KEY": pulumi.Config().get_secret("TOGETHER_API_KEY"),
            "HUGGINGFACE_API_TOKEN": pulumi.Config().get_secret("HUGGINGFACE_API_TOKEN"),
            
            # Cost controls from ESC
            "DAILY_BUDGET_USD": pulumi.Config().get("DAILY_BUDGET_USD") or "100",
            "MAX_TOKENS_PER_REQUEST": pulumi.Config().get("MAX_TOKENS_PER_REQUEST") or "4096"
        }
    )
    
    # Deploy Vector Store Service
    vector_store_service = FlyApp("vector-store-service", vector_service_config)
    
    # Export outputs for other stacks (ESC-enhanced)
    pulumi.export("vector_store_url", vector_store_service.public_url)
    pulumi.export("vector_store_internal_url", vector_store_service.internal_url)
    pulumi.export("weaviate_url", weaviate_db.weaviate_url)
    pulumi.export("weaviate_collections", weaviate_db.collections)
    pulumi.export("weaviate_version", weaviate_db.version)
    
    # Export environment-specific configuration
    # Export ESC integration status
    pulumi.export("configuration_management", {
        "system": "pulumi_esc",
        "environment": environment,
        "adr_compliance": "ADR-006",
        "hierarchical_config": True,
        "secret_encryption": True,
        "intelligent_scaling": True
    })
    
    # Export enhanced embedding configuration
    pulumi.export("embedding_enhanced_config", {
        "three_tier_routing": {
            "tier_s": {
                "model": pulumi.Config().get("EMBED_MODEL_TIER_S") or "voyage-3-large",
                "dimension": 1024,
                "max_tokens": 8192 if environment == "prod" else 4096,
                "use_cases": ["production", "critical", "security", "financial"],
                "cost_tier": "premium"
            },
            "tier_a": {
                "model": pulumi.Config().get("EMBED_MODEL_TIER_A") or "cohere/embed-multilingual-v3.0",
                "dimension": 768,
                "max_tokens": 2048,
                "use_cases": ["standard", "multilingual", "semantic_search"],
                "cost_tier": "balanced"
            },
            "tier_b": {
                "model": pulumi.Config().get("EMBED_MODEL_TIER_B") or "BAAI/bge-base-en-v1.5",
                "dimension": 768,
                "max_tokens": 512,
                "use_cases": ["fast", "bulk_processing", "development"],
                "cost_tier": "economy"
            }
        },
        "environment_optimizations": {
            "cache_size": cache_size,
            "instances": vector_instances,
            "memory_per_instance": f"{vector_memory_mb}MB",
            "cpu_per_instance": vector_cpu_cores,
            "intelligent_routing_enabled": True,
            "quantization_enabled": True,
            "batch_processing_optimized": True
        }
    })
    pulumi.export("esc_environment", environment)
    pulumi.export("vector_instances", vector_instances)
    pulumi.export("cache_size", cache_size)
    
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