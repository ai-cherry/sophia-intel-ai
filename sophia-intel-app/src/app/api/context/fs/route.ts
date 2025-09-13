import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const pattern = searchParams.get('pattern') || '*'
  try {
    const r = await fetch(`http://127.0.0.1:8082/index?pattern=${encodeURIComponent(pattern)}`, { cache: 'no-store' })
    if (!r.ok) return NextResponse.json({ ok: false, files: [], error: `fs:${r.status}` }, { status: 200 })
    const data = await r.json()
    const files: string[] = Array.isArray(data) ? data : (Array.isArray(data?.files) ? data.files : [])
    return NextResponse.json({ ok: true, files })
  } catch (e:any) {
    return NextResponse.json({ ok: false, files: [], error: e?.message ?? 'fs-failed' })
  }
}

export async function POST(request: Request) {
  // Read snippet for a file
  try {
    const body = await request.json()
    const { path, start, end } = body || {}
    if (!path) return NextResponse.json({ error: 'path required' }, { status: 400 })
    const r = await fetch('http://127.0.0.1:8082/read', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, start, end }),
      cache: 'no-store',
    })
    if (!r.ok) return NextResponse.json({ ok: false, error: `fs-read:${r.status}` }, { status: 200 })
    const data = await r.json()
    return NextResponse.json({ ok: true, content: data?.content ?? '' })
  } catch (e:any) {
    return NextResponse.json({ ok: false, error: e?.message ?? 'fs-read-failed' })
  }
}

