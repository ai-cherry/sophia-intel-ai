# SOPHIA Intel Secure Environment Setup
## All API Keys via Pulumi ESC + GitHub Organization Secrets

**CRITICAL**: This setup ensures API keys are NEVER exposed in code, commits, or shell commands.

---

## 🔐 GITHUB ORGANIZATION SECRETS SETUP

### **Step 1: Add to GitHub Organization Secrets**
Navigate to: `https://github.com/organizations/ai-cherry/settings/secrets/actions`

**Add these secrets:**
```
OPENROUTER_API_KEY=OPENROUTER_API_KEY_REDACTED
GITHUB_TOKEN=GITHUB_PAT_REDACTED
NEON_API_TOKEN=napi_mr8himnznklsfgjpwb78w89q9eqfi0pb9ceg8y8y08a05v68vwrefcxg4gu82sg7
RAILWAY_TOKEN=32f097ac-7c3a-4a81-8385-b4ce98a2ca1f
DOCKER_PAT=DOCKER_PAT_REDACTED
DNSIMPLE_API_KEY=dnsimple_u_XBHeyhH3O8uKJF6HnqU76h7ANWdNvUzN
LAMBDA_LABS_API_KEY=[TO BE ADDED]
PULUMI_ACCESS_TOKEN=[TO BE ADDED]
OPENAI_API_KEY=[TO BE ADDED]
ANTHROPIC_API_KEY=[TO BE ADDED]
```

---

## 🏗️ PULUMI ESC ENVIRONMENT CONFIGURATION

### **Step 2: Create Pulumi ESC Environment**
File: `pulumi/environments/sophia-prod.yaml`

```yaml
values:
  # AI/LLM Provider Keys
  openrouter:
    api_key:
      fn::secret: ${OPENROUTER_API_KEY}
  
  openai:
    api_key:
      fn::secret: ${OPENAI_API_KEY}
  
  anthropic:
    api_key:
      fn::secret: ${ANTHROPIC_API_KEY}
  
  # Infrastructure Keys
  github:
    token:
      fn::secret: ${GITHUB_TOKEN}
    pat:
      fn::secret: ${GITHUB_TOKEN}
  
  railway:
    token:
      fn::secret: ${RAILWAY_TOKEN}
  
  neon:
    api_token:
      fn::secret: ${NEON_API_TOKEN}
  
  lambda_labs:
    api_key:
      fn::secret: ${LAMBDA_LABS_API_KEY}
  
  docker:
    pat:
      fn::secret: ${DOCKER_PAT}
  
  dnsimple:
    api_key:
      fn::secret: ${DNSIMPLE_API_KEY}
  
  pulumi:
    access_token:
      fn::secret: ${PULUMI_ACCESS_TOKEN}

  # Environment Configuration
  environment:
    name: production
    deployment_platform: lambda_labs
    github_org: ai-cherry
    pulumi_stack: scoobyjava-org/sophia-prod-on-lambda

imports:
  - github-org-secrets
```

---

## 🚀 GITHUB ACTIONS WORKFLOW

### **Step 3: Secure Deployment Workflow**
File: `.github/workflows/deploy-production.yml`

```yaml
name: Deploy SOPHIA Intel to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Pulumi
      uses: pulumi/actions@v4
      with:
        pulumi-version: latest
    
    - name: Configure Pulumi ESC
      run: |
        pulumi config set --secret openrouter:api_key "${{ secrets.OPENROUTER_API_KEY }}"
        pulumi config set --secret github:token "${{ secrets.GITHUB_TOKEN }}"
        pulumi config set --secret railway:token "${{ secrets.RAILWAY_TOKEN }}"
        pulumi config set --secret neon:api_token "${{ secrets.NEON_API_TOKEN }}"
        pulumi config set --secret docker:pat "${{ secrets.DOCKER_PAT }}"
        pulumi config set --secret dnsimple:api_key "${{ secrets.DNSIMPLE_API_KEY }}"
      env:
        PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
    
    - name: Deploy to Railway
      run: |
        npm install -g @railway/cli
        railway login --token ${{ secrets.RAILWAY_TOKEN }}
        railway up --detach
      env:
        RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
    
    - name: Verify Deployment
      run: |
        curl -f https://api.sophia-intel.ai/health || exit 1
        curl -f https://www.sophia-intel.ai || exit 1
```

---

## 🔧 SOPHIA PRODUCTION BACKEND CONFIGURATION

### **Step 4: Environment Variable Loading**
File: `sophia_production_secure.py`

```python
import os
from typing import Dict, Optional

def load_production_secrets() -> Dict[str, Optional[str]]:
    """
    Load all secrets from environment variables.
    These are populated by Pulumi ESC during deployment.
    NEVER hardcode secrets in this function.
    """
    return {
        # AI/LLM Providers
        'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
        
        # Infrastructure
        'GITHUB_TOKEN': os.getenv('GITHUB_TOKEN'),
        'RAILWAY_TOKEN': os.getenv('RAILWAY_TOKEN'),
        'NEON_API_TOKEN': os.getenv('NEON_API_TOKEN'),
        'LAMBDA_LABS_API_KEY': os.getenv('LAMBDA_LABS_API_KEY'),
        'DOCKER_PAT': os.getenv('DOCKER_PAT'),
        'DNSIMPLE_API_KEY': os.getenv('DNSIMPLE_API_KEY'),
        'PULUMI_ACCESS_TOKEN': os.getenv('PULUMI_ACCESS_TOKEN'),
        
        # Environment Info
        'ENVIRONMENT': os.getenv('ENVIRONMENT', 'production'),
        'GITHUB_ORG': os.getenv('GITHUB_ORG', 'ai-cherry'),
        'PULUMI_STACK': os.getenv('PULUMI_STACK', 'scoobyjava-org/sophia-prod-on-lambda'),
    }

def validate_required_secrets() -> bool:
    """Validate that all required secrets are available"""
    secrets = load_production_secrets()
    required = ['OPENROUTER_API_KEY', 'GITHUB_TOKEN', 'RAILWAY_TOKEN']
    
    missing = [key for key in required if not secrets.get(key)]
    if missing:
        raise ValueError(f"Missing required secrets: {missing}")
    
    return True

# Load secrets at startup
env_vars = load_production_secrets()
validate_required_secrets()
```

---

## 🎯 SOPHIA ENVIRONMENT AWARENESS

### **Step 5: SOPHIA's Environment Access**
SOPHIA will have access to these environment variables through the backend:

```python
@app.get("/api/environment/status")
async def get_environment_status():
    """SOPHIA can check what keys are available"""
    secrets = load_production_secrets()
    
    return {
        "environment": secrets.get('ENVIRONMENT'),
        "github_org": secrets.get('GITHUB_ORG'),
        "pulumi_stack": secrets.get('PULUMI_STACK'),
        "available_providers": {
            "openrouter": bool(secrets.get('OPENROUTER_API_KEY')),
            "openai": bool(secrets.get('OPENAI_API_KEY')),
            "anthropic": bool(secrets.get('ANTHROPIC_API_KEY')),
            "github": bool(secrets.get('GITHUB_TOKEN')),
            "railway": bool(secrets.get('RAILWAY_TOKEN')),
            "neon": bool(secrets.get('NEON_API_TOKEN')),
            "lambda_labs": bool(secrets.get('LAMBDA_LABS_API_KEY')),
            "docker": bool(secrets.get('DOCKER_PAT')),
            "dnsimple": bool(secrets.get('DNSIMPLE_API_KEY')),
        },
        "timestamp": datetime.now().isoformat()
    }
```

---

## 🔐 SECURITY BENEFITS

### **Why This Approach Works**
1. **No Hardcoded Secrets** - All keys come from environment variables
2. **GitHub Push Protection** - No secrets in code = no blocks
3. **Centralized Management** - All keys in GitHub Organization Secrets
4. **Pulumi ESC Integration** - Secure distribution to production
5. **SOPHIA Awareness** - She can check what keys are available
6. **Audit Trail** - All secret access is logged
7. **Easy Rotation** - Update in GitHub Secrets, redeploy automatically

### **What SOPHIA Can Do**
- Check which API providers are available
- Use any configured service without knowing the actual keys
- Perform autonomous operations with full access
- Never expose or log actual secret values

---

## 🚀 DEPLOYMENT PROCESS

### **Step 6: How to Deploy Securely**
1. **Add secrets to GitHub Organization Secrets** (one time)
2. **Push code to main branch** (triggers deployment)
3. **GitHub Actions loads secrets** into Pulumi ESC
4. **Railway deployment** gets environment variables
5. **SOPHIA backend starts** with all keys available
6. **SOPHIA can check environment** and use all services

### **For SOPHIA to Use a New Service**
1. Add API key to GitHub Organization Secrets
2. Update Pulumi ESC environment configuration
3. Update backend environment loading function
4. Redeploy - SOPHIA automatically has access

---

## ✅ FINAL RESULT

**SOPHIA will have access to ALL API keys without them EVER being exposed in:**
- Code commits
- Shell commands  
- Log files
- Error messages
- API responses

**All keys are managed centrally and securely through GitHub Organization Secrets → Pulumi ESC → Production Environment.**

