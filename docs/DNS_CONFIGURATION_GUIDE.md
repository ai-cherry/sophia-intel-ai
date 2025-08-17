# SOPHIA Intel DNS Configuration Guide

## 🎯 Overview

This guide provides the DNS configuration needed for SOPHIA Intel production deployment with proper domain routing and SSL certificates.

## 🌐 Domain Structure

### Primary Domain: `sophia-intel.ai`

```
sophia-intel.ai                    → Main application (Railway)
www.sophia-intel.ai               → Main application (Railway)
api.sophia-intel.ai               → API Gateway (Railway)
dashboard.sophia-intel.ai         → Monitoring Dashboard (Railway)
mcp.sophia-intel.ai               → MCP Server (Railway)
inference-primary.sophia-intel.ai → Lambda Labs Primary (192.222.51.223)
inference-secondary.sophia-intel.ai → Lambda Labs Secondary (192.222.50.242)
```

## 📋 Required DNS Records

### DNSimple Configuration

```dns
# Main application
@ IN CNAME sophia-intel-production.up.railway.app.
www IN CNAME sophia-intel-production.up.railway.app.

# API services
api IN CNAME api-gateway-production.up.railway.app.
dashboard IN CNAME dashboard-production.up.railway.app.
mcp IN CNAME mcp-server-production.up.railway.app.

# Lambda Labs inference servers
inference-primary IN A 192.222.51.223
inference-secondary IN A 192.222.50.242

# Email and verification
@ IN MX 10 mail.sophia-intel.ai.
@ IN TXT "v=spf1 include:_spf.google.com ~all"
_dmarc IN TXT "v=DMARC1; p=quarantine; rua=mailto:dmarc@sophia-intel.ai"
```

### Alternative: Cloudflare Configuration

If using Cloudflare instead of DNSimple:

```dns
# Main application (Proxied)
sophia-intel.ai CNAME sophia-intel-production.up.railway.app (Proxied: Yes)
www CNAME sophia-intel-production.up.railway.app (Proxied: Yes)

# API services (Proxied for security)
api CNAME api-gateway-production.up.railway.app (Proxied: Yes)
dashboard CNAME dashboard-production.up.railway.app (Proxied: Yes)
mcp CNAME mcp-server-production.up.railway.app (Proxied: Yes)

# Lambda Labs servers (DNS Only - no proxy for direct access)
inference-primary A 192.222.51.223 (Proxied: No)
inference-secondary A 192.222.50.242 (Proxied: No)
```

## 🔒 SSL/TLS Configuration

### Railway SSL Certificates

Railway automatically provides SSL certificates for custom domains. Configure in Railway dashboard:

1. **Add Custom Domain**: Go to each service → Settings → Domains
2. **Add Domain**: Enter the subdomain (e.g., `api.sophia-intel.ai`)
3. **Verify DNS**: Railway will verify the CNAME record
4. **SSL Certificate**: Automatically provisioned via Let's Encrypt

### Required Domain Configurations

```yaml
Services:
  sophia-intel-production:
    domains:
      - sophia-intel.ai
      - www.sophia-intel.ai
  
  api-gateway-production:
    domains:
      - api.sophia-intel.ai
  
  dashboard-production:
    domains:
      - dashboard.sophia-intel.ai
  
  mcp-server-production:
    domains:
      - mcp.sophia-intel.ai
```

## 🚀 Deployment Steps

### Step 1: Configure Railway Services

```bash
# Set custom domains in Railway
railway domain add sophia-intel.ai
railway domain add www.sophia-intel.ai
railway domain add api.sophia-intel.ai
railway domain add dashboard.sophia-intel.ai
railway domain add mcp.sophia-intel.ai
```

### Step 2: Update DNS Records

Using DNSimple API (when proper access is available):

```bash
# Export DNSimple API key
export DNSIMPLE_API_KEY="your_api_key_here"

# Run DNS configuration script
python3 scripts/configure_dns.py
```

Manual DNS configuration:
1. Log into DNSimple dashboard
2. Navigate to sophia-intel.ai domain
3. Add the CNAME records listed above
4. Verify propagation with `dig` or online tools

### Step 3: Verify SSL Certificates

```bash
# Check SSL certificate status
curl -I https://sophia-intel.ai
curl -I https://api.sophia-intel.ai
curl -I https://dashboard.sophia-intel.ai
curl -I https://mcp.sophia-intel.ai

# Verify Lambda Labs direct access
curl -I http://inference-primary.sophia-intel.ai:8000/health
curl -I http://inference-secondary.sophia-intel.ai:8000/health
```

## 🔧 Environment Variables

Update environment variables to use custom domains:

```bash
# Production URLs
ORCHESTRATOR_URL=https://api.sophia-intel.ai
DASHBOARD_URL=https://dashboard.sophia-intel.ai
MCP_BASE_URL=https://mcp.sophia-intel.ai
API_GATEWAY_URL=https://api.sophia-intel.ai

# Lambda Labs inference endpoints
LAMBDA_PRIMARY_URL=http://inference-primary.sophia-intel.ai:8000
LAMBDA_SECONDARY_URL=http://inference-secondary.sophia-intel.ai:8000

# CORS configuration
CORS_ALLOWED_ORIGINS=https://sophia-intel.ai,https://www.sophia-intel.ai,https://dashboard.sophia-intel.ai
```

## 📊 Health Check Endpoints

After DNS configuration, verify all services:

```bash
# Main application
curl https://sophia-intel.ai/health
curl https://www.sophia-intel.ai/health

# API services
curl https://api.sophia-intel.ai/health
curl https://dashboard.sophia-intel.ai/health
curl https://mcp.sophia-intel.ai/health

# Lambda Labs inference
curl http://inference-primary.sophia-intel.ai:8000/health
curl http://inference-secondary.sophia-intel.ai:8000/health
```

## 🔍 Troubleshooting

### DNS Propagation Issues

```bash
# Check DNS propagation
dig sophia-intel.ai
dig www.sophia-intel.ai
dig api.sophia-intel.ai

# Check from different locations
nslookup sophia-intel.ai 8.8.8.8
nslookup sophia-intel.ai 1.1.1.1
```

### SSL Certificate Issues

```bash
# Check certificate details
openssl s_client -connect sophia-intel.ai:443 -servername sophia-intel.ai

# Verify certificate chain
curl -vI https://sophia-intel.ai
```

### Railway Domain Verification

1. Check Railway dashboard for domain status
2. Verify CNAME records are correct
3. Wait for SSL certificate provisioning (up to 24 hours)
4. Check Railway logs for any domain-related errors

## 📈 Monitoring

### DNS Monitoring

Set up monitoring for:
- DNS resolution times
- SSL certificate expiration
- Domain accessibility from different regions

### Health Check Integration

Update monitoring dashboard to check:
- All custom domain endpoints
- SSL certificate status
- DNS resolution health

## 🔄 Maintenance

### Regular Tasks

- Monitor SSL certificate expiration (auto-renewed by Railway)
- Check DNS propagation after changes
- Verify all endpoints are accessible
- Update CORS origins when adding new domains

### Updates

When adding new services:
1. Create Railway service
2. Add custom domain in Railway
3. Update DNS records
4. Update environment variables
5. Test SSL certificate provisioning

---

## 📋 Current Status

### ✅ Completed
- Lambda Labs GH200 servers operational
- Inference endpoints responding
- DNS configuration documented

### 🔄 In Progress
- Railway service deployment
- Custom domain configuration
- SSL certificate setup

### ⏳ Pending
- DNSimple API access resolution
- DNS record creation
- End-to-end testing

---

**Note**: This configuration assumes Railway deployment is complete. Adjust domain names and endpoints based on actual Railway service URLs.

