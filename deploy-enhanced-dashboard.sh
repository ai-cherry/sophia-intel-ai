#!/bin/bash
# deploy-enhanced-dashboard.sh - Production deployment for Enhanced Secret Management Dashboard

set -e

echo "🎖️ Deploying Enhanced Sophia Secret Management Dashboard to Production"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DASHBOARD_VERSION="2.0.0"
DOCKER_IMAGE="sophia-secret-dashboard:${DASHBOARD_VERSION}"
COMPOSE_FILE="docker-compose.enhanced.yml"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Pre-deployment checks
log_info "Running pre-deployment checks..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    log_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if required files exist
required_files=(
    "enhanced_secret_dashboard.py"
    "requirements-enhanced.txt"
    "Dockerfile.enhanced"
    "$COMPOSE_FILE"
    "prometheus.yml"
    "alert_rules.yml"
)

for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        log_error "Required file $file not found"
        exit 1
    fi
done

log_success "Pre-deployment checks passed"

# Environment setup
log_info "Setting up environment variables..."

# Check for required environment variables
required_env_vars=(
    "OPENAI_API_KEY"
    "ANTHROPIC_API_KEY"
    "LAMBDA_API_KEY"
    "EXA_API_KEY"
)

missing_vars=()
for var in "${required_env_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        missing_vars+=("$var")
    fi
done

if [[ ${#missing_vars[@]} -gt 0 ]]; then
    log_warning "Missing environment variables: ${missing_vars[*]}"
    log_info "These can be set in the Docker Compose environment section"
fi

# Generate JWT secret if not provided
if [[ -z "$JWT_SECRET" ]]; then
    export JWT_SECRET=$(openssl rand -hex 32)
    log_info "Generated JWT secret"
fi

# Build Docker image
log_info "Building Docker image: $DOCKER_IMAGE"
docker build -f Dockerfile.enhanced -t "$DOCKER_IMAGE" .

if [[ $? -eq 0 ]]; then
    log_success "Docker image built successfully"
else
    log_error "Failed to build Docker image"
    exit 1
fi

# Stop existing services
log_info "Stopping existing services..."
docker-compose -f "$COMPOSE_FILE" down --remove-orphans

# Create necessary directories
log_info "Creating necessary directories..."
sudo mkdir -p /opt/sophia/{logs,data,backups}
sudo chown -R $USER:$USER /opt/sophia

# Deploy services
log_info "Deploying services with Docker Compose..."
docker-compose -f "$COMPOSE_FILE" up -d

# Wait for services to be ready
log_info "Waiting for services to be ready..."
sleep 30

# Health checks
log_info "Running health checks..."

# Check dashboard health
dashboard_health=$(curl -s -o /dev/null -w "%{http_code}" http://104.171.202.103:8080/health || echo "000")
if [[ "$dashboard_health" == "200" ]]; then
    log_success "Dashboard is healthy"
else
    log_error "Dashboard health check failed (HTTP $dashboard_health)"
fi

# Check Prometheus
prometheus_health=$(curl -s -o /dev/null -w "%{http_code}" http://104.171.202.103:9090/-/healthy || echo "000")
if [[ "$prometheus_health" == "200" ]]; then
    log_success "Prometheus is healthy"
else
    log_warning "Prometheus health check failed (HTTP $prometheus_health)"
fi

# Check Grafana
grafana_health=$(curl -s -o /dev/null -w "%{http_code}" http://104.171.202.103:3000/api/health || echo "000")
if [[ "$grafana_health" == "200" ]]; then
    log_success "Grafana is healthy"
else
    log_warning "Grafana health check failed (HTTP $grafana_health)"
fi

# Display service URLs
echo ""
log_success "🎉 Enhanced Secret Management Dashboard deployed successfully!"
echo ""
echo "📊 Service URLs:"
echo "  • Dashboard API:     http://104.171.202.103:8080"
echo "  • Dashboard Health:  http://104.171.202.103:8080/health"
echo "  • Prometheus:        http://104.171.202.103:9090"
echo "  • Grafana:          http://104.171.202.103:3000 (admin/sophia123)"
echo "  • Metrics:          http://104.171.202.103:8080/metrics"
echo ""

# Display authentication info
echo "🔐 Authentication:"
echo "  • Default login:    admin/sophia123"
echo "  • JWT Secret:       $JWT_SECRET"
echo ""

# Display next steps
echo "🚀 Next Steps:"
echo "  1. Open dashboard_frontend.html in your browser"
echo "  2. Login with admin/sophia123 to get JWT token"
echo "  3. Configure your API keys in the dashboard"
echo "  4. Monitor secret health in real-time"
echo ""

# Integration with main Sophia platform
log_info "Setting up integration with main Sophia platform..."

# Create integration script
cat > sophia_integration.py << 'EOF'
#!/usr/bin/env python3
"""
Sophia Platform Integration with Enhanced Secret Management Dashboard
"""

import asyncio
import aiohttp
import os
from datetime import datetime

class SophiaSecretIntegration:
    def __init__(self):
        self.dashboard_url = "http://104.171.202.103:8080"
        self.auth_token = None
    
    async def authenticate(self):
        """Authenticate with the secret dashboard"""
        async with aiohttp.ClientSession() as session:
            login_data = {
                "username": "admin",
                "password": "sophia123"
            }
            async with session.post(f"{self.dashboard_url}/api/auth/login", json=login_data) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.auth_token = data["access_token"]
                    print("✅ Authenticated with secret dashboard")
                    return True
                else:
                    print("❌ Authentication failed")
                    return False
    
    async def check_secrets_health(self):
        """Check secret health before deployment"""
        if not self.auth_token:
            await self.authenticate()
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.dashboard_url}/api/secrets/health", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    health_score = data["health_score"]
                    
                    if health_score >= 95:
                        print(f"✅ Secret health excellent: {health_score:.1f}%")
                        return True
                    elif health_score >= 80:
                        print(f"⚠️  Secret health good: {health_score:.1f}%")
                        return True
                    else:
                        print(f"❌ Secret health poor: {health_score:.1f}%")
                        return False
                else:
                    print("❌ Failed to check secret health")
                    return False
    
    async def switch_to_production(self):
        """Switch to production environment"""
        if not self.auth_token:
            await self.authenticate()
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        switch_data = {"environment": "production"}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.dashboard_url}/api/environment/switch",
                json=switch_data,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data["success"]:
                        print("✅ Switched to production environment")
                        return True
                    else:
                        print(f"❌ Failed to switch: {data.get('error')}")
                        return False
                else:
                    print("❌ Environment switch request failed")
                    return False

async def main():
    """Main integration function"""
    integration = SophiaSecretIntegration()
    
    print("🎖️ Sophia Platform - Secret Management Integration")
    print("=" * 50)
    
    # Check secret health
    health_ok = await integration.check_secrets_health()
    
    if health_ok:
        print("✅ Secret health check passed - ready for production")
    else:
        print("❌ Secret health check failed - review secrets before deployment")
    
    return health_ok

if __name__ == "__main__":
    asyncio.run(main())
EOF

chmod +x sophia_integration.py

log_success "Integration script created: sophia_integration.py"

# Create systemd service for production
if command -v systemctl &> /dev/null; then
    log_info "Creating systemd service for production deployment..."
    
    sudo tee /etc/systemd/system/sophia-secret-dashboard.service > /dev/null << EOF
[Unit]
Description=Sophia AI Enhanced Secret Management Dashboard
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/docker-compose -f $COMPOSE_FILE up -d
ExecStop=/usr/bin/docker-compose -f $COMPOSE_FILE down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable sophia-secret-dashboard.service
    
    log_success "Systemd service created and enabled"
fi

# Final status
echo ""
log_success "🎖️ Enhanced Secret Management Dashboard deployment complete!"
echo ""
echo "📋 Deployment Summary:"
echo "  • Version: $DASHBOARD_VERSION"
echo "  • Services: Dashboard, PostgreSQL, Redis, Prometheus, Grafana"
echo "  • Health Status: $(curl -s http://104.171.202.103:8080/health | jq -r '.status' 2>/dev/null || echo 'Unknown')"
echo "  • Integration: Ready for Sophia Platform"
echo ""

# Test the integration
log_info "Testing integration with Sophia platform..."
python3 sophia_integration.py

echo ""
log_success "🚀 Enhanced Secret Management Dashboard is ready for production use!"

