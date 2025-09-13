#!/usr/bin/env bash
set -euo pipefail

# Scaffold an external Workbench UI (server-only) in a sibling folder.
# Creates an independent Node+TS Fastify app with Portkey-backed health/logs/console.

TARGET_DIR="${1:-"../worktrees/workbench-ui"}"
PORT="${PORT:-3200}"

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

cat > "${TARGET_DIR}/src/server.ts" << EOF
import Fastify from 'fastify'
import { request } from 'undici'
import { loadEnvMaster } from './env.js'

loadEnvMaster(process.env.REPO_ENV_MASTER_PATH)

const app = Fastify({ logger: true })
const PORT = Number(process.env.PORT || ${PORT})
const PORTKEY_API_KEY = process.env.PORTKEY_API_KEY || ''
const PORTKEY_BASE = process.env.PORTKEY_BASE_URL || 'https://api.portkey.ai/v1'

app.get('/health', async () => ({ status: 'ok', service: 'workbench' }))

app.get('/api/portkey/health', async (_req, reply) => {
  if (!PORTKEY_API_KEY) return reply.code(400).send({ error: 'Missing PORTKEY_API_KEY' })
  try {
    const res = await request(`${PORTKEY_BASE}/models`, {
      method: 'GET',
      headers: { 'x-portkey-api-key': PORTKEY_API_KEY }
    })
    const json = await res.body.json()
    return reply.send({ ok: true, models: Array.isArray(json?.data) ? json.data.length : 0 })
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
  const headers: Record<string, string> = {
    'content-type': 'application/json',
    'x-portkey-api-key': PORTKEY_API_KEY
  }
  const vk = process.env.PORTKEY_VK_ANTHROPIC || process.env.PORTKEY_VK_OPENAI
  if (vk) headers['x-portkey-config'] = JSON.stringify({ targets: [{ virtual_key: vk }] })
  try {
    const res = await request(`${PORTKEY_BASE}/chat/completions`, {
      method: 'POST', headers,
      body: JSON.stringify({ model: 'openai/gpt-4o', messages: [{ role: 'user', content }] })
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

app.listen({ port: PORT, host: '0.0.0.0' }).then(() => {
  app.log.info(`Workbench listening on :${PORT}`)
})
EOF

echo "✅ Workbench scaffolded at ${TARGET_DIR}"

