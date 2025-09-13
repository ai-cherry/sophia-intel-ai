#!/bin/bash

# Cleanup and Reorganize Script for Sophia Intel AI
# Removes deprecated squad systems and reorganizes project structure

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Sophia Intel AI - Cleanup & Reorganization        ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# Get the repository root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo -e "${YELLOW}Starting cleanup and reorganization...${NC}"
echo ""

# =====================================
# STEP 1: Remove OpenRouter Squad Files
# =====================================
echo -e "${YELLOW}1. Removing OpenRouter squad files...${NC}"

OPENROUTER_FILES=(
    "app/services/openrouter_server.py"
    "app/services/openrouter_squad_service.py"
    "config/openrouter_squad_config.yaml"
    "test_openrouter_squad.py"
)

for file in "${OPENROUTER_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "   Removing: $file"
        rm "$file"
    fi
done

echo -e "${GREEN}   ✓ OpenRouter files removed${NC}"
echo ""

# =====================================
# STEP 2: Remove AIMLAPI Squad Files (Keep Enhanced Router)
# =====================================
echo -e "${YELLOW}2. Removing AIMLAPI squad files (keeping enhanced router)...${NC}"

AIMLAPI_FILES=(
    "config/aimlapi_squad_config.yaml"
    "test_aimlapi_squad.py"
    "app/services/aimlapi_squad_service.py"
)

for file in "${AIMLAPI_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "   Removing: $file"
        rm "$file"
    fi
done

echo -e "${GREEN}   ✓ AIMLAPI squad files removed${NC}"
echo ""

# =====================================
# STEP 3: Create New Directory Structure
# =====================================
echo -e "${YELLOW}3. Creating organized directory structure...${NC}"

# Create main app directories
mkdir -p apps/sophia-intel-app
mkdir -p apps/agno-builder-app
mkdir -p apps/litellm-builder-app

# Create service directories
mkdir -p services/unified-api
mkdir -p services/mcp-servers
mkdir -p services/litellm-router

# Create shared libraries
mkdir -p libs/shared-components
mkdir -p libs/ai-agents
mkdir -p libs/research-tools

# Create config directories
mkdir -p config/environments
mkdir -p config/deployments
mkdir -p config/models

echo -e "${GREEN}   ✓ Directory structure created${NC}"
echo ""

# =====================================
# STEP 4: Move Files to New Structure
# =====================================
echo -e "${YELLOW}4. Reorganizing files...${NC}"

# Move Sophia Intel App files
if [ -d "sophia-intel-app" ]; then
    echo -e "   Moving Agent UI to sophia-intel-app..."
    cp -r sophia-intel-app/* apps/sophia-intel-app/ 2>/dev/null || true
fi

# Move LiteLLM files
if [ -f "app/services/litellm_coding_router.py" ]; then
    echo -e "   Moving LiteLLM router..."
    cp app/services/litellm_coding_router.py services/litellm-router/ 2>/dev/null || true
fi

# Move research swarm
if [ -f "app/services/research_swarm.py" ]; then
    echo -e "   Moving research swarm..."
    cp app/services/research_swarm.py libs/research-tools/ 2>/dev/null || true
fi

echo -e "${GREEN}   ✓ Files reorganized${NC}"
echo ""

# =====================================
# STEP 5: Update Configuration Files
# =====================================
echo -e "${YELLOW}5. Updating configuration files...${NC}"

# Update .env.example to remove deprecated services
if [ -f ".env.example" ]; then
    echo -e "   Cleaning .env.example..."
    # Remove OpenRouter and redundant AIMLAPI references
    sed -i.bak '/OPENROUTER_SQUAD/d' .env.example
    sed -i.bak '/AIMLAPI_SQUAD_PORT/d' .env.example
    rm .env.example.bak 2>/dev/null || true
fi

echo -e "${GREEN}   ✓ Configuration updated${NC}"
echo ""

# =====================================
# STEP 6: Create Project READMEs
# =====================================
echo -e "${YELLOW}6. Creating project documentation...${NC}"

# Sophia Intel App README
cat > apps/sophia-intel-app/README.md << 'EOF'
# Sophia Intel App

Production-ready B2B business intelligence platform.

## Features
- Real-time business analytics
- Slack, Asana, HubSpot, Gong integrations
- AI-powered insights
- Custom dashboards

## Tech Stack
- Frontend: React/Next.js
- Backend: FastAPI (Unified API)
- AI: LiteLLM Router
- Database: Neon PostgreSQL + Milvus

## Getting Started
```bash
npm install
npm run dev
```

Access at: http://localhost:3000
EOF

# Agno Builder App README
cat > apps/agno-builder-app/README.md << 'EOF'
# Agno Builder App

AI agent development platform with research capabilities.

## Features
- AI agent creation tools
- Research swarm with web scraping
- Code generation assistance
- Solution tracking in GitHub

## Tech Stack
- Frontend: React/Vite
- Backend: FastAPI
- AI: LiteLLM + Research Swarm
- Tools: Playwright, BeautifulSoup

## Getting Started
```bash
npm install
npm run dev
```

Access at: http://localhost:3001
EOF

# LiteLLM Builder App README
cat > apps/litellm-builder-app/README.md << 'EOF'
# LiteLLM Builder App

Intelligent AI routing system optimized for coding excellence.

## Features
- Cost-optimized model routing
- Specialized coding agents
- Task complexity analysis
- Automatic fallbacks

## Models
- Architecture: Claude Opus
- Implementation: DeepSeek Coder
- Debugging: OpenAI O1
- Documentation: Gemini Flash

## Getting Started
```bash
pip install -r requirements.txt
python setup.py
```

API at: http://localhost:8090
EOF

echo -e "${GREEN}   ✓ Documentation created${NC}"
echo ""

# =====================================
# STEP 7: Clean Up Old References
# =====================================
echo -e "${YELLOW}7. Cleaning up old references...${NC}"

# Find and report files with OpenRouter/AIMLAPI references
echo -e "   Searching for remaining references..."

REMAINING_REFS=$(grep -r "openrouter\|aimlapi" --include="*.py" --include="*.yaml" --include="*.md" . 2>/dev/null | grep -v "Binary file" | wc -l)

if [ "$REMAINING_REFS" -gt 0 ]; then
    echo -e "${YELLOW}   ⚠ Found $REMAINING_REFS remaining references to deprecated services${NC}"
    echo -e "${YELLOW}   Run 'grep -r \"openrouter\\|aimlapi\" .' to find them${NC}"
else
    echo -e "${GREEN}   ✓ No remaining references found${NC}"
fi

echo ""

# =====================================
# STEP 8: Create Launch Scripts
# =====================================
echo -e "${YELLOW}8. Creating unified launch scripts...${NC}"

# Create main launcher
cat > launch_sophia.sh << 'EOF'
#!/bin/bash
# Launch Sophia Intel AI Platform

# Source port configuration
source scripts/lib/ports.sh 2>/dev/null || true

echo "Launching Sophia Intel AI Platform..."

# Start services in order
echo "1. Starting MCP servers..."
python3 -m mcp.memory.server &
python3 -m mcp.filesystem.server &
python3 -m mcp.git.server &

echo "2. Starting LiteLLM router..."
cd services/litellm-router && python3 litellm_coding_router.py &

echo "3. Starting Unified API..."
python3 sophia_unified_server.py &

echo "4. Starting Sophia Intel App..."
cd apps/sophia-intel-app && npm run dev &

echo ""
echo "Services available at:"
echo "  - Sophia Intel App: http://localhost:3000"
echo "  - Unified API: http://localhost:8000"
echo "  - LiteLLM Router: http://localhost:8090"
echo "  - API Docs: http://localhost:8000/docs"
EOF

chmod +x launch_sophia.sh

echo -e "${GREEN}   ✓ Launch scripts created${NC}"
echo ""

# =====================================
# SUMMARY
# =====================================
echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                   CLEANUP COMPLETE                    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ Removed OpenRouter squad files${NC}"
echo -e "${GREEN}✓ Removed AIMLAPI squad files${NC}"
echo -e "${GREEN}✓ Created organized directory structure${NC}"
echo -e "${GREEN}✓ Moved files to new locations${NC}"
echo -e "${GREEN}✓ Updated configuration${NC}"
echo -e "${GREEN}✓ Created documentation${NC}"
echo -e "${GREEN}✓ Created launch scripts${NC}"
echo ""
echo -e "${BLUE}New Structure:${NC}"
echo "  apps/"
echo "    ├── sophia-intel-app/     # Business intelligence platform"
echo "    ├── agno-builder-app/     # AI agent builder"
echo "    └── litellm-builder-app/  # Coding AI system"
echo "  services/"
echo "    ├── unified-api/          # Main API"
echo "    ├── mcp-servers/          # Context servers"
echo "    └── litellm-router/       # AI routing"
echo "  libs/"
echo "    ├── shared-components/    # Shared UI"
echo "    ├── ai-agents/           # Agent implementations"
echo "    └── research-tools/      # Research swarm"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Review remaining references with: grep -r 'openrouter\\|aimlapi' ."
echo "  2. Test the new structure with: ./launch_sophia.sh"
echo "  3. Commit changes: git add . && git commit -m 'Reorganize project structure'"
echo ""
echo -e "${GREEN}Cleanup and reorganization complete!${NC}"