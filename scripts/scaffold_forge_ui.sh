#!/usr/bin/env bash
set -euo pipefail

# Scaffold an external Forge Coding UI (server-only) in a sibling folder.
# Creates an independent Node+TS Fastify app with MCP + Portkey wiring.

TARGET_DIR="${1:-"../worktrees/forge-ui"}"
PORT="${PORT:-3100}"

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

cat > "${TARGET_DIR}/src/server.ts" << EOF
import Fastify from 'fastify'
import { z } from 'zod'
import { loadEnvMaster } from './env.js'
import { planWithLLM } from './portkey.js'
import { fsWrite, gitCommit, memorySearch } from './mcp.js'

loadEnvMaster(process.env.REPO_ENV_MASTER_PATH)

const app = Fastify({ logger: true })
const PORT = Number(process.env.PORT || ${PORT})

app.get('/health', async () => ({ status: 'ok', service: 'forge-ui' }))

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

app.get('/api/providers/vk', async (_req, reply) => {
  const present = Object.keys(process.env).filter(k => k.startsWith('PORTKEY_VK_') && String(process.env[k]).trim())
  return reply.send({ present, count: present.length })
})

app.listen({ port: PORT, host: '0.0.0.0' }).then(() => {
  app.log.info(`Forge UI listening on :${PORT}`)
})
EOF

echo "✅ Forge UI scaffolded at ${TARGET_DIR}"

