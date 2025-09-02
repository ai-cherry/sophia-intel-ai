"""
API Gateway and Networking Infrastructure for Sophia Intel AI
Implements unified routing to microservices with rate limiting and load balancing.
"""

import os
import sys

import pulumi
from pulumi import StackReference

# Add shared components to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from shared import FlyApp, FlyAppConfig


def main():
    """Deploy API Gateway infrastructure."""

    config = pulumi.Config()
    environment = config.get("environment") or "dev"
    domain = config.get("domain") or "sophia-intel-ai.fly.dev"
    rate_limit = config.get_int("rate_limit") or 100

    # Reference shared components
    shared_stack = StackReference(f"shared-{environment}")

    # Gateway configuration
    gateway_config = FlyAppConfig(
        name=f"sophia-gateway-{environment}",
        image="ghcr.io/sophia-intel-ai/api-gateway:latest",
        port=8080,
        scale=2,  # Multiple instances for HA
        memory_mb=1024,  # More memory for routing
        cpu_cores=1.0,
        env_vars={
            "ENVIRONMENT": environment,
            "RATE_LIMIT_PER_MINUTE": str(rate_limit),
            "LOG_LEVEL": "INFO" if environment == "prod" else "DEBUG",

            # Service discovery - will be populated by StackReference
            "AGENT_ORCHESTRATOR_URL": "http://agent-orchestrator.internal:8080",
            "MCP_SERVER_URL": "http://mcp-server.internal:8080",
            "VECTOR_STORE_URL": "http://vector-store.internal:8080",
            "UI_SERVICE_URL": "http://ui-service.internal:3000",

            # External integrations
            "PORTKEY_API_KEY": pulumi.Config().require_secret("portkey_api_key"),
            "CORS_ORIGINS": f"https://{domain},https://localhost:3000"
        }
    )

    # Deploy API Gateway
    api_gateway = FlyApp("api-gateway", gateway_config)

    # Export networking outputs for other stacks
    pulumi.export("api_gateway_url", api_gateway.public_url)
    pulumi.export("api_gateway_internal_url", api_gateway.internal_url)
    pulumi.export("domain", domain)
    pulumi.export("environment", environment)

    # Load balancing configuration
    pulumi.export("load_balancer_config", {
        "health_check_path": "/healthz",
        "health_check_interval": "15s",
        "health_check_timeout": "10s",
        "rate_limit": rate_limit,
        "sticky_sessions": False,
        "auto_scaling": {
            "min_instances": 1,
            "max_instances": 10,
            "cpu_threshold": 70,
            "memory_threshold": 80
        }
    })

    # Service registry for microservice routing
    pulumi.export("service_routes", {
        "/api/swarms": "agent-orchestrator",
        "/api/teams": "agent-orchestrator",
        "/api/workflows": "agent-orchestrator",
        "/api/memory": "mcp-server",
        "/api/tools": "mcp-server",
        "/api/embeddings": "vector-store",
        "/api/search": "vector-store",
        "/api/health": "api-gateway",
        "/": "ui-service"
    })

if __name__ == "__main__":
    main()
