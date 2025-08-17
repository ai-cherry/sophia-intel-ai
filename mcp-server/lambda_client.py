"""
Lambda Labs API client for SOPHIA Intel GH200 server management
"""
import os
import requests
from typing import Dict, Any, Optional

class LambdaLabsClient:
    def __init__(self):
        self.api_key = os.getenv("LAMBDA_API_KEY")
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    def get_instances(self) -> Dict[str, Any]:
        """Get all Lambda Labs instances"""
        resp = requests.get(f"{self.base_url}/instances", headers=self.headers)
        resp.raise_for_status()
        return resp.json()
    
    def get_instance(self, instance_id: str) -> Dict[str, Any]:
        """Get specific instance details"""
        resp = requests.get(f"{self.base_url}/instances/{instance_id}", headers=self.headers)
        resp.raise_for_status()
        return resp.json()
    
    def rename_instance(self, instance_id: str, new_name: str) -> Dict[str, Any]:
        """Rename a Lambda Labs instance"""
        payload = {"name": new_name}
        resp = requests.put(f"{self.base_url}/instances/{instance_id}", 
                           json=payload, headers=self.headers)
        resp.raise_for_status()
        return resp.json()
    
    def get_instance_status(self, instance_id: str) -> str:
        """Get instance status"""
        instance = self.get_instance(instance_id)
        return instance.get("data", {}).get("status", "unknown")

# Server configurations
SERVERS = {
    "primary": {
        "id": "07c099ae5ceb48ffaccd5c91b0560c0e",
        "ip": "192.222.51.223",
        "name": "sophia-gh200-primary-us-east-3",
        "role": "real-time inference"
    },
    "secondary": {
        "id": "9095c29b3292440fb81136810b0785a3", 
        "ip": "192.222.50.242",
        "name": "sophia-gh200-secondary-us-east-3",
        "role": "batch/fine-tuning"
    }
}
