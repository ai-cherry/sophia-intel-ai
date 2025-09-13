import { NextResponse } from 'next/server'
import fs from 'node:fs'
import path from 'node:path'

const repoRoot = path.resolve(process.cwd(), '..')
const dataDir = path.join(repoRoot, 'data', 'profiles')
const currentPath = path.join(dataDir, 'current.json')

export async function GET() {
  try {
    const raw = fs.readFileSync(currentPath, 'utf8')
    const json = JSON.parse(raw)
    return NextResponse.json({ ok: true, profile: json })
  } catch {
    // Return a sensible default
    const profile = {
      name: 'default',
      agents: [
        { role: 'architect', aliasOrModel: 'claude', temperature: 0.2, tools: ['reason','plan'] },
        { role: 'coder', aliasOrModel: 'fast', temperature: 0.3, tools: ['write','refactor'] },
        { role: 'reviewer', aliasOrModel: 'claude', temperature: 0.2, tools: ['review','critique'] },
      ],
    }
    return NextResponse.json({ ok: true, profile })
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json()
    if (!body || !body.name || !Array.isArray(body.agents)) {
      return NextResponse.json({ ok: false, error: 'invalid profile' }, { status: 400 })
    }
    fs.mkdirSync(dataDir, { recursive: true })
    fs.writeFileSync(currentPath, JSON.stringify(body, null, 2), 'utf8')
    return NextResponse.json({ ok: true })
  } catch (e:any) {
    return NextResponse.json({ ok: false, error: e?.message ?? 'save-failed' }, { status: 500 })
  }
}

