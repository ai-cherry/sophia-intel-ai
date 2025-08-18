# 🚂 Railway Configuration - Specific Answers

## Your Questions Answered:

### 1. **"Do I click on wait for CI or not?"**
**Answer: NO** - Don't click "Wait for CI"
- SOPHIA Intel doesn't use CI/CD pipelines like GitHub Actions
- Railway should deploy directly from the repository
- Leave this unchecked for immediate deployment

### 2. **"There isn't a field for port, what do I put?"**
**Answer: Port goes in Environment Variables**
- Go to **Variables** tab
- Add: `PORT=8000`
- Railway automatically detects and uses this port
- Don't look for a separate port field in Settings

### 3. **"What do I put in root directory?"**
**Answer: Leave it as `/` (root)**
- Your current setting `/` is correct
- This tells Railway to look at the entire repository
- Don't change this - it's already right

### 4. **"Builder nixpacks by default?"**
**Answer: YES, keep Nixpacks**
- Nixpacks is Railway's automatic builder
- It will detect your Python app automatically
- It's better than Docker for this deployment
- Don't change the builder

### 5. **"Cron schedule?"**
**Answer: Leave empty for now**
- SOPHIA Intel doesn't need scheduled tasks for basic deployment
- Celery agents handle background tasks
- You can add cron jobs later if needed
- Skip this field initially

### 6. **"Railway config file? File path?"**
**Answer: Not needed**
- Railway will auto-detect your Python app
- No config file required for basic deployment
- The `requirements.txt` and Python files are enough
- Skip any config file fields

## 🎯 **Exact Configuration Steps:**

### **Variables Tab** - Add These:
```
DATABASE_URL=postgresql://sophia_user@ep-cool-cloud-123456.us-east-1.aws.neon.tech/sophia?sslmode=require
PORT=8000
ENVIRONMENT=production
OPENROUTER_API_KEY=OPENROUTER_API_KEY_REDACTED
LLAMA_API_KEY=llx-MfsEhU0wHNL7PcRN4YEFM3eWcPQggq7edEr52IdnvkHZPPYj
NEON_API_TOKEN=napi_mr8himnznklsfgjpwb78w89q9eqfi0pb9ceg8y8y08a05v68vwrefcxg4gu82sg7
```

### **Settings Tab** - Configure:
- ✅ **Root Directory**: `/` (already correct)
- ✅ **Builder**: Nixpacks (keep default)
- ❌ **Wait for CI**: Leave unchecked
- ❌ **Cron Schedule**: Leave empty
- ❌ **Config File**: Not needed

### **Deploy Settings** (if available):
- **Start Command**: `python -m backend.unified_sophia_app`
- **Health Check**: `/health`

## 🚨 **Critical: Add Redis Service First**

Before deploying, you MUST add Redis:
1. Click **"+ New"** in your Railway project
2. Select **"Add Service"** 
3. Choose **"Database"**
4. Select **"Redis"**
5. After it's created, update your variables:
   - `REDIS_URL=redis://[new-redis-connection-string]`

## 📋 **Step-by-Step Checklist:**

1. ✅ **Add Redis Service** (critical first step)
2. ✅ **Go to Variables tab**
3. ✅ **Add all environment variables above**
4. ✅ **Verify Settings tab** (root directory `/`, Nixpacks builder)
5. ✅ **Don't check "Wait for CI"**
6. ✅ **Leave cron schedule empty**
7. ✅ **Click "Deploy" or let auto-deploy trigger**

## 🎯 **What Railway Will Do Automatically:**

- ✅ Detect Python application
- ✅ Install requirements.txt dependencies
- ✅ Find and run your main application
- ✅ Expose on the PORT you specify
- ✅ Generate a public URL

## ⚠️ **Common Mistakes to Avoid:**

- ❌ Don't look for a separate port field (use PORT variable)
- ❌ Don't change root directory from `/`
- ❌ Don't check "Wait for CI"
- ❌ Don't try to add a config file
- ❌ Don't forget to add Redis service first

## 🚀 **Expected Result:**

After configuration:
- Build will start automatically
- You'll see logs in Deployments tab
- App will be available at generated Railway URL
- Health check at `/health` will work

---

**Start with adding Redis service, then configure variables!** 🎯

