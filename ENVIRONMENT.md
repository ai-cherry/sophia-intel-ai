# Sophia Intel AI - Environment Setup Guide

Note: As of 2025-09-13, local development uses a single-source env file only: <repo>/.env.master. Do not use .env.local or ~/.config/sophia/env. Runtime code must rely on process env loaded by ./sophia; cloud deploys inject secrets via CI.

## 🎯 The Proper Environment for This Project

### Core Environment File: `.env.master`

This is the **SINGLE SOURCE OF TRUTH** for all configuration. Every service and agent uses this.

```bash
# Location
~/sophia-intel-ai/.env.master

# Permissions (CRITICAL)
chmod 600 .env.master  # Only owner can read/write
```

### Required Environment Variables

```bash
# === CORE AI PROVIDERS ===
ANTHROPIC_API_KEY="your-key-here"      # Claude models
OPENAI_API_KEY="your-key-here"         # GPT models
XAI_API_KEY="your-key-here"            # Grok models
# No direct Google key; access Gemini via OpenRouter/AIMLAPI/Together/HF
OPENROUTER_API_KEY=""                  # 100+ models (includes Gemini)

# === ADDITIONAL PROVIDERS (Optional) ===
GROQ_API_KEY=""                        # Fast inference
DEEPSEEK_API_KEY=""                    # Code models
MISTRAL_API_KEY=""                     # Mistral models
PERPLEXITY_API_KEY=""                  # Web search
OPENROUTER_API_KEY=""                  # 100+ models
TOGETHER_API_KEY=""                    # Open models

## Portkey Gateway is the only routing layer; no alternate local proxies

# === MCP SERVER CONFIGURATION ===
MCP_MEMORY_PORT=8081                   # Memory server
MCP_FILESYSTEM_PORT=8082               # Filesystem server
MCP_GIT_PORT=8084                       # Git server
MCP_DEV_BYPASS=true                    # Bypass auth for dev
# MCP_TOKEN=secure-token               # Production auth token

# === REDIS CONFIGURATION ===
REDIS_PORT=6379                        # Redis port
REDIS_URL="redis://localhost:6379/1"  # Connection string

# === LOGGING ===
LOG_LEVEL=info                         # Log verbosity
```

## 🤖 How to Ensure All Agents Use the Correct Environment

### 1. Always Start Services with `./sophia`

The `sophia` master control script **automatically**:
- Sources `.env.master` before starting anything
- Passes environment variables to all child processes
- Validates the environment is correct
- Ensures consistent configuration

```bash
# This is ALL you need
./sophia start

# Everything gets the right environment automatically
```

### 2. For Direct Python Scripts

```python
# At the top of any Python script
import os
from pathlib import Path

# Load environment from .env.master
env_file = Path.home() / "sophia-intel-ai" / ".env.master"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value.strip('"')
```

### 3. For Shell Scripts

```bash
#!/bin/bash
# At the top of any shell script

# Source the master environment
source ~/sophia-intel-ai/.env.master

# Now all variables are available
echo "Using Portkey Gateway with VKs"
```

### 4. For Node.js/JavaScript

```javascript
// At the top of any JS file
require('dotenv').config({ 
  path: '~/sophia-intel-ai/.env.master' 
});

// Now process.env has all variables
console.log('Portkey Gateway enabled');
```

## 🔒 Security Best Practices

### 1. Never Commit `.env.master`

```bash
# Add to .gitignore
echo ".env.master" >> .gitignore
```

### 2. Secure File Permissions

```bash
# Only owner can read/write
chmod 600 ~/.sophia-intel-ai/.env.master

# Verify permissions
ls -la ~/.sophia-intel-ai/.env.master
# Should show: -rw-------
```

### 3. Use Different Keys for Production

```bash
# Development (.env.master)
MCP_DEV_BYPASS=true
PORTKEY_API_KEY="your_portkey_api_key"

# Production (.env.production)
MCP_DEV_BYPASS=false
MCP_TOKEN="cryptographically-secure-token"
```

## 🚀 Quick Setup for New Developers

```bash
# 1. Clone the repo
git clone <repo-url> ~/sophia-intel-ai
cd ~/sophia-intel-ai

# 2. Copy environment template
cp .env.template .env.master

# 3. Add your API keys
nano .env.master  # Edit with your keys

# 4. Secure the file
chmod 600 .env.master

# 5. Initialize and start
./sophia init
./sophia start

# 6. Verify everything works
./sophia test
```

## 📋 Environment Validation

### Check if environment is correct:

```bash
# Run this to validate
./sophia test

# Should show:
# ✅ Redis: PASS
# ✅ Portkey Gateway: PASS
# ✅ MCP Memory: PASS
# ✅ MCP Filesystem: PASS
# ✅ MCP Git: PASS
```

### Common Issues and Fixes:

| Issue | Solution |
|-------|----------|
| "API key not found" | Check `.env.master` has the key |
| "Permission denied" | Run `chmod 600 .env.master` |
| "Port already in use" | Run `./sophia clean` then `./sophia start` |
| "Service won't start" | Check logs: `./sophia logs <service>` |

## 🎯 The Golden Rules

1. **ONE environment file**: `.env.master`
2. **ONE way to start**: `./sophia start`
3. **ONE place for logs**: `logs/`
4. **ONE place for PIDs**: `.pids/`
5. **ALWAYS use the sophia script** for service management

## 🔧 For CI/CD and Automation

```yaml
# GitHub Actions example
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  # ... other keys from secrets

steps:
  - name: Setup Environment
    run: |
      # Create .env.master from secrets
      cat > .env.master << EOF
      ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"
      OPENAI_API_KEY="$OPENAI_API_KEY"
      # ... other variables
      EOF
      chmod 600 .env.master
      
  - name: Start Services
    run: ./sophia start
    
  - name: Run Tests
    run: ./sophia test
```

## 📝 Summary

The proper environment for this project is:

1. **All configuration in `.env.master`** (secured with 600 permissions)
2. **All services started with `./sophia`** (which sources the environment)
3. **All agents inherit the environment** from their parent process
4. **Never hardcode credentials** in code
5. **Always validate with `./sophia test`** before deploying

This ensures **100% consistency** across all components, agents, and services.
