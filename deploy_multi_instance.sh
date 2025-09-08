#!/bin/bash
# 🎖️ Sophia AI Platform - Multi-Instance Deployment Script
# Generated on 2025-08-09 17:17:24

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Instance configurations
PRODUCTION_IP="104.171.202.103"
CORE_IP="192.222.58.232"
ORCHESTRATOR_IP="104.171.202.117"
PIPELINE_IP="104.171.202.134"
DEVELOPMENT_IP="155.248.194.183"

echo -e "${BLUE}🎖️ Sophia AI Platform - Multi-Instance Deployment${NC}"
echo "=================================================="

# Function to deploy to a single instance
deploy_to_instance() {
    local instance_name=$1
    local instance_ip=$2
    local services=$3
    
    echo -e "${YELLOW}📡 Deploying to $instance_name ($instance_ip)...${NC}"
    
    # Test connectivity
    if ! nc -z -w5 $instance_ip 22; then
        echo -e "${RED}❌ Cannot connect to $instance_name ($instance_ip)${NC}"
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
        echo -e "${GREEN}✅ Successfully deployed to $instance_name${NC}"
    else
        echo -e "${RED}❌ Failed to deploy to $instance_name${NC}"
    fi
}

# Deploy to all instances
echo -e "${BLUE}🚀 Starting multi-instance deployment...${NC}"

deploy_to_instance "Production" "$PRODUCTION_IP" "dashboard,api,monitoring"
deploy_to_instance "AI Core" "$CORE_IP" "inference,training"
deploy_to_instance "MCP Orchestrator" "$ORCHESTRATOR_IP" "mcp,orchestration"
deploy_to_instance "Data Pipeline" "$PIPELINE_IP" "data-processing,etl"
deploy_to_instance "Development" "$DEVELOPMENT_IP" "testing,development"

echo -e "${GREEN}🎉 Multi-instance deployment completed!${NC}"
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
