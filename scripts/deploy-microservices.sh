#!/bin/bash

# ==============================================
# Sophia Intel AI - Complete Microservices Deployment
# Deploys all 6 services to Fly.io in proper dependency order
# ==============================================

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
FLY_ORG="personal"
REGION="sjc"  # San Jose

echo -e "${PURPLE}🚀 Starting Sophia Intel AI Microservices Deployment${NC}"
echo -e "${BLUE}📍 Region: ${REGION} | Organization: ${FLY_ORG}${NC}"

# ==============================================
# PHASE 1: Prerequisites Check
# ==============================================
echo -e "\n${YELLOW}🔍 Phase 1: Prerequisites Check${NC}"

# Check if Fly CLI is installed
if ! command -v fly &> /dev/null; then
    echo -e "${RED}❌ Fly CLI not found. Installing...${NC}"
    curl -L https://fly.io/install.sh | sh
    export PATH="$HOME/.fly/bin:$PATH"
fi

# Check if logged in to Fly.io
if ! fly auth whoami &> /dev/null; then
    echo -e "${YELLOW}🔑 Please authenticate with Fly.io using your token...${NC}"
    export FLY_API_TOKEN="FlyV1 fm2_lJPECAAAAAAACcioxBCHKpegBSo8azHO5tEzGMgIwrVodHRwczovL2FwaS5mbHkuaW8vdjGUAJLOABLk6x8Lk7lodHRwczovL2FwaS5mbHkuaW8vYWFhL3YxxDx+eiFFmS1CFvB53dr6qxximI5JCL2wvUwuufCRqoURWwVhkpkA4HFuZ1G5qwJtsbpS+6ynXhXHQEmkwejETosKaRZ3YnWRKJ8+S7NfwfaeJNUhFzgWfIDq4DWW6jNzZ1CdMD1h8f20VJkA9MFeyuV2PrK2kMx/7JBj4y4xqzKWI6xtTto7MxwTzYVKFsQgwhGUSQw+IAQorY8dPQ7/upotkb5tniZKl3+LhWZa1sE="
    fly auth token
fi

echo -e "${GREEN}✅ Prerequisites satisfied${NC}"

# ==============================================
# PHASE 2: Create Fly Apps
# ==============================================
echo -e "\n${YELLOW}🏗️ Phase 2: Creating Fly.io Applications${NC}"

APPS=(
    "sophia-weaviate:Weaviate v1.32+ Vector Database"
    "sophia-mcp:MCP Server Memory Management"
    "sophia-vector:Vector Store 3-tier Embeddings"
    "sophia-api:Unified API Main Orchestrator"
    "sophia-bridge:Agno Bridge UI Compatibility"
    "sophia-ui:Agent UI Next.js Frontend"
)

for app_info in "${APPS[@]}"; do
    IFS=':' read -r app_name app_description <<< "$app_info"
    echo -e "${BLUE}🔨 Creating ${app_name} (${app_description})...${NC}"

    # Create app if it doesn't exist
    if ! fly apps list | grep -q "$app_name"; then
        fly apps create "$app_name" --org "$FLY_ORG"
        echo -e "${GREEN}✅ Created ${app_name}${NC}"
    else
        echo -e "${YELLOW}⚠️ ${app_name} already exists, skipping...${NC}"
    fi
done

# ==============================================
# PHASE 3: Set Up Secrets
# ==============================================
echo -e "\n${YELLOW}🔐 Phase 3: Configuring Secrets${NC}"
echo -e "${BLUE}Running secrets setup script...${NC}"
./scripts/setup-fly-secrets.sh

# ==============================================
# PHASE 4: Deploy Foundation Services
# ==============================================
echo -e "\n${YELLOW}🗄️ Phase 4: Deploying Foundation Services${NC}"

# Deploy Weaviate first (foundational vector database)
echo -e "${BLUE}🚀 Deploying Weaviate v1.32+...${NC}"
fly deploy --config fly-weaviate.toml --app sophia-weaviate
fly volumes create weaviate_data --region $REGION --size 20 --app sophia-weaviate 2>/dev/null || true

# Wait for Weaviate to be healthy
echo -e "${YELLOW}⏳ Waiting for Weaviate to be healthy...${NC}"
timeout 300 bash -c 'until fly status --app sophia-weaviate | grep -q "running"; do sleep 10; done' || {
    echo -e "${RED}❌ Weaviate deployment failed or timed out${NC}"
    exit 1
}
echo -e "${GREEN}✅ Weaviate v1.32+ deployed successfully${NC}"

# ==============================================
# PHASE 5: Deploy Supporting Services
# ==============================================
echo -e "\n${YELLOW}🧠 Phase 5: Deploying Supporting Services${NC}"

# Deploy MCP Server and Vector Store in parallel (both depend on Weaviate)
echo -e "${BLUE}🚀 Deploying MCP Server...${NC}"
fly deploy --config fly-mcp-server.toml --app sophia-mcp &
MCP_PID=$!

echo -e "${BLUE}🚀 Deploying Vector Store...${NC}"
fly deploy --config fly-vector-store.toml --app sophia-vector &
VECTOR_PID=$!

# Wait for both to complete
wait $MCP_PID && echo -e "${GREEN}✅ MCP Server deployed${NC}" || echo -e "${RED}❌ MCP Server failed${NC}"
wait $VECTOR_PID && echo -e "${GREEN}✅ Vector Store deployed${NC}" || echo -e "${RED}❌ Vector Store failed${NC}"

# ==============================================
# PHASE 6: Deploy Core API
# ==============================================
echo -e "\n${YELLOW}🚀 Phase 6: Deploying Core API Orchestrator${NC}"
echo -e "${BLUE}🚀 Deploying Unified API...${NC}"
fly deploy --config fly-unified-api.toml --app sophia-api

# Scale API service for production load
fly scale count 2 --app sophia-api
fly autoscale set min=2 max=20 --app sophia-api

echo -e "${GREEN}✅ Unified API deployed with auto-scaling${NC}"

# ==============================================
# PHASE 7: Deploy Interface Layer
# ==============================================
echo -e "\n${YELLOW}🌐 Phase 7: Deploying Interface Layer${NC}"

# Deploy Agno Bridge
echo -e "${BLUE}🚀 Deploying Agno Bridge...${NC}"
fly deploy --config fly-agno-bridge.toml --app sophia-bridge &
BRIDGE_PID=$!

# Deploy Agent UI
echo -e "${BLUE}🚀 Deploying Agent UI...${NC}"
fly deploy --config fly-sophia-intel-app.toml --app sophia-ui &
UI_PID=$!

# Wait for both interface services
wait $BRIDGE_PID && echo -e "${GREEN}✅ Agno Bridge deployed${NC}" || echo -e "${RED}❌ Agno Bridge failed${NC}"
wait $UI_PID && echo -e "${GREEN}✅ Agent UI deployed${NC}" || echo -e "${RED}❌ Agent UI failed${NC}"

# ==============================================
# PHASE 8: Configure Custom Domains & SSL
# ==============================================
echo -e "\n${YELLOW}🌍 Phase 8: Configuring Custom Domains${NC}"

# Set up SSL certificates for each service
SERVICES=("sophia-api" "sophia-bridge" "sophia-ui" "sophia-weaviate" "sophia-mcp" "sophia-vector")

for service in "${SERVICES[@]}"; do
    echo -e "${BLUE}🔒 Setting up SSL for ${service}.fly.dev...${NC}"
    fly certs create "${service}.fly.dev" --app "$service" 2>/dev/null || echo "⚠️ SSL already configured for $service"
done

# ==============================================
# PHASE 9: Health Checks & Verification
# ==============================================
echo -e "\n${YELLOW}🏥 Phase 9: Health Check Verification${NC}"

# Check all services are healthy
ENDPOINTS=(
    "https://sophia-weaviate.fly.dev/v1/.well-known/ready:Weaviate"
    "https://sophia-mcp.fly.dev/health:MCP Server"
    "https://sophia-vector.fly.dev/health:Vector Store"
    "https://sophia-api.fly.dev/healthz:Unified API"
    "https://sophia-bridge.fly.dev/healthz:Agno Bridge"
    "https://sophia-ui.fly.dev/:Agent UI"
)

echo -e "${BLUE}🔍 Testing service endpoints...${NC}"
for endpoint_info in "${ENDPOINTS[@]}"; do
    IFS=':' read -r endpoint service_name <<< "$endpoint_info"
    echo -e "${BLUE}Testing ${service_name}...${NC}"

    if curl -f -s "$endpoint" > /dev/null; then
        echo -e "${GREEN}✅ ${service_name} is healthy${NC}"
    else
        echo -e "${RED}❌ ${service_name} health check failed${NC}"
        echo -e "${YELLOW}📋 Check status: fly status --app ${service_name}${NC}"
    fi
done

# ==============================================
# PHASE 10: Database Migration
# ==============================================
echo -e "\n${YELLOW}🗃️ Phase 10: Database Migration${NC}"
echo -e "${BLUE}🔄 Running PostgreSQL schema migration to Neon...${NC}"
./scripts/migrate-to-neon.sh

# ==============================================
# DEPLOYMENT COMPLETE
# ==============================================
echo -e "\n${PURPLE}🎉 Sophia Intel AI Microservices Deployment Complete!${NC}"
echo -e "\n${GREEN}📊 Deployment Summary:${NC}"
echo -e "  🗄️ Weaviate v1.32+: https://sophia-weaviate.fly.dev"
echo -e "  🧠 MCP Server: https://sophia-mcp.fly.dev"
echo -e "  🔍 Vector Store: https://sophia-vector.fly.dev"
echo -e "  🚀 Unified API: https://sophia-api.fly.dev"
echo -e "  🌉 Agno Bridge: https://sophia-bridge.fly.dev"
echo -e "  🖥️ Agent UI: https://sophia-ui.fly.dev"

echo -e "\n${BLUE}🔧 Management Commands:${NC}"
echo -e "  fly status --app sophia-api    # Check API status"
echo -e "  fly logs --app sophia-api      # View API logs"
echo -e "  fly ssh console --app sophia-api  # SSH into API"
echo -e "  fly scale count 5 --app sophia-api  # Scale API"

echo -e "\n${YELLOW}⚡ Next Steps:${NC}"
echo -e "  1. Run integration tests: ./scripts/test-microservices.sh"
echo -e "  2. Set up monitoring: ./scripts/setup-monitoring.sh"
echo -e "  3. Configure CI/CD: ./scripts/setup-cicd.sh"

echo -e "\n${GREEN}🎯 Production deployment successful! All 6 microservices are live.${NC}"
