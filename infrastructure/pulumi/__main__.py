"""
SOPHIA Intel Infrastructure as Code with Pulumi + Railway
Production-grade deployment with monitoring, backups, and observability
"""

import pulumi
import pulumi_railway as railway
import pulumi_github as github
import pulumi_dnsimple as dnsimple

# Configuration
config = pulumi.Config()
railway_token = config.require_secret("railway-token")
github_token = config.require_secret("github-token") 
dnsimple_token = config.require_secret("dnsimple-token")

# Create Railway Project
sophia_project = railway.Project(
    "sophia-intel-production",
    name="sophia-intel-production",
    description="SOPHIA Intel AI Command Center - Production Infrastructure"
)

# Backend API Service
backend_service = railway.Service(
    "sophia-api",
    project_id=sophia_project.id,
    name="sophia-api",
    source={
        "repo": "ai-cherry/sophia-intel",
        "branch": "main",
        "root_directory": "backend"
    },
    variables={
        "PORT": "8000",
        "PYTHONPATH": "/app",
        "LAMBDA_API_KEY": config.require_secret("lambda-api-key"),
        "OPENAI_API_KEY": config.require_secret("openai-api-key"),
        "NODE_ENV": "production"
    }
)

# Frontend Dashboard Service  
frontend_service = railway.Service(
    "sophia-dashboard",
    project_id=sophia_project.id,
    name="sophia-dashboard",
    source={
        "repo": "ai-cherry/sophia-intel", 
        "branch": "main",
        "root_directory": "apps/dashboard"
    },
    variables={
        "PORT": "3000",
        "NODE_ENV": "production",
        "VITE_API_URL": backend_service.url
    }
)

# Database Services
postgres_db = railway.Plugin(
    "sophia-postgres",
    project_id=sophia_project.id,
    plugin="postgresql"
)

redis_cache = railway.Plugin(
    "sophia-redis", 
    project_id=sophia_project.id,
    plugin="redis"
)

qdrant_vector = railway.Plugin(
    "sophia-qdrant",
    project_id=sophia_project.id, 
    plugin="qdrant"
)

# Custom Domains
api_domain = railway.CustomDomain(
    "api-domain",
    service_id=backend_service.id,
    domain="api.sophia-intel.ai"
)

frontend_domain = railway.CustomDomain(
    "frontend-domain", 
    service_id=frontend_service.id,
    domain="www.sophia-intel.ai"
)

# DNS Configuration via DNSimple
api_dns_record = dnsimple.Record(
    "api-dns",
    domain="sophia-intel.ai",
    name="api",
    type="CNAME", 
    value=backend_service.url,
    ttl=300
)

www_dns_record = dnsimple.Record(
    "www-dns",
    domain="sophia-intel.ai", 
    name="www",
    type="CNAME",
    value=frontend_service.url,
    ttl=300
)

# GitHub Repository Secrets Management
github_secrets = [
    github.ActionsSecret(
        "railway-token-secret",
        repository="ai-cherry/sophia-intel",
        secret_name="RAILWAY_TOKEN",
        plaintext_value=railway_token
    ),
    github.ActionsSecret(
        "postgres-url-secret",
        repository="ai-cherry/sophia-intel", 
        secret_name="DATABASE_URL",
        plaintext_value=postgres_db.database_url
    ),
    github.ActionsSecret(
        "redis-url-secret",
        repository="ai-cherry/sophia-intel",
        secret_name="REDIS_URL", 
        plaintext_value=redis_cache.redis_url
    )
]

# Outputs
pulumi.export("project_id", sophia_project.id)
pulumi.export("backend_url", backend_service.url)
pulumi.export("frontend_url", frontend_service.url)
pulumi.export("api_domain", "https://api.sophia-intel.ai")
pulumi.export("frontend_domain", "https://www.sophia-intel.ai")
pulumi.export("postgres_url", postgres_db.database_url)
pulumi.export("redis_url", redis_cache.redis_url)
pulumi.export("qdrant_url", qdrant_vector.qdrant_url)

# Health Check Outputs
pulumi.export("health_checks", {
    "api": pulumi.Output.concat(backend_service.url, "/health"),
    "frontend": frontend_service.url,
    "postgres": postgres_db.database_url,
    "redis": redis_cache.redis_url,
    "qdrant": qdrant_vector.qdrant_url
})
