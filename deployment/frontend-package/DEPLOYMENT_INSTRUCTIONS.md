
# 🚀 SOPHIA Intel Frontend Deployment Instructions

## 📦 Deployment Package Location
/home/ubuntu/sophia-intel/deployment/frontend-package

## 🌐 Railway Deployment (Recommended)

### Method 1: Railway Dashboard
1. Visit https://railway.app/dashboard
2. Click "New Project" → "Deploy from GitHub repo"
3. Select repository: ai-cherry/sophia-intel
4. Set root directory: apps/dashboard
5. Railway will auto-detect Dockerfile and deploy

### Method 2: Railway CLI (if token is valid)
```bash
cd /home/ubuntu/sophia-intel/deployment/frontend-package
railway login
railway init
railway up
```

## 🐳 Docker Deployment (Alternative)

### Build and Run Locally
```bash
cd /home/ubuntu/sophia-intel/deployment/frontend-package
docker build -t sophia-frontend .
docker run -p 80:80 sophia-frontend
```

### Deploy to Container Platform
```bash
# Tag for registry
docker tag sophia-frontend your-registry/sophia-frontend:latest

# Push to registry
docker push your-registry/sophia-frontend:latest

# Deploy to your container platform
```

## ☁️ Static Hosting Deployment

### Netlify
```bash
cd /home/ubuntu/sophia-intel/deployment/frontend-package/dist
# Upload dist folder to Netlify
# Configure redirects for SPA routing
```

### Vercel
```bash
cd /home/ubuntu/sophia-intel/deployment/frontend-package
npx vercel --prod
```

### AWS S3 + CloudFront
```bash
cd /home/ubuntu/sophia-intel/deployment/frontend-package/dist
aws s3 sync . s3://your-bucket-name
# Configure CloudFront distribution
```

## 🔧 Environment Variables (if needed)
```
NODE_ENV=production
VITE_API_URL=https://sophia-backend-production-1fc3.up.railway.app
```

## 🌐 Custom Domain Configuration
After deployment, configure DNS:
```
www.sophia-intel.ai → [deployment-url]
sophia-intel.ai → [deployment-url]
api.sophia-intel.ai → sophia-backend-production-1fc3.up.railway.app
```

## ✅ Verification Steps
1. Visit deployment URL
2. Check SOPHIA logo loads correctly
3. Test dashboard functionality
4. Verify backend API connectivity
5. Test responsive design on mobile

## 📋 Files Included in Package
- Dockerfile (multi-stage build)
- nginx.conf (production server config)
- railway.json (Railway deployment config)
- package.json (dependencies)
- dist/ (built static files)
- src/ (source code for rebuilding)

The deployment package is ready for production deployment to any platform.
