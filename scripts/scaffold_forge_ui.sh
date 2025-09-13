#!/usr/bin/env bash
set -euo pipefail

# Scaffold an external Forge Coding UI (server-only) in a sibling folder.
# Creates an independent Node+TS Fastify app with MCP + Portkey wiring.

TARGET_DIR="${1:-"../worktrees/forge-ui"}"
PORT="${PORT:-3100}"
IMAGE_NAME="${IMAGE_NAME:-forge-ui}"

echo "Scaffolding Forge UI at: ${TARGET_DIR} (port ${PORT})"
mkdir -p "${TARGET_DIR}/src"

cat > "${TARGET_DIR}/README.md" << 'EOF'
# Forge Coding UI (External)

Server-only app for Plan→Patch→Validate coding flow.

Ports
- App: 3100 (default)

Env Contract (server-side only)
- REPO_ENV_MASTER_PATH: absolute path to <repo>/.env.master
- MCP_MEMORY_URL: http://localhost:8081 (default)
- MCP_FS_URL: http://localhost:8082 (default)
- MCP_GIT_URL: http://localhost:8084 (default)
- PORTKEY_API_KEY: your Portkey API key
- Optional: VK envs (PORTKEY_VK_*) to advertise presence

Endpoints
- POST /api/coding/plan
- POST /api/coding/patch?apply=true|false
- POST /api/coding/validate
- GET  /api/providers/vk

Dev
```bash
pnpm i || npm i
REPO_ENV_MASTER_PATH=/absolute/path/to/<repo>/.env.master \
  MCP_MEMORY_URL=http://localhost:8081 \
  MCP_FS_URL=http://localhost:8082 \
  MCP_GIT_URL=http://localhost:8084 \
  PORTKEY_API_KEY=pk_live_xxx \
  npm run dev
```
EOF

cat > "${TARGET_DIR}/package.json" << EOF
{
  "name": "forge-ui",
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
    "zod": "^3.23.8",
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

cat > "${TARGET_DIR}/src/mcp.ts" << 'EOF'
import { request } from 'undici'

const FS = process.env.MCP_FS_URL || 'http://localhost:8082'
const GIT = process.env.MCP_GIT_URL || 'http://localhost:8084'
const MEM = process.env.MCP_MEMORY_URL || 'http://localhost:8081'
const AUTH = process.env.MCP_TOKEN ? { Authorization: `Bearer ${process.env.MCP_TOKEN}` } : {}

export async function fsWrite(path: string, content: string) {
  const url = `${FS}/fs/write`
  const res = await request(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json', ...AUTH },
    body: JSON.stringify({ path, content, create_dirs: true })
  })
  return res.body.json()
}

export async function gitCommit(message: string) {
  const url = `${GIT}/git/commit`
  const res = await request(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json', ...AUTH },
    body: JSON.stringify({ message })
  })
  return res.body.json()
}

export async function memorySearch(query: string) {
  const url = `${MEM}/search?query=${encodeURIComponent(query)}`
  const res = await request(url, { method: 'POST', headers: { ...AUTH } })
  return res.body.json()
}
EOF

cat > "${TARGET_DIR}/src/portkey.ts" << 'EOF'
import { request } from 'undici'

const PORTKEY_API_KEY = process.env.PORTKEY_API_KEY || ''
const PORTKEY_BASE = process.env.PORTKEY_BASE_URL || 'https://api.portkey.ai/v1'

export async function planWithLLM(task: string) {
  if (!PORTKEY_API_KEY) {
    return { steps: ["Add PORTKEY_API_KEY to server env"], impacts: { filesTouched: [] } }
  }
  const headers: Record<string, string> = {
    'content-type': 'application/json',
    'x-portkey-api-key': PORTKEY_API_KEY
  }
  // Example VK routing; customize as needed
  const vk = process.env.PORTKEY_VK_ANTHROPIC || process.env.PORTKEY_VK_OPENAI
  if (vk) headers['x-portkey-config'] = JSON.stringify({ targets: [{ virtual_key: vk }] })

  const res = await request(`${PORTKEY_BASE}/chat/completions`, {
    method: 'POST', headers,
    body: JSON.stringify({
      model: 'openai/gpt-4o',
      messages: [
        { role: 'system', content: 'You produce concise step-by-step coding plans.' },
        { role: 'user', content: `Task: ${task}\nReturn a bullet list of concrete steps.` }
      ]
    })
  })
  const json: any = await res.body.json()
  const text = json?.choices?.[0]?.message?.content || ''
  const steps = text.split(/\n|\r/).map((s: string) => s.trim()).filter(Boolean)
  return { steps, impacts: { filesTouched: [] } }
}
EOF

cat > "${TARGET_DIR}/src/server.ts" << 'EOF'
import Fastify from 'fastify'
import { z } from 'zod'
import { loadEnvMaster } from './env.js'
import { planWithLLM } from './portkey.js'
import { fsWrite, gitCommit, memorySearch } from './mcp.js'

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
await app.register((await import('@fastify/rate-limit')).default, {
  max: 60,
  timeWindow: '1 minute',
  allowList: [],
  ban: 1
})
const PORT = Number(process.env.PORT || 3100)
const AUTH_BYPASS_TOKEN = process.env.AUTH_BYPASS_TOKEN || ''
const REQUIRED_ENVS = ['PORTKEY_API_KEY', 'MCP_MEMORY_URL', 'MCP_FS_URL', 'MCP_GIT_URL', 'MCP_TOKEN']

// Fail fast in non-dev if critical envs are missing
if (process.env.NODE_ENV !== 'development') {
  const missing = REQUIRED_ENVS.filter(k => !process.env[k] || !String(process.env[k]).trim())
  if (missing.length) {
    console.error(`Missing required envs: ${missing.join(', ')}`)
    process.exit(1)
  }
}

app.addHook('onRequest', async (req, reply) => {
  // Require bearer outside dev; optional in dev
  if (process.env.NODE_ENV !== 'development' || AUTH_BYPASS_TOKEN) {
    const auth = req.headers['authorization'] || ''
    if (auth !== `Bearer ${AUTH_BYPASS_TOKEN}`) {
      return reply.code(401).send({ error: 'unauthorized' })
    }
  }
})

app.get('/health', async () => ({ status: 'ok', service: 'forge-ui' }))

// Metrics (protected by bearer via hook)
const client = await import('prom-client')
const register = new client.Registry()
client.collectDefaultMetrics({ register })
const httpHistogram = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request latency',
  labelNames: ['route', 'method', 'status_code']
})
register.registerMetric(httpHistogram)
app.addHook('onResponse', async (req, res) => {
  const route = req.routerPath || req.url || 'unknown'
  httpHistogram.labels({ route, method: req.method, status_code: String(res.statusCode) }).observe((res as any).getResponseTime?.() / 1000 || 0)
})
app.get('/metrics', async (_req, reply) => {
  reply.header('content-type', register.contentType)
  return reply.send(await register.metrics())
})

app.post('/api/coding/plan', async (req, reply) => {
  const schema = z.object({ task: z.string().min(1), context: z.any().optional() })
  const body = schema.parse(req.body)
  const plan = await planWithLLM(body.task)
  return reply.send({ plan, impacts: plan.impacts })
})

app.post('/api/coding/patch', async (req, reply) => {
  const schema = z.object({
    task: z.string().min(1),
    selections: z.array(z.string()).optional(),
    changes: z.array(z.object({ path: z.string(), content: z.string() })).optional()
  })
  const body = schema.parse(req.body)
  const apply = (req.query as any)?.apply === 'true'
  // Policy checks
  const MAX_CHANGES = 10
  const MAX_CONTENT = 200_000 // 200 KB
  if ((body.changes?.length || 0) > MAX_CHANGES) return reply.code(400).send({ error: 'too_many_changes' })
  if ((body.changes || []).some(c => c.path.startsWith('.') || c.path.includes('..') || c.path.includes('node_modules') || c.path.includes('.env'))) {
    return reply.code(400).send({ error: 'invalid_paths' })
  }
  if ((body.changes || []).some(c => c.content.length > MAX_CONTENT)) return reply.code(400).send({ error: 'change_too_large' })
  const diff = (body.changes || []).map(c => `--- a/${c.path}\n+++ b/${c.path}\n@@\n${c.content}`)
  if (apply && body.changes?.length) {
    for (const c of body.changes) await fsWrite(c.path, c.content)
    await gitCommit(body.task)
  }
  return reply.send({ diff: diff.join('\n\n'), applied: Boolean(apply && body.changes?.length), notes: [] })
})

app.post('/api/coding/validate', async (req, reply) => {
  // Minimal stub: leverage memory search as a placeholder signal
  try {
    const r = await memorySearch('TODO')
    return reply.send({ result: 'pass', stats: { passed: 1, failed: 0 }, logs: JSON.stringify(r).slice(0, 400) })
  } catch (e: any) {
    return reply.send({ result: 'fail', stats: { passed: 0, failed: 1 }, logs: String(e) })
  }
})

// Contract test: create dummy file, commit, validate
app.post('/contract-test', async (_req, reply) => {
  const path = 'CONTRACT_TEST.md'
  const content = `# Contract Test\nTimestamp: ${new Date().toISOString()}\n`
  try {
    await fsWrite(path, content)
    await gitCommit('forge contract test')
    const r = await memorySearch('contract test')
    return reply.send({ ok: true, path, result: 'pass', memory: Array.isArray(r) ? r.length : 0 })
  } catch (e: any) {
    return reply.code(500).send({ ok: false, error: String(e) })
  }
})

// Swarm trigger placeholder
app.post('/api/coding/swarm/trigger', async (_req, reply) => {
  return reply.code(202).send({ accepted: true, status: 'queued' })
})

app.get('/api/providers/vk', async (_req, reply) => {
  const present = Object.keys(process.env).filter(k => k.startsWith('PORTKEY_VK_') && String(process.env[k]).trim())
  return reply.send({ present, count: present.length })
})

app.listen({ port: PORT, host: '0.0.0.0' }).then(() => {
  app.log.info(`Forge UI listening on :${PORT}`)
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

echo "✅ Forge UI scaffolded at ${TARGET_DIR}"

# --- GitHub Actions CI (generated) ---
mkdir -p "${TARGET_DIR}/.github/workflows"
cat > "${TARGET_DIR}/.github/workflows/ci.yml" << 'EOF'
name: forge-ci

on:
  push:
  pull_request:

jobs:
  build-and-health:
    runs-on: ubuntu-latest
    env:
      APP_PORT: 3100
      AUTH_BYPASS_TOKEN: ci-token
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci || npm i --no-audit --no-fund
      - run: npm run build
      - name: Start server
        run: |
          nohup env NODE_ENV=production PORT=$APP_PORT AUTH_BYPASS_TOKEN=$AUTH_BYPASS_TOKEN node dist/server.js > server.log 2>&1 &
          sleep 2
          tail -n +1 server.log || true
      - name: Health check
        run: curl -fsS http://127.0.0.1:$APP_PORT/health

  contract-smoke:
    runs-on: ubuntu-latest
    if: ${{ env.MCP_MEMORY_URL != '' && env.MCP_FS_URL != '' && env.MCP_GIT_URL != '' && env.MCP_TOKEN != '' }}
    env:
      APP_PORT: 3100
      AUTH_BYPASS_TOKEN: ci-token
      MCP_MEMORY_URL: ${{ secrets.MCP_MEMORY_URL }}
      MCP_FS_URL: ${{ secrets.MCP_FS_URL }}
      MCP_GIT_URL: ${{ secrets.MCP_GIT_URL }}
      MCP_TOKEN: ${{ secrets.MCP_TOKEN }}
      PORTKEY_API_KEY: ${{ secrets.PORTKEY_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci || npm i --no-audit --no-fund
      - run: npm run build
      - name: Start server
        run: |
          nohup env NODE_ENV=production PORT=$APP_PORT AUTH_BYPASS_TOKEN=$AUTH_BYPASS_TOKEN \
            MCP_MEMORY_URL="$MCP_MEMORY_URL" MCP_FS_URL="$MCP_FS_URL" MCP_GIT_URL="$MCP_GIT_URL" MCP_TOKEN="$MCP_TOKEN" \
            PORTKEY_API_KEY="$PORTKEY_API_KEY" \
            node dist/server.js > server.log 2>&1 &
          sleep 2
      - name: Contract test
        run: |
          curl -fsS -X POST http://127.0.0.1:$APP_PORT/contract-test -H "authorization: Bearer $AUTH_BYPASS_TOKEN"
EOF
