#!/usr/bin/env python3
"""
SOPHIA Intel Production Deployment - Go-Live Gauntlet Phase 1
CPU-optimized Lambda Labs cluster with K3s, Kong Ingress, and SSL
"""

import os
import json
import time
import requests
from typing import Dict, List, Optional

class LambdaLabsDeployer:
    def __init__(self):
        self.api_key = os.environ.get('LAMBDA_CLOUD_API_KEY')
        if not self.api_key:
            raise ValueError("LAMBDA_CLOUD_API_KEY environment variable required")
        
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        self.headers = {"Content-Type": "application/json"}
        
        # Target CPU instance configuration
        self.target_instances = [
            {"name": "sophia-cpu-control-01", "role": "control"},
            {"name": "sophia-cpu-worker-01", "role": "worker"},
            {"name": "sophia-cpu-worker-02", "role": "worker"}
        ]
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make authenticated request to Lambda Labs API"""
        url = f"{self.base_url}/{endpoint}"
        
        if method.upper() == "GET":
            response = requests.get(url, auth=(self.api_key, ""), headers=self.headers)
        elif method.upper() == "POST":
            response = requests.post(url, auth=(self.api_key, ""), 
                                   headers=self.headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        if response.status_code not in [200, 201]:
            print(f"API Error: {response.status_code} - {response.text}")
            return {}
        
        return response.json()
    
    def get_available_instance_types(self) -> List[Dict]:
        """Get all available instance types"""
        result = self.make_request("GET", "instance-types")
        data = result.get("data", {})
        
        # Lambda Labs API returns data as dict of dicts, not list
        if isinstance(data, dict):
            return [info["instance_type"] for info in data.values()]
        return []
    
    def find_cpu_instance_type(self) -> Optional[str]:
        """Find the best CPU instance type available"""
        instance_types = self.get_available_instance_types()
        
        # Look for CPU instances (Lambda Labs might not have cpu.c2-2 specifically)
        cpu_types = []
        for instance_type in instance_types:
            name = instance_type.get("name", "").lower()
            desc = instance_type.get("description", "").lower()
            
            # Look for CPU instances or small GPU instances as fallback
            if "cpu" in name or "cpu" in desc:
                cpu_types.append(instance_type)
            elif any(gpu in name for gpu in ["rtx4000", "rtx3080", "rtx3090"]):
                # Smaller GPU instances as fallback
                cpu_types.append(instance_type)
        
        if cpu_types:
            # Sort by price and return cheapest
            cpu_types.sort(key=lambda x: x.get("price_cents_per_hour", 9999))
            return cpu_types[0]["name"]
        
        # Fallback to smallest available instance
        if instance_types:
            instance_types.sort(key=lambda x: x.get("price_cents_per_hour", 9999))
            return instance_types[0]["name"]
        
        return None
    
    def get_ssh_keys(self) -> List[str]:
        """Get available SSH keys"""
        result = self.make_request("GET", "ssh-keys")
        keys = result.get("data", [])
        
        # Look for SOPHIA production key
        for key in keys:
            if "sophia" in key.get("name", "").lower() or "production" in key.get("name", "").lower():
                return [key["name"]]
        
        # Return first available key
        if keys:
            return [keys[0]["name"]]
        
        return []
    
    def launch_instance(self, name: str, instance_type: str, ssh_keys: List[str]) -> Optional[Dict]:
        """Launch a new instance"""
        data = {
            "region_name": "us-south-1",  # Texas region
            "instance_type_name": instance_type,
            "ssh_key_names": ssh_keys,
            "name": name
        }
        
        print(f"Launching instance: {name} ({instance_type})")
        result = self.make_request("POST", "instance-operations/launch", data)
        
        if "data" in result:
            instance_ids = result["data"].get("instance_ids", [])
            if instance_ids:
                print(f"✅ Instance {name} launched with ID: {instance_ids[0]}")
                return {"id": instance_ids[0], "name": name}
        
        print(f"❌ Failed to launch instance {name}")
        return None
    
    def wait_for_instance_active(self, instance_id: str, timeout: int = 300) -> Optional[Dict]:
        """Wait for instance to become active"""
        print(f"Waiting for instance {instance_id} to become active...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = self.make_request("GET", "instances")
            instances = result.get("data", [])
            
            for instance in instances:
                if instance.get("id") == instance_id:
                    status = instance.get("status")
                    if status == "active":
                        ip = instance.get("ip")
                        print(f"✅ Instance {instance_id} is active at {ip}")
                        return instance
                    elif status == "unhealthy":
                        print(f"❌ Instance {instance_id} is unhealthy")
                        return None
                    else:
                        print(f"⏳ Instance {instance_id} status: {status}")
            
            time.sleep(10)
        
        print(f"❌ Timeout waiting for instance {instance_id}")
        return None
    
    def deploy_cpu_cluster(self) -> List[Dict]:
        """Deploy the CPU cluster for SOPHIA Intel"""
        print("🚀 Starting CPU cluster deployment for SOPHIA Intel")
        
        # Find best CPU instance type
        instance_type = self.find_cpu_instance_type()
        if not instance_type:
            print("❌ No suitable instance type found")
            return []
        
        print(f"Using instance type: {instance_type}")
        
        # Get SSH keys
        ssh_keys = self.get_ssh_keys()
        if not ssh_keys:
            print("❌ No SSH keys available")
            return []
        
        print(f"Using SSH keys: {ssh_keys}")
        
        # Launch instances
        launched_instances = []
        for target in self.target_instances:
            instance = self.launch_instance(target["name"], instance_type, ssh_keys)
            if instance:
                instance["role"] = target["role"]
                launched_instances.append(instance)
            else:
                print(f"❌ Failed to launch {target['name']}")
        
        # Wait for all instances to become active
        active_instances = []
        for instance in launched_instances:
            active_instance = self.wait_for_instance_active(instance["id"])
            if active_instance:
                active_instance["role"] = instance["role"]
                active_instances.append(active_instance)
        
        return active_instances

def main():
    """Main deployment function"""
    try:
        deployer = LambdaLabsDeployer()
        
        print("=== PHASE 1: DNS, SSL & INGRESS CONFIGURATION ===")
        print("Deploying CPU-optimized Lambda Labs cluster...")
        
        # Deploy cluster
        instances = deployer.deploy_cpu_cluster()
        
        if not instances:
            print("❌ Failed to deploy cluster")
            return 1
        
        print(f"\n✅ Successfully deployed {len(instances)} instances:")
        for instance in instances:
            name = instance.get("name", "unknown")
            ip = instance.get("ip", "no-ip")
            role = instance.get("role", "unknown")
            print(f"  {name}: {ip} ({role})")
        
        # Save instance information for next phases
        with open("/tmp/sophia_instances.json", "w") as f:
            json.dump(instances, f, indent=2)
        
        print("\n🎯 Phase 1 Infrastructure Ready!")
        print("Next: K3s installation and Kong Ingress deployment")
        
        return 0
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())

