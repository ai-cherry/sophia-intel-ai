#!/usr/bin/env bash
set -euo pipefail

# Scaffold an external Workbench UI (server-only) in a sibling folder.
# Creates an independent Node+TS Fastify app with Portkey-backed health/logs/console.

TARGET_DIR="${1:-"../worktrees/workbench-ui"}"
PORT="${PORT:-3200}"
IMAGE_NAME="${IMAGE_NAME:-workbench-ui}"

echo "Scaffolding Workbench at: ${TARGET_DIR} (port ${PORT})"
mkdir -p "${TARGET_DIR}/src"

cat > "${TARGET_DIR}/README.md" << 'EOF'
# Workbench (External)

Server-only coding console for VK Health, Routing, Request Logs, and Live Console.

Ports
- App: 3200 (default)

Env Contract (server-side only)
- REPO_ENV_MASTER_PATH: absolute path to <repo>/.env.master
- PORTKEY_API_KEY: your Portkey API key
- PORTKEY_BASE_URL: https://api.portkey.ai/v1 (default)
- Optional: VK envs (PORTKEY_VK_*) to display presence

Endpoints
- GET  /api/portkey/health
- GET  /api/portkey/logs (placeholder)
- POST /api/portkey/console

Dev
```bash
pnpm i || npm i
REPO_ENV_MASTER_PATH=/absolute/path/to/<repo>/.env.master \
  PORTKEY_API_KEY=pk_live_xxx \
  npm run dev
```
EOF

cat > "${TARGET_DIR}/package.json" << EOF
{
  "name": "workbench-ui",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "node --loader ts-node/esm src/server.ts",
    "build": "tsc -p .",
    "start": "node dist/server.js"
  },
  "dependencies": {
    "fastify": "^4.27.2",
    "@fastify/helmet": "^11.2.1",
    "@fastify/compress": "^7.0.2",
    "@fastify/cors": "^9.0.1",
    "@fastify/rate-limit": "^10.3.0",
    "prom-client": "^15.1.3",
    "undici": "^6.19.8"
  },
  "devDependencies": {
    "ts-node": "^10.9.2",
    "typescript": "^5.6.2",
    "@types/node": "^20.11.30"
  }
}
EOF

cat > "${TARGET_DIR}/tsconfig.json" << 'EOF'
{
  "compilerOptions": {
    "module": "ES2022",
    "target": "ES2022",
    "moduleResolution": "Bundler",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "strict": true,
    "outDir": "dist",
    "resolveJsonModule": true
  },
  "include": ["src/**/*"]
}
EOF

cat > "${TARGET_DIR}/src/env.ts" << 'EOF'
import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'

export function loadEnvMaster(absPath?: string) {
  const p = absPath || process.env.REPO_ENV_MASTER_PATH || ''
  if (!p) return
  const path = resolve(p)
  if (!existsSync(path)) return
  const lines = readFileSync(path, 'utf-8').split('\n')
  for (const raw of lines) {
    const line = raw.trim()
    if (!line || line.startsWith('#') || !line.includes('=')) continue
    const idx = line.indexOf('=')
    const key = line.slice(0, idx).trim()
    let val = line.slice(idx + 1).trim()
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1)
    }
    if (!process.env[key]) process.env[key] = val
  }
}
EOF

cat > "${TARGET_DIR}/src/server.ts" << 'EOF'
import Fastify from 'fastify'
import { request } from 'undici'
import { loadEnvMaster } from './env.js'

loadEnvMaster(process.env.REPO_ENV_MASTER_PATH)

const app = Fastify({
  trustProxy: true,
  logger: {
    level: 'info',
    redact: { paths: ['req.headers.authorization', 'res.headers.authorization'], remove: true },
    genReqId: () => Math.random().toString(36).slice(2)
  }
})
await app.register((await import('@fastify/helmet')).default)
await app.register((await import('@fastify/compress')).default, { global: true })
await app.register((await import('@fastify/cors')).default, {
  origin: (origin, cb) => {
    const allowlist = (process.env.CORS_ALLOWLIST || '').split(',').map(s => s.trim()).filter(Boolean)
    if (!origin) return cb(null, allowlist.length === 0 ? false : true)
    if (allowlist.length === 0) return cb(null, false)
    cb(null, allowlist.includes(origin))
  },
  credentials: true
})
await app.register((await import('@fastify/rate-limit')).default, { max: 60, timeWindow: '1 minute' })
const PORT = Number(process.env.PORT || 3200)
const PORTKEY_API_KEY = process.env.PORTKEY_API_KEY || ''
const PORTKEY_BASE = process.env.PORTKEY_BASE_URL || 'https://api.portkey.ai/v1'
const AUTH_BYPASS_TOKEN = process.env.AUTH_BYPASS_TOKEN || ''
const MODEL_ALLOWLIST = (process.env.MODEL_ALLOWLIST || 'openai/gpt-4o,anthropic/claude-3-opus-20240229,google/gemini-2.5-flash').split(',').map(s => s.trim()).filter(Boolean)
const MAX_TOKENS = Number(process.env.MAX_TOKENS || 1000)

if (process.env.NODE_ENV !== 'development' && (!PORTKEY_API_KEY || !PORTKEY_API_KEY.trim())) {
  console.error('PORTKEY_API_KEY is required')
  process.exit(1)
}

app.addHook('onRequest', async (req, reply) => {
  if (AUTH_BYPASS_TOKEN) {
    const auth = req.headers['authorization'] || ''
    if (auth !== `Bearer ${AUTH_BYPASS_TOKEN}`) {
      return reply.code(401).send({ error: 'unauthorized' })
    }
  }
})

app.get('/health', async () => ({ status: 'ok', service: 'workbench' }))

// Metrics (protected via bearer)
const client = await import('prom-client')
const register = new client.Registry()
client.collectDefaultMetrics({ register })
app.get('/metrics', async (_req, reply) => {
  reply.header('content-type', register.contentType)
  return reply.send(await register.metrics())
})

app.get('/api/portkey/health', async (_req, reply) => {
  if (!PORTKEY_API_KEY) return reply.code(400).send({ error: 'Missing PORTKEY_API_KEY' })
  try {
    const res = await request(`${PORTKEY_BASE}/models`, {
      method: 'GET',
      headers: { 'x-portkey-api-key': PORTKEY_API_KEY }
    })
    const json = await res.body.json()
    const models = (Array.isArray(json?.data) ? json.data.map((m:any)=>m.id||m.name) : []).filter((m:string)=>MODEL_ALLOWLIST.includes(m)).length
    return reply.send({ ok: true, models_allowed: models })
  } catch (e: any) {
    return reply.code(502).send({ ok: false, error: String(e) })
  }
})

app.get('/api/portkey/logs', async (_req, reply) => {
  // Placeholder: expose structure with filters
  return reply.send({ items: [], filters: { vk: [], model: [], from: null, to: null } })
})

app.post('/api/portkey/console', async (req, reply) => {
  if (!PORTKEY_API_KEY) return reply.code(400).send({ error: 'Missing PORTKEY_API_KEY' })
  const body: any = req.body || {}
  const content = String(body?.prompt || '')
  if (!content) return reply.code(400).send({ error: 'prompt required' })
  const model = String(body?.model || 'openai/gpt-4o')
  if (!MODEL_ALLOWLIST.includes(model)) return reply.code(400).send({ error: 'model_not_allowed' })
  const max_tokens = Math.min(Number(body?.max_tokens || 512), MAX_TOKENS)
  const headers: Record<string, string> = {
    'content-type': 'application/json',
    'x-portkey-api-key': PORTKEY_API_KEY
  }
  const vk = process.env.PORTKEY_VK_ANTHROPIC || process.env.PORTKEY_VK_OPENAI
  if (vk) headers['x-portkey-config'] = JSON.stringify({ targets: [{ virtual_key: vk }] })
  try {
    const res = await request(`${PORTKEY_BASE}/chat/completions`, {
      method: 'POST', headers,
      body: JSON.stringify({ model, max_tokens, messages: [{ role: 'user', content }], tools: [], tool_choice: 'none' })
    })
    const json = await res.body.json()
    return reply.send({
      ok: true,
      output: json?.choices?.[0]?.message?.content || ''
    })
  } catch (e: any) {
    return reply.code(502).send({ ok: false, error: String(e) })
  }
})

// Contract smoke test: health + minimal console
app.post('/contract-test', async (_req, reply) => {
  try {
    const ok = await (await fetch('http://127.0.0.1:'+PORT+'/api/portkey/health', { headers: { authorization: `Bearer ${AUTH_BYPASS_TOKEN}` } })).json()
    if (!ok?.ok) return reply.code(500).send({ ok: false, step: 'health_failed' })
    const res = await (await fetch('http://127.0.0.1:'+PORT+'/api/portkey/console', {
      method: 'POST',
      headers: { 'content-type': 'application/json', authorization: `Bearer ${AUTH_BYPASS_TOKEN}` },
      body: JSON.stringify({ prompt: 'ping', model: MODEL_ALLOWLIST[0] })
    })).json()
    return reply.send({ ok: true, output_len: (res?.output||'').length })
  } catch (e:any) {
    return reply.code(500).send({ ok: false, error: String(e) })
  }
})

app.listen({ port: PORT, host: '0.0.0.0' }).then(() => {
  app.log.info(`Workbench listening on :${PORT}`)
})
EOF

cat > "${TARGET_DIR}/Dockerfile" << EOF
# syntax=docker/dockerfile:1
FROM node:20.11-alpine AS base
WORKDIR /app

FROM base AS deps
COPY package.json tsconfig.json ./
RUN npm i --no-audit --no-fund

FROM deps AS build
COPY src ./src
RUN npm run build

FROM base AS runner
ENV NODE_ENV=production
COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
EXPOSE ${PORT}
CMD ["node","dist/server.js"]
EOF

cat > "${TARGET_DIR}/fly.toml" << EOF
app = "${IMAGE_NAME}"
primary_region = "sjc"

[http_service]
  auto_start_machines = true
  auto_stop_machines = true
  min_machines_running = 1
  processes = ["app"]
  internal_port = ${PORT}
  force_https = true

[[http_service.checks]]
  interval = "15s"
  timeout = "3s"
  grace_period = "5s"
  method = "GET"
  path = "/health"
EOF

echo "✅ Workbench scaffolded at ${TARGET_DIR}"
