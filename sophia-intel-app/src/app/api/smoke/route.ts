import { NextResponse } from 'next/server'

async function ok(url: string, init?: RequestInit) {
  try { const r = await fetch(url, { ...init, cache: 'no-store' }); return r.status < 400 } catch { return false }
}

export async function GET() {
  const pk = process.env.PORTKEY_API_KEY
  const gateway = pk ? await ok('https://api.portkey.ai/v1/health', { headers: { 'x-portkey-api-key': pk } }) : false
  const mem = await ok('http://127.0.0.1:8081/health')
  const fs = await ok('http://127.0.0.1:8082/health')
  const git = await ok('http://127.0.0.1:8084/health')
  const models = await (async () => { try { const r = await fetch('http://localhost:3000/api/models',{cache:'no-store'}); return r.status<400 } catch { return false }})()
  const chat = await (async () => {
    try {
      const r = await fetch('http://localhost:3000/api/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ model:'openrouter/google/gemini-1.5-pro', messages:[{role:'user', content:'ping'}] }) })
      return r.status < 400
    } catch { return false }
  })()
  return NextResponse.json({ gateway, mcp:{mem,fs,git}, models, chat })
}
