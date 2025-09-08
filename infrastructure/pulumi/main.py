"""
Pulumi Infrastructure as Code for Sophia Intel AI
Manages Redis Cloud, vector databases, and API key infrastructure with ESC integration.
"""

import json

# Import ESC components
import sys
from pathlib import Path
from typing import Any, Dict

import pulumi_aws as aws
import pulumi_random as random

import pulumi
from pulumi import Config, Output, export

sys.path.append(str(Path(__file__).parent.parent.parent))


class SophiaIntelAIInfrastructure:
    """Main infrastructure class for Sophia Intel AI"""

    def __init__(self):
        # Get Pulumi configuration
        self.config = Config()
        self.stack = pulumi.get_stack()
        self.project = pulumi.get_project()

        # Environment-specific settings
        self.environment = self.config.get("environment") or self.stack
        self.region = self.config.get("region") or "us-west-2"

        # Resource tags
        self.tags = {
            "Project": "sophia-intel-ai",
            "Environment": self.environment,
            "ManagedBy": "pulumi",
            "Stack": self.stack,
            "Owner": "sophia-intel",
        }

        # Infrastructure components
        self.redis_resources = {}
        self.vector_db_resources = {}
        self.monitoring_resources = {}
        self.security_resources = {}
        self.networking_resources = {}

    def deploy_infrastructure(self):
        """Deploy complete infrastructure stack"""

        # 1. Networking and security foundation
        self._create_networking()
        self._create_security_groups()

        # 2. Redis Cloud infrastructure
        self._create_redis_infrastructure()

        # 3. Vector database infrastructure
        self._create_vector_db_infrastructure()

        # 4. API key management and rotation
        self._create_api_key_infrastructure()

        # 5. Monitoring and observability
        self._create_monitoring_infrastructure()

        # 6. Export important outputs
        self._export_outputs()

        return {
            "redis": self.redis_resources,
            "vector_db": self.vector_db_resources,
            "monitoring": self.monitoring_resources,
            "security": self.security_resources,
            "networking": self.networking_resources,
        }

    def _create_networking(self):
        """Create networking infrastructure"""

        # VPC for isolated resources (if using AWS)
        if self.config.get_bool("create_vpc"):
            vpc = aws.ec2.Vpc(
                "sophia-vpc",
                cidr_block="10.0.0.0/16",
                enable_dns_hostnames=True,
                enable_dns_support=True,
                tags={**self.tags, "Name": f"sophia-vpc-{self.environment}"},
            )

            # Public subnets
            public_subnet_1 = aws.ec2.Subnet(
                "sophia-public-subnet-1",
                vpc_id=vpc.id,
                cidr_block="10.0.1.0/24",
                availability_zone=f"{self.region}a",
                map_public_ip_on_launch=True,
                tags={**self.tags, "Name": f"sophia-public-1-{self.environment}"},
            )

            public_subnet_2 = aws.ec2.Subnet(
                "sophia-public-subnet-2",
                vpc_id=vpc.id,
                cidr_block="10.0.2.0/24",
                availability_zone=f"{self.region}b",
                map_public_ip_on_launch=True,
                tags={**self.tags, "Name": f"sophia-public-2-{self.environment}"},
            )

            # Private subnets for databases
            private_subnet_1 = aws.ec2.Subnet(
                "sophia-private-subnet-1",
                vpc_id=vpc.id,
                cidr_block="10.0.10.0/24",
                availability_zone=f"{self.region}a",
                tags={**self.tags, "Name": f"sophia-private-1-{self.environment}"},
            )

            private_subnet_2 = aws.ec2.Subnet(
                "sophia-private-subnet-2",
                vpc_id=vpc.id,
                cidr_block="10.0.11.0/24",
                availability_zone=f"{self.region}b",
                tags={**self.tags, "Name": f"sophia-private-2-{self.environment}"},
            )

            # Internet Gateway
            igw = aws.ec2.InternetGateway(
                "sophia-igw",
                vpc_id=vpc.id,
                tags={**self.tags, "Name": f"sophia-igw-{self.environment}"},
            )

            # Route table for public subnets
            public_rt = aws.ec2.RouteTable(
                "sophia-public-rt",
                vpc_id=vpc.id,
                tags={**self.tags, "Name": f"sophia-public-rt-{self.environment}"},
            )

            aws.ec2.Route(
                "sophia-public-route",
                route_table_id=public_rt.id,
                destination_cidr_block="0.0.0.0/0",
                gateway_id=igw.id,
            )

            # Associate public subnets with route table
            aws.ec2.RouteTableAssociation(
                "sophia-public-rt-assoc-1",
                subnet_id=public_subnet_1.id,
                route_table_id=public_rt.id,
            )

            aws.ec2.RouteTableAssociation(
                "sophia-public-rt-assoc-2",
                subnet_id=public_subnet_2.id,
                route_table_id=public_rt.id,
            )

            self.networking_resources = {
                "vpc": vpc,
                "public_subnets": [public_subnet_1, public_subnet_2],
                "private_subnets": [private_subnet_1, private_subnet_2],
                "internet_gateway": igw,
                "public_route_table": public_rt,
            }

    def _create_security_groups(self):
        """Create security groups for various services"""

        if "vpc" in self.networking_resources:
            vpc_id = self.networking_resources["vpc"].id

            # Redis security group
            redis_sg = aws.ec2.SecurityGroup(
                "sophia-redis-sg",
                name=f"sophia-redis-{self.environment}",
                description="Security group for Redis instances",
                vpc_id=vpc_id,
                ingress=[
                    aws.ec2.SecurityGroupIngressArgs(
                        protocol="tcp",
                        from_port=6379,
                        to_port=6379,
                        cidr_blocks=["10.0.0.0/16"],  # Only from VPC
                        description="Redis port",
                    )
                ],
                egress=[
                    aws.ec2.SecurityGroupEgressArgs(
                        protocol="-1", from_port=0, to_port=0, cidr_blocks=["0.0.0.0/0"]
                    )
                ],
                tags={**self.tags, "Name": f"sophia-redis-sg-{self.environment}"},
            )

            # Application security group
            app_sg = aws.ec2.SecurityGroup(
                "sophia-app-sg",
                name=f"sophia-app-{self.environment}",
                description="Security group for application servers",
                vpc_id=vpc_id,
                ingress=[
                    aws.ec2.SecurityGroupIngressArgs(
                        protocol="tcp",
                        from_port=80,
                        to_port=80,
                        cidr_blocks=["0.0.0.0/0"],
                        description="HTTP",
                    ),
                    aws.ec2.SecurityGroupIngressArgs(
                        protocol="tcp",
                        from_port=443,
                        to_port=443,
                        cidr_blocks=["0.0.0.0/0"],
                        description="HTTPS",
                    ),
                    aws.ec2.SecurityGroupIngressArgs(
                        protocol="tcp",
                        from_port=8080,
                        to_port=8080,
                        cidr_blocks=["0.0.0.0/0"],
                        description="Application port",
                    ),
                ],
                egress=[
                    aws.ec2.SecurityGroupEgressArgs(
                        protocol="-1", from_port=0, to_port=0, cidr_blocks=["0.0.0.0/0"]
                    )
                ],
                tags={**self.tags, "Name": f"sophia-app-sg-{self.environment}"},
            )

            self.security_resources = {"redis_sg": redis_sg, "app_sg": app_sg}

    def _create_redis_infrastructure(self):
        """Create Redis Cloud infrastructure"""

        # Environment-specific Redis configurations
        redis_configs = {
            "dev": {
                "memory_size_gb": 1,
                "replica_count": 0,
                "modules": ["RedisJSON", "RediSearch"],
                "backup_enabled": False,
            },
            "staging": {
                "memory_size_gb": 2,
                "replica_count": 1,
                "modules": ["RedisJSON", "RediSearch", "RedisTimeSeries"],
                "backup_enabled": True,
            },
            "production": {
                "memory_size_gb": 4,
                "replica_count": 2,
                "modules": ["RedisJSON", "RediSearch", "RedisTimeSeries", "RedisBloom"],
                "backup_enabled": True,
            },
        }

        redis_config = redis_configs.get(self.environment, redis_configs["dev"])

        # Generate Redis password
        redis_password = random.RandomPassword(
            "redis-password",
            length=32,
            special=True,
            min_lower=4,
            min_upper=4,
            min_numeric=4,
            min_special=2,
        )

        # Redis Enterprise Cloud configuration would go here
        # For now, we'll create a placeholder configuration
        redis_instance = {
            "name": f"sophia-redis-{self.environment}",
            "memory_size_gb": redis_config["memory_size_gb"],
            "replica_count": redis_config["replica_count"],
            "modules": redis_config["modules"],
            "backup_enabled": redis_config["backup_enabled"],
            "password": redis_password.result,
            "ssl_enabled": True,
            "region": self.region,
        }

        # Store in ESC (would integrate with actual Redis Cloud API)
        redis_connection_string = Output.concat(
            "redis://:@redis-", pulumi.get_stack(), ".sophia-intel-ai.com:6379"
        )

        self.redis_resources = {
            "instance": redis_instance,
            "password": redis_password,
            "connection_string": redis_connection_string,
            "ssl_enabled": True,
            "modules": redis_config["modules"],
        }

    def _create_vector_db_infrastructure(self):
        """Create vector database infrastructure (Qdrant, Weaviate)"""

        # Qdrant configuration
        qdrant_config = {
            "dev": {"memory_gb": 2, "replicas": 1},
            "staging": {"memory_gb": 4, "replicas": 2},
            "production": {"memory_gb": 8, "replicas": 3},
        }

        # Weaviate configuration
        weaviate_config = {
            "dev": {"memory_gb": 2, "replicas": 1},
            "staging": {"memory_gb": 4, "replicas": 2},
            "production": {"memory_gb": 8, "replicas": 3},
        }

        env_config = qdrant_config.get(self.environment, qdrant_config["dev"])

        # Generate API keys for vector databases
        qdrant_api_key = random.RandomString(
            "qdrant-api-key", length=48, special=False, upper=True, lower=True, numeric=True
        )

        weaviate_api_key = random.RandomString(
            "weaviate-api-key", length=48, special=False, upper=True, lower=True, numeric=True
        )

        # Vector database instances (placeholder - would integrate with actual APIs)
        qdrant_instance = {
            "name": f"sophia-qdrant-{self.environment}",
            "memory_gb": env_config["memory_gb"],
            "replicas": env_config["replicas"],
            "api_key": qdrant_api_key.result,
            "region": self.region,
            "ssl_enabled": True,
            "backup_enabled": self.environment != "dev",
        }

        weaviate_instance = {
            "name": f"sophia-weaviate-{self.environment}",
            "memory_gb": env_config["memory_gb"],
            "replicas": env_config["replicas"],
            "api_key": weaviate_api_key.result,
            "region": self.region,
            "ssl_enabled": True,
            "backup_enabled": self.environment != "dev",
        }

        self.vector_db_resources = {
            "qdrant": {
                "instance": qdrant_instance,
                "api_key": qdrant_api_key,
                "url": Output.concat("https://", qdrant_instance["name"], ".qdrant.tech"),
            },
            "weaviate": {
                "instance": weaviate_instance,
                "api_key": weaviate_api_key,
                "url": Output.concat("https://", weaviate_instance["name"], ".weaviate.network"),
            },
        }

    def _create_api_key_infrastructure(self):
        """Create infrastructure for API key management and rotation"""

        # AWS Secrets Manager for sensitive keys (if using AWS)
        if self.config.get_bool("use_aws_secrets"):

            # Create secrets for various providers
            providers = [
                "openai",
                "anthropic",
                "deepseek",
                "groq",
                "mistral",
                "together",
                "cohere",
                "perplexity",
                "huggingface",
            ]

            secrets = {}

            for provider in providers:
                secret = aws.secretsmanager.Secret(
                    f"sophia-{provider}-secret",
                    name=f"sophia/{self.environment}/{provider}/api-key",
                    description=f"API key for {provider} in {self.environment}",
                    tags={**self.tags, "Provider": provider},
                )

                # Placeholder secret version (actual keys would be set separately)
                secret_version = aws.secretsmanager.SecretVersion(
                    f"sophia-{provider}-secret-version",
                    secret_id=secret.id,
                    secret_string=json.dumps(
                        {
                            "api_key": f"placeholder-{provider}-key-{self.environment}",
                            "provider": provider,
                            "environment": self.environment,
                            "created_date": "2024-01-01T00:00:00Z",
                        }
                    ),
                )

                secrets[provider] = {"secret": secret, "version": secret_version, "arn": secret.arn}

            # IAM role for API key access
            api_key_role = aws.iam.Role(
                "sophia-api-key-role",
                assume_role_policy=json.dumps(
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Action": "sts:AssumeRole",
                                "Effect": "Allow",
                                "Principal": {
                                    "Service": ["ec2.amazonaws.com", "lambda.amazonaws.com"]
                                },
                            }
                        ],
                    }
                ),
                tags=self.tags,
            )

            # Policy for accessing secrets
            api_key_policy = aws.iam.RolePolicy(
                "sophia-api-key-policy",
                role=api_key_role.id,
                policy=Output.json_dumps(
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": [
                                    "secretsmanager:GetSecretValue",
                                    "secretsmanager:DescribeSecret",
                                ],
                                "Resource": [
                                    secret_data["secret"].arn for secret_data in secrets.values()
                                ],
                            }
                        ],
                    }
                ),
            )

            self.security_resources.update(
                {
                    "api_key_secrets": secrets,
                    "api_key_role": api_key_role,
                    "api_key_policy": api_key_policy,
                }
            )

    def _create_monitoring_infrastructure(self):
        """Create monitoring and observability infrastructure"""

        # CloudWatch dashboard (if using AWS)
        if self.config.get_bool("create_monitoring"):

            dashboard_body = {
                "widgets": [
                    {
                        "type": "metric",
                        "properties": {
                            "metrics": [
                                ["AWS/ApplicationELB", "RequestCount"],
                                ["AWS/ApplicationELB", "TargetResponseTime"],
                            ],
                            "period": 300,
                            "stat": "Sum",
                            "region": self.region,
                            "title": "Application Load Balancer",
                        },
                    },
                    {
                        "type": "log",
                        "properties": {
                            "query": f"SOURCE '/aws/lambda/sophia-{self.environment}' | fields @timestamp, @message | sort @timestamp desc | limit 100",
                            "region": self.region,
                            "title": "Application Logs",
                        },
                    },
                ]
            }

            dashboard = aws.cloudwatch.Dashboard(
                "sophia-dashboard",
                dashboard_name=f"Sophia-Intel-AI-{self.environment}",
                dashboard_body=json.dumps(dashboard_body),
            )

            # CloudWatch alarms
            alarms = []

            # High error rate alarm
            error_alarm = aws.cloudwatch.MetricAlarm(
                "sophia-error-alarm",
                alarm_name=f"Sophia-High-Error-Rate-{self.environment}",
                comparison_operator="GreaterThanThreshold",
                evaluation_periods="2",
                metric_name="5XXError",
                namespace="AWS/ApplicationELB",
                period="300",
                statistic="Sum",
                threshold="10",
                alarm_description="High error rate detected",
                tags=self.tags,
            )
            alarms.append(error_alarm)

            # High response time alarm
            latency_alarm = aws.cloudwatch.MetricAlarm(
                "sophia-latency-alarm",
                alarm_name=f"Sophia-High-Latency-{self.environment}",
                comparison_operator="GreaterThanThreshold",
                evaluation_periods="3",
                metric_name="TargetResponseTime",
                namespace="AWS/ApplicationELB",
                period="300",
                statistic="Average",
                threshold="2",
                alarm_description="High response time detected",
                tags=self.tags,
            )
            alarms.append(latency_alarm)

            self.monitoring_resources = {"dashboard": dashboard, "alarms": alarms}

    def _export_outputs(self):
        """Export important infrastructure outputs"""

        # Redis outputs
        if self.redis_resources:
            export("redis_connection_string", self.redis_resources.get("connection_string"))
            export("redis_ssl_enabled", self.redis_resources.get("ssl_enabled"))
            export("redis_modules", self.redis_resources.get("modules"))

        # Vector DB outputs
        if self.vector_db_resources:
            export("qdrant_url", self.vector_db_resources["qdrant"]["url"])
            export("weaviate_url", self.vector_db_resources["weaviate"]["url"])

        # Networking outputs
        if self.networking_resources:
            if "vpc" in self.networking_resources:
                export("vpc_id", self.networking_resources["vpc"].id)
                export(
                    "public_subnet_ids",
                    [subnet.id for subnet in self.networking_resources["public_subnets"]],
                )
                export(
                    "private_subnet_ids",
                    [subnet.id for subnet in self.networking_resources["private_subnets"]],
                )

        # Security outputs
        if self.security_resources:
            if "api_key_role" in self.security_resources:
                export("api_key_role_arn", self.security_resources["api_key_role"].arn)

        # General outputs
        export("environment", self.environment)
        export("region", self.region)
        export("project", self.project)
        export("stack", self.stack)

        # Infrastructure summary
        export(
            "infrastructure_summary",
            {
                "redis_enabled": bool(self.redis_resources),
                "vector_db_enabled": bool(self.vector_db_resources),
                "monitoring_enabled": bool(self.monitoring_resources),
                "networking_enabled": bool(self.networking_resources),
                "security_enabled": bool(self.security_resources),
                "environment": self.environment,
                "region": self.region,
            },
        )


# Environment-specific configurations
def get_environment_config():
    """Get environment-specific configuration"""
    config = Config()
    environment = config.get("environment") or pulumi.get_stack()

    # Base configuration
    base_config = {
        "create_vpc": config.get_bool("create_vpc") or False,
        "create_monitoring": config.get_bool("create_monitoring") or True,
        "use_aws_secrets": config.get_bool("use_aws_secrets") or True,
        "enable_backup": True,
        "region": config.get("region") or "us-west-2",
    }

    # Environment-specific overrides
    env_configs = {
        "dev": {"create_vpc": False, "enable_backup": False, "monitoring_level": "basic"},
        "staging": {"create_vpc": True, "enable_backup": True, "monitoring_level": "standard"},
        "production": {
            "create_vpc": True,
            "enable_backup": True,
            "monitoring_level": "comprehensive",
            "high_availability": True,
        },
    }

    # Merge configurations
    if environment in env_configs:
        base_config.update(env_configs[environment])

    return base_config


# Integration with Pulumi ESC
class ESCIntegration:
    """Integration with Pulumi ESC for configuration management"""

    def __init__(self, environment: str):
        self.environment = environment
        self.config = Config()

    def get_esc_values(self) -> Dict[str, Any]:
        """Get values from Pulumi ESC"""
        try:
            # This would integrate with actual ESC API
            # For now, return placeholder values
            return {
                "redis": {
                    "url": self.config.get_secret("redis_url") or "redis://localhost:6379",
                    "password": self.config.get_secret("redis_password") or "",
                },
                "vector_db": {
                    "qdrant": {
                        "url": self.config.get_secret("qdrant_url") or "",
                        "api_key": self.config.get_secret("qdrant_api_key") or "",
                    },
                    "weaviate": {
                        "url": self.config.get_secret("weaviate_url") or "",
                        "api_key": self.config.get_secret("weaviate_api_key") or "",
                    },
                },
                "llm_providers": {
                    "openai": {"api_key": self.config.get_secret("openai_api_key") or ""},
                    "anthropic": {"api_key": self.config.get_secret("anthropic_api_key") or ""},
                },
            }
        except Exception as e:
            print(f"Warning: Could not load ESC values: {e}")
            return {}

    def store_outputs_in_esc(self, outputs: Dict[str, Any]):
        """Store infrastructure outputs in ESC"""
        try:
            # This would store outputs back to ESC
            # For now, just log what would be stored
            print(f"Would store outputs in ESC for environment: {self.environment}")
            for key, value in outputs.items():
                print(f"  {key}: {type(value)}")
        except Exception as e:
            print(f"Warning: Could not store outputs in ESC: {e}")


# Main infrastructure deployment
def main():
    """Main deployment function"""

    # Get environment configuration
    env_config = get_environment_config()
    environment = pulumi.get_stack()

    # Initialize ESC integration
    esc_integration = ESCIntegration(environment)
    esc_values = esc_integration.get_esc_values()

    # Create infrastructure
    infrastructure = SophiaIntelAIInfrastructure()
    resources = infrastructure.deploy_infrastructure()

    # Store outputs in ESC
    esc_integration.store_outputs_in_esc(resources)

    # Output deployment summary
    export(
        "deployment_summary",
        {
            "timestamp": pulumi.Output.secret(Output.from_input("2024-01-01T00:00:00Z")),
            "environment": environment,
            "config": env_config,
            "resources_created": {
                "redis": len(resources.get("redis", {})),
                "vector_db": len(resources.get("vector_db", {})),
                "monitoring": len(resources.get("monitoring", {})),
                "security": len(resources.get("security", {})),
                "networking": len(resources.get("networking", {})),
            },
            "esc_integration": True,
        },
    )


# Run main deployment
if __name__ == "__main__":
    main()
