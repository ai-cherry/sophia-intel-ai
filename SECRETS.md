# 🔐 Secrets and Configuration Management

**Sophia Intel Platform - Comprehensive Configuration Guide**

This document provides complete guidance on managing secrets, configuration, and environment setup for the Sophia Intel AI agent platform.

## 📋 Table of Contents

- [Configuration Architecture](#configuration-architecture)
- [Required Secrets](#required-secrets)
- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)
- [Environment Variables Reference](#environment-variables-reference)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)

---

## 🏗️ Configuration Architecture

The Sophia Intel platform uses a **three-tier configuration system** with clear precedence:

```
1. Environment Variables (.env, GitHub Secrets)  ← HIGHEST PRIORITY
2. YAML Configuration (config/sophia.yaml)       ← DEFAULT VALUES
3. Python Defaults (config/config.py)           ← FALLBACK
```

### Configuration Flow

```mermaid
graph TB
    A[Application Start] --> B{Environment Variables?}
    B -->|Yes| C[Use Environment Values]
    B -->|No| D{YAML Config?}
    D -->|Yes| E[Use YAML Values]
    D -->|No| F[Use Python Defaults]
    C --> G[Validate Configuration]
    E --> G
    F --> G
    G --> H{Valid?}
    H -->|Yes| I[Start Services]
    H -->|No| J[Show Errors & Exit]
```

---

## 🔑 Required Secrets

### **Tier 1: Critical (Platform Won't Start)**

| Secret | Format | Description | Example |
|--------|--------|-------------|---------|
| `OPENROUTER_API_KEY` | `sk-or-v1-*` | OpenRouter API access (REQUIRED) | `sk-or-v1-1234567890abcdef...` |
| `SECRET_KEY` | 32+ chars | Django-style secret key | `your-32-char-secret-key-here...` |
| `ENCRYPTION_KEY` | Exactly 32 chars | AES-256 encryption key | `12345678901234567890123456789012` |
| `JWT_SECRET` | 16+ chars | JWT token signing | `jwt-secret-16-chars-minimum` |

### **Tier 2: Recommended (Enhanced Features)**

| Secret | Format | Description | Example |
|--------|--------|-------------|---------|
| `PORTKEY_API_KEY` | `pk-*` | Portkey AI gateway (optional) | `pk-1234567890abcdef...` |
| `LAMBDA_API_KEY` | `ll-*` | Lambda Labs GPU access | `ll-1234567890abcdef...` |
| `EXA_API_KEY` | `exa-*` | Exa search integration | `exa-1234567890abcdef...` |
| `QDRANT_API_KEY` | Any | Qdrant Cloud authentication | `your-qdrant-cloud-key` |

### **Tier 3: Optional (Development Convenience)**

| Secret | Format | Description | Default |
|--------|--------|-------------|---------|
| `API_SALT` | 16+ chars | Additional security salt | `dev-api-salt-change` |
| `DATABASE_URL` | PostgreSQL URL | Custom database connection | Local Docker |
| `REDIS_URL` | Redis URL | Custom Redis connection | Local Docker |

---

## 🛠️ Development Setup

### **Step 1: Copy Environment Template**

```bash
# In your Codespace terminal
cp .env.example .env
```

### **Step 2: Obtain Required API Keys**

#### OpenRouter API Key (REQUIRED)
1. Visit [OpenRouter.ai](https://openrouter.ai/)
2. Sign up for an account
3. Navigate to "API Keys"
4. Create a new key (starts with `sk-or-v1-`)
5. Add to `.env`: `OPENROUTER_API_KEY=sk-or-v1-your-key-here`

#### Portkey API Key (Recommended)
1. Visit [Portkey.ai](https://portkey.ai/)
2. Create account and get API key (starts with `pk-`)
3. Add to `.env`: `PORTKEY_API_KEY=pk-your-key-here`

#### Lambda Labs API Key (Optional - GPU Features)
1. Visit [Lambda Labs Cloud](https://cloud.lambdalabs.com/)
2. Create account and generate API key (starts with `ll-`)
3. Add to `.env`: `LAMBDA_API_KEY=ll-your-key-here`

### **Step 3: Generate Security Keys**

```bash
# Generate secure random keys
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_hex(16))"
python -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(24))"
python -c "import secrets; print('API_SALT=' + secrets.token_urlsafe(16))"
```

Copy the generated values to your `.env` file.

### **Step 4: Configure Database URLs (Optional)**

For local development with Docker:
```bash
# Default values work out of the box
DATABASE_URL=postgresql+asyncpg://sophia:devpass@localhost:5432/sophia
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333
```

For cloud services:
```bash
# Example Qdrant Cloud
QDRANT_URL=https://your-cluster-id.us-east1-0.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-cloud-api-key

# Example managed PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:pass@your-postgres-host:5432/sophia

# Example managed Redis
REDIS_URL=redis://your-redis-host:6379/0
```

### **Step 5: Validate Configuration**

```bash
# Run the comprehensive validation script
python scripts/validate_config.py
```

Expected output for valid configuration:
```
🔍 Sophia Intel Configuration Validator
==================================================
✅ All configuration validation checks passed!
Your Sophia Intel platform is properly configured.
```

### **Step 6: Start Development Environment**

```bash
# Start local services (if using Docker)
docker-compose up -d

# Verify services are running
docker-compose ps

# Start the application services
# Terminal 1: MCP Server
uvicorn mcp_servers.unified_mcp_server:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2: Backend API
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 3: Agent API
python scripts/agno_api.py

# Terminal 4: Frontend (optional)
cd frontend && npm install && npm start
```

---

## 🚀 Production Deployment

### **GitHub Secrets Configuration**

For production deployment, set these as GitHub repository secrets:

```bash
# Navigate to: GitHub Repository → Settings → Secrets and variables → Actions

# Required secrets
OPENROUTER_API_KEY=sk-or-v1-production-key-here
SECRET_KEY=production-secret-key-32-chars-minimum
ENCRYPTION_KEY=production-encryption-key-exactly-32
JWT_SECRET=production-jwt-secret-16-chars-minimum

# Recommended secrets  
PORTKEY_API_KEY=pk-production-portkey-key
LAMBDA_API_KEY=ll-production-lambda-key
EXA_API_KEY=exa-production-search-key

# Production database URLs
DATABASE_URL=postgresql+asyncpg://prod_user:secure_pass@prod-db:5432/sophia
REDIS_URL=redis://prod-redis:6379/0
QDRANT_URL=https://prod-cluster.qdrant.tech:6333
QDRANT_API_KEY=production-qdrant-key

# Additional production settings
ENVIRONMENT=production
LOG_LEVEL=INFO
API_SALT=production-api-salt-16-chars-minimum
```

### **Production Security Checklist**

- [ ] All secrets use strong, randomly generated values
- [ ] No development or placeholder values in production
- [ ] Database connections use SSL/TLS encryption
- [ ] API keys have appropriate rate limits and quotas
- [ ] Secrets are stored in secure secret management systems
- [ ] Regular secret rotation schedule established
- [ ] Access logs and monitoring configured

---

## 📖 Environment Variables Reference

### **Core Application Settings**

```bash
# Environment Configuration
ENVIRONMENT=development|staging|production|test
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR|CRITICAL

# API Configuration
API_HOST=0.0.0.0                    # API bind address
API_PORT=8000                       # API port
MCP_PORT=8001                       # MCP server port
MCP_GATEWAY_PORT=8002               # MCP gateway port
```

### **Service Endpoints**

```bash
# Internal Service URLs
SOPHIA_API_ENDPOINT=http://localhost:8000
SOPHIA_MCP_ENDPOINT=http://localhost:8001  
SOPHIA_FRONTEND_ENDPOINT=http://localhost:3000
LAMBDA_GATEWAY_ENDPOINT=http://localhost:8002
```

### **AI/LLM Configuration**

```bash
# LLM Provider Settings
LLM_PROVIDER=openrouter              # Provider selection
CACHE_TTL_SECONDS=300               # Response cache TTL
MAX_TOKENS=4096                     # Maximum tokens per request
TEMPERATURE=0.7                     # Sampling temperature

# Memory/Embedding Settings  
MEMORY_COLLECTION_NAME=code_memory   # Qdrant collection name
EMBEDDING_DIMENSION=1536            # Vector dimension (for text-embedding-3-small)
MAX_CONTEXT_LENGTH=10000            # Maximum context length
```

### **Agent Configuration**

```bash
# Agent Runtime Settings
AGNO_STORAGE_DB=data/agents.db      # SQLite database path
AGENT_CONCURRENCY=2                 # Max concurrent agent tasks
AGENT_TIMEOUT_SECONDS=300           # Task timeout

# Monitoring Settings
ENABLE_METRICS=true                 # Enable Prometheus metrics
METRICS_PORT=9090                   # Metrics endpoint port
```

---

## 🔧 Troubleshooting

### **Common Configuration Errors**

#### 1. **"Configuration validation FAILED"**
```bash
# Run validation to see specific errors
python scripts/validate_config.py

# Common fixes:
# - Remove placeholder values (your-key-here, dev-, test-)
# - Ensure API keys have correct prefixes
# - Generate proper length security keys
```

#### 2. **"OpenRouter API authentication failed"**
```bash
# Check API key format
echo $OPENROUTER_API_KEY
# Should start with: sk-or-v1-

# Test API key manually
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     https://openrouter.ai/api/v1/models
```

#### 3. **"Database connection failed"**
```bash
# Check PostgreSQL URL format
echo $DATABASE_URL
# Should be: postgresql+asyncpg://user:pass@host:port/dbname

# Test connection
python -c "
import asyncio
from config.config import settings
print(f'Database URL: {settings.DATABASE_URL}')
"
```

#### 4. **"Qdrant connection failed"**
```bash
# Check Qdrant URL and API key
echo $QDRANT_URL
echo $QDRANT_API_KEY

# Test connection manually
curl -H "api-key: $QDRANT_API_KEY" $QDRANT_URL/collections
```

### **Validation Script Outputs**

#### ✅ **Success Output**
```
🔍 Sophia Intel Configuration Validator
==================================================
✅ All configuration validation checks passed!
Your Sophia Intel platform is properly configured.
```

#### ❌ **Error Output**
```
🔍 Sophia Intel Configuration Validator
==================================================
❌ Configuration validation FAILED with 3 errors.

🚨 ERRORS (must be fixed):
  ❌ OPENROUTER_API_KEY appears to be a placeholder value: sk-or-v1-your-openr...
  ❌ SECRET_KEY appears to be a development placeholder: dev-secret-key-chang...
  ❌ ENCRYPTION_KEY must be exactly 32 characters long, got 28
```

---

## 🛡️ Security Best Practices

### **Secret Management**

1. **Never commit secrets to git**
   - Use `.env` files locally (gitignored)
   - Use GitHub Secrets or secret management systems in production

2. **Use strong, unique secrets**
   - Generate cryptographically secure random values
   - Use different secrets for different environments

3. **Regular rotation**
   - Rotate API keys quarterly
   - Rotate security keys annually
   - Monitor for compromised keys

### **Access Control**

1. **Principle of least privilege**
   - Only grant necessary API permissions
   - Use separate keys for different services

2. **Environment isolation**
   - Never use production keys in development
   - Separate secrets for staging and production

### **Monitoring**

1. **Secret usage tracking**
   - Monitor API key usage and quotas
   - Set up alerts for unusual activity

2. **Configuration validation**
   - Run validation in CI/CD pipelines
   - Validate before production deployments

### **Backup & Recovery**

1. **Secure backup**
   - Store secrets in secure secret management systems
   - Maintain encrypted backups of configuration

2. **Recovery procedures**
   - Document secret recovery processes
   - Test recovery procedures regularly

---

## 📞 Support & Resources

### **Quick Reference Links**

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [Portkey Documentation](https://docs.portkey.ai/)
- [Lambda Labs API Docs](https://cloud.lambdalabs.com/api/v1/docs)
- [Qdrant Documentation](https://qdrant.tech/documentation/)

### **Configuration Commands**

```bash
# Validate configuration
python scripts/validate_config.py

# Generate new secrets
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Test API connectivity
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     https://openrouter.ai/api/v1/models

# Check service health
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:7777/health
```

### **Getting Help**

1. **Run the validation script first**: `python scripts/validate_config.py`
2. **Check service logs** for specific error messages
3. **Verify API keys** are properly formatted and active
4. **Test individual components** before full system startup

---

**✅ Configuration Checklist**

- [ ] `.env` file created from template
- [ ] All required API keys obtained and configured
- [ ] Security keys generated and set
- [ ] Database URLs configured (if not using defaults)
- [ ] Configuration validation passed
- [ ] All services start successfully
- [ ] Health endpoints respond correctly

*For additional support, consult the main [README.md](README.md) or run the validation script for specific guidance.*