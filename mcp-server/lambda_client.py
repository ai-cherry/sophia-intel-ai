"""
Lambda Labs API client for SOPHIA Intel GH200 server management
"""
import os
import json
import logging
import requests
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LambdaLabsClient:
    def __init__(self):
        self.api_key = os.getenv("LAMBDA_API_KEY")
        if not self.api_key:
            raise ValueError("LAMBDA_API_KEY environment variable is required")
        
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    def get_instances(self) -> Dict[str, Any]:
        """Get all Lambda Labs instances"""
        try:
            resp = requests.get(f"{self.base_url}/instances", headers=self.headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get instances: {e}")
            raise
    
    def get_instance(self, instance_id: str) -> Dict[str, Any]:
        """Get specific instance details"""
        try:
            resp = requests.get(f"{self.base_url}/instances/{instance_id}", headers=self.headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get instance {instance_id}: {e}")
            raise
    
    def start_instance(self, instance_id: str) -> Dict[str, Any]:
        """Start a Lambda Labs instance"""
        try:
            resp = requests.post(f"{self.base_url}/instances/{instance_id}/start", 
                               headers=self.headers, timeout=30)
            resp.raise_for_status()
            logger.info(f"Started instance {instance_id}")
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"Failed to start instance {instance_id}: {e}")
            raise
    
    def stop_instance(self, instance_id: str) -> Dict[str, Any]:
        """Stop a Lambda Labs instance"""
        try:
            resp = requests.post(f"{self.base_url}/instances/{instance_id}/stop", 
                               headers=self.headers, timeout=30)
            resp.raise_for_status()
            logger.info(f"Stopped instance {instance_id}")
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"Failed to stop instance {instance_id}: {e}")
            raise
    
    def restart_instance(self, instance_id: str) -> Dict[str, Any]:
        """Restart a Lambda Labs instance"""
        try:
            resp = requests.post(f"{self.base_url}/instances/{instance_id}/restart", 
                               headers=self.headers, timeout=30)
            resp.raise_for_status()
            logger.info(f"Restarted instance {instance_id}")
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"Failed to restart instance {instance_id}: {e}")
            raise
    
    def rename_instance(self, instance_id: str, new_name: str) -> Dict[str, Any]:
        """Rename a Lambda Labs instance"""
        try:
            payload = {"name": new_name}
            resp = requests.put(f"{self.base_url}/instances/{instance_id}", 
                               json=payload, headers=self.headers, timeout=10)
            resp.raise_for_status()
            logger.info(f"Renamed instance {instance_id} to {new_name}")
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"Failed to rename instance {instance_id}: {e}")
            raise
    
    def get_instance_status(self, instance_id: str) -> str:
        """Get instance status"""
        try:
            instance = self.get_instance(instance_id)
            return instance.get("data", {}).get("status", "unknown")
        except Exception as e:
            logger.error(f"Failed to get status for instance {instance_id}: {e}")
            return "error"
    
    def get_instance_stats(self, instance_id: str) -> Dict[str, Any]:
        """Get instance statistics (GPU utilization, etc.)"""
        try:
            # Note: Lambda Labs API doesn't provide real-time stats
            # This would need to be implemented via SSH or monitoring agent
            instance = self.get_instance(instance_id)
            data = instance.get("data", {})
            
            return {
                "instance_id": instance_id,
                "status": data.get("status", "unknown"),
                "instance_type": data.get("instance_type", {}).get("name", "unknown"),
                "region": data.get("region", {}).get("name", "unknown"),
                "ip": data.get("ip", "unknown"),
                "hostname": data.get("hostname", "unknown"),
                "uptime": "N/A",  # Would need SSH access to get real uptime
                "gpu_utilization": "N/A",  # Would need monitoring agent
                "memory_usage": "N/A"  # Would need monitoring agent
            }
        except Exception as e:
            logger.error(f"Failed to get stats for instance {instance_id}: {e}")
            return {"error": str(e)}

def get_server_config() -> Dict[str, Any]:
    """Load server configuration from environment variable or use defaults"""
    servers_json = os.getenv("LAMBDA_SERVERS_JSON")
    
    if servers_json:
        try:
            return json.loads(servers_json)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid LAMBDA_SERVERS_JSON format: {e}")
            # Fall back to defaults
    
    # Default configuration for development
    return {
        "primary": {
            "id": "07c099ae5ceb48ffaccd5c91b0560c0e",
            "ip": "192.222.51.223",
            "name": "sophia-gh200-primary-us-east-3",
            "role": "real-time inference",
            "inference_url": "http://192.222.51.223:8000"
        },
        "secondary": {
            "id": "9095c29b3292440fb81136810b0785a3", 
            "ip": "192.222.50.242",
            "name": "sophia-gh200-secondary-us-east-3",
            "role": "batch/fine-tuning",
            "inference_url": "http://192.222.50.242:8000"
        }
    }

# Load server configuration at module level
SERVERS = get_server_config()
