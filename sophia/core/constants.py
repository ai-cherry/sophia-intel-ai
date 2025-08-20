"""
SOPHIA AI Orchestrator - Constants
Centralized constants for all components to avoid duplication.
"""

# Environment Variables
ENV_VARS = {
    # AI Model Providers
    "OPENAI_API_KEY": "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY": "ANTHROPIC_API_KEY", 
    "GEMINI_API_KEY": "GEMINI_API_KEY",
    "DEEPSEEK_API_KEY": "DEEPSEEK_API_KEY",
    "QWEN_API_KEY": "QWEN_API_KEY",
    "MOONSHOT_API_KEY": "MOONSHOT_API_KEY",
    "MISTRAL_API_KEY": "MISTRAL_API_KEY",
    "ZHIPU_API_KEY": "ZHIPU_API_KEY",
    
    # Business Services
    "GONG_BASE_URL": "GONG_BASE_URL",
    "GONG_ACCESS_TOKEN": "GONG_ACCESS_TOKEN",
    "GONG_API_KEY": "GONG_API_KEY",
    "SLACK_BOT_TOKEN": "SLACK_BOT_TOKEN",
    "HUBSPOT_API_KEY": "HUBSPOT_API_KEY",
    "SALESFORCE_CLIENT_ID": "SALESFORCE_CLIENT_ID",
    "SALESFORCE_CLIENT_SECRET": "SALESFORCE_CLIENT_SECRET",
    "NOTION_API_KEY": "NOTION_API_KEY",
    
    # Research Services
    "SERPER_API_KEY": "SERPER_API_KEY",
    "TAVILY_API_KEY": "TAVILY_API_KEY",
    "ZENROWS_API_KEY": "ZENROWS_API_KEY",
    "APIFY_API_KEY": "APIFY_API_KEY",
    "BRIGHT_DATA_API_KEY": "BRIGHT_DATA_API_KEY",
    
    # Infrastructure
    "GITHUB_TOKEN": "GITHUB_TOKEN",
    "FLY_API_TOKEN": "FLY_API_TOKEN",
    "LAMBDA_API_KEY": "LAMBDA_API_KEY",
    
    # Databases
    "NEON_DATABASE_URL": "NEON_DATABASE_URL",
    "REDIS_URL": "REDIS_URL",
    "QDRANT_URL": "QDRANT_URL",
    "QDRANT_API_KEY": "QDRANT_API_KEY",
    "WEAVIATE_URL": "WEAVIATE_URL",
    "WEAVIATE_API_KEY": "WEAVIATE_API_KEY",
    "MEM0_API_KEY": "MEM0_API_KEY",
}

# Approved AI Models (20 Best Models Only)
APPROVED_MODELS = [
    "gpt-5",
    "claude-sonnet-4", 
    "gemini-2.5-flash",
    "deepseek-v3-0324",
    "gemini-2.5-pro",
    "qwen3-coder",
    "claude-3.7-sonnet",
    "deepseek-v3-0324-free",
    "r1-0528-free",
    "kimi-k2",
    "gpt-oss-120b",
    "qwen3-coder-free",
    "gemini-2.5-flash-lite",
    "glm-4.5",
    "mistral-nemo",
    "gpt-4o-mini",
    "claude-3.5-haiku",
    "llama-3.3-70b-instruct",
    "qwen-2.5-coder-32b-instruct",
    "gemini-1.5-flash",
]

# Model Quality Rankings (1 = highest quality)
MODEL_QUALITY = {
    "gpt-5": 1,
    "claude-sonnet-4": 1,
    "gemini-2.5-flash": 2,
    "deepseek-v3-0324": 2,
    "gemini-2.5-pro": 2,
    "qwen3-coder": 3,
    "claude-3.7-sonnet": 3,
    "deepseek-v3-0324-free": 4,
    "r1-0528-free": 4,
    "kimi-k2": 4,
    "gpt-oss-120b": 5,
    "qwen3-coder-free": 5,
    "gemini-2.5-flash-lite": 5,
    "glm-4.5": 6,
    "mistral-nemo": 6,
    "gpt-4o-mini": 7,
    "claude-3.5-haiku": 7,
    "llama-3.3-70b-instruct": 8,
    "qwen-2.5-coder-32b-instruct": 8,
    "gemini-1.5-flash": 9,
}

# Task Types
TASK_TYPES = [
    "code_generation",
    "research", 
    "deployment",
    "creative",
    "reasoning",
    "analysis",
    "translation",
    "summarization",
]

# Provider Names
PROVIDERS = {
    "OPENAI": "openai",
    "ANTHROPIC": "anthropic", 
    "GOOGLE": "google",
    "DEEPSEEK": "deepseek",
    "QWEN": "qwen",
    "MOONSHOT": "moonshot",
    "MISTRAL": "mistral",
    "ZHIPU": "zhipu",
}

# Service Endpoints
SERVICE_ENDPOINTS = {
    "GONG_DEFAULT_BASE_URL": "https://api.gong.io",
    "SLACK_API_BASE_URL": "https://slack.com/api",
    "HUBSPOT_API_BASE_URL": "https://api.hubapi.com",
    "SALESFORCE_API_BASE_URL": "https://login.salesforce.com",
    "NOTION_API_BASE_URL": "https://api.notion.com/v1",
    "GITHUB_API_BASE_URL": "https://api.github.com",
    "FLY_API_BASE_URL": "https://api.machines.dev/v1",
    "LAMBDA_API_BASE_URL": "https://cloud.lambdalabs.com/api/v1",
}

# Health Check Endpoints
HEALTH_ENDPOINTS = {
    "HEALTHZ": "/healthz",
    "METRICS": "/metrics", 
    "STATUS": "/status",
    "READY": "/ready",
}

# Default Timeouts (seconds)
TIMEOUTS = {
    "DEFAULT": 30,
    "LONG_RUNNING": 300,
    "QUICK": 10,
    "RESEARCH": 60,
    "DEPLOYMENT": 600,
}

# Rate Limits
RATE_LIMITS = {
    "GONG_REQUESTS_PER_MINUTE": 100,
    "SLACK_REQUESTS_PER_MINUTE": 50,
    "HUBSPOT_REQUESTS_PER_MINUTE": 100,
    "RESEARCH_REQUESTS_PER_MINUTE": 60,
}

# Memory Configuration
MEMORY_CONFIG = {
    "EMBEDDING_DIMENSION": 1536,
    "MAX_CONTEXT_LENGTH": 8192,
    "BATCH_SIZE": 100,
    "SIMILARITY_THRESHOLD": 0.8,
}

# Deployment Configuration
DEPLOYMENT_CONFIG = {
    "FLY_REGIONS": ["ord", "sjc", "iad"],
    "DEFAULT_INSTANCE_SIZE": "shared-cpu-1x",
    "MIN_INSTANCES": 1,
    "MAX_INSTANCES": 10,
}

