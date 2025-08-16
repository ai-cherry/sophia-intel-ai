# Northflank GitHub Integration Best Practices

## 🏗️ Build Configuration Best Practices

### **1. Dockerfile Optimization**
```dockerfile
# Use multi-stage builds for smaller images
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:20-alpine AS runtime
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

### **2. Build Context Management**
- **Keep .dockerignore updated** to exclude unnecessary files
- **Minimize build context** - only include what's needed
- **Use specific COPY commands** instead of `COPY . .` when possible

```dockerignore
node_modules
.git
.github
*.md
.env.local
coverage/
.nyc_output
```

### **3. Environment-Specific Builds**
```yaml
# GitHub Actions workflow
- name: Build for Environment
  run: |
    if [ "${{ github.ref }}" = "refs/heads/main" ]; then
      docker build -t $IMAGE_NAME:prod --build-arg NODE_ENV=production .
    else
      docker build -t $IMAGE_NAME:dev --build-arg NODE_ENV=development .
    fi
```

## 🔧 GitHub Actions Workflow Best Practices

### **1. Workflow Structure**
```yaml
name: Deploy to Northflank

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run tests
        run: npm test
      
      - name: Build application
        run: npm run build

  deploy:
    needs: build-and-test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Northflank
        uses: northflank/deploy-to-northflank@v1
        with:
          northflank-api-key: ${{ secrets.NORTHFLANK_API_KEY }}
          project-id: ${{ vars.PROJECT_ID }}
          service-id: ${{ vars.SERVICE_ID }}
```

### **2. Secret Management**
```yaml
# Organization-level secrets (recommended)
secrets:
  NORTHFLANK_API_KEY: "nf-xxx..."
  DATABASE_URL: "postgresql://..."
  API_KEYS: "encrypted-values"

# Repository variables for non-sensitive data
vars:
  PROJECT_ID: "my-project"
  SERVICE_ID: "my-service"
  ENVIRONMENT: "production"
```

### **3. Build Caching Strategies**
```yaml
- name: Setup Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Build and push
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

## 🚀 Northflank Service Configuration

### **1. Service Setup**
```json
{
  "name": "sophia-api",
  "type": "combined-service",
  "deployment": {
    "instances": 2,
    "docker": {
      "configType": "default",
      "context": "./",
      "dockerfile": "./Dockerfile"
    }
  },
  "ports": [
    {
      "name": "http",
      "internalPort": 5000,
      "public": true,
      "protocol": "HTTP"
    }
  ]
}
```

### **2. Environment Variables**
```yaml
# In Northflank service configuration
environment:
  NODE_ENV: production
  PORT: 5000
  DATABASE_URL: ${secret.DATABASE_URL}
  API_KEY: ${secret.API_KEY}
```

### **3. Health Checks**
```yaml
healthcheck:
  path: "/health"
  port: 5000
  initialDelaySeconds: 30
  periodSeconds: 10
```

## 📦 Build Details & Optimization

### **1. Build Performance**
- **Parallel builds** for multiple services
- **Layer caching** to speed up subsequent builds
- **Build-time optimizations** (tree shaking, minification)

```yaml
strategy:
  matrix:
    service: [api, dashboard, worker]
  max-parallel: 3
```

### **2. Build Artifacts**
```yaml
- name: Upload build artifacts
  uses: actions/upload-artifact@v4
  with:
    name: build-${{ github.sha }}
    path: |
      dist/
      build/
      *.tar.gz
```

### **3. Build Monitoring**
```yaml
- name: Build metrics
  run: |
    echo "Build size: $(du -sh dist/)"
    echo "Build time: ${{ steps.build.outputs.time }}"
    echo "Dependencies: $(npm list --depth=0 | wc -l)"
```

## 🔍 Debugging & Troubleshooting

### **1. Build Logs**
```yaml
- name: Debug build
  if: failure()
  run: |
    echo "Node version: $(node --version)"
    echo "NPM version: $(npm --version)"
    echo "Available space: $(df -h)"
    echo "Memory usage: $(free -h)"
```

### **2. Common Issues & Solutions**

| Issue | Solution |
|-------|----------|
| Build timeout | Increase timeout, optimize dependencies |
| Out of memory | Use smaller base images, multi-stage builds |
| Cache misses | Optimize cache keys, use proper cache strategies |
| Failed tests | Run tests locally first, check environment differences |

### **3. Rollback Strategy**
```yaml
- name: Rollback on failure
  if: failure()
  run: |
    nf rollback service $SERVICE_ID \
      --project=$PROJECT_ID \
      --to-previous-deployment
```

## 🛡️ Security Best Practices

### **1. Image Security**
```yaml
- name: Scan image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
    format: 'sarif'
    output: 'trivy-results.sarif'
```

### **2. Dependency Management**
```yaml
- name: Audit dependencies
  run: |
    npm audit --audit-level=high
    npm outdated
```

### **3. Secret Rotation**
- Rotate API keys regularly
- Use short-lived tokens when possible
- Monitor secret usage in logs

## 📊 Monitoring & Observability

### **1. Deployment Metrics**
```yaml
- name: Report deployment
  run: |
    curl -X POST $WEBHOOK_URL \
      -H "Content-Type: application/json" \
      -d '{
        "deployment": "${{ github.sha }}",
        "status": "success",
        "environment": "production"
      }'
```

### **2. Performance Monitoring**
- Set up application performance monitoring (APM)
- Monitor build times and success rates
- Track deployment frequency and lead time

## 🎯 Lessons Learned from SOPHIA Intel

### **What Worked Well:**
1. **Single comprehensive workflow** instead of multiple conflicting ones
2. **Proper secret management** at organization level
3. **Clear separation** of build, test, and deploy phases
4. **Comprehensive error handling** and fallback strategies

### **Common Pitfalls to Avoid:**
1. **Multiple workflows** triggering simultaneously
2. **Missing dependencies** in build environment
3. **Incorrect file paths** in workflow configuration
4. **Insufficient error handling** causing silent failures

### **Recommended Workflow Structure:**
```
.github/workflows/
├── deploy-production.yml    # Main deployment workflow
├── test-pr.yml             # PR validation only
└── security-scan.yml       # Security checks
```

## 🚀 Advanced Patterns

### **1. Blue-Green Deployments**
```yaml
- name: Blue-Green Deploy
  run: |
    # Deploy to staging slot
    nf deploy service $SERVICE_ID-staging
    
    # Run health checks
    ./scripts/health-check.sh $STAGING_URL
    
    # Swap slots
    nf swap-slots $SERVICE_ID
```

### **2. Feature Branch Deployments**
```yaml
- name: Deploy feature branch
  if: github.event_name == 'pull_request'
  run: |
    BRANCH_NAME=${GITHUB_HEAD_REF//\//-}
    nf create service $SERVICE_ID-$BRANCH_NAME \
      --template=$SERVICE_ID
```

### **3. Automated Rollbacks**
```yaml
- name: Health check and rollback
  run: |
    sleep 60  # Wait for deployment
    if ! curl -f $HEALTH_CHECK_URL; then
      echo "Health check failed, rolling back"
      nf rollback service $SERVICE_ID
      exit 1
    fi
```

This comprehensive approach ensures reliable, secure, and efficient deployments using GitHub integration with Northflank.

