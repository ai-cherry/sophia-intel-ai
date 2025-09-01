# 🛠️ Sophia Intel AI - Troubleshooting Guide

This comprehensive guide helps you diagnose and resolve common issues with local deployment and real API integrations.

## 🚀 **Quick Start Diagnostics**

### 1. Pre-Flight Check
```bash
# Validate all API connections
python3 scripts/validate-apis.py

# Check environment variables
./start-local.sh validate

# Test Docker setup
docker --version && docker-compose --version
```

### 2. Service Status Check
```bash
# Check all services
./start-local.sh status

# View service logs
./start-local.sh logs

# Run health checks
curl http://localhost:8003/health/detailed
```

## ⚠️ **Common Issues & Solutions**

### API Connection Issues

**❌ Problem: "OpenAI API key not found or is dummy"**
```bash
# Check if key is properly set
grep OPENAI_API_KEY .env.local

# Expected: OPENAI_API_KEY=sk-...
# If missing or dummy, update .env.local

# Reload environment
source .env.local
./start-local.sh restart
```

**❌ Problem: "Rate limit exceeded"**
```bash
# Check API usage dashboard
# OpenAI: https://platform.openai.com/usage
# Anthropic: https://console.anthropic.com/

# Solutions:
# 1. Wait for rate limit reset
# 2. Upgrade API plan
# 3. Implement request queuing
```

**❌ Problem: "Invalid API response format"**
```bash
# Check provider status
curl -s https://status.openai.com/api/v2/status.json

# Test direct API call
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

### Docker & Container Issues

**❌ Problem: "Container build failed"**
```bash
# Check Docker disk space
docker system df

# Clean up if needed
docker system prune -f

# Rebuild with verbose output
docker-compose -f docker-compose.local.yml build --no-cache --progress=plain
```

**❌ Problem: "Port already in use"**
```bash
# Find process using port
lsof -i :8003  # or :7777, :8080, etc.

# Kill process
kill -9 <PID>

# Or use different ports in docker-compose.local.yml
```

**❌ Problem: "Container health check failing"**
```bash
# Check container logs
docker logs sophia-unified-api

# Inspect health check
docker inspect sophia-unified-api | grep -A 10 Health

# Test health endpoint manually
docker exec sophia-unified-api curl -f http://localhost:8003/healthz
```

### Database Connection Issues

**❌ Problem: "Redis connection failed"**
```bash
# Check Redis container status
docker ps | grep redis

# Test Redis connection
docker exec sophia-redis-local redis-cli -a sophia_redis_2024 ping

# Check Redis logs
docker logs sophia-redis-local

# Alternative: Use Redis Cloud URL
export REDIS_URL="redis://default:pdM2P5F7oO269JCCtBURsrCBrSacqZmF@redis-15014.fcrce172.us-east-1-1.ec2.redns.redis-cloud.com:15014"
```

**❌ Problem: "PostgreSQL connection failed"**
```bash
# Check PostgreSQL container
docker ps | grep postgres

# Test connection
docker exec sophia-postgres-local pg_isready -U sophia -d sophia

# Check PostgreSQL logs
docker logs sophia-postgres-local

# Manual connection test
docker exec -it sophia-postgres-local psql -U sophia -d sophia -c "SELECT version();"
```

**❌ Problem: "Weaviate vector database unavailable"**
```bash
# Test Weaviate connection
curl -s http://localhost:8080/v1/.well-known/ready

# Check Weaviate container
docker ps | grep weaviate

# Verify Weaviate health
curl -s http://localhost:8080/v1/meta | jq '.version'
```

### Service Integration Issues

**❌ Problem: "Unified API server not responding"**
```bash
# Check service dependencies
curl http://localhost:8080/v1/.well-known/ready  # Weaviate
curl http://localhost:5432                       # PostgreSQL (will fail, but shows connection)

# Check unified API logs
docker logs sophia-unified-api -f

# Test internal service communication
docker exec sophia-unified-api curl http://weaviate:8080/v1/.well-known/ready
```

**❌ Problem: "Agno Bridge proxy errors"**
```bash
# Check unified API connectivity from bridge
docker exec sophia-agno-bridge curl http://unified-api:8003/healthz

# Check Agno Bridge logs
docker logs sophia-agno-bridge -f

# Test bridge endpoints
curl http://localhost:7777/healthz
curl http://localhost:7777/agents
```

**❌ Problem: "Memory/Vector search not working"**
```bash
# Test vector store service
curl http://localhost:8005/health

# Test MCP server
curl http://localhost:8004/health

# Check service logs
docker logs sophia-mcp-server
docker logs sophia-vector-store
```

## 🔧 **Advanced Troubleshooting**

### Performance Issues

**🐌 Problem: Slow API responses**
```bash
# Check service resource usage
docker stats

# Monitor API response times
curl -w "@curl-format.txt" http://localhost:8003/healthz

# Create curl-format.txt:
cat > curl-format.txt << 'EOF'
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
EOF
```

**📈 Problem: High memory usage**
```bash
# Check container memory usage
docker stats --no-stream

# Check system memory
free -h

# Optimize container resources in docker-compose.local.yml
# Add memory limits:
deploy:
  resources:
    limits:
      memory: 512M
```

### Network Issues

**🌐 Problem: Service discovery failures**
```bash
# Check Docker network
docker network ls
docker network inspect sophia_local_network

# Test inter-service connectivity
docker exec sophia-unified-api nslookup weaviate
docker exec sophia-agno-bridge nslookup unified-api

# Check port bindings
docker port sophia-unified-api
docker port sophia-agno-bridge
```

### Data Persistence Issues

**💾 Problem: Data not persisting between restarts**
```bash
# Check Docker volumes
docker volume ls | grep sophia

# Inspect volume mounts
docker inspect sophia-postgres-local | grep -A 5 Mounts
docker inspect sophia-weaviate-local | grep -A 5 Mounts

# Backup important data
docker exec sophia-postgres-local pg_dump -U sophia sophia > backup.sql
```

## 🚨 **Emergency Recovery**

### Complete System Reset
```bash
# Stop all services
./start-local.sh stop

# Clean everything
./start-local.sh clean

# Remove all data (WARNING: Irreversible)
docker volume rm $(docker volume ls -q | grep sophia)

# Fresh start
./start-local.sh
```

### Partial Service Recovery
```bash
# Restart specific service
docker-compose -f docker-compose.local.yml restart unified-api

# Rebuild specific service
docker-compose -f docker-compose.local.yml up --build unified-api

# View specific service logs
docker-compose -f docker-compose.local.yml logs -f unified-api
```

### API Key Recovery
```bash
# Test all API keys
python3 scripts/validate-apis.py

# Check specific provider
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models | jq '.data[0].id'

# Regenerate keys if needed (from provider dashboards)
# Update .env.local
# Restart services
./start-local.sh restart
```

## 📊 **Monitoring & Logging**

### Log Analysis
```bash
# View all service logs
./start-local.sh logs

# Filter by service
docker-compose -f docker-compose.local.yml logs unified-api

# Filter by error level
docker-compose -f docker-compose.local.yml logs | grep -i error

# Follow logs in real-time
docker-compose -f docker-compose.local.yml logs -f --tail=100
```

### Health Monitoring
```bash
# Comprehensive health check
curl http://localhost:8003/health/detailed | jq

# Individual service health
curl http://localhost:8003/health/redis | jq
curl http://localhost:8003/health/weaviate | jq
curl http://localhost:8003/health/api-providers | jq

# Environment validation
curl http://localhost:8003/health/environment | jq
```

### Performance Monitoring
```bash
# Container resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# API response monitoring (install httpstat)
# pip install httpstat
httpstat http://localhost:8003/healthz
```

## 🔍 **Debug Commands Reference**

### Container Management
```bash
# List all Sophia containers
docker ps -a | grep sophia

# Get container IP addresses
docker inspect --format='{{.Name}} - {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker ps -aq)

# Execute commands in containers
docker exec -it sophia-unified-api bash
docker exec -it sophia-postgres-local psql -U sophia sophia
docker exec -it sophia-redis-local redis-cli -a sophia_redis_2024
```

### Service Testing
```bash
# Test unified API endpoints
curl http://localhost:8003/healthz
curl http://localhost:8003/teams
curl -X POST http://localhost:8003/memory/search -H "Content-Type: application/json" -d '{"query":"test"}'

# Test Agno Bridge endpoints
curl http://localhost:7777/healthz
curl http://localhost:7777/v1/playground/agents
```

### Database Operations
```bash
# PostgreSQL queries
docker exec sophia-postgres-local psql -U sophia -d sophia -c "
SELECT table_name FROM information_schema.tables WHERE table_schema='public';
SELECT COUNT(*) FROM memory_entries;
SELECT * FROM sessions LIMIT 5;
"

# Redis operations
docker exec sophia-redis-local redis-cli -a sophia_redis_2024 INFO
docker exec sophia-redis-local redis-cli -a sophia_redis_2024 KEYS "*"
```

## 📞 **Getting Help**

### Before Reporting Issues
1. ✅ Run the validation script: `python3 scripts/validate-apis.py`
2. ✅ Check service health: `curl http://localhost:8003/health/detailed`
3. ✅ Review logs: `./start-local.sh logs`
4. ✅ Try service restart: `./start-local.sh restart`

### Issue Reporting Template
```markdown
**Environment:**
- OS: [macOS/Linux/Windows]
- Docker version: [output of `docker --version`]
- Python version: [output of `python3 --version`]

**Issue Description:**
[Describe the problem]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Error Messages:**
```
[Paste error messages here]
```

**Service Status:**
```
[Output of `./start-local.sh status`]
```
```

### Support Resources
- 📖 **API Keys Guide**: [`API_KEYS_GUIDE.md`](API_KEYS_GUIDE.md)
- 🚀 **Deployment Guide**: [`PULUMI_2025_DEPLOYMENT_GUIDE.md`](PULUMI_2025_DEPLOYMENT_GUIDE.md)
- 🏗️ **Architecture Overview**: [`DEDUPLICATION_STRATEGY.md`](DEDUPLICATION_STRATEGY.md)

---

**Last Updated**: January 2025  
**Version**: 2.0.0  
**Status**: Production Ready - No Mocks