#!/usr/bin/env python3
"""
🎖️ Sophia AI Platform - Lambda Labs Environment Scanner
Comprehensive audit and discovery of Lambda Labs infrastructure
"""

import os
import sys
import json
import requests
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

class LambdaLabsScanner:
    def __init__(self):
        self.api_key = os.getenv('LAMBDA_API_KEY', 'secret_sophia5apikey_a404a99d985d41828d7020f0b9a122a2.PjbWZb0lLubKu1nmyWYLy9Ycl3vyL18o')
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.scan_results = {
            "timestamp": datetime.now().isoformat(),
            "instances": [],
            "ssh_keys": [],
            "instance_types": [],
            "regions": [],
            "network_info": {},
            "recommendations": []
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with timestamps"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def make_api_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Optional[Dict]:
        """Make authenticated API request to Lambda Labs"""
        try:
            url = f"{self.base_url}/{endpoint}"
            self.log(f"Making {method} request to: {endpoint}")
            
            if method == "GET":
                response = requests.get(url, headers=self.headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=30)
            else:
                self.log(f"Unsupported method: {method}", "ERROR")
                return None
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                self.log("Authentication failed - check API key", "ERROR")
                return None
            else:
                self.log(f"API request failed: {response.status_code} - {response.text}", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"Network error: {str(e)}", "ERROR")
            return None
        except Exception as e:
            self.log(f"Unexpected error: {str(e)}", "ERROR")
            return None
    
    def scan_instances(self) -> List[Dict]:
        """Scan all Lambda Labs instances"""
        self.log("🔍 Scanning Lambda Labs instances...")
        
        instances_data = self.make_api_request("instances")
        if not instances_data:
            self.log("Failed to retrieve instances", "ERROR")
            return []
        
        instances = instances_data.get("data", [])
        self.log(f"Found {len(instances)} instances")
        
        for instance in instances:
            instance_id = instance.get("id", "unknown")
            name = instance.get("name", "unnamed")
            status = instance.get("status", "unknown")
            instance_type = instance.get("instance_type", {}).get("name", "unknown")
            region = instance.get("region", {}).get("name", "unknown")
            
            # Get IP addresses
            ip_info = instance.get("ip", "unknown")
            public_ip = "unknown"
            private_ip = "unknown"
            
            if isinstance(ip_info, str):
                public_ip = ip_info
            elif isinstance(ip_info, dict):
                public_ip = ip_info.get("public", "unknown")
                private_ip = ip_info.get("private", "unknown")
            
            instance_info = {
                "id": instance_id,
                "name": name,
                "status": status,
                "instance_type": instance_type,
                "region": region,
                "public_ip": public_ip,
                "private_ip": private_ip,
                "ssh_key_names": instance.get("ssh_key_names", []),
                "hostname": instance.get("hostname", "unknown"),
                "jupyter_token": instance.get("jupyter_token", None),
                "jupyter_url": instance.get("jupyter_url", None),
                "created_at": instance.get("created_at", "unknown")
            }
            
            self.scan_results["instances"].append(instance_info)
            
            self.log(f"📊 Instance: {name} ({instance_id})")
            self.log(f"   Status: {status}")
            self.log(f"   Type: {instance_type}")
            self.log(f"   Region: {region}")
            self.log(f"   Public IP: {public_ip}")
            self.log(f"   Private IP: {private_ip}")
        
        return instances
    
    def scan_ssh_keys(self) -> List[Dict]:
        """Scan SSH keys"""
        self.log("🔑 Scanning SSH keys...")
        
        keys_data = self.make_api_request("ssh-keys")
        if not keys_data:
            self.log("Failed to retrieve SSH keys", "ERROR")
            return []
        
        keys = keys_data.get("data", [])
        self.log(f"Found {len(keys)} SSH keys")
        
        for key in keys:
            key_info = {
                "id": key.get("id", "unknown"),
                "name": key.get("name", "unnamed"),
                "public_key": key.get("public_key", "")[:50] + "..." if key.get("public_key") else "unknown"
            }
            self.scan_results["ssh_keys"].append(key_info)
            self.log(f"🔑 SSH Key: {key_info['name']} ({key_info['id']})")
        
        return keys
    
    def scan_instance_types(self) -> List[Dict]:
        """Scan available instance types"""
        self.log("💻 Scanning instance types...")
        
        types_data = self.make_api_request("instance-types")
        if not types_data:
            self.log("Failed to retrieve instance types", "ERROR")
            return []
        
        instance_types = types_data.get("data", [])
        self.log(f"Found {len(instance_types)} instance types")
        
        for itype in instance_types:
            if isinstance(itype, dict):
                type_info = {
                    "name": itype.get("name", "unknown"),
                    "description": itype.get("description", ""),
                    "price_cents_per_hour": itype.get("price_cents_per_hour", 0),
                    "vcpus": itype.get("specs", {}).get("vcpus", 0) if isinstance(itype.get("specs"), dict) else 0,
                    "memory_gib": itype.get("specs", {}).get("memory_gib", 0) if isinstance(itype.get("specs"), dict) else 0,
                    "storage_gib": itype.get("specs", {}).get("storage_gib", 0) if isinstance(itype.get("specs"), dict) else 0,
                    "gpus": itype.get("specs", {}).get("gpus", []) if isinstance(itype.get("specs"), dict) else []
                }
            else:
                type_info = {
                    "name": str(itype),
                    "description": "Unknown type",
                    "price_cents_per_hour": 0,
                    "vcpus": 0,
                    "memory_gib": 0,
                    "storage_gib": 0,
                    "gpus": []
                }
            self.scan_results["instance_types"].append(type_info)
        
        return instance_types
    
    def test_connectivity(self, ip_address: str) -> Dict:
        """Test connectivity to an instance"""
        self.log(f"🌐 Testing connectivity to {ip_address}...")
        
        connectivity = {
            "ip": ip_address,
            "ping": False,
            "ssh": False,
            "http_8080": False,
            "http_3000": False,
            "http_9090": False
        }
        
        # Test ping
        try:
            result = subprocess.run(['ping', '-c', '1', '-W', '5', ip_address], 
                                  capture_output=True, text=True, timeout=10)
            connectivity["ping"] = result.returncode == 0
        except:
            connectivity["ping"] = False
        
        # Test SSH (port 22)
        try:
            result = subprocess.run(['nc', '-z', '-w', '5', ip_address, '22'], 
                                  capture_output=True, timeout=10)
            connectivity["ssh"] = result.returncode == 0
        except:
            connectivity["ssh"] = False
        
        # Test HTTP ports
        for port, key in [(8080, "http_8080"), (3000, "http_3000"), (9090, "http_9090")]:
            try:
                result = subprocess.run(['nc', '-z', '-w', '3', ip_address, str(port)], 
                                      capture_output=True, timeout=5)
                connectivity[key] = result.returncode == 0
            except:
                connectivity[key] = False
        
        return connectivity
    
    def analyze_network_configuration(self):
        """Analyze network configuration and connectivity"""
        self.log("🌐 Analyzing network configuration...")
        
        for instance in self.scan_results["instances"]:
            if instance["status"] == "active" and instance["public_ip"] != "unknown":
                connectivity = self.test_connectivity(instance["public_ip"])
                instance["connectivity"] = connectivity
                
                self.log(f"📡 Connectivity for {instance['name']} ({instance['public_ip']}):")
                self.log(f"   Ping: {'✅' if connectivity['ping'] else '❌'}")
                self.log(f"   SSH: {'✅' if connectivity['ssh'] else '❌'}")
                self.log(f"   Dashboard (8080): {'✅' if connectivity['http_8080'] else '❌'}")
                self.log(f"   Grafana (3000): {'✅' if connectivity['http_3000'] else '❌'}")
                self.log(f"   Prometheus (9090): {'✅' if connectivity['http_9090'] else '❌'}")
    
    def generate_recommendations(self):
        """Generate optimization recommendations"""
        self.log("💡 Generating recommendations...")
        
        recommendations = []
        
        # Check for active instances
        active_instances = [i for i in self.scan_results["instances"] if i["status"] == "active"]
        if not active_instances:
            recommendations.append({
                "type": "critical",
                "title": "No Active Instances",
                "description": "No active Lambda Labs instances found. You need to launch an instance to deploy Sophia AI Platform.",
                "action": "Launch a new instance with GPU support (recommended: gpu_1x_h100_pcie)"
            })
        
        # Check for SSH connectivity
        for instance in active_instances:
            if instance.get("connectivity", {}).get("ssh", False) == False:
                recommendations.append({
                    "type": "warning",
                    "title": f"SSH Access Issue - {instance['name']}",
                    "description": f"Cannot connect to SSH on {instance['public_ip']}:22",
                    "action": "Check security groups and SSH key configuration"
                })
        
        # Check for running services
        for instance in active_instances:
            connectivity = instance.get("connectivity", {})
            if not connectivity.get("http_8080", False):
                recommendations.append({
                    "type": "info",
                    "title": f"Dashboard Not Running - {instance['name']}",
                    "description": "Sophia AI Dashboard not detected on port 8080",
                    "action": "Deploy the enhanced dashboard using the deployment scripts"
                })
        
        # Cost optimization
        expensive_instances = [i for i in active_instances 
                             if any(t["name"] == i["instance_type"] and t["price_cents_per_hour"] > 1000 
                                   for t in self.scan_results["instance_types"])]
        if expensive_instances:
            recommendations.append({
                "type": "optimization",
                "title": "Cost Optimization Opportunity",
                "description": f"Found {len(expensive_instances)} expensive instances running",
                "action": "Consider using smaller instances for development or implement auto-shutdown"
            })
        
        self.scan_results["recommendations"] = recommendations
        
        for rec in recommendations:
            level = rec["type"].upper()
            self.log(f"💡 {level}: {rec['title']}")
            self.log(f"   {rec['description']}")
            self.log(f"   Action: {rec['action']}")
    
    def save_results(self, filename: str = "lambda_labs_scan_results.json"):
        """Save scan results to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.scan_results, f, indent=2)
            self.log(f"💾 Scan results saved to {filename}")
        except Exception as e:
            self.log(f"Failed to save results: {str(e)}", "ERROR")
    
    def generate_deployment_config(self):
        """Generate deployment configuration based on scan results"""
        self.log("⚙️ Generating deployment configuration...")
        
        active_instances = [i for i in self.scan_results["instances"] if i["status"] == "active"]
        
        if not active_instances:
            self.log("No active instances found for deployment configuration", "WARNING")
            return
        
        # Use the first active instance as primary
        primary_instance = active_instances[0]
        
        config = {
            "deployment": {
                "primary_instance": {
                    "id": primary_instance["id"],
                    "name": primary_instance["name"],
                    "public_ip": primary_instance["public_ip"],
                    "private_ip": primary_instance["private_ip"],
                    "instance_type": primary_instance["instance_type"],
                    "region": primary_instance["region"]
                },
                "endpoints": {
                    "dashboard": f"http://{primary_instance['public_ip']}:8080",
                    "grafana": f"http://{primary_instance['public_ip']}:3000",
                    "prometheus": f"http://{primary_instance['public_ip']}:9090",
                    "ssh": f"ssh ubuntu@{primary_instance['public_ip']}"
                },
                "ssh_command": f"ssh ubuntu@{primary_instance['public_ip']}",
                "deployment_commands": [
                    f"ssh ubuntu@{primary_instance['public_ip']}",
                    "git clone https://github.com/ai-cherry/sophia-main.git",
                    "cd sophia-main",
                    "./install_auto_login.sh && ./create_system_service.sh"
                ]
            }
        }
        
        # Save deployment config
        with open("deployment_config.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        self.log("⚙️ Deployment configuration generated")
        return config
    
    def run_complete_scan(self):
        """Run complete Lambda Labs environment scan"""
        self.log("🎖️ Starting comprehensive Lambda Labs scan...")
        
        try:
            # Scan all components
            self.scan_instances()
            self.scan_ssh_keys()
            self.scan_instance_types()
            self.analyze_network_configuration()
            self.generate_recommendations()
            
            # Generate outputs
            deployment_config = self.generate_deployment_config()
            self.save_results()
            
            # Summary
            self.log("📊 Scan Summary:")
            self.log(f"   Instances: {len(self.scan_results['instances'])}")
            self.log(f"   SSH Keys: {len(self.scan_results['ssh_keys'])}")
            self.log(f"   Instance Types: {len(self.scan_results['instance_types'])}")
            self.log(f"   Recommendations: {len(self.scan_results['recommendations'])}")
            
            active_instances = [i for i in self.scan_results["instances"] if i["status"] == "active"]
            if active_instances:
                self.log("🎯 Ready for deployment!")
                primary = active_instances[0]
                self.log(f"   Primary Instance: {primary['name']} ({primary['public_ip']})")
                self.log(f"   SSH Command: ssh ubuntu@{primary['public_ip']}")
            else:
                self.log("⚠️ No active instances found - need to launch instance first")
            
            return True
            
        except Exception as e:
            self.log(f"Scan failed: {str(e)}", "ERROR")
            return False

def main():
    """Main execution function"""
    print("🎖️ Sophia AI Platform - Lambda Labs Environment Scanner")
    print("=" * 60)
    
    scanner = LambdaLabsScanner()
    
    # Check API key
    if not scanner.api_key or scanner.api_key == "YOUR_LAMBDA_API_KEY":
        print("❌ Lambda Labs API key not configured!")
        print("Set LAMBDA_API_KEY environment variable or update the script")
        sys.exit(1)
    
    # Run scan
    success = scanner.run_complete_scan()
    
    if success:
        print("\n🎉 Lambda Labs scan completed successfully!")
        print("📄 Results saved to: lambda_labs_scan_results.json")
        print("⚙️ Deployment config: deployment_config.json")
    else:
        print("\n❌ Lambda Labs scan failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()

