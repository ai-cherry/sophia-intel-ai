import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const mode = searchParams.get('mode') || 'symbols' // symbols|deps
  const query = searchParams.get('query') || ''
  const file = searchParams.get('file') || ''
  try {
    let url = ''
    if (mode === 'deps' && file) url = `http://127.0.0.1:8084/deps?file=${encodeURIComponent(file)}`
    else url = `http://127.0.0.1:8084/symbols?query=${encodeURIComponent(query)}`
    const r = await fetch(url, { cache: 'no-store' })
    if (!r.ok) return NextResponse.json({ ok: false, results: [], error: `git:${r.status}` }, { status: 200 })
    const data = await r.json()
    const results = Array.isArray(data) ? data : (Array.isArray(data?.results) ? data.results : [])
    return NextResponse.json({ ok: true, results })
  } catch (e:any) {
    return NextResponse.json({ ok: false, results: [], error: e?.message ?? 'git-failed' })
  }
}

