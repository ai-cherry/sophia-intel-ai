# Vite Host Configuration Fix

## Problem

The SOPHIA Intel dashboard was experiencing blank screens and "This host is not allowed" errors when accessed from external domains. This was preventing proper deployment to production domains like www.sophia-intel.ai.

## Root Cause

Vite's development and preview servers have built-in security restrictions:

1. **Host Binding**: By default, Vite only listens on localhost
2. **Allowed Hosts**: Vite blocks requests from external hosts to prevent DNS rebinding attacks
3. **CORS Protection**: External domains are rejected unless explicitly allowed

## Solution

### 1. Update Vite Configuration

File: `apps/dashboard/vite.config.js`

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: false
  },
  preview: {
    host: '0.0.0.0',        // CRITICAL: Listen on all addresses
    port: 8080,
    strictPort: false,
    allowedHosts: true      // CRITICAL: Allow any host
  }
})
```

### 2. Key Configuration Options

| Option | Purpose | Required Value |
|--------|---------|----------------|
| `host: '0.0.0.0'` | Listen on all network interfaces | Required for external access |
| `allowedHosts: true` | Allow requests from any host | Required for production domains |
| `port: 8080` | Consistent port for production | Recommended |

### 3. Alternative Secure Configuration

For production environments where you want to restrict hosts:

```javascript
preview: {
  host: '0.0.0.0',
  port: 8080,
  allowedHosts: [
    'sophia-intel.ai',
    'www.sophia-intel.ai',
    'localhost',
    '127.0.0.1'
  ]
}
```

## Testing the Fix

### Before Fix
- ❌ Blank screens on external domains
- ❌ "This host is not allowed" error messages
- ❌ CORS errors in browser console

### After Fix
- ✅ Dashboard loads properly on all domains
- ✅ All components render correctly
- ✅ No host-related errors

## Deployment Impact

This fix is **CRITICAL** for:

1. **Production Deployment**: Enables access from www.sophia-intel.ai
2. **Development**: Allows team access from different machines
3. **CI/CD**: Enables automated testing on external hosts
4. **Mobile Testing**: Allows mobile device access during development

## Security Considerations

### Using `allowedHosts: true`

**Pros:**
- Simple configuration
- Works with any domain
- No maintenance required

**Cons:**
- Less secure (allows any host)
- Potential for DNS rebinding attacks

### Using Specific Host List

**Pros:**
- More secure
- Explicit control over allowed domains
- Better for production environments

**Cons:**
- Requires maintenance when adding new domains
- Can break if domains change

## Recommendation

- **Development**: Use `allowedHosts: true` for flexibility
- **Production**: Use specific host list for security
- **Always**: Use `host: '0.0.0.0'` for external access

## Related Documentation

- [Vite Configuration Reference](https://vitejs.dev/config/)
- [Vite Security Considerations](https://vitejs.dev/config/server-options.html#server-host)
- [SOPHIA Deployment Guide](./deployment/README.md)

## Commit Reference

This fix was implemented in commit: `4518414` - "fix: Resolve Vite host restrictions - SOPHIA Intel dashboard now fully accessible with allowedHosts: true"

