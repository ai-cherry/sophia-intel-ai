
# SOPHIA Intel Deployment Runbook

## 🎯 **Purpose**

This runbook provides step-by-step procedures for deploying, monitoring, and maintaining SOPHIA Intel in production. It serves as the definitive operational guide for the platform.

## 📋 **Quick Reference**

### Emergency Contacts
- **Primary**: GitHub Issues (https://github.com/ai-cherry/sophia-intel/issues)
- **Repository**: https://github.com/ai-cherry/sophia-intel
- **Monitoring**: GitHub Actions workflows
- **Platform**: Railway (https://railway.app)

### Critical URLs
- **Production Dashboard**: https://www.sophia-intel.ai
- **API Endpoint**: https://api.sophia-intel.ai
- **Health Check**: https://api.sophia-intel.ai/health
- **Dashboard**: https://dashboard.sophia-intel.ai

### Key Commands
```bash
# Health check
python monitoring/health-check.py

# Deploy to production
git push origin main

# Emergency rollback
git revert HEAD && git push origin main

# View logs
railway logs --service sophia-api
```

## 🚀 **Deployment Procedures**

### Standard Deployment

**Prerequisites**:
- [ ] All tests passing locally
- [ ] Code reviewed and approved
- [ ] No active incidents
- [ ] Backup completed within 24 hours

**Procedure**:
1. **Pre-deployment Checks**
   ```bash
   # Verify current system health
   python monitoring/health-check.py
   
   # Check for any active alerts
   gh issue list --label "monitoring"
   
   # Verify backup status
   ls -la backups/ | head -5
   ```

2. **Deploy to Production**
   ```bash
   # Ensure you're on main branch
   git checkout main
   git pull origin main
   
   # Push changes (triggers CI/CD)
   git push origin main
   
   # Monitor deployment
   gh run watch
   ```

3. **Post-deployment Verification**
   ```bash
   # Wait 2 minutes for services to stabilize
   sleep 120
   
   # Run health checks
   python monitoring/health-check.py
   
   # Verify specific endpoints
   curl -f https://www.sophia-intel.ai
   curl -f https://api.sophia-intel.ai/health
   
   # Check performance
   curl -w "@curl-format.txt" -o /dev/null -s https://api.sophia-intel.ai/health
   ```

4. **Deployment Verification Checklist**
   - [ ] Frontend loads successfully
   - [ ] API health endpoint returns 200
   - [ ] Chat interface functional
   - [ ] Database connectivity confirmed
   - [ ] Response times < 3 seconds
   - [ ] No error alerts triggered

### Emergency Deployment

**When to Use**: Critical security patches, urgent bug fixes

**Procedure**:
1. **Immediate Assessment**
   ```bash
   # Assess current system state
   python monitoring/health-check.py
   
   # Check error rates
   railway logs --service sophia-api | grep -i error | tail -20
   ```

2. **Fast-track Deployment**
   ```bash
   # Create hotfix branch
   git checkout -b hotfix/critical-fix
   
   # Make minimal necessary changes
   # Test locally if possible
   
   # Deploy directly
   git checkout main
   git merge hotfix/critical-fix
   git push origin main
   ```

3. **Emergency Verification**
   ```bash
   # Immediate health check
   curl -f https://api.sophia-intel.ai/health
   
   # Monitor for 10 minutes
   watch -n 30 'curl -s https://api.sophia-intel.ai/health | jq .status'
   ```

### Rollback Procedures

**Automatic Rollback Triggers**:
- Health checks fail for > 5 minutes
- Error rate > 10%
- Response time > 10 seconds

**Manual Rollback**:
1. **Immediate Rollback**
   ```bash
   # Revert last commit
   git revert HEAD
   git push origin main
   
   # Monitor rollback
   gh run watch
   ```

2. **Service-specific Rollback**
   ```bash
   # Rollback specific service
   railway rollback --service sophia-api
   
   # Or rollback frontend
   railway rollback --service sophia-dashboard
   ```

3. **Infrastructure Rollback**
   ```bash
   cd infrastructure/pulumi
   pulumi stack select production
   pulumi history
   pulumi cancel  # If deployment in progress
   pulumi up --target-dependents  # Restore previous state
   ```

## 🏥 **Monitoring Procedures**

### Daily Health Checks

**Morning Routine** (9 AM UTC):
```bash
# 1. Check overnight alerts
gh issue list --label "monitoring" --state open

# 2. Run comprehensive health check
python monitoring/health-check.py

# 3. Review backup status
cat monitoring/reports/latest_backup_report.txt

# 4. Check performance trends
python monitoring/performance-report.py

# 5. Verify service status
railway status
```

**Health Check Interpretation**:
- **Green (✅)**: All systems operational
- **Yellow (⚠️)**: Performance degradation, monitor closely
- **Red (❌)**: Service failure, immediate action required

### Automated Monitoring

**GitHub Actions Monitoring**:
- **Schedule**: Every 15 minutes
- **Workflow**: `.github/workflows/monitoring.yml`
- **Alerts**: Automatic issue creation on failures

**Monitoring Endpoints**:
```bash
# Frontend health
curl -I https://www.sophia-intel.ai

# API health
curl https://api.sophia-intel.ai/health

# Database connectivity
curl https://api.sophia-intel.ai/db-health
```

### Performance Monitoring

**Key Metrics**:
- **Response Time**: Target < 3 seconds
- **Error Rate**: Target < 1%
- **Uptime**: Target 99.9%
- **Throughput**: Monitor requests/minute

**Performance Commands**:
```bash
# Response time check
curl -w "@curl-format.txt" -o /dev/null -s https://api.sophia-intel.ai/health

# Load test (if needed)
ab -n 100 -c 10 https://api.sophia-intel.ai/health

# Database performance
railway connect postgres -c "SELECT pg_stat_database.datname, pg_size_pretty(pg_database_size(pg_stat_database.datname)) AS size FROM pg_stat_database;"
```

## 🔧 **Maintenance Procedures**

### Weekly Maintenance

**Every Monday 10 AM UTC**:
1. **Dependency Updates**
   ```bash
   # Update frontend dependencies
   cd apps/dashboard
   npm update
   npm audit fix
   
   # Update backend dependencies
   cd backend
   pip install -r requirements.txt --upgrade
   pip-audit
   ```

2. **Security Scan**
   ```bash
   # Frontend security scan
   cd apps/dashboard && npm audit

   # Backend security scan
   cd backend && pip-audit
   
   # Infrastructure scan
   cd infrastructure/pulumi && pulumi preview
   ```

3. **Performance Review**
   ```bash
   # Generate performance report
   python monitoring/performance-report.py
   
   # Review logs for patterns
   railway logs --service sophia-api | grep -E "(error|warning)" | tail -50
   ```

4. **Backup Verification**
   ```bash
   # Test backup integrity
   python monitoring/backup-system.py --verify
   
   # Check backup retention
   find backups/ -type d -mtime +30 -exec rm -rf {} \;
   ```

### Monthly Maintenance

**First Monday of Each Month**:
1. **Infrastructure Review**
   ```bash
   # Review infrastructure costs
   railway usage
   
   # Optimize resource allocation
   cd infrastructure/pulumi && pulumi preview
   ```

2. **Security Audit**
   ```bash
   # Review access logs
   gh api /repos/ai-cherry/sophia-intel/events | jq '.[] | select(.type == "PushEvent")'
   
   # Check secret rotation needs
   python scripts/check-secret-rotation.py
   ```

3. **Disaster Recovery Test**
   ```bash
   # Test backup restoration (in staging)
   python monitoring/restore-system.py --test-mode
   
   # Verify DNS failover
   dig www.sophia-intel.ai
   ```

### Quarterly Maintenance

**Every 3 Months**:
1. **Full Infrastructure Audit**
2. **Disaster Recovery Drill**
3. **Performance Optimization Review**
4. **Security Penetration Testing**
5. **Documentation Updates**

## 🚨 **Incident Response**

### Incident Classification

**P0 - Critical (Response: Immediate)**:
- Complete service outage
- Data loss or corruption
- Security breach

**P1 - High (Response: < 1 hour)**:
- Significant performance degradation
- Partial service outage
- Authentication failures

**P2 - Medium (Response: < 4 hours)**:
- Minor performance issues
- Non-critical feature failures
- Monitoring alerts

**P3 - Low (Response: < 24 hours)**:
- Documentation issues
- Minor UI bugs
- Enhancement requests

### Incident Response Workflow

1. **Detection & Assessment**
   ```bash
   # Immediate health check
   python monitoring/health-check.py
   
   # Check service status
   railway status
   
   # Review recent deployments
   gh run list --limit 5
   ```

2. **Initial Response**
   ```bash
   # Create incident issue
   gh issue create --title "INCIDENT: [Description]" --label "incident,P0"
   
   # Notify team (if applicable)
   # Begin investigation
   ```

3. **Investigation**
   ```bash
   # Check logs
   railway logs --service sophia-api --tail 100
   
   # Check metrics
   python monitoring/performance-report.py
   
   # Check infrastructure
   cd infrastructure/pulumi && pulumi stack --show-urns
   ```

4. **Resolution**
   ```bash
   # Apply fix (rollback or hotfix)
   git revert HEAD && git push origin main
   
   # Verify resolution
   python monitoring/health-check.py
   
   # Monitor for stability
   watch -n 60 'curl -s https://api.sophia-intel.ai/health'
   ```

5. **Post-Incident**
   ```bash
   # Update incident issue with resolution
   gh issue comment [issue-number] --body "Resolved: [description]"
   
   # Close incident
   gh issue close [issue-number]
   
   # Schedule post-mortem (for P0/P1)
   ```

### Common Incident Scenarios

**Frontend Not Loading**:
```bash
# Check DNS
nslookup www.sophia-intel.ai

# Check service
railway status --service sophia-dashboard

# Check fallback
curl -I https://www.sophia-intel.ai

# Resolution: DNS update or service restart
```

**API Errors**:
```bash
# Check API health
curl https://api.sophia-intel.ai/health

# Check database
railway connect postgres -c "SELECT 1;"

# Check logs
railway logs --service sophia-api | grep -i error

# Resolution: Service restart or database fix
```

**Performance Degradation**:
```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s https://api.sophia-intel.ai/health

# Check resource usage
railway ps --service sophia-api

# Check database performance
railway connect postgres -c "SELECT * FROM pg_stat_activity;"

# Resolution: Scale up or optimize queries
```

## 🔐 **Security Procedures**

### Secret Rotation

**Monthly Secret Rotation**:
```bash
# Generate new Railway token
railway login
railway tokens create

# Update GitHub secrets
gh secret set RAILWAY_TOKEN --body "new_token_value"

# Update Pulumi configuration
cd infrastructure/pulumi
pulumi config set railway-token "new_token_value" --secret

# Deploy with new secrets
pulumi up
```

### Security Incident Response

**Suspected Breach**:
1. **Immediate Actions**
   - Rotate all API keys and tokens
   - Review access logs
   - Check for unauthorized changes

2. **Investigation**
   ```bash
   # Check recent commits
   git log --oneline -10
   
   # Check access patterns
   gh api /repos/ai-cherry/sophia-intel/events
   
   # Review service logs
   railway logs --service sophia-api | grep -E "(auth|login|token)"
   ```

3. **Containment**
   - Revoke compromised credentials
   - Update security configurations
   - Monitor for continued threats

### Access Control Review

**Monthly Access Review**:
```bash
# Review repository collaborators
gh api /repos/ai-cherry/sophia-intel/collaborators

# Check Railway team members
railway team list

# Review Pulumi organization access
pulumi org ls
```

## 📊 **Backup & Recovery**

### Backup Procedures

**Daily Automated Backup**:
- **Schedule**: 2 AM UTC daily
- **Scope**: Databases, configuration, application code
- **Retention**: 30 days
- **Location**: `backups/` directory

**Manual Backup**:
```bash
# Run immediate backup
python monitoring/backup-system.py

# Verify backup
ls -la backups/ | head -5

# Test backup integrity
python monitoring/backup-system.py --verify
```

### Recovery Procedures

**Database Recovery**:
```bash
# List available backups
ls -la backups/sophia_intel_backup_*/

# Restore from specific backup
python monitoring/restore-system.py --backup-id 20250816_020000

# Verify restoration
railway connect postgres -c "SELECT COUNT(*) FROM users;"
```

**Full System Recovery**:
```bash
# Restore infrastructure
cd infrastructure/pulumi
pulumi stack import production

# Restore services
railway up --service sophia-api
railway up --service sophia-dashboard

# Restore databases
python monitoring/restore-system.py --full-restore
```

## 📈 **Performance Optimization**

### Performance Monitoring

**Key Performance Indicators**:
- Frontend load time: < 2 seconds
- API response time: < 500ms
- Database query time: < 100ms
- Error rate: < 0.1%

**Performance Testing**:
```bash
# Load testing
ab -n 1000 -c 50 https://api.sophia-intel.ai/health

# Database performance
railway connect postgres -c "EXPLAIN ANALYZE SELECT * FROM users LIMIT 10;"

# Frontend performance
lighthouse https://www.sophia-intel.ai --output json
```

### Optimization Procedures

**Database Optimization**:
```bash
# Analyze slow queries
railway connect postgres -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Update statistics
railway connect postgres -c "ANALYZE;"

# Check index usage
railway connect postgres -c "SELECT schemaname, tablename, indexname, idx_scan FROM pg_stat_user_indexes ORDER BY idx_scan;"
```

**Application Optimization**:
```bash
# Profile API endpoints
python -m cProfile -o profile.stats backend/main.py

# Analyze memory usage
python -m memory_profiler backend/main.py

# Check for memory leaks
python -m tracemalloc backend/main.py
```

## 📞 **Escalation Procedures**

### Escalation Matrix

**Level 1**: Automated monitoring and alerts
**Level 2**: On-call engineer response
**Level 3**: Senior engineer escalation
**Level 4**: Management and external support

### Contact Information

**Primary Contacts**:
- GitHub Issues: https://github.com/ai-cherry/sophia-intel/issues
- Repository Maintainers: @ai-cherry team
- Platform Support: Railway support

**Escalation Triggers**:
- P0 incidents lasting > 30 minutes
- P1 incidents lasting > 2 hours
- Multiple simultaneous incidents
- Security incidents

## 📚 **Reference Information**

### Useful Commands Reference

**Health & Monitoring**:
```bash
# Quick health check
curl -f https://api.sophia-intel.ai/health

# Detailed monitoring
python monitoring/health-check.py

# Performance check
curl -w "@curl-format.txt" -o /dev/null -s https://api.sophia-intel.ai/health
```

**Deployment & Management**:
```bash
# Deploy to production
git push origin main

# Check deployment status
gh run list --workflow=production-deploy.yml

# Rollback deployment
git revert HEAD && git push origin main
```

**Service Management**:
```bash
# Check service status
railway status

# View service logs
railway logs --service sophia-api

# Restart service
railway up --service sophia-api
```

### Configuration Files

**Important Files**:
- `.github/workflows/production-deploy.yml`: Main deployment workflow
- `.github/workflows/monitoring.yml`: Health monitoring workflow
- `infrastructure/pulumi/__main__.py`: Infrastructure definition
- `monitoring/health-check.py`: Health monitoring script
- `monitoring/backup-system.py`: Backup automation

### External Dependencies

**Critical Services**:
- **Railway**: Application hosting platform
- **DNSimple**: DNS management
- **GitHub**: Code repository and CI/CD
- **Pulumi**: Infrastructure as Code
- **Lambda AI**: AI model services

**Service Status Pages**:
- Railway: https://status.railway.app/
- GitHub: https://www.githubstatus.com/
- DNSimple: https://status.dnsimple.com/

---

**SOPHIA Intel Deployment Runbook**  
**Last Updated**: August 2025  
**Version**: 1.0.0  
**Next Review**: September 2025

