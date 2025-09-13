import { NextResponse } from 'next/server'

async function httpOk(url: string, init?: RequestInit): Promise<boolean> {
  try {
    const ctrl = new AbortController()
    const t = setTimeout(() => ctrl.abort(), 2000)
    const r = await fetch(url, { ...init, signal: ctrl.signal, cache: 'no-store' })
    clearTimeout(t)
    return r.status < 400
  } catch {
    return false
  }
}

export async function GET() {
  const pk = process.env.PORTKEY_API_KEY
  const gatewayOK = pk ? await httpOk('https://api.portkey.ai/v1/health', { headers: { 'x-portkey-api-key': pk } }) : false
  const memOK = await httpOk('http://127.0.0.1:8081/health')
  const fsOK = await httpOk('http://127.0.0.1:8082/health')
  const gitOK = await httpOk('http://127.0.0.1:8084/health')
  return NextResponse.json({ gateway: { ok: gatewayOK, provider: gatewayOK ? 'portkey' : 'none' }, mcp: { memory: memOK, fs: fsOK, git: gitOK } })
}
