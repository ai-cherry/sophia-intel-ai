"""
SOPHIA Intel Infrastructure as Code
Proper Pulumi implementation using resource classes instead of direct API calls
"""

import pulumi
import pulumi_kubernetes as k8s
from pulumi import Config, Output
from typing import Dict, List, Optional
import os

# Load configuration
config = Config()
stack = pulumi.get_stack()

# Configuration values with defaults
DOMAIN = config.get("domain") or "sophia-intel.ai"
NAMESPACE = config.get("namespace") or "sophia-intel"
CLUSTER_NAME = config.get("cluster_name") or "sophia-k3s"
ENVIRONMENT = config.get("environment") or stack
NODE_IP = config.get("node_ip") or os.environ.get("KUBERNETES_NODE_IP", "127.0.0.1")

# Resource configuration
REPLICA_COUNT = config.get_int("replica_count") or 1
CPU_LIMIT = config.get("cpu_limit") or "500m"
MEMORY_LIMIT = config.get("memory_limit") or "512Mi"

class SophiaInfrastructure:
    """SOPHIA Intel Infrastructure Management"""
    
    def __init__(self):
        self.namespace = None
        self.secrets = None
        self.config_map = None
        self.deployments = {}
        self.services = {}
        self.ingress = None
        
    def create_namespace(self) -> k8s.core.v1.Namespace:
        """Create the SOPHIA namespace"""
        self.namespace = k8s.core.v1.Namespace(
            "sophia-namespace",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=NAMESPACE,
                labels={
                    "name": NAMESPACE,
                    "environment": ENVIRONMENT,
                    "managed-by": "pulumi"
                }
            )
        )
        return self.namespace
    
    def create_secrets(self) -> k8s.core.v1.Secret:
        """Create Kubernetes secrets from Pulumi configuration"""
        
        # Get secrets from Pulumi config (these should be set via Pulumi ESC)
        secret_data = {}
        
        # AI & LLM Services
        if config.get_secret("openrouter_api_key"):
            secret_data["openrouter-api-key"] = config.get_secret("openrouter_api_key")
        if config.get_secret("openai_api_key"):
            secret_data["openai-api-key"] = config.get_secret("openai_api_key")
        if config.get_secret("elevenlabs_api_key"):
            secret_data["elevenlabs-api-key"] = config.get_secret("elevenlabs_api_key")
            
        # Vector Databases
        if config.get_secret("qdrant_api_key"):
            secret_data["qdrant-api-key"] = config.get_secret("qdrant_api_key")
        if config.get_secret("qdrant_url"):
            secret_data["qdrant-url"] = config.get_secret("qdrant_url")
        if config.get_secret("weaviate_admin_api_key"):
            secret_data["weaviate-admin-api-key"] = config.get_secret("weaviate_admin_api_key")
            
        # Database Services
        if config.get_secret("neon_api_token"):
            secret_data["neon-api-key"] = config.get_secret("neon_api_token")
        if config.get_secret("neon_database_url"):
            secret_data["neon-database-url"] = config.get_secret("neon_database_url")
            
        # Integration Services
        if config.get_secret("github_pat"):
            secret_data["github-pat"] = config.get_secret("github_pat")
        if config.get_secret("notion_api_key"):
            secret_data["notion-api-key"] = config.get_secret("notion_api_key")
        if config.get_secret("brightdata_api_key"):
            secret_data["brightdata-api-key"] = config.get_secret("brightdata_api_key")
        if config.get_secret("slack_webhook_url"):
            secret_data["slack-webhook-url"] = config.get_secret("slack_webhook_url")
            
        # Infrastructure
        if config.get_secret("lambda_cloud_api_key"):
            secret_data["lambda-cloud-api-key"] = config.get_secret("lambda_cloud_api_key")
        if config.get_secret("dnsimple_api_key"):
            secret_data["dnsimple-api-key"] = config.get_secret("dnsimple_api_key")
            
        # Security
        if config.get_secret("flask_secret_key"):
            secret_data["flask-secret-key"] = config.get_secret("flask_secret_key")
        if config.get_secret("jwt_secret_key"):
            secret_data["jwt-secret-key"] = config.get_secret("jwt_secret_key")
        
        self.secrets = k8s.core.v1.Secret(
            "sophia-secrets",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="sophia-secrets-enhanced",
                namespace=self.namespace.metadata.name,
                labels={
                    "app": "sophia-intel",
                    "component": "secrets",
                    "managed-by": "pulumi"
                }
            ),
            string_data=secret_data,
            type="Opaque"
        )
        return self.secrets
    
    def create_config_map(self) -> k8s.core.v1.ConfigMap:
        """Create configuration map for non-sensitive settings"""
        
        config_data = {
            # Domain configuration
            "SOPHIA_DOMAIN": DOMAIN,
            "SOPHIA_API_URL": f"https://api.{DOMAIN}",
            "SOPHIA_DASHBOARD_URL": f"https://dashboard.{DOMAIN}",
            "SOPHIA_WEB_URL": f"https://www.{DOMAIN}",
            
            # Environment settings
            "ENVIRONMENT": ENVIRONMENT,
            "LOG_LEVEL": config.get("log_level") or "INFO",
            "DEBUG": "false",
            
            # MCP Services configuration
            "SOPHIA_MCP_HOST": "0.0.0.0",
            "SOPHIA_MCP_PORT": "5000",
            "SOPHIA_TELEMETRY_PORT": "5001",
            "SOPHIA_EMBEDDING_PORT": "5002",
            "SOPHIA_RESEARCH_PORT": "5003",
            "SOPHIA_NOTION_PORT": "5004",
            
            # Kubernetes configuration
            "KUBERNETES_NAMESPACE": NAMESPACE,
            "KUBERNETES_CLUSTER_NAME": CLUSTER_NAME,
            "KUBERNETES_NODE_IP": NODE_IP,
            
            # Resource limits
            "REPLICA_COUNT": str(REPLICA_COUNT),
            "RESOURCE_LIMITS_CPU": CPU_LIMIT,
            "RESOURCE_LIMITS_MEMORY": MEMORY_LIMIT
        }
        
        self.config_map = k8s.core.v1.ConfigMap(
            "sophia-config",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="sophia-config",
                namespace=self.namespace.metadata.name,
                labels={
                    "app": "sophia-intel",
                    "component": "config",
                    "managed-by": "pulumi"
                }
            ),
            data=config_data
        )
        return self.config_map
    
    def create_deployment(self, name: str, image: str, port: int, 
                         env_vars: Optional[Dict[str, str]] = None) -> k8s.apps.v1.Deployment:
        """Create a deployment with standardized configuration"""
        
        # Base environment variables from ConfigMap
        env_from = [
            k8s.core.v1.EnvFromSourceArgs(
                config_map_ref=k8s.core.v1.ConfigMapEnvSourceArgs(
                    name=self.config_map.metadata.name
                )
            )
        ]
        
        # Environment variables from secrets
        env = [
            k8s.core.v1.EnvVarArgs(
                name="OPENROUTER_API_KEY",
                value_from=k8s.core.v1.EnvVarSourceArgs(
                    secret_key_ref=k8s.core.v1.SecretKeySelectorArgs(
                        name=self.secrets.metadata.name,
                        key="openrouter-api-key"
                    )
                )
            ),
            k8s.core.v1.EnvVarArgs(
                name="OPENAI_API_KEY",
                value_from=k8s.core.v1.EnvVarSourceArgs(
                    secret_key_ref=k8s.core.v1.SecretKeySelectorArgs(
                        name=self.secrets.metadata.name,
                        key="openai-api-key"
                    )
                )
            ),
            # Add more secret environment variables as needed
        ]
        
        # Add custom environment variables
        if env_vars:
            for key, value in env_vars.items():
                env.append(k8s.core.v1.EnvVarArgs(name=key, value=value))
        
        deployment = k8s.apps.v1.Deployment(
            f"{name}-deployment",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=self.namespace.metadata.name,
                labels={
                    "app": name,
                    "component": "application",
                    "managed-by": "pulumi"
                }
            ),
            spec=k8s.apps.v1.DeploymentSpecArgs(
                replicas=REPLICA_COUNT,
                selector=k8s.meta.v1.LabelSelectorArgs(
                    match_labels={"app": name}
                ),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(
                        labels={"app": name}
                    ),
                    spec=k8s.core.v1.PodSpecArgs(
                        containers=[
                            k8s.core.v1.ContainerArgs(
                                name=name,
                                image=image,
                                ports=[k8s.core.v1.ContainerPortArgs(
                                    container_port=port,
                                    name="http"
                                )],
                                env=env,
                                env_from=env_from,
                                resources=k8s.core.v1.ResourceRequirementsArgs(
                                    limits={
                                        "cpu": CPU_LIMIT,
                                        "memory": MEMORY_LIMIT
                                    },
                                    requests={
                                        "cpu": "250m",
                                        "memory": "256Mi"
                                    }
                                ),
                                liveness_probe=k8s.core.v1.ProbeArgs(
                                    http_get=k8s.core.v1.HTTPGetActionArgs(
                                        path="/health",
                                        port="http"
                                    ),
                                    initial_delay_seconds=30,
                                    period_seconds=10
                                ),
                                readiness_probe=k8s.core.v1.ProbeArgs(
                                    http_get=k8s.core.v1.HTTPGetActionArgs(
                                        path="/health",
                                        port="http"
                                    ),
                                    initial_delay_seconds=5,
                                    period_seconds=5
                                )
                            )
                        ]
                    )
                )
            )
        )
        
        self.deployments[name] = deployment
        return deployment
    
    def create_service(self, name: str, port: int, target_port: int = None) -> k8s.core.v1.Service:
        """Create a service for a deployment"""
        
        if target_port is None:
            target_port = port
            
        service = k8s.core.v1.Service(
            f"{name}-service",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=self.namespace.metadata.name,
                labels={
                    "app": name,
                    "component": "service",
                    "managed-by": "pulumi"
                }
            ),
            spec=k8s.core.v1.ServiceSpecArgs(
                selector={"app": name},
                ports=[k8s.core.v1.ServicePortArgs(
                    port=port,
                    target_port=target_port,
                    name="http"
                )],
                type="ClusterIP"
            )
        )
        
        self.services[name] = service
        return service
    
    def create_ingress(self, routes: List[Dict[str, str]]) -> k8s.networking.v1.Ingress:
        """Create Kong ingress with multiple routes"""
        
        rules = []
        for route in routes:
            rules.append(
                k8s.networking.v1.IngressRuleArgs(
                    host=route["host"],
                    http=k8s.networking.v1.HTTPIngressRuleValueArgs(
                        paths=[
                            k8s.networking.v1.HTTPIngressPathArgs(
                                path=route.get("path", "/"),
                                path_type="Prefix",
                                backend=k8s.networking.v1.IngressBackendArgs(
                                    service=k8s.networking.v1.IngressServiceBackendArgs(
                                        name=route["service"],
                                        port=k8s.networking.v1.ServiceBackendPortArgs(
                                            number=route["port"]
                                        )
                                    )
                                )
                            )
                        ]
                    )
                )
            )
        
        self.ingress = k8s.networking.v1.Ingress(
            "sophia-ingress",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="sophia-ingress",
                namespace=self.namespace.metadata.name,
                labels={
                    "app": "sophia-intel",
                    "component": "ingress",
                    "managed-by": "pulumi"
                },
                annotations={
                    "kubernetes.io/ingress.class": "kong",
                    "cert-manager.io/cluster-issuer": "letsencrypt-prod",
                    "konghq.com/strip-path": "false"
                }
            ),
            spec=k8s.networking.v1.IngressSpecArgs(
                tls=[
                    k8s.networking.v1.IngressTLSArgs(
                        hosts=[f"www.{DOMAIN}", f"api.{DOMAIN}", f"dashboard.{DOMAIN}"],
                        secret_name="sophia-tls-secret"
                    )
                ],
                rules=rules
            )
        )
        return self.ingress

# Create the infrastructure
def create_sophia_infrastructure():
    """Main function to create all SOPHIA infrastructure"""
    
    sophia = SophiaInfrastructure()
    
    # Create namespace
    namespace = sophia.create_namespace()
    
    # Create secrets and config
    secrets = sophia.create_secrets()
    config_map = sophia.create_config_map()
    
    # Create main applications
    api_deployment = sophia.create_deployment(
        "sophia-api-enhanced", 
        "sophia-intel/api:latest", 
        8000
    )
    api_service = sophia.create_service("sophia-api-enhanced", 8000)
    
    dashboard_deployment = sophia.create_deployment(
        "sophia-dashboard", 
        "sophia-intel/dashboard:latest", 
        3000
    )
    dashboard_service = sophia.create_service("sophia-dashboard", 3000)
    
    # Create ingress routes
    ingress_routes = [
        {
            "host": f"www.{DOMAIN}",
            "service": "sophia-dashboard",
            "port": 3000
        },
        {
            "host": f"api.{DOMAIN}",
            "service": "sophia-api-enhanced",
            "port": 8000
        },
        {
            "host": f"dashboard.{DOMAIN}",
            "service": "sophia-dashboard",
            "port": 3000
        }
    ]
    
    ingress = sophia.create_ingress(ingress_routes)
    
    # Export important values
    pulumi.export("namespace", namespace.metadata.name)
    pulumi.export("api_endpoint", f"https://api.{DOMAIN}")
    pulumi.export("dashboard_endpoint", f"https://dashboard.{DOMAIN}")
    pulumi.export("web_endpoint", f"https://www.{DOMAIN}")
    pulumi.export("cluster_name", CLUSTER_NAME)
    pulumi.export("environment", ENVIRONMENT)
    
    return sophia

# Execute if run directly
if __name__ == "__main__":
    infrastructure = create_sophia_infrastructure()

