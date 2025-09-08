# Auto-added by pre-commit hook
import os
import sys

try:
    sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    from core.environment_enforcer import enforce_environment
    enforce_environment()
except ImportError:

#!/usr/bin/env python3
"""
Lambda Labs GPU Cluster Management
Secure and scalable GPU compute infrastructure for Sophia AI
"""

import json
import os
import time
from typing import Any, Dict, List, Optional

import pulumi
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

class LambdaLabsManager:
    """Manages Lambda Labs GPU clusters with security and cost optimization"""

    def __init__(self, project_name: str, environment: str, security_group_id: str):
        self.project_name = project_name
        self.environment = environment
        self.security_group_id = security_group_id

        # Lambda Labs configuration from ESC using secure secret retrieval
        # Get secrets from AWS Secrets Manager or Vault
        lambda_credentials = self._get_lambda_credentials()
        self.api_key = lambda_credentials["api_key"]
        self.base_url = lambda_credentials.get(
            "base_url", "https://cloud.lambda.ai/api/v1")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"SophiaAI/{environment}",
        }

    def _get_lambda_credentials(self) -> dict:
        """
        Securely retrieve Lambda Labs API credentials from AWS Secrets Manager or HashiCorp Vault

        Returns:
            Dictionary with API credentials
        """
        import json
        import logging
        import os

        # Set up logging
        logger = logging.getLogger(__name__)

        # Check if we should use Vault
        use_vault = os.getenv("USE_VAULT", "false").lower() == "true"

        if use_vault:
            try:
                import hvac

                # Initialize Vault client
                vault_addr = os.getenv(
                    "VAULT_ADDR", "https://vault.sophia-ai.internal:8200")
                vault_client = hvac.Client(url=vault_addr)

                # Authenticate using AWS authentication
                vault_client.auth.aws.iam_login(
                    role=f"sophia-ai-{self.environment}",
                )

                # Get secret from Vault
                secret_path = f"sophia-ai/{self.environment}/lambda-labs"
                secret_data = vault_client.secrets.kv.v2.read_secret_version(
                    path=secret_path
                )

                if secret_data and "data" in secret_data and "data" in secret_data["data"]:
                    credentials = secret_data["data"]["data"]
                    return {
                        "api_key": credentials["api_key"],
                        "base_url": credentials.get("base_url", "https://cloud.lambda.ai/api/v1")
                    }

                # Fallback to AWS Secrets Manager if Vault fails
                print("Vault lookup failed, falling back to AWS Secrets Manager")

            except Exception as e:
                print(f"Error using Vault for secret lookup: {str(e)}")
                print("Falling back to AWS Secrets Manager")

        try:
            # Use AWS Secrets Manager
            session = boto3.session.Session()
            client = session.client(service_name="secretsmanager")

            # Get secret from AWS Secrets Manager
            secret_id = f"/{self.project_name}/{self.environment}/lambda-labs"
            response = client.get_secret_value(SecretId=secret_id)

            if "SecretString" in response:
                secret = json.loads(response["SecretString"])
                return {
                    "api_key": secret["api_key"],
                    "base_url": secret.get("base_url", "https://cloud.lambda.ai/api/v1")
                }

        except Exception as e:
            print(f"Error retrieving Lambda Labs credentials: {str(e)}")

            # In case of emergency, use an environment variable (not recommended)
            env_api_key = os.getenv("LAMBDA_API_KEY", "")
            if env_api_key:
                print("WARNING: Using environment variable for Lambda Labs API key")
                return {
                    "api_key": env_api_key,
                    "base_url": "https://cloud.lambda.ai/api/v1"
                }

            # If all else fails, fail safely
            raise Exception(f"Failed to retrieve Lambda Labs credentials: {str(e)}")

        # Cluster configuration
        self.cluster_config = {
            "name": f"{project_name}-{environment}-cluster",
            "instance_type": "gpu_8x_h100_sxm5",
            "min_instances": 1,
            "max_instances": 5,
            "reservation_type": "1_month",
            "auto_scaling_enabled": True,
            "cost_optimization_enabled": True,
        }

    def create_production_cluster(self) -> dict[str, Any]:
        """Create production-ready GPU cluster with all optimizations"""

        pulumi.log.info(
            f"🚀 Creating Lambda Labs production cluster: {self.cluster_config['name']}"
        )

        try:
            # 1. Generate secure SSH key pair
            ssh_keys = self._generate_ssh_keys()

            # 2. Create cluster configuration
            cluster_request = {
                "name": self.cluster_config["name"],
                "instance_type": self.cluster_config["instance_type"],
                "num_instances": 2,  # Start with 2 instances
                "region": "lambda-labs-us-east",
                "reservation": {
                    "type": self.cluster_config["reservation_type"],
                    "auto_renew": True,
                    "payment_method": "credit_card",
                },
                "auto_scaling": {
                    "enabled": self.cluster_config["auto_scaling_enabled"],
                    "min_instances": self.cluster_config["min_instances"],
                    "max_instances": self.cluster_config["max_instances"],
                    "scale_up_threshold": 80,  # CPU/GPU utilization %
                    "scale_down_threshold": 20,
                    "cooldown_period": 300,  # 5 minutes
                    "metrics": [
                        "cpu_utilization",
                        "gpu_utilization",
                        "memory_utilization",
                    ],
                },
                "networking": {
                    "vpc_id": "default",  # Will be updated with actual VPC
                    "security_groups": [self.security_group_id],
                    "public_ip": True,
                    "firewall_rules": [
                        {
                            "port": 22,
                            "protocol": "tcp",
                            "source": "${BIND_IP}/0",  # Will be restricted
                            "description": "SSH access",
                        },
                        {
                            "port": 8000,
                            "protocol": "tcp",
                            "source": "${BIND_IP}/0",
                            "description": "AI service port",
                        },
                        {
                            "port": 443,
                            "protocol": "tcp",
                            "source": "${BIND_IP}/0",
                            "description": "HTTPS",
                        },
                    ],
                },
                "ssh_keys": [ssh_keys["public_key_name"]],
                "startup_script": self._generate_startup_script(),
                "monitoring": {
                    "enabled": True,
                    "metrics": ["cpu", "gpu", "memory", "network", "disk"],
                    "alerts": {
                        "high_utilization": 90,
                        "low_utilization": 10,
                        "cost_threshold": 1000,  # $1000/month
                        "downtime_alert": True,
                    },
                    "log_retention_days": 30,
                },
                "cost_optimization": {
                    "auto_shutdown": {
                        "enabled": self.cluster_config["cost_optimization_enabled"],
                        "idle_timeout": 3600,  # 1 hour
                        "schedule": {
                            "weekdays": "06:00-22:00",  # 6 AM to 10 PM
                            "weekends": "08:00-20:00",  # 8 AM to 8 PM
                        },
                    },
                    "spot_instances": {
                        "enabled": False,  # Disabled for production stability
                        "max_spot_percentage": 50,
                    },
                    "reserved_pricing": {
                        "enabled": True,
                        "commitment_period": "1_month",
                    },
                },
                "backup": {
                    "enabled": True,
                    "schedule": "daily",
                    "retention_days": 7,
                    "backup_type": "snapshot",
                },
                "tags": {
                    "Project": self.project_name,
                    "Environment": self.environment,
                    "ManagedBy": "Pulumi",
                    "Owner": "SophiaAI",
                    "CostCenter": "AI-Compute",
                    "AutoShutdown": "enabled",
                },
            }

            # 3. Create the cluster
            cluster_response = self._create_cluster_request(cluster_request)

            # 4. Wait for cluster to be ready
            cluster_id = cluster_response.get("cluster_id")
            if cluster_id:
                cluster_status = self._wait_for_cluster_ready(cluster_id)

                # 5. Configure cluster post-creation
                self._configure_cluster_post_creation(cluster_id)

                return {
                    "cluster_id": cluster_id,
                    "cluster_name": self.cluster_config["name"],
                    "status": cluster_status,
                    "instance_type": self.cluster_config["instance_type"],
                    "num_instances": cluster_response.get("num_instances", 2),
                    "ssh_key_name": ssh_keys["public_key_name"],
                    "estimated_monthly_cost": self._calculate_estimated_cost(
                        cluster_response
                    ),
                    "endpoints": {
                        "ssh": f"ssh -i ~/.ssh/{ssh_keys['private_key_name']} user@{cluster_response.get('public_ip')}",
                        "api": f"https://{cluster_response.get('public_ip')}:8000",
                        "monitoring": f"https://{cluster_response.get('public_ip')}:3000",
                    },
                    "created_at": time.time(),
                    "configuration": cluster_request,
                }
            else:
                raise Exception("Failed to create Lambda Labs cluster")

        except Exception as e:
            pulumi.log.error(f"❌ Failed to create Lambda Labs cluster: {str(e)}")
            raise e

    def _generate_ssh_keys(self) -> dict[str, str]:
        """Generate secure SSH key pair for cluster access"""

        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=4096, backend=default_backend()
        )

        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        # Get public key
        public_key = private_key.public_key()
        public_ssh = public_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH,
        )

        key_name = f"{self.project_name}-{self.environment}-key"

        return {
            "private_key": private_pem.decode(),
            "public_key": public_ssh.decode(),
            "private_key_name": f"{key_name}",
            "public_key_name": f"{key_name}.pub",
        }

    def _generate_startup_script(self) -> str:
        """Generate startup script for cluster instances"""

        return f"""#!/bin/bash
# Sophia AI Lambda Labs Startup Script
set -e

# Update system
apt-get update -y
apt-get upgrade -y

# Install essential packages
apt-get install -y curl wget git htop nvidia-smi docker.io docker-compose

# Configure Docker
systemctl start docker
systemctl enable docker

# Install NVIDIA Docker runtime
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | tee /etc/apt/sources.list.d/nvidia-docker.list
apt-get update -y
apt-get install -y nvidia-docker2
systemctl restart docker

# Install Python and AI libraries
apt-get install -y python3 python3-pip python3-venv
pip3 install --upgrade pip

# Install AI/ML packages
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip3 install transformers accelerate bitsandbytes
pip3 install qdrant-client redis sentence-transformers
pip3 install fastapi uvicorn requests aiohttp
pip3 install pulumi boto3 psycopg2-binary

# Create application directory
mkdir -p /opt/sophia-ai
chown sophia:sophia /opt/sophia-ai

# Install monitoring tools
pip3 install prometheus-client grafana-api

# Configure system limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Configure GPU monitoring
cat > /etc/systemd/system/gpu-monitor.service << EOF
[Unit]
Description=GPU Monitoring Service
After=network.target

[Service]
Type=simple

WorkingDirectory=/opt/sophia-ai
ExecStart=/usr/bin/python3 /opt/sophia-ai/gpu_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create GPU monitoring script
cat > /opt/sophia-ai/gpu_monitor.py << 'PYTHON_EOF'
import time
import subprocess
import json
import requests
import os

def get_gpu_stats():
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu', '--format=csv,noheader,nounits'],
                              capture_output=True, text=True)
        lines = result.stdout.strip().split('\\n')
        stats = []
        for line in lines:
            parts = line.split(', ')
            stats.append({{
                'gpu_utilization': float(parts[0]),
                'memory_used': float(parts[1]),
                'memory_total': float(parts[2]),
                'temperature': float(parts[3])
            }})
        return stats
    except Exception as e:
        print(f"Error getting GPU stats: {{e}}")
        return []

def send_metrics(stats):
    # Send metrics to monitoring system
    try:
        # This would send to CloudWatch or Prometheus
        print(f"GPU Stats: {{json.dumps(stats, indent=2)}}")
    except Exception as e:
        print(f"Error sending metrics: {{e}}")

if __name__ == "__main__":
    while True:
        stats = get_gpu_stats()
        if stats:
            send_metrics(stats)
        time.sleep(60)  # Send metrics every minute
PYTHON_EOF

chown sophia:sophia /opt/sophia-ai/gpu_monitor.py
chmod +x /opt/sophia-ai/gpu_monitor.py

# Enable GPU monitoring service
systemctl daemon-reload
systemctl enable gpu-monitor
systemctl start gpu-monitor

# Configure auto-shutdown based on idle time
cat > /opt/sophia-ai/auto_shutdown.py << 'PYTHON_EOF'
import time
import subprocess
import os

IDLE_THRESHOLD = 3600  # 1 hour in seconds
CHECK_INTERVAL = 300   # 5 minutes

def get_system_load():
    try:
        with open('/proc/loadavg', 'r') as f:
            load = float(f.read().split()[0])
        return load
    except Exception:return 1.0  # Default to active if can't read

def get_gpu_utilization():
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'],
                              capture_output=True, text=True)
        utilizations = [float(line.strip()) for line in result.stdout.strip().split('\\n')]
        return max(utilizations) if utilizations else 0
    except Exception:return 100  # Default to active if can't read

def should_shutdown():
    load = get_system_load()
    gpu_util = get_gpu_utilization()

    # Consider idle if CPU load < 0.1 and GPU utilization < 5%
    return load < 0.1 and gpu_util < 5

if __name__ == "__main__":
    idle_start = None

    while True:
        if should_shutdown():
            if idle_start is None:
                idle_start = time.time()
                print(f"System appears idle, starting idle timer")
            else:
                idle_duration = time.time() - idle_start
                print(f"System idle for {{idle_duration:.0f}} seconds")

                if idle_duration >= IDLE_THRESHOLD:
                    print("Idle threshold reached, shutting down...")
                    subprocess.run(['sudo', 'shutdown', '-h', 'now'])
                    break
        else:
            if idle_start is not None:
                print("System active again, resetting idle timer")
                idle_start = None

        time.sleep(CHECK_INTERVAL)
PYTHON_EOF

chown sophia:sophia /opt/sophia-ai/auto_shutdown.py
chmod +x /opt/sophia-ai/auto_shutdown.py

# Create auto-shutdown service (only if cost optimization is enabled)
if [ "{self.cluster_config['cost_optimization_enabled']}" = "True" ]; then
    cat > /etc/systemd/system/auto-shutdown.service << EOF
[Unit]
Description=Auto Shutdown Service
After=network.target

[Service]
Type=simple

WorkingDirectory=/opt/sophia-ai
ExecStart=/usr/bin/python3 /opt/sophia-ai/auto_shutdown.py
Restart=no

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable auto-shutdown
    systemctl start auto-shutdown
fi

# Log startup completion
echo "$(date): Sophia AI Lambda Labs startup script completed" >> /var/log/sophia-ai-startup.log

# Signal completion
touch /tmp/startup-complete
"""

    def _create_cluster_request(self, cluster_config: dict[str, Any]) -> dict[str, Any]:
        """Make API request to create cluster"""

        try:
            response = requests.post(
                f"{self.base_url}/instances",
                headers=self.headers,
                json=cluster_config,
                timeout=60,
            )

            if response.status_code in [200, 201]:
                return response.json()
            else:
                error_msg = (
                    f"Lambda Labs API error: {response.status_code} - {response.text}"
                )
                pulumi.log.error(error_msg)
                raise Exception(error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to connect to Lambda Labs API: {str(e)}"
            pulumi.log.error(error_msg)
            raise Exception(error_msg)

    def _wait_for_cluster_ready(self, cluster_id: str, timeout: int = 1800) -> str:
        """Wait for cluster to be ready (max 30 minutes)"""

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                status = self.get_cluster_status(cluster_id)

                if status["status"] == "running":
                    pulumi.log.info(f"✅ Cluster {cluster_id} is ready")
                    return "running"
                elif status["status"] == "failed":
                    raise Exception(f"Cluster {cluster_id} failed to start")
                else:
                    pulumi.log.info(
                        f"⏳ Cluster {cluster_id} status: {status['status']}"
                    )
                    time.sleep(30)  # Check every 30 seconds

            except Exception as e:
                pulumi.log.warn(f"Error checking cluster status: {str(e)}")
                time.sleep(30)

        raise Exception(
            f"Cluster {cluster_id} did not become ready within {timeout} seconds"
        )

    def _configure_cluster_post_creation(self, cluster_id: str):
        """Configure cluster after creation"""

        # Additional configuration that needs to be done after cluster is running
        pulumi.log.info(f"🔧 Configuring cluster {cluster_id} post-creation")

        # This would include:
        # - Setting up monitoring agents
        # - Configuring log forwarding
        # - Installing additional software
        # - Setting up backup schedules


    def _calculate_estimated_cost(self, cluster_response: dict[str, Any]) -> float:
        """Calculate estimated monthly cost"""

        # H100 pricing: $2.49/hour for on-demand, ~$1.90/hour for reserved
        hourly_rate = 1.90 if self.cluster_config.get("reservation_type") else 2.49
        num_instances = cluster_response.get("num_instances", 2)

        # Assume 70% utilization with auto-shutdown
        utilization_factor = (
            0.7 if self.cluster_config["cost_optimization_enabled"] else 1.0
        )

        monthly_cost = hourly_rate * num_instances * 24 * 30 * utilization_factor

        return round(monthly_cost, 2)

    def get_cluster_status(self, cluster_id: str) -> dict[str, Any]:
        """Get current cluster status"""

        try:
            response = requests.get(
                f"{self.base_url}/instances/{cluster_id}",
                headers=self.headers,
                timeout=30,
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to get cluster status: {response.status_code}")

        except Exception as e:
            pulumi.log.error(f"Error getting cluster status: {str(e)}")
            return {"status": "unknown", "error": str(e)}

    def scale_cluster(self, cluster_id: str, target_instances: int) -> dict[str, Any]:
        """Scale cluster to target number of instances"""

        try:
            scale_request = {
                "cluster_id": cluster_id,
                "target_instances": target_instances,
            }

            response = requests.post(
                f"{self.base_url}/instances/{cluster_id}/scale",
                headers=self.headers,
                json=scale_request,
                timeout=60,
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to scale cluster: {response.status_code}")

        except Exception as e:
            pulumi.log.error(f"Error scaling cluster: {str(e)}")
            return {"status": "error", "error": str(e)}

    def terminate_cluster(self, cluster_id: str) -> dict[str, Any]:
        """Terminate cluster (use with caution)"""

        try:
            response = requests.delete(
                f"{self.base_url}/instances/{cluster_id}",
                headers=self.headers,
                timeout=60,
            )

            if response.status_code == 200:
                return {"status": "terminated", "cluster_id": cluster_id}
            else:
                raise Exception(f"Failed to terminate cluster: {response.status_code}")

        except Exception as e:
            pulumi.log.error(f"Error terminating cluster: {str(e)}")
            return {"status": "error", "error": str(e)}
