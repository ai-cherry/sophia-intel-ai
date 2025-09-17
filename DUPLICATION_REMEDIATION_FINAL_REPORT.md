# Sophia Intel AI - Dashboard & Chat Duplication Audit Report

## Executive Summary

Comprehensive audit reveals **multiple dashboard implementations** with significant duplication and security concerns. The repository contains:
- 3 separate UI entry points (Next.js, Vite/React, HTML/JS)
- 3 chat component implementations
- 2 API routing patterns (pages/api and app/api)
- 1 Streamlit dashboard
- Hard-coded URLs and XSS vulnerabilities

## 1. Dashboard/Chat Inventory Table

| Entry Point | Type | Location | Status | Last Modified | Risk Level |
|-------------|------|----------|---------|--------------|------------|
| **src/app/page.tsx** | Next.js App Router | `/src/app/page.tsx` | **ACTIVE (Primary)** | Current | Medium |
| **pages/index.tsx** | Next.js Pages Router | `/pages/index.tsx` | ACTIVE (Redirects) | Current | Low |
| **index.html + src/main.tsx** | Vite/React | `/index.html` + `/src/main.tsx` | **DUPLICATE** | Current | High |
| **app/templates/hub.html** | Static HTML + JS | `/app/templates/hub.html` | **LEGACY** | Sep 16 | High |
| **sophia_chat_dashboard.py** | Streamlit | `/dashboards/` | **ORPHANED** | Sep 14 | Medium |

### Chat Components

| Component | Location | Usage | Issues |
|-----------|----------|-------|--------|
| **UnifiedSophiaChat** | `/src/components/sophia/` | Primary in src/app/page.tsx | Hard-coded WS URL, XSS risk |
| **EnhancedPersistentChat** | `/src/components/shared/` | Unused | Hard-coded URLs |
| **PersistentChat** | `/src/components/shared/` | Unused | Legacy |

### API Routes

| Route | Location | Status | Issues |
|-------|----------|--------|--------|
| **/api/chat/query** | `/pages/api/chat/query.ts` | ACTIVE | Mock SSE simulation |
| **/api/chat/query** | `/src/app/api/chat/query/route.ts` | DUPLICATE | Redundant |
| **/api/bi/metrics** | Both pages & app | DUPLICATE | Inconsistent |
| **/api/flowise/health** | Both pages & app | DUPLICATE | Inconsistent |

## 2. Critical Issues (By Severity)

### 🔴 HIGH SEVERITY

#### H1: XSS Vulnerability in UnifiedSophiaChat
- **Location**: `/src/components/sophia/UnifiedSophiaChat.tsx:562,590`
- **Issue**: `dangerouslySetInnerHTML` without sanitization
```tsx
dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }}
```
- **Risk**: User input or API responses could execute arbitrary JavaScript
- **Fix Required**: Implement DOMPurify or remove dangerous HTML rendering

#### H2: Duplicate Entry Points Creating Bundle Bloat
- **Issue**: Both Vite (`index.html`) and Next.js (`src/app/page.tsx`) mount the same app
- **Impact**: Confusing deployment, potential for serving wrong version
- **Evidence**:
  - `/index.html` → loads `/src/main.tsx`
  - `/src/main.tsx` → imports `./app/page` (same as Next.js)

#### H3: Legacy Hub with Direct Port References
- **Location**: `/app/templates/hub.html` + `/app/static/js/`
- **Issue**: References services on ports 8005, 8501 directly
- **Risk**: Bypasses proxy, exposes internal services

### 🟡 MEDIUM SEVERITY

#### M1: Hard-coded Backend URLs
- **Locations**:
  - `UnifiedSophiaChat.tsx:175`: `ws://127.0.0.1:8000/ws/chat`
  - `EnhancedPersistentChat.tsx:55`: `ws://127.0.0.1:8000/ws/chat`
  - `EnhancedPersistentChat.tsx:117`: `http://127.0.0.1:8000/api/chat`
- **Issue**: No environment variable usage, breaks in production
- **Fix**: Use `process.env.NEXT_PUBLIC_BACKEND_URL`

#### M2: Mock SSE Implementation
- **Location**: `/pages/api/chat/query.ts:36-45`
- **Issue**: Splits response by spaces to simulate streaming
```typescript
const chunks = data.response?.split(' ') || ['Hello', 'from', 'Sophia']
```
- **Impact**: Not real streaming, poor UX for long responses

#### M3: Orphaned Streamlit Dashboard
- **Location**: `/dashboards/sophia_chat_dashboard.py`
- **Issue**: No references in codebase, but contains active code
- **Risk**: May be accidentally deployed or confuse developers

### 🟢 LOW SEVERITY

#### L1: Unused Chat Components
- **Components**: `EnhancedPersistentChat`, `PersistentChat`
- **Issue**: Dead code increasing bundle size
- **Location**: `/src/components/shared/`

#### L2: Duplicate API Routes
- **Issue**: Same endpoints in both `/pages/api/` and `/src/app/api/`
- **Impact**: Maintenance burden, potential inconsistency

#### L3: Misleading Integration Status
- **Location**: `UnifiedSophiaChat` initial greeting
- **Issue**: Claims live connections that may not exist

## 3. Duplication Remediation Plan

### Phase 1: Immediate Actions (Critical)
1. **Remove Vite entry point**
   - Delete: `/index.html`, `/src/main.tsx`, `/vite.config.ts`
   - Impact: Eliminates duplicate mounting point

2. **Add XSS sanitization**
   ```bash
   npm install dompurify @types/dompurify
   ```
   - Update `formatMessage` in `UnifiedSophiaChat.tsx`
   - Sanitize all HTML before rendering

3. **Archive legacy hub**
   - Move `/app/templates/hub.html` → `/archive/legacy-hub/`
   - Move `/app/static/js/` → `/archive/legacy-hub/static/`

### Phase 2: Consolidation (High Priority)
1. **Centralize API routes**
   - Keep: `/pages/api/` (Next.js Pages Router standard)
   - Remove: `/src/app/api/` duplicates
   - Update all imports

2. **Environment variable migration**
   ```typescript
   // Before
   ws://127.0.0.1:8000/ws/chat

   // After
   process.env.NEXT_PUBLIC_WS_URL || 'ws://127.0.0.1:8000/ws/chat'
   ```

3. **Remove unused components**
   - Delete: `EnhancedPersistentChat.tsx`, `PersistentChat.tsx`
   - Update any lingering imports

### Phase 3: Enhancement (Medium Priority)
1. **Implement real SSE**
   - Replace mock streaming in `/pages/api/chat/query.ts`
   - Use proper EventSource API

2. **Add reconnection logic**
   - WebSocket auto-reconnect with exponential backoff
   - Connection status indicator

3. **Archive Streamlit dashboard**
   - Move `/dashboards/` → `/archive/streamlit-dashboard/`
   - Document migration path

## 4. Configuration Recommendations

### Environment Variables Required
```env
# Add to .env.local
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000
NEXT_PUBLIC_WS_URL=ws://127.0.0.1:8000
NEXT_PUBLIC_API_TIMEOUT=30000
```

### TypeScript Configuration
```typescript
// src/config/api.ts
export const API_CONFIG = {
  baseUrl: process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000',
  wsUrl: process.env.NEXT_PUBLIC_WS_URL || 'ws://127.0.0.1:8000',
  timeout: Number(process.env.NEXT_PUBLIC_API_TIMEOUT) || 30000,
}
```

## 5. Testing Recommendations

### Unit Tests Required
1. XSS sanitization test for `formatMessage`
2. WebSocket reconnection logic
3. API fallback behavior

### Integration Tests
1. SSE streaming functionality
2. Chat message persistence
3. Integration status accuracy

### Bundle Analysis
```bash
# Add to package.json
"analyze": "ANALYZE=true next build"
```

## 6. Documentation Updates Needed

1. **README.md**
   - Remove references to multiple dashboards
   - Document single entry point: `http://127.0.0.1:3000`

2. **CLAUDE.md**
   - Update to reflect consolidated structure
   - Remove legacy service references

3. **Developer Guide**
   - Document new environment variables
   - Explain consolidated API structure

## 7. Files to Keep vs Delete

### ✅ Keep (Canonical)
```
src/app/page.tsx                    # Primary entry
src/app/layout.tsx                  # App layout
src/components/sophia/UnifiedSophiaChat.tsx  # Primary chat (after XSS fix)
pages/api/**                        # API routes
pages/_app.tsx                      # Next.js app wrapper
pages/index.tsx                     # Redirect to app
```

### ❌ Delete/Archive
```
index.html                          # Vite entry
src/main.tsx                        # Vite mount
vite.config.ts                      # Vite config
app/templates/hub.html              # Legacy hub
app/static/js/**                    # Legacy JS
src/app/api/**                      # Duplicate API routes
src/components/shared/EnhancedPersistentChat.tsx
src/components/shared/PersistentChat.tsx
dashboards/sophia_chat_dashboard.py # Orphaned Streamlit
```

## 8. Migration Commands

```bash
# Create archive directory
mkdir -p archive/{vite,legacy-hub,streamlit,duplicate-components}

# Archive files
mv index.html src/main.tsx vite.config.ts archive/vite/
mv app/templates/hub.html app/static archive/legacy-hub/
mv dashboards archive/streamlit/
mv src/components/shared/*PersistentChat.tsx archive/duplicate-components/

# Remove duplicate API routes
rm -rf src/app/api

# Install security dependencies
npm install dompurify @types/dompurify

# Run validation
npm run build
npm run validate:architecture
```

## Conclusion

The Sophia Intel AI codebase requires immediate attention to:
1. **Security**: Fix XSS vulnerability in chat component
2. **Architecture**: Remove duplicate entry points and API routes
3. **Configuration**: Centralize all environment variables
4. **Maintenance**: Archive legacy code properly

Estimated effort: 2-3 days for complete remediation
Risk if unaddressed: Production security incident, deployment confusion, maintenance overhead

---

Generated: 2025-01-17
Audit Version: 1.0.0