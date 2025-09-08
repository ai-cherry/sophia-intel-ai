#!/usr/bin/env python3
"""
🎖️ Sophia AI Platform - IP Address Alignment & Codebase Configuration
Updates all IP addresses and endpoints throughout the codebase based on Lambda Labs scan results
"""

import os
import json
import re
import glob
from typing import Dict, List, Tuple
from datetime import datetime

class IPAlignmentUpdater:
    def __init__(self):
        self.deployment_config = self.load_deployment_config()
        self.scan_results = self.load_scan_results()
        self.updates_made = []
        self.files_processed = 0
        
        # Extract key information
        if self.deployment_config:
            self.primary_ip = self.deployment_config["deployment"]["primary_instance"]["public_ip"]
            self.endpoints = self.deployment_config["deployment"]["endpoints"]
        else:
            self.primary_ip = "104.171.202.103"  # Fallback from scan
            self.endpoints = {
                "dashboard": f"http://{self.primary_ip}:8080",
                "grafana": f"http://{self.primary_ip}:3000",
                "prometheus": f"http://{self.primary_ip}:9090",
                "ssh": f"ssh ubuntu@{self.primary_ip}"
            }
        
        # All discovered instances
        self.all_instances = {
            "production": "104.171.202.103",    # sophia-production-instance (RTX6000)
            "core": "192.222.58.232",          # sophia-ai-core (GH200)
            "orchestrator": "104.171.202.117", # sophia-mcp-orchestrator (A6000)
            "pipeline": "104.171.202.134",     # sophia-data-pipeline (A100)
            "development": "155.248.194.183"   # sophia-development (A10)
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with timestamps"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def load_deployment_config(self) -> Dict:
        """Load deployment configuration"""
        try:
            with open("deployment_config.json", 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.log("Deployment config not found, using defaults", "WARNING")
            return None
        except Exception as e:
            self.log(f"Error loading deployment config: {str(e)}", "ERROR")
            return None
    
    def load_scan_results(self) -> Dict:
        """Load Lambda Labs scan results"""
        try:
            with open("lambda_labs_scan_results.json", 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.log("Scan results not found", "WARNING")
            return None
        except Exception as e:
            self.log(f"Error loading scan results: {str(e)}", "ERROR")
            return None
    
    def find_files_to_update(self) -> List[str]:
        """Find all files that might contain IP addresses or endpoints"""
        patterns = [
            "*.py", "*.sh", "*.md", "*.yml", "*.yaml", "*.json", 
            "*.html", "*.js", "*.ts", "*.env*", "*.conf", "*.cfg"
        ]
        
        files = []
        for pattern in patterns:
            files.extend(glob.glob(pattern, recursive=False))
            files.extend(glob.glob(f"**/{pattern}", recursive=True))
        
        # Filter out certain directories and files
        exclude_patterns = [
            ".git/", "__pycache__/", "node_modules/", ".venv/", "venv/",
            "lambda_labs_scan_results.json", "deployment_config.json"
        ]
        
        filtered_files = []
        for file in files:
            if not any(exclude in file for exclude in exclude_patterns):
                filtered_files.append(file)
        
        return list(set(filtered_files))  # Remove duplicates
    
    def update_file_content(self, filepath: str) -> bool:
        """Update IP addresses and endpoints in a file"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            original_content = content
            updates_in_file = []
            
            # Define replacement patterns
            replacements = [
                # Generic IP patterns (be careful not to replace valid IPs)
                (r'104.171.202.103', self.primary_ip),
                (r'104.171.202.103', self.primary_ip),
                (r'104.171.202.103', self.primary_ip),
                (r'104.171.202.103', self.primary_ip),
                
                # Specific endpoint patterns
                (r'http://104.171.202.103:8080', self.endpoints["dashboard"]),
                (r'http://127\.0\.0\.1:8080', self.endpoints["dashboard"]),
                (r'http://0\.0\.0\.0:8080', self.endpoints["dashboard"]),
                
                (r'http://104.171.202.103:3000', self.endpoints["grafana"]),
                (r'http://127\.0\.0\.1:3000', self.endpoints["grafana"]),
                (r'http://0\.0\.0\.0:3000', self.endpoints["grafana"]),
                
                (r'http://104.171.202.103:9090', self.endpoints["prometheus"]),
                (r'http://127\.0\.0\.1:9090', self.endpoints["prometheus"]),
                (r'http://0\.0\.0\.0:9090', self.endpoints["prometheus"]),
                
                # SSH command patterns
                (r'ssh ubuntu@104.171.202.103', f'ssh ubuntu@{self.primary_ip}'),
                (r'ssh ubuntu@104.171.202.103', f'ssh ubuntu@{self.primary_ip}'),
                (r'ssh ubuntu@104.171.202.103', f'ssh ubuntu@{self.primary_ip}'),
                
                # Domain patterns (update to use IP for now)
                (r'https://api\.sophia-intel\.ai', f'http://{self.primary_ip}:8080/api'),
                (r'https://app\.sophia-intel\.ai', f'http://{self.primary_ip}:8080'),
                (r'https://monitoring\.sophia-intel\.ai', self.endpoints["grafana"]),
                (r'https://metrics\.sophia-intel\.ai', self.endpoints["prometheus"]),
            ]
            
            # Apply replacements
            for pattern, replacement in replacements:
                matches = re.findall(pattern, content)
                if matches:
                    content = re.sub(pattern, replacement, content)
                    updates_in_file.append(f"{pattern} -> {replacement} ({len(matches)} occurrences)")
            
            # Save if changes were made
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.updates_made.extend([f"{filepath}: {update}" for update in updates_in_file])
                self.log(f"Updated {filepath} ({len(updates_in_file)} changes)")
                return True
            
            return False
            
        except Exception as e:
            self.log(f"Error updating {filepath}: {str(e)}", "ERROR")
            return False
    
    def create_environment_configs(self):
        """Create environment-specific configuration files"""
        self.log("Creating environment-specific configurations...")
        
        # Production environment config
        prod_config = {
            "environment": "production",
            "primary_instance": self.all_instances["production"],
            "instances": {
                "production": {
                    "ip": self.all_instances["production"],
                    "type": "gpu_1x_rtx6000",
                    "role": "primary",
                    "services": ["dashboard", "api", "monitoring"]
                },
                "core": {
                    "ip": self.all_instances["core"],
                    "type": "gpu_1x_gh200",
                    "role": "ai-core",
                    "services": ["inference", "training"]
                },
                "orchestrator": {
                    "ip": self.all_instances["orchestrator"],
                    "type": "gpu_1x_a6000",
                    "role": "mcp-orchestrator",
                    "services": ["mcp", "orchestration"]
                },
                "pipeline": {
                    "ip": self.all_instances["pipeline"],
                    "type": "gpu_1x_a100",
                    "role": "data-pipeline",
                    "services": ["data-processing", "etl"]
                },
                "development": {
                    "ip": self.all_instances["development"],
                    "type": "gpu_1x_a10",
                    "role": "development",
                    "services": ["testing", "development"]
                }
            },
            "endpoints": {
                "dashboard": f"http://{self.all_instances['production']}:8080",
                "api": f"http://{self.all_instances['production']}:8080/api",
                "grafana": f"http://{self.all_instances['production']}:3000",
                "prometheus": f"http://{self.all_instances['production']}:9090",
                "ai_core": f"http://{self.all_instances['core']}:8000",
                "mcp_orchestrator": f"http://{self.all_instances['orchestrator']}:8001",
                "data_pipeline": f"http://{self.all_instances['pipeline']}:8002"
            },
            "ssh_commands": {
                "production": f"ssh ubuntu@{self.all_instances['production']}",
                "core": f"ssh ubuntu@{self.all_instances['core']}",
                "orchestrator": f"ssh ubuntu@{self.all_instances['orchestrator']}",
                "pipeline": f"ssh ubuntu@{self.all_instances['pipeline']}",
                "development": f"ssh ubuntu@{self.all_instances['development']}"
            }
        }
        
        with open("environment_config.json", 'w') as f:
            json.dump(prod_config, f, indent=2)
        
        self.log("Environment configuration created: environment_config.json")
    
    def create_deployment_scripts(self):
        """Create deployment scripts with real IP addresses"""
        self.log("Creating deployment scripts with real IPs...")
        
        # Multi-instance deployment script
        deploy_script = f"""#!/bin/bash
# 🎖️ Sophia AI Platform - Multi-Instance Deployment Script
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

set -e

# Color codes for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

# Instance configurations
PRODUCTION_IP="{self.all_instances['production']}"
CORE_IP="{self.all_instances['core']}"
ORCHESTRATOR_IP="{self.all_instances['orchestrator']}"
PIPELINE_IP="{self.all_instances['pipeline']}"
DEVELOPMENT_IP="{self.all_instances['development']}"

echo -e "${{BLUE}}🎖️ Sophia AI Platform - Multi-Instance Deployment${{NC}}"
echo "=================================================="

# Function to deploy to a single instance
deploy_to_instance() {{
    local instance_name=$1
    local instance_ip=$2
    local services=$3
    
    echo -e "${{YELLOW}}📡 Deploying to $instance_name ($instance_ip)...${{NC}}"
    
    # Test connectivity
    if ! nc -z -w5 $instance_ip 22; then
        echo -e "${{RED}}❌ Cannot connect to $instance_name ($instance_ip)${{NC}}"
        return 1
    fi
    
    # Deploy via SSH
    ssh -o StrictHostKeyChecking=no ubuntu@$instance_ip << 'EOF'
        # Update system
        sudo apt-get update -qq
        
        # Clone/update repository
        if [ -d "sophia-main" ]; then
            cd sophia-main && git pull
        else
            git clone https://github.com/ai-cherry/sophia-main.git
            cd sophia-main
        fi
        
        # Set up environment
        export PULUMI_ACCESS_TOKEN="YOUR_PULUMI_ACCESS_TOKEN"
        export EXA_API_KEY="fdf07f38-34ad-44a9-ab6f-74ca2ca90fd4"
        export LAMBDA_API_KEY="secret_sophia5apikey_a404a99d985d41828d7020f0b9a122a2.PjbWZb0lLubKu1nmyWYLy9Ycl3vyL18o"
        
        # Run deployment
        chmod +x *.sh
        ./install_auto_login.sh
        ./create_system_service.sh
        
        echo "✅ Deployment completed on $(hostname)"
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "${{GREEN}}✅ Successfully deployed to $instance_name${{NC}}"
    else
        echo -e "${{RED}}❌ Failed to deploy to $instance_name${{NC}}"
    fi
}}

# Deploy to all instances
echo -e "${{BLUE}}🚀 Starting multi-instance deployment...${{NC}}"

deploy_to_instance "Production" "$PRODUCTION_IP" "dashboard,api,monitoring"
deploy_to_instance "AI Core" "$CORE_IP" "inference,training"
deploy_to_instance "MCP Orchestrator" "$ORCHESTRATOR_IP" "mcp,orchestration"
deploy_to_instance "Data Pipeline" "$PIPELINE_IP" "data-processing,etl"
deploy_to_instance "Development" "$DEVELOPMENT_IP" "testing,development"

echo -e "${{GREEN}}🎉 Multi-instance deployment completed!${{NC}}"
echo ""
echo "📊 Access Points:"
echo "  Dashboard:    http://$PRODUCTION_IP:8080"
echo "  Grafana:      http://$PRODUCTION_IP:3000"
echo "  Prometheus:   http://$PRODUCTION_IP:9090"
echo "  AI Core:      http://$CORE_IP:8000"
echo "  MCP:          http://$ORCHESTRATOR_IP:8001"
echo "  Data Pipeline: http://$PIPELINE_IP:8002"
echo ""
echo "🔑 SSH Access:"
echo "  Production:   ssh ubuntu@$PRODUCTION_IP"
echo "  AI Core:      ssh ubuntu@$CORE_IP"
echo "  Orchestrator: ssh ubuntu@$ORCHESTRATOR_IP"
echo "  Pipeline:     ssh ubuntu@$PIPELINE_IP"
echo "  Development:  ssh ubuntu@$DEVELOPMENT_IP"
"""
        
        with open("deploy_multi_instance.sh", 'w') as f:
            f.write(deploy_script)
        
        os.chmod("deploy_multi_instance.sh", 0o755)
        self.log("Multi-instance deployment script created: deploy_multi_instance.sh")
    
    def run_alignment_update(self):
        """Run the complete IP alignment update process"""
        self.log("🎖️ Starting IP alignment and codebase configuration...")
        
        # Find files to update
        files_to_update = self.find_files_to_update()
        self.log(f"Found {len(files_to_update)} files to process")
        
        # Update files
        updated_files = 0
        for filepath in files_to_update:
            if self.update_file_content(filepath):
                updated_files += 1
            self.files_processed += 1
        
        # Create additional configurations
        self.create_environment_configs()
        self.create_deployment_scripts()
        
        # Summary
        self.log("📊 IP Alignment Summary:")
        self.log(f"   Files processed: {self.files_processed}")
        self.log(f"   Files updated: {updated_files}")
        self.log(f"   Total changes: {len(self.updates_made)}")
        self.log(f"   Primary IP: {self.primary_ip}")
        
        # Save update report
        report = {
            "timestamp": datetime.now().isoformat(),
            "primary_ip": self.primary_ip,
            "all_instances": self.all_instances,
            "endpoints": self.endpoints,
            "files_processed": self.files_processed,
            "files_updated": updated_files,
            "updates_made": self.updates_made
        }
        
        with open("ip_alignment_report.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        self.log("💾 Update report saved to: ip_alignment_report.json")
        
        return True

def main():
    """Main execution function"""
    print("🎖️ Sophia AI Platform - IP Address Alignment & Codebase Configuration")
    print("=" * 70)
    
    updater = IPAlignmentUpdater()
    success = updater.run_alignment_update()
    
    if success:
        print("\\n🎉 IP alignment and codebase configuration completed successfully!")
        print("📄 Report saved to: ip_alignment_report.json")
        print("⚙️ Environment config: environment_config.json")
        print("🚀 Multi-instance deployment: deploy_multi_instance.sh")
    else:
        print("\\n❌ IP alignment failed!")
        return 1

if __name__ == "__main__":
    main()

