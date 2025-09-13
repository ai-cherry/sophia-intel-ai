#!/bin/bash

# Fix Naming Convention Script
# Renames sophia-intel-app to sophia-intel-app and updates all references

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     FIXING NAMING CONVENTION                        ║${NC}"
echo -e "${BLUE}║     sophia-intel-app → sophia-intel-app                     ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# Get repository root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Step 1: Check if sophia-intel-app exists
if [ -d "sophia-intel-app" ]; then
    echo -e "${YELLOW}Step 1: Renaming sophia-intel-app directory to sophia-intel-app...${NC}"
    mv sophia-intel-app sophia-intel-app
    echo -e "${GREEN}✓ Directory renamed${NC}"
else
    echo -e "${YELLOW}Note: sophia-intel-app directory not found, checking for sophia-intel-app...${NC}"
    if [ -d "sophia-intel-app" ]; then
        echo -e "${GREEN}✓ sophia-intel-app already exists${NC}"
    else
        echo -e "${RED}✗ Neither sophia-intel-app nor sophia-intel-app found${NC}"
        exit 1
    fi
fi

# Step 2: Update package.json
if [ -f "sophia-intel-app/package.json" ]; then
    echo -e "${YELLOW}Step 2: Updating package.json...${NC}"
    sed -i.bak 's/"name": "sophia-intel-app"/"name": "sophia-intel-app"/g' sophia-intel-app/package.json
    rm sophia-intel-app/package.json.bak 2>/dev/null || true
    echo -e "${GREEN}✓ package.json updated${NC}"
fi

# Step 3: Update TypeScript/JavaScript imports
echo -e "${YELLOW}Step 3: Updating imports in TypeScript/JavaScript files...${NC}"
find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) \
    -not -path "*/node_modules/*" \
    -not -path "*/.git/*" \
    -exec sed -i.bak 's/sophia-intel-app/sophia-intel-app/g' {} \; \
    -exec rm {}.bak \; 2>/dev/null || true
echo -e "${GREEN}✓ Imports updated${NC}"

# Step 4: Update Markdown files
echo -e "${YELLOW}Step 4: Updating documentation...${NC}"
find . -type f -name "*.md" \
    -not -path "*/node_modules/*" \
    -not -path "*/.git/*" \
    -exec sed -i.bak 's/sophia-intel-app/sophia-intel-app/g' {} \; \
    -exec rm {}.bak \; 2>/dev/null || true
echo -e "${GREEN}✓ Documentation updated${NC}"

# Step 5: Update environment files
echo -e "${YELLOW}Step 5: Updating environment variables...${NC}"
for env_file in .env .env.example .env.local .env.development .env.production; do
    if [ -f "$env_file" ]; then
        sed -i.bak 's/AGENT_UI/SOPHIA_INTEL_APP/g' "$env_file"
        sed -i.bak 's/sophia-intel-app/sophia-intel-app/g' "$env_file"
        rm "${env_file}.bak" 2>/dev/null || true
        echo -e "  Updated: $env_file"
    fi
done
echo -e "${GREEN}✓ Environment files updated${NC}"

# Step 6: Update Docker files
echo -e "${YELLOW}Step 6: Updating Docker configurations...${NC}"
for docker_file in Dockerfile docker-compose.yml docker-compose.*.yml; do
    if [ -f "$docker_file" ]; then
        sed -i.bak 's/sophia-intel-app/sophia-intel-app/g' "$docker_file"
        rm "${docker_file}.bak" 2>/dev/null || true
        echo -e "  Updated: $docker_file"
    fi
done

# Check infra directory
if [ -d "infra" ]; then
    find infra -type f \( -name "Dockerfile*" -o -name "docker-compose*.yml" \) \
        -exec sed -i.bak 's/sophia-intel-app/sophia-intel-app/g' {} \; \
        -exec rm {}.bak \; 2>/dev/null || true
fi
echo -e "${GREEN}✓ Docker configurations updated${NC}"

# Step 7: Update shell scripts
echo -e "${YELLOW}Step 7: Updating shell scripts...${NC}"
find . -type f -name "*.sh" \
    -not -path "*/node_modules/*" \
    -not -path "*/.git/*" \
    -exec sed -i.bak 's/sophia-intel-app/sophia-intel-app/g' {} \; \
    -exec rm {}.bak \; 2>/dev/null || true
echo -e "${GREEN}✓ Shell scripts updated${NC}"

# Step 8: Update Python files
echo -e "${YELLOW}Step 8: Updating Python files...${NC}"
find . -type f -name "*.py" \
    -not -path "*/node_modules/*" \
    -not -path "*/.git/*" \
    -not -path "*/__pycache__/*" \
    -exec sed -i.bak 's/sophia-intel-app/sophia-intel-app/g' {} \; \
    -exec rm {}.bak \; 2>/dev/null || true
echo -e "${GREEN}✓ Python files updated${NC}"

# Step 9: Update Makefile
if [ -f "Makefile" ]; then
    echo -e "${YELLOW}Step 9: Updating Makefile...${NC}"
    sed -i.bak 's/sophia-intel-app/sophia-intel-app/g' Makefile
    rm Makefile.bak 2>/dev/null || true
    echo -e "${GREEN}✓ Makefile updated${NC}"
fi

# Step 10: Create proper app structure
echo -e "${YELLOW}Step 10: Ensuring proper app structure...${NC}"

# Create apps directory if it doesn't exist
mkdir -p apps

# Create proper directories for all three apps
mkdir -p apps/sophia-intel-app
mkdir -p apps/agno-builder-app
mkdir -p apps/litellm-builder-app

# If sophia-intel-app exists in root, suggest moving it
if [ -d "sophia-intel-app" ] && [ ! -L "sophia-intel-app" ]; then
    echo -e "${YELLOW}  Note: sophia-intel-app exists in root. Consider moving to apps/sophia-intel-app${NC}"
    echo -e "${YELLOW}  Command: mv sophia-intel-app apps/${NC}"
fi

echo -e "${GREEN}✓ App structure verified${NC}"

# Summary
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                  NAMING FIXED!                       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ All references to 'sophia-intel-app' have been updated to 'sophia-intel-app'${NC}"
echo ""
echo -e "${BLUE}Correct naming convention:${NC}"
echo "  • sophia-intel-app  - Business Intelligence Dashboard (Port 3000)"
echo "  • agno-builder-app  - AI Agent Development Platform (Port 3001)"
echo "  • litellm-builder-app - Intelligent Routing System (Port 8090)"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. If sophia-intel-app is in root, move it: mv sophia-intel-app apps/"
echo "  2. Update any CI/CD pipelines that reference sophia-intel-app"
echo "  3. Clear browser cache if accessing the UI"
echo "  4. Rebuild Docker images if using containers"
echo "  5. Run: npm install in sophia-intel-app/"
echo ""
echo -e "${GREEN}Naming convention successfully fixed!${NC}"