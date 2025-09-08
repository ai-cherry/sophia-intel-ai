"""
Deployment Engine Module
========================

Handles build, packaging, and deployment of applications.
"""

import subprocess
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


class DeploymentTarget(Enum):
    """Deployment target environments"""

    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"


class BuildType(Enum):
    """Types of builds"""

    DEBUG = "debug"
    RELEASE = "release"
    MINIFIED = "minified"
    OPTIMIZED = "optimized"


class DeploymentStatus(Enum):
    """Deployment status"""

    PENDING = "pending"
    BUILDING = "building"
    TESTING = "testing"
    DEPLOYING = "deploying"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class BuildConfig:
    """Build configuration"""

    project_path: str
    build_type: BuildType
    language: str
    framework: Optional[str] = None
    output_dir: Optional[str] = None
    environment_vars: Dict[str, str] = None
    dependencies: List[str] = None


@dataclass
class DeploymentConfig:
    """Deployment configuration"""

    build_config: BuildConfig
    target: DeploymentTarget
    version: str
    replicas: int = 1
    health_check_url: Optional[str] = None
    rollback_on_failure: bool = True
    pre_deploy_scripts: List[str] = None
    post_deploy_scripts: List[str] = None


@dataclass
class DeploymentResult:
    """Deployment result"""

    status: DeploymentStatus
    target: DeploymentTarget
    version: str
    url: Optional[str] = None
    build_artifact: Optional[str] = None
    deployment_id: Optional[str] = None
    logs: List[str] = None
    error: Optional[str] = None


class DeploymentEngine:
    """
    Main deployment engine for Artemis.
    Handles building, packaging, and deploying applications.
    """

    def __init__(self):
        """Initialize the deployment engine"""
        self.builders = self._init_builders()
        self.deployers = self._init_deployers()
        self.active_deployments = {}
        self.deployment_history = []

    def _init_builders(self) -> Dict[str, Dict]:
        """Initialize builders for different languages"""
        return {
            "python": {
                "command": "python setup.py build",
                "package": "python setup.py sdist bdist_wheel",
                "dependencies": "pip install -r requirements.txt",
            },
            "javascript": {
                "command": "npm run build",
                "package": "npm pack",
                "dependencies": "npm install",
            },
            "typescript": {
                "command": "tsc && npm run build",
                "package": "npm pack",
                "dependencies": "npm install",
            },
            "go": {
                "command": "go build -o {output}",
                "package": "tar -czf {output}.tar.gz {output}",
                "dependencies": "go mod download",
            },
            "rust": {
                "command": "cargo build --release",
                "package": "cargo package",
                "dependencies": "cargo fetch",
            },
            "java": {
                "command": "mvn clean package",
                "package": "mvn package",
                "dependencies": "mvn dependency:resolve",
            },
        }

    def _init_deployers(self) -> Dict[DeploymentTarget, Dict]:
        """Initialize deployers for different targets"""
        return {
            DeploymentTarget.LOCAL: {
                "deploy": self._deploy_local,
                "verify": self._verify_local,
            },
            DeploymentTarget.DOCKER: {
                "deploy": self._deploy_docker,
                "verify": self._verify_docker,
            },
            DeploymentTarget.KUBERNETES: {
                "deploy": self._deploy_kubernetes,
                "verify": self._verify_kubernetes,
            },
            DeploymentTarget.AWS: {
                "deploy": self._deploy_aws,
                "verify": self._verify_aws,
            },
        }

    def build(self, config: BuildConfig) -> Tuple[bool, str]:
        """
        Build the application.

        Args:
            config: Build configuration

        Returns:
            Success status and build artifact path
        """
        # Create build directory
        build_dir = Path(config.output_dir or tempfile.mkdtemp())
        build_dir.mkdir(parents=True, exist_ok=True)

        # Install dependencies
        if config.dependencies:
            self._install_dependencies(config)

        # Get builder for language
        builder = self.builders.get(config.language, {})
        build_command = builder.get("command", "")

        if not build_command:
            return False, f"No builder available for {config.language}"

        # Execute build
        success, output = self._execute_command(
            build_command, cwd=config.project_path, env=config.environment_vars
        )

        if not success:
            return False, f"Build failed: {output}"

        # Package the build
        package_command = builder.get("package", "")
        if package_command:
            success, artifact = self._package_build(package_command, config, build_dir)
            if success:
                return True, artifact

        return True, str(build_dir)

    def deploy(self, config: DeploymentConfig) -> DeploymentResult:
        """
        Deploy the application.

        Args:
            config: Deployment configuration

        Returns:
            Deployment result
        """
        import uuid

        deployment_id = str(uuid.uuid4())

        # Record deployment start
        self.active_deployments[deployment_id] = {
            "config": config,
            "status": DeploymentStatus.PENDING,
            "start_time": self._get_timestamp(),
        }

        # Build the application
        self._update_deployment_status(deployment_id, DeploymentStatus.BUILDING)
        build_success, artifact = self.build(config.build_config)

        if not build_success:
            self._update_deployment_status(deployment_id, DeploymentStatus.FAILED)
            return DeploymentResult(
                status=DeploymentStatus.FAILED,
                target=config.target,
                version=config.version,
                error=f"Build failed: {artifact}",
            )

        # Run pre-deployment scripts
        if config.pre_deploy_scripts:
            for script in config.pre_deploy_scripts:
                self._execute_script(script)

        # Deploy to target
        self._update_deployment_status(deployment_id, DeploymentStatus.DEPLOYING)
        deployer = self.deployers.get(config.target, {})
        deploy_func = deployer.get("deploy")

        if not deploy_func:
            return DeploymentResult(
                status=DeploymentStatus.FAILED,
                target=config.target,
                version=config.version,
                error=f"No deployer available for {config.target}",
            )

        # Execute deployment
        try:
            result = deploy_func(config, artifact)

            # Verify deployment
            verify_func = deployer.get("verify")
            if verify_func:
                verified = verify_func(result)
                if not verified and config.rollback_on_failure:
                    self.rollback(deployment_id)
                    return DeploymentResult(
                        status=DeploymentStatus.ROLLED_BACK,
                        target=config.target,
                        version=config.version,
                        error="Deployment verification failed",
                    )

            # Run post-deployment scripts
            if config.post_deploy_scripts:
                for script in config.post_deploy_scripts:
                    self._execute_script(script)

            # Mark as completed
            self._update_deployment_status(deployment_id, DeploymentStatus.COMPLETED)

            return DeploymentResult(
                status=DeploymentStatus.COMPLETED,
                target=config.target,
                version=config.version,
                url=result.get("url"),
                build_artifact=artifact,
                deployment_id=deployment_id,
            )

        except Exception as e:
            self._update_deployment_status(deployment_id, DeploymentStatus.FAILED)
            if config.rollback_on_failure:
                self.rollback(deployment_id)

            return DeploymentResult(
                status=DeploymentStatus.FAILED,
                target=config.target,
                version=config.version,
                error=str(e),
            )

    def rollback(self, deployment_id: str) -> bool:
        """
        Rollback a deployment.

        Args:
            deployment_id: Deployment ID to rollback

        Returns:
            Success status
        """
        deployment = self.active_deployments.get(deployment_id)
        if not deployment:
            return False

        # Get previous successful deployment
        previous = self._get_previous_deployment(deployment["config"].target)
        if not previous:
            return False

        # Redeploy previous version
        previous_config = previous["config"]
        result = self.deploy(previous_config)

        if result.status == DeploymentStatus.COMPLETED:
            self._update_deployment_status(deployment_id, DeploymentStatus.ROLLED_BACK)
            return True

        return False

    def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """Get status of a deployment"""
        deployment = self.active_deployments.get(deployment_id, {})
        return {
            "id": deployment_id,
            "status": deployment.get("status", DeploymentStatus.PENDING),
            "target": (
                deployment.get("config", {}).target
                if deployment.get("config")
                else None
            ),
            "version": (
                deployment.get("config", {}).version
                if deployment.get("config")
                else None
            ),
            "start_time": deployment.get("start_time"),
            "end_time": deployment.get("end_time"),
        }

    def create_dockerfile(self, config: BuildConfig) -> str:
        """
        Generate a Dockerfile for the application.

        Args:
            config: Build configuration

        Returns:
            Dockerfile content
        """
        dockerfiles = {
            "python": """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
""",
            "javascript": """FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
CMD ["node", "index.js"]
""",
            "go": """FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o main .

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/main .
CMD ["./main"]
""",
            "rust": """FROM rust:1.70 AS builder
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src ./src
RUN cargo build --release

FROM debian:bullseye-slim
COPY --from=builder /app/target/release/app /usr/local/bin/app
CMD ["app"]
""",
        }

        return dockerfiles.get(
            config.language, "FROM ubuntu:latest\nWORKDIR /app\nCOPY . ."
        )

    def create_kubernetes_manifest(self, config: DeploymentConfig) -> str:
        """
        Generate Kubernetes manifest for the application.

        Args:
            config: Deployment configuration

        Returns:
            Kubernetes manifest YAML
        """
        manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": f"{config.build_config.project_path}-deployment",
                "labels": {
                    "app": config.build_config.project_path,
                    "version": config.version,
                },
            },
            "spec": {
                "replicas": config.replicas,
                "selector": {"matchLabels": {"app": config.build_config.project_path}},
                "template": {
                    "metadata": {
                        "labels": {
                            "app": config.build_config.project_path,
                            "version": config.version,
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": config.build_config.project_path,
                                "image": f"{config.build_config.project_path}:{config.version}",
                                "ports": [{"containerPort": 8080}],
                            }
                        ]
                    },
                },
            },
        }

        return yaml.dump(manifest, default_flow_style=False)

    def create_ci_cd_pipeline(self, config: BuildConfig) -> str:
        """
        Generate CI/CD pipeline configuration.

        Args:
            config: Build configuration

        Returns:
            Pipeline configuration (GitHub Actions example)
        """
        pipeline = f"""name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up {config.language}
      uses: actions/setup-{config.language}@v2

    - name: Install dependencies
      run: |
        {self.builders.get(config.language, {}).get('dependencies', 'echo "No dependencies"')}

    - name: Build
      run: |
        {self.builders.get(config.language, {}).get('command', 'echo "No build command"')}

    - name: Test
      run: |
        echo "Running tests..."

    - name: Deploy
      if: github.ref == 'refs/heads/main'
      run: |
        echo "Deploying to production..."
"""
        return pipeline

    # Helper methods
    def _install_dependencies(self, config: BuildConfig) -> bool:
        """Install project dependencies"""
        builder = self.builders.get(config.language, {})
        deps_command = builder.get("dependencies", "")

        if deps_command:
            success, _ = self._execute_command(deps_command, cwd=config.project_path)
            return success
        return True

    def _execute_command(
        self, command: str, cwd: str = None, env: Dict[str, str] = None
    ) -> Tuple[bool, str]:
        """Execute shell command"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    def _execute_script(self, script: str) -> bool:
        """Execute a deployment script"""
        success, _ = self._execute_command(script)
        return success

    def _package_build(
        self, command: str, config: BuildConfig, build_dir: Path
    ) -> Tuple[bool, str]:
        """Package the build artifact"""
        success, output = self._execute_command(
            command.format(output=str(build_dir / "app")), cwd=config.project_path
        )

        if success:
            # Find the created package
            for file in build_dir.iterdir():
                if file.suffix in [".tar", ".gz", ".zip", ".whl"]:
                    return True, str(file)

        return success, str(build_dir)

    def _update_deployment_status(
        self, deployment_id: str, status: DeploymentStatus
    ) -> None:
        """Update deployment status"""
        if deployment_id in self.active_deployments:
            self.active_deployments[deployment_id]["status"] = status
            if status in [
                DeploymentStatus.COMPLETED,
                DeploymentStatus.FAILED,
                DeploymentStatus.ROLLED_BACK,
            ]:
                self.active_deployments[deployment_id][
                    "end_time"
                ] = self._get_timestamp()
                # Move to history
                self.deployment_history.append(self.active_deployments[deployment_id])

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime

        return datetime.utcnow().isoformat()

    def _get_previous_deployment(self, target: DeploymentTarget) -> Optional[Dict]:
        """Get previous successful deployment for target"""
        for deployment in reversed(self.deployment_history):
            if (
                deployment.get("config", {}).target == target
                and deployment.get("status") == DeploymentStatus.COMPLETED
            ):
                return deployment
        return None

    # Deployment target implementations
    def _deploy_local(self, config: DeploymentConfig, artifact: str) -> Dict[str, Any]:
        """Deploy to local environment"""
        # Start local server
        port = 8080
        command = f"python -m http.server {port}"

        subprocess.Popen(command, shell=True, cwd=artifact)

        return {"url": f"http://localhost:{port}", "type": "local"}

    def _verify_local(self, result: Dict[str, Any]) -> bool:
        """Verify local deployment"""
        import requests

        try:
            response = requests.get(result["url"], timeout=5)
            return response.status_code == 200
        except:
            return False

    def _deploy_docker(self, config: DeploymentConfig, artifact: str) -> Dict[str, Any]:
        """Deploy using Docker"""
        # Build Docker image
        dockerfile = self.create_dockerfile(config.build_config)
        dockerfile_path = Path(artifact) / "Dockerfile"

        with open(dockerfile_path, "w") as f:
            f.write(dockerfile)

        # Build image
        image_name = f"{config.build_config.project_path}:{config.version}"
        build_command = f"docker build -t {image_name} {artifact}"
        success, _ = self._execute_command(build_command)

        if not success:
            raise Exception("Docker build failed")

        # Run container
        run_command = f"docker run -d -p 8080:8080 --name {config.build_config.project_path} {image_name}"
        success, output = self._execute_command(run_command)

        if not success:
            raise Exception("Docker run failed")

        return {
            "url": "http://localhost:8080",
            "type": "docker",
            "container_id": output.strip(),
        }

    def _verify_docker(self, result: Dict[str, Any]) -> bool:
        """Verify Docker deployment"""
        # Check if container is running
        check_command = f"docker ps -q -f id={result.get('container_id', '')}"
        success, output = self._execute_command(check_command)
        return success and output.strip() != ""

    def _deploy_kubernetes(
        self, config: DeploymentConfig, artifact: str
    ) -> Dict[str, Any]:
        """Deploy to Kubernetes"""
        # Generate manifest
        manifest_yaml = self.create_kubernetes_manifest(config)
        manifest_path = Path(artifact) / "k8s-deployment.yaml"

        with open(manifest_path, "w") as f:
            f.write(manifest_yaml)

        # Apply manifest
        apply_command = f"kubectl apply -f {manifest_path}"
        success, output = self._execute_command(apply_command)

        if not success:
            raise Exception(f"Kubernetes deployment failed: {output}")

        # Get service URL
        service_command = f"kubectl get service {config.build_config.project_path} -o jsonpath='{{.status.loadBalancer.ingress[0].ip}}'"
        success, ip = self._execute_command(service_command)

        return {
            "url": f"http://{ip.strip()}",
            "type": "kubernetes",
            "deployment": config.build_config.project_path,
        }

    def _verify_kubernetes(self, result: Dict[str, Any]) -> bool:
        """Verify Kubernetes deployment"""
        # Check deployment status
        check_command = (
            f"kubectl rollout status deployment/{result.get('deployment', '')}"
        )
        success, _ = self._execute_command(check_command)
        return success

    def _deploy_aws(self, config: DeploymentConfig, artifact: str) -> Dict[str, Any]:
        """Deploy to AWS (placeholder)"""
        # This would integrate with AWS services like ECS, Lambda, or EC2
        return {
            "url": f"https://{config.build_config.project_path}.amazonaws.com",
            "type": "aws",
        }

    def _verify_aws(self, result: Dict[str, Any]) -> bool:
        """Verify AWS deployment (placeholder)"""
        # This would check AWS deployment status
        return True
