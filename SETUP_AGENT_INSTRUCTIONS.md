# Setup Instructions for Local Coding Agent

This document provides step-by-step instructions for setting up the slim-agno project with all necessary keys and configurations.

## Keys You Need to Provide

Please provide the following keys to complete the setup:

### Portkey Virtual Keys
1. **OpenRouter VK**: `pk-live-xxxxx` (for chat/LLM calls)
2. **Together AI VK**: `pk-live-xxxxx` (for embeddings)

### Pulumi Access Token
3. **Pulumi PAT**: `pul-xxxxx` (for infrastructure management)

## Setup Tasks

### Task 1: Configure Local Environment

```bash
# 1. Navigate to project root
cd /Users/lynnmusil/sophia-intel-ai

# 2. Update .env file with your keys
cat > .env <<EOF
# LLM gateway (Portkey → OpenRouter)
OPENAI_BASE_URL=https://api.portkey.ai/v1
OPENAI_API_KEY=<INSERT_OPENROUTER_VK_HERE>
HTTP_REFERER=http://localhost:3000
X_TITLE=slim-agno

# Embeddings (Portkey → Together AI)  
EMBED_BASE_URL=https://api.portkey.ai/v1
EMBED_API_KEY=<INSERT_TOGETHER_VK_HERE>
EMBED_MODEL=togethercomputer/m2-bert-80M-8k-retrieval

# Weaviate (local Docker)
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=
WEAVIATE_CLASS_CODE=CodeChunk
WEAVIATE_CLASS_DOC=DocChunk

# Playground
PLAYGROUND_PORT=7777
EOF
```

### Task 2: Start Weaviate

```bash
# Start Weaviate container
docker compose -f docker-compose.weaviate.yml up -d

# Verify Weaviate is running
curl -s http://localhost:8080/v1/meta | jq '.'
```

### Task 3: Install Python Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### Task 4: Set Up Pulumi (Infrastructure)

```bash
# Navigate to infra directory
cd infra

# Set Pulumi access token
export PULUMI_ACCESS_TOKEN="<INSERT_PULUMI_PAT_HERE>"

# Run setup script
./setup_pulumi.sh

# Set secret configurations
pulumi config set --secret portkeyOpenRouterVK "<INSERT_OPENROUTER_VK_HERE>"
pulumi config set --secret portkeyTogetherVK "<INSERT_TOGETHER_VK_HERE>"

# Preview configuration
pulumi preview

# Apply configuration
pulumi up --yes

# Return to project root
cd ..
```

### Task 5: Test Portkey Integration

```bash
# Activate virtual environment if not already active
source .venv/bin/activate

# Run smoke test
python test_portkey.py
```

### Task 6: Start Agno Playground

```bash
# Start the playground
python -m app.playground

# The playground will be available at http://localhost:7777
```

## Verification Checklist

After setup, verify:

- [ ] `.env` file contains both Portkey VKs
- [ ] Weaviate is running on port 8080
- [ ] Python dependencies are installed
- [ ] Pulumi stack is configured with secrets
- [ ] Smoke test passes (all green checkmarks)
- [ ] Agno Playground starts on port 7777

## Optional: Agno Agent UI

If you want to use the Agno Agent UI:

```bash
# In a new terminal
npx create-agent-ui@latest agent-ui
cd agent-ui
pnpm install
pnpm dev

# Configure endpoint to: http://localhost:7777
```

## Troubleshooting

### If Portkey tests fail:
- Check that both VKs are correctly set in `.env`
- Ensure VKs start with `pk-live-` or `pk_live_`
- Verify internet connection

### If Weaviate fails:
- Check Docker is running
- Ensure port 8080 is not in use
- Run `docker logs <container_id>` for errors

### If Pulumi fails:
- Verify PAT is correct
- Check you're logged into correct org (sophia-ai)
- Run `pulumi whoami` to verify

## Security Notes

- Never commit `.env` file (it's git-ignored)
- Store all secrets in Pulumi with `--secret` flag
- PAT and VKs should never appear in logs or commits