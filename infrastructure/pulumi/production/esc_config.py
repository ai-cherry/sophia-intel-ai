#!/usr/bin/env python3
"""
🔐 Pulumi ESC Configuration - Cloud Services Integration

This module configures Pulumi ESC (Environments, Secrets, and Configuration)
for the Sophia AI platform, providing centralized secret management and
configuration distribution across all cloud services.

Architecture:
GitHub Organization Secrets → Pulumi ESC → Application Runtime

Services Configured:
- Lambda Labs (GPU compute)
- Neon PostgreSQL (database)
- Qdrant (vector database)
- Redis (caching)
- OpenAI/OpenRouter/Portkey (AI services)
- LangChain/LangSmith (AI tooling)
- N8n/Estuary Flow (automation)
- Monitoring & Analytics services
"""

import json
from typing import Any, Dict, List

import pulumi
import pulumi_esc as esc

class SophiaAIESCConfig:
    """
    Sophia AI Pulumi ESC Configuration Manager

    Manages centralized configuration and secrets for all cloud services
    through Pulumi ESC integration with GitHub Organization Secrets.
    """

    def __init__(self, organization: str = "sophia-ai", project: str = "sophia-ai"):
        self.organization = organization
        self.project = project
        self.environment_name = "sophia-prod-on-lambda"

    def create_production_environment(self) -> esc.Environment:
        """Create production environment with all service configurations"""

        # Environment configuration
        environment_config = {
            "imports": [
                f"{self.organization}/github-secrets",
                f"{self.organization}/lambda-labs-config",
            ],
            "values": {
                # Core application configuration
                "app": {
                    "name": "sophia-ai",
                    "version": "1.0.0",
                    "environment": "production",
                    "host": "${BIND_IP}",
                    "port": 8000,
                },
                # AI Service Configuration
                "ai_services": {
                    "openai": {
                        "api_key": "${github-secrets.OPENAI_API_KEY}",
                        "api_base": "https://api.openai.com/v1",
                        "model_default": "gpt-4o-mini",
                        "max_tokens": 4096,
                    },
                    "openrouter": {
                        "api_key": "${github-secrets.OPENROUTER_API_KEY}",
                        "base_url": "https://openrouter.ai/api/v1",
                        "models": {
                            "primary": "anthropic/claude-3-5-sonnet-20241022",
                            "coding": "qwen/qwen-2.5-coder-32b-instruct",
                            "reasoning": "deepseek/deepseek-r1-distill-qwen-32b",
                        },
                    },
                    "portkey": {
                        "api_key": "${github-secrets.PORTKEY_API_KEY}",
                        "config": "${github-secrets.PORTKEY_CONFIG}",
                        "base_url": "https://api.portkey.ai/v1",
                    },
                    "langchain": {
                        "api_key": "${github-secrets.LANGCHAIN_API_KEY}",
                        "tracing": True,
                        "project": "sophia-ai-production",
                    },
                    "langsmith": {
                        "api_key": "${github-secrets.LANGSMITH_API_KEY}",
                        "endpoint": "https://api.smith.langchain.com",
                    },
                },
                # Database Configuration
                "databases": {
                    "neon": {
                        "database_url": "${github-secrets.NEON_DATABASE_URL}",
                        "api_key": "${github-secrets.NEON_API_KEY}",
                        "pool_size": 20,
                        "max_overflow": 30,
                        "pool_timeout": 30,
                    },
                    "qdrant": {
                        "url": "${github-secrets.QDRANT_URL}",
                        "api_key": "${github-secrets.QDRANT_API_KEY}",
                        "timeout": 30,
                        "prefer_grpc": True,
                        "collections": {
                            "documents": {"size": 1536, "distance": "cosine"},
                            "code": {"size": 768, "distance": "cosine"},
                        },
                    },
                    "redis": {
                        "url": "${github-secrets.REDIS_URL}",
                        "password": "${github-secrets.REDIS_PASSWORD}",
                        "max_connections": 100,
                        "retry_on_timeout": True,
                        "health_check_interval": 30,
                    },
                },
                # Infrastructure Configuration
                "infrastructure": {
                    "lambda_labs": {
                        "api_key": "${github-secrets.LAMBDA_LABS_API_KEY}",
                        "region": "us-west-2",
                        "instance_types": {
                            "development": "gpu_1x_a10",
                            "production": "gpu_1x_h100",
                        },
                        "ssh_key": "${github-secrets.LAMBDA_LABS_SSH_KEY}",
                    },
                    "pulumi": {
                        "access_token": "${github-secrets.PULUMI_ACCESS_TOKEN}",
                        "stack": f"{self.organization}/sophia-prod-on-lambda",
                        "backend_url": "https://api.pulumi.com",
                    },
                },
                # Automation Services
                "automation": {
                    "n8n": {
                        "api_key": "${github-secrets.N8N_API_KEY}",
                        "webhook_url": "${github-secrets.N8N_WEBHOOK_URL}",
                        "base_url": "${github-secrets.N8N_BASE_URL}",
                    },
                    "estuary_flow": {
                        "api_token": "${github-secrets.ESTUARY_API_TOKEN}",
                        "endpoint": "https://api.estuary.dev",
                        "collections": {
                            "sophia_logs": "sophia/logs",
                            "sophia_metrics": "sophia/metrics",
                            "sophia_events": "sophia/events",
                        },
                    },
                    "estuary": {
                        "client_id": "${github-secrets.ESTUARY_CLIENT_ID}",
                        "client_secret": "${github-secrets.ESTUARY_CLIENT_SECRET}",
                        "base_url": "https://api.estuary.dev/v1",
                    },
                },
                # Monitoring & Analytics
                "monitoring": {
                    "arize": {
                        "space_id": "${github-secrets.ARIZE_SPACE_ID}",
                        "api_key": "${github-secrets.ARIZE_API_KEY}",
                        "model_id": "sophia-ai-v1",
                        "model_version": "1.0.0",
                    },
                    "prometheus": {
                        "port": 9090,
                        "scrape_interval": "15s",
                        "retention": "30d",
                    },
                    "grafana": {
                        "port": 3000,
                        "admin_password": "${github-secrets.GRAFANA_ADMIN_PASSWORD}",
                    },
                },
                # Security Configuration
                "security": {
                    "jwt": {
                        "secret_key": "${github-secrets.JWT_SECRET_KEY}",
                        "algorithm": "HS256",
                        "expiration_hours": 24,
                    },
                    "encryption": {
                        "key": "${github-secrets.ENCRYPTION_KEY}",
                        "fernet_key": "${github-secrets.FERNET_KEY}",
                    },
                    "cors": {
                        "allowed_origins": [
                            "https://sophia-ai.vercel.app",
                            "https://sophia-ai.github.io",
                            "${SOPHIA_FRONTEND_ENDPOINT}",
                        ],
                        "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                        "allowed_headers": ["*"],
                    },
                },
                # Feature Flags
                "features": {
                    "enable_monitoring": True,
                    "enable_caching": True,
                    "enable_tracing": True,
                    "enable_auto_optimization": True,
                    "enable_ml_optimization": True,
                    "enable_distributed_tracing": True,
                },
                # Performance Configuration
                "performance": {
                    "max_concurrent_requests": 1000,
                    "request_timeout": 30,
                    "cache_ttl": 3600,
                    "worker_processes": 4,
                    "worker_threads": 8,
                    "memory_limit": "4GB",
                },
                # Development Tools
                "development": {
                    "github": {
                        "token": "${github-secrets.GITHUB_TOKEN}",
                        "organization": self.organization,
                        "repository": "sophia-main",
                    },
                    "docker": {
                        "username": "${github-secrets.DOCKER_USER_NAME}",
                        "token": "${github-secrets.DOCKER_PERSONAL_ACCESS_TOKEN}",
                    },
                    "huggingface": {"token": "${github-secrets.HUGGINGFACE_API_TOKEN}"},
                },
                # Additional Services
                "additional_services": {
                    "together_ai": {"api_key": "${github-secrets.TOGETHER_AI_API_KEY}"},
                    "tavily": {"api_key": "${github-secrets.TAVILY_API_KEY}"},
                    "twingly": {"api_key": "${github-secrets.TWINGLY_API_KEY}"},
                    "zenrows": {"api_key": "${github-secrets.ZENROWS_API_KEY}"},
                    "phantombuster": {
                        "api_key": "${github-secrets.PHANTOM_BUSTER_API_KEY}"
                    },
                    "apify": {"token": "${github-secrets.APIFY_API_TOKEN}"},
                },
            },
        }

        # Create the environment
        return esc.Environment(
            f"{self.environment_name}",
            name=self.environment_name,
            organization=self.organization,
            yaml=pulumi.Output.from_input(environment_config).apply(
                lambda config: json.dumps(config, indent=2)
            ),
        )

    def create_development_environment(self) -> esc.Environment:
        """Create development environment with relaxed security"""

        development_config = {
            "imports": [f"{self.organization}/github-secrets"],
            "values": {
                "app": {
                    "name": "sophia-ai-dev",
                    "version": "dev",
                    "environment": "development",
                    "debug": True,
                    "log_level": "DEBUG",
                },
                # Inherit most config from production but with development overrides
                "ai_services": {
                    "openai": {
                        "api_key": "${github-secrets.OPENAI_API_KEY}",
                        "model_default": "gpt-4o-mini",  # Use cheaper model for dev
                        "max_tokens": 2048,
                    }
                },
                "features": {
                    "enable_monitoring": False,  # Disable heavy monitoring in dev
                    "enable_caching": False,
                    "enable_tracing": True,
                    "enable_auto_optimization": False,
                },
                "performance": {"max_concurrent_requests": 10, "worker_processes": 1},
            },
        }

        return esc.Environment(
            f"{self.environment_name}-dev",
            name=f"{self.environment_name}-dev",
            organization=self.organization,
            yaml=pulumi.Output.from_input(development_config).apply(
                lambda config: json.dumps(config, indent=2)
            ),
        )

    def create_github_secrets_environment(self) -> esc.Environment:
        """Create GitHub secrets integration environment"""

        github_secrets_config = {
            "imports": [],
            "values": {
                # GitHub Organization Secrets integration
                "github-secrets": {
                    "provider": "github",
                    "organization": self.organization,
                    "secrets": {
                        # AI Services
                        "OPENAI_API_KEY": {"from_secret": "OPENAI_API_KEY"},
                        "OPENROUTER_API_KEY": {"from_secret": "OPENROUTER_API_KEY"},
                        "PORTKEY_API_KEY": {"from_secret": "PORTKEY_API_KEY"},
                        "PORTKEY_CONFIG": {"from_secret": "PORTKEY_CONFIG"},
                        "LANGCHAIN_API_KEY": {"from_secret": "LANGCHAIN_API_KEY"},
                        "LANGSMITH_API_KEY": {"from_secret": "LANGSMITH_API_KEY"},
                        # Databases
                        "NEON_DATABASE_URL": {"from_secret": "NEON_DATABASE_URL"},
                        "NEON_API_KEY": {"from_secret": "NEON_API_KEY"},
                        "QDRANT_URL": {"from_secret": "QDRANT_URL"},
                        "QDRANT_API_KEY": {"from_secret": "QDRANT_API_KEY"},
                        "REDIS_URL": {"from_secret": "REDIS_URL"},
                        "REDIS_PASSWORD": {"from_secret": "REDIS_PASSWORD"},
                        # Infrastructure
                        "LAMBDA_LABS_API_KEY": {"from_secret": "LAMBDA_LABS_API_KEY"},
                        "LAMBDA_LABS_SSH_KEY": {"from_secret": "LAMBDA_LABS_SSH_KEY"},
                        "PULUMI_ACCESS_TOKEN": {"from_secret": "PULUMI_ACCESS_TOKEN"},
                        # Automation
                        "N8N_API_KEY": {"from_secret": "N8N_API_KEY"},
                        "N8N_WEBHOOK_URL": {"from_secret": "N8N_WEBHOOK_URL"},
                        "N8N_BASE_URL": {"from_secret": "N8N_BASE_URL"},
                        "ESTUARY_API_TOKEN": {"from_secret": "ESTUARY_API_TOKEN"},
                        "ESTUARY_CLIENT_SECRET": {
                            "from_secret": "ESTUARY_CLIENT_SECRET"
                        },
                        # Monitoring
                        "ARIZE_SPACE_ID": {"from_secret": "ARIZE_SPACE_ID"},
                        "ARIZE_API_KEY": {"from_secret": "ARIZE_API_KEY"},
                        "GRAFANA_ADMIN_PASSWORD": {
                            "from_secret": "GRAFANA_ADMIN_PASSWORD"
                        },
                        # Security
                        "JWT_SECRET_KEY": {"from_secret": "JWT_SECRET_KEY"},
                        "ENCRYPTION_KEY": {"from_secret": "ENCRYPTION_KEY"},
                        "FERNET_KEY": {"from_secret": "FERNET_KEY"},
                        # Development
                        "GITHUB_TOKEN": {"from_secret": "GITHUB_TOKEN"},
                        "DOCKER_USER_NAME": {"from_secret": "DOCKER_USER_NAME"},
                        "DOCKER_PERSONAL_ACCESS_TOKEN": {
                            "from_secret": "DOCKER_PERSONAL_ACCESS_TOKEN"
                        },
                        "HUGGINGFACE_API_TOKEN": {
                            "from_secret": "HUGGINGFACE_API_TOKEN"
                        },
                        # Additional Services
                        "TOGETHER_AI_API_KEY": {"from_secret": "TOGETHER_AI_API_KEY"},
                        "TAVILY_API_KEY": {"from_secret": "TAVILY_API_KEY"},
                        "TWINGLY_API_KEY": {"from_secret": "TWINGLY_API_KEY"},
                        "ZENROWS_API_KEY": {"from_secret": "ZENROWS_API_KEY"},
                        "PHANTOM_BUSTER_API_KEY": {
                            "from_secret": "PHANTOM_BUSTER_API_KEY"
                        },
                        "APIFY_API_TOKEN": {"from_secret": "APIFY_API_TOKEN"},
                    },
                }
            },
        }

        return esc.Environment(
            "github-secrets",
            name="github-secrets",
            organization=self.organization,
            yaml=pulumi.Output.from_input(github_secrets_config).apply(
                lambda config: json.dumps(config, indent=2)
            ),
        )

def main():
    """Main function to create all ESC environments"""

    # Initialize ESC configuration
    esc_config = SophiaAIESCConfig()

    # Create GitHub secrets environment
    github_secrets_env = esc_config.create_github_secrets_environment()

    # Create production environment
    production_env = esc_config.create_production_environment()

    # Create development environment
    development_env = esc_config.create_development_environment()

    # Export environment names for reference
    pulumi.export("github_secrets_environment", github_secrets_env.name)
    pulumi.export("production_environment", production_env.name)
    pulumi.export("development_environment", development_env.name)

    # Export configuration summary
    pulumi.export(
        "configuration_summary",
        {
            "organization": esc_config.organization,
            "project": esc_config.project,
            "environments_created": 3,
            "services_configured": 15,
            "secrets_managed": 30,
        },
    )

if __name__ == "__main__":
    main()
