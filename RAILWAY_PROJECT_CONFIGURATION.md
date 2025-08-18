# 🚂 Railway Project Configuration Guide

## Current Railway Project Status
- ✅ **Project**: `sophia-backend` 
- ✅ **Source Repo**: `ai-cherry/sophia-intel` (connected)
- ✅ **Branch**: `main` (connected to production)
- ✅ **Root Directory**: `/` (correct)

## 🔧 **Required Configuration Steps**

### 1. **Variables Tab** - Set Environment Variables
Click on **Variables** and add these essential variables:

```bash
# Core Application
DATABASE_URL=postgresql://sophia_user@ep-cool-cloud-123456.us-east-1.aws.neon.tech/sophia?sslmode=require
REDIS_URL=redis://redis:6379/0
PORT=8000
ENVIRONMENT=production

# AI Services
OPENAI_API_KEY=your-openai-key-here
OPENROUTER_API_KEY=OPENROUTER_API_KEY_REDACTED
LLAMA_API_KEY=llx-MfsEhU0wHNL7PcRN4YEFM3eWcPQggq7edEr52IdnvkHZPPYj

# Database & Infrastructure
NEON_API_TOKEN=napi_mr8himnznklsfgjpwb78w89q9eqfi0pb9ceg8y8y08a05v68vwrefcxg4gu82sg7
NEON_PROJECT=sophia

# Security
JWT_SECRET_KEY=your-secure-jwt-secret-key-here
ENCRYPTION_KEY=your-32-byte-encryption-key-here

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### 2. **Settings Tab** - Configure Build & Deploy
Click on **Settings** and configure:

#### **Build Settings**
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python -m backend.unified_sophia_app`
- **Dockerfile**: Use existing `Dockerfile.unified`

#### **Deploy Settings**
- **Health Check Path**: `/health`
- **Health Check Timeout**: `300` seconds
- **Port**: `8000`

#### **Environment Settings**
- **Python Version**: `3.11`
- **Node.js**: Not needed (Python app)

### 3. **Add Required Services**
You need to add these services to your project:

#### **Add Redis Service**
1. Click **"+ New"** in your project
2. Select **"Database"** 
3. Choose **"Redis"**
4. This will provide the Redis URL for caching and Celery

#### **PostgreSQL Database**
- You're already using Neon, so this is configured via `DATABASE_URL`
- No additional Railway database needed

### 4. **Deploy Configuration**
Click the **"Deploy"** button or wait for automatic deployment after configuration.

## 📋 **Step-by-Step Action Plan**

### **Immediate Actions Needed:**

1. **Click "Variables" Tab**
   - Add all environment variables listed above
   - Make sure to use your actual API keys

2. **Click "Settings" Tab**
   - Set Start Command: `python -m backend.unified_sophia_app`
   - Set Health Check Path: `/health`
   - Verify Port: `8000`

3. **Add Redis Service**
   - Click "+ New" in project
   - Add Redis database
   - Update `REDIS_URL` variable with the new Redis connection string

4. **Apply Changes**
   - Click "Apply 2 changes" button you mentioned
   - This will trigger a new deployment

5. **Monitor Deployment**
   - Go to "Deployments" tab
   - Watch build logs
   - Verify health checks pass

## 🔍 **Files Railway Will Use**

Railway will automatically detect and use:
- ✅ `requirements.txt` (for Python dependencies)
- ✅ `backend/unified_sophia_app.py` (main application)
- ✅ `Dockerfile.unified` (if Docker build preferred)

## 🚨 **Critical Environment Variables**

**Must be set for deployment to work:**
```bash
DATABASE_URL=postgresql://...  # Neon connection
REDIS_URL=redis://...          # Redis connection  
OPENAI_API_KEY=sk-...          # AI functionality
PORT=8000                      # Railway port
ENVIRONMENT=production         # App configuration
```

## 🎯 **Expected Deployment Flow**

1. **Configure Variables** → 2 minutes
2. **Add Redis Service** → 1 minute  
3. **Apply Changes** → Triggers deployment
4. **Build Process** → 3-5 minutes
5. **Health Checks** → 1 minute
6. **Live Application** → Ready!

## ✅ **Success Indicators**

After configuration, you should see:
- ✅ Build logs showing successful pip install
- ✅ Application starting on port 8000
- ✅ Health check at `/health` returning 200
- ✅ Public URL accessible
- ✅ No error messages in logs

## 🆘 **If Deployment Fails**

Check these common issues:
1. **Missing Environment Variables** - Verify all required vars are set
2. **Port Configuration** - Ensure PORT=8000 is set
3. **Start Command** - Verify: `python -m backend.unified_sophia_app`
4. **Dependencies** - Check requirements.txt includes all packages
5. **Health Check** - Ensure `/health` endpoint is accessible

---

**Ready to configure! Start with the Variables tab and add the environment variables.** 🚀

