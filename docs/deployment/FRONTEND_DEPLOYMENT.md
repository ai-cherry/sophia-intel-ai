# Frontend Deployment Guide

## Overview

The SOPHIA Intel dashboard is a React application built with Vite. This guide covers deployment considerations, configuration, and troubleshooting.

## Build Process

### 1. Install Dependencies

```bash
cd apps/dashboard
npm install
```

### 2. Build for Production

```bash
npm run build
```

This creates a `dist/` directory with optimized static files.

### 3. Preview Build

```bash
npm run preview
```

## Configuration

### Critical Vite Settings

The most important configuration is in `vite.config.js`:

```javascript
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: '0.0.0.0',        // Development server
    port: 5173,
    strictPort: false
  },
  preview: {
    host: '0.0.0.0',        // CRITICAL for production
    port: 8080,
    strictPort: false,
    allowedHosts: true      // CRITICAL for external access
  }
})
```

### Environment Variables

Create `.env.production` for production builds:

```bash
VITE_API_BASE_URL=https://api.sophia-intel.ai
VITE_WS_URL=wss://api.sophia-intel.ai/ws
```

## Deployment Methods

### Method 1: Static File Serving

After building, serve the `dist/` directory with any static file server:

```bash
# Python HTTP server
cd dist && python3 -m http.server 8080

# Node.js serve
npx serve dist -p 8080

# Nginx
# Copy dist/ contents to /var/www/html/
```

### Method 2: Vite Preview Server

For development-like environments:

```bash
npm run preview
```

**Important**: Ensure `allowedHosts: true` is set for external access.

### Method 3: Docker

```dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Production Considerations

### 1. API Configuration

Update API endpoints for production:

```javascript
// src/config/api.js
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';
```

### 2. SSL/HTTPS

Ensure all API calls use HTTPS in production:

```javascript
const API_BASE_URL = 'https://api.sophia-intel.ai';
const WS_URL = 'wss://api.sophia-intel.ai/ws';
```

### 3. Performance Optimization

The build process includes:
- Code splitting
- Asset optimization
- Tree shaking
- Minification

Monitor bundle size and consider dynamic imports for large components.

## Troubleshooting

### Blank Screen on External Domains

**Symptom**: Dashboard loads on localhost but shows blank screen on production domain.

**Cause**: Vite host restrictions.

**Solution**: Set `allowedHosts: true` in `vite.config.js`.

### API Connection Errors

**Symptom**: "Connection Error" or failed API requests.

**Solutions**:
1. Check `VITE_API_BASE_URL` environment variable
2. Verify CORS settings on backend
3. Ensure API server is accessible from frontend domain

### Build Failures

**Symptom**: `npm run build` fails with errors.

**Solutions**:
1. Clear node_modules and reinstall: `rm -rf node_modules && npm install`
2. Check for TypeScript errors: `npm run type-check`
3. Verify all imports are correct

### Large Bundle Size Warning

**Symptom**: Vite warns about chunks larger than 500 kB.

**Solutions**:
1. Use dynamic imports for large components
2. Configure manual chunks in `vite.config.js`
3. Analyze bundle with `npm run build -- --analyze`

## Monitoring

### Performance Metrics

Monitor these metrics in production:
- First Contentful Paint (FCP)
- Largest Contentful Paint (LCP)
- Time to Interactive (TTI)
- Bundle size

### Error Tracking

Implement error tracking:

```javascript
// src/utils/errorTracking.js
window.addEventListener('error', (event) => {
  console.error('Frontend error:', event.error);
  // Send to monitoring service
});
```

## Security

### Content Security Policy

Implement CSP headers:

```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';">
```

### Environment Variables

Never expose sensitive data in frontend environment variables. All `VITE_*` variables are publicly accessible.

## Related Documentation

- [Vite Host Fix](../VITE_HOST_FIX.md)
- [Environment Variables](../environment-variables.md)
- [Main Deployment Guide](./README.md)

