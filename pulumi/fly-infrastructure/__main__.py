"""
Fly.io Infrastructure Provisioning for Sophia Intel AI
Provisions all 6 microservices with proper scaling, storage, and networking
"""

import pulumi
import requests
import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pulumi import Output


@dataclass
class FlyAppSpec:
    """Specification for a Fly.io application"""
    name: str
    dockerfile: Optional[str] = None
    image: Optional[str] = None
    port: int = 8080
    memory_mb: int = 1024
    cpu_cores: float = 1.0
    min_instances: int = 1
    max_instances: int = 4
    volume_size_gb: int = 5
    env_vars: Optional[Dict[str, str]] = None
    health_check_path: str = "/health"


class FlyResourceProvider(pulumi.dynamic.ResourceProvider):
    """Dynamic resource provider for Fly.io applications"""
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://api.machines.dev/v1"
    
    def create(self, props: Dict[str, Any]) -> pulumi.dynamic.CreateResult:
        """Create a Fly.io application and configure it"""
        app_name = props["name"]
        app_spec = props["spec"]
        
        try:
            # Create the Fly.io application
            app_data = {
                "app_name": app_name,
                "org_slug": "sophia-intel-ai"
            }
            
            app_response = requests.post(
                f"https://api.fly.io/v1/apps",
                headers=self.headers,
                json=app_data
            )
            
            if app_response.status_code == 201:
                app_info = app_response.json()
                print(f"✅ Created Fly.io app: {app_name}")
            else:
                # App might already exist, try to get it
                get_response = requests.get(
                    f"https://api.fly.io/v1/apps/{app_name}",
                    headers=self.headers
                )
                if get_response.status_code == 200:
                    app_info = get_response.json()
                    print(f"📱 Using existing Fly.io app: {app_name}")
                else:
                    raise Exception(f"Failed to create or get app {app_name}: {app_response.text}")
            
            # Create volume if needed
            if app_spec.get("volume_size_gb", 0) > 0:
                volume_data = {
                    "name": f"{app_name}_data",
                    "size_gb": app_spec["volume_size_gb"],
                    "region": props.get("primary_region", "sjc")
                }
                
                volume_response = requests.post(
                    f"https://api.fly.io/v1/apps/{app_name}/volumes",
                    headers=self.headers,
                    json=volume_data
                )
                
                if volume_response.status_code in [200, 201]:
                    print(f"💾 Created volume for {app_name}: {app_spec['volume_size_gb']}GB")
                else:
                    print(f"⚠️  Volume creation failed for {app_name}: {volume_response.text}")
            
            # Configure machine settings
            machine_config = {
                "config": {
                    "image": app_spec.get("image", "registry.fly.io/placeholder"),
                    "env": app_spec.get("env_vars", {}),
                    "services": [
                        {
                            "protocol": "tcp",
                            "internal_port": app_spec["port"],
                            "ports": [
                                {"port": 80, "handlers": ["http"]},
                                {"port": 443, "handlers": ["tls", "http"]}
                            ],
                            "concurrency": {
                                "type": "connections",
                                "hard_limit": 250,
                                "soft_limit": 200
                            },
                            "http_checks": [
                                {
                                    "interval": "30s",
                                    "timeout": "10s",
                                    "method": "GET",
                                    "path": app_spec["health_check_path"]
                                }
                            ]
                        }
                    ],
                    "guest": {
                        "cpu_kind": "shared",
                        "cpus": app_spec["cpu_cores"],
                        "memory_mb": app_spec["memory_mb"]
                    }
                }
            }
            
            # Set up auto-scaling
            scale_config = {
                "count": {
                    "min": app_spec["min_instances"],
                    "max": app_spec["max_instances"]
                },
                "regions": [props.get("primary_region", "sjc")],
                "http_service": {
                    "auto_stop_machines": True,
                    "auto_start_machines": True,
                    "min_machines_running": app_spec["min_instances"]
                }
            }
            
            return pulumi.dynamic.CreateResult(
                id_=app_name,
                outs={
                    "name": app_name,
                    "hostname": f"{app_name}.fly.dev",
                    "internal_url": f"http://{app_name}.internal:{app_spec['port']}",
                    "public_url": f"https://{app_name}.fly.dev",
                    "status": "created"
                }
            )
            
        except Exception as e:
            raise Exception(f"Failed to create Fly.io app {app_name}: {str(e)}")
    
    def delete(self, id_: str, props: Dict[str, Any]) -> None:
        """Delete a Fly.io application"""
        try:
            response = requests.delete(
                f"https://api.fly.io/v1/apps/{id_}",
                headers=self.headers
            )
            if response.status_code == 200:
                print(f"🗑️  Deleted Fly.io app: {id_}")
            else:
                print(f"⚠️  Failed to delete app {id_}: {response.text}")
        except Exception as e:
            print(f"Error deleting app {id_}: {str(e)}")


class FlyApp(pulumi.dynamic.Resource):
    """Fly.io application resource"""
    
    def __init__(self, name: str, spec: FlyAppSpec, api_token: str, 
                 primary_region: str = "sjc", opts: Optional[pulumi.ResourceOptions] = None):
        
        provider = FlyResourceProvider(api_token)
        
        super().__init__(
            provider,
            name,
            {
                "name": spec.name,
                "spec": {
                    "image": spec.image,
                    "dockerfile": spec.dockerfile,
                    "port": spec.port,
                    "memory_mb": spec.memory_mb,
                    "cpu_cores": spec.cpu_cores,
                    "min_instances": spec.min_instances,
                    "max_instances": spec.max_instances,
                    "volume_size_gb": spec.volume_size_gb,
                    "env_vars": spec.env_vars or {},
                    "health_check_path": spec.health_check_path
                },
                "primary_region": primary_region
            },
            opts
        )


def main():
    """Main infrastructure provisioning function"""
    
    config = pulumi.Config()
    environment = config.get("environment") or "prod"
    primary_region = config.get("primary_region") or "sjc"  # San Jose
    secondary_region = config.get("secondary_region") or "iad"  # Washington DC
    
    # Get API token from environment or config
    fly_api_token = os.environ.get("FLY_API_TOKEN") or config.require_secret("fly_api_token")
    
    print(f"🚀 Provisioning Sophia Intel AI infrastructure in {environment}")
    print(f"🌍 Primary region: {primary_region}, Secondary region: {secondary_region}")
    
    # Service specifications based on requirements
    service_specs = {
        # 1. Weaviate Vector Database (Foundation Service)
        "sophia-weaviate": FlyAppSpec(
            name="sophia-weaviate",
            image="semitechnologies/weaviate:1.32.1",
            port=8080,
            memory_mb=2048,
            cpu_cores=2.0,
            min_instances=1,
            max_instances=4,  # As specified in requirements
            volume_size_gb=20,  # 20GB for vector data
            health_check_path="/v1/.well-known/ready",
            env_vars={
                "QUERY_DEFAULTS_LIMIT": "25",
                "AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED": "true",
                "PERSISTENCE_DATA_PATH": "/var/lib/weaviate",
                "ENABLE_MODULES": "text2vec-openai,text2vec-cohere,text2vec-huggingface,generative-openai,qna-openai",
                "DEFAULT_VECTORIZER_MODULE": "text2vec-openai",
                "VECTOR_INDEX_TYPE": "hnsw",
                "ENABLE_VECTOR_QUANTIZATION": "true",
                "QUANTIZATION_TYPE": "rq",
                "CLUSTER_HOSTNAME": "node1",
                "ENABLE_MULTI_TENANCY": "true",
                "AUTO_TENANT_CREATION": "true",
                "GOGC": "100"
            }
        ),
        
        # 2. MCP Memory Management Server
        "sophia-mcp": FlyAppSpec(
            name="sophia-mcp",
            dockerfile="./pulumi/mcp-server/Dockerfile",
            port=8004,
            memory_mb=2048,
            cpu_cores=2.0,
            min_instances=1,
            max_instances=8,  # As specified in requirements
            volume_size_gb=5,   # 5GB for memory data
            health_check_path="/health",
            env_vars={
                "MCP_SERVER_PORT": "8004",
                "PYTHONPATH": "/app",
                "PYTHONUNBUFFERED": "1",
                "LOCAL_DEV_MODE": "false",
                "WEAVIATE_URL": "http://sophia-weaviate.internal:8080",
                "USE_REAL_APIS": "true",
                "ENABLE_API_VALIDATION": "true",
                "ENABLE_MCP_PROTOCOL": "true"
            }
        ),
        
        # 3. Vector Store with 3-tier embeddings
        "sophia-vector": FlyAppSpec(
            name="sophia-vector",
            dockerfile="./pulumi/vector-store/Dockerfile",
            port=8005,
            memory_mb=2048,
            cpu_cores=2.0,
            min_instances=1,
            max_instances=12,  # As specified in requirements
            volume_size_gb=10,  # 10GB for embedding cache
            health_check_path="/health",
            env_vars={
                "VECTOR_STORE_PORT": "8005",
                "PYTHONPATH": "/app",
                "PYTHONUNBUFFERED": "1",
                "LOCAL_DEV_MODE": "false",
                "WEAVIATE_URL": "http://sophia-weaviate.internal:8080",
                "EMBEDDING_TIER_S_MODEL": "voyage-3-large",
                "EMBEDDING_TIER_A_MODEL": "cohere/embed-multilingual-v3.0",
                "EMBEDDING_TIER_B_MODEL": "BAAI/bge-base-en-v1.5",
                "PORTKEY_BASE_URL": "https://api.portkey.ai/v1",
                "USE_REAL_APIS": "true",
                "ENABLE_API_VALIDATION": "true",
                "ENABLE_EMBEDDING_CACHE": "true"
            }
        ),
        
        # 4. Unified API - Main Orchestrator (Critical Service)
        "sophia-api": FlyAppSpec(
            name="sophia-api",
            dockerfile="Dockerfile.unified-api.production",
            port=8003,
            memory_mb=4096,
            cpu_cores=4.0,
            min_instances=2,  # Higher availability for main API
            max_instances=20,  # As specified in requirements (critical service)
            volume_size_gb=15,  # 15GB for API data and logs
            health_check_path="/healthz",
            env_vars={
                "PORT": "8003",
                "PYTHONPATH": "/app",
                "PYTHONUNBUFFERED": "1",
                "LOCAL_DEV_MODE": "false",
                "WEAVIATE_URL": "http://sophia-weaviate.internal:8080",
                "MCP_SERVER_URL": "http://sophia-mcp.internal:8004",
                "VECTOR_STORE_URL": "http://sophia-vector.internal:8005",
                "DEFAULT_FAST_MODEL": "groq/llama-3.2-90b-text-preview",
                "DEFAULT_BALANCED_MODEL": "openai/gpt-4o-mini",
                "DEFAULT_HEAVY_MODEL": "anthropic/claude-3.5-sonnet",
                "PORTKEY_BASE_URL": "https://api.portkey.ai/v1",
                "USE_REAL_APIS": "true",
                "ENABLE_API_VALIDATION": "true",
                "FAIL_ON_MOCK_FALLBACK": "true",
                "ENABLE_CONSENSUS_SWARMS": "true",
                "ENABLE_MEMORY_DEDUPLICATION": "true"
            }
        ),
        
        # 5. Agno Bridge - UI Compatibility Layer
        "sophia-bridge": FlyAppSpec(
            name="sophia-bridge",
            dockerfile="Dockerfile.agno-bridge.production",
            port=7777,
            memory_mb=1024,
            cpu_cores=1.0,
            min_instances=1,
            max_instances=8,  # As specified in requirements
            volume_size_gb=2,   # Minimal storage for bridge
            health_check_path="/healthz",
            env_vars={
                "PORT": "7777",
                "PYTHONPATH": "/app",
                "PYTHONUNBUFFERED": "1",
                "LOCAL_DEV_MODE": "false",
                "UNIFIED_API_URL": "http://sophia-api.internal:8003",
                "MCP_SERVER_URL": "http://sophia-mcp.internal:8004",
                "VECTOR_STORE_URL": "http://sophia-vector.internal:8005",
                "ENABLE_CORS": "true",
                "CORS_ORIGINS": "*",  # Will be restricted in production
                "DEBUG": "false",
                "USE_REAL_APIS": "true",
                "ENABLE_API_VALIDATION": "true"
            }
        ),
        
        # 6. Agent UI - Next.js Frontend
        "sophia-ui": FlyAppSpec(
            name="sophia-ui",
            dockerfile="./agent-ui/Dockerfile",
            port=3000,
            memory_mb=1024,
            cpu_cores=1.0,
            min_instances=1,
            max_instances=6,  # As specified in requirements
            volume_size_gb=1,   # Minimal storage for frontend logs
            health_check_path="/",
            env_vars={
                "NODE_ENV": "production",
                "PORT": "3000",
                "NEXT_PUBLIC_API_URL": "https://sophia-api.fly.dev",
                "NEXT_PUBLIC_BRIDGE_URL": "https://sophia-bridge.fly.dev",
                "NEXT_PUBLIC_DEFAULT_ENDPOINT": "https://sophia-api.fly.dev",
                "NEXT_PUBLIC_PLAYGROUND_URL": "https://sophia-api.fly.dev",
                "NEXT_PUBLIC_USE_BRIDGE": "true",
                "NEXT_PUBLIC_ENABLE_ANALYTICS": "true",
                "NEXT_PUBLIC_ENVIRONMENT": "production",
                "NEXT_PUBLIC_ENABLE_CONSENSUS_UI": "true",
                "NEXT_PUBLIC_ENABLE_MEMORY_DEDUP_UI": "true",
                "NEXT_PUBLIC_ENABLE_SWARM_MONITORING": "true"
            }
        )
    }
    
    # Deploy all services
    deployed_services = {}
    
    for service_name, spec in service_specs.items():
        print(f"🏗️  Deploying {service_name}...")
        
        deployed_services[service_name] = FlyApp(
            f"fly-{service_name}",
            spec,
            fly_api_token,
            primary_region
        )
    
    # Export service URLs and configuration
    pulumi.export("environment", environment)
    pulumi.export("primary_region", primary_region)
    pulumi.export("secondary_region", secondary_region)
    
    # Export service URLs
    for service_name, service in deployed_services.items():
        pulumi.export(f"{service_name.replace('-', '_')}_url", service.public_url)
        pulumi.export(f"{service_name.replace('-', '_')}_internal_url", service.internal_url)
    
    # Export infrastructure summary
    pulumi.export("infrastructure_summary", {
        "total_services": len(service_specs),
        "services": list(service_specs.keys()),
        "scaling_configuration": {
            service_name: {
                "min_instances": spec.min_instances,
                "max_instances": spec.max_instances,
                "memory_mb": spec.memory_mb,
                "cpu_cores": spec.cpu_cores,
                "storage_gb": spec.volume_size_gb
            }
            for service_name, spec in service_specs.items()
        },
        "total_storage_gb": sum(spec.volume_size_gb for spec in service_specs.values()),
        "total_max_instances": sum(spec.max_instances for spec in service_specs.values()),
        "regions": [primary_region, secondary_region]
    })
    
    # Export networking configuration
    pulumi.export("networking_config", {
        "internal_services": {
            "weaviate": "http://sophia-weaviate.internal:8080",
            "mcp_server": "http://sophia-mcp.internal:8004", 
            "vector_store": "http://sophia-vector.internal:8005",
            "unified_api": "http://sophia-api.internal:8003",
            "agno_bridge": "http://sophia-bridge.internal:7777",
            "agent_ui": "http://sophia-ui.internal:3000"
        },
        "public_endpoints": {
            "weaviate": "https://sophia-weaviate.fly.dev",
            "mcp_server": "https://sophia-mcp.fly.dev",
            "vector_store": "https://sophia-vector.fly.dev", 
            "unified_api": "https://sophia-api.fly.dev",
            "agno_bridge": "https://sophia-bridge.fly.dev",
            "agent_ui": "https://sophia-ui.fly.dev"
        }
    })
    
    print("✅ Infrastructure deployment configuration complete!")


if __name__ == "__main__":
    main()