"""
SOPHIA Intel Production Infrastructure
Deploys to Kubernetes with proper scaling, monitoring, and security
"""

import pulumi
import pulumi_aws as aws
import pulumi_kubernetes as k8s
from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs
from pulumi_kubernetes.core.v1 import (
    Service, ServiceSpecArgs, ServicePortArgs,
    ConfigMap, Secret, Namespace
)
from pulumi_kubernetes.networking.v1 import Ingress, IngressSpecArgs

# Configuration
config = pulumi.Config()
cluster_name = config.get("cluster_name") or "sophia-intel-prod"
namespace_name = config.get("namespace") or "sophia-intel"

# Create namespace
namespace = Namespace(
    "sophia-intel-namespace",
    metadata={"name": namespace_name}
)

# Secrets for API keys
secrets = Secret(
    "sophia-intel-secrets",
    metadata={
        "name": "sophia-intel-secrets",
        "namespace": namespace_name
    },
    string_data={
        "LAMBDA_API_KEY": config.require_secret("lambda_api_key"),
        "OPENROUTER_API_KEY": config.require_secret("openrouter_api_key"),
        "GITHUB_PAT": config.require_secret("github_pat"),
        "DNSIMPLE_API_KEY": config.require_secret("dnsimple_api_key"),
    },
    opts=pulumi.ResourceOptions(depends_on=[namespace])
)

# ConfigMap for non-sensitive config
config_map = ConfigMap(
    "sophia-intel-config",
    metadata={
        "name": "sophia-intel-config", 
        "namespace": namespace_name
    },
    data={
        "LAMBDA_API_BASE": "https://api.lambda.ai/v1",
        "ENVIRONMENT": "production",
        "LOG_LEVEL": "INFO"
    },
    opts=pulumi.ResourceOptions(depends_on=[namespace])
)

# Dashboard Backend Deployment
dashboard_backend = Deployment(
    "sophia-dashboard-backend",
    metadata={
        "name": "sophia-dashboard-backend",
        "namespace": namespace_name
    },
    spec=DeploymentSpecArgs(
        replicas=3,
        selector={"matchLabels": {"app": "sophia-dashboard-backend"}},
        template={
            "metadata": {"labels": {"app": "sophia-dashboard-backend"}},
            "spec": {
                "containers": [{
                    "name": "dashboard-backend",
                    "image": "sophia-intel/dashboard-backend:latest",
                    "ports": [{"containerPort": 5000}],
                    "env": [
                        {"name": "PORT", "value": "5000"},
                        {"name": "LAMBDA_API_KEY", "valueFrom": {"secretKeyRef": {"name": "sophia-intel-secrets", "key": "LAMBDA_API_KEY"}}},
                        {"name": "LAMBDA_API_BASE", "valueFrom": {"configMapKeyRef": {"name": "sophia-intel-config", "key": "LAMBDA_API_BASE"}}},
                    ],
                    "livenessProbe": {
                        "httpGet": {"path": "/health", "port": 5000},
                        "initialDelaySeconds": 30,
                        "periodSeconds": 10
                    },
                    "readinessProbe": {
                        "httpGet": {"path": "/health", "port": 5000},
                        "initialDelaySeconds": 5,
                        "periodSeconds": 5
                    },
                    "resources": {
                        "requests": {"cpu": "100m", "memory": "256Mi"},
                        "limits": {"cpu": "500m", "memory": "512Mi"}
                    }
                }]
            }
        }
    ),
    opts=pulumi.ResourceOptions(depends_on=[namespace, secrets, config_map])
)

# Dashboard Backend Service
dashboard_backend_service = Service(
    "sophia-dashboard-backend-service",
    metadata={
        "name": "sophia-dashboard-backend",
        "namespace": namespace_name
    },
    spec=ServiceSpecArgs(
        selector={"app": "sophia-dashboard-backend"},
        ports=[ServicePortArgs(port=5000, target_port=5000)],
        type="ClusterIP"
    ),
    opts=pulumi.ResourceOptions(depends_on=[dashboard_backend])
)

# API Gateway Deployment
api_gateway = Deployment(
    "sophia-api-gateway",
    metadata={
        "name": "sophia-api-gateway",
        "namespace": namespace_name
    },
    spec=DeploymentSpecArgs(
        replicas=3,
        selector={"matchLabels": {"app": "sophia-api-gateway"}},
        template={
            "metadata": {"labels": {"app": "sophia-api-gateway"}},
            "spec": {
                "containers": [{
                    "name": "api-gateway",
                    "image": "sophia-intel/api-gateway:latest", 
                    "ports": [{"containerPort": 8000}],
                    "env": [
                        {"name": "PORT", "value": "8000"},
                        {"name": "LAMBDA_API_KEY", "valueFrom": {"secretKeyRef": {"name": "sophia-intel-secrets", "key": "LAMBDA_API_KEY"}}},
                        {"name": "OPENROUTER_API_KEY", "valueFrom": {"secretKeyRef": {"name": "sophia-intel-secrets", "key": "OPENROUTER_API_KEY"}}},
                    ],
                    "livenessProbe": {
                        "httpGet": {"path": "/health", "port": 8000},
                        "initialDelaySeconds": 30,
                        "periodSeconds": 10
                    },
                    "readinessProbe": {
                        "httpGet": {"path": "/health", "port": 8000},
                        "initialDelaySeconds": 5,
                        "periodSeconds": 5
                    },
                    "resources": {
                        "requests": {"cpu": "200m", "memory": "512Mi"},
                        "limits": {"cpu": "1000m", "memory": "1Gi"}
                    }
                }]
            }
        }
    ),
    opts=pulumi.ResourceOptions(depends_on=[namespace, secrets, config_map])
)

# API Gateway Service
api_gateway_service = Service(
    "sophia-api-gateway-service",
    metadata={
        "name": "sophia-api-gateway",
        "namespace": namespace_name
    },
    spec=ServiceSpecArgs(
        selector={"app": "sophia-api-gateway"},
        ports=[ServicePortArgs(port=8000, target_port=8000)],
        type="ClusterIP"
    ),
    opts=pulumi.ResourceOptions(depends_on=[api_gateway])
)

# MCP Servers Deployment
mcp_servers = Deployment(
    "sophia-mcp-servers",
    metadata={
        "name": "sophia-mcp-servers",
        "namespace": namespace_name
    },
    spec=DeploymentSpecArgs(
        replicas=2,
        selector={"matchLabels": {"app": "sophia-mcp-servers"}},
        template={
            "metadata": {"labels": {"app": "sophia-mcp-servers"}},
            "spec": {
                "containers": [{
                    "name": "mcp-servers",
                    "image": "sophia-intel/mcp-servers:latest",
                    "ports": [{"containerPort": 8001}],
                    "env": [
                        {"name": "PORT", "value": "8001"},
                        {"name": "LAMBDA_API_KEY", "valueFrom": {"secretKeyRef": {"name": "sophia-intel-secrets", "key": "LAMBDA_API_KEY"}}},
                        {"name": "GITHUB_PAT", "valueFrom": {"secretKeyRef": {"name": "sophia-intel-secrets", "key": "GITHUB_PAT"}}},
                    ],
                    "livenessProbe": {
                        "httpGet": {"path": "/health", "port": 8001},
                        "initialDelaySeconds": 30,
                        "periodSeconds": 10
                    },
                    "readinessProbe": {
                        "httpGet": {"path": "/health", "port": 8001},
                        "initialDelaySeconds": 5,
                        "periodSeconds": 5
                    },
                    "resources": {
                        "requests": {"cpu": "100m", "memory": "256Mi"},
                        "limits": {"cpu": "500m", "memory": "512Mi"}
                    }
                }]
            }
        }
    ),
    opts=pulumi.ResourceOptions(depends_on=[namespace, secrets, config_map])
)

# MCP Servers Service
mcp_servers_service = Service(
    "sophia-mcp-servers-service",
    metadata={
        "name": "sophia-mcp-servers",
        "namespace": namespace_name
    },
    spec=ServiceSpecArgs(
        selector={"app": "sophia-mcp-servers"},
        ports=[ServicePortArgs(port=8001, target_port=8001)],
        type="ClusterIP"
    ),
    opts=pulumi.ResourceOptions(depends_on=[mcp_servers])
)

# Ingress for external access
ingress = Ingress(
    "sophia-intel-ingress",
    metadata={
        "name": "sophia-intel-ingress",
        "namespace": namespace_name,
        "annotations": {
            "kubernetes.io/ingress.class": "nginx",
            "cert-manager.io/cluster-issuer": "letsencrypt-prod",
            "nginx.ingress.kubernetes.io/ssl-redirect": "true"
        }
    },
    spec=IngressSpecArgs(
        tls=[{
            "hosts": ["sophia-intel.ai", "api.sophia-intel.ai", "dashboard.sophia-intel.ai"],
            "secretName": "sophia-intel-tls"
        }],
        rules=[
            {
                "host": "sophia-intel.ai",
                "http": {
                    "paths": [{
                        "path": "/",
                        "pathType": "Prefix",
                        "backend": {"service": {"name": "sophia-api-gateway", "port": {"number": 8000}}}
                    }]
                }
            },
            {
                "host": "api.sophia-intel.ai", 
                "http": {
                    "paths": [{
                        "path": "/",
                        "pathType": "Prefix",
                        "backend": {"service": {"name": "sophia-api-gateway", "port": {"number": 8000}}}
                    }]
                }
            },
            {
                "host": "dashboard.sophia-intel.ai",
                "http": {
                    "paths": [{
                        "path": "/",
                        "pathType": "Prefix", 
                        "backend": {"service": {"name": "sophia-dashboard-backend", "port": {"number": 5000}}}
                    }]
                }
            }
        ]
    ),
    opts=pulumi.ResourceOptions(depends_on=[api_gateway_service, dashboard_backend_service])
)

# Export important values
pulumi.export("namespace", namespace_name)
pulumi.export("dashboard_backend_service", dashboard_backend_service.metadata["name"])
pulumi.export("api_gateway_service", api_gateway_service.metadata["name"])
pulumi.export("mcp_servers_service", mcp_servers_service.metadata["name"])
pulumi.export("ingress_name", ingress.metadata["name"])
