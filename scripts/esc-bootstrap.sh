#!/bin/bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Pulumi ESC Bootstrap Script ===${NC}"
echo "This script will securely set up all secrets in Pulumi ESC"
echo ""

# Check prerequisites
REPO_OWNER="$(gh repo view --json owner -q .owner.login 2>/dev/null || echo '')"
REPO_NAME="$(gh repo view --json name -q .name 2>/dev/null || echo '')"

if [ -z "$REPO_OWNER" ] || [ -z "$REPO_NAME" ]; then 
  echo -e "${RED}❌ GitHub CLI not authenticated or not in a repo${NC}"
  echo "Please run: gh auth login"
  exit 1
fi

echo -e "${GREEN}✅ Repo: $REPO_OWNER/$REPO_NAME${NC}"

# Install Pulumi ESC if needed
if ! command -v esc &> /dev/null; then
    echo -e "${YELLOW}Installing Pulumi ESC CLI...${NC}"
    curl -fsSL https://get.pulumi.com/esc/install.sh | sh
    export PATH=$PATH:$HOME/.pulumi/bin
fi

# Function to safely read secrets
read_secret() {
    local var_name=$1
    local prompt=$2
    local value=""
    
    echo -n "$prompt: "
    read -rs value
    echo ""
    
    if [ -z "$value" ]; then
        echo -e "${YELLOW}⚠️  Skipping $var_name (no value provided)${NC}"
        return 1
    fi
    
    eval "$var_name='$value'"
    return 0
}

echo -e "${GREEN}Step 1: Collect secrets securely${NC}"
echo "Enter your secrets (they will not be displayed):"
echo ""

# Collect GitHub PAT for repo secret management
read_secret TEMP_GH_PAT "GitHub PAT (with repo secret permissions)"

# Collect Pulumi token
read_secret PULUMI_ACCESS_TOKEN "PULUMI_ACCESS_TOKEN"

# Login to Pulumi
echo -e "${GREEN}Step 2: Logging into Pulumi...${NC}"
export PULUMI_ACCESS_TOKEN
pulumi login

# Create or update ESC environment
echo -e "${GREEN}Step 3: Setting up Pulumi ESC environment sophia/dev...${NC}"

# Create the environment if it doesn't exist
esc env init sophia/dev 2>/dev/null || echo "Environment already exists"

# Set all the secrets provided by the user
echo -e "${GREEN}Setting secrets in ESC...${NC}"

# Read additional secrets
read_secret QDRANT_URL "QDRANT_URL"
read_secret QDRANT_API_KEY "QDRANT_API_KEY"
read_secret GITHUB_PAT "GitHub PAT (optional, or use GH_FINE_GRAINED_TOKEN)"
read_secret OPENROUTER_API_KEY "OPENROUTER_API_KEY (or another LLM key)"

# Critical secrets
[ -n "${PULUMI_ACCESS_TOKEN:-}" ] && esc env set sophia/dev environmentVariables.PULUMI_ACCESS_TOKEN "$PULUMI_ACCESS_TOKEN" --secret
[ -n "${QDRANT_URL:-}" ] && esc env set sophia/dev environmentVariables.QDRANT_URL "$QDRANT_URL" --secret
[ -n "${QDRANT_API_KEY:-}" ] && esc env set sophia/dev environmentVariables.QDRANT_API_KEY "$QDRANT_API_KEY" --secret

# GitHub tokens
[ -n "${GH_FINE_GRAINED_TOKEN:-}" ] && esc env set sophia/dev environmentVariables.GH_FINE_GRAINED_TOKEN "$GH_FINE_GRAINED_TOKEN" --secret
[ -n "${GITHUB_PAT:-}" ] && esc env set sophia/dev environmentVariables.GITHUB_PAT "$GITHUB_PAT" --secret

# LLM Keys - collect any that the user has
[ -n "${OPENROUTER_API_KEY:-}" ] && esc env set sophia/dev environmentVariables.OPENROUTER_API_KEY "$OPENROUTER_API_KEY" --secret
[ -n "${PORTKEY_API_KEY:-}" ] && esc env set sophia/dev environmentVariables.PORTKEY_API_KEY "$PORTKEY_API_KEY" --secret
[ -n "${ANTHROPIC_API_KEY:-}" ] && esc env set sophia/dev environmentVariables.ANTHROPIC_API_KEY "$ANTHROPIC_API_KEY" --secret
[ -n "${OPENAI_API_KEY:-}" ] && esc env set sophia/dev environmentVariables.OPENAI_API_KEY "$OPENAI_API_KEY" --secret
[ -n "${DEEPSEEK_API_KEY:-}" ] && esc env set sophia/dev environmentVariables.DEEPSEEK_API_KEY "$DEEPSEEK_API_KEY" --secret
[ -n "${GROQ_API_KEY:-}" ] && esc env set sophia/dev environmentVariables.GROQ_API_KEY "$GROQ_API_KEY" --secret
[ -n "${MISTRAL_API_KEY:-}" ] && esc env set sophia/dev environmentVariables.MISTRAL_API_KEY "$MISTRAL_API_KEY" --secret
[ -n "${HUGGINGFACE_API_TOKEN:-}" ] && esc env set sophia/dev environmentVariables.HUGGINGFACE_API_TOKEN "$HUGGINGFACE_API_TOKEN" --secret
[ -n "${AGNO_API_KEY:-}" ] && esc env set sophia/dev environmentVariables.AGNO_API_KEY "$AGNO_API_KEY" --secret
[ -n "${LLAMA_API_KEY:-}" ] && esc env set sophia/dev environmentVariables.LLAMA_API_KEY "$LLAMA_API_KEY" --secret

# Optional services
[ -n "${LAMBDA_CLOUD_API_KEY:-}" ] && esc env set sophia/dev environmentVariables.LAMBDA_CLOUD_API_KEY "$LAMBDA_CLOUD_API_KEY" --secret
[ -n "${TAVILY_API_KEY:-}" ] && esc env set sophia/dev environmentVariables.TAVILY_API_KEY "$TAVILY_API_KEY" --secret
[ -n "${SERPER_API_KEY:-}" ] && esc env set sophia/dev environmentVariables.SERPER_API_KEY "$SERPER_API_KEY" --secret
[ -n "${PERPLEXITY_API_KEY:-}" ] && esc env set sophia/dev environmentVariables.PERPLEXITY_API_KEY "$PERPLEXITY_API_KEY" --secret

echo -e "${GREEN}Step 4: Creating read-only ESC service token...${NC}"
# Create a read-only service token
ESC_TOKEN_VAL=$(esc tokens create --name sophia-dev-ro --description "Read-only token for sophia/dev environment" 2>/dev/null || esc tokens list --json | jq -r '.[] | select(.name=="sophia-dev-ro") | .token')

if [ -z "$ESC_TOKEN_VAL" ]; then
    echo -e "${RED}❌ Failed to create/retrieve ESC token${NC}"
    exit 1
fi

echo -e "${GREEN}Step 5: Setting repo-level secrets...${NC}"
# Login to GitHub with the PAT
echo "$TEMP_GH_PAT" | gh auth login --with-token

# Set repo secrets for Actions and Codespaces
gh secret set ESC_ENV --repo "$REPO_OWNER/$REPO_NAME" --app actions --body "sophia/dev"
gh secret set ESC_TOKEN --repo "$REPO_OWNER/$REPO_NAME" --app actions --body "$ESC_TOKEN_VAL"
gh secret set ESC_ENV --repo "$REPO_OWNER/$REPO_NAME" --app codespaces --body "sophia/dev"
gh secret set ESC_TOKEN --repo "$REPO_OWNER/$REPO_NAME" --app codespaces --body "$ESC_TOKEN_VAL"

echo -e "${GREEN}Step 6: Verifying setup...${NC}"
# List secrets (names only)
echo "Repository secrets:"
gh secret list --repo "$REPO_OWNER/$REPO_NAME"

# Verify ESC environment
echo ""
echo "ESC environment keys:"
esc env get sophia/dev --format json 2>/dev/null | jq -r '.environmentVariables | keys[]' | head -20

echo -e "${GREEN}Step 7: Cleaning up...${NC}"
# Logout and clean up
gh auth logout -h github.com -y 2>/dev/null || true
unset TEMP_GH_PAT PULUMI_ACCESS_TOKEN ESC_TOKEN_VAL
history -c 2>/dev/null || true
history -w 2>/dev/null || true

echo ""
echo -e "${GREEN}✅ ESC Bootstrap Complete!${NC}"
echo ""
echo "Next steps:"
echo "1. The code will be updated to use ESC automatically"
echo "2. Restart your Codespace to load the new secrets"
echo "3. Revoke your temporary GitHub PAT in GitHub Settings"
echo ""
echo "Repository now uses only ESC_ENV and ESC_TOKEN for all secrets!"