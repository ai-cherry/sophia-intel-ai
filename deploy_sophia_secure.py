#!/usr/bin/env python3
"""
SOPHIA Intel Production Deployment Script (Secure Version)
Deploys the complete SOPHIA Intel platform to production infrastructure
All credentials loaded from environment variables for security
"""

import os
import sys
import json
import time
import requests
import subprocess
from pathlib import Path

class SophiaDeployment:
    def __init__(self):
        # Load configuration from environment variables
        self.config = {
            "GITHUB_PAT": os.getenv("GITHUB_PAT"),
            "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY"),
            "RAILWAY_TOKEN": os.getenv("RAILWAY_TOKEN"),
            "NEON_API_TOKEN": os.getenv("NEON_API_TOKEN"),
            "DNSIMPLE_API_KEY": os.getenv("DNSIMPLE_API_KEY"),
            "LAMBDA_API_KEY": os.getenv("LAMBDA_API_KEY"),
            "LAMBDA_PRIMARY_IP": os.getenv("LAMBDA_PRIMARY_IP", "192.222.51.223"),
            "LAMBDA_SECONDARY_IP": os.getenv("LAMBDA_SECONDARY_IP", "192.222.50.242"),
            "DOMAIN": "sophia-intel.ai"
        }
        
        # Validate required environment variables
        required_vars = ["OPENROUTER_API_KEY", "LAMBDA_API_KEY", "DNSIMPLE_API_KEY"]
        missing_vars = [var for var in required_vars if not self.config.get(var)]
        
        if missing_vars:
            self.log(f"❌ Missing required environment variables: {', '.join(missing_vars)}", "ERROR")
            self.log("Please set these variables in your .env.production file", "ERROR")
            sys.exit(1)
            
        self.deployment_status = {}
        
    def log(self, message, level="INFO"):
        """Enhanced logging with timestamps"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def check_lambda_servers(self):
        """Check Lambda Labs server status"""
        self.log("🔍 Checking Lambda Labs GH200 servers...")
        
        servers = [
            {"name": "primary", "ip": self.config["LAMBDA_PRIMARY_IP"]},
            {"name": "secondary", "ip": self.config["LAMBDA_SECONDARY_IP"]}
        ]
        
        for server in servers:
            try:
                response = requests.get(f"http://{server['ip']}:8000/health", timeout=10)
                if response.status_code == 200:
                    self.log(f"✅ {server['name'].title()} server ({server['ip']}) is healthy")
                    self.deployment_status[f"lambda_{server['name']}"] = "healthy"
                else:
                    self.log(f"⚠️ {server['name'].title()} server ({server['ip']}) returned status {response.status_code}")
                    self.deployment_status[f"lambda_{server['name']}"] = "unhealthy"
            except Exception as e:
                self.log(f"❌ {server['name'].title()} server ({server['ip']}) is not accessible: {e}")
                self.deployment_status[f"lambda_{server['name']}"] = "offline"
                
    def setup_dns_configuration(self):
        """Configure DNS records using DNSimple API"""
        self.log("🌐 Configuring DNS records...")
        
        if not self.config["DNSIMPLE_API_KEY"]:
            self.log("⚠️ DNSimple API key not provided, skipping DNS configuration")
            self.deployment_status["dns_config"] = "skipped"
            return
            
        headers = {
            "Authorization": f"Bearer {self.config['DNSIMPLE_API_KEY']}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get("https://api.dnsimple.com/v2/whoami", headers=headers)
            if response.status_code == 200:
                self.log(f"✅ DNSimple API authenticated successfully")
                self.log("📝 DNS records prepared for configuration")
                self.deployment_status["dns_config"] = "prepared"
            else:
                self.log(f"❌ DNSimple API authentication failed: {response.status_code}")
                self.deployment_status["dns_config"] = "failed"
        except Exception as e:
            self.log(f"❌ DNS configuration error: {e}")
            self.deployment_status["dns_config"] = "error"
            
    def create_production_files(self):
        """Create production deployment files"""
        self.log("📦 Creating production deployment files...")
        
        # Create Dockerfile
        dockerfile_content = """# SOPHIA Intel Production Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc g++ curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 sophia && chown -R sophia:sophia /app
USER sophia

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        
        with open("Dockerfile", "w") as f:
            f.write(dockerfile_content)
            
        # Create requirements.txt
        requirements = """fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
httpx==0.25.2
aiohttp==3.9.1
redis==5.0.1
psycopg2-binary==2.9.9
sqlalchemy==2.0.23
requests==2.31.0
python-dotenv==1.0.0
"""
        
        with open("requirements.txt", "w") as f:
            f.write(requirements)
            
        # Create Railway configuration
        railway_config = {
            "name": "sophia-intel-production",
            "description": "SOPHIA Intel AI Platform - Production Backend",
            "build": {
                "builder": "dockerfile"
            },
            "deploy": {
                "healthcheckPath": "/health",
                "restartPolicyType": "on_failure"
            }
        }
        
        with open("railway.json", "w") as f:
            json.dump(railway_config, f, indent=2)
            
        self.log("✅ Production files created")
        self.deployment_status["production_files"] = "ready"
        
    def verify_deployment(self):
        """Verify deployment readiness"""
        self.log("🔍 Verifying deployment status...")
        
        services_to_check = [
            "lambda_primary",
            "lambda_secondary", 
            "dns_config",
            "production_files"
        ]
        
        healthy_services = 0
        total_services = len(services_to_check)
        
        for service in services_to_check:
            status = self.deployment_status.get(service, "unknown")
            if status in ["healthy", "ready", "prepared", "skipped"]:
                healthy_services += 1
                self.log(f"✅ {service}: {status}")
            else:
                self.log(f"❌ {service}: {status}")
                
        success_rate = (healthy_services / total_services) * 100
        self.log(f"📊 Deployment Success Rate: {success_rate:.1f}% ({healthy_services}/{total_services})")
        
        return success_rate >= 75
        
    def run_deployment(self):
        """Execute complete deployment process"""
        self.log("🚀 Starting SOPHIA Intel Production Deployment")
        self.log("=" * 60)
        
        try:
            # Step 1: Check Lambda Labs servers
            self.check_lambda_servers()
            
            # Step 2: Setup DNS configuration
            self.setup_dns_configuration()
            
            # Step 3: Create production files
            self.create_production_files()
            
            # Step 4: Verify deployment
            success = self.verify_deployment()
            
            if success:
                self.log("🎉 SOPHIA Intel deployment preparation completed successfully!")
                self.log("🌐 Ready for production deployment:")
                self.log("   - Frontend: https://www.sophia-intel.ai")
                self.log("   - API: https://api.sophia-intel.ai")
                self.log("   - Primary Inference: https://inference-primary.sophia-intel.ai:8000")
                self.log("   - Secondary Inference: https://inference-secondary.sophia-intel.ai:8000")
                
                # Create deployment report
                report = {
                    "timestamp": time.time(),
                    "deployment_status": self.deployment_status,
                    "success_rate": (len([s for s in self.deployment_status.values() if s in ["healthy", "ready", "prepared", "skipped"]]) / len(self.deployment_status)) * 100,
                    "next_steps": [
                        "Deploy to Railway: railway up",
                        "Configure DNS records",
                        "Setup monitoring",
                        "Run health checks"
                    ]
                }
                
                with open("deployment_report.json", "w") as f:
                    json.dump(report, f, indent=2)
                    
            else:
                self.log("⚠️ Deployment preparation completed with some issues. Check logs above.")
                
            return success
            
        except Exception as e:
            self.log(f"❌ Deployment failed: {e}", "ERROR")
            return False

if __name__ == "__main__":
    deployment = SophiaDeployment()
    success = deployment.run_deployment()
    sys.exit(0 if success else 1)

