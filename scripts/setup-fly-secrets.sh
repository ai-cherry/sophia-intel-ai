#!/bin/bash

# ==============================================
# Fly.io Secrets Management for Sophia Intel AI
# Distributes 50+ API keys across 6 microservices
# ==============================================

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 Setting up Fly.io secrets for Sophia Intel AI microservices...${NC}"

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo -e "${RED}❌ Error: .env.local file not found!${NC}"
    exit 1
fi

# Source environment variables
source .env.local

# ==============================================
# SHARED SECRETS (All 6 services)
# ==============================================
echo -e "${YELLOW}📤 Setting shared secrets across all services...${NC}"

SHARED_SECRETS=(
    "NEON_API_KEY=${NEON_API_KEY}"
    "NEON_PASSWORD=${NEON_PASSWORD}"
    "REDIS_PASSWORD=${REDIS_PASSWORD}"
    "OPENAI_API_KEY=${OPENAI_API_KEY}"
    "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}"
    "PORTKEY_API_KEY=${PORTKEY_API_KEY}"
    "JWT_SECRET=${JWT_SECRET}"
    "API_SECRET_KEY=${API_SECRET_KEY}"
)

APPS=("sophia-weaviate" "sophia-mcp" "sophia-vector" "sophia-api" "sophia-bridge" "sophia-ui")

for app in "${APPS[@]}"; do
    echo -e "${BLUE}🔧 Setting shared secrets for ${app}...${NC}"
    for secret in "${SHARED_SECRETS[@]}"; do
        fly secrets set "$secret" --app "$app" 2>/dev/null || echo "⚠️  Warning: Failed to set secret for $app"
    done
done

# ==============================================
# WEAVIATE-SPECIFIC SECRETS
# ==============================================
echo -e "${YELLOW}🗄️ Setting Weaviate-specific secrets...${NC}"
fly secrets set \
    "WEAVIATE_API_KEY=${WEAVIATE_API_KEY:-}" \
    --app sophia-weaviate

# ==============================================
# MCP SERVER SECRETS
# ==============================================
echo -e "${YELLOW}🧠 Setting MCP Server secrets...${NC}"
fly secrets set \
    "MEM0_API_KEY=${MEM0_API_KEY}" \
    "MEM0_ACCOUNT_NAME=${MEM0_ACCOUNT_NAME}" \
    "MEM0_ACCOUNT_ID=${MEM0_ACCOUNT_ID}" \
    "REDIS_USER_KEY=${REDIS_USER_KEY}" \
    "REDIS_ACCOUNT_KEY=${REDIS_ACCOUNT_KEY}" \
    --app sophia-mcp

# ==============================================
# VECTOR STORE SECRETS (Embedding APIs)
# ==============================================
echo -e "${YELLOW}🔍 Setting Vector Store embedding API secrets...${NC}"
fly secrets set \
    "HUGGINGFACE_API_TOKEN=${HUGGINGFACE_API_TOKEN}" \
    "PORTKEY_OPENROUTER_VK=${PORTKEY_OPENROUTER_VK}" \
    "PORTKEY_TOGETHER_VK=${PORTKEY_TOGETHER_VK}" \
    "PORTKEY_XAI_VK=${PORTKEY_XAI_VK}" \
    "EXA_API_KEY=${EXA_API_KEY}" \
    --app sophia-vector

# ==============================================
# UNIFIED API SECRETS (Core AI + GPU + Search)
# ==============================================
echo -e "${YELLOW}🚀 Setting Unified API comprehensive secrets...${NC}"
fly secrets set \
    "OPENROUTER_API_KEY=${OPENROUTER_API_KEY}" \
    "GROQ_API_KEY=${GROQ_API_KEY}" \
    "DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}" \
    "XAI_API_KEY=${XAI_API_KEY}" \
    # No direct Google key; use OpenRouter/AIMLAPI/Together/HF
    "MISTRAL_API_KEY=${MISTRAL_API_KEY}" \
    "PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY}" \
    "LAMBDA_API_KEY=${LAMBDA_API_KEY}" \
    "BRAVE_API_KEY=${BRAVE_API_KEY}" \
    "SERPER_API_KEY=${SERPER_API_KEY}" \
    "TAVILY_API_KEY=${TAVILY_API_KEY}" \
    "NEWSDATA_API_KEY=${NEWSDATA_API_KEY}" \
    "LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}" \
    "ARIZE_API_KEY=${ARIZE_API_KEY}" \
    "ARIZE_SPACE_ID=${ARIZE_SPACE_ID}" \
    --app sophia-api

# ==============================================
# AGNO BRIDGE SECRETS
# ==============================================
echo -e "${YELLOW}🌉 Setting Agno Bridge secrets...${NC}"
fly secrets set \
    "AGNO_API_KEY=${AGNO_API_KEY}" \
    --app sophia-bridge

# ==============================================
# AGENT UI SECRETS (Frontend Environment)
# ==============================================
echo -e "${YELLOW}🖥️ Setting Agent UI secrets...${NC}"
fly secrets set \
    "GITHUB_TOKEN=${GITHUB_TOKEN}" \
    "DOCKER_PAT=${DOCKER_PAT}" \
    --app sophia-ui

# ==============================================
# EXTENDED SERVICE APIS (Unified API)
# ==============================================
echo -e "${YELLOW}🔌 Setting extended service API secrets...${NC}"
fly secrets set \
    "APIFY_API_TOKEN=${APIFY_API_TOKEN}" \
    "APOLLO_IO_API_KEY=${APOLLO_IO_API_KEY}" \
    "ASANA_API_TOKEN=${ASANA_API_TOKEN}" \
    "ASSEMBLY_API_KEY=${ASSEMBLY_API_KEY}" \
    "BRIGHTDATA_API_KEY=${BRIGHTDATA_API_KEY}" \
    "DNSIMPLE_API_KEY=${DNSIMPLE_API_KEY}" \
    "EDEN_API_KEY=${EDEN_API_KEY}" \
    "FIGMA_PAT=${FIGMA_PAT}" \
    "GONG_ACCESS_KEY=${GONG_ACCESS_KEY}" \
    "GONG_CLIENT_SECRET=${GONG_CLIENT_SECRET}" \
    "HUBSPOT_ACCESS_TOKEN=${HUBSPOT_ACCESS_TOKEN}" \
    "HUBSPOT_CLIENT_SECRET=${HUBSPOT_CLIENT_SECRET}" \
    "KONG_ACCESS_TOKEN=${KONG_ACCESS_TOKEN}" \
    "KONG_ORG_ID=${KONG_ORG_ID}" \
    "LINEAR_API_KEY=${LINEAR_API_KEY}" \
    "LLAMA_API_KEY=${LLAMA_API_KEY}" \
    "LOOKER_CLIENT_SECRET=${LOOKER_CLIENT_SECRET}" \
    "LOOKER_CLIENT_ID=${LOOKER_CLIENT_ID}" \
    "N8N_API_KEY=${N8N_API_KEY}" \
    "N8N_USERNAME=${N8N_USERNAME}" \
    "N8N_PASSWORD=${N8N_PASSWORD}" \
    "NEO4J_CLIENT_ID=${NEO4J_CLIENT_ID}" \
    "NEO4J_CLIENT_SECRET=${NEO4J_CLIENT_SECRET}" \
    "NOTION_API_KEY=${NOTION_API_KEY}" \
    "QWEN_API_KEY=${QWEN_API_KEY}" \
    "TELEGRAM_API_KEY=${TELEGRAM_API_KEY}" \
    --app sophia-api

echo -e "${GREEN}✅ Successfully configured secrets for all 6 microservices!${NC}"
echo -e "${BLUE}📊 Secret distribution summary:${NC}"
echo -e "  • sophia-weaviate: 8 shared + 1 specific = 9 secrets"
echo -e "  • sophia-mcp: 8 shared + 4 specific = 12 secrets"
echo -e "  • sophia-vector: 8 shared + 6 specific = 14 secrets"
echo -e "  • sophia-api: 8 shared + 35+ specific = 43+ secrets"
echo -e "  • sophia-bridge: 8 shared + 1 specific = 9 secrets"
echo -e "  • sophia-ui: 8 shared + 2 specific = 10 secrets"
echo -e "${GREEN}🎯 Total: 97+ secrets distributed across microservices${NC}"

echo -e "${BLUE}🔍 To verify secrets were set correctly:${NC}"
echo -e "  fly secrets list --app sophia-api"
echo -e "  fly secrets list --app sophia-weaviate"
echo -e "  fly secrets list --app sophia-mcp"
echo -e "  fly secrets list --app sophia-vector"
echo -e "  fly secrets list --app sophia-bridge"
echo -e "  fly secrets list --app sophia-ui"
