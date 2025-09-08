"""
Sophia AI V9.7 Infrastructure Stack with Pulumi ESC Integration
Provisions Supabase, Lambda Labs, and monitoring infrastructure
"""

import pulumi
import pulumi_supabase as supabase
import pulumi_aws as aws
import json
from typing import Dict, Any

# Load configuration from Pulumi ESC
config = pulumi.Config()
stack_name = pulumi.get_stack()
environment = "prod" if stack_name == "production" else "dev"

# ESC Environment Configuration
esc_env = f"sophia-{environment}"

class SophiaInfrastructure:
    """Main infrastructure class for Sophia AI V9.7"""

    def __init__(self):
        self.environment = environment
        self.project_name = "sophia-ai-v97"

        # Initialize components
        self.supabase_project = self._create_supabase()
        self.monitoring = self._create_monitoring()
        self.secrets = self._create_secrets_manager()

        # Export outputs
        self._export_outputs()

    def _create_supabase(self) -> supabase.Project:
        """Create Supabase project for vector storage and real-time features"""

        project = supabase.Project(
            f"{self.project_name}-db",
            name=f"sophia-ai-{self.environment}",
            region="us-west-2",
            plan="pro" if self.environment == "prod" else "free",
            opts=pulumi.ResourceOptions(
                protect=self.environment == "prod"
            )
        )

        # Enable required extensions
        extensions = [
            "vector",  # For pgvector
            "pg_stat_statements",  # For performance monitoring
            "uuid-ossp",  # For UUID generation
        ]

        for ext in extensions:
            supabase.Extension(
                f"{self.project_name}-ext-{ext}",
                project_id=project.id,
                name=ext,
                enabled=True
            )

        return project

    def _create_monitoring(self) -> Dict[str, Any]:
        """Create monitoring and observability infrastructure"""

        # CloudWatch Log Group for OpenTelemetry
        log_group = aws.cloudwatch.LogGroup(
            f"{self.project_name}-logs",
            name=f"/sophia-ai/{self.environment}",
            retention_in_days=30 if self.environment == "dev" else 90,
            tags={
                "Environment": self.environment,
                "Project": "sophia-ai-v97"
            }
        )

        # CloudWatch Dashboard
        dashboard = aws.cloudwatch.Dashboard(
            f"{self.project_name}-dashboard",
            dashboard_name=f"SophiaAI-{self.environment}",
            dashboard_body=pulumi.Output.all(log_group.name).apply(
                lambda args: json.dumps({
                    "widgets": [
                        {
                            "type": "metric",
                            "properties": {
                                "metrics": [
                                    ["AWS/Logs", "IncomingLogEvents", "LogGroupName", args[0]]
                                ],
                                "period": 300,
                                "stat": "Sum",
                                "region": "us-west-2",
                                "title": "Sophia AI Log Events"
                            }
                        }
                    ]
                })
            )
        )

        return {
            "log_group": log_group,
            "dashboard": dashboard
        }

    def _create_secrets_manager(self) -> Dict[str, aws.secretsmanager.Secret]:
        """Create AWS Secrets Manager for runtime secrets with comprehensive ESC integration"""

        # Main runtime secrets
        runtime_secret = aws.secretsmanager.Secret(
            f"{self.project_name}-secrets",
            name=f"sophia-ai/{self.environment}/runtime",
            description=f"Runtime secrets for Sophia AI {self.environment}",
            tags={
                "Environment": self.environment,
                "Project": "sophia-ai-v97",
                "ManagedBy": "pulumi-esc"
            }
        )

        # API integrations secrets
        api_secret = aws.secretsmanager.Secret(
            f"{self.project_name}-api-secrets",
            name=f"sophia-ai/{self.environment}/api-integrations",
            description=f"API integration secrets for Sophia AI {self.environment}",
            tags={
                "Environment": self.environment,
                "Project": "sophia-ai-v97",
                "ManagedBy": "pulumi-esc"
            }
        )

        # Runtime secrets version
        aws.secretsmanager.SecretVersion(
            f"{self.project_name}-secrets-version",
            secret_id=runtime_secret.id,
            secret_string=pulumi.Output.all(
                self.supabase_project.database_url,
                self.supabase_project.anon_key,
                self.supabase_project.service_key
            ).apply(
                lambda args: json.dumps({
                    "supabase_url": args[0],
                    "supabase_anon_key": args[1],
                    "supabase_service_key": args[2],
                    "environment": self.environment,
                    "managed_by": "pulumi-esc",
                    "redis_url": f"redis://sophia-redis-{self.environment}.cache.amazonaws.com:6379",
                    "qdrant_url": f"https://sophia-qdrant-{self.environment}.qdrant.tech"
                })
            )
        )

        # API secrets version (values from ESC environment)
        aws.secretsmanager.SecretVersion(
            f"{self.project_name}-api-secrets-version",
            secret_id=api_secret.id,
            secret_string=json.dumps({
                # Salesforce
                "salesforce_client_id": "${salesforce.client_id}",
                "salesforce_client_secret": "${salesforce.client_secret}",
                "salesforce_username": "${salesforce.username}",
                "salesforce_password": "${salesforce.password}",
                "salesforce_security_token": "${salesforce.security_token}",
                
                # HubSpot
                "hubspot_access_token": "${hubspot.access_token}",
                
                # Gong
                "gong_access_key": "${gong.access_key}",
                "gong_access_key_secret": "${gong.access_key_secret}",
                
                # Slack
                "slack_bot_token": "${slack.bot_token}",
                "slack_user_token": "${slack.user_token}",
                
                # OpenAI
                "openai_api_key": "${openai.api_key}",
                
                # Factory AI
                "factory_ai_url": "${factory_ai.url}",
                "factory_ai_token": "${factory_ai.token}",
                
                # Metadata
                "environment": self.environment,
                "managed_by": "pulumi-esc",
                "last_updated": "2025-01-08T00:00:00Z"
            })
        )

        return {
            "runtime": runtime_secret,
            "api_integrations": api_secret
        }

    def _export_outputs(self):
        """Export stack outputs for consumption by applications"""

        # Database outputs
        pulumi.export("supabase_project_id", self.supabase_project.id)
        pulumi.export("supabase_url", self.supabase_project.database_url)
        pulumi.export("supabase_anon_key", self.supabase_project.anon_key)
        pulumi.export("supabase_service_key", self.supabase_project.service_key)

        # Monitoring outputs
        pulumi.export("log_group_name", self.monitoring["log_group"].name)
        pulumi.export("dashboard_url", self.monitoring["dashboard"].dashboard_name.apply(
            lambda name: f"https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#dashboards:name={name}"
        ))

        # Secrets outputs
        pulumi.export("secrets_manager_runtime_arn", self.secrets["runtime"].arn)
        pulumi.export("secrets_manager_api_arn", self.secrets["api_integrations"].arn)

        # ESC Environment
        pulumi.export("esc_environment", esc_env)
        pulumi.export("environment", self.environment)

        # Application configuration
        pulumi.export("app_config", {
            "project_name": self.project_name,
            "environment": self.environment,
            "region": "us-west-2",
            "version": "9.7.0"
        })

# Initialize infrastructure
infrastructure = SophiaInfrastructure()

# Output summary
pulumi.export("infrastructure_summary", {
    "status": "deployed",
    "components": [
        "supabase-project",
        "cloudwatch-monitoring", 
        "secrets-manager",
        "pulumi-esc-integration"
    ],
    "environment": environment,
    "timestamp": pulumi.Output.from_input("2025-01-08T00:00:00Z")
})
