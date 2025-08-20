# 🚀 SOPHIA v4.1.1 - Complete Fly.io Deployment Guide

## Prerequisites
1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Login to Fly.io: `flyctl auth login` (opens browser)
3. Clone the repo: `git clone https://github.com/ai-cherry/sophia-intel.git`

## 1. Create All Apps

```bash
cd sophia-intel

# Create apps (run these one by one)
flyctl apps create sophia-dashboard --org personal
flyctl apps create sophia-code --org personal  
flyctl apps create sophia-context --org personal
flyctl apps create sophia-memory --org personal
flyctl apps create sophia-research --org personal
flyctl apps create sophia-business --org personal
```

## 2. Deploy Dashboard (Main UI)

```bash
cd dashboard

# Deploy dashboard
flyctl deploy --config fly.toml --app sophia-dashboard

# Get URL
flyctl status --app sophia-dashboard
```

## 3. Deploy MCP Services

```bash
cd ../mcp_servers

# Deploy each service
flyctl deploy --config ../fly/sophia-code.fly.toml --app sophia-code
flyctl deploy --config ../fly/sophia-context.fly.toml --app sophia-context  
flyctl deploy --config ../fly/sophia-memory.fly.toml --app sophia-memory
flyctl deploy --config ../fly/sophia-research.fly.toml --app sophia-research
flyctl deploy --config ../fly/sophia-business.fly.toml --app sophia-business
```

## 4. Set Environment Variables

```bash
# Dashboard secrets
flyctl secrets set \
  OPENAI_API_KEY="your-key-here" \
  ANTHROPIC_API_KEY="your-key-here" \
  GEMINI_API_KEY="your-key-here" \
  GITHUB_TOKEN="your-token-here" \
  GONG_API_KEY="your-key-here" \
  ASANA_ACCESS_TOKEN="your-token-here" \
  LINEAR_API_KEY="your-key-here" \
  NOTION_API_KEY="your-key-here" \
--app sophia-dashboard

# Repeat for each service with their required keys
```

## 5. Verify Deployment

```bash
# Check all services are healthy
curl https://sophia-dashboard.fly.dev/healthz
curl https://sophia-code.fly.dev/healthz
curl https://sophia-context.fly.dev/healthz
curl https://sophia-memory.fly.dev/healthz
curl https://sophia-research.fly.dev/healthz
curl https://sophia-business.fly.dev/healthz
```

## 6. Your Production URLs

After deployment, you'll have:
- **Dashboard:** https://sophia-dashboard.fly.dev
- **Code Service:** https://sophia-code.fly.dev
- **Context Service:** https://sophia-context.fly.dev
- **Memory Service:** https://sophia-memory.fly.dev
- **Research Service:** https://sophia-research.fly.dev
- **Business Service:** https://sophia-business.fly.dev

## Troubleshooting

If deployment fails:
1. Check `flyctl logs --app sophia-dashboard`
2. Verify all required files are present
3. Check environment variables are set
4. Ensure Docker builds successfully locally

## Alternative: Use Current Working URL

**SOPHIA is already deployed and working at:**
**https://j6h5i7cpydeg.manus.space**

This URL works from any browser, anywhere in the world, right now.

