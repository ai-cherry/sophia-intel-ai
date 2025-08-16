# Environment Variables Reference

This document lists all environment variables used across the Sophia Intel platform, their purposes, and configuration requirements.

## Core Application Variables

### API Gateway Service

| Variable | Required | Default | Description | Service |
|----------|----------|---------|-------------|---------|
| `OPENROUTER_API_KEY` | Yes | - | OpenRouter API key for AI model access | API Gateway |
| `CORS_ORIGINS` | No | `*` | Comma-separated list of allowed CORS origins | API Gateway |
| `HOST` | No | `0.0.0.0` | Host address to bind the service | API Gateway |
| `PORT` | No | `8000` | Port number for the API Gateway | API Gateway |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARN, ERROR) | API Gateway |

### Dashboard Backend Service

| Variable | Required | Default | Description | Service |
|----------|----------|---------|-------------|---------|
| `DASHBOARD_API_TOKEN` | Yes (Prod) | - | Authentication token for dashboard API access | Dashboard Backend |
| `OPENROUTER_API_KEY` | Yes | - | OpenRouter API key for AI functionality | Dashboard Backend |
| `FLASK_ENV` | No | `production` | Flask environment mode | Dashboard Backend |
| `SECRET_KEY` | Yes | - | Flask secret key for session management | Dashboard Backend |
| `HOST` | No | `0.0.0.0` | Host address to bind the service | Dashboard Backend |
| `PORT` | No | `5000` | Port number for the dashboard backend | Dashboard Backend |

### Dashboard Frontend Service

| Variable | Required | Default | Description | Service |
|----------|----------|---------|-------------|---------|
| `REACT_APP_API_URL` | No | `/api` | Backend API URL for frontend requests | Dashboard Frontend |
| `REACT_APP_ENVIRONMENT` | No | `production` | Environment mode for React app | Dashboard Frontend |
| `PORT` | No | `3000` | Development server port | Dashboard Frontend |

## Database and Storage Variables

### PostgreSQL Database

| Variable | Required | Default | Description | Service |
|----------|----------|---------|-------------|---------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string | All Services |
| `DB_HOST` | No | `localhost` | Database host address | All Services |
| `DB_PORT` | No | `5432` | Database port number | All Services |
| `DB_NAME` | No | `sophia` | Database name | All Services |
| `DB_USER` | No | `postgres` | Database username | All Services |
| `DB_PASSWORD` | Yes | - | Database password | All Services |
| `DB_SSL_MODE` | No | `prefer` | SSL mode for database connection | All Services |

### Redis Cache

| Variable | Required | Default | Description | Service |
|----------|----------|---------|-------------|---------|
| `REDIS_URL` | Yes | - | Redis connection string | All Services |
| `REDIS_HOST` | No | `localhost` | Redis host address | All Services |
| `REDIS_PORT` | No | `6379` | Redis port number | All Services |
| `REDIS_PASSWORD` | No | - | Redis password (if required) | All Services |
| `REDIS_DB` | No | `0` | Redis database number | All Services |

### Vector Database (Qdrant)

| Variable | Required | Default | Description | Service |
|----------|----------|---------|-------------|---------|
| `QDRANT_URL` | Yes | - | Qdrant server URL | MCP Services |
| `QDRANT_API_KEY` | No | - | Qdrant API key (if required) | MCP Services |
| `QDRANT_HOST` | No | `localhost` | Qdrant host address | MCP Services |
| `QDRANT_PORT` | No | `6333` | Qdrant port number | MCP Services |

## External API Keys

### AI and ML Services

| Variable | Required | Default | Description | Service |
|----------|----------|---------|-------------|---------|
| `OPENROUTER_API_KEY` | Yes | - | OpenRouter API for AI models | All Services |
| `ANTHROPIC_API_KEY` | No | - | Anthropic Claude API key | AI Services |
| `OPENAI_API_KEY` | No | - | OpenAI API key | AI Services |
| `COHERE_API_KEY` | No | - | Cohere API key | AI Services |
| `HUGGINGFACE_API_TOKEN` | No | - | Hugging Face API token | AI Services |
| `TOGETHER_AI_API_KEY` | No | - | Together AI API key | AI Services |

### Data and Research Services

| Variable | Required | Default | Description | Service |
|----------|----------|---------|-------------|---------|
| `EXA_API_KEY` | No | - | Exa search API key | Research Services |
| `TAVILY_API_KEY` | No | - | Tavily search API key | Research Services |
| `BRAVE_API_KEY` | No | - | Brave search API key | Research Services |
| `APIFY_API_TOKEN` | No | - | Apify web scraping API | Research Services |

### Business Intelligence Services

| Variable | Required | Default | Description | Service |
|----------|----------|---------|-------------|---------|
| `HUBSPOT_API_KEY` | No | - | HubSpot CRM API key | Business Services |
| `HUBSPOT_ACCESS_TOKEN` | No | - | HubSpot OAuth access token | Business Services |
| `GONG_ACCESS_KEY` | No | - | Gong conversation analytics API | Business Services |
| `GONG_CLIENT_SECRET` | No | - | Gong client secret | Business Services |
| `LINEAR_API_KEY` | No | - | Linear project management API | Business Services |
| `ASANA_API_TOKEN` | No | - | Asana project management API | Business Services |

### Monitoring and Observability

| Variable | Required | Default | Description | Service |
|----------|----------|---------|-------------|---------|
| `ARIZE_API_KEY` | No | - | Arize ML monitoring API key | Monitoring |
| `ARIZE_SPACE_ID` | No | - | Arize workspace identifier | Monitoring |
| `LANGSMITH_API_KEY` | No | - | LangSmith tracing API key | Monitoring |
| `PORTKEY_API_KEY` | No | - | Portkey gateway API key | Monitoring |

## Infrastructure Variables

### Cloud Infrastructure

| Variable | Required | Default | Description | Service |
|----------|----------|---------|-------------|---------|
| `LAMBDA_CLOUD_API_KEY` | Yes | - | Lambda Labs cloud API key | Infrastructure |
| `LAMBDA_API_KEY` | Yes | - | Lambda Labs API key (alias) | Infrastructure |
| `AWS_ACCESS_KEY_ID` | No | - | AWS access key for S3/other services | Infrastructure |
| `AWS_SECRET_ACCESS_KEY` | No | - | AWS secret key | Infrastructure |
| `AWS_REGION` | No | `us-east-1` | AWS region | Infrastructure |

### DNS and Networking

| Variable | Required | Default | Description | Service |
|----------|----------|---------|-------------|---------|
| `DNSIMPLE_API_KEY` | Yes | - | DNSimple API key for DNS management | Infrastructure |
| `DNSIMPLE_ACCOUNT_ID` | No | - | DNSimple account identifier | Infrastructure |
| `CLOUDFLARE_API_TOKEN` | No | - | Cloudflare API token | Infrastructure |

### Container Registry

| Variable | Required | Default | Description | Service |
|----------|----------|---------|-------------|---------|
| `DOCKER_HUB_USERNAME` | No | - | Docker Hub username | CI/CD |
| `DOCKER_PERSONAL_ACCESS_TOKEN` | No | - | Docker Hub access token | CI/CD |
| `GITHUB_PAT` | Yes | - | GitHub Personal Access Token | CI/CD |
| `DEPLOYMENT_PAT` | Yes | - | GitHub PAT for deployment (alias) | CI/CD |

## Security and Encryption

### Authentication and Authorization

| Variable | Required | Default | Description | Service |
|----------|----------|---------|-------------|---------|
| `JWT_SECRET` | Yes | - | JWT token signing secret | All Services |
| `API_SECRET_KEY` | Yes | - | API request signing key | All Services |
| `ENCRYPTION_KEY` | Yes | - | Data encryption key (32 characters) | All Services |
| `BACKUP_ENCRYPTION_KEY` | No | - | Backup data encryption key | Infrastructure |

### Session Management

| Variable | Required | Default | Description | Service |
|----------|----------|---------|-------------|---------|
| `SESSION_SECRET` | Yes | - | Session cookie signing secret | Dashboard Backend |
| `CSRF_SECRET` | No | - | CSRF token secret | Dashboard Backend |

## Development and Testing

### Development Environment

| Variable | Required | Default | Description | Service |
|----------|----------|---------|-------------|---------|
| `ENVIRONMENT` | No | `production` | Application environment (dev/staging/prod) | All Services |
| `DEBUG` | No | `false` | Enable debug mode | All Services |
| `TESTING` | No | `false` | Enable testing mode | All Services |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity level | All Services |

### Testing Configuration

| Variable | Required | Default | Description | Service |
|----------|----------|---------|-------------|---------|
| `TEST_DATABASE_URL` | No | - | Test database connection string | Testing |
| `TEST_REDIS_URL` | No | - | Test Redis connection string | Testing |
| `PYTEST_TIMEOUT` | No | `300` | Test timeout in seconds | Testing |

## Deployment Configuration

### Pulumi Infrastructure

| Variable | Required | Default | Description | Service |
|----------|----------|---------|-------------|---------|
| `PULUMI_ACCESS_TOKEN` | Yes | - | Pulumi Cloud access token | Infrastructure |
| `PULUMI_STACK` | No | `production` | Pulumi stack name | Infrastructure |
| `PULUMI_CONFIG_PASSPHRASE` | No | - | Pulumi config encryption passphrase | Infrastructure |

### Kubernetes

| Variable | Required | Default | Description | Service |
|----------|----------|---------|-------------|---------|
| `KUBECONFIG` | No | `~/.kube/config` | Kubernetes configuration file path | Infrastructure |
| `KUBERNETES_NAMESPACE` | No | `sophia-intel` | Kubernetes namespace | Infrastructure |
| `KUBERNETES_CONTEXT` | No | `default` | Kubernetes context | Infrastructure |

## Configuration by Environment

### Development Environment

Required variables for local development:
- `OPENROUTER_API_KEY`
- `DATABASE_URL` (local PostgreSQL)
- `REDIS_URL` (local Redis)
- `SECRET_KEY`
- `JWT_SECRET`
- `ENCRYPTION_KEY`

### Staging Environment

Additional variables for staging:
- `DASHBOARD_API_TOKEN`
- `LAMBDA_CLOUD_API_KEY`
- `DNSIMPLE_API_KEY`
- Production database URLs

### Production Environment

All variables should be configured, with particular attention to:
- All security keys and tokens
- Production database connections
- Monitoring and observability keys
- Infrastructure API keys

## Security Best Practices

### Secret Management

1. **Never commit secrets to version control**
2. **Use environment-specific secret stores**:
   - Development: `.env` files (gitignored)
   - Staging/Production: Pulumi ESC + GitHub Secrets
3. **Rotate secrets regularly**
4. **Use least-privilege access**

### Environment Variable Validation

Each service validates required environment variables at startup:

```python
# Example validation in Python services
import os
from typing import Optional

def get_required_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Required environment variable {key} is not set")
    return value

def get_optional_env(key: str, default: Optional[str] = None) -> Optional[str]:
    return os.getenv(key, default)
```

### Configuration Loading

Services use a hierarchical configuration loading approach:

1. Environment variables (highest priority)
2. Configuration files
3. Default values (lowest priority)

## Troubleshooting

### Common Issues

**Missing Required Variables**
```bash
# Check if variable is set
echo $OPENROUTER_API_KEY

# List all environment variables
env | grep SOPHIA
```

**Invalid Variable Format**
```bash
# Validate database URL format
python -c "from sqlalchemy import create_engine; create_engine('$DATABASE_URL')"

# Validate Redis URL format  
python -c "import redis; redis.from_url('$REDIS_URL')"
```

**Permission Issues**
```bash
# Check API key permissions
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" https://openrouter.ai/api/v1/models
```

### Environment Variable Debugging

Enable debug logging to see configuration loading:

```bash
export LOG_LEVEL=DEBUG
export DEBUG=true
```

This will show which environment variables are loaded and their sources.

## References

- [Deployment Guide](deployment/README.md)
- [Security Documentation](security.md)
- [Development Setup](development.md)
- [Pulumi Configuration](../infra/README.md)

