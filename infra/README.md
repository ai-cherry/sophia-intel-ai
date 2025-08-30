# Pulumi Infrastructure for slim-agno

This directory contains the Pulumi infrastructure configuration for the slim-agno project.

## Setup

### 1. Prerequisites

- Pulumi CLI installed (`brew install pulumi/tap/pulumi`)
- Pulumi Personal Access Token (PAT) from https://app.pulumi.com/account/tokens

### 2. Initialize Pulumi

```bash
# Set your PAT
export PULUMI_ACCESS_TOKEN="pul-your-token-here"

# Run the setup script
./setup_pulumi.sh
```

### 3. Configure Secrets

After running the setup script, add your Portkey Virtual Keys:

```bash
# Set Portkey VKs as secrets
pulumi config set --secret portkeyOpenRouterVK "pk-live-your-openrouter-vk"
pulumi config set --secret portkeyTogetherVK "pk-live-your-together-vk"
```

### 4. Deploy Configuration

```bash
# Preview changes
pulumi preview

# Apply configuration
pulumi up --yes
```

## Stack Management

### Current Stack: dev

To create additional stacks:

```bash
# Create staging stack
pulumi stack init staging
pulumi config set weaviateUrl "http://staging-weaviate:8080"
# ... set other configs

# Create production stack
pulumi stack init prod
pulumi config set weaviateUrl "https://prod-weaviate.example.com"
# ... set other configs
```

### Switch Between Stacks

```bash
pulumi stack select dev
pulumi stack select staging
pulumi stack select prod
```

## Configuration Values

| Key | Description | Secret |
|-----|-------------|--------|
| `weaviateUrl` | Weaviate instance URL | No |
| `openaiBaseUrl` | Portkey gateway URL for chat | No |
| `embedBaseUrl` | Portkey gateway URL for embeddings | No |
| `portkeyOpenRouterVK` | Portkey Virtual Key for OpenRouter | Yes |
| `portkeyTogetherVK` | Portkey Virtual Key for Together AI | Yes |
| `environment` | Environment name (dev/staging/prod) | No |

## Future Additions

This Pulumi project will eventually manage:

- Fly.io applications and machines
- Neon PostgreSQL databases
- Redis instances
- Weaviate cloud deployments
- Lambda Labs GPU instances (via custom resources)

For now, it serves as a secure configuration store for the local-first development environment.