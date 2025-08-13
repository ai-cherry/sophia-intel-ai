#!/usr/bin/env bash
# Pulumi ESC Bootstrap Script for SOPHIA
# Sets up Environment Secret Control for secure cloud operations

set -e
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="$ROOT_DIR/.env.sophia"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for .env.sophia file
if [ ! -f "$ENV_FILE" ]; then
  echo -e "${RED}Error: .env.sophia file not found.${NC}"
  echo -e "Create one from .env.template with your secrets."
  exit 1
fi

# Source environment variables
source "$ENV_FILE"

# Check for required variables
for VAR in PULUMI_ESC_TOKEN PULUMI_ORG; do
  if [ -z "${!VAR}" ]; then
    echo -e "${RED}Error: $VAR is not set in .env.sophia${NC}"
    exit 1
  fi
done

echo -e "${GREEN}Configuring Pulumi ESC...${NC}"

# Install Pulumi CLI if not present
if ! command -v pulumi &> /dev/null; then
  echo -e "${YELLOW}Pulumi CLI not found. Installing...${NC}"
  curl -fsSL https://get.pulumi.com | sh
  export PATH=$PATH:$HOME/.pulumi/bin
fi

# Login to Pulumi
echo -e "${GREEN}Logging in to Pulumi...${NC}"
pulumi login

# Set up ESC
echo -e "${GREEN}Setting up Environment Secret Control...${NC}"
# Create organization ESC context
pulumi env context create org."$PULUMI_ORG" --description "SOPHIA ESC Context"

# Configure GitHub and AWS secrets
echo -e "${GREEN}Configuring GitHub secrets...${NC}"
pulumi env secret create org."$PULUMI_ORG"/github_token --value "$GH_API_TOKEN" --description "GitHub API Token"

# Grant read access to projects that need it
echo -e "${GREEN}Setting up access policies...${NC}"
pulumi env permission grant read org."$PULUMI_ORG"/github_token --project "$PULUMI_PROJECT" --description "Allow GitHub access from SOPHIA"

echo -e "${GREEN}ESC setup complete! Your environment is ready.${NC}"
echo -e "You can now use 'pulumi env open' to view your secrets in the Pulumi Cloud Console."
echo -e "In your Pulumi programs, reference secrets with: pulumi.getSecretOutput(\"github_token\")"
