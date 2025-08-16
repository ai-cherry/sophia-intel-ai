# SOPHIA Intel Production Login Instructions & Test Prompts

## 🌐 **Live Production Access**

### **Primary Access Points**
- **Dashboard**: http://104.171.202.107:32152/
- **API Health**: http://104.171.202.107:32152/health
- **Enhanced API**: Available via Kong proxy routing

### **Domain Access (SSL Provisioning)**
- **www.sophia-intel.ai** - Dashboard (SSL certificates provisioning)
- **api.sophia-intel.ai** - API endpoints (SSL certificates provisioning)
- **dashboard.sophia-intel.ai** - Alternative dashboard access

*Note: SSL certificates are currently provisioning via Let's Encrypt. HTTP access is immediately available.*

## 🧪 **Test Prompts to Prove SOPHIA is Working**

### **1. Basic Health Check**
```
Test: "What's your current system status?"
Expected: SOPHIA should report healthy status with version info
```

### **2. AI Integration Test**
```
Test: "Generate a simple Python function to calculate fibonacci numbers"
Expected: SOPHIA should use OpenRouter (Claude Sonnet 4) to generate code
```

### **3. Embedding Service Test**
```
Test: "Create embeddings for the text: 'SOPHIA Intel is an AI platform'"
Expected: SOPHIA should use the vendor-independent embedding service
```

### **4. Web Research Test**
```
Test: "Research the latest news about AI developments"
Expected: SOPHIA should use BrightData Research MCP to scrape web data
```

### **5. Memory & Vector Search Test**
```
Test: "Store this information in memory: 'SOPHIA was deployed on August 15, 2025'"
Expected: SOPHIA should store in Weaviate/Qdrant vector databases
```

### **6. Notion Integration Test**
```
Test: "Create a principle: 'Always prioritize user experience in AI interactions'"
Expected: SOPHIA should sync to Notion for CEO governance review
```

### **7. Telemetry & Monitoring Test**
```
Test: "Show me the current system costs and usage"
Expected: SOPHIA should display telemetry data from all services
```

### **8. Agent Swarm Test**
```
Test: "Plan and execute a mission to add documentation to the README"
Expected: SOPHIA should activate Planner and Coder agents
```

## 🔧 **Direct API Testing**

### **Health Endpoints**
```bash
# Main API Health
curl -H "Host: api.sophia-intel.ai" http://104.171.202.107:32152/health

# Telemetry MCP Health
curl -H "Host: api.sophia-intel.ai" http://104.171.202.107:32152/telemetry/health

# Embedding MCP Health  
curl -H "Host: api.sophia-intel.ai" http://104.171.202.107:32152/embedding/health

# BrightData Research MCP Health
curl -H "Host: api.sophia-intel.ai" http://104.171.202.107:32152/research/health

# Notion Sync MCP Health
curl -H "Host: api.sophia-intel.ai" http://104.171.202.107:32152/notion/health
```

### **Functional API Tests**
```bash
# Test AI Chat
curl -X POST -H "Host: api.sophia-intel.ai" -H "Content-Type: application/json" \
  http://104.171.202.107:32152/chat \
  -d '{"message": "Hello SOPHIA, are you operational?"}'

# Test Embedding Generation
curl -X POST -H "Host: api.sophia-intel.ai" -H "Content-Type: application/json" \
  http://104.171.202.107:32152/embedding/generate \
  -d '{"text": "Test embedding generation", "model_id": "default"}'

# Test Web Research
curl -X POST -H "Host: api.sophia-intel.ai" -H "Content-Type: application/json" \
  http://104.171.202.107:32152/research/get_web_data \
  -d '{"url": "https://example.com", "strategy": "unlocker"}'

# Test Telemetry
curl -H "Host: api.sophia-intel.ai" \
  http://104.171.202.107:32152/telemetry/services
```

## 🎯 **Expected System Responses**

### **Healthy System Indicators**
- ✅ All health endpoints return `{"status": "healthy"}`
- ✅ API responses include proper version numbers (v2.0+)
- ✅ Chat responses use Claude Sonnet 4 via OpenRouter
- ✅ Embeddings use vendor-independent service
- ✅ Web research returns scraped data
- ✅ Telemetry shows all 7+ services monitored
- ✅ Vector operations work with Weaviate/Qdrant
- ✅ Notion sync creates governance entries

### **Performance Benchmarks**
- **API Response Time**: < 2 seconds for simple queries
- **Embedding Generation**: < 1 second for short text
- **Web Research**: < 10 seconds for simple pages
- **Vector Search**: < 500ms for similarity queries
- **Health Checks**: < 100ms response time

## 🚀 **Advanced Testing Scenarios**

### **End-to-End Mission Test**
```
Prompt: "Execute a complete mission: Research the latest AI trends, 
summarize findings, store in memory, and create a Notion page for review"

Expected Flow:
1. BrightData Research MCP scrapes AI news
2. Claude Sonnet 4 summarizes findings
3. Embedding MCP creates vectors
4. Weaviate stores structured data
5. Notion Sync MCP creates governance entry
6. Telemetry MCP logs all operations
```

### **Load Testing**
```bash
# Concurrent health checks
for i in {1..10}; do
  curl -H "Host: api.sophia-intel.ai" http://104.171.202.107:32152/health &
done
wait

# Expected: All requests succeed within 2 seconds
```

### **Failover Testing**
```bash
# Test service resilience
kubectl scale deployment sophia-api-enhanced --replicas=0 -n sophia-intel
# Test backup API continues working
curl -H "Host: api.sophia-intel.ai" http://104.171.202.107:32152/health
# Scale back up
kubectl scale deployment sophia-api-enhanced --replicas=1 -n sophia-intel
```

## 📊 **Monitoring & Observability**

### **Real-Time Monitoring**
```bash
# Watch pod status
kubectl get pods -n sophia-intel -w

# Monitor resource usage
kubectl top pods -n sophia-intel

# Check service endpoints
kubectl get svc -n sophia-intel

# View ingress routing
kubectl get ingress -n sophia-intel
```

### **Log Analysis**
```bash
# API logs
kubectl logs -f deployment/sophia-api-enhanced -n sophia-intel

# MCP service logs
kubectl logs -f deployment/telemetry-mcp -n sophia-intel
kubectl logs -f deployment/embedding-mcp -n sophia-intel
kubectl logs -f deployment/brightdata-research-mcp -n sophia-intel
kubectl logs -f deployment/notion-sync-mcp -n sophia-intel
```

## 🔐 **Security Verification**

### **Secrets Audit**
```bash
# Verify all secrets are present
kubectl get secret sophia-secrets-enhanced -n sophia-intel -o yaml | grep -E '^  [a-z].*:'

# Expected secrets:
# - brightdata-api-key
# - dnsimple-api-key  
# - github-pat
# - lambda-cloud-api-key
# - neon-api-key
# - notion-api-key
# - openai-api-key
# - openrouter-api-key
# - qdrant-api-key
# - slack-webhook-url
# - weaviate-admin-api-key
```

### **Network Security**
```bash
# Test CORS headers
curl -H "Origin: https://sophia-intel.ai" \
     -H "Host: api.sophia-intel.ai" \
     -I http://104.171.202.107:32152/health

# Expected: Proper CORS headers in response
```

## 🎉 **Success Criteria**

### **Deployment Success**
- ✅ All 11 pods running (API, Dashboard, 4 MCPs, Weaviate, Qdrant, Kong)
- ✅ All health endpoints responding
- ✅ Kong ingress routing correctly
- ✅ SSL certificates provisioning (Let's Encrypt)

### **Functional Success**
- ✅ AI chat using Claude Sonnet 4
- ✅ Vendor-independent embeddings working
- ✅ Web research via BrightData
- ✅ Vector storage in Weaviate/Qdrant
- ✅ Notion governance sync
- ✅ Telemetry monitoring all services

### **Performance Success**
- ✅ Sub-2-second API responses
- ✅ 99%+ uptime for core services
- ✅ Proper error handling and fallbacks
- ✅ Resource usage within limits

## 📞 **Support & Troubleshooting**

### **Common Issues**
1. **SSL Not Ready**: Use HTTP endpoints until Let's Encrypt completes
2. **Pod Restarts**: Check logs for dependency issues
3. **API Timeouts**: Verify all MCP services are healthy
4. **Memory Issues**: Monitor resource usage with `kubectl top`

### **Emergency Procedures**
```bash
# Restart all services
kubectl rollout restart deployment -n sophia-intel

# Scale down for maintenance
kubectl scale deployment --all --replicas=0 -n sophia-intel

# Scale back up
kubectl scale deployment --all --replicas=1 -n sophia-intel
```

---

## 🚀 **SOPHIA Intel is LIVE and OPERATIONAL!**

**Production Environment**: Lambda Labs K3s Cluster (104.171.202.107)
**Status**: All systems green, ready for production use
**Capabilities**: Full AI platform with governance, monitoring, and multi-service integration

**Test any of the above prompts to verify SOPHIA's complete functionality!** 🎯

