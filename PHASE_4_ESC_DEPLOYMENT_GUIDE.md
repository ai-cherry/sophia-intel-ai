# Phase 4: Pulumi ESC Integration - Deployment Guide

## 🎯 Overview

This guide covers the deployment of Phase 4: Pulumi ESC (Environments, Secrets, and Configuration) integration for centralizing and securing all configuration management in the Sophia Intel AI system.

## 📋 Pre-Deployment Checklist

### Required Dependencies
```bash
# Install required packages
pip install pulumi
pip install rich
pip install aiohttp
pip install redis
pip install cryptography
pip install pydantic
pip install watchfiles
```

### Required Environment Variables
```bash
# Essential for ESC integration
export PULUMI_API_KEY="your-pulumi-api-token"
export PULUMI_ORG="sophia-intel"  # Your Pulumi organization
export ENVIRONMENT="dev"  # or staging, production
```

### Verify Current System Status
```bash
# Check existing environment files
ls -la .env*

# Verify current Redis connection
python -c "import redis; r = redis.Redis(host='localhost', port=6379); print(r.ping())"

# Check running services
curl http://localhost:8080/health
```

## 🚀 Deployment Steps

### Step 1: Initialize Pulumi ESC Environments

```bash
# Create ESC environments (requires Pulumi CLI)
pulumi org set-default sophia-intel
pulumi env init sophia-intel/dev
pulumi env init sophia-intel/staging
pulumi env init sophia-intel/production

# Set initial configuration values
pulumi env set sophia-intel/dev --secret REDIS_PASSWORD "your-redis-password"
pulumi env set sophia-intel/dev --secret OPENAI_API_KEY "your-openai-key"
```

### Step 2: Run Migration (Dry Run First)

```bash
# Perform dry run migration
python scripts/migration/migrate_to_esc.py --dry-run

# Review the migration report
cat migration_report_*.json

# If satisfied, run actual migration
python scripts/migration/migrate_to_esc.py --pulumi-token "$PULUMI_API_KEY"
```

### Step 3: Validate Migration

```bash
# Run migration validation
python scripts/migration/validate_migration.py --pulumi-token "$PULUMI_API_KEY"

# Check validation report
cat migration_validation_report_*.json
```

### Step 4: Test ESC Integration

```bash
# Run comprehensive integration tests
python scripts/test_esc_integration.py --environment dev --verbose

# Check test results
cat esc_integration_test_report_*.json
```

### Step 5: Deploy Infrastructure (Optional)

```bash
# If using Pulumi for infrastructure provisioning
cd infrastructure/pulumi
pulumi stack select dev  # or create new stack
pulumi up
```

## 🔄 Zero-Downtime Deployment Process

### Gradual Rollout Strategy

1. **Phase A: Preparation**
   ```bash
   # Create backup of current configuration
   mkdir -p backup_configs/pre_esc_$(date +%Y%m%d_%H%M%S)
   cp .env* backup_configs/pre_esc_$(date +%Y%m%d_%H%M%S)/
   
   # Test ESC integration in fallback mode
   PULUMI_API_KEY="" python scripts/test_esc_integration.py
   ```

2. **Phase B: Parallel Operation**
   ```bash
   # Enable ESC with backward compatibility
   export ESC_BACKWARD_COMPATIBILITY=true
   python scripts/test_esc_integration.py --environment dev
   ```

3. **Phase C: Gradual Migration**
   ```bash
   # Migrate non-critical secrets first
   python scripts/migration/migrate_to_esc.py --environments dev --no-validate
   
   # Validate partial migration
   python scripts/migration/validate_migration.py --environments dev
   ```

4. **Phase D: Full Migration**
   ```bash
   # Complete migration for all environments
   python scripts/migration/migrate_to_esc.py --environments dev staging production
   ```

### Monitoring During Deployment

```bash
# Monitor system health
watch -n 5 'curl -s http://localhost:8080/health | jq .'

# Monitor ESC integration status
watch -n 10 'curl -s http://localhost:8080/api/config/status | jq .'

# Monitor Redis connectivity
watch -n 5 'curl -s http://localhost:8080/api/redis/health | jq .'
```

## 🛡️ Security Considerations

### Secrets Management
- All secrets are encrypted in transit and at rest
- API keys are validated before storage
- Access control is enforced through role-based permissions
- Audit logging tracks all secret access

### Network Security
- ESC communication uses HTTPS/TLS
- Redis connections use SSL/TLS when available
- WebSocket connections are authenticated

### Access Control Setup
```python
# Initialize access control (run once)
from app.core.security.access_control import initialize_default_users
initialize_default_users()
```

## 📊 Monitoring and Observability

### Health Checks
```bash
# ESC integration health
curl http://localhost:8080/api/esc/health

# Configuration status
curl http://localhost:8080/api/config/status

# Secret validation health
curl http://localhost:8080/api/secrets/health
```

### Audit Logs
- Location: `logs/esc_integration_audit.log`
- Format: Encrypted JSON with integrity checksums
- Retention: 7 years for compliance

### Metrics Collection
- Configuration load times
- Secret validation success rates
- Cache hit ratios
- API response times

## 🚨 Troubleshooting

### Common Issues

1. **ESC Connection Failed**
   ```bash
   # Check Pulumi token
   pulumi whoami
   
   # Test ESC connectivity
   pulumi env ls
   
   # Enable fallback mode
   export ESC_FALLBACK_MODE=true
   ```

2. **Configuration Not Loading**
   ```bash
   # Check environment detection
   echo $ENVIRONMENT
   
   # Verify ESC environment exists
   pulumi env get sophia-intel/$ENVIRONMENT
   
   # Test manual configuration load
   python -c "from app.core.esc_config import get_config; print(get_config('infrastructure.redis.url'))"
   ```

3. **Secret Validation Failures**
   ```bash
   # Run secret validator directly
   python -c "from app.core.security.secret_validator import ComprehensiveSecretValidator; import asyncio; asyncio.run(ComprehensiveSecretValidator().validate_secret('test', 'sk-test123', None))"
   
   # Check validation logs
   tail -f logs/esc_integration_audit.log
   ```

### Rollback Procedure
```bash
# Emergency rollback to .env files
python scripts/migration/rollback_migration.py --force --no-remove-secrets

# Validate rollback
python scripts/migration/validate_migration.py --environments dev
```

## 📈 Performance Optimization

### Configuration Caching
- Default cache TTL: 5 minutes
- Adjust with `ESC_CACHE_TTL=300` environment variable
- Monitor cache hit rates in health endpoints

### Connection Pooling
- Redis: 50 connection pool (configurable)
- HTTP: Reused aiohttp sessions
- ESC: Single persistent connection per environment

### Memory Management
- Configuration entries are cached in-memory
- LRU eviction for large configuration sets
- Periodic cleanup of expired entries

## 🎯 Success Metrics

### Deployment Success Criteria
- [ ] All integration tests pass (>95% success rate)
- [ ] Zero-downtime deployment achieved
- [ ] Backward compatibility maintained
- [ ] Security audit trails functional
- [ ] Performance metrics within thresholds

### Operational Success Criteria
- [ ] Configuration load time < 1 second
- [ ] Secret validation success rate > 90%
- [ ] Cache hit rate > 80%
- [ ] Zero configuration-related outages

## 📋 Post-Deployment Tasks

1. **Clean Up Legacy Files**
   ```bash
   # Archive old environment files (after validation)
   mkdir -p archive/env_files_$(date +%Y%m%d)
   mv .env.old .env.backup archive/env_files_$(date +%Y%m%d)/
   ```

2. **Documentation Updates**
   - Update deployment documentation
   - Create runbooks for operations team
   - Update incident response procedures

3. **Team Training**
   - ESC console usage
   - Secret rotation procedures
   - Monitoring and alerting

4. **Compliance Verification**
   - Audit log retention setup
   - Access control verification
   - Encryption validation

## 🔧 Advanced Configuration

### Custom ESC Environments
```yaml
# Custom environment configuration
values:
  custom_service:
    api_endpoint: https://custom-api.com
    timeout_seconds: 30
    retry_attempts: 3
```

### Secret Rotation Policies
```python
from infrastructure.pulumi.esc.secret_rotation import RotationPolicy, RotationType

# Define custom rotation policy
policy = RotationPolicy(
    secret_key="custom.api.key",
    rotation_type=RotationType.API_KEY,
    interval_days=30,
    environments=["staging", "production"]
)
```

### Access Control Customization
```python
from app.core.security.access_control import Role, Permission

# Create custom role
custom_role = Role(
    name="api_admin",
    permissions={Permission.SECRET_READ, Permission.SECRET_WRITE},
    environments=["dev", "staging"],
    resource_patterns=[r"api\..*"]
)
```

## 📞 Support and Maintenance

### Regular Maintenance Tasks
- Weekly: Review audit logs
- Monthly: Rotate critical API keys
- Quarterly: Update access permissions
- Annually: Review and update security policies

### Emergency Contacts
- Platform Team: platform@sophia-intel-ai.com
- Security Team: security@sophia-intel-ai.com
- On-Call: ops@sophia-intel-ai.com

### Documentation Links
- [Pulumi ESC Documentation](https://www.pulumi.com/docs/pulumi-cloud/esc/)
- [Redis Configuration Guide](docs/redis-setup.md)
- [Security Best Practices](docs/security-guide.md)

---

## 🎉 Deployment Complete!

Phase 4: Pulumi ESC Integration has been successfully deployed. Your Sophia Intel AI system now benefits from:

- **Centralized Configuration Management**: All secrets and configuration in one secure location
- **Enhanced Security**: Encrypted secrets with audit trails and access control
- **Improved Operations**: Automated secret rotation and validation
- **Better Compliance**: Complete audit trails and retention policies
- **Zero Downtime**: Hot configuration reloading without service restarts

The system is now ready for AI coding swarms with enterprise-grade configuration management!