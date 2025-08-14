#!/usr/bin/env bash
# Roo Reset & Troubleshooter Script
# Use this when experiencing 401 authentication errors with Roo

set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Roo Reset & Troubleshooter ===${NC}"
echo

# Check for Roo extension
echo -e "${YELLOW}Checking Roo extension...${NC}"
if code --list-extensions | grep -q "rooveterinaryinc.roo-cline"; then
  echo -e "${GREEN}✓ Roo extension is installed${NC}"
else
  echo -e "${RED}❌ Roo extension not found!${NC}"
  echo -e "   Please install the Roo extension from VS Code marketplace"
  echo -e "   Extension ID: rooveterinaryinc.roo-cline"
  exit 1
fi

# Check .roomodes file
echo -e "\n${YELLOW}Checking .roomodes file...${NC}"
if [ -f .roomodes ]; then
  MODE_COUNT=$(grep -c "slug:" .roomodes || echo "0")
  echo -e "${GREEN}✓ .roomodes file exists with ${MODE_COUNT} modes${NC}"
else
  echo -e "${RED}❌ .roomodes file missing!${NC}"
  exit 1
fi

# Check for MCP configuration
echo -e "\n${YELLOW}Checking MCP configuration...${NC}"
if [ -f .vscode/mcp.json ]; then
  echo -e "${GREEN}✓ .vscode/mcp.json exists${NC}"
else
  echo -e "${RED}❌ .vscode/mcp.json is missing!${NC}"
  exit 1
fi

# Check MCP server health
echo -e "\n${YELLOW}Checking MCP server health...${NC}"
if python mcp/code_context/server.py --health | grep -q "healthy"; then
  echo -e "${GREEN}✓ Code context MCP server is healthy${NC}"
else
  echo -e "${RED}❌ Code context MCP server failed health check${NC}"
  exit 1
fi

# Clean up potential cached/corrupted state
echo -e "\n${YELLOW}Cleaning up potential cached state...${NC}"

# Create a directory for VS Code's cache directories
mkdir -p ~/.roo-troubleshoot

# Check for .roo directory and back it up
if [ -d .roo ]; then
  echo "Backing up .roo directory to ~/.roo-troubleshoot/"
  cp -r .roo ~/.roo-troubleshoot/roo-backup-$(date +%Y%m%d%H%M%S)
  echo "Removing .roo directory"
  rm -rf .roo
fi

# Remove potential VS Code state files that might be causing issues
ROO_CACHE_DIR=~/.config/Code/User/globalStorage/rooveterinaryinc.roo-cline
if [ -d "$ROO_CACHE_DIR" ]; then
  echo "Backing up Roo VS Code state"
  cp -r "$ROO_CACHE_DIR" ~/.roo-troubleshoot/roo-vscode-state-$(date +%Y%m%d%H%M%S)
  echo "Cleaning Roo VS Code state"
  rm -rf "$ROO_CACHE_DIR"/*
fi

# Check for Codespaces-specific paths
CODESPACES_PATHS=(
  ~/.vscode-remote/data/User/globalStorage/rooveterinaryinc.roo-cline
  ~/.vscode-remote/extensions/rooveterinaryinc.roo-cline*/data
  ~/vscode-remote/data/User/globalStorage/rooveterinaryinc.roo-cline
)

for CODESPACES_ROO_DIR in "${CODESPACES_PATHS[@]}"; do
  if [ -d "$CODESPACES_ROO_DIR" ]; then
    echo "Found Codespaces Roo state at: $CODESPACES_ROO_DIR"
    echo "Backing up Codespaces Roo state"
    cp -r "$CODESPACES_ROO_DIR" ~/.roo-troubleshoot/roo-codespaces-state-$(date +%Y%m%d%H%M%S) 2>/dev/null || true
    echo "Cleaning Codespaces Roo state"
    rm -rf "$CODESPACES_ROO_DIR"/* 2>/dev/null || true
  fi
done

# Check for GitHub authentication files that might be causing issues
GITHUB_AUTH_PATHS=(
  ~/.vscode-remote/data/User/globalStorage/github.vscode-pull-request-github
  ~/.vscode-remote/data/User/globalStorage/github.copilot
  ~/.vscode-remote/data/User/globalStorage/github.copilot-chat
)

for AUTH_PATH in "${GITHUB_AUTH_PATHS[@]}"; do
  if [ -d "$AUTH_PATH" ]; then
    echo "Found GitHub auth state at: $AUTH_PATH"
    echo "Backing up GitHub auth state"
    cp -r "$AUTH_PATH" ~/.roo-troubleshoot/github-auth-state-$(date +%Y%m%d%H%M%S) 2>/dev/null || true
    echo "Cleaning GitHub auth state"
    rm -rf "$AUTH_PATH"/auth*.json 2>/dev/null || true
    rm -rf "$AUTH_PATH"/token*.json 2>/dev/null || true
    rm -rf "$AUTH_PATH"/session*.json 2>/dev/null || true
  fi
done

echo -e "\n${GREEN}Cleanup complete!${NC}"

# Check if we're in a Codespace
if [ "${CODESPACES:-false}" = "true" ]; then
  echo -e "\n${YELLOW}Codespace-specific instructions:${NC}"
  echo -e "1. ${BLUE}Run the command${NC}: kill -9 \$(pgrep code-server)"
  echo -e "   This will restart the VS Code server"
  echo -e "2. ${BLUE}Wait for the Codespace to reconnect${NC} (page will reload)"
  echo -e "3. ${BLUE}Sign in to GitHub Copilot${NC} if prompted"
  echo -e "4. ${BLUE}Open the Roo sidebar${NC} and click 'Project Prompts'"
else
  echo -e "\n${YELLOW}Please follow these steps:${NC}"
  echo -e "1. ${BLUE}Close and reopen VS Code${NC} (or reload the window with Ctrl+Shift+P > 'Reload Window')"
  echo -e "2. ${BLUE}Sign in to GitHub Copilot${NC} if prompted"
  echo -e "3. ${BLUE}Open the Roo sidebar${NC}"
  echo -e "4. ${BLUE}Click on 'Project Prompts'${NC} and select a mode from the dropdown"
fi
echo
echo -e "${YELLOW}If you're still experiencing issues:${NC}"
echo -e "1. Check your GitHub Copilot subscription status"
echo -e "2. Make sure your GitHub account has access to Roo features"
echo -e "3. Try running in a fresh Codespace"
echo 
echo -e "${BLUE}For more information, see docs/roo_code_setup.md${NC}"
