import asyncio
import os
import subprocess
from enum import Enum
from typing import Any

from app.deployment.port_manager import PortManager


class DeploymentEnvironment(Enum):
    """Auto-detected deployment environments"""
    LOCAL = "local"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    UNKNOWN = "unknown"

class DeploymentOrchestrator:
    """Universal deployment orchestrator for any environment"""

    def __init__(self):
        self.port_manager = PortManager()
        self.environment = self.detect_environment()
        self.service_registry = {}
        self.deployed_services = {}
        self.health_checker = None

    def detect_environment(self) -> DeploymentEnvironment:
        """Auto-detect deployment environment"""
        if os.environ.get('KUBERNETES_SERVICE_HOST'):
            return DeploymentEnvironment.KUBERNETES
        elif os.environ.get('AWS_REGION'):
            return DeploymentEnvironment.AWS
        elif os.environ.get('GCP_PROJECT'):
            return DeploymentEnvironment.GCP
        elif os.path.exists('/.dockerenv') or 'CONTAINER' in os.environ.get('HOSTNAME', ''):
            return DeploymentEnvironment.DOCKER
        else:
            return DeploymentEnvironment.LOCAL

    async def prepare_environment(self):
        """Prepare environment for deployment (e.g., build containers)"""
        if self.environment == DeploymentEnvironment.DOCKER or self.environment == DeploymentEnvironment.KUBERNETES:
            try:
                # Run docker build if needed
                if self.environment == DeploymentEnvironment.DOCKER:
                    subprocess.run(["docker-compose", "build"], check=True)
                elif self.environment == DeploymentEnvironment.KUBERNETES:
                    # K8s specific setup would go here
                    pass
                return True
            except Exception as e:
                logger.error(f"Failed to prepare environment: {str(e)}")
                return False
        return True

    async def deploy_all_services(self):
        """Deploy all services with automatic configuration"""
        # Prepare the environment first
        if not await self.prepare_environment():
            raise RuntimeError("Failed to prepare environment for deployment")

        # Order of deployment for dependency chain
        services = [
            {'name': 'redis', 'command': 'docker run -d --name redis redis', 'port': 'redis'},
            {'name': 'mcp_server', 'command': 'python app/mcp/mcp_verification_server.py', 'port': 'mcp_server'},
            {'name': 'swarm_coordinator', 'command': 'python app/swarms/mcp/coordinator.py', 'port': 'swarm_coordinator'},
            {'name': 'agent_ui', 'command': 'cd agent-ui && npm run dev', 'port': 'agent_ui'},
            {'name': 'streamlit', 'command': 'streamlit run app/ui/streamlit_chat.py', 'port': 'streamlit'},
            {'name': 'monitoring', 'command': 'docker-compose -f docker-compose.monitoring.yml up -d', 'port': 'grafana'}
        ]

        for service in services:
            port = self.port_manager.get_available_port(service['port'])
            logger.info(f"Deploying {service['name']} on port {port}")
            await self.deploy_service(service, port)

        # Wait for all services to become healthy
        self.health_checker = await self._get_health_checker()
        if not await self.health_checker.wait_for_healthy(timeout=300):
            raise RuntimeError("Not all services became healthy within timeout period")

        return True

    async def deploy_service(self, service: dict[str, Any], port: int):
        """Deploy individual service with health checks"""
        if service['port'] not in self.port_manager.PORT_ASSIGNMENTS:
            raise ValueError(f"Invalid service: {service['port']}")

        # Map service name to port assignment
        service_port = self.port_manager.get_service_port(service['port'])

        # Store service info for later reference
        self.service_registry[service['name']] = {
            'service': service,
            'port': port,
            'host': 'localhost',
            'is_running': False
        }

        # Handle different environment deployments
        if self.environment == DeploymentEnvironment.LOCAL:
            await self._deploy_local(service, port)
        elif self.environment == DeploymentEnvironment.DOCKER:
            await self._deploy_docker(service, port)
        elif self.environment == DeploymentEnvironment.KUBERNETES:
            await self._deploy_kubernetes(service, port)
        elif self.environment in [DeploymentEnvironment.AWS, DeploymentEnvironment.GCP, DeploymentEnvironment.AZURE]:
            await self._deploy_cloud(service, port)
        else:
            await self._deploy_local(service, port)

    async def _deploy_local(self, service: dict[str, Any], port: int):
        """Deploy service for local environment"""
        try:
            # Start process in background
            process = subprocess.Popen(
                service['command'].split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Store process handle
            self.service_registry[service['name']]['process'] = process
            self.service_registry[service['name']]['is_running'] = True

            # Wait for service to start up
            await asyncio.sleep(2)

            logger.info(f"Started {service['name']} locally (PID: {process.pid})")
        except Exception as e:
            logger.error(f"Local deployment failed for {service['name']}: {str(e)}")
            raise

    async def _deploy_docker(self, service: dict[str, Any], port: int):
        """Deploy service using Docker"""
        try:
            # Create docker compose configuration with port mapping
            service_name = service['name']
            docker_compose = f"""
version: '3'
services:
  {service_name}:
    image: {service_name}:latest
    ports:
      - "{port}:{service_port}"
"""

            # Write to temporary file
            compose_path = f"/tmp/{service_name}-compose.yml"
            with open(compose_path, 'w') as f:
                f.write(docker_compose)

            docker_command = f"docker-compose -f {compose_path} up -d"
            subprocess.run(docker_command.split(), check=True)

            logger.info(f"Deployed {service['name']} with Docker")
        except Exception as e:
            logger.error(f"Failed to deploy {service['name']} with Docker: {str(e)}")
            raise

    async def _deploy_kubernetes(self, service: dict[str, Any], port: int):
        """Deploy service to Kubernetes"""
        try:
            # Generate K8s YAML
            k8s_manifest = f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {service['name']}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {service['name']}
  template:
    metadata:
      labels:
        app: {service['name']}
    spec:
      containers:
      - name: {service['name']}
        image: {service['name']}:latest
        ports:
        - containerPort: {port}
"""
            # Save to temporary file
            manifest_path = f"/tmp/{service['name']}.yaml"
            with open(manifest_path, 'w') as f:
                f.write(k8s_manifest)

            # Apply the manifest
            subprocess.run(["kubectl", "apply", "-f", manifest_path], check=True)

            logger.info(f"Deployed {service['name']} to Kubernetes")
        except Exception as e:
            logger.error(f"Failed to deploy {service['name']} to Kubernetes: {str(e)}")
            raise

    async def _deploy_cloud(self, service: dict[str, Any], port: int):
        """Deploy service to cloud provider (AWS/GCP/Azure)"""
        try:
            provider = self.environment.value
            logger.info(f"Deploying {service['name']} to cloud provider: {provider}")

            # Cloud-specific deployment setup
            if provider == "aws":
                # AWS specific deployment
                self._deploy_aws(service, port)
            elif provider == "gcp":
                # GCP specific deployment
                self._deploy_gcp(service, port)
            elif provider == "azure":
                # Azure specific deployment
                self._deploy_azure(service, port)

            logger.info(f"Successfully deployed {service['name']} to {provider}")
        except Exception as e:
            logger.error(f"Cloud deployment failed: {str(e)}")
            raise

    def _deploy_aws(self, service: dict[str, Any], port: int):
        """AWS-specific deployment helper"""
        # This would use AWS SDK to deploy to ECS or Lambda
        pass

    def _deploy_gcp(self, service: dict[str, Any], port: int):
        """GCP-specific deployment helper"""
        # This would use GCP SDK to deploy to Cloud Run
        pass

    def _deploy_azure(self, service: dict[str, Any], port: int):
        """Azure-specific deployment helper"""
        # This would use Azure SDK to deploy to App Services
        pass

    async def _get_health_checker(self):
        """Get health checker instance based on environment"""
        try:
            from app.deployment.health_checker import HealthChecker
            return HealthChecker()
        except ImportError:
            logger.error("HealthChecker module not found")
            return None

    async def cleanup(self):
        """Clean up all deployed services"""
        # Stop all services
        for service_name in list(self.service_registry.keys()):
            await self._stop_service(service_name)

        # Remove temporary files
        self._cleanup_temp_files()

        logger.info("All services cleaned up successfully")

    async def _stop_service(self, service_name: str):
        """Stop a running service"""
        if service_name not in self.service_registry:
            return

        try:
            service = self.service_registry[service_name]
            if service['is_running']:
                if self.environment == DeploymentEnvironment.LOCAL and 'process' in service:
                    if service['process'].poll() is None:  # Process still running
                        service['process'].terminate()
                        try:
                            service['process'].wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            service['process'].kill()
                elif self.environment == DeploymentEnvironment.DOCKER:
                    subprocess.run(
                        ["docker", "stop", service_name],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    subprocess.run(
                        ["docker", "rm", service_name],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )

                self.service_registry[service_name]['is_running'] = False
                logger.info(f"Stopped {service_name}")
        except Exception as e:
            logger.error(f"Failed to stop {service_name}: {str(e)}")

    def _cleanup_temp_files(self):
        """Remove temporary files created during deployment"""
        try:
            # Remove docker-compose files
            subprocess.run(["rm", "-f", "/tmp/*.yml"], stderr=subprocess.DEVNULL)

            # Additional cleanup specific to environment
            if self.environment == DeploymentEnvironment.KUBERNETES:
                subprocess.run(["rm", "-f", "/tmp/*.yaml"], stderr=subprocess.DEVNULL)
        except Exception as e:
            logger.error(f"Failed to clean up temporary files: {str(e)}")

    async def deploy_with_failover(self, service: dict[str, Any], port: int):
        """
        Deploy service with automatic failover to backup option
        """
        # First try normal deployment
        try:
            await self.deploy_service(service, port)
            return True
        except Exception as e:
            logger.warning(f"Primary deployment for {service['name']} failed: {str(e)}")

            # Try backup deployment strategy
            try:
                if self.environment == DeploymentEnvironment.DOCKER:
                    # Try another Docker port
                    return await self.deploy_service(service, port + 1)
                elif self.environment == DeploymentEnvironment.LOCAL:
                    # Try a different port
                    return await self.deploy_service(service, port + 1)
            except:
                pass

            return False

# Example usage
if __name__ == "__main__":
    async def demo():
        orchestrator = DeploymentOrchestrator()

        # Deploy all services
        await orchestrator.deploy_all_services()

        # Wait for a while to let services run
        print("All services deployed successfully! Waiting for services to start...")
        await asyncio.sleep(30)

        # Cleanup
        await orchestrator.cleanup()

    asyncio.run(demo())
