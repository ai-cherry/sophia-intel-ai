# 🚀 Simplified Fly.io Deployment (2-Service Architecture)

## Architecture: 2 Services Instead of 6

```
┌─────────────────┐         ┌─────────────────┐
│   sophia-api    │────────▶│  sophia-ui      │
│  (Backend API)  │         │  (Frontend)     │
└─────────────────┘         └─────────────────┘
        │
        ├── Weaviate (embedded or cloud)
        ├── Redis Cloud (existing)
        ├── Lambda Labs API (on-demand GPU)
        └── All LLM APIs (OpenRouter, etc)
```

## Quick Start Deployment

### Step 1: Deploy Backend API
```bash
# Deploy the unified API
fly launch --config fly-unified-api.toml --name sophia-api --region sjc
fly secrets set -a sophia-api < .env.local
fly deploy -a sophia-api
```

### Step 2: Deploy Frontend UI
```bash
# Deploy the UI
fly launch --config fly-agent-ui.toml --name sophia-ui --region sjc  
fly deploy -a sophia-ui
```

### Step 3: Verify Deployment
```bash
# Check status
fly status -a sophia-api
fly status -a sophia-ui

# Test endpoints
curl https://sophia-api.fly.dev/healthz
curl https://sophia-ui.fly.dev
```

## Cost Breakdown

| Service | Monthly Cost | Notes |
|---------|-------------|--------|
| sophia-api | $60-120 | 2-4 instances with auto-scaling |
| sophia-ui | $20-40 | Static site, minimal resources |
| Weaviate Cloud | $75 | Optional - can embed in API |
| Redis Cloud | Free tier | Already configured |
| Lambda Labs | Pay-per-use | ~$0.02 per GPU request |
| **Total** | **$80-235/month** | Much cheaper than $1,260-4,500 |

## Why This Works Better

1. **Simpler**: 2 services instead of 6 = easier to manage
2. **Cheaper**: $80-235/month vs $1,260-4,500/month
3. **Faster**: Deploy in 30 minutes, not 4 days
4. **Flexible**: Lambda GPU on-demand, not 24/7

## Environment Variables

Your existing `.env.local` has everything needed:
- ✅ LAMBDA_API_KEY for GPU
- ✅ WEAVIATE_URL (use cloud or embed)
- ✅ REDIS connection strings
- ✅ All LLM API keys

## Next Steps

1. **Test locally first**:
   ```bash
   ./deploy_local.sh
   ```

2. **Deploy to Fly.io**:
   ```bash
   fly auth token  # Use your token
   fly launch --name sophia-api
   fly deploy
   ```

3. **Monitor & Scale**:
   ```bash
   fly logs -a sophia-api
   fly scale count 2-5 -a sophia-api
   ```

## Lambda Labs GPU Integration

Your app already supports Lambda via API:
```python
# Already in your code
lambda_client = LambdaClient(api_key=os.getenv("LAMBDA_API_KEY"))

# On-demand GPU execution
result = lambda_client.run_inference(
    model="llama-70b",
    prompt="...",
    use_gpu=True
)
```

No need for dedicated GPU instances - just API calls!