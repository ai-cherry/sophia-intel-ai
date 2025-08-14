# Secrets Management Contract

## Overview

This repository uses **Pulumi ESC (Environments, Secrets, and Configuration)** as the single source of truth for all secrets and sensitive configuration. This approach provides:

- **Centralized Management**: All secrets in one secure location
- **Audit Trail**: Full history of secret changes
- **Access Control**: Fine-grained permissions
- **Zero Trust**: No secrets stored in code or CI/CD config

## Architecture

```
┌─────────────────┐
│   Pulumi ESC    │ ← Single source of truth
│  sophia/dev     │
└────────┬────────┘
         │
    ┌────▼─────┐
    │ESC_TOKEN │ ← Read-only service token
    └────┬─────┘
         │
    ┌────▼─────────────────────┐
    │     Repository Secrets    │
    │  • ESC_ENV = sophia/dev   │
    │  • ESC_TOKEN = <token>    │
    └────┬──────────┬──────────┘
         │          │
    ┌────▼────┐ ┌──▼──────────┐
    │Codespaces│ │GitHub Actions│
    └─────────┘ └─────────────┘
```

## Configuration Loading Precedence

The `services/config_loader.py` module loads configuration with the following precedence:

1. **Pulumi ESC** (if ESC_ENV and ESC_TOKEN are set)
2. **Environment Variables** (overrides/supplements ESC values)
3. **Config Files** (fallback for local development)

## Required Repository Secrets

Only **TWO** secrets are stored at the repository level:

| Secret | Purpose | Scope |
|--------|---------|-------|
| `ESC_ENV` | ESC environment name (e.g., `sophia/dev`) | Actions + Codespaces |
| `ESC_TOKEN` | Read-only ESC service token | Actions + Codespaces |

## Secret Categories in ESC

### Critical Secrets (Required)
- `PULUMI_ACCESS_TOKEN` - Pulumi management
- `QDRANT_URL` - Vector database endpoint
- `QDRANT_API_KEY` - Vector database authentication
- GitHub token (one of):
  - `GH_FINE_GRAINED_TOKEN` (preferred)
  - `GITHUB_PAT` 

### LLM Provider Keys (At least one required)
- `OPENROUTER_API_KEY` - OpenRouter gateway
- `PORTKEY_API_KEY` - Portkey gateway
- `ANTHROPIC_API_KEY` - Claude models
- `OPENAI_API_KEY` - GPT models
- `DEEPSEEK_API_KEY` - DeepSeek models
- `GROQ_API_KEY` - Groq inference
- `MISTRAL_API_KEY` - Mistral models

### Optional Services
- `DATABASE_URL` - PostgreSQL connection
- `LAMBDA_CLOUD_API_KEY` - Lambda Labs compute
- `TAVILY_API_KEY` - Search API
- `SERPER_API_KEY` - Search API
- `PERPLEXITY_API_KEY` - Perplexity AI

## Secret Rotation Process

### 1. Update Secret in ESC
```bash
# Login to Pulumi
pulumi login

# Update the secret
esc env set sophia/dev environmentVariables.SECRET_NAME "new-value" --secret

# Verify
esc env get sophia/dev --format json | jq '.environmentVariables | keys'
```

### 2. Rotate ESC Token (if compromised)
```bash
# Create new token
NEW_TOKEN=$(esc tokens create --name sophia-dev-ro-new --description "Rotated token")

# Update repository secrets
gh secret set ESC_TOKEN --repo OWNER/REPO --app actions --body "$NEW_TOKEN"
gh secret set ESC_TOKEN --repo OWNER/REPO --app codespaces --body "$NEW_TOKEN"

# Delete old token
esc tokens delete sophia-dev-ro
```

### 3. Restart Services
- **Codespaces**: Restart the Codespace
- **GitHub Actions**: New runs will automatically use updated secrets

## Local Development

For local development without ESC access:

1. Copy `.env.example` to `.env`
2. Set required environment variables
3. The config loader will use environment variables as fallback

```bash
# Example .env file
export GH_FINE_GRAINED_TOKEN="your-token"
export QDRANT_URL="http://localhost:6333"
export QDRANT_API_KEY="your-key"
export OPENROUTER_API_KEY="your-key"
```

## Security Best Practices

1. **Never commit secrets** to the repository
2. **Use read-only tokens** for ESC access
3. **Rotate secrets regularly** (quarterly minimum)
4. **Audit access logs** in Pulumi dashboard
5. **Limit scope** of tokens to minimum required permissions

## Verification

Run the smoke check to verify configuration:

```bash
python tools/smoke_env_check.py
```

Expected output:
```
=== Sophia Configuration Smoke Check ===

--- ESC Configuration ---
✅ ESC_ENV: sophia/dev
✅ ESC_TOKEN: ***abcd

--- Config Loader Check ---
✅ GitHub Token: ***efgh
✅ Pulumi Token: ***ijkl
✅ Qdrant URL: ***mnop
✅ Qdrant API Key: ***qrst

--- Summary ---
✅ All checks passed! Configuration loaded from ESC
```

## Emergency Access

If ESC is unavailable:

1. Set environment variables directly in Codespace/CI
2. Config loader will fall back to environment variables
3. Fix ESC access as soon as possible
4. Run verification: `python tools/smoke_env_check.py`

## Support

For issues with secret management:
1. Check ESC dashboard: https://app.pulumi.com/
2. Verify repository secrets: `gh secret list --repo OWNER/REPO`
3. Run smoke check: `python tools/smoke_env_check.py`
4. Review logs in `.github/workflows/checks.yml` runs

---

**Remember**: The canonical source for all secrets is Pulumi ESC. Never store secrets elsewhere!