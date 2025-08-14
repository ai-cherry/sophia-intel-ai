#!/usr/bin/env bash
# SOPHIA Roo Environment Check
# This script verifies that all required environment variables and tools
# are available for Roo Code integration with MCP servers.

echo "=== SOPHIA Roo Environment Check ==="
echo ""

if [ -f .env.sophia ]; then
  set -a
  . ./.env.sophia
  set +a
  echo "Loaded environment from .env.sophia"
fi

set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

EXIT_CODE=0

# Check for required environment variables
echo -e "${YELLOW}Checking for required environment variables...${NC}"
for v in LAMBDA_CLOUD_API_KEY GH_API_TOKEN; do
  if [ -z "${!v:-}" ]; then
    echo -e "${RED}❌ MISSING: $v${NC}"
    EXIT_CODE=1
  else
    echo -e "${GREEN}✓ $v is set${NC}"
  fi
done

echo -e "\n${YELLOW}Checking for required tools...${NC}"

# Check for ripgrep (optional)
if command -v rg &>/dev/null; then
  RG_VERSION=$(rg --version | head -n1)
  echo -e "${GREEN}✓ ripgrep${NC} (${RG_VERSION})"
else
  echo -e "${YELLOW}⚠ ripgrep not found${NC} (optional but recommended for better performance)"
fi

# Check for GitHub MCP
echo -e "\n${YELLOW}Checking for MCP servers...${NC}"
if npx --no-install @modelcontextprotocol/server-github --version &>/dev/null; then
  GITHUB_MCP_VERSION=$(npx --no-install @modelcontextprotocol/server-github --version)
  echo -e "${GREEN}✓ GitHub MCP${NC} (${GITHUB_MCP_VERSION})"
else
  echo -e "${RED}❌ GitHub MCP not installed${NC}"
  echo "   Run: npm i -g @modelcontextprotocol/server-github"
  EXIT_CODE=1
fi

# Check Code MCP
if [[ -x "mcp/code_context/server.py" ]]; then
  if python mcp/code_context/server.py --health | grep -q '"status": "healthy"'; then
    echo -e "${GREEN}✓ Code Context MCP${NC}"
  else
    echo -e "${RED}❌ Code Context MCP is unhealthy${NC}"
    EXIT_CODE=1
  fi
else
  echo -e "${RED}❌ Code Context MCP missing or not executable${NC}"
  echo "   Check mcp/code_context/server.py"
  EXIT_CODE=1
fi

# Check VS Code configuration
echo -e "\n${YELLOW}Checking VS Code configuration...${NC}"
if [[ -f .vscode/mcp.json ]]; then
  echo -e "${GREEN}✓ MCP configuration exists${NC}"
else
  echo -e "${RED}❌ MCP configuration missing${NC}"
  echo "   Create .vscode/mcp.json"
  EXIT_CODE=1
fi

# Check Roo modes with comprehensive validation
if [[ -f .roomodes ]]; then
  echo -e "${YELLOW}Validating .roomodes file...${NC}"
  if python3 scripts/validate_roomodes.py --json > /dev/null 2>&1; then
    MODE_COUNT=$(python3 scripts/validate_roomodes.py --json | jq -r '.modes' 2>/dev/null || grep -c "slug:" .roomodes)
    echo -e "${GREEN}✓ .roomodes file is valid${NC} (${MODE_COUNT} modes)"
  else
    echo -e "${RED}❌ .roomodes file validation failed${NC}"
    echo "   Run: python3 scripts/validate_roomodes.py for details"
    EXIT_CODE=1
  fi
else
  echo -e "${RED}❌ .roomodes file missing${NC}"
  EXIT_CODE=1
fi

echo ""
if [[ $EXIT_CODE -eq 0 ]]; then
  echo -e "${GREEN}All checks passed! Roo environment is ready.${NC}"
else
  echo -e "${RED}Some checks failed. See above for details.${NC}"
fi

exit $EXIT_CODE
