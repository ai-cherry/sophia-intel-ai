# Security Policy & Procedures

## MCP JWT Authentication

All MCP servers (filesystem, memory, git, vector) use JWT-based authentication with HMAC-SHA256 signing.

### Required Environment Variables

```bash
# Production (required)
MCP_JWT_SECRET=your-strong-secret-here

# Development (optional bypass)
MCP_DEV_BYPASS=1  # Only for local development
```

### Token Generation

```bash
# Generate a 15-minute token for filesystem access
./bin/mcp-token --aud filesystem --ttl 900

# Generate token for specific audience
./bin/mcp-token --aud memory --ttl 600 --sub admin
```

### JWT Claims Structure

```json
{
  "sub": "user-identifier",
  "aud": "filesystem|memory|git|vector",
  "iat": 1641234567,
  "exp": 1641235467
}
```

## Secret Management

### Environment Variables

- **Production**: Use GitHub Environments with OIDC
- **Development**: Use `.env.local` (gitignored)
- **CI/CD**: Use GitHub Secrets and Actions

### Protected Secrets

1. **MCP_JWT_SECRET** - JWT signing key
2. **PORTKEY_API_KEY** - Model routing API key  
3. **SLACK_BOT_TOKEN** - Slack integration
4. **MICROSOFT_SECRET_KEY** - MS Graph API
5. **Database credentials** - Redis, Weaviate, etc.

## Secret Rotation Schedule

### Monthly (High-Priority)
- MCP_JWT_SECRET
- PORTKEY_API_KEY
- Database passwords

### Quarterly (Medium-Priority)  
- SLACK_BOT_TOKEN
- MICROSOFT_SECRET_KEY
- GitHub PATs

### Annually (Low-Priority)
- SSH keys
- Certificate authorities

## Rotation Procedures

### 1. MCP JWT Secret Rotation

```bash
# 1. Generate new secret
NEW_SECRET=$(openssl rand -base64 32)

# 2. Update production environment
# Via GitHub Environments UI or CLI

# 3. Restart MCP servers
# Via deployment pipeline

# 4. Verify health endpoints
curl https://your-domain/mcp/filesystem/health
curl https://your-domain/mcp/memory/health
```

### 2. Portkey API Key Rotation

```bash
# 1. Generate new virtual key in Portkey dashboard
# 2. Update PORTKEY_API_KEY in environment
# 3. Test model connectivity
python -c "
import os
from config.python_settings import settings_from_env
s = settings_from_env()
print(f'Portkey configured: {bool(s.PORTKEY_API_KEY)}')
"
```

### 3. Database Credentials

```bash
# Redis
# 1. Create new user/password in Redis
# 2. Update REDIS_URL environment variable
# 3. Remove old user

# Weaviate  
# 1. Generate new API key in Weaviate
# 2. Update WEAVIATE_API_KEY
# 3. Revoke old key
```

## Incident Response

### Secret Exposure

1. **Immediate** (< 1 hour):
   - Revoke exposed secret at source
   - Generate replacement secret
   - Update production environment
   - Restart affected services

2. **Follow-up** (< 24 hours):
   - Rotate related secrets
   - Review access logs
   - Purge from git history if committed:
     ```bash
     # Use BFG or git-filter-repo
     git filter-repo --replace-text secrets.txt
     git push --force-with-lease origin main
     ```

3. **Prevention** (< 1 week):
   - Update .gitignore if needed
   - Review CI/CD secret detection
   - Security training for team

### Compromise Detection

Monitor for:
- Unauthorized API calls
- Failed authentication attempts
- Unusual data access patterns
- Resource usage spikes

## CI/CD Security Gates

### Required Checks

1. **Gitleaks** - Secret detection
2. **Safety** - Python vulnerability scanning  
3. **Bandit** - Python security linting
4. **Trivy** - Filesystem vulnerability scanning
5. **Secret Patterns** - Custom hardcoded secret detection
6. **MCP Validation** - JWT configuration compliance

### Deployment Gates

- All security checks must pass
- Secrets must be validated in target environment
- Health checks must succeed post-deployment

## Access Controls

### GitHub Repository
- Branch protection on `main`
- Required reviews for security-related changes
- CODEOWNERS for sensitive files

### Production Environment
- OIDC authentication for deployments
- Environment-specific secrets
- Audit logging enabled

### MCP Servers
- JWT authentication required
- Rate limiting enabled (configurable RPM)
- Health/metrics endpoints exempt from auth

## Security Headers & Configuration

### FastAPI Security
```python
# Already implemented in MCP servers
- JWT validation middleware
- Rate limiting per IP
- CORS controls
- Request/response metrics
```

### Network Security
- HTTPS required in production
- Internal service communication encrypted
- Database connections over TLS

## Monitoring & Alerting

### Metrics Tracked
- Authentication failures
- Rate limit hits
- Token expiration patterns
- API response times

### Alert Thresholds
- > 10 auth failures/minute
- > 100 requests/minute from single IP
- Token expiring in < 1 hour

## Security Contacts

- **Security Issues**: Create GitHub Security Advisory
- **Incident Response**: [Your incident response contact]
- **General Questions**: [Your security team contact]

## Vulnerability Reporting

1. **DO NOT** open public issues for security vulnerabilities
2. Use GitHub Security Advisories (preferred) or email [security@yourcompany.com]
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Compliance

### Standards Followed
- JWT RFC 7519
- HMAC RFC 2104
- OAuth 2.0 for external APIs
- TLS 1.2+ for all connections

### Regular Reviews
- **Monthly**: Secret rotation status
- **Quarterly**: Access reviews
- **Annually**: Security architecture review

---

**Last Updated**: September 2025  
**Next Review**: December 2025
