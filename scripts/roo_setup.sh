#!/usr/bin/env bash
# Roo Codespace Setup & Healthcheck
# This script is designed to run on Codespace startup

set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Roo Codespace Setup ===${NC}"

# Check for environment files
if [ -f .env.sophia ]; then
  source .env.sophia
  echo -e "${GREEN}✓ Loaded environment from .env.sophia${NC}"
fi

# Check MCP server health
echo -e "\n${YELLOW}Checking MCP server health...${NC}"
if python mcp/code_context/server.py --health | grep -q "healthy"; then
  echo -e "${GREEN}✓ Code context MCP server is healthy${NC}"
else
  echo -e "${RED}❌ Code context MCP server failed health check${NC}"
  echo -e "   Please check the server implementation or run scripts/roo_troubleshoot.sh"
fi

# Make sure scripts are executable
chmod +x scripts/mcp/healthcheck.sh scripts/start_all_mcps.sh scripts/stop_all_mcps.sh scripts/roo_troubleshoot.sh mcp/code_context/server.py

echo -e "\n${GREEN}✓ Roo setup complete!${NC}"
echo
echo -e "${YELLOW}If you encounter any issues with Roo:${NC}"
echo -e "1. Run ${BLUE}bash scripts/roo_troubleshoot.sh${NC} to reset Roo state"
echo -e "2. See ${BLUE}docs/roo_code_setup.md${NC} for detailed setup instructions"
echo -e "3. Make sure you have access to GitHub Copilot and Roo features"
echo
echo -e "${BLUE}Roo Modes Available:${NC}"
grep "slug:" .roomodes | sed 's/.*slug: //' | while read -r slug; do
  name=$(grep -A1 "slug: $slug" .roomodes | grep "name:" | sed 's/.*name: "\(.*\)"/\1/')
  echo -e "${YELLOW}• ${name}${NC}"
done
