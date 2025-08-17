# 🚂 Railway Deployment Guide for SOPHIA Intel

## Current Status & Issues

### ❌ **Authentication Problem**
- Railway CLI requires browser-based authentication
- Token-based authentication not working with current CLI version
- Need to complete interactive login process

### ✅ **What We Have Ready**
- Complete unified SOPHIA Intel application
- Production-ready Docker configuration
- Environment variables properly configured
- GitHub repository synchronized

## 🔧 **Required Steps to Fix Railway Deployment**

### Step 1: Complete Railway Authentication
```bash
# Interactive login (requires browser)
railway login

# Follow the browser prompts to authenticate
# This creates a local authentication token
```

### Step 2: Create or Link Railway Project
```bash
# Option A: Create new project
railway init

# Option B: Link to existing project (if you have one)
railway link [PROJECT_ID]
```

### Step 3: Configure Environment Variables
```bash
# Set all required environment variables in Railway
railway variables set OPENAI_API_KEY="your-key"
railway variables set OPENROUTER_API_KEY="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"
railway variables set LLAMA_API_KEY="llx-MfsEhU0wHNL7PcRN4YEFM3eWcPQggq7edEr52IdnvkHZPPYj"
railway variables set NEON_API_TOKEN="napi_mr8himnznklsfgjpwb78w89q9eqfi0pb9ceg8y8y08a05v68vwrefcxg4gu82sg7"
railway variables set DATABASE_URL="postgresql://sophia_user@ep-cool-cloud-123456.us-east-1.aws.neon.tech/sophia?sslmode=require"
railway variables set REDIS_URL="redis://redis:6379/0"
```

### Step 4: Add Required Services
```bash
# Add PostgreSQL database (or use Neon connection)
railway add postgresql

# Add Redis for caching and Celery
railway add redis

# Check services
railway status
```

### Step 5: Deploy Application
```bash
# Deploy the unified SOPHIA application
railway up

# Monitor deployment
railway logs
```

## 📋 **Alternative Deployment Methods**

### Method 1: GitHub Integration
1. Connect Railway to your GitHub repository
2. Set up automatic deployments from main branch
3. Configure environment variables in Railway dashboard
4. Deploy automatically on git push

### Method 2: Docker Deployment
1. Build Docker image locally
2. Push to container registry
3. Deploy from registry to Railway

### Method 3: Manual File Upload
1. Create Railway project via web interface
2. Upload project files directly
3. Configure build settings
4. Deploy manually

## 🔧 **Required Files for Railway Deployment**

### 1. Dockerfile (Already Created)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "-m", "backend.unified_sophia_app"]
```

### 2. requirements.txt (Already Created)
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
# ... all other dependencies
```

### 3. railway.json (Optional Configuration)
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "startCommand": "python -m backend.unified_sophia_app",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

## 🌐 **Environment Variables Needed**

### Core Application
- `DATABASE_URL` - Neon PostgreSQL connection
- `REDIS_URL` - Redis cache connection
- `OPENAI_API_KEY` - OpenAI API access
- `OPENROUTER_API_KEY` - OpenRouter API access
- `LLAMA_API_KEY` - LLAMA API access

### Data Sources (Pay Ready Integration)
- `SALESFORCE_API_KEY`
- `HUBSPOT_API_KEY`
- `GONG_API_KEY`
- `INTERCOM_API_KEY`
- `LOOKER_API_KEY`
- `SLACK_BOT_TOKEN`
- `ASANA_API_KEY`
- `LINEAR_API_KEY`
- `FACTOR_AI_API_KEY`
- `NOTION_API_KEY`
- `NETSUITE_API_KEY`

### Security & Monitoring
- `JWT_SECRET_KEY`
- `SENTRY_DSN` (optional)
- `GRAFANA_API_KEY` (optional)

## 🚀 **Immediate Action Plan**

### What You Need to Do:
1. **Complete Railway Login**
   - Run `railway login` in terminal
   - Complete browser authentication
   - Verify with `railway list`

2. **Create/Link Project**
   - Either create new project or link existing
   - Configure project settings

3. **Set Environment Variables**
   - Add all required API keys
   - Configure database connections

4. **Deploy Application**
   - Run `railway up` to deploy
   - Monitor logs and health checks

### What I Can Do Once Authenticated:
1. **Optimize Deployment Configuration**
2. **Set Up Monitoring and Health Checks**
3. **Configure Custom Domains**
4. **Set Up Automatic Deployments**
5. **Test All Endpoints and Features**

## 📊 **Expected Deployment Timeline**

- **Authentication & Setup**: 5 minutes
- **Environment Configuration**: 10 minutes
- **Initial Deployment**: 15 minutes
- **Testing & Validation**: 20 minutes
- **Total Time**: ~50 minutes

## 🎯 **Success Criteria**

✅ Railway authentication completed
✅ Project created/linked successfully
✅ All environment variables configured
✅ Application deployed and running
✅ Health checks passing
✅ All API endpoints responding
✅ Database connections working
✅ Real-time features operational

## 🆘 **Troubleshooting**

### Common Issues:
1. **Authentication Fails**: Clear Railway cache, retry login
2. **Build Fails**: Check Dockerfile and requirements.txt
3. **Environment Variables Missing**: Verify all keys are set
4. **Database Connection Issues**: Check Neon connection string
5. **Port Conflicts**: Ensure PORT environment variable is set

### Support Resources:
- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- GitHub Issues: Check repository for deployment issues

---

**Ready to proceed once Railway authentication is completed!** 🚀

