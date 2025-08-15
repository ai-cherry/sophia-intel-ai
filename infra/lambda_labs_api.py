#!/usr/bin/env python3
"""
Lambda Labs API Integration for SOPHIA MVP
Direct API calls since Pulumi provider not available
"""
import os
import json
import time
import requests
from typing import Dict, List, Any, Optional

class LambdaLabsAPI:
    """Lambda Labs API client"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def list_instance_types(self) -> List[Dict[str, Any]]:
        """List available instance types"""
        response = requests.get(f"{self.base_url}/instance-types", headers=self.headers)
        response.raise_for_status()
        return response.json().get("data", [])
    
    def list_instances(self) -> List[Dict[str, Any]]:
        """List all instances"""
        response = requests.get(f"{self.base_url}/instances", headers=self.headers)
        response.raise_for_status()
        return response.json().get("data", [])
    
    def create_instance(self, 
                       instance_type: str,
                       region: str,
                       ssh_key_names: List[str],
                       name: str) -> Dict[str, Any]:
        """Create a new instance"""
        data = {
            "region_name": region,
            "instance_type_name": instance_type,
            "ssh_key_names": ssh_key_names,
            "name": name
        }
        
        response = requests.post(f"{self.base_url}/instance-operations/launch", 
                               headers=self.headers, json=data)
        response.raise_for_status()
        return response.json().get("data", {})
    
    def terminate_instance(self, instance_id: str) -> bool:
        """Terminate an instance"""
        response = requests.post(f"{self.base_url}/instance-operations/terminate",
                               headers=self.headers, 
                               json={"instance_ids": [instance_id]})
        return response.status_code == 200
    
    def list_ssh_keys(self) -> List[Dict[str, Any]]:
        """List SSH keys"""
        response = requests.get(f"{self.base_url}/ssh-keys", headers=self.headers)
        response.raise_for_status()
        return response.json().get("data", [])
    
    def add_ssh_key(self, name: str, public_key: str) -> Dict[str, Any]:
        """Add SSH key"""
        data = {
            "name": name,
            "public_key": public_key
        }
        
        response = requests.post(f"{self.base_url}/ssh-keys", 
                               headers=self.headers, json=data)
        response.raise_for_status()
        return response.json().get("data", {})
    
    def wait_for_instance_running(self, instance_id: str, timeout: int = 300) -> bool:
        """Wait for instance to be running"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            instances = self.list_instances()
            for instance in instances:
                if instance.get("id") == instance_id:
                    status = instance.get("status")
                    if status == "running":
                        return True
                    elif status in ["terminated", "error"]:
                        return False
            
            time.sleep(10)
        
        return False

def create_ssh_key_pair() -> tuple[str, str]:
    """Create SSH key pair"""
    import subprocess
    import tempfile
    
    with tempfile.TemporaryDirectory() as temp_dir:
        key_path = f"{temp_dir}/sophia_key"
        
        # Generate key pair
        subprocess.run([
            "ssh-keygen", "-t", "ed25519", "-f", key_path, "-N", "", "-C", "sophia-mvp"
        ], check=True)
        
        # Read keys
        with open(key_path, "r") as f:
            private_key = f.read()
        
        with open(f"{key_path}.pub", "r") as f:
            public_key = f.read().strip()
        
        return private_key, public_key

def provision_k3s_instance(api_key: str) -> Dict[str, Any]:
    """Provision K3s instance on Lambda Labs"""
    print("🚀 Provisioning K3s instance on Lambda Labs...")
    
    client = LambdaLabsAPI(api_key)
    
    # Generate SSH key pair
    print("🔑 Generating SSH key pair...")
    private_key, public_key = create_ssh_key_pair()
    
    # Add SSH key to Lambda Labs
    print("📤 Adding SSH key to Lambda Labs...")
    ssh_key_name = f"sophia-mvp-{int(time.time())}"
    ssh_key_result = client.add_ssh_key(ssh_key_name, public_key)
    
    # List available instance types
    print("📋 Checking available instance types...")
    instance_types = client.list_instance_types()
    
    # Find suitable instance type (prefer GPU for AI workloads)
    suitable_types = [
        "gpu_1x_a10", "gpu_1x_rtx6000", "gpu_1x_a6000", 
        "cpu_4x", "cpu_8x"
    ]
    
    available_type = None
    for instance_type in suitable_types:
        for available in instance_types:
            if available.get("name") == instance_type:
                regions = available.get("regions_with_capacity_available", [])
                if regions:
                    available_type = instance_type
                    region = regions[0].get("name")
                    break
        if available_type:
            break
    
    if not available_type:
        raise Exception("No suitable instance types available")
    
    print(f"🖥️  Creating instance: {available_type} in {region}")
    
    # Create instance
    instance_result = client.create_instance(
        instance_type=available_type,
        region=region,
        ssh_key_names=[ssh_key_name],
        name="sophia-mvp-k3s"
    )
    
    instance_id = instance_result.get("instance_ids", [None])[0]
    if not instance_id:
        raise Exception("Failed to create instance")
    
    print(f"⏳ Waiting for instance {instance_id} to be running...")
    if not client.wait_for_instance_running(instance_id):
        raise Exception("Instance failed to start")
    
    # Get instance details
    instances = client.list_instances()
    instance = None
    for inst in instances:
        if inst.get("id") == instance_id:
            instance = inst
            break
    
    if not instance:
        raise Exception("Could not find created instance")
    
    instance_ip = instance.get("ip")
    
    print(f"✅ Instance created successfully!")
    print(f"   Instance ID: {instance_id}")
    print(f"   IP Address: {instance_ip}")
    print(f"   SSH Key: {ssh_key_name}")
    
    return {
        "instance_id": instance_id,
        "instance_ip": instance_ip,
        "ssh_key_name": ssh_key_name,
        "private_key": private_key,
        "public_key": public_key
    }

if __name__ == "__main__":
    # Test the API
    api_key = os.getenv("LAMBDA_LABS_API_KEY")
    if not api_key:
        print("❌ LAMBDA_LABS_API_KEY environment variable not set")
        exit(1)
    
    try:
        result = provision_k3s_instance(api_key)
        print(f"🎉 Success: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)

