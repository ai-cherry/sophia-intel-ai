# SOPHIA Continue.dev Environment Check
# This script verifies that all required environment variables and tools
# are available for Continue.dev integration with MCP servers.

echo "=== SOPHIA Continue.dev Environment Check ==="
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

# Check for required environment variables (warn if missing or empty)
check_env_var() {
  VAR_NAME=$1
  OPTIONAL=$2
  if [[ -z "${!VAR_NAME}" ]]; then
    if [[ "$OPTIONAL" == "optional" ]]; then
      echo -e "${YELLOW}⚠️  Optional: ${VAR_NAME} is not set${NC}"
    else
      echo -e "${RED}❌ Missing ${VAR_NAME}${NC}"
      echo "   Please set this environment variable in your Codespace or .env.sophia."
      EXIT_CODE=1
    fi
    return 1
  else
    MASKED_VALUE="${!VAR_NAME:0:4}...${!VAR_NAME: -4}"
    echo -e "${GREEN}✓ ${VAR_NAME} is set${NC} (${MASKED_VALUE})"
    return 0
  fi
}

# Check environment variables
echo "Environment Variables:"
check_env_var "CONTINUE_API_KEY"
check_env_var "GH_API_TOKEN"
check_env_var "PULUMI_ESC_TOKEN" optional
#!/bin/bash
# SOPHIA Continue.dev Environment Check
# This script verifies that all required environment variables and tools
# are available for Continue.dev integration with MCP servers.

set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== SOPHIA Continue.dev Environment Check ==="
echo ""

# Check for required environment variables
check_env_var() {
  VAR_NAME=$1
  ENV_FILE=".env.sophia"
  
  if [[ -z "${!VAR_NAME}" ]]; then
    # Check if it's in .env.sophia
    if [[ -f "$ENV_FILE" ]] && grep -q "^${VAR_NAME}=" "$ENV_FILE"; then
      echo -e "${YELLOW}⚠️ ${VAR_NAME} found in ${ENV_FILE} but not loaded${NC}"
      echo "   Run: source ${ENV_FILE}"
      EXIT_CODE=1
      return 1
    else
      echo -e "${RED}❌ Missing ${VAR_NAME}${NC}"
      echo "   Set in Codespace secrets or add to .env.sophia from template"
      EXIT_CODE=1
      return 1
    fi
  else
    LENGTH=${#VAR_NAME}
    MASKED_VALUE="${!VAR_NAME:0:4}...${!VAR_NAME: -4}"
    echo -e "${GREEN}✓ ${VAR_NAME} is set${NC} (${MASKED_VALUE})"
    return 0
  fi
}

# Check for required commands
check_command() {
  CMD=$1
  if ! command -v $CMD &> /dev/null; then
    echo -e "${RED}❌ Missing command: ${CMD}${NC}"
    echo "   Please install this command to use Continue.dev fully."
    EXIT_CODE=1
    return 1
  else
    VERSION=$($CMD --version 2>&1 | head -n1)
    echo -e "${GREEN}✓ ${CMD} is installed${NC} (${VERSION})"
    return 0
  fi
}

# Check for MCP servers
check_mcp_servers() {
  if ! check_command "npx"; then
    echo -e "${RED}❌ Cannot check MCP servers (npx not found)${NC}"
    return 1
  fi
  
  echo ""
  echo "MCP Server Status:"

  # Check GitHub MCP
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
    echo -e "${GREEN}✓ Code MCP${NC} (local)"
  else
    echo -e "${RED}❌ Code MCP script not executable${NC}"
    echo "   Run: chmod +x mcp/code_context/server.py"
    EXIT_CODE=1
  fi
}

# Check for .env.sophia file
check_env_file() {
  ENV_FILE=".env.sophia"
  if [[ -f "$ENV_FILE" ]]; then
    echo -e "${GREEN}✓ ${ENV_FILE} file exists${NC}"
    # Check if it's been sourced
    if grep -q "^CONTINUE_API_KEY=" "$ENV_FILE" && [[ -z "$CONTINUE_API_KEY" ]]; then
      echo -e "${YELLOW}⚠️ ${ENV_FILE} exists but hasn't been sourced${NC}"
      echo "   Run: source ${ENV_FILE}"
    fi
  else
    echo -e "${YELLOW}⚠️ ${ENV_FILE} not found${NC}"
    echo "   Create from .env.template: cp .env.template ${ENV_FILE}"
    echo "   Then add your secrets and run: source ${ENV_FILE}"
  fi
  echo ""
}

# Main checks
EXIT_CODE=0

# Check .env file
check_env_file

# Check environment variables
echo "Environment Variables:"
check_env_var "CONTINUE_API_KEY"
check_env_var "GH_API_TOKEN"
check_env_var "PULUMI_ESC_TOKEN" || echo -e "${YELLOW}⚠️ Optional: Set PULUMI_ESC_TOKEN for Pulumi ESC integration${NC}"

echo ""
echo "Required Tools:"
check_command "node"
check_command "npm"
check_command "npx"
check_command "python"
check_command "rg" || echo -e "${YELLOW}⚠️  ripgrep (rg) not found, but optional${NC}"

# Check MCP servers
check_mcp_servers

echo ""
if [[ $EXIT_CODE -eq 0 ]]; then
  echo -e "${GREEN}✓ All critical checks passed!${NC}"
  echo "   You can now use Continue.dev with MCP servers."
else
  echo -e "${RED}❌ Some checks failed.${NC}"
  echo "   Please address the issues above before using Continue.dev."
fi

exit $EXIT_CODE
