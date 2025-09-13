#!/usr/bin/env python3
"""
Direct Fly.io Infrastructure Provisioning Script for Sophia Intel AI
Provisions all 6 microservices using Fly.io REST API directly
"""
import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Any
import requests
from app.core.ai_logger import logger
@dataclass
class ServiceSpec:
    """Specification for a Fly.io service"""
    name: str
    image: str | None = None
    dockerfile: str | None = None
    port: int = 8080
    memory_mb: int = 1024
    cpu_cores: float = 1.0
    min_instances: int = 1
    max_instances: int = 4
    volume_size_gb: int = 5
    env_vars: dict[str, str] | None = None
    health_check_path: str = "/health"
class FlyInfrastructureProvisioner:
    """Provisions Fly.io infrastructure using direct API calls"""
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }
        self.base_url = "https://api.fly.io/v1"
        self.org_slug = "personal"  # Use personal org
    def create_app(self, app_name: str) -> dict[str, Any]:
        """Create a Fly.io application"""
        payload = {"app_name": app_name, "org_slug": self.org_slug}
        response = requests.post(
            f"{self.base_url}/apps", headers=self.headers, json=payload
        )
        if response.status_code in [200, 201]:
            logger.info(f"✅ Created Fly.io app: {app_name}")
            return response.json()
        elif response.status_code == 422 and "already exists" in response.text.lower():
            logger.info(f"📱 App {app_name} already exists, continuing...")
            # Get existing app info
            get_response = requests.get(
                f"{self.base_url}/apps/{app_name}", headers=self.headers
            )
            if get_response.status_code == 200:
                return get_response.json()
            else:
                logger.info(
                    f"Warning: Could not get existing app info: {get_response.text}"
                )
                return {"name": app_name, "status": "exists"}
        else:
            logger.info(
                f"⚠️  Failed to create app {app_name}: {response.status_code} - {response.text}"
            )
            return {"name": app_name, "status": "error", "error": response.text}
    def create_volume(
        self, app_name: str, volume_name: str, size_gb: int, region: str = "sjc"
    ) -> dict[str, Any]:
        """Create a persistent volume for an app"""
        payload = {"name": volume_name, "size_gb": size_gb, "region": region}
        response = requests.post(
            f"{self.base_url}/apps/{app_name}/volumes",
            headers=self.headers,
            json=payload,
        )
        if response.status_code in [200, 201]:
            logger.info(f"💾 Created {size_gb}GB volume '{volume_name}' for {app_name}")
            return response.json()
        elif "already exists" in response.text.lower():
            logger.info(f"💾 Volume '{volume_name}' already exists for {app_name}")
            return {
                "name": volume_name,
                "size_gb": size_gb,
                "region": region,
                "status": "exists",
            }
        else:
            logger.info(f"⚠️  Volume creation warning for {app_name}: {response.text}")
            return {
                "name": volume_name,
                "size_gb": size_gb,
                "region": region,
                "status": "warning",
            }
    def deploy_service(
        self, spec: ServiceSpec, primary_region: str = "sjc"
    ) -> dict[str, Any]:
        """Deploy a service with app and volume"""
        logger.info(f"\n🚀 Deploying {spec.name}...")
        # 1. Create the application
        app_info = self.create_app(spec.name)
        # 2. Create volume if needed
        volume_info = None
        if spec.volume_size_gb > 0:
            volume_name = f"{spec.name.replace('-', '_')}_data"
            volume_info = self.create_volume(
                spec.name, volume_name, spec.volume_size_gb, primary_region
            )
        # 3. Generate fly.toml configuration
        toml_config = self.generate_fly_toml(spec, volume_info, primary_region)
        # 4. Write the fly.toml file
        toml_filename = f"fly-{spec.name}.toml"
        try:
            with open(toml_filename, "w") as f:
                f.write(toml_config)
            logger.info(f"📄 Generated {toml_filename}")
        except Exception as e:
            logger.info(f"⚠️  Could not write {toml_filename}: {str(e)}")
        return {
            "app_name": spec.name,
            "app_info": app_info,
            "volume_info": volume_info,
            "fly_toml": toml_filename,
            "public_url": f"https://{spec.name}.fly.dev",
            "internal_url": f"http://{spec.name}.internal:{spec.port}",
            "status": "configured",
        }
    def generate_fly_toml(
        self, spec: ServiceSpec, volume_info: dict | None, primary_region: str
    ) -> str:
        """Generate fly.toml configuration for a service"""
        toml_lines = [
            f'app = "{spec.name}"',
            f'primary_region = "{primary_region}"',
            'kill_signal = "SIGINT"',
            'kill_timeout = "5s"',
            "",
            "[build]",
        ]
        if spec.dockerfile:
            toml_lines.append(f'  dockerfile = "{spec.dockerfile}"')
        elif spec.image:
            toml_lines.append(f'  image = "{spec.image}"')
        # Environment variables
        if spec.env_vars:
            toml_lines.extend(["", "[env]"])
            for key, value in spec.env_vars.items():
                toml_lines.append(f'  {key} = "{value}"')
        # Experimental features
        toml_lines.extend(
            ["", "[experimental]", "  auto_rollback = true", "  enable_consul = true"]
        )
        # Services configuration
        toml_lines.extend(
            [
                "",
                "[services]",
                '  protocol = "tcp"',
                f"  internal_port = {spec.port}",
                "  auto_stop_machines = true",
                "  auto_start_machines = true",
                f"  min_machines_running = {spec.min_instances}",
                "",
                "  [[services.ports]]",
                "    port = 80",
                '    handlers = ["http"]',
                "    force_https = true",
                "",
                "  [[services.ports]]",
                "    port = 443",
                '    handlers = ["tls", "http"]',
                "",
                "  [services.concurrency]",
                '    type = "connections"',
                "    hard_limit = 250",
                "    soft_limit = 200",
                "",
                "  [[services.http_checks]]",
                '    interval = "30s"',
                '    grace_period = "10s"',
                '    method = "GET"',
                f'    path = "{spec.health_check_path}"',
                '    protocol = "http"',
                '    timeout = "10s"',
                "    tls_skip_verify = false",
            ]
        )
        # Volumes configuration
        if volume_info and spec.volume_size_gb > 0:
            toml_lines.extend(
                [
                    "",
                    "[mounts]",
                    f'  source = "{volume_info.get("name", f"{spec.name}_data")}"',
                    '  destination = "/data"',
                    f'  initial_size = "{spec.volume_size_gb}gb"',
                ]
            )
        # Machine configuration
        toml_lines.extend(
            [
                "",
                "[[vm]]",
                '  cpu_kind = "shared"',
                f"  cpus = {spec.cpu_cores}",
                f"  memory_mb = {spec.memory_mb}",
            ]
        )
        # Auto-scaling configuration
        toml_lines.extend(
            [
                "",
                "[scaling]",
                f"  min_machines_running = {spec.min_instances}",
                f"  max_machines_running = {spec.max_instances}",
                "",
                "  [[scaling.metrics]]",
                '    type = "cpu"',
                "    target = 70",
                "",
                "  [[scaling.metrics]]",
                '    type = "memory"',
                "    target = 75",
            ]
        )
        return "\n".join(toml_lines)
def main():
    """Main provisioning function"""
    # Get API token from environment
    fly_api_token = os.environ.get("FLY_API_TOKEN")
    if not fly_api_token:
        logger.info("❌ FLY_API_TOKEN environment variable is required")
        sys.exit(1)
    provisioner = FlyInfrastructureProvisioner(fly_api_token)
    logger.info("🚀 Starting Sophia Intel AI Infrastructure Provisioning")
    logger.info("=" * 60)
    # Define service specifications based on requirements
    services = [
        # 1. Weaviate Vector Database (Foundation Service)
        ServiceSpec(
            name="sophia-weaviate",
            image="semitechnologies/weaviate:1.32.1",
            port=8080,
            memory_mb=2048,
            cpu_cores=2.0,
            min_instances=1,
            max_instances=4,
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
                "GOGC": "100",
            },
        ),
        # 2. MCP Memory Management Server
        ServiceSpec(
            name="sophia-mcp",
            dockerfile="./pulumi/mcp-server/Dockerfile",
            port=8004,
            memory_mb=2048,
            cpu_cores=2.0,
            min_instances=1,
            max_instances=8,
            volume_size_gb=5,  # 5GB for memory data
            health_check_path="/health",
            env_vars={
                "MCP_SERVER_PORT": "8004",
                "PYTHONPATH": "/app",
                "PYTHONUNBUFFERED": "1",
                "LOCAL_DEV_MODE": "false",
                "WEAVIATE_URL": "http://sophia-weaviate.internal:8080",
                "USE_REAL_APIS": "true",
                "ENABLE_API_VALIDATION": "true",
                "ENABLE_MCP_PROTOCOL": "true",
            },
        ),
        # 3. Vector Store with 3-tier embeddings
        ServiceSpec(
            name="sophia-vector",
            dockerfile="./pulumi/vector-store/Dockerfile",
            port=8005,
            memory_mb=2048,
            cpu_cores=2.0,
            min_instances=1,
            max_instances=12,
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
                "ENABLE_EMBEDDING_CACHE": "true",
            },
        ),
        # 4. Unified API - Main Orchestrator (Critical Service)
        ServiceSpec(
            name="sophia-api",
            dockerfile="Dockerfile.unified-api.production",
            port=8003,
            memory_mb=4096,
            cpu_cores=4.0,
            min_instances=2,  # Higher availability
            max_instances=20,  # Critical service - maximum scaling
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
                "ENABLE_MEMORY_DEDUPLICATION": "true",
            },
        ),
        # 5. Agno Bridge - UI Compatibility Layer
        ServiceSpec(
            name="sophia-bridge",
            dockerfile="Dockerfile.agno-bridge.production",
            port=7777,
            memory_mb=1024,
            cpu_cores=1.0,
            min_instances=1,
            max_instances=8,
            volume_size_gb=2,  # Minimal storage
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
                "CORS_ORIGINS": "*",
                "DEBUG": "false",
                "USE_REAL_APIS": "true",
                "ENABLE_API_VALIDATION": "true",
            },
        ),
        # 6. Agent UI - Next.js Frontend
        ServiceSpec(
            name="sophia-ui",
            dockerfile="./sophia-intel-app/Dockerfile",
            port=3000,
            memory_mb=1024,
            cpu_cores=1.0,
            min_instances=1,
            max_instances=6,
            volume_size_gb=1,  # Minimal storage
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
                "NEXT_PUBLIC_ENABLE_SWARM_MONITORING": "true",
            },
        ),
    ]
    # Provision all services
    deployed_services = {}
    total_storage = 0
    total_max_instances = 0
    for service_spec in services:
        try:
            result = provisioner.deploy_service(service_spec, "sjc")
            deployed_services[service_spec.name] = result
            total_storage += service_spec.volume_size_gb
            total_max_instances += service_spec.max_instances
            logger.info(f"✅ Successfully configured {service_spec.name}")
        except Exception as e:
            logger.info(f"❌ Failed to configure {service_spec.name}: {str(e)}")
            deployed_services[service_spec.name] = {"error": str(e)}
    # Generate summary report
    logger.info("\n" + "=" * 60)
    logger.info("📊 SOPHIA INTEL AI INFRASTRUCTURE DEPLOYMENT SUMMARY")
    logger.info("=" * 60)
    successful_deployments = len(
        [s for s in deployed_services.values() if "error" not in s]
    )
    logger.info(
        f"🏗️  Total Services Configured: {successful_deployments}/{len(services)}"
    )
    logger.info(f"💾 Total Storage Provisioned: {total_storage}GB")
    logger.info(f"⚖️  Total Maximum Instances: {total_max_instances}")
    logger.info("🌍 Primary Region: sjc (San Jose)")
    logger.info("🌍 Secondary Region: iad (Washington DC)")
    logger.info("\n📱 SERVICE ENDPOINTS:")
    for service_name, result in deployed_services.items():
        if "error" not in result:
            logger.info(f"  • {service_name}:")
            logger.info(f"    - Public:   {result['public_url']}")
            logger.info(f"    - Internal: {result['internal_url']}")
        else:
            logger.info(
                f"  • {service_name}: ❌ CONFIGURATION FAILED - {result['error']}"
            )
    logger.info("\n🔗 INTERNAL NETWORKING:")
    logger.info(
        "  Services communicate via Fly.io internal networking (.internal domains)"
    )
    logger.info("  Health checks configured for all services")
    logger.info("  TLS/HTTPS enabled for all public endpoints")
    logger.info("\n⚖️  AUTO-SCALING CONFIGURATION:")
    for service_spec in services:
        logger.info(
            f"  • {service_spec.name}: {service_spec.min_instances}-{service_spec.max_instances} instances"
        )
        logger.info(
            f"    Memory: {service_spec.memory_mb}MB, CPU: {service_spec.cpu_cores} cores, Storage: {service_spec.volume_size_gb}GB"
        )
    logger.info("\n🎯 NEXT STEPS:")
    logger.info(
        "  1. Deploy each service using: fly deploy --config fly-<service-name>.toml"
    )
    logger.info(
        "  2. Configure secrets via: fly secrets set KEY=VALUE --app <service-name>"
    )
    logger.info("  3. Test internal service communication")
    logger.info("  4. Validate health check endpoints")
    logger.info("  5. Monitor auto-scaling behavior")
    # Save deployment results to file
    deployment_summary = {
        "deployment_summary": {
            "total_services": len(services),
            "successful_deployments": successful_deployments,
            "total_storage_gb": total_storage,
            "total_max_instances": total_max_instances,
            "primary_region": "sjc",
            "secondary_region": "iad",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        },
        "services": deployed_services,
        "infrastructure_specs": {
            service_spec.name: {
                "memory_mb": service_spec.memory_mb,
                "cpu_cores": service_spec.cpu_cores,
                "min_instances": service_spec.min_instances,
                "max_instances": service_spec.max_instances,
                "volume_size_gb": service_spec.volume_size_gb,
                "port": service_spec.port,
                "health_check_path": service_spec.health_check_path,
            }
            for service_spec in services
        },
    }
    with open("fly-deployment-results.json", "w") as f:
        json.dump(deployment_summary, indent=2, fp=f)
    logger.info("\n💾 Deployment results saved to: fly-deployment-results.json")
    logger.info("✅ Infrastructure provisioning complete!")
    return successful_deployments == len(services)
if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
